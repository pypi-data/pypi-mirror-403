import json
from pathlib import Path
from typing import Optional

from nonebot import require

require("nonebot_plugin_localstore")
from nonebot_plugin_localstore import (
    get_plugin_data_dir,
    get_plugin_config_file,
)

plugin_config_file: Path = get_plugin_config_file("default_data.json")
plugin_data_dir: Path = get_plugin_data_dir()
default_data: Optional[dict] = None
custom_data: dict[str, dict] = {}

# =====================
# session / path
# =====================

def get_session_id(event) -> str:
    if hasattr(event, "group_id"):
        return f"group_{event.group_id}"
    return f"private_{event.user_id}"


def _get_path(session_id: str) -> Path:
    return plugin_data_dir / f"{session_id}.json"


# =====================
# 会话数据（群 / 私聊）
# =====================

def load_data(session_id: str) -> dict:
    global custom_data
    if session_id not in custom_data:
        path = _get_path(session_id)
        if not path.exists():
            custom_data[session_id] = {"custom_dice": {}}
        else:
            try:
                custom_data[session_id] = json.loads(path.read_text(encoding="utf-8"))
            except Exception:
                custom_data[session_id] = {"custom_dice": {}}
    return custom_data[session_id]

def save_data(session_id: str, data: dict) -> None:
    path = _get_path(session_id)
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

# =====================
# 默认数据（全插件共用）
# =====================

def load_default_data() -> dict:
    global default_data
    if default_data is None:
        if not plugin_config_file.exists():
            default_data = {}
        else:
            try:
                default_data = json.loads(plugin_config_file.read_text(encoding="utf-8"))
            except Exception:
                default_data = {}
    return default_data

def get_default_section(section: str) -> dict:
    """
    读取 default_data.json 中的某个模块数据
    例如：section="dice"
    """
    data = load_default_data()
    value = data.get(section)
    return value if isinstance(value, dict) else {}
