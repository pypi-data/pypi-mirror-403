import requests
from sphere_can.config import api_base


def stop(name: str):
    """
    Stop a running CAN sender by name.
    """

    url = f"{api_base()}/can/stop/{name}"

    r = requests.post(url, timeout=2)
    r.raise_for_status()

    print(f"[stop] stopped {name}")
