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
from collections import Counter
from pathlib import Path

from lab8.console import utf8_stdio
from lab9 import stats
from lab9.eval import SPEC, aggregate, load_spec, per_item
from lab9.graders import GRADERS


def _finite(value) -> bool:
    return isinstance(value, (int, float)) and math.isfinite(value)


def _ratchet(spec: dict, base_spec: dict) -> list[str]:
    if spec.get("eval_set_version") != base_spec.get("eval_set_version"):
        return []
    problems = []
    for section in ("metrics", "slices"):
        key = (lambda m: m["id"]) if section == "metrics" else (lambda m: (m["name"], m["metric"]))
        current = {key(m): m for m in spec.get(section, [])}
        for old in base_spec.get(section, []):
            identity = key(old)
            new = current.get(identity)
            if new is None:
                problems.append(f"ratchet: removed {section} {identity}")
                continue
            if old.get("blocking") and not new.get("blocking"):
                problems.append(f"ratchet: disabled blocking for {identity}")
            before = old.get("threshold", {}) if section == "metrics" else old
            after = new.get("threshold", {}) if section == "metrics" else new
            for threshold in ("min", "max", "max_increase"):
                if threshold in before and (threshold not in after or not _finite(after[threshold]) or
                    (after[threshold] < before[threshold] if threshold == "min" else after[threshold] > before[threshold])):
                    problems.append(f"ratchet: loosened {threshold} for {identity}")
            if before.get("no_significant_drop") and not after.get("no_significant_drop"):
                problems.append(f"ratchet: removed no_significant_drop for {identity}")
            for field in ("kind", "grader", "level"):
                if field in old and old[field] != new.get(field):
                    problems.append(f"ratchet: changed {field} for {identity}")
    if set(spec.get("seeds", [])) != set(base_spec.get("seeds", [])):
        problems.append("ratchet: changed seeds on the same eval set")
    return problems


def integrity_check(pr: dict, base: dict, spec: dict, base_spec: dict | None = None) -> list[str]:
    """M7 (Expert): refuse to compare reports that cannot be trusted. Return a list of problems
    (empty = trustworthy). A gate that passes a broken report is worse than no gate.
    Must catch at least:
      - any metric value in pr["metrics"] that is NaN or inf
      - len(pr["rows"]) != manifest items x len(manifest seeds)   (dropped / duplicated rows)
      - the (item_id, seed) set of PR differs from the baseline's (cherry-picked seeds/items)
      - pr["evaluator_failures"] non-empty, or a row whose value for a graded spec metric is
        None (a crashed grader silently scores as "missing" and drops out of the mean)
      - base_spec given and a threshold in spec is LOOSER than in base_spec for the same
        eval-set version (ratchet: max may not rise, min may not fall, a blocking metric may
        not become non-blocking, a metric may not disappear; the same for spec["slices"],
        including dropping no_significant_drop)
      - an item's slice tags in PR rows differ from the baseline's (relabelling an item out of a
        slice hides its regression from the slice gate)"""
    problems = []
    base_rows = base.get("rows") if isinstance(base.get("rows"), list) else []
    graded = [m["id"] for m in spec["metrics"] if m["id"] in GRADERS or m.get("grader") == "code" or
              any(isinstance(r, dict) and m["id"] in r for r in base_rows)]
    required = {m["id"] for m in spec["metrics"]}
    if len(required) != len(spec["metrics"]):
        problems.append("duplicate metric definitions")
    slice_ids = [(s["name"], s["metric"]) for s in spec.get("slices", [])]
    if len(slice_ids) != len(set(slice_ids)):
        problems.append("duplicate slice definitions")
    for section in (spec["metrics"], spec.get("slices", [])):
        for definition in section:
            limits = definition.get("threshold", definition)
            for key in ("min", "max", "max_increase"):
                if key in limits and not _finite(limits[key]):
                    problems.append(f"invalid spec threshold {key}")
    identities = {}
    tags_of = {}
    for name, report in (("PR", pr), ("baseline", base)):
        manifest, rows, metrics = report.get("manifest", {}), report.get("rows"), report.get("metrics")
        if not isinstance(manifest.get("eval_set_sha"), str) or not manifest["eval_set_sha"]:
            problems.append(f"{name}: missing eval-set SHA")
        if not isinstance(rows, list) or not isinstance(metrics, dict):
            problems.append(f"{name}: missing rows or metrics")
            continue
        if report.get("evaluator_failures"):
            problems.append(f"{name}: evaluator failures")
        for mid, value in metrics.items():
            if not _finite(value):
                problems.append(f"{name}: non-finite/missing metric {mid}")
        for mid in required - metrics.keys():
            problems.append(f"{name}: missing metric {mid}")
        seeds, item_count = manifest.get("seeds"), manifest.get("items")
        if (not isinstance(seeds, list) or not seeds or
            any(type(s) is not int for s in seeds) or len(seeds) != len(set(seeds)) or
            type(item_count) is not int or item_count < 1):
            problems.append(f"{name}: invalid item/seed manifest")
            continue
        if len(rows) != item_count * len(seeds):
            problems.append(f"{name}: row count does not match items x seeds")
        pairs, tags, valid = [], {}, True
        for row in rows:
            if not isinstance(row, dict) or not isinstance(row.get("item_id"), str) or type(row.get("seed")) is not int:
                problems.append(f"{name}: malformed item/seed row")
                valid = False
                continue
            item, seed = row["item_id"], row["seed"]
            pairs.append((item, seed))
            slices = row.get("slices", [])
            if not isinstance(slices, list) or any(not isinstance(t, str) for t in slices):
                problems.append(f"{name}: malformed slices for {item}")
                valid = False
                continue
            tags.setdefault(item, set()).add(frozenset(slices))
            for mid in graded:
                value = row.get(mid)
                if not _finite(value) or value not in (0, 1):
                    problems.append(f"{name}: missing/invalid grader {mid} on {item}@{seed}")
                    valid = False
            if "cost" in row and (not _finite(row["cost"]) or row["cost"] < 0):
                problems.append(f"{name}: invalid cost on {item}@{seed}")
                valid = False
            if "cost_per_success" in required and "cost" not in row:
                problems.append(f"{name}: missing cost on {item}@{seed}")
                valid = False
        counts = Counter(pairs)
        items = {item for item, _ in pairs}
        expected = {(item, seed) for item in items for seed in seeds}
        if any(n != 1 for n in counts.values()) or set(pairs) != expected or len(items) != item_count:
            problems.append(f"{name}: incomplete/duplicated item x seed grid")
        if any(len(t) != 1 for t in tags.values()):
            problems.append(f"{name}: inconsistent slice tags across seeds")
        identities[name], tags_of[name] = set(pairs), tags
        # Recompute aggregates so an edited summary cannot conceal failing rows.
        if valid and rows:
            calculated = aggregate([{**r, "cost": r.get("cost", 0)} for r in rows], graded,
                                   k_values=spec.get("pass_k", []))
            for definition in spec["metrics"]:
                if definition.get("kind") == "safety" and definition["id"] in graded:
                    calculated[definition["id"]] = sum(r[definition["id"]] for r in rows)
            for mid, actual in calculated.items():
                if mid in metrics and _finite(metrics[mid]) and (not _finite(actual) or
                    not math.isclose(metrics[mid], actual, rel_tol=0, abs_tol=1e-4)):
                    problems.append(f"{name}: aggregate {mid} does not match rows")
    if identities.get("PR") != identities.get("baseline"):
        problems.append("PR item/seed set differs from baseline")
    if tags_of.get("PR") != tags_of.get("baseline"):
        problems.append("PR slice tags differ from baseline")
    pr_seeds, base_seeds = pr.get("manifest", {}).get("seeds", []), base.get("manifest", {}).get("seeds", [])
    if (isinstance(pr_seeds, list) and isinstance(base_seeds, list) and
        all(type(s) is int for s in pr_seeds + base_seeds) and set(pr_seeds) != set(base_seeds)):
        problems.append("PR manifest seeds differ from baseline")
    if "seeds" in spec and set(spec["seeds"]) != set(base.get("manifest", {}).get("seeds", [])):
        problems.append("spec seeds differ from baseline")
    if base_spec is not None:
        problems.extend(_ratchet(spec, base_spec))
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
    for rule in spec.get("slices", []):
        name, metric = rule["name"], rule["metric"]
        identity = f"slice:{name}/{metric}"
        a, b = per_item(pr, metric, name), per_item(base, metric, name)
        note, failed = "", False
        value = sum(a.values()) / len(a) if a else None
        if not a or a.keys() != b.keys() or any(not _finite(v) for v in [*a.values(), *b.values()]):
            failed, note = True, "missing/misaligned slice evidence"
        else:
            failed = "min" in rule and value < rule["min"]
            failed |= "max" in rule and value > rule["max"]
            if rule.get("no_significant_drop"):
                keys = sorted(a)
                if len(keys) < 2:
                    failed, note = True, "insufficient items for paired CI"
                else:
                    d, lo, hi = stats.paired_bootstrap([a[k] for k in keys], [b[k] for k in keys],
                        n_resamples=bs.get("n_resamples", 1000), rng=bs.get("rng", 2027),
                        confidence=bs.get("confidence", 0.95))
                    note = f"Δ {d:+.3f} CI [{lo:+.3f}, {hi:+.3f}]"
                    failed |= hi < 0
        if failed and rule.get("blocking"):
            blocked.append(identity)
        verdict = "BLOCK" if failed and rule.get("blocking") else "warn" if failed else "ok"
        lines.append(f"  {identity:<38} {value!s:<8} {note:<32} {verdict}")
    return blocked, lines


def check(pr: dict, base: dict, spec: dict, base_spec: dict | None = None) -> tuple[list[str], list[str]]:
    if pr.get("manifest", {}).get("eval_set_sha") != base.get("manifest", {}).get("eval_set_sha"):
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
            if len(keys) < 2 or a.keys() != b.keys():
                blocked.append(mid)
                lines.append(f"  {mid} BLOCK: insufficient/misaligned paired evidence")
                continue
            d, lo, hi = stats.paired_bootstrap([a[k] for k in keys], [b[k] for k in keys],
                                               n_resamples=bs.get("n_resamples", 1000), rng=bs.get("rng", 2027),
                                               confidence=bs.get("confidence", 0.95))
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
