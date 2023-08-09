#!/usr/bin/python3
# -*- coding=utf-8 -*-
r"""

"""
import io
import mimetypes
import typing as t
import os.path as p
import urllib.parse
import httpx
import textual.widget
from textual.reactive import reactive
import cairosvg
from PIL import Image


class ImageBase(textual.widget.Widget):
    _message: str = reactive("<No Image set>", layout=True)
    _src: t.Optional[str] = None
    _image: t.Optional[Image.Image] = reactive(None, layout=True)

    @property
    def image(self) -> t.Optional[Image.Image]:
        return self._image

    @image.setter
    def image(self, new: Image.Image):
        self._image = new.copy()
        self._image.thumbnail((1000, 1000))  # pre-shrink for ?performance-gain?

    def __init__(
            self,
            src: t.Optional[str] = None,
            *,
            id: t.Optional[str] = None,
            classes: t.Optional[str] = None,
    ):
        super().__init__(id=id, classes=classes)
        self._src = src

    async def on_mount(self):
        if self._src is not None:
            await self.load(self._src)

    async def load(self, src: str):
        self._src = src
        if src.startswith("http://") or src.startswith("https://"):
            await self.load_web(url=src)
        elif p.isfile(src):
            await self.load_file(path=p.abspath(src))
        else:
            raise FileNotFoundError(src)

    async def load_web(self, url: str):
        worker = self.run_worker(self._load_web(url), exclusive=True)
        await worker.wait()
        if worker.error:
            self._message = f"{type(worker.error).__name__}: {worker.error}"

    async def _load_web(self, url: str):
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            if not response.is_success:
                self._message = f"{response.status_code}: {response.reason_phrase}"
            else:
                buffer = io.BytesIO(await response.aread())
                buffer.name = p.basename(urllib.parse.urlparse(url).path)
                self._from_buffer(buffer)

    async def load_file(self, path: str):
        try:
            with open(path, 'rb') as buffer:
                self._from_buffer(buffer)
        except (FileNotFoundError, IsADirectoryError) as error:
            self._message = f"{type(error).__name__}: {error}"

    @staticmethod
    def _convert_svg2png(buffer: t.BinaryIO) -> t.BinaryIO:
        out = io.BytesIO()
        cairosvg.svg2png(file_obj=buffer, write_to=out)
        out.seek(0)
        return out

    def _from_buffer(self, buffer: t.BinaryIO):
        buffer.seek(0)
        mime, _ = mimetypes.guess_type(buffer.name)
        if mime and mime.startswith("image/svg"):
            buffer = self._convert_svg2png(buffer)
        self.image = Image.open(buffer)
