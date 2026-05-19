from __future__ import annotations

import re
from typing import Any


def sanitize_rating_terms(text: str) -> str:
    value = str(text or "")
    value = re.sub(r"(?<![A-Za-z0-9])16\s*[kK](?![A-Za-z0-9])", "w6", value)
    value = re.sub(r"(?<![A-Za-z0-9])15\s*[kK](?![A-Za-z0-9])", "w5", value)
    value = re.sub(r"(?<!\d)16[0-4]\d{2}(?!\d)", "w6", value)
    value = re.sub(r"(?<!\d)15\d{3}(?!\d)", "w5", value)
    value = re.sub(r"(?<!\d)1[7-9]\d{3}(?!\d)", "顶段", value)
    return value.replace("```json", "").replace("```", "")


def f(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def i(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default
