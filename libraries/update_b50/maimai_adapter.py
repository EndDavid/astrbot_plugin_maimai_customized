from __future__ import annotations

from importlib import metadata
from typing import Any

MIN_MAIMAI_PY = (1, 4, 2)
MIN_MAIMAI_FFI = (0, 7, 0)


class MaimaiDependencyError(RuntimeError):
    pass


def parse_version(version: str) -> tuple[int, ...]:
    parts: list[int] = []
    for part in version.replace("-", ".").split("."):
        digits = ""
        for char in part:
            if not char.isdigit():
                break
            digits += char
        if digits:
            parts.append(int(digits))
    return tuple(parts)


def is_version_at_least(version: str, minimum: tuple[int, ...]) -> bool:
    parsed = parse_version(version)
    width = max(len(parsed), len(minimum))
    return parsed + (0,) * (width - len(parsed)) >= minimum + (0,) * (width - len(minimum))


class MaimaiAdapter:
    def __init__(self, timeout: float = 30.0, http_proxy: str = ""):
        self.timeout = float(timeout or 30.0)
        self.http_proxy = (http_proxy or "").strip() or None
        self._client: Any | None = None
        self._imports: dict[str, Any] | None = None

    def ensure_dependency_versions(self) -> None:
        missing: list[str] = []
        too_old: list[str] = []
        installed: list[str] = []
        for package_name, minimum in (("maimai-py", MIN_MAIMAI_PY), ("maimai-ffi", MIN_MAIMAI_FFI)):
            minimum_text = ".".join(str(part) for part in minimum)
            try:
                version = metadata.version(package_name)
            except metadata.PackageNotFoundError:
                missing.append(f"{package_name}>={minimum_text}")
                continue
            installed.append(f"{package_name}=={version}")
            if not is_version_at_least(version, minimum):
                too_old.append(f"{package_name}=={version}，需要 >= {minimum_text}")
        if missing or too_old:
            detail = "；".join(missing + too_old)
            installed_text = "，当前已安装：" + "、".join(installed) if installed else ""
            raise MaimaiDependencyError(f"maimai-py/maimai-ffi 版本不满足当前插件要求。{detail}{installed_text}。请完全关闭 AstrBot 后重新安装 requirements.txt，再启动 AstrBot。")

    def load_imports(self) -> dict[str, Any]:
        if self._imports is not None:
            return self._imports
        self.ensure_dependency_versions()
        try:
            from maimai_py import ArcadeProvider, DivingFishProvider, MaimaiClientMultithreading, PlayerIdentifier
            from maimai_py import exceptions as maimai_exceptions
            import httpx
        except SyntaxError as exc:
            raise MaimaiDependencyError("maimai-py/maimai-ffi 依赖导入失败，当前安装可能版本冲突或文件损坏。请在 AstrBot 的 Python 环境中重新安装 requirements.txt。") from exc
        except ImportError as exc:
            raise MaimaiDependencyError("缺少 maimai-py 依赖，请先安装插件 requirements.txt。") from exc
        try:
            arcade_provider_probe = ArcadeProvider(http_proxy=self.http_proxy)
        except TypeError:
            arcade_provider_probe = ArcadeProvider()
        if hasattr(arcade_provider_probe, "get_player"):
            raise MaimaiDependencyError("当前 AstrBot 进程仍在使用旧版 maimai-py ArcadeProvider。请完全关闭 AstrBot 后重新安装 requirements.txt，并重启 AstrBot。")
        self._imports = {
            "ArcadeProvider": ArcadeProvider,
            "DivingFishProvider": DivingFishProvider,
            "MaimaiClient": MaimaiClientMultithreading,
            "PlayerIdentifier": PlayerIdentifier,
            "AimeServerError": getattr(maimai_exceptions, "AimeServerError", None),
            "ArcadeError": getattr(maimai_exceptions, "ArcadeError", None),
            "ArcadeIdentifierError": getattr(maimai_exceptions, "ArcadeIdentifierError", None),
            "InvalidDeveloperTokenError": getattr(maimai_exceptions, "InvalidDeveloperTokenError", None),
            "InvalidPlayerIdentifierError": getattr(maimai_exceptions, "InvalidPlayerIdentifierError", None),
            "MaimaiPyError": getattr(maimai_exceptions, "MaimaiPyError", None),
            "PrivacyLimitationError": getattr(maimai_exceptions, "PrivacyLimitationError", None),
            "TitleServerBlockedError": getattr(maimai_exceptions, "TitleServerBlockedError", None),
            "TitleServerError": getattr(maimai_exceptions, "TitleServerError", None),
            "TitleServerNetworkError": getattr(maimai_exceptions, "TitleServerNetworkError", None),
            "HTTPError": httpx.HTTPError,
        }
        return self._imports

    @property
    def client(self) -> Any:
        imports = self.load_imports()
        if self._client is None:
            kwargs = {"trust_env": False}
            if self.http_proxy:
                kwargs["proxy"] = self.http_proxy
            try:
                self._client = imports["MaimaiClient"](timeout=self.timeout, **kwargs)
            except ImportError as exc:
                if "socks" in str(exc).lower():
                    raise MaimaiDependencyError("当前 maimai_http_proxy 使用 socks 代理，但缺少 socksio 依赖。请安装 socksio，或将代理改为 HTTP 代理。") from exc
                raise
        return self._client

    def arcade_provider(self) -> Any:
        return self.load_imports()["ArcadeProvider"](http_proxy=self.http_proxy)

    def divingfish_provider(self) -> Any:
        return self.load_imports()["DivingFishProvider"]()

    def identifier(self, credentials: str) -> Any:
        return self.load_imports()["PlayerIdentifier"](credentials=credentials)

    async def prepare_song_cache_without_aliases(self) -> None:
        songs = getattr(self.client, "songs", None)
        if not songs:
            return
        try:
            await songs(alias_provider=None)
        except TypeError:
            return

    async def arcade_identifier_from_sgid(self, sgid: str) -> Any:
        identifier = await self.client.qrcode(sgid, http_proxy=self.http_proxy)
        arcade_credentials = getattr(identifier, "credentials", None)
        if not isinstance(arcade_credentials, str) or not arcade_credentials:
            raise RuntimeError("二维码返回的凭据格式异常。")
        return self.identifier(arcade_credentials)
