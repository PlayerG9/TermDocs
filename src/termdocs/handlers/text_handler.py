#!/usr/bin/python3
# -*- coding=utf-8 -*-
r"""

"""
import logging
from pathlib import Path
import textual.app
import textual.widgets
import rich.syntax
from util import Compatibility, measured_function
from util.constants import SIZE2LANGUAGES
from .basehandler import BaseHandler
from .register import register_handler


@register_handler
class TextHandler(BaseHandler):
    @staticmethod
    def supports(file: Path) -> Compatibility:
        import mimetypes
        mime, _ = mimetypes.guess_type(file.name)
        if mime and mime.startswith("text/"):
            return Compatibility.DEFAULT
        return Compatibility.NONE

    def compose(self) -> textual.app.ComposeResult:
        yield textual.widgets.Static(markup=False)

    def on_mount(self):
        text = self.query_one(textual.widgets.Static)
        syntax = self.get_rendered_syntax()
        text.update(syntax)

    @measured_function
    def get_rendered_syntax(self) -> rich.syntax.Syntax:
        content = self.filepath.read_text()
        lexer = rich.syntax.Syntax.guess_lexer(path=str(self.filepath))
        logging.debug(f"guessed language is {lexer!r}")
        return rich.syntax.Syntax(
            code=content,
            lexer=lexer,
            theme='ansi_dark',
            dedent=False,
            line_numbers=False,
            # highlight_lines={2,3,4,5,6,7,8},
            # code_width=80,
            tab_size=2 if lexer in SIZE2LANGUAGES else 4,
            word_wrap=False,
            background_color=None,
            indent_guides=False,
            padding=(0, 1),
        )