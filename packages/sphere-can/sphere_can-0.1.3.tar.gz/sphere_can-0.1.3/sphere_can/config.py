import os

DEFAULT_API = "http://server:8000"

def api_base():
    return os.environ.get("SPHERE_API", DEFAULT_API)

def ws_base():
    return api_base().replace("http", "ws")
