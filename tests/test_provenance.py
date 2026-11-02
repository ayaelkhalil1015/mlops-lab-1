import shutil
from pathlib import Path

import pytest

from food11.provenance import evaluation_revision


def make_evaluation(root):
    (root / "Bread").mkdir(parents=True)
    shutil.copyfile(
        Path(__file__).parent / "fixtures/bread.jpg", root / "Bread/bread.jpg"
    )


def test_revision_survives_relocation_but_detects_content_change(tmp_path):
    original = tmp_path / "original"
    make_evaluation(original)
    copied = tmp_path / "copy"
    shutil.copytree(original, copied)
    revision = evaluation_revision(original)
    assert revision.startswith("sha256:")
    assert evaluation_revision(copied) == revision
    (copied / "Bread/bread.jpg").write_bytes(b"changed")
    assert evaluation_revision(copied) != revision


def test_revision_detects_label_change(tmp_path):
    make_evaluation(tmp_path)
    before = evaluation_revision(tmp_path)
    (tmp_path / "Bread").rename(tmp_path / "Dessert")
    assert evaluation_revision(tmp_path) != before


def test_missing_and_empty_evaluation_are_rejected(tmp_path):
    for path in [tmp_path / "missing", tmp_path]:
        with pytest.raises(ValueError):
            evaluation_revision(path)
