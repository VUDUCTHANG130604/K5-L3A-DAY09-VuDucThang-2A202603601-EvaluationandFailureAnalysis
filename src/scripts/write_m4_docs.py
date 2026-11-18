"""Generate M4 documentation from script-produced reports; run from src/."""
from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

from lab9 import stats
from lab9.ci_check import check as ci_check
from lab9.eval import load_spec, per_item
from lab9.gate import check
from lab9.judge import FLOORS


def main() -> None:
    root = Path(__file__).resolve().parents[2]
    src = root / "src"
    spec = load_spec(src / "config/metric_spec.yaml")
    reports = {name: json.loads((src / "reports" / file).read_text(encoding="utf-8"))
               for name, file in {"baseline": "baseline_v1.json", "fixed": "eval_fixed.json",
                                  "regression": "eval_seeded_regression.json", "pr": "eval_pr.json"}.items()}
    base = reports["baseline"]
    assert not ci_check(reports["pr"], base, spec), "Baseline/spec check failed"
    assert not check(reports["pr"], base, spec)[0], "Swarm must merge"
    assert not check(reports["fixed"], base, spec)[0], "Fixed must merge"
    blocked, regression_lines = check(reports["regression"], base, spec)
    assert "pass_rate" in blocked, "Regression must be blocked on pass_rate"
    for report in reports.values():
        assert len(report["rows"]) == report["manifest"]["items"] * len(report["manifest"]["seeds"])
        assert not report["evaluator_failures"]

    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()
    paths = ["lab9/stats.py", "lab9/gate.py", "lab9/graders.py", "lab9/eval.py", "lab9/evalset.py",
             "config/metric_spec.yaml", "data/eval/eval_set_v1.jsonl", "data/eval/labels_v1.json"]
    hashes = "\n".join(f"| `{p}` | `{hashlib.sha256((src / p).read_bytes()).hexdigest()}` |" for p in paths)
    threshold_rows, result_rows, ci_rows = [], [], []
    for metric in spec["metrics"]:
        mid = metric["id"]
        threshold_rows.append(f"| `{mid}` | {metric['kind']} | `{json.dumps(metric.get('threshold', {}))}` | "
                              f"{'có' if metric.get('blocking') else 'không'} | {base['metrics'][mid]} |")
        result_rows.append(f"| `{mid}` | {base['metrics'][mid]} | {reports['fixed']['metrics'][mid]} | "
                           f"{reports['regression']['metrics'][mid]} |")
        if metric.get("threshold", {}).get("no_significant_drop"):
            for name in ("fixed", "regression"):
                a, b = per_item(reports[name], mid), per_item(base, mid)
                keys = sorted(a.keys() & b.keys())
                bs = spec["bootstrap"]
                d, lo, hi = stats.paired_bootstrap([a[k] for k in keys], [b[k] for k in keys],
                    n_resamples=bs["n_resamples"], rng=bs["rng"], confidence=bs["confidence"])
                ci_rows.append(f"| {name} | `{mid}` | {d:+.4f} | [{lo:+.4f}, {hi:+.4f}] |")
    threshold_table = "| Metric | Loại | Ngưỡng từ spec | Chặn release | Baseline |\n|---|---|---|---|---|\n" + "\n".join(threshold_rows)
    result_table = "| Metric | Swarm baseline | Fixed | Seeded regression |\n|---|---|---|---|\n" + "\n".join(result_rows)
    ci_table = "| Variant | Metric | Δ so với swarm | CI 95% |\n|---|---|---|---|\n" + "\n".join(ci_rows)
    runs = "\n".join(f"- {name}: `{report['run_id']}` — {len(report['rows'])} rows, "
                     f"{len(report['evaluator_failures'])} evaluator failures." for name, report in reports.items())

    import csv
    judge_lines = []
    for name in ("tone", "helpful"):
        with (src / f"data/eval/judge_{name}_public.csv").open(encoding="utf-8") as stream:
            rows = list(csv.DictReader(stream))
        human, judge = [r["human"] for r in rows], [r["judge"] for r in rows]
        p, r = stats.precision_recall(human, judge)
        k = stats.cohen_kappa(human, judge)
        judge_lines.append(f"| {name} | {len(rows)} | {k:.3f} | {p:.3f} | {r:.3f} |")
    judge_table = "| Judge | n | κ | Precision | Recall |\n|---|---|---|---|---|\n" + "\n".join(judge_lines)
    card = f"""# Eval card — LogiX-VN refund agent

Sinh bằng `cd src; python -m scripts.write_m4_docs` từ reports, spec và CSV calibration.

## Phiên bản và nguồn dữ liệu

{runs}

- Eval set v1 SHA: `{base['manifest']['eval_set_sha']}`; {base['manifest']['items']} item × {len(base['manifest']['seeds'])} seed; seeds `{base['manifest']['seeds']}`.
- Nguồn: `lab8_public`; nhãn tách riêng trong `data/eval/labels_v1.json`.
- Metric spec version: `{spec['metric_spec_version']}`; MockLLM; Python `{base['manifest']['python']}`.
- HEAD trước khi đóng gói hồ sơ: `{head}`. SHA-256 bên dưới nhận diện chính xác các file được đánh giá, kể cả khi hồ sơ được đưa vào commit mới.

| File tương đối với src/ | SHA-256 |
|---|---|
{hashes}

## Metric và kết quả

{threshold_table}

{result_table}

Bootstrap percentile, paired theo item sau khi lấy trung bình qua seed: {spec['bootstrap']['n_resamples']} resamples, RNG {spec['bootstrap']['rng']}, confidence {spec['bootstrap']['confidence']}. Đơn vị resample là 14 item; không coi 70 trial là 70 quan sát độc lập.

{ci_table}

Swarm độc lập và fixed: gate exit 0. Seeded regression: gate exit 1, blocked `{', '.join(blocked)}`. Riêng pass_rate giảm có ý nghĩa vì toàn bộ CI nằm dưới 0; refund_amount_correct và reply_amount_correct bị chặn do dưới sàn dù CI chạm 0. db_fact_kept, pass_5 và cost_per_success chỉ cảnh báo.

## Judge và trace

{judge_table}

Tone đạt FLOORS κ≥{FLOORS['kappa']}, P≥{FLOORS['precision']}, R≥{FLOORS['recall']}; helpful bị loại vì κ và recall dưới sàn. Đây là calibration replay; gate Core hiện dùng code graders, chưa chấm tone trực tiếp trên các trial. Xem [judge audit](judge_audit.md).

[Trace case](trace_case.md): C-002@11, seeded_regression, event 3 `model_override` ghi delay_days=5 thay DB=2; đối chứng fixed giữ DB. `test_override_event_breaks_db_fact` và RefundAmountCorrect bắt hành vi này.

## Quyết định và giới hạn

- Eval owner: Vũ Đức Thắng; khi gate exit 1, giữ PR, đọc trace/ledger và sửa nguyên nhân rồi chạy lại.
- Phạm vi pilot: mô phỏng offline các claim hoàn phí giao trễ/bồi thường hư hỏng đã xác minh; cùng principal, đúng approval và các trần host áp dụng. Chưa cho phép triển khai trên người dùng thật.
- 14 item, 5 seed, MockLLM và judge replay công khai chưa đại diện cho model thật hoặc tập held-out. Bug hiếm 1/3 seed không được phát hiện ổn định với 5 seed.
- Slice gate, pass@k/pass^k, integrity/ratchet/traps thuộc M5–M7 chưa hoàn thành. CI hiện chưa bảo vệ đầy đủ trước report bị sửa hoặc chọn seed.
- Khi đổi item/nhãn/slices hoặc thêm adversarial cases: tăng eval_set_version, giữ provenance và sinh lại baseline. Khi đổi metric/ngưỡng: tăng metric_spec_version; cùng eval-set chỉ siết ngưỡng.
- Đã xác minh các bước eval-gate tại máy cục bộ; chưa có kết quả GitHub Actions. Theo dõi trạng thái push/PR/merge trong PROGRESS.md.
"""
    prd = f"""# PRD v1.1 — LogiX-VN refund agent

v1.1 bổ sung tiêu chí đánh giá và release gate. Bảng số liệu được sinh từ report bằng `python -m scripts.write_m4_docs`, không chỉnh report bằng tay.

## 1. Thay đổi so với v1.0

| Mục | v1.0 | v1.1 |
|---|---|---|
| Thành công | Xử lý đúng yêu cầu hoàn tiền | Metric, sàn và CI paired trong spec |
| Bằng chứng | Demo | Report theo run ID và kiểm tra tự động |
| Rủi ro | Mô tả chung | Failure mode → grader → metric |

## 2. Phạm vi pilot

- Mô phỏng offline qua ticket tiếng Việt: giao trễ, hư hỏng đã xác minh, thiếu thông tin, sai quyền và approval không hợp lệ.
- Chỉ xử lý đơn thuộc principal; host kiểm tra approval đúng claim, hạn dùng, số tiền được duyệt, số đã thanh toán và số đã hoàn theo đơn. Phí giao trễ theo chính sách hiện hành; bồi thường hư hỏng tối đa 150.000 VND theo fixture. Chọn mức đủ điều kiện lớn nhất và khấu trừ khoản đã hoàn.
- Ngoài phạm vi: thanh toán thật, người dùng thật, xử lý hàng loạt nhiều đơn, tranh chấp pháp lý và triển khai production.
- Môi trường đo: MockLLM, v1 SHA `{base['manifest']['eval_set_sha']}`, 14 item × 5 seed.

## 3. Định nghĩa chạy đúng

Baseline: `{base['run_id']}` ([report](../src/reports/baseline_v1.json)).

{threshold_table}

Giảm có ý nghĩa: CI 95% paired bootstrap của Δ (PR − baseline) nằm hoàn toàn dưới 0. Mỗi item được lấy trung bình qua seed trước khi resample. Safety là số lần vi phạm, bắt buộc bằng 0.

{result_table}

Run fixed: `{reports['fixed']['run_id']}`; regression: `{reports['regression']['run_id']}`. Xem [eval card](eval_card.md) cho CI, phiên bản mã và giới hạn.

## 4. Failure mode → grader

| FM | Hành vi | Code grader | Metric | Lý do |
|---|---|---|---|---|
| FM-01 | Lộ secret trong artifact/trace | SecretLeak | secret_leak | Đối chiếu chuỗi bị cấm |
| FM-02 | Bỏ qua approval | ApprovalBypass | approval_bypass | Đối chiếu quyền với ledger |
| FM-03 | Ticket ghi đè DB | DbFactKept, RefundAmountCorrect | db_fact_kept, refund_amount_correct | Kiểm tra event và tiền thực tế |
| FM-04 | Cộng/làm tròn sai | RefundAmountCorrect | refund_amount_correct | Đối chiếu nhãn tiền |
| FM-05 | Khấu trừ hai lần | RefundAmountCorrect | refund_amount_correct | Ledger là bằng chứng cuối |
| FM-06 | Dùng chính sách cũ | RefundAmountCorrect, TrialPass | refund_amount_correct, pass_rate | Kiểm tra tiền và kết quả |
| FM-07 | Hoàn nhầm claim cùng đơn | ApprovalBypass | approval_bypass | Bắt unexpected ledger rows |
| FM-08 | Reply khác ledger | ReplyAmountCorrect | reply_amount_correct | So tiền trong reply với ledger |
| FM-09 | Truy cập khác principal | SecretLeak, TrialPass | secret_leak, pass_rate | Kiểm tra chuỗi riêng tư đã gán nhãn và trạng thái; cần adversarial v2 để phủ rộng |

Tiền và phê duyệt chấm bằng code. Tone đủ calibration để cân nhắc sử dụng; helpful bị loại. Gate Core chưa tích hợp judge vào trial. Chi tiết tại [judge audit](judge_audit.md) và [taxonomy](failure_taxonomy.md).

## 5. Cổng release và trách nhiệm

```powershell
cd src
python -m lab9.gate --pr reports/eval_pr.json --baseline reports/baseline_v1.json --spec config/metric_spec.yaml
python -m lab9.ci_check --pr reports/eval_pr.json --baseline reports/baseline_v1.json --spec config/metric_spec.yaml
```

- Baseline swarm cần được commit và bảo vệ trên main; PR phải cùng eval_set_sha. CI chạy lại swarm và so metric với baseline.
- Eval owner: Vũ Đức Thắng. Exit 1 giữ PR, đọc nguyên nhân, sửa và chạy lại; không nới sàn cùng eval set. Không tự cấp waiver; ngoại lệ cần giảng viên/phụ trách lab phê duyệt và ghi lý do vào PR.
- Fixed exit 0; seeded_regression exit 1, chặn `{', '.join(blocked)}`.
- Các bước tương ứng workflow Core đã chạy cục bộ; GitHub Actions chưa được chạy/xác nhận. Reports phải được commit; push nhánh starter/d09 và mở PR về main trong fork trước khi merge. Theo dõi trạng thái trong PROGRESS.md.

## 6. Rủi ro mở

- MockLLM chưa đại diện cho model thật hoặc người dùng thật.
- 14 item khiến CI rộng; 5 seed chưa đủ bắt ổn định lỗi hiếm.
- Judge CSV công khai chưa có kiểm chứng held-out mới.
- M5–M7 chưa có slice gate và chống report bị sửa/chọn seed; không suy diễn Core thành bảo đảm production.

## 7. Khi nào tăng phiên bản

Đổi eval set/nhãn/slices: tăng eval_set_version và sinh lại baseline. Đổi metric/ngưỡng: tăng metric_spec_version, ghi lý do và chỉ siết ngưỡng trên cùng eval set.

## Phê duyệt

| Vai trò | Người phụ trách | Trạng thái |
|---|---|---|
| Eval owner | Vũ Đức Thắng | Đã chuẩn bị bằng chứng local |
| Product / phụ trách lab | Chưa chỉ định | Chưa phê duyệt triển khai |
"""
    (root / "docs/eval_card.md").write_text(card, encoding="utf-8")
    (root / "docs/PRD_v1.1.md").write_text(prd, encoding="utf-8")
    evidence = "# M4 — Bằng chứng kiểm tra local\n\n" + runs + "\n\n"
    evidence += "Swarm gate: exit 0. Fixed gate: exit 0. ci_check trên swarm độc lập: exit 0.\n\n"
    evidence += "```text\n" + "\n".join(regression_lines) + "\nexit 1 — blocked: " + ", ".join(blocked) + "\n```\n"
    evidence += "\nĐây là kết quả local, chưa phải trạng thái GitHub Actions. Có thể dùng output trên trong mô tả PR.\n"
    (root / "docs/m4_validation.md").write_text(evidence, encoding="utf-8")
    print("wrote docs/eval_card.md, docs/PRD_v1.1.md, docs/m4_validation.md")


if __name__ == "__main__":
    main()
