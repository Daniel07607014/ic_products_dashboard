# CLAUDE.md — IC 產品毛利率 Dashboard

Streamlit dashboard 分析 IC 產品組合的毛利率（產品／客戶／時間／成本結構切片）。
附合成資料產生器，接真實 ERP 資料前即可運作。

## Session 開場（先做這個）

1. **對現實**：`git log --oneline -5` + `ls app/pages/`。使用者會在 session 之間
   自己大改 repo（發生過整次頁面重構），任何記憶與文件都可能已過時。
2. 讀 `TODO.md` 對照專案現況——它是進度帳本，勾選狀態代表事實。
3. 需要委派、驗證、判斷疑難時，查下方路由表。
4. **改了架構或慣例，同一輪更新本檔對應行 + TODO.md 勾選**（規則：`docs/claude/maintenance.md`）。

## 路由表 — 制度檔案

| 情境 | 讀這個 |
|---|---|
| 要派 subagent、選 model、驗證產出 | `docs/claude/dispatch.md` |
| 不確定該不該升級模型／算不算完成／該不該問使用者 | `docs/claude/judgment.md` |
| 撰寫委派 prompt（搜尋/實作/重構/研究/審查） | `docs/claude/delegation-templates.md` |
| 要修改制度檔或 CLAUDE.md 本身 | `docs/claude/maintenance.md` |
| 想知道 harness 的已知失效模式 | `docs/claude/diagnosis.md` |
| 接手前因後果、未解地雷 | `docs/claude/letter-to-future-sessions.md` |

## 環境實況（2026-07 驗證，與直覺不同處特別注意）

- **OS**: Windows 11。Bash tool 是 Git Bash；PowerShell 5.1 沒有 `&&`/`||`。
- **Python**: 3.13.7（`requirements.txt` 假設 3.11，目前無衝突但升套件時留意）。
- **venv 叫 `ic_venv`（不是 `.venv`）**。跑任何 Python 一律：
  ```bash
  ./ic_venv/Scripts/python.exe scripts/xxx.py
  ./ic_venv/Scripts/python.exe -m pytest tests/ -q
  ```
  不要 activate、不要裸 `python`（那是系統 Python，沒裝套件）。
- **互動輸入必卡死**：`getpass`/`input()` 類程式（如 `deploy/scripts/init_admin.py`）
  在 harness 內跑會永遠等不到輸入。改寫非互動臨時腳本放 scratchpad 執行。
- **終端中文亂碼 ≠ 資料壞掉**（cp950 顯示問題）。用 pandas 讀回驗證，不要重跑。
- `.env.example` 已刻意刪除，不要重建。`.env`、`config/auth_config.yaml`、`data/raw/*`
  皆已 gitignore，永不進 git。
- **資料後端（2026-07-10 起）**：`.env` 的 `DATA_BACKEND=mysql|csv` 切換。
  mysql = docker 裡的 `mysql:8.4`（`docker compose up -d db`，只綁 127.0.0.1:3306，
  named volume `mysql-data` 持久化），使用者也存在 DB 的 `users` 表；
  csv = 舊模式（`data/raw/*.csv` + `auth_config.yaml`），DB 掛掉時的退路。

## 目錄結構與三個邊界

```
app/            # UI 層：只 render + 呼叫 src/，禁止商業邏輯
  main.py       # st.navigation 入口；登入集中在這裡把關
  pages/        # 0_Overview / 1_Product / 2_Industry / 3_Trend / 4_Cost / 5_Admin / 6_Key_Accounts（薄殼，共 7 頁）
  components/   # filters, kpi_cards, charts, data_loader
    views/      # 頁面實際內容在這（trend/product/cost/industry/key_accounts/admin）——改 UI 先找這裡
  auth/         # authenticator.py（登入）+ permissions.py（角色）
src/            # 業務邏輯層：無 Streamlit 依賴，pytest 可直接測
  data/         # CSV → typed DataFrame（loader.py, schema.py）
  etl/          # 清洗 + join → fact table（join.build_fact_table）
  analytics/    # 純函式：metrics, dimension_analysis, ranking, risk, trend_analysis
scripts/        # generate_sample_data.py（合成資料）
config/         # settings.py + auth_config.yaml
tests/          # pytest（test_metrics / test_ranking / test_risk）
docs/claude/    # AI session 制度檔（見路由表）
```

1. **`src/` 不 import Streamlit**。要顯示東西，回傳 DataFrame 讓 `app/` 處理。
2. **金額一律 USD 儲存**（`revenue_usd` 等）。顯示他幣時在 UI 層用 `fx_rates` 轉。
3. **新公式進 `src/analytics/` + 補 `tests/`；新欄位先改 `src/data/schema.py`**。

## 認證（2026-07 重構後）

- 登入集中在 `app/main.py`：未登入時 `st.navigation` 只露出 Login 頁。
- 頁面頂部只需 `require_role("viewer")`（或 `"admin"`）——**不要再加 `require_login()`**，
  那是留給 scripts/notebooks 的 backward-compat。
- 使用者來源依 `DATA_BACKEND`：mysql = DB 的 `users` 表（bcrypt，
  `src/data/users.py` 做 CRUD，權限管理頁可直接新增/停用/重設密碼）；
  csv = `config/auth_config.yaml`（唯讀顯示）。權限管理是獨立頁
  `5_Admin`（`require_role("admin")`，非 admin 連選單都看不到），
  實作在 `app/components/views/admin.py`。

## 常用指令

```bash
./ic_venv/Scripts/python.exe -m pytest tests/ -q                  # 測試
./ic_venv/Scripts/python.exe scripts/generate_sample_data.py --seed 42   # 重生假資料 CSV
docker compose up -d db                                           # 只起 MySQL
./ic_venv/Scripts/python.exe scripts/init_db.py --migrate-users   # 建表 + CSV 灌入 DB + 搬使用者
./ic_venv/Scripts/python.exe scripts/daily_etl.py                 # 每日 ETL：驗證 CSV → 全量灌 DB（log 在 logs/etl.log）
streamlit run app/main.py                                         # 本機啟動（使用者自己跑）
docker compose up -d --build                                      # Docker 整組（db + app + nginx）
```

## 發佈 / CI-CD（2026-07-10 起）

- 上 `v*` tag（`git tag v1.0.0 && git push origin v1.0.0`）→ GitHub Actions 跑
  pytest → build → 推 `ghcr.io/daniel07607014/ic-dashboard`（`.github/workflows/release.yml`）。
- 主機上的 Watchtower 容器每 5 分鐘檢查 GHCR，自動 pull 新 image 重開 app 容器。
- GHCR 映像名必須全小寫——workflow 裡是寫死的，不要改成 `${{ github.repository_owner }}`。

## 資料規格

五個 CSV 在 `data/raw/`，schema 唯一定義處是 `src/data/schema.py`。
mysql 模式下同樣五張表存在 DB（表名 = csv 檔名去副檔名），由 `scripts/init_db.py`
從 CSV 灌入；`src/data/loader.py` 兩種 backend 回傳完全相同形狀的 DataFrame。
`src/etl/join.build_fact_table` 合成單一 fact table（含 `cogs_usd`、`gross_profit_usd`、
`gross_margin_pct`、`yield_rate`）——所有 analytics 函式都從它出發。

## 開發約定

- 快取只在 `app/components/data_loader.py` 用 `@st.cache_data(ttl=...)`，頁面不自己快取。
- 清洗政策集中 `src/etl/clean.py`，不要在頁面散落 `fillna`/`dropna`。
- 註解只寫 *why*，不寫 *what*。
- 待辦與擴充方向一律看 `TODO.md`，本檔不重複維護。
