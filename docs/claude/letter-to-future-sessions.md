# 給未來 Session 的信

寫於 2026-07-10，Fable 5 session。你大概率是 Sonnet 或更小的模型。
這封信講三件使用者沒問、但對這個環境最重要的事，以及這套制度會怎麼死、怎麼防。

## 一、使用者會在 session 之間自己動 repo——開場永遠先對現實

這是本環境最重要的單一事實。實例：某次 session 之間，整個頁面結構被重構
（0~9 十頁 → 4 頁）、auth 從每頁把關改成 main.py 集中把關、admin 頁被刪除——
而前一個 session 的記憶與 TODO.md 都還停在舊世界。

所以：**不要信任何記憶或文件對「現在長什麼樣」的描述，開場花 30 秒驗證**：
`git log --oneline -5` + `ls app/pages/` + 讀 TODO.md 頂部。
成本極低，錯誤方向工作的成本極高。使用者不會主動告訴你他改了什麼——
對他來說那是「他自己的 repo 的正常演進」，不是需要交接的事項。

## 二、祕密衛生有一筆既成事實要處理

- admin 密碼曾以明文出現在對話記錄中（建帳號時使用者直接打在訊息裡）。
  對話記錄不是祕密儲存區。**正式部署前提醒使用者 rotate admin 密碼與 COOKIE_KEY**。
- 永遠不要把密碼/金鑰 echo 進指令、寫進回報文字、或存進非 gitignore 的檔案。
  需要使用者提供祕密時，請他寫進 `.env` 或用互動終端自己跑，而不是貼在對話裡
  ——貼了就永久留在 transcript。
- 現況：`.env`、`config/auth_config.yaml`、`ic_venv/` 都已在 `.gitignore`
  （2026-07-10 驗證）。順帶一課：這一段的初稿寫著「ic_venv 不在 gitignore 裡」，
  兩天內就被使用者的修改變成錯的——文件裡的「已驗證」只代表寫下當天，
  要引用前自己重新驗一次。

## 三、有幾顆地雷還沒爆，先知道位置

1. **Python 版本漂移**：本機 3.13.7，CLAUDE.md 舊版與 Dockerfile 假設 3.11。
   本機測試全過 ≠ Docker build 會過。第一次 `docker compose build` 時把版本差異
   當成首要嫌疑人。
2. **重構後頁面是殼、views 是肉**：4 個 page 檔背後的實際內容在
   `app/components/views/`（trend / product / cost / customer / detail / admin）。
   TODO.md 第二區塊的功能構想（PVM 瀑布、drill-down、售價成本散布）已對應到
   views 檔案，但尚未實作——`pvm_decomposition()` 在
   `src/analytics/trend_analysis.py:39` 仍是 stub。改 UI 先找 views/，不是 pages/。
3. **`streamlit run` 由使用者自己跑**。harness 裡起 Streamlit server 會佔住前台
   或需要背景管理，且登入流程需要瀏覽器互動。驗證 UI 改動的極限是：
   py_compile + pytest + 用真資料實算函式。真正的畫面驗收要請使用者開瀏覽器。

## 這套制度最可能的死法（按機率排序）與預防

1. **文件-現實漂移**（就是它殺死了舊 CLAUDE.md）：改了東西沒回寫文件，
   三次之後文件比沒有更糟——它會自信地誤導你。
   防法：落地協議（CLAUDE.md 開場第 3 條）+ 開場對現實（本信第一節）。
2. **規則通脹**：每踩一個坑加一條規則，兩個月後沒有模型會全部讀完，
   等於全部沒寫。防法：maintenance.md 的精簡觸發條件（LESSONS >20 條就合併升格）。
   加新規則前先問：這條跟既有規則重複嗎？能合併嗎？
3. **便利性侵蝕**：未來 session 覺得某條規則麻煩（備份、驗證不自驗、成本閘門），
   「就這一次」跳過，然後成為慣例。防法：maintenance.md 規定「讓規則變寬鬆的修改
   必須先問使用者」。你現在想跳過的那條規則，就是當初被踩坑換來的那條。
4. **cargo-cult 執行**：照模板填空但不理解動機，例如派工時「動機」欄寫
   「使用者要求」——那不是動機。防法：三件套中動機欄的意義是讓 agent 遇到
   意外時知道怎麼取捨；寫不出取捨依據就是還沒想清楚，回去想。

## 交接欄（context 快用完的 session 把未完成事項寫在這）

（目前無未完成交接事項。）
