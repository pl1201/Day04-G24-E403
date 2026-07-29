from __future__ import annotations

from typing import Any

from tools import _alphaxiv
from tools._shared import err


def get_alphaxiv_overview(arxiv_url: str = "", language: str = "en") -> dict[str, Any]:
    try:
        identifier = _alphaxiv.require_arxiv_id(arxiv_url)
        resolved = _alphaxiv.resolve_paper(identifier)
        version_id = resolved.get("versionId")
        if not version_id:
            raise RuntimeError("AlphaXiv did not return a versionId for this paper")

        overview = _alphaxiv.get_json(f"/papers/v3/{version_id}/overview/{language or 'en'}")
        summary = overview.get("summary") or {}

        return {
            "tool": "get_alphaxiv_overview",
            "arxiv_id": identifier,
            "title": resolved.get("title") or overview.get("title"),
            "abstract": _alphaxiv.clean_text(resolved.get("abstract") or overview.get("abstract")),
            "ai_overview": summary.get("summary") if isinstance(summary, dict) else summary,
            "url": resolved.get("sourceUrl") or f"https://www.alphaxiv.org/abs/{identifier}",
            "source": "alphaxiv.org",
        }
    except Exception as exc:
        return err("get_alphaxiv_overview", exc)
