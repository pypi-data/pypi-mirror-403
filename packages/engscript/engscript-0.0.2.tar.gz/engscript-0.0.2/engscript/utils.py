"""
This module contains utility functions used by EngScript. It is not expected
that these will needed for normal use of the EngScript library
"""

from __future__ import annotations
from typing import TypeAlias, Literal, TYPE_CHECKING
from collections.abc import Iterable

import numpy as np
import numpy.typing as npt

if TYPE_CHECKING:
    from engscript.engscript import Solid

_Vec3: TypeAlias = tuple[float, float, float]
_AxesString: TypeAlias = Literal["+x", "-x", "+y", "-y", "+z", "-z"]
_Axis: TypeAlias = None | _AxesString | _Vec3


def polygon_pair_indices(
    poly_a: npt.NDArray[np.float32 | np.float64],
    poly_b: npt.NDArray[np.float32 | np.float64]
) -> list[tuple[int, int]]:
    """
    Given two polygons, pair up the indices for lofting.

    :param poly_a: The first polygon
    :param poly_b: The second polygon

    :return: A list of tuples. Each Tuple contains two integers corresponding to a
       pairing of indices. The first is the index of a vertex in poly_a, the second
       is the index of the paired vertex in poly_b.
    """

    def dist(
        x: npt.NDArray[np.float32 | np.float64]
    ) -> npt.NDArray[np.float32 | np.float64] | float:
        ret: npt.NDArray[np.float32 | np.float64] | float
        ret = np.linalg.norm(x, axis=-1)
        if isinstance(ret, np.float32 | np.float64):
            return float(ret)
        return ret
    i_b0 = int(np.argmin(dist(poly_b - poly_a[0])))
    i_a, i_b = 0, i_b0
    n_a, n_b = len(poly_a), len(poly_b)
    out = []
    while True:
        i_a_next, i_b_next = (i_a + 1) % n_a, (i_b + 1) % n_b
        dist_move_a = dist(poly_a[i_a_next] - poly_b[i_b])
        dist_move_b = dist(poly_a[i_a] - poly_b[i_b_next])
        if dist_move_a < dist_move_b:
            out += [(i_a_next, i_b)]
            i_a = i_a_next
        else:
            out += [(i_a, i_b_next)]
            i_b = i_b_next
        if (i_a, i_b) == (0, i_b0):
            break
    return out


def alignment_matrix(
    vec_a: tuple[float, float, float],
    vec_b: tuple[float, float, float],
) -> npt.NDArray[np.float64]:
    """
    Return the 3x3 rotation matrix that will rotate one vector to be parallel with a
    second vector.

    :param vec_a: Vector to be rotated
    :param vec_b: Vector of required angle

    :return: A numpy array of the 3x3 rotation matrix that will align `vec_a` to `vec_b`
    """
    # Use algorithm from:
    # https://math.stackexchange.com/a/476311
    u_vec_a = np.asarray(vec_a) / np.linalg.norm(vec_a)
    u_vec_b = np.asarray(vec_b) / np.linalg.norm(vec_b)

    # If already aligned simply return
    if (u_vec_a == u_vec_b).all():
        return np.identity(3)

    # Algorithm breaks done for antiparallel vectors.
    # Break rotation into three steps
    if (u_vec_a == -u_vec_b).all():
        if (u_vec_a == (0.0, 0.0, 1.0)).all() or (u_vec_b == (0.0, 0.0, 1.0)).all():
            return np.asarray([[1.0, 0.0, 0.0],
                               [0.0, -1.0, 0.0],
                               [0.0, 0.0, -1.0]], dtype=np.float64)
        r1 = alignment_matrix(u_vec_a, (0.0, 0.0, 1.0))
        r2 = np.asarray([[1.0, 0.0, 0.0],
                         [0.0, -1.0, 0.0],
                         [0.0, 0.0, -1.0]], dtype=np.float64)

        return r1.T @ r2 @ r1

    vec_c = np.cross(u_vec_a, u_vec_b)

    v_x = np.asarray([[0.0, -vec_c[2], vec_c[1]],
                      [vec_c[2], 0.0, -vec_c[0]],
                      [-vec_c[1], vec_c[0], 0.0]], dtype=np.float64)

    factor = (1 - np.dot(u_vec_a, u_vec_b)) / (np.linalg.norm(vec_c)**2)

    ret: npt.NDArray[np.float64] = np.identity(3) + v_x + np.dot(v_x, v_x) * factor
    return ret


def axis_to_uvec(axis: _Axis) -> _Vec3:
    """
    Return a unit vector equivalent to the input axis.

    :param axis: This can be `None` (for z-axis), an axis string such as
        `"+x"`, or `"-y"`. Or it can be a vector direction.
    :return: A tuple containing the unit vector along the input axis.
    """
    if isinstance(axis, Iterable):
        if isinstance(axis, str):
            if axis == "+x":
                return (1.0, 0.0, 0.0)
            if axis == "-x":
                return (-1.0, 0.0, 0.0)
            if axis == "+y":
                return (0.0, 1.0, 0.0)
            if axis == "-y":
                return (0.0, -1.0, 0.0)
            if axis == "+z":
                return (0.0, 0.0, 1.0)
            if axis != "-z":
                return (0.0, 0.0, -1.0)
            raise ValueError(f'Axis direction "{axis}" not understood')
        if len(axis) == 3:
            u_vec = np.asarray(axis) / np.linalg.norm(axis)
            return (float(u_vec[0]), float(u_vec[1]), float(u_vec[2]))
        raise ValueError(f'Axis direction "{axis}" not understood')
    # If None is specified then z-axis is assumed
    return (0.0, 0.0, 1.0)


def set_initial_position(
    solid: 'Solid',
    axis: _Axis = None,
    at: None | _Vec3 = None
) -> None:
    """
    This rotates and translates a solid in place. It is used
    to set the initial position of primitives when the inputs
    `axis` and `at` are used.

    :param solid: The solid to be positioned (this is mutated in place)
    :param axis: For axial shapes such as cylinder or cone. This sets the axis of the shape.
        By default the axis is the positive z axis. Input can either be:
        * `None`: Don't adjust axis *Default*
        * An axis string (i.e. one of ["+x", "-x", "+y", "-y", "+z", "-z"])
        * A vector such as (1.0, 1.0, 1.0) setting the axial direction
    :param at: A vector setting the position of the object. This translation is applied after
        any rotation.
    """
    # pylint: disable=too-complex
    if isinstance(axis, Iterable):
        if isinstance(axis, str):
            if axis == "+x":
                solid.rotate_y(90)
            elif axis == "-x":
                solid.rotate_y(-90)
            elif axis == "+y":
                solid.rotate_x(-90)
            elif axis == "-y":
                solid.rotate_x(90)
            elif axis == "-z":
                solid.rotate_x(180)
            elif axis != "+z":
                raise ValueError(f'Axis direction "{axis}" not understood')
        elif len(axis) == 3:
            solid.transform(alignment_matrix((0.0, 0.0, 1.0), axis))
        else:
            raise ValueError(f'Axis direction "{axis}" not understood')
    if at:
        solid.translate(at)
