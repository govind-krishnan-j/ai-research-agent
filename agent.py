from groq import Groq
from dotenv import load_dotenv
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
import streamlit as st

import os
import json
import time

from tools import web_search, read_page


# ----------------------------------------------------
# Load environment variables
# ----------------------------------------------------
load_dotenv()

api_key = os.getenv("GROQ_API_KEY") or st.secrets.get("GROQ_API_KEY")

client = Groq(
    api_key=api_key,
)

console = Console()


# ----------------------------------------------------
# Model Configuration
# ----------------------------------------------------
MODEL = "qwen/qwen3-32b"

TEMPERATURE = 0.2

MAX_COMPLETION_TOKENS = 4096

MAX_SEARCHES = 1

MAX_PAGE_READS = 2

MAX_RETRIES = 3


# ----------------------------------------------------
# Tool Definitions
# ----------------------------------------------------
tools_definition = [
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": "Search the web and return a list of relevant URLs.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query"
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
            "description": "Read the textual content of a webpage.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "Webpage URL"
                    }
                },
                "required": ["url"]
            }
        }
    }
]


available_tools = {
    "web_search": web_search,
    "read_page": read_page,
}

def build_messages(topic: str):
    """
    Create the initial conversation sent to the LLM.
    """

    return [
        {
            "role": "system",
            "content": (
                "You are an AI research assistant.\n\n"

                "You have access to ONLY TWO tools:\n"
                "1. web_search\n"
                "2. read_page\n\n"

                "Rules:\n"

                "- Call web_search ONLY ONCE.\n"
                "- Read the TWO most relevant pages.\n"
                "- If one page cannot be read or has poor information, "
                "you may read ONE additional page.\n"
                "- Never search again.\n"
                "- After gathering enough information, immediately write the report.\n"
                "- Never invent information.\n"
                "- Base every claim on the webpages you have read."
            )
        },
        {
            "role": "user",
            "content": (
                f'Research this topic:\n\n"{topic}"\n\n'
                "Generate a structured report with:\n"
                "- Introduction\n"
                "- Background\n"
                "- Key Findings\n"
                "- Current Developments\n"
                "- Challenges\n"
                "- Future Outlook\n"
                "- Conclusion\n\n"
                "Maximum length: 700 words."
            )
        }
    ]

def call_llm(messages, allow_tools=True):
    """
    Send the conversation to the model.

    Automatically retries if the request fails.
    """

    for attempt in range(MAX_RETRIES):

        try:

            params = {
                "model": MODEL,
                "messages": messages,
                "temperature": TEMPERATURE,
                "max_completion_tokens": MAX_COMPLETION_TOKENS,
            }

            if allow_tools:
                params["tools"] = tools_definition
                params["tool_choice"] = "auto"

            return client.chat.completions.create(**params)

        except Exception as e:

            if attempt == MAX_RETRIES - 1:
                raise 

            wait = 2 ** attempt

            console.print(
                f"[yellow]Retrying in {wait} seconds...[/yellow]"
            )

            time.sleep(wait)