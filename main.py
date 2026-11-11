from agent import ResearchError, research_topic
from report import save_report


def main():
    print("=" * 60)
    print("       AI Research Assistant Agent")
    print("       Powered by Groq + DuckDuckGo")
    print("=" * 60)

    topic = input("\nEnter a research topic: ").strip()

    if not topic:
        print("No topic entered. Exiting.")
        return

    try:
        report_content, sources = research_topic(topic)
    except ResearchError as exc:
        print(str(exc))
        return

    # Append sources to report
    if sources:
        sources_text = "\n\n---\nSources:\n"
        for i, url in enumerate(sources, 1):
            sources_text += f"{i}. {url}\n"
        full_report = report_content + sources_text
    else:
        full_report = report_content

    filepath = save_report(topic, full_report)

    print("\n" + "=" * 60)
    print("FINAL REPORT")
    print("=" * 60)
    print(full_report)

    if sources:
        print("\n" + "-" * 20 + " Sources " + "-" * 20)
        for i, url in enumerate(sources, 1):
            print(f"  {i}. {url}")

    print(f"\n✓ Report saved to: {filepath}")


if __name__ == "__main__":
    main()