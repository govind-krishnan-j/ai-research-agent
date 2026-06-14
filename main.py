from agent import run_agent
from report import save_report
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt

console = Console()

def main():
    console.print(Panel.fit(
        "[bold blue]AI Research Assistant Agent[/bold blue]\n[dim]Powered by Gemini + DuckDuckGo[/dim]",
        border_style="blue"
    ))

    topic = Prompt.ask("\n[bold yellow]Enter a research topic[/bold yellow]")

    if not topic.strip():
        console.print("[red]No topic entered. Exiting.[/red]")
        return

    report_content = run_agent(topic)
    filepath = save_report(topic, report_content)

    console.print(Panel(
        report_content,
        title="[bold green]Final Report[/bold green]",
        border_style="green"
    ))

    console.print(f"\n[bold green]✓ Report saved to:[/bold green] [dim]{filepath}[/dim]")


if __name__ == "__main__":
    main()