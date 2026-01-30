"""
This submodule deals with colors. Including functions
for setting multi-colored objects and for converting between
color definitions
"""
from collections.abc import Callable

import numpy as np
import numpy.typing as npt
from PIL import ImageColor


def get_rainbow(
    scale: float = 2.0
) -> Callable[
    [npt.NDArray[np.float32], list[float]],
    tuple[float, float, float, float]
]:
    """
    Return a function for setting the color of a Solid
    to a rainbow.

    :param scale: The scaling of the rainbow. This value is the height
        of each band of color

    :return: A callable function that can be passed as an input to
        `engscript.engscript.Solid.set_color_by_function`
    """
    def rainbow(
        pos: npt.NDArray[np.float32],
        _: list[float]
    ) -> tuple[float, float, float, float]:
        col_index = int((pos[2] / scale) % 6)

        r_cols = ((0.45, 0.16, 0.51, 1.0),
                  (0.0, 0.30, 1.0, 1.0),
                  (0.0, 0.50, 0.15, 1.0),
                  (1.0, 0.93, 0.0, 1.0),
                  (1.0, 0.55, 0.0, 1.0),
                  (0.89, 0.01, 0.01, 1.0))

        return r_cols[col_index]
    return rainbow


def get_color_from_str(colorstring: str) -> tuple[float, float, float, float]:
    """
    Return an rgba color tuple for an input color string.

    :param colorstring: This can be an html hex value (i.e '#ffffff'), webcolor
        name (i.e 'DodgerBlue'). Or anything else that
        [Pillow.ImageColor](https://pillow.readthedocs.io/en/stable/reference/ImageColor.html)
        understands.  Such as hsl and hsv function strings.

    :return: rgba color tuple. Each channel is a float from 0.0 to 1.0
    """

    rgba = ImageColor.getcolor(colorstring, 'RGBA')
    return tuple(c / 255 for c in rgba)  # type: ignore[return-value, union-attr]
