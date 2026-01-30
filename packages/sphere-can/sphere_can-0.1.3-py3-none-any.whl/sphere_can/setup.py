import typer
import requests
from sphere_can.config import api_base

setup = typer.Typer(
    help=(
        "ECU relay control\n\n"
        "Examples:\n"
        "  sphere-can setup on ddec\n"
        "  sphere-can setup off cummins\n"
        "  sphere-can setup status\n"
        "  sphere-can setup list\n\n"
        "Available ECUs:\n"
        "  cummins, ddec, bendix"
    )
)

AVAILABLE_ECUS = ["cummins", "ddec", "bendix"]


@setup.command("on")
def ecu_on(
    ecu: str = typer.Argument(
        ...,
        help="ECU name (one of: cummins, ddec, bendix)"
    )
):
    """Turn ECU relay ON."""
    r = requests.post(f"{api_base()}/relay", params={"ecu": ecu, "on": True})
    r.raise_for_status()
    print(f"{ecu}: ON")


@setup.command("off")
def ecu_off(
    ecu: str = typer.Argument(
        ...,
        help="ECU name (one of: cummins, ddec, bendix)"
    )
):
    """Turn ECU relay OFF."""
    r = requests.post(f"{api_base()}/relay", params={"ecu": ecu, "on": False})
    r.raise_for_status()
    print(f"{ecu}: OFF")


@setup.command("status")
def ecu_status():
    """Show ECU relay status."""
    r = requests.get(f"{api_base()}/status")
    r.raise_for_status()
    for ecu, state in r.json()["ecus"].items():
        print(f"{ecu}: {'ON' if state else 'OFF'}")


@setup.command("list")
def ecu_list():
    """List available ECUs."""
    for ecu in AVAILABLE_ECUS:
        print(ecu)
