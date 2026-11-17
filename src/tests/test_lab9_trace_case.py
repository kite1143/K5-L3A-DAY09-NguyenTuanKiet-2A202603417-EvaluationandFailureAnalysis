"""Regression test cho docs/trace_case.md: C-002@11 (FM-03 ticket_trust).

Bước sai đầu tiên là event 3 `model_override {"delay_days": 5}`: ticket nói 5 ngày,
DB ghi 2 ngày. `DbFactKept` phải bắt được trên shape lỗi và im lặng trên `fixed`.
"""

import tempfile
from pathlib import Path

import pytest

pytestmark = pytest.mark.student


@pytest.fixture(scope="module")
def run_trial():
    from lab8.db import load_json, load_jsonl
    from lab9 import variants
    from lab9.eval import WORLD, make_task

    variants.register()
    claims = load_jsonl(Path("data/public_claims.jsonl"))
    labels = {c["claim_id"]: c["expected"] for c in claims}

    def run(shape: str, claim_id: str, seed: int = 11) -> dict:
        with tempfile.TemporaryDirectory(prefix="lab9-trace-", ignore_cleanup_errors=True) as tmp:
            task = make_task(shape, load_json(WORLD), claims, labels, Path(tmp))
            return task({"claim_id": claim_id, "seed": seed})

    return run


def _db_fact_kept(trial: dict) -> bool:
    from pydantic_evals.evaluators import EvaluatorContext

    from lab9.graders import DbFactKept

    ctx = EvaluatorContext(name="t", inputs={}, metadata=None, expected_output={}, output=trial,
                           duration=0.0, _span_tree=None, attributes={}, metrics={})
    return DbFactKept().evaluate(ctx).value


def test_ticket_trust_override_is_the_first_wrong_step(run_trial):
    trial = run_trial("seeded_regression", "C-002")
    events = trial["events"]
    assert events[2]["kind"] == "model_override"
    assert events[2]["payload"] == {"delay_days": 5}
    assert _db_fact_kept(trial) is False
    # Policy needs >= 3 days and the DB says 2: this money must not move.
    assert trial["snapshot"]["refund_vnd"] == 20000
    assert trial["lab8_pass"] is False


def test_fixed_control_keeps_the_db_fact(run_trial):
    trial = run_trial("fixed", "C-002")
    assert [e for e in trial["events"] if e["kind"] == "model_override"] == []
    assert _db_fact_kept(trial) is True
    assert trial["snapshot"]["refund_vnd"] == 0
    assert trial["lab8_pass"] is True
