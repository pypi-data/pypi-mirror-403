from nonebot.plugin import PluginMetadata
from .config import DiceHelperConfig

__plugin_meta__ = PluginMetadata(
    name="Dice Helper",
    description="NoneBot 可自定义骰子的骰子插件",
    usage=(
        "roll / 投掷 <参数>\n"
        "add_dice <骰子名> <面1> <面2> ...\n"
        "del_dice <骰子名>\n"
        "dice_list"
    ),
    type="application",
    homepage="https://github.com/CaptainDemo/nonebot-plugin-dice-helper",
    config=DiceHelperConfig,
    supported_adapters={"~onebot.v11"},
)

from . import roll
