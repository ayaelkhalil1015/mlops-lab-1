# Lab 5 final evidence

`lab5-q10-results.json` is a sanitized export of the actual isolated CPU experiment:
three registered model versions and fresh evaluation runs, correct counts and
accuracies, split fingerprints, all 20 validation epochs, checkpoint selection,
dry-run gate results, artifact hashes, and preservation audit. It contains no
tracking database, model weights, personal credentials, or production writes.

Verify the recorded arithmetic using only the Python standard library:

```bash
python3 lab/evidence/verify_lab5_q10.py
```

This checks the recorded evidence; it does not reevaluate model predictions or
prove that historical models were trained without leakage. Isolated v3 qualifies
as champion under the lab gate; no candidate alias was applied. Full methodology,
CI/PR links and limitations are in `lab/lab5.md`.

The complete local experiment was copied to `.lab5-local/q10-20261103/`, with
`.lab5-local/q10-20261103-sha256.json` covering every archived file. This directory
is excluded by the local `.git/info/exclude` and must never be force-added.
It includes the isolated SQLite registry, artifacts, selected checkpoint, cleaned
data, original experiment scripts/logs and environment metadata. No production
tracking database or credentials were copied into this archive.

The registry snapshot retains its original `/tmp` artifact URIs. To inspect an
archived model later, use its relative `mlartifacts/models/<model-id>/artifacts`
path in a disposable working copy, or restore the isolated directory to its
original location. Do not point the production MLflow service at this snapshot.
The raw archive is local evidence, not an uploaded or Git-backed backup.

GHCR publication succeeded at the merged commit tag. Local pulling and running
that published image remain unverified because of the documented slow transfer;
no further full-image download was attempted for final submission.
