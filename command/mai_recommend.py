from __future__ import annotations

import math
from collections import Counter
from typing import Any

from astrbot.api.event import AstrMessageEvent

from ..command.mai_base import convert_message_segment_to_chain, extract_at_qqid
from ..libraries.chart_tags.lookup import get_chart_tags
from ..libraries.maimaidx_api_data import maiApi
from ..libraries.maimaidx_error import UserDisabledQueryError, UserNotExistsError, UserNotFoundError
from ..libraries.maimaidx_music import mai
from ..libraries.maimaidx_music_info import draw_music_info


def _score(ds: float, achievements: float) -> int:
    value = min(float(achievements), 100.5)
    if value >= 100.5:
        coefficient = 0.224
    elif value >= 100:
        coefficient = 0.216
    elif value >= 99.5:
        coefficient = 0.211
    elif value >= 99:
        coefficient = 0.208
    elif value >= 98:
        coefficient = 0.203
    elif value >= 97:
        coefficient = 0.2
    elif value >= 94:
        coefficient = 0.168
    elif value >= 90:
        coefficient = 0.152
    elif value >= 80:
        coefficient = 0.136
    elif value >= 75:
        coefficient = 0.128
    elif value >= 70:
        coefficient = 0.112
    elif value >= 60:
        coefficient = 0.096
    elif value >= 50:
        coefficient = 0.08
    elif value >= 40:
        coefficient = 0.064
    elif value >= 30:
        coefficient = 0.048
    elif value >= 20:
        coefficient = 0.032
    elif value >= 10:
        coefficient = 0.016
    else:
        coefficient = 0
    return math.floor(float(ds) * value * coefficient)


def _fit_diff(song_id: Any, level_index: int) -> float | None:
    music = mai.total_list.by_id(str(song_id))
    if not music or not music.stats or level_index >= len(music.stats):
        return None
    stats = music.stats[level_index]
    value = getattr(stats, "fit_diff", None) if stats else None
    return float(value) if value is not None else None


def _buckets(user: Any) -> tuple[list[Any], list[Any]]:
    b35 = list((user.charts.sd or [])[:35]) if user.charts else []
    b15 = list((user.charts.dx or [])[:15]) if user.charts else []
    return b35, b15


def _best_tags(charts: list[Any]) -> list[str]:
    counter = Counter()
    for chart in charts:
        tags = get_chart_tags(chart.song_id, chart.level_index)
        for tag in tags:
            counter[tag] += max(1, int(chart.ra or 0) // 100)
    return [tag for tag, _ in counter.most_common(5)]


def _candidate_score(candidate: dict[str, Any], preferred_tags: list[str], floor_ra: int, bucket: str) -> float:
    tags = set(candidate["tags"])
    tag_hit = len(tags & set(preferred_tags))
    fit = candidate.get("fit_diff") or candidate["ds"]
    fit_delta = float(fit) - float(candidate["ds"])
    target = max(floor_ra + 1, 1)
    need_100 = _score(candidate["ds"], 100.0)
    need_1005 = _score(candidate["ds"], 100.5)
    reachable = 1.0 if need_1005 >= target else 0.0
    near = max(0.0, 1 - abs(need_100 - target) / 80)
    bucket_bonus = 0.25 if bucket == "B15" and candidate.get("is_new") else 0
    return tag_hit * 5 + fit_delta * 3 + near * 2 + reachable + bucket_bonus


def _collect_candidates(user: Any, preferred_tags: list[str], b35_floor: int, b15_floor: int) -> list[dict[str, Any]]:
    owned = {(str(chart.song_id), int(chart.level_index)) for chart in [*(user.charts.sd or []), *(user.charts.dx or [])]}
    result = []
    for music in mai.total_list:
        if int(music.id) >= 100000:
            continue
        for level_index in [2, 3, 4]:
            if level_index >= len(music.ds) or level_index >= len(music.charts):
                continue
            key = (str(music.id), level_index)
            if key in owned:
                continue
            tags = get_chart_tags(music.id, level_index)
            if preferred_tags and not set(tags) & set(preferred_tags):
                continue
            fit = _fit_diff(music.id, level_index)
            candidate = {
                "music": music,
                "song_id": str(music.id),
                "title": music.title,
                "level_index": level_index,
                "level": music.level[level_index],
                "ds": float(music.ds[level_index]),
                "fit_diff": fit,
                "tags": tags,
                "is_new": bool(music.basic_info.is_new),
            }
            bucket = "B15" if candidate["is_new"] else "B35"
            floor = b15_floor if bucket == "B15" else b35_floor
            candidate["bucket"] = bucket
            candidate["floor_ra"] = floor
            candidate["score"] = _candidate_score(candidate, preferred_tags, floor, bucket)
            if _score(candidate["ds"], 100.5) > floor:
                result.append(candidate)
    result.sort(key=lambda item: item["score"], reverse=True)
    return result


async def score_recommend_handler(event: AstrMessageEvent):
    qq = extract_at_qqid(event) or event.get_sender_id()
    try:
        user = await maiApi.query_user_b50(qqid=int(qq))
    except (UserNotFoundError, UserNotExistsError):
        yield event.plain_result('没有找到该玩家的水鱼 B50，请确认已绑定 QQ 或允许查询')
        return
    except UserDisabledQueryError:
        yield event.plain_result('该玩家关闭了水鱼第三方成绩查询')
        return
    except Exception as exc:
        yield event.plain_result(f'获取 B50 失败：{type(exc).__name__}')
        return

    b35, b15 = _buckets(user)
    if not b35 and not b15:
        yield event.plain_result('没有获取到可用 B50 数据')
        return

    preferred_tags = _best_tags([*b35, *b15])
    if not preferred_tags:
        yield event.plain_result('还没有可用谱面标签，请先在 WebUI 完成谱面标签更新')
        return

    b35_floor = min([int(chart.ra or 0) for chart in b35], default=0)
    b15_floor = min([int(chart.ra or 0) for chart in b15], default=0)
    candidates = _collect_candidates(user, preferred_tags, b35_floor, b15_floor)
    if not candidates:
        yield event.plain_result('暂时没有找到符合你 B50 标签倾向且理论可吃分的候选谱面')
        return

    candidate = candidates[0]
    music = candidate["music"]
    fit_text = f'{candidate["fit_diff"]:.2f}' if candidate.get("fit_diff") is not None else '未知'
    tags_text = '、'.join(candidate["tags"][:6])
    reason = (
        f'推荐吃分：{candidate["title"]} [{candidate["level"]} / {candidate["ds"]}]\n'
        f'推荐分区：{candidate["bucket"]}，当前最低分：{candidate["floor_ra"]}\n'
        f'命中标签：{tags_text}\n'
        f'玩家擅长标签：{"、".join(preferred_tags)}\n'
        f'拟合定数：{fit_text}，实际定数：{candidate["ds"]}\n'
        f'理由：这张谱面命中了你 B50 中出现频率较高的标签，并且理论 Rating 有机会超过当前 {candidate["bucket"]} 最低分。'
    )
    yield event.plain_result(reason)
    pic = await draw_music_info(music, event.get_sender_id(), user)
    chain = convert_message_segment_to_chain(pic)
    yield event.chain_result(chain)
