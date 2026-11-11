from inspect import signature
import json
import os
import time

from dotenv import load_dotenv
from groq import Groq

from tools import read_page, web_search

# ----------------------------------------------------
# Load environment variables
# ----------------------------------------------------

load_dotenv()

API_KEY = os.getenv("GROQ_API_KEY")

if not API_KEY:
    raise RuntimeError("GROQ_API_KEY is not set. Add it to your environment before starting the agent.")

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

MIN_REPORT_WORDS = 800
MAX_REPORT_WORDS = 900
MAX_LENGTH_REVISIONS = 2

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

Write {MIN_REPORT_WORDS} to {MAX_REPORT_WORDS} words across these sections, aiming for 850.
Use the space to explain evidence, compare findings, and discuss limitations.
Avoid repetition and unsupported details. Sources are listed separately by the app.
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

        except Exception as exc:
            # Invalid tool calls will not be fixed by retrying the same request.
            if "tool_use_failed" in str(exc) or "tool choice is none" in str(exc).lower():
                raise

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

    # ------------------------------------------------
    # Unknown tool
    # ------------------------------------------------

    if tool_name not in available_tools:

        return {
            "content": f"Unknown tool: {tool_name}"
        }

    argument = "query" if tool_name == "web_search" else "url"
    try:
        tool_args = json.loads(tool_call.function.arguments)
    except (ValueError, TypeError):
        tool_args = None
    if (not isinstance(tool_args, dict)
            or not isinstance(tool_args.get(argument), str)
            or not tool_args[argument].strip()):
        return {"content": f"Invalid arguments for {tool_name}. Supply a nonempty {argument} string."}

    tool = available_tools[tool_name]
    try:
        signature(tool).bind(**tool_args)
    except TypeError:
        return {"content": f"Invalid arguments for {tool_name}. Check the tool definition."}

    # ------------------------------------------------
    # web_search
    # ------------------------------------------------

    if tool_name == "web_search":

        if state["search_count"] >= MAX_SEARCHES:

            return {
                "content": "Search limit reached."
            }

        state["search_count"] += 1

        result = tool(**tool_args)

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

        result = tool(**tool_args)

        if not result.startswith(("Could not read page:", "Page content could not be extracted")):
            if url not in state["sources"]:
                state["sources"].append(url)
            state["pages"].append((url, result))

        return {
            "content": result
        }

    return {
        "content": "Tool execution failed."
    }


# ----------------------------------------------------
# Final report from a clean, text-only conversation
# ----------------------------------------------------


class ResearchError(Exception):
    """An expected terminal failure with the evidence collected so far."""

    def __init__(self, message: str, sources: list[str]):
        super().__init__(message)
        self.sources = sources


def finish_report(topic: str, state, draft: str = "") -> tuple[str, list[str]]:
    # Match the website's whitespace-based count for the report body.
    word_count = len(draft.split())
    if MIN_REPORT_WORDS <= word_count <= MAX_REPORT_WORDS:
        return draft, state["sources"]

    if not state["pages"]:
        raise ResearchError("The agent could not read enough source material. Please try again.", state["sources"])

    source_text = "\n\n".join(
        f"Source {index}: {url}\n{text}"
        for index, (url, text) in enumerate(state["pages"], 1)
    )
    messages = [
        {
            "role": "system",
            "content": "Write a research report using only the supplied source text. "
                       "Return Markdown prose only. Do not request actions or tools. "
                       "If the sources do not support a claim, omit it.",
        },
        {
            "role": "user",
            "content": f"{user_prompt(topic)}\n\nSource material:\n{source_text}",
        },
    ]
    # A supplied draft already used its first generation attempt.
    attempts = MAX_LENGTH_REVISIONS if draft else MAX_LENGTH_REVISIONS + 1
    for _ in range(attempts):
        if draft:
            messages = messages[:2] + [
                {"role": "assistant", "content": draft},
                {"role": "user", "content": f"This draft has {word_count} words. Rewrite the complete "
                 f"report in {MIN_REPORT_WORDS} to {MAX_REPORT_WORDS} words using the supplied sources."},
            ]
        try:
            response = call_llm(messages, allow_tools=False)
            draft = response.choices[0].message.content or ""
        except Exception as exc:
            raise ResearchError("The agent could not generate the report. Please try again.", state["sources"]) from exc
        word_count = len(draft.split())
        if MIN_REPORT_WORDS <= word_count <= MAX_REPORT_WORDS:
            return draft, state["sources"]

    raise ResearchError(
        f"The agent could not produce a {MIN_REPORT_WORDS}–{MAX_REPORT_WORDS} word report. Please try again.",
        state["sources"],
    )


# ----------------------------------------------------
# Main Agent Loop
# ----------------------------------------------------


def research_topic(topic: str) -> tuple[str, list[str]]:
    """
    Run the research agent on a given topic.
    Returns (report_text, sources_list).
    """

    messages = build_messages(topic)

    state = {
        "search_count": 0,
        "read_count": 0,
        "sources": [],
        "pages": [],
    }

    for step in range(MAX_AGENT_STEPS):

        # Force finish once limits are hit
        force_finish = (
            state["search_count"] >= MAX_SEARCHES
            and state["read_count"] >= MAX_PAGE_READS
        )

        if force_finish:
            return finish_report(topic, state)

        try:
            response = call_llm(messages)
        except Exception:
            if state["pages"]:
                return finish_report(topic, state)
            raise ResearchError("The agent could not complete research. Please try again.", state["sources"])

        message = response.choices[0].message

        # Model wants to call a tool (and we still allow it)
        if message.tool_calls:

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

        return finish_report(topic, state, draft=message.content or "")

    return finish_report(topic, state)


def run_agent(topic: str) -> tuple[str, list[str]]:
    """Keep the original text-and-sources interface for existing callers."""
    try:
        return research_topic(topic)
    except ResearchError as exc:
        return str(exc), exc.sources
