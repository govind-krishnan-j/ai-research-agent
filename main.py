from agent import run_agent
from report import save_report
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.rule import Rule

console = Console()

def main():
    console.print(Panel.fit(
        "[bold blue]AI Research Assistant Agent[/bold blue]\n[dim]Powered by Groq (Llama) + DuckDuckGo[/dim]",
        border_style="blue"
    ))

    topic = Prompt.ask("\n[bold yellow]Enter a research topic[/bold yellow]")

    if not topic.strip():
        console.print("[red]No topic entered. Exiting.[/red]")
        return

    # run_agent now returns (report, sources)
    report_content, sources = run_agent(topic)

    # Append sources to report
    if sources:
        sources_text = "\n\n---\n**Sources:**\n"
        for i, url in enumerate(sources, 1):
            sources_text += f"{i}. {url}\n"
        full_report = report_content + sources_text
    else:
        full_report = report_content

    filepath = save_report(topic, full_report)

    console.print(Panel(
        full_report,
        title="[bold green]Final Report[/bold green]",
        border_style="green"
    ))

    # Print sources separately in a styled panel
    if sources:
        console.print(Rule("[dim]Sources[/dim]"))
        for i, url in enumerate(sources, 1):
            console.print(f"  [dim]{i}.[/dim] [blue]{url}[/blue]")

    console.print(f"\n[bold green]✓ Report saved to:[/bold green] [dim]{filepath}[/dim]")


if __name__ == "__main__":
    main()