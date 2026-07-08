# TODO — IC 產品毛利率 Dashboard

專案骨架已建立，以下為待完成事項。分成 4 大區塊：**環境啟用** → **功能補完** → **部署上線** → **未來擴充**。

---

## 一、環境啟用 (先做這些才能跑起來)

- [ ] 建立 Python 虛擬環境
  ```bash
  python -m venv .venv
  .venv\Scripts\activate           # macOS/Linux: source .venv/bin/activate
  ```
- [ ] 安裝套件：`pip install -r requirements.txt`
- [ ] 產生假資料 (寫進 `data/raw/`)：`python scripts/generate_sample_data.py --seed 42`
- [ ] 建立第一個 admin 帳號：`python deploy/scripts/init_admin.py --username admin`
- [ ] 複製 `.env.example` → `.env`，並填入 `COOKIE_KEY`
  ```bash
  python -c "import secrets; print(secrets.token_hex(32))"   # 產生長隨機字串
  ```
- [ ] 本機啟動測試：`streamlit run app/main.py`
- [ ] 執行單元測試：`pytest tests/`

---

## 二、功能補完 (code 內留的 TODO)

### `src/analytics/trend_analysis.py`
- [ ] **PVM 三因子拆解** — `pvm_decomposition()` 目前只回傳 revenue/profit 前後期總和，需補：
  - Price effect  = Σ (P1 − P0) × Q1
  - Volume effect = Σ (Q1 − Q0) × P0
  - Mix effect    = residual
- [ ] 在 `3_Trend_Analysis.py` 頁面畫出 PVM 瀑布圖 (Plotly Waterfall)

### `app/pages/1_Product_Analysis.py`
- [ ] 加入「單一料號 drill-down」：選一顆 IC → 顯示該產品的
  - 月度價格 vs 成本折線
  - 良率變化
  - Top 客戶清單

### `app/pages/4_Cost_Breakdown.py`
- [ ] 加入「售價 vs 成本散布圖」(需要 join 銷售資料，不能只用 costs 表)
- [ ] 良率影響分析：`gross_margin_pct` 對 `yield_rate` 的散布 + 迴歸線

### `app/pages/9_Admin.py`
- [ ] 在 UI 內直接**新增/停用使用者** (目前僅唯讀顯示)
- [ ] 修改密碼功能 (呼叫 `authenticator.reset_password`)

### 資料層
- [ ] `src/etl/clean.py` — 目前只有 3 個 helper，補：
  - 匯率標準化：把非 USD 交易轉成 USD (`src/etl/normalize_currency.py`)
  - 日期範圍檢查、重複訂單偵測

---

## 三、部署上線

- [ ] 產生 SSL 憑證
  - **開發用 self-signed**：
    ```bash
    openssl req -x509 -newkey rsa:2048 -nodes -days 365 \
        -keyout deploy/nginx/certs/privkey.pem \
        -out    deploy/nginx/certs/fullchain.pem \
        -subj "/CN=localhost"
    ```
  - **正式用**：向公司 CA 或 Let's Encrypt 申請，放到同一位置
- [ ] `docker compose build` 確認可 build
- [ ] `docker compose up -d` 啟動整組服務
- [ ] 驗證 `curl -k https://localhost/_stcore/health` 回 200
- [ ] 瀏覽器打開 `https://<主機IP>/` 測試登入 + WebSocket 即時互動
- [ ] 檢查 Nginx access log 有 `101 Switching Protocols` (代表 WS 通了)
- [ ] 設定容器重啟策略、log 輪替 (docker-compose 已加 `restart: unless-stopped`)

---

## 四、未來擴充方向

- [ ] **接真的 SQL 資料庫** (替代 CSV)
  - 在 `requirements.txt` 打開 `sqlalchemy` / `pyodbc` / `psycopg2-binary`
  - 只改 `src/data/loader.py`，UI 與 analytics 完全不動
- [ ] **SSO 整合** (LDAP / OIDC / Azure AD)
  - 替換 `streamlit-authenticator`，改用 `streamlit-oauth` 或自寫 middleware
- [ ] **Let's Encrypt 自動續憑** — 加一個 `certbot` sidecar container
- [ ] **CI/CD** — GitHub Actions：跑 pytest + build image + push registry
- [ ] **權限細分** — 目前只有 admin/viewer，可加：
  - `analyst`：可看 + 匯出，不能改設定
  - `product_manager_XXX`：只能看特定產品系列
- [ ] **預測模組** — 用 `statsmodels` / `prophet` 對月度營收、毛利率做 3~6 個月預測
- [ ] **客戶分群** — `scikit-learn` KMeans/DBSCAN 對客戶做行為分群
- [ ] **匯出報告** — 一鍵產生 PDF/PPT 月報 (可用 `reportlab` 或 `python-pptx`)
- [ ] **告警機制** — 毛利率跌破閾值時發 email / Slack

---

## 五、資料相關 (由使用者提供)

- [ ] 確認實際 ERP 匯出檔的欄位是否與 `src/data/schema.py` 對得起來，不對就更新 schema
- [ ] 定義各成本項目在公司內部的分攤規則 (目前假資料是隨機的)
- [ ] 補上實際的產品/客戶主檔到 `data/raw/`
- [ ] 決定資料更新頻率 (每日 / 每月批次) 與觸發方式
