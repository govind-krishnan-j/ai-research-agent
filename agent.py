import json
import os
import time

import streamlit as st
from dotenv import load_dotenv
from groq import Groq

from tools import read_page, web_search

# ----------------------------------------------------
# Load environment variables
# ----------------------------------------------------

load_dotenv()

API_KEY = os.getenv("GROQ_API_KEY")

if not API_KEY:
    API_KEY = st.secrets["GROQ_API_KEY"]

client = Groq(api_key=API_KEY)

# ----------------------------------------------------
# Configuration
# ----------------------------------------------------

MODEL = "openai/gpt-oss-120b"

TEMPERATURE = 0.2

MAX_COMPLETION_TOKENS = 4096

MAX_SEARCHES = 1

MAX_PAGE_READS = 2

MAX_RETRIES = 3

MAX_AGENT_STEPS = 6

# ----------------------------------------------------
# System Prompt
# ----------------------------------------------------

SYSTEM_PROMPT = """
You are an AI Research Assistant.

You have access to exactly TWO tools:

1. web_search
2. read_page

Rules:

- Call web_search exactly once.
- Read the two most relevant webpages.
- If one webpage cannot be read, you may read one additional page.
- Never search twice.
- Never invent facts.
- Base every claim on the webpages you have read.
- After gathering enough information, immediately generate the report.
"""

# ----------------------------------------------------
# User Prompt Template
# ----------------------------------------------------


def user_prompt(topic: str) -> str:

    return f"""
Research the following topic:

{topic}

Write a report containing:

- Introduction
- Background
- Key Findings
- Current Developments
- Challenges
- Future Outlook
- Conclusion

Maximum length:
700 words.
"""

# ----------------------------------------------------
# Tool Definitions
# ----------------------------------------------------

tools_definition = [
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": "Search the web and return relevant URLs.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string"
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
            "description": "Read a webpage and return its textual content.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string"
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

# ----------------------------------------------------
# Build Initial Conversation
# ----------------------------------------------------


def build_messages(topic: str):

    return [
        {
            "role": "system",
            "content": SYSTEM_PROMPT,
        },
        {
            "role": "user",
            "content": user_prompt(topic),
        },
    ]


# ----------------------------------------------------
# Call the LLM
# ----------------------------------------------------


def call_llm(messages, allow_tools=True):
    """
    Send a request to Groq.

    Automatically retries if the API temporarily fails.
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

        except Exception:

            if attempt == MAX_RETRIES - 1:
                raise

            wait = 2 ** attempt

            time.sleep(wait)


# ----------------------------------------------------
# Execute Tool Call
# ----------------------------------------------------

def execute_tool(tool_call, state):
    """
    Execute a tool requested by the LLM.
    """

    tool_name = tool_call.function.name
    tool_args = json.loads(tool_call.function.arguments)

    # ------------------------------------------------
    # Unknown tool
    # ------------------------------------------------

    if tool_name not in available_tools:

        return {
            "content": f"Unknown tool: {tool_name}"
        }

    # ------------------------------------------------
    # web_search
    # ------------------------------------------------

    if tool_name == "web_search":

        if state["search_count"] >= MAX_SEARCHES:

            return {
                "content": "Search limit reached."
            }

        state["search_count"] += 1

        result = available_tools[tool_name](**tool_args)

        return {
            "content": str(result)
        }

    # ------------------------------------------------
    # read_page
    # ------------------------------------------------

    if tool_name == "read_page":

        if state["read_count"] >= MAX_PAGE_READS:

            return {
                "content": "Page read limit reached."
            }

        state["read_count"] += 1

        url = tool_args["url"]

        if url not in state["sources"]:
            state["sources"].append(url)

        result = available_tools[tool_name](**tool_args)

        return {
            "content": result
        }

    return {
        "content": "Tool execution failed."
    }


# ----------------------------------------------------
# Main Agent Loop
# ----------------------------------------------------


def run_agent(topic: str) -> tuple[str, list[str]]:
    """
    Run the research agent on a given topic.
    Returns (report_text, sources_list).
    """

    messages = build_messages(topic)

    state = {
        "search_count": 0,
        "read_count": 0,
        "sources": [],
    }

    for step in range(MAX_AGENT_STEPS):

        # Force finish once limits are hit
        force_finish = (
            state["search_count"] >= MAX_SEARCHES
            and state["read_count"] >= MAX_PAGE_READS
        )

        if force_finish:
            messages.append({
                "role": "user",
                "content": "You have gathered enough information. Write the final report now."
            })

        try:
            response = call_llm(messages, allow_tools=not force_finish)
        except Exception as e:
            return f"Sorry, the agent encountered an issue: {str(e)[:200]}", state["sources"]

        message = response.choices[0].message

        # Model wants to call a tool (and we still allow it)
        if message.tool_calls and not force_finish:

            messages.append({
                "role": "assistant",
                "content": message.content,
                "tool_calls": message.tool_calls,
            })

            for tool_call in message.tool_calls:
                tool_result = execute_tool(tool_call, state)

                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": tool_result["content"],
                })

            continue

        # No tool calls (or forced) — treat as final report
        content = message.content

        if not content or not content.strip():
            # One recovery attempt with tools re-enabled
            try:
                recovery = call_llm(
                    messages + [{
                        "role": "user",
                        "content": "Stop using tools. Write the complete report now based on what you already know."
                    }],
                    allow_tools=True
                )
                content = recovery.choices[0].message.content
            except Exception:
                content = None

        if not content or not content.strip():
            return "The agent completed research but could not generate a report. Please try again.", state["sources"]

        return content, state["sources"]

    return "The agent could not complete the report within the step limit. Please try again.", state["sources"]