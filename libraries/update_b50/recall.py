from __future__ import annotations

from typing import Any

from ... import log


class MessageRecaller:
    def __init__(self, context: Any):
        self.context = context

    async def recall_sensitive(self, event: Any) -> str:
        msg_id = self._message_id(event)
        if not msg_id:
            return "未能获取消息 ID，请手动撤回刚才发送的敏感消息。"
        platform_name = self._platform_name(event)
        inst = self._find_platform_inst(platform_name)
        client = inst.get_client() if inst is not None and hasattr(inst, "get_client") else None
        if not client or not hasattr(client, "call_action"):
            return "当前平台不支持自动撤回，请手动撤回刚才发送的敏感消息。"
        try:
            message_id: int | str = int(msg_id) if str(msg_id).isdigit() else msg_id
            await client.call_action("delete_msg", message_id=message_id)
            return ""
        except Exception as exc:
            log.warning(f"更新b50消息撤回失败: {exc}")
            return "消息撤回失败，请确认 Bot 拥有撤回权限并手动撤回敏感消息。"

    @staticmethod
    def _platform_name(event: Any) -> str:
        getter = getattr(event, "get_platform_name", None)
        if callable(getter):
            try:
                return str(getter() or "").lower()
            except Exception:
                return ""
        return ""

    @staticmethod
    def _message_id(event: Any) -> str:
        msg_obj = getattr(event, "message_obj", None)
        value = getattr(msg_obj, "message_id", "") if msg_obj is not None else ""
        if value:
            return str(value)
        raw = getattr(msg_obj, "raw_message", None) if msg_obj is not None else None
        if isinstance(raw, dict):
            for key in ("message_id", "msg_id", "id"):
                if raw.get(key):
                    return str(raw[key])
        return ""

    def _find_platform_inst(self, platform_name: str) -> Any | None:
        getter = getattr(self.context, "get_platform_inst", None)
        if callable(getter) and platform_name:
            try:
                inst = getter(platform_name)
                if inst:
                    return inst
            except Exception:
                pass
        manager = getattr(self.context, "platform_manager", None)
        for inst in getattr(manager, "platform_insts", []) or []:
            try:
                meta = inst.meta()
                if str(meta.name).lower() == platform_name:
                    return inst
            except Exception:
                continue
        return None


async def recall_current_message(event: Any, context: Any | None, config: dict | None) -> str:
    if context is None:
        return ""
    if not bool((config or {}).get("warn_unsupported_recall", True)):
        return ""
    warning = await MessageRecaller(context).recall_sensitive(event)
    return "🔒 已尝试撤回消息，如果没撤回请手动撤回。" if not warning else f"🔒 {warning}"
