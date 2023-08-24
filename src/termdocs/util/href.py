#!/usr/bin/python3
# -*- coding=utf-8 -*-
r"""

"""
import re
import os.path as p
from pathlib import Path
import typing as t


WEB_URL_RE = re.compile(r"^https?://")
DATE_URL_RE = re.compile(r"^data:(?P<mimetype>[\w\-.]+/[\w\-.]+)(?:;(?P<encoding>\w+))?,(?P<data>.*)$")


class HyperRef:
    def __init__(self, href: t.Union[str, Path]):
        self._href = str(href)

    def __str__(self) -> str:
        return self._href

    def __repr__(self) -> str:
        return f"<{self._href[-50:]}>"

    def as_path(self) -> Path:
        return Path(self._href)

    def absolute(self, to: t.Union[str, Path] = None) -> 'HyperRef':
        if not self.check_is_file():
            raise TypeError("href is not for a file")
        elif to:
            if isinstance(to, str):
                to = Path(to)
            if to.is_file():
                to = to.parent
            return HyperRef((to / self._href).absolute())
        else:
            return HyperRef(p.abspath(self._href))

    def check_is_idref(self: t.Union['HyperRef', str, Path]) -> bool:
        href = self._href if isinstance(self, HyperRef) else str(self)
        return href.startswith('#')  # maybe better with regex?

    def check_is_url(self: t.Union['HyperRef', str, Path]) -> bool:
        href = self._href if isinstance(self, HyperRef) else str(self)
        return WEB_URL_RE.match(href) is not None

    def check_is_data(self: t.Union['HyperRef', str, Path]) -> bool:
        href = self._href if isinstance(self, HyperRef) else str(self)
        return DATE_URL_RE.match(href) is not None

    def check_is_file(self: t.Union['HyperRef', str, Path]) -> bool:
        return not any((
            HyperRef.check_is_url(self),
            HyperRef.check_is_data(self),
            HyperRef.check_is_idref(self),
        ))

    def check_is_absolute(self: t.Union['HyperRef', str, Path]):
        href = self._href if isinstance(self, HyperRef) else str(self)
        return HyperRef.check_is_file(href) and p.isabs(href)
