#!/usr/bin/python3
# -*- coding=utf-8 -*-
r"""

"""
import logging
from pathlib import Path
import textual.app
import textual.widgets
from widgets import Markdown
from .basehandler import BaseHandler
from .register import register_handler


@register_handler
class MarkdownHandler(BaseHandler):
    @staticmethod
    def supports(file: Path):
        return 2 if file.is_file() and file.suffix == ".md" else 0

    def compose(self) -> textual.app.ComposeResult:
        yield Markdown(file=self.filepath)

    def on_custom_markdown_link_clicked(self, event: Markdown.LinkClicked):
        logging.info(event)
