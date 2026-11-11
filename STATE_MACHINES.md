# Research Atlas workflows

This inventory covers application-owned transitions in the website, Python API, research agent, CLI and report renderer. Each row describes what triggers the next state.

| Workflow | States and transitions |
| --- | --- |
| Topic entry | Typing updates the draft. A launchpad question fills and focuses the draft. Form submission, a suggested topic or a recent topic starts research. The form requires two trimmed characters. |
| Research session | Idle → running → ready or failed. Failure allows retry. A new topic starts another run. New research clears the completed report and draft. A pending request guards every research entry point. |
| PDF download | Each ready report owns its export. Idle or failed → preparing → idle on download, failed on error. Starting over or replacing the report aborts its pending browser download. |
| Text download | Ready report → create a temporary file URL → trigger download → release the URL. |
| Navigation | Home ↔ How it works. Changing views retains the research session. Starting a research request selects Home. |
| Workspace | Desktop expanded ↔ collapsed, persisted when storage is available. Mobile drawer closed ↔ open via the menu, close button or backdrop. Navigation and starting research close the drawer. |
| History | On load, restore up to six topic strings. Successful research moves its topic to the front, deduplicating case-insensitively. Storage failure leaves in-memory history available. |
| Launchpad | One of four subjects is selected. Changing subject replaces its brief and starter question. Applying the question is available while research is idle or failed. |
| Scroll reveal | A mounted section waits for intersection, becomes visible once and is unobserved. Reduced-motion styling displays sections immediately. |
| Research API | Validate → trim and check → run agent → return report and sources. Invalid input returns 422. Expected agent failures and unexpected agent exceptions return 502. |
| Agent loop | Ask model → execute requested tools and append their replies → ask again. A direct answer of 800 to 900 words completes the run. Other drafts enter length-checked finalization. Empty answers, exhausted steps or both tool budgets exhausted enter text-only finalization. A model error enters finalization if evidence exists, otherwise it ends the run. |
| Model retries | Request → response, immediate tool-choice failure, or delayed retry. The last unsuccessful attempt raises to the calling phase. |
| Tool dispatch and budgets | Unknown tool, invalid arguments or exhausted budget → tool feedback. Valid search and page-read attempts consume separate budgets. Search returns URLs or an empty list. A failed or unextractable page yields feedback. Readable pages add evidence and unique source URLs. |
| Finalization | No readable pages → expected failure. With pages, a fresh text-only conversation produces a draft. Out-of-range drafts get up to two revisions before an expected failure. The original Python entry point still translates expected failures into its historical text-and-sources tuple. |
| CLI | Prompt → exit on empty input, print an expected failure, or append sources and save the finished report. |
| PDF API and renderer | Validate → render → PDF response or HTTP error. The renderer scans Markdown lines, collects table rows through the end of each table, resumes ordinary text/heading processing, appends sources when present and emits PDF bytes. |
| Website serving | API startup detects the frontend build. With a build, asset and frontend routes are registered, serving files or the SPA entry point. Development uses Vite's API proxy. |

The browser's research and PDF variants live in `web/src/main.tsx`. The Python entry point for callers that need to distinguish failure is `agent.research_topic`. A successful direct model answer can still have an empty source list. Search results alone do not enter that list.
