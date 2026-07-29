from __future__ import annotations

import os
import re
from typing import Any

import requests

from tools._shared import TIMEOUT, err


ALPHAXIV_API_URL = "https://api.alphaxiv.org"


def _alphaxiv_headers() -> dict[str, str]:
    key = os.getenv("ALPHAXIV_API_KEY")
    if not key:
        raise RuntimeError("Missing ALPHAXIV_API_KEY env var")
    return {
        "Authorization": f"Bearer {key}",
        "User-Agent": "AI20k-Day04-Research-Agent/1.0 (educational lab)",
    }


def _arxiv_id(value: str) -> str:
    match = re.search(r"(\d{4}\.\d{4,5}(?:v\d+)?)", value or "")
    return match.group(1) if match else (value or "").strip()


def get_alphaxiv_overview(arxiv_url: str = "", language: str = "en") -> dict[str, Any]:
    try:
        identifier = _arxiv_id(arxiv_url)
        if not identifier:
            raise ValueError("arxiv_url must contain an arXiv id (e.g. 1706.03762) or an arXiv URL")
        headers = _alphaxiv_headers()

        resolved_resp = requests.get(f"{ALPHAXIV_API_URL}/papers/v3/{identifier}", headers=headers, timeout=TIMEOUT)
        resolved_resp.raise_for_status()
        resolved = resolved_resp.json()
        version_id = resolved.get("versionId")
        if not version_id:
            raise RuntimeError("AlphaXiv did not return a versionId for this paper")

        overview_resp = requests.get(
            f"{ALPHAXIV_API_URL}/papers/v3/{version_id}/overview/{language}", headers=headers, timeout=TIMEOUT
        )
        overview_resp.raise_for_status()
        overview = overview_resp.json()
        summary = overview.get("summary") or {}

        return {
            "tool": "get_alphaxiv_overview",
            "arxiv_id": identifier,
            "title": resolved.get("title") or overview.get("title"),
            "abstract": resolved.get("abstract") or overview.get("abstract"),
            "ai_overview": summary.get("summary") if isinstance(summary, dict) else summary,
            "url": resolved.get("sourceUrl") or f"https://www.alphaxiv.org/abs/{identifier}",
            "source": "alphaxiv.org",
        }
    except Exception as exc:
        return err("get_alphaxiv_overview", exc)
