from enum import Enum
# 定義季節類型
class SeasonType(str, Enum):
    SPRING_BRIGHT = "Spring Bright"
    SPRING_LIGHT = "Spring Light"
    SUMMER_LIGHT = "Summer Light"
    SUMMER_MUTE = "Summer Mute"
    AUTUMN_DEEP = "Autumn Deep"
    AUTUMN_MUTE = "Autumn Mute"
    WINTER_BRIGHT = "Winter Bright"
    WINTER_DARK = "Winter Dark"