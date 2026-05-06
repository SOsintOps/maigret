"""Maigret wrapper with real-time progress tracking via asyncio Queue."""

import asyncio
import time
import json
import io
import os
from dataclasses import dataclass, field
from typing import Optional

from maigret.sites import MaigretDatabase
from maigret.notify import QueryNotify
from maigret.result import MaigretCheckStatus
from maigret.checking import maigret as maigret_search
from maigret import report


@dataclass
class ScanProgress:
    completed: int = 0
    total: int = 0
    found: int = 0
    site: str = ""
    status: str = ""
    url: str = ""


@dataclass
class ScanJob:
    id: str
    username: str
    status: str = "pending"  # pending, running, done, error
    progress: ScanProgress = field(default_factory=ScanProgress)
    results: dict = field(default_factory=dict)
    queue: asyncio.Queue = field(default_factory=asyncio.Queue)
    started_at: float = 0.0
    finished_at: float = 0.0
    error: Optional[str] = None
    db: Optional[MaigretDatabase] = None
    general_results: list = field(default_factory=list)


class ProgressNotify(QueryNotify):
    """Subclass that pushes every check result onto an asyncio Queue."""

    def __init__(self, total_sites: int, queue: asyncio.Queue, loop: asyncio.AbstractEventLoop):
        super().__init__()
        self.total = total_sites
        self.completed = 0
        self.found = 0
        self._queue = queue
        self._loop = loop

    def start(self, message=None, id_type="username"):
        self.completed = 0
        self.found = 0

    def update(self, result, is_similar=False):
        self.result = result
        self.completed += 1
        status_str = "claimed" if result.status == MaigretCheckStatus.CLAIMED else "available"
        if result.status == MaigretCheckStatus.CLAIMED:
            self.found += 1
        event = {
            "completed": self.completed,
            "total": self.total,
            "found": self.found,
            "site": result.site_name,
            "status": status_str,
            "url": result.site_url_user if result.status == MaigretCheckStatus.CLAIMED else "",
        }
        asyncio.run_coroutine_threadsafe(self._queue.put(event), self._loop)

    def finish(self, message=None):
        # done event is sent by run_scan's finally block; avoid duplicate
        pass


# Global database — loaded once
_db: Optional[MaigretDatabase] = None


def get_db() -> MaigretDatabase:
    global _db
    if _db is None:
        _db = MaigretDatabase()
        data_path = os.path.join(
            os.path.dirname(__import__("maigret").__file__),
            "resources",
            "data.json",
        )
        with open(data_path) as f:
            _db.load_from_str(f.read())
    return _db


def get_all_tags(db: MaigretDatabase) -> list[dict]:
    """Return all tags with site counts."""
    tag_counts: dict[str, int] = {}
    for site in db.sites:
        for tag in site.tags:
            tag_counts[tag] = tag_counts.get(tag, 0) + 1
    return sorted(
        [{"tag": t, "count": c} for t, c in tag_counts.items()],
        key=lambda x: x["count"],
        reverse=True,
    )


async def run_scan(
    job: ScanJob,
    top_sites: int = 500,
    timeout: int = 30,
    tags: list[str] | None = None,
    excluded_tags: list[str] | None = None,
    recursive: bool = False,
) -> None:
    """Run a maigret scan with progress updates pushed to job.queue."""
    db = get_db()
    job.db = db
    job.status = "running"
    job.started_at = time.time()

    try:
        sites_dict = db.ranked_sites_dict(
            tags=tags or [],
            names_top=top_sites,
            disabled=False,
            id_type="username",
        )
        if excluded_tags:
            sites_dict = {
                k: v for k, v in sites_dict.items()
                if not any(t in (v.tags or []) for t in excluded_tags)
            }

        total = len(sites_dict)
        job.progress.total = total

        loop = asyncio.get_running_loop()
        notifier = ProgressNotify(total, job.queue, loop)

        results = await maigret_search(
            username=job.username,
            site_dict=sites_dict,
            logger=None,
            query_notify=notifier,
            timeout=timeout,
            is_parsing_enabled=recursive,
            no_progressbar=True,
            max_connections=50,
        )

        job.results = results
        job.general_results = [(job.username, "username", results)]
        job.status = "done"

    except Exception as e:
        job.status = "error"
        job.error = str(e)
        await job.queue.put({"type": "error", "message": str(e)})

    finally:
        job.finished_at = time.time()
        await job.queue.put({"type": "done"})


def get_found_profiles(results: dict) -> list[dict]:
    """Extract claimed profiles from results."""
    profiles = []
    for site_name, data in results.items():
        status = data.get("status")
        if status and status.status == MaigretCheckStatus.CLAIMED:
            profiles.append({
                "site": site_name,
                "url": status.site_url_user,
                "tags": list(status.tags) if status.tags else [],
                "response_time": round(status.query_time, 2) if status.query_time else None,
                "http_status": data.get("http_status"),
                "ids_data": status.ids_data or {},
            })
    return sorted(profiles, key=lambda p: p["site"].lower())


def get_graph_json(results: dict, db: MaigretDatabase, username: str) -> dict:
    """Build NetworkX graph and return as JSON node-link data."""
    try:
        import networkx as nx
        from networkx.readwrite import json_graph

        G = nx.Graph()
        G.add_node(f"username: {username}", size=25, group=1, color="#7c3aed")

        for site_name, data in results.items():
            status = data.get("status")
            if not status or status.status != MaigretCheckStatus.CLAIMED:
                continue

            node_id = f"site: {site_name}"
            tags = list(status.tags) if status.tags else []
            G.add_node(node_id, size=12, group=2, color="#22c55e",
                       url=status.site_url_user, tags=tags)
            G.add_edge(f"username: {username}", node_id, weight=2)

            if status.ids_data:
                for key, val in status.ids_data.items():
                    if val and len(str(val)) < 100:
                        data_id = f"{key}: {val}"
                        G.add_node(data_id, size=8, group=3, color="#f59e0b")
                        G.add_edge(node_id, data_id, weight=1)

        return json_graph.node_link_data(G)
    except ImportError:
        return {"nodes": [], "links": []}


def generate_export(job: ScanJob, fmt: str) -> tuple[bytes, str, str]:
    """Generate export in requested format. Returns (content, content_type, filename)."""
    username = job.username
    results = job.results

    if fmt == "csv":
        buf = io.StringIO()
        report.generate_csv_report(username, results, buf)
        return buf.getvalue().encode(), "text/csv", f"{username}-maigret.csv"

    elif fmt == "json":
        buf = io.StringIO()
        report.generate_json_report(username, results, buf, "simple")
        return buf.getvalue().encode(), "application/json", f"{username}-maigret.json"

    elif fmt == "txt":
        buf = io.StringIO()
        report.generate_txt_report(username, results, buf)
        return buf.getvalue().encode(), "text/plain", f"{username}-maigret.txt"

    elif fmt == "pdf":
        import tempfile
        context = report.generate_report_context(job.general_results)
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            tmp_path = f.name
        report.save_pdf_report(tmp_path, context)
        with open(tmp_path, "rb") as f:
            content = f.read()
        os.unlink(tmp_path)
        return content, "application/pdf", f"{username}-maigret.pdf"

    elif fmt == "html":
        import tempfile
        context = report.generate_report_context(job.general_results)
        with tempfile.NamedTemporaryFile(suffix=".html", delete=False, mode="w") as f:
            tmp_path = f.name
        report.save_html_report(tmp_path, context)
        with open(tmp_path, "r") as f:
            content = f.read().encode()
        os.unlink(tmp_path)
        return content, "text/html", f"{username}-maigret.html"

    else:
        raise ValueError(f"Unsupported format: {fmt}")
