# Báo cáo cá nhân — Lê Nhật Linh

## 1. Thông tin thành viên

- Họ tên: Lê Nhật Linh
- MSSV: 2A202603514
- Email: 26ai.linhln@vinuni.edu.vn
- GitHub: [NhatLinh056](https://github.com/NhatLinh056)

## 2. Phần việc phụ trách

- Xây dựng shape `single`: một agent chạy vòng ReAct có giới hạn, chỉ dùng read tool trong vòng lặp và để host thực hiện refund.
- Bổ sung kiểm thử ba nhánh approval cho cả `workflow`, `single` và `orchestrator`.
- Chạy benchmark bốn shape trên 14 claim public với năm seed và lưu artifact tái lập.
- Phụ trách ADR lựa chọn shape dựa trên số liệu benchmark của nhóm.

## 3. Đóng góp cụ thể

- Commit `6f59b95`: triển khai `src/lab8/shapes/single.py` và thêm `src/tests/test_single_shape.py`.
  - Dùng bộ nhớ riêng trong `decide()` vì `run_react` chỉ giữ kết quả tool cuối.
  - Không đưa ticket vào observation hoặc prompt; quote chỉ lấy từ order view và `compute_compensation`.
  - Giới hạn tối đa 8 bước, chỉ cho phép read tool; `issue_refund` chỉ được gọi bởi host sau vòng lặp.
  - Truyền full quote và `crash_at` vào durability để giữ đúng approval, idempotency và per-order cap.
- Commit `78cc808`: thêm `src/tests/test_shape_approval_paths.py`, kiểm 3 shape × 3 trường hợp approval mượn, revoked và thiếu approval.
- Commit `64d65ec`: chạy benchmark đúng lệnh của lab và commit nguyên `src/reports/benchmark.json`, không sửa JSON bằng tay.
- Commit `a1e71c9`: hoàn thiện `report/team/decision_adr.md`, chốt chọn shape `workflow` dựa trên số liệu benchmark 14 claim × 5 seed.
- Quyết định kỹ thuật chính: model chỉ chọn bước đọc; tiền, approval và side effect được giữ trong code/host.

## 4. Bằng chứng

- Commit single: [6f59b95](https://github.com/trinhcongduc112/K5-L3A-DAY08-DKL-FromWorkflowsToAgents/commit/6f59b95)
- Commit approval test: [78cc808](https://github.com/trinhcongduc112/K5-L3A-DAY08-DKL-FromWorkflowsToAgents/commit/78cc808)
- Commit benchmark: [64d65ec](https://github.com/trinhcongduc112/K5-L3A-DAY08-DKL-FromWorkflowsToAgents/commit/64d65ec)
- Commit ADR: [a1e71c9](https://github.com/trinhcongduc112/K5-L3A-DAY08-DKL-FromWorkflowsToAgents/commit/a1e71c9)
- Test single:
  - `test_react_uses_only_bounded_read_tools`
  - `test_ticket_claims_cannot_override_structured_order_data`
- Test approval: `test_invalid_approval_is_denied_and_audited` chạy 9 tổ hợp.
- Run id dẫn chứng: `R-single-C-001-s11` và `R-single-C-002-s55`.
- `src/reports/benchmark.json`: single đạt pass rate `1.0`, pass^5 `1.0`, seed min–max `1.0–1.0`, variance `0.0`, cost/success mô phỏng `28.905714285714286` VND.
- Artifact benchmark gồm 280 trial, không có `status=error` hoặc `leak_suspect`; miss duy nhất là weakness công khai của swarm tại `C-002`, seed `55`.

## 5. Công cụ AI đã dùng

- OpenAI Codex trong Orca: đọc yêu cầu, đối chiếu code sẵn có, hỗ trợ triển khai shape single, viết test, kiểm artifact benchmark và soạn báo cáo.
- AI chỉ hỗ trợ đề xuất và thao tác; tôi kiểm lại bằng diff, test thật, dữ liệu SQLite, nội dung JSON và code review độc lập trước mỗi lần push.
- Các lệnh tự kiểm chính:
  - `python -m pytest -q`
  - `python -m pytest -q -m student -o addopts=`
  - `python -m pytest -q -m student -o addopts= -k "single and not workflow and not orchestrator and not swarm"`
  - `python -m lab8.benchmark --shapes workflow,single,orchestrator,swarm --cases data/public_claims.jsonl --seeds 11,22,33,44,55 --out reports/benchmark.json`
- Benchmark được chạy lặp và cho cùng SHA-256 `503800B4DEC79C63156BE5CC7221576DA43275853D0F172BEA20A525833D7C8A` trên môi trường thực hiện.

## 6. Tự đánh giá

- Hoàn thành đúng phạm vi được giao cho shape single, test approval và benchmark; các thay đổi được chia thành commit riêng, dễ truy vết.
- Shape single đạt toàn bộ 70/70 trial public, ổn định trên năm seed và có chi phí mô phỏng thấp hơn hai topology multi-agent trong benchmark của nhóm.
- Phần làm tốt nhất là giữ ranh giới code/model rõ: agent chỉ đọc và lập bước, còn host chịu trách nhiệm policy cùng side effect.
- Hạn chế: kết quả dùng MockLLM, latency không được đo và chưa có `student_drop/`, nên chưa thể tự kết luận hiệu năng hoặc độ chính xác trên bộ hidden.
