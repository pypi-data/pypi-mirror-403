"""
This is the core submodule of EngScript.

We generally prefer to import this module with the following line:

```python
from engscript import engscript as es
```

Please not that all examples using `es.`*something* assume that this line is
already in your python script.

## Class structure

Its two main classes are:

* `Sketch` - holding 2D geometry
* `Solid` - holding 3D geometry

## Helper functions

This submodule provides a number of helper functions for creating [Solids](#Solid) (such
as `cube()`, `cylinder()`, `cone()`, etc) or [Sketches](#Sketch) (such as `square()`,
`circle()`, and `polygon()`.

The helper functions are the preferred way to create. `Solid` and `Sketch` objects. Creating
the objects directly requires using the functions of the underlying kernel
[`manifold3d`](https://pypi.org/project/manifold3d/).

## Transformation functions

### Transforming between object classes

This submodule also provides a transformation functions for combining Solids and Sketches
and for converting a `Sketch` into a `Solid` (such as `extrude()` or `revolve()`)

### Transforming a specific object

Note that many transformations are properties of the `Sketch` or `Solid` itself.
The general rule is that if a transformation simply affects only one `Sketch` or `Solid`
then it is a method and applies to that object in place:

```python
#create a cube called my_cube
my_cube = es.cube([10.0, 10.0, 10.0], center=True)
#my_cube is now a Solid representing a cube centered at the origin

my_cube.translate_z(10.0)
#my_cube is a Solid representing a cube centered at (0, 0, 10)
```

### Transforming multiple objects

Transform functions such as `hull()` combine multiple `Solid` objects, whereas
`split_by_plane()` divides one `Solid` into two separate `Solid` objects.

### Boolean Operations

Boolean operations can be performed with mathematical operators.

* **Union:**  `+` operator
* **Difference:**  `-` operator
* **Intersection:**  `&` operator

"""

from __future__ import annotations
from typing import Any, TypeAlias, Literal
from collections.abc import Iterable, Callable
from copy import copy

from manifold3d import (Manifold,  # type: ignore
                        CrossSection,
                        FillRule,
                        JoinType,
                        triangulate,
                        Mesh)
import trimesh
import numpy as np
import numpy.typing as npt
from matplotlib.text import TextPath
from matplotlib.font_manager import FontProperties

from engscript.export import save_image, Scene
from engscript.colors import get_color_from_str
from engscript.utils import (polygon_pair_indices,
                             set_initial_position,
                             alignment_matrix,
                             axis_to_uvec)

_Vec3: TypeAlias = tuple[float, float, float]
_Vec6: TypeAlias = tuple[float, float, float, float, float, float]

_AxesString: TypeAlias = Literal["+x", "-x", "+y", "-y", "+z", "-z"]
_Axis: TypeAlias = None | _AxesString | _Vec3


def square(
    size: tuple[float, float],
    center: bool | tuple[bool, bool] = False,
    at: None | tuple[float, float] = None
) -> Sketch:
    """
    Create a `Sketch` of a square (technically a rectangle).

    :param size: The (x, y) dimensions of the square.
    :param center: *Optional* Whether to center the square on the origin (or `at` position
        if specified).
        * `False`: square with one corner at the origin, and far corner at (x, y). **Default**
        * `True`: square centered at the origin
        * `(True, False)`: Use a list to select centering by axis.
    :param at: *Optional* Position to translate the square to, default is the origin.
    :return: A `Sketch` object containing a square.

    ## Examples

    ### Example 1
    <!--start engscript-doc
    from engscript import engscript as es
    -->
    ```python
    square1 = es.square([5, 4], False)
    ```
    <!--end engscript-doc
    square1.save_image('../docs/api-docs/doc-images/square1.png', resolution=(300, 300), grid=True)
    --->
    ![](../docs/api-docs/doc-images/square1.png)

    ### Example 2
    <!--start engscript-doc
    from engscript import engscript as es
    -->
    ```python
    square2 = es.square([5, 4], True)
    ```
    <!--end engscript-doc
    square2.save_image('../docs/api-docs/doc-images/square2.png', resolution=(300, 300), grid=True)
    --->
    ![](../docs/api-docs/doc-images/square2.png)

    ### Example 3
    <!--start engscript-doc
    from engscript import engscript as es
    -->
    ```python
    square3 = es.square([5, 4], [False, True])
    ```
    <!--end engscript-doc
    square3.save_image('../docs/api-docs/doc-images/square3.png', resolution=(300, 300), grid=True)
    --->
    ![](../docs/api-docs/doc-images/square3.png)
    """
    if isinstance(center, bool):
        sketch = Sketch(CrossSection.square(size, center))
        if at:
            sketch.translate(at)
        return sketch
    if not isinstance(center, Iterable) or len(center) != 2:
        raise ValueError(
            "centre must be a boolean or an iterable of two booleans")
    shift = (-int(center[0]) * size[0] / 2, -int(center[1]) * size[1] / 2)
    sketch = Sketch(CrossSection.square(size, False))
    sketch.translate(shift)
    if at:
        sketch.translate(at)
    return sketch


def circle(
    r: float | None = None,
    d: float | None = None,
    fn: int = 64,
    at: None | tuple[float, float] = None
) -> Sketch:
    """
    Create a `Sketch` of a circle.

    :param r|d: The radius or diameter of the circle. One of these must be set,
        only one can be set.
    :param fn: *Optional* Sets the number of line segments that make up the circle
        **Default=64**
    :param at: *Optional* Position to translate the circle to, default is the origin.
    :return: A `Sketch` object containing a circle.

    ## Examples

    ### Example 1
    <!--start engscript-doc
    from engscript import engscript as es
    -->
    ```python
    circle1 = es.circle(r=4)
    #This is equivalent to es.circle(d=8)
    ```
    <!--end engscript-doc
    circle1.save_image('../docs/api-docs/doc-images/circle1.png', resolution=(300, 300), grid=True)
    --->
    ![](../docs/api-docs/doc-images/circle1.png)

    ### Example 2 - Creating regular polygons
    <!--start engscript-doc
    from engscript import engscript as es
    from engscript.export import save_image
    -->
    ```python
    hex = es.circle(r=4, fn=6)
    ```
    <!--end engscript-doc
    circ = es.circle(r=4)
    save_image([hex, circ], '../docs/api-docs/doc-images/hex.png',
        resolution=(300, 300), grid=True, lineformats=['b-','c--'])
    --->
    ![](../docs/api-docs/doc-images/hex.png)

    Note that here the 6 points sit on the circle of radius 4 (shown in cyan). Some geomerty is
    needed to calculate polygons of set height, distance-across-flats, or side-length.
    """
    # pylint: disable=missing-param-doc
    if r is None:
        if d is None:
            raise ValueError('r or d must be set for circle')
        r = d / 2
    elif d is not None:
        raise ValueError("r and d can't both be set for circle")

    sketch = Sketch(CrossSection.circle(radius=r, circular_segments=fn))
    if at:
        sketch.translate(at)
    return sketch


def ellipse(
    a: float,
    b: float,
    fn: int = 64,
    at: None | tuple[float, float] = None
) -> Sketch:
    """
    Create a Sketch of an ellipse of width 2a and height 2b.

    :param a: The size of the semi-axis in x
    :param b: The size of the semi-axis in y
    :param fn: *Optional* Sets the number of line segments that make up the ellipse
        **Default=64**
    :param at: *Optional* Position to translate the ellipse to, default is the origin.
    :return: A `Sketch` object containing an ellipse.

    ### Example 1
    <!--start engscript-doc
    from engscript import engscript as es
    -->
    ```python
    ellipse1 = es.ellipse(a=5, b=3)

    ```
    <!--end engscript-doc
    ellipse1.save_image('../docs/api-docs/doc-images/ellipse.png', resolution=(300, 300), grid=True)
    --->
    ![](../docs/api-docs/doc-images/ellipse.png)
    """
    sketch = circle(r=1.0, fn=fn)
    sketch.scale((a, b))
    if at:
        sketch.translate(at)
    return sketch


def polygon(points: list[tuple[float, float]]) -> Sketch:
    """
    Create a `Sketch` of a polygon from a list of (x,y) points.

    :param points: The list of points that make up the polygon. Each point should
        be a tuple containing two floats representing (x, y). The list of points
        will self close. So for a triangle you only need to specify three points.

    :return: A `Sketch` object containing a circle.


    ## Example
    <!--start engscript-doc
    from engscript import engscript as es
    -->
    ```python
    points = [(-3,0), (0,4), (2, 1)]
    poly = es.polygon(points)
    ```
    <!--end engscript-doc
    poly.save_image('../docs/api-docs/doc-images/poly.png', resolution=(300, 300), grid=True)
    --->
    ![](../docs/api-docs/doc-images/poly.png)
    """
    return Sketch(CrossSection([points], fillrule=FillRule.EvenOdd))


def text(
    string: str,
    size: float = 10.0,
    at: tuple[float, float] = (0.0, 0.0),
    *,
    halign: Literal["left", "center", "right"] = "left",
    valign: Literal["top", "center", "baseline", "bottom"] = "baseline",
    font: str = "sans-serif",
    style: Literal["normal", "italic", "oblique"] = "normal",
    variant: Literal["normal", "small-caps"] = "normal",
    weight: Literal["ultralight", "light", "normal", "regular",
                    "book", "medium", "roman", "semibold", "demibold",
                    "demi", "bold", "heavy", "extra bold", "black"] = "normal"
) -> Sketch:
    """
    Return a sketch containing text.

    :param string: The string of text to write.
    :param size: Height of characters in mm **Default=10.0**
    :param at: The placement position (x, y) **Default=(0.0, 0.0)**
    :param halign: Horizontal alignment around `at` position. Options are:
        * "left" **Default**
        * "right"
        * "center"
        ***Keyword only parameter***
    :param valign: Vertical alignment around `at` position. Options are:
        * "top"
        * "center"
        * "baseline" **Default**
        * "bottom"
        ***Keyword only parameter***
    :param font: A text string to identify the font. This can be the full font name
        or a more generic font style such as "sans-serif", "serif" or "monospace"
        **Default="sans-serif"**
        ***Keyword only parameter***
    :param style: Text style. Options are:
        * "normal" **Default**
        * "italic"
        * "oblique"
        ***Keyword only parameter***
    :param variant: Font variant. Options are:
        * "normal" **Default**
        * "small-caps"
    :param weight: Font weight. Options are:
        ["ultralight", "light", "normal", "regular", "book", "medium", "roman",
        "semibold", "demibold", "demi", "bold", "heavy", "extra bold", "black"]
        **Default="normal"** ***Keyword only parameter***

    ## Example
    <!--start engscript-doc
    from engscript import engscript as es
    -->
    ```python
    text = es.text("hello world", size=15.0, halign="center",
                   font="serif", style="italic")
    ```
    <!--end engscript-doc
    text.save_image('../docs/api-docs/doc-images/text.png', resolution=(300, 300), grid=True)
    --->
    ![](../docs/api-docs/doc-images/text.png)
    """
    fp = FontProperties(family=font, style=style, variant=variant, weight=weight)
    path = TextPath((0.0, 0.0), string, size=size, prop=fp)
    # A bit of a horrible nested list comprehension to change from np array to list
    # of list of tuples of floats. Type checking turned off as the input type is poorly
    # defined and creating an accurate enough type hint would also probably not be
    # readable
    polys = [
        [tuple(float(j) for j in i) for i in p]  # type: ignore[union-attr, arg-type]
        for p in path.to_polygons()
    ]

    sketch = Sketch(CrossSection(polys, fillrule=FillRule.EvenOdd))

    box = sketch.bounding_box
    x_tr = at[0]
    if halign == "center":
        x_tr -= (box[2] + box[0]) / 2
    elif halign == "right":
        x_tr -= box[2]
    elif halign != "left":
        raise ValueError(f'Unknown halign value "{halign}". Valid '
                         'options are "left", "center", and "right"')
    y_tr = at[1]
    if valign == "center":
        y_tr -= (box[3] + box[1]) / 2
    elif valign == "top":
        y_tr -= box[3]
    elif valign == "bottom":
        y_tr -= box[1]
    elif valign != "baseline":
        raise ValueError(f'Unknown halign value "{halign}". Valid '
                         'options are "top", "center", "baseline", and "bottom"')

    sketch.translate((x_tr, y_tr))
    return sketch


def hull2d(sketches: list[Sketch]) -> Sketch:
    """
    Return a `Sketch` of the complex hull of a list of other sketches

    :param sketches: A list of Sketches to be hulled.

    :return: A `Sketch` object containing the resulting complex hull.


    ## Example - Polygon from above with rounded corners
    <!--start engscript-doc
    from engscript import engscript as es
    -->
    ```python

    points = [(-3,0), (0,4), (2, 1)]
    circles = []
    for point in points:
        circles.append(es.circle(r=1, at=point))

    rounded_poly = es.hull2d(circles)
    ```
    <!--end engscript-doc
    rounded_poly.save_image('../docs/api-docs/doc-images/rounded_poly.png', resolution=(300, 300), grid=True)
    --->
    ![](../docs/api-docs/doc-images/rounded_poly.png)
    """
    cross_secs = [s.cross_sec for s in sketches]
    return Sketch(CrossSection.batch_hull(cross_secs))


class Sketch:
    """
    This is the main class for creating an manipulating 2D shapes in EngScript.

    ## Creating sketches
    Functions such as `circle()`, `square()`, and `polygon()` are the recommended
    way to make Sketches.

    Creating Sketch objects directly with `Sketch(cross_sec)` requires interacting
    with the underlying [`manifold3d`](https://pypi.org/project/manifold3d/). You
    shouldn't need to do this unless you are doing something special that we don't
    support yet!

    ## Manipulating sketches

    ### Transforming a specific `Sketch`

    A `Sketch` object can be modified with transforms such as `translate()` (or
    derivatives such as `translate_x()`), `rotate()`, `scale()`, `mirror()` etc.
    These modifications modify the existing `Sketch`:
    ```python
    #create a square called my_square
    my_square = es.square([10.0, 10.0], center=True)
    #my_square is now a Sketch representing a square centered at the origin

    my_square.translate_y(10.0)
    #my_square is a Sketch representing a square centered at (0, 10)
    ```
    More information on these transformations are below.

    ### Combining sketches

    The key way to combine sketches is with the `+`, `-`, and `&` operators:

    For example taking the following code:
    <!--start engscript-doc
    from engscript import engscript as es
    -->
    ```python
    # A square centred at the origin
    my_square = es.square([10.0, 10.0], center=True)
    #A second square with one corner at the origin
    my_other_square = es.square([10.0, 10.0], center=False)

    # The union of the two squares
    sketch_union = my_square + my_other_square

    # The difference of the two squares
    sketch_diff = my_square - my_other_square

    # The intersection of the two squares
    sketch_inter = my_square & my_other_square
    ```
    <!--end engscript-doc
    sketch_union.save_image('../docs/api-docs/doc-images/sketch_union.png',
                            grid=True, resolution=(300, 300))
    sketch_diff.save_image('../docs/api-docs/doc-images/sketch_diff.png',
                            grid=True, resolution=(300, 300))
    sketch_inter.save_image('../docs/api-docs/doc-images/sketch_inter.png',
                            grid=True, resolution=(300, 300))
    -->
    The resulting sketches would be

    **`sketch_union`**

    ![](../docs/api-docs/doc-images/sketch_union.png)

    **`sketch_diff`**

    ![](../docs/api-docs/doc-images/sketch_diff.png)

    **`sketch_inter`:**

    ![](../docs/api-docs/doc-images/sketch_inter.png)

    Sketches can also be combined with functions such as `hull2d()`.

    ### Creating a `Solid` from a `Sketch`

    You can create a `Solid` from a Sketch` with functions such as
    `extrude()`, `revolve()`, `spiral_revolve()`
    """

    def __init__(self, cross_sec: CrossSection) -> None:
        """
        Creating a sketch with this constructor is not recommended. To
        do so you will need to work with the underlying
        [`manifold3d`](https://pypi.org/project/manifold3d/) kernel. Instead
        it is recommended you use functions such as `circle()`, `square()`, and
        `polygon()`.

        :param cross_sec: A `manifold3d.CrossSection` object of the desired 2D
            geometry.

        """
        self._cross_sec = cross_sec

    def __add__(self, other: Sketch) -> Sketch:
        return Sketch(self.cross_sec + other.cross_sec)

    def __sub__(self, other: Sketch) -> Sketch:
        return Sketch(self.cross_sec - other.cross_sec)

    def __and__(self, other: Sketch) -> Sketch:
        return Sketch(self.cross_sec ^ other.cross_sec)

    @property
    def bounding_box(self) -> tuple[float, float, float, float]:
        """
        Get the axis aligned bounding box of the sketch.
        This is a tuple of 6 floats.

        The order is x_min, y_min, x_max, y_max
        """
        bbox: tuple[float, float, float, float] = self.cross_sec.bounds()
        return bbox

    @property
    def bounding_box_corners(self) -> tuple[
        tuple[float, float],
        tuple[float, float],
        tuple[float, float],
        tuple[float, float]
    ]:
        """
        Get the corners of the axis aligned bounding box of the sketch.

        Return a tuple containing four tuples of (x,y) coordinates.
        """
        x_min, y_min, x_max, y_max = self.bounding_box
        return ((x_min, y_min),
                (x_min, y_max),
                (x_max, y_min),
                (x_max, y_max))

    @property
    def cross_sec(self) -> CrossSection:
        """
        Read only property that returns the underlying `manifold3d.CrossSection`
        object holding the 2D geometry.

        For normal use cases you shouldn't need to access this directly.
        """
        return self._cross_sec

    def translate(self, xy: tuple[float, float]) -> None:
        """
        Translate this sketch in the xy-plane.

        :param xy: The (x,y) of the distances to translate in x and y.

        ## Example
        <!--start engscript-doc
        from engscript import engscript as es
        -->
        ```python
        # A square with the bottom left corner at the origin
        square1 = es.square([10, 10], center=False)
        square1.translate([2, -2])
        ```
        <!--end engscript-doc
        square1.save_image('../docs/api-docs/doc-images/translate_sketch.png',
                           resolution=(300, 300), grid=True)
        --->
        ![](../docs/api-docs/doc-images/translate_sketch.png)

        See also: `Sketch.translate_x()` and `Sketch.translate_y()`
        """
        self._cross_sec = self.cross_sec.translate(xy)

    def translate_x(self, x: float) -> None:
        """
        Translate the sketch in only the x-direction.

        :param x: The distance to translate in x.

        See also: `Sketch.translate()` and `Sketch.translate_y()`

        """
        self._cross_sec = self.cross_sec.translate((x, 0))

    def translate_y(self, y: float) -> None:
        """
        Translate the sketch in only the y-direction.

        :param y: The distance to translate in y.

        See also: `Sketch.translate()` and `Sketch.translate_x()`

        """
        self._cross_sec = self.cross_sec.translate((0, y))

    def rotate(self, angle: float) -> None:
        """
        Rotate this sketch about the origin.

        :param angle: The angle in degrees to rotate by. Rotations are anti-clockwise
            about the origin

        ## Examples

        ### Example 1
        <!--start engscript-doc
        from engscript import engscript as es
        -->
        ```python
        # A square centered at the origin
        square1 = es.square([10, 10], center=True)
        square1.rotate(10)
        ```
        <!--end engscript-doc
        square1.save_image('../docs/api-docs/doc-images/rotate_sketch1.png',
                           resolution=(300, 300), grid=True)
        --->
        ![](../docs/api-docs/doc-images/rotate_sketch1.png)

        ### Example 2
        <!--start engscript-doc
        from engscript import engscript as es
        -->
        ```python
        # A square with the bottom left corner at the origin
        square2 = es.square([10, 10], center=False)
        square2.rotate(45)
        ```
        <!--end engscript-doc
        square2.save_image('../docs/api-docs/doc-images/rotate_sketch2.png',
                           resolution=(300, 300), grid=True)
        --->
        ![](../docs/api-docs/doc-images/rotate_sketch2.png)

        """
        self._cross_sec = self.cross_sec.rotate(angle)

    def scale(self, factor: float | tuple[float, float]) -> None:
        """
        Scale this Sketch

        :param factor: The scaling factor. To scale differently in x and y you can
            enter a list or tuple of scaling factors.

        ##Examples
        ### Example 1
        <!--start engscript-doc
        from engscript import engscript as es
        -->
        ```python
        from copy import copy
        # A square
        square1 = es.square([10, 10], center=False)
        # Copy the square and scale to much larger
        square2 = copy(square1)
        square2.scale(5)
        shape = square2 - square1
        ```
        <!--end engscript-doc
        shape.save_image('../docs/api-docs/doc-images/2d_scaled_difference.png',
                           resolution=(300, 300), grid=True)
        --->
        ![](../docs/api-docs/doc-images/2d_scaled_difference.png)

        ### Example 2
        <!--start engscript-doc
        from engscript import engscript as es
        -->
        ```python
        #Create a squashed octagon
        octagon = es.circle(d=1, fn=8)
        octagon.scale([8, 3])
        ```
        <!--end engscript-doc
        octagon.save_image('../docs/api-docs/doc-images/squashed_octagon.png',
                           resolution=(300, 300), grid=True)
        --->
        ![](../docs/api-docs/doc-images/squashed_octagon.png)

        """
        if not isinstance(factor, Iterable):
            factor = (factor, factor)
        self._cross_sec = self.cross_sec.scale(factor)

    def mirror(self, normal: tuple[float, float]) -> None:
        """
        Mirror this sketch.

        :param normal: a vector normal to the mirror, the mirror passes through the
            origin.

        ##Examples

        In the following examples a cyan dashed shape is the shape before mirroring
        the green dotted line is the the mirror.

        ### Example 1 - Mirror in the y axis
        <!--start engscript-doc
        from engscript import engscript as es
        from engscript.export import save_image
        -->
        ```python
        # A square
        sq = es.square([10, 10], center=False)
        ## (1,0) is normal to the y axis
        sq.mirror((1, 0))
        ```
        <!--end engscript-doc
        orig = es.square([10, 10], center=False)
        save_image([sq, orig], '../docs/api-docs/doc-images/2d_mirror1.png',
            resolution=(300, 300), grid=True, lineformats=['b-','c--'],
            showlines=[(0,0,1,0,'g',':')])
        --->
        ![](../docs/api-docs/doc-images/2d_mirror1.png)

        ### Example 2 - Mirror in the x axis
        <!--start engscript-doc
        from engscript import engscript as es
        from engscript.export import save_image
        -->
        ```python
        # A square
        sq = es.square([10, 10], center=False)
        ## (0,1) is normal to the x axis
        sq.mirror((0, 1))
        ```
        <!--end engscript-doc
        orig = es.square([10, 10], center=False)
        save_image([sq, orig], '../docs/api-docs/doc-images/2d_mirror2.png',
            resolution=(300, 300), grid=True, lineformats=['b-','c--'],
            showlines=[(0,0,0,1,'g',':')])
        --->
        ![](../docs/api-docs/doc-images/2d_mirror2.png)

        ### Example 3 - An angled mirror
        <!--start engscript-doc
        from engscript import engscript as es
        from engscript.export import save_image
        -->
        ```python
        # A square
        sq = es.square([10, 10], center=False)
        sq.mirror((3, 1))
        ```
        <!--end engscript-doc
        orig = es.square([10, 10], center=False)
        save_image([sq, orig], '../docs/api-docs/doc-images/2d_mirror3.png',
            resolution=(300, 300), grid=True, lineformats=['b-','c--'],
            showlines=[(0,0,3,1,'g',':')])
        --->
        ![](../docs/api-docs/doc-images/2d_mirror3.png)


        See also: `Sketch.reflect()`
        """
        self._cross_sec = self.cross_sec.mirror(normal)

    def reflect(self, normal: tuple[float, float]) -> None:
        """
        Mirror this sketch and union it with the original sketch.

        :param normal: a vector normal to the mirror, the mirror passes through the
            origin.

        ## Example

        In this example the green dotted line is the the mirror.

        <!--start engscript-doc
        from engscript import engscript as es
        from engscript.export import save_image
        -->
        ```python
        circ = es.circle(d=10, at=[5, 0])
        circ.reflect((3,1))
        ```
        <!--end engscript-doc
        save_image([circ], '../docs/api-docs/doc-images/2d_reflect.png',
            resolution=(300, 300), grid=True, lineformats=['b-'],
            showlines=[(0,0,3,1,'g',':')])
        --->
        ![](../docs/api-docs/doc-images/2d_reflect.png)

        See also: `Sketch.mirror()`
        """

        self._cross_sec += self.cross_sec.mirror(normal)

    def offset(
        self,
        delta: float,
        fn: int = 64,
        join_type: Literal["round", "square", "mitre", "mitre"] = "round"
    ) -> None:
        """
        Offset this sketch by a distance.

        :param delta: The distance to offset the sketch.
        :param fn: *Optional* Sets the number of line segments that make up circular joins.
            Only used if `join_type` is `round`
        :param join_type: *Optional* The type of join to use at corners. Allowed values are
            * `"round"`: After offsetting the joints are filled in with circular sections
                **Default**
            * `"square"`: After offsetting the joints are connected with lines. This gives
                each corner a "squared-off" or chamfered appearance
            * `"mitre"` or `"mitre"`: After offsetting the lines are extended to form sharp
                corners.


        ## Examples

        ### Example 1 - Simple Offset
        <!--start engscript-doc
        from engscript import engscript as es
        from engscript.export import save_image
        -->
        ```python
        # A square
        sq = es.square([10, 10], center=False)
        sq.offset(2)
        ```
        <!--end engscript-doc
        orig = es.square([10, 10], center=False)
        save_image([sq, orig], '../docs/api-docs/doc-images/2d_offset.png',
            resolution=(300, 300), grid=True, lineformats=['b-','c--'])
        --->
        ![](../docs/api-docs/doc-images/2d_offset.png)

        ### Example 2 - Offset Types
        <!--start engscript-doc
        from engscript import engscript as es
        from engscript.export import save_image
        -->
        ```python
        from copy import copy
        shape = es.square([10, 10], center=True) - es.square([10, 10], center=False)

        round_offset = copy(shape)
        round_offset.offset(2, join_type="round")

        square_offset = copy(shape)
        square_offset.offset(2, join_type="square")

        miter_offset = copy(shape)
        # Alternate spelling "mitre" creates same shape.
        miter_offset.offset(2, join_type="miter")
        ```
        <!--end engscript-doc
        save_image([round_offset, shape], '../docs/api-docs/doc-images/2d_offset-round.png',
            resolution=(300, 300), grid=True, lineformats=['b-','c--'])
        save_image([square_offset, shape], '../docs/api-docs/doc-images/2d_offset-square.png',
            resolution=(300, 300), grid=True, lineformats=['b-','c--'])
        save_image([ miter_offset, shape], '../docs/api-docs/doc-images/2d_offset- miter.png',
            resolution=(300, 300), grid=True, lineformats=['b-','c--'])
        --->

        **`round_offset`**

        ![](../docs/api-docs/doc-images/2d_offset-round.png)

        **`square_offset`**

        ![](../docs/api-docs/doc-images/2d_offset-square.png)

        **`miter_offset`:**

        ![](../docs/api-docs/doc-images/2d_offset- miter.png)

        """
        if join_type == "round":
            jt = JoinType.Round
        elif join_type == "square":
            jt = JoinType.Square
        elif join_type in {"miter", "mitre"}:
            jt = JoinType.Miter
        else:
            raise ValueError(
                f'join_type "{join_type}" unknown. Should be one of the following '
                '"round", "square", or "miter". Will also accept "mitre" as an '
                'alternative spelling.')
        self._cross_sec = self.cross_sec.offset(
            delta,
            jt,
            circular_segments=fn
        )

    def chamfer(self, length: float = 1.0) -> None:
        """
        Chamfer the corners of this sketch. **Note** that this is done
        with insetting and then offsetting the shape, may return unexpected results,
        if features are separated by less than 3x the chamfer length

        :param length: The length of the chamfer

        ## Example
        <!--start engscript-doc
        from engscript import engscript as es
        from engscript.export import save_image
        -->
        ```python
        # A square
        shape = es.square([10, 10], center=True) - es.square([10, 10], center=False)
        shape.chamfer(1.0)
        ```
        <!--end engscript-doc
        orig = es.square([10, 10], center=True) - es.square([10, 10], center=False)
        save_image([shape, orig], '../docs/api-docs/doc-images/chamfer.png',
            resolution=(300, 300), grid=True, lineformats=['b-','c--'])
        --->
        ![](../docs/api-docs/doc-images/chamfer.png)
        """
        delta = 1.5 * length
        self.offset(-delta, join_type="square")
        self.offset(2 * delta, join_type="square")
        self.offset(-delta, join_type="square")

    def fillet(self, radius: float = 1.0, fn: int = 64) -> None:
        """
        Fillet the corners of this sketch. **Note** that this is done
        with insetting and then offsetting the shape, may return unexpected results,
        if features are separated by less than 2x the fillet radius

        :param radius: The radius of the fillet
        :param fn: *Optional* Sets the number of line segments that make up fillets.

        ## Example
        <!--start engscript-doc
        from engscript import engscript as es
        from engscript.export import save_image
        -->
        ```python
        # A square
        shape = es.square([10, 10], center=True) - es.square([10, 10], center=False)
        shape.fillet(1.0)
        ```
        <!--end engscript-doc
        orig = es.square([10, 10], center=True) - es.square([10, 10], center=False)
        save_image([shape, orig], '../docs/api-docs/doc-images/fillet.png',
            resolution=(300, 300), grid=True, lineformats=['b-','c--'])
        --->
        ![](../docs/api-docs/doc-images/fillet.png)
        """
        self.offset(-radius, fn=fn)
        self.offset(2 * radius, fn=fn)
        self.offset(-radius, fn=fn)

    def save_image(self,
                   filename: str,
                   grid: bool = False,
                   resolution: tuple[int, int] = (1920, 1080),
                   lineformat: str = "b-"
                   ) -> None:
        """
        Save an image of this `Sketch`. This is a plot using matplotlib.

        :param filename: The file name to save the image to. The format of the image
            is determined by the file extension. PNG is recommended
        :param grid: Set to True to add a grid to the background of the image. Also adds
            dashed axes lines.
        :param resolution: The desired image resolution. Default: (1920, 1080)
        :param lineformat: The format of the line for the shape. Specified
            as a matplotlib format string. Default: 'b-' (a blue line).

        #Example

        <!--start engscript-doc
        from engscript import engscript as es
        -->
        ```python
        pentagon = es.circle(r=5, fn=5)
        pentagon.save_image(
            '../docs/api-docs/doc-images/sketch_save_image.png',
            grid=True,
            resolution=(600,600),
            lineformat='bo--')
        ```
        <!--end engscript-doc--->
        This generate this image:

        ![](../docs/api-docs/doc-images/sketch_save_image.png)

        See also: `engscript.export.save_image()`
        """
        save_image(
            sketches=[self],
            filename=filename,
            grid=grid,
            resolution=resolution,
            lineformats=[lineformat]
        )


def cube(
    size: _Vec3,
    center: bool | tuple[bool, bool, bool] = False,
    at: None | _Vec3 = None
) -> Solid:
    """
    Create a cube (technically a cuboid) represented as a `Solid`.

    :param size: The [x, y, z] dimensions of the cube.
    :param center: *Optional* Whether to center the cube on the origin (or `at`
        position if used).
        * `False`: cube with one corner at the origin, and far corner at (x, y, z).
           **Default**
        * `True`: cube centered at the origin
        * `[True, True, False]`: Use a list to select centering by axis.
    :param at: A vector setting the position of the of the cube.
    :return: A `Sketch` object containing a cube.

    ## Examples

    ### Example 1
    <!--start engscript-doc
    from engscript import engscript as es
    -->
    ```python
    cube1 = es.cube([10, 10, 6], False)
    ```
    <!--end engscript-doc
    cube1.scene.capture('../docs/api-docs/doc-images/cube1.png', resolution=(300, 300), axes=True)
    --->
    ![](../docs/api-docs/doc-images/cube1.png)

    ### Example 2
    <!--start engscript-doc
    from engscript import engscript as es
    -->
    ```python
    cube2 = es.cube([10, 10, 6], True)
    ```
    <!--end engscript-doc
    cube2.scene.capture('../docs/api-docs/doc-images/cube2.png', resolution=(300, 300), axes=True)
    --->
    ![](../docs/api-docs/doc-images/cube2.png)

    ### Example 3
    <!--start engscript-doc
    from engscript import engscript as es
    -->
    ```python
    cube3 = es.cube([10, 10, 6], [True, True, False])
    ```
    <!--end engscript-doc
    cube3.scene.capture('../docs/api-docs/doc-images/cube3.png', resolution=(300, 300), axes=True)
    --->
    ![](../docs/api-docs/doc-images/cube3.png)
    """

    if isinstance(center, bool):
        solid = Solid(Manifold.cube(size, center))
        set_initial_position(solid, None, at)
        return solid
    if not isinstance(center, Iterable) or len(center) != 3:
        raise TypeError(
            "centre must be a boolean or a list of three booleans")
    shift = [
        -int(center[0]) * size[0] / 2,
        -int(center[1]) * size[1] / 2,
        -int(center[2]) * size[2] / 2]
    solid = Solid(Manifold.cube(size, False).translate(shift))
    set_initial_position(solid, None, at)
    return solid


def cylinder(
    h: float,
    r: float | None = None,
    d: float | None = None,
    fn: int = 64,
    center: bool = False,
    axis: _Axis = None,
    at: None | _Vec3 = None
) -> Solid:
    """
    Create a cylinder.

    :param h: The height of the cylinder.
    :param r|d: The radius or diameter of the cylinder. One of these must be set,
        only one can be set.
    :param fn: *Optional* Sets the number of line segments that make up the circular
        face of the cylinder  **Default=64**
    :param center: *Optional* Whether to center the cylinder in the z-direction.
        * `False`: Cylinder bottom is a `z=0`, top is at `z=h`.
           **Default**
        * `True`: Cylinder bottom is a `z=-h/2`, top is at `z=h/2`.
    :param axis: This sets the axis of the cylinder.
        By default the axis is the positive z axis. Input can either be:
        * `None`: Don't adjust axis *Default*
        * An axis string (i.e. one of ["+x", "-x", "+y", "-y", "+z", "-z"])
        * A vector such as (1.0, 1.0, 1.0) setting the axial direction
    :param at: A vector setting the position of the cylinder. This translation is applied after
        any rotation from axis.
    :return: A `Solid` object containing a cylinder.

    ## Examples

    ### Example 1
    <!--start engscript-doc
    from engscript import engscript as es
    -->
    ```python
    cyl1 = es.cylinder(r=3, h=2, center=False)
    ```
    <!--end engscript-doc
    cyl1.scene.capture('../docs/api-docs/doc-images/cyl1.png', resolution=(300, 300), axes=True)
    --->
    ![](../docs/api-docs/doc-images/cyl1.png)

    ### Example 2
    <!--start engscript-doc
    from engscript import engscript as es
    -->
    ```python
    cyl2 = es.cylinder(d=3, h=2, center=True)
    ```
    <!--end engscript-doc
    cyl2.scene.capture('../docs/api-docs/doc-images/cyl2.png', resolution=(300, 300), axes=True)
    --->
    ![](../docs/api-docs/doc-images/cyl2.png)

    ### Example 3 - prism of a regular polygon
    <!--start engscript-doc
    from engscript import engscript as es
    -->
    ```python
    hex_prism = es.cylinder(d=3, h=2, fn=6, center=True)
    ```
    <!--end engscript-doc
    hex_prism.scene.capture('../docs/api-docs/doc-images/hex_prism.png', resolution=(300, 300), axes=True)
    --->
    ![](../docs/api-docs/doc-images/hex_prism.png)

    ### Example 4 - Cylinders in different orientations and positions
    <!--start engscript-doc
    from engscript import engscript as es
    from engscript.assemble import Component
    -->
    ```python
    # A Cylinder in the x-axis
    cyl_x = es.cylinder(d=3, h=10, center=False, axis="+x")
    cyl_x.set_color('green')

    # A Cylinder in the x-axis that is translated (note center is now True)
    cyl_x_tr = es.cylinder(d=3, h=10, center=True, axis="+x", at=[0, 0, 6])
    cyl_x_tr.set_color('red')


    # A Cylinder along an arbitrary axis
    cyl_arb = es.cylinder(d=3, h=10, center=True, axis=[1, -1, 1])
    cyl_arb.set_color('cyan')
    ```
    <!--end engscript-doc
    comp = Component([cyl_x, cyl_x_tr, cyl_arb])
    comp.scene.capture('../docs/api-docs/doc-images/cylinder_orientations.png',
        resolution=(300, 300), elev=15, axes=True)
    --->
    ![](../docs/api-docs/doc-images/cylinder_orientations.png)
    """

    # pylint: disable=missing-param-doc
    if r is None:
        if d is None:
            raise ValueError('r or d must be set for cylinder')
        r = d / 2
    elif d is not None:
        raise ValueError("r and d can't both be set for cylinder")
    if r <= 0:
        raise ValueError("radius of cylinder must be positive")
    if h <= 0:
        raise ValueError("height of cylinder must be positive")
    solid = Solid(Manifold.cylinder(
        height=h,
        radius_low=r,
        circular_segments=fn,
        center=center))

    set_initial_position(solid, axis, at)
    return solid


def cone(
    h: float,
    r_b: float | None = None,
    d_b: float | None = None,
    r_t: float | None = None,
    d_t: float | None = None,
    fn: int = 64,
    center: bool = False,
    axis: _Axis = None,
    at: None | _Vec3 = None
) -> Solid:
    """
    Create a cone or truncated cone.

    :param h: The height of the cone.
    :param r_b|d_b: The radius or diameter of the bottom of the cone.
        One of these must be set, only one can be set.
    :param r_t|d_t: The radius or diameter of the top of the cone.
        Only one can be set, if neither are set default is zero
    :param fn: *Optional* Sets the number of line segments that make up each
        circular face of the cone.  **Default=64**
    :param center: *Optional* Whether to center the cone in the z-direction.
        * `False`: Cone bottom is a `z=0`, top is at `z=h`.
           **Default**
        * `True`: Cone bottom is a `z=-h/2`, top is at `z=h/2`.
    :param axis: This sets the axis of the cone.
        By default the axis is the positive z axis. Input can either be:
        * `None`: Don't adjust axis *Default*
        * An axis string (i.e. one of ["+x", "-x", "+y", "-y", "+z", "-z"])
        * A vector such as (1.0, 1.0, 1.0) setting the axial direction
    :param at: A vector setting the position of the cone. This translation is applied after
        any rotation from axis.
    :return: A `Solid` object containing a cone.

    ## Examples

    ### Example 1
    <!--start engscript-doc
    from engscript import engscript as es
    -->
    ```python
    cone1 = es.cone(r_b=3, h=4, center=False)
    ```
    <!--end engscript-doc
    cone1.scene.capture('../docs/api-docs/doc-images/cone1.png', resolution=(300, 300), axes=True)
    --->
    ![](../docs/api-docs/doc-images/cone1.png)

    ### Example 2
    <!--start engscript-doc
    from engscript import engscript as es
    -->
    ```python
    cone2 = es.cone(d_b=2, d_t=3, h=2, center=True)
    ```
    <!--end engscript-doc
    cone2.scene.capture('../docs/api-docs/doc-images/cone2.png', resolution=(300, 300), axes=True)
    --->
    ![](../docs/api-docs/doc-images/cone2.png)

    ### Example 3 - a right regular hexagonal [frustum](https://en.wikipedia.org/wiki/Frustum)
    <!--start engscript-doc
    from engscript import engscript as es
    -->
    ```python
    hex_frustum = es.cone(d_b=5, d_t=2, h=2, fn=6, center=True)
    ```
    <!--end engscript-doc
    hex_frustum.scene.capture('../docs/api-docs/doc-images/hex_frustum.png',
        resolution=(300, 300), axes=True)
    --->
    ![](../docs/api-docs/doc-images/hex_frustum.png)
    """
    # pylint: disable=missing-param-doc
    if r_b is None:
        if d_b is None:
            raise ValueError('r_b or d_b must be set for cone')
        r_b = d_b / 2
    elif d_b is not None:
        raise ValueError("r_b and d_b can't both be set for cone")

    if r_t is None:
        if d_t is None:
            r_t = 0.0
        else:
            r_t = d_t / 2
    elif d_t is not None:
        raise ValueError("r_t and d_t can't both be set for cone")

    if r_b < 0:
        raise ValueError("radius of cone must be positive")
    if r_t < 0:
        raise ValueError("radius of cone must be positive")
    if h <= 0:
        raise ValueError("height of cone must be positive")

    # manifold creates a broken result for cones with zero for the bottom dimension
    # Create a flipped cone and then flip it
    if r_b == 0.0:
        if r_t == 0.0:
            raise ValueError("r_b and r_t can't both be zero")
        solid = Solid(Manifold.cylinder(
            height=h,
            radius_low=r_t,
            radius_high=r_b,
            circular_segments=fn,
            center=center))
        if not center:
            solid.translate_z(-h)
        solid.mirror_z()
        set_initial_position(solid, axis, at)
        return solid
    solid = Solid(Manifold.cylinder(
        height=h,
        radius_low=r_b,
        radius_high=r_t,
        circular_segments=fn,
        center=center))
    set_initial_position(solid, axis, at)
    return solid


def sphere(
    r: float | None = None,
    d: float | None = None,
    fn: int = 64,
    at: None | _Vec3 = None
) -> Solid:
    """
    Create a cone or truncated cone.

    :param r|d: The radius or diameter of the sphere.
        One of these must be set, only one can be set.
    :param fn: *Optional* Sets the number of line segments that make up the
        sphere.  **Default=64**
    :param at: A vector setting the position of the center of the sphere.
    :return: A `Solid` object containing a sphere.

    ## Examples

    ### Example 1
    <!--start engscript-doc
    from engscript import engscript as es
    -->
    ```python
    sphere1 = es.sphere(r=5)
    ```
    <!--end engscript-doc
    sphere1.scene.capture('../docs/api-docs/doc-images/sphere1.png', resolution=(300, 300), axes=True)
    --->
    ![](../docs/api-docs/doc-images/sphere1.png)

    ### Example 2 - roughly triangulated sphere
    <!--start engscript-doc
    from engscript import engscript as es
    -->
    ```python
    sphere2 = es.sphere(r=5, fn=10)
    ```
    <!--end engscript-doc
    sphere2.scene.capture('../docs/api-docs/doc-images/sphere2.png', resolution=(300, 300), axes=True)
    --->
    ![](../docs/api-docs/doc-images/sphere2.png)
    """
    # pylint: disable=missing-param-doc
    if r is None:
        if d is None:
            raise ValueError('r or d must be set for sphere')
        r = d / 2
    elif d is not None:
        raise ValueError("r and d can't both be set for sphere")
    if r <= 0:
        raise ValueError("radius of sphere must be positive")
    solid = Solid(Manifold.sphere(
        radius=r,
        circular_segments=fn))
    set_initial_position(solid, None, at)
    return solid


def polyhedron(points: list[_Vec3]) -> Solid:
    """
    Return a convex polyhedron from a list of points.

    :param points: the list of (x,y,z) points to form the polyhedron
        from.
    :return: The Solid containing the polyhedron

    ## Example

    <!--start engscript-doc
    from engscript import engscript as es
    -->
    ```python
    # A list of points, all corresponding to the corners of a 1x1x1 cube
    # except (1,1,1) is replaced by (1,1,2)
    points = [(0.0,0.0,0.0),
              (1.0,0.0,0.0),
              (1.0,1.0,0.0),
              (1.0,0.0,1.0),
              (1.0,1.0,2.0),
              (0.0,1.0,0.0),
              (0.0,1.0,1.0),
              (0.0,0.0,1.0)]
    shape = es.polyhedron(points)
    ```
    <!--end engscript-doc
    shape.scene.capture('../docs/api-docs/doc-images/polyhedron.png', resolution=(300, 300), axes=True)
    --->
    ![](../docs/api-docs/doc-images/polyhedron.png)

    """
    p_array = np.asarray(points, dtype="float32")
    return Solid(Manifold.hull_points(p_array))


def extrude(
    sketch: Sketch,
    h: float,
    center: bool = False,
    divisions: int = 0,
    twist: float = 0.0,
    scale_top: tuple[float, float] | None = None
) -> Solid:
    """
    Extrude a `Sketch` into a `Solid` the direction of extrusion
    is in the z-axis.

    :param sketch: The sketch to be extruded
    :param h: The height to extrude to (must be positive)
    :param center: Whether to center the extrusion in the z-direction.
        * `False`: Extrusion bottom is a `z=0`, top is at `z=h`.
           **Default**
        * `True`: Extrusion bottom is a `z=-h/2`, top is at `z=h/2`.
    :param divisions: The number divisions in the extrusion direction. This
        is most useful in conjunction with the twist parameter below.
        **Default=0**
    :param twist: The rotation of the top face relative to the bottom (in degrees,
        anti-clockwise abound the z-axis). **Default=0**
    :param scale_top: The scaling of the top face relative to the bottom. Set
        as (x scale factor, y scale factor)  **Default=(1.0, 1.0)**
    :return: A `Solid` object containing the extrusion.

    ## Examples

    ### Example 1
    <!--start engscript-doc
    from engscript import engscript as es
    -->
    ```python
    sq_with_hole = es.square((6, 6), center=True) - es.circle(d=4)
    square_doughnut = es.extrude(sq_with_hole, h=2)
    ```
    <!--end engscript-doc
    square_doughnut.scene.capture('../docs/api-docs/doc-images/square_doughnut.png',
        resolution=(300, 300), axes=True)
    --->
    ![](../docs/api-docs/doc-images/square_doughnut.png)

    ### Example 2 - twisted extrusion
    <!--start engscript-doc
    from engscript import engscript as es
    -->
    ```python
    sq_with_hole = es.square((6, 6), center=True) - es.circle(d=4)
    square_doughnut2 = es.extrude(sq_with_hole, h=2, divisions=24, twist=45)
    ```
    <!--end engscript-doc
    square_doughnut2.scene.capture('../docs/api-docs/doc-images/square_doughnut2.png',
        resolution=(300, 300), axes=True)
    --->
    ![](../docs/api-docs/doc-images/square_doughnut2.png)

    ### Example 3 - Scaling the top
    <!--start engscript-doc
    from engscript import engscript as es
    -->
    ```python
    sq_with_hole = es.square((6, 6), center=True) - es.circle(d=4)
    square_doughnut3 = es.extrude(sq_with_hole, h=2, scale_top=(0.5,1.0), center=True)
    ```
    <!--end engscript-doc
    square_doughnut3.scene.capture('../docs/api-docs/doc-images/square_doughnut3.png',
        resolution=(300, 300), axes=True)
    --->
    ![](../docs/api-docs/doc-images/square_doughnut3.png)
    """
    if scale_top is None:
        scale_top = (1.0, 1.0)
    extrusion = Solid(Manifold.extrude(
        sketch.cross_sec,
        h,
        divisions,
        twist,
        scale_top))

    if center:
        extrusion.translate_z(-h / 2)
    return extrusion


def revolve(
    sketch: Sketch,
    angle: float = 360.0,
    fn: int = 64
) -> Solid:
    """
    Revolve a `Sketch` into a `Solid`. The sketch is first projected onto the
    x-z plane. The revolution is anti-clockwise about the z-axis.

    :param sketch: The sketch to be revolved
    :param angle: The angle (in degrees) that the shape should be revolved through.
        This should be greater than 0.0 and less than or equal to 360.0.
        **Default=360.0**
    :param fn: *Optional* Sets the number of line segments that make up the
        revolution.  **Default=64**
    :return: A `Solid` object containing the revolution.

    ## Examples

    ### Example 1
    <!--start engscript-doc
    from engscript import engscript as es
    -->
    ```python
    circ = es.circle(d=4)
    circ.translate_x(10)
    ring = es.revolve(circ, angle=330)
    ```
    <!--end engscript-doc
    ring.scene.capture('../docs/api-docs/doc-images/revolve_ring.png',
        resolution=(300, 300), axes=True)
    --->
    ![](../docs/api-docs/doc-images/revolve_ring.png)

    ### Example 2
    <!--start engscript-doc
    from engscript import engscript as es
    -->
    ```python
    circ = es.circle(d=40)
    circ.translate_x(100)
    #By setting fn down to 3 the individual circular sections become clear
    bent_rod = es.revolve(circ, angle=90, fn=3)
    ```
    <!--end engscript-doc
    bent_rod.scene.capture('../docs/api-docs/doc-images/revolve_bent_rod.png',
        resolution=(300, 300), axes=True)
    --->
    ![](../docs/api-docs/doc-images/revolve_bent_rod.png)
    """
    return Solid(Manifold.revolve(
        sketch.cross_sec,
        circular_segments=fn,
        revolve_degrees=angle))


def spiral_revolve(
    sketch: Sketch,
    pitch: float,
    rotations: float = 1.0,
    fn: int = 64
) -> Solid:
    """
    Spiral revolve a `Sketch` into a `Solid` for making screw threads and other
    spiral structures such as springs. The sketch is first projected onto the
    x-z plane. The revolution is anti-clockwise about the z-axis.
    The threads are right-handed. The result can be reflected to create
    a left-handed thread.

    Note that the centre of the spiral rotation will extend from -0.75*pitch to
    (rotations-0.75)*pitch. As such cutting the thread at z=0 should produce a
    clean lead in to the thread.

    :param sketch: The sketch to be revolved
    :param pitch: The pitch of the spiral (z-distance between successive rotations)
    :param rotations: The number of complete rotations for the spiral. For example,
        rotations=2.5 would be two and a half rotations or 900 degrees.
        **Default=1.0**
    :param fn: *Optional* Sets the number of line segments that make up each rotation
        revolution.  **Default=64**
    :return: A `Solid` object containing the spiral revolution.

    ## Examples

    ### Example 1
    <!--start engscript-doc
    from engscript import engscript as es
    -->
    ```python
    trapezium = es.polygon([(5,-.5),
                            (6,-0.4),
                            (6,0.4),
                            (5,.5)])
    buttress_thread = es.spiral_revolve(trapezium, pitch=2, rotations=1.25)
    ```
    <!--end engscript-doc
    buttress_thread.scene.capture('../docs/api-docs/doc-images/buttress_thread.png',
        resolution=(300, 300), axes=True)
    --->
    ![](../docs/api-docs/doc-images/buttress_thread.png)

    ### Example 2 - Solid threaded bar
    <!--start engscript-doc
    from engscript import engscript as es
    -->
    ```python
    trapezium = es.polygon([(5,-.5),
                            (6,-0.4),
                            (6,0.4),
                            (5,.5)])
    threads = 10
    pitch = 2
    #revolve the desired thread plus 1.5 extra pitches
    threaded_bar = es.spiral_revolve(trapezium,
                                      pitch=pitch,
                                      rotations=threads+1.5)
    #cut off above and below desired thread.
    threaded_bar.trim_by_plane([0,0,1])
    threaded_bar.trim_by_plane([0,0,-1], offset=-threads*pitch)
    threaded_bar += es.cylinder(h=threads*pitch, r=5.05)
    ```
    <!--end engscript-doc
    threaded_bar.scene.capture('../docs/api-docs/doc-images/threaded_bar.png',
        resolution=(300, 300), elev=15, axes=True)
    --->
    ![](../docs/api-docs/doc-images/threaded_bar.png)

    """
    def shift(vec: npt.NDArray[np.float32]) -> None:
        theta = np.arctan2(vec[:, 0], vec[:, 1])
        vec[:, 2] -= pitch * (theta / (2 * np.pi) + 0.5)

    half_rots = int(np.floor(rotations * 2))
    extra_deg = (rotations - (half_rots) * .5) * 360
    mani = Manifold()
    if half_rots > 0:
        mani_half = Manifold.revolve(
            sketch.cross_sec,
            circular_segments=int(fn / 2),
            revolve_degrees=180)
        mani_half = mani_half.warp_batch(shift)
        mani += mani_half
        for i in range(1, half_rots):
            tr_vec = [0, 0, i * pitch / 2]
            if i % 2 == 0:
                mani += mani_half.translate(tr_vec)
            else:
                mani += mani_half.translate(tr_vec).rotate([0, 0, 180])
    if extra_deg > 1e-3:
        extra_fn = int(np.ceil(fn / extra_deg))
        mani_extra = Manifold.revolve(
            sketch.cross_sec,
            circular_segments=extra_fn,
            revolve_degrees=extra_deg)
        mani_extra = mani_extra.warp_batch(shift)
        i = half_rots
        tr_vec = [0, 0, i * pitch / 2]
        if i % 2 == 0:
            mani += mani_extra.translate(tr_vec)
        else:
            mani += mani_extra.translate(tr_vec).rotate([0, 0, 180])
    return Solid(mani)


def loft(sketches: list[Sketch], z_pos: list[float]) -> Solid:
    """
    Create a solid by lofting between a list of sketches. This only works for simple
    sketches without holes. May have unexpected results for complex shapes or sketches
    that are offset significantly in the x-y plane or

    :param sketches: The list of sketches to list between
    :param z_pos: The z-position of each sketch. This should be a list the same
        length as sketches. The list should be increasing in z.

    :return: The `Solid` resulting from the loft operation.

    ## Examples

    ### Example 1 - Top and bottom chamfers
    <!--start engscript-doc
    from engscript import engscript as es
    -->
    ```python
    from copy import copy
    shape = es.square([9,9]) - es.square([9,9], center=True)
    shape_inset = copy(shape)
    shape_inset.offset(-1, join_type="mitre")

    lofted = es.loft(
        [shape_inset, shape, shape, shape_inset],
        [0,1,8,9]
    )
    ```
    <!--end engscript-doc
    lofted.scene.capture('../docs/api-docs/doc-images/lofted-chamfer.png',
        resolution=(300, 300), elev=15, axes=True)
    --->
    ![](../docs/api-docs/doc-images/lofted-chamfer.png)

    ### Example 2 - Lofted complex shape
    <!--start engscript-doc
    from engscript import engscript as es
    -->
    ```python
    shape = es.square([9,9]) - es.square([9,9], center=True)

    shape2 = es.circle(10)

    lofted = es.loft([shape2, shape], [0, 10])
    ```
    <!--end engscript-doc
    lofted.scene.capture('../docs/api-docs/doc-images/lofted-complex.png',
        resolution=(300, 300), axes=True)
    --->
    ![](../docs/api-docs/doc-images/lofted-complex.png)

    """
    n_sketch = len(sketches)
    if len(z_pos) != n_sketch:
        raise ValueError("List of z positions must be same length as list of sketches "
                         "for loft operation.")
    if len(sketches) < 2:
        raise ValueError("Expecting at least two sketches for loft operation")
    if len(sketches) > 2:
        ret = loft([sketches[0], sketches[1]], [z_pos[0], z_pos[1]])
        for i in range(1, len(sketches) - 1):
            ret += loft([sketches[i], sketches[i + 1]], [z_pos[i], z_pos[i + 1]])
        return ret

    if z_pos[1] <= z_pos[0]:
        raise ValueError("z positions must increase for loft operations")
    poly_a = sketches[0].cross_sec.to_polygons()
    poly_b = sketches[1].cross_sec.to_polygons()
    if len(poly_a) != 1 or len(poly_b) != 1:
        raise ValueError("Loft operation only possible on simple polygons")

    # Add z values using pad
    verts_a = np.pad(poly_a[0], [[0, 0], [0, 1]], constant_values=z_pos[0])
    verts_b = np.pad(poly_b[0], [[0, 0], [0, 1]], constant_values=z_pos[1])

    n_verts_a = verts_a.shape[0]

    # Triangulate bottom and flip normals
    tris1 = triangulate(poly_a)
    tmp = tris1[:, 1].copy()
    tris1[:, 1] = tris1[:, 2]
    tris1[:, 2] = tmp

    # Triangulate top and increase indices
    tris2 = triangulate(poly_b)
    tris2 += n_verts_a

    pairings = polygon_pair_indices(verts_a, verts_b)
    pairings = [(i_a, i_b + n_verts_a) for i_a, i_b in pairings]

    # build the skirt faces
    tris3: Any = []
    for n, (i_a, i_b) in enumerate(pairings):
        prev_i_a, prev_i_b = pairings[n - 1]
        if i_a != prev_i_a:
            tris3 += [[prev_i_a, i_a, prev_i_b]]
        if i_b != prev_i_b:
            tris3 += [[i_a, i_b, prev_i_b]]
    tris3 = np.array(tris3)

    verts = np.concatenate((verts_a, verts_b))
    tris = np.concatenate((tris1, tris2, tris3))
    return Solid(Manifold(Mesh(verts, tris)))


def surface(
    height_map: list[list[float]] | npt.NDArray[np.float32 | np.float64]
) -> Solid:
    """
    Create a solid with stop surface given by a height map

    :param height_map: The height map for the top surface
    :return: Solid x and y dimensions are equal to the x and y size of the input
        array. The top surface is set by the input height map. The bottoms surface is
        1mm lower than the lowest point on the height map.

    ### Example
    <!--start engscript-doc
    from engscript import engscript as es
    -->
    ```python
    import numpy as np
    xs, ys = np.meshgrid(
        np.linspace(0,2*3.1415*4, 160),
        np.linspace(0,2*3.1415*6, 240),
        indexing='xy')

    h_map = 10*(2+np.sin(xs)+np.sin(ys))
    surf = es.surface(h_map)

    ```
    <!--end engscript-doc
    surf.scene.capture('../docs/api-docs/doc-images/surface.png',
        resolution=(300, 300), axes=True)
    --->
    ![](../docs/api-docs/doc-images/surface.png)

    """
    if not isinstance(height_map, np.ndarray):
        height_map = np.asarray(height_map)
    if height_map.dtype != np.float32:
        height_map = height_map.astype('float32')
    w, h = height_map.shape
    mini = np.min(height_map)

    def warp_to_surface(vec: npt.NDArray[np.float32]) -> None:
        ind_x = np.full(vec.shape, False, bool)
        ind_y = np.copy(ind_x)
        ind_z = np.copy(ind_x)
        ind_z[:, 2] = vec[:, 2] >= mini
        ind_y[:, 1] = ind_z[:, 2]
        ind_x[:, 0] = ind_z[:, 2]
        x_coord = np.round(vec[ind_x]).astype(int)
        y_coord = np.round(vec[ind_y]).astype(int)
        vec[ind_z] = height_map[x_coord, y_coord]

    xs = list(range(w)) + list(range(w - 1, -1, -1))
    ys = [0] * w + [1] * w
    points = [(float(x), float(y)) for x, y in zip(xs, ys)]
    solid = extrude(polygon(points), h - 1, divisions=h - 2)
    solid.rotate_x(-90)
    solid.translate_z(float(mini))

    solid.warp(warp_to_surface)
    return solid


def projection(solid: Solid, axis: _Axis = None) -> Sketch:
    """
    Return a 2D sketch of the input solid projected along the
    input axis (or z-axis is not specified).

    :param solid: The Solid to be projected
    :param axis: The projection axis

    ## Example

    <!--start engscript-doc
    from engscript import engscript as es
    from engscript.export import save_image
    -->
    ```python
    #create a cube with a hole through the centre
    shape = es.cube([10, 10, 15], center=True)
    shape -= es.cylinder(r=3, h=11, center=True)

    #Projection in z is blue
    projection_z = es.projection(shape)
    #Projection in x is green
    projection_x = es.projection(shape, "+x")
    #Projection in 111 is red
    projection_111 = es.projection(shape, [1, 1, 1])

    ```
    <!--end engscript-doc
    save_image([projection_z, projection_x, projection_111],
        '../docs/api-docs/doc-images/projection.png', resolution=(300, 300),
        grid=True, lineformats=['b-','g-','r-'])
    --->
    ![](../docs/api-docs/doc-images/projection.png)

    See also `cross_section`
    """
    if axis is not None:
        solid = copy(solid)
        solid.align_a_to_b(axis_to_uvec(axis), (0.0, 0.0, 1.0))
    return Sketch(solid.manifold.project())


def cross_section(solid: Solid, normal: _Axis = None, offset: float = 0.0,) -> Sketch:
    """
    Return a 2D sketch of a cross-section through the input solid. The plane is
    normal to the input vector (default is z-axis, i.e. the x-y plane). And offset by
    the given value

    :param solid: The Solid to be sectioned
    :param normal: A vector normal to the sectioning plane (can be an axis string
        such as `"+x"` or `"-y"`)
    :param offset: The offset of the sectioning plane in the normal direction

    ## Example

    <!--start engscript-doc
    from engscript import engscript as es
    from engscript.export import save_image
    -->
    ```python
    #create a cube with a hole through the centre
    shape = es.cube([10, 10, 15], center=True)
    shape -= es.cylinder(r=3, h=11, center=True)

    #Section in z is blue
    cross_section_z = es.cross_section(shape)
    #Section in x is green
    cross_section_x = es.cross_section(shape, normal="+x")
    #Section in 111 is red
    cross_section_111 = es.cross_section(shape, normal=[1, 1, 1])

    #Section in z is dashed cyan when offset by 4
    cross_section_z_off4 = es.cross_section(shape, offset=4)
    #Section in x is dashed yellow when offset by 4
    cross_section_x_off4 = es.cross_section(shape, normal="+x", offset=4)
    #Section in 111 is dashed magenta when offset by 4
    cross_section_111_off4 = es.cross_section(shape, normal=[1, 1, 1], offset=4)

    ```
    <!--end engscript-doc
    save_image([cross_section_z, cross_section_x, cross_section_111,
                cross_section_z_off4, cross_section_x_off4, cross_section_111_off4],
        '../docs/api-docs/doc-images/cross_section.png', resolution=(300, 300),
        grid=True, lineformats=['b-','g-','r-','c--','y--','m--'])
    --->
    ![](../docs/api-docs/doc-images/cross_section.png)

    See also `projection`
    """
    if normal is not None:
        solid = copy(solid)
        solid.align_a_to_b(axis_to_uvec(normal), (0.0, 0.0, 1.0))
    return Sketch(solid.manifold.slice(offset))


def split_by_plane(
    solid: Solid,
    normal: _Axis = (0.0, 0.0, 1.0),
    offset: float = 0.0
) -> list[Solid]:
    """
    Split a solid in two along a plane

    :param solid: The Solid to be split
    :param normal: A vector normal to the splitting plane (can be an axis string
        such as `"+x"` or `"-y"`) **Default=(0.0, 0.0, 1.0)**
    :param offset: Offset of the plane from the origin (in direction of normal)
        **Default=0.0**

    :return: A list two `Solid` object one each side of the plane. The first solid is
    be on the side of the plane defined by the normal.

    ### Example
    <!--start engscript-doc
    from engscript import engscript as es
    from engscript.assemble import Component
    -->
    ```python
    # Make a cube (centred in x and y only)
    cube = es.cube([10,10,10], [True, True, False])
    # And a sphere centered in that cube
    sphere = es.sphere(d=7)
    sphere.translate_z(5)
    #subtract the sphere from the cube
    cube -= sphere
    #split along the y-z plane
    halves = es.split_by_plane(cube, normal=(1,0,0))
    #Rotate one half by 90 degrees to show they are split
    halves[0].rotate_y(90)
    ```
    <!--end engscript-doc
    comp = Component(halves)
    comp.scene.capture('../docs/api-docs/doc-images/split_by_plane.png',
        resolution=(300, 300), axes=True)
    --->
    ![](../docs/api-docs/doc-images/split_by_plane.png)

    See also `Solid.trim_by_plane`
    """
    normal = axis_to_uvec(normal)
    manifolds = solid.manifold.split_by_plane(normal, offset)
    return [Solid(m) for m in manifolds]


def hull(solids: list[Solid]) -> Solid:
    """
    Returns the convex hull of a list of Solids

    :param solids: The list Solid objects to be hulled
    :return: A `Solid` object containing the hulled shape.

    ### Example
    <!--start engscript-doc
    from engscript import engscript as es
    -->
    ```python
    balls = []
    locations = [(10,10,0),
                 (-10,10,0),
                 (-10,-10,0),
                 (10,-10,0)]
    for loc in locations:
        balls.append(es.sphere(r=3, at=loc))

    hulled = es.hull(balls)

    ```
    <!--end engscript-doc
    hulled.scene.capture('../docs/api-docs/doc-images/hull_balls.png',
        resolution=(300, 300), axes=True)
    --->
    ![](../docs/api-docs/doc-images/hull_balls.png)

    """
    manifolds = [s.manifold for s in solids]
    return Solid(Manifold.hull(Manifold.compose(manifolds)))


def sequential_hull(solids: list[Solid]) -> Solid:
    """
    Returns convex hull of sequential pairs in a list of solids.
    For example given a lists of four solids, this will return the
    Union of: the hull of solid 1 and solid 2, the hull of solid 2
    and solid 3, and the hull of solid 3 and solid 4

    :param solids: The list Solid objects to be hulled
    :return: A `Solid` object containing the sequentially hulled shape.

    ### Example
    <!--start engscript-doc
    from engscript import engscript as es
    -->
    ```python
    balls = []
    locations = [(10,10,0),
                 (-10,10,0),
                 (-10,-10,0),
                 (10,-10,0)]
    for loc in locations:
        balls.append(es.sphere(r=3, at=loc))

    seq_hulled = es.sequential_hull(balls)

    ```
    <!--end engscript-doc
    seq_hulled.scene.capture('../docs/api-docs/doc-images/seq_hull_balls.png',
        resolution=(300, 300), axes=True)
    --->
    ![](../docs/api-docs/doc-images/seq_hull_balls.png)

    """
    if len(solids) == 0:
        raise ValueError("Must be at least one solid to perform sequential_hull")
    if len(solids) == 1:
        return copy(solids[0])

    for i in range(len(solids) - 1):
        manifolds = [solids[i].manifold, solids[i + 1].manifold]
        if i == 0:
            output = Solid(Manifold.hull(Manifold.compose(manifolds)))
        else:
            output += Solid(Manifold.hull(Manifold.compose(manifolds)))
    return output


class Solid:
    """
    This is the main class for creating an manipulating 3D shapes in EngScript.

    ## Creating a `Solid`
    Solids can be created as primitive shapes using functions such as `sphere()`,
    `cube()`, `cylinder()`, and `cone()`.  You can also create a `Solid` from a
    `Sketch` with functions such as `extrude()`, `revolve()`, `spiral_revolve()`.

    Creating Sketch objects directly with `Solid(manifold)` requires interacting
    with the underlying [`manifold3d`](https://pypi.org/project/manifold3d/). You
    shouldn't need to do this unless you are doing something special that we don't
    support yet!

    ## Manipulating solids

    ### Transforming a specific `Solid`

    A `Solid` object can be modified with transforms such as:
    * Translation with `translate()`, or derivatives such as `translate_x()`,
        `translate_y()`, `translate_z()`
    * Rotation with `rotate_x()`, `rotate_y()`, `rotate_z()`. There is currently
       no arbitrary 3D rotate function.
    * Scaling with `scale()`
    * Mirroring with `mirror()` (or `mirror_x()`, `mirror_y()`, `mirror_z()`) to
       return only the mirrored object. To return the Union of both the original
       and mirrored object use `reflect()` (or `reflect_x()`, `reflect_y()`,
       `reflect_z()`)

    These modifications modify the existing `Solid`:
    ```python
    #create a cube called my_cube
    my_cube = es.cube([10.0, 10.0, 10.0], center=True)
    #my_cube is now a Solid representing a cube centered at the origin

    my_cube.translate_y(10.0)
    #my_cube is a Solid representing a cube centered at (0, 10, 0)
    ```
    More information on these transformations are below.

    ### Combining solids

    The key way to combine solids is with the `+`, `-`, and `&` operators:

    For example taking the following code:
    <!--start engscript-doc
    from engscript import engscript as es
    -->
    ```python
    # A cube centred at the origin
    my_cube = es.cube([10.0, 10.0, 10.0], center=True)
    #A second cube with the centre of one vertical edge at the origin
    my_other_cube = es.cube([10.0, 10.0, 10.0], center=[False, False, True])

    # The union of the two cubes
    solid_union = my_cube + my_other_cube

    # The difference of the two cubes
    solid_diff = my_cube - my_other_cube

    # The intersection of the two cubes
    solid_inter = my_cube & my_other_cube
    ```
    <!--end engscript-doc
    solid_union.scene.capture('../docs/api-docs/doc-images/solid_union.png',
        resolution=(300, 300), axes=True)
    solid_diff.scene.capture('../docs/api-docs/doc-images/solid_diff.png',
        resolution=(300, 300), axes=True)
    solid_inter.scene.capture('../docs/api-docs/doc-images/solid_inter.png',
        resolution=(300, 300), axes=True)
    -->
    The resulting solids would be

    **`solid_union`**

    ![](../docs/api-docs/doc-images/solid_union.png)

    **`solid_diff`**

    ![](../docs/api-docs/doc-images/solid_diff.png)

    **`solid_inter`:**

    ![](../docs/api-docs/doc-images/solid_inter.png)

    Solids can also be combined with functions such as `hull()` or
    `sequential_hull()`.


    """

    def __init__(self, manifold: Manifold) -> None:
        """

        Creating a solid with this constructor is not recommended. To
        do so you will need to work with the underlying
        [`manifold3d`](https://pypi.org/project/manifold3d/) kernel. Instead
        it is recommended you use functions such as `sphere()`, `cube()`,
        `cylinder()`, and `cone()`. Or to create a `Solid` from a `Sketch` with
        functions such as `extrude()`, `revolve()`, `spiral_revolve()`.

        :param manifold: A `manifold3d.Manifold` object of the desired 3D
            geometry.

        """
        self._manifold = manifold

    @property
    def manifold(self) -> Manifold:
        """
        Read only property that returns the underlying `manifold3d.Manifold`
        object holding the 3D geometry.

        For normal use cases you shouldn't need to access this directly.
        """
        return self._manifold

    def __add__(self, other: Solid) -> Solid:
        return Solid(self.manifold + other.manifold)

    def __sub__(self, other: Solid) -> Solid:
        return Solid(self.manifold - other.manifold)

    def __and__(self, other: Solid) -> Solid:
        return Solid(self.manifold ^ other.manifold)

    @property
    def bounding_box(self) -> _Vec6:
        """
        Get the axis aligned bounding box of the solid.
        This is a tuple of 6 floats.

        The order is x_min, y_min, z_min, x_max, y_max, z_max
        """
        bbox: _Vec6 = self.manifold.bounding_box()
        return bbox

    @property
    def bounding_box_corners(self) -> tuple[
        _Vec3,
        _Vec3,
        _Vec3,
        _Vec3,
        _Vec3,
        _Vec3,
        _Vec3,
        _Vec3
    ]:
        """
        Get the corners of the axis aligned bounding box of the solid.

        Return a tuple containing eight tuples of (x,y,z) coordinates.
        """
        x_min, y_min, z_min, x_max, y_max, z_max = self.bounding_box
        return ((x_min, y_min, z_min),
                (x_min, y_min, z_max),
                (x_min, y_max, z_min),
                (x_min, y_max, z_max),
                (x_max, y_min, z_min),
                (x_max, y_min, z_max),
                (x_max, y_max, z_min),
                (x_max, y_max, z_max))

    @property
    def x_min(self) -> float:
        """
        Get the furthest extent of this solid in the negative x-direction
        """
        return self.bounding_box[0]

    @property
    def y_min(self) -> float:
        """
        Get the furthest extent of this solid in the negative y-direction
        """
        return self.bounding_box[1]

    @property
    def z_min(self) -> float:
        """
        Get the furthest extent of this solid in the negative z-direction
        """
        return self.bounding_box[2]

    @property
    def x_max(self) -> float:
        """
        Get the furthest extent of this solid in the positive x-direction
        """
        return self.bounding_box[3]

    @property
    def y_max(self) -> float:
        """
        Get the furthest extent of this solid in the positive y-direction
        """
        return self.bounding_box[4]

    @property
    def z_max(self) -> float:
        """
        Get the furthest extent of this solid in the positive z-direction
        """
        return self.bounding_box[5]

    @property
    def num_vert(self) -> int:
        """
        Get the number of vertices in the mesh
        """
        return self.manifold.num_vert()  # type: ignore[no-any-return]

    @property
    def num_edge(self) -> int:
        """
        Get the number of edges in the mesh
        """
        return self.manifold.num_edge()  # type: ignore[no-any-return]

    @property
    def num_tri(self) -> int:
        """
        Get the number of edges in the mesh
        """
        return self.manifold.num_tri()  # type: ignore[no-any-return]

    def translate(self, xyz: _Vec3) -> None:
        """
        Translate this solid in by a 3D vector.

        :param xyz: The (x,y,z) vector for translation.

        ## Example
        <!--start engscript-doc
        from engscript import engscript as es
        -->
        ```python
        # A cube with the bottom left corner at the origin
        cube1 = es.cube([10, 10, 10], center=False)
        cube1.translate([15, 0, 5])
        ```
        <!--end engscript-doc
        cube1.scene.capture('../docs/api-docs/doc-images/translate_solid.png',
            distance_ratio=2, resolution=(300, 300), axes=True)
        --->
        ![](../docs/api-docs/doc-images/translate_solid.png)

        See also: `Solid.translate_x()`, `Solid.translate_y()`, and
        `Solid.translate_z()`
        """
        self._manifold = self.manifold.translate(xyz)

    def translate_x(self, x: float) -> None:
        """
        Translate the solid in only the x-direction.

        :param x: The distance to translate in x.

        See also: `Solid.translate()`, `Solid.translate_y()`, and
        `Solid.translate_z()`
        """
        self._manifold = self.manifold.translate([x, 0, 0])

    def translate_y(self, y: float) -> None:
        """
        Translate the solid in only the y-direction.

        :param y: The distance to translate in y.

        See also: `Solid.translate()`, `Solid.translate_x()`, and
        `Solid.translate_z()`
        """
        self._manifold = self.manifold.translate([0, y, 0])

    def translate_z(self, z: float) -> None:
        """
        Translate the solid in only the z-direction.

        :param z: The distance to translate in z.

        See also: `Solid.translate()`, `Solid.translate_x()`, and
        `Solid.translate_y()`
        """
        self._manifold = self.manifold.translate([0, 0, z])

    def rotate_x(self, angle: float) -> None:
        """
        Rotate this `Solid` about the x-axis.

        :param angle: The angle in degrees to rotate by. Rotations are
            anti-clockwise about the x-axis

        ## Example
        <!--start engscript-doc
        from engscript import engscript as es
        -->
        ```python
        # A cube with the bottom left corner at the origin
        my_cube = es.cube([10, 10, 10], center=False)
        my_cube.rotate_x(45)
        ```
        <!--end engscript-doc
        my_cube.scene.capture('../docs/api-docs/doc-images/rotate_x_solid.png',
            distance_ratio=2, resolution=(300, 300), axes=True)
        --->
        ![](../docs/api-docs/doc-images/rotate_x_solid.png)

        See also: `engscript.Solid.rotate_y`, `engscript.Solid.rotate_z`, and
        `engscript.Solid.align_a_to_b`

        **Note:** Currently there is no arbitrary 3D rotation function. It is
        unclear how best to specify this. Euler angles (in which convention!),
        rotation axis and angle, quaternions.
        """
        self._manifold = self.manifold.rotate((float(angle), 0.0, 0.0))

    def rotate_y(self, angle: float) -> None:
        """
        Rotate this `Solid` about the y-axis.

        :param angle: The angle in degrees to rotate by. Rotations are
            anti-clockwise about the y-axis

        ## Example
        <!--start engscript-doc
        from engscript import engscript as es
        -->
        ```python
        # A cube with the bottom left corner at the origin
        my_cube = es.cube([10, 10, 10], center=False)
        my_cube.rotate_y(45)
        ```
        <!--end engscript-doc
        my_cube.scene.capture('../docs/api-docs/doc-images/rotate_y_solid.png',
            distance_ratio=2, resolution=(300, 300), axes=True)
        --->
        ![](../docs/api-docs/doc-images/rotate_y_solid.png)

        See also: `engscript.Solid.rotate_x`, `engscript.Solid.rotate_z`, and
        `engscript.Solid.align_a_to_b`

        **Note:** Currently there is no arbitrary 3D rotation function. It is
        unclear how best to specify this. Euler angles (in which convention!),
        rotation axis and angle, quaternions.
        """
        self._manifold = self.manifold.rotate((0.0, float(angle), 0.0))

    def rotate_z(self, angle: float) -> None:
        """
        Rotate this `Solid` about the z-axis.

        :param angle: The angle in degrees to rotate by. Rotations are
            anti-clockwise about the z-axis

        ## Example
        <!--start engscript-doc
        from engscript import engscript as es
        -->
        ```python
        # A cube with the bottom left corner at the origin
        my_cube = es.cube([10, 10, 10], center=False)
        my_cube.rotate_z(45)
        ```
        <!--end engscript-doc
        my_cube.scene.capture('../docs/api-docs/doc-images/rotate_z_solid.png',
            distance_ratio=2, resolution=(300, 300), axes=True)
        --->
        ![](../docs/api-docs/doc-images/rotate_z_solid.png)

        See also: `engscript.Solid.rotate_x`, `engscript.Solid.rotate_y`, and
        `engscript.Solid.align_a_to_b`

        **Note:** Currently there is no arbitrary 3D rotation function. It is
        unclear how best to specify this. Euler angles (in which convention!),
        rotation axis and angle, quaternions. `engscript.Solid.align_a_to_b` is
        the function best able to do arbitrary rotations.
        """

        self._manifold = self.manifold.rotate((0.0, 0.0, float(angle)))

    def align_a_to_b(self, vec1: _Vec3, vec2: _Vec3) -> None:
        """
        Rotate this solid through the rotation that would align one vector
        with a second.

        :param vec1: The vector in the Solid's current position.
        :param vec2: The desired direction of vec1 once rotated.

        # Example
        <!--start engscript-doc
        from engscript import engscript as es
        -->
        ```python
        # A cube with the bottom left corner at the origin
        my_cube = es.cube([10, 10, 10], center=False)
        #Rotate so that the [1,1,1] direction becomes the z_axis
        my_cube.align_a_to_b([1,1,1], [0,0,1])
        ```
        <!--end engscript-doc
        my_cube.scene.capture('../docs/api-docs/doc-images/align_a_to_b.png',
            distance_ratio=2, resolution=(300, 300), axes=True)
        --->
        ![](../docs/api-docs/doc-images/align_a_to_b.png)
        """
        self.transform(alignment_matrix(vec1, vec2))

    def scale(self, factor: float | _Vec3) -> None:
        """
        Scale this solid by a fixed factor or a 3D vector.

        :param factor: The scaling factor. To scale differently in x,y, and z you can
            enter a list or tuple of (x,y,z) scaling factors.

        ## Examples

        ##Example1
        <!--start engscript-doc
        from engscript import engscript as es
        from engscript.assemble import Component
        -->
        ```python
        from copy import copy
        # A cube with the bottom left corner at the origin
        cube1 = es.cube([10, 10, 10], center=False)
        cube2 = copy(cube1)
        cube2.scale(3)
        cube2.translate_x(30)
        ```
        <!--end engscript-doc
        comp = Component([cube1, cube2])
        comp.scene.capture('../docs/api-docs/doc-images/scale_solid.png',
            resolution=(300, 300), axes=True)
        --->
        ![](../docs/api-docs/doc-images/scale_solid.png)

        ##Example2
        <!--start engscript-doc
        from engscript import engscript as es
        from engscript.assemble import Component
        -->
        ```python
        from copy import copy
        # A cube with the bottom left corner at the origin
        cube1 = es.cube([10, 10, 10], center=False)
        cube2 = copy(cube1)
        cube2.scale([3, .5, 1])
        cube2.translate_x(30)
        ```
        <!--end engscript-doc
        comp = Component([cube1, cube2])
        comp.scene.capture('../docs/api-docs/doc-images/scale_solid2.png',
            resolution=(300, 300), axes=True)
        --->
        ![](../docs/api-docs/doc-images/scale_solid2.png)

        """
        if not isinstance(factor, Iterable):
            factor = (factor, factor, factor)
        self._manifold = self.manifold.scale(factor)

    def mirror(self, normal: _Axis) -> None:
        """
        Mirror this solid. The new solid replaces the old. To keep both the original
        and mirrored, see `Solid.reflect()`

        :param normal: a vector normal to the mirror, the mirror passes through the
            origin  (can be an axis string such as `"+x"` or `"-y"`).

        ## Example

        <!--start engscript-doc
        from engscript import engscript as es
        from engscript.assemble import Component
        -->
        ```python
        from copy import copy
        # A cube with the bottom left corner at the origin
        cone1 = es.cone(h=10, r_b=0, r_t=5)
        cone2 = copy(cone1)
        cone2.mirror([1, 1, 1])

        # Original is cyan
        cone1.set_color('cyan')
        # Mirrored is Blue
        cone2.set_color('blue')
        ```
        <!--end engscript-doc
        comp = Component([cone1, cone2])
        comp.scene.capture('../docs/api-docs/doc-images/mirror_solid_xyz.png',
            resolution=(300, 300), axes=True)
        --->
        ![](../docs/api-docs/doc-images/mirror_solid_xyz.png)

        See also: `engscript.Solid.mirror_x()`, `engscript.Solid.mirror_y()`,
        `engscript.Solid.mirror_z()`, and `engscript.Solid.reflect()`
        """
        normal = axis_to_uvec(normal)
        self._manifold = self.manifold.mirror(normal)

    def mirror_x(self) -> None:
        """
        Mirror this solid in the x-direction. The new solid replaces the old.
        To keep both the original and mirrored, see `Solid.reflect_x()`

        ## Example

        <!--start engscript-doc
        from engscript import engscript as es
        from engscript.assemble import Component
        -->
        ```python
        from copy import copy
        # A cube with the bottom left corner at the origin
        sphere1 = es.sphere(r=5)
        sphere1.translate_x(10)
        sphere2 = copy(sphere1)
        sphere2.mirror_x()

        # Original is cyan
        sphere1.set_color('cyan')
        # Mirrored is Blue
        sphere2.set_color('blue')
        ```
        <!--end engscript-doc
        comp = Component([sphere1, sphere2])
        comp.scene.capture('../docs/api-docs/doc-images/mirror_solid_x.png',
            resolution=(300, 300), axes=True)
        --->
        ![](../docs/api-docs/doc-images/mirror_solid_x.png)

        See also: `engscript.Solid.mirror()`, `engscript.Solid.mirror_y()`,
        `engscript.Solid.mirror_z()`, and `engscript.Solid.reflect_x()`
        """
        self._manifold = self.manifold.mirror([1, 0, 0])

    def mirror_y(self) -> None:
        """
        Mirror this solid in the y-direction. The new solid replaces the old.
        To keep both the original and mirrored, see `Solid.reflect_y()`

        ## Example

        <!--start engscript-doc
        from engscript import engscript as es
        from engscript.assemble import Component
        -->
        ```python
        from copy import copy
        # A cube with the bottom left corner at the origin
        sphere1 = es.sphere(r=5)
        sphere1.translate_y(10)
        sphere2 = copy(sphere1)
        sphere2.mirror_y()

        # Original is cyan
        sphere1.set_color('cyan')
        # Mirrored is Blue
        sphere2.set_color('blue')
        ```
        <!--end engscript-doc
        comp = Component([sphere1, sphere2])
        comp.scene.capture('../docs/api-docs/doc-images/mirror_solid_y.png',
            resolution=(300, 300), axes=True)
        --->
        ![](../docs/api-docs/doc-images/mirror_solid_y.png)

        See also: `engscript.Solid.mirror()`, `engscript.Solid.mirror_x()`,
        `engscript.Solid.mirror_z()`, and `engscript.Solid.reflect_y()`
        """
        self._manifold = self.manifold.mirror([0, 1, 0])

    def mirror_z(self) -> None:
        """
        Mirror this solid in the z-direction. The new solid replaces the old.
        To keep both the original and mirrored, see `Solid.reflect_z()`

        ## Example

        <!--start engscript-doc
        from engscript import engscript as es
        from engscript.assemble import Component
        -->
        ```python
        from copy import copy
        # A cube with the bottom left corner at the origin
        sphere1 = es.sphere(r=5)
        sphere1.translate_z(10)
        sphere2 = copy(sphere1)
        sphere2.mirror_z()

        # Original is cyan
        sphere1.set_color('cyan')
        # Mirrored is Blue
        sphere2.set_color('blue')
        ```
        <!--end engscript-doc
        comp = Component([sphere1, sphere2])
        comp.scene.capture('../docs/api-docs/doc-images/mirror_solid_z.png',
            resolution=(300, 300), axes=True)
        --->
        ![](../docs/api-docs/doc-images/mirror_solid_z.png)

        See also: `engscript.Solid.mirror()`, `engscript.Solid.mirror_x()`,
        `engscript.Solid.mirror_y()`, and `engscript.Solid.reflect_z()`
        """
        self._manifold = self.manifold.mirror([0, 0, 1])

    def reflect(self, normal: _Axis) -> None:
        """
        Mirror this solid and union it with the original solid. To simply create a
        new `Solid` that replaces the original, see `Solid.mirror()`

        :param normal: a vector normal to the mirror, the mirror passes through the
            origin (can be an axis string such as `"+x"` or `"-y"`).

        ## Example

        <!--start engscript-doc
        from engscript import engscript as es
        from engscript.assemble import Component
        -->
        ```python
        from copy import copy
        # A cube with the bottom left corner at the origin
        double_sphere = es.sphere(r=5)
        double_sphere.translate_z(3)
        double_sphere.reflect([1,1,1])

        ```
        <!--end engscript-doc
        double_sphere.scene.capture('../docs/api-docs/doc-images/reflect_solid_xyz.png',
            resolution=(300, 300), axes=True)
        --->
        ![](../docs/api-docs/doc-images/reflect_solid_xyz.png)

        See also: `engscript.Solid.reflect_x()`, `engscript.Solid.reflect_y()`,
        `engscript.Solid.reflect_z()`, and `engscript.Solid.mirror()`
        """
        normal = axis_to_uvec(normal)
        self._manifold += self.manifold.mirror(normal)

    def reflect_x(self) -> None:
        """
        Mirror this solid in the x-direction and union it with the original solid.
        To simply create a new `Solid` that replaces the original, see
        `Solid.mirror_x()`

        ## Example

        <!--start engscript-doc
        from engscript import engscript as es
        from engscript.assemble import Component
        -->
        ```python
        from copy import copy
        # A cube with the bottom left corner at the origin
        double_sphere = es.sphere(r=5)
        double_sphere.translate_x(3)
        double_sphere.reflect_x()

        ```
        <!--end engscript-doc
        double_sphere.scene.capture('../docs/api-docs/doc-images/reflect_solid_x.png',
            resolution=(300, 300), axes=True)
        --->
        ![](../docs/api-docs/doc-images/reflect_solid_x.png)

        See also: `engscript.Solid.reflect()`, `engscript.Solid.reflect_y()`,
        `engscript.Solid.reflect_z()`, and `engscript.Solid.mirror_x()`
        """
        self._manifold += self.manifold.mirror([1, 0, 0])

    def reflect_y(self) -> None:
        """
        Mirror this solid in the y-direction and union it with the original solid.
        To simply create a new `Solid` that replaces the original, see
        `Solid.mirror_y()`

        ## Example

        <!--start engscript-doc
        from engscript import engscript as es
        from engscript.assemble import Component
        -->
        ```python
        from copy import copy
        # A cube with the bottom left corner at the origin
        double_sphere = es.sphere(r=5)
        double_sphere.translate_y(3)
        double_sphere.reflect_y()

        ```
        <!--end engscript-doc
        double_sphere.scene.capture('../docs/api-docs/doc-images/reflect_solid_y.png',
            resolution=(300, 300), axes=True)
        --->
        ![](../docs/api-docs/doc-images/reflect_solid_y.png)

        See also: `engscript.Solid.reflect()`, `engscript.Solid.reflect_x()`,
        `engscript.Solid.reflect_z()`, and `engscript.Solid.mirror_y()`
        """
        self._manifold += self.manifold.mirror([0, 1, 0])

    def reflect_z(self) -> None:
        """
        Mirror this solid in the z-direction and union it with the original solid.
        To simply create a new `Solid` that replaces the original, see
        `Solid.mirror_z()`

        ## Example

        <!--start engscript-doc
        from engscript import engscript as es
        from engscript.assemble import Component
        -->
        ```python
        from copy import copy
        # A cube with the bottom left corner at the origin
        double_sphere = es.sphere(r=5)
        double_sphere.translate_z(3)
        double_sphere.reflect_z()

        ```
        <!--end engscript-doc
        double_sphere.scene.capture('../docs/api-docs/doc-images/reflect_solid_z.png',
            resolution=(300, 300), axes=True)
        --->
        ![](../docs/api-docs/doc-images/reflect_solid_z.png)

        See also: `engscript.Solid.reflect()`, `engscript.Solid.reflect_x()`,
        `engscript.Solid.reflect_y()`, and `engscript.Solid.mirror_z()`
        """
        self._manifold += self.manifold.mirror([0, 0, 1])

    def transform(self, matrix: list[list[float]] | npt.NDArray[Any]) -> None:
        """
        Transform this solid using an arbitrary transformation matrix.

        :param matrix: The transformation matrix. This can be a 3x3 transformation
            matrix, a 4x4 affine transformation matrix. Or a 3x4 matrix representing
            the top 3 rows of an affine transformation matrix with the final fixed
            line omitted.
        """
        if not isinstance(matrix, np.ndarray):
            matrix = np.asarray(matrix)
        if matrix.dtype != np.float32:
            matrix = matrix.astype('float32')
        if matrix.shape == (4, 4):
            # pylint: disable=consider-using-assignment-expr
            final_row = tuple(float(i) for i in matrix[-1, :])
            if final_row != (0.0, 0.0, 0.0, 1.0):
                raise ValueError("Final row of affine transformation matrix should be "
                                 f"(0.0, 0.0, 0.0, 1.0) not {final_row}")
            matrix = matrix[:-1, :]
        elif matrix.shape == (3, 3):
            matrix = np.pad(matrix, [[0, 0], [0, 1]])
        elif not matrix.shape == (3, 4):
            raise ValueError("Expecting a 3x3, 3x4, or 4x4 transformation matrix. "
                             f"Input matrix has shape {matrix.shape}")
        self._manifold = self.manifold.transform(matrix)

    def trim_by_plane(
        self,
        normal: _Axis = (0, 0, 1),
        offset: float = 0.0
    ) -> None:
        """
        Cut off anything below a plane. Plane position set by normal
        and offset.

        :param normal: A vector normal to the splitting plane (can be an axis string
        such as `"+x"` or `"-y"`) **Default=(0.0, 0.0, 1.0)**
        :param offset: Offset of the plane from the origin (in direction of normal)
            **Default=0.0**

        ### Examples

        ## Example 1
        <!--start engscript-doc
        from engscript import engscript as es
        -->
        ```python
        # Make a sphere (called hemisphere)
        hemisphere = es.sphere(d=10)
        #Trim all below the xy-plane to get a hemisphere
        hemisphere.trim_by_plane()
        ```
        <!--end engscript-doc

        hemisphere.scene.capture('../docs/api-docs/doc-images/hemisphere.png',
            resolution=(300, 300), axes=True)
        --->
        ![](../docs/api-docs/doc-images/hemisphere.png)

        ## Example 2
        <!--start engscript-doc
        from engscript import engscript as es
        -->
        ```python
        # Make a sphere
        cap = es.sphere(d=10)
        # Trim off everything except a small cap in the positive x-direction
        cap.trim_by_plane([1,0,0], 3)
        ```
        <!--end engscript-doc

        cap.scene.capture('../docs/api-docs/doc-images/trimmed_cap.png',
            resolution=(300, 300), axes=True)
        --->
        ![](../docs/api-docs/doc-images/trimmed_cap.png)

        See also engscript.split_by_plane for splitting into two objects
        """
        normal = axis_to_uvec(normal)
        self._manifold = self.manifold.trim_by_plane(normal, offset)

    def warp(self, function: Callable[[npt.NDArray[np.float32]], None]) -> None:
        """
        Directly adjust the underlying mesh with a custom function. If care
        is not taken this can lead to broken meshes.

        :param function: This should be a callable function. The input is a
        numpy array of np.float32. This array should be modified in place.
        There is no return values.

        The numpy array contains all N vertices. The size of the array is Nx3.

        ## Eggs-ample

        <!--start engscript-doc
        from engscript import engscript as es
        -->
        ```python

        # Create egg transform function
        def eggify(vec):
            import numpy as np
            # Create an np array of same shape, for
            # boolean indexing
            ind = np.full(vec.shape, False, bool)
            # Set the index values to true for just
            # z coordinates > 0
            ind[:,2] = vec[:,2] > 0
            # Stretch anything above the xy plane
            vec[ind] = 1.7*vec[ind]

        # Create sphere
        egg = es.sphere(r=20)
        # Warp into an egg
        egg.warp(eggify)
        # Set colour for good measure
        egg.set_color([0.98, 0.90, 0.75, 1.0])
        ```
        <!--end engscript-doc
        egg.scene.capture('../docs/api-docs/doc-images/egg.png',
            resolution=(300, 300), axes=True)
        --->
        ![](../docs/api-docs/doc-images/egg.png)


        """
        self._manifold = self.manifold.warp_batch(function)

    def set_color(self, color: tuple[float, float, float, float] | str) -> None:
        """
        Set the color of the Solid to one solid color.

        :param color: The rgba color as a tuple of 4 floats ranging from 0.0 to 1.0
           or a color string. The string can be an html hex value (i.e '#ffffff'), webcolor
           name (i.e 'DodgerBlue'). Or anything else that
           [Pillow.ImageColor](https://pillow.readthedocs.io/en/stable/reference/ImageColor.html)
           understands.  Such as hsl and hsv function strings.

        ## Example

        <!--start engscript-doc
        from engscript import engscript as es
        -->
        ```python
        ball = es.sphere(r=10)
        ball.set_color("DodgerBlue")
        ```
        <!--end engscript-doc
        ball.scene.capture('../docs/api-docs/doc-images/color_by_name.png',
            resolution=(300, 300), axes=True)
        --->
        ![](../docs/api-docs/doc-images/color_by_name.png)

        See also `set_color_by_function()`
        """
        if isinstance(color, str):
            rgba = get_color_from_str(color)
        else:
            rgba = color

        def _col(_: Any, __: Any) -> tuple[float, float, float, float]:
            return rgba
        self._manifold = self.manifold.set_properties(4, _col)

    def set_color_by_function(
        self,
        function: Callable[
            [npt.NDArray[np.float32], list[float]],
            tuple[float, float, float, float]
        ]
    ) -> None:
        """
        Set the color to vary across the face as deigned by a
        function.

        :param function: A callable function to set the colour.
            This function will be called for each vertex. The inputs
            the position of the vertex (as an numpy array), and the current
            color of the vertex (as a list, that is empty if no color is set)


        ## Example

        <!--start engscript-doc
        from engscript import engscript as es
        -->
        ```python
        from engscript.colors import get_rainbow
        circ = es.circle(r=10)
        cyl = es.extrude(circ, h=11.95, divisions=100)
        cyl.set_color_by_function(get_rainbow(scale=2.0))
        ```
        <!--end engscript-doc
        cyl.scene.capture('../docs/api-docs/doc-images/rainbow.png',
            resolution=(300, 300), axes=True)
        --->
        ![](../docs/api-docs/doc-images/rainbow.png)

        See also `set_color()`
        """
        self._manifold = self.manifold.set_properties(4, function)

    @property
    def as_trimesh(self) -> trimesh.Trimesh:
        """
        Read only property. Returns the underlying mesh as
        a trimesh.Trimesh object. This allows any functionality
        of the [trimesh library](https://trimesh.org/).
        """
        mesh = self.manifold.to_mesh()

        if mesh.vert_properties.shape[1] > 3:
            vertices = mesh.vert_properties[:, :3]
            colors = (mesh.vert_properties[:, 3:] * 255).astype(np.uint8)
        else:
            vertices = mesh.vert_properties
            colors = None

        return trimesh.Trimesh(
            vertices=vertices, faces=mesh.tri_verts, vertex_colors=colors
        )

    @property
    def scene(self) -> Scene:
        """
        Read only property. Returns an `engscript.export.Scene`
        object with this set as the geometry in the scene.
        This can be used for 3D rendering.
        """
        return Scene(self.as_trimesh)

    def export_glb(self, filename: str) -> None:
        """
        Export this solid as a glb file. This is primarily used
        for 3D viewing on the web.

        :param filename: the filename of the glb file.
        """
        trimesh.exchange.export.export_mesh(self.as_trimesh, filename, "glb")

    def export_stl(self, filename: str) -> None:
        """
        Export this solid as an STL file. This is the standard
        file format used for 3D printing.

        :param filename: the filename of the stl file.
        """
        trimesh.exchange.export.export_mesh(self.as_trimesh, filename, "stl")
