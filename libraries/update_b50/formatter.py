from __future__ import annotations

from .result import SyncResult


def format_success(result: SyncResult) -> str:
    lines = [
        "✅ 水鱼更新完成！",
        f"Rating：{result.rating}",
        f"B35+B15：{result.rating_b35}+{result.rating_b15}",
        f"成绩数：{result.score_count}",
        "现在可以查询最新 B50。",
    ]
    if result.max_score_title:
        lines.insert(-1, f"最高单曲：{result.max_score_title}（RA {result.max_score_rating}，{result.max_score_achievements:.4f}%）")
    if result.player_warning:
        lines.insert(-1, result.player_warning)
    return "\n".join(lines)
