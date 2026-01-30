# Copyright (c) 2021, Thomas Aglassinger
# All rights reserved. Distributed under the BSD 3-Clause License.
import argparse
import glob
import logging
import sys
from collections.abc import Iterator
from pathlib import Path

from . import __version__, log
from .sanitize import sanitize_file

_FOLDER_NAMES_TO_SKIP = {".venv", "site-packages", "venv"}


def _parsed_args(args=None):
    parser = argparse.ArgumentParser(description="Sanitize PO files from gettext for version control")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument(
        "po_paths",
        metavar="PO-FILE",
        nargs="+",
        type=Path,
        help=(
            "PO file(s) to sanitize; "
            "use glob patterns to process multiple files; "
            'use "**" for recursive scans; '
            "use folders to recursively process all PO files inside them"
        ),
    )
    return parser.parse_args(args)


def main_without_logging_setup(args=None) -> int:
    result = 0
    po_path = None
    actual_args = [(str(arg) if isinstance(arg, Path) else arg) for arg in args] if args is not None else None
    sanitized_file_count = 0
    arguments = _parsed_args(actual_args)
    try:
        for po_path in po_paths_from(arguments.po_paths):
            sanitize_file(po_path)
            sanitized_file_count += 1
    except Exception as error:
        log.error('cannot sanitize "%s": %s', po_path, error)
        result = 1
    if result == 0:
        if sanitized_file_count >= 1:
            log.info("sanitized %d file(s)", sanitized_file_count)
        else:
            log.error("cannot find any PO-FILE matching the specified glob pattern(s)")
            result = 1
    return result


def po_paths_from(po_path_patterns: list[str]) -> Iterator[Path]:
    for po_path_pattern in po_path_patterns:
        po_path_pattern_path = Path(po_path_pattern)
        if po_path_pattern_path.is_file():
            yield po_path_pattern_path
        else:
            if po_path_pattern_path.is_dir():
                po_path_pattern_path = po_path_pattern_path / "**" / "*.po"
            for po_path_name in glob.iglob(str(po_path_pattern_path), recursive=True):  # noqa: PTH207
                # NOTE: There does not seem to be a way for `path.glob(pattern)` to separate `path`
                #  from the `pattern`, while `iglob(path_with_pattern)` can process a single
                #  combined path and pattern.
                # HACK This is inefficient because it traverses all subfolders inside e.g. ".venv"
                #  even though the technically could be skipped. A more efficient solution using
                #  e.g. `Path.walk()` would require more code and would be harder to maintain.
                po_path = Path(po_path_name)
                is_path_to_skip = bool(_FOLDER_NAMES_TO_SKIP.intersection(set(po_path.parts)))
                if not is_path_to_skip:
                    yield po_path


def main(args=None) -> int:
    logging.basicConfig(level=logging.INFO)
    return main_without_logging_setup(args)


if __name__ == "__main__":
    sys.exit(main())
