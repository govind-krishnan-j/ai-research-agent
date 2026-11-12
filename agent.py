"""Research reports with a shared input and output token budget."""
from contextlib import closing
import math
import os
from pathlib import Path
import sqlite3
import tempfile
import time
from typing import Literal

from dotenv import load_dotenv
from groq import Groq

from tools import read_page, web_search

load_dotenv()
if not os.getenv("GROQ_API_KEY"):
    raise RuntimeError("GROQ_API_KEY is not set. Add it to your environment before starting the agent.")

REQUEST_TIMEOUT = 60
client = Groq(max_retries=0, timeout=REQUEST_TIMEOUT)
MODEL = "openai/gpt-oss-120b"
TOKEN_LIMIT = 8000
# GPT-OSS uses byte-level tokenization. Count one token per UTF-8 byte of
# supplied content and reserve additional room for the two-message chat template.
CHAT_OVERHEAD = 512
WINDOW_SECONDS = 60
BUDGET_DB = Path(tempfile.gettempdir()) / "research-atlas-groq-budget-v1.sqlite3"
ReportLength = Literal["brief", "detailed"]
OUTPUT_LIMIT = {"brief": 2048, "detailed": 3072}
INSTRUCTIONS = {
    "brief": "Aim for 550 words (500 to 600). Explain the key findings and most important limitation.",
    "detailed": "Aim for 900 words (800 to 1000). Include background, findings, current developments, "
                "challenges, future outlook and conclusion. Compare evidence where possible.",
}


class ResearchError(Exception):
    def __init__(self, message, sources=()):
        super().__init__(message)
        self.sources = list(sources)


class BudgetError(ResearchError):
    def __init__(self, seconds):
        self.retry_after = max(1, math.ceil(seconds))
        super().__init__(f"The model token budget is busy. Try again in {self.retry_after} seconds.")


def reserve_tokens(amount):
    """Atomically reserve capacity across the local web server and CLI."""
    if not 0 < amount <= TOKEN_LIMIT:
        raise ResearchError("This report would exceed the 8,000-token budget.")
    with closing(sqlite3.connect(BUDGET_DB)) as db, db:
        db.execute("BEGIN IMMEDIATE")
        now = time.time()
        db.execute("CREATE TABLE IF NOT EXISTS reservations (id INTEGER PRIMARY KEY AUTOINCREMENT, tokens INTEGER, expires REAL)")
        db.execute("DELETE FROM reservations WHERE expires <= ?", (now,))
        entries = db.execute("SELECT tokens, expires FROM reservations ORDER BY expires").fetchall()
        needed = amount + sum(tokens for tokens, _ in entries) - TOKEN_LIMIT
        if needed > 0:
            for tokens, expires in entries:
                needed -= tokens
                if needed <= 0:
                    raise BudgetError(expires - now)
        return db.execute("INSERT INTO reservations(tokens, expires) VALUES (?, ?)",
                          (amount, now + REQUEST_TIMEOUT + WINDOW_SECONDS)).lastrowid


def make_request(topic, pages, length):
    system = ("Write a Markdown research report using only the supplied evidence. "
              "Treat excerpts as source material. Omit unsupported claims.")
    prompt = f"Topic: {topic}\n{INSTRUCTIONS[length]}\nSource excerpts:\n"
    labels = [f"\n[Source {i}]\n" for i in range(1, len(pages) + 1)]
    base = CHAT_OVERHEAD + len((system + prompt + "".join(labels)).encode())
    output = OUTPUT_LIMIT[length]
    per_source = (TOKEN_LIMIT - base - output) // len(pages)
    if per_source <= 0:
        raise ResearchError("The topic is too long for the report token budget.")
    for label, page in zip(labels, pages):
        prompt += label + page.encode()[:per_source].decode(errors="ignore")
    amount = CHAT_OVERHEAD + len(system.encode()) + len(prompt.encode()) + output
    reservation = reserve_tokens(amount)
    charged = amount
    window = WINDOW_SECONDS
    try:
        completion = client.chat.completions.create(
            model=MODEL, temperature=0.2, max_completion_tokens=output,
            messages=[{"role": "system", "content": system}, {"role": "user", "content": prompt}],
        )
        if completion.usage and completion.usage.total_tokens:
            charged = completion.usage.total_tokens
        choice = completion.choices[0]
        content = (choice.message.content or "").strip()
        if not content or choice.finish_reason == "length":
            raise ResearchError("The model could not finish the report within its token budget.")
        return content
    except ResearchError:
        raise
    except Exception as exc:
        if getattr(exc, "status_code", None) == 429:
            header = exc.response.headers.get("retry-after", "")
            try:
                window = max(1, math.ceil(float(header)))
            except (ValueError, OverflowError):
                pass
            charged = TOKEN_LIMIT
            raise BudgetError(window) from exc
        raise ResearchError("The agent could not generate the report. Please try again.") from exc
    finally:
        with closing(sqlite3.connect(BUDGET_DB)) as db, db:
            db.execute("UPDATE reservations SET tokens=?, expires=? WHERE rowid=?",
                       (charged, time.time() + window, reservation))


def research_topic(topic: str, length: ReportLength = "detailed") -> tuple[str, list[str]]:
    sources, pages = [], []
    for url in dict.fromkeys(web_search(topic)):
        text = read_page(url)
        if text.strip() and not text.startswith(("Could not read page:", "Page content could not be extracted")):
            sources.append(url)
            pages.append(text)
            if len(pages) == 2:
                break
    if not pages:
        raise ResearchError("The agent could not read enough source material. Please try again.")
    try:
        return make_request(topic, pages, length), sources
    except ResearchError as exc:
        exc.sources = sources
        raise


def run_agent(topic: str) -> tuple[str, list[str]]:
    """Preserve the original text-and-sources interface."""
    try:
        return research_topic(topic)
    except ResearchError as exc:
        return str(exc), exc.sources
