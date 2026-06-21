# 🔬 AI Research Assistant Agent

An autonomous AI agent that researches any topic by searching the web, reading sources, and compiling a structured report — available as both a CLI tool and a deployed web app.

Built from scratch using **agentic function calling**, powered by **Groq (Llama 4)** for fast inference and **DuckDuckGo** for live web search.

🔗 **Live Demo:** [ai-research-agent.streamlit.app](https://ai-research-agent-6ua9dxxbwldju4mm8hhobg.streamlit.app/) 
📦 **Repository:** [github.com/govind-krishnan-j/ai-research-agent](https://github.com/govind-krishnan-j/ai-research-agent)

---

## 📸 Preview

```
🔬 AI Research Assistant
Enter any topic — the agent will autonomously research and compile a report.

Enter a research topic: machine learning trends 2026
                                                    [🔍 Research]

⚙️ Agent Progress
✅ Web search complete
✅ Pages read
✅ Synthesis complete
✅ Report compiled

📄 Research Report
📊 612 words · ⏱️ ~3 min read · 🔗 3 sources

## Summary
[Full structured report generated here]

## Key Findings
1. ...
2. ...

## Conclusion
[...]

🔗 Sources
1. https://...
2. https://...

[⬇️ Download .txt]  [⬇️ Download PDF]
```

---

## 🧠 How It Works

This isn't a simple API wrapper — it's a genuine **agentic loop** where the LLM autonomously decides which actions to take, in what order, and when it has gathered enough information to stop.

```
User enters a topic
       │
       ▼
Llama (via Groq) reasons: "I need to search the web first"
       │
       ▼
Agent calls web_search() → returns list of URLs
       │
       ▼
Llama reasons: "Now I should read these pages"
       │
       ▼
Agent calls read_page() on each URL → returns clean text
       │
       ▼
Llama synthesizes all gathered information
       │
       ▼
Structured report (Summary, Key Findings, Conclusion)
       │
       ▼
Sources cited + report saved + downloadable (.txt / PDF)
```

The model decides **on its own**, turn by turn, whether to keep gathering information or whether it's ready to write the final report — this decision-making loop is what makes it an "agent" rather than a single prompt-response call.

---

##  Features

- **Autonomous web research** — no manual searching required, the agent decides what and how much to search
- **Real agentic tool use** — Llama dynamically chooses between `web_search` and `read_page` via function calling
- **Structured, detailed reports** — Summary, 6+ Key Findings, and Conclusion, minimum 600 words
- **Source citation** — every report lists the exact URLs used, for credibility and traceability
- **Dual interface** — a Rich-styled CLI for developers, and a polished Streamlit web app for everyone else
- **Multiple export formats** — download reports as `.txt` or formatted `.PDF`
- **Fast inference** — powered by Groq's LPU hardware, noticeably faster than typical LLM APIs
- **Resilient error handling** — gracefully handles rate limits, JavaScript-rendered pages, and malformed model responses without crashing

---

## Project Structure

```
ai-research-agent/
│
├── main.py              # CLI entry point — Rich-styled terminal interface
├── app.py                # Streamlit web app — browser-based interface
├── agent.py              # Core agentic loop + Llama function calling logic
├── tools.py               # Tool implementations: web_search() and read_page()
├── report.py             # Report saving (.txt) and PDF generation
│
├── requirements.txt
├── .env                    # API keys (gitignored, not committed)
├── .gitignore
├── .streamlit/
│   └── config.toml      # Custom dark theme configuration
└── reports/               # Locally generated reports (auto-created, gitignored)
```

---

## Tech Stack

| Layer | Technology | Purpose |
|---|---|---|
| LLM inference | **Groq API** (`meta-llama/llama-4-scout-17b-16e-instruct`) | Fast function-calling capable model |
| Web search | **ddgs** (DuckDuckGo Search) | Free, no-API-key web search |
| Web scraping | **requests** + **BeautifulSoup4** | Fetching and cleaning page content |
| Web UI | **Streamlit** | Browser-based interface, deployed on Streamlit Cloud |
| CLI styling | **Rich** | Colored terminal output, spinners, styled panels |
| PDF generation | **fpdf2** | Converting reports into downloadable PDFs |
| Config | **python-dotenv** | Local environment variable management |

---

## Setup & Installation

### 1. Clone the repository
```bash
git clone https://github.com/govind-krishnan-j/ai-research-agent.git
cd ai-research-agent
```

### 2. Create a virtual environment
```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS/Linux
source .venv/bin/activate
```

### 3. Install dependencies
```bash
python -m pip install -r requirements.txt
```

### 4. Add your Groq API key

Create a `.env` file in the project root:
```env
GROQ_API_KEY=your_groq_api_key_here
```

Get a free API key at [console.groq.com](https://console.groq.com) — Groq's free tier is generous (30K tokens/minute) and works reliably worldwide.

### 5. Run the agent

**CLI version:**
```bash
python main.py
```

**Web version:**
```bash
streamlit run app.py
```

---

## Deployment

This project is deployed on **Streamlit Community Cloud** (free tier).

To deploy your own copy:
1. Push your code to a public GitHub repository
2. Go to [share.streamlit.io](https://share.streamlit.io) and connect your GitHub account
3. Create a new app pointing to `app.py` on your `main` branch
4. Under **Advanced settings → Secrets**, add:
   ```toml
   GROQ_API_KEY = "your_actual_groq_api_key_here"
   ```
5. Click Deploy

> **Note:** `agent.py` reads the API key from `os.getenv()` locally and falls back to `st.secrets.get()` on Streamlit Cloud, so the same codebase works in both environments without modification.

---

## Key Engineering Concepts Demonstrated

- **Agentic loops** — multi-turn autonomous reasoning where the model decides its own next action, rather than a single prompt-response exchange
- **Function calling / tool use** — structured JSON tool definitions that let an LLM invoke real Python functions and reason over their results
- **Prompt engineering for reliability** — iteratively refined system prompts to reduce tool-call hallucination and enforce consistent output structure
- **Graceful degradation** — the agent continues working even when individual pages fail to load, return JavaScript-rendered empty content, or when the API rate-limits
- **Dual-interface architecture** — one shared backend (`agent.py`, `tools.py`, `report.py`) powering two completely different frontends (CLI and web)
- **API migration under real constraints** — originally built on Gemini, migrated to Groq after hitting India-specific free-tier rate limits, without changing the agent's core logic
- **Environment-aware configuration** — same code runs locally (`.env`) and in production (Streamlit Secrets) without modification

---

## Engineering Challenges & Solutions

Building this surfaced a number of real-world issues, each solved along the way:

| Challenge | Solution |
|---|---|
| `googlesearch-python` got blocked by Google | Switched to `ddgs` (DuckDuckGo Search) |
| Gemini free tier in India had extremely low quotas (0–20 req/day) | Migrated to Groq API (30K tokens/minute, no regional restrictions) |
| Llama occasionally hallucinated tool names or skipped function calls | Strengthened system prompts to explicitly name available tools and mandate their use |
| JavaScript-rendered pages returned empty content | Added a content-length check with a graceful fallback message instead of crashing |
| Windows-invalid characters (`?`, `:`, etc.) in topic names broke file saving | Added regex sanitization before writing filenames |
| Streamlit Cloud's ephemeral filesystem doesn't persist saved reports | Relied on in-browser download buttons (`.txt` / PDF) instead of server-side storage |
| Local `.env` doesn't exist in the deployed environment | Implemented a fallback: `os.getenv()` locally, `st.secrets.get()` on Streamlit Cloud |

---

## Known Limitations

- Cannot read JavaScript-heavy pages (uses static HTML parsing, not a headless browser)
- Search result quality depends on DuckDuckGo's index for the given query
- Free-tier API rate limits apply under heavy usage
- Reports are not persisted server-side on the deployed version (by design — see deployment notes)

---

## Future Improvements

- [ ] Multi-query search — search several angles of a topic for deeper, more comprehensive reports
- [ ] Conversation memory — support follow-up questions on a previously generated report
- [ ] Headless browser fallback (Playwright) for JavaScript-rendered pages
- [ ] Full-stack version (FastAPI + React) as a learning project post-placements

---

## Author

**Govind Krishnan J**
B.Tech Electronics & Communication Engineering, SCMS School of Engineering and Technology

- 🔗 LinkedIn: [linkedin.com/in/govind-krishnan-j-3264b6296](https://linkedin.com/in/govind-krishnan-j-3264b6296)
- 💻 GitHub: [github.com/govind-krishnan-j](https://github.com/govind-krishnan-j)

---

## License

This project is open source and available under the [MIT License](LICENSE).
