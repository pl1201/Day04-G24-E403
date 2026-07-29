from __future__ import annotations

import re
from typing import Any

from tools._shared import err, fold_text


MERGEABLE_FIELDS = ("title", "summary", "url", "source", "date", "section")


def _url_key(value: str) -> str:
    """Normalize a URL so tracking params and trailing slashes do not hide a duplicate."""
    cleaned = str(value or "").split("?")[0].split("#")[0].rstrip("/")
    return re.sub(r"^https?://(www\.)?", "", fold_text(cleaned))


def _title_key(value: str) -> str:
    """Fold accents/case/punctuation so two headlines differing only in styling collide."""
    return " ".join(re.findall(r"[a-z0-9]+", fold_text(str(value or ""))))


def _merged(kept: dict[str, Any], duplicate: dict[str, Any]) -> dict[str, Any]:
    """Return a new item, filling fields the kept copy is missing from the duplicate."""
    filled = {field: duplicate.get(field) for field in MERGEABLE_FIELDS if not kept.get(field) and duplicate.get(field)}
    return {**kept, **filled} if filled else kept


def deduplicate_sources(items: list[dict[str, Any]] | None = None, merge_fields: bool = True) -> dict[str, Any]:
    try:
        raw_items = items or []
        if not isinstance(raw_items, list):
            raise ValueError("items must be a list of research item objects")

        kept: list[dict[str, Any]] = []
        seen: dict[str, int] = {}
        groups: list[dict[str, Any]] = []
        ignored_count = 0

        for item in raw_items:
            if not isinstance(item, dict):
                ignored_count += 1
                continue

            url_key = _url_key(item.get("url", ""))
            title_key = _title_key(item.get("title", ""))
            match_index = None
            matched_on = ""
            if url_key and url_key in seen:
                match_index, matched_on = seen[url_key], "url"
            elif title_key and title_key in seen:
                match_index, matched_on = seen[title_key], "title"

            if match_index is None:
                index = len(kept)
                kept.append(dict(item))
                for key in (url_key, title_key):
                    if key:
                        seen.setdefault(key, index)
                continue

            if merge_fields:
                kept[match_index] = _merged(kept[match_index], item)
            groups.append({
                "kept": kept[match_index].get("title") or kept[match_index].get("url") or "",
                "dropped": item.get("title") or item.get("url") or "",
                "matched_on": matched_on,
            })

        return {
            "tool": "deduplicate_sources",
            "items": kept,
            "input_count": len(raw_items),
            "item_count": len(kept),
            "removed_count": len(groups),
            "ignored_count": ignored_count,
            "duplicates": groups,
        }
    except Exception as exc:
        return err("deduplicate_sources", exc)
