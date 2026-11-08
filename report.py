import os
from datetime import datetime
from html import unescape
import re
from fpdf import FPDF


def save_report(topic: str, content: str) -> str:
    """Save the final research report to a text file."""

    # Create reports folder if it doesn't exist
    os.makedirs("reports", exist_ok=True)

    # Create a clean filename from the topic
    filename = topic.strip().lower().replace(" ", "_")
    filename = re.sub(r'[<>:"/\\|?*]', '', filename)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filepath = f"reports/{filename}_{timestamp}.txt"

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(f"RESEARCH REPORT: {topic.upper()}\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("=" * 60 + "\n\n")
        f.write(content)

    print(f"[Report] Saved to: {filepath}")
    return filepath


def _pdf_text(value: str) -> str:
    """Convert common Markdown/HTML text to characters Helvetica can render."""
    value = re.sub(r"<br\s*/?>", "\n", value, flags=re.IGNORECASE)
    value = re.sub(r"<[^>]+>", "", value)
    value = unescape(value)
    value = re.sub(r"!?\[([^]]+)\]\([^)]+\)", r"\1", value)
    value = re.sub(r"(\*\*|__|`)", "", value)
    for old, new in {"\u2019": "'", "\u2018": "'", "\u201c": '"', "\u201d": '"',
                     "\u2022": "-", "\u2013": "-", "\u2014": "-", "\u2192": "->",
                     "\u2190": "<-", "\u00a0": " "}.items():
        value = value.replace(old, new)
    return value.encode("latin-1", errors="replace").decode("latin-1")


def _table_cells(line: str) -> list[str]:
    return [_pdf_text(cell.strip().replace(r"\|", "|")) for cell in re.split(r"(?<!\\)\|", line.strip().strip("|"))]


def _is_table_separator(line: str) -> bool:
    return bool(re.fullmatch(r"\s*\|?\s*:?-{3,}:?(?:\s*\|\s*:?-{3,}:?)*\s*\|?\s*", line))


def _render_table(pdf: FPDF, lines: list[str]) -> None:
    headers = _table_cells(lines[0])
    rows = [_table_cells(line) for line in lines[2:]]
    column_count = len(headers)
    if column_count < 2:
        return

    pdf.set_font("Helvetica", "", 9)
    # Give the explanation column extra room in the common two-column report table.
    widths = (1, 2.5) if column_count == 2 else None
    with pdf.table(col_widths=widths, text_align="LEFT", line_height=5.5, padding=2) as table:
        for cells in [headers, *rows]:
            row = table.row()
            for cell in (cells + [""] * column_count)[:column_count]:
                row.cell(cell)
    pdf.set_font("Helvetica", "", 11)
    pdf.ln(4)


def generate_pdf_bytes(topic: str, content: str, sources: list = []) -> bytes:
    """Generate a PDF report and return it as bytes for download."""
    pdf = FPDF()
    pdf.add_page()

    # Title
    pdf.set_font("Helvetica", "B", 16)
    safe_topic = _pdf_text(topic)
    pdf.multi_cell(0, 10, safe_topic.upper())
    pdf.ln(2)

    # Generated timestamp
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(128, 128, 128)
    pdf.cell(0, 8, f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", ln=True)
    pdf.ln(3)
    pdf.set_text_color(0, 0, 0)

    # Render headings, paragraphs, and Markdown tables separately.
    lines = content.splitlines()
    index = 0
    while index < len(lines):
        line = lines[index].strip()
        if not line:
            pdf.ln(3)
            index += 1
            continue
        if index + 1 < len(lines) and "|" in line and _is_table_separator(lines[index + 1]):
            table_lines = [line, lines[index + 1]]
            index += 2
            while index < len(lines) and "|" in lines[index] and lines[index].strip():
                table_lines.append(lines[index])
                index += 1
            _render_table(pdf, table_lines)
            continue
        heading = re.match(r"^(#{1,6})\s+(.+)$", line)
        if heading:
            pdf.set_font("Helvetica", "B", 13 if len(heading.group(1)) <= 2 else 11)
            pdf.multi_cell(0, 8, _pdf_text(heading.group(2)), new_x="LMARGIN", new_y="NEXT")
            pdf.set_font("Helvetica", "", 11)
        else:
            pdf.set_font("Helvetica", "", 11)
            pdf.multi_cell(0, 7, _pdf_text(line), new_x="LMARGIN", new_y="NEXT")
        index += 1

    # Sources section with hyperlinks
    if sources:
        pdf.ln(5)
        pdf.set_font("Helvetica", "B", 12)
        pdf.cell(0, 10, "Sources", ln=True)
        pdf.set_font("Helvetica", "", 10)
        for i, url in enumerate(sources, 1):
            safe_url = _pdf_text(url)
            pdf.set_text_color(0, 0, 255)
            pdf.cell(8, 8, f"{i}.", ln=False)
            pdf.cell(0, 8, safe_url, ln=True, link=url)
            pdf.set_text_color(0, 0, 0)

    return bytes(pdf.output())
