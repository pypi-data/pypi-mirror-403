import os
import sys

import typer
from rich.console import Console
from rich.table import Table

from epivault.deps import check_dependencies, install_system_deps
from epivault.manager import LockAbortedError, VolumeInUseError, VolumeManager

app = typer.Typer(help="EpiVault: Secure, Ephemeral, FIDO2-bound Storage.")
console = Console()
manager = VolumeManager()


def _warn_and_offer_install_if_needed(uses_ttl: bool, no_service_warning: bool) -> None:
    """If TTL is used and the boot service is not installed, warn and offer to install."""
    if no_service_warning or not uses_ttl or manager.is_rehydrate_timer_installed():
        return
    console.print(
        "[yellow]The boot service is not installed. Auto cleanup (lock/purge) will not "
        "persist across reboots.[/yellow]"
    )
    if typer.confirm("Install the boot service now?", default=False):
        manager.install_rehydrate_timer()


@app.callback(invoke_without_command=True)
def callback(ctx: typer.Context):
    """
    EpiVault CLI
    """
    if ctx.invoked_subcommand is None:
        typer.echo(ctx.get_help())
        raise typer.Exit(0)


@app.command()
def create(
    name: str = typer.Argument(..., help="Name of the volume (e.g., project_alpha)"),
    size: int = typer.Option(None, "--size", "-s", help="Size in MB"),
    purge: str = typer.Option(None, "--purge", "-p", help="Auto-purge TTL (e.g., 2h, 1d)"),
    no_service_warning: bool = typer.Option(
        False,
        "--no-service-warning",
        help="Do not warn when the boot service is not installed (auto cleanup won't persist).",
    ),
):
    """Create a new secure volume (Interactive FIDO2 enrollment)."""
    if not check_dependencies():
        console.print("[red]Missing dependencies. Run 'epivault install-deps'.[/red]")
        raise typer.Exit(1)

    # Prompt for size if not provided
    if size is None:
        size_input = typer.prompt("Volume size in MB", default="500")
        try:
            size = int(size_input)
        except ValueError as e:
            console.print("[bold red]Error:[/bold red] Size must be a valid integer.")
            raise typer.Exit(1) from e

    # Prompt for purge TTL if not provided
    if purge is None:
        purge = typer.prompt(
            "Auto-purge TTL (optional, e.g., 2h, 1d). Press Enter to skip",
            default="",
            show_default=False,
        )
        purge = purge.strip() if purge.strip() else None

    _warn_and_offer_install_if_needed(uses_ttl=bool(purge), no_service_warning=no_service_warning)

    try:
        manager.create_volume(name, size, purge)
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        raise typer.Exit(1) from e


@app.command()
def list():
    """List all available volumes."""
    vols = manager.list_volumes()

    table = Table(title="EpiVault Volumes")
    table.add_column("Name", style="cyan")
    table.add_column("Logical Size", justify="right")
    table.add_column("Disk Used", justify="right")
    table.add_column("Status")
    table.add_column("Mount Point")
    table.add_column("TTL", style="dim")

    for v in vols:
        status_style = "green" if v["status"] == "Mounted" else "red"
        table.add_row(
            v["name"],
            v["size"],
            v["used"],
            f"[{status_style}]{v['status']}[/{status_style}]",
            v["mount"],
            v["ttl"],
        )

    console.print(table)


def _select_volume() -> str:
    """Interactive volume selector. Returns the selected volume name."""
    vols = manager.list_volumes()
    if not vols:
        console.print("[red]No volumes found.[/red]")
        raise typer.Exit(1)

    console.print("\n[bold cyan]Available volumes:[/bold cyan]")
    for i, v in enumerate(vols, 1):
        status_style = (
            "green"
            if v["status"] == "Mounted"
            else "yellow"
            if v["status"] == "Unlocked"
            else "red"
        )
        console.print(
            f"  [bold]{i}.[/bold] {v['name']} - "
            f"[{status_style}]{v['status']}[/{status_style}] - "
            f"{v['size']} - {v['ttl']}"
        )

    while True:
        try:
            choice = typer.prompt(f"\nSelect volume (1-{len(vols)})", default="1")
            idx = int(choice) - 1
            if 0 <= idx < len(vols):
                return vols[idx]["name"]
            console.print(
                f"[red]Invalid choice. Please enter a number between 1 and {len(vols)}.[/red]"
            )
        except ValueError:
            console.print("[red]Invalid input. Please enter a number.[/red]")
        except (KeyboardInterrupt, EOFError):
            console.print("\n[yellow]Cancelled.[/yellow]")
            raise typer.Exit(0) from None


@app.command()
def unlock(
    name: str = typer.Argument(
        None, help="Name of the volume (optional, will prompt if not provided)"
    ),
    mount: str = typer.Option(None, "--mount", "-m", help="Custom mount point (optional)"),
    lock: str = typer.Option(None, "--lock", "-l", help="Auto-lock TTL (e.g., 30m)"),
    no_service_warning: bool = typer.Option(
        False,
        "--no-service-warning",
        help="Do not warn when the boot service is not installed (auto cleanup won't persist).",
    ),
):
    """Unlock and mount a volume (Interactive FIDO2 auth)."""
    # If no name provided, show interactive selector
    if name is None:
        name = _select_volume()

    # Default: mount in ./epivault-<name> so the shell doesn't need to cd out/in
    default_mount = os.path.join(os.getcwd(), f"epivault-{name}")

    # Prompt for mount point if not provided
    if mount is None:
        mount_input = typer.prompt(
            "Mount point (optional). Press Enter for default",
            default=default_mount,
            show_default=True,
        )
        # If user entered something custom, use it; otherwise use None to trigger default behavior
        mount = (
            mount_input.strip()
            if mount_input.strip() and mount_input.strip() != default_mount
            else None
        )

    # Prompt for lock TTL if not provided
    if lock is None:
        lock_input = typer.prompt(
            "Auto-lock TTL (optional, e.g., 30m, 1h, 1d). Press Enter to skip",
            default="",
            show_default=False,
        )
        lock = lock_input.strip() if lock_input.strip() else None

    _warn_and_offer_install_if_needed(uses_ttl=bool(lock), no_service_warning=no_service_warning)

    try:
        manager.unlock_volume(name, lock, mount)
    except Exception as e:
        console.print(f"[bold red]Unlock failed:[/bold red] {e}")
        raise typer.Exit(1) from e


def _confirm_before_kill():
    """Return a confirm callback when running interactively (TTY); None when non-interactive (e.g. timer)."""
    if not sys.stdin.isatty():
        return None

    def confirm(msg: str) -> bool:
        return typer.confirm(msg, default=False)

    return confirm


@app.command()
def lock(name: str):
    """Lock (unmount and close) a volume."""
    try:
        manager.lock_volume(name, confirm_before_kill=_confirm_before_kill())
    except VolumeInUseError:
        raise typer.Exit(1) from None
    except LockAbortedError:
        raise typer.Exit(0) from None


@app.command()
def purge(
    name: str,
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation prompt"),
):
    """Destroy a volume permanently."""
    # Skip confirmation if --yes flag or non-interactive (no TTY, e.g. systemd timer)
    should_purge = yes or not sys.stdin.isatty()
    if not should_purge:
        should_purge = typer.confirm(
            f"Are you sure you want to DESTROY {name}? This cannot be undone."
        )

    if should_purge:
        try:
            manager.purge_volume(name, confirm_before_kill=_confirm_before_kill())
        except VolumeInUseError:
            raise typer.Exit(1) from None
        except LockAbortedError:
            raise typer.Exit(0) from None


@app.command()
def cleanup(
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation prompt"),
):
    """Emergency cleanup of all volumes."""
    # Skip confirmation if --yes flag or non-interactive (no TTY)
    should_cleanup = yes or not sys.stdin.isatty()
    if not should_cleanup:
        should_cleanup = typer.confirm("Force close all volumes?")

    if should_cleanup:
        try:
            manager.cleanup_all(confirm_before_kill=_confirm_before_kill())
        except VolumeInUseError:
            raise typer.Exit(1) from None
        except LockAbortedError:
            raise typer.Exit(0) from None


@app.command()
def install_deps():
    """Install system dependencies (apt)."""
    install_system_deps()


@app.command()
def install_service():
    """Install systemd boot service for TTL reliability."""
    manager.install_rehydrate_timer()


@app.command()
def uninstall_service():
    """Remove the systemd boot service (opposite of install-service)."""
    manager.uninstall_rehydrate_timer()


# --- Internal Systemd Callbacks ---


@app.command(hidden=True)
def rehydrate():
    manager.rehydrate_timers()


if __name__ == "__main__":
    app()
