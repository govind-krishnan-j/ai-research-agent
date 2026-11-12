"""HTTP API for the research website."""

from pathlib import Path
import re

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from agent import BudgetError, ReportLength, ResearchError, research_topic
from report import generate_pdf_bytes


app = FastAPI(title="Research Atlas API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=False,
    allow_methods=["POST", "GET"],
    allow_headers=["Content-Type"],
)


class ResearchRequest(BaseModel):
    length: ReportLength = "detailed"
    topic: str = Field(min_length=2, max_length=300)


class ReportRequest(BaseModel):
    topic: str = Field(min_length=2, max_length=300)
    content: str = Field(min_length=1, max_length=100_000)
    sources: list[str] = Field(default_factory=list, max_length=20)


@app.post("/api/research")
def research(request: ResearchRequest):
    topic = request.topic.strip()
    if len(topic) < 2:
        raise HTTPException(status_code=422, detail="Enter a research topic.")

    try:
        report, sources = research_topic(topic, request.length)
    except BudgetError as exc:
        raise HTTPException(status_code=429, detail=str(exc), headers={"Retry-After": str(exc.retry_after)}) from exc
    except ResearchError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail="Research failed. Please try again.") from exc

    return {"topic": topic, "report": report, "sources": sources}


@app.post("/api/pdf")
def pdf(request: ReportRequest):
    try:
        data = generate_pdf_bytes(request.topic, request.content, request.sources)
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Could not create the PDF.") from exc

    filename = re.sub(r"[^a-zA-Z0-9_-]+", "_", request.topic).strip("_")[:60] or "research"
    return Response(
        content=data,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}_report.pdf"'},
    )


# A production build can be served by the same Python process.
DIST = Path(__file__).parent / "web" / "dist"
if DIST.is_dir():
    app.mount("/assets", StaticFiles(directory=DIST / "assets"), name="assets")

    @app.get("/{path:path}")
    def frontend(path: str):
        candidate = (DIST / path).resolve()
        if candidate.is_file() and candidate.is_relative_to(DIST.resolve()):
            return FileResponse(candidate)
        return FileResponse(DIST / "index.html")
