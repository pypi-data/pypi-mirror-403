from dataclasses import dataclass
from enum import Enum, auto
from typing import Generic, TypeAlias, TypeVar, cast

ColorType: TypeAlias = int | str | tuple[int, int, int]
T = TypeVar("T")


COLORNAMES: list[str] = [
    "black", "red", "green", "yellow", "blue", "magenta", "cyan", "white"
]

FG_COLOR_SHIFT = 30
BG_COLOR_SHIFT = 40
BRIGTH_COLOR_SHIFT = 60


def validate_color_name(name: str) -> None:
    """
    Validates if the provided color name exists in a predefined list of valid
    color names.

    :param name: The color name to validate
    :type name: str
    :raises ValueError: If the given color name is not found in the predefined
        list of valid color names
    """
    if name not in COLORNAMES:
        raise ValueError(
            f"Unknown color name: {name}\n"
            f"Valid color names are: {', '.join(COLORNAMES)}"
        )


def named_to_color_code(name: str, is_bg: bool, is_bright: bool) -> str:
    """
    Converts a named color to its corresponding ANSI color code.

    :param name: Name of the color. Must exist in the `COLORNAMES` list.
    :type name: str
    :param is_bg: If True, the color is treated as a background color.
        Otherwise, it is treated as a foreground color.
    :type is_bg: bool
    :param is_bright: If True, the bright variant of the color is used.
    :type is_bright: bool
    :return: The ANSI color code corresponding to the specified color name,
        background/foreground setting, and brightness.
    :rtype: str
    """
    index = COLORNAMES.index(name)
    shift_a = FG_COLOR_SHIFT if not is_bg else BG_COLOR_SHIFT
    shift_b = BRIGTH_COLOR_SHIFT if is_bright else 0
    shift = shift_a + shift_b
    return f"{index + shift}"


class ColorKind(Enum):
    """
    Represents different kinds of color specifications.
    """
    ANSI256 = auto()
    NAMED = auto()
    RGB = auto()


@dataclass(frozen=True)
class Color(Generic[T]):
    """
    Represents a color in different formats and provides utility methods to
    operate on colors.

    :ivar kind: The kind of color representation, indicating whether it is
        named, RGB, or ANSI256.
    :type kind: ColorKind
    :ivar value: The value of the color, which changes depending on the kind.
        It could be a string for named colors, a tuple of integers for RGB, or
        an integer for ANSI256.
    :type value: T
    :ivar is_bright: Indicates whether the color is bright.
        Applicable for named colors.
    :type is_bright: bool
    """
    kind: ColorKind
    value: T
    is_bright: bool = False

    @staticmethod
    def named(name: str, is_bright: bool = False) -> Color[str]:
        """
        Constructs a predefined named color based on the provided name
        and brightness.

        :param name: The name of the predefined color.
        :type name: str
        :param is_bright: Indicates whether the color should have a bright
            variant. Defaults to False.
        :type is_bright: bool
        :return: A Color object representing the named color.
        :rtype: Color[str]
        """
        validate_color_name(name)
        return Color(ColorKind.NAMED, name, is_bright)

    @staticmethod
    def rgb(r: int, g: int, b: int) -> Color[tuple[int, int, int]]:
        """
        Converts RGB values into a Color object of kind RGB. Validates that
        each RGB component is in the range of 0 to 255 inclusive.
        A ValueError is raised if any value is outside this range.

        :param r: Red component of the color,
            an integer between 0 and 255 inclusive.
        :type r: int
        :param g: Green component of the color,
            an integer between 0 and 255 inclusive.
        :type g: int
        :param b: Blue component of the color,
            an integer between 0 and 255 inclusive.
        :type b: int
        :return: A Color object with kind RGB and the RGB tuple as its value.
        :raises ValueError: If any of the RGB components is not in
            the range 0..255.
        """
        for x in (r, g, b):
            if not 0 <= x <= 255:
                raise ValueError("RGB values must be in range 0..255")
        return Color(ColorKind.RGB, (r, g, b))

    @staticmethod
    def ansi256(code: int) -> Color[int]:
        """
        Converts an ANSI256 color code to a Color object.

        :param code: An integer representing an ANSI256 color code. It must
            be in the range of 0 to 255.
        :type code: int
        :return: A Color object initialized with the ANSI256 color code.
        :rtype: Color[int]
        :raises ValueError: If the ANSI256 color code is not in the valid
            range of 0 to 255.
        """
        if not 0 <= code <= 255:
            raise ValueError("ANSI256 color must be in range 0..255")
        return Color(ColorKind.ANSI256, code)

    def escape_code(self, is_bg: bool) -> str:
        """
        Generates an ANSI escape code for a color based on the color
        kind and value.

        :param is_bg: A boolean indicating whether the escape code is for
            a background color. If ``True``, the method generates a background
            color code. If ``False``, a text color code is generated.
        :type is_bg: bool
        :return: The generated ANSI escape code for the color.
        :rtype: str
        """
        match self.kind:
            case ColorKind.NAMED:
                value = cast(str, self.value)
                return named_to_color_code(value, is_bg, self.is_bright)
            case ColorKind.RGB:
                value = cast(tuple[int, int, int], self.value)
                r, g, b = value
                return f"{48 if is_bg else 38};2;{r};{g};{b}"
            case ColorKind.ANSI256:
                return f"{48 if is_bg else 38};5;{self.value}"
