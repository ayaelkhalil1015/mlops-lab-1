"""Content-and-label fingerprint for the evaluation split used by a training run."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


def evaluation_revision(evaluation_dir: Path) -> str:
    """Hash relative paths (including class labels) and file contents, not mtimes.

    Run on the validated, fixed evaluation split before training. The revision
    describes actual files rather than assuming a DVC pointer matches a checkout.
    """
    if not evaluation_dir.is_dir():
        raise ValueError(f"Evaluation split not found: {evaluation_dir}")
    manifest = {
        path.relative_to(evaluation_dir).as_posix(): hashlib.sha256(
            path.read_bytes()
        ).hexdigest()
        for path in sorted(evaluation_dir.rglob("*"))
        if path.is_file()
    }
    if not manifest:
        raise ValueError(f"Evaluation split is empty: {evaluation_dir}")
    payload = json.dumps(manifest, sort_keys=True, separators=(",", ":")).encode()
    return "sha256:" + hashlib.sha256(payload).hexdigest()
