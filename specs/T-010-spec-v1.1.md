# T-010 spec v1.1 DRAFT — Midtown C+ 低品質 coverage 建築立面試點

> **狀態：PROPOSED / NOT MARTIN-APPROVED。** 這是 ChatGPT 的設計草案，不是已登錄任務、執行許可或完成的效能測試。
>
> **Design baseline / latest main checked:** `f57d890d090ec43196daf962c5f63e4ec5e9faa3`（2026-11-22）。實作分支必須從開工時最新 `main` 建立並重新記錄 SHA。
>
> **Source of truth:** root `COLLAB.md` v3.6（D-027，§3、§4.3、§5.1–5.2）、`TASKS.md`、`DECISIONS.md`（D-013／D-026／D-030）、`AGENTS.md`、`specs/TEMPLATE.md`。
>
> **Owner / Implementer:** Codex（提案）；**Reviewer / releaser:** Claude；**Final approver / device acceptance:** Martin。
>
> **Risk:** HIGH（修改世界可見幾何與 renderer draw calls，依 v3.6 §5.1「觸及高風險系統即 high」）。**Volume:** SMALL（單一街區、單一系統）。**Routing rationale:** 第一個建築立面需要幾何比例、貼合與遮擋判斷，按 v3.6 預設由 Codex 做；將來經驗證的機械式批量覆蓋可另立 Gemini Stage 3 任務，且每個高風險子任務仍須 §4.3 完整閘門。
>
> **Priority:** P1（C+ 首個玩家可見的建築質感示範）。**Branch:** `codex/T-010-midtown-facade-pilot`；PR 只對 `main`，不和任何其他 code PR 同時進行。

## 1. Goal and non-goals

### 1.1 玩家可見成果

讓 Midtown 某一個現存街區的**後期新增低品質 `coverage` 建築**，在玩家開車靠近時有更完整、寫實比例的外立面：既有玻璃窗外增加窗框與窗台、頂部有清楚的收邊線條，保持原本城市風格和色彩。不變動建築位置或尺寸，不取代原本品質較好的模組化建築。

### 1.2 本任務不做

不做全面重製、外部 Higgsfield 貼圖、美術二進位素材、道路加寬／縮窄、建築碰撞修改、交通／警察 AI、車輛／相機手感、物理參數、時間／天氣、遠景天際線、`vh_save` schema、PWA 架構、任何 UI 或新商店互動。第一階段以**低成本可重用的幾何立面模組**驗證方向；大規模材質與城市重建屬後續獨立 T-011+ 任務。

## 2. Current source diagnosis and fixed constraints

1. 在基準 `index.html`，`buildKitFacades()` 從 `WORLD.roofs` 取 `!r.coverage` 的建築，並使用現有門窗／檐口模組及室內映射。低品質 coverage 由 `buildCityInfill()`／`buildCoverageFacades()` 建置，後者主要是簡化門面與條狀裝飾。**這是程式碼結構事實；哪些個別建築最不好看仍須截圖驗證，不能只憑此宣稱實際畫面結果。**
2. 選定區域為 MID 街區：**`-420 < x < -240`、`-360 < z < -240`**（以建築中心判定）；它位於 `ROAD_NET.avenuesX` 的 -420 與 -240、`crossZ` 的 -360 與 -240 之間；`cityDistrict(-330,-300) === 'MID'`。**只能使用運行中實際存在的 coverage parcels，不可直接把 `CITY_COVERAGE_LOTS` 編譯候選清單視為已放置建築**，因建置時仍有道路、樹、建築遮擋 veto。
3. 試點只涵蓋**最多 6 棟**符合條件的 coverage 建築；由 `WORLD.cityInfill` 中 `coverage===true && district==='MID'` 的已放置建築決定。以**朝大道 -240 的東向立面**優先，從實際候選依 `abs(b.x+240)`、再 `abs(b.z+300)`、再 `(x,z,w,d)` 固定順序選前 6 個。禁止把 selection 隨機化；不要重排或改動原本 parcel list 的順序。如果在任何要求的 profile 中可見候選不足 6，**先停止並由 Claude 檢查實際場景；須修訂規格、重新批准才能改範圍或數字**。這是待 Claude 審查的前置風險，不可冒稱已確認有 6 棟。**測試必須讀取遊戲運行中實際生成的 `WORLD.cityInfill`，不得寫死建築名單。**
4. 應在 `PHONE_LOW`、`TABLET_MED`、`DESKTOP_HIGH` 上保留一致的選擇規則；不同 profile 的實際 parcel 配置可能不同，每個 profile 分別列出選到的 6 棟 `(x,z,w,d,h)`、`styleHash` 與其朝道路的方向，不要求三種 profile 的 world list 相同。**測試必須從各 profile 運行中實際生成的 `WORLD.cityInfill` 讀取名單，不得寫死跨 profile 候選清單。**
5. 規格初版不導入任何新 GLB、貼圖、外部 CDN、音效或字型；離線 PWA、現有光照、夜間窗戶與 existing assets 皆保持。所有需要新 `tools/test/` 的檔案只准由實作者新增／修改，CI workflow 接線、docs、`sw.js` 由 Claude 處理。

## 3. Visual design / exact implementation boundary

1. 每棟選中建築只在**東向立面**增加 3 類非碰撞裝飾：**窗框、窗台、屋頂收邊**。既有 coverage 玻璃窗與 `windowData`、night windows 的生成和 LOD 保持不變。coverage 東向玻璃窗的實際中心為 `x = b.x + b.w/2 + 0.06`、`y = 6.2 + floor*4.6`、`z = b.z`；玻璃原始大小為 **2.2 × 2.4 m**，其中寬度縮放比例是 **`b.w/5`**（有效寬度 `2.2*(b.w/5)` m）。**窗框與窗台必須位於既有玻璃外側、沿東向法線至少外移 `0.07 m`，不得與玻璃共面**；不可改動舊玻璃的位置。每棟最多兩列窗：`floor = 0 .. min(1, floor((b.h-6)/4.6)-1)`，低層樓不得產生超出 roof 的窗框。
2. 窗框外徑隨現有玻璃寬縮放：窗面有效寬 `2.2*(b.w/5)` m、高 `2.4` m；四邊框厚度建議 **0.12 m**，窗台向外突起不超過 **0.18 m**，窗口裝飾位於原牆外至多 **0.25 m**；框不得覆蓋玻璃中央或在光照變化時閃爍。若基準玻璃與框的表面高度／方向需調整，**只能調新增裝飾，不得改動舊玻璃或碰撞體**。
3. 頂部沿東立面加一條水平屋簷收邊：y 高 `b.h - 0.22 m`，長度 `b.d`、垂直厚度 `0.22 m`，向外深度 `≤0.20 m`；不可伸入道路、相鄰建築、現有大樓的透明窗或遠高出屋頂。
4. 新增幾何最多 **2 個批次 `THREE.InstancedMesh`、2 個共享材質**，總共最多 **+2 draw-submitting meshes**；`castShadow=false`、不發光、不透明、`roughness ≥0.8`、`metalness=0`。**新增的兩個 `InstancedMesh` 必須加入 `FACADE.chunks`，使用既有以 230 m 為基準的近距顯示邏輯（依 `FACADE.nearDist` 的現行 profile 設定，低階裝置不另行強制覆寫距離）**；不得新增獨立 LOD 管理器。不新增外部貼圖。新幾何、材質和矩陣只在世界初始化建立，無每幀 allocations、不新增 `rAF` callbacks、listener、observer 或獨立 LOD 更新 loop。
5. 既有 buildings/roofs/placements、`WORLD.cityInfillStats`、`CITY_COVERAGE_LOTS`、`ROAD_NET`、`TREES`、所有 physics bodies/shapes、道路和 `WORLD.vehicles` 完全不變。新增裝飾為**純視覺**，不加 hitbox。材質選色從現有 `b.tint` 或固定中性色推導，三種畫質都可辨識但不過亮。
6. 輸出一個可供 Claude 查核的 debug handle（例如 `WORLD.midtownFacadePilot`，具 readonly-ish 選擇名單／可見 mesh references）；**不得新增持久化儲存欄位**。選擇結果必須固定並可由實際網格矩陣驗證，不能在測試中自行重新實作一套假選擇邏輯。

## 4. Deliverable boundary / phases

**只有一項程式任務、一位實作者、一個 PR。** 開始前先完成審查預檢（無程式 PR）：

- **Gate G0 — Claude 設計審查與現場確認：** 確認指定區域在各 profile 皆有至少 6 棟可從大道看見的 coverage 建築；擷取基準日／夜視角，檢查是否受 Vice Broadway、互相遮擋、地形或路口重疊影響；若不足或不適合，回報並要求 v1.1，而不是讓 Codex 自行換座標。
- **Gate G1 — Martin 批准 v1：** Claude 完成 review 後，Martin 明確批准同一完整版本；Claude 的 docs-only PR 登錄完整規格與 `TASKS`、`DECISIONS`，並提供新的 `main` SHA。
- **Gate G2 — Stage 3 開工前測試確認：** 確認 PR 鎖空閒、baseline 可得、全套 AGENTS + `route_legality` 能跑；物理和 draw-call baseline/PR 成對程序能由 Claude 重播；缺任一條件，不可開程式 PR。
- **Implement — Codex:** 只修改 `index.html` + 新增 `tools/test/midtown_facade_pilot_check.mjs`；不得修改 docs、`sw.js`、`.github`、二進位素材、原測試／baseline。Production 建議 `≤200` 行，測試建議 `≤250` 行；超出須 Claude 先審查拆分。
- **Review/Release/Accept — Claude / Martin:** Claude 獨立功能、效能和 D-013 檢查；完整測試接入 CI、發布與離線驗證；Martin 實機日／夜查看並記錄 FPS。

**後續獨立任務（僅 roadmap，不在 T-010 核准範圍）**：T-011 可把已驗收模組按資料表擴展到其他 MID 街區（重複、可測試的 bulk 工作優先 Gemini Stage 3）；T-012 可拓展至其他城區；T-013 才研究素材授權、材質 atlas、Higgsfield 貼圖候選和光影（renderer 改動須另立高風險規格）。絕不為了完成 T-010 提前做這些工作。

## 5. Regression tests — each risk must fail on mutation

新測試 `node tools/test/midtown_facade_pilot_check.mjs` 必須針對**實際 production builder 和生成的 InstancedMesh**，用 repo 既有 harness / VM + Three.js，不能只 grep 字串或複製 fake builder。

| Risk | Failure-capable assertions | Suggested mutation (temporary, not committed) |
|---|---|---|
| R1 選址與對象 | 實際已放置 coverage / MID parcel 中挑選、在指定 bbox 且每 profile 恰好 6 棟；相同 seed、profile 再跑名單完全相同，未選中物件不加裝飾 | 把 bbox 改大或把候選排序換成亂數 → FAIL |
| R2 立面位置／尺寸 | 從實際 instanceMatrix 還原窗框、窗台、收邊，對照每棟原本 east-facing 窗座標；框不得超過屋頂、遮住窗面或超出 0.25m | 把 window y 增加 4.6m，或反向到西牆 → FAIL |
| R3 批次與成本 | 最多 2 個 InstancedMesh、2 個材質，`castShadow=false`；初始化後傳送／切換語言不產生重複網格；無每幀更新 | 改成 32 個普通 Mesh 或啟用 castShadow → FAIL |
| R4 物理／路網相容 | Builder 前後 body count、sum(shapes)、原有 body shapes 摘要、路線點、road net、building transforms、save schema 全相同 | 加任何新 CANNON.Box、移動一個 building 或 route point → FAIL |
| R5 真瀏覽器可見性（**Claude 獨立執行；不要求納入 Node 測試**） | Claude 使用真實 Chromium 瀏覽器、固定鏡頭確認至少一棟新建築的窗框與屋簷可見；日／夜均無閃爍／玻璃被蓋住，且無 console error／網路資產遺失 | Claude 檢查 mesh 放入原牆內或未 `scene.add` 等故障時是否不可見 → FAIL；此項由 Claude 瀏覽器驗證，不要求 Node 自動測試 |

需驗證測試對 baseline（尚未有新功能）為 FAIL（缺乏 production pilot），且 baseline 的舊測試皆 PASS。Claude review 時至少實施 2 種不同 mutation，確認新測試真能抓到錯誤。不更動現有 `route_legality.mjs`、`urban_check.mjs`、`collision_check.mjs` 的 baseline/assertions。

## 6. Independent benchmark — COLLAB §4.3

**測量責任歸 Claude；Codex 只需提交功能、測試與 AGENTS 結果，Claude 獨立測量，無量測即不得 merge。**

### 6.1 Fixed inputs and scenes

- Presets：`PHONE_LOW`（建議 390×844）、`TABLET_MED`（**800×1280，Android 平板 UA，`profile=TABLET`、`quality=MED`，與 T-009 一致**）、`DESKTOP_HIGH`（1280×800）；若以 UA / synthetic GPU 模擬 profile，記錄方法，不能冒稱 device-measured。
- 固定 seed `5019`、同樣 localStorage、同樣時間／日照、無控制輸入、相同鏡頭模式／相機位置。**目標近景相機固定位置 `(-232,5,-292)`，看向 `(-268,7,-310)`；baseline 與 PR 必須使用完全相同的相機位置、朝向及鏡頭狀態**。**控制遠景**維持 `teleportTo(110,650,0)`；Claude 必須先確認近景真正能看到選定建築及日／夜可比較、遠景看不到新增物件；若無法建立公平可見基準則修訂本規格，不得默默換場景。
- 三組 preset × 兩種場景各自比較，日／夜至少各一組截圖；每組 baseline 與 PR 必須使用相同相機和 renderer state。測試實際 browser / Three.js，不以靜態物件數推算 draw calls。

### 6.2 Physics — unchanged world, measured anyway

1. **Primary hard gate:** `physicsWorld.bodies.length` 及 `sum(body.shapes.length)`，對於 baseline/PR、各 preset/scene 必須 **delta = 0**；現有 body shape 型別、位置與內容摘要、交通路線摘要須相同。任意非零或物理/路網改動直接 FAIL，不得靠計時結果豁免。
2. Claude 對各 preset × scene 建立**乾淨獨立 context**。首次從 baseline SHA 建立 baseline/baseline calibration **5 成對**（A/B 交替），各 sample 在載入與 teleport 後，於頁內同步 `__VH.physicsWorld.step(1/60,1/60,3)`：先 warmup **≥900** 步，再以 `performance.now()` 計算連續 **360 步總時間**。顯示 5 組雙時間、ratio 分布及中位數；有效性區間 `0.75 ≤ calibration median ≤ 1.33`，區間外為 **MEASUREMENT BLOCKER**，不得發放 PASS。
3. 正式 baseline/PR 成對 **5 組**，A/B 執行順序交替，固定 `ratio=PR_ms/base_ms`；逐組報告 360 步時間和比率，中位數必須 **≤1.25**。如初始 >1.25，新增 4 組保留原樣本，合計 **9 組**後以中位數對同一 1.25 上限判定。9 組仍超標 → FAIL / no merge。不得把 T-005B 的 1.35 套為本任務門檻。同步測量不依賴 rAF render loop；不可把整幀 FPS 冒充物理 step 時間。

### 6.3 Draw calls and scene cost

1. Claude 於真實 Chromium 頁面讀取 `__VH.renderer.info.render.calls`；每個 preset × scene 對 baseline 和 PR 各取 **≥60 個完成渲染的 frame**，使用**每版中位數**算 draw-call delta，明列各版絕對數據和攝影機/quality/後處理狀態。
2. **目標近景 draw-call 上限：** PHONE_LOW **+2**、TABLET_MED **+3**、DESKTOP_HIGH **+4**。**控制遠景上限 +0**（若遠景可見此試點物件，需於規格審查時改成真正不受影響的控制場景）。
3. 新增 Cannon body / shape **+0**；在固定種子下 `WORLD.cityInfill` 數量、建築位置、交通數量、現有材質來源須保持 baseline；沒有額外 CDN、貼圖或 GLB。
4. 任何 preset / scene 超過 draw-call hard cap、無法取得真實 renderer 計數或同畫面不具可比性 → **FAIL / MEASUREMENT BLOCKER，不得 merge**。不得藉修改 baseline、測試、畫質設定、相機角度或降低陰影以達成 PASS。

### 6.4 AGENTS and device acceptance

- 運行所有 `AGENTS.md` 指令：`syntax_check.py`、兩種 i18n、`hud_check.mjs`、`camera_check.mjs <base SHA>`、`traffic_check.mjs`、`collision_check.mjs`、`suburb_check.mjs`、`urban_check.mjs`；加跑 `route_legality.mjs` 和本任務新測試。每項列實際 PASS/FAIL/未執行原因。
- Claude 獨立重新執行並核對 D-013 分支保護（包括 PR required、enforce_admins、force push/deletion 禁止、rulesets 與時間），將新測試在 Claude-owned docs/release PR 接入 `.github/workflows/pwa-cache-check.yml` 並確認 CI 實際執行 PASS，發版後檢查離線 PWA。
- Martin 使用 S26 Ultra（手機）及 Tab S11（平板）前往指定區域，白天、夜晚各檢視一次；確認至少 6 棟試點候選能看出窗框與屋頂收邊、沒有框壓住玻璃／飄浮、車輛碰撞手感不變。以 `?fps=1` 在相同路線量測每裝置 **60 秒平均 FPS ≥30**（預設畫質及同樣畫質設定），報出裝置、quality、平均 FPS 與最近 60 秒最低 1 秒讀數。未回報 FPS 必須標為「未量測」，不得冒稱通過。

## 7. Decision and stop rules

- **任何未達測試／效能上限、沒有 baseline、測試只做 smoke 而抓不住錯、程式 PR 非 allowlist、未批准更換範圍、CI/離線失敗、D-013 不符 → 不准 merge。** Claude 依 COLLAB 最多兩輪 changes requested，未能過關交 Martin 決定。
- 若 `G0` 現場候選不足 6、鏡頭看不到立面、面板需要更動原有玻璃 shader / 車道 / collider，或效能預算實際不可能達到，先改出 **T-010 spec v1.1** 讓 Martin 明確批准，不能私下放寬。
- 保留「一個 active code PR、一項 task 一位 implementer」；任何新增工作須重新走流程。文檔、CI wiring、cache 只准 Claude 在自己的 PR 修改。

## 8. Future roadmap (NOT approved by this spec)

| 順序 | 候選任務 | 建議實作者 | 重點 |
|---|---|---|---|
| T-010 | 單一 MID 街區 coverage 建築立面試點 | Codex | 第一個高風險幾何判斷；形成可重用幾何標準 |
| T-011 | 已驗收幾何套用到其他 MID 街區（每階段不超過 v3.6 建議 PR 尺寸） | Gemini Stage 3 | 大量可重複資料/模組工作；物理/draw gate 仍強制 |
| T-012 | OLD / CBD / 海濱逐區品質一致化 | Codex 判斷、Gemini 分批執行 | 依城區分段，不混同一 code PR |
| T-013 | Texture atlas、Higgsfield 材質導入與日夜光影 | 待單獨評估 | 新素材與 renderer 成本須另行批准、授權和測試 |

## HANDOFF ChatGPT -> Claude

```text
HANDOFF ChatGPT -> Claude
Task: T-010-spec-v1-DRAFT (PROPOSED / NOT Martin-approved)
Base commit: f57d890d090ec43196daf962c5f63e4ec5e9faa3
Read: COLLAB.md v3.6 §3/§4.3/§5.1–5.2; AGENTS.md; TASKS.md;
      DECISIONS D-013/D-026/D-027/D-030; specs/TEMPLATE.md
Context: T-009 PR #71 was released and Martin-accepted; FPS remains unmeasured.
Context: T-010 proposes a six-building MID district coverage facade pilot in
         the block bounded by avenues -420/-240 and cross streets -360/-240.
Context: Routing HIGH risk + SMALL volume => Codex by default under v3.6;
         mechanical mass-rollout (T-011+) can be separately routed to Gemini.
Deliverable: Check G0 real-world parcel selection for PHONE_LOW/TABLET_MED/
             DESKTOP_HIGH and sightlines; review exact geometry, regression
             assertions, browser measurement reproducibility and performance
             caps. Request corrections if G0 fails. Do not register/start any
             T-010 code PR before Martin explicitly approves complete spec v1.
SPEC: Attached T-010-spec-v1-DRAFT.md (complete proposal)
```
