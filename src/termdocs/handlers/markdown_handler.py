#!/usr/bin/python3
# -*- coding=utf-8 -*-
r"""

"""
import logging
import webbrowser
from pathlib import Path
import textual.app
import textual.widgets
from widgets import Markdown
from util import Compatibility, HyperRef
from .basehandler import BaseHandler
from .register import register_handler


@register_handler
class MarkdownHandler(BaseHandler):
    @staticmethod
    def supports(file: Path) -> Compatibility:
        if file.suffix == ".md":
            return Compatibility.HIGH
        return Compatibility.NONE

    def compose(self) -> textual.app.ComposeResult:
        yield Markdown(file=self.filepath)

    @textual.on(Markdown.LinkClicked)
    def on_markdown_link_clicked(self, event: Markdown.LinkClicked):
        href = HyperRef(event.href)
        if href.check_is_file():
            path = href.absolute(to=self.app.path).as_path()
            if path.is_dir():
                for index in {'index.md', 'README.md', 'readme.md'}:
                    file = path / index
                    if file.is_file():
                        path = file
                        break
            self.app.path = path
        elif href.check_is_http_url():
            logging.debug("Open url in browser")
            if not webbrowser.open(url=str(href)):
                logging.error(f"Can't open url {href!r}")
        else:
            logging.error(f"Can't handle link {href!r}")
