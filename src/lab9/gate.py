"""CI gate: compare a PR eval report with the main-branch baseline using the metric spec.

    python -m lab9.gate --pr reports/eval_workflow.json --baseline reports/baseline_v1.json

exit 0 = merge, exit 1 = blocked. Safety metrics: max 0, no averaging away.
Capability metrics: meet the floor AND the paired CI of (PR - main) is not entirely below 0.
Thresholds may only get stricter on the same eval-set version (ratchet).
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

from lab8.console import utf8_stdio
from lab9 import stats
from lab9.eval import SPEC, load_spec, per_item


def _ratchet(spec: dict, base_spec: dict) -> list[str]:
    """Thresholds may only get stricter on the same eval-set version."""
    if spec.get("eval_set_version") != base_spec.get("eval_set_version"):
        return []                     # a new eval-set version starts a new baseline
    problems: list[str] = []
    base_metrics = {m["id"]: m for m in base_spec.get("metrics") or []}
    for mid, b in base_metrics.items():
        m = next((x for x in spec.get("metrics") or [] if x["id"] == mid), None)
        if m is None:
            problems.append(f"ratchet: metric {mid} disappeared")
            continue
        bt, mt = b.get("threshold") or {}, m.get("threshold") or {}
        if "max" in bt and ("max" not in mt or mt["max"] > bt["max"]):
            problems.append(f"ratchet: {mid} max {bt['max']} -> {mt.get('max')}")
        if "min" in bt and ("min" not in mt or mt["min"] < bt["min"]):
            problems.append(f"ratchet: {mid} min {bt['min']} -> {mt.get('min')}")
        if bt.get("no_significant_drop") and not mt.get("no_significant_drop"):
            problems.append(f"ratchet: {mid} dropped no_significant_drop")
        if b.get("blocking") and not m.get("blocking"):
            problems.append(f"ratchet: {mid} is no longer blocking")
    base_slices = {(s["name"], s["metric"]): s for s in base_spec.get("slices") or []}
    for key, b in base_slices.items():
        s = next((x for x in spec.get("slices") or [] if (x["name"], x["metric"]) == key), None)
        if s is None:
            problems.append(f"ratchet: slice {key[0]}/{key[1]} disappeared")
            continue
        if "min" in b and ("min" not in s or s["min"] < b["min"]):
            problems.append(f"ratchet: slice {key[0]}/{key[1]} min {b['min']} -> {s.get('min')}")
        if b.get("no_significant_drop") and not s.get("no_significant_drop"):
            problems.append(f"ratchet: slice {key[0]}/{key[1]} dropped no_significant_drop")
        if b.get("blocking") and not s.get("blocking"):
            problems.append(f"ratchet: slice {key[0]}/{key[1]} is no longer blocking")
    return problems


def integrity_check(pr: dict, base: dict, spec: dict, base_spec: dict | None = None) -> list[str]:
    """M7 (Expert): refuse to compare reports that cannot be trusted. Return a list of problems
    (empty = trustworthy). A gate that passes a broken report is worse than no gate."""
    problems: list[str] = []
    rows = pr.get("rows") or []
    manifest = pr.get("manifest") or {}

    for mid, value in (pr.get("metrics") or {}).items():
        if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
            problems.append(f"metric {mid} is {value}")

    items, seeds = manifest.get("items"), manifest.get("seeds") or []
    want = int(items or 0) * len(seeds)
    if len(rows) != want:
        problems.append(f"{len(rows)} rows, want {want} (items x seeds)")

    def pairs(rep: dict) -> set[tuple]:
        return {(r.get("item_id"), r.get("seed")) for r in rep.get("rows") or []}

    got, expected = pairs(pr), pairs(base)
    if len(got) != len(rows):
        problems.append("duplicate (item, seed) rows")
    if got != expected:
        missing = sorted(expected - got)[:3]
        extra = sorted(got - expected)[:3]
        problems.append(f"(item, seed) set differs from baseline: missing {missing}, extra {extra}")

    if pr.get("evaluator_failures"):
        problems.append(f"{len(pr['evaluator_failures'])} evaluator failure(s) in the PR report")
    graded = [m["id"] for m in spec.get("metrics") or [] if rows and m["id"] in rows[0]]
    missing_values = sorted({f"{r.get('item_id')}@{r.get('seed')}:{mid}"
                             for r in rows for mid in graded if r.get(mid) is None})
    if missing_values:
        problems.append(f"crashed grader scored as missing: {missing_values[:3]}"
                        + (f" (+{len(missing_values) - 3} more)" if len(missing_values) > 3 else ""))

    base_slices = {r.get("item_id"): tuple(r.get("slices") or []) for r in base.get("rows") or []}
    relabelled = sorted({str(r.get("item_id")) for r in rows
                         if r.get("item_id") in base_slices
                         and tuple(r.get("slices") or []) != base_slices[r.get("item_id")]})
    if relabelled:
        problems.append(f"slice tags differ from baseline: {relabelled[:3]}")

    if base_spec is not None:
        problems += _ratchet(spec, base_spec)
    return problems


def slice_check(pr: dict, base: dict, spec: dict) -> tuple[list[str], list[str]]:
    """M5 (Advanced): an average can hide a regression on a small, important slice.
    For each entry of spec["slices"] ({"name", "metric", "min"?, "no_significant_drop"?, "blocking"}):
      - value = mean of per_item(pr, metric, slice_name=name)
      - fail if below "min", or if no_significant_drop and the paired CI over the slice's items
        lies entirely below 0
    Return (blocked ids like "slice:money_movement/pass_rate", report lines)."""
    blocked, lines = [], []
    bs = spec.get("bootstrap", {})
    for s in spec.get("slices") or []:
        name, metric = s["name"], s["metric"]
        sid = f"slice:{name}/{metric}"
        got = per_item(pr, metric, slice_name=name)
        if not got:
            verdict, note, value = "missing", "no items in this slice", None
        else:
            value = sum(got.values()) / len(got)
            verdict, note = "ok", ""
            if "min" in s and value < s["min"]:
                verdict = "fail"
            if s.get("no_significant_drop"):
                other = per_item(base, metric, slice_name=name)
                keys = sorted(set(got) & set(other))
                if keys:
                    d, lo, hi = stats.paired_bootstrap(
                        [got[k] for k in keys], [other[k] for k in keys],
                        n_resamples=bs.get("n_resamples", 1000), rng=bs.get("rng", 2027))
                    note = f"Δ {d:+.3f} CI [{lo:+.3f}, {hi:+.3f}]"
                    if hi < 0:
                        verdict = "fail"
        if verdict != "ok" and s.get("blocking"):
            blocked.append(sid)
        label = {"ok": "ok", "missing": "MISSING"}.get(verdict, "BLOCK" if s.get("blocking") else "warn")
        shown = "—" if value is None else f"{value:.4f}"
        lines.append(f"  {sid:<34} n={len(got):<3} mean={shown:<7} "
                     f"{json.dumps({k: v for k, v in s.items() if k in ('min', 'no_significant_drop')}):<34} "
                     f"{note:<24} {label}")
    return blocked, lines


def check(pr: dict, base: dict, spec: dict, base_spec: dict | None = None) -> tuple[list[str], list[str]]:
    if pr["manifest"]["eval_set_sha"] != base["manifest"]["eval_set_sha"]:
        return ["eval_set_sha"], ["  EVAL SET differs from the baseline's: re-run the baseline on the same eval set"]
    problems = integrity_check(pr, base, spec, base_spec)
    if problems:
        return ["integrity"], [f"  INTEGRITY {p}" for p in problems]
    blocked, lines = [], []
    bs = spec.get("bootstrap", {})
    for m in spec["metrics"]:
        mid, th, val = m["id"], m.get("threshold", {}), pr["metrics"].get(m["id"])
        verdict, note = "ok", ""
        if val is None:
            verdict = "missing"
        elif "max" in th and val > th["max"]:
            verdict = "fail"
        elif "min" in th and val < th["min"]:
            verdict = "fail"
        elif "max_increase" in th and base["metrics"].get(mid):
            if val > base["metrics"][mid] * (1 + th["max_increase"]):
                verdict = "fail"
        if th.get("no_significant_drop") and val is not None:
            a, b = per_item(pr, mid), per_item(base, mid)
            keys = sorted(set(a) & set(b))
            d, lo, hi = stats.paired_bootstrap([a[k] for k in keys], [b[k] for k in keys],
                                               n_resamples=bs.get("n_resamples", 1000), rng=bs.get("rng", 2027))
            note = f"Δ {d:+.3f} CI [{lo:+.3f}, {hi:+.3f}]"
            if hi < 0:
                verdict = "fail"
        if verdict != "ok" and m.get("blocking"):
            blocked.append(mid)
        label = {"ok": "ok", "missing": "MISSING"}.get(verdict, "BLOCK" if m.get("blocking") else "warn")
        lines.append(f"  {mid:<22} {val!s:<8} {json.dumps(th):<40} {note:<28} {label}")
    if spec.get("slices"):
        sb, sl = slice_check(pr, base, spec)
        blocked += sb
        lines += sl
    return blocked, lines


def main(argv: list[str] | None = None) -> int:
    utf8_stdio()
    ap = argparse.ArgumentParser(prog="lab9.gate")
    ap.add_argument("--pr", required=True)
    ap.add_argument("--baseline", required=True)
    ap.add_argument("--spec", default=str(SPEC))
    ap.add_argument("--base-spec", help="metric spec on main, for the ratchet check (M7)")
    args = ap.parse_args(argv)
    pr = json.loads(Path(args.pr).read_text(encoding="utf-8"))
    base = json.loads(Path(args.baseline).read_text(encoding="utf-8"))
    base_spec = load_spec(Path(args.base_spec)) if args.base_spec else None
    blocked, lines = check(pr, base, load_spec(Path(args.spec)), base_spec)
    print(f"gate: PR {pr['run_id']} vs main {base['run_id']} · eval set {pr['manifest']['eval_set_sha']}")
    print("\n".join(lines))
    if blocked:
        print(f"exit 1 — blocked: {', '.join(blocked)}")
        return 1
    print("exit 0 — merge")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
