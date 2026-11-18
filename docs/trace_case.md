# Trace case: từ trace tới quyết định sai đầu tiên

Một trace case trả lời một câu: **bước nào là bước sai đầu tiên**, và test nào sẽ bắt được nó lần sau.

```bash
cd src
python -m lab9.trace_case --shape seeded_regression --claim C-002 --seed 11
python -m lab9.trace_case --shape fixed --claim C-002 --seed 11   # đối chứng
```

Lệnh in ra ba phần: các event trong trace (`reply`, `decision`, `model_override`, `error` …), ledger so với nhãn, và lý do của grader Lab 8.

## Mẫu điền (mỗi bạn 1 case, lấy từ trial đang fail trong report)

| Trường | Nội dung |
|---|---|
| Trial | `seeded_regression C-002@11`, run ID: `seeded_regression-C-002-11` |
| Triệu chứng | Grader Lab 8 fail: `status resolved != denied`. Grader `DbFactKept` fail (`1 override event(s)`), `RefundAmountCorrect` fail (ledger `refund_vnd=20000` != nhãn `0`). Reply thông báo: *"Dạ, LogiX đã hoàn 20.000đ cho đơn O-202."* trong khi đơn chỉ trễ 2 ngày (không đủ điều kiện bồi thường). |
| Bước sai đầu tiên | **Event 3**: `model_override` `{"delay_days": 5}` |
| Vì sao là bước *đầu tiên* | Event 1 (`handoff`) khởi tạo ủy quyền điều tra chính xác cho `C-002`. Event 2 (`investigator`) tra cứu DB chính xác, đọc đúng `delay_days: 2` từ bản ghi đơn hàng `O-202`. Đến hết Event 2 mọi dữ liệu đều đúng. Tại Event 3, agent tự ý lấy số ngày khách hàng tự khai trong ticket ("trễ 5 ngày") để ghi đè lên dữ liệu DB. |
| Failure mode | **FM-03**: `ticket_trust — tin ticket hơn DB` |
| Đối chứng | Trên shape `fixed` (`C-002@11`): Sau Event 2 tra cứu DB ra `delay_days: 2`, không có Event `model_override`. Event 3 (`quote`) tính toán đúng `amount_vnd: 0, reason: "no_entitlement"`. Event 4 (`reply`) thông báo từ chối lịch sự: *"Dạ, đơn O-202 chưa đủ điều kiện hoàn theo chính sách hiện hành."* Ledger ghi nhận `refund_vnd: 0`, khớp hoàn toàn với nhãn. |
| Regression test | Grader `DbFactKept` (`tests/test_lab9_graders.py::test_override_event_breaks_db_fact`) bắt sự kiện `model_override`; grader `RefundAmountCorrect` bắt sai lệch tiền trên ledger. Đã kiểm chứng: fail trên `seeded_regression` và pass trên `fixed`. |
| Chưa chắc chắn | Trace chỉ ghi nhận hành vi đè dữ liệu (`model_override`) sau khi gọi tool, không chứng minh được liệu mô hình bị lừa do prompt thiếu chỉ dẫn bảo vệ DB hay do thiên kiến đồng thuận với khiếu nại của khách hàng (*sycophancy*). |

## Quy tắc

- Đọc **ledger trước reply**: reply trôi chảy vẫn có thể đi kèm một khoản hoàn sai.
- "Bước sai đầu tiên" phải dẫn số event cụ thể, không phải "agent bị nhầm".
- Case chỉ hoàn thành khi có regression test chạy được: thêm vào `tests/`, hoặc thành item mới trong eval set với `provenance.from_trace`.
