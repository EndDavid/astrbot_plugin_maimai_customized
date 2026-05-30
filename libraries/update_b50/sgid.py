from __future__ import annotations

import hashlib
import re
import time
from dataclasses import dataclass
from datetime import datetime

SGID_PATTERN = re.compile(r"(SGWCMAID[^\s<>\]\[\"']+)", re.IGNORECASE)
SGID_TIMESTAMP_PATTERN = re.compile(r"^SGWCMAID(\d{12})", re.IGNORECASE)
_used_sgid_hashes: dict[str, float] = {}


@dataclass(frozen=True, slots=True)
class SgidFreshness:
    ok: bool
    message: str = ""
    issued_at: int = 0


def extract_sgid(text: str) -> str | None:
    match = SGID_PATTERN.search((text or "").strip())
    if not match:
        return None
    return match.group(1).strip()


def is_probable_sgid(value: str) -> bool:
    value = (value or "").strip()
    return value.upper().startswith("SGWCMAID") and 12 <= len(value) <= 1024


def sgid_issued_at(value: str) -> int | None:
    match = SGID_TIMESTAMP_PATTERN.match((value or "").strip())
    if not match:
        return None
    try:
        dt = datetime.strptime(f"20{match.group(1)}", "%Y%m%d%H%M%S")
    except ValueError:
        return None
    return int(dt.timestamp())


def validate_sgid_freshness(value: str, max_age_seconds: int = 600, future_tolerance_seconds: int = 60) -> SgidFreshness:
    issued_at = sgid_issued_at(value)
    if issued_at is None:
        return SgidFreshness(False, "SGID 时间戳无法解析，请重新从官方公众号获取二维码后再试。")
    current = int(datetime.now().timestamp())
    age = current - issued_at
    if age < -abs(int(future_tolerance_seconds)):
        return SgidFreshness(False, "SGID 时间晚于当前系统时间，请检查服务器时间或重新获取二维码。", issued_at)
    if age > max(1, int(max_age_seconds)):
        return SgidFreshness(False, f"SGID 已超过 {max_age_seconds} 秒有效窗口，请重新从官方公众号获取二维码后再试。", issued_at)
    return SgidFreshness(True, issued_at=issued_at)


def validate_sgid_for_one_time_use(sgid: str, max_age_seconds: int) -> str:
    freshness = validate_sgid_freshness(sgid, max_age_seconds=max_age_seconds)
    if not freshness.ok:
        return freshness.message
    now = time.time()
    for digest, expires_at in list(_used_sgid_hashes.items()):
        if expires_at <= now:
            _used_sgid_hashes.pop(digest, None)
    digest = hashlib.sha256(sgid.encode("utf-8")).hexdigest()
    if digest in _used_sgid_hashes:
        return "这条 SGID 已经被使用过，请重新从官方公众号获取二维码后再试。"
    _used_sgid_hashes[digest] = now + max(max_age_seconds + 60, 300)
    return ""
