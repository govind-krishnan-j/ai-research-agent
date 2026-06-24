import os
from datetime import datetime
from rich.console import Console
import re
from fpdf import FPDF

console = Console()

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

    console.print(f"\n[bold green][Report][/bold green] Saved to: [dim]{filepath}[/dim]")
    return filepath

def generate_pdf_bytes(topic: str, content: str, sources: list = []) -> bytes:
    """Generate a PDF report and return it as bytes (for Streamlit download)."""
    pdf = FPDF()
    pdf.add_page()

    # Title
    pdf.set_font("Helvetica", "B", 16)
    safe_topic = topic.encode('latin-1', errors='replace').decode('latin-1')
    pdf.multi_cell(0, 10, safe_topic.upper())
    pdf.ln(2)

    # Generated timestamp
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(128, 128, 128)
    pdf.cell(0, 8, f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", ln=True)
    pdf.ln(3)
    pdf.set_text_color(0, 0, 0)

    # Report content
    pdf.set_font("Helvetica", "", 11)
    clean_content = content.replace("**", "").replace("###", "").replace("##", "").replace("#", "")
    clean_content = clean_content.replace("\u2019", "'").replace("\u2018", "'")
    clean_content = clean_content.replace("\u201c", '"').replace("\u201d", '"')
    clean_content = clean_content.replace("\u2022", "-").replace("\u2013", "-").replace("\u2014", "-")
    clean_content = clean_content.replace("\u2192", "->").replace("\u2190", "<-")
    safe_content = clean_content.encode('latin-1', errors='replace').decode('latin-1')
    pdf.multi_cell(0, 7, safe_content)

    # Sources section with hyperlinks
    if sources:
        pdf.ln(5)
        pdf.set_font("Helvetica", "B", 12)
        pdf.cell(0, 10, "Sources", ln=True)
        pdf.set_font("Helvetica", "", 10)
        for i, url in enumerate(sources, 1):
            safe_url = url.encode('latin-1', errors='replace').decode('latin-1')
            pdf.set_text_color(0, 0, 255)
            pdf.cell(8, 8, f"{i}.", ln=False)
            pdf.cell(0, 8, safe_url, ln=True, link=url)
            pdf.set_text_color(0, 0, 0)

    return bytes(pdf.output())