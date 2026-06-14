from agent import run_agent
from report import save_report


def main():
    print("=" * 60)
    print("       AI RESEARCH ASSISTANT AGENT")
    print("=" * 60)

    # Get topic from user
    topic = input("\nEnter a research topic: ").strip()

    if not topic:
        print("No topic entered. Exiting.")
        return

    # Run the agent
    report_content = run_agent(topic)

    # Save the report
    filepath = save_report(topic, report_content)

    # Print the report to terminal as well
    print("\n" + "=" * 60)
    print("FINAL REPORT")
    print("=" * 60)
    print(report_content)
    print(f"\n✅ Report saved to: {filepath}")


if __name__ == "__main__":
    main()