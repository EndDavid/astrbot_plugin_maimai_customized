"""用户 Import-Token 绑定管理模块"""
import json
import os
from pathlib import Path
from typing import Dict, Optional

from .. import log


class UserTokenManager:
    def __init__(self, storage_path: Path):
        self.storage_path = storage_path
        self._tokens: Dict[str, str] = {}
        self._load()

    def _load(self):
        """从文件加载 token 数据"""
        if self.storage_path.exists():
            try:
                with open(self.storage_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self._tokens = data.get('tokens', {})
            except Exception as exc:
                log.error(f'用户 Import-Token 文件加载失败: {exc}')
                self._tokens = {}

    def _save(self):
        """保存 token 数据到文件"""
        try:
            self.storage_path.parent.mkdir(parents=True, exist_ok=True)
            data = {'tokens': self._tokens}
            tmp_path = self.storage_path.with_suffix(self.storage_path.suffix + '.tmp')
            with open(tmp_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            os.chmod(tmp_path, 0o600)
            tmp_path.replace(self.storage_path)
        except Exception as exc:
            log.error(f'用户 Import-Token 文件保存失败: {exc}')
            raise

    def set_token(self, qq_id: str, token: str) -> None:
        """为用户绑定 token"""
        qq_id = str(qq_id)
        token = token.strip()
        if token:
            self._tokens[qq_id] = token
        else:
            self._tokens.pop(qq_id, None)
        self._save()

    def get_token(self, qq_id: str) -> Optional[str]:
        """获取用户的 token"""
        qq_id = str(qq_id)
        return self._tokens.get(qq_id)

    def has_token(self, qq_id: str) -> bool:
        """检查用户是否已绑定 token"""
        return str(qq_id) in self._tokens

    def delete_token(self, qq_id: str) -> bool:
        """删除用户的 token，返回是否成功删除"""
        qq_id = str(qq_id)
        if qq_id in self._tokens:
            del self._tokens[qq_id]
            self._save()
            return True
        return False


# 全局实例（在 main.py 中初始化）
_token_manager: Optional[UserTokenManager] = None


def init_token_manager(storage_path: Path) -> None:
    """初始化全局 token 管理器"""
    global _token_manager
    _token_manager = UserTokenManager(storage_path)


def get_token_manager() -> Optional[UserTokenManager]:
    """获取全局 token 管理器"""
    return _token_manager
