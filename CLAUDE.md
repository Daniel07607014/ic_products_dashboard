# CLAUDE.md — IC 產品毛利率 Dashboard

This file is loaded automatically by Claude Code. It captures the project's
conventions and the shortest path to being productive.

## 專案目標 / What this is

A Streamlit dashboard analysing gross margin of an IC product portfolio.
Slices data by product / customer / time / cost-structure. Ships with a
synthetic data generator so the app runs even before real ERP data is
plugged in.

## 技術棧 / Tech stack

- **UI**: Streamlit multi-page app (`app/pages/*.py`)
- **Auth**: `streamlit-authenticator` (bcrypt + cookie session)
- **Analytics**: pandas / numpy / plotly (`src/analytics/`)
- **Deploy**: Docker + docker-compose behind Nginx reverse proxy
- **Python**: 3.11

## 目錄結構與分層原則

```
app/            # UI 層。禁止寫商業邏輯，只 render + 呼叫 src/
  auth/         # 登入與角色權限
  pages/        # 每個檔 = 一個側邊欄頁 (0_Overview ~ 9_Admin)
  components/   # 共用 UI 元件 (filters, kpi_cards, charts, data_loader)
src/            # 業務邏輯層。無 Streamlit 依賴，可被 pytest / notebook 直接呼叫
  data/         # 讀 CSV → typed DataFrame (loader.py, schema.py)
  etl/          # 清洗 + join → fact table
  analytics/    # 純函式：吃 DataFrame → 吐 DataFrame / scalar
scripts/        # 一次性/CLI 工具 (目前只有 generate_sample_data.py)
config/         # settings.py + auth_config.yaml
deploy/         # Dockerfile 已在根目錄；此處放 nginx/ + scripts/
data/raw/       # 輸入 CSV (git-ignored；用 generate_sample_data.py 產生)
tests/          # pytest
```

### 三個必須遵守的邊界

1. **`src/analytics/` 不 import Streamlit。** 一切純函式。要顯示東西，回傳 DataFrame 讓 `app/` 處理。
2. **金額統一以 USD 儲存 (`revenue_usd`, `unit_cost_usd`…)。** 需要顯示 TWD/JPY 時，在 UI 層透過 `fx_rates` 轉換。
3. **敏感檔案永不進 git**：`.env`、`config/auth_config.yaml`、`deploy/nginx/certs/*`、`data/raw/*`、`.streamlit/secrets.toml`。都已列入 `.gitignore`。

## 啟動指令 / How to run

```bash
# 本機開發
pip install -r requirements.txt
python scripts/generate_sample_data.py --seed 42
python deploy/scripts/init_admin.py
cp .env.example .env    # 填入 COOKIE_KEY
streamlit run app/main.py

# Docker (Nginx https 反向代理)
docker compose up -d --build
```

## 資料規格 / Input schema

Five CSVs under `data/raw/` — schemas defined in `src/data/schema.py`.

| File | Key columns |
|---|---|
| `product_master.csv` | product_id, product_family, process_node, package_type, launch_date, product_status |
| `customer_master.csv` | customer_id, customer_name, customer_tier (A/B/C), industry, country |
| `sales_transactions.csv` | order_id, order_date, product_id, customer_id, quantity, unit_price_usd, revenue_usd |
| `cost_data.csv` | product_id, period (YYYY-MM), wafer/packaging/testing/overhead cost, yield_rate, unit_cost_usd |
| `fx_rates.csv` | period, currency, rate_to_usd |

`src/etl/join.build_fact_table` merges all five into one per-transaction fact
table with `cogs_usd`, `gross_profit_usd`, `gross_margin_pct` pre-computed.
Every analytics function starts from that fact table.

## 認證與權限 / Auth

- Users defined in `config/auth_config.yaml` (bcrypt password hashes).
- Generate a hash: `python deploy/scripts/hash_password.py`.
- Roles: `admin` (all pages incl. `9_Admin`) and `viewer` (all except admin).
- Every page top-of-file:
  ```python
  require_login()
  require_role("viewer")   # or "admin"
  ```

## 部署架構 / Deployment topology

```
Browser ──https──▶ Nginx (443, deploy/nginx/nginx.conf)
                      │  proxy_pass + WebSocket headers
                      ▼
                  app service (Streamlit :8501, internal only)
                      │  volumes:
                      │    ./data          → /app/data           (rw)
                      │    ./config/auth_config.yaml → /app/config/... (ro)
                      ▼
                  CSV files under data/raw/
```

`app` is not exposed to the host — only `nginx` publishes 80/443.

## 開發約定 / Conventions

- **New calculation → `src/analytics/`, not a page file.** Pages assemble; formulas live in analytics.
- **New raw column → update `src/data/schema.py` first.** Loader will fail loudly if the CSV drifts.
- **Streamlit caching**: use `@st.cache_data(ttl=...)` in `app/components/data_loader.py` — pages should not cache directly.
- **Cleaning policy** is centralised in `src/etl/clean.py`. Don't sprinkle `fillna`/`dropna` around pages.
- **Tests**: add cases to `tests/test_metrics.py` when introducing a new formula. Run with `pytest tests/`.
- **Comments**: only for the *why*. Well-named columns/functions should explain the *what*.

## 常用指令 / Common commands

```bash
pytest tests/                                     # run tests
python scripts/generate_sample_data.py            # regenerate synthetic data
python deploy/scripts/hash_password.py            # bcrypt hash for a new user
streamlit run app/main.py                         # local dashboard
docker compose up -d --build                      # build + start Docker stack
docker compose logs -f app                        # tail app logs
docker compose exec app python scripts/generate_sample_data.py   # regen inside container
```

## 擴充方向 / Future work

- Swap CSV loader for SQL (uncomment `sqlalchemy` / `pyodbc` in `requirements.txt`; only `src/data/loader.py` needs to change).
- Implement PVM waterfall in `src/analytics/trend_analysis.pvm_decomposition`.
- Drill-down page: single product cost/price trend, top customers per SKU.
- SSO integration (LDAP / OIDC) replacing `streamlit-authenticator`.
- Let's Encrypt auto-renewal for the Nginx SSL certificate (`certbot` sidecar).
