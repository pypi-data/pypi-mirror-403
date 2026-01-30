"""
This submodule allows parsing HTML comments in docstrings to generate images
for documentation.

Rather than running from this submodule use the `engscript-doc` entrypoint. If engscript
is installed you should be able to run

    engscript-doc -h

from your terminal for more details.

**Rendering will execute python code from docstrings.**

If you didn't write the python file then take the same care before running this
as you would with executing any other python file!

## Using engscript-doc to generate images.

We use pdoc to generate our API-documentation as pdoc understands markdown. Within
markdown you can use html comments:
```html
<!-- This is a comment -->
```
These comments will not appear in the text, as such we can use them to instruct
engscript-doc to run a code block without having to modify how pdoc runs.

To run a code block make sure it is create with three backticks rather than
indentation. The first sent of backticks can specify `python` to ensure correct
syntax highlighting.

Before the code block we add comments that start with `start engscript-doc` followed
on new lines with any code we wish to run before the code block. For example:
```
<!--start engscript-doc
from engscript import engscript as es
-->
```

After the code block we add comments that start with `end engscript-doc` followed
on new lines with any code we wish to run after the code block. For example:
```
<!--end engscript-doc
poly.save_image('../docs/api-docs/doc-images/poly.png', resolution=(300, 300), grid=True)
--->
```

This will be run in the directory of the python file so all paths should be
relative to the file being documented. Any generated images can be included
into pdoc using markdown image syntax
```md
![](../docs/api-docs/doc-images/poly.png')
```

For example:

![](../docs/mkdocs/img/engscript-doc_example.png)

will render in pdoc as:

![](../docs/mkdocs/img/engscript-doc_example_result.png)

## Note about list comprehension:

Prior to Python 3.12 the line `circles = [es.circle(r) for r in range(26)]`
probably won't work in engscript-doc due to how it Python handles variable
scopes for inline comprehension. Use a full loop instead.
See [PEP 709](https://peps.python.org/pep-0709/) for more details.

"""
from typing import Any
import warnings
import re
import os

from pdoc import extract
from pdoc.doc import Doc, Module, Class


# Filter pdoc warning about stopping an imported module calling lspcu
warnings.filterwarnings(
    action='ignore',
    category=UserWarning,
    module='subprocess')


def generate(modules: list[str]) -> int:
    """
    Run all engscript-doc code blocks in the documentation.

    :param modules: A list of python modules as strings. This will recurse
        through submodules. To ignore a submodule add it to the list prepended
        by an `!`.

    :return: The number of warnings raised (see below).

    Please note that deleting any now unused renders, or creating the
    directories for images to be saved in is not done by engscript-doc.

    If an exception is raised during execution of an engscript-doc code
    block, this exception will be captured and re-raised as a warning.
    """
    all_modules = []
    for module_name in extract.walk_specs(modules):
        all_modules.append(Module.from_name(module_name))

    all_doc_items = _get_all(all_modules)
    n_warns = _get_engscript_doc_calls(all_doc_items)
    return n_warns


def _get_all(all_modules: list[Module]) -> list[Doc[Any]]:
    all_doc_items: list[Doc[Any]] = []
    # module_doc is the pdoc.doc.Module class which is a subclass of
    # pdoc.doc.Doc
    for module_doc in all_modules:
        all_doc_items.append(module_doc)
        all_doc_items += _get_all_from_module(module_doc)
    return all_doc_items


def _get_all_from_module(module_doc: Module) -> list[Doc[Any]]:
    all_doc_items = []
    for member_doc in module_doc.members.values():
        all_doc_items.append(member_doc)
        if isinstance(member_doc, Class):
            all_doc_items += _get_all_from_class(member_doc)
    return all_doc_items


def _get_all_from_class(class_doc: Class) -> list[Doc[Any]]:
    all_doc_items = []
    for cls_member_doc in class_doc.own_members:
        if not cls_member_doc.name.startswith('_'):
            all_doc_items.append(cls_member_doc)
    return all_doc_items


def _get_engscript_doc_calls(all_doc_items: list[Doc[Any]]) -> int:
    pattern = re.compile(
        r'^<!--+\s*start\s*engscript-doc(?P<pre_code>.*?)-+->\n'
        r'(?P<main_code_block>.*?)\n'
        r'^<!--+\s*end\s*engscript-doc(?P<post_code>.*?)-+->\n',
        re.MULTILINE | re.DOTALL)

    n_warns = 0
    for doc_item in all_doc_items:
        docstring = doc_item.docstring
        for match in pattern.finditer(docstring):
            groups = match.groupdict()

            main_code_block = groups['main_code_block'].split('\n')
            # check first and last line are code fences
            if (
                main_code_block[0] not in ["```", "```python"]
                or main_code_block[-1] != "```"
            ):
                _block_warning(doc_item.fullname)
                n_warns += 1
                continue
            main_code = main_code_block[1:-1]
            pre_code = groups['pre_code'].split('\n')
            post_code = groups['post_code'].split('\n')
            code = '\n'.join(pre_code + main_code + post_code)
            # Run the block and add any warning counts.
            n_warns += _run_block(code, doc_item)

    return n_warns


def _run_block(code: str, doc_item: Doc[Any]) -> int:
    warned = 0
    this_dir = os.getcwd()
    if doc_item.source_file is None:
        msg = "Trying to execute code, but cannot determine source directory"
        raise RuntimeError(msg)
    source_dir = os.path.dirname(doc_item.source_file)

    os.chdir(source_dir)
    try:
        exec(code, {}, {})  # pylint: disable=exec-used
    except Exception as e:  # pylint: disable=broad-exception-caught
        msg = ("engscript-doc: Error while running code in "
               f"(in {doc_item.fullname}):\n{e}\n\n{code}\n\n")
        warnings.warn(RuntimeWarning(msg))
        warned = 1
    os.chdir(this_dir)
    return warned


def _block_warning(fullname: str) -> None:
    warn = RuntimeWarning(
        f"engscript-doc warning (in {fullname}): "
        "engscript-doc code block should start and end with ```")
    warnings.warn(warn)
