# TODO — IC 產品毛利率 Dashboard

本檔是進度帳本：勾選狀態代表事實，完成當輪就要更新（規則見 `docs/claude/maintenance.md`）。
分成 4 大區塊：**環境啟用** → **功能補完** → **部署上線** → **未來擴充**。

---

## 一、環境啟用 ✅ 已完成 (2026-07-08)

- [x] 建立 Python 虛擬環境（實際名稱 `ic_venv`，非 `.venv`；跑法見 CLAUDE.md「環境實況」）
- [x] 安裝套件：`pip install -r requirements.txt`
- [x] 產生假資料 (寫進 `data/raw/`)：`generate_sample_data.py --seed 42`（已改版：成本隨製程/封裝/腳位連動）
- [x] 建立第一個 admin 帳號（`config/auth_config.yaml` 已存在）
- [x] `.env` 已填入隨機 `COOKIE_KEY`（`.env.example` 已刻意刪除，不要重建）
- [x] 執行單元測試：`pytest tests/`（18 passed，2026-07-08）
- [ ] 本機啟動測試：`streamlit run app/main.py`（使用者自己跑；harness 內不啟動 server）

---

## 二、功能補完 (code 內留的 TODO)

### `src/analytics/trend_analysis.py`
- [x] **PVM 拆解**（2026-07-12，實作為價/成本/量/組合**四因子**——成本效果從價格中分離：
  price = Σ(P1−P0)×Q1、cost = −Σ(C1−C0)×Q1、volume = Σ(Q1−Q0)×m0（common SKU、
  加權平均單價/單位成本）、mix = 殘差＝新進/退出料號貢獻；四項加總恆等於 ΔGP，
  tests/test_trend.py 有各因子隔離測試與恆等式測試。注意：單月 vs 單月比較時
  很多料號當月無訂單，mix 會偏大——demo 敘事時說明這點）
- [x] 在「趨勢分析」頁畫出 PVM 瀑布圖（2026-07-12，Plotly Waterfall +
  基期/當期月份選擇，`charts.pvm_waterfall`）

### `app/components/views/product.py` (業績分析 · 產品維度)
- [ ] 加入「單一料號 drill-down」：選一顆 IC → 顯示該產品的
  - 月度價格 vs 成本折線
  - 良率變化
  - Top 客戶清單

### `app/components/views/cost.py` (成本與體質)
- [ ] 加入「售價 vs 成本散布圖」(需要 join 銷售資料，不能只用 costs 表)
- [ ] 良率影響分析：`gross_margin_pct` 對 `yield_rate` 的散布 + 迴歸線

### `app/components/views/admin.py` (資料與管理 · Admin tab)
- [x] 在 UI 內直接**新增/停用使用者**（2026-07-10，mysql backend 時啟用；走 `src/data/users.py`）
- [x] 修改密碼功能（2026-07-10，改走 users 表 `reset_password`，非 authenticator API）

### 資料層
- [ ] `src/etl/clean.py` — 目前只有 3 個 helper，補：
  - 匯率標準化：把非 USD 交易轉成 USD (`src/etl/normalize_currency.py`)
  - 日期範圍檢查、重複訂單偵測

---

## 三、部署上線

- [x] 產生 SSL 憑證（2026-07-10，開發用 self-signed 已放 `deploy/nginx/certs/`；
  對外網址走 Tailscale 的受信任憑證，見下方，nginx 這張只做內層加密）
- [x] `docker compose build` 確認可 build（2026-07-10，CI 也會在每次上 tag 時 build）
- [x] `docker compose up -d` 啟動整組服務（2026-07-10，db + app + nginx + watchtower 全部 healthy）
- [x] 驗證 `curl -k https://localhost/_stcore/health` 回 200（2026-07-10）
- [ ] 瀏覽器打開 `https://<主機IP>/` 測試登入 + WebSocket 即時互動
- [ ] 檢查 Nginx access log 有 `101 Switching Protocols` (代表 WS 通了)
- [x] 設定容器重啟策略 (docker-compose 已加 `restart: unless-stopped`)；log 輪替未設

### Tailscale 對外 https（網址零警告、不開防火牆、不買網域）

原理：Tailscale 在最外層用受信任憑證處理 TLS，內層 nginx 的 self-signed 憑證
瀏覽器永遠看不到，Docker 架構完全不用改。

- [x] 1. 安裝並登入 Tailscale（2026-07-12；CLI 在 `C:\Program Files\Tailscale\tailscale.exe`，
  舊終端機視窗吃不到 PATH 要用完整路徑）
- [x] 2. 開啟 HTTPS 憑證（2026-07-12；tailnet = `taile767b8.ts.net`）
- [x] 3. 掛上 dashboard（2026-07-12）：
  ```powershell
  tailscale serve --bg https+insecure://localhost:443
  ```
  （`+insecure` = 不驗證內層 nginx 的 self-signed 憑證，這段只在本機內部；
  `--bg` 常駐、重開機仍在。關閉：`tailscale serve --https=443 off`）
- [x] 4. 網址：**https://ic-product-dashboard.taile767b8.ts.net**（tailnet only，
  憑證由 Tailscale 自動續期；`/_stcore/health` 已驗回 200。機器名用
  `tailscale set --hostname ic-product-dashboard` 改過——DNS 不允許底線，故用連字號）
- [ ] 5. 分享：管理後台 → Users → **Invite users**（免費可邀 3 人），
  對方裝 Tailscale 接受邀請後用同一網址；未受邀者完全掃不到這台機器
- [ ] 6. 驗收：開網址應見登入頁顯示版本號、瀏覽器鎖頭無警告（使用者自己開瀏覽器確認）

---

## 四、未來擴充方向

- [x] **接 SQL 資料庫**（2026-07-10 完成 MySQL 版：docker `mysql:8.4` + `scripts/init_db.py`
  灌假資料 + `users` 權限表；`DATA_BACKEND=csv|mysql` 可切換。之後接真 ERP 時
  只需把 ERP 匯出灌進同五張表，loader 與上層不用再動）
- [ ] **SSO 整合** (LDAP / OIDC / Azure AD)
  - 替換 `streamlit-authenticator`，改用 `streamlit-oauth` 或自寫 middleware
- [ ] **Let's Encrypt 自動續憑** — 加一個 `certbot` sidecar container
- [x] **CI/CD**（2026-07-10）— `.github/workflows/release.yml`：上 `v*` tag → pytest →
  build → push `ghcr.io/daniel07607014/ic-dashboard`；主機上 Watchtower 每 5 分鐘
  自動 pull 新版重開 app 容器（見 docker-compose.yml）
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
- [x] 決定資料更新頻率與觸發方式（2026-07-11：每日全量重灌，`scripts/daily_etl.py`，
  先驗證 CSV schema 再寫 DB、log 在 `logs/etl.log`；排程用 Windows Task Scheduler，
  註冊指令見腳本 docstring。資料量大到單次載入需數分鐘時改增量）
