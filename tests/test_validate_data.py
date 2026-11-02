import shutil

from PIL import Image

from food11.data import CLASSES, SPLITS
from food11.validate_data import validate


def make_dataset(root):
    for split_index, split in enumerate(SPLITS):
        for index, category in enumerate(CLASSES):
            folder = root / split / category
            folder.mkdir(parents=True)
            Image.new("RGB", (128, 128), (split_index * 80, index * 20, 1)).save(
                folder / "image.png"
            )


def test_valid_and_temporary_duplicate(tmp_path, capsys):
    make_dataset(tmp_path)
    assert validate(tmp_path, min_per_class=1)
    source = tmp_path / "training" / "Bread" / "image.png"
    target = tmp_path / "validation" / "Bread" / "duplicate.png"
    try:
        shutil.copyfile(source, target)
        assert not validate(tmp_path, min_per_class=1)
        assert "duplicate across splits" in capsys.readouterr().out
    finally:
        target.unlink()
    assert validate(tmp_path, min_per_class=1)


def test_bad_images_counts_structure_and_distribution(tmp_path, capsys):
    make_dataset(tmp_path)
    folder = tmp_path / "training" / "Bread"
    (folder / "bad.jpg").write_bytes(b"not an image")
    Image.new("L", (10, 10)).save(folder / "wrong.png")
    (tmp_path / "evaluation" / "unexpected").mkdir()
    assert not validate(tmp_path, min_per_class=2, tau=0)
    output = capsys.readouterr().out
    for message in [
        "cannot read image",
        "expected RGB",
        "expected exactly",
        "images <",
        "distribution:",
    ]:
        assert message in output


def test_missing_root_cli(tmp_path):
    import subprocess
    import sys

    result = subprocess.run(
        [sys.executable, "-m", "food11.validate_data", str(tmp_path / "missing")],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 1
    assert "FAIL: dataset validation" in result.stdout
