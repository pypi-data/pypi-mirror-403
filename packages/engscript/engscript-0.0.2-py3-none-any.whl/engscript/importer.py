"""
This submodule contains functions for importing files.
"""

from tempfile import gettempdir
import os
import warnings

import cascadio  # type: ignore
import trimesh
import ezdxf
import numpy as np
from manifold3d import CrossSection, FillRule, Manifold, Mesh  # type: ignore

from engscript.assemble import Component
from engscript.engscript import Sketch, Solid


def load_dxf(dxffilepath: str) -> Sketch:
    """
    Load a dxf file as a Sketch. Note that only DFX files made up
    of polylines without arcs are supported.

    :param dxffilepath: The file path of the DFX file
    :return: A Sketch containing the DXF data.
    """
    dxf = ezdxf.readfile(dxffilepath)  # type: ignore[attr-defined]
    layers = dxf.modelspace().groupby(dxfattrib="layer")

    polys = []
    for layer in layers.values():
        for elem in layer:
            poly = []
            if elem.dxf.dxftype not in ("POLYLINE", "LWPOLYLINE"):
                warnings.warn(
                    RuntimeWarning(
                        "Engscript can only process POLYLINE and LWPOLYLINE elements "
                        f"of dxf files. The element of type {elem.dxf.dxftype} will be "
                        "ignored. This may create unexpected results"))
                continue
            for sub_el in elem.virtual_entities():

                if sub_el.dxf.dxftype != "LINE":
                    warnings.warn(
                        RuntimeWarning(
                            "Engscript can only process LINE elements within POLYLINE "
                            "and LWPOLYLINE elements of a dxf file. The element of type "
                            f"{sub_el.dxf.dxftype} will be ignored. This may create "
                            "unexpected results"))
                    continue
                xyz = sub_el.dxf.start.xyz
                poly.append((xyz[0], xyz[1]))
            polys.append(poly)

    return Sketch(CrossSection(polys, fillrule=FillRule.EvenOdd))


def load_stl(stlfilepath: str) -> Solid:
    """
    Load an STL file as a Solid. If the mesh is broken it may fail to load
    properly. External mesh fixing tools may be needed.

    :param stlfilepath: The file path of the STL file
    :return: A Solid containing the STL model.
    """
    with open(stlfilepath, 'rb') as file_obj:
        tmesh_dict = trimesh.exchange.stl.load_stl(file_obj)
    tmesh = trimesh.Trimesh(**tmesh_dict)
    if not tmesh.is_volume:
        raise RuntimeError(
            f"The mesh stored in {stlfilepath} is faulty and cannot be loaded "
            "into the Manifold kernel. Try using a tool such as admesh to fix "
            "the mesh.")
    m = Manifold(Mesh(np.asarray(tmesh.vertices), np.asarray(tmesh.faces)))
    return Solid(m)


def load_stepfile(stepfilepath: str) -> Component:
    """
    Create an `engscript.enscript.Component` of a STEP file.

    This is experimental. The import uses the OpenCASCADE kernel and the library cascadio

    It may not be possible to convert the component to a `engscript.enscript.Solid`
    for transformation as the mesh conversion might not be watertight.

    It may be possible to fix broken meshes with [`pymeshfix`](https://pypi.org/project/pymeshfix/)
    using a script such as:


    ```python
    from engscript.importer import load_stepfile
    import pymeshfix

    component = load_stepfile('mystepfile.step')

    for i, tmesh  in enumerate(component.all_trimeshes):
        if tmesh.is_volume:
            print(f"Mesh {i} is ok")
        else:
            print(f"Attempting to fix mesh {i}")
        tmesh.vertices, tmesh.faces = pymeshfix.clean_from_arrays(tmesh.vertices, tmesh.faces)
        if tmesh.is_volume:
            print(f"Mesh {i} fixed!")
        else:
            print(f"Failed! Mesh {i} is not fixed!")
    ```

    If the second print statement is `True` then pymeshfix has been able to fix the mesh file

    """

    stepfilename = os.path.split(stepfilepath)[1]
    glbfilename = os.path.splitext(stepfilename)[0] + '.glb'
    glbfilepath = os.path.join(gettempdir(), glbfilename)
    cascadio.step_to_glb(stepfilepath, glbfilepath)

    scene = trimesh.load(glbfilepath)
    if isinstance(scene, trimesh.Scene):
        return Component(list(scene.geometry.values()))
    raise TypeError(f"Expecting GLB file to load as trimesh scene not a {type(scene)}")
