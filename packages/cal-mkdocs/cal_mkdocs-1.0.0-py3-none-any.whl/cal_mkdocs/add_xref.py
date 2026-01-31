#!/usr/bin/env python3
# ----------------------------------------------------------------------------------------
#   add_xref
#   --------
#
#   The documentation is produced using `mkdocs`. This is a post processor that will add
#   cross references into the HTML for objects marked with backticks in the source.
#   This is called as `cal-mkdocs-xref` in the `cal-mkdocs` python package.
#
#   Authors
#   -------
#   gatto
#
#   Version History
#   ---------------
#   Jul 2025 - Created (in CalPythonCommon repo)
#   Dec 2025 - Moved into cal-mkdocs
# ----------------------------------------------------------------------------------------

# ----------------------------------------------------------------------------------------
#   Imports
# ----------------------------------------------------------------------------------------

import argparse
import glob
import os
import re
import sys
from re import Match

# ----------------------------------------------------------------------------------------
#   Types
# ----------------------------------------------------------------------------------------

ElementMap = dict[str, list[str]]

# ----------------------------------------------------------------------------------------
#   Functions
# ----------------------------------------------------------------------------------------


# ----------------------------------------------------------------------------------------
def main(argv: list[str]) -> int:
    """
    Main function
    """

    parser = argparse.ArgumentParser(
        description="Adds crossrefs in the post mkdocs HTML for CalrepSDK/CaltechSDK"
    )
    parser.add_argument(
        "--dir", "-d", required=True, help="The HTML output directory from mkdocs"
    )
    parser.add_argument("--module", "-m", help="The name of the module")
    args = parser.parse_args(argv)

    files = glob.glob(os.path.join(args.dir, "*.html"))

    print("Processing HTML files")

    element_map: ElementMap = {}
    module_names: list[str] = []
    for file in files:
        name = file.removeprefix(args.dir + "/").removesuffix(".html")
        module_names.append(name)
        new_elements = _find_elements(file)
        for element in new_elements:
            if element in element_map:
                element_map[element].extend(new_elements[element])
            else:
                element_map[element] = new_elements[element]

    for file in files:
        _add_cross_references(
            file_name=file,
            module_names=module_names,
            element_map=element_map,
            our_module_name=args.module,
        )

    return 0


# ----------------------------------------------------------------------------------------
def _find_elements(file_name: str) -> ElementMap:
    """
    Looks for anchor points for elements such as methods or properties in the class
    within an HTML file.
    """

    with open(file_name) as f:
        lines = f.readlines()

    element_map: ElementMap = {}

    regex = re.compile(r'<h3 id="(.*?)" class=".*?">')
    for line in lines:
        if m := regex.search(line):
            ref = m.group(1)
            element = ref.split(".")[-1]
            base_name = os.path.basename(file_name)
            link = f"{base_name}#{ref}"

            element_map[element] = [link]

    return element_map


# ----------------------------------------------------------------------------------------
def _add_cross_references(
    *,
    file_name: str,
    module_names: list[str],
    element_map: ElementMap,
    our_module_name: str | None,
) -> None:
    """
    Processes the html file specified by `file_name`. This will add in cross references
    to objects marked in backticks
    """

    with open(file_name) as f:
        lines = f.readlines()
    changed = False

    module_name = our_module_name or ""

    regex1 = re.compile(rf"<code>(?:{module_name}\.)?([a-zA-Z0-9_]+?)</code>")
    regex2 = re.compile(r"<code>\.([a-zA-Z0-9_]+?)(\(\))?</code>")
    regex3 = re.compile(
        rf"<code>({module_name})\.(error|Error)\.([a-zA-Z0-9_]+?)</code>"
    )
    regex4 = re.compile(r'href="Error.html#([a-zA-Z0-9_.]+?)">([a-zA-Z0-9_]+?)</a>')

    def replacer1(match: Match[str]) -> str:
        full_match: str = match.group(0)
        module_name: str = match.group(1)
        if module_name in module_names:
            return f'<a href="{module_name}.html">{full_match}</a>'
        return full_match

    def replacer2(match: Match[str]) -> str:
        full_match: str = match.group(0)
        element_name: str = match.group(1)
        if element_name in element_map:
            ref = None
            if len(element_map[element_name]) == 1:
                # Easy, only one reference so pick it
                ref = element_map[element_name][0]
            else:
                # This means there is more than one element with this name. What we will
                # do is see if there is an entry to THIS document, and if so use it,
                # otherwise we will have to just leave it.
                for try_ref in element_map[element_name]:
                    ref_file = try_ref.split("#")[0]
                    if file_name.endswith(f"/{ref_file}"):
                        ref = try_ref
            if ref:
                return f'<a href="{ref}">{full_match}</a>'
        return full_match

    def replacer3(match: Match[str]) -> str:
        full_match: str = match.group(0)
        main_module: str = match.group(1)
        error_module: str = match.group(2)
        exception_name: str = match.group(3)
        return (
            f'<a href="{error_module}.html'
            f'#{main_module}.{error_module}.{exception_name}">{full_match}</a>'
        )

    def replacer4(match: Match[str]) -> str:
        full_match: str = match.group(0)
        full_exception: str = match.group(1)
        exception_name: str = match.group(2)
        if full_exception.endswith(exception_name):
            return f'<a href="Error.html#{full_exception}">{full_exception}</a>'
        return full_match

    new_lines: list[str] = []
    for line in lines:
        new_line = regex1.sub(replacer1, line)
        new_line = regex2.sub(replacer2, new_line)
        new_line = regex3.sub(replacer3, new_line)
        new_line = regex4.sub(replacer4, new_line)
        if new_line != line:
            changed = True
        new_lines.append(new_line)
    if changed:
        with open(file_name, "w+") as f:
            for line in new_lines:
                print(line, file=f, end="")


# ----------------------------------------------------------------------------------------
#   Entry
# ----------------------------------------------------------------------------------------


def __main__():
    exit(main(sys.argv[1:]))


if __name__ == "__main__":
    __main__()
