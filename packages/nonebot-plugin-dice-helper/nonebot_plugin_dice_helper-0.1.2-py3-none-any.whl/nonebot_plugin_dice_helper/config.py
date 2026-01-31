from pydantic import BaseModel
from nonebot import get_plugin_config

class DiceHelperConfig(BaseModel):
    dice_helper_use_prefix_variance: bool = False

plugin_config = get_plugin_config(DiceHelperConfig)