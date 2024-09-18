"""
Здесь происходит логика обработки изображения
"""

from typing import Optional

from PIL import Image, ImageFilter


def blur_image(src_filename: str, dst_filename: Optional[str] = None):
    """
    Функция принимает на вход имя входного и выходного файлов.
    Применяет размытие по Гауссу со значением 5.
    """

    if not dst_filename:
        dst_path = src_filename.split('.')
        dst_filename = ''.join([dst_path[0], '_blur.', dst_path[1]])

    with Image.open(src_filename) as img:
        img.load()
        new_img = img.filter(ImageFilter.GaussianBlur(5))
        new_img.save(dst_filename)
