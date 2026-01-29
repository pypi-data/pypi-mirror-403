import csv
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

def export_csv(networks, filename=wifi_report.csv)
    if not networks
        return

    with open(filename, w, newline=, encoding=utf-8) as f
        writer = csv.DictWriter(f, fieldnames=networks[0].keys())
        writer.writeheader()
        writer.writerows(networks)

def export_pdf(networks, filename=wifi_report.pdf)
    c = canvas.Canvas(filename, pagesize=A4)
    y = 800

    c.drawString(40, y, Cybrushwifi – Wi‑Fi Security Report)
    y -= 30

    for n in networks
        line = f{n['SSID']}  {n['Encryption']}  {n['Signal']}  {n['Risk']}
        c.drawString(40, y, line)
        y -= 20

        if y  50
            c.showPage()
            y = 800

    c.save()
