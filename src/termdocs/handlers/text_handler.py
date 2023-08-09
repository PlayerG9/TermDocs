#!/usr/bin/python3
# -*- coding=utf-8 -*-
r"""

"""
from pathlib import Path
import textual.app
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

    def render(self) -> textual.app.RenderableType:
        try:
            return rich.syntax.Syntax.from_path(
                path=str(self.filepath),
            )
        except Exception:
            return self.filepath.read_text()
