#!/usr/bin/python3
# -*- coding=utf-8 -*-
r"""

"""
import enum


class Compatibility(enum.IntEnum):
    NONE = enum.auto()
    FALLBACK = enum.auto()
    DEFAULT = enum.auto()
    HIGH = enum.auto()
