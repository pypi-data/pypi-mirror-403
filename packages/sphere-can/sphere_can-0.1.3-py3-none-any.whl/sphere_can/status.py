import requests
from sphere_can.config import api_base

def status():
    """
    Show server status
    """
    url = f"{api_base()}/status"
    r = requests.get(url)
    r.raise_for_status()

    data = r.json()

    print("ECUs:")
    for ecu, state in data["ecus"].items():
        print(f"  {ecu}: {'ON' if state else 'OFF'}")

    print("\nCAN interfaces:")
    for c in data["can_interfaces"]:
        print(f"  {c}")
