from __future__ import annotations

from typing import Any

from tools import _alphaxiv
from tools._shared import err


MAX_SUMMARY_CHARS = 400


def _summary(raw: dict[str, Any]) -> str:
    paper_summary = raw.get("paper_summary")
    if isinstance(paper_summary, dict) and paper_summary.get("summary"):
        return _alphaxiv.clean_text(paper_summary["summary"])[:MAX_SUMMARY_CHARS]
    return _alphaxiv.clean_text(raw.get("abstract"))[:MAX_SUMMARY_CHARS]


def _as_list(value: Any) -> list[Any]:
    return list(value) if isinstance(value, list) else []


def _item(raw: dict[str, Any]) -> dict[str, Any]:
    paper_id = raw.get("universal_paper_id") or ""
    return {
        "title": _alphaxiv.clean_text(raw.get("title")),
        "summary": _summary(raw),
        "url": f"https://www.alphaxiv.org/abs/{paper_id}" if paper_id else "",
        "arxiv_id": paper_id,
        "authors": _as_list(raw.get("authors")),
        "date": raw.get("publication_date"),
        "topics": _as_list(raw.get("topics")),
        "source": "alphaxiv.org",
    }


def find_related_papers(arxiv_url: str = "", max_results: int = 5) -> dict[str, Any]:
    try:
        identifier = _alphaxiv.require_arxiv_id(arxiv_url)
        max_results = max(1, min(int(max_results or 5), 10))

        payload = _alphaxiv.get_json(f"/papers/v3/{identifier}/similar-papers")
        raw_items = payload if isinstance(payload, list) else []
        items = [_item(raw) for raw in raw_items[:max_results] if isinstance(raw, dict)]

        return {
            "tool": "find_related_papers",
            "arxiv_id": identifier,
            "items": items,
            "item_count": len(items),
            "total_available": len(raw_items),
        }
    except Exception as exc:
        return err("find_related_papers", exc)
