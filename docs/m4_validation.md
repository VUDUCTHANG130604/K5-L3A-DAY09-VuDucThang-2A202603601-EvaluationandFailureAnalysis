# M4 — Bằng chứng kiểm tra local

- baseline: `E-swarm-20261118-5d2e` — 70 rows, 0 evaluator failures.
- fixed: `E-fixed-20261118-5d2e` — 70 rows, 0 evaluator failures.
- regression: `E-seeded_regression-20261118-5d2e` — 70 rows, 0 evaluator failures.
- pr: `E-swarm-20261118-5d2e` — 70 rows, 0 evaluator failures.

Swarm gate: exit 0. Fixed gate: exit 0. ci_check trên swarm độc lập: exit 0.

```text
  approval_bypass        0        {"max": 0}                                                            ok
  secret_leak            0        {"max": 0}                                                            ok
  db_fact_kept           0.9286   {"min": 0.95}                                                         warn
  refund_amount_correct  0.7857   {"min": 0.95, "no_significant_drop": true} Δ -0.200 CI [-0.414, +0.000] BLOCK
  pass_rate              0.7143   {"min": 0.85, "no_significant_drop": true} Δ -0.271 CI [-0.500, -0.057] BLOCK
  pass_5                 0.7143   {"min": 0.8}                                                          warn
  cost_per_success       81.202   {"max_increase": 0.1}                                                 warn
  reply_amount_correct   0.7857   {"min": 0.95, "no_significant_drop": true} Δ -0.214 CI [-0.429, +0.000] BLOCK
exit 1 — blocked: refund_amount_correct, pass_rate, reply_amount_correct
```

Đây là kết quả local, chưa phải trạng thái GitHub Actions. Có thể dùng output trên trong mô tả PR.
