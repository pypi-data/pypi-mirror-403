import fcntl
import json
import os
import re
import secrets
import subprocess
import sys
import tempfile
import time
from collections.abc import Callable
from pathlib import Path

from rich.console import Console

console = Console()


class VolumeInUseError(Exception):
    """Raised when a volume cannot be closed because the device is still in use."""

    pass


class LockAbortedError(Exception):
    """Raised when the user declines to confirm killing processes during lock."""

    pass


class VolumeManager:
    """
    Manages encrypted LUKS2 volumes with YubiKey FIDO2 authentication via CLI.
    """

    BASE_DIR = Path("/var/lib/epivault")
    MOUNT_BASE = Path("/mnt/epivault")

    SYSTEMD_CRYPTSETUP = "/usr/lib/systemd/systemd-cryptsetup"
    if not Path(SYSTEMD_CRYPTSETUP).exists():
        SYSTEMD_CRYPTSETUP = "/lib/systemd/systemd-cryptsetup"

    def __init__(self):
        # Secure directory creation
        old_umask = os.umask(0o077)
        try:
            self.BASE_DIR.mkdir(parents=True, exist_ok=True, mode=0o700)
            self.MOUNT_BASE.mkdir(parents=True, exist_ok=True, mode=0o700)
        finally:
            os.umask(old_umask)

        self._check_root()

        # Setup secure log directory for debugs
        self._log_dir = Path("/var/log/epivault")
        try:
            self._log_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
        except OSError:
            pass

    def _check_root(self):
        if os.geteuid() != 0:
            raise PermissionError("EpiVault must be run as root.")

    # --- Helpers ---

    def _run_silent(self, cmd: list[str], check=True):
        """Run a command headlessly, capturing output (good for scripts)."""
        return subprocess.run(
            cmd,
            check=check,
            capture_output=True,
            text=True,
            stdin=subprocess.DEVNULL,
        )

    def _run_interactive(self, cmd: list[str]):
        """
        Run a command allowing it to interact with the TTY directly.
        Essential for FIDO2 PIN prompts and Touch requests.
        """
        try:
            # We do NOT capture output; we let it flow to stdout/stderr
            subprocess.run(cmd, check=True)
        except subprocess.CalledProcessError as e:
            console.print(f"[bold red]Command failed:[/bold red] {' '.join(cmd)}")
            raise e

    def _validate_volume_name(self, name: str) -> str:
        if not re.match(r"^[a-zA-Z0-9_-]+$", name):
            raise ValueError(
                "Volume name can only contain letters, numbers, underscores, and hyphens"
            )
        return name

    def _sanitize_unit_name(self, name: str) -> str:
        safe = re.sub(r"[^a-zA-Z0-9_.-]", "_", name)
        return safe

    def _find_all_mount_points(self, device: str) -> list[Path]:
        """Return all mount points for a device (e.g. primary + bind mounts)."""
        result = self._run_silent(["findmnt", "-n", "-o", "TARGET", device], check=False)
        if result.returncode != 0 or not result.stdout.strip():
            return []
        return [Path(p.strip()) for p in result.stdout.strip().splitlines() if p.strip()]

    def _find_mount_point(self, device: str) -> Path | None:
        """Find one mount point for a device, if any. Returns None if not mounted."""
        mounts = self._find_all_mount_points(device)
        return mounts[0] if mounts else None

    def _kill_processes_using(self, path: str | Path) -> None:
        """Kill processes using the given path (mount point or device)."""
        subprocess.run(
            ["fuser", "-km", str(path)],
            capture_output=True,
            timeout=10,
        )

    def _ensure_unmounted(self, device: str, max_attempts: int = 5) -> bool:
        """
        Unmount a device and wait until it is fully unmounted. Handles multiple mount points
        (e.g. bind mounts). Tries lazy then force per mount. Returns True if no mounts remain.
        """
        for _ in range(max_attempts):
            mount_points = self._find_all_mount_points(device)
            if not mount_points:
                return True
            for mp in mount_points:
                r = subprocess.run(["umount", "-l", str(mp)], capture_output=True, text=True)
                if r.returncode != 0:
                    subprocess.run(["umount", "-f", str(mp)], capture_output=True)
            time.sleep(0.3)
        return len(self._find_all_mount_points(device)) == 0

    def _unlock_volume_lock_path(self, name: str) -> Path:
        """Path to the per-volume lock file for atomic unlock."""
        lock_dir = self.BASE_DIR / "locks"
        lock_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
        return lock_dir / f"{name}.lock"

    # --- TTL & Timer Logic (Unchanged as it is robust) ---

    @property
    def _timers_dir(self) -> Path:
        d = self.BASE_DIR / "timers"
        d.mkdir(parents=True, exist_ok=True)
        return d

    def _ttl_to_seconds(self, ttl: str) -> int:
        ttl = ttl.strip().lower()
        if not ttl:
            raise ValueError("Empty TTL")

        # Simple parser
        units = {"s": 1, "m": 60, "h": 3600, "d": 86400}
        if ttl[-1] in units:
            val = int(ttl[:-1])
            mult = units[ttl[-1]]
        else:
            val = int(ttl)
            mult = 60  # Default minutes

        return val * mult

    def _write_timer_meta(self, name: str, kind: str, ttl: str) -> None:
        name = self._validate_volume_name(name)
        seconds = self._ttl_to_seconds(ttl)
        expires_at = int(time.time()) + seconds
        meta = {"name": name, "kind": kind, "expires_at": expires_at}

        path = self._timers_dir / f"{kind}-{name}.json"
        with path.open("w") as f:
            json.dump(meta, f)
        os.chmod(path, 0o600)

    def _remove_timer_meta(self, name: str, kind: str) -> None:
        path = self._timers_dir / f"{kind}-{name}.json"
        try:
            path.unlink()
        except FileNotFoundError:
            pass

    def _humanize_seconds(self, seconds: int) -> str:
        """Format seconds as human-readable time remaining (e.g. '2h 15m', '45m', '30s')."""
        if seconds <= 0:
            return "now"
        parts = []
        d, remainder = divmod(seconds, 86400)
        if d:
            parts.append(f"{d}d")
        h, remainder = divmod(remainder, 3600)
        if h:
            parts.append(f"{h}h")
        m, s = divmod(remainder, 60)
        if m:
            parts.append(f"{m}m")
        if s or not parts:
            parts.append(f"{s}s")
        return " ".join(parts)

    def _get_volume_ttl(self, name: str) -> str:
        """Return humanized TTL summary for a volume (lock and/or purge), or '-' if none."""
        now = int(time.time())
        results = []
        for kind, label in [("lock", "Lock"), ("purge", "Purge")]:
            path = self._timers_dir / f"{kind}-{name}.json"
            if not path.exists():
                continue
            try:
                with path.open("r") as f:
                    meta = json.load(f)
                expires_at = meta.get("expires_at")
                if expires_at is None:
                    continue
                remaining = expires_at - now
                if remaining <= 0:
                    results.append(f"{label} now")
                else:
                    results.append(f"{label} in {self._humanize_seconds(remaining)}")
            except (json.JSONDecodeError, OSError):
                continue
        return ", ".join(results) if results else "-"

    def rehydrate_timers(self) -> None:
        """Re-schedules timers after a reboot based on persisted JSON metadata."""
        if not self._timers_dir.exists():
            return
        now = int(time.time())

        for meta_path in self._timers_dir.glob("*.json"):
            try:
                with meta_path.open("r") as f:
                    meta = json.load(f)

                name = meta.get("name")
                kind = meta.get("kind")
                expires_at = meta.get("expires_at")

                if not name or not expires_at:
                    continue

                remaining = expires_at - now
                if remaining <= 0:
                    # Expired while off: execute immediately
                    if kind == "lock":
                        self.lock_volume(name)
                    elif kind == "purge":
                        self.purge_volume(name)
                    meta_path.unlink(missing_ok=True)
                else:
                    # Reschedule
                    self._schedule_systemd_task(
                        unit_name=f"epivault-{kind}-{self._sanitize_unit_name(name)}",
                        action=kind,
                        volume_name=name,
                        time_spec=f"{remaining}s",
                    )
            except Exception:
                continue

    # --- Core Operations ---

    def list_volumes(self):
        volumes = []
        for file_path in self.BASE_DIR.glob("*.img"):
            name = file_path.stem
            mapper_path = Path(f"/dev/mapper/{name}")

            # Check if device is mounted anywhere (not just at MOUNT_BASE)
            all_mounts = self._find_all_mount_points(str(mapper_path))
            mapper_exists = mapper_path.exists()

            status = "Locked"
            if all_mounts:
                status = "Mounted"
            elif mapper_exists:
                status = "Unlocked"

            try:
                size_gb = file_path.stat().st_size / (1024**3)
                du = self._run_silent(["du", "-k", str(file_path)])
                used_mb = int(du.stdout.split()[0]) / 1024
            except (FileNotFoundError, IndexError):
                size_gb, used_mb = 0, 0

            ttl = self._get_volume_ttl(name)
            mount_str = ", ".join(str(p) for p in all_mounts) if all_mounts else "-"
            volumes.append(
                {
                    "name": name,
                    "size": f"{size_gb:.1f} GB",
                    "used": f"{used_mb:.1f} MB",
                    "status": status,
                    "mount": mount_str,
                    "ttl": ttl,
                }
            )
        return volumes

    def create_volume(self, name: str, size_mb: int, purge_ttl: str | None = None):
        name = self._validate_volume_name(name)
        vol_path = self.BASE_DIR / f"{name}.img"

        if vol_path.exists():
            raise FileExistsError(f"Volume {name} already exists.")

        console.print(f"[cyan]Allocating {size_mb}MB sparse file...[/cyan]")
        subprocess.run(["truncate", "-s", f"{size_mb}M", str(vol_path)], check=True)
        os.chmod(vol_path, 0o600)

        # 1. Generate bootstrap key for non-interactive formatting
        with tempfile.NamedTemporaryFile(mode="w", dir=self.BASE_DIR, delete=False) as tmp:
            os.chmod(tmp.name, 0o600)
            tmp.write(secrets.token_hex(64))
            bootstrap_key = Path(tmp.name)

        try:
            # 2. Format with LUKS2 (Silent)
            console.print("[cyan]Initializing LUKS2 container...[/cyan]")
            self._run_silent(
                [
                    "cryptsetup",
                    "luksFormat",
                    "-q",
                    "--type",
                    "luks2",
                    str(vol_path),
                    str(bootstrap_key),
                ]
            )

            # 3. Enroll FIDO2 (Interactive)
            console.print("\n[bold yellow]👉 ENROLLMENT: Interaction Required[/bold yellow]")
            console.print("[dim]The system will now ask for your FIDO2 PIN and/or Touch.[/dim]")

            self._run_interactive(
                [
                    "systemd-cryptenroll",
                    "--fido2-device=auto",
                    f"--unlock-key-file={bootstrap_key}",
                    str(vol_path),
                ]
            )

            # 4. Wipe Bootstrap Key
            console.print("\n[cyan]Wiping bootstrap key...[/cyan]")
            self._run_silent(
                [
                    "systemd-cryptenroll",
                    f"--unlock-key-file={bootstrap_key}",
                    "--wipe-slot=0",
                    str(vol_path),
                ]
            )

            # 5. Attach for Formatting (Interactive - requires FIDO2 unlock)
            console.print(
                "\n[bold yellow]👉 VERIFICATION: Unlocking to format filesystem...[/bold yellow]"
            )
            self._run_interactive(
                [
                    self.SYSTEMD_CRYPTSETUP,
                    "attach",
                    name,
                    str(vol_path),
                    "-",
                    "fido2-device=auto",
                ]
            )

            # 6. Make Filesystem
            console.print("[cyan]Creating ext4 filesystem...[/cyan]")
            self._run_silent(
                [
                    "mkfs.ext4",
                    "-q",
                    "-L",
                    name,
                    "-E",
                    "lazy_itable_init=1,lazy_journal_init=1",
                    f"/dev/mapper/{name}",
                ]
            )

            # 7. Detach
            self._run_silent([self.SYSTEMD_CRYPTSETUP, "detach", name])

            # 8. Schedule Purge if requested
            if purge_ttl:
                console.print(f"[cyan]Scheduling auto-purge in {purge_ttl}...[/cyan]")
                self._write_timer_meta(name, "purge", purge_ttl)
                self._schedule_systemd_task(
                    f"epivault-purge-{self._sanitize_unit_name(name)}",
                    "purge",
                    name,
                    purge_ttl,
                )

            console.print(f"[bold green]✅ Volume '{name}' created successfully.[/bold green]")

        finally:
            if bootstrap_key.exists():
                subprocess.run(["shred", "-u", str(bootstrap_key)], check=False)

    def unlock_volume(
        self,
        name: str,
        lock_ttl: str | None = None,
        mount_path: str | None = None,
    ):
        name = self._validate_volume_name(name)
        vol_path = self.BASE_DIR / f"{name}.img"
        mapper_path = Path(f"/dev/mapper/{name}")

        if not vol_path.exists():
            raise FileNotFoundError(f"Volume {name} not found.")

        # Determine mount point. Avoid mounting over cwd: the shell would still see
        # the pre-mount view until the user runs `cd .` or re-enters the directory.
        if mount_path:
            mp = Path(mount_path).resolve()
            mount_is_cwd = mp == Path.cwd()
        else:
            # Default: mount in a subdirectory of cwd so the shell doesn't need to cd out/in
            mp = Path.cwd() / f"epivault-{name}"
            mount_is_cwd = False

        # Atomic unlock: exclusive lock per volume to prevent double-mount and races
        lock_path = self._unlock_volume_lock_path(name)
        with open(lock_path, "w") as lock_file:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
            try:
                # Refuse if already unlocked or mounted
                if mapper_path.exists():
                    mount_where = self._find_mount_point(str(mapper_path))
                    if mount_where:
                        raise RuntimeError(
                            f"Volume {name} is already mounted at {mount_where}. Lock it first with 'epivault lock {name}'."
                        )
                    raise RuntimeError(
                        f"Volume {name} is already unlocked (mapper exists). Lock it first with 'epivault lock {name}'."
                    )

                # 1. Attach (Interactive)
                console.print("\n[bold yellow]👉 UNLOCK: Interaction Required[/bold yellow]")
                self._run_interactive(
                    [
                        self.SYSTEMD_CRYPTSETUP,
                        "attach",
                        name,
                        str(vol_path),
                        "-",
                        "fido2-device=auto",
                    ]
                )

                # 2. Mount (still under lock so no race with another unlock)
                mp.mkdir(parents=True, exist_ok=True)
                self._run_silent(["mount", f"/dev/mapper/{name}", str(mp)])
            finally:
                fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)

        # Fix permissions so user can write (outside lock; mount is done)
        try:
            os.chmod(mp, 0o777)
        except Exception:
            pass  # VFAT/NTFS might fail, EXT4 usually ok

        # 3. Schedule Lock if requested
        if lock_ttl:
            console.print(f"[cyan]Scheduling auto-lock in {lock_ttl}...[/cyan]")
            self._write_timer_meta(name, "lock", lock_ttl)
            self._schedule_systemd_task(
                f"epivault-lock-{self._sanitize_unit_name(name)}",
                "lock",
                name,
                lock_ttl,
            )

        console.print(f"[bold green]✅ Volume unlocked at: {mp}[/bold green]")
        if not mount_path:
            console.print(f"[dim]Run: [bold]cd {mp.name}[/bold] to use the volume.[/dim]")
        elif mount_is_cwd:
            console.print(
                "[dim]This is your current directory. Run: [bold]cd .[/bold] to see the volume in this terminal.[/dim]"
            )

    def lock_volume(
        self,
        name: str,
        *,
        confirm_before_kill: Callable[[str], bool] | None = None,
    ):
        """
        Unmount and close the volume. If the volume or device is in use, processes may be
        killed to force lock. When confirm_before_kill is provided (interactive use), the
        user is asked to confirm before any processes are killed. When None (e.g. timer),
        processes are killed without prompting.
        """
        name = self._validate_volume_name(name)
        mapper_path = Path(f"/dev/mapper/{name}")

        if not mapper_path.exists():
            console.print(f"[yellow]Volume {name} is not unlocked; nothing to lock.[/yellow]")
            return

        device_str = str(mapper_path)
        mount_points_before = self._find_all_mount_points(device_str)

        # Ensure all mounts are gone (lazy then force, with retries; kill processes if needed)
        if not self._ensure_unmounted(device_str):
            remaining = self._find_all_mount_points(device_str)
            if remaining:
                if confirm_before_kill is not None:
                    msg = (
                        "Volume is in use. Lock will terminate all processes using it "
                        "(e.g. shells, editors). Continue?"
                    )
                    if not confirm_before_kill(msg):
                        raise LockAbortedError("Lock aborted by user.")
                console.print("[yellow]Volume in use; terminating processes using it...[/yellow]")
                for mp in remaining:
                    self._kill_processes_using(mp)
                time.sleep(1.0)
            if not self._ensure_unmounted(device_str):
                remaining = self._find_all_mount_points(device_str)
                remaining_str = ", ".join(str(p) for p in remaining)
                console.print(
                    f"[bold red]Could not unmount {name}.[/bold red] "
                    f"Still mounted at: {remaining_str}."
                )
                raise RuntimeError(f"Volume {name} is still mounted at {remaining_str}")

        # Remove mount point directories we had (if empty)
        for mp in mount_points_before:
            try:
                mp.rmdir()
            except (OSError, FileNotFoundError):
                pass

        # Close LUKS: give kernel a moment after unmount, then try systemd + cryptsetup with retries
        time.sleep(0.5)
        subprocess.run(
            [self.SYSTEMD_CRYPTSETUP, "detach", name],
            capture_output=True,
            text=True,
        )
        close_result = None
        for _ in range(5):
            close_result = subprocess.run(
                ["cryptsetup", "close", name],
                capture_output=True,
                text=True,
            )
            if close_result.returncode == 0:
                break
            # Check if device is already closed (success case)
            err = (close_result.stderr or close_result.stdout or "").strip().lower()
            if "not active" in err or "does not exist" in err or "not found" in err:
                # Device is already closed - success
                break
            time.sleep(0.8)

        # If device still in use, kill processes holding it and retry close
        for _ in range(3):
            device_closed = not mapper_path.exists()
            if device_closed:
                break
            if close_result and close_result.returncode == 0:
                break
            err = (close_result.stderr or close_result.stdout or "").strip().lower()
            if "still in use" not in err and "busy" not in err:
                break
            if confirm_before_kill is not None:
                msg = (
                    "Device is still in use. Lock will terminate all processes using it. Continue?"
                )
                if not confirm_before_kill(msg):
                    raise LockAbortedError("Lock aborted by user.")
            console.print("[yellow]Device in use; terminating processes using it...[/yellow]")
            self._kill_processes_using(device_str)
            time.sleep(2.0)
            subprocess.run(
                [self.SYSTEMD_CRYPTSETUP, "detach", name],
                capture_output=True,
                text=True,
            )
            close_result = subprocess.run(
                ["cryptsetup", "close", name],
                capture_output=True,
                text=True,
            )

        device_closed = not mapper_path.exists()
        if close_result and close_result.returncode != 0 and not device_closed:
            err = (close_result.stderr or close_result.stdout or "").strip()
            mount_hint = (
                f" (e.g. lsof +D {mount_points_before[0]!s})" if mount_points_before else ""
            )
            console.print(
                f"[bold red]Could not close volume {name}.[/bold red] Device is still in use."
            )
            console.print(
                "[yellow]Find what is using it: [bold]lsof /dev/mapper/"
                + name
                + "[/bold]"
                + mount_hint
                + "[/yellow]"
            )
            console.print(
                "[yellow]Close those processes, then run [bold]epivault lock "
                + name
                + "[/bold] again.[/yellow]"
            )
            if err:
                console.print(f"[dim]{err}[/dim]")
            raise VolumeInUseError(f"Failed to close volume: {err or close_result.returncode}")

        # Stop Systemd Timer
        safe_name = self._sanitize_unit_name(name)
        subprocess.run(
            ["systemctl", "--user", "stop", f"epivault-lock-{safe_name}"],
            stderr=subprocess.DEVNULL,
        )

        self._remove_timer_meta(name, "lock")
        console.print(f"[yellow]Locked volume {name}.[/yellow]")

    def purge_volume(
        self,
        name: str,
        *,
        confirm_before_kill: Callable[[str], bool] | None = None,
    ):
        name = self._validate_volume_name(name)
        self.lock_volume(name, confirm_before_kill=confirm_before_kill)

        vol_path = self.BASE_DIR / f"{name}.img"
        if vol_path.exists():
            console.print(f"[red]Shredding {name}...[/red]")
            subprocess.run(["shred", "-u", str(vol_path)])

        # Clean timers
        safe_name = self._sanitize_unit_name(name)
        for t in ["lock", "purge"]:
            subprocess.run(
                ["systemctl", "stop", f"epivault-{t}-{safe_name}.timer"],
                stderr=subprocess.DEVNULL,
            )

        self._remove_timer_meta(name, "purge")
        self._remove_timer_meta(name, "lock")

        console.print(f"[bold red]Volume {name} purged.[/bold red]")

    def cleanup_all(
        self,
        *,
        confirm_before_kill: Callable[[str], bool] | None = None,
    ):
        """Emergency cleanup."""
        console.print("[bold red]Starting Emergency Cleanup...[/bold red]")
        for file_path in self.BASE_DIR.glob("*.img"):
            self.lock_volume(file_path.stem, confirm_before_kill=confirm_before_kill)
        console.print("[green]Cleanup complete.[/green]")

    def _schedule_systemd_task(self, unit_name, action, volume_name, time_spec):
        # Stop any existing timer/service with this name so systemd-run can create fresh transient units
        for suffix in (".timer", ".service"):
            subprocess.run(
                ["systemctl", "stop", f"{unit_name}{suffix}"],
                capture_output=True,
                check=False,
            )
        # Clear failed state so the unit name can be reused (failed transient units stick around)
        for suffix in (".timer", ".service"):
            subprocess.run(
                ["systemctl", "reset-failed", f"{unit_name}{suffix}"],
                capture_output=True,
                check=False,
            )
        cmd = [
            "systemd-run",
            "--collect",
            "--unit",
            unit_name,
            "--on-active",
            time_spec,
            sys.executable,
            "-m",
            "epivault.main",
            action,
            volume_name,
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            err = (result.stderr or result.stdout or "").strip()
            raise RuntimeError(f"Failed to schedule timer: {err or result.returncode}")

    # --- Boot Service ---

    REHYDRATE_SERVICE_PATH = Path("/etc/systemd/system/epivault-rehydrate.service")
    REHYDRATE_TIMER_PATH = Path("/etc/systemd/system/epivault-rehydrate.timer")

    def is_rehydrate_timer_installed(self) -> bool:
        """Return True if the rehydrate timer (boot service) is installed."""
        return self.REHYDRATE_TIMER_PATH.exists()

    def install_rehydrate_timer(self) -> None:
        service = f"""[Unit]
Description=EpiVault Rehydration
[Service]
Type=oneshot
ExecStart={sys.executable} -m epivault.main rehydrate
"""
        timer = """[Unit]
Description=EpiVault Rehydration Timer
[Timer]
OnBootSec=30s
OnUnitActiveSec=5m
Unit=epivault-rehydrate.service
[Install]
WantedBy=multi-user.target
"""
        self.REHYDRATE_SERVICE_PATH.write_text(service)
        self.REHYDRATE_TIMER_PATH.write_text(timer)
        subprocess.run(["systemctl", "daemon-reload"])
        subprocess.run(["systemctl", "enable", "--now", "epivault-rehydrate.timer"])
        console.print("[green]Boot service installed.[/green]")

    def uninstall_rehydrate_timer(self) -> None:
        """Remove the rehydrate timer and service (opposite of install_rehydrate_timer)."""
        if not self.is_rehydrate_timer_installed():
            console.print("[yellow]Boot service is not installed.[/yellow]")
            return
        subprocess.run(
            ["systemctl", "disable", "--now", "epivault-rehydrate.timer"],
            capture_output=True,
        )
        subprocess.run(["systemctl", "daemon-reload"])
        try:
            self.REHYDRATE_TIMER_PATH.unlink()
        except FileNotFoundError:
            pass
        try:
            self.REHYDRATE_SERVICE_PATH.unlink()
        except FileNotFoundError:
            pass
        console.print("[green]Boot service uninstalled.[/green]")
