def check_alerts(networks)
    alerts = []

    for n in networks
        if n[Encryption].lower() == open
            alerts.append(f⚠ Open network detected {n['SSID']})

        if isinstance(n[Signal], (int, float)) and n[Signal]  30
            alerts.append(f⚠ Weak signal {n['SSID']})

    return alerts
