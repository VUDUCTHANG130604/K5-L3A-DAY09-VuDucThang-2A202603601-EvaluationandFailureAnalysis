"""Generate v2 evidence through the official CLIs, then verify M5-M7 decisions.

Run from src/: python -m scripts.verify_advanced
Reports are generated, never edited. Fails immediately on an unexpected verdict.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from collections import Counter
from pathlib import Path

from lab9 import gate, traps
from lab9.eval import load_spec, per_item

SPEC = Path("config/metric_spec_v2.yaml")


def run(*args: str) -> str:
    result = subprocess.run([sys.executable, "-m", *args], capture_output=True, text=True,
                            encoding="utf-8", errors="replace")
    print(result.stdout, end="", flush=True)
    if result.returncode:
        raise RuntimeError(f"{' '.join(args)}: exit {result.returncode}\n{result.stderr}")
    return result.stdout


def main() -> None:
    run("lab9.evalset", "--v2")
    spec = load_spec(SPEC)
    files = {"swarm": "baseline_v2.json", "aa": "eval_aa_v2.json", "fixed": "eval_fixed_v2.json",
             "honest_refactor": "eval_honest_refactor.json", "seeded_regression": "eval_seeded_regression_v2.json",
             "slice_regression": "eval_slice_regression.json", "flaky_regression": "eval_flaky_regression.json"}
    reports = {}
    for name, file in files.items():
        print(f"\nEvaluating {name}...", flush=True)
        args = ["lab9.eval", "--shape", "swarm" if name == "aa" else name, "--spec", str(SPEC),
                "--out", str(Path("reports") / file)]
        if name == "aa":
            args += ["--seeds", "66,77,88,99,110"]
        run(*args)
        reports[name] = json.loads((Path("reports") / file).read_text(encoding="utf-8"))
    base = reports["swarm"]
    decisions = {}
    for name, report in reports.items():
        if name == "aa":
            continue
        blocked, lines = gate.check(report, base, spec, spec)
        print(f"\n{name}: {'block' if blocked else 'merge'}\n" + "\n".join(lines), flush=True)
        want_block = name.endswith("regression")
        assert bool(blocked) == want_block, (name, blocked)
        decisions[name] = {"blocked": blocked, "lines": lines}
    assert decisions["slice_regression"]["blocked"] == ["slice:money_movement/pass_rate"]
    assert "pass_hat_5" in decisions["flaky_regression"]["blocked"]
    delta = {k: round(reports["aa"]["metrics"][k] - v, 8) for k, v in base["metrics"].items()}
    assert all(v == 0 for v in delta.values()), delta
    reliability_rule = next(m for m in spec["metrics"] if m["id"] == "pass_hat_5")
    assert 0.8 <= reliability_rule["threshold"]["min"] < min(
        base["metrics"]["pass_hat_5"], reports["aa"]["metrics"]["pass_hat_5"])
    trap_results = {}
    for name, (report, changed_spec) in traps.build(reports["slice_regression"], spec).items():
        blocked, lines = gate.check(report, base, changed_spec or spec, spec)
        assert blocked == ["integrity"], (name, blocked, lines)
        trap_results[name] = {"blocked": blocked, "problems": lines}
    trap_output = run("lab9.traps", "--pr", "reports/eval_slice_regression.json", "--baseline",
                      "reports/baseline_v2.json", "--spec", str(SPEC))
    mutation_output = run("lab9.mutation", "--spec", str(SPEC), "--baseline", "reports/baseline_v2.json")
    items = [json.loads(line) for line in Path(spec["eval_set"]).read_text(encoding="utf-8").splitlines()]
    modes = Counter(fm for item in items for fm in item["failure_modes"])
    slices = {name: {metric: per_item(base, metric, name) for metric in ("pass_rate",)}
              for name in ("money_movement", "adversarial", "denial")}
    sources = ["lab9/gate.py", "lab9/stats.py", "lab9/graders.py", str(SPEC)]
    evidence = {"manifest": base["manifest"], "runs": {k: r["run_id"] for k, r in reports.items()},
                "files": files, "metrics": {k: r["metrics"] for k, r in reports.items()},
                "failure_mode_counts": dict(sorted(modes.items())), "slices": slices,
                "aa_seeds": reports["aa"]["manifest"]["seeds"], "aa_delta": delta,
                "decisions": decisions, "traps": trap_results, "trap_output": trap_output,
                "mutation_output": mutation_output,
                "sha256": {p: hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in sources}}
    Path("reports/advanced_validation.json").write_text(json.dumps(evidence, ensure_ascii=False, indent=2), encoding="utf-8")
    print("\nM5-M7 PASS: wrote reports/advanced_validation.json", flush=True)


if __name__ == "__main__":
    main()
