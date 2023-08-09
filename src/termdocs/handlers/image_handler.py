#!/usr/bin/python3
# -*- coding=utf-8 -*-
r"""

"""
import logging
import mimetypes
import typing as t
from pathlib import Path
import textual.app
import textual.events
import textual.widget
import textual.binding
import textual.reactive
import textual.containers
from widgets.detail_image import DetailImage
from widgets.color_image import ColorImage
from .basehandler import BaseHandler
from .register import register_handler


@register_handler
class ImageHandler(BaseHandler):
    @staticmethod
    def supports(filepath: Path):
        mime, _ = mimetypes.guess_type(filepath.name)
        return mime and mime.startswith("image/")

    detailed: bool = textual.reactive.reactive(False)

    def compose(self) -> textual.app.ComposeResult:
        yield textual.containers.Container()

    async def set_widget(self, widget: textual.widget.Widget):
        container = self.query_one(textual.containers.Container)
        await container.remove_children()
        await container.mount(widget)

    async def on_mount(self):
        await self.update()

    async def update(self):
        await self.set_widget(
            (DetailImage if self.detailed else ColorImage)(src=str(self.filepath))
        )

    async def on_mouse_down(self):
        self.detailed = not self.detailed
        await self.update()
