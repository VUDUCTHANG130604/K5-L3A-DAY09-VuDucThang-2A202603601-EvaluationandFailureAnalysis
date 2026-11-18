# Judge audit

Chạy: `python -m lab9.judge --csv <file> --audit 5`

| Tiêu chí | n | κ | Precision | Recall | Đạt FLOORS (κ≥0.6, P≥0.8, R≥0.7)? | Quyết định |
|---|---|---|---|---|---|---|
| tone_ok | 100 | 0.757 | 0.857 | 0.800 | Đạt cả 3 chỉ số (κ=0.757 ≥ 0.6, P=0.857 ≥ 0.8, R=0.800 ≥ 0.7) | **dùng** |
| helpful | 100 | 0.375 | 1.000 | 0.300 | Không đạt (κ=0.375 < 0.6, R=0.300 < 0.7) | **loại** |

## ≥5 case audit thủ công

| # | Case | Judge nói | Người nói | Ai đúng? | Ghi chú & Hành động sửa Rubric |
|---|---|---|---|---|---|
| 1 | H-008 (`judge_tone`): "Em đã hoàn tiền cho anh rồi nha, anh check giúp em." | PASS | FAIL | Người đúng | **Lý do:** Lời văn xưng hô "Em - anh", đuôi từ "nha", "check" quá suồng sã, không đạt chuẩn mực giao tiếp CSKH chuyên nghiệp của LogiX. Judge bị đánh lừa vì câu có thái độ hợp tác.<br>**Sửa Rubric:** Bổ sung quy định cấm đại từ xưng hô thân mật tự phát, bắt buộc quy chuẩn xưng hô "LogiX - Quý khách/Anh/Chị" và cấm từ đệm suồng sã ("nha", "nhé bạn"). |
| 2 | H-029 (`judge_tone`): "Dạ, vui lòng chờ. Hệ thống đang xử lý, không cần nhắn thêm." | PASS | FAIL | Người đúng | **Lý do:** Giọng điệu gắt gỏng, thiếu kiên nhẫn, mang tính xua đuổi khách hàng ("không cần nhắn thêm"). Judge bỏ qua yếu tố cảm xúc tiêu cực này.<br>**Sửa Rubric:** Thêm tiêu chí phạt nặng (FAIL) đối với các câu có sắc thái cộc cằn, ra lệnh hoặc từ chối hỗ trợ tiếp nhận thông tin từ khách hàng. |
| 3 | H-042 (`judge_tone`): "Dạ, đơn O-808 đã hoàn 120.000đ. Tiền về trong 3–5 ngày ạ." | FAIL | PASS | Người đúng | **Lý do:** Câu trả lời chuẩn mực, rõ ràng, cung cấp thông tin SLA hoàn tiền hữu ích. Judge chấm FAIL (False Positive) do hiểu nhầm việc cam kết 3-5 ngày là vượt quyền.<br>**Sửa Rubric:** Làm rõ trong Rubric: việc cung cấp khung thời gian chuẩn 3–5 ngày làm việc của ngân hàng là thông tin tiêu chuẩn được phép, không coi là vi phạm tone. |
| 4 | H-051 (`judge_tone`): "Dạ, LogiX đã refund 90.000đ cho đơn O-202 ạ." | FAIL | PASS | Cả hai có lý | **Lý do:** Dùng từ chêm tiếng Anh ("refund"). Người chấm PASS vì thông tin rõ ràng, tôn trọng; Judge bắt bẻ lỗi pha trộn ngôn ngữ.<br>**Sửa Rubric:** Khuyến khích dùng từ tiếng Việt thuần túy ("hoàn tiền"), nhưng quy định rõ chỉ cảnh báo nhẹ chứ không đánh FAIL nếu câu văn vẫn lịch sự và khách hàng hiểu đúng nghĩa. |
| 5 | HL-016 (`judge_helpful`): "Dạ, LogiX thành thật xin lỗi anh/chị vì sự bất tiện này và rất trân trọng sự kiên nhẫn của..." | PASS | FAIL | Người đúng | **Lý do:** Câu trả lời hoàn toàn là lời xin lỗi sáo rỗng, không cung cấp giải pháp, không có số tiền, không nêu trạng thái claim. Judge chấm PASS vì lời văn nghe trôi chảy, lịch sự.<br>**Sửa Rubric:** Phân định rạch ròi giữa "lịch sự" (Tone) và "giải quyết được việc" (Helpful). Bắt buộc câu trả lời helpful phải chứa ít nhất một hành động cụ thể hoặc thông tin trạng thái/tiền hoàn. |
| 6 | HL-047 (`judge_helpful`): "Ok bạn, đơn O-515 xử lý rồi nhé." | PASS | FAIL | Người đúng | **Lý do:** Trả lời quá cụt ngủn ("xử lý rồi" nhưng không rõ xử lý thế nào: hoàn bao nhiêu, từ chối hay chuyển tiếp). Khách hàng không có thông tin đối soát.<br>**Sửa Rubric:** Yêu cầu câu trả lời hoàn tất phải nêu rõ kết quả cụ thể (số tiền hoàn hoặc lý do từ chối), không chấp nhận các thông báo chung chung. |

## Kết luận

### 1. Tiêu chí bị loại và lý do
- **Tiêu chí bị loại:** `judge_helpful`.
- **Dẫn chứng ma trận nhầm lẫn:**
  $$\text{Confusion Matrix: } \text{TP}=9, \text{FP}=0, \text{FN}=21, \text{TN}=70$$
  * Tổng số ca lỗi người gán nhãn là $30$ ca ($\text{TP} + \text{FN} = 9 + 21 = 30$).
  * Judge bỏ sót tới **21/30** ca lỗi ($\text{Recall} = 30.0\%$), dẫn tới chỉ số tương đồng Cohen's Kappa chỉ đạt $\kappa = 0.375$ (thấp hơn rất nhiều so với ngưỡng sàn tối thiểu $0.6$).
  * Tỉ lệ lỗi quan sát thấy bởi judge chỉ là $9\%$, trong khi tỉ lệ lỗi thực tế sau hiệu chỉnh Rogan-Gladen là $30\%$.
  * **Lý do:** Judge LLM bị hiện tượng thiên vị văn phong mượt mà (*fluency / politeness bias*): một phản hồi xin lỗi hoa mỹ nhưng hoàn toàn vô dụng vẫn được judge cho điểm đỗ (PASS). Do đó, `judge_helpful` hoàn toàn mất tác dụng bảo vệ, **không đủ tin cậy để làm cổng CI Release Gate** (sẽ để lọt 70% các câu trả lời vô nghĩa ra production).
- **Tiêu chí được chấp nhận:** `judge_tone` đạt $\kappa = 0.757 \ge 0.6$, $P = 0.857 \ge 0.8$, $R = 0.800 \ge 0.7$, tỷ lệ nhầm lẫn thấp, đủ điều kiện đưa vào hệ thống đánh giá.

### 2. Rủi ro còn lại
- Dữ liệu hiệu chuẩn hiện tại dựa trên tập replay đã công khai (`judge_tone_public.csv`); có nguy cơ bị overfitting vào tập mẫu nhỏ ($n=100$).
- Cần xây dựng tập dữ liệu kiểm thử độc lập (*held-out set*) được gán nhãn bởi con người mới để kiểm chứng liên tục trước khi triển khai rộng rãi.
