import google.generativeai as genai
from dotenv import load_dotenv
import os
import time
from tools import web_search, read_page

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# --- Define tools for Gemini (function calling) ---
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

# --- Map tool names to actual Python functions ---
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
                print(f"\n[Agent] Rate limit hit. Waiting {wait}s before retry {i+1}/{retries}...")
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

    print(f"\n[Agent] Starting research on: {topic}")
    print("[Agent] Thinking...\n")

    response = send_with_retry(chat, prompt)

    # --- Agentic loop ---
    while True:
        try:
            function_call = response.candidates[0].content.parts[0].function_call
            if function_call.name:
                tool_name = function_call.name
                tool_args = dict(function_call.args)

                print(f"[Agent] Calling tool: {tool_name} with args: {tool_args}")

                tool_result = available_tools[tool_name](**tool_args)

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
                print("\n[Agent] Research complete. Compiling report...")
                return response.text

        except (AttributeError, IndexError):
            # No function call found — Gemini is done
            print("\n[Agent] Research complete. Compiling report...")
            try:
                return response.text
            except ValueError:
                # Response was cut short — extract text manually
                for part in response.candidates[0].content.parts:
                    if hasattr(part, "text") and part.text:
                        return part.text
                return "Agent could not complete the report. Please try again."