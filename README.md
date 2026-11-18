# VICE HORIZON VI — 離線 App 版 (PWA)

這個資料夾是可以「安裝到手機主畫面、沒網路也能玩」的版本。所有程式庫、3D 模型、貼圖、字型都已經放在資料夾裡，不需要連到外部網站。

## 放到 GitHub Pages（免費）

1. 到 https://github.com 註冊並登入。
2. 右上角「+」→「New repository」，名稱例如 `vice-horizon`，選 **Public**，按「Create repository」。
3. 在新的 repository 頁面點「uploading an existing file」，把這個資料夾**裡面的所有檔案和資料夾**拖進去（index.html 要在最外層），按「Commit changes」。
4. 進「Settings」→ 左邊「Pages」→ Source 選「Deploy from a branch」，Branch 選 `main`、資料夾 `/ (root)`，按「Save」。
5. 等 1～2 分鐘，網址會是 `https://你的帳號.github.io/vice-horizon/`。

## 安裝到手機

- **Android（Chrome）**：打開網址，畫面下方會出現「📲 安裝遊戲到主畫面」按鈕，或從右上角選單選「安裝應用程式」。
- **iPhone / iPad（Safari）**：打開網址 → 點下方「分享」→「加入主畫面」。

第一次打開需要網路（約 27 MB），之後從主畫面開啟就能離線玩。

## 更新遊戲

改完檔案重新上傳後，把 `sw.js` 第 3 行的 `CACHE` 版本號改掉（例如最後的 `-2` 改成 `-3`），玩家下次開啟就會自動下載新版。

## 放回 Google Sites

Google Sites →「插入」→「嵌入」→ 選「依網址」，貼上 GitHub Pages 的網址即可。
