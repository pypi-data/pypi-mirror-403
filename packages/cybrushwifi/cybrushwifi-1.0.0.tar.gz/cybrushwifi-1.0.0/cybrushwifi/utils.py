import socket
import requests

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "Unknown"

def get_public_ip():
    try:
        return requests.get("https://api.ipify.org", timeout=5).text
    except Exception:
        return "Unavailable"
