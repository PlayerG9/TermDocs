#!/usr/bin/python3
# -*- coding=utf-8 -*-
r"""

"""
import io
import re
import logging
import mimetypes
import time
import typing as t
import os.path as p
import urllib.parse
import httpx
import textual.widget
from textual.reactive import reactive, var
import textual.timer
import cairosvg
from PIL import Image


class ImageBase(textual.widget.Widget):
    _message: str = reactive("<No Image set>", layout=True)
    _src: t.Optional[str] = None
    _start_time: t.Optional[float] = None
    _last_frame_update: t.Optional[float] = 0.0
    _image: t.Optional[Image.Image] = reactive(None, layout=True)
    _is_animated: bool = False
    _timer: t.Optional[textual.timer.Timer] = None
    _cached_frames: t.List[t.Tuple[int, t.Optional[textual.widget.RenderableType]]] = var(list)

    @property
    def image(self) -> t.Optional[Image.Image]:
        return self._image

    @image.setter
    def image(self, new: Image.Image):
        self._image = new
        self._start_time = time.time()
        self._is_animated = getattr(self._image, 'is_animated', False)
        self.stop_frame_updates()
        if self._is_animated:
            self.stop_frame_updates()
        else:
            self._image.thumbnail((1000, 1000))  # pre-shrink for ?performance-gain?

    def update_current_frame(self):
        if not self._is_animated:
            return
        time_offset = (time.time() - self._start_time)
        total_frame = round(time_offset / (self._image.info["duration"] / 1000))
        frame = total_frame % self._image.n_frames
        fps = round(1 / (time.time() - self._last_frame_update), 2)
        self._last_frame_update = time.time()
        logging.debug(f"Update to frame={frame} with fps={fps}")
        self._image.seek(frame)

    def start_frame_updates(self):
        self.stop_frame_updates()
        self._start_time = time.time()
        # ~5fps
        self._timer = self.set_interval(1 / 5, self.request_refresh)

    def stop_frame_updates(self):
        if self._timer:
            self._timer.stop()
            self._timer = None

    def on_enter(self) -> None:
        self.start_frame_updates()

    def on_leave(self) -> None:
        self.stop_frame_updates()

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

    def request_refresh(self):
        self.refresh()

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
            with open(path, 'rb') as file:
                buffer = io.BytesIO(file.read())
                buffer.name = file.name
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
        self._cached_frames.clear()

    @property
    def cached(self) -> t.Optional[textual.widget.RenderableType]:
        frame = self._image.tell()
        if frame >= len(self._cached_frames):
            return None
        for_width, rendered = self._cached_frames[frame]
        if for_width == self.size.width:
            return rendered
        else:
            return None

    @cached.setter
    def cached(self, rendered: textual.widget.RenderableType):
        frame = self._image.tell()
        if len(self._cached_frames) <= frame:
            self._cached_frames.extend([(0, None)] * (frame + 1 - len(self._cached_frames)))
        self._cached_frames[frame] = (self.size.width, rendered)
