import argparse
import json
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


FONT_REGULAR = r"C:\Windows\Fonts\malgun.ttf"
FONT_BOLD = r"C:\Windows\Fonts\malgunbd.ttf"


def para(text, style):
    return Paragraph(str(text).replace("\n", "<br/>"), style)


def footer(canvas, doc):
    canvas.saveState()
    canvas.setFont("Malgun", 8)
    canvas.setFillColor(colors.black)
    canvas.drawRightString(A4[0] - 18 * mm, 12 * mm, str(doc.page))
    canvas.restoreState()


def table_from_rows(rows, label_style, cell_style):
    data = [[para(key, label_style), para(value, cell_style)] for key, value in rows]
    table = Table(data, colWidths=[48 * mm, 124 * mm], hAlign="LEFT")
    table.setStyle(
        TableStyle(
            [
                ("FONTNAME", (0, 0), (-1, -1), "Malgun"),
                ("TEXTCOLOR", (0, 0), (-1, -1), colors.black),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#BFBFBF")),
                ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#F2F2F2")),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
                ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    return table


def build(input_path, output_override=None):
    input_path = Path(input_path)
    payload = json.loads(input_path.read_text(encoding="utf-8"))
    output_path = Path(output_override or payload.get("output") or f"{input_path.stem}.pdf")
    if not output_path.is_absolute():
        output_path = input_path.parent / output_path

    pdfmetrics.registerFont(TTFont("Malgun", FONT_REGULAR))
    pdfmetrics.registerFont(TTFont("Malgun-Bold", FONT_BOLD))

    styles = getSampleStyleSheet()
    base = ParagraphStyle(
        "base",
        parent=styles["Normal"],
        fontName="Malgun",
        fontSize=9.5,
        leading=14,
        textColor=colors.black,
        alignment=TA_LEFT,
        wordWrap="CJK",
    )
    title = ParagraphStyle("title", parent=base, fontName="Malgun-Bold", fontSize=15, leading=20, alignment=TA_CENTER, spaceAfter=8)
    section = ParagraphStyle("section", parent=base, fontName="Malgun-Bold", fontSize=11, leading=15, spaceBefore=8, spaceAfter=4)
    cell = ParagraphStyle("cell", parent=base, fontSize=9, leading=13)
    label = ParagraphStyle("label", parent=cell, fontName="Malgun-Bold")
    note = ParagraphStyle("note", parent=base, fontSize=8.5, leading=12)

    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=A4,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        topMargin=18 * mm,
        bottomMargin=18 * mm,
        title=payload.get("title", ""),
        author="",
    )

    story = [para(payload.get("title", "한국어 번역본"), title)]
    for item in payload.get("sections", []):
        if item.get("heading"):
            story.append(para(item["heading"], section))
        if item.get("rows"):
            story.append(table_from_rows(item["rows"], label, cell))
        if item.get("note"):
            story.append(Spacer(1, 3 * mm))
            story.append(para(item["note"], note))

    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    print(output_path)


def main():
    parser = argparse.ArgumentParser(description="Build a Korean product-spec PDF from structured JSON.")
    parser.add_argument("json", help="Input JSON path")
    parser.add_argument("--out", help="Optional output PDF path")
    args = parser.parse_args()
    build(args.json, args.out)


if __name__ == "__main__":
    main()
