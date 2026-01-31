import re
from copy import deepcopy
from dataclasses import replace

from .color import Color, validate_color_name
from .modifier import Modifier, ModifierKind
from .presets import ALL_MODIFIERS, BG_COLOR_MODIFIER, FG_COLOR_MODIFIER
from .style import StyleState


class AnsiStr(object):
    """
    Represents a string with ANSI styling capabilities.

    AnsiStr provides functionality to manipulate and render strings with
    ANSI styles, such as foreground and background colors, RGB color
    specifications, ANSI color codes, and additional color effects.
    This class is intended for applications requiring styled terminal output.

    :ivar _s: The string content to be styled.
    :type _s: str
    :ivar _style: Current style state associated with the string.
    :type _style: StyleState
    """
    def __init__(self, s: str, style: StyleState | None = None):
        self._s: str = s
        self._style: StyleState = style or StyleState()

    @property
    def style(self) -> StyleState:
        """
        Retrieves the style state for the object.

        :return: The current style state.
        :rtype: StyleState
        """
        return self._style

    @style.setter
    def style(self, style: StyleState):
        """
        Sets the style of the object.

        :param style: The new style to be assigned to the object.
        :type style: StyleState
        """
        self._style = style

    def render(self) -> str:
        """
        Renders the content using the defined style.

        This method processes the content stored in the `_s` attribute through
        the rendering logic of the `_style` attribute. The resulting string
        represents the styled version of the content.

        :return: The rendered string output.
        :rtype: str
        """
        return self._style.render(self._s)

    @property
    def default_bg(self) -> AnsiStr:
        """
        Retrieves the default background color by replacing the current
        background color with none while preserving the foreground color value.
        This effectively resets the background color to its default state.

        :return: The updated AnsiStr object with the default background color.
        :rtype: AnsiStr
        """
        return self._replace_color(None, is_bg=True)

    @property
    def default_fg(self) -> AnsiStr:
        """
        Retrieves the default foreground color by replacing the current
        foreground color with none while preserving the background color value.
        This effectively resets the foreground color to its default state.

        :return: The updated AnsiStr object with the default foreground color.
        :rtype: AnsiStr
        """
        return self._replace_color(None, is_bg=False)

    def bg(self, color_name: str) -> AnsiStr:
        """
        Sets the background color using the provided color name.

        :param color_name: The name of the color to set as the background.
        :type color_name: str
        :return: An updated AnsiStr instance with the new background color.
        :rtype: AnsiStr
        """
        return self._set_color_name(color_name, is_bg=True)

    def fg(self, color_name: str) -> AnsiStr:
        """
        Sets the foreground color using the provided color name.

        :param color_name: Name of the color to set as the foreground.
        :type color_name: str
        :return: An updated AnsiStr instance with the new foreground color.
        :rtype: AnsiStr
        """
        return self._set_color_name(color_name, is_bg=False)

    def fg_rgb(self, r: int, g: int, b: int) -> AnsiStr:
        """
        Replaces the foreground color of the text using the RGB values.

        :param r: Red component of the RGB value, specified as an integer
            within the range of 0 to 255.
        :type r: int
        :param g: Green component of the RGB value, specified as an integer
            within the range of 0 to 255.
        :type g: int
        :param b: Blue component of the RGB value, specified as an integer
            within the range of 0 to 255.
        :type b: int
        :return: An `AnsiStr` object representing the foreground ANSI color
            string for the specified RGB values.
        """
        color = Color.rgb(r, g, b)
        return self._replace_color(color, is_bg=False)

    def bg_rgb(self, r: int, g: int, b: int) -> AnsiStr:
        """
        Replaces the background color of the text using the RGB values.

        :param r: Red component of the RGB color (0-255).
        :type r: int
        :param g: Green component of the RGB color (0-255).
        :type g: int
        :param b: Blue component of the RGB color (0-255).
        :type b: int
        :return: The text with the updated background color.
        :rtype: AnsiStr
        """
        color = Color.rgb(r, g, b)
        return self._replace_color(color, is_bg=True)

    def rgb(self, r: int, g: int, b: int) -> AnsiStr:
        """
        Replaces the foreground color of the text using the RGB values.

        :param r: Red component of the RGB value, specified as an integer
            within the range of 0 to 255.
        :type r: int
        :param g: Green component of the RGB value, specified as an integer
            within the range of 0 to 255.
        :type g: int
        :param b: Blue component of the RGB value, specified as an integer
            within the range of 0 to 255.
        :type b: int
        :return: An `AnsiStr` object representing the foreground ANSI color
            string for the specified RGB values.
        """
        return self.fg_rgb(r, g, b)

    def fg_ansi_color(self, color_code: int) -> AnsiStr:
        """
        Replaces the foreground color of the ANSI string with the
        specified 256-color code.

        :param color_code: Color code to be applied, given as an integer.
            Represents the ANSI color code for the desired foreground color.
        :type color_code: int
        :return: An ANSI string object representing the formatted text with the
            specified ANSI color applied.
        :rtype: AnsiStr
        """
        color = Color.ansi256(color_code)
        return self._replace_color(color, is_bg=False)

    def bg_ansi_color(self, color_code: int) -> AnsiStr:
        """
        Replace the background color of the ANSI string with the
        specified 256-color code.

        :param color_code: Color code to be applied, given as an integer.
            Represents the ANSI color code for the desired background color.
        :type color_code: int
        :return: An ANSI string object representing the formatted text with the
            specified ANSI color applied.
        :rtype: AnsiStr
        """
        color = Color.ansi256(color_code)
        return self._replace_color(color, is_bg=True)

    def ansi_color(self, color_code: int) -> AnsiStr:
        """
        Replaces the foreground color of the ANSI string with the
        specified 256-color code.

        :param color_code: Color code to be applied, given as an integer.
            Represents the ANSI color code for the desired foreground color.
        :type color_code: int
        :return: An ANSI string object representing the formatted text with the
            specified ANSI color applied.
        :rtype: AnsiStr
        """
        return self.fg_ansi_color(color_code)

    def invert_colors(self) -> AnsiStr:
        """
        Invert the foreground and background colors of the current AnsiStr
        object.

        :return: A new AnsiStr object with the foreground and background colors
            swapped.
        :rtype: AnsiStr
        """
        ansi_str = self.copy()
        fg = self._style.fg
        bg = self._style.bg
        ansi_str.style = replace(ansi_str.style, fg=bg, bg=fg)
        return ansi_str

    def reset(self) -> AnsiStr:
        """
        Resets the current object state and returns a new instance of AnsiStr
        initialized with the original value.

        :return: A new AnsiStr object initialized with the original
            string value.
        :rtype: AnsiStr
        """
        return AnsiStr(self._s)

    def _set_color_name(self, color_name: str, is_bg: bool) -> AnsiStr:
        """
        Sets the color name for the text based on the specified color and
        background flag.

        :param color_name: The name of the color to apply.
        :type color_name: str
        :param is_bg: A boolean flag indicating whether the color is for the
            background (True) or foreground (False).
        :type is_bg: bool
        :return: The modified text with the applied color.
        :rtype: AnsiStr
        """
        validate_color_name(color_name)
        mod = BG_COLOR_MODIFIER[f"bg_{color_name}"] if is_bg else\
            FG_COLOR_MODIFIER[f"fg_{color_name}"]
        return self._apply_modifier(mod)

    def _replace_color(self, color: Color | None, is_bg: bool) -> AnsiStr:
        """
        Replaces the current color with a new one and applies it as a
        foreground or background modifier to the string.

        :param color: The new color to apply. If None, the color modifier will
            be cleared.
        :type color: Color or None
        :param is_bg: Indicates whether the color should be applied as a
            background (True) or foreground (False) modifier.
        :type is_bg: bool
        :return: An updated string with the color modification applied.
        :rtype: AnsiStr
        """
        mod_kind = ModifierKind.BG if is_bg else ModifierKind.FG
        mod = Modifier(mod_kind, color)
        return self._apply_modifier(mod)

    def _apply_modifier(self, mod) -> AnsiStr:
        """
        Applies a given modifier to the current object and returns a new
        modified instance.

        :param mod: The modifier to be applied to the object's style.
        :type mod: Any
        :return: A new instance of the object with the applied modifier.
        :rtype: AnsiStr
        """
        ansi_str = self.copy()
        ansi_str.style = ansi_str._style.apply(mod)
        return ansi_str

    def copy(self) -> AnsiStr:
        """
        Creates and returns a deep copy of the current `AnsiStr` object.

        :return: A deep copy of the `AnsiStr` instance.
        :rtype: AnsiStr
        """
        return deepcopy(self)

    def __format__(self, format_spec: str) -> str:
        """
        Formats the object according to the given format specification string.
        The format specification string can include multiple format specifiers
        separated by semicolons. Each specifier corresponds to a style
        modifier or a method call that is applied sequentially to generate the
        formatted output.

        :param format_spec: A string containing one or more semicolon-separated
            format specifiers.
        :type format_spec: str
        :return: A formatted string representation of the object.
        :rtype: str
        :raises ValueError: If any of the provided format specifiers are
            invalid.
        """
        if not format_spec:
            return str(self)

        style = self.style
        for spec in format_spec.split(";"):
            spec = spec.strip()
            if not spec:
                continue
            style = self._apply_format_spec(style, spec)

        return style.render(self._s)

    def _apply_format_spec(self, style: StyleState, spec: str) -> StyleState:
        """
        Applies a format specification to a given style and returns a new
        updated style.


        :param style: The initial style state to which the format specification
            will be applied.
        :type style: StyleState
        :param spec: A string representing the format specification to apply.
            It may correspond to a pre-defined modifier, a parameterized
            function, or a parameterless method.
        :type spec: str
        :return: A new `StyleState` object that reflects the applied format
            specification.
        :rtype: StyleState
        :raises ValueError: If the format specification is invalid or
            unsupported.
        """
        if spec in ALL_MODIFIERS:
            return style.apply(ALL_MODIFIERS[spec])

        allowed_funcs = {
            "rgb", "fg_rgb", "bg_rgb", "reset", "invert_colors",
            "ansi_color", "fg_ansi_color", "bg_ansi_color",
            "default_fg", "default_bg"
        }

        # Handle parameterized functions
        match = re.match(r"(\w+)\((.*)\)", spec)
        if match:
            func_name = match.group(1)
            args_str = match.group(2)
            return self._apply_format_func(
                style, func_name, args_str, allowed_funcs
            )

        # Handle parameterless methods
        if spec in allowed_funcs and hasattr(self, spec):
            # Special case for functions that don't just apply a modifier
            if spec == "reset":
                return StyleState()
            if spec == "invert_colors":
                return replace(style, fg=style.bg, bg=style.fg)
            if spec == "default_fg":
                return style.apply(Modifier(ModifierKind.FG, None))
            if spec == "default_bg":
                return style.apply(Modifier(ModifierKind.BG, None))

        raise ValueError(f"Invalid format specifier: {spec}")

    @staticmethod
    def _apply_format_func(
        style: StyleState,
        func_name: str,
        args_str: str,
        allowed_funcs: set[str]
    ) -> StyleState:
        """
        Applies a formatting function to a given style state using the
        specified function name and arguments. This method supports specific
        formatting functions withbpredefined argument types and relies on
        external modifiers and color utilities.

        :param style: The current style state to be modified.
        :type style: StyleState
        :param func_name: The name of the formatting function to apply.
            Must be one of the allowed functions.
        :type func_name: str
        :param args_str: A string containing arguments for the formatting
            function, separated by commas.
        :type args_str: str
        :param allowed_funcs: A set of function names that are permitted for
            modifying the style.
        :type allowed_funcs: set[str]
        :return: A modified instance of the style state after applying the
            formatting function.
        :rtype: StyleState
        :raises ValueError: If the function name is not in the allowed
            functions, or if the arguments provided are invalid for the
            specified formatting function.
        """
        if func_name not in allowed_funcs:
            raise ValueError(f"Unknown format function: {func_name}")

        args = [arg.strip() for arg in args_str.split(",") if arg.strip()]

        try:
            # Convert arguments to integers if they look like integers
            typed_args = []
            for arg in args:
                try:
                    typed_args.append(int(arg))
                except ValueError:
                    typed_args.append(arg)

            if func_name in ("rgb", "fg_rgb"):
                return style.apply(Modifier.fg(Color.rgb(*typed_args)))
            if func_name == "bg_rgb":
                return style.apply(Modifier.bg(Color.rgb(*typed_args)))
            if func_name in ("ansi_color", "fg_ansi_color"):
                return style.apply(Modifier.fg(Color.ansi256(*typed_args)))
            if func_name == "bg_ansi_color":
                return style.apply(Modifier.bg(Color.ansi256(*typed_args)))

            return style
        except (TypeError, ValueError) as e:
            raise ValueError(
                f"Invalid arguments for {func_name}: {args_str}"
            ) from e

    def __str__(self) -> str:
        return self.render()

    def __repr__(self) -> str:
        return f"AnsiStr('{self._s}')"


for _name, _mod in ALL_MODIFIERS.items():
    if hasattr(AnsiStr, _name):
        raise RuntimeError(
            f"Cannot add modifier attribute '{_name}'"
        )
    setattr(
        AnsiStr, _name,
        property(lambda self, m=_mod: self._apply_modifier(m)),
    )
