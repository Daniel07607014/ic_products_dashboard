# Harness 診斷 — 三大失效模式與修法

寫於 2026-07-10（Fable 5 session）。依據：本專案實際 session 記錄，非推測。
其他制度檔（dispatch.md / judgment.md / maintenance.md）皆引用本檔結論。

## 1. 文件與現實脫節（最容易出錯）

**證據**：CLAUDE.md 寫 Python 3.11、`.venv`、`.env.example`、`app/pages/0~9` 十頁架構、
每頁都要 `require_login()`。實際上：Python 3.13.7、venv 叫 `ic_venv`、`.env.example` 已刪除、
頁面已重構為 4 頁（0_Overview / 1_Performance / 2_Cost / 3_Data）、登入已集中在
`app/main.py` 的 `st.navigation`，頁面只呼叫 `require_role()`。
TODO.md 的「環境啟用」區塊全部未勾選，但實際上全部已完成。

**後果**：每個新 session 都會照過時文件行動——用錯 venv、想恢復被刻意刪除的檔案、
在新頁面加上已廢棄的 `require_login()`。錯誤方向的工作 + 使用者糾正 = 雙重浪費。

**修法**（已落實）：
- CLAUDE.md 重寫為與現實一致的精簡路由（見本次改版）。
- 落地協議：**改了架構、慣例、或檔案結構，同一輪就要更新 CLAUDE.md 對應行與 TODO.md 勾選**。
  規則寫在 maintenance.md。判準：如果下一個 session 只讀 CLAUDE.md + TODO.md，
  它對專案狀態的理解會不會是錯的？會，就是還沒落地。

## 2. 主對話當工人用（最漏 token）

**證據**：本 session 為了規劃一個功能，在主對話全文讀入了十多個檔案
（所有 pages、所有 analytics、components）。每一輪對話這些內容都重新佔用 context，
直到壓縮丟失。而其中多數檔案只需要「有哪些函式、簽名長怎樣」。

**後果**：context 提早耗盡 → 壓縮 → 丟失早期決策 → 重新推導或做出矛盾決定。

**修法**：
- 已知檔案+大概位置 → `Read` 加 `offset`/`limit`，或先 `Grep` 定位再讀小段。
- 要掃超過 3 個檔案（>3，與 dispatch.md 的閘門一致）、或不知道東西在哪
  → 派 Explore agent（read-only），主對話只收結論與 `檔案:行號`。詳見 dispatch.md。
- 長產物（報告、diff、資料 dump）一律落檔，主對話只傳路徑。

## 3. Windows 環境陷阱重複踩坑（最浪費來回）

**證據**：本 session 實際踩過：
- `echo "password" | python init_admin.py` 卡死——Windows 的 `getpass` 直接讀 console
  不讀 stdin，pipe 進去永遠等不到輸入。最後用 TaskStop 殺掉、改寫非互動腳本才過。
- 終端輸出中文/符號變亂碼（`→` 變 `��`）——cp950 編碼顯示問題，檔案本身沒壞，
  不要因此重跑或改檔。
- PowerShell 5.1 沒有 `&&`／`||`，bash 語法貼過去直接 parser error。

**後果**：每個陷阱第一次踩都是一次完整的失敗來回（執行→卡住→診斷→換路）。

**修法**：環境實況集中寫在 CLAUDE.md「環境實況」段（單一位置，避免散落）。
核心三條：
1. 跑 Python 一律 `./ic_venv/Scripts/python.exe ...`（Bash tool）——不要 activate，不要裸 `python`。
2. 任何會互動輸入的程式（getpass、input、Read-Host）在這個 harness 都會卡死：
   改寫成非互動臨時腳本放 scratchpad 執行，用完即刪。
3. 輸出亂碼 ≠ 資料壞掉。先用 pandas 讀回來驗證內容再下判斷。
