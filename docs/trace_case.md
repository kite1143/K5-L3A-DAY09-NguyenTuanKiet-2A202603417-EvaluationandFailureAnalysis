# Trace case: từ trace tới quyết định sai đầu tiên

Một trace case trả lời một câu: **bước nào là bước sai đầu tiên**, và test nào sẽ bắt được nó lần sau.

```bash
cd src
python -m lab9.trace_case --shape seeded_regression --claim C-002 --seed 11
python -m lab9.trace_case --shape fixed --claim C-002 --seed 11   # đối chứng
```

Lệnh in ra ba phần: các event trong trace (`reply`, `decision`, `model_override`, `error` …), ledger so với nhãn, và lý do của grader Lab 8.

## Mẫu điền (mỗi nhóm 1 case, lấy từ trial đang fail trong report)

| Trường | Nội dung |
|---|---|
| Trial | `seeded_regression C-002@11`, run ID `R-seeded_regression-C-002-s11` trong `reports/eval_seeded_regression.json` (run `E-seeded_regression-20261117-d454`) |
| Triệu chứng | Grader Lab 8 fail `status resolved != denied`; reply nói "Dạ, LogiX đã hoàn 20.000đ cho đơn O-202", ledger ghi `refund_vnd=20000, refund_count=1`, nhãn là `0/0` + `denied`. |
| Bước sai đầu tiên | Event **3** `model_override {"delay_days": 5}` — ticket nói 5 ngày, DB ghi 2 ngày. |
| Vì sao là bước *đầu tiên* | Event 1 `handoff` có `facts={}` và allowlist đọc đúng; event 2 `investigator` trả `lookup_order` với `delay_days: 2` khớp DB — cả hai chưa sai. Event 3 mới thay fact DB bằng số trong ticket; event 4 `quote` ra 20.000đ `entitled` là hệ quả (2 ngày < ngưỡng 3 nên đáng lẽ phải `no_entitlement`). |
| Failure mode | **FM-03 ticket_trust** (`docs/failure_taxonomy.md`) |
| Đối chứng | `fixed C-002@11`: không có event `model_override`; event 3 `quote {"amount_vnd": 0, "reason": "no_entitlement"}`; ledger `0/0`; status `denied`; grader Lab 8 PASS. |
| Regression test | `src/tests/test_lab9_trace_case.py::test_ticket_trust_override_is_the_first_wrong_step` — assert `DbFactKept` = False, `events[2]` là `model_override {delay_days: 5}`, ledger 20.000đ, `lab8_pass` False. Đối chứng `::test_fixed_control_keeps_the_db_fact` — `DbFactKept` = True, không có override, ledger 0, `lab8_pass` True. Đã chạy: 2 passed. |
| Chưa chắc chắn | Trace không ghi event approval/host, nên không phân biệt được số 20.000đ đến từ quote sai hay từ trần approval (`A-002 = 20.000đ`); cả hai đều không hợp lệ vì claim lẽ ra `denied`. Trace cũng không chứng minh được agent "biết" DB đúng — chỉ chứng minh nó đã ghi đè fact. |

## Quy tắc

- Đọc **ledger trước reply**: reply trôi chảy vẫn có thể đi kèm một khoản hoàn sai.
- "Bước sai đầu tiên" phải dẫn số event cụ thể, không phải "agent bị nhầm".
- Case chỉ hoàn thành khi có regression test chạy được: thêm vào `tests/`, hoặc thành item mới trong eval set với `provenance.from_trace`.
