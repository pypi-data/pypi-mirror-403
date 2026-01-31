# ----------------------------------------------------------------------------------------
#   cal-mkdocs
#   ----------
#
#   Sets up environment variables to point to various internal resources that MkDocs
#   can then reference using `!ENV`. It then launches mkdocs
#
#   Authors
#   -------
#   gatto
#
#   Version History
#   ---------------
#   Jul 2025 - Created
# ----------------------------------------------------------------------------------------

# ----------------------------------------------------------------------------------------
#   Imports
# ----------------------------------------------------------------------------------------

import argparse
import importlib.resources
import os
import subprocess
from .version import VERSION_STR

# ----------------------------------------------------------------------------------------
#   Functions
# ----------------------------------------------------------------------------------------


# ----------------------------------------------------------------------------------------
def main(argv: list[str]) -> int:
    """
    Main function called when run from command line.
    """

    parser = argparse.ArgumentParser(
        prog="cal-mkdocs", description=f"cal-mkdocs: {VERSION_STR}"
    )
    parser.add_argument(
        "--version", action="version", version=f"cal-mkdocs: {VERSION_STR}"
    )
    parser.add_argument(
        "--config", "-f", required=True, help="Provide a specific MkDocs config."
    )
    parser.add_argument(
        "--output",
        "-o",
        required=True,
        help="The directory to output the result of the documentation build.",
    )
    parser.add_argument(
        "--docs", "-d", required=True, help="Root folder containing MD files."
    )

    args = parser.parse_args(argv)

    folder_theme_cal = str(importlib.resources.files("cal_mkdocs.themes.theme_cal"))
    folder_theme_std = str(importlib.resources.files("cal_mkdocs.themes.theme_std"))

    config_file = os.path.abspath(args.config)
    output_folder = os.path.abspath(args.output)
    docs_folder = os.path.abspath(args.docs)

    env: dict[str, str] = os.environ.copy()
    env.update(
        {
            "CAL_MKDOCS_DOCS_DIR": docs_folder,
            "CAL_MKDOCS_THEME_CAL": folder_theme_cal,
            "THEME_CAL": folder_theme_cal + "/cal-theme.yml",
            "CAL_MKDOCS_THEME_STD": folder_theme_std,
            "THEME_STD": folder_theme_std + "/std-theme.yml",
        }
    )

    result = subprocess.run(
        ["mkdocs", "build", "--config-file", config_file, "--site-dir", output_folder],
        env=env,
    )

    return result.returncode
