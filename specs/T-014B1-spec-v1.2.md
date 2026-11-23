<!-- v1.1 CHANGE VERSION: Claude G0 correction -->
# T-014B1 spec v1.2 — Site A Procedural Massing + Street Pilot（GEMINI STAGE 3 REASSIGNMENT PROPOSAL / DRAFT）
<!-- END v1.1 CHANGE VERSION -->

> **REGISTRATION NOTE (Claude, 2026-11-23):** Approved by Martin ("批准", 2026-11-23 09:09) as T-014B1 v1.2; Gemini reassignment requested by Martin (Codex usage nearly exhausted). Registered verbatim from ChatGPT's v1.2 DRAFT except 3 editorial fixes that change no requirement: (1) title/status/approval phrase v1.1 -> v1.2; (2) §4 residual chip-name sentence limited to `wm-sel-sub` so §4 names stay authoritative. Where the DRAFT/NOT-APPROVED wording below conflicts, this note and D-043 prevail. **Gemini must not start until Claude records the §5A pre-start gates as PASS.**

> **Status: GEMINI REASSIGNMENT PROPOSAL / DRAFT / NOT MARTIN-APPROVED / DO NOT REGISTER OR IMPLEMENT.** 這是從 T-014 v2.2 + Claude 回報的 G0 結果拆出的**獨立單一程式 PR 候選規格**，並非 T-014B0/B2/B3 的同時批准。必須經 Claude 獨立審查、Martin 明確「<!-- v1.1 CHANGE VERSION-APPROVAL: Claude G0 correction -->
批准 T-014B1 v1.2
<!-- END v1.1 CHANGE VERSION-APPROVAL -->」、Claude docs-only 註冊後才能派工。**沒有 ART PASS；沒有發布許可。**
>
> **Baseline（查核時）：** `main` = `ff0ced15ec85f80905b4ef5c0b696afbf0f93194`（D-042）。**開工前重取最新 main SHA、確認唯一 code-PR 鎖及 GitHub 檔案現況**；若有與地圖／初始化／傳送衝突的變更，須退回 Claude re-review。
>
> **Source of truth:** repo root `COLLAB.md` v3.6 §§3,4.3,5.1,5.2,7.1；`AGENTS.md`；`TASKS.md`；`DECISIONS.md` D-013/D-021/D-026/D-039–D-042；`HANDOFF.md`；`index.html`；本對話 Claude 提交的 T-014 v2.2 G0 五點結論、`T-014-spec-v2.2-DRAFT.md`（設計背景）。本 B1 對**自身階段**的範圍優先於 v2.2 其他階段提案；未經批准不得自行加入後續階段。

## 0. G0 證據、前提與決策

**Claude G0 已回報（依本對話提供的結果，不冒稱 ChatGPT 獨立量測）：**

1. 真 **R8 單通道夜窗遮罩**，含 mip、自訂 shader 取 `.r`，實測可行；**屬 B2 的技術可行性證據，B1 不實作 R8**。
2. **Site A：中心 (x,z)=(-501,-790)**，100 m 街道沿 x 軸，位於 `x=-600` 與 `x=-420` 兩大道之間；G0 回報該地無既有建築、道路、碰撞及任務點。**本規格以下新增的建築包絡尺寸，尚須 Claude 在相同現行 main 上做 footprint 級二次交叉檢查**；Site A 通過不自動證明任意新外形都安全。
3. G0 原型：**建築 A 約 308 triangles、B 約 744 triangles；兩棟共 +4 draw calls，街道 +2 draw calls**（原型數字，非本版重新驗證）。
4. 展示入口縮至**一筆快速傳送地點 + 一個按鈕**；**不做返回按鈕**，**不新增車內或任務停用條件**；現有玩家／車／任務的傳送後續行為，須按照 §4 明確驗證與揭露。
5. FPS 提案：**≥30 平均 FPS**底線；同一裝置、同一座標、同條件展示 ON/OFF **各三組中位數，下降 ≤10%**；控制組 OFF/OFF 雜訊 **≤5%**。**相對門檻與校準仍待 Martin 實機確認**，不能寫成已通過或擅自放寬。

**任務分類：** `Risk: HIGH`（世界幾何／renderer／傳送）；`Volume: SMALL`（限定 2 棟 + 100m 視覺街道 + 一個現有地圖 UI 入口；預期 `index.html` 新增＋修改不超過約 600 行）。<!-- REASSIGN CHANGE R1: Implementer and routing justification -->
**Implementer: Gemini（Antigravity Remote Agents，Stage 3；改派提案，尚未批准）**。**選擇理由／偏離預設路由：**本任務仍是 HIGH/SMALL，依 COLLAB v3.6 §5.1 原則預設 Codex；Martin 現要求評估由已取得 Stage 3 資格的 Gemini 整項承接，以運用第二實作者並以明確 footprint、幾何硬上限、可重播測試與 Claude 獨立量測控制風險。這是逐案例外，不代表 Gemini 優先於 Codex，也不降低 §4.3 任一閘門。**Reviewer/Releaser: Claude**；**Device/Art judge: Martin**。Claude 須先確認 §5A 的全部前置條件；不成立則退回 Codex／測試設施規劃及 Martin 裁決，不可啟動 Gemini PR。
<!-- END REASSIGN CHANGE R1 -->

## 1. B1 僅有的成果與明確排除事項

### 1.1 必須產出

- 在已通過 G0 的 **Site A** 建造一段**僅視覺**的 100m 直線展示街道，含 asphalt 與兩側簡化 sidewalk/curb，同一單位為現有遊戲世界座標（公尺）。
- **Building A**：不對稱 L 型、可辨退縮、女兒牆及簡化屋頂設備；**Building B**：非 L、弧角（至少 8、最多 12 段）、高度不同的屋頂及設備。A/B 外牆四側及屋頂均需有封閉可見的量體；用**目前已具備的基本材質型別**（純色、無 map）。
- **一筆 Site A `FAST_TRAVEL` 項目**，並讓它於現有 Game Hub 世界地圖生成**一個可點擊的地點 chip 按鈕**；使用既有地圖的 `wm-travel` 確認按鈕完成傳送。**不另外新增 WORLD 面板按鈕、返回鈕或 3D portal**（因此「一個按鈕」特指此次新增的 chip；`wm-travel` 為原本已存在的確認按鈕）。<!-- CHANGE 4 START: §1.1 chip text authority -->
以 §4 的正式名稱為唯一權威：EN `Showcase Site A (No Collision)`、ZH-TW `展示區 A（無碰撞）`，供 world-map chip 與 `VH_I18N.name` Banner 完整顯示；「可能穿牆」只放在現有 `wm-sel-sub` 說明，不作 chip 名稱或 Banner 文字。
<!-- CHANGE 4 END -->
- 供測試使用的**非玩家介面 ON/OFF** 展示群組控制，能在**同一鏡頭下**真正隱藏新增兩棟和街面而不影響其他場景，以供 calls/FPS 配對量測；不能加入常駐新的 UI toggle。

### 1.2 B1 明確不做

- **B2**：任何 Canvas atlas（包括 1024² 底色）、R8 mask、窗格隨機夜光、玻璃內部 shader、貼圖生成、二進位資產。
- **B3**：真凹窗、陽台、實體逃生梯／欄杆、精緻窗框、任何新 near/far LOD 或更改 `updateFacadeLOD()`；B1 是**一套單一可見量體**，既有城市 LOD 完全照舊，B3 才掛進**既有** `updateFacadeLOD()` 的單一 scheduler。
- **C/玩法**：CANNON 靜態碰撞體、道路納入 `ROAD_NET`、AI route、地圖/小地圖導航算法、道路合法性、警察/交通/任務調整、存檔 schema、實際可駕駛道路；**絕不把視覺路面誤當作新增物理地板**。
- T-015 所有 `SKY_PRESETS`／曝光／Bloom／ToneMapping 調整；亦不加點光源、陰影 caster、shadow map、新 CDN 或網路存取。
- 任何原始參考 ZIP、GLB、`.blend`、JPG/PNG、第三方貼圖、版面表或新增二進位資產。`modern-city-block.zip`／`modern_city_block.glb` G0 數據（61,243 tris、52 meshes、7 materials、21 textures）僅作美術量級參考，**不參與本 B1 內容生成或檔案複製**。

## 2. Site A 完整座標與 footprint（程式規格必須固定）

**世界約定：** 水平 `(x,z)`、垂直 `y`；Site A 基準中心 **(-501,-790)**。下表是**B1 的具體幾何提案**，與 G0 已確認的區域選址要分開記錄，**Claude 須在 G0 snapshot 上驗證它們的逐個 polygon / bounds**。若提案 footprint 衝突，必須退回修規格（不得實作者靜默平移位置）。

| 物件 | 唯一尺寸／外框（m） | 地面、垂直與用途 | 與既有及新增幾何的關係 |
|---|---|---|---|
| **Site A** | 中心 `(-501,-790)`；走向平行 x 軸；長 100m | G0 以此選址 | 區域位於 `x=-600/-420` 大道之間，不改兩大道 |
| **Street asphalt** | `x∈[-551,-451]`；`z∈[-795,-785]`；100×10 | 表面以採樣既有 `terrainHeight(x,z)` 為基準，作純視覺上浮 `+0.04~0.08 m` | 不加入 `ROAD_NET`、collision；不越出 100m 長度 |
| **South sidewalk + curb** | `x∈[-551,-451]`；`z∈[-799,-795]` | 簡化分區，略高於街面 | 和 North sidewalk **合併為一個 draw batch**，包含路緣 |
| **North sidewalk + curb** | `x∈[-551,-451]`；`z∈[-785,-781]` | 簡化分區，略高於街面 | 不產生額外獨立 draw call |
| **Building A bounding box** | `x∈[-539,-517]`，`z∈[-777,-763]`（22×14） | 基座起點 `terrainHeight`，量體約 13–17m 高 | 離 North sidewalk 外緣 `z=-781` **4m**；無重疊 |
| **Building B bounding box** | `x∈[-484,-461]`，`z∈[-821,-803]`（23×18） | 基座起點 `terrainHeight`，量體約 20–25m 高 | 離 South sidewalk 外緣 `z=-799` **4m**；無重疊 |

**A 精確 L 型平面 polygon（從上往下的世界 x,z 座標；頂視圖）：**

`[(-539,-777), (-517,-777), (-517,-763), (-526,-763), (-526,-770), (-539,-770)]`，閉合回第一點。注意此 polygon 是**缺一角的 L 型**，不可簡化成 `22×14` 方盒；按此輪廓作封閉牆面、底面及屋頂。建築 A 的上層需有**可由街上看到的 ≥1.2m 退縮**；屋頂標高建議主體 13–15m，局部 16–17m。屋頂設備是獨立造型、但**可合併進同一個 roof draw batch**（不另開 draw call）。

**B 圓角平面：** 定義外框 `[-484,-461] × [-821,-803]`，**西北角為半徑 4m 的 1/4 圓弧**，圓心 `(-480,-807)`；曲線以**10 段**從 `(-480,-803)` 連到 `(-484,-807)`（沿角度 90°→180°），其餘邊保持長直段並閉合，實作需核對頂點朝向和法線。需可辨**非 L 的圓角 + 2 層屋頂高度輪廓**，主量體約 20–22m，局部 23–25m；屋頂設備至多 2 件低面數原創 primitive，合併到同一 roof draw batch。不能把 B 做成 A 的純色複製。

**街道 + 外框幾何隔離規則：**

- `asphalt` 與 `sidewalk` 高度是**視覺**高度，G0 需於 `x=-551,-501,-451` 與 z 各鋪面邊界採樣已有地形，避免懸空或 z-fighting；本版不新增地面支撐碰撞。
- 建築 A/B 的地面基準以自身 footprint 角點取既有地表高度；若變化造成底座裸露，允許在**相同 bounding box 內**作 0.1–0.4m 的簡單底裙收邊，不改 physics。**不能未授權把兩棟放上另一條道路。**
- 新場景必須與既有**路網（含直線／ribbon）、交通路線、任務點、地形邊界、既有碰撞形狀、舊 T-012/T-013 區塊**保持空間不重疊。可新增**純資料表 footprint**供測試，不能把它們註冊成真實 `WORLD.buildings` collider 或 AI 障礙。
- 測試時對 `ROAD_NET`、舊 `WORLD.buildings`、`WORLD.roofs`、`CITY`、既有任務與 `physicsWorld` 做前後 fingerprint；**不得為通過測試去改原路線、移走背景建築或碰撞**。

## 3. B1 造型與 GPU geometry／draw-call 預算

**優先採用程式化 `THREE.BufferGeometry` / `THREE.Shape` / `ExtrudeGeometry` 或等價 JS 幾何生成**（方法由指定實作者 Gemini 判斷，須可決定性重建並正確計算三角形）。本階段只是**完整街景量體原型**，非貼圖完成品；可用不貼圖的 `MeshStandardMaterial`／既有等價基本材質，設定與現有日夜光照相容，無 `map`／`emissiveMap`。不得依賴 `.glb`。

| GPU 預算項 | G0 原型回報 | **B1 建議 hard cap** | 如何核對 |
|---|---:|---:|---|
| A 全部 mesh（含退縮、女兒牆、屋頂設備） | 約 **308 triangles** | **≤400 triangles** | Σ visible geometry triangles（無 Instanced 時逐 mesh 求和） |
| B 全部 mesh（含弧角、不同屋頂與設備） | 約 **744 triangles** | **≤900 triangles** | same；B 10 段弧角不可刪減以換預算 |
| 兩棟合計 | 約 **1,052 triangles** | **≤1,300 triangles** | A+B 不超額 |
| 街道（asphalt + sidewalks + curbs） | G0 未給 triangles | **≤120 triangles** | 含兩側路緣及面片實際索引 |
| **B1 全展示合計** | — | **≤1,420 triangles** | 以 ON 可見全部 geometry 統計 |
| 兩棟 **新增主色彩 pass draw calls** | **+4** | **≤+4** | 相同相機 ON/OFF delta，兩棟各 2 batches（shell + roof） |
| 街道 **新增主色彩 pass draw calls** | **+2** | **≤+2** | asphalt 1、合併 sidewalks+curbs 1 |
| **整體主色彩 pass** | **+6** | **≤+6** | 必須真的兩棟與街道同時進視錐，不能靠剔除蒙混過關 |
| 新建築 shadow-pass | 原規格要求 +0 | **0（硬）** | 每個新增展示 Mesh **`castShadow=false`**，含 roof/curb 街景亦不 casting |
| 新貼圖／Shader／光源／physics bodies | 原規格排除 | **0** | `renderer.info.memory.textures` 與 world/cannon 狀態比對 |

**Draw-call 計數前提：** +4 / +2 是**展示 ON 與 OFF 的相對增量**，同一 build、同裝置／viewport/DPR／quality／camera／sky、固定既有 shadows、postFX 與被渲染的物件。`renderer.info.render.calls` 須在同一種主色彩 render pass 上配對；若 EffectComposer/陰影 pass 影響總數，另外記錄 pass breakdown，**不能把 postFX 固有成本拿來當新增建築成本**。每種 PRESET 需確認 `castShadow=false`。量測前固定 `camera`、清理 PMREM/材質首載影響、主動控制視椎內/外狀態，不能只是「程式存在 6 個 Mesh」就自稱 +6。

**批次與隔離：** B1 只需要**一套 A/B/街面 mesh**，不引入第二套展示 LOD；**不改 `updateFacadeLOD()`**（現有函式每 10 幀仍為唯一外牆 LOD 更新）。新增 group 必須保留開關可見性，不被 `batchStaticMeshes()` 合併進既有世界；可在既有 `batchStaticMeshes()` **之後**初始化這組展示，或僅標記展示 Mesh `userData.noBatch`，不全域停用 batching。group OFF 應對 WebGL 產生**+0 新增 calls**、原有場景不變；必須重複 ON→OFF→ON，證明沒有重造 geometry/material 或堆積場景物件。注意 B2/B3 才改共享 LOD 入口與資源生命週期。

**材質預算：** B1 新增**≤5 個**不帶 map 的基本材質實例（A shell、B shell、共用 roof/trim、asphalt、兩側 sidewalk/curb 共用）。無 `CanvasTexture`、`DataTexture`、`GLTFLoader` 新資產；顏色選擇必須讓 A/B 輪廓可分辨而非靠著色來假裝不同。B1 **不新增夜窗像素**，夜間是檢查量體可見性而非夜窗美術驗收。

## 4. 唯一展示入口、快速傳送與已知風險

**採用現有路徑：** `FAST_TRAVEL`（`index.html` 約 10188 行）新增**一筆 `id='SHOWCASE_SITE_A'`**，固定 `x=-501,z=-790`，朝向（heading）先設朝向街道方向（供 Claude/G0 固定，建議 0 rad，畫面由玩家自行旋轉）。現有 `setupWorldMap()` 會對新地點生成**唯一新增 chip 按鈕**；使用者選取 chip 後按**既有** `wm-travel` 傳送。兩個入口元件中，**只有 chip 是本任務新增 DOM button，既有確認鍵不複製**。不新增 Game Hub WORLD 動作鈕、返回鈕、彈窗頁或 3D portal。

<!-- v1.1 CHANGE FIX-1-2-TRAVEL: Claude G0 correction -->
**既有傳送限制與本任務 G0 的衝突解法：** `fastTravelTo(t)` 現有程式遇 `DELIVERY.job` 會擋住一般地點；Claude G0 明確要求**不做任務／車內停用**。因此**只有目標 `t.id === 'SHOWCASE_SITE_A'` 可以繞過 `fastTravelTo` 的 `DELIVERY.job` guard**；所有其他 `FAST_TRAVEL` entries 在配送任務進行中仍由原 guard 阻擋，不得擴大例外。**傳送至 Site A 前後，進行中的 `DELIVERY.job` 必須保持同一任務且內容／進度／狀態完整，不得取消、重設、重新建立或隱性完成；既有計時規則不因本例外改變。**快速傳送流程不新增 `MISSION.active`／`STATE.mode` guard。既有 `teleportTo(x,z,heading,y)` 可同時處理車與步行，**不修改其通用物理/傳送語意**；其他地點快傳不可受影響。車內傳送至 Site A 時須驗證既有 `teleportTo` 車輛分支會清除 `STUNT.active`，且車輛位置、速度及其他暫態依**既有**傳送重置語意正確處理，不保留傳送前不合理運動狀態；步行模式也須可成功傳送且保持步行模式。需在 PR 明確揭露並測試**沒有新增獎勵、沒有未預期重置 `SAVE` 或 `MISSION` 持久欄位**。不得暗中禁止車內、跳出任務、強迫下車；若發現傳送造成不可接受的主線資料破壞，**STOP，回 Claude + Martin 決議是否修規格**，不可自行擴張任務。
<!-- END v1.1 CHANGE FIX-1-2-TRAVEL -->

<!-- v1.1 CHANGE FIX-3-I18N: Claude G0 correction -->
**安全與標示：** 地圖選擇面板說明（`wm-sel-sub`）要能讓玩家知道**「展示街（未設碰撞，可能穿牆）」**；chip 名稱與 Banner 文字不含此句。**正式 `FAST_TRAVEL` 地點名稱（必須完整顯示，不得縮短）：EN `Showcase Site A (No Collision)`；ZH-TW `展示區 A（無碰撞）`。**現有 `setupWorldMap()` 自動生成的 world-map chip，與傳送成功 Banner 使用的 `VH_I18N.name`，都必須依目前語言顯示上述完全相同的字串；`wm-sel-sub` 可保留額外「可能穿牆」說明，**不能新增一整個 UI panel**。必須有英／繁中正確顯示的兩語訊息，不用硬編入獨立語言。無返回快捷鍵，玩家依現有世界地圖其他地點自行快傳離開。選定後以 `terrainHeight(-501,-790)` 的**既有地面支撐**安置玩家／車輛，允許既有 `teleportTo()` 的 y 規則；避免把玩家放到新街道純視覺面上並宣稱有 collider。**Site A 沒有新增碰撞**，人物與車可穿過新建築牆、街緣及路面；此為已知展示限制，不得用測試假裝可正常開車。
<!-- END v1.1 CHANGE FIX-3-I18N -->

**測試專用控制面（非遊戲玩家按鈕）：** 新建築/街道 group 暴露給現有 `__VH` debug 物件或等價測試入口，讓獨立測試在固定鏡頭反覆 ON/OFF；不得污染存檔、新增系統按鍵，或讓「展示 OFF」關閉既有道路、建築、陰影/世界特效。

## 5. 檔案 allowlist、嚴格界線、PR 管理

<!-- REASSIGN CHANGE R2: Implementer terminology -->
**Gemini code PR（如經批准）實作僅允許以下兩個路徑：**
<!-- END REASSIGN CHANGE R2 -->

1. **`index.html`**：新增 Site A 建築 A/B／街面程序化 builder、初始化註冊及 `WORLD` 展示 group（內部控制供量測）、`FAST_TRAVEL` 項目、既有傳送函式對 Site A 的局部特判、現有地圖區塊簡化安全警語與 2 語 UI key、調試輸出。**不改一般快傳條件**。
2. **`tools/test/t014b1_site_a_check.mjs`**（僅新增）：對 production path 的實際幾何、世界 state fingerprint、互動傳送與負面 mutation 執行可重現回歸測試；可引用既有 `tools/test/collision_harness.mjs` 等測試工具，但不可修改它們。

**明確禁止**：新增/修改任何其他程式或測試檔、`sw.js`、`.github/workflows/*`、`package.json`、`COLLAB.md`、`AGENTS.md`、`HANDOFF.md`、`TASKS.md`、`DECISIONS.md`、`LOG.md`、`specs/*`、`libs/*`、`models/*`、`textures/*`、二進位圖檔或所有第三方來源。<!-- CHANGE 2 START: §5 release-branch CI wiring -->
**CI 接入由 Claude 在 release 階段直接提交至同一個 code-PR branch（CACHE bump + `.github/workflows/pwa-cache-check.yml` wiring），不是提前另開 docs/maintenance PR**；原因是新測試檔在 code PR 合併前尚不存在於 `main`。此 Claude release commit 為實作者兩檔 allowlist 的例外，Gemini **仍不得修改** `sw.js`、workflow 或協作文件；規格登錄依既有 docs-only 核准流程，不與 CI wiring 混淆。
<!-- CHANGE 2 END -->
且不得誤碰程式 PR 鎖或破壞 baseline；Gemini PR 應提供執行 `node tools/test/t014b1_site_a_check.mjs` 的獨立測試證據。

**體量：** `index.html` 新增＋修改建議 **≤600 行**（依 COLLAB §5.2），且只聚焦同一段 showcase visual world + 最小既有快傳接線；禁止順手重構原城市生成或重排整頁。若實際 >600 行或 UI 接線與展示幾何難以單一審查，Claude 必須在開始前退回**重新拆分小 PR 與新規格／批准**，不得由實作者自行突破。**一時間只有一個未合併的程式 PR**。Gemini 自最新 `main` 開 `gemini/T-014B1-site-a-showcase` → PR → Claude review → release → Martin 驗收；未經 Martin 明確批准前不執行。

<!-- REASSIGN CHANGE R3: New Stage 3 pre-start and independent measurement gates -->
## 5A. Gemini Stage 3 改派專用 G0 前置閘門（COLLAB v3.6 §4.3；僅在改派獲 Martin 核准後生效）

**資格與路由：** `TASKS.md` 記錄 Gemini `Current stage: 3`（D-026），但這只表示可被考慮。HIGH/SMALL 預設 Codex；改派 Gemini 須由 Claude 審查本補充及 Martin **明確批准整份改派規格**。本段不擴張 §1–§5 的展示功能、兩檔 allowlist、幾何/渲染上限、快傳例外、存檔與物理不變原則。任何 Stage 3 前置條件未滿足，**BLOCKED / NO PR**。

**開工前檢查（缺一不可，由 Claude 在 G0 記錄 PASS／BLOCKED）：**

1. **可核對 baseline**：重新取得最新 `main` SHA（§0 所載 `ff0ced15...` 僅為歷史查核基準，不可直接視為開工基準）、確認 D-013 `main` 保護、唯一 code-PR 鎖空閒、Antigravity 可在指定 repo 建立 `gemini/T-014B1-site-a-showcase` 分支與 PR；列出 `index.html`、現有 `FAST_TRAVEL`/`teleportTo`、`ROAD_NET`、物理／renderer 測試入口的實際可用性。
2. **自足規格及風險對照**：<!-- CHANGE VERSION START -->以本 v1.2 全文<!-- CHANGE VERSION END -->（§1–§9）作 self-contained spec；HIGH 風險為世界幾何/地形、renderer/draw calls、快傳/車輛/配送任務狀態、物理碰撞不變、PWA/i18n/save。§6 的 `B1-SITE/SHAPE/BUDGET/RENDER/PHYS/TRAVEL/REPEAT/COMPAT` 均須有可執行 production-path 斷言與故意破壞後變 RED 的案例；固定 seed／可重播的玩家模式、job、車輛狀態與相機情境；不得僅 grep、mock renderer 計數或宣稱「已覆蓋」。
3. **Claude 可獨立重跑**：先在 Claude 環境證明既有 harness 可取得 baseline、可固定 seed／camera／preset、可運行 §6 測試、可收集 `cannon-es` step 與真實 Chrome `renderer.info.render.calls`。若需測試設施而目前無法取得，**不得先開 Gemini 高風險 PR**；由 Claude 提出 Codex 或另立測試設施任務供 Martin 裁決。
4. **量化閾值與超標處置**：§3 的 triangles/calls/material/shadow 硬上限、§7 的 ≥30 FPS 與待 Martin 校準的 ON/OFF ≤10%、OFF/OFF noise ≤5% 不變。額外提議物理回歸 `median(PR step time / baseline step time) ≤1.25`（**本次改派提案的新量化上限，須 Claude G0 審查及 Martin 批准才生效**）；<!-- CHANGE 3 START: §5A physics hard gate and control -->
各 preset 分別判定；**硬閘門為 `physicsWorld.bodies` 數量及各 body `shapes` 數量／內容 delta = 0**。另以相同方法、相同 seed／場景／preset 做 **baseline-vs-baseline ≥5 組配對控制**，控制組中位數時間比值若 **>1.10**，該 preset 量測 **INVALID，必須重跑**；控制組不得用於解釋或豁免 PR/baseline >1.25。
<!-- CHANGE 3 END -->任一量測缺失、樣本不可重播、超額、CI 缺測、重大回歸或任務狀態損壞均 STOP／不 merge；不能改 baseline、放寬既有測試或自行調高門檻。

**Claude 獨立測量計畫（PR 審查與發布時，不得由 Gemini 自證代替）：**

- **物理成對測試**：同一 baseline 與 Gemini PR、相同 seed／場景／畫質，至少 `PHONE_LOW`、`DESKTOP_HIGH`，並對 Site A 相關情境加 `TABLET_MED`；每個 preset **至少 5 組成對** `cannon-es` step/headless 時間。逐組公布 baseline ms、PR ms、PR/baseline ratio、各 preset 中位數；本提案物理 cap 1.25（待批准）。<!-- CHANGE 3 START: §5A paired physics procedure -->
另以同樣方法、相同 seed／場景／preset 做至少 5 組 **baseline-vs-baseline** 配對，逐組報告兩側 step ms 與比值；控制組中位數比值 **>1.10 即 INVALID，須排除環境雜訊後重測**，絕不能拿控制組無效或偏高當作 PR 超標的豁免。**`physicsWorld.bodies` 與每個 body 的 `shapes` delta = 0 是獨立硬閘門**，即使時間比值通過也不能放行結構差異。測試 Site A showcase ON/OFF 與無新增碰撞，並與既有物理控制場景對照；不得以「新增 0 collider」代替 step-time 量測。
<!-- CHANGE 3 END -->
- **真實 WebGL draw calls**：在相同 camera xyz/lookAt、視角、seed、sky、viewport、DPR、preset 下量測 baseline、PR showcase OFF、PR showcase ON；至少 `PHONE_LOW`、`DESKTOP_HIGH`、`TABLET_MED`。逐場景列出實際 Chrome `renderer.info.render.calls` 的絕對值、OFF/ON delta 與 pass breakdown；須滿足 §3 A+B ≤+4、street ≤+2、合計 ≤+6、shadow +0、OFF +0，並排除首載及 frustum-cull 假陽性。無法獨立取得真 renderer 數據則 BLOCKED，不得以結構估算或 Martin FPS 取代。
- **完整回歸與 CI**：Claude 重跑 `AGENTS.md` 所有適用檢查與 `node tools/test/t014b1_site_a_check.mjs`，親自驗證 §6 mutations（至少 B1-SHAPE/PHYS/TRAVEL/RENDER 各一項 RED），記錄命令、SHA、seed、preset、輸出、PASS/FAIL；確認離線 PWA、載入、舊快傳、配送任務、車輛、存檔相容、無碰撞與雙語 chip/banner。<!-- CHANGE 2 START: §5A CI integration timing -->
Claude 於 **release 階段在現有 code-PR branch 直接提交 CACHE bump（`sw.js`）與 `.github/workflows/pwa-cache-check.yml` 測試接線的 release commit**，確認 CI 確實執行新增測試且通過後才能完成合併／發布；**不得先另開 docs/release PR**（新測試檔尚未存在於 `main`）。Gemini 的實作 commit 仍嚴守兩檔 allowlist，**不得碰 workflow 或 `sw.js`**。
<!-- CHANGE 2 END -->
- **裝置證據分離**：Martin 的 S26 Ultra PHONE_MED、Tab S11 TABLET_MED `?fps=1` 與美術驗收仍依 §7；須標明 `code-reviewed`／`headless-measured`／`browser-measured`／`device-measured`，不得將任一類別冒稱另一類別。

**退回／停工：** 任一 §4.3 測試、物理或 draw-call 獨立量測缺失而企圖 merge，或重大效能/物理/存檔/離線回歸、越權 diff、不實測試宣稱，Claude 應阻擋發布並依 COLLAB v3.6 §4.3 將 Gemini 新高風險指派暫停、交 Martin 裁決是否退回 Stage 2；故意繞過 PR 鎖／保護或偽造證據則暫停全部 Gemini 指派。一般可修正 bug 依既有最多兩輪 review，不能換另一代理直接接管同一 PR。
<!-- END REASSIGN CHANGE R3 -->

## 6. 可失敗的 tests / 回歸與 mutation 設計（必須跑 production 行為）

測試須執行／載入**真實 `index.html` 的 builder、初始化、地圖與傳送接線**（例如沿用既有 VM/THREE test harness 或真瀏覽器）；**不以 grep、檔名存在、純 regex 比對代替行為驗證**。測試檔須提供**故意改壞會變紅的 mutation** 及紀錄；測試允許自己建立 harness 的 stub，但 production geometry 必須是實際執行結果。

| Test ID | Production 斷言（成功條件） | 刻意變異，必須 FAIL |
|---|---|---|
| **B1-SITE** | `Site A (-501,-790)`；道路 `100m x 10m`、sidewalk 各 4m；A / B 的頂點、包絡與 `ROAD_NET`/既有道路/任務/碰撞/建築完全不重疊；<!-- CHANGE 1 START: B1-SITE terrain-height assertion -->
asphalt／sidewalk／building base 的 y 必須在各取樣點等於 production `terrainHeight(x,z)` 加上 §2 指定的視覺 offset（如適用）；Site A 實測平坦 y=0，不能以「非全為 y=0」作通過條件
<!-- CHANGE 1 END --> | 把 A 的 polygon 推入街面、把道路平移到 `x=-600` 大道，或<!-- CHANGE 1 START: B1-SITE y mutation -->
將所有新增 asphalt／sidewalk／building base 的 y 一律抬高 `+0.5m` → RED
<!-- CHANGE 1 END --> |
| **B1-SHAPE** | A 使用上述六點 L polygon 並真的缺一角，退縮 ≥1.2m；B 真正有 10 段圓弧與獨立屋頂高度，四面與屋頂皆可見、法線合理；兩建築不可互換輪廓 | 把 A 封成方盒、把 B 改 1 段斜切或變同輪廓、刪掉退縮 → RED |
| **B1-BUDGET** | production 渲染可見 triangles：A≤400、B≤900、street≤120、合計≤1420；材質≤5、無 texture 或外部請求；每個新增 Mesh castShadow=false | 增加過度細分 geometry、開 `castShadow`、新增 texture → RED |
| **B1-RENDER** | 固定視角/預設、同 frame 同世界：A+B 主 pass ≤+4 calls、street ≤+2、總 ≤+6，shadow pass +0；showcase OFF 真正 +0 calls、回復 ON 後幾何/material reference 不變；既有全域 batching 維持 | 增加未合併的 Mesh、OFF 仍渲染或材質重建、啟用陰影 → RED |
| **B1-PHYS** | `physicsWorld.bodies` 和每 body 的 `shapes` 前後相等；`ROAD_NET`、交通 routes、mission state、existing roofs/buildings、舊 T-010/012/013 幾何 fingerprint 不變；無 `vh_save` 新欄位 | 加一個 CANNON Box、改 road route、刪既有建築、更新 save schema → RED |
<!-- v1.1 CHANGE FIX-1-2-3-TESTS: Claude G0 correction -->
| **B1-TRAVEL** | FAST_TRAVEL 只增 `SHOWCASE_SITE_A` 一筆；新增 chip 可選、existing `wm-travel` 可點；**(a)** `DELIVERY.job` 有效時傳送至 Site A 成功且原 job identity、內容、進度、狀態完整保留（不取消／不重設）；**(b)** 同一有效 job 下傳送任一其他 FAST_TRAVEL entry 仍被原 guard 阻擋且 job 不變；**(c)** 車內傳送 Site A 成功、`STUNT.active` 清除、車輛位置及既有速度／運動暫態重置正確；**(d)** 步行模式傳送成功且保持步行模式；**(e)** EN chip 與 `VH_I18N.name` Banner 均精確顯示 `Showcase Site A (No Collision)`；**(f)** ZH-TW chip 與 `VH_I18N.name` Banner 均精確顯示 `展示區 A（無碰撞）`；英／繁中有無碰撞警示；沒新增返回 button | 刪新 chip、對 Site A 套用 `DELIVERY` 阻擋、傳送時清除／重建 job、意外解除其他地點 guard、保留 `STUNT.active` 或車輛異常動態、阻擋步行模式、把目的地寫錯、任一語言 chip／Banner 名稱不符或少掉警語 → RED |
<!-- END v1.1 CHANGE FIX-1-2-3-TESTS -->
| **B1-REPEAT** | 連續 2 次傳送、切英／繁中、天氣/日夜切換、ON/OFF 三輪：scene 子節點數、materials、geometry、physics bodies 與 renderer.texture count 不持續增加 | 每次傳送都重新呼叫 builder 或新增 material → RED |
| **B1-COMPAT** | 所有 AGENTS 對應既有回歸通過（尤其 T-010/012/013、road legality、碰撞與地圖/任務/存檔）；離線 PWA、兩語、手機 HUD、第三人稱、交通控制仍可用 | 故意破壞既有 `FAST_TRAVEL` 點或 `vh_save` 讀寫 → RED |

**CI 驗證 gate：** Claude 確認測試有辨識力、production path 可被測到、錯誤不僅是 parser fail；至少從 **B1-SHAPE、B1-PHYS、B1-TRAVEL、B1-RENDER** 各做一個最小負面變異且有真正 RED 證據。若實際環境無法做 WebGL pass 粒度 headless，`B1-RENDER` 分為 Claude 的固定瀏覽器對照與 Martin 裝置證據，不能把 mock count 冒稱真 WebGL draw-call。`code-reviewed` / `headless-measured` / `device-measured` 要明確區隔。

## 7. FPS 校準與裝置驗收（門檻為 G0 提案，**尚未獲 Martin 校準**）

**G0 量測提案（待 Martin 裝置校準確認）：**

- 裝置：**S26 Ultra PHONE_MED**、**Tab S11 TABLET_MED**；各在同一裝置、固定位置與 camera、resolution scale、pixelRatio、time-of-day、畫質、地面交通與陰影條件對照。**事前檢查遊戲 FPS 限制已關閉**；明確記錄系統螢幕更新率、省電、溫度、是否正在快速傳送或 PMREM 載入。
- **絕對底線：** showcase ON 白天與夜晚每個 60s 取平均 FPS，**每組三次的中位數 ≥30**；各次平均與 1 秒最低 FPS 一併保存；若某次跌破 30 需調查，不只展示最佳一次。
- **相對門檻（暫定）：** 在每種裝置 × 固定 day/night（逆光畫面評估可以另附），安排 **3 個完整 ON/OFF 量測配對**，各 60s、先暖機並交錯順序。定義 `control = median(FPS_OFF[1..3])`、`showcase = median(FPS_ON[1..3])`、`drop = max(0, 1 - showcase/control)`，暫定須 `drop ≤ 0.10`。**不能將 D-041 舊 Midtown 74.4/70.6 與 46.0/49.6 直接當這次 Site A 的控制組**；只可背景對照。
- **雜訊有效性（暫定）：** 同裝置／同位置先做至少 **3 組 OFF/OFF 配對**，`noise = max_i |FPS_OFF_Ai - FPS_OFF_Bi| / median(FPS_OFF_A1..A3, FPS_OFF_B1..B3)`，暫定 `noise ≤ 0.05`；若 >5%，**此次 ON/OFF 相對下降結論 INVALID**（檢查溫度、刷新率、背景耗電、FPS cap，重新校準）；**不得把雜訊超標當成性能合格或自行加大 10% 門檻**。
- **配對測試必須固定相機**而非由傳送時自動相機移動；需全 showcase 在畫面內且不被 frustum/occlusion cull；另測附近步行視角是人工審美檢查。每次截圖/錄影/CSV 記錄 time、device/preset、DPR、viewport、sky、camera xyz/lookAt、ON/OFF、FPS avg/min1s、renderer calls、shadow state、備註；由 Martin 做最終實機判讀。若環境難以嚴格重現交通/熱狀態，應標為待校準，不可美化數字。
- **裝置 gate 地位：** ≥30 FPS 為必守底線；**≤10% 與 ≤5% 是 Claude G0 已提出、待 Martin 校準/確認的初始建議**。Martin 沒確認前不能宣稱相對性能通過；若需調整數字，**經 Claude/ Martin 額外決議並更新已批准規格**，不容 Gemini 自行修改。B1 的自動/人工測試與最終 acceptance 分開：單元測試 PASS 不代表 Martin 的美術或裝置 PASS。

**供 Claude 固定比較的座標建議（不是玩家額外傳送點）：**

- A 街對面：camera `(-528, 6, -791)` → lookAt `(-528, 9, -770)`。
- B 街對面：camera `(-473, 8, -788)` → lookAt `(-473, 12, -812)`。
- 雙棟總覽：camera `(-501, 24, -742)` → lookAt `(-501, 10, -790)`；記 FOV、解析度、固定同一光照。

高度是**世界絕對 y 的拍攝建議**，若實際 Site A terrainHeight 不為 0，則整組 camera y 與 lookAt y 須一致加上現場實測 groundY 並鎖定。**不得混比不同天空與地點。**

## 8. 美術交付、既有系統保護、依賴與驗收

- **B1 ART checkpoint = 量體方向審閱（非最終 ART PASS）**：至少正面、雙斜角、鳥瞰，以及 A/B 天際線比較；同一 daytime 照明；允許夜晚照明下看可見性，但不應評 B2 尚不存在的夜窗/材質。A 明確 L 形且有退縮；B 明確弧角、屋頂層級不同；視覺街面與基座接地，不可大量 z-fighting、穿過既有建物或路面。
- **打光規則**：優先讓獨立批准／發布的 `T-015` 先確立光照；若 T-015 尚未完成，使用 main **完全相同** sky/time/exposure/PMREM/Bloom/grade 作 before/after board；不在本 B1 改任何全域光照。不把 B1 的基本材質畫面判定為整個 T-014 的最終畫質。
- **Compatibility**：`vh_save` 全欄位不變，舊快傳/任務/交通與車輛物理不變，所有既有模型、城市建築、Lod、Game Hub、地圖、雙語與離線 PWA 可運作；CPU/VRAM/texture 不因重複快速傳送或 ON/OFF 累積。`castShadow=false` 意味新建築不投真動態陰影，是已知美術取捨。
- **通過路徑**：Claude review 與 CI PASS → Claude release（遵守 COLLAB）→ Martin 實機 FPS 校準（含 noise gate）及 B1 輪廓審閱 → 才有 B1 驗收。**T-014B2/B3 尚未批准**；R8 雖經 G0 可行，也不能在 B1 PR 偷做。整條街道成為可駕駛區域或進行全市普及須另立 T-014C／後續任務，Martin 另批。

## 9. 送 Claude 審查前須明確回覆的窄項目

1. **footprint 再核對**：§2 的 A/B polygon、街面與 sidewalks 是否仍位於 G0 已掃描可用範圍，尤其北側 z=-763、南側 z=-821 的範圍。若超出 G0 已驗證 footprint，先擴充 G0 collision/route 驗證；不可只憑中心點乾淨就合格。
2. **一次新增一筆 + 一按鈕的 UI 解讀**：確認採「`FAST_TRAVEL` 一筆→`setupWorldMap` 自動產生一個 chip，使用現有 `wm-travel`」符合本次 G0。若 Claude 指的是**額外新建 Game Hub WORLD 直接傳送按鈕**，需在 Martin 核准之前明確修訂 allowlist/test/UI 規格，不能默默多做。
<!-- v1.1 CHANGE FIX-1-2-3-G0-QUESTION: Claude G0 correction -->
3. **快傳例外**：只有 `SHOWCASE_SITE_A` 繞過 `fastTravelTo` 的 `DELIVERY.job` guard，且 active job 完整保留；其他地點仍被阻擋。車內 `teleportTo` 重置 `STUNT.active` 及車輛狀態、步行傳送均須實測；chip 與 `VH_I18N.name` Banner 的 EN/ZH-TW 完整「無碰撞」名稱亦須實測。若 G0 不接受，退回裁決。
<!-- END v1.1 CHANGE FIX-1-2-3-G0-QUESTION -->
4. **測試重現**：確認當前 `collision_harness` 可驗證新 B1 builder/地形/快傳；確立 renderer 與陰影 pass +6/+0 能由哪個工具執行，不能只使用 stub。
5. **控制組可用性／FPS 噪聲**：Claude 建議的 10% drop、5% OFF/OFF 門檻仍待 Martin 校準；若無法有效控制溫度/refresh，先提出裝置量測變更方案。

---

## HANDOFF ChatGPT -> Claude

```text
HANDOFF ChatGPT -> Claude
<!-- v1.1 CHANGE VERSION-HANDOFF: Claude G0 correction -->
<!-- CHANGE VERSION START -->
Task: T-014B1 spec v1.2 DRAFT (Gemini Stage 3 reassignment; Claude G0 conditional pass)
<!-- CHANGE VERSION END -->
<!-- END v1.1 CHANGE VERSION-HANDOFF -->   Base commit: ff0ced15ec85f80905b4ef5c0b696afbf0f93194   Read: COLLAB.md, DECISIONS D-013/D-021/D-026/D-039-D-042, TASKS.md, AGENTS.md
Context: G0 selected Site A (-501,-790), 100m x-axis corridor between avenues -600/-420, clean of existing buildings/roads/colliders/missions; B1 footprint is explicitly specified for Claude to recheck.
Context: B1 only generates original A L-massing + B curved-corner massing + basic 100m visual street: prototype ~308/~744 tris, +4 building/+2 street main-pass calls. No atlas, R8, night windows, colliders, routes, added LOD, or reference assets. New Mesh castShadow=false.
<!-- v1.1 CHANGE FIX-1-2-3-HANDOFF: Claude G0 correction -->
Context: Minimal single new FAST_TRAVEL entry and one map chip button; no return or new car/mission disabling. Device gate >=30 FPS plus proposed <=10% median ON/OFF drop and <=5% OFF/OFF noise, subject to Martin device calibration.
Context: v1.1 G0 corrections: SHOWCASE_SITE_A-only DELIVERY.job bypass preserving active job; other entries remain blocked; car STUNT.active/vehicle reset and on-foot tests; EN "Showcase Site A (No Collision)" / ZH-TW "展示區 A（無碰撞）" on map chip and VH_I18N.name banner.
<!-- END v1.1 CHANGE FIX-1-2-3-HANDOFF -->
Deliverable: <!-- CHANGE VERSION START -->Review the attached full T-014B1 v1.2 draft;<!-- CHANGE VERSION END --> validate precise footprint, minimal-entry semantics, production/mutation tests, file allowlist, draw budget, and task-state teleport side effects. Review proposed Gemini Stage 3 exception and physics cap 1.25; <!-- CHANGE APPROVAL START -->Martin must confirm that he requested Gemini reassignment; approval wording must be 「批准 T-014B1 v1.2」 before registration. Obtain explicit approval first.<!-- CHANGE APPROVAL END --> Do not register, implement or start a code PR yet.
<!-- v1.1 CHANGE VERSION-FILENAME: Claude G0 correction -->
<!-- CHANGE VERSION START -->
SPEC: T-014B1-spec-v1.2-GEMINI-REASSIGNMENT-DRAFT.md (this file)
<!-- CHANGE VERSION END -->
<!-- END v1.1 CHANGE VERSION-FILENAME -->
```
