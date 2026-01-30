"""
This submodule contains extra functionality for exporting to files.

Most exporting can be done directly as class methods of the geometry classes
such as `engscript.engscript.Sketch.save_image()` or
`engscript.engscript.Solid.export_export_stl()`
"""
from typing import TYPE_CHECKING, TypeAlias, Any
from collections.abc import Iterable
from copy import deepcopy
import io
import platform

from PIL import Image
from matplotlib import pyplot as plt
from matplotlib.axes import Axes
from mpl_toolkits.mplot3d.axes3d import Axes3D  # type: ignore
import trimesh
import numpy as np
import numpy.typing as npt

if TYPE_CHECKING:
    from engscript.engscript import Sketch

_Vec3: TypeAlias = tuple[float, float, float]


def save_image(
    sketches: list['Sketch'],
    filename: str,
    grid: bool = False,
    resolution: tuple[int, int] = (1920, 1080),
    lineformats: str | list[str] | None = None,
    showlines: list[tuple[float, float, float, float, str, str]] | None = None
) -> None:
    """
    Export one image for multiple sketches.

    :param sketches: List of the `engscript.engscript.Sketch` objects to draw
    :param filename: The file name to save the image to. The format of the image
        is determined by the file extension. PNG is recommended
    :param grid: Set to True to add a grid to the background of the image. Also adds
        dashed axes lines.
    :param resolution: The desired image resolution. Default: (1920, 1080)
    :param lineformats: A list of line formats for the images. Specified in matplotlib
        format.
        A single string can be set for all sketches to have the same format.
        If nothing is set this will loop through formats starting with 'b-'.
    :param showlines: Add a list of extra lines to show on the plot. Each line is
        tuple of four floats and a string (x0, y0, norm_x, norm_y, color, style). Where
        (x0,y0) are the coordinates of a point the line goes through.
        (norm_x, norm_y) is the normal vector perpendicular to the line, and color and
        style are the color and style defined in matplotlib.
        All values need to be specified.
    ### Example 3

    <!--start engscript-doc
    from engscript import engscript as es
    from engscript.export import save_image
    -->
    ```python
    #There are 24 default line options print 25 circles
    circles = []
    for r in range(1, 26):
        circles.append(es.circle(r))
    save_image(circles, '../docs/api-docs/doc-images/many_circles.png',
        grid=True, resolution=(800,800))
    ```
    <!--end engscript-doc-->
    ![](../docs/api-docs/doc-images/many_circles.png)

    See also `engscript.engscript.Sketch.save_image()`
    """
    lineformats = _fix_lineformats(sketches, lineformats)

    size = (resolution[0] / 100, resolution[1] / 100)

    fig = plt.figure(figsize=size, dpi=100)
    fig.add_subplot(111)
    ax = fig.axes[0]
    ax.set_aspect('equal', 'datalim')
    if grid:
        ax.grid(True, which='both')
        ax.axhline(y=0, color='k', linestyle='--')
        ax.axvline(x=0, color='k', linestyle='--')

    _plot_polygons(ax, sketches, lineformats)

    if showlines is not None:
        _plot_extra_lines(ax, showlines)

    fig.savefig(filename)
    plt.close(fig)


def _fix_lineformats(
    sketches: list['Sketch'],
    lineformats: str | list[str] | None
) -> list[str]:
    """
    Create fixed list of line formats of same length as sketches
    """
    n_sketch = len(sketches)
    if isinstance(lineformats, Iterable):
        if isinstance(lineformats, str):
            return [lineformats] * n_sketch
        return lineformats

    if lineformats is None:
        cols = ['b', 'g', 'r', 'c', 'm', 'y']
        stys = ['-', '--', ':', '-.']
        return [cols[i % 6] + stys[(i // 6) % 4] for i in range(n_sketch)]

    raise TypeError(f'Unexpected data type {type(lineformats)} for lineformats')


def _plot_polygons(
    ax: Axes,
    sketches: list['Sketch'],
    lineformats: list[str]
) -> None:
    """
    Plot the sketches on this axis
    """
    for sketch, lineformat in zip(sketches, lineformats):
        polys = sketch.cross_sec.to_polygons()
        for poly in polys:
            # just using list(poly[:,0]) has a list of np.float64s which goes
            # weird
            x = [float(i) for i in poly[:, 0]]
            x += [x[0]]
            y = [float(i) for i in poly[:, 1]]
            y += [y[0]]
            ax.plot(x, y, lineformat)


def _plot_extra_lines(
    ax: Axes,
    showlines: list[tuple[float, float, float, float, str, str]]
) -> None:
    """
    Plot extra lines
    """
    for line in showlines:
        ax.axline((line[0], line[1]),
                  xy2=(line[0] - line[3], line[1] + line[2]),
                  color=line[4],
                  linestyle=line[5])


class Scene:
    """
    This is the main class for 3D rendering. It uses the trimesh library
    as the main geometry and rendering and back end.

    Generally it is expected that Scenes will be created using the `.scene`
    property of `engscript.engscript.Solid` and `engscript.assemble.Component`.
    """

    def __init__(
        self,
        geometry: trimesh.Trimesh | list[trimesh.Trimesh]
    ) -> None:
        """
        Creating a scene with this constructor is not recommended. To
        do so you will need to work with the underlying
        trimesh library. Instead it is recommended you use the `.scene`
        property of `engscript.engscript.Solid` and
        `engscript.assemble.Component`.

        :param geometry: A Trimesh geometry object or a list of Trimesh geometry
        objects

        """
        self.geometry = deepcopy(geometry)
        self.scene = trimesh.scene.scene.Scene(geometry)

    def capture(
        self,
        filename: str,
        elev: float = 30.0,
        azim: float = -60.0,
        *,
        distance_ratio: float = 1.5,
        resolution: tuple[int, int] = (1920, 1080),
        axes: bool = False
    ) -> None:
        """
        Create a PNG render of this scene. Note that all renders use perspective.
        Orthographic rendering may be possible at a later date when other rendering
        libraries are supported.

        Note that in Windows a window will pop up momentarily as the render takes
        place.

        :param filename: The desired filename of the output PNG image.
        :param elev: The camera elevation angle in degrees. elev=0 corresponds to a
            vertical z-axis in the image. This value must be between +/-90.0.
            **Default=30.0**
        :param azim: The azimuthal rotation of the camera. **Default=60.0**
        :param distance_ratio: Sets the camera distance to `distance_ratio*d0` where
            `d0` is the camera distance where geometry is just within view.
            **Default=1.5** ***Keyword only parameter***
        :param resolution: The output resolution of the final image.
            **Default=(1920, 1080)** ***Keyword only parameter***
        :param axes: Set this to True to add axes to the render. This adds both
            x,y,z-axes through the image and also adds labelled axes in the corner
            **Default=False** ***Keyword only parameter***

        """
        if isinstance(self.geometry, trimesh.Trimesh):
            tmesh = self.geometry
        else:
            tmesh = trimesh.util.concatenate(self.geometry)
        # copy scene for this output
        output_scene = self.scene.copy()

        r = _get_camera_rotation_matrix(elev, azim)

        output_scene.camera.resolution = resolution

        corners = trimesh.bounds.corners(tmesh.bounds)
        center = (tmesh.bounds[0] + tmesh.bounds[1]) / 2

        tight_transform = output_scene.camera.look_at(corners,
                                                      rotation=r,
                                                      center=center)

        x = tight_transform[0][3]
        y = tight_transform[1][3]
        z = tight_transform[2][3]
        base_d = ((center[0] - x)**2 + (center[1] - y)**2 + (center[2] - z)**2)**.5
        distance = distance_ratio * base_d

        output_scene.camera_transform = output_scene.camera.look_at(corners,
                                                                    rotation=r,
                                                                    distance=distance,
                                                                    center=center)

        if axes:
            output_scene.add_geometry(_3d_axes_geometry(corners))

        # Set window to visible on Windows otherwise render is blank.
        visible = platform.system() == "Windows"
        png = output_scene.save_image(resolution=resolution, visible=visible)

        if axes:
            _save_with_mini_axes(png, filename, elev, azim)
        else:
            with open(filename, "wb") as f:
                f.write(png)

    def show(
        self,
        axes: bool = False,
        grid: bool = False
    ) -> Any:
        """
        Show the scene either in a window or in a jupyter notebook. This is
        fairly experimental

        :param axes: Add axes to the scene (doesn't show up well in notebook)
        :param grid: Add a grid under the object in the x-y plane
             (not available in notebook)
        :return: Either a pyglet window or a ipython widget depending on where
            it was called from.
        """
        if isinstance(self.geometry, trimesh.Trimesh):
            tmesh = self.geometry
        else:
            tmesh = trimesh.util.concatenate(self.geometry)
        output_scene = self.scene.copy()
        if axes:
            corners = trimesh.bounds.corners(tmesh.bounds)
            output_scene.add_geometry(_3d_axes_geometry(corners))
        flags = {"grid": True} if grid else {}
        return output_scene.show(flags=flags)


def _3d_axes_geometry(
    corners: tuple[_Vec3, _Vec3, _Vec3, _Vec3, _Vec3, _Vec3, _Vec3, _Vec3]
) -> list[trimesh.path.Path3D]:
    """
    Return the trimesh geometry for the x,y,z axes
    """
    # corners 0 and 6 are the most negative and positive corners
    # find absolute max for setting axes.
    maxi = max(abs(dim) for dim in list(corners[0]) + list(corners[6]))
    el = trimesh.path.entities.Line([0.0, 1.0])
    vs = [[-maxi * 5, 0, 0], [maxi * 5, 0, 0]]
    xax = trimesh.path.Path3D(entities=[el], vertices=vs)
    vs = [[0, -maxi * 5, 0], [0, maxi * 5, 0]]
    yax = trimesh.path.Path3D(entities=[el], vertices=vs)
    vs = [[0, 0, -maxi * 5], [0, 0, maxi * 5]]
    zax = trimesh.path.Path3D(entities=[el], vertices=vs)
    return [xax, yax, zax]


def _get_camera_rotation_matrix(
    elev: float,
    azim: float
) -> npt.NDArray[np.float32]:
    """
    Return the camera rotation matrix required for the desired camera angles
    """
    if elev > 90 or elev < -90:
        raise ValueError("Elevation should be from -90 to +90")
    azim = (azim + 180) % 360 - 180
    elev_rad = elev / 180 * np.pi
    azim_rad = azim / 180 * np.pi
    r0 = np.asarray([
        [0.0, 0.0, 1.0, 0.0],
        [1.0, 0.0, 0.0, 0.0],
        [0.0, 1.0, 0.0, 0.0],
        [0.0, 0.0, 0.0, 1.0]], dtype=np.float64)

    r1 = np.asarray([
        [np.cos(elev_rad), 0.0, -np.sin(elev_rad), 0.0],
        [0.0, 1.0, 0.0, 0.0],
        [np.sin(elev_rad), 0.0, np.cos(elev_rad), 0.0],
        [0.0, 0.0, 0.0, 1.0]], dtype=np.float64)

    r2 = np.asarray([
        [np.cos(azim_rad), -np.sin(azim_rad), 0.0, 0.0],
        [np.sin(azim_rad), np.cos(azim_rad), 0.0, 0.0],
        [0.0, 0.0, 1.0, 0.0],
        [0.0, 0.0, 0.0, 1.0]], dtype=np.float64)

    # As no are deprecating matrix, we us nparrays and the
    # `@` matrix multiplication symbol
    return r2 @ r1 @ r0


def _save_with_mini_axes(
    png_data: bytes,
    filename: str,
    elev: float,
    azim: float
) -> None:
    """
    Save the image with mini x,y,z axis markers in corner
    """
    png = Image.open(io.BytesIO(png_data))
    ax_buf = _mini_axes(elev, azim)
    ax_png = Image.open(ax_buf)
    orig_size = png.size
    ax_size = (int(orig_size[0] / 7), int(orig_size[0] / 7))
    ax_png_sm = ax_png.resize(ax_size)
    png.paste(
        ax_png_sm,
        (orig_size[0] - ax_size[0], orig_size[1] - ax_size[1]),
        ax_png_sm)
    png.save(filename)


def _mini_axes(elev: float, azim: float) -> io.BytesIO:
    """
    Return a buffer containing a png image file of
    mini x,y,z axes in the desired rotation.
    These are created using matplotlib
    """
    fig = plt.figure(figsize=(1, 1), dpi=100)
    ax = fig.add_subplot(projection='3d')
    if not isinstance(ax, Axes3D):
        raise TypeError("Expecting a 3D axis!")
    ax.set_aspect('equal', 'datalim')
    ax.set_axis_off()
    # order of  angles are ax.view_init(elev, azim, roll)
    ax.view_init(elev, azim, 0)
    # mypy is confused because the projection argument creates a different
    # class of axis mpl_toolkits.mplot3d.axes3d.Axes3D (without typhints)

    # Depending on the angle the axes need plotting in different orders
    # As the last plotted is always what is showing on top.
    if elev >= 0:
        _plt_z_ax_tail(ax)
        _plt_xy_ax(ax, azim)
        _plt_z_ax(ax)
    else:
        _plt_z_ax(ax)
        _plt_xy_ax(ax, azim)
        _plt_z_ax_tail(ax)

    buf = io.BytesIO()
    fig.savefig(buf, format='png', bbox_inches='tight', transparent=True)
    plt.close(fig)
    buf.seek(0)

    return buf


def _plt_xy_ax(ax: Axes3D, azim: float) -> None:
    if (azim > -135.0) & (azim <= -45.0):
        _plt_y_ax_tail(ax)
        _plt_x_ax(ax)
        _plt_x_ax_tail(ax)
        _plt_y_ax(ax)
    elif (azim > -45.0) & (azim <= 45.0):
        _plt_x_ax(ax)
        _plt_y_ax(ax)
        _plt_y_ax_tail(ax)
        _plt_x_ax_tail(ax)
    elif (azim > 45.0) & (azim <= 135.0):
        _plt_y_ax(ax)
        _plt_x_ax(ax)
        _plt_x_ax_tail(ax)
        _plt_y_ax_tail(ax)
    else:
        _plt_x_ax_tail(ax)
        _plt_y_ax(ax)
        _plt_y_ax_tail(ax)
        _plt_x_ax(ax)


def _plt_x_ax(ax: Axes3D) -> None:
    ax.plot([0, 1], [0, 0], [0, 0], 'r')
    ax.plot([.9, 1, .9], [.1, 0, -.1], [0, 0, 0], 'r')
    ax.text(1.3, 0, 0, "x",
            color='red',
            fontsize='xx-large',
            horizontalalignment='center',
            verticalalignment='center')


def _plt_x_ax_tail(ax: Axes3D) -> None:
    ax.plot([-.3, 0], [0, 0], [0, 0], 'r')


def _plt_y_ax(ax: Axes3D) -> None:
    ax.plot([0, 0], [0, 1], [0, 0], 'g')
    ax.plot([.1, 0, -.1], [.9, 1, .9], [0, 0, 0], 'g')
    ax.text(0, 1.3, 0, "y",
            color='green',
            fontsize='xx-large',
            horizontalalignment='center',
            verticalalignment='center')


def _plt_y_ax_tail(ax: Axes3D) -> None:
    ax.plot([0, 0], [-.3, 0], [0, 0], 'g')


def _plt_z_ax(ax: Axes3D) -> None:
    ax.plot([0, 0], [0, 0], [0, 1], 'b')
    ax.plot([0, 0, 0], [.1, 0, -.1], [.9, 1, .9], 'b')
    ax.text(0, 0, 1.3, "z",
            color='blue',
            fontsize='xx-large',
            horizontalalignment='center',
            verticalalignment='center')


def _plt_z_ax_tail(ax: Axes3D) -> None:
    ax.plot([0, 0], [0, 0], [-.3, 0], 'b')
