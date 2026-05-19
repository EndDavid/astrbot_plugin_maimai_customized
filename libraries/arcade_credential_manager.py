from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Optional

from .. import log


class ArcadeCredentialManager:
    def __init__(self, storage_path: Path):
        self.storage_path = storage_path
        self._credentials: dict[str, str] = {}
        self._load()

    def _load(self) -> None:
        if not self.storage_path.exists():
            return
        try:
            data = json.loads(self.storage_path.read_text(encoding="utf-8"))
            raw = data.get("credentials", {}) if isinstance(data, dict) else {}
            self._credentials = {str(key): str(value) for key, value in raw.items() if str(value).strip()}
        except Exception as exc:
            log.error(f"用户机台凭据文件加载失败: {exc}")
            self._credentials = {}

    def _save(self) -> None:
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        data = {"credentials": self._credentials}
        tmp_path = self.storage_path.with_suffix(self.storage_path.suffix + ".tmp")
        tmp_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        os.chmod(tmp_path, 0o600)
        tmp_path.replace(self.storage_path)

    def set_credential(self, qq_id: str, credential: str) -> None:
        qq_id = str(qq_id)
        credential = str(credential or "").strip()
        if credential:
            self._credentials[qq_id] = credential
        else:
            self._credentials.pop(qq_id, None)
        self._save()

    def get_credential(self, qq_id: str) -> Optional[str]:
        return self._credentials.get(str(qq_id))

    def has_credential(self, qq_id: str) -> bool:
        return str(qq_id) in self._credentials

    def delete_credential(self, qq_id: str) -> bool:
        qq_id = str(qq_id)
        if qq_id in self._credentials:
            self._credentials.pop(qq_id, None)
            self._save()
            return True
        return False

    def count(self) -> int:
        return len(self._credentials)


_credential_manager: Optional[ArcadeCredentialManager] = None


def init_arcade_credential_manager(storage_path: Path) -> ArcadeCredentialManager:
    global _credential_manager
    _credential_manager = ArcadeCredentialManager(storage_path)
    return _credential_manager


def get_arcade_credential_manager() -> Optional[ArcadeCredentialManager]:
    return _credential_manager
