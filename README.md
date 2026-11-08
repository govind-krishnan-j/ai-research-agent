# Research Atlas

Research Atlas is a dark-themed research website powered by a Python AI agent. Enter a topic, and the agent searches the web, reads selected pages, and writes a structured report with source links. Reports can be downloaded as text or PDF.

The project also includes a command-line interface.

## How it works

1. The React website sends a topic to the FastAPI backend.
2. `agent.py` uses Groq function calling to decide when to search, read, and write.
3. `tools.py` searches with DuckDuckGo and extracts text from web pages.
4. The website displays the report and sources. `report.py` creates the PDF export.

The current agent uses `openai/gpt-oss-120b` through Groq. It is limited to one search, two page reads, and six agent steps per request.

## Project structure

```text
api.py             FastAPI backend and built-site serving
agent.py           Groq agent loop
tools.py           Web search and page reading
report.py          Text report saving and PDF generation
main.py            CLI entry point
web/               React, TypeScript, Vite, and custom CSS frontend
requirements.txt   Python dependencies
reports/           Locally generated CLI reports (ignored by Git)
```

## Local setup

Create a Python virtual environment and install the backend dependencies:

```bash
python -m venv .venv
python -m pip install -r requirements.txt
```

Install the frontend dependencies:

```bash
cd web
npm install
```

Set `GROQ_API_KEY` in the backend environment. For local development, you can put it in a `.env` file in the project root. `.env` is ignored by Git. Never put the key in the frontend source or a variable prefixed with `VITE_`.

### Development mode

Run the API from the project root:

```bash
python -m uvicorn api:app --reload
```

In a second terminal, run the frontend from `web/`:

```bash
cd web
npm run dev
```

Open the URL printed by Vite, normally `http://127.0.0.1:5173/`. Vite forwards `/api` calls to FastAPI at `http://127.0.0.1:8000`.

### Built website

Build the frontend:

```bash
cd web
npm run build
```

Then run `python -m uvicorn api:app --reload` from the project root. FastAPI serves `web/dist/` and the API together at `http://127.0.0.1:8000/`. Rebuild after frontend changes.

### CLI

From the project root, run `python main.py`. CLI reports are saved under `reports/`.

## Current limitations

- Some JavaScript-rendered pages cannot be extracted by the static page reader.
- Search quality depends on DuckDuckGo results.
- The website's recent topics are stored only in the current browser.
- The website shows an in-progress state while the agent works; it does not yet stream individual agent steps.
- Groq rate limits and external page failures can interrupt research.

## License

MIT License. See [LICENSE](LICENSE).

Created by Govind Krishnan J.
