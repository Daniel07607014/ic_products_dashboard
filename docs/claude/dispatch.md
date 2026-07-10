# 模型調度守則 (Dispatch Rules)

寫於 2026-07-10。所有型號與參數皆經環境實測驗證，非憑印象。

**優先序（不要搞反）**：harness 系統提示對 Agent tool 的政策（例如「未經使用者
要求不得 spawn」）**永遠優先於本檔**。本檔不覆寫它。本檔的角色是：
- 當使用者要求委派、或 harness 政策允許時，規範**怎麼派才對**（三件套、回報合約、升降級）。
- 當任務符合下方「派出去」條件但 harness 政策禁止主動 spawn 時，正確動作是
  **用一句話向使用者提議**：「這需要掃 N 個檔／查外部文件，要我派一個
  {Explore|general-purpose} agent 嗎？」——由使用者的回覆構成授權，不是由本檔。

## 核心原則：指揮官不下場

主對話的 context 是最貴的資源（見 diagnosis.md §2）。主對話負責：決策、整合、
與使用者溝通。大量讀取、掃 repo、查網頁、批次改檔——派出去，只收結論。

## 成本閘門：什麼時候派、什麼時候自己做

**自己做（inline）**：
- 讀 ≤3 個已知檔案的已知區段（用 Read + offset/limit，先 Grep 定位）
- 單點修改、跑測試、跑指令
- 任何 5 分鐘內能收工的事——spawn 的冷啟動成本會超過收益

**派出去（Agent tool）**：
- 掃 >3 個檔案、或不知道目標在哪的搜尋 → `Explore`
- 需要完整讀多個大檔才能下的結論（審查、架構分析）→ `general-purpose` 或 `Plan`
- 網頁研究、外部文件查證 → `general-purpose`
- 同模式批次改 N 個檔 → 先自己改一個當範本，剩下派 agent 照樣板套用

## 本環境實際可用的 agent 與 model（2026-07 實測）

| subagent_type | 工具權限 | 用途 |
|---|---|---|
| `Explore` | 唯讀（不能 Edit/Write） | 找檔案、找符號、「X 定義在哪」。呼叫時註明 breadth：quick / medium / very thorough |
| `Plan` | 唯讀 | 設計實作方案、架構取捨 |
| `general-purpose` | 全部 | 多步驟研究、需要寫檔的委派 |
| `claude` | 全部 | 通用，等同 default |
| `claude-code-guide` | 唯讀+網路 | 只回答 Claude Code / API / SDK 本身的問題 |

**model 參數只接受**：`haiku`、`sonnet`、`opus`、`fable`（省略則繼承主對話）。

| model | 派什麼 |
|---|---|
| `haiku` | 機械性批次工作：照範本套改、格式轉換、簡單搜尋 |
| `sonnet` | 預設工作馬：實作、審查、研究 |
| `opus` | 難題：跨檔不變量推理、連環失敗的除錯、架構決策 |
| `fable` | 若可用才用（本守則寫定後未必還在環境裡）；不可用時 fallback `opus` |

**effort 誠實標註**：這個環境的 Agent tool **沒有 effort 參數**。effort 只能透過
`.claude/agents/*.md` frontmatter 定義（目前不存在此目錄）。不要在派工時
假裝能設 effort；要更深的推理就升 model，不是調不存在的參數。

**執行模式**：Agent 預設背景執行。需要結果才能往下走時，設 `run_in_background: false`。
要延續某個 agent 的 context 追問，用 `SendMessage` 對它的 ID，不要重開新 agent。

## 派工三件套（缺一不派）

每個委派 prompt 必含，模板見 delegation-templates.md：
1. **目標與動機**——不只說做什麼，說為什麼要做（agent 遇到意外時才知道怎麼取捨）
2. **驗收條件**——可機械檢查的完成定義（「測試全過」「回傳 檔案:行號」）
3. **回報格式**——明說要什麼形狀的答案，防止收到一篇作文

## 回報合約

- Subagent 只回：結論、`檔案:行號`、必要的最小引文。
- 長產物（報告、大 diff、資料表）落檔到 scratchpad 或 `docs/`，回報只傳路徑。
- 主模型轉述給使用者時重述重點，不貼原始輸出。

## 升降級路徑

- `haiku` 錯一次 → 直接升 `sonnet` 重派，不重試。
- `sonnet` 同一子任務連錯兩次 → 帶**完整失敗軌跡**（兩次的 prompt、輸出、錯在哪）升 `opus`。
  沒附失敗軌跡的升級等於重新猜，禁止。
- `opus` 解出模式後，同型的剩餘工作降回 `haiku`/`sonnet` 批次套用。
- 同一件事同一方法最多重試兩輪。兩輪後還不行，是方法錯了：換路或問使用者
  （判準見 judgment.md §4）。

## 驗證不自驗

寫產出的 agent 不能當自己的驗收者。驗收一律 fresh-context：

- **檔案落地** → 新 agent（或主對話）read-back：檔案存在、內容完整、路徑正確。
- **程式碼** → 跑測試或實跑，看輸出，不是看程式碼「應該對」。
  本專案：`./ic_venv/Scripts/python.exe -m pytest tests/ -q` + 用真資料算一輪看數字合理性。
- **高風險判斷**（架構、對外行為、刪東西）→ 第二意見：再派一個不知道第一個
  結論的 agent 做同一題，比對答案；分歧就升級或問使用者。
