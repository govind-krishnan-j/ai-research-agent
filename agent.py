import google.generativeai as genai
from dotenv import load_dotenv
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
import os
import time
from tools import web_search, read_page

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

console = Console()

tools_definition = [
    {
        "function_declarations": [
            {
                "name": "web_search",
                "description": "Search Google for a query and get a list of relevant URLs.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "The search query to look up on Google"
                        }
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "read_page",
                "description": "Read and extract text content from a webpage URL.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "url": {
                            "type": "string",
                            "description": "The URL of the webpage to read"
                        }
                    },
                    "required": ["url"]
                }
            }
        ]
    }
]

available_tools = {
    "web_search": web_search,
    "read_page": read_page
}


def send_with_retry(chat, message, retries=3, wait=60):
    """Send a message to Gemini with automatic retry on rate limit."""
    for i in range(retries):
        try:
            return chat.send_message(message)
        except Exception as e:
            if "RESOURCE_EXHAUSTED" in str(e):
                console.print(f"[yellow]⚠ Rate limit hit. Waiting {wait}s before retry {i+1}/{retries}...[/yellow]")
                time.sleep(wait)
            else:
                raise e
    raise Exception("[Agent] Max retries exceeded. Please wait a few minutes and try again.")


def run_agent(topic: str) -> str:
    """Run the research agent on a given topic."""

    model = genai.GenerativeModel(
        model_name="gemini-2.5-flash-lite",
        tools=tools_definition
    )

    chat = model.start_chat()

    prompt = f"""You are a research assistant agent. Your job is to research the topic: "{topic}"

Follow these steps:
1. Search the web for the topic using the web_search tool
2. Pick the 2 most relevant URLs from the results
3. Read each URL using the read_page tool
4. Compile everything into a structured research report with:
   - Summary
   - Key findings (at least 3 points)
   - Conclusion

Start researching now."""

    console.print(f"\n[bold blue][Agent][/bold blue] Starting research on: [bold yellow]{topic}[/bold yellow]")

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
        transient=True
    ) as progress:
        progress.add_task("[dim]Thinking...[/dim]", total=None)
        response = send_with_retry(chat, prompt)

    # --- Agentic loop ---
    while True:
        try:
            function_call = response.candidates[0].content.parts[0].function_call
            if function_call.name:
                tool_name = function_call.name
                tool_args = dict(function_call.args)

                if tool_name == "web_search":
                    console.print(f"\n[bold green][Tool][/bold green] Searching for: [yellow]{tool_args.get('query')}[/yellow]")
                elif tool_name == "read_page":
                    console.print(f"[bold green][Tool][/bold green] Reading: [dim]{tool_args.get('url')}[/dim]")

                with Progress(
                    SpinnerColumn(),
                    TextColumn("[progress.description]{task.description}"),
                    console=console,
                    transient=True
                ) as progress:
                    progress.add_task(f"[dim]Running {tool_name}...[/dim]", total=None)
                    tool_result = available_tools[tool_name](**tool_args)

                if tool_name == "web_search":
                    console.print(f"[bold green][Tool][/bold green] Found [bold]{len(tool_result)}[/bold] URLs ✓")

                response = send_with_retry(
                    chat,
                    {
                        "role": "tool",
                        "parts": [{
                            "function_response": {
                                "name": tool_name,
                                "response": {"result": str(tool_result)}
                            }
                        }]
                    }
                )
            else:
                console.print("\n[bold blue][Agent][/bold blue] [green]✓ Research complete! Compiling report...[/green]")
                return response.text

        except (AttributeError, IndexError):
            console.print("\n[bold blue][Agent][/bold blue] [green]✓ Research complete! Compiling report...[/green]")
            try:
                return response.text
            except ValueError:
                for part in response.candidates[0].content.parts:
                    if hasattr(part, "text") and part.text:
                        return part.text
                return "Agent could not complete the report. Please try again."