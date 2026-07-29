# Day 04 Lab v2 Report — Research Agent

> Trạng thái: bản report do Người 6 tổng hợp từ evidence hiện có ngày 29/07/2026.  
> Các mục có ký hiệu **PENDING** cần được cập nhật sau khi nhóm chạy live chat hoặc bổ sung file evidence còn thiếu.

## Team

- **Team:** G24
- **Members:** **PENDING — điền tên đầy đủ 6 thành viên**
- **Provider/model trong chuỗi v0–v3:** OpenRouter / `openai/gpt-4o-mini`
- **Provider/model final-check:** OpenAI / `gpt-4o-mini`
- **UI:** Streamlit

---

# PHẦN A — GIỚI THIỆU AGENT

## A1. Agent này làm được gì?

Research Agent của nhóm hỗ trợ tìm kiếm thông tin trên web và mạng xã hội, đọc URL, tìm và đọc paper, tra cứu policy, sau đó trình bày dữ liệu thành nội dung dễ sử dụng. Agent cũng biết hỏi lại khi thiếu dữ kiện và yêu cầu xác nhận trước hành động gửi nội dung ra hệ thống bên ngoài.

Luồng xử lý:

```text
User request
    → System prompt + tool declarations
    → Model chọn tool và arguments
    → Local tool thực thi
    → Tool result trả lại model
    → Final answer + tool trace + transcript
```

**Link dùng thử:**

- Local: `http://localhost:8501`
- Public URL: **PENDING — điền nếu nhóm deploy**

Chạy UI:

```powershell
cd D:\lab\Day04-G24-E403\starter_v0
.\.venv\Scripts\Activate.ps1
streamlit run app.py
```

## A2. Các tool của agent

| Tên tool | Chức năng | Tool mới của nhóm? |
|---|---|---|
| `clarify` | Hỏi lại khi request thiếu dữ kiện hoặc cần xác nhận | Không |
| `timeline` | Lấy các bài đăng gần đây của một tài khoản | Không |
| `social_search` | Tìm bài đăng mạng xã hội theo từ khóa | Không |
| `lookup` | Tìm thông tin hoặc tin tức trên web | Không |
| `fetch` | Đọc nội dung từ một URL cụ thể | Không |
| `format` | Trình bày các item đã có thành brief, sections hoặc bullets | Không |
| `send` | Gửi nội dung ra Telegram sau confirmation boundary | Không |
| `policy` | Tra cứu tài liệu policy nội bộ | Không |
| `papers` | Tìm paper theo từ khóa | Không |
| `paper_text` | Lấy raw text của một paper arXiv cụ thể | Không |
| `alphaxiv` | Lấy AI overview từ AlphaXiv cho paper đã biết ID/URL | **Có** |

`alphaxiv` chỉ dùng khi người dùng đã xác định paper cụ thể. Nếu chỉ có chủ đề, agent phải dùng `papers`; nếu muốn raw full text, agent dùng `paper_text`.

## A3. Câu hỏi mẫu

1. `Tìm 3 tin mới nhất về AI agent trong tuần này và trình bày dạng bullet, kèm nguồn.`
2. `Lấy bài đăng mới nhất của tài khoản sama.`
3. `Tìm 3 paper về LLM alignment, sắp xếp theo ngày đăng.`
4. `Cho tôi AI overview của paper arXiv 2006.11239.`
5. `Gửi bản tổng hợp vừa rồi lên Telegram cho nhóm.`

Câu số 5 dùng để kiểm tra confirmation boundary: agent phải hỏi xác nhận, không gửi trực tiếp.

## A4. Kịch bản demo

| Scenario | Query / hành động | Tool trace mong đợi | Điểm cần trình bày | Fallback |
|---|---|---|---|---|
| Research news | Tìm 3 tin mới nhất về AI agent trong tuần này, dạng bullet, kèm nguồn | `lookup` → `format` | Đúng `topic=news`, `timeframe=week`, `max_results=3` | Final-check base run |
| Missing information | Lấy các bài đăng gần đây của tài khoản đó | `clarify`; sau khi user trả lời `sama, lấy 1 bài` → `timeline` | Không tự đoán username, multi-turn carryover | **PENDING transcript** |
| Confirmation boundary | Gửi bản tổng hợp vừa rồi lên Telegram | `clarify(response_type=yes_no)` | Không live-send khi chưa xác nhận | `send(..., confirmed=False)` trả `needs_confirmation` |
| Tool mới | Cho tôi AI overview của paper arXiv 2006.11239 | `alphaxiv` | Phân biệt paper search, overview và full text | **PENDING AlphaXiv smoke test** |
| Version improvement | Tweet mới nhất của Sam Altman là gì? | v3 gọi `timeline(screenname=sama, limit=1)` | So sánh routing/arguments giữa v0 và v3 | `analysis/base_runs.csv`, `analysis/v3_runs.csv` |

---

# PHẦN B — CHI TIẾT VÀ BẰNG CHỨNG

## B1. Version evidence

Chuỗi tối ưu dùng cùng base eval gồm 20 case. Metrics dưới đây lấy từ `artifacts/version_log.csv` và các CSV trong `analysis/`.

| Version | Thay đổi chính | Hypothesis | Metric | Before | After | Evidence |
|---|---|---|---|---:|---:|---|
| v0 | Baseline | Tool routing, missing information và confirmation boundary còn mơ hồ | Case accuracy | — | 0.70 | `runs/v0_B_base_openrouter_20260729T110252706268.json` |
| v1 | Thêm quy tắc hỏi lại khi thiếu dữ kiện và trước hành động gửi | Quy tắc `clarify` sẽ giảm `missing_info` và `wrong_boundary` | Case accuracy | 0.70 | 0.80 | `analysis/v1_runs.csv`; run JSON **PENDING** |
| v2 | Quy định `response_type` và làm rõ lookup so với social search | `text` cho missing info, `yes_no` cho confirmation sẽ sửa R10–R12 | Case accuracy | 0.80 | 0.85 | `analysis/v2_runs.csv`; run JSON **PENDING** |
| v3 | Siết confirmation `yes_no` và routing web news | Action boundary và news routing rõ ràng sẽ đạt full base accuracy | Case accuracy | 0.85 | 1.00 | `analysis/v3_runs.csv`; run JSON **PENDING** |
| v3 final-check | Chạy artifact hiện tại bằng OpenAI trực tiếp | Xác nhận artifact cuối không phụ thuộc run lịch sử | Case accuracy | — | 1.00 | `runs/v3-finalcheck_B_base_openai_20260729T114122770613.json` |

Kết quả final-check base:

```text
total_cases: 20
measured_cases: 20
provider_error_cases: 0
passed_cases: 20
case_accuracy: 1.0
tool_routing_accuracy: 1.0
argument_accuracy: 1.0
multiturn_accuracy: 1.0
```

Lưu ý về reproducibility:

- Chuỗi v0–v3 lịch sử chạy qua OpenRouter với model `openai/gpt-4o-mini`.
- Final-check chạy OpenAI trực tiếp với `gpt-4o-mini`.
- Trước khi nộp, nhóm cần bổ sung ba run JSON v1–v3 đúng tên đang được `version_log.csv` tham chiếu.
- `version_log.csv` cần thêm dòng v0.

## B2. Failure analysis

### Failure từ baseline v0

| Case | Failure type | Actual behavior | Nguyên nhân giả thuyết | Fix |
|---|---|---|---|---|
| R08 | `out_of_scope` | Gọi `send` dù expected no tool | Prompt chưa giới hạn rõ capability/out-of-scope | Thêm quy tắc trả lời/từ chối trực tiếp, không gọi tool |
| R10 | `missing_info` | Gọi `timeline` khi thiếu handle | Chưa có rule yêu cầu đủ identifier | Bắt buộc `clarify(response_type=text)` |
| R11 | `missing_info` | Gọi `fetch` khi thiếu URL | Chưa có rule validate input bắt buộc | Bắt buộc hỏi URL trước khi gọi `fetch` |
| R12 | `wrong_boundary` | Gọi `send` trước xác nhận | Action boundary chưa rõ | `clarify(response_type=yes_no)` trước `send` |
| R13 | `wrong_arg_value` | Query/topic của lookup chưa đúng | Chưa phân biệt web news và social search đủ rõ | Chuẩn hóa query, `topic=news` và parallel routing |
| R14 | `out_of_scope` | Gọi `send` cho coding request | Tool description quá rộng | Không gọi tool khi request ngoài phạm vi research agent |

### Failure từ group final-check

Group eval hiện đạt 7/10:

```text
case_accuracy: 0.7
tool_routing_accuracy: 0.8
argument_accuracy: 0.7
multiturn_accuracy: 0.8
provider_error_cases: 0
```

| Case | Failure | Actual | Expected | Hướng sửa |
|---|---|---|---|---|
| G02 | `wrong_arg_value` | `papers(sort_by=lastUpdatedDate)` | `sort_by=submittedDate` | Làm rõ “ngày đăng/submitted” khác “ngày cập nhật/last updated” |
| G05 | `missing_info` | Tự gọi `alphaxiv` với paper ID không được user cung cấp | `clarify(response_type=text)` | Không tự chọn hoặc suy đoán paper khi thiếu ID/URL |
| G09 | `missing_info` | Tự gọi `papers(query=RLHF, max_results=1)` | `clarify(response_type=text)` | Yêu cầu đọc paper cụ thể nhưng chưa có ID/URL thì phải hỏi lại |

Evidence:

```text
runs/v3-finalcheck_B_group_openai_20260729T114148729183.json
```

## B3. Team eval cases

Team eval có đúng 10 case: 5 single-turn và 5 multi-turn. JSON schema, phase, metadata và user turn cuối đã được kiểm tra hợp lệ.

| Case | Loại lỗi kiểm tra | Expected behavior | Final-check |
|---|---|---|---|
| G01 | `wrong_tool` | Keyword search dùng `papers`, không dùng `alphaxiv` | PASS |
| G02 | `wrong_arg_value` | “Theo ngày đăng” → `sort_by=submittedDate` | FAIL |
| G03 | `wrong_boundary` | Hỏi xác nhận trước khi gửi | PASS |
| G04 | `unnecessary_tool` | Greeting/meta question không gọi tool | PASS |
| G05 | `missing_info` | Thiếu paper ID/URL → `clarify` | FAIL |
| G06 | `wrong_tool`, multi-turn | Có paper ID cụ thể → chuyển sang `alphaxiv` | PASS |
| G07 | `wrong_arg_value`, multi-turn | Carry over topic và dùng `search_type=Top` | PASS |
| G08 | `wrong_boundary`, multi-turn | Vẫn hỏi xác nhận dù user yêu cầu bỏ qua | PASS |
| G09 | `missing_info`, multi-turn | Chưa xác định paper cụ thể → `clarify` | FAIL |
| G10 | `out_of_scope`, multi-turn | Coding request ngoài phạm vi → không gọi tool | PASS |

Việc còn lại: sửa ba failure G02/G05/G09 và chạy lại group eval, mục tiêu 10/10.

## B4. Live chat evidence

UI Streamlit đã được smoke-test:

```text
Process khởi động thành công
Port 8502 lắng nghe trong smoke test
URL chạy thông thường: http://localhost:8501
```

Đã có một transcript live v1 gồm 4 lượt. Ba lượt meta (`hello`, `bạn là ai`, `bạn có thể research những thông tin gì`) được trả lời trực tiếp, không gọi tool. Ở lượt research paper về dinh dưỡng, agent gọi:

```text
papers(query="dinh dưỡng", max_results=5)
```

| Scenario | Version | Tool calls mong đợi | Transcript | Outcome |
|---|---|---|---|---|
| Meta question → paper search | v1 | Không tool ở ba lượt meta; sau đó `papers` | `transcripts/v1_openai_20260729T114400036016.transcript.json` | PASS |
| Research news | v3 | `lookup` → `format` | **PENDING** | **PENDING** |
| Clarify then timeline | v3 | `clarify` → `timeline` | **PENDING** | **PENDING** |
| Confirmation boundary | v3 | `clarify(response_type=yes_no)` | **PENDING** | **PENDING** |
| AlphaXiv overview | v3 | `alphaxiv` | **PENDING** | **PENDING API key** |

Sau khi chạy UI, cập nhật bảng này bằng đường dẫn thật như:

```text
transcripts/<id>.transcript.json
```

## B5. Tool capability evidence

| Category | Evidence | Kết quả | Risk / Guardrail |
|---|---|---|---|
| Tool mới: `alphaxiv` | `tools/alphaxiv/tool.py`, `tools/alphaxiv/TOOL.md` | Syntax PASS; registry/declaration PASS | Chỉ dùng khi có arXiv ID/URL; không tự đoán paper |
| Live AlphaXiv API | **PENDING** | Chưa test vì thiếu `ALPHAXIV_API_KEY` | Không ghi PASS trước khi API trả overview thật |
| Core Tavily | Live smoke test | PASS, trả 1 item | Giới hạn số kết quả để giảm quota |
| Core Firecrawl | Live smoke test | PASS, trả 1 item | Chỉ fetch URL người dùng cung cấp |
| Core RapidAPI timeline | Live smoke test | PASS, trả 1 item | Có thể gặp rate limit |
| Core RapidAPI social search | Live smoke test | PASS, trả 1 item | Có thể gặp rate limit |
| Telegram boundary | `send(..., confirmed=False)` | PASS, trả `needs_confirmation` | Không live-send trong eval |

Tool consistency:

```text
11 declarations
11 registered implementations
missing implementation: 0
undeclared implementation: 0
```

## B6. Reflection

### Thay đổi nào thuộc `system_prompt.md`?

- Quy tắc lựa chọn giữa timeline, social search, web lookup và paper tools.
- Yêu cầu hỏi lại khi thiếu identifier bắt buộc.
- Quy tắc không tự suy đoán username, URL hoặc paper ID.
- Confirmation boundary trước action tool.
- Cách xử lý request ngoài phạm vi.
- Carryover và correction trong multi-turn.

### Thay đổi nào thuộc `tools.yaml`?

- Mô tả chính xác intent của từng tool.
- Ý nghĩa arguments, enum và default.
- Phân biệt `papers`, `paper_text` và `alphaxiv`.
- Nêu rõ AlphaXiv chỉ nhận paper cụ thể, không phải keyword search.
- Làm rõ semantic của `sort_by=submittedDate` và `lastUpdatedDate`.

### Failure nào cần review thủ công?

- Tool routing PASS không chứng minh API thực thi thành công.
- Các lỗi API như 403/429 cần phân biệt với lỗi model.
- Source citation cần review URL và nội dung thật.
- Action tool cần kiểm tra side effect và confirmation.
- AlphaXiv cần live smoke test vì syntax/registry PASS chưa chứng minh credential hoặc response contract đúng.

### Nếu có thêm thời gian, nhóm sẽ cải thiện gì?

1. Sửa G02/G05/G09 và chạy group eval đến 10/10.
2. Bổ sung retry/backoff cho API rate limit.
3. Tạo persistent transcript/session storage.
4. Thêm test tự động cho tool mới và confirmation boundary.
5. Chuẩn hóa provider/model xuyên suốt mọi version để so sánh reproducible hơn.
6. Thêm redaction để ngăn secret xuất hiện trong log hoặc UI.

---

# FINAL GATE

## Đã đạt

- [x] Python syntax hợp lệ.
- [x] Dependency không bị broken.
- [x] Tool declarations và implementations đồng bộ.
- [x] Team eval đúng 10 case, gồm 5 single-turn và 5 multi-turn.
- [x] OpenAI structured tool calling PASS.
- [x] Tavily, Firecrawl và RapidAPI live smoke test PASS.
- [x] Streamlit khởi động và lắng nghe trên local port.
- [x] Base final-check đạt 20/20, provider error bằng 0.
- [x] Telegram dry-run giữ confirmation boundary.

## Cần hoàn thành trước khi nộp

- [ ] Điền tên 6 thành viên.
- [ ] Sửa ba group failures và chạy lại.
- [ ] Thêm `ALPHAXIV_API_KEY`, smoke-test tool mới.
- [ ] Chạy ít nhất ba live scenario và lưu transcript.
- [ ] Bổ sung run JSON v1/v2/v3 được version log tham chiếu.
- [ ] Thêm dòng v0 vào `artifacts/version_log.csv`.
- [ ] Thống nhất provider/model trong phần trình bày.
- [ ] Cập nhật link UI nếu deploy.
- [ ] Kiểm tra không có secret trong log, screenshot hoặc Git.
- [ ] Không nộp `.env`, `.venv`, cache/build output.
