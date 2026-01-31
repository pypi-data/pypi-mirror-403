from dataclasses import dataclass
from typing import Literal

FONT_FAMILY: str = "Inter"
ICON_FONT_FAMILY: str = "Material Icons"


@dataclass(frozen=True)
class FontSpec:
    family: str
    style: Literal["", "B", "I"]
    filename: str


FONTS: tuple[FontSpec, ...] = (
    FontSpec(FONT_FAMILY, "", "Inter-Regular.ttf"),
    FontSpec(FONT_FAMILY, "B", "Inter-Bold.ttf"),
    FontSpec(FONT_FAMILY, "I", "Inter-Italic.ttf"),
    FontSpec(ICON_FONT_FAMILY, "", "MaterialIcons-Regular.ttf"),
)
