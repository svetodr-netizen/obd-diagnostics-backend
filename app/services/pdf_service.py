from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from datetime import datetime
import io
import os

# Register fonts
_dir = os.path.dirname(__file__)
pdfmetrics.registerFont(TTFont('DejaVu', os.path.join(_dir, 'DejaVuSans.ttf')))
pdfmetrics.registerFont(TTFont('DejaVu-Bold', os.path.join(_dir, 'DejaVuSans-Bold.ttf')))


def generate_pdf_report(
    dtc_codes: list,
    ai_analysis: str,
    sensor_data: dict = None,
    vehicle_info: dict = None,
) -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=2*cm,
        leftMargin=2*cm,
        topMargin=2*cm,
        bottomMargin=2*cm,
    )

    title_style = ParagraphStyle('Title', fontSize=20, fontName='DejaVu-Bold', textColor=colors.HexColor('#1a1a2e'), spaceAfter=6, alignment=TA_CENTER)
    subtitle_style = ParagraphStyle('Subtitle', fontSize=11, fontName='DejaVu', textColor=colors.HexColor('#666666'), spaceBefore=8, spaceAfter=20, alignment=TA_CENTER)
    heading_style = ParagraphStyle('Heading', fontSize=13, fontName='DejaVu-Bold', textColor=colors.HexColor('#4f46e5'), spaceAfter=8, spaceBefore=16)
    body_style = ParagraphStyle('Body', fontSize=10, fontName='DejaVu', textColor=colors.HexColor('#333333'), spaceAfter=6, leading=16)

    story = []

    story.append(Paragraph("OBD-AI Dijagnostički Izvještaj", title_style))
    story.append(Paragraph(f"Generirano: {datetime.now().strftime('%d.%m.%Y %H:%M')}", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor('#4f46e5')))
    story.append(Spacer(1, 0.5*cm))

    if vehicle_info:
        story.append(Paragraph("Informacije o vozilu", heading_style))
        vehicle_data = [
            ['Marka', vehicle_info.get('make', '-')],
            ['Model', vehicle_info.get('model', '-')],
            ['Godina', str(vehicle_info.get('year', '-'))],
            ['Motor', vehicle_info.get('engine_code', '-')],
            ['Protokol', vehicle_info.get('protocol', '-')],
        ]
        t = Table(vehicle_data, colWidths=[4*cm, 12*cm])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f0f0ff')),
            ('FONTNAME', (0, 0), (0, -1), 'DejaVu-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'DejaVu'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cccccc')),
            ('PADDING', (0, 0), (-1, -1), 6),
        ]))
        story.append(t)
        story.append(Spacer(1, 0.3*cm))

    if dtc_codes:
        story.append(Paragraph(f"Detektirane greške ({len(dtc_codes)})", heading_style))
        dtc_data = [['Kod', 'Opis']]
        for dtc in dtc_codes:
            dtc_data.append([dtc.get('code', '-'), dtc.get('description', 'Nepoznato')])
        t = Table(dtc_data, colWidths=[3*cm, 13*cm])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4f46e5')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'DejaVu-Bold'),
            ('FONTNAME', (0, 1), (-1, -1), 'DejaVu'),
            ('FONTNAME', (0, 1), (0, -1), 'DejaVu-Bold'),
            ('TEXTCOLOR', (0, 1), (0, -1), colors.HexColor('#ef4444')),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cccccc')),
            ('PADDING', (0, 0), (-1, -1), 6),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f8ff')]),
        ]))
        story.append(t)
        story.append(Spacer(1, 0.3*cm))

    if sensor_data:
        story.append(Paragraph("Stanje senzora", heading_style))
        sensor_table_data = [['Senzor', 'Vrijednost', 'Jedinica']]
        for key, data in sensor_data.items():
            if isinstance(data, dict):
                sensor_table_data.append([
                    data.get('name', key).replace('_', ' '),
                    str(data.get('value', '-')),
                    data.get('unit', '-'),
                ])
        t = Table(sensor_table_data, colWidths=[7*cm, 5*cm, 4*cm])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4f46e5')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'DejaVu-Bold'),
            ('FONTNAME', (0, 1), (-1, -1), 'DejaVu'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cccccc')),
            ('PADDING', (0, 0), (-1, -1), 5),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f8ff')]),
        ]))
        story.append(t)
        story.append(Spacer(1, 0.3*cm))

    if ai_analysis:
        story.append(Paragraph("AI Dijagnostička Analiza", heading_style))
        story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#cccccc')))
        story.append(Spacer(1, 0.2*cm))
        for line in ai_analysis.split('\n'):
            line = line.strip()
            if not line:
                story.append(Spacer(1, 0.2*cm))
            elif line.startswith('## ') or line.startswith('### ') or line.startswith('# '):
                text = line.lstrip('#').strip().replace('**', '')
                story.append(Paragraph(text, heading_style))
            elif line.startswith('* ') or line.startswith('- '):
                text = '• ' + line[2:].replace('**', '')
                story.append(Paragraph(text, body_style))
            else:
                clean = line.replace('**', '')
                story.append(Paragraph(clean, body_style))

    story.append(Spacer(1, 1*cm))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#cccccc')))
    story.append(Paragraph("OBD-AI Diagnostics — Automatski generiran izvještaj",
                           ParagraphStyle('Footer', fontSize=8, fontName='DejaVu', textColor=colors.grey, alignment=TA_CENTER)))

    doc.build(story)
    buffer.seek(0)
    return buffer.read()
def generate_driving_report(
    session_data: dict,
    ai_analysis: str,
    vehicle_info: dict = None,
) -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=2*cm,
        leftMargin=2*cm,
        topMargin=2*cm,
        bottomMargin=2*cm,
    )

    title_style = ParagraphStyle('Title', fontSize=20, fontName='DejaVu-Bold', textColor=colors.HexColor('#1a1a2e'), spaceAfter=6, alignment=TA_CENTER)
    subtitle_style = ParagraphStyle('Subtitle', fontSize=11, fontName='DejaVu', textColor=colors.HexColor('#666666'), spaceBefore=8, spaceAfter=20, alignment=TA_CENTER)
    heading_style = ParagraphStyle('Heading', fontSize=13, fontName='DejaVu-Bold', textColor=colors.HexColor('#4f46e5'), spaceAfter=8, spaceBefore=16)
    body_style = ParagraphStyle('Body', fontSize=10, fontName='DejaVu', textColor=colors.HexColor('#333333'), spaceAfter=6, leading=16)

    story = []

    story.append(Paragraph("OBD-AI Izvještaj Vožnje", title_style))
    story.append(Paragraph(f"Generirano: {datetime.now().strftime('%d.%m.%Y %H:%M')}", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor('#4f46e5')))
    story.append(Spacer(1, 0.5*cm))

    if vehicle_info:
        story.append(Paragraph("Informacije o vozilu", heading_style))
        vehicle_data = [
            ['Marka', vehicle_info.get('make', '-')],
            ['Model', vehicle_info.get('model', '-')],
            ['Godina', str(vehicle_info.get('year', '-'))],
            ['Motor', vehicle_info.get('engine_code', '-')],
        ]
        t = Table(vehicle_data, colWidths=[4*cm, 12*cm])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f0f0ff')),
            ('FONTNAME', (0, 0), (0, -1), 'DejaVu-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'DejaVu'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cccccc')),
            ('PADDING', (0, 0), (-1, -1), 6),
        ]))
        story.append(t)
        story.append(Spacer(1, 0.3*cm))

    story.append(Paragraph("Statistika vožnje", heading_style))
    stats_data = [
        ['Trajanje', f"{session_data.get('duration_min', 0)} min"],
        ['Broj mjerenja', str(session_data.get('snapshots', 0))],
        ['Prosječni RPM', str(session_data.get('avg_rpm', 0))],
        ['Maksimalna brzina', f"{session_data.get('max_speed', 0)} km/h"],
        ['Prosječno opterećenje', f"{session_data.get('avg_load', 0)}%"],
        ['Maksimalna temperatura', f"{session_data.get('max_temp', 0)}°C"],
    ]
    t = Table(stats_data, colWidths=[6*cm, 10*cm])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f0f0ff')),
        ('FONTNAME', (0, 0), (0, -1), 'DejaVu-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'DejaVu'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cccccc')),
        ('PADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(t)
    story.append(Spacer(1, 0.3*cm))

    dtc_codes = session_data.get('dtc_codes', [])
    if dtc_codes:
        story.append(Paragraph(f"DTC Greške ({len(dtc_codes)})", heading_style))
        dtc_data = [['Kod', 'Opis']]
        for dtc in dtc_codes:
            dtc_data.append([dtc.get('code', '-'), dtc.get('description', 'Nepoznato')])
        t = Table(dtc_data, colWidths=[3*cm, 13*cm])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4f46e5')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'DejaVu-Bold'),
            ('FONTNAME', (0, 1), (-1, -1), 'DejaVu'),
            ('FONTNAME', (0, 1), (0, -1), 'DejaVu-Bold'),
            ('TEXTCOLOR', (0, 1), (0, -1), colors.HexColor('#ef4444')),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cccccc')),
            ('PADDING', (0, 0), (-1, -1), 6),
        ]))
        story.append(t)
        story.append(Spacer(1, 0.3*cm))

    if ai_analysis:
        story.append(Paragraph("AI Analiza Vožnje", heading_style))
        story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#cccccc')))
        story.append(Spacer(1, 0.2*cm))
        for line in ai_analysis.split('\n'):
            line = line.strip()
            if not line:
                story.append(Spacer(1, 0.2*cm))
            elif line.startswith('## ') or line.startswith('### ') or line.startswith('# '):
                text = line.lstrip('#').strip().replace('**', '')
                story.append(Paragraph(text, heading_style))
            elif line.startswith('* ') or line.startswith('- '):
                text = '• ' + line[2:].replace('**', '')
                story.append(Paragraph(text, body_style))
            else:
                clean = line.replace('**', '')
                story.append(Paragraph(clean, body_style))

    story.append(Spacer(1, 1*cm))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#cccccc')))
    story.append(Paragraph("OBD-AI Diagnostics — Automatski generiran izvještaj",
                           ParagraphStyle('Footer', fontSize=8, fontName='DejaVu', textColor=colors.grey, alignment=TA_CENTER)))

    doc.build(story)
    buffer.seek(0)
    return buffer.read()