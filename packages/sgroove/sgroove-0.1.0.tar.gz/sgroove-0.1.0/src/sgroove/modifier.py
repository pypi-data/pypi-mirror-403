from dataclasses import dataclass
from enum import Enum, auto
from typing import Generic, TypeVar

from .color import Color

T = TypeVar("T")


class ModifierKind(Enum):
    FG = auto()
    BG = auto()
    FLAG_ADD = auto()
    FLAG_REMOVE = auto()
    RESET = auto()


@dataclass(frozen=True)
class Modifier(Generic[T]):
    kind: ModifierKind
    payload: T

    @staticmethod
    def fg(color: Color) -> Modifier[Color]:
        return Modifier(ModifierKind.FG, color)

    @staticmethod
    def bg(color: Color) -> Modifier[Color]:
        return Modifier(ModifierKind.BG, color)

    @staticmethod
    def flag_add(name: str) -> Modifier[str]:
        return Modifier(ModifierKind.FLAG_ADD, name)

    @staticmethod
    def flag_remove(name: str) -> Modifier[str]:
        return Modifier(ModifierKind.FLAG_REMOVE, name)

    @staticmethod
    def reset() -> Modifier[None]:
        return Modifier(ModifierKind.RESET, None)
