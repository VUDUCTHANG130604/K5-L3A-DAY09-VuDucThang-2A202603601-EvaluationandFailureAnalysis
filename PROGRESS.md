# Kế Hoạch & Tiến Độ Thực Hiện — Lab 9 (Evaluation & Failure Analysis)

> **Mã sinh viên:** `2A202603601` — **Họ và tên:** `Vũ Đức Thắng`
> **Repository:** `K5-L3A-DAY09-VuDucThang-2A202603601-EvaluationandFailureAnalysis`
> **Mục tiêu:** Hoàn thành 100/100 điểm (Core 60 · Advanced 25 · Expert 15) + Bonus 5

---

## 📊 Bảng Tổng Hợp Tiến Độ

| Mục | Hạng mục | Điểm | Trạng thái |
|:---:|:---|:---:|:---:|
| **M0** | Môi trường, tích hợp mã Day 8 & Eval set build | Tiên quyết | 🟢 Đã hoàn thành |
| **M1** | Failure Taxonomy ($\ge 5$ FM) & Gán nhãn Eval set v1 | 12đ | 🟢 Đã hoàn thành |
| **M2** | Judge-the-Judge Calibration & Audit ($\ge 5$ case) | 12đ | 🟢 Đã hoàn thành |
| **M3** | Trajectory Graders (ApprovalBypass, RefundAmount, FM-08) | 12đ | 🟢 Đã hoàn thành |
| **M4** | Paired Bootstrap & Release Gate (CI `eval-gate` xanh) | 15đ | 🟡 Core đã kiểm tra local; chờ push/PR và CI GitHub |
| **DOCS**| Hoàn thiện hồ sơ báo cáo (Eval card, PRD v1.1, Trace case) | 9đ | 🟢 Đã hoàn thành bản Core |
| **M5** | Eval Set v2, Adversarial Pack & Slice Gate | 10đ | ⚪ Chưa bắt đầu |
| **M6** | Phân tích nhiễu A/A & Thống kê $\text{pass}@k$, $\text{pass}^k$ | 15đ | ⚪ Chưa bắt đầu |
| **M7** | Gate chống gian lận (Integrity check, Ratchet, Traps) | 15đ | ⚪ Chưa bắt đầu |
| **BONUS** | Port grader sang Inspect AI / DeepEval | +5đ | ⚪ Tùy chọn |

---

## ⚠️ Quy Tắc "Sống Còn" (Tránh Bị Trừ Điểm)

- [ ] **Không sửa bất kỳ file nào trong `src/lab8/`** *(vi phạm trừ 10đ)*.
- [ ] **Không sửa tay các file `.json` trong `reports/`** *(vi phạm trừ 20đ)*.
- [ ] **Bắt buộc commit reports bằng `git add -f reports/*.json`** *(vì thư mục bị `.gitignore` bỏ qua)*.
- [ ] **Không gán nhãn inline trong file item `.jsonl`** *(nhãn phải nằm riêng trong `labels_v1.json`, vi phạm trừ 5đ)*.
- [ ] **Không nới lỏng ngưỡng trên cùng eval-set version** *(tuân thủ nguyên tắc Ratchet, vi phạm trừ 10đ)*.
- [ ] **Mở PR trong bản fork của chính mình** (`starter/d09` $\to$ `main`), không mở vào repo gốc VinUni.

---

## 🛠️ Chi Tiết Từng Bước Thực Hiện

### Giai đoạn 1: Core (60 Điểm — Hoàn thành trên lớp)

#### [x] M0 — Thiết lập môi trường & Tích hợp mã Day 8
- [x] Tạo nhánh làm bài: `git switch -c starter/d09`
- [x] Chép code từ Day 8: `Copy-Item -Recurse -Force ..\day8-goc\src\* src\` (hoặc thư mục Lab8 tương đương).
- [x] Cài đặt dependencies:
  ```powershell
  cd src
  python -m pip install -r requirements.txt -r requirements-lab9.txt
  ```
- [x] Chạy smoke test:
  ```powershell
  python -m lab9.smoke
  ```
  *(Yêu cầu: In ra `M0 PASS`)*
- [x] Khởi tạo eval set v1:
  ```powershell
  python -m lab9.evalset --build
  ```
  *(Sinh ra `data/eval/eval_set_v1.jsonl` và `data/eval/labels_v1.json`)*

---

#### [x] M1 — Failure Taxonomy & Eval Set v1 (12đ)
- [x] Phân tích các failure modes (FM-01 đến FM-09) từ mã nguồn `variant_agent.py` và trace log.
- [x] Điền tài liệu [docs/failure_taxonomy.md](docs/failure_taxonomy.md):
  - [x] $\ge 5$ Failure Modes (đủ định nghĩa 1 câu, layer, bằng chứng trace, grader, metric).
  - [x] Khớp 5 anchor bắt buộc của giảng viên.
- [x] Cập nhật hàm `build()` trong [src/lab9/evalset.py](src/lab9/evalset.py) để gán nhãn `failure_modes` cho 14 items trong eval set v1.
- [x] Kiểm tra tính toàn vẹn:
  ```powershell
  python -m lab9.evalset --build
  python -m lab9.evalset --check
  ```
  *(Yêu cầu: `eval set ...: 0 problem(s)`)*

---

#### [x] M2 — Judge-the-Judge Calibration (12đ)
- [x] Lập trình các hàm thống kê trong [src/lab9/stats.py](src/lab9/stats.py):
  - [x] `confusion(human, judge)` (FAIL là positive class).
  - [x] `precision_recall(human, judge)` (trả về 0.0 nếu mẫu số = 0).
  - [x] `cohen_kappa(human, judge)` (ném `ValueError` nếu $p_e == 1$).
  - [x] `rogan_gladen(observed_rate, sensitivity, specificity)` (clip về $[0, 1]$).
- [x] Kiểm tra qua unit test:
  ```powershell
  python -m pytest -q -m student -o addopts= -k test_lab9_stats
  ```
- [x] Chạy calibration trên dữ liệu replay:
  ```powershell
  python -m lab9.judge --csv data/eval/judge_tone_public.csv --audit 5
  python -m lab9.judge --csv data/eval/judge_helpful_public.csv --audit 5
  ```
- [x] Hoàn thành tài liệu [docs/judge_audit.md](docs/judge_audit.md):
  - [x] Điền bảng chỉ số ($n, \kappa, P, R$, đạt FLOORS hay không, quyết định dùng/loại).
  - [x] Audit $\ge 5$ case bất đồng giữa người và judge.
  - [x] Giải thích lý do loại `judge_helpful` (không đủ tin cậy để làm cổng CI release gate).

---

#### [x] M3 — Trajectory Graders & Assertion (12đ)
- [x] Lập trình graders trong [src/lab9/graders.py](src/lab9/graders.py):
  - [x] `ApprovalBypass`: bắt hoàn tiền khi chưa duyệt hoặc ghi lén ledger claim khác.
  - [x] `RefundAmountCorrect`: so khớp số tiền trong ledger với label.
  - [x] Custom Grader cho **FM-08** (Misreport): so khớp số tiền trong câu trả lời văn bản (`reply`) với số tiền thực tế trong ledger (`snapshot["refund_vnd"]`).
  - [x] Đăng ký grader FM-08 vào `GRADERS` dict.
- [x] Cập nhật [src/config/metric_spec.yaml](src/config/metric_spec.yaml): thêm metric bắt FM-08 (`capability`, `blocking: true`).
- [x] Chạy unit test graders:
  ```powershell
  python -m pytest -q -m student -o addopts= -k test_lab9_graders
  ```
- [x] Kiểm tra tỷ lệ phát hiện và cảnh báo nhầm:
  ```powershell
  python -m lab9.mutation --detect
  ```
  *(Đạt: detection 100.00%, false alarms 0.00%)*
- [x] Thực hiện điều tra trace và điền [docs/trace_case.md](docs/trace_case.md):
  ```powershell
  python -m lab9.trace_case --shape seeded_regression --claim C-002 --seed 11
  python -m lab9.trace_case --shape fixed --claim C-002 --seed 11
  ```
  *(Chỉ rõ bước sai đầu tiên với event id cụ thể)*

---

#### [ ] M4 — Paired Bootstrap & Release Gate (15đ) + Báo Cáo (9đ)

Đã xác minh local ngày 18/11/2026: 17 test Core pass; smoke M0 PASS; eval set 0 lỗi; swarm và fixed gate exit 0; seeded_regression gate exit 1 trên `refund_amount_correct`, `pass_rate`, `reply_amount_correct`; ci_check trên swarm chạy độc lập exit 0. Xem [bằng chứng M4](docs/m4_validation.md). Đã chuẩn bị mã, reports và [nội dung PR](docs/core_pr.md) để chốt Core. Kết nối github.com:443 thất bại cả khi thử ngoài sandbox; chưa push/mở PR/merge, chưa xác nhận GitHub Actions xanh.

- [x] Lập trình `paired_bootstrap` trong [src/lab9/stats.py](src/lab9/stats.py) sử dụng `scipy.stats.bootstrap(paired=True, method="percentile")`.
- [x] Chạy sinh baseline v1 từ `swarm`:
  ```powershell
  python -m lab9.eval --shape swarm --spec config/metric_spec.yaml --out reports/baseline_v1.json
  ```
- [x] Kiểm tra hoạt động của Release Gate:
  ```powershell
  # 1. Shape fixed -> phải EXIT 0 (MERGE)
  python -m lab9.eval --shape fixed --spec config/metric_spec.yaml --out reports/eval_fixed.json
  python -m lab9.gate --pr reports/eval_fixed.json --baseline reports/baseline_v1.json

  # 2. Shape seeded_regression -> phải EXIT 1 (BLOCK trên pass_rate)
  python -m lab9.eval --shape seeded_regression --spec config/metric_spec.yaml --out reports/eval_seeded_regression.json
  python -m lab9.gate --pr reports/eval_seeded_regression.json --baseline reports/baseline_v1.json
  ```
- [x] Kiểm tra tính toàn vẹn CI:
  ```powershell
  python -m lab9.ci_check --pr reports/baseline_v1.json --baseline reports/baseline_v1.json --spec config/metric_spec.yaml
  ```
- [x] Cập nhật [src/harness_map.yaml](src/harness_map.yaml): merge section `eval` từ `src/harness_map.eval.yaml` (bump version lên `1.2`).
- [x] Hoàn thành tài liệu [docs/eval_card.md](docs/eval_card.md) & [docs/PRD_v1.1.md](docs/PRD_v1.1.md) với số liệu thật từ report. Tái sinh bằng `cd src; python -m scripts.write_m4_docs`.
- [ ] Commit reports và mở Pull Request Core:
  ```powershell
  git add -f reports/*.json
  git add -A
  git commit -m "feat: complete M1-M4 core evaluation"
  git push origin starter/d09
  ```
  *(Mở PR `starter/d09` -> `main` trên GitHub fork; chờ workflow `eval-gate` xanh rồi merge vào `main`)*

---

### Giai đoạn 2: Advanced (25 Điểm)

#### [ ] M5 — Eval Set v2 & Slice Gate (10đ)
- [ ] Cấu hình ánh xạ cơ chế tấn công trong [src/config/fm_map.yaml](src/config/fm_map.yaml).
- [ ] Cài đặt hàm `slice_check` trong [src/lab9/gate.py](src/lab9/gate.py).
- [ ] Cập nhật [src/config/metric_spec_v2.yaml](src/config/metric_spec_v2.yaml): thêm slices `money_movement`, `adversarial` và metric FM-08.
- [ ] Xây dựng eval set v2:
  ```powershell
  python -m lab9.evalset --v2 --build
  python -m lab9.evalset --v2
  ```
  *(Đảm bảo mỗi FM bị tấn công có $\ge 3$ items)*
- [ ] Sinh baseline v2:
  ```powershell
  python -m lab9.eval --shape swarm --spec config/metric_spec_v2.yaml --out reports/baseline_v2.json
  ```
- [ ] Kiểm tra variant `slice_regression`: gate phải block chỉ qua slice `money_movement`.

---

#### [ ] M6 — Phân tích nhiễu A/A & Thống kê $\text{pass}@k$, $\text{pass}^k$ (15đ)
- [ ] Lập trình `pass_at_k` và `pass_hat_k` trong [src/lab9/stats.py](src/lab9/stats.py).
- [ ] Chạy test Advanced cho thống kê:
  ```powershell
  python -m pytest -q -m student -o addopts= -k advanced
  ```
- [ ] Chạy đo dải nhiễu A/A giữa 2 bộ seed:
  ```powershell
  python -m lab9.mutation --spec config/metric_spec_v2.yaml --aa 66,77,88,99,110
  ```
- [ ] Cập nhật metric `pass_hat_5` (blocking) vào `config/metric_spec_v2.yaml` với ngưỡng sàn $\ge 0.8$ (nằm ngoài dải nhiễu A/A).
- [ ] Kiểm tra gate chặn đứng `flaky_regression`.

---

### Giai đoạn 3: Expert (15 Điểm)

#### [ ] M7 — Gate Chống Gian Lận (Integrity Check & Traps) (15đ)
- [ ] Cài đặt hàm `integrity_check` trong [src/lab9/gate.py](src/lab9/gate.py) để ngăn chặn:
  - [ ] Giá trị metric là `NaN` hoặc `inf`.
  - [ ] Thiếu hoặc trùng lặp số hàng (dropped rows / duplicated rows).
  - [ ] Lọc chọn hạt giống đẹp (cherry-picked seeds khác với baseline).
  - [ ] Grader crash (`evaluator_failures` non-empty hoặc trả về `None`).
  - [ ] Cơ chế Ratchet: cấm hạ sàn, cấm tăng trần, cấm bỏ blocking, cấm bỏ slices khi so với `base_spec`.
  - [ ] Sửa đổi slice tags của item giữa PR và baseline.
- [ ] Chạy kiểm thử Traps (tất cả traps phải bị block, exit 0):
  ```powershell
  python -m lab9.eval --shape slice_regression --spec config/metric_spec_v2.yaml --out reports/eval_slice_regression.json
  python -m lab9.traps --pr reports/eval_slice_regression.json --baseline reports/baseline_v2.json --spec config/metric_spec_v2.yaml
  ```
- [ ] Chạy Mutation Scorecard tổng hợp:
  ```powershell
  python -m lab9.mutation --spec config/metric_spec_v2.yaml --baseline reports/baseline_v2.json
  ```
  *(Yêu cầu: `mutation score 3/3 · false alarms 0`, exit 0)*
- [ ] Cập nhật mục v2 trong [docs/eval_card.md](docs/eval_card.md).
- [ ] Commit reports baseline v2 bằng `git add -f reports/*.json` và push để kích hoạt job `eval-gate-v2`.

---

## 📝 Hồ Sơ Nộp Bài Checklist

- [ ] Tất cả mã nguồn M1–M7 đã hoàn thành và test pass.
- [ ] File `harness_map.yaml` có section `eval` (phiên bản 1.2).
- [ ] Đầy đủ 5 tài liệu docs:
  - [ ] `docs/failure_taxonomy.md`
  - [ ] `docs/judge_audit.md`
  - [ ] `docs/trace_case.md`
  - [ ] `docs/eval_card.md`
  - [ ] `docs/PRD_v1.1.md`
- [ ] Các file reports json đã được commit trên Git:
  - [ ] `src/reports/baseline_v1.json`
  - [ ] `src/reports/eval_fixed.json`
  - [ ] `src/reports/eval_seeded_regression.json`
  - [ ] `src/reports/baseline_v2.json` (nếu làm Advanced/Expert)
- [ ] PR đã merge vào `main` trên bản fork cá nhân.
- [ ] GitHub Actions: Job `eval-gate` (và `eval-gate-v2`) hiển thị xanh.
- [ ] Đã nộp link repo fork cá nhân lên LMS theo hạn của ca.
