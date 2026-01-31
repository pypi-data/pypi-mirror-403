import shutil
import subprocess
import sys

from rich.console import Console

console = Console()

REQUIRED_BINS = [
    "cryptsetup",
    "systemd-cryptenroll",
    "mkfs.ext4",
    "truncate",
    "systemd-run",
    "fuser",
]
REQUIRED_PKGS = "systemd-cryptsetup fido2-tools libfido2-1 cryptsetup-bin psmisc"


def check_dependencies() -> bool:
    """Checks if all required system binaries are present."""
    missing = [bin for bin in REQUIRED_BINS if shutil.which(bin) is None]

    if missing:
        console.print(f"[bold red]❌ Missing system binaries:[/bold red] {', '.join(missing)}")
        return False
    return True


def install_system_deps():
    """Runs apt to install required packages."""
    console.print(f"[bold cyan]📦 Installing system dependencies: {REQUIRED_PKGS}...[/bold cyan]")
    try:
        subprocess.run(["apt", "update"], check=True)
        # Use list form instead of shell=True to prevent injection
        subprocess.run(["apt", "install", "-y"] + REQUIRED_PKGS.split(), check=True)
        console.print("[bold green]✅ System dependencies installed successfully.[/bold green]")
    except subprocess.CalledProcessError as e:
        console.print(f"[bold red]❌ Installation failed: {e}[/bold red]")
        sys.exit(1)
