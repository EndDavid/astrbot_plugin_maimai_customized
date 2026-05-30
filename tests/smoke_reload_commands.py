import asyncio
import json
import tempfile
from pathlib import Path


QQ_TEST = "1000000000"
IMPORT_TOKEN = "test-import-token"
DEV_TOKEN = "test-developer-token"


class FakeMessageObj:
    def __init__(self, group_id=None):
        self.group_id = group_id
        self.message_id = "smoke_msg"
        self.message = []


class FakeBot:
    async def get_group_member_info(self, **kwargs):
        return {"role": "owner"}

    async def call_action(self, action, **kwargs):
        return {"status": "ok"}


class FakeEvent:
    def __init__(self, message_str, sender_id=QQ_TEST, group_id=None):
        self.message_str = message_str
        self._sender_id = sender_id
        self.message_obj = FakeMessageObj(group_id=group_id)
        self.bot = FakeBot()

    def get_sender_id(self):
        return self._sender_id

    def get_sender_name(self):
        return "smoke"

    def get_platform_name(self):
        return "aiocqhttp"

    def is_at_or_atall(self):
        return False

    def plain_result(self, text):
        return ("text", text)

    def chain_result(self, chain):
        return ("chain", [type(item).__name__ for item in chain])


async def collect(name, generator):
    replies = []
    async for reply in generator:
        replies.append(reply)
    if not replies:
        raise AssertionError(f"{name} returned no reply")
    return replies


async def main():
    from data.plugins.astrbot_plugin_maimaidx.libraries.arcade_credential_manager import init_arcade_credential_manager
    from data.plugins.astrbot_plugin_maimaidx.libraries.maimaidx_api_data import maiApi
    from data.plugins.astrbot_plugin_maimaidx.libraries.maimaidx_music import mai
    from data.plugins.astrbot_plugin_maimaidx.libraries.user_token_manager import init_token_manager
    from data.plugins.astrbot_plugin_maimaidx.command import mai_base, mai_score, mai_table
    from data.plugins.astrbot_plugin_maimaidx.libraries.update_b50.sgid import validate_sgid_freshness

    temp_dir = Path(tempfile.mkdtemp(prefix="maimai_smoke_"))
    token_file = temp_dir / "tokens.json"
    cred_file = temp_dir / "credentials.json"
    token_file.write_text(json.dumps({"tokens": {QQ_TEST: IMPORT_TOKEN}}), encoding="utf-8")
    cred_file.write_text(json.dumps({"credentials": {}}), encoding="utf-8")
    init_token_manager(token_file)
    init_arcade_credential_manager(cred_file)

    maiApi.config.maimaidxtoken = DEV_TOKEN
    maiApi.load_token_proxy()
    await mai.load_local_cache()
    mai.guess()

    cases = [
        ("help", mai_base.maimaidxhelp_handler(FakeEvent("帮助"))),
        ("random", mai_base.random_song_handler(FakeEvent("来个13+"))),
        ("bind-empty", mai_score.bind_token_handler(FakeEvent("绑定水鱼"))),
        ("score-help", mai_score.score_handler(FakeEvent("分数线"))),
        ("score-missing", mai_score.score_handler(FakeEvent("分数线 紫999999 100"))),
        ("rating-table", mai_table.rating_table_handler(FakeEvent("14+定数表"))),
        ("level-process", mai_table.level_process_handler(FakeEvent("14+ ss 进度"))),
        ("level-process-spaced", mai_table.level_process_handler(FakeEvent("14+ ss 紫 进度"))),
        ("score-list", mai_table.level_achievement_list_handler(FakeEvent("14.5分数列表"))),
        ("update-alias-denied", mai_base.update_alias_handler(FakeEvent("更新别名库", sender_id="999"), [QQ_TEST])),
        ("update-table-denied", mai_table.update_table_handler(FakeEvent("更新定数表", sender_id="999"), [QQ_TEST])),
        ("update-plate-denied", mai_table.update_plate_handler(FakeEvent("更新完成表", sender_id="999"), [QQ_TEST])),
    ]

    for name, generator in cases:
        await collect(name, generator)

    stale_sgid = "SGWCMAID000101000000FAKE"
    freshness = validate_sgid_freshness(stale_sgid, max_age_seconds=600)
    if freshness.ok:
        raise AssertionError("stale SGID unexpectedly passed freshness check")

    print(f"smoke ok: {len(cases)} reply cases, sgid default helper checked")


if __name__ == "__main__":
    asyncio.run(main())
