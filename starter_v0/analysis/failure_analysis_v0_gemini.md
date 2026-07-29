# Failure analysis — baseline v0 (Gemini)

Run file: `runs/v0_B_base_gemini_20260729T113451236224.json`
Artifact: `v0+peb1c8179815b+t6e9c7a9d521c` · provider `gemini` · model `gemini-3.6-flash`

Baseline hợp lệ: `provider_error_cases = 0`, `measured_cases = 20 / 20`.

| Metric | v0 |
|---|---|
| `case_accuracy` | 0.50 |
| `tool_routing_accuracy` | 0.65 |
| `argument_accuracy` | 0.50 |
| `multiturn_accuracy` | 0.6667 |

`failure_counts`: `wrong_tool` 3 · `out_of_scope` 2 · `missing_info` 2 · `unnecessary_tool` 1 · `wrong_boundary` 1 · `wrong_arg_value` 1

## Bảng case fail

| Case ID | Failure type | Expected | Actual | Giả thuyết |
|---|---|---|---|---|
| R03_web_news_routing | wrong_tool | `lookup(query="AI", topic="news", timeframe="day")` | `lookup(query="tin tức AI hôm nay", ...)` | H3 |
| R08_out_of_scope | out_of_scope | no_tool (refuse) | `policy(query="tool_usage policy...")` | H4 |
| R09_no_tool_capability | unnecessary_tool | no_tool (answer) | `policy(query="chức năng vai trò trợ lý AI")` | H4 |
| R10_missing_handle | missing_info | `clarify(response_type="text")` | `timeline(screenname="sama", limit=5)` | H1 |
| R11_missing_url | missing_info | `clarify(response_type="text")` | `policy(query="tool usage...")` | H1 + H4 |
| R12_confirm_before_send | wrong_boundary | `clarify(response_type="yes_no")` | `send(confirmed=true, text=...)` | H2 |
| R13_parallel_web_and_tweets | wrong_tool | `lookup` **+** `social_search` | `policy(...)` duy nhất | H4 |
| R14_out_of_scope_coding | out_of_scope | no_tool (refuse) | `send(text="```python def fibonacci...")` | H2 + H4 |
| M02_carryover_timeframe | wrong_arg_value | `lookup(query="robotics")` | `lookup(query="robotics news today")` | H3 |
| M06_switch_tool | wrong_tool | `lookup(query="OpenAI")` | `lookup(query="OpenAI news")` | H3 |

## Bốn giả thuyết

### H1 — Prompt cấm hỏi lại nên mọi case thiếu thông tin đều trượt

`artifacts/system_prompt.md` viết thẳng: *"The user is busy and hates being asked
questions… do not ask them back — just make a sensible guess"* và *"pick a
well-known account like Sam Altman"*.

Bằng chứng trực tiếp: R10 trả về `timeline(screenname="sama")` — đúng cái tên mà
prompt gợi ý, chứ không phải model tự suy luận. Agent không bao giờ gọi `clarify`.

Sửa: thay đoạn đó bằng điều kiện bắt buộc gọi `clarify` (thiếu handle, thiếu URL,
trước hành động có side effect). Kỳ vọng `missing_info` 2 → 0.

### H2 — `send` không có confirmation boundary, lại bị prompt xúi hành động ngay

`tools.yaml` mô tả `send` là *"Gửi một đoạn văn bản đi."* — không nói gửi **đi
đâu**, không nói cần xác nhận. Prompt bồi thêm: *"When the user wants to send,
post, or publish something, just go ahead and do it."*

Bằng chứng: R12 gọi thẳng `send(confirmed=true)` bỏ qua bước hỏi; R14 dùng `send`
như kênh **trả lời** người dùng (nhét code Fibonacci vào `text`) chứ không phải để
đăng bài.

Sửa: mô tả `send` nêu rõ đích đến là kênh Telegram bên ngoài và bắt buộc
`clarify(response_type="yes_no")` trước; prompt nói rõ tool không phải kênh trả
lời. Kỳ vọng `wrong_boundary` 1 → 0.

### H3 — `query` không có convention nên model nhồi cả topic/timeframe vào

`tools.yaml` mô tả `query` chỉ là *"Truy vấn"*. Model lặp lại thông tin đã nằm ở
`topic` và `timeframe` ngay trong `query`.

Ba bằng chứng cùng một dạng:

- R03: expected `AI`, got `tin tức AI hôm nay`
- M02: expected `robotics`, got `robotics news today`
- M06: expected `OpenAI`, got `OpenAI news`

Đáng chú ý là routing của cả ba case đều **đúng** (`lookup`); chỉ argument sai.

Sửa: nêu convention trong description — `query` chỉ chứa chủ đề thuần, không lặp
lại thông tin đã truyền qua `topic`/`timeframe`. Đây là fix rẻ nhất, chạm 3 case.

### H4 — Ép "một bước, một tool" vừa chặn parallel call vừa đẻ ra tool call bừa

Prompt: *"Always finish the request in a single step. Pick one tool."*

Hệ quả kép:

1. R13 cần **hai** tool (`lookup` + `social_search`) nhưng agent chỉ được phép gọi một.
2. Khi câu hỏi vốn **không cần tool nào** (R08 hỏi tích phân, R09 hỏi "bạn là gì"),
   agent vẫn buộc phải gọi một tool và chọn bừa.

Bằng chứng mạnh cho vế 2: so hai run cùng prompt nhưng khác số declaration —

| tools.yaml | Tool bị gọi bừa ở R08/R09/R11/R13 |
|---|---|
| 11 tool (`t...ee55f2ba381e`) | `send` |
| 14 tool (`t...6e9c7a9d521c`) | `policy` |

Cùng một prompt, chỉ thêm declaration, mà "nạn nhân" đổi từ `send` sang `policy`.
Nghĩa là nguyên nhân **không** nằm ở mô tả của một tool cụ thể, mà ở sức ép "phải
gọi gì đó" do prompt tạo ra. Sửa mô tả `send` thôi sẽ chỉ đẩy lỗi sang tool khác.

Sửa: cho phép nhiều tool call trong một lượt, và nêu rõ trường hợp **không gọi
tool nào** (câu hỏi ngoài phạm vi research, câu hỏi về chính năng lực của agent).

## Thứ tự đề xuất cho v1 → v3

Mỗi version chỉ kiểm chứng một giả thuyết:

1. **v1 — H3**: sửa `tools.yaml`, thêm convention cho `query`. Rẻ nhất, chạm 3 case, không đụng prompt.
2. **v2 — H1 + H2**: viết lại phần hỏi lại và confirmation boundary trong prompt (2 nhóm này cùng gốc "không bao giờ gọi `clarify`").
3. **v3 — H4**: bỏ ràng buộc "single step / one tool", nêu rõ khi nào không gọi tool.

## Ghi chú vận hành (ảnh hưởng mọi người chạy eval)

**Quota Gemini free tier tính theo `PerDayPerProjectPerModel`** — mỗi key chỉ có
**20 request/ngày cho mỗi model**, kèm giới hạn ~5 request/phút. Một lần chạy base
eval tốn ~25 request, nên một key đơn lẻ **không đủ cho dù chỉ một lần chạy**.

Đã xử lý trong `providers/gemini_provider.py`:

- xoay vòng `GEMINI_API_KEY`, `GEMINI_API_KEY_2..N` (5 key ⇒ ~100 request/ngày/model);
- gặp 429 per-minute thì đổi key ngay; gặp 429 `PerDay` thì **loại hẳn** key đó khỏi vòng xoay;
- gặp 503 `UNAVAILABLE` (model quá tải, không phải quota) thì retry có backoff;
- khi mọi key cạn quota ngày, báo lỗi nói rõ nên đổi `--model` hoặc `--provider`.

Vì quota tách theo **model**, đổi `--model` sẽ được bucket mới — đây là cách nhanh
nhất khi hết quota giữa buổi.
