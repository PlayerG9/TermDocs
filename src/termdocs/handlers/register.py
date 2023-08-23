#!/usr/bin/python3
# -*- coding=utf-8 -*-
r"""

"""
import typing as t
from .basehandler import BaseHandler


HANDLERS: t.List[t.Type[BaseHandler]] = []


def register_handler(cls: t.Type[BaseHandler]):
    HANDLERS.append(cls)
    return cls
