from nonebot import get_plugin_config
from pydantic import BaseModel


class SDGBConfig(BaseModel):
    region_id: int = 1
    region_name: str = "北京"
    place_id: int = 1403
    place_name: str = "插电师北京王府井银泰店"
    client_id: str = "A63E01C2805"
    keychip_id: str = "A63E-01C28055905"


class Config(BaseModel):
    sdgb: SDGBConfig = SDGBConfig()


config = get_plugin_config(Config).sdgb
