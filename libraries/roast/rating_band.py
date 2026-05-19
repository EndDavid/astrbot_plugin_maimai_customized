from __future__ import annotations


def rating_band_hint(rating: int) -> str:
    if rating >= 16000:
        return "当前 Rating 属于超高分段，B50 里低含金量、不到 100% 还吃分的谱要重点拷打；能留在 B50 的低达成谱通常说明它定数高或上限空间很大。"
    if rating >= 15500:
        return "当前 Rating 属于高分段，B50 应该逐步减少靠不到 100% 撑分的谱；如果仍有高定数低达成谱，说明潜力和债都很明显。"
    if rating >= 15000:
        return "当前 Rating 属于中高分段，B50 里出现一些不到 100% 但还能吃分的谱很正常，可判断为上限尝试或潜力股；但地板谱如果太多就说明基本盘不稳。"
    if rating >= 14500:
        return "当前 Rating 属于成长分段，B50 里高定数不到 100% 的谱可以看作正在摸上限；锐评时要区分潜力股和纯靠定数硬蹭。"
    return "当前 Rating 属于积累分段，B50 结构比单张成绩更重要；不到 100% 的谱如果能进 B50，通常代表上限尝试，但也要指出基本盘和鸟率问题。"
