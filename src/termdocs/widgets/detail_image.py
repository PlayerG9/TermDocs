#!/usr/bin/python3
# -*- coding=utf-8 -*-
r"""

"""
import logging
import math
from textual.app import RenderableType
from PIL import Image
from ._image_base import ImageBase


OFFSET = 0x2800

X0 = 0
L1 = 1
L2 = 2
L3 = 4
R1 = 8
R2 = 16
R3 = 32
L4 = 64
R4 = 128
OFFSETMAP = {
    (0, 0): L1,
    (0, 1): L2,
    (0, 2): L3,
    (0, 3): L4,
    (1, 0): R1,
    (1, 1): R2,
    (1, 2): R3,
    (1, 3): R4,
}


class DetailImage(ImageBase):
    @staticmethod
    def image_boundary(img: Image.Image) -> int:
        total = 0
        for y in range(img.height):
            for x in range(img.width):
                light, alpha = img.getpixel((x, y))
                total += (light + 1) * alpha
        return round(total / (img.width * img.height))

    def render(self) -> RenderableType:
        if self._image is None:
            return self._message.center(self.size.width)
        logging.debug(f"Rendering Image: {self._src} as {self.size}")
        img = self._image.convert('LA')
        img.thumbnail((self.size.width * 2, self.size.height * 4))
        tw, th = math.ceil(img.width / 2), math.ceil(img.height / 4)
        boundary = self.image_boundary(img)
        invert = boundary < (50 * 255)
        lines = []
        for ty in range(th):
            characters = []
            for tx in range(tw):
                b = X0
                for oy in range(4):
                    for ox in range(2):
                        rx, ry = (tx * 2) + ox, (ty * 4) + oy
                        try:
                            light, alpha = img.getpixel((rx, ry))
                        except IndexError:
                            pass
                        else:
                            color = (light + 1) * alpha
                            if color < boundary if invert else color > boundary:
                                b |= OFFSETMAP[(ox, oy)]
                characters.append(chr(OFFSET + b))
            lines.append(''.join(characters))
        return '\n'.join(lines)
        # return '\n'.join(line.center(self.size.width) for line in lines)
