# Phân công công việc — Day 04 Research Agent

## 1. Mục tiêu chung

Nhóm hoàn thiện Research Agent với các đầu ra bắt buộc:

- Chạy baseline `v0` và ba vòng cải tiến thật `v1`, `v2`, `v3`.
- Có ít nhất một tool mới do nhóm tự xây dựng.
- Có đúng 10 team eval cases: 5 single-turn và 5 multi-turn.
- Có giao diện chat hiển thị tool trace và lưu transcript.
- Có evidence từ run JSON, metrics và live chat.
- Hoàn thiện `artifacts/REPORT.md`.
- Không commit hoặc nộp `.env`, API key, `.venv` và cache.

Provider/model thống nhất:

```text
Provider: openai
Model: gpt-4o-mini
```

## 2. Việc chung đầu tiên

Không sửa prompt hoặc tool declaration trước khi chạy baseline `v0`.

```powershell
cd D:\lab\Day04-G24-E403\starter_v0
.\.venv\Scripts\Activate.ps1

python run_eval.py `
  --provider openai `
  --model gpt-4o-mini `
  --version v0 `
  --suite base `
  --eval-cases data/eval_base.json
```

Baseline hợp lệ khi:

```text
provider_error_cases = 0
measured_cases = total_cases
```

## 3. Phân công 6 thành viên

| Thành viên | Vai trò | File/thư mục sở hữu | Kết quả bàn giao |
|---|---|---|---|
| Người 1 | Baseline và phân tích lỗi | `runs/`, `analysis/` | Metrics v0, danh sách case fail, ba giả thuyết |
| Người 2 | Tối ưu system prompt | `artifacts/system_prompt.md` | Ba vòng cải tiến v1–v3 |
| Người 3 | Thiết kế team eval | `data/eval_group.json` | Đúng 10 case và kết quả group eval |
| Người 4 | Xây tool mới | `tools/<tool_moi>/` | `tool.py`, `TOOL.md`, smoke test, YAML đề xuất |
| Người 5 | Xây giao diện | `app.py`, dependency UI | UI chat, tool trace và transcript |
| Người 6 | Report, demo và QA | `artifacts/REPORT.md` | Report A/B, demo scenarios, final checklist |

---

## 4. Người 1 — Baseline và phân tích evidence

### Nhiệm vụ

1. Chạy baseline `v0`.
2. Kiểm tra metrics và provider errors.
3. Parse run JSON:

```powershell
python scripts/parse_runs.py runs/ --output analysis/base_runs.csv
```

4. Với từng case fail, đọc:

```text
observed_mismatch
failures
actual_tool_calls
tool_results
```

5. Bàn giao bảng:

| Case ID | Failure type | Expected | Actual | Giả thuyết |
|---|---|---|---|---|
| | | | | |

### Không được sửa

- `artifacts/system_prompt.md`
- `artifacts/tools.yaml`
- `data/eval_base.json`

### Done khi

- Có file run `v0`.
- Có đủ metrics.
- Có ít nhất ba giả thuyết dựa trên failure thật.
- Mọi `tool_results` có error đều được review thủ công.

---

## 5. Người 2 — Tối ưu system prompt

### File sở hữu

```text
artifacts/system_prompt.md
```

### Quy trình

1. Nhận failure analysis từ người 1.
2. Chọn đúng một giả thuyết.
3. Sửa prompt.
4. Chạy đúng một version.
5. So sánh metric trước/sau.
6. Tiếp tục với giả thuyết kế tiếp.

Ví dụ chạy `v1`:

```powershell
python run_eval.py `
  --provider openai `
  --model gpt-4o-mini `
  --version v1 `
  --suite base `
  --eval-cases data/eval_base.json
```

Thay `v1` thành `v2` hoặc `v3` ở vòng tương ứng.

### Nguyên tắc

- Mỗi version chỉ kiểm chứng một thay đổi chính.
- Không hard-code đáp án của eval vào prompt.
- Không chạy v1/v2/v3 với ba artifact giống nhau.
- Mỗi version phải có reason, hypothesis và metric.

### Done khi

- Có evidence riêng cho v1, v2, v3.
- Mỗi version có thay đổi và giả thuyết rõ ràng.
- Có thông tin để cập nhật `version_log.csv` và report.

---

## 6. Người 3 — Team eval

### File sở hữu

```text
data/eval_group.json
```

### Yêu cầu

- Đúng 10 case.
- 5 case single-turn dùng `query`.
- 5 case multi-turn dùng `turns`.
- `phase` luôn là `"B"`.
- Có `metadata.what_it_tests`.
- Turn cuối của case multi-turn phải là user turn được chấm.

Phân bổ failure type đề xuất:

| Failure type | Số case |
|---|---:|
| `wrong_tool` | 2 |
| `wrong_arg_value` | 2 |
| `wrong_boundary` | 2 |
| `unnecessary_tool` | 1 |
| `missing_info` | 2 |
| `out_of_scope` | 1 |

Kiểm tra JSON:

```powershell
python -m json.tool data/eval_group.json > $null
```

Chạy sau khi khóa `v3`:

```powershell
python run_eval.py `
  --provider openai `
  --model gpt-4o-mini `
  --version v3 `
  --suite group `
  --eval-cases data/eval_group.json
```

### Done khi

- JSON hợp lệ.
- Đúng cơ cấu 5 single-turn và 5 multi-turn.
- Các case kiểm tra nhiều routing/boundary khác nhau.
- Group eval có run JSON và không có provider error.

---

## 7. Người 4 — Tool mới bắt buộc

### Phạm vi sở hữu

```text
tools/<tool_moi>/
├── tool.py
└── TOOL.md
```

Tool đề xuất:

```text
deduplicate_sources
```

Mục đích: loại các research item trùng URL hoặc tiêu đề trước khi format digest.

Ưu điểm:

- Không cần API key mới.
- Không tiêu quota.
- Có thể unit/smoke test độc lập.
- Dễ trình bày giá trị trong demo.

### Bàn giao thêm

Người 4 chuẩn bị nhưng không tự merge:

- Đoạn đăng ký cho `tools/__init__.py`.
- Declaration đề xuất cho `artifacts/tools.yaml`.
- Ví dụ input/output.
- Smoke-test command.

Hai file dùng chung chỉ được tích hợp một lần bởi trưởng nhóm:

```text
tools/__init__.py
artifacts/tools.yaml
```

### Done khi

- Input hợp lệ chạy thành công.
- Input trống được xử lý an toàn.
- Output contract rõ ràng.
- Có `TOOL.md` mô tả khi nào dùng và không dùng.
- Có smoke-test evidence.

---

## 8. Người 5 — UI Streamlit

### File sở hữu

```text
app.py
```

Nếu dùng Streamlit, bổ sung:

```text
streamlit>=1.30.0
```

Cài:

```powershell
python -m pip install "streamlit>=1.30.0"
```

### Yêu cầu

UI phải tái sử dụng:

```python
run_model_tool_loop
```

từ `chat.py`; không tự viết một agent loop khác.

UI phải hiển thị:

- User request.
- Assistant response.
- Tool name.
- Tool arguments.
- Tool result hoặc error.
- Version/artifact.
- Transcript đã lưu.

Chạy:

```powershell
streamlit run app.py
```

### Done khi

- Mở được `http://localhost:8501`.
- Chat được nhiều lượt.
- Tool trace hiển thị rõ.
- Transcript được lưu.
- Không render hoặc log API key.

---

## 9. Người 6 — Report, demo và final QA

### File sở hữu

```text
artifacts/REPORT.md
```

### Report phần A

Hoàn thành sớm:

- Tên team và thành viên.
- Provider/model.
- Agent làm được gì.
- Danh sách tool.
- 3–5 câu hỏi mẫu.
- Link UI.
- Demo scenarios.

### Demo scenarios tối thiểu

1. Research bình thường và gọi đúng research tool.
2. Request thiếu dữ kiện, agent gọi `clarify`, user bổ sung ở lượt sau.
3. Action nhạy cảm, agent yêu cầu confirmation trước khi gửi.

Nên có thêm:

4. Scenario sử dụng tool mới.
5. Cùng một request cho thấy khác biệt v0 và version mới.

### Report phần B

- Evidence v0–v3.
- Failure analysis.
- 10 team eval cases.
- Live chat evidence.
- Tool capability evidence.
- Reflection.

### Final QA

```text
[ ] Có run JSON cho v0, v1, v2, v3
[ ] provider_error_cases = 0
[ ] measured_cases = total_cases
[ ] eval_group.json có đúng 10 case
[ ] Có ít nhất một tool mới
[ ] Tool mới có TOOL.md và smoke test
[ ] UI chạy được và hiển thị tool trace
[ ] Có transcript live chat
[ ] REPORT.md hoàn chỉnh
[ ] Không nộp .env
[ ] Không nộp .venv
[ ] Không có API key trong log, screenshot hoặc report
```

---

## 10. Quy tắc Git và file ownership

Mỗi thành viên dùng một branch:

```text
member-1-analysis
member-2-prompt
member-3-eval
member-4-new-tool
member-5-ui
member-6-report
```

Không sửa file thuộc sở hữu người khác nếu chưa trao đổi.

File dễ conflict:

```text
artifacts/tools.yaml
tools/__init__.py
artifacts/version_log.csv
requirements.txt
```

Các file này chỉ do một người tích hợp cuối cùng cập nhật.

Không commit:

```text
.env
.venv/
__pycache__/
*.pyc
API key hoặc token
```

## 11. Thứ tự tích hợp

```text
1. Baseline v0
2. Failure analysis
3. Prompt v1
4. Tool mới + declaration
5. Prompt/eval v2
6. Team eval + UI + Report A
7. Demo và nhận feedback
8. Prompt v3
9. Group eval cuối
10. Report B và final QA
```

## 12. Kênh bàn giao nội bộ

Mỗi người khi hoàn thành gửi một tin theo mẫu:

```text
Tên:
Branch:
File đã thay đổi:
Lệnh test:
Kết quả:
Evidence file:
Vấn đề còn lại:
```

Không gửi API key hoặc nội dung `.env` vào nhóm chat.
