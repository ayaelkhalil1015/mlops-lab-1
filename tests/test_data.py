import pytest
from PIL import Image

from food11.data import CLASSES, category_from_filename, resize_image


@pytest.mark.parametrize(
    ("filename", "expected"), [("0_12.jpg", "Bread"), ("10_3.jpg", "Vegetable-Fruit")]
)
def test_category(filename, expected):
    assert category_from_filename(filename) == expected


def test_resize():
    result = resize_image(Image.new("L", (512, 384)))
    assert result.mode == "RGB"
    assert result.size == (128, 128)


def test_classes():
    assert len(CLASSES) == 12
