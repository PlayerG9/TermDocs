#!/usr/bin/python3
# -*- coding=utf-8 -*-
r"""

"""
import io
import re
import time
import base64
import logging
import mimetypes
import typing as t
import os.path as p
import urllib.parse
from pathlib import Path
import httpx
import textual.widget
from textual.reactive import reactive, var
import textual.timer
import cairosvg
from PIL import Image


WEB_IMAGE_MAX_SIZE = 1024*1024*10  # ~10MB
WEB_URL_RE = re.compile(r"^https?://")
DATE_URL_RE = re.compile(r"^data:(?P<mimetype>[\w\-.]+/[\w\-.]+)(?:;(?P<encoding>\w+))?,(?P<data>.*)$")
DECODE_MAP = {
    'base16': base64.b16decode,
    'base32': base64.b32decode,
    'base64': base64.b64decode,
    'base85': base64.b85decode,
}


class ImageBase(textual.widget.Widget):
    DEFAULT_CSS = r"""
    ImageBase {
        text-align: center;
    }
    """

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
        if not self._is_animated:
            # note: removes frames
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
        # todo: skip frames if rendering takes to long
        self._timer = self.set_interval(1 / 5, self.request_refresh)

    def stop_frame_updates(self):
        if self._timer:
            self._timer.stop()
            self._timer = None

    def on_enter(self) -> None:
        if self._is_animated:
            self.start_frame_updates()

    def on_leave(self) -> None:
        self.stop_frame_updates()

    def __init__(
            self,
            src: t.Union[str, Path, None] = None,
            *,
            id: t.Optional[str] = None,
            classes: t.Optional[str] = None,
    ):
        super().__init__(id=id, classes=classes)
        self._src = str(src) if isinstance(src, Path) else src

    async def on_mount(self):
        if self._src is not None:
            await self.load(self._src)

    def request_refresh(self):
        self.refresh()

    async def load(self, src: t.Union[str, Path]):
        self._src = src = str(src)
        self._message = "Loading..."
        try:
            if self.check_is_url(src):
                await self.load_web_url(url=src)
            elif self.check_is_data(src):
                await self.load_data_url(url=src)
            elif p.isfile(src):
                await self.load_file(path=src)
            else:
                raise FileNotFoundError(src)
        except Exception as error:
            logging.error(f"Failed to load resource: {src}", exc_info=error)
            self._message = f"{type(error).__name__}: {error}"

    async def load_web_url(self, url: str):
        self._load_web(url)

    @textual.work(exclusive=True)
    async def _load_web(self, url: str):
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url)
                response.raise_for_status()
                if response.headers.get('Content-Length') > WEB_IMAGE_MAX_SIZE:
                    raise PermissionError("Web-Resource is too big")
                buffer = io.BytesIO()
                async for chunk in response.aiter_bytes(1024*10):  # ~10Kb/chunk
                    if response.num_bytes_downloaded > WEB_IMAGE_MAX_SIZE:
                        raise PermissionError("Web-Resource is too big")
                    buffer.write(chunk)
                buffer.name = p.basename(urllib.parse.urlparse(url).path)
                self._from_buffer(buffer)
        except Exception as error:
            logging.error(f"Failed to load resource: {url}", exc_info=error)
            self._message = f"{type(error).__name__}: {error}"

    async def load_data_url(self, url: str):
        match = DATE_URL_RE.match(url)
        groups = match.groupdict()
        mimetype = groups.get("mimetype")
        encoding = groups.get("encoding")
        # https://stackoverflow.com/questions/2941995/python-ignore-incorrect-padding-error-when-base64-decoding
        data = groups.get("data") + '=='
        if encoding not in DECODE_MAP:
            raise LookupError(f"Unsupported encoding: {encoding}")
        decoder = DECODE_MAP[encoding]
        buffer = io.BytesIO(decoder(data))
        self._from_buffer(buffer, mime=mimetype)

    async def load_file(self, path: str):
        with open(path, 'rb') as file:
            buffer = io.BytesIO(file.read())
            buffer.name = file.name
        self._from_buffer(buffer)

    @staticmethod
    def _convert_svg2png(buffer: t.BinaryIO) -> t.BinaryIO:
        out = io.BytesIO()
        cairosvg.svg2png(file_obj=buffer, write_to=out)
        out.seek(0)
        return out

    def _from_buffer(self, buffer: t.BinaryIO, mime: t.Optional[str] = None):
        buffer.seek(0)
        if mime is None:
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

    @staticmethod
    def check_is_url(src: str) -> bool:
        return WEB_URL_RE.match(src) is not None

    @staticmethod
    def check_is_data(src: str) -> bool:
        return DATE_URL_RE.match(src) is not None

    @staticmethod
    def check_is_file(src: str) -> bool:
        return not ImageBase.check_is_url(src) and not ImageBase.check_is_data(src)
