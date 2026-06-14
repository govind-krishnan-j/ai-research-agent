import os
from datetime import datetime


def save_report(topic: str, content: str) -> str:
    """Save the final research report to a text file."""

    # Create reports folder if it doesn't exist
    os.makedirs("reports", exist_ok=True)

    # Create a clean filename from the topic
    filename = topic.strip().lower().replace(" ", "_")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filepath = f"reports/{filename}_{timestamp}.txt"

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(f"RESEARCH REPORT: {topic.upper()}\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("=" * 60 + "\n\n")
        f.write(content)

    print(f"\n[Report] Saved to: {filepath}")
    return filepath