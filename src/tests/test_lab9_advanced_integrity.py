"""Additional corruption and honest-refactor cases, independent of variant names."""
import copy
from itertools import combinations

import pytest

from lab9 import gate, stats
from tests.test_lab9_advanced import ROWS, SPEC, _report

pytestmark = pytest.mark.student


@pytest.fixture
def clean():
    return _report(copy.deepcopy(ROWS), {"pass_rate": 1.0})


@pytest.mark.parametrize("change", ["duplicate", "seeds", "slice", "none", "crash", "inf", "summary", "missing"])
def test_integrity_rejects_corruption(clean, change):
    bad = copy.deepcopy(clean)
    if change == "duplicate":
        bad["rows"][-1] = copy.deepcopy(bad["rows"][0])
    elif change == "seeds":
        bad["manifest"]["seeds"] = [1, 3]
        for row in bad["rows"]:
            if row["seed"] == 2:
                row["seed"] = 3
    elif change == "slice":
        for row in bad["rows"]:
            row["slices"] = []
    elif change == "none":
        bad["rows"][0]["pass_rate"] = None
    elif change == "crash":
        bad["evaluator_failures"] = ["grader crashed"]
    elif change == "inf":
        bad["metrics"]["pass_rate"] = float("inf")
    elif change == "summary":
        bad["rows"][0]["pass_rate"] = False
    else:
        bad["metrics"].pop("pass_rate")
    assert gate.check(bad, clean, SPEC)[0] == ["integrity"]


def test_integrity_accepts_reordered_rows_and_seed_list(clean):
    honest = copy.deepcopy(clean)
    honest["rows"].reverse()
    honest["manifest"]["seeds"].reverse()
    assert gate.integrity_check(honest, clean, SPEC) == []


@pytest.mark.parametrize("change", ["drop_metric", "blocking", "min", "max", "increase", "drop_slice", "slice_min", "slice_ci"])
def test_ratchet_prevents_weaker_rules(clean, change):
    before = copy.deepcopy(SPEC)
    before["metrics"][0]["threshold"].update(max=1, max_increase=0.1)
    before["slices"] = [{"name": "denial", "metric": "pass_rate", "min": 0.9,
                         "blocking": True, "no_significant_drop": True}]
    after = copy.deepcopy(before)
    if change == "drop_metric":
        after["metrics"] = []
    elif change == "blocking":
        after["metrics"][0]["blocking"] = False
    elif change in ("min", "max", "increase"):
        key = "max_increase" if change == "increase" else change
        after["metrics"][0]["threshold"][key] = 0 if key == "min" else 2
    elif change == "drop_slice":
        after["slices"] = []
    elif change == "slice_min":
        after["slices"][0]["min"] = 0.1
    else:
        after["slices"][0]["no_significant_drop"] = False
    assert gate.integrity_check(clean, clean, after, before)
    assert gate.integrity_check(clean, clean, before, before) == []


def test_slice_ci_detects_drop_even_when_floor_passes(clean):
    bad = copy.deepcopy(clean)
    for row in bad["rows"]:
        if "denial" in row["slices"]:
            row["pass_rate"] = False
    spec = {**SPEC, "slices": [{"name": "denial", "metric": "pass_rate", "min": 0,
                               "no_significant_drop": True, "blocking": True}]}
    assert gate.slice_check(bad, clean, spec)[0] == ["slice:denial/pass_rate"]


def test_empty_blocking_slice_fails_closed(clean):
    spec = {**SPEC, "slices": [{"name": "priority", "metric": "pass_rate", "blocking": True}]}
    assert gate.slice_check(clean, clean, spec)[0] == ["slice:priority/pass_rate"]


@pytest.mark.parametrize("args", [(0, 0, 1), (5, -1, 2), (-1, 0, 1), (5, 2, 6),
                                  (5, 2, 0), (5.0, 2, 1), (True, 1, 1)])
def test_both_pass_estimators_reject_invalid_input(args):
    for fn in (stats.pass_at_k, stats.pass_hat_k):
        with pytest.raises(ValueError):
            fn(*args)


def test_pass_estimators_match_exhaustive_sampling():
    for n in range(1, 8):
        for c in range(n + 1):
            for k in range(1, n + 1):
                samples = list(combinations(range(n), k))
                at = sum(any(i < c for i in s) for s in samples) / len(samples)
                every = sum(all(i < c for i in s) for s in samples) / len(samples)
                assert stats.pass_at_k(n, c, k) == pytest.approx(at)
                assert stats.pass_hat_k(n, c, k) == pytest.approx(every)


@pytest.mark.parametrize("text,amount", [("Đã hoàn 35,000 VND", 35000),
    ("Đã hoàn tiền 35 000 đồng", 35000), ("Đã thanh toán 250.000đ, LogiX hoàn phí 35.000đ.", 35000)])
def test_refund_extraction_preserves_honest_wording(text, amount):
    from lab9.graders import extract_reply_amount
    assert extract_reply_amount(text) == amount


def test_reply_grader_checks_ledger_instead_of_label():
    from lab9.graders import ReplyAmountCorrect
    from tests.test_lab9_graders import ctx, trial
    assert not ReplyAmountCorrect().evaluate(ctx(trial(refund_vnd=20000, events=[
        {"kind": "reply", "payload": {"text": "Đã hoàn 35.000đ"}}]))).value
