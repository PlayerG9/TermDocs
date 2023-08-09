#!/usr/bin/python3
# -*- coding=utf-8 -*-
r"""

"""
from pathlib import Path
import textual.app
import textual.widgets
from .basehandler import BaseHandler
from .register import register_handler


@register_handler
class MarkdownHandler(BaseHandler):
    @staticmethod
    def supports(file: Path):
        return 2 if file.is_file() and file.suffix == ".md" else 0

    def compose(self) -> textual.app.ComposeResult:
        yield textual.widgets.Static()

    async def on_mount(self):
        if self.filepath:
            self.query_one(textual.widgets.Static).update(self.filepath.read_text())
