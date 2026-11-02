"""Compare registered versions; alias writes require an explicit --apply."""

from __future__ import annotations

import argparse
import math
import os

from mlflow import MlflowClient


def decide(candidate: float, champion: float, n: int) -> tuple[str, float, float]:
    if (
        not all(math.isfinite(p) and 0 <= p <= 1 for p in (candidate, champion))
        or n <= 0
    ):
        raise ValueError("Accuracies must be finite proportions and n must be positive")
    # p is the incumbent accuracy: uncertainty in the baseline being surpassed.
    se = math.sqrt(champion * (1 - champion) / n)
    threshold = champion + 2 * se
    return ("champion" if candidate >= threshold else "challenger", se, threshold)


def promote(client, version: str, n: int | None = None, apply: bool = False) -> dict:
    name = "food11"
    candidate = client.get_model_version(name, version)
    champion = client.get_model_version_by_alias(name, "champion")
    if str(candidate.version) == str(champion.version):
        raise ValueError("Candidate is already champion")
    if not candidate.run_id or not champion.run_id:
        raise ValueError("Both versions must have producing run IDs")
    runs = [client.get_run(v.run_id) for v in (candidate, champion)]
    accuracies = [run.data.metrics["test_accuracy"] for run in runs]
    sizes = [run.data.params.get("test_size") for run in runs]
    if n is None:
        if not all(sizes) or sizes[0] != sizes[1]:
            raise ValueError(
                "Missing or unequal test_size records; supply verified --n"
            )
        n = int(sizes[0])
    elif any(size is not None and int(size) != n for size in sizes):
        raise ValueError("--n conflicts with recorded test_size")
    alias, se, threshold = decide(*accuracies, n)
    result = {
        "decision": alias,
        "candidate_accuracy": accuracies[0],
        "champion_accuracy": accuracies[1],
        "standard_error": se,
        "threshold": threshold,
        "n": n,
        "champion_version": str(champion.version),
    }
    if apply:
        current = client.get_model_version_by_alias(name, "champion")
        if str(current.version) != str(champion.version):
            raise ValueError("Champion changed during evaluation; retry")
        for key, value in result.items():
            client.set_model_version_tag(
                name, version, f"quality_gate.{key}", str(value)
            )
        client.set_registered_model_alias(name, alias, version)
    print(f"{'APPLIED' if apply else 'DRY RUN'}: {result}")
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", required=True)
    parser.add_argument(
        "--n", type=int, help="Verified size of the shared evaluation set"
    )
    parser.add_argument(
        "--apply", action="store_true", help="Write decision tags and alias"
    )
    args = parser.parse_args()
    client = MlflowClient(
        tracking_uri=os.getenv("MLFLOW_TRACKING_URI", "http://127.0.0.1:5000")
    )
    try:
        promote(client, args.version, args.n, args.apply)
    except (ValueError, KeyError) as exc:
        parser.exit(1, f"Quality gate failed: {exc}\n")


if __name__ == "__main__":
    main()
