import subprocess
import platform
import re

def scan_networks():
    os_name = platform.system()
    networks = []

    if os_name == "Windows":
        output = subprocess.check_output(
            ["netsh", "wlan", "show", "networks", "mode=bssid"],
            shell=True,
            text=True,
            errors="ignore"
        )

        ssid = None
        enc = "Unknown"

        for line in output.splitlines():
            line = line.strip()

            if line.startswith("SSID") and "BSSID" not in line:
                ssid = line.split(":", 1)[1].strip()

            elif line.startswith("Authentication"):
                enc = line.split(":", 1)[1].strip()

            elif line.startswith("Signal"):
                signal = int(line.split(":", 1)[1].replace("%", "").strip())

                networks.append({
                    "SSID": ssid or "Hidden",
                    "Encryption": enc,
                    "Signal": signal,
                    "Risk": "HIGH" if enc == "Open" else "MEDIUM"
                })

    elif os_name == "Linux":
        iface_info = subprocess.check_output(["iw", "dev"], text=True)
        iface = re.search(r'Interface (\w+)', iface_info).group(1)

        scan = subprocess.check_output(
            ["iw", iface, "scan"],
            stderr=subprocess.DEVNULL,
            text=True
        )

        for block in scan.split("BSS"):
            if "SSID:" in block:
                ssid = re.search(r"SSID: (.+)", block)
                signal = re.search(r"signal: ([-\d.]+)", block)
                enc = "Open" if "RSN:" not in block else "WPA/WPA2"

                networks.append({
                    "SSID": ssid.group(1) if ssid else "Hidden",
                    "Encryption": enc,
                    "Signal": float(signal.group(1)) if signal else -90,
                    "Risk": "HIGH" if enc == "Open" else "MEDIUM"
                })

    return networks
