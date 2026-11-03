"""Verify recorded Q10 arithmetic without MLflow, model loading, or writes."""

import json
import math
from pathlib import Path


def main() -> None:
    results = json.loads(
        Path(__file__).with_name("lab5-q10-results.json").read_text()
    )
    baseline, weak, candidate = results["evaluations"]
    revision = results["dataset"]["split_fingerprints"]["evaluation"]
    assert len({row["version"] for row in results["evaluations"]}) == 3
    for row in results["evaluations"]:
        assert row["n"] == 1096
        assert row["evaluation_revision"] == revision
        assert math.isclose(row["accuracy"], row["correct"] / row["n"], abs_tol=1e-15)
    p = baseline["correct"] / baseline["n"]
    se = math.sqrt(p * (1 - p) / baseline["n"])
    threshold = p + 2 * se
    for row in (weak, candidate):
        decision = results["dry_runs"][row["role"]]
        expected = "champion" if row["accuracy"] >= threshold else "challenger"
        assert decision["decision"] == expected
        assert decision["provenance_status"] == "verified"
        assert decision["evaluation_revision"] == revision
        assert decision["n"] == baseline["n"]
        for key, value in (("standard_error", se), ("threshold", threshold)):
            assert math.isclose(decision[key], value, rel_tol=0, abs_tol=1e-15)
        print(f"Isolated v{row['version']}: {row['correct']}/{row['n']} -> {expected}")
    best = max(
        results["training"], key=lambda row: (row["val_accuracy"], -row["val_loss"])
    )
    assert len(results["training"]) == 20
    assert best["epoch"] == results["selected_epoch"] == 16
    assert results["isolated_aliases"] == {"champion": "1"}
    assert results["aliases_applied_to_candidates"] is False
    audit = results["preservation_audit"]
    assert audit["original_mini_images_unchanged"] == 3292
    assert audit["all_1096_evaluation_images_preserved"] is True
    assert audit["production_aliases_unchanged"] is True
    print(f"SE={se:.17f}; threshold={threshold:.16f}")
    print(f"Minimum qualifying correct count: {math.ceil(threshold * baseline['n'])}")
    print("PASS: recorded results are consistent; no promotion is applied.")


if __name__ == "__main__":
    main()
