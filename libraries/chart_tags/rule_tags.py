from __future__ import annotations

from collections.abc import Iterable

from .constants import ALLOWED_TAGS, TAG_ALIASES


def normalize_tag(tag: str) -> str:
    value = str(tag or "").strip()
    return TAG_ALIASES.get(value, value)


def filter_allowed_tags(tags: Iterable[str]) -> list[str]:
    allowed = set(ALLOWED_TAGS)
    result = []
    seen = set()
    for tag in tags:
        normalized = normalize_tag(tag)
        if normalized not in allowed or normalized in seen:
            continue
        seen.add(normalized)
        result.append(normalized)
    return result
