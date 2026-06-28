from groq import Groq
from dotenv import load_dotenv
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
import os
import json
from tools import web_search, read_page
import streamlit as st

load_dotenv()
api_key = os.getenv("GROQ_API_KEY") or st.secrets.get("GROQ_API_KEY")
client = Groq(api_key=api_key)
console = Console()

tools_definition = [
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": "Search the web for a query and get a list of relevant URLs.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query"
                    }
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "read_page",
            "description": "Read and extract text content from a webpage URL.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "The URL to read"
                    }
                },
                "required": ["url"]
            }
        }
    }
]

available_tools = {
    "web_search": web_search,
    "read_page": read_page
}


def run_agent(topic: str) -> tuple[str, list[str]]:
    """Run the research agent on a given topic."""

    sources = []
    search_count = 0
    read_count = 0
    messages = [
        {
            "role": "system",
            "content": "You are a research assistant agent. You have access to exactly two tools: 'web_search' and 'read_page'. Follow these steps STRICTLY in order: 1) Call web_search ONCE with the topic as query. 2) Call read_page on EXACTLY 2 URLs from the results. 3) Write the final report immediately after reading 2 pages. Do NOT call web_search more than once. Do NOT read more than 3 pages. After reading pages, you MUST write the report — do not search again."
        },
        {
            "role": "user",
            "content": f'Research this topic and write a full detailed report of at most 700 words: "{topic}". Remember: each key finding must be a full paragraph of at least 80 words, not a short bullet point.'
        }
    ]

    console.print(f"\n[bold blue][Agent][/bold blue] Starting research on: [bold yellow]{topic}[/bold yellow]")

    # --- Agentic loop ---
    while True:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
            transient=True
        ) as progress:
            progress.add_task("[dim]Thinking...[/dim]", total=None)
            try:
                response = client.chat.completions.create(
                    model="openai/gpt-oss-120b",
                    messages=messages,
                    tools=tools_definition,
                    tool_choice="auto",
                    max_tokens=4096,
                )
            except Exception as e:
                console.print(f"[red]⚠ API error: {str(e)[:200]}[/red]")
                return "Sorry, the agent encountered an issue processing this topic. Please try rephrasing it or try again.", sources

        message = response.choices[0].message

        # Check if model wants to call a tool
        if message.tool_calls:
            messages.append({
                "role": "assistant",
                "content": message.content,
                "tool_calls": message.tool_calls
            })

            for tool_call in message.tool_calls:
                tool_name = tool_call.function.name
                tool_args = json.loads(tool_call.function.arguments)

                if tool_name == "web_search":
                    search_count += 1
                    if search_count > 1:
                        console.print(f"[yellow][Agent] Search limit reached — skipping extra search.[/yellow]")
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": "Search limit reached. Please write the report now using information already gathered."
                        })
                        continue
                    console.print(f"\n[bold green][Tool][/bold green] Searching for: [yellow]{tool_args.get('query')}[/yellow]")

                elif tool_name == "read_page":
                    read_count += 1
                    if read_count > 3:
                        console.print(f"[yellow][Agent] Read limit reached — skipping extra page.[/yellow]")
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": "Page read limit reached. Please write the report now using information already gathered."
                        })
                        continue
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

                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": str(tool_result)
                })

        else:
            # No tool calls — final report ready
            console.print("\n[bold blue][Agent][/bold blue] [green]✓ Research complete! Compiling report...[/green]")

            content = message.content
            if not content or content.strip() == "":
                for choice in response.choices:
                    if choice.message.content and choice.message.content.strip():
                        content = choice.message.content
                        break

            if not content or content.strip() == "":
                return "The agent completed research but could not generate a report. Please try again.", sources

            return content, sources