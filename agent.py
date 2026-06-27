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
console=Console()

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
    messages = [

    {
    "role": "system",
    "content": "You are a research assistant agent. You have access to two tools: web_search and read_page. To research any topic, you MUST actually call these tools using proper function calling — never describe what you would do, always DO it by calling the tool. Steps: 1) Call web_search with the topic as the query. 2) Call read_page on at least 2 of the returned URLs. 3) After reading the pages, write a DETAILED structured report. The report MUST contain: a Summary section (at least 100 words), a Key Findings section with EXACTLY 6 points (each point MUST be at least 80 words long with specific details, examples and data), and a Conclusion section (at least 100 words). The total report MUST be not more than 700 words. Do not write short bullet points — write full detailed paragraphs for each finding."
    },

    {
    "role": "user",
    "content": f'Research this topic and write a full detailed report of atmost 700 words: "{topic}". Remember: each key finding must be a full paragraph of at least 80 words, not a short bullet point.'
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
                    model="qwen/qwen3.6-27b",
                    messages=messages,
                    tools=tools_definition,
                    tool_choice="auto",
                    max_tokens=8192,
                    reasoning_format="hidden"
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

                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": str(tool_result)
                })

        else:
            # No tool calls — final report ready
            console.print("\n[bold blue][Agent][/bold blue] [green]✓ Research complete! Compiling report...[/green]")
            
            # Handle qwen thinking models that return empty content
            content = message.content
            if not content or content.strip() == "":
                # Try extracting from choices directly
                for choice in response.choices:
                    if choice.message.content and choice.message.content.strip():
                        content = choice.message.content
                        break
            
            if not content or content.strip() == "":
                return "The agent completed research but could not generate a report. Please try again.", sources
                
            return content, sources