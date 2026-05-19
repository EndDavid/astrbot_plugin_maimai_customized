from __future__ import annotations

import json
import re
from typing import Any

from .common import sanitize_rating_terms
from .prompt_builder import SYSTEM_PROMPT, build_final_prompt


def cleanup_response(raw_text: str) -> dict:
    text = str(raw_text or "").strip()
    text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.I)
    text = re.sub(r"\s*```$", "", text, flags=re.I)
    try:
        data = json.loads(text)
    except Exception:
        match = re.search(r"\{[\s\S]*\}", text)
        if match:
            try:
                data = json.loads(match.group(0))
            except Exception:
                data = {}
        else:
            data = {}
    if not data:
        data = {"title": "B50锐评", "overall_roast": text, "impression_roast": ""}
    return {
        "title": sanitize_rating_terms(str(data.get("title") or "B50锐评")).replace("\n", " ").strip(),
        "taste_roast": sanitize_rating_terms(str(data.get("taste_roast") or "")).replace("\n", " ").strip(),
        "overall_roast": sanitize_rating_terms(str(data.get("overall_roast") or text)).replace("\n", " ").strip(),
        "impression_roast": sanitize_rating_terms(str(data.get("impression_roast") or "")).replace("\n", " ").strip(),
    }


async def resolve_roast_provider_id(context: Any, config: dict | None) -> str | None:
    provider_id = str((config or {}).get("roast_b50_provider_id", "") or "").strip()
    if provider_id:
        return provider_id
    return await context.get_current_chat_provider_id(None)


async def call_llm(context: Any, prompt: str, style: str = "", persona_prompt: str = "", matched_persona_name: str | None = None, taste_roast_setting: str = "", special_note_setting: str = "", config: dict | None = None) -> dict:
    final_prompt = build_final_prompt(prompt, style, persona_prompt, matched_persona_name, taste_roast_setting, special_note_setting)
    provider_id = await resolve_roast_provider_id(context, config)
    dedicated_provider = bool(str((config or {}).get("roast_b50_provider_id", "") or "").strip())
    try:
        response = await context.llm_generate(
            chat_provider_id=provider_id,
            system_prompt=SYSTEM_PROMPT,
            prompt=final_prompt,
        )
    except Exception as exc:
        if dedicated_provider:
            raise RuntimeError(f"锐评B50专用模型不可用或配置错误: {provider_id}") from exc
        raise
    return cleanup_response(response.completion_text if response else "")
