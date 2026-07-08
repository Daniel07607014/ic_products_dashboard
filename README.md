# IC 產品毛利率 Dashboard

Streamlit-based dashboard for tracking gross margin across an IC product portfolio.
Analyses cover product, customer, time-series and cost-structure dimensions.
Ships with a sample-data generator so you can spin the app up before real data lands.

## 快速開始 / Quick start

### 1. 本機開發 (Local development)

```bash
# Windows PowerShell / cmd — bash / zsh works the same
python -m venv .venv
.venv\Scripts\activate            # macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt

# 產生範例資料 (寫進 data/raw/)
python scripts/generate_sample_data.py --seed 42

# 初始化第一個 admin 帳號 (產生 config/auth_config.yaml)
python deploy/scripts/init_admin.py --username admin

# 設定環境變數
copy .env.example .env             # macOS/Linux: cp .env.example .env
# 編輯 .env，將 COOKIE_KEY 換成長隨機字串

# 啟動
streamlit run app/main.py
# → 開啟 http://localhost:8501
```

### 2. 正式部署 (Docker + Nginx)

```bash
# 準備 SSL 憑證 (開發用 self-signed)
openssl req -x509 -newkey rsa:2048 -nodes -days 365 \
    -keyout deploy/nginx/certs/privkey.pem \
    -out    deploy/nginx/certs/fullchain.pem \
    -subj "/CN=localhost"

# .env 與 config/auth_config.yaml 準備好之後
docker compose up -d --build
# → https://localhost/ (self-signed 憑證會有瀏覽器警告)
```

## 目錄結構

```
app/           Streamlit UI (pages, auth, shared components)
src/           Business logic (data loading, ETL, analytics — no Streamlit dependency)
scripts/      Sample-data generator
config/       Settings and auth config
deploy/       Dockerfile support (nginx.conf, hash_password.py)
data/raw/     Input CSVs (gitignored)
tests/        pytest suite
```

參閱 `CLAUDE.md` 了解完整分層原則與開發約定。

## 常用指令

```bash
pytest tests/                         # 執行單元測試
streamlit run app/main.py             # 本機啟動 dashboard
python deploy/scripts/hash_password.py  # 產生 bcrypt 密碼 hash
docker compose build && docker compose up -d
docker compose logs -f app            # 看 app 記錄
docker compose down                   # 停掉整組服務
```
