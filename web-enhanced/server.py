"""Maigret Enhanced — FastAPI server with SSE progress streaming."""

import asyncio
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, Response, StreamingResponse
from pydantic import BaseModel

import json

from scanner import ScanJob, run_scan, get_db, get_all_tags, get_found_profiles, get_graph_json, generate_export


# In-memory job store
jobs: dict[str, ScanJob] = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    get_db()
    yield


app = FastAPI(title="Maigret Enhanced", lifespan=lifespan)
app.mount("/static", StaticFiles(directory="static"), name="static")


class ScanRequest(BaseModel):
    username: str
    top_sites: int = 500
    timeout: int = 30
    tags: list[str] | None = None
    excluded_tags: list[str] | None = None
    recursive: bool = False

    def model_post_init(self, __context):
        self.username = self.username.strip()
        if not self.username or len(self.username) > 64:
            raise ValueError("Username must be 1-64 characters")
        if not all(c.isalnum() or c in "._-" for c in self.username):
            raise ValueError("Username contains invalid characters")


@app.get("/")
async def index():
    return FileResponse("static/index.html")


@app.post("/api/scan")
async def start_scan(req: ScanRequest):
    job_id = str(uuid.uuid4())[:8]
    job = ScanJob(id=job_id, username=req.username)
    jobs[job_id] = job

    asyncio.create_task(run_scan(
        job,
        top_sites=req.top_sites,
        timeout=req.timeout,
        tags=req.tags,
        excluded_tags=req.excluded_tags,
        recursive=req.recursive,
    ))

    return {"id": job_id, "username": req.username, "status": "started"}


@app.get("/api/scan/{job_id}/progress")
async def scan_progress(job_id: str):
    job = jobs.get(job_id)
    if not job:
        raise HTTPException(404, "Job not found")

    async def event_stream():
        while True:
            try:
                event = await asyncio.wait_for(job.queue.get(), timeout=60)
            except asyncio.TimeoutError:
                yield ": keepalive\n\n"
                continue

            if event.get("type") == "done":
                yield f"data: {json.dumps({'type': 'done', 'found': job.progress.found})}\n\n"
                break
            elif event.get("type") == "error":
                yield f"data: {json.dumps({'type': 'error', 'message': event.get('message', 'Unknown error')})}\n\n"
                break
            else:
                job.progress.completed = event["completed"]
                job.progress.total = event["total"]
                job.progress.found = event["found"]
                yield f"data: {json.dumps(event)}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@app.get("/api/scan/{job_id}/results")
async def scan_results(job_id: str):
    job = jobs.get(job_id)
    if not job:
        raise HTTPException(404, "Job not found")
    if job.status not in ("done", "error"):
        return {"status": job.status, "progress": {
            "completed": job.progress.completed,
            "total": job.progress.total,
            "found": job.progress.found,
        }}

    profiles = get_found_profiles(job.results)
    elapsed = round(job.finished_at - job.started_at, 1) if job.finished_at else 0

    return {
        "status": job.status,
        "username": job.username,
        "profiles": profiles,
        "total_checked": job.progress.total,
        "total_found": len(profiles),
        "elapsed_seconds": elapsed,
        "error": job.error,
    }


@app.get("/api/scan/{job_id}/graph")
async def scan_graph(job_id: str):
    job = jobs.get(job_id)
    if not job or job.status != "done":
        raise HTTPException(400, "Scan not complete")
    return get_graph_json(job.results, job.db, job.username)


@app.get("/api/scan/{job_id}/export/{fmt}")
async def scan_export(job_id: str, fmt: str):
    job = jobs.get(job_id)
    if not job or job.status != "done":
        raise HTTPException(400, "Scan not complete")
    if fmt not in ("csv", "json", "txt", "pdf", "html"):
        raise HTTPException(400, f"Unsupported format: {fmt}")

    content, content_type, filename = generate_export(job, fmt)
    return Response(
        content=content,
        media_type=content_type,
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@app.get("/api/tags")
async def list_tags():
    db = get_db()
    return get_all_tags(db)


@app.get("/api/sites")
async def list_sites():
    db = get_db()
    sites = []
    for site in sorted(db.sites, key=lambda s: s.alexa_rank or 999999):
        sites.append({
            "name": site.name,
            "url_main": site.url_main,
            "tags": list(site.tags) if site.tags else [],
            "rank": site.alexa_rank,
        })
    return sites[:1000]


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=5001)
