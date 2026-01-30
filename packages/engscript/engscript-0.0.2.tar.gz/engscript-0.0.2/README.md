# EngScript
![](./docs/mkdocs/logo/engscript-256x256.png)

[API Documentation](https://gitbuilding.gitlab.io/engscript)

## What is EngScript

EngScript is an experimental library aiming to provide fast OpenSCAD-like, python tool, with integrated rendering and assembly capabilities.

Ideally EngScript will eventually be able to support complex projects like the OpenFlexure microscope.

## Installation

To install EngScript you must have Python 3.10 or greater installed, and pip installed. You can then run:

    pip install engscript

from your terminal.

A more complete [getting started guide](https://gitbuilding.gitlab.io/engscript/gettingstarted/index.html) is available.

## Why write another code CAD program?

![](./docs/mkdocs/img/code_cad.png)

This is a fair question. The open source code-CAD space is very crowded, and there is arguably very little to gain from creating another similar tool. This tool is experimental and is based on extensive experience building complex hardware in OpenSCAD.

We created the [OpenFlexure Microscope](http://openflexure.org) in OpenSCAD ([repo](https://gitlab.com/openflexure/openflexure-microscope/)). OpenSCAD allowed us to build a very compact, complex, precision translation stage for 3D printing a microscope body. We also have written a lot of custom assembly scripts allowing us to automatically generate the images for our [assembly instructions](https://build.openflexure.org/openflexure-microscope/v7.0.0-beta2/) in OpenSCAD:

![](https://build.openflexure.org/openflexure-microscope/v7.0.0-beta2/renders/complete_microscope_rms1.png)

While OpenSCAD has taken us a long way we still have issues with:

* A lack of language specific tools such linters (we wrote our own [SCAD linter](https://gitlab.com/bath_open_instrumentation_group/sca2d/)), unit test frameworks, package managers, etc.
* Difficulty handling data for a large complex project
* Speed issues
* Faulty meshs

As [OpenSCAD moves to the manifold kernel](https://github.com/openscad/openscad/issues/4825) the mesh quality and speed will improve. But a project the size and complexity of OpenFlexure really feels that it needs advanced language features and tools that OpenSCAD. For this it makes sense to look for an alternative in an established general purpose language.

Other options include:

* [CadQuery](https://github.com/CadQuery/cadquery/) - CadQuery is a really ambitious project, bringing full B-rep modelling (and STEP file compatibility) to the open source code CAD world. Moving away from meshes would open up opportunities outside 3D printing. For OpenFlexure the microscope is designed entirely around 3D printing, and relies heavily on operations not supported in the underlying OCC kernel. Porting to CadQuery would be a huge task, and would require a lot of work on CADQuery to reproduce our renders (This work is ongoing in CadQuery and is very exciting).
* [Python OpenSCAD](https://pythonscad.org/) - Another cool project which brings Python to OpenSCAD. However, as the python runs within OpenSCAD this ties the project still to many of the pitfalls of the OpenSCAD internals. I also worry that this approach makes it hard to run python virtual environments so that different projects can have different libraries installed, and so that packages can be handled with a package manager.
* Web-based CAD such as [ManifoldCAD](https://manifoldcad.org/) - The web provides easy options for getting started, nothing to install, just start coding. However, I think that as a project becomes more complex and has multiple files and even external packages this simplicity goes away. Either you need a fully hosted solution with storage, multiple files, and package management; or you need to run things locally, hosting dev servers, installing packages with npm. I don't see an easy way for this to scale.
* One of the many other PythonCADs - There are lots of other programs similar to EngScript which are Python based, using the same or different underlying kernel. While many look really cool, none I found seem to be very mature and stable. (Not that EngScript is mature or stable either).

The purpose of EngScript is to take all the lessons we learned in creating the OpenFlexure in OpenSCAD, the lessons we learned making auto-updating rendered assembly manuals, and the lessons collaborating on the code with a [growing community](https://openflexure.discourse.group/). EngScript doesn't offer to solve these problems yet, but it is a space for us to experiment with features that are needed for complex projects. A key focus of this will be object oriented code so that object properties can be queried during the design process. This should help mitigate some data handling issues, but should also make it easier to capture design intent.

EngScript may be a successful new code CAD program adopted by the OpenFlexure project. It may just be a place to try new things and to learn from that experience.

## Should *I* use EngScript

* If you want to play around with something new - Yes
* If you want to help develop it - Very yes
* If you want a good stable CAD package - Nope!

## See also

This package heavily uses [manifold](https://github.com/elalish/manifold) and [trimesh](https://github.com/mikedh/trimesh/).

It also too a lot of inspiration from [badcad](https://github.com/wrongbad/badcad/).

