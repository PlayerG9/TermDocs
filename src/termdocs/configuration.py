#!/usr/bin/python3
# -*- coding=utf-8 -*-
r"""
interactive terminal markdown-documentation viewer with support for images and with code-highlighting.
"""
import typing as _t
import argparse as __argparse
from pathlib import Path as __Path
from __version__ import __version__


class __Namespace:
    all: bool
    css: _t.List[str]
    docs: str

    def __repr__(self):
        return f"<{vars(self)}>"


__parser = __argparse.ArgumentParser(
    prog="termdocs",
    description=__doc__,
    formatter_class=__argparse.ArgumentDefaultsHelpFormatter
)
__parser.add_argument('-a', '--all', type=bool, action=__argparse.BooleanOptionalAction,
                      help="show all files in the filetree and not just .md files")
__parser.add_argument('--css', '--tcss', action="append", type=str, default=[],
                      help="additional tcss (textual-css) files to load")
__parser.add_argument('--md-css', '--md-style', dest="css", action="append_const", const="markdown.css",
                      help="load default tailwind-like css classes for the markdown attributes\n"
                           "(e.g. p-1, bg-warning, text-right)\n"
                           "(increases load time significantly)")
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
