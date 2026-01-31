import re
from typing import List, Tuple
from nonebot.permission import SUPERUSER
from nonebot.adapters import Event
from nonebot.adapters.onebot.v11 import (
    Bot,
    GroupMessageEvent,
    PrivateMessageEvent
)
from nonebot.internal.permission import Permission
from nonebot import logger

from .config import plugin_config
prefix_variance = None
if plugin_config.dice_helper_use_prefix_variance:
    try:
        from MiniDemo.plugins.message_limiter import prefix_variance
    except ImportError as e:
        prefix_variance = None
        logger.warning(
            "prefix_variance 未加载，dice_helper 将不使用前缀扰动功能",
            exc_info=e,
        )
    
async def dice_admin_permission(bot: Bot, event: Event) -> bool:
    if isinstance(event, PrivateMessageEvent):
        return True

    # 群聊：群主 / 管理员 / 超级用户
    if isinstance(event, GroupMessageEvent):
        return (
            event.sender.role in ("admin", "owner")
            or await SUPERUSER(bot, event)
        )

    return False
    
DICE_ADMIN = Permission(dice_admin_permission)
    
def maybe_apply_prefix_variance(text: str) -> str:
    """
    根据配置决定是否使用 prefix_variance
    """
    if prefix_variance is None:
        return text

    try:
        return prefix_variance.apply(text)
    except Exception:
        return text    

def parse_roll_args(parts: list[str]) -> List[Tuple[int, str]]:
    """
    将参数解析为 [(数量, 骰子名), ...]
    支持：
      2d6
      d6
      3命中骰
      命中骰
    """
    result: List[Tuple[int, str]] = []

    for part in parts:
        part = part.strip()
        if not part:
            continue

        # 尝试匹配“数字 + 骰子名”
        m = re.fullmatch(r"(\d+)(.+)", part)
        if m:
            count = int(m.group(1))
            dice = m.group(2)
            result.append((count, dice))
            continue

        # 没有数字，默认 1
        result.append((1, part))

    return result
