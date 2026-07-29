from __future__ import annotations

import os
import re
from typing import Any

import requests

from tools._shared import TIMEOUT


API_URL = "https://api.alphaxiv.org"
USER_AGENT = "AI20k-Day04-Research-Agent/1.0 (educational lab)"


def headers() -> dict[str, str]:
    key = os.getenv("ALPHAXIV_API_KEY")
    if not key:
        raise RuntimeError("Missing ALPHAXIV_API_KEY env var")
    return {"Authorization": f"Bearer {key}", "User-Agent": USER_AGENT}


def arxiv_id(value: str) -> str:
    """Accept a bare id, an abs/pdf URL, or an alphaxiv URL and return the arXiv id."""
    match = re.search(r"(\d{4}\.\d{4,5}(?:v\d+)?)", value or "")
    if match:
        return match.group(1)
    return (value or "").strip()


def require_arxiv_id(value: str) -> str:
    identifier = arxiv_id(value)
    if not identifier:
        raise ValueError("arxiv_url must contain an arXiv id (e.g. 1706.03762) or an arXiv URL")
    return identifier


def get_json(path: str) -> Any:
    response = requests.get(f"{API_URL}{path}", headers=headers(), timeout=TIMEOUT)
    response.raise_for_status()
    return response.json()


def resolve_paper(identifier: str) -> dict[str, Any]:
    """GET /papers/v3/{id} -> paper metadata incl. versionId, title, citationBibtex."""
    payload = get_json(f"/papers/v3/{identifier}")
    if not isinstance(payload, dict):
        raise RuntimeError("AlphaXiv returned an unexpected payload for this paper")
    return payload


def clean_text(value: Any) -> str:
    return " ".join(str(value or "").split())
