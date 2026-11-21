# T-007 spec v1 — Game Hub「下一站靈感」卡片（Gemini Stage 2 首項試跑）

**狀態：Proposed／提案，待 Claude 審查與 Martin 明確批准 T-007 v1；未授權實作。**  
**作者／設計 Owner：** ChatGPT。**實作者／實作 Owner：** Gemini（Antigravity Remote Agents）。  
**Reviewer／Integrator／Releaser：** Claude。**Priority：** P2。  
**Base commit：** `20a793a5c37cf85d161532e1b683911c7ae4f5d6`（D-023 已登錄之 main；正式開工使用當時最新 main，若變動需確認 diff 並更新任務紀錄）。  
**依據：** `COLLAB.md` v3.5 §3、§4.2、§7.3、§9；`AGENTS.md`；`TASKS.md` Gemini qualification；D-013、D-021、D-022、D-023。  
**Required Gemini stage：** 2，且本任務為升階後**第一項強制 Stage 2 trial**。  
**指定 branch：** `gemini/T-007`；PR base `main`；全任務僅一個程式 PR。  
**路由理由：** 完整但單一的 Game Hub 展示互動，包含局部 HTML、既有 `STRINGS` 中英翻譯和一個按鈕事件；沒有持久化、核心世界／物理／渲染系統相依，能以自動回歸測試獨立驗收。  
**目前驗證層級：** `designed`；不宣稱程式已完成、CI 已通過、實機已測量或 Martin 已批准。

**本文件為唯一完整工作規格。** 除文中明確授權的變更外不得「順手重構」。對於無法遵守的要求，Gemini 應停止、回報，而非自行擴權。

## 1. 目標與明確不做的事

在現有 Game Hub 的 **WORLD** 分頁新增一張「**下一站靈感／Next Stop**」探索卡片。玩家能按「**換個地點／Next idea**」按鈕，依固定順序輪流瀏覽遊戲內四個已有的觀光／兜風目的地，每張包含地點名稱、簡短建議與 `1 / 4` 至 `4 / 4` 進度。這是**不帶獎勵的遊玩靈感**，不是新任務、導航或快速傳送。玩家可在 S26 Ultra／Tab S11 上直接看見並操作，且既有繁體中文／英文切換可以立即更新卡片文字。

**不做：** 新增地圖位置、地圖圖示、導航／waypoint、傳送、景點解鎖、獎勵、隨機世界事件、每日任務、車輛控制、物理、碰撞、交通／警察 AI、地形／世界生成、renderer 或渲染效能變動、相機、存檔讀寫及 schema 變更。不得做新分頁、新模態視窗、新資產、聲音／動畫特效或遊戲主迴圈更新。此功能不具「已完成景點」紀錄。

## 2. 固定限制、依賴與開始閘門

1. **先審查再批准：** Claude 必須先收到此完整規格，完成 spec review；只有 Martin 在同一完整規格可見的對話中明確說「批准 T-007 v1」或同義語，Claude 才能透過 docs-only PR 原文登錄 `specs/T-007-spec-v1.md`，於 `TASKS.md` 標記 Implementer Gemini／Required stage 2／Stage 2 trial 並確認 main SHA。**D-023 的升階批准不等於 T-007 規格批准。**
2. **資格和鎖：** 開工時 `TASKS.md` 的 Gemini qualification 必須仍是 `Current stage: 2` 或更高、沒有 paused／rollback；T-006 的完成與 Martin 驗收紀錄可核查；Codex 與 Gemini 共用的**單一尚未合併程式 PR 鎖**必須空閒。若不符，停止、不開新 PR。
3. **整個任務只由 Gemini 實作**；從最新 main 建立 `gemini/T-007`，使用 repo PR template；一個 task 一個 PR；不直推 main、不自行合併；若 Antigravity 自動生成其他分支名稱，停下並向 Martin／Claude 回報，不以第二個 PR 迴避。
4. **允許修改的檔案只有：** `index.html`（WORLD 分頁 HTML、兩語 `STRINGS` 翻譯、局部 UI 控制事件與必要的 scoped 樣式）及**新增** `tools/test/explore_picks_check.mjs`（單一可重跑回歸測試）。不得更動既有 `tools/test/` 測試來放寬斷言。`css/app.css`、`sw.js`、`AGENTS.md`、`COLLAB.md`、`TASKS.md`、`DECISIONS.md`、`specs/`、`HANDOFF.md`、`LOG.md`、`.github/`、任何二進位素材、manifest、其他檔案皆不得由 Gemini 修改。
5. 保留現有 `#quick-actions`（native dialog）、五個 `HUB_TABS`／`HUB_PANELS`、`openGameHub()`、`closeModals()`、原 WORLD 按鈕、原語言系統 `VH_I18N.apply()`／`changeLanguage()`、`#desktop-hints` 與所有控制、存檔及輸入行為。不得更改 `vh_save`、設定儲存或新建 localStorage／sessionStorage／IndexedDB／cookie 記錄。
6. **零新渲染負擔：** UI 僅由原本 Game Hub 的 HTML/CSS 組成；不建立 Three.js 物件、WebGL texture、renderer、Cannon body/shape；**零新增 WebGL draw calls、零新增物理 bodies/shapes**。事件只在按鈕按下時執行；不加入 `requestAnimationFrame`、`setInterval`、`setTimeout`、per-frame listener 或常駐 polling。
7. PWA 離線可用、現有單一 renderer、`vh_save` 兼容、不引入外部 CDN、npm runtime dependency、額外資產或網路請求。`sw.js` CACHE 更新僅 Claude 於發布處理。真實手機 30 FPS 是既有專案目標；本小型 UI 任務不宣稱改善 FPS。

## 3. 詳細功能規格

### 3.1 精確入口、範圍與版面

- **入口：** 點左上角 minimap `#radar-container` 進 Game Hub，點 `#hub-world-tab`（WORLD），在現有 `section#hub-world` 內、原 WORLD 動作區下方，顯示**一張**探索卡片模組。不得把它放到 `#game-canvas` 上方的常駐 HUD，亦不得新增第六個 Hub tab。
- **建議 DOM 錨點（供稽核）：** 新模組根元素 `id="explore-picks"`；唯一操作按鈕 `id="explore-next"`、`type="button"`；四張卡片以 `data-explore-card="0"`、`"1"`、`"2"`、`"3"` 識別。不與既有 ID 重複。新模組位於 `#hub-world` 內，不搬移 `#desktop-hints`、`#notice-area` 或既有按鈕。
- **模組內容：** 標題「🧭 下一站靈感／🧭 Next Stop」、說明「純探索建議；不會設定導航或開始任務。／Just an idea; no waypoint or mission is started.」、目前景點名稱與短描述、一行數字進度 `1 / 4`…`4 / 4`，以及「換個地點／Next idea」按鈕。四張卡片必須保留於 HTML 中，非選中卡片具有真正的隱藏狀態，不得同時顯示多於一張。建議以現有 `hidden` 狀態／`hidden` class 實現，不新增第三方 UI 套件。
- **視覺：** 沿用現有 `hud-glass`、`font-vice` 與青／粉／琥珀色等既有視覺語彙；卡片寬度不得超出 WORLD 面板可視寬度，上限 **440 CSS px**；內距手機 **12 px**、較寬裝置 **16 px**，圓角 **16 px**。按鈕可觸高度 **≥44 CSS px**；內文 **≥12 CSS px**；在窄寬度必須自動換行、不橫向溢位。只准局部樣式，不能修改全域根字級、Hub 高度或整頁 scroll 行為。
- **可存取性：** 原生 `<button>` 可用觸控及鍵盤 Enter／Space 啟動；保留可見 focus 樣式；卡片容器使用適當區域標籤，切換內容應能由 `aria-live="polite"` 或等效既有 DOM 更新方式通知輔助工具。非當前卡片不應在可存取樹中當成可見內容。不得攔截或覆寫全域鍵盤控制事件。

### 3.2 目的地與不可任意更改的順序

每次新載入頁面預設選擇索引 `0`。按一次依 `0 → 1 → 2 → 3 → 0` 循環。以下四項名稱必須沿用兩個語系的**既有**翻譯 key，不另造地名、不增刪景點：

| 索引 | 既有 key（兩語皆有） | 地點（en／zh-TW，依目前 repo 翻譯） | 本功能新增描述 key |
|---|---|---|---|
| 0 | `ocean_drive` | Ocean Drive／海濱大道 | `explore_tip_ocean` |
| 1 | `starlight_marina` | Starlight Marina／遊艇碼頭 | `explore_tip_marina` |
| 2 | `mount_chiliad_summit` | Mount Chiliad Summit／奇利亞德山頂 | `explore_tip_chiliad` |
| 3 | `ring_expressway` | Ring Expressway／環狀高架 | `explore_tip_ring` |

**精確新增字串（`STRINGS.en`、`STRINGS["zh-TW"]` 必須具有同一組 7 個新 key；表內為原始值）：**

| Key | `en` | `zh-TW` |
|---|---|---|
| `explore_picks_heading` | `🧭 Next Stop` | `🧭 下一站靈感` |
| `explore_picks_note` | `Just an idea; no waypoint or mission is started.` | `純探索建議；不會設定導航或開始任務。` |
| `explore_picks_next` | `Next idea` | `換個地點` |
| `explore_tip_ocean` | `Cruise along the palm-lined coast at dusk.` | `沿著棕櫚樹林立的海岸大道欣賞黃昏。` |
| `explore_tip_marina` | `Visit the marina for a relaxed waterfront drive.` | `前往遊艇碼頭，沿著水岸輕鬆兜風。` |
| `explore_tip_chiliad` | `Follow the winding mountain road toward the summit.` | `沿著蜿蜒山路往山頂前進。` |
| `explore_tip_ring` | `Try one complete lap of the elevated ring road.` | `試著沿高架環線完整兜風一圈。` |

- 所有新增面向玩家的文字使用已有 `data-i18n`／`tr()` 基礎設施；四個靜態卡片的文字能隨 `VH_I18N.apply()` 全面同步，**不需要**修改 `changeLanguage()` 或引入第二套語系狀態。
- 禁止新增「目的地座標」、「選取導航／快速傳送」等對外看似可執行、但實際不動作的按鈕。數字進度只是卡片順序，不可稱為任務完成率。
- 只使用文字／既有 CSS，不使用圖片、遠端資料、地圖畫布、動畫或音效。

### 3.3 UI 互動與生命週期

1. 玩家打開 WORLD 時，四張卡片中**剛好一張可見**，初次載入時是 Ocean Drive／海濱大道，顯示 `1 / 4`。
2. `#explore-next` 每次按下只前進一項；四次按下回到第一張；連按不得跳號或註冊重複 click handler。一次按下不得觸發世界狀態、導航、任務、HUD 常駐視圖或遊戲輸入。
3. 在同一頁面中關閉 Game Hub、切到其他 Hub 分頁再回 WORLD，保留上次選中的卡片；**重新整理頁面則重設為索引 0**。這個索引只存在記憶體，不寫任何持久化儲存，也不讀取既有 save 或改變 `SAVE`／`STATE`。
4. 玩家在 SETTINGS 切換 `en → zh-TW → en`，目前選中卡片**不變**，其標題、描述、按鈕及說明立即切換語系；不得造成中文／英文同時顯示、產生遺漏翻譯或改動其他 UI 字串。
5. 在 Game Hub 關閉時無任何新定時器、渲染、DOM 更新工作；在別的分頁按既有按鈕（天氣、警察、畫質、地圖、關閉）結果和 baseline 一致。
6. 所有 DOM 查找在初始化與按鈕事件內完成；避免熱路徑。新增控制邏輯可放在現有 `setupControlsAndEvents()` 中，或以相鄰單一小函式呼叫；不得改動 `HUB_TABS`／`HUB_PANELS` 的順序或既有 `openGameHub()`、`hideHubPanels()`、`closeModals()` 核心流程。

## 4. 實作任務與逐項可驗收條件

| ID | 名稱 | 依賴 | 可驗收項目 |
|---|---|---|---|
| **T-007** | WORLD「下一站靈感」四張循環卡片（Gemini Stage 2 first trial） | D-023 Stage 2 已登錄；T-006 Done + Martin accepted；Martin 另行批准 T-007 v1；Claude 先登錄 spec；程式 PR 共用鎖空閒 | 以下 A1–A13 全數必要；一個程式 PR |

- **A1 — 治理與 PR：** `TASKS.md` 顯示 Stage 2、T-007 為已批准待實作；PR head `gemini/T-007`、base `main`，僅一個未合併程式 PR；PR 模板填寫完整；Claude 審查時重新查核 D-013：PR required、`enforce_admins=true`、不可 force-push、不可 delete、repository rulesets 為空，**記錄時間與實際結果**。任一不符為 hard violation，停止合併。
- **A2 — 檔案與 diff：** Gemini PR 中只允許 `index.html` 和新增的 `tools/test/explore_picks_check.mjs`；沒有其他更動；`index.html` 只在兩語 STRINGS、新 WORLD 卡片區及其局部事件／樣式範圍有必要變化；所有既有 ID、五個 Hub tab、鍵盤控制及遊戲系統行為不變。
- **A3 — 卡片與尺寸：** WORLD 分頁有 `#explore-picks`、四張 `data-explore-card=0..3`、一個 `#explore-next`；初始只有索引 0 可見，進度 `1 / 4`，可見區不超過 **440 CSS px**，按鈕觸控高度 **≥44 CSS px**、內文 **≥12 CSS px**。沒有第六個 Hub tab。
- **A4 — 循環與隔離：** 從 index 0 起每按一次觀察到 `1,2,3,0`；連續四次之後恰好回到第一張，任意時刻只有一張可見；沒有雙重事件註冊、導航、任務開始、傳送或常駐 HUD 變更。
- **A5 — 會話／重載：** 同頁關閉並重開 Hub、切換 WORLD ↔ SETTINGS 保留索引；完整重新載入後回到索引 0；本功能沒有 localStorage、sessionStorage、IndexedDB、cookie、SAVE 或 saveSettings 讀寫。
- **A6 — 中英雙語：** 新增精確七個 key 且 en／zh-TW 同構；四個地點標題沿用既有 key；在 index 2 時切換 `en → zh-TW → en` 文字立即變更但 index 不變。所有 `i18n_check` PASS；不得有硬編碼的未翻譯中文字落在 STRINGS 之外。
- **A7 — 可存取性與響應式：** 手指點按、鍵盤 Enter／Space 都能觸發；focus 可見、非選中卡片被隱藏並不在可存取樹曝光；在 **360×640**、**390×844**、**844×390**、**1280×800 CSS px** 四種 viewport 可見卡片與按鈕不被裁切、內容可於既有 WORLD 面板滾動、沒有水平溢位或遮住關閉控制；PR 附至少 **390×844 與 1280×800** 實際瀏覽器截圖，其餘兩種報告結果。截圖放 PR 描述／評論，不提交到 repo。
- **A8 — 零核心副作用：** 只在點擊時變動 UI；無 requestAnimationFrame、timer／interval／network，無新 renderer、Three.js、Cannon 物件；新增 **0 個 WebGL draw-call 路徑、0 個物理 body/shape**。不得編輯碰撞、世界、交通／警察、車輛、遊戲主迴圈、`vh_save`。Claude 進行 diff 稽核並視需要以同場景 `renderer.info.render.calls` 作補充證據；本 Stage 2 trial 不需要 Stage 3 的五組 paired 量測。
- **A9 — 真正的專項自動測試：** 新增 `tools/test/explore_picks_check.mjs`，命令 `node tools/test/explore_picks_check.mjs` PASS；測試從**實際 `index.html` 讀取原始 HTML／正式控制程式**，至少斷言四張卡片及唯一按鈕存在、雙語 key 一致、循環 `0→1→2→3→0`、單頁保留與重載重設、無未經授權儲存寫入或導航副作用。**不可在測試中自行複製另一套循環函式當成受測實作**；要透過可重跑的 DOM／event harness 或受控瀏覽器驅動正式程式。測試至少有一項明確 failure assertion；Claude 必須示範移除事件連結或破壞循環規則時測試會 FAIL（可在臨時工作樹操作，不提交破壞檔案）。
- **A10 — AGENTS 必跑與誠實報告：** 逐條嘗試本規格 §5.1 的**九個**既有 AGENTS 測試，以及 A9 的新測試。PR 說明用兩欄列出 `Actually run`／`Not run`，每項包含完整命令、PASS／FAIL／BLOCKED 結果和失敗／未執行原因；附 `main` baseline SHA 與 Node／browser 環境。**未跑不可寫 PASS，CI 綠燈不等同自己跑過**；任何 BLOCKED 給 Claude 獨立補驗，必要測試未通過不得 release。
- **A11 — CI 接線（Claude 負責）：** `tools/test/explore_picks_check.mjs` 由 Gemini 在功能 PR 提交，Claude 親自重跑、審查測試有效性，並於此功能合併／發版的自己 docs／release PR 把該命令接入 `.github/workflows/pwa-cache-check.yml`。**必須確認 GitHub Actions 真正跑過新測試並為 PASS**，不是只看檔案存在；Gemini 不可修改 `.github/`。
- **A12 — Claude 強化 Stage 2 試跑審查：** Claude 逐項檢查 A1–A11、實際開啟 WORLD、語言切換、四個尺寸及既有 Hub 退出路徑；於 PR review **明確寫出 `Stage 2 trial：通過／未通過`**，附自跑命令、CI、影像與 D-013 主分支保護結果。若不合格，最多在同 PR 修正兩輪；失敗後不得繼續安排一般 Stage 2 任務，依 COLLAB §4.2 由 Martin 處置。
- **A13 — Martin 實機接受：** Claude 完成發版後，Martin 在 **Samsung S26 Ultra** 和 **Samsung Tab S11** 各開 WORLD，檢查第一張／四次切換／中英文／Hub 退出／無覆蓋 UI；回報「通過／不通過」與必要截圖。**Martin 尚未實機回報前只可稱 `code-reviewed`／`headless-measured`，不能稱 `device-measured`。** 本任務通過可作為 Stage 2 的首項合格證據；**不代表自動升至 Stage 3**，後續仍須第二項不同範疇任務與 Martin 另行明確升階批准。

## 5. 驗證計畫與交付證據

### 5.1 Gemini 開 PR 前必須逐項嘗試的 AGENTS.md 檢查

在可取得完整 git history 的環境、對實際工作分支執行（`<base>` 應用**開工當時最新 main SHA**，本草案設計基準為 `20a793a5c37cf85d161532e1b683911c7ae4f5d6`）：

```bash
python3 tools/test/syntax_check.py
python3 tools/test/i18n_check.py
node tools/test/i18n_check.mjs
node tools/test/hud_check.mjs
node tools/test/camera_check.mjs 20a793a5c37cf85d161532e1b683911c7ae4f5d6
node tools/test/traffic_check.mjs
node tools/test/collision_check.mjs
node tools/test/suburb_check.mjs
node tools/test/urban_check.mjs
node tools/test/explore_picks_check.mjs
```

前九行是 AGENTS 現有檢查，第十行是 T-007 新的功能回歸測試。依本 repo `AGENTS.md`，還應嘗試使用本機靜態伺服器開啟 headless browser、檢查啟動 console error；若環境不能執行，清楚記錄 `Not run` 原因，由 Claude 補驗。不得用未經實際執行的範例輸出或推測數字當作結果。

### 5.2 PR 說明必附的固定報告格式

- **Scope：** `index.html`、`tools/test/explore_picks_check.mjs`（列出 changed files、diff 大小、四張卡片與事件變更）；確認除此以外無任何修改。
- **Governance：** Stage 2 qualification 來源、使用的 baseline SHA、唯一程式 PR、Gemini 有讀 COLLAB／AGENTS／TASKS／DECISIONS／spec 的具體規則摘要、未編輯 `sw.js`／文件／`.github/`。
- **Actually run：** 每一個**真的由 Gemini 執行**的命令、結果、關鍵 PASS／FAIL 訊息；另列瀏覽器尺寸、語言測試及 console 結果。
- **Not run／blocked：** 對 §5.1 每一個未執行項目逐項說明原因（例如缺 git history／缺 Chromium／環境權限）；如有 FAIL，列明具體失敗、是否已修正重跑及未解決風險；**不得把 CI 或 Claude 的結果混寫為 Gemini 自跑**。
- **Screenshots：** 390×844、1280×800 的 WORLD 卡片畫面；文字說明另兩個 viewport 的結果，並註明真實瀏覽器或 DOM/headless、勿冒充實機照片。
- **Safety：** 無持久化讀寫、無高風險系統改動，新增 0 個遊戲 draw-call／物理實體路徑；未做真實裝置 FPS 量測則寫 `not device-measured`。

### 5.3 Claude 的獨立審核與發版

1. 使用 repo PR diff 確認實際變更檔案與新功能均在 Stage 2 容許範圍；追查任何 out-of-scope 變更或既有測試變弱情形。重新取得 baseline，重跑 §5.1 所有檢查及專項測試，不能採信 Gemini 自報結果代替。
2. 比對 `COLLAB §4.2`：此次確為**第一項 Stage 2 trial**，單一完整功能且無持久化；加強檢查四個 viewport、按鈕生命週期、語系切換、舊的五分頁與最小地圖／設定退出回歸。可用 headless browser 截圖；headless 不等於實機。
3. 審查新回歸測試至少能對一項目標失誤產生 FAIL；檢查遊戲主迴圈、Three.js／Cannon、存檔、`sw.js`、所有新網路請求沒有變動。
4. **重新核驗 D-013 主分支保護**（required PR、enforce_admins、no force push、no deletion、rulesets empty），在 Gemini PR 審查記下核對方法、時間、結果；不能確認即視為 hard violation、暫停合併。
5. 審核通過後按 COLLAB 合併／發布；**僅 Claude**更新 `sw.js` CACHE、必要的 TASKS／DECISIONS／LOG／HANDOFF，及 `.github/workflows/pwa-cache-check.yml` 使新回歸測試在 CI 跑起來；確認 workflow 執行 PASS、網站更新與 PWA 離線工作。先取得其實執行綠燈證據，再將 Stage 2 trial 列為可供 Martin 驗收。
6. Claude 必須在 PR review 留下正式結論：`Stage 2 trial：通過` 或 `Stage 2 trial：未通過`，並附明確證據；發版與 Martin 實機接受是另一道閘門。

### 5.4 Martin 操作驗收（發布後）

在 S26 Ultra、Tab S11 各執行：開遊戲 → 點 minimap → WORLD → 看到「下一站靈感」與 `1 / 4` → 點「換個地點」四次觀察回到 Ocean Drive → 切 SETTINGS 轉繁中／英文再回 WORLD → 關閉／重開 Game Hub 不重設卡片；確認沒有擋住觸控、其他 WORLD 按鈕可正常使用。重載頁面後重設 `1 / 4`。記錄裝置、版本／日期、通過或失敗及畫面；若量 FPS 必須提供真實數字與預設，否則不聲稱 `device-measured FPS`。

## 6. 風險、限制與待 Claude 審查

1. **既有 WORLD 分頁內容／可視高度：** `section#hub-world` 含天氣／警察按鈕、徽章、RPM／nitro，且包含 `#desktop-hints` 固定定位元素。新卡片必須位於面板正常排版內，不修改原隱藏或焦點邏輯；若窄景擠壓，僅可局部縮排或依既有 scroll，不能更動全域 Hub 結構。
2. **既有語系行為：** `VH_I18N.apply()` 已會更新所有 `[data-i18n]`；以四個預先存在的卡片保證切換語系自動更新，避免額外修改儲存語言的 `changeLanguage()`。
3. **多餘 API／權限風險：** 不使用地理定位、資料抓取、真實地圖導航、遠端貼圖與外部服務；選卡絕對不修改世界位置或導航標記。
4. **測試可用性：** 現有 `hud_check.mjs` 使用 Node VM 及假 DOM 驗證 Game Hub；新測試可採類似方式，**但必須驅動真正的新事件處理程式**，不可只測一份複製的 dummy 功能。若測試環境不足，應在 Claude 審查期明確提出阻礙，不以人工點擊代替專項自動測試。
5. **跨版本引用：** 上述 ID／既有 key 依 `20a793a5c37cf85d161532e1b683911c7ae4f5d6` 的 `index.html` 確認；正式執行如 main 前進，Gemini／Claude 須先重新定位來源，並於 PR 陳述差異。若核心 DOM 結構已移動或要求不可在容許範圍內達成，先停下申請規格修訂。
6. **資格不自動晉升：** T-007 就算通過，也只是 Stage 2 試跑的首份證據；`COLLAB §4.2` 明定 Stage 2→3 要連續 **2 項不同範疇**完整任務、零違規、各自發布與 Martin 接受，再由 Martin 另外明確批准；本 spec 不預先授權下一任務。
7. **待 Claude 評估：** WORLD 的卡片是否能在 844×390 橫向短螢幕透過原有 `hub-scroll` 正常捲動，以及讀屏 live region 的可行性；若不行，請回覆規格審查意見，不能擴大改動全域 Hub 或無條件放寬 A7。

---

## 7. Antigravity（Gemini）English prompt — COLLAB v3.5 §7.3 Stage 2

**僅在 Martin 批准 T-007 v1、Claude 登錄完成且鎖空閒後，由 Martin 交給 Antigravity。** 下列為 §7.3 Stage 2 prompt 的任務化版本，含本任務額外要求：

```text
Implement the single approved task T-007 according to TASKS.md, its complete spec at specs/T-007-spec-v1.md, and AGENTS.md. Confirm that the current Gemini authorization recorded in the repository is Stage 2 or higher (D-023). Start from latest main (design base: 20a793a5c37cf85d161532e1b683911c7ae4f5d6), on gemini/T-007; open one code PR only if the shared PR lock is free. Own the whole feature yourself. Stay strictly inside the approved WORLD/Game Hub UI scope. Do not begin before Martin explicitly approves this spec and Claude registers it.

Add one small Next Stop / 下一站靈感 feature to the existing WORLD tab: four fixed, bilingual, non-persistent destination suggestion cards and one Next idea button that cycles 0→1→2→3→0. Reuse the existing i18n keys for destination names and add only the seven new en/zh-TW strings specified in the spec. Keep the selection in memory only, reset it on page reload, preserve it while switching Hub tabs, and update displayed language without changing language-saving logic. This feature must NOT start a mission, set a waypoint, teleport, write storage, or run in the game loop. Preserve all existing Hub tabs, controls, events, saves and offline behavior. Use only index.html and a new focused regression test at tools/test/explore_picks_check.mjs; do not add dependencies or binary assets.

Do not edit cannon-es physics, collisions, vehicle control, world/terrain/road generation, traffic/police AI, renderer/draw-call/performance hot paths, or the vh_save schema. Do not edit sw.js, project documentation, specs, or .github/. Add the targeted automated regression test required by the spec and do not weaken existing tests. Run ALL AGENTS.md checks plus the new T-007 test and report the actual commands, PASS/FAIL results, and limitations. Explicitly list which AGENTS checks YOU RAN and which YOU DID NOT RUN, with reasons; CI results are separate from tests you ran yourself. Include evidence from 390×844 and 1280×800 CSS viewport browser checks when available, and never call headless screenshots real-device evidence.

Stop before making any forbidden cross-system change. Never push to main or merge. If the scope cannot be completed without forbidden changes or the mandatory tests cannot be made meaningful, report the blocker so Martin and Claude can review the whole task. Claude alone owns sw.js, docs, GitHub Actions CI wiring, independent review, release, and Martin's acceptance gate.
```

## HANDOFF ChatGPT -> Claude

```text
HANDOFF ChatGPT -> Claude
Task: T-007 spec v1 (Gemini Stage 2 first trial, PROPOSED / NOT Martin-approved)   Base commit: 20a793a5c37cf85d161532e1b683911c7ae4f5d6   Read: COLLAB.md v3.5 §3/§4.2/§7.3/§9, DECISIONS D-013/D-021/D-022/D-023, TASKS.md Gemini qualification Stage 2, AGENTS.md, specs/TEMPLATE.md
Context: Martin promoted Gemini to Stage 2 under D-023, but T-007 has no spec approval, registration, or implementation authorization yet; T-006 Stage 1 is Done and Martin-accepted.
Context: One self-contained WORLD-tab Next Stop UI feature: four bilingual, deterministic non-persistent destination cards, one click-cycling button, existing i18n keys and no core game, save or renderer changes.
Context: Gemini's only code files are index.html and new tools/test/explore_picks_check.mjs; all AGENTS checks must be reported honestly; Claude must independently review and wire the new regression test into CI during its release PR.
Deliverable: review the complete attached T-007-spec-v1.md for scope, mobile layout, meaningful regression coverage, Stage 2 trial constraints and D-013 protection. After Martin explicitly approves T-007 v1, register the spec verbatim via Claude-only docs PR, set TASKS Ready for Implementer and unlock Gemini's one-PR Stage 2 trial; do not start work on this proposed document.
SPEC: full attached T-007-spec-v1.md (includes complete English Antigravity prompt and this handoff).
```
