from __future__ import annotations

import re
from pathlib import Path

import uvicorn
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from Pipeline.main import run_pipeline
from Pipeline.retrieval_agent import RetrievalAgent
from backend.knowledge_graph import persist_knowledge_graph
from pydantic import BaseModel

ROOT_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = ROOT_DIR / "raw"
MAX_PREVIEW_CHARS = 4_000
TEXT_EXTENSIONS = {".txt", ".md", ".json", ".csv", ".py", ".html", ".xml"}
PDF_EXTENSION = ".pdf"
SUPPORTED_EXTENSIONS = TEXT_EXTENSIONS | {PDF_EXTENSION, ".doc", ".docx"}


def sanitize_filename(filename: str) -> str:
    cleaned = Path(filename).name.strip()
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "_", cleaned)
    return cleaned or "upload.bin"


def build_destination(filename: str) -> Path:
    RAW_DIR.mkdir(exist_ok=True)
    safe_name = sanitize_filename(filename)
    candidate = RAW_DIR / safe_name
    stem = candidate.stem
    suffix = candidate.suffix
    counter = 1

    while candidate.exists():
        candidate = RAW_DIR / f"{stem}_{counter}{suffix}"
        counter += 1

    return candidate


def create_preview(contents: bytes, destination: Path) -> str:
    if destination.suffix.lower() == PDF_EXTENSION:
        return (
            f"PDF stored at {destination.relative_to(ROOT_DIR)}\n"
            f"Filename: {destination.name}\n"
            f"Size: {len(contents)} bytes"
        )

    if destination.suffix.lower() in TEXT_EXTENSIONS:
        return contents.decode("utf-8", errors="replace")[:MAX_PREVIEW_CHARS]

    return f"Stored binary file at {destination.relative_to(ROOT_DIR)}"


app = FastAPI(title="MyWiki Upload API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_origin_regex=r"http://(localhost|127\.0\.0\.1):\d+",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def healthcheck() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/files")
def list_files() -> dict[str, list[str]]:
    RAW_DIR.mkdir(exist_ok=True)
    files = sorted(
        [path.name for path in RAW_DIR.iterdir() if path.is_file()],
        key=str.lower,
    )
    return {"files": files}


@app.get("/knowledge-graph")
def knowledge_graph() -> dict[str, object]:
    graph_data = persist_knowledge_graph(ROOT_DIR / "Agents" / "index.md")
    return {"source": "Agents/index.md", **graph_data}


class ChatRequest(BaseModel):
    query: str


@app.post("/chat")
def chat(request: ChatRequest) -> dict[str, object]:
    query_text = request.query.strip()
    if not query_text:
        raise HTTPException(status_code=400, detail="A non-empty query is required.")

    try:
        result = RetrievalAgent().answer(query_text)
        return result
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/upload")
async def upload_file(file: UploadFile = File(...)) -> dict[str, object]:
    if not file.filename:
        msg = "A filename is required."
        raise HTTPException(status_code=400, detail=msg)

    suffix = Path(file.filename).suffix.lower()
    if suffix not in SUPPORTED_EXTENSIONS:
        msg = f"Unsupported file type: {suffix or 'unknown'}"
        raise HTTPException(status_code=400, detail=msg)

    contents = await file.read()
    if not contents:
        msg = "Uploaded file is empty."
        raise HTTPException(status_code=400, detail=msg)

    destination = build_destination(file.filename)
    destination.write_bytes(contents)

    response: dict[str, object] = {
        "filename": destination.name,
        "path": str(destination.relative_to(ROOT_DIR)),
        "size": len(contents),
        "preview": create_preview(contents, destination),
        "message": f"Saved {destination.name} to raw/",
    }

    if suffix == PDF_EXTENSION:
        try:
            pipeline_result = run_pipeline(destination.name)
            graph_result = persist_knowledge_graph(ROOT_DIR / "Agents" / "index.md")
            response["pipeline"] = {
                "status": "indexed",
                **pipeline_result,
                "graph_path": graph_result.get("graph_path", "Agents/graph.json"),
            }
        except Exception as exc:
            response["pipeline"] = {
                "status": "failed",
                "error": str(exc),
            }

    return response


def main() -> None:
    uvicorn.run("backend.app:app", host="0.0.0.0", port=8000, reload=False)


if __name__ == "__main__":
    main()
