from __future__ import annotations

from typing import Any

from ...libraries.maimaidx_music import mai
from .common import f


def chart_music(chart: Any) -> Any:
    return mai.total_list.by_id(str(chart.song_id)) if hasattr(mai, "total_list") else None


def chart_ds(chart: Any) -> float:
    music = chart_music(chart)
    if music and len(music.ds) > chart.level_index:
        return f(music.ds[chart.level_index])
    return f(chart.ds)


def chart_fit_diff(chart: Any) -> float:
    music = chart_music(chart)
    if music and music.stats and len(music.stats) > chart.level_index:
        stats = music.stats[chart.level_index]
        if stats and stats.fit_diff is not None:
            return f(stats.fit_diff)
    return 0.0


def chart_value_delta(chart: Any) -> float:
    fit_diff = chart_fit_diff(chart)
    ds = chart_ds(chart)
    return fit_diff - ds if fit_diff else 0.0


def chart_author_info(chart: Any) -> tuple[str, str]:
    music = chart_music(chart)
    if not music:
        return "未知曲师", "未知谱师"
    artist = getattr(getattr(music, "basic_info", None), "artist", None) or "未知曲师"
    charter = "未知谱师"
    charts = getattr(music, "charts", None) or []
    if len(charts) > chart.level_index and getattr(charts[chart.level_index], "charter", None):
        charter = charts[chart.level_index].charter
    return str(artist), str(charter)


def chart_bucket(chart_type: str) -> str:
    return "B15" if str(chart_type).lower() == "dx" else "B35"


def value_level_text(value_delta: float, bucket: str) -> str:
    adj_delta = value_delta + 0.1 if bucket == "B15" else value_delta
    if adj_delta >= 0.2:
        return "含金量特别高"
    if adj_delta >= -0.1:
        return "含金量正常"
    if adj_delta >= -0.4:
        return "含水量较高"
    return "含水量很高"


def average_value_level_text(value_delta: float) -> str:
    if value_delta >= 0.15:
        return "整体含金量偏高"
    if value_delta >= -0.15:
        return "整体含金量正常"
    if value_delta >= -0.35:
        return "整体略有水分"
    return "整体含水量偏高"
