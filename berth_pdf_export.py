"""PDF-Export des Kaibelegungsplans (fpdf2, Helvetica-Kernfont)."""

import time


def generate_berth_plan_pdf(label, instance, result):
    from fpdf import FPDF
    from fpdf.enums import XPos, YPos

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, "Kaiplatz-Belegungsplan", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(120, 120, 120)
    pdf.cell(0, 6, f"Methode: {label}  -  Erstellt: {time.strftime('%d.%m.%Y %H:%M')}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_text_color(0, 0, 0)
    pdf.ln(4)

    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, "Zusammenfassung", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font("Helvetica", "", 10)
    summary_rows = [
        ("Kailänge", f"{instance.quay_length} m"),
        ("Anzahl Schiffe", str(result["n_ships"])),
        ("Gewichtete Wartezeit (Score)", f"{result['total_weighted_wait']:.1f}"),
        ("Wartezeit gesamt", f"{result['total_wait']:.1f} h"),
        ("Letzte Abfahrt", f"{result['last_departure']} h"),
        ("Sicherheitsabstand", f"{instance.safety_margin} m"),
    ]
    for label_text, value_text in summary_rows:
        pdf.cell(80, 7, label_text, border=0)
        pdf.cell(0, 7, value_text, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(4)

    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, "Belegung je Schiff", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font("Helvetica", "B", 9)
    headers = ["Schiff", "Priorität", "Ankunft", "Anlegebeginn", "Wartezeit", "Position"]
    widths = [28, 25, 22, 28, 24, 40]
    pdf.set_fill_color(230, 230, 230)
    for header, width in zip(headers, widths):
        pdf.cell(width, 7, header, border=1, fill=True, new_x=XPos.RIGHT, new_y=YPos.TOP)
    pdf.ln(7)

    pdf.set_font("Helvetica", "", 9)
    for idx in sorted(result["plan"].keys()):
        ship = instance.ships[idx]
        info = result["plan"][idx]
        row = [
            ship.name, ship.priority, f"{ship.arrival} h", f"{info['start']} h", f"{info['wait']} h",
            f"{info['pos']}-{info['pos'] + ship.length} m",
        ]
        for value, width in zip(row, widths):
            pdf.cell(width, 7, value, border=1, new_x=XPos.RIGHT, new_y=YPos.TOP)
        pdf.ln(7)

    return bytes(pdf.output())
