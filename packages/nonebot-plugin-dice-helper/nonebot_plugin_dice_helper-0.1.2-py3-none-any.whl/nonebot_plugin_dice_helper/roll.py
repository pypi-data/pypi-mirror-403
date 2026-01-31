import random

from nonebot import on_command
from nonebot.adapters.onebot.v11 import MessageEvent, Message
from nonebot.params import CommandArg

from .utils import parse_roll_args, maybe_apply_prefix_variance, DICE_ADMIN
from .custom_dice import (
    add_custom_dice,
    del_custom_dice,
    get_custom_dice,
    get_all_dice,
    get_default_dice,
)
from .storage import get_session_id


# =====================
# roll / 投掷（所有人可用）
# =====================

roll_cmd = on_command("roll", aliases={"投掷"}, priority=5)


@roll_cmd.handle()
async def handle_roll(
    event: MessageEvent,
    args: Message = CommandArg(),
):
    text = args.extract_plain_text().strip()
    if not text:
        await roll_cmd.finish(maybe_apply_prefix_variance("用法：roll 4d6 2命中骰"))

    parts = text.split()
    rolls = parse_roll_args(parts)
    if not rolls:
        await roll_cmd.finish(maybe_apply_prefix_variance("参数格式错误"))

    session_id = get_session_id(event)
    all_dice = get_all_dice(session_id)

    num_sum = 0
    dice_results: dict[str, list[str]] = {}
    custom_counter: dict[str, int] = {}

    for count, dice in rolls:
        # ===== 数字骰 dN =====
        if dice.startswith("d") and dice[1:].isdigit():
            face = int(dice[1:])
            bucket = dice_results.setdefault(dice, [])

            for _ in range(count):
                r = random.randint(1, face)
                bucket.append(str(r))
                num_sum += r
            continue

        # ===== 自定义骰 =====
        if dice in all_dice:
            faces = all_dice[dice]
            bucket = dice_results.setdefault(dice, [])

            for _ in range(count):
                face = random.choice(faces)
                text_face = "|".join(face)
                bucket.append(text_face)

                for item in face:
                    if item.isdigit():
                        num_sum += int(item)
                    else:
                        custom_counter[item] = custom_counter.get(item, 0) + 1
            continue    

        await roll_cmd.finish(maybe_apply_prefix_variance(f"未定义的骰子：{dice}"))

    total_parts = []
    if num_sum:
        total_parts.append(str(num_sum))
    for k, v in custom_counter.items():
        total_parts.append(f"{v}{k}")
        
    lines = ["骰子结果"]
    for dice, values in dice_results.items():
        lines.append(
            f"{dice} ×{len(values)}："
            + "，".join(values)
        )
    lines.append(
        "合计"
        + ("，".join(total_parts) if total_parts else "无")
    )

    msg = "\n".join(lines)
    await roll_cmd.finish(maybe_apply_prefix_variance(msg))


# =====================
# add_dice（仅群管理 / 超级用户）
# =====================

add_cmd = on_command(
    "add_dice",
    priority=5,
    permission=DICE_ADMIN,
)


@add_cmd.handle()
async def handle_add(
    event: MessageEvent,
    args: Message = CommandArg(),
):
    text = args.extract_plain_text().strip()
    if not text:
        await add_cmd.finish(maybe_apply_prefix_variance("用法：add_dice 骰子名 面1 面2 ..."))

    parts = text.split()
    if len(parts) < 2:
        await add_cmd.finish(maybe_apply_prefix_variance("至少需要一个骰子面"))

    name = parts[0]
    faces = [p.split("|") for p in parts[1:]]

    session_id = get_session_id(event)
    ok = add_custom_dice(session_id, name, faces)

    await add_cmd.finish(maybe_apply_prefix_variance("定义成功" if ok else "定义失败"))


# =====================
# del_dice（仅群管理 / 超级用户）
# =====================

del_cmd = on_command(
    "del_dice",
    priority=5,
    permission=DICE_ADMIN,
)


@del_cmd.handle()
async def handle_del(
    event: MessageEvent,
    args: Message = CommandArg(),
):
    name = args.extract_plain_text().strip()
    if not name:
        await del_cmd.finish(maybe_apply_prefix_variance("用法：del_dice 骰子名"))

    session_id = get_session_id(event)
    ok = del_custom_dice(session_id, name)

    await del_cmd.finish(maybe_apply_prefix_variance("删除成功" if ok else "删除失败"))

# =====================
# dice list / dice_list
# =====================

dice_list_cmd = on_command(
    "dice_list",
    priority=5,
)


@dice_list_cmd.handle()
async def handle_dice_list(event: MessageEvent):
    session_id = get_session_id(event)
    default_dice = get_default_dice()
    custom_dice = get_custom_dice(session_id)

    lines = ["当前可用骰子："]

    if default_dice:
        lines.append("【默认骰子】")
        for name, faces in default_dice.items():
            lines.append(f"- {name}（{len(faces)}面）")

    if custom_dice:
        lines.append("【自定义骰子】")
        for name, faces in custom_dice.items():
            lines.append(f"- {name}（{len(faces)}面）")

    if not default_dice and not custom_dice:
        lines.append("（暂无骰子）")

    await dice_list_cmd.finish(
        maybe_apply_prefix_variance("\n".join(lines))
    )