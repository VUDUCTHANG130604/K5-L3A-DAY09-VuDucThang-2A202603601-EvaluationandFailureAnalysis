# Complete M0–M4 Core evaluation and release gate

Core evaluation now labels all 14 public items, calibrates the replay judges, and grades approval, refund amounts, DB overrides and reply/ledger agreement. Paired percentile bootstrap compares item means across the five fixed seeds. The harness map is version 1.2 and the eval card/PRD include generated report values and confidence intervals.

Includes the Lab 8 source overlay required by the starter repository, public fixtures, and script-generated baseline/fixed/regression reports. No Lab 8 source was edited during M4 or Core closeout.

Validation on 2026-11-18:

- Core student tests: 18 passed; smoke: M0 PASS; eval set: 0 problems.
- Independent swarm rerun matches baseline; swarm gate, fixed gate and ci_check exit 0.
- Each report contains 70 distinct item/seed rows and no evaluator failures.
- Seeded regression gate exits 1 with the required pass_rate verdict:

```text
refund_amount_correct  0.7857  Δ -0.200 CI [-0.414, +0.000] BLOCK
pass_rate              0.7143  Δ -0.271 CI [-0.500, -0.057] BLOCK
reply_amount_correct   0.7857  Δ -0.214 CI [-0.429, +0.000] BLOCK
exit 1 — blocked: refund_amount_correct, pass_rate, reply_amount_correct
```

M5–M7 remain pending. GitHub Actions must pass before merge. Target this fork's main branch, not the instructor repository.

Cross-platform fix: JSONL files use LF via .gitattributes and explicit newline writing. Reports were regenerated with eval set SHA `5d2ebeb3d40b`; semantic items and thresholds are unchanged. A regression test verifies LF-only output on Windows.

GitHub Actions passed on `e62b2a9`: [Core workflow 44239263815](https://github.com/VUDUCTHANG130604/K5-L3A-DAY09-VuDucThang-2A202603601-EvaluationandFailureAnalysis/actions/runs/44239263815). The v2 job succeeds by omitting Advanced steps because baseline_v2 is absent; this does not claim M5–M7 completion.
