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
| Source collection | Both modes search directly and read up to two usable pages. Missing evidence ends the run before generation. |
| Report generation | Brief targets 550 words and Detailed targets 900. Both use a single bounded request. A complete answer is returned with its actual word count. Empty or token-truncated answers produce an error. |
| Token budget | Reserve input, chat overhead and maximum completion before sending. Local workers sharing the budget file reserve atomically. Successful requests charge reported usage for 60 seconds after completion. Failures retain their reservation. Local capacity limits and provider throttling return HTTP 429 with a retry time. |
| CLI | Prompt → exit on empty input, print an expected failure, or append sources and save the finished report. |
| PDF API and renderer | Validate → render → PDF response or HTTP error. The renderer scans Markdown lines, collects table rows through the end of each table, resumes ordinary text/heading processing, appends sources when present and emits PDF bytes. |
| Website serving | API startup detects the frontend build. With a build, asset and frontend routes are registered, serving files or the SPA entry point. Development uses Vite's API proxy. |

The browser's research and PDF variants live in `web/src/main.tsx`. The Python entry point for callers that need to distinguish failure is `agent.research_topic`. Only readable source pages enter the returned source list.
