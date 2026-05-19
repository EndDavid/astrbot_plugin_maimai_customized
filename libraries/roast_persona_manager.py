import json
import re
from collections import deque
from pathlib import Path
from typing import Deque, Dict, List, Optional

from .. import log


class RoastPersonaManager:
    def __init__(self, storage_path: Path, min_samples: int = 50, max_prompt_samples: int = 120):
        self.storage_path = storage_path
        self.min_samples = min_samples
        self.max_prompt_samples = max_prompt_samples
        self.personas: Dict[str, Dict[str, object]] = {}
        self._load()

    def _load(self) -> None:
        if not self.storage_path.exists():
            self._save()
            return
        try:
            data = json.loads(self.storage_path.read_text(encoding="utf-8"))
            self.personas = {}
            raw_personas = data.get("personas", {}) if isinstance(data, dict) else {}
            raw_samples = data.get("samples", {}) if isinstance(data, dict) else {}
            global_taste = str(data.get("taste_roast", "") or "") if isinstance(data, dict) else ""
            if raw_personas and all(isinstance(value, dict) and isinstance(value.get("samples", []), list) for value in raw_personas.values()):
                for name, info in raw_personas.items():
                    self._set_loaded_persona(str(name), info.get("samples", []), str(info.get("taste_roast", "") or ""), str(info.get("special_note", "") or ""))
            elif raw_personas and all(isinstance(value, list) for value in raw_personas.values()):
                for name, messages in raw_personas.items():
                    self._set_loaded_persona(str(name), messages, global_taste)
            elif isinstance(raw_personas, dict) and isinstance(raw_samples, dict):
                for group_id, persona in raw_personas.items():
                    if not isinstance(persona, dict):
                        continue
                    name = str(persona.get("name", group_id)).strip()
                    user_id = str(persona.get("user_id", "")).strip()
                    messages = raw_samples.get(str(group_id), {}).get(user_id, []) if isinstance(raw_samples.get(str(group_id), {}), dict) else []
                    self._set_loaded_persona(name, messages, global_taste)
            self._save()
        except Exception as exc:
            backup_path = self.storage_path.with_suffix(self.storage_path.suffix + ".broken")
            try:
                if self.storage_path.exists():
                    backup_path.write_text(self.storage_path.read_text(encoding="utf-8"), encoding="utf-8")
            except Exception as backup_exc:
                log.error(f"锐评人格配置备份失败: {backup_exc}")
            log.error(f"锐评人格配置加载失败，已保留当前内存空状态且不会立即覆盖原文件: {exc}")
            self.personas = {}

    def _set_loaded_persona(self, name: str, messages: List[str], taste_roast: str = "", special_note: str = "") -> None:
        name = self._normalize_name(name)
        if not name:
            return
        cleaned = []
        seen = set()
        for message in messages:
            text = self._clean_message(str(message))
            if not self._is_valid_sample(text) or text in seen:
                continue
            seen.add(text)
            cleaned.append(text)
        self.personas[name] = {
            "samples": deque(cleaned),
            "taste_roast": str(taste_roast or "").strip(),
            "special_note": str(special_note or "").strip(),
        }

    def _save(self) -> None:
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "personas": {
                name: {
                    "samples": list(info.get("samples", [])),
                    "taste_roast": str(info.get("taste_roast", "") or ""),
                    "special_note": str(info.get("special_note", "") or ""),
                }
                for name, info in self.personas.items()
            }
        }
        tmp_path = self.storage_path.with_suffix(self.storage_path.suffix + ".tmp")
        tmp_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp_path.replace(self.storage_path)

    def set_persona(self, name: str, messages: List[str], taste_roast: str | None = None, special_note: str | None = None) -> tuple[int, int, int]:
        name = self._normalize_name(name)
        if not name:
            return 0, 0, 0
        if name not in self.personas:
            self.personas[name] = {"samples": deque(), "taste_roast": "", "special_note": ""}
        samples_obj = self.personas[name].get("samples", deque())
        if not isinstance(samples_obj, deque):
            samples_obj = deque(samples_obj if isinstance(samples_obj, list) else [])
            self.personas[name]["samples"] = samples_obj
        samples: Deque[str] = samples_obj
        existing = set(samples)
        added = 0
        skipped = 0
        for message in messages:
            text = self._clean_message(message)
            if not self._is_valid_sample(text):
                skipped += 1
                continue
            if text in existing:
                skipped += 1
                continue
            samples.append(text)
            existing.add(text)
            added += 1
        if taste_roast is not None:
            self.personas[name]["taste_roast"] = str(taste_roast or "").strip()
        if special_note is not None:
            self.personas[name]["special_note"] = str(special_note or "").strip()
        self._save()
        return added, skipped, len(samples)

    def replace_samples(self, name: str, messages: List[str]) -> int:
        name = self._normalize_name(name)
        if not name:
            return 0
        if name not in self.personas:
            self.personas[name] = {"samples": deque(), "taste_roast": "", "special_note": ""}
        cleaned = []
        seen = set()
        for message in messages:
            text = self._clean_message(str(message))
            if not self._is_valid_sample(text) or text in seen:
                continue
            seen.add(text)
            cleaned.append(text)
        self.personas[name]["samples"] = deque(cleaned)
        self._save()
        return len(cleaned)

    def remove_persona(self, name: str) -> None:
        name = self._normalize_name(name)
        self.personas.pop(name, None)
        self._save()

    def list_personas(self) -> List[Dict[str, str]]:
        return [
            {
                "name": name,
                "sample_count": str(len(info.get("samples", []))),
                "has_taste_roast": "true" if str(info.get("taste_roast", "") or "").strip() else "false",
                "has_special_note": "true" if str(info.get("special_note", "") or "").strip() else "false",
            }
            for name, info in sorted(self.personas.items(), key=lambda item: item[0])
        ]

    def get_samples(self, name: str, limit: int | None = None, offset: int = 0) -> List[str]:
        name = self._normalize_name(name)
        info = self.personas.get(name)
        if not info:
            return []
        samples = list(info.get("samples", []))
        offset = max(0, int(offset or 0))
        if limit is None:
            return samples[offset:]
        limit = max(0, int(limit or 0))
        return samples[offset:offset + limit]

    def get_taste_roast(self, name: str) -> str:
        name = self._normalize_name(name)
        info = self.personas.get(name)
        if not info:
            return ""
        return str(info.get("taste_roast", "") or "").strip()

    def get_special_note(self, name: str) -> str:
        name = self._normalize_name(name)
        info = self.personas.get(name)
        if not info:
            return ""
        return str(info.get("special_note", "") or "").strip()

    def get_sample_count(self, name: str) -> int:
        return len(self.get_samples(name))

    def find_persona_name(self, style: str) -> Optional[str]:
        style = (style or "").strip()
        if not style:
            return None
        names = sorted(self.personas.keys(), key=len, reverse=True)
        for name in names:
            if style == name or name in style:
                return name
        return None

    def build_prompt_by_style(self, style: str) -> tuple[str, Optional[str], str, str]:
        name = self.find_persona_name(style)
        if not name:
            return "", None, "", ""
        messages = self.get_samples(name)
        if not messages:
            return "", name, self.get_taste_roast(name), self.get_special_note(name)
        selected = self._select_prompt_samples(messages)
        sample_text = "\n".join(f"- {msg}" for msg in selected)
        return (
            f"用户指定的人格名命中了本地自定义人格：{name}。以下是该人格语言样本，共 {len(selected)} 条。"
            "这份本地人格优先级高于普通风格描述和模型自行理解的人格。"
            "你必须学习该人格的句式结构、语气强弱、吐槽节奏、表达密度和转折方式，并在分析优势、分析短板、给建议时都体现这种风格。"
            "可以少量借用口癖，但不要高频复读人格库词汇，不要把样本当固定短语库刷屏。"
            "不要复述样本原文，不要泄露样本来源，不要声称自己就是某个现实用户。\n"
            f"人格样本：\n{sample_text}",
            name,
            self.get_taste_roast(name),
            self.get_special_note(name),
        )

    def update_prompt_sample_limit(self, max_prompt_samples: int) -> None:
        self.max_prompt_samples = max(1, int(max_prompt_samples or 1))

    def _select_prompt_samples(self, messages: List[str]) -> List[str]:
        limit = max(1, int(self.max_prompt_samples))
        if len(messages) <= limit:
            return messages
        recent_count = max(1, int(limit * 0.7))
        spread_count = limit - recent_count
        recent = messages[-recent_count:]
        older = messages[:-recent_count]
        if not older or spread_count <= 0:
            return recent
        step = max(1, len(older) // spread_count)
        spread = older[::step][:spread_count]
        return spread + recent

    def _normalize_name(self, name: str) -> str:
        return re.sub(r"\s+", "", str(name or "").strip())[:40]

    def _clean_message(self, message: str) -> str:
        text = (message or "").strip()
        text = re.sub(r"\s+", " ", text)
        return text[:120]

    def _is_valid_sample(self, text: str) -> bool:
        if len(text) < 3 or len(text) > 120:
            return False
        if text.startswith(("/", "#")):
            return False
        if re.search(r"https?://|\[CQ:|base64|<image|<at", text, re.I):
            return False
        blocked_prefixes = ("锐评b50", "绑定水鱼", "更新/b50", "更新b50", "导 ", "帮助", "help", "b50", "B50")
        return not text.startswith(blocked_prefixes)


_manager: Optional[RoastPersonaManager] = None


def init_roast_persona_manager(storage_path: Path, max_prompt_samples: int = 120) -> RoastPersonaManager:
    global _manager
    _manager = RoastPersonaManager(storage_path, max_prompt_samples=max_prompt_samples)
    return _manager


def get_roast_persona_manager() -> Optional[RoastPersonaManager]:
    return _manager
