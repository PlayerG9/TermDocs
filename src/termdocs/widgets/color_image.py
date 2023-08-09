#!/usr/bin/python3
# -*- coding=utf-8 -*-
r"""
Customised Version of
https://github.com/davep/textual-canvas/blob/main/textual_canvas/canvas.py
"""
import functools
import logging
import math
import typing as t
from PIL import Image
from rich.text import Text
import textual.app
import textual.widget
import textual.color
from ._image_base import ImageBase


RGB = t.Tuple[int, int, int]
RGBA = t.Tuple[int, int, int, int]


class ColorImage(ImageBase):
    @staticmethod
    def image_brightness(img: Image.Image) -> int:
        r"""
        Copied from Pillow.Image.Image.convert()
        When translating a color image to greyscale (mode "L"),
        the library uses the ITU-R 601-2 luma transform::

            L = R * 299/1000 + G * 587/1000 + B * 114/1000
        """
        total = 0
        pixel_count = 0
        # r/g/b-factor
        rf, gf, bf = 299 / 1000, 587 / 1000, 114 / 1000
        for y in range(img.height):
            for x in range(img.width):
                r, g, b, a = img.getpixel((x, y))
                if a < 50:  # ignore almost not visible pixel
                    continue
                total += (r*rf + g*gf + b*bf) * (a / 255)
                pixel_count += 1
        return round(total / pixel_count)

    def render(self) -> textual.app.RenderableType:
        if self.image is None:
            return self._message.center(self.size.width)
        if self.cached:
            return self.cached

        img = self.image.convert('RGBA')
        img.thumbnail((self.size.width, self.size.height * 2))

        # not using
        # f"\033[48;2;{tr};{tg};{tb}m\033[38;2;{br};{bg};{bb}m\u2584"
        # to *greatly* improve performance by only adding tcodes on color change

        lines = []
        last_top_color: t.Optional[RGBA] = None
        last_bottom_color: t.Optional[RGBA] = None

        if img.getextrema()[3][0] < 255:  # check image has alpha
            # background-r/g/b
            # manual way depending on the brightness of the image
            # br, bg, bb = (255, 255, 255) if self.image_brightness(img) < 128 else (0, 0, 0)
            # "smart" way by just grabbing the background
            br, bg, bb, _ = self.background_colors[0]

            @functools.lru_cache()
            def get_color(rgba: RGBA) -> RGB:
                cr, cg, cb, a = rgba  # color-r/g/b
                if a == 255:  # no need to make calculations
                    return cr, cg, cb
                if a == 0:  # no need to make calculations
                    return br, bg, bb
                ia = 255 - a  # inverted alpha
                return (
                    int((br*ia + cr*a) / 255),
                    int((bg*ia + cg*a) / 255),
                    int((bb*ia + cb*a) / 255),
                )
        else:
            def get_color(rgba: RGBA) -> RGB:
                return rgba[:3]

        for y in range(math.ceil(img.height / 2)):
            characters = []
            for x in range(img.width):
                character = "\u2584"
                top = y * 2
                top_color = img.getpixel((x, top))
                if top_color != last_top_color:
                    last_top_color = top_color
                    r, g, b = get_color(top_color)
                    character = f"\033[48;2;{r};{g};{b}m{character}"
                bottom = y * 2 + 1
                bottom_color = img.getpixel((x, bottom)) if bottom < img.height else (0, 0, 0, 0)
                if bottom_color != last_bottom_color:
                    last_bottom_color = bottom_color
                    r, g, b = get_color(bottom_color)
                    character = f"\033[38;2;{r};{g};{b}m{character}"

                characters.append(character)

            lines.append(''.join(characters))
        return Text.from_ansi('\n'.join(lines) + '\033[39m\033[49m')
