#!/usr/bin/python3
# -*- coding=utf-8 -*-
r"""
interactive terminal markdown-documentation viewer with support for images and with code-highlighting.
"""
import argparse as __argparse
from pathlib import Path as __Path
from __version__ import __version__


class __Namespace:
    docs: str


__parser = __argparse.ArgumentParser(
    prog="termdocs",
    description=__doc__,
    formatter_class=__argparse.ArgumentDefaultsHelpFormatter
)
__parser.add_argument('docs', nargs='?', default='.',
                      help="folder or file to view")
__parser.add_argument('-v', '--version', action='version', version=__version__)

args = __parser.parse_args(namespace=__Namespace())

docs = __Path(args.docs)
if not docs.exists():
    raise LookupError(f"file or directory {docs} does not exist")
root_dir = __Path(docs)
if root_dir.is_file():
    index_file = root_dir
    root_dir = root_dir.parent
    is_custom_file = True
else:
    is_custom_file = False
    for _ in {'index.md', 'README.md', 'readme.md'}:
        __ = root_dir / _
        if __.is_file():
            index_file = __
            break
    else:
        index_file = None
