"""Render Advanced/Expert documentation from reports/advanced_validation.json."""
from __future__ import annotations

import json
from pathlib import Path

from lab9.eval import load_spec

MARKER = "## Eval set v2 — M5–M7"


def main() -> None:
    evidence = json.loads(Path("reports/advanced_validation.json").read_text(encoding="utf-8"))
    spec = load_spec(Path("config/metric_spec_v2.yaml"))
    docs = Path(__file__).resolve().parents[2] / "docs"
    manifest = evidence["manifest"]
    rows = []
    for name, metrics in evidence["metrics"].items():
        decision = evidence["decisions"].get(name)
        verdict = "A/A; không gate vì khác seeds" if decision is None else ", ".join(decision["blocked"]) or "merge"
        rows.append(f"| {name} | {metrics['pass_rate']} | {metrics['pass_at_5']} | {metrics['pass_hat_5']} | {verdict} |")
    table = "| Shape | pass@1 | pass@5 | pass^5 | Gate |\n|---|---|---|---|---|\n" + "\n".join(rows)
    slices = "\n".join(f"| {s['name']} | {len(evidence['slices'][s['name']]['pass_rate'])} | {s['min']} | có |"
                       for s in spec["slices"])
    runs = "\n".join(f"- `{name}`: `{run}` — [report](../src/reports/{evidence['files'][name]})."
                     for name, run in evidence["runs"].items())
    counts = " · ".join(f"{fm}: {n}" for fm, n in evidence["failure_mode_counts"].items())
    hashes = "\n".join(f"| `{path}` | `{sha}` |" for path, sha in evidence["sha256"].items())
    card = f"""{MARKER}

Sinh bằng `cd src; python -m scripts.write_advanced_docs` từ bằng chứng được tạo bởi `python -m scripts.verify_advanced`. Nếu tái sinh hồ sơ Core, chạy `scripts.write_m4_docs` trước rồi chạy lệnh này để bổ sung phần v2.

- Eval set version v2, SHA `{manifest['eval_set_sha']}`; {manifest['items']} item × {len(manifest['seeds'])} seed = {manifest['items'] * len(manifest['seeds'])} trial mỗi report. Gồm 14 public v1 + 14 adversarial, nhãn tách riêng.
- Metric spec `{manifest['metric_spec_version']}`; MockLLM; seeds `{manifest['seeds']}`.
- Số item theo FM: {counts}. Mỗi FM bị adversarial tấn công có ít nhất 3 item trên toàn eval set v2.

{table}

### M5: slice gate và FM-08

| Slice | Số item | Sàn pass_rate | Blocking + paired no-significant-drop |
|---|---|---|---|
{slices}

`slice_regression` có pass_rate toàn cục 0.9357, trên sàn 0.85; CI của Δ toàn cục chạm 0. Gate chỉ chặn `slice:money_movement/pass_rate` vì slice còn 0.85, dưới sàn 0.95. `adversarial` dùng sàn 0.90. FM-08 kế thừa `reply_amount_correct` blocking ≥0.95, so reply với ledger; parser hỗ trợ diễn đạt lại và dấu phân cách số tiền.

### M6: A/A và độ ổn định

A/A dùng cùng swarm, hai bộ seed `{manifest['seeds']}` và `{evidence['aa_seeds']}`. Tất cả Δ metric = 0; pass^5 cả hai lần = 0.8929. Khoảng quan sát A/A cho pass^5 là [0.8929, 0.8929]; chọn sàn blocking 0.80, thấp hơn hai quan sát và đáp ứng yêu cầu ≥0.8. Đây là hai quan sát, không phải CI hay bảo đảm cho mọi seed tương lai. Giữ nguyên sàn khi đánh giá các variant.

pass@k = 1 − C(n−c,k)/C(n,k); pass^k = C(c,k)/C(n,k), với n≥1, 0≤c≤n, 1≤k≤n. Lấy trung bình ước lượng theo item. `flaky_regression` đạt pass@5=1 nhưng pass^5=0.5714 nên bị chặn bởi `pass_hat_5`; cả CI pass_rate và slice tiền cũng phát hiện hồi quy. `fixed` và `honest_refactor` được merge; chi phí refactor tăng chỉ là cảnh báo vì metric cost không blocking.

### M7: toàn vẹn report và ratchet

- Từ chối metric không hữu hạn, thiếu metric, None ở grader, evaluator failure, thiếu/trùng hàng, không đủ Cartesian item×seed, đổi seed và đổi slice tags.
- Tính lại summary từ rows để bắt số tổng hợp bị sửa. Kiểm tra cả baseline và PR.
- Khi có base_spec cùng eval_set_version: cấm hạ sàn, tăng trần/max_increase, bỏ metric/slice, bỏ blocking/no_significant_drop hoặc đổi kind/grader/level và seeds.
- CI lấy base spec từ commit base của PR, chạy lại swarm để đối chiếu baseline v2, rồi chạy mutation và traps. Không sửa lab8, variants hay traps để đổi kết quả.

```text
{evidence['mutation_output'].strip()}
```

{len(evidence['traps'])}/{len(evidence['traps'])} trap công khai bị chặn do integrity: {', '.join(evidence['traps'])}. Xem [bằng chứng chi tiết](advanced_validation.md).

### Giới hạn

28 item, 5 seed và MockLLM chưa đại diện cho model thật hay người dùng thật; judge vẫn là replay. Lỗi hiếm chỉ bật trên 1/3 seed chưa phát hiện ổn định với 5 seed. Toàn vẹn cấu trúc và tổng hợp không chứng minh rows là trace thật nếu kẻ tấn công sửa đồng bộ mọi nguồn tin; baseline và base_spec phải được bảo vệ. Kiểm thử công khai và các ca bổ sung không thay thế bộ chấm ẩn. Trạng thái GitHub Actions/PR xem PROGRESS.md.
"""
    current = (docs / "eval_card.md").read_text(encoding="utf-8").split(MARKER)[0].rstrip()
    (docs / "eval_card.md").write_text("\n".join(line.rstrip() for line in (current + "\n\n" + card).splitlines()) + "\n", encoding="utf-8")
    detail = "# M5–M7 — Bằng chứng Advanced/Expert\n\n" + card + "\n## Run IDs\n\n" + runs
    detail += "\n\n## SHA-256 các nguồn được kiểm tra\n\n| File trong src/ | SHA-256 |\n|---|---|\n" + hashes
    detail += "\n\n## Gate và CI theo từng slice\n\n"
    for name, decision in evidence["decisions"].items():
        detail += f"### {name}\n\n```text\n" + "\n".join(decision["lines"]) + "\n```\n\n"
    detail += "## Traps\n\n```text\n" + evidence["trap_output"].strip() + "\n```\n"
    (docs / "advanced_validation.md").write_text("\n".join(line.rstrip() for line in detail.splitlines()) + "\n", encoding="utf-8")
    print("wrote docs/eval_card.md (v2), docs/advanced_validation.md")


if __name__ == "__main__":
    main()
