#!/usr/bin/python3
# -*- coding=utf-8 -*-
r"""

"""
from pathlib import Path
import textual.app
import textual.widgets
import rich.syntax
from .basehandler import BaseHandler
from .register import register_handler


@register_handler
class TextHandler(BaseHandler):
    @staticmethod
    def supports(file: Path) -> int:
        import mimetypes
        mime, _ = mimetypes.guess_type(file.name)
        return mime and mime.startswith("text/")

    def compose(self) -> textual.app.ComposeResult:
        yield textual.widgets.Static(markup=False)

    def on_mount(self):
        text = self.query_one(textual.widgets.Static)
        content = self.filepath.read_text()
        lexer = rich.syntax.Syntax.guess_lexer(path=str(self.filepath))
        syntax = rich.syntax.Syntax(
            code=content,
            lexer=lexer,
            theme='ansi_dark',
            dedent=False,
            line_numbers=False,
            # highlight_lines={2,3,4,5,6,7,8},
            # code_width=80,
            tab_size=4,
            word_wrap=False,
            background_color=None,
            indent_guides=False,
            padding=0,
        )
        text.update(syntax)
