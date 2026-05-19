from __future__ import annotations

from typing import Any

from .storage import read_chart_tags


def chart_key(song_id: Any, level_index: Any) -> str:
    return f"{song_id}:{level_index}"


def get_chart_tags(song_id: Any, level_index: Any) -> list[str]:
    data = read_chart_tags()
    charts = data.get("charts", {}) if isinstance(data, dict) else {}
    item = charts.get(chart_key(song_id, level_index), {})
    tags = item.get("final_tags") or item.get("tags") or item.get("llm_tags") or []
    if not isinstance(tags, list):
        return []
    return [str(tag) for tag in tags if str(tag).strip()]


def format_chart_tags(song_id: Any, level_index: Any, max_tags: int = 4) -> str:
    tags = get_chart_tags(song_id, level_index)
    if not tags:
        return ""
    return " 标签:" + "/".join(tags[:max_tags])
