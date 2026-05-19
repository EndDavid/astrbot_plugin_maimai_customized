from __future__ import annotations

from typing import Any

from .common import f, i
from ..chart_tags.lookup import format_chart_tags
from .rating_band import rating_band_hint
from .value_level import average_value_level_text, chart_author_info, chart_ds, chart_fit_diff, chart_value_delta, value_level_text


def counter_lines(charts: list[Any], label: str, getter) -> list[str]:
    counts: dict[str, int] = {}
    for chart in charts:
        value = getter(chart)
        if not value or value.startswith("未知"):
            continue
        counts[value] = counts.get(value, 0) + 1
    items = sorted(counts.items(), key=lambda item: item[1], reverse=True)[:10]
    if not items:
        return [f"{label}：暂无"]
    return [f"{label}：" + "、".join(f"{name}×{count}" for name, count in items)]


def chart_bucket(chart_type: str) -> str:
    return "B15" if str(chart_type).lower() == "dx" else "B35"


def chart_line(chart: Any, bucket: str | None = None) -> str:
    bucket = bucket or chart_bucket(chart.type)
    ds = chart_ds(chart)
    fit_diff = chart_fit_diff(chart)
    value_delta = chart_value_delta(chart)
    fc = f" {chart.fc.upper()}" if chart.fc else ""
    fs = f" {chart.fs.upper()}" if chart.fs else ""
    artist, charter = chart_author_info(chart)
    tags = format_chart_tags(chart.song_id, chart.level_index)
    fit_text = f" {value_level_text(value_delta, bucket)}" if fit_diff else " 含金量未知"
    return f"[{bucket} {chart.type} {ds}] {chart.title} {chart.achievements:.4f}% RA {chart.ra} {chart.rate.upper()}{fc}{fs}{fit_text}{tags} 曲师:{artist} 谱师:{charter}"


def build_analysis_context(userinfo: Any, qqid: str) -> str:
    sd = list((userinfo.charts.sd or [])[:35])
    dx = list((userinfo.charts.dx or [])[:15])
    charts = sd + dx
    rating = i(userinfo.rating)
    b35_ra = sum(i(c.ra) for c in sd)
    b15_ra = sum(i(c.ra) for c in dx)
    avg_ach = sum(f(c.achievements) for c in charts) / len(charts) if charts else 0
    avg_ds = sum(chart_ds(c) for c in charts) / len(charts) if charts else 0
    value_deltas = [chart_value_delta(c) for c in charts if chart_fit_diff(c)]
    avg_value_delta = sum(value_deltas) / len(value_deltas) if value_deltas else 0
    top_cards = sorted(((c, "B35") for c in sd), key=lambda item: i(item[0].ra), reverse=True)[:8] + sorted(((c, "B15") for c in dx), key=lambda item: i(item[0].ra), reverse=True)[:8]
    top_cards = sorted(top_cards, key=lambda item: i(item[0].ra), reverse=True)[:8]
    floor_cards = sorted([(c, "B35") for c in sd] + [(c, "B15") for c in dx], key=lambda item: i(item[0].ra))[:8]
    high_ach_cards = sorted([(c, "B35") for c in sd] + [(c, "B15") for c in dx], key=lambda item: f(item[0].achievements), reverse=True)[:8]
    high_value_cards = sorted([(c, "B35") for c in sd] + [(c, "B15") for c in dx], key=lambda item: chart_value_delta(item[0]), reverse=True)[:8]
    low_value_cards = sorted([(c, "B35") for c in sd] + [(c, "B15") for c in dx], key=lambda item: chart_value_delta(item[0]))[:8]
    artist_lines = counter_lines(charts, "B50 曲师分布", lambda c: chart_author_info(c)[0])
    charter_lines = counter_lines(charts, "B50 谱师分布", lambda c: chart_author_info(c)[1])
    lines = [
        f"玩家：{userinfo.nickname or userinfo.username or qqid}  Rating：{rating}",
        f"B35 RA：{b35_ra}  B15 RA：{b15_ra}",
        f"全B50平均达成：{avg_ach:.4f}%  平均定数：{avg_ds:.2f}  整体含金量：{average_value_level_text(avg_value_delta)}",
        rating_band_hint(rating),
        "锐评正文必须结合当前 Rating 判断谱面是否应该出现在 B50：同样一张不到 100% 的高定数谱，在低中分段可能是潜力股，在高分段可能就是债；如果某些谱靠不到 100.0 的达成率吃到了分，要指出这是上限潜力、硬蹭定数，还是需要尽快补鸟的地板漏洞。",
        "B35 是旧版本/历史 best 35，看基本盘、下限、长期结构；B15 是当前版本/new best 15，看近期推分效率、上限突破、新版本适应。",
        "100% 是鸟，100.5% 是鸟加，101% 是理论值；100.xx 是吃到分，99.xx 才叫没吃到分。",
        "拟合定数来自水鱼 chart_stats；含金量差 = 拟合定数 - 实际定数。差值越高，说明该成绩越超出同定数平均表现，越能吹；差值越低，说明这张在同定数里更水或成绩含金量偏低。",
        "谱面标签若出现，只能作为辅助证据，重点帮助判断玩家偏科：键盘配置、星星配置、综合配置、耐力或爆发；不要逐条复读标签，也不要无标签时强行猜标签。",
        "锐评时必须结合含金量差判断：不要只按 Rating 粗暴评价。",
        "曲师来自 basic_info.artist，谱师来自 charts[level_index].charter；谱师/曲师可能存在中文翻译名、日本字原名、罗马音音译、玩家俗称等多个名字，品味锐评不能只做简单字符串直搜。比如中文说法可能对应日文原名，音译名也可能对应罗马字。判断时要结合语义、常见译名/音译/别名推断，但不确定时要说成倾向而不是强行断言。不同类型谱面风格要分开看：standard/sd 与 dx 同一谱师也可能完全不是一个手感；曲师同理，不要把某谱师/曲师的所有谱或所有曲一概而论，要说明是在评价全部、某个类型，还是具体一两张谱。",
        *artist_lines,
        *charter_lines,
        "",
        "最高 RA 谱：",
        *[chart_line(c, bucket) for c, bucket in top_cards],
        "",
        "B50 地板谱：",
        *[chart_line(c, bucket) for c, bucket in floor_cards],
        "",
        "高达成谱：",
        *[chart_line(c, bucket) for c, bucket in high_ach_cards],
        "",
        "含金量最高谱：",
        *[chart_line(c, bucket) for c, bucket in high_value_cards],
        "",
        "含金量最低谱：",
        *[chart_line(c, bucket) for c, bucket in low_value_cards],
    ]
    return "\n".join(lines)
