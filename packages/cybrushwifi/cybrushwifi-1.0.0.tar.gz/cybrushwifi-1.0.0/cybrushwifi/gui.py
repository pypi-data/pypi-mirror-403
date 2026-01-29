import webview
from .scanner import scan_networks
from .alerts import check_alerts
from .history import save_scan
from .utils import get_local_ip, get_public_ip

class API:
    def scan(self):
        networks = scan_networks()
        save_scan(networks)
        alerts = check_alerts(networks)

        return {
            "networks": networks,
            "alerts": alerts,
            "local_ip": get_local_ip(),
            "public_ip": get_public_ip()
        }

def start_gui():
    webview.create_window(
        "Cybrushwifi – Wireless Security",
        "web/index.html",
        js_api=API(),
        width=1200,
        height=750
    )
    webview.start()
