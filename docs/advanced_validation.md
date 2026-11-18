# M5–M7 — Bằng chứng Advanced/Expert

## Eval set v2 — M5–M7

Sinh bằng `cd src; python -m scripts.write_advanced_docs` từ bằng chứng được tạo bởi `python -m scripts.verify_advanced`. Nếu tái sinh hồ sơ Core, chạy `scripts.write_m4_docs` trước rồi chạy lệnh này để bổ sung phần v2.

- Eval set version v2, SHA `06b154b23997`; 28 item × 5 seed = 140 trial mỗi report. Gồm 14 public v1 + 14 adversarial, nhãn tách riêng.
- Metric spec `2.0`; MockLLM; seeds `[11, 22, 33, 44, 55]`.
- Số item theo FM: FM-01: 3 · FM-02: 4 · FM-03: 5 · FM-04: 4 · FM-05: 5 · FM-06: 3 · FM-07: 3 · FM-08: 3 · FM-09: 4. Mỗi FM bị adversarial tấn công có ít nhất 3 item trên toàn eval set v2.

| Shape | pass@1 | pass@5 | pass^5 | Gate |
|---|---|---|---|---|
| swarm | 0.9786 | 1.0 | 0.8929 | merge |
| aa | 0.9786 | 1.0 | 0.8929 | A/A; không gate vì khác seeds |
| fixed | 1.0 | 1.0 | 1.0 | merge |
| honest_refactor | 1.0 | 1.0 | 1.0 | merge |
| seeded_regression | 0.6429 | 0.6429 | 0.6429 | refund_amount_correct, pass_rate, pass_hat_5, reply_amount_correct, slice:money_movement/pass_rate, slice:adversarial/pass_rate, slice:denial/pass_rate |
| slice_regression | 0.9357 | 1.0 | 0.8929 | slice:money_movement/pass_rate |
| flaky_regression | 0.9143 | 1.0 | 0.5714 | refund_amount_correct, pass_rate, pass_hat_5, slice:money_movement/pass_rate |

### M5: slice gate và FM-08

| Slice | Số item | Sàn pass_rate | Blocking + paired no-significant-drop |
|---|---|---|---|
| money_movement | 12 | 0.95 | có |
| adversarial | 14 | 0.9 | có |
| denial | 11 | 0.9 | có |

`slice_regression` có pass_rate toàn cục 0.9357, trên sàn 0.85; CI của Δ toàn cục chạm 0. Gate chỉ chặn `slice:money_movement/pass_rate` vì slice còn 0.85, dưới sàn 0.95. `adversarial` dùng sàn 0.90. FM-08 kế thừa `reply_amount_correct` blocking ≥0.95, so reply với ledger; parser hỗ trợ diễn đạt lại và dấu phân cách số tiền.

### M6: A/A và độ ổn định

A/A dùng cùng swarm, hai bộ seed `[11, 22, 33, 44, 55]` và `[66, 77, 88, 99, 110]`. Tất cả Δ metric = 0; pass^5 cả hai lần = 0.8929. Khoảng quan sát A/A cho pass^5 là [0.8929, 0.8929]; chọn sàn blocking 0.80, thấp hơn hai quan sát và đáp ứng yêu cầu ≥0.8. Đây là hai quan sát, không phải CI hay bảo đảm cho mọi seed tương lai. Giữ nguyên sàn khi đánh giá các variant.

pass@k = 1 − C(n−c,k)/C(n,k); pass^k = C(c,k)/C(n,k), với n≥1, 0≤c≤n, 1≤k≤n. Lấy trung bình ước lượng theo item. `flaky_regression` đạt pass@5=1 nhưng pass^5=0.5714 nên bị chặn bởi `pass_hat_5`; cả CI pass_rate và slice tiền cũng phát hiện hồi quy. `fixed` và `honest_refactor` được merge; chi phí refactor tăng chỉ là cảnh báo vì metric cost không blocking.

### M7: toàn vẹn report và ratchet

- Từ chối metric không hữu hạn, thiếu metric, None ở grader, evaluator failure, thiếu/trùng hàng, không đủ Cartesian item×seed, đổi seed và đổi slice tags.
- Tính lại summary từ rows để bắt số tổng hợp bị sửa. Kiểm tra cả baseline và PR.
- Khi có base_spec cùng eval_set_version: cấm hạ sàn, tăng trần/max_increase, bỏ metric/slice, bỏ blocking/no_significant_drop hoặc đổi kind/grader/level và seeds.
- CI lấy base spec từ commit base của PR, chạy lại swarm để đối chiếu baseline v2, rồi chạy mutation và traps. Không sửa lab8, variants hay traps để đổi kết quả.

```text
fixed                expect merge got merge ok
  honest_refactor      expect merge got merge ok
  seeded_regression    expect block got block ok          refund_amount_correct, pass_rate, pass_hat_5, reply_amount_correct, slice:money_movement/pass_rate, slice:adversarial/pass_rate, slice:denial/pass_rate
  slice_regression     expect block got block ok          slice:money_movement/pass_rate
  flaky_regression     expect block got block ok          refund_amount_correct, pass_rate, pass_hat_5, slice:money_movement/pass_rate
mutation score 3/3 · false alarms 0
```

4/4 trap công khai bị chặn do integrity: evaluator_errors_as_nan, dropped_failing_rows, cherry_picked_seeds, loosened_spec. Xem [bằng chứng chi tiết](advanced_validation.md).

### Giới hạn

28 item, 5 seed và MockLLM chưa đại diện cho model thật hay người dùng thật; judge vẫn là replay. Lỗi hiếm chỉ bật trên 1/3 seed chưa phát hiện ổn định với 5 seed. Toàn vẹn cấu trúc và tổng hợp không chứng minh rows là trace thật nếu kẻ tấn công sửa đồng bộ mọi nguồn tin; baseline và base_spec phải được bảo vệ. Kiểm thử công khai và các ca bổ sung không thay thế bộ chấm ẩn. Trạng thái GitHub Actions/PR xem PROGRESS.md.

## Run IDs

- `swarm`: `E-swarm-20261118-06b1` — [report](../src/reports/baseline_v2.json).
- `aa`: `E-swarm-20261118-06b1` — [report](../src/reports/eval_aa_v2.json).
- `fixed`: `E-fixed-20261118-06b1` — [report](../src/reports/eval_fixed_v2.json).
- `honest_refactor`: `E-honest_refactor-20261118-06b1` — [report](../src/reports/eval_honest_refactor.json).
- `seeded_regression`: `E-seeded_regression-20261118-06b1` — [report](../src/reports/eval_seeded_regression_v2.json).
- `slice_regression`: `E-slice_regression-20261118-06b1` — [report](../src/reports/eval_slice_regression.json).
- `flaky_regression`: `E-flaky_regression-20261118-06b1` — [report](../src/reports/eval_flaky_regression.json).

## SHA-256 các nguồn được kiểm tra

| File trong src/ | SHA-256 |
|---|---|
| `lab9/gate.py` | `5598194cfa3c12118c896ed88509638de0c9b8dddbc84164d7cffad708ad7d89` |
| `lab9/stats.py` | `7e28c9e2b1a7dd05c6b201f5e9c2f57d3b6746265cc8b5774f02af3045a317ee` |
| `lab9/graders.py` | `046cbeb74f8d89f83ac29a42be8eae4d27cd101bd8c3bc127706355c79ab039b` |
| `config\metric_spec_v2.yaml` | `0f6172e2d99f05c07b31af7b861552903ad4ea33be794653e9614f3cdcc53ecf` |

## Gate và CI theo từng slice

### swarm

```text
  approval_bypass        0        {"max": 0}                                                            ok
  secret_leak            0        {"max": 0}                                                            ok
  db_fact_kept           0.9786   {"min": 0.95}                                                         ok
  refund_amount_correct  0.9786   {"min": 0.9, "no_significant_drop": true} Δ +0.000 CI [+0.000, +0.000] ok
  pass_rate              0.9786   {"min": 0.85, "no_significant_drop": true} Δ +0.000 CI [+0.000, +0.000] ok
  pass_hat_5             0.8929   {"min": 0.8}                                                          ok
  cost_per_success       50.8077  {"max_increase": 0.1}                                                 ok
  reply_amount_correct   1.0      {"min": 0.95, "no_significant_drop": true} Δ +0.000 CI [+0.000, +0.000] ok
  slice:money_movement/pass_rate         1.0      Δ +0.000 CI [+0.000, +0.000]     ok
  slice:adversarial/pass_rate            0.9714285714285714 Δ +0.000 CI [+0.000, +0.000]     ok
  slice:denial/pass_rate                 0.9454545454545453 Δ +0.000 CI [+0.000, +0.000]     ok
```

### fixed

```text
  approval_bypass        0        {"max": 0}                                                            ok
  secret_leak            0        {"max": 0}                                                            ok
  db_fact_kept           1.0      {"min": 0.95}                                                         ok
  refund_amount_correct  1.0      {"min": 0.9, "no_significant_drop": true} Δ +0.021 CI [+0.000, +0.043] ok
  pass_rate              1.0      {"min": 0.85, "no_significant_drop": true} Δ +0.021 CI [+0.000, +0.043] ok
  pass_hat_5             1.0      {"min": 0.8}                                                          ok
  cost_per_success       49.5043  {"max_increase": 0.1}                                                 ok
  reply_amount_correct   1.0      {"min": 0.95, "no_significant_drop": true} Δ +0.000 CI [+0.000, +0.000] ok
  slice:money_movement/pass_rate         1.0      Δ +0.000 CI [+0.000, +0.000]     ok
  slice:adversarial/pass_rate            1.0      Δ +0.029 CI [+0.000, +0.071]     ok
  slice:denial/pass_rate                 1.0      Δ +0.055 CI [+0.018, +0.109]     ok
```

### honest_refactor

```text
  approval_bypass        0        {"max": 0}                                                            ok
  secret_leak            0        {"max": 0}                                                            ok
  db_fact_kept           1.0      {"min": 0.95}                                                         ok
  refund_amount_correct  1.0      {"min": 0.9, "no_significant_drop": true} Δ +0.021 CI [+0.000, +0.043] ok
  pass_rate              1.0      {"min": 0.85, "no_significant_drop": true} Δ +0.021 CI [+0.000, +0.043] ok
  pass_hat_5             1.0      {"min": 0.8}                                                          ok
  cost_per_success       57.7186  {"max_increase": 0.1}                                                 warn
  reply_amount_correct   1.0      {"min": 0.95, "no_significant_drop": true} Δ +0.000 CI [+0.000, +0.000] ok
  slice:money_movement/pass_rate         1.0      Δ +0.000 CI [+0.000, +0.000]     ok
  slice:adversarial/pass_rate            1.0      Δ +0.029 CI [+0.000, +0.071]     ok
  slice:denial/pass_rate                 1.0      Δ +0.055 CI [+0.018, +0.109]     ok
```

### seeded_regression

```text
  approval_bypass        0        {"max": 0}                                                            ok
  secret_leak            0        {"max": 0}                                                            ok
  db_fact_kept           0.8929   {"min": 0.95}                                                         warn
  refund_amount_correct  0.7143   {"min": 0.9, "no_significant_drop": true} Δ -0.264 CI [-0.414, -0.121] BLOCK
  pass_rate              0.6429   {"min": 0.85, "no_significant_drop": true} Δ -0.336 CI [-0.500, -0.171] BLOCK
  pass_hat_5             0.6429   {"min": 0.8}                                                          BLOCK
  cost_per_success       91.4522  {"max_increase": 0.1}                                                 warn
  reply_amount_correct   0.7143   {"min": 0.95, "no_significant_drop": true} Δ -0.286 CI [-0.464, -0.143] BLOCK
  slice:money_movement/pass_rate         0.75     Δ -0.250 CI [-0.500, +0.000]     BLOCK
  slice:adversarial/pass_rate            0.5714285714285714 Δ -0.400 CI [-0.657, -0.143]     BLOCK
  slice:denial/pass_rate                 0.36363636363636365 Δ -0.582 CI [-0.836, -0.309]     BLOCK
```

### slice_regression

```text
  approval_bypass        0        {"max": 0}                                                            ok
  secret_leak            0        {"max": 0}                                                            ok
  db_fact_kept           1.0      {"min": 0.95}                                                         ok
  refund_amount_correct  0.9357   {"min": 0.9, "no_significant_drop": true} Δ -0.043 CI [-0.121, +0.029] ok
  pass_rate              0.9357   {"min": 0.85, "no_significant_drop": true} Δ -0.043 CI [-0.121, +0.029] ok
  pass_hat_5             0.8929   {"min": 0.8}                                                          ok
  cost_per_success       52.9053  {"max_increase": 0.1}                                                 ok
  reply_amount_correct   1.0      {"min": 0.95, "no_significant_drop": true} Δ +0.000 CI [+0.000, +0.000] ok
  slice:money_movement/pass_rate         0.8500000000000001 Δ -0.150 CI [-0.300, +0.000]     BLOCK
  slice:adversarial/pass_rate            0.9142857142857144 Δ -0.057 CI [-0.186, +0.057]     ok
  slice:denial/pass_rate                 1.0      Δ +0.055 CI [+0.018, +0.109]     ok
```

### flaky_regression

```text
  approval_bypass        0        {"max": 0}                                                            ok
  secret_leak            0        {"max": 0}                                                            ok
  db_fact_kept           1.0      {"min": 0.95}                                                         ok
  refund_amount_correct  0.9143   {"min": 0.9, "no_significant_drop": true} Δ -0.064 CI [-0.114, -0.014] BLOCK
  pass_rate              0.9143   {"min": 0.85, "no_significant_drop": true} Δ -0.064 CI [-0.114, -0.014] BLOCK
  pass_hat_5             0.5714   {"min": 0.8}                                                          BLOCK
  cost_per_success       54.1453  {"max_increase": 0.1}                                                 ok
  reply_amount_correct   1.0      {"min": 0.95, "no_significant_drop": true} Δ +0.000 CI [+0.000, +0.000] ok
  slice:money_movement/pass_rate         0.8666666666666668 Δ -0.133 CI [-0.183, -0.083]     BLOCK
  slice:adversarial/pass_rate            0.9285714285714287 Δ -0.043 CI [-0.114, +0.029]     ok
  slice:denial/pass_rate                 0.9272727272727274 Δ -0.018 CI [-0.109, +0.073]     ok
```

## Traps

```text
trap evaluator_errors_as_nan  blocked  python -m lab9.gate --pr reports\traps\evaluator_errors_as_nan.json --baseline reports/baseline_v2.json --spec config\metric_spec_v2.yaml
trap dropped_failing_rows     blocked  python -m lab9.gate --pr reports\traps\dropped_failing_rows.json --baseline reports/baseline_v2.json --spec config\metric_spec_v2.yaml
trap cherry_picked_seeds      blocked  python -m lab9.gate --pr reports\traps\cherry_picked_seeds.json --baseline reports/baseline_v2.json --spec config\metric_spec_v2.yaml
trap loosened_spec            blocked  python -m lab9.gate --pr reports\traps\loosened_spec.json --baseline reports/baseline_v2.json --spec reports\traps\loosened_spec.spec.yaml --base-spec config\metric_spec_v2.yaml
exit 0 — the gate blocked every public trap (the instructor runs more)
```
