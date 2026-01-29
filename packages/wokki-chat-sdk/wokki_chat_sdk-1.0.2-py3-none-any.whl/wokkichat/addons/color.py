"""
.. include:: ../../subdocs/color.md
"""

from typing import Union, Optional, Tuple

WEB_COLORS = { # keep or remove?
    "black": (0, 0, 0),
    "white": (255, 255, 255),
    "red": (255, 0, 0),
    "green": (0, 128, 0),
    "blue": (0, 0, 255),
    "yellow": (255, 255, 0),
    "orange": (255, 165, 0),
    "purple": (128, 0, 128),
    "pink": (255, 192, 203),
}

def to_hex(color_input: Union[Tuple[int, int, int, Optional[int]], str], include_alpha: bool = False) -> str:
    """
    Convert a color to hex.
    """
    if isinstance(color_input, str):
        color_input = WEB_COLORS.get(color_input.lower())
        if color_input is None:
            raise ValueError(f"Unknown color name '{color_input}'")

    if not isinstance(color_input, (tuple, list)):
        raise TypeError("Color must be a string or tuple/list")

    rgb = color_input[:3]
    alpha = color_input[3] if include_alpha and len(color_input) == 4 else None

    hex_color = "#{:02x}{:02x}{:02x}".format(*rgb)
    if alpha is not None:
        hex_color += "{:02x}".format(alpha)
    return hex_color
