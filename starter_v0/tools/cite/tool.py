from __future__ import annotations

import re
from typing import Any

from tools import _alphaxiv
from tools._shared import err


MAX_LISTED_AUTHORS = 6


def _bibtex_field(bibtex: str, field: str) -> str:
    match = re.search(rf"{field}\s*=\s*\{{(.*?)\}},?\s*\n", bibtex or "", re.DOTALL)
    return _alphaxiv.clean_text(match.group(1)) if match else ""


def _authors(bibtex: str) -> list[str]:
    raw = _bibtex_field(bibtex, "author")
    return [name for name in (part.strip() for part in re.split(r"\s+and\s+", raw)) if name]


def _apa_name(full_name: str) -> str:
    parts = full_name.split()
    if len(parts) < 2:
        return full_name
    initials = " ".join(f"{part[0]}." for part in parts[:-1] if part)
    return f"{parts[-1]}, {initials}"


def _apa(title: str, authors: list[str], year: str, identifier: str) -> str:
    if not authors:
        author_text = "Unknown author"
    elif len(authors) > MAX_LISTED_AUTHORS:
        author_text = ", ".join(_apa_name(name) for name in authors[:MAX_LISTED_AUTHORS]) + ", et al."
    else:
        author_text = ", ".join(_apa_name(name) for name in authors)
    year_text = year or "n.d."
    return f"{author_text} ({year_text}). {title}. arXiv:{identifier}. https://arxiv.org/abs/{identifier}"


def build_citation(arxiv_url: str = "", style: str = "bibtex") -> dict[str, Any]:
    try:
        identifier = _alphaxiv.require_arxiv_id(arxiv_url)
        style = style if style in {"bibtex", "apa"} else "bibtex"
        resolved = _alphaxiv.resolve_paper(identifier)

        bibtex = resolved.get("citationBibtex") or ""
        title = _alphaxiv.clean_text(resolved.get("title") or _bibtex_field(bibtex, "title"))
        authors = _authors(bibtex)
        year = _bibtex_field(bibtex, "year")
        apa = _apa(title, authors, year, identifier)

        return {
            "tool": "build_citation",
            "arxiv_id": identifier,
            "style": style,
            "citation": bibtex if style == "bibtex" else apa,
            "bibtex": bibtex,
            "apa": apa,
            "title": title,
            "authors": authors,
            "year": year,
            "url": resolved.get("sourceUrl") or f"https://arxiv.org/abs/{identifier}",
            "source": "alphaxiv.org",
        }
    except Exception as exc:
        return err("build_citation", exc)
