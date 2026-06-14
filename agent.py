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


def run_agent(topic: str) -> tuple[str, list[str]]:
    """Run the research agent on a given topic.
    Returns a tuple of (report_text, sources_list)
    """

    model = genai.GenerativeModel(
        model_name="gemini-2.5-flash-lite",
        tools=tools_definition
    )

    chat = model.start_chat()

    # Track sources as agent reads pages
    sources = []

    prompt = f"""You are a research assistant agent. Your job is to research the topic: "{topic}"

You MUST follow these steps in order:
1. Call web_search tool to search for the topic
2. From the results, pick the 3 most relevant URLs and call read_page on EACH of them one by one
3. If a page returns empty or useless content, skip it and try the next URL
4. After reading pages, compile a structured research report with:
   - Summary
   - Key findings (at least 3 points)
   - Conclusion

IMPORTANT: You MUST attempt to read at least 3 pages. Do not write the report until you have read multiple pages.
Start now."""

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
        parts = response.candidates[0].content.parts

        # Find if any part is a function call
        function_call_part = None
        for part in parts:
            if hasattr(part, "function_call") and part.function_call.name:
                function_call_part = part
                break

        if function_call_part:
            tool_name = function_call_part.function_call.name
            tool_args = dict(function_call_part.function_call.args)

            if tool_name == "web_search":
                console.print(f"\n[bold green][Tool][/bold green] Searching for: [yellow]{tool_args.get('query')}[/yellow]")
            elif tool_name == "read_page":
                url = tool_args.get('url')
                console.print(f"[bold green][Tool][/bold green] Reading: [dim]{url}[/dim]")
                if url and url not in sources:
                    sources.append(url)

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
            # No function call — extract text from parts
            console.print("\n[bold blue][Agent][/bold blue] [green]✓ Research complete! Compiling report...[/green]")
            for part in parts:
                if hasattr(part, "text") and part.text:
                    return part.text, sources
            return "Agent could not complete the report. Please try again.", sources