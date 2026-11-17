# Research card

File này nằm cố định ở `report/team/research_card.md`; `python -m lab8.check_submission` đọc cột "Nhóm điền" bằng máy.

Phần này nối tiếp phần mini research ở buổi lý thuyết (slide 62–63). Chọn **một** câu R1–R4, điền 6 dòng, rồi biến nó thành **một ablation** chạy được trong lab: giữ nguyên model (MockLLM), tool, seed, corpus và giá, chỉ thay đổi một biến.

| Câu | Nguồn (thư viện tham khảo, slide 68–69) | Câu hỏi gợi ý cho lab |
| --- | --- | --- |
| R1 · Scaling | Google Research 2026, *Towards a Science of Scaling Agent Systems* | Task claims chủ yếu tuần tự hay song song được? Dự đoán thêm investigator sẽ làm pass rate và cost/success thay đổi thế nào. |
| R2 · Failure taxonomy | MAST, NeurIPS 2025, *Why Do Multi-Agent LLM Systems Fail?* | Các trial fail của swarm (seed 55) thuộc nhóm nào: lỗi giao việc, lệch mục tiêu, hay lỗi kiểm chứng? |
| R3 · Architecture choices | AgentArch, AACL 2026 | Nếu đổi topology mà giữ nguyên mọi thứ khác, biến nào phải cố định để kết luận còn đúng? |
| R4 · Evaluation confounders | EMNLP 2026, *Rethinking Evaluation of MAS Efficiency* | Làm sao chứng minh chênh lệch giữa A/B/C/D là do topology, không phải do prompt, tool hay seed? |

## Phiếu của nhóm

Điền vào cột cuối. Không xóa hai cột đầu.

| Field | Hướng dẫn | Nhóm điền |
| --- | --- | --- |
| CÂU | R1 / R2 / R3 / R4 | R1 · Scaling |
| SOURCE | Paper/blog, năm, URL, loại bằng chứng (benchmark, production report, blog kinh nghiệm) | Yubin Kim và 18 tác giả khác (Google Research, Google DeepMind, MIT), *Towards a Science of Scaling Agent Systems*, arXiv:2512.08296, v1 tháng 12/2025, bản v3 tháng 4/2026: https://arxiv.org/abs/2512.08296. Blog tóm tắt của Google Research, 28/01/2026: https://research.google/blog/towards-a-science-of-scaling-agent-systems-when-and-why-agent-systems-work/. Loại bằng chứng: benchmark. |
| CLAIM | Một kết luận gốc của nguồn. Không viết rộng hơn phạm vi paper | Kiến trúc tốt nhất phụ thuộc cấu trúc task. Trên PlanCraft (task lập kế hoạch tuần tự), mọi biến thể multi-agent được thử đều giảm hiệu năng 39–70% so với single-agent. Trên Finance-Agent (task phân rã song song được), multi-agent tập trung tăng khoảng +81%. |
| BOUNDARY | Model / dataset / setup giới hạn kết luận đó | LLM thật của ba họ GPT, Gemini, Claude; năm kiến trúc (single, independent, centralized, decentralized, hybrid). Blog nêu 180 cấu hình và 4 benchmark (Finance-Agent, BrowseComp-Plus, PlanCraft, Workbench); arXiv v3 nêu 260 cấu hình và 6 benchmark. Con số 39–70% chỉ thuộc PlanCraft. Kết luận không áp thẳng cho MockLLM hay task hoàn phí của LogiX. Nhóm chỉ đọc abstract và blog, chưa đọc toàn văn. |
| HYPOTHESIS | Nếu đổi shape A→B (hoặc bật/tắt một thành phần), metric X sẽ đổi theo hướng nào, khoảng bao nhiêu | Claims flow là tuần tự: phải có order mới tính được quote, có quote mới gọi host. Vì vậy đi từ workflow sang orchestrator rồi swarm thì pass rate không tăng, còn cost/success tăng khoảng 1,5 đến 2 lần do thêm lượt gọi model (plan, peer, parse) và tool đọc của investigator. |
| METHOD | Biến giữ cố định: model, tools, seed, corpus, giá, evaluator. Biến duy nhất được thay đổi: … | Cố định: MockLLM, tool và host (durability, policy), seed 11/22/33/44/55, 14 claim public C-001 đến C-014, `config/pricing.yaml`, `as_of` 2026-11-15, evaluator `lab8.metrics`, một SQLite mới cho mỗi trial. Biến duy nhất thay đổi: shape (topology). Chuỗi chính workflow → orchestrator → swarm; single làm đối chứng. |
| FAILURE / METRIC | Một lỗi dự kiến và cách đo nó: pass rate, pass^5, variance, cost/success, leak, bypass | Lỗi dự kiến: swarm tin số ngày ghi trong ticket ở seed chia hết cho 5 (REFERENCE_WEAKNESS), nên C-002 (T02) ở seed 55 trả 20.000 thay vì denied. Đo bằng pass rate, pass^5, seed variance và cost/success trong `by_shape` của `benchmark.json`; kèm secret leak và approval bypass phải bằng 0. |

## Kết quả ablation

- Lệnh đã chạy (copy nguyên văn): `python -m lab8.benchmark --shapes workflow,single,orchestrator,swarm --cases data/public_claims.jsonl --seeds 11,22,33,44,55 --out reports/benchmark.json` (chạy trong `src/`, commit `64d65ec`)
- Run id / file report: `src/reports/benchmark.json`. Run id đối chứng: `R-workflow-C-002-s55` (pass) và `R-swarm-C-002-s55` (fail, `status resolved != denied`).
- Kết quả so với hypothesis (đúng / sai / không kết luận được), kèm số liệu: **đúng hướng, chưa kết luận được nguyên nhân do topology.** Số lấy từ `by_shape` của `benchmark.json` (70 trial mỗi shape):

  | Shape | Pass rate | pass^5 | Seed min–max | Seed variance | Cost/success (VND mô phỏng) | So với workflow |
  | --- | ---: | ---: | --- | ---: | ---: | ---: |
  | workflow | 1,000 | 1,000 | 1,000–1,000 | 0 | 28,79 | 1,00× |
  | single | 1,000 | 1,000 | 1,000–1,000 | 0 | 28,91 | 1,00× |
  | orchestrator | 1,000 | 1,000 | 1,000–1,000 | 0 | 47,73 | 1,66× |
  | swarm | 0,986 | 0,929 | 0,929–1,000 | 0,000816 | 49,57 | 1,72× |

  - Pass rate không tăng khi thêm agent: orchestrator bằng workflow, swarm thấp hơn (69/70). Cost/success tăng khoảng 1,7 lần ở orchestrator và swarm. Cả hai khớp hypothesis.
  - Lỗi dự kiến xảy ra đúng một trial: swarm, C-002, seed 55. Đó là lý do swarm có variance khác 0.
  - Không kết luận được rằng "nhiều agent hơn thì kém hơn" nói chung. Swarm sai vì điểm yếu được cài sẵn trong code, không phải vì topology. Orchestrator có cùng topology nhiều agent mà vẫn đạt 1,000.
- Giới hạn: MockLLM không phải model sản xuất, latency là `unavailable`.
  - Card được điền sau khi benchmark đã chạy; con số "1,5 đến 2 lần" trong hypothesis ước từ số lượt gọi model và tool trong code từng shape, không phải dự đoán đăng ký trước khi có số.
  - Chỉ 14 claim × 5 seed = 70 trial mỗi shape, không có khoảng tin cậy.
  - Chênh cost gần như hoàn toàn do tool call (10 VND mỗi lần, chiếm khoảng 95–97% cost mỗi trial). Giá token là mô phỏng và prompt của MockLLM ngắn, nên các lượt gọi model gần như không tốn.
  - `mean_steps` đếm số event trong trace nên phụ thuộc cách mỗi shape ghi trace, không dùng để so sánh các shape với nhau.

Muốn đi xa hơn một ablation để lấy điểm cộng thì xem [docs/bonus_topics.md](../../docs/bonus_topics.md).
