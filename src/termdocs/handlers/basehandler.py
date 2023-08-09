#!/usr/bin/python3
# -*- coding=utf-8 -*-
r"""

"""
import typing as t
from pathlib import Path
from abc import abstractmethod
import textual.widget
import textual.reactive


class BaseHandler(textual.widget.Widget):
    filepath: Path = textual.reactive.reactive(None, layout=True)

    @staticmethod
    @abstractmethod
    def supports(file: Path) -> int:
        raise NotImplementedError()

    def __init__(
            self,
            path: t.Optional[Path] = None,
            *,
            name: t.Optional[str] = None,
            id: t.Optional[str] = None,
            classes: t.Optional[str] = None,
            disabled: bool = False,
    ):
        super().__init__(name=name, id=id, classes=classes, disabled=disabled)
        self.filepath = path
