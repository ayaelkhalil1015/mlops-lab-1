from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from food11.promote import decide, promote


def client_for(candidate=0.9, champion=0.8, size="1000"):
    client = Mock()
    client.get_model_version.return_value = SimpleNamespace(
        version="2", run_id="candidate"
    )
    client.get_model_version_by_alias.return_value = SimpleNamespace(
        version="1", run_id="champion"
    )
    client.get_run.side_effect = [
        SimpleNamespace(
            data=SimpleNamespace(
                metrics={"test_accuracy": p}, params={"test_size": size} if size else {}
            )
        )
        for p in (candidate, champion)
    ]
    return client


def test_promotion_and_tags():
    client = client_for()
    result = promote(client, "2", apply=True)
    assert result["decision"] == "champion"
    assert result["standard_error"] == pytest.approx((0.8 * 0.2 / 1000) ** 0.5)
    client.set_registered_model_alias.assert_called_once_with("food11", "champion", "2")
    assert client.set_model_version_tag.call_count == len(result)


def test_challenger_preserves_champion():
    client = client_for(candidate=0.81)
    assert promote(client, "2", apply=True)["decision"] == "challenger"
    client.set_registered_model_alias.assert_called_once_with(
        "food11", "challenger", "2"
    )


def test_dry_run():
    client = client_for()
    promote(client, "2")
    client.set_registered_model_alias.assert_not_called()
    client.set_model_version_tag.assert_not_called()


def test_missing_size_and_explicit_size():
    with pytest.raises(ValueError, match="Missing"):
        promote(client_for(size=None), "2")
    assert promote(client_for(size=None), "2", n=1000)["n"] == 1000


@pytest.mark.parametrize(
    ("p", "q", "n"), [(float("nan"), 0.8, 100), (0.8, 1.1, 100), (0.8, 0.7, 0)]
)
def test_invalid_inputs(p, q, n):
    with pytest.raises(ValueError):
        decide(p, q, n)


def test_boundary():
    _, _, threshold = decide(0.9, 0.8, 1000)
    assert decide(threshold, 0.8, 1000)[0] == "champion"
    assert decide(threshold - 1e-9, 0.8, 1000)[0] == "challenger"


def test_missing_metric_does_not_write():
    client = client_for()
    client.get_run.side_effect = None
    client.get_run.return_value = SimpleNamespace(
        data=SimpleNamespace(metrics={}, params={})
    )
    with pytest.raises(KeyError):
        promote(client, "2", n=1000, apply=True)
    client.set_registered_model_alias.assert_not_called()


def test_conflicting_size():
    with pytest.raises(ValueError, match="conflicts"):
        promote(client_for(), "2", n=10, apply=True)
