import hashlib

import pytest
from test_validate_data import make_dataset

from food11.deduplicate_data import clean_copy
from food11.validate_data import validate


def hashes(root):
    return {
        str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in root.rglob("*")
        if p.is_file()
    }


def test_clean_copy_protects_evaluation_and_source(tmp_path):
    source, destination = tmp_path / "source", tmp_path / "clean"
    make_dataset(source)
    evaluation = source / "evaluation" / "Bread" / "image.png"
    (source / "training" / "Bread" / "duplicate.png").write_bytes(
        evaluation.read_bytes()
    )
    (source / "validation" / "Bread" / "duplicate.png").write_bytes(
        evaluation.read_bytes()
    )
    before = hashes(source)
    assert clean_copy(source, destination) == (33, 2)
    assert hashes(source) == before
    assert (
        destination / "evaluation" / "Bread" / "image.png"
    ).read_bytes() == evaluation.read_bytes()
    assert validate(destination, min_per_class=1)


def test_refuses_overwrite_and_nested_paths(tmp_path):
    source = tmp_path / "source"
    make_dataset(source)
    for destination in [source, source / "nested", tmp_path]:
        with pytest.raises(ValueError, match="separate"):
            clean_copy(source, destination)
    existing = tmp_path / "existing"
    existing.mkdir()
    with pytest.raises(ValueError, match="already exists"):
        clean_copy(source, existing)
