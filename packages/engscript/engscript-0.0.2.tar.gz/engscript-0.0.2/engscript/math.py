"""
This module contains mathematical functions for accurate meshing
such as trigonometric functions in degrees with exact values returned
for key angles.
"""

import math


def sin_d(deg: float) -> float:
    """
    Calculate sin in degrees with exact values for key angles. This
    can help to reduce meshing errors.

    :param deg: An angle in degrees
    :return: The tangent of that angle

    ## Example
    ```python
    >>> import math
    >>> math.cos(270/180*math.pi)
    -1.8369701987210297e-16
    >>> from engscript import math as esmath
    >>> esmath.cos_d(270)
    0.0
    ```
    """
    # bound in 0-360
    deg = float(deg % 360)

    # return exact values without rounding errors
    if deg in {0.0, 180.0, 360.0}:
        return 0.0
    if deg in {90.0}:
        return 1.0
    if deg in {270.0}:
        return -1.0
    if deg in {30.0, 150.0}:
        return 0.5
    if deg in {210.0, 330.0}:
        return -0.5
    return math.sin(deg / 180 * math.pi)


def cos_d(deg: float) -> float:
    """
    Calculate cosine in degrees with exact values for key angles. This
    can help to reduce meshing errors.

    :param deg: An angle in degrees
    :return: The cosine of that angle

    ## Example
    ```python
    >>> import math
    >>> math.cos(60/180*math.pi)
    0.5000000000000001
    >>> from engscript import math as esmath
    >>> esmath.cos_d(60)
    0.5
    ```
    """

    # bound in 0-360
    deg = float(deg % 360)

    # return exact values without rounding errors
    if deg in {0.0, 360.0}:
        return 1.0
    if deg in {180.0}:
        return -1.0
    if deg in {90.0, 270.0}:
        return 0.0
    if deg in {60.0, 300.0}:
        return 0.5
    if deg in {120.0, 240.0}:
        return -0.5
    return math.cos(deg / 180 * math.pi)


def tan_d(deg: float) -> float:
    """
    Calculate tangent in degrees with exact values for key angles. This
    can help to reduce meshing errors.

    :param deg: An angle in degrees
    :return: The tangent of that angle

    ## Example
    ```python
    >>> import math
    >>> math.tan(135/180*math.pi)
    -1.0000000000000002
    >>> from engscript import math as esmath
    >>> esmath.tan_d(135)
    -1.0
    ```
    """
    # bound in 0-360
    deg = float(deg % 360)

    # return exact values without rounding errors
    if deg in {0.0, 180.0, 360.0}:
        return 0.0
    if deg in {45.0, 225.0}:
        return 1.0
    if deg in {135.0, 315.0}:
        return -1.0
    return math.tan(deg / 180 * math.pi)
