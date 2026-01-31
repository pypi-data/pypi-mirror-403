"""
@Author: 馒头 (chocolate)
@Email: neihanshenshou@163.com
@File: __init__.py
@Time: 2023/12/9 18:00
"""

import os
from typing import Any

from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont

current_path = os.path.abspath(__file__)
BASE_DIR = os.path.abspath(os.path.dirname(current_path) + os.path.sep)


def compress_image(filename: str):
    """
    不改变图片尺寸压缩到指定大小
    """
    im = Image.open(filename)
    im.save(filename, quality=100)


def processing(filename: str, image="", text: str = "⊙", color: str = 'red', w: Any = 0, h: Any = 0, font_size=45):
    """
    点击截图增加水印
    :param filename: 源图片文件
    :param image: 另存为(可选)
    :param text: 水印文案
    :param color: 水印颜色
    :param w: 水印位置 宽 比: 0 ~ 1
    :param h: 水印位置 高 比: 0 ~ 1
    :param font_size: 水印字体大小
    :return:
    """
    font_dir = os.path.join(BASE_DIR, "font/song.ttc")
    font = ImageFont.truetype(font_dir, font_size)
    im1 = Image.open(filename)

    draw = ImageDraw.Draw(im1)
    img_width, img_height = im1.size
    x = img_width * w - font_size / 2
    y = img_height * h - font_size / 2
    draw.text(xy=(x, y), text=text, fill=color, font=font, stroke_width=2)  # 设置文字位置/内容/颜色/字体/加粗
    ImageDraw.Draw(im1)  # Just draw it!
    im1.save(image or filename)

    compress_image(filename)
