from .color import COLORNAMES, Color
from .modifier import Modifier

COLORS: dict[str, Color[str]] = dict()

for k in COLORNAMES:
    COLORS[k] = Color.named(k)
    COLORS[f"bright_{k}"] = Color.named(k, is_bright=True)

FG_COLOR_MODIFIER: dict[str, Modifier[Color[str]]] = dict()
BG_COLOR_MODIFIER: dict[str, Modifier[Color[str]]] = dict()

for k, v in COLORS.items():
    FG_COLOR_MODIFIER[k] = Modifier.fg(v)
    FG_COLOR_MODIFIER[f"fg_{k}"] = Modifier.fg(v)
    BG_COLOR_MODIFIER[f"bg_{k}"] = Modifier.bg(v)

ADD_FLAGS: dict[str, str] = {
    "bold": "1",
    "faint": "2",
    "italic": "3",
    "underlined": "4",
    "blinking": "5",
    "crossed_out": "9",
    "framed": "51",
    "encircled": "52",
    "overlined": "53"
}

ADD_FLAG_MODIFIERS: dict[str, Modifier[str]] = dict(
    (k, Modifier.flag_add(k)) for k in ADD_FLAGS
)

REMOVE_FLAG_MODIFIERS: dict[str, Modifier[str]] = dict(
    (f"not_{k}", Modifier.flag_remove(k)) for k in ADD_FLAGS
)

ALL_MODIFIERS: dict[str, Modifier[Color[str]] | Modifier[str]] = (
        FG_COLOR_MODIFIER | BG_COLOR_MODIFIER |
        ADD_FLAG_MODIFIERS | REMOVE_FLAG_MODIFIERS
)

__all__ = [
    "COLORS", "FG_COLOR_MODIFIER", "BG_COLOR_MODIFIER", "ADD_FLAGS",
    "ALL_MODIFIERS", "ADD_FLAG_MODIFIERS", "REMOVE_FLAG_MODIFIERS"
]
