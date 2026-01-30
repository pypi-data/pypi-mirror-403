'''
This module holds entrypoints for comand line utilities. Currently
the only command line utility provided is engscript-doc.

For more information on engscript-doc see `engscript.doc`
'''

import sys
import os
import argparse
import importlib
import pickle
import traceback
from typing import Any
# Once 3.10 is discontinued can import `Never` from typing
from typing_extensions import Never

import yaml

from engscript import doc
from engscript.engscript import Solid
from engscript.assemble import BaseAssemblyObject

ALLOWED_EXTS = {"stl", "glb", "pkl", "png"}

def _error(msg: str, code: int=1) -> Never:
    """Print an error message then exit with an error code."""
    print(f"\n\nError: {msg}")
    sys.exit(code)


def engscript_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run Engscript to generate CAD models or transfer files.")
    parser.add_argument(
        "-o", "--output",
        action="append",
        required=True,
        help="Specify an output file (repeat for multiple files)"
    )
    parser.add_argument(
        "-a", "--arg",
        action="append",
        default=[],
        help="Add an argument to parse to generate(). A single key:value mapping parsed as YAML"
    )
    parser.add_argument(
        "-L", "--local",
        action="store_true",
        help="Allow importing modules relative to the current working directory"
    )
    parser.add_argument(
        "module",
        type=str,
        help="The python module defining the CAD element.")
    return parser

def cli(args: list[str] | None = None) -> None:
    """Entrypoint for engscript. Used to generate cad files."""
    parser = engscript_parser()
    opts = parser.parse_args(args)
    generate_args = _read_generate_arguments(opts.arg)
    if opts.local:
        sys.path.insert(0, os.getcwd())
    module = importlib.import_module(opts.module)
    try:
        cad_obj = module.generate(**generate_args)
    except Exception as e: # pylint: disable=broad-exception-caught
        traceback.print_exc()
        _error(f"Could not run generate for module: {e}")

    if not isinstance(cad_obj, (Solid, BaseAssemblyObject)):
        _error(
            "The module generate function doesn't return an EngScript Solid or "
            "Assembly object."
        )

    for output in opts.output:
        _generate_output(output, cad_obj)

def _read_generate_arguments(args: list[str]) -> dict[str, Any]:
    """Turn the arguments from the --arg flags into a dictionary."""
    generate_args = {}
    for arg in args:
        try:
            arg_dict = yaml.safe_load(arg)
        except yaml.YAMLError:
            _error(f"Invalid YAML in --arg '{arg}'")

        if not isinstance(arg_dict, dict):
            _error(f"--arg must be a YAML mapping, got {type(arg_dict).__name__}")

        if len(arg_dict) != 1:
            _error("--arg should parse to excatly one value in yaml.")
        key, value = next(iter(arg_dict.items()))
        generate_args[key] = value
    return generate_args

def _generate_output(output: str, cad_obj: Solid|BaseAssemblyObject) -> None:
    """Generate an output file."""
    _, ext = os.path.splitext(output)
    ext = ext.lower().lstrip(".")
    if ext not in ALLOWED_EXTS:
        _error(f"{ext} is not a valid extension. Use one of {ALLOWED_EXTS}")

    if ext == "stl":
        cad_obj.export_stl(output)
    elif ext == "glb":
        cad_obj.export_glb(output)
    elif ext == "pkl":
        with open(output, "wb") as f:
            pickle.dump(cad_obj, f)
    elif ext == "png":
        cad_obj.scene.capture(output)

def get_doc_parser() -> argparse.ArgumentParser:
    """
    Return the argument parser for the engscript-doc CLI.

    :returns: An `argparse.ArgumentParser` for parsing the engscript-doc CLI arguments
    """
    parser = argparse.ArgumentParser(
        description="Automatically generate images for your EngScript API docs. "
        "This only generates the images you need to use an program "
        "such as pdoc to generate the final documentation.")
    parser.add_argument(
        "modules",
        type=str,
        default=[],
        metavar="module",
        nargs="*",
        help="Python module names. These may be importable Python module names "
        "(e.g `engscript.engscript`) or file paths (`./engscript/engscript.py`). "
        "Exclude submodules by specifying a negative !regex pattern, e.g. "
        "`engscript-doc engscript '!engscript.doc'`")
    return parser


def doc_cli(args: list[str] | None = None) -> None:
    """
    Entry point for engscript-docs
    """
    parser = get_doc_parser()
    opts = parser.parse_args(args)
    if not opts.modules:
        parser.print_help()
        _error("Please specify which files or modules you want to document.")

    if doc.generate(opts.modules) > 0:
        # Generate returns the number of warnings.
        # Exit with error code if this is non-zero
        sys.exit(2)
