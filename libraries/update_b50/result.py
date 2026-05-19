from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class SyncResult:
    player_name: str
    rating: int
    score_count: int
    rating_b35: int = 0
    rating_b15: int = 0
    b35_count: int = 0
    b15_count: int = 0
    max_score_rating: int = 0
    max_score_title: str = ""
    max_score_achievements: float = 0.0
    player_warning: str = ""
