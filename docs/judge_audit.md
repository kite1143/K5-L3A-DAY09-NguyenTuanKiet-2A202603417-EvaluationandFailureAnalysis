# Judge audit

Chạy: `python -m lab9.judge --csv <file> --audit 5`

| Tiêu chí | n | κ | Precision | Recall | Đạt FLOORS (κ≥0.6, P≥0.8, R≥0.7)? | Quyết định |
|---|---|---|---|---|---|---|
| tone_ok | 100 | 0.757 | 0.857 | 0.800 | Có (tp=24, fp=4, fn=6, tn=66) | dùng — chỉ để soát giọng điệu |
| helpful | 100 | 0.375 | 1.000 | 0.300 | Không (κ và recall dưới sàn; tp=9, fp=0, fn=21, tn=70) | loại — bỏ sót 21/30 ca FAIL |

Tỉ lệ lỗi: tone quan sát 0.28 → hiệu chỉnh Rogan-Gladen 0.30; helpful quan sát 0.09 → hiệu chỉnh 0.30 (judge bỏ sót gần 2/3 lỗi, nên con số thô thấp hơn thực tế ~3.3 lần).

## ≥5 case audit thủ công
| # | Case | Judge nói | Người nói | Ai đúng? | Ghi chú |
|---|---|---|---|---|---|
| 1 | H-008 | PASS | FAIL | Người | "Em … nha" quá suồng sã với khách; rubric yêu cầu "Dạ, anh/chị". Judge đọc "nha" là thân thiện. |
| 2 | H-017 | PASS | FAIL | Người | Xưng "bạn ơi" với khách lớn tuổi; cùng lỗi từ vựng như H-008. |
| 3 | H-029 | PASS | FAIL | Người | "không cần nhắn thêm" là giọng ra lệnh; judge chỉ bắt được mở đầu "Dạ, vui lòng". |
| 4 | H-042 | FAIL | PASS | Người | Ngắn nhưng đủ ý (số tiền, đơn, thời gian); rubric không bắt buộc xin lỗi. Judge phạt vì thiếu câu xin lỗi. |
| 5 | H-051 | FAIL | PASS | Người | Từ "refund" được CS LogiX cho phép; judge phạt vì thấy tiếng Anh. |
| 6 | H-081 | FAIL | PASS | **Judge** | Nhãn người sai (đọc nhầm ticket): câu trả lời "chưa đủ điều kiện hoàn" đúng chính sách. Cần sửa nhãn, không sửa judge. |
| 7 | HL-015 | PASS | FAIL | Người | Reply nói 55.000đ, ledger ghi 40.000đ. Judge không có ledger nên không thể thấy — lỗi thiết kế, không phải lỗi nhãn. |
| 8 | HL-047 | PASS | FAIL | Người | "Ok bạn, đơn O-515 xử lý rồi nhé." sai xưng hô và không xin lỗi; judge helpful bỏ qua vì câu ngắn, lịch sự bề mặt. |

## Kết luận
- **Loại `helpful`**: recall 0.30 < 0.70 và κ 0.375 < 0.60. 21/30 ca FAIL bị bỏ sót, gần như toàn bộ là **sai số tiền so với ledger** — đúng FM-08, thứ chỉ code grader (`ReplyMatchesLedger`, M3) bắt được. Giữ judge này sẽ khiến `pass_rate` của FM-08 bị thổi lên.
- **Giữ `tone_ok`**: qua cả ba sàn (κ 0.757, P 0.857, R 0.800), dùng như bộ soát ngôn ngữ. Hai lỗi hệ thống của nó đã ghi ở #1–#5: nhận "nha/bạn ơi" là thân thiện, và phạt câu ngắn đúng ý.
- **Sửa nhãn**: H-081 là nhãn người sai, cần sửa trước khi dùng CSV làm tham chiếu; các case còn lại người đúng.
- Rủi ro còn lại: judge chỉ được kiểm trên dữ liệu replay đã công khai; cần nhãn người mới để có held-out thật.
