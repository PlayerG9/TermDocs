#!/usr/bin/python3
# -*- coding=utf-8 -*-
r"""

"""
import mimetypes
from pathlib import Path
import textual.app
import textual.events
import textual.widget
import textual.binding
import textual.reactive
import textual.containers
from widgets import ColorImage, DetailImage
from .basehandler import BaseHandler
from .register import register_handler


@register_handler
class ImageHandler(BaseHandler):
    @staticmethod
    def supports(filepath: Path):
        mime, _ = mimetypes.guess_type(filepath.name)
        return mime and mime.startswith("image/")

    detailed: bool = textual.reactive.reactive(False)

    async def watch_detailed(self):
        await self.update()

    def compose(self) -> textual.app.ComposeResult:
        yield textual.containers.Container()

    async def _set_image_widget(self, widget: textual.widget.Widget):
        container = self.query_one(textual.containers.Container)
        with self.app.batch_update():
            await container.remove_children()
            await container.mount(widget)

    async def on_mount(self):
        await self.update()

    async def update(self):
        await self._set_image_widget(
            (DetailImage if self.detailed else ColorImage)(src=str(self.filepath))
        )

    async def on_click(self, event: textual.events.Click):
        event.stop()
        self.detailed = not self.detailed
