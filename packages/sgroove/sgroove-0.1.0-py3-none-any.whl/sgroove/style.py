from dataclasses import dataclass, replace

from .color import Color
from .modifier import Modifier, ModifierKind
from .presets import ADD_FLAGS


@dataclass(frozen=True)
class StyleState:
    """
    Represents the visual style state encapsulating foreground color,
    background color, and style flags for text rendering. The class is
    immutable and designed for building and applying styling modifications in
    a composable manner.

    :ivar fg: The foreground color for the style. If `None`, no foreground
        color is applied.
    :type fg: Color | None
    :ivar bg: The background color for the style. If `None`, no background
        color is applied.
    :type bg: Color | None
    :ivar flags: A set of active style flags such as bold or underline.
    :type flags: frozenset[str]
    """
    fg: Color | None = None
    bg: Color | None = None
    flags: frozenset[str] = frozenset()

    def apply(self, mod: Modifier) -> StyleState:
        """
        Applies a given `Modifier` to the current `StyleState`, updating its
        attributes as specified by the modifier's kind and payload.

        :param mod: The `Modifier` instance to apply. Its kind determines the
            type of modification, which can include updating the foreground
            color (FG), background color (BG), adding a flag, removing a flag,
            or resetting the state.
        :type mod: Modifier

        :return: A new instance of `StyleState` with the applied modification.
            The specific changes depend on the kind of the modifier:
                 - If `ModifierKind.FG`, updates the foreground color.
                 - If `ModifierKind.BG`, updates the background color.
                 - If `ModifierKind.FLAG_ADD`, adds the specified flag to the
                    style state.
                 - If `ModifierKind.FLAG_REMOVE`, removes the specified flag
                    from the style state.
                 - If `ModifierKind.RESET`, returns a new default `StyleState`
                    instance.
        :rtype: StyleState
        """
        match mod.kind:
            case ModifierKind.FG:
                return replace(self, fg=mod.payload)
            case ModifierKind.BG:
                return replace(self, bg=mod.payload)
            case ModifierKind.FLAG_ADD:
                return replace(self, flags=self.flags | {mod.payload})
            case ModifierKind.FLAG_REMOVE:
                return replace(self, flags=self.flags - {mod.payload})
            case ModifierKind.RESET:
                return StyleState()
            case _:
                raise ValueError(f"Invalid modifier kind: {mod.kind}")

    def render(self, s: str):
        """
        Generates ANSI escape sequences based on the foreground color,
        background color, and applied flags, wrapping the provided string and
        resetting styles after the string.

        :param s: The string to be styled and rendered.
        :type s: str
        :return: The styled string wrapped with ANSI escape sequences.
        :rtype: str
        """
        esc = []
        if self.fg is not None:
            esc.append(self.fg.escape_code(False))
        if self.bg is not None:
            esc.append(self.bg.escape_code(True))
        for flag in self.flags:
            esc.append(ADD_FLAGS[flag])
        esc_list = ";".join(esc)
        if not esc_list:
            return s
        return f"\033[{esc_list}m{s}\033[0m"
