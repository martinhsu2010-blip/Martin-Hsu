# T-006 spec v1 — 繁體中文「空白鍵」文字修正（Antigravity Stage 1 試跑）

**狀態：提案（Proposed）；尚待 Claude 規格審查及 Martin 明確批准「T-006 v1」。未獲准開始實作。**  
**作者：** ChatGPT  
**Base commit：** `6b669b8`（GitHub main：`6b669b8f4f796bd6e6cd6dcf07e1517f2804843d`；實作開始時須再次核對最新 `main`）  
**依據：** `COLLAB.md` v3.5（§3、§4.1、§6、§7.3、§9）、`AGENTS.md`、`TASKS.md` 的 `Gemini qualification`、`DECISIONS.md` D-013／D-019／D-020／D-021。  
**任務 Owner／Implementer：** Gemini（Antigravity Remote Agents）；`Required Gemini stage: 1`，目前 `TASKS.md` 已記錄 `Current stage: 1`。  
**指定理由：** 只更新 `index.html` 中 `STRINGS["zh-TW"].shared_space` 的單一翻譯值，不影響邏輯；可用既有 i18n 與 UI 檢查驗證，適合作為階段 1 的首個完整任務。  
**Reviewer／Integrator／Releaser：** Claude。  
**優先級：** P2（Gemini Stage 1 試跑）。  
**驗證狀態：** `designed`；尚無程式 PR、CI 結果或實機測量。  
**指定分支／PR：** `gemini/T-006` → `main`；一個任務、同一實作者、唯一程式 PR。

**規格原則：** 未寫入本規格的任何修改均未獲批准。若需求變動，應重新出版本並由 Martin 批准；不能以本提案當作開工許可。

## 1. 目標與不在範圍內的事項

在遊戲語言設為繁體中文 `zh-TW` 時，鍵盤操作提示中的空白鍵標籤應顯示 **「空白鍵」**，而不再是 **`Space`**。切回英文 `en` 時仍顯示 **`Space`**。

T-006 同時是 `COLLAB.md` v3.5 §4.1 定義的 **Gemini Stage 1 首項試跑**，用來檢查 Antigravity 能否讀取 `AGENTS.md`、依規定從 `main` 建立分支、保持極小 diff、如實列出測試結果與限制、交出可由 Claude 審查的 PR。**完成 T-006 並不自動取得 Stage 2 權限**。

**不在範圍內：** 任何其他翻譯鍵值、英文文案、HTML fallback、標記／DOM、CSS／UI 版面、按鍵綁定、JavaScript 邏輯、鍵盤事件、攝影機、物理／碰撞、車輛、世界生成、交通／警察 AI、渲染／效能、存檔、依賴、模型／貼圖等素材、`sw.js`／CACHE、任何協作文件、`.github/`、`tools/` 及任何不相關缺陷。

## 2. 固定限制與開工閘門

1. **目前不得開工。** `COLLAB.md` v3.5 已由 Martin 批准（D-021），但 **T-006 v1 尚未批准**。必須先由 Claude 審查本完整規格、Martin 明確批准「T-006 v1」，之後由 Claude 以 docs-only PR 將本規格原文登錄至 `specs/T-006-spec-v1.md`、將 `TASKS.md` 的 T-006 正確登記在 `Ready for Implementer`，並回報已合併的最新 `main` SHA，才可啟動 Antigravity。即使基準列為 `6b669b8`，開工時仍以登錄後的最新 `main` 為分支起點。
2. **前置任務已符合：** `TASKS.md` 與 D-019 顯示 T-005B 已合併、發布並由 Martin 於裝置驗收；不必重新執行 T-005B。開工前仍需重新確認目前**沒有其他尚未合併的程式 PR**；Codex/Gemini 共用單一 PR 鎖。
3. Antigravity 須從最新 `main` 建立 **`gemini/T-006`** 分支，提交至 `main` 的**一個** PR，使用 repo PR 模板。禁止直接 push `main`、自行 merge、與 Codex 共同修改同一 PR。若平台不允許指定分支，應回報實際分支名稱並由 Claude 判斷是否符合試跑；不得假稱使用了 `gemini/T-006`。
4. 實作者的**已提交 diff** 只能修改 `index.html` 的一行：GitHub 變更統計必須為**一個檔案、+1／−1**。其他翻譯、空白、縮排、換行風格或檔案均不得改動。
5. 階段 1 只能修改 `index.html`；不得新增或更新 `tools/test/`，不得修改 `sw.js`／CACHE、任何 `.md`／`specs/` 文件、`.github/`、manifest、遊戲版本字串、二進位素材或其他路徑。版本與文件由 Claude 在審查／發布流程處理。
6. 不得修改 `vh_save`、離線 PWA、單一 renderer、控制輸入及任何其他遊戲行為；無新網路請求、依賴或 draw call。預期無新增 CPU／GPU 工作，但**不得宣稱已量到的 FPS**。
7. 如果畫面驗收需要 CSS、HTML 或邏輯調整，**停止並回報失敗／阻礙**；不可藉機擴大本試跑規格。若缺少可執行的測試環境，如實列入未執行清單，由 Claude 獨立補驗；不得把未跑過的測試寫成 PASS。
8. **D-013 安全檢查：** Claude 審查每個 Gemini PR 時，必須在 GitHub 重新確認 `main` 必須經 PR、`enforce_admins=true`、禁止強推、禁止刪除、repository rulesets 為空；在 PR review 記錄查核時間、來源和結果。設定不符或無法查證即視為 hard violation，停止合併並交 Martin 處理。

## 3. 詳細需求與精確修改位置

以登錄後最新 `main` 的 `index.html` 為準，尋找檔案開頭的 `I18N_TABLE_*` 標記和 `STRINGS` 物件；**請使用語系區塊與鍵名定位，不依賴固定行號**。

| 位置 | Key | 原文（before） | 新文（after） | 規定 |
|---|---|---|---|---|
| `STRINGS["zh-TW"]` | `shared_space` | `"shared_space": "Space",` | `"shared_space": "空白鍵",` | **唯一允許修改的來源行** |
| `STRINGS["en"]` | `shared_space` | `"shared_space": "Space",` | **不變** | 不可修改 |
| `#desktop-hints` 的 HTML | `data-i18n="shared_space"` | `<span data-i18n="shared_space">Space</span>` | **不變** | 保留 HTML fallback |

原有提示列含 `WASD`、`Shift`、`F`、`M` 等按鍵標籤；`data-i18n` 已連接到本地化表。**不可修改** `tr()`、`changeLanguage()`、HTML 文字、CSS 或按鍵處理。

**運行結果：**

- 語言為 `zh-TW`：已顯示的 `#desktop-hints` 對應按鍵文字為 **空白鍵**；不應在標籤內換行、覆蓋相鄰 `F`／`M` 提示或遮擋文字。
- 切回 `en`：同一按鍵文字還原為 **Space**。
- 空白鍵原先用於跳躍／手煞車的行為完全不變。

**畫面證據（附在 PR 說明或留言，不可提交到 repo）：**

1. **390 × 844 CSS px** 的窄螢幕檢查，`zh-TW`，顯示包含 **空白鍵** 的完整鍵盤提示列，無換行、重疊或遮蔽。
2. **1280 × 800 CSS px** 的桌面檢查，`zh-TW`，同一列顯示 **空白鍵**，無換行、重疊或遮蔽。

`#desktop-hints` 在真正的手機模式通常會被隱藏。390 × 844 畫面允許在**瀏覽器 DevTools 或測試工具的暫時 DOM 檢查中強制顯示既有元素**，不能提交任何來源變更；必須在 PR 明確註記「forced-visible narrow-layout inspection」，不得冒充正常手機 HUD 截圖。完全看不到文字的截圖不算通過。若無法無修改 CSS 地通過，應回報失敗並停止。

## 4. 任務與可驗收條件

| ID | 名稱 | 前置條件 | 驗收 |
|---|---|---|---|
| **T-006** | `zh-TW` `shared_space` 翻譯；Gemini Stage 1 首次試跑 | T-005B 已完成並驗收；T-006 v1 由 Martin 批准、Claude 登錄；共用 PR 鎖空閒；qualification 階段仍為 1 | **A1–A8 全部達成** |

**A1 — 分支與單人任務：** PR head 確認是 `gemini/T-006`、base 為 `main`；只有一個程式 PR；由 Gemini 獨立完成，不自行合併。

**A2 — 嚴格 diff：** PR 只包含 `index.html` 一個檔案，GitHub diff 統計 **+1／−1**，且唯一改變為 `STRINGS["zh-TW"].shared_space`：`Space` → `空白鍵`。英文對應值、HTML fallback、CSS、邏輯與其他字元均未修改。

**A3 — CI 及 AGENTS 檢查：** CI 所有已設定的檢查必須通過。Gemini 依現行 `AGENTS.md` 嘗試執行全部強制指令，包括語法、Python/Node i18n、HUD、camera（帶 base SHA）、traffic、collision、suburb、urban；並如實指出環境無法執行的指令。CI 綠燈不表示所有手動檢查都執行過。Claude 應獨立補驗必要檢查，未取得必要證據前不得批准 PR。

**A4 — 繁體中文 UI：** `zh-TW` 的 `#desktop-hints [data-i18n="shared_space"]` 實際呈現 **空白鍵**，並提供 **390 × 844** 與 **1280 × 800** CSS px 兩張合格截圖；窄螢幕強制顯示時須清楚揭露。

**A5 — 英文及行為不變：** 切回 `en` 時顯示 **Space**；英文字串、HTML fallback、原空白鍵跳躍／手煞車及其餘遊戲行為不變，PR 內附明確驗證描述（畫面或文字）。

**A6 — Stage 1 流程證據：** PR 說明要明確記錄 Gemini **實際讀取** `COLLAB.md` v3.5、`AGENTS.md`、`TASKS.md`、`DECISIONS.md` 與 T-006 已登錄 spec，並列出它實際遵守的關鍵限制：D-021/Stage 1 範圍、單一程式 PR、分支命名、最新 main、單行 diff、禁區、不能修改文件／CACHE、不得自行 merge、誠實揭露限制。Claude 必須根據 PR metadata／diff 獨立核對，不可僅相信聲明。

**A7 — PR 必填「實際執行／未執行的 AGENTS 測試」清單：** 在 PR 說明中**逐一列出以下每個命令**，並分成「實際執行（附 PASS／FAIL 及證據）」與「未執行（寫明原因）」兩類；不得省略、以「all tests PASS」取代，或把 CI、Claude 代跑的結果冒稱 Gemini 自行執行。`camera_check` 必須標示所用 base SHA。對於 `collision_check` 及其他需要完整 git history 的檢查，如缺少歷史應在未執行／阻礙欄說明。必要項目為：

```text
python3 tools/test/syntax_check.py
python3 tools/test/i18n_check.py
node tools/test/i18n_check.mjs
node tools/test/hud_check.mjs
node tools/test/camera_check.mjs <base-main-sha>
node tools/test/traffic_check.mjs
node tools/test/collision_check.mjs
node tools/test/suburb_check.mjs
node tools/test/urban_check.mjs
```

另外，若執行了 `node tools/test/route_legality.mjs` 或瀏覽器 smoke test，也應單獨列出實際結果；若未執行瀏覽器 smoke test，註明原因。PR 說明須將「Gemini 本機／遠端代理實際執行」、「GitHub CI 執行」、「Claude 獨立補驗」分成不同來源，不能混稱。任何 FAIL 不得寫成 PASS；若有測試無法執行，須由 Claude 審視是否仍能在補驗後通過 A3。

**A8 — Claude 安全與試跑裁定：** Claude 在 review 逐項查核 A1–A7 以及 D-013 `main` 保護五項條件（PR required、enforce_admins=true、force push disabled、deletion disabled、rulesets empty），記錄實際查核證據、時間、來源及 Stage 1 trial **通過／未通過**。未確認分支保護、未補足必要測試或發現越權變更，不得合併。

## 5. 驗證計畫與證據

**開工前（Claude／Martin）：** 核對 D-021 的 Stage 1 qualification、T-006 的個別批准與登錄 PR、最新 `main` SHA，以及共用程式 PR 鎖。`6b669b8` 是設計基準，不代表登錄後程式分支仍以此 SHA 起始。

**靜態／GitHub diff：** 兩個 `shared_space` 語系值、`#desktop-hints` HTML fallback 及 PR 變更檔案統計。必須是一個檔案、+1／−1；不可額外提交截圖或測試碼。

**自動測試：** 逐項按 A7 列示的 AGENTS 清單跑測試並記錄 PASS／FAIL／未執行；確認 GitHub Actions 既有 CI 綠燈。因 Stage 1 無權修改 `tools/test/` 或 `.github/workflows/pwa-cache-check.yml`，本任務**不新增新測試，也不涉及 Stage 2/3 的 CI 接入程序**。Claude 獨立補驗 Gemini 未能執行的必要檢查及任何存疑結果；不實陳述視為 hard violation。

**瀏覽器／UI：** 確認繁中、英文切換後的同一鍵盤提示列及 390×844／1280×800 CSS px 截圖，檢查文字換行、重疊、遮擋；如果無法操作瀏覽器，明確報告未測，不得假稱 A4/A5 通過。鍵盤輸入的行為沿用舊邏輯，可用適當的瀏覽器測試或 Claude 獨立比對保證未改程式。

**Claude review／發布：** 依 v3.5 首次 Gemini PR 的嚴格審查執行；確認分支保護五項要求、測試聲明真實與最小 diff。取得證據後標記 `code-reviewed`，合併並由 Claude 在**自己的** release PR 更新 `sw.js` CACHE 及相關紀錄，確認 GitHub Pages 的版本更新與離線支援。不能用規格或 headless 結果冒充實機數據。

**Martin 實機驗收：** 在 Samsung S26 Ultra 與 Samsung Tab S11 的正式釋出版本上切換 `zh-TW`／`en`，檢查對應文字是否正確、無其他顯示或控制回歸；若手機正常 UI 不顯示 `#desktop-hints`，此項只驗證無意外 UI 回歸，桌面提示版面由 Claude 的兩尺寸 browser 證據驗收。Martin 記錄裝置與通過／不通過。此任務不增加新的 FPS 數值門檻；除非 Martin 實際量測，禁止標示 `device-measured` 或聲稱 FPS 改善。

**升階提醒：** T-006 發布並經 Martin 驗收通過，只能做為 Claude 建議晉升 Stage 2 的資格證據；**Gemini 不自動升級**。只有 Martin **另行明確批准「Gemini 升至階段 2」**，由 Claude 登錄必要決策與治理文件後才有 Stage 2 權限。

## 6. 風險與待決事項

1. **手機版提示不可見：** `#desktop-hints` 通常在手機隱藏；390×844 檢查若暫時強制顯示必須明確標註，不能假稱正常手機顯示。
2. **單行變更 vs. 版面：** `空白鍵` 可能比 `Space` 寬；若出現溢出或遮擋，不能在此 PR 補改 CSS，交由 Claude／Martin 決定另案。
3. **設計與實作 base 不同：** 本規格對照 `6b669b8`，但需先完成規格批准與登錄；Gemini 實作須讀取當時最新 `main`，並確認原值仍為 `Space`。若已被他人修改，停下而不是覆寫。
4. **現有文件的舊版本字樣：** `AGENTS.md` 首行與 `TASKS.md` 開頭仍可能出現 v3.4 字樣；目前已登錄的 `COLLAB.md` v3.5／D-021／`Gemini qualification: 1` 具有優先性。不得由實作者於 T-006 順手修改任何文件；若 Claude 認為需要修正，以獨立 docs-only PR 處理。
5. **審查與安全：** Antigravity Remote Agents 可能不經逐項確認執行命令，D-013 `main` 保護是關鍵保險；Claude 須查證保護設置及實際 PR 證據。測試失敗、缺失或不實回報不得掩蓋。
6. **未批准：** COLLAB v3.5 已批准，不代表 T-006 v1 已批准；須經 Claude 審查、Martin 獨立批准、Claude 登錄才能開工。

## 7. 給 Antigravity 的英文 Prompt（依 COLLAB v3.5 §7.3 Stage 1 原文，僅代入 base SHA）

**僅在 Martin 批准 T-006 v1、Claude 登錄並確認程式 PR 鎖空閒後使用。** 下列兩段英文沿用目前 `COLLAB.md` §7.3 Stage 1 的規範；將 `<SHA>` 具體化為本設計 base（若登錄後 `main` 前進，啟動時應替換為最新 SHA）。

```text
Implement T-006 (or the exact assigned Stage 1 task) using the approved spec in specs/ and TASKS.md. Read COLLAB.md, AGENTS.md, DECISIONS.md and the task spec before editing. Base your branch on the latest main (6b669b8) and use gemini/T-006 (or the assigned gemini/T-xxx-short-name). One task, one implementer, one PR; if another code PR is open, do not start.

Your current authorization is Gemini Stage 1 only: localized UI strings, wording, and purely static CSS. For T-006, change exactly the one approved localized string and nothing else. Never change game logic, physics, collisions, vehicles, traffic/police AI, world generation, rendering/performance, save data, sw.js, project documentation, or unrelated code. Do not reformat files. Run the applicable syntax, i18n, and UI checks. Open a PR to main with the repository template, listing the exact changed lines, commands, actual test results, and tests not run. Never push to main or merge. If anything requires a broader edit, stop and report the blocker without opening an out-of-scope PR.
```

## HANDOFF ChatGPT -> Claude

```text
HANDOFF ChatGPT -> Claude
Task: T-006 spec v1   Base commit: 6b669b8f4f796bd6e6cd6dcf07e1517f2804843d   Read: COLLAB.md v3.5, DECISIONS D-013/D-019/D-020/D-021, TASKS.md (Gemini qualification: Stage 1), AGENTS.md
Context: COLLAB v3.5 is Martin-approved and registered at main 6b669b8; Gemini qualification is Stage 1, but T-006 v1 is still proposed and has not been registered or authorized for implementation.
Context: T-005B is merged, released and Martin-accepted; the shared code-PR lock is reported free, but must be checked again before task start.
Context: T-006 changes exactly one zh-TW STRINGS.shared_space value from Space to 空白鍵; English/HTML/logic/CSS remain unchanged. The PR must disclose each AGENTS check actually run and each not run.
Deliverable: review the attached complete T-006-spec-v1.md; register via Claude-only docs PR and unlock Gemini Stage 1 trial only AFTER Martin explicitly approves T-006 v1. Do not treat COLLAB v3.5 approval as T-006 approval.
SPEC: attached as T-006-spec-v1.md (full text; includes Stage 1 Antigravity English prompt).
```
