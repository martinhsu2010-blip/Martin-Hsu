# T-008 spec v1 — 區域抵達提示 HUD（Zone Arrival HUD；Gemini Stage 2 第二項任務）

**狀態：PROPOSED／草案；待 Claude spec review 與 Martin 明確批准「T-008 v1」。未註冊、未授權開工。**  
**作者／設計 Owner：** ChatGPT。**實作 Owner／Implementer：** Gemini（Antigravity Remote Agents）。**Reviewer／Integrator／Releaser：** Claude。**Priority：** P2。  
**Base commit（設計基準與本文引用的 main）：** `af6209d912a773d930a5520d0823d4ff2dedeee4`（GitHub compare `af6209d...main` 為 identical；正式實作仍從開工當時最新 `main` 建分支）。  
**依據：** `COLLAB.md` v3.5 §§3、4.2、6、7.3、9；`AGENTS.md`；`TASKS.md` Gemini qualification；`DECISIONS.md` D-013／D-021／D-023／D-024；`specs/TEMPLATE.md`。  
**Required Gemini stage：** 2。**類別：general HUD behavior（一般遊玩 HUD 行為），與 T-007「Game Hub WORLD UI 卡片」不同。**  
**指定分支：** `gemini/T-008`；**PR base：** `main`；**單一完整任務、單一實作者、單一程式 PR。**  
**Verification（目前）：** `designed` only；沒有程式碼實作、CI／headless／實機驗收結果。本文及 D-024 對 T-007 的批准與驗收，**不構成 T-008 批准，更不構成 Stage 3 升階**。

> 規格原則：只允許本文明確列出的變更。任何範圍、動線、測試或 UI 要求如需更動禁區，必須停止並交 Claude／Martin 審查；不能「順手修理」核心程式。

## 1. Goal and non-goals／目標與不做的事

**玩家體驗：** 在遊戲正常駕駛或步行過程中，當玩家由目前區域跨入另一個由**既有 HUD 區域判定**識別的地區，左上雷達下方短暫出現一張小型霓虹玻璃提示：

- 英文：`NOW ENTERING` ＋ 既有英文地區名稱；繁體中文：`正在進入` ＋ 既有繁體中文地區名稱。
- 例如：從 Downtown CBD 進入 Ocean Drive，顯示 `NOW ENTERING / Ocean Drive`（英文）或 `正在進入 / 海濱大道`（繁中），**2,500 ms 後自動消失**。
- 玩家第一次載入遊戲時，不彈出；只有後續**真正變更地區識別 key** 才出現。玩家保持在同一地區時不反覆觸發。這只是被動的沉浸感回饋，**不是任務、限速資訊、成就或解鎖**。

**為何選 Gemini：** 單一局部 HUD 元件、一段以既有區域判定結果為輸入的小型 DOM 更新與定時器、兩語一個 i18n key，以及一個可重現的真實函式回歸測試；不動任何遊戲核心系統。這是 Stage 2 第二項**不同範疇**的完整任務候選：T-007 是 Game Hub／WORLD 卡片，T-008 是正常遊玩時的 general HUD behavior。

**明確不做：** 不改 `ROAD_NET`、`terrainHeight`、區域邊界座標、地名計算優先順序、世界地圖、HUD 雷達繪圖、攝影機、車輛速度與操控、物理碰撞、交通／警察 AI、任務、導航／傳送、獎勵、音效、特效粒子、WebGL canvas／renderer／draw calls、任何存檔或設定讀寫。無成就計數、無提示歷史、無持久化。

## 2. Fixed constraints／硬限制與啟動閘門

1. **批准及登錄閘門：** Claude 先審查此完整原文；Martin 必須另外明確批准「T-008 v1」，Claude 才能在**自己的 docs-only PR** 將本文件原文登錄至 `specs/T-008-spec-v1.md`，並更新 `TASKS.md` 的 `Ready for Implementer`、Owner／Implementer／Reviewer、Required Gemini stage 與設計基準。**本草案不得直接當成 Gemini 開工指令。**
2. **資格與共享鎖：** 開工時 `TASKS.md` 的 `Gemini qualification` 必須為 Stage 2（或更高）且無 paused／rollback；T-007 PR #59 應有 Claude「Stage 2 trial：通過」、正式發布與 Martin 實機接受的紀錄。Codex／Gemini 共用的一把 code-PR lock 必須空閒。若有另一個未合併 code PR，T-008 停止開工。
3. **檔案白名單（Gemini 程式 PR）：** 只准修改 `index.html` 的頂部 `STRINGS` 英／繁中表、左上 HUD 小元件、局部 scoped CSS，以及 `renderDrivingHUD()` 結尾的地區通知整合與緊鄰的小型 helper；另**新增** `tools/test/zone_arrival_check.mjs` 一支測試。不得改既有測試以放寬斷言。若檔案已於最新 `main` 有衝突，停止並回報，不私下擴大白名單。
4. **絕對禁止 Gemini 修改：** `sw.js`／CACHE、協作文件（`COLLAB.md`、`AGENTS.md`、`TASKS.md`、`DECISIONS.md`、`LOG.md`、`HANDOFF.md`、`specs/` 等）、`.github/`、`css/app.css`、`models/`、`textures/`、`libs/`、二進位素材與其餘路徑。新測試接入 workflow 由 Claude 發布流程另開 docs／release PR 處理。
5. **不變的核心：** `vh_save`／`vh_settings`／其他 localStorage／sessionStorage／IndexedDB／cookies **零新增讀寫，零新增欄位**；既有 PWA 離線、原本一個 renderer、三維場景、物理 body／shape、車輛處理、輸入按鈕與五個 Game Hub 分頁均不更動。禁止新 CDN／npm runtime dependency／HTTP 請求／新圖像與音效檔案。
6. **效能邊界：** 既有 `renderDrivingHUD()` 每畫面更新一次，本任務只能在其**既有地區判定結果**上做常數時間比較，無新 DOM 查詢迴圈、無陣列掃描或新物件每幀配置、無新遊戲 `requestAnimationFrame`／`setInterval`／常駐 polling、無新 Three.js／Cannon 物件。只在第一次初始化、地區更動、顯示中語言更動或到期時更新提示 DOM。新增 WebGL draw calls 與 physics bodies/shapes 都應是 **0**（靜態 diff 佐證；這不宣稱 DOM compositing 成本為零）。
7. **基準需複核：** 目前 `index.html` 的 `renderDrivingHUD()` 已用一連串 if／else 判定 `zone`，並把其文字顯示在 `#radar-zone`；不能重新定義或「修正」該條件。若正式開工前改版使錨點失效，Gemini 停止並請 Claude 重新確認本規格。

## 3. Detailed requirements／精確功能規格

### 3.1 原始碼定位與資料來源

在設計基準版 `index.html` 可直接找到：

- `renderDrivingHUD()`：約第 **9273** 行；結尾依 `getActivePosition()` 與現有區域條件設定 `zone`，最後更新 `document.getElementById('radar-zone').textContent`（約第 9299–9315 行）。此處為唯一區域資訊來源；**不准建立第二份新區域判定算法**。
- `#radar-zone`：遊戲左上雷達既有位置名稱；`#game-hud`、`#radar-container`、`#status-column` 仍保持原結構，不能更動原位置名稱顯示結果。
- `STRINGS.en`／`STRINGS["zh-TW"]` 與 `tr()`：既有翻譯系統，`changeLanguage()` 既有流程會刷新 HUD。
- 現有地名 key（依原本的分支順序）：`midtown`（預設）、`ring_expressway`、`mount_chiliad`、`suburbs`、`old_town`、`downtown_cbd`、`vice_circle`、`starlight_marina`、`santa_cruz_boardwalk`、`ocean_drive`、`stunt_airport`。這份清單只供通知功能識別，不准改地名、區域劃分或先後順序。

**狀態判斷必須用不受語言影響的 key（例如上述現有 key），不得以已翻譯的地名字串作為地區改變依據。** Gemini 可以在既有 if／else 分支中同步保留 `zoneKey`（或等效固定識別），但不准改動原條件、順序、速度／座標來源或 `#radar-zone` 更新語意。

### 3.2 版面與 UI

- **新增唯一元件：** `#zone-arrival`；建議放在 `#game-hud` 的左上雷達附近，定位在雷達**正下方**，不重排現有 HUD。包含 `#zone-arrival-caption`（提示前綴）與 `#zone-arrival-name`（地區名稱）兩個文字節點。唯一新的雙語 i18n key：`zone_arrival_label`。
- `STRINGS.en.zone_arrival_label = "NOW ENTERING"`；`STRINGS["zh-TW"].zone_arrival_label = "正在進入"`；其餘地名以既有 `tr(zoneKey)` 得出，不能複製第二套地名詞庫。
- **顯示：** 預設 `hidden`，區域變更後顯示兩行文字；上排標籤 10–11 CSS px，下排地名至少 12 CSS px，兩行互不覆蓋。建議使用現有 `hud-glass` 色系、半透明深藍背景、青色細框，邊角半徑 **12 px**、內距 **8–10 px**；不加漸變背景特效、燈光／粒子或動畫迴圈。
- **位置／限制：** 左側依既有 `--left-edge`，頂端依 `--top-edge` 加 `--radar-size` 再下移 **6–10 px**；寬度上限 **220 CSS px**，同時不得超出可見視窗右側及安全區。高度以文字自適應（一般兩行約 **36–50 CSS px**），長地名允許在本元件內換行但不得溢出；**不遮住**右側狀態卡、上方雷達、任務面板操作、搖桿或 Game Hub 開啟入口。`pointer-events: none`。
- **可存取性：** 對提示使用 `role="status"`、`aria-live="polite"`、`aria-atomic="true"` 或等效無障礙標示；避免每幀重寫文字造成讀屏反覆宣告。隱藏時不佔焦點，也不阻擋觸控。不得動既有選單焦點控制。
- **不得新增任何按鈕／互動入口。** 玩家完全透過日常移動觸發，與 T-007 的 Game Hub 點擊卡片互動不同。

### 3.3 觸發與計時的不可變規則

| 狀況 | 期望 |
|---|---|
| 初次載入後首次執行 `renderDrivingHUD()` | 只記錄目前 `zoneKey`，不彈出提示；`#radar-zone` 維持原顯示。 |
| 從 A 地區判定 key 轉為 B key（A ≠ B） | **同一回 HUD 更新** 顯示 `zone_arrival_label` ＋ B 的現有語系地名，並設 **2,500 ms** 到期隱藏。 |
| 當前地區未改變，連續更新 300 次 | 不重開／延長計時器、不反覆重寫 DOM 內容、不多產生計時器。 |
| B 提示尚未消失又跨入 C | 立即改成 C，取消 B 的到期回呼，只保留一個有效的隱藏計時器；**2,500 ms 自 C 開始**。 |
| 2,500 ms 到期且地區未再改變 | 提示隱藏，既有 `#radar-zone` 繼續顯示目前名稱。 |
| 提示顯示時玩家由 `en` 切到 `zh-TW`（反之亦然） | 同一個 `zoneKey`，**只更新前綴與地名**；不當成新的入區事件、不重新開始 2,500 ms 倒數；已隱藏提示不因此重現。 |
| 步行／駕車切換，或傳送到另一區域 | 按相同既有 `renderDrivingHUD()` 區域判定處理，無額外任務／導航／控制行為。 |
| 遊戲進入 Game Hub 或其他模態視窗 | 不改動原 Hub 結構與互動；提示無指標事件，不能吃掉原本的點擊。 |

補充硬限制：

- 不能呼叫 `showBanner()` 來借用任務／獎勵公告；避免蓋掉更重要的警車、任務與獎勵提示。T-008 必須是**獨立、非互動的 HUD 微提示**。
- 可使用**單一** `setTimeout` 完成 2,500 ms 隱藏並在跨區時 `clearTimeout` 既有 timer；不得使用無限輪詢／每幀新增 timeout。頁面結束後不要求保留提示；完全沒有 persistent storage。
- 地區更動判定的地理意義**沿用現況**；本任務不解決 zone mapping 本身的先後順序／空白區域／道路連通問題，那些屬於別的 Codex 系統任務。

### 3.4 兼容要求

1. `#radar-zone` 地名仍每次正常更新，已有 `renderDrivingHUD()` 的速度、齒比／RPM、油門與附近車輛邏輯逐字行為不變；新增提示不能改車輛物件狀態。
2. `en → zh-TW → en` 即時切換仍有效；既有 `STRINGS` key 不改值，新 key 在兩語中都存在，i18n lint 不得出現新增的 missing/untranslated 結果。
3. 預設 `PHONE_LOW`、`TABLET_MED`、`DESKTOP_HIGH` 都可顯示；低畫質不使用降級後消失的新特效，也不要求調整 renderer。
4. 即使地區頻繁切換，顯示也不應產生無限 timer、垃圾 DOM、WebGL draw calls、額外 Canvas、持久化資訊或 console error。

## 4. Single task and full acceptance criteria／任務及完整驗收

| ID | Name | Depends on | Acceptance |
|---|---|---|---|
| **T-008** | Zone Arrival HUD（general HUD behavior） | T-007 已經 Claude 審查、發布並由 Martin 接受；Gemini Stage 2；Martin 另行批准 T-008 v1；Claude 登錄本規格；共用程式 PR 鎖空閒 | **A1–A12 全部必須有對應證據** |

**A1 — 授權及 PR：** `TASKS.md` Gemini qualification 仍 Stage 2、T-007 在 Done、T-008 規格已獲 Martin **另外**批准並登錄；Gemini 從最新 `main` 建立 `gemini/T-008`，單一 code PR 對 `main`，PR 使用 repo 模板，不直推 `main`、不自行 merge，也不與另一個 code PR 同時存在。

**A2 — 檔案與 diff：** 只有 `index.html` ＋**新增** `tools/test/zone_arrival_check.mjs`；不變更 `sw.js`、workflow、docs、原有測試、素材等。修改聚焦 `STRINGS`、局部 HTML/CSS、HUD 小 helper 與 `renderDrivingHUD` 原有 zone 分支的**固定 key 註記**；必須在 PR 列出變更區塊，不重排無關程式。

**A3 — 精確內容：** DOM 有且僅有一個 `#zone-arrival`、`#zone-arrival-caption`、`#zone-arrival-name`，第一次載入隱藏；兩種語言都有唯一 `zone_arrival_label` key，英文 `NOW ENTERING`、繁中 `正在進入`；地名使用既有地區翻譯；不更動 `#radar-zone` 原文字。

**A4 — 區域轉換：** 開始於 Downtown CBD 不顯示；移往 Ocean Drive 顯示正確現有地名；再移至 Suburbs 能顯示另一正確地名；測試至少涵蓋**3 個可控制的地區識別**，且不引入新的地理偵測邏輯。

**A5 — 2,500 ms 與重複更新：** 顯示 2,499 ms 時仍可見、2,500 ms 到期時隱藏；同一地區連續 300 次 `renderDrivingHUD()` 不重開 timer／不重觸發；在顯示期間跨區，舊 timer 不得提前把新提示關閉，整個生命週期最多一個有效隱藏 timer。

**A6 — 雙語即時性：** 出現提示時切換 `en ↔ zh-TW`，前綴與地名都更新、沒有缺 key、倒數**不重設**；提示已隱藏時切語系不彈出。語系切換的既有存檔機制不因本任務新增任何讀寫。

**A7 — 既有 HUD／玩法零回歸：** `#radar-zone`、`#hud-speed`、`#hud-gear`、RPM、任務狀態、遊戲輸入與切換車輛不受影響；沒有新的 `showBanner` 呼叫、導航、任務或獎金；`vh_save`／`vh_settings` 無**本功能新增的**讀寫。保留 Game Hub 五個 tab 與 T-007 Next Stop。

**A8 — 真實程式回歸測試：** `node tools/test/zone_arrival_check.mjs` **PASS**，必須直接載入 `index.html` 裡的**真實生產版 `renderDrivingHUD()` 和同一新增 helper**（例如 Node `vm` 抽取該原始碼，搭配最小 DOM、定時器與 `STATE` stub），實際呼叫函式並讓 `getActivePosition()` 的座標跨區，驗證 A3–A7 的可執行結果。**只用 regex 找字串、複寫一份簡化函式、或只測模擬 helper 不算合格。** 必須包含明確可失敗的 `assert`：例如缺少 zone change 更新、2,500 ms 期滿不隱藏、跨區未取消舊 timer、切語系重開 timer 等都會 `exit != 0`。Claude **必須**獨立重跑並以至少 **2 種針對性故障注入／mutation** 確認測試真的會 FAIL，再還原程式；測試不得偷修改正式遊戲邏輯以方便通過。

**A9 — AGENTS 全套檢查與 CI：** Gemini 執行本規格 §5.1 列出的九個檢查命令及本任務新測試，紀錄實際 PASS/FAIL／未執行原因；所有既有 CI 檢查必須綠燈。`hud_check.mjs`、`camera_check.mjs`（需要 git history）不可被省略且仍宣稱全 PASS；失敗不得藉放寬舊測試解決。

**A10 — 版面與無障礙：** 至少 `390×844`（手機直向）、`844×390`（手機橫向）、`1280×800`（桌面）CSS viewport，在 `en`、`zh-TW` 觀察一次實際區域轉換；確認雷達下方提示可見、可讀、無畫面溢出或遮蔽可操作控制項；未檢視的尺寸不得寫成已驗證。`aria-live` 不每幀宣告，點擊可穿透，原本的 Game Hub 與任務面板仍能操作。截圖屬 headless／browser，不當作真機。

**A11 — Claude 獨立審查、分支保護及 CI 接入：** Claude 重跑新測試與 AGENTS 相關檢查，核對 diff／雙語／timer／未改 core；**每次 Gemini PR review 必須即時核查 `main` D-013 分支保護**，記錄時間／來源與 `required PR=true`、`enforce_admins=true`、`allow_force_pushes=false`、`allow_deletions=false`、repo rulesets 數量 **0**，任何不符或不可查證均為 hard violation、不得 merge。新測試先由 Gemini 的 PR 提交；Claude 必須在該 PR 合併／發版的**自己的** docs／release PR 將 `node tools/test/zone_arrival_check.mjs` 加入 `.github/workflows/pwa-cache-check.yml`，確認 workflow 確實執行且 PASS；Gemini 絕不改 `.github/`。Claude 完成 release、CACHE 更新和 PWA live／offline 驗收才交 Martin 實機測試。

**A12 — Martin 最終驗收與資格：** 在 Samsung S26 Ultra（PHONE_LOW）與 Samsung Tab S11（TABLET_MED）實際步行／駕車切換至少 **3 次**跨區（建議 Downtown → Ocean → Suburbs，實際可傳送到既有合法路段），觀察 2.5 秒退場、語言切換與既有 HUD、Game Hub；各用正常操作遊玩 **≥60 秒**，回報是否通過、裝置／畫質／地區／截圖及（若使用 `?fps=1`）平均 FPS。設備未回報的 FPS 一律標示 `not device-measured`。**T-008 若通過，僅能列為第二個不同範疇 Stage 2 證據；升至 Stage 3 仍須 Claude 審核條件、另外由 Martin 明確批准，並完成 §4.3 測試閘門，絕不自動升階。**

## 5. Verification plan／測試與證據規範

### 5.1 Gemini 必跑 AGENTS.md 檢查（9 項）＋任務檢查

從完整 git history、當時最新 `main` base 上執行以下原本 `AGENTS.md` 要求的檢查；**逐項記錄**執行指令、退出碼、代表性 PASS／FAIL 輸出或阻礙原因。不能把 GitHub CI、Claude 代跑或預期結果冒充 Gemini 自己的執行結果。

```bash
python3 tools/test/syntax_check.py
python3 tools/test/i18n_check.py
node tools/test/i18n_check.mjs
node tools/test/hud_check.mjs
node tools/test/camera_check.mjs af6209d912a773d930a5520d0823d4ff2dedeee4
node tools/test/traffic_check.mjs
node tools/test/collision_check.mjs
node tools/test/suburb_check.mjs
node tools/test/urban_check.mjs
# T-008 新增，必測：
node tools/test/zone_arrival_check.mjs
```

注意：`camera_check.mjs` 的參數應在正式開工時改為**實際最新 main base SHA**，並在 PR 寫出完整 SHA；`collision_check`、`camera_check` 需要完整 git history。CI 清單另外包括 `route_legality.mjs` 與 T-007 `explore_picks_check.mjs`，不可因本任務省略。若 headless browser 可用，還需由本機 static server 載入完整遊戲、記錄 console errors；沒有瀏覽器就明確標示**未測**，由 Claude 獨立補驗，不能冒充 PASS。

### 5.2 具實際失敗斷言的專項回歸測試

新檔固定名稱：`tools/test/zone_arrival_check.mjs`。標準 Node.js ESM、repo 既有 node/VM 能執行、不新增 npm 相依。測試應：

1. 讀取 repo 真正的 `index.html`，從明確界線**抽取生產用** HUD function 和本任務新增 helper，在 `vm` 裡執行。使用最小實作的 `document.getElementById`、`classList`、`textContent`、`getActivePosition`、`getActiveSpeed`、`tr()`、可控制的 `setTimeout`／`clearTimeout`、`STATE`、`ROAD_NET` 等 stub。若生產程式重構而測試不能找到區塊，**測試 FAIL**，不得退回測試中自建假函式取代。
2. 用位置驅動真實 `renderDrivingHUD()`：初始 `(x=-200,z=0,y=0)` 應為現有 Downtown CBD 判定，不能通知；移到 `(x=130,z=0,y=0)` 應是 Ocean Drive，通知顯示；移到郊區中心 `(x=-1060,z=-238,y=0)` 應顯示 Suburbs。測試設定 `ROAD_NET`／車輛 stub 以通過**原有**其餘邏輯，不得改 zone 條件。若相機／道路結構版本不同，Claude 重新確認這些測試輸入，不能偷調地理真值。
3. 使用可控假時鐘精確斷言到期時刻 **2499 ms 可見、2500 ms 隱藏**；同區 300 次更新不加 timer；B→C 快速切換時舊 timer 無法隱藏 C；切換 `tr` 語系後字樣更動而 timer 不重設、無額外入區事件。
4. 驗證原 `#radar-zone` 結果不變，原 HUD 速度、檔位與 player mode 沒被此 UI 機制覆寫；以 storage/API spies 確認新增 HUD 邏輯不呼叫保存、傳送、任務或場景建立動作。
5. 使用 `assert`／非零 exit code 明確失敗，成功輸出獨立的 `RESULT: PASS`；**Claude 故障注入**至少：移除 zone-change 更新一次、改錯 2500 ms 時間一次，兩次均須讓新測試以非零碼 FAIL，並清除故障注入後重跑 PASS。也可替換成對真實 bug 有同等辨識度的故障案例，但須列出每次注入方式與實際結果。

### 5.3 PR 必須如實交付的報告

Gemini PR 說明固定包含下列欄位（使用 repo PR template，其他欄位照填；**不得只寫「all tests pass」**）：

```text
Scope: T-008 Zone Arrival HUD; Required Gemini stage: 2; category: general HUD behavior (different from T-007 Game Hub UI)
Base main SHA: <full SHA>
Files changed: <precise list and why>
Changed code sections / extra work: <exactly what changed; no cleanup>
AGENTS checks I actually ran: <all commands, exit codes, PASS/FAIL evidence>
AGENTS checks I did NOT run: <commands and honest reasons; write 'none' only if truly none>
Task-specific test: node tools/test/zone_arrival_check.mjs -> <observed result>
Browser/headless checks I ran: <viewport, language, input scenario, screenshots, console errors>
Browser/device/offline/FPS checks NOT run: <explicit list; do not attribute Claude/Martin runs to Gemini>
CI results: <GitHub status separately from my local results>
Save/physics/renderer risk: <why scope was not touched; no invented benchmark numbers>
Remaining limitations/blockers: <known issues or none>
```

**Claude 的 review 報告**則另列獨立跑過的指令、測試資料、至少兩次 mutation FAIL 證據、真實網頁檢驗，以及 D-013 權限核對；分開標記 `code-reviewed`、`headless-measured` 與 `device-measured`。**未有 Martin 真機回報，不得聲稱 device-measured 或 30 FPS 實測。**

## 6. Risks and open questions／風險及待 Claude 審查問題

1. **既有 zone 條件可能有地理優先順序問題。** 本任務必須照原本 if／else 判定與結果；若某個地區被別的條件遮蔽，另開 Codex 設計／bug 任務，不能藉 T-008 改 `ROAD_NET` 或地圖邊界。
2. **既有 `renderDrivingHUD()` 會每影格執行。** 因此不能增加每幀 timer 或重建 DOM；前綴與名稱只有在 zone 改變或當前顯示中的語言改變才重寫。Claude 要在 source diff 確認只有 O(1) 比較，並測試 300 次不重複觸發。
3. **HUD 空間在手機橫向較窄。** 要在實際 UI 用 390×844、844×390、1280×800 檢驗；若位置遮擋既有互動面板，先在本次允許的 scoped CSS 內修正；若必須重排核心 HUD、增設新分頁或改動 Game Hub 結構，停止並請 Martin 另批規格。
4. **Stage 3 尚未獲授權。** T-008 即使是第二個不同範疇的合格任務，也只滿足升階評估所需「連續兩個不同範疇已完成 Stage 2 task」的一項必要條件。Martin 之後須另行明確批准 Gemini 升階，Claude 也必須先確認 §4.3 的回歸測試與獨立物理／draw-call 量測閘門，不能自動放行。
5. **目前尚未執行任何程式、測試或裝置實驗。** 本文件所有時間、尺寸與行為是**提案驗收值**，不得表述為已測得的品質數據。若 Claude 指出與現有測試或 HUD 衝突，先提出 spec v2 給 Martin 批准，不擅自改已批准規格。

---

## Antigravity prompt (English; COLLAB v3.5 §7.3 Stage 2; USE ONLY AFTER APPROVAL AND REGISTRATION)

```text
Implement the single approved task T-008 according to TASKS.md, its complete registered spec at specs/T-008-spec-v1.md, COLLAB.md v3.5 and AGENTS.md. Confirm that the repository records Gemini Stage 2 authorization and that T-007 has been released and accepted. This is the second Stage 2 task in a different category: general in-game HUD behavior, not a Game Hub UI card.

Use the latest main as your implementation base (design baseline: af6209d912a773d930a5520d0823d4ff2dedeee4). Create branch gemini/T-008 and open one PR against main only when the shared code-PR lock is free. Own this entire task yourself. Never push to main, merge your own PR, or start work before Martin's explicit T-008 v1 approval and Claude's spec registration.

Add exactly one small, non-interactive Zone Arrival HUD notification beneath the existing radar. It should show the localized 'NOW ENTERING' / '正在進入' prefix and the existing district name when the production renderDrivingHUD() zone-key result changes. Do not show it on the first HUD update; show it for 2500 ms on each later real district change, avoid retriggering in the same zone, cancel stale timers on rapid changes, and update the visible wording on language switches without restarting the timer. Keep existing zone boundaries, zone priority and #radar-zone behavior completely unchanged. Use a stable, language-independent zone key for change detection. The feature must do nothing to navigation, missions, rewards, saves, vehicles, physics or rendering. Do not use showBanner() or any polling/render loop.

Your code PR may edit only index.html and may add only tools/test/zone_arrival_check.mjs. The new regression test MUST load and execute the real production renderDrivingHUD() function and its actual new helper using a small controlled DOM/clock/state harness. Assert initial suppression, real coordinate-driven zone transitions, exactly 2500 ms visibility, no repeated timer for 300 unchanged frames, safe rapid transition, locale changes without timer reset, and unchanged radar speed/gear labels. Never replace production logic in the test with a fake clone. Do not weaken old tests.

Do not edit cannon-es physics, collisions, vehicle controls, world/terrain/road generation, traffic/police AI, renderer/draw-call/performance code, vh_save or settings persistence, sw.js, docs/specs, .github/, css/app.css, assets, or unrelated code. Do not reformat files or add new runtime dependencies. Run ALL nine required AGENTS checks plus node tools/test/zone_arrival_check.mjs. Report actual commands, observed PASS/FAIL outputs, skipped checks with reasons, browser scenarios and what was NOT tested, separately from CI and real-device results. Use a local static server for headless checks if available; do not claim real-device FPS without real-device measurements.

Claude independently reviews this PR, re-checks main branch protection under D-013, reruns the tests and verifies that mutations are caught. Only Claude wires the new test into .github/workflows/pwa-cache-check.yml during the release docs PR and updates sw.js CACHE. If anything needs an unauthorized system change, stop and report the blocker instead of expanding scope. Completing this task does NOT automatically promote Gemini to Stage 3; only Martin can explicitly approve such a promotion after all COLLAB v3.5 gates are satisfied.
```

## HANDOFF ChatGPT -> Claude

```text
HANDOFF ChatGPT -> Claude
Task: T-008 spec v1 (PROPOSED / NOT Martin-approved; Gemini Stage 2 second distinct-category task)   Base commit: af6209d912a773d930a5520d0823d4ff2dedeee4   Read: COLLAB.md v3.5 §§3/4.2/7.3/9, AGENTS.md, TASKS.md Gemini qualification and T-007 Done, DECISIONS D-013/D-021/D-023/D-024, specs/TEMPLATE.md
Context: T-007 Game Hub WORLD card (PR #59, D-024) is released and Martin-accepted; Gemini remains Stage 2. T-008 is a different category: general in-game HUD behavior, a passive 2.5-second localized district-entry prompt using the EXISTING renderDrivingHUD zone logic.
Context: One Gemini code PR only; files index.html and new tools/test/zone_arrival_check.mjs. No changes to save/schema/settings, physics, collisions, vehicle control, world/roads, AI, renderer/draw calls or game logic outside this HUD.
Context: Regression test must run the REAL production renderDrivingHUD() through a controlled harness and have failing assertions; Claude independently re-runs it and verifies at least two targeted mutations fail; Gemini honestly lists AGENTS checks run/not run. Claude independently checks D-013 protection and wires new test into CI in its release PR.
Deliverable: Review complete attached T-008-spec-v1.md for safety, HUD layout, real-code test feasibility, T-007 category distinction, and Stage 2 two-task gate. Do not register or start implementation until Martin explicitly approves T-008 v1. After approval register verbatim via docs-only PR, update TASKS Ready for Implementer, verify shared code-PR lock, then allow Gemini. Stage 3 still requires a separate explicit Martin approval and the COLLAB §4.3 test gate.
SPEC: attached full T-008-spec-v1.md (including exact acceptance criteria, English Antigravity prompt and this HANDOFF).
```
