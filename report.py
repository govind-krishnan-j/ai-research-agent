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

def generate_pdf_bytes(topic: str, content: str) -> bytes:
    """Generate a PDF report and return it as bytes (for Streamlit download)."""
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 16)
    pdf.multi_cell(0, 10, topic.upper())
    pdf.ln(2)
    pdf.set_font("Helvetica", "", 11)

    # Clean text for PDF (remove markdown symbols that don't render well)
    clean_content = content.replace("**", "").replace("###", "").replace("##", "")

    pdf.multi_cell(0, 7, clean_content)
    return bytes(pdf.output())