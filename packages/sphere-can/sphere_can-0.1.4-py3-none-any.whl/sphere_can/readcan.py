import json
import time
import websocket
import sys
import threading
from typing import Optional
from sphere_can.config import api_base


_stop = False

def _watch_ctrl_c():
    global _stop
    try:
        while True:
            ch = sys.stdin.read(1)
            if ch == "\x03":  # literal Ctrl+C
                _stop = True
                break
    except Exception:
        pass


def _format_frame(f):
    ts = f["ts"]
    bus = f["bus"]
    raw_id = f["id"]
    arb = int(raw_id, 16)
    arb_str = f"{arb:x}"
    raw_data = f["data"]
    if isinstance(raw_data, str):
        data = raw_data[2:] if raw_data.startswith("0x") else raw_data
    else:
        data = "".join(f"{b:02x}" for b in raw_data)

    return f"({ts:.6f}) {bus} {arb_str}#{data}"


def _parse_filter_id(val: Optional[str]) -> Optional[int]:
    if val is None:
        return None
    return int(val, 16)


def readcan(
    can_interface: str,
    *,
    filter_id: Optional[str] = None,
    log: Optional[str] = None,
    timeout: Optional[float] = None,
):

    """
    Read CAN frames from server (candump-style).
    """
    global _stop
    _stop = False

    # start Ctrl+C watcher
    threading.Thread(target=_watch_ctrl_c, daemon=True).start()
    start_time = time.monotonic()
    url = f"{api_base().replace('http', 'ws')}/ws/readcan/{can_interface}"

    # IMPORTANT: timeout required so loop can notice _stop
    ws = websocket.WebSocket(timeout=1.0)
    ws.connect(url)

    logfile = None
    if log:
        logfile = open(log, "a", buffering=1)
        print(f"[readcan] logging to {log}")

    filter_arb = _parse_filter_id(filter_id)

    try:
        while not _stop:
            if timeout is not None:
                if time.monotonic() - start_time >= timeout:
                    break
            
            try:
                frames = json.loads(ws.recv())
            except websocket.WebSocketTimeoutException:
                continue

            for f in frames:
                if _stop:
                    break

                arb = int(f["id"], 16)

                if filter_arb is not None and arb != filter_arb:
                    continue

                line = _format_frame(f)

                print(line)

                if logfile:
                    logfile.write(line + "\n")

    finally:
        print("\n[readcan] stopped")

        try:
            ws.close()
        except Exception:
            pass

        if logfile:
            logfile.close()
