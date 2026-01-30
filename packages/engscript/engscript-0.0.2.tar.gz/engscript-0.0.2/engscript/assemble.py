"""
This submodule is currently under development

It will contain functionality for creating components,
subassemblies, and assemblies.
"""

from __future__ import annotations
from typing import TypeAlias, Any, Optional
from collections.abc import Iterable
from copy import deepcopy


import trimesh
import numpy as np
import numpy.typing as npt

from engscript.export import Scene
from engscript.engscript import Solid

_Vec3: TypeAlias = tuple[float, float, float]


class BaseAssemblyObject:
    """The base object for Component and Assembly."""

    def __init__(self) -> None:
        """
        Initalise the base class.
        """

        self._total_transform = np.array(
            [
                [1.0, 0.0, 0.0, 0.0],
                [0.0, 1.0, 0.0, 0.0],
                [0.0, 0.0, 1.0, 0.0],
                [0.0, 0.0, 0.0, 0.0]
            ]
        )

    @property
    def total_transform(self) -> npt.NDArray[np.float32 | np.float64]:
        """The total transform applied to this object."""
        return self._total_transform

    def apply_transform(
        self,
        matrix: npt.NDArray[np.float32 | np.float64]
    ) -> None:
        """Apply a a 3D affine transformation matrix to the geometry

        :param matrix: A 4x4 numpy array containing the matrix. Note that
            np.matrix is not supported as it is being deprecated.
        """
        self._total_transform = matrix*self._total_transform

    def scale(self, factor: float | _Vec3) -> None:
        """Scale  by a fixed factor or a 3D vector.

        :param factor: The scaling factor. To scale differently in x,y, and z you can
            enter a list or tuple of (x,y,z) scaling factors.
        """
        if not isinstance(factor, Iterable):
            factor = (factor, factor, factor)
        self.apply_transform(
            np.array([
                [factor[0], 0.0, 0.0, 0.0],
                [0.0, factor[1], 0.0, 0.0],
                [0.0, 0.0, factor[2], 0.0],
                [0.0, 0.0, 0.0, 0.0]]
            )
        )

    def translate(self, xyz: _Vec3) -> None:
        """Translate in by a 3D vector.

        :param xyz: The (x,y,z) vector for translation.

        See also: `BaseAssemblyObject.translate_x()`,
        `BaseAssemblyObject.translate_y()`, and `BaseAssemblyObject.translate_z()`
        """
        self.apply_transform(
            np.array([
                [1.0, 0.0, 0.0, xyz[0]],
                [0.0, 1.0, 0.0, xyz[1]],
                [0.0, 0.0, 1.0, xyz[2]],
                [0.0, 0.0, 0.0, 0.0]]
            )
        )

    def translate_x(self, x: float) -> None:
        """Translate  in only the x-direction.

        :param x: The distance to translate in x.

        See also: `BaseAssemblyObject.translate()`, `BaseAssemblyObject.translate_y()`,
        and `BaseAssemblyObject.translate_z()`
        """
        self.apply_transform(
            np.array([
                [1.0, 0.0, 0.0, x],
                [0.0, 1.0, 0.0, 0.0],
                [0.0, 0.0, 1.0, 0.0],
                [0.0, 0.0, 0.0, 0.0]]
            )
        )

    def translate_y(self, y: float) -> None:
        """Translate in only the y-direction.

        :param y: The distance to translate in y.

        See also: `BaseAssemblyObject.translate()`, `BaseAssemblyObject.translate_x()`,
        and `BaseAssemblyObject.translate_z()`
        """
        self.apply_transform(
            np.array([
                [1.0, 0.0, 0.0, 0.0],
                [0.0, 1.0, 0.0, y],
                [0.0, 0.0, 1.0, 0.0],
                [0.0, 0.0, 0.0, 0.0]]
            )
        )

    def translate_z(self, z: float) -> None:
        """
        Translate in only the z-direction.

        :param z: The distance to translate in z.

        See also: `BaseAssemblyObject.translate()`, `BaseAssemblyObject.translate_x()`,
        and `BaseAssemblyObject.translate_y()`
        """
        self.apply_transform(
            np.array([
                [1.0, 0.0, 0.0, 0.0],
                [0.0, 1.0, 0.0, 0.0],
                [0.0, 0.0, 1.0, z],
                [0.0, 0.0, 0.0, 0.0]]
            )
        )

    @property
    def as_trimesh(self) -> trimesh.Trimesh:
        """
        Read only property. Returns the entire component as a single
        Unioned trimesh. This can remove color information and combines all
        underlying meshes of the component.

        See also `all_trimeshes`
        """
        tmesh: trimesh.Trimesh = trimesh.util.concatenate(self.all_trimeshes)
        return tmesh

    @property
    def all_trimeshes(self) -> list[trimesh.Trimesh]:
        """All trimeshes for this object. This must be implemented by child classes."""
        raise NotImplementedError("This should be implemented by a child class.")

    @property
    def scene(self) -> Scene:
        """
        Read only property. Returns an `engscript.export.Scene`
        object with this set as the geometry in the scene.
        This can be used for 3D rendering.
        """
        return Scene(self.all_trimeshes)

    def export_glb(self, filename: str) -> None:
        """Export as a glb file. This is primarily used for 3D viewing on the web.

        :param filename: the filename of the glb file.
        """
        trimesh.exchange.export.export_mesh(self.scene.scene, filename, "glb")

    def export_stl(self, filename: str) -> None:
        """Export as an STL file. This is the standard file format used for 3D printing.

        Note that as the component meshes are not always watertight especially if
        they are imported from other sources like STEP files from manufacturers.
        Where possible it is best to export STLs of `engscript.engscript.Solid`
        objects rather than of components.

        :param filename: the filename of the stl file.
        """
        trimesh.exchange.export.export_mesh(self.as_trimesh, filename, "stl")


class Component(BaseAssemblyObject):
    """
    A grouping class for individual components assemblies. This class can hold
    multiple 3D mesh objects which are treated as a single component.

    Create a component with

    ```python
    my_component = Component([obj1, obj2, obj3])
    ```

    the input components can be `engscript.engscript.Solid` objects or `trimesh.Trimesh`
    objects. This component will convert any solids into trimeshes.

    This means that non-watertight meshes that cannot be manipulated as solids can still
    be used in rendering of assemblies.
    """

    def __init__(
        self,
        geometry: list[trimesh.Trimesh | Solid] | trimesh.Trimesh | Solid
    ) -> None:
        """
        Create a component from a solid, a trimesh, or a list containing a mixture
        of the two

        :param geometry: The geometry objects to add to this component.
        """

        super().__init__()
        self._tmeshs: list[trimesh.Trimesh] = []
        self._transformed_cache: Optional[dict[str, Any]] = None
        self.add_geometry(geometry)

    def add_geometry(
        self,
        geometry: list[trimesh.Trimesh | Solid] | trimesh.Trimesh | Solid
    ) -> None:
        """Add new geometry to this component.

        :param geometry: The geometry objects to add to this component. This can be
            a solid, a trimesh or a list containing a mixutre of the two.
        """
        if not isinstance(geometry, Iterable):
            geometry = [geometry]
        for geometry_el in geometry:
            if isinstance(geometry_el, Solid):
                self._tmeshs.append(geometry_el.as_trimesh)
            elif isinstance(geometry_el, trimesh.Trimesh):
                self._tmeshs.append(deepcopy(geometry_el))
            else:
                raise TypeError(
                    'A component should be made up of trimesh or solid objects')
        self._transformed_cache = None

    @property
    def all_trimeshes(self) -> list[trimesh.Trimesh]:
        """
        Read only property. Returns a list of each of the underlying meshes
        that make up this component. This will preserve colour, but is less
        useful than a single mesh when trying to ascertain properties such
        as the bounding box.

        If the the componet has been trasnformed from the base meshes, and the transform
        hasn't been cached, this will need to process the transformation.

        See also `as_trimesh`
        """
        if self._transformed_cache is not None:
            cached_transform = self._transformed_cache.get("transform")
            if cached_transform is not None and np.array_equal(cached_transform, self.total_transform):
                tmeshs: list[trimesh.Trimesh] = self._transformed_cache["tmeshs"]
                return tmeshs

        tmeshs = deepcopy(self._tmeshs)
        for tmesh in tmeshs:
            tmesh.apply_transform(self.total_transform)

        # Cache the transform.
        self._transformed_cache = {
            "transform": self.total_transform,
            # Copy again for caching in case downstream code alters
            "tmeshs": deepcopy(tmeshs),
        }
        return tmeshs

class Assembly(BaseAssemblyObject):
    """An assembly of components."""
    def __init__(
        self,
        components: list[trimesh.Trimesh | Solid | BaseAssemblyObject] | trimesh.Trimesh | Solid | BaseAssemblyObject
    ) -> None:
        """
        Create a an assembly from Components or sub-assembloes

        :param components: The Component or Assembly objects to add to this Assembly.
        """

        super().__init__()
        self._components: list[BaseAssemblyObject] = []
        if not isinstance(components, Iterable):
            components = [components]
        for component in components:
            self.add_component(component)

    def add_component(
        self,
        component:  trimesh.Trimesh | Solid | BaseAssemblyObject
    ) -> None:
        """Add a component to this assembly.

        :param component: Add a component to this assembly. Note it is added in the
            base reference frame of the component, even if the component has been
            transformed.
        """

        if isinstance(component, (Solid, trimesh.Trimesh)):
            component = Component(component)

        if not isinstance(component, BaseAssemblyObject):
            raise TypeError(
                "Assembly should be created from Components, or Assemblies. Solids and "
                "trimesh objects will be converted to Components"
            )
        self._components.append(component)


    @property
    def all_trimeshes(self) -> list[trimesh.Trimesh]:
        """
        Read only property. Returns a list of each of the underlying meshes
        that make up this component. This will preserve colour, but is less
        useful than a single mesh when trying to ascertain properties such
        as the bounding box.

        Assemblies do not yet cache transforms so this may be slow even on repeat use.

        See also `as_trimesh`
        """
        tmeshs = []
        for component in self._components:
            tmeshs += component.all_trimeshes

        for tmesh in tmeshs:
            tmesh.apply_transform(self.total_transform)

        return tmeshs
