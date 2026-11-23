# T-014B2 spec v1.2 — Site A Commercial + Office Art-Quality Facades / R8 Night Windows（DRAFT）

> **REGISTRATION NOTE (Claude, 2026-11-23):** Approved by Martin ("批准", 2026-11-23 19:55) as T-014B2 v1.2 (D-045). Registered verbatim from ChatGPT's v1.2 DRAFT; the DRAFT/NOT-APPROVED wording below is superseded by this note. Claude G0 checks: T-014 v2.2 capacity numbers (R8 512² ≈0.25/0.33 MiB) match; B1 test compatibility confirmed by reading (B1 test extracts only the T-014B1 marker block and requires exactly one buildShowcaseSiteA() call in startup); browser CI precedent exists (coverage-render.yml uses preinstalled google-chrome + playwright 1.55.0). **Gemini must not start until Claude records the §5 pre-start gates as PASS.**

> **Status: DRAFT / NOT MARTIN-APPROVED / DO NOT REGISTER OR IMPLEMENT.** 本文件僅提出 B2，非 B3 或全城 rollout 授權。**v1.1 延續美術方向：Building A = Commercial（商業）；Building B = Office（辦公）；Residential（住宅）留待 B3，B2 不新增第三棟。**Claude G0 審查 → Martin 明確「批准 T-014B2 v1.2」→ Claude 登錄 → Gemini 單一 code PR → Claude 獨立驗證及 release → Martin 裝置／美術驗收。**沒有 ART PASS。**
>
> **Source of truth:** repo root `COLLAB.md` v3.6 §§3,4.3,5.1–5.2,7.1；`AGENTS.md`、`TASKS.md`、`DECISIONS.md` D-026/D-027/D-043/D-044；`specs/T-014B1-spec-v1.2.md`；`index.html`；Martin 提供的 T-014 v2.2 B2 方向與 Claude R8 G0 結果。**注意：本次未能在 repo `specs/` 找到 `T-014-spec-v2.2.md`；以下 v2.2 相關數字依 Martin 此次提供的摘要，不冒稱逐字核對原檔。**
>
> **Baseline:** B1 release `vh-2026-11-23-01` / PR #93 / commit `2e801b1`（D-044）。開工前 Claude 必須重取最新 `main` SHA，確認 B1 的 6 meshes、5 materials、無碰撞與唯一 code-PR 鎖；如已偏離，STOP 並重新審查。

## 0. 分工、分類與開工條件

- **Task:** T-014B2；**Risk: HIGH**（材質/shader、WebGL texture、renderer、行動裝置效能）；**Volume: SMALL**（僅既有 Site A 6 meshes；`index.html` 新增＋修改目標 ≤600 行）。
- **Implementer: Gemini（Antigravity Remote Agents, Stage 3）**；**Reviewer/Releaser: Claude**；**Device/Art judge: Martin**。偏離 COLLAB §5.1 預設 Codex 的理由：Codex 額度接近耗盡；B2 被隔離於 B1 6 meshes，規格有可測量的貼圖、draw-call、物理及資源生命週期硬閘門。此為單次例外，絕不降低 §4.3。Claude 若無法重跑自動測試、物理配對或真 Chrome renderer，**不得**讓 Gemini 啟動高風險 PR。
- Gemini 不得開始直到：Martin 核准完整自足 spec；Claude 確認 baseline/分支保護/唯一 PR 鎖、測試 harness、Chrome renderer 及 `cannon-es` 可重跑；每項風險有可失敗的 assertion 和 mutation；§5 所有閘門可執行。不能以 stub 或「預期 PASS」替代證據。

## 1. 唯一交付範圍

1. 在 **B1 原有 Site A (-501,-790) 的 6 個 meshes** 上提供共享程序化立面貼圖：**1024×1024 RGBA8 Canvas base atlas**（色彩、非發光立面）與 **512×512 真 R8 單通道 window mask**（控制夜窗）。不建立第 7 個展示 mesh；不更改 B1 A 六點 L 型、B 十段圓角、屋頂、街道、坐標、三角形數量、group 結構或碰撞。僅允許在現有 builder 補充 UV attribute；貼圖／材質 patch 必須由 builder 外的獨立函式處理；對非立面（roof、asphalt、sidewalk）可保留原外觀，但仍不得新增第三張 texture。兩張貼圖須可共用於所有需要它們的現有 mesh，且 A/B 外觀能區別。**A 必須呈現商業用途、B 必須呈現辦公用途；不可僅以配色或招牌作區分。**
2. Atlas 必須是**由本地 JS Canvas 在初始化時一次生成的原創內容**：牆面色塊、可讀窗格/層線、適度不規則的立面節奏；日間窗戶不應被夜光效果洗白。**夜間發光只由 R8 mask 的 `.r` 通道決定**，遮罩的 lit/dark pixel 必須有實際亮度差；亮窗分 **3 個可辨亮度級**，黑窗不可因 shader 基礎 emissive 變亮。固定 seed 產生可重現結果，不得每幀隨機重建。**窗格與材質節奏須服從 §2A 的商業／辦公美術規則，禁止兩棟只換色的通用重複窗格。**
3. R8 必須是真正 GPU `R8` storage（G0 證據：`texStorage2D` internalFormat `33321`）、具有 mip，custom shader 從 `.r` 取樣；不能用 RGBA 貼圖假冒單通道或靠 material alpha 近似。G0 的 lit 225 / dark 6 是原型觀測值，**不是新實作的通過結果**。若現行 Three.js/WebGL API 不支援所需 R8 mip 路徑，**STOP**，交 Claude 裁決；不可私自換 RGBA mask 或加 CDN。
4. <!-- CHANGE 3 START: existing night path and no new loop -->
日／夜必須重用既有 `STATE.night`／sky-preset 更新路徑驅動，不新增獨立 loop、scheduler 或第二套夜間狀態；既有世界日夜狀態驅動，不能修改 `SKY_PRESETS`、T-015 的曝光、Bloom、ToneMapping、PMREM 或全域燈光。可在既有 render/update 入口更新**已存在 uniform 的純數值**；不在每幀建立 material、texture、array、typed array、closure 或 shader。日間夜窗發光關閉；夜間以 mask 三級亮度顯示，切換後不殘留白天或前一夜狀態。若 B1 材質採共享 roof trim，改造不得使非立面被誤套夜窗。
<!-- CHANGE 3 END -->
5. 保留 B1 唯一 `SHOWCASE_SITE_A` 快傳、EN `Showcase Site A (No Collision)` / ZH-TW `展示區 A（無碰撞）`、`wm-sel-sub` 警示、配送任務例外及 `teleportTo` 車／步行語意。不得改 `VH_I18N` keys、UI、`updateFacadeLOD()`、`ROAD_NET`、`physicsWorld`、存檔、任務、交通、LOD、地形、碰撞、導航。B3 的凹窗／窗框／陽台／逃生梯／細節幾何一律不做。**本版所稱窗框、立柱、飾帶與入口皆只能由貼圖／shader 的平面視覺表達，不得產生厚度或新幾何；住宅類型及其陽台留待 B3。**

## 2. 貼圖、UV 與 shader 行為

<!-- CHANGE 3 START: concrete texture and atlas contracts -->
- **Atlas:** 1024² RGBA8、mipmaps，使用 `THREE.CanvasTexture`、`THREE.SRGBColorSpace`、`flipY=false`；固定 deterministic seed，於展示初始化時一次生成。**唯一展開、非 tiled 的 atlas UV layout**：A/B 各自獨立且不重疊的 island，沿實際牆段／弧長展開，不能把同一窗格 tile 在整棟牆面重複貼滿；透明度保持不透明。
- **Mask GPU contract:** 512² `THREE.DataTexture`、`THREE.RedFormat` + `THREE.UnsignedByteType`（真 `R8`）、`THREE.NoColorSpace`、`unpackAlignment=1`、啟用 mipmaps，shader 只讀 `.r`；每個有效窗格在 mask 至少 **4×4 texels**，相鄰窗格之間至少 **1 texel 全暗 gutter**，含 mip 採樣邊界檢查；不足時必須重新分配 island，而非降低門檻。
- **Test/screenshot metadata:** `WORLD.showcaseSiteA.atlas = { seed, islands: { A, B } }`；`islands` 必須提供可供測試與截圖定位的 deterministic UV bounds／牆段映射資料；不得以 metadata 取代實際 GPU 驗證。
<!-- CHANGE 3 END -->
- **Mask:** 512²、R8、mipmaps、線性單通道，採 `.r`。mask 以 0 表示 dark，三種非零級別表示 lit；建議規格化 `0, 0.33, 0.66, 1.0`，允許因量化 ±1/255；三個 lit level 在夜間最終 shader output 必須可區分。不能只驗證 JS 陣列值而不驗證 GPU 取樣結果。固定 seed 下亮/暗窗皆存在，至少抽樣各一個並保留測試坐標。
- **UV:** 目前 B1 builder 產生 `position`/`normal`，尚無可用立面 UV（本次讀取 main `buildShowcaseSiteA`）。Gemini 可在 builder 的既有 6 個 geometry 補充 UV，對 A 的六段 L 牆面（含內凹轉角、退縮）及 B 的十段圓弧**沿牆面實際弧長連續映射**，避免扭曲／鏡射／整段弧角共用同一 texel；上下層不應產生明顯斷層。頂／底面須有有限合法 UV，避免 NaN；屋頂和道路可保持原材質或使用 atlas 的非窗格區。不得增加 triangles、submesh/material group 或 draw calls 來修 UV。
- **Mask/atlas alignment:** 同一表面上的 atlas 與 mask 應使用一致的 facade 局部座標（容許不同解析度），窗格邊界與亮窗位置相符；跨 atlas island 的 UV 不得讓夜窗出現在 asphalt/roof。A/B 外牆法線、背面與弧角視覺須在正面及斜角實機截圖檢查。
- **Shader:** 僅 Site A 既有材質使用 custom shader patch 或等價受控方式，維持原日夜光照相容；材質生命週期固定，`customProgramCacheKey`／shader cache 不得隨日夜切換無限制增加；不得污染其他世界材質。材質數量 **≤B1 的 5 個**；若因 Three.js shader/material 組合確需額外材質，先退回 Claude 改規格，不能暗增 draw calls。

## 2A. v1.1 延續 建築美術規格（ART-QUALITY；僅 2D Atlas／既有 Mesh）

**本節是新增的可驗收設計要求，不授權擴大 §1／§3 的 GPU、mesh、material、draw-call 或工時預算。** Atlas 可分配獨立 island 給 A/B；兩棟使用相同兩個 texture objects，但具有不同的立面節奏與用途辨識度。若現有 1024² atlas 的有效 texel 密度無法達標，須向 Claude 回報 ART/效能衝突並請 Martin 決策；不得自行提高解析度、添加貼圖、幾何、燈光或第三棟。

### 2A.1 Building A — Commercial（商業用途，L 型）

- **街道層（ground floor）**：以 atlas 表現連續但有明確店面模組的大面積玻璃展示窗、入口門扇／門框、店面之間的實牆或金屬分隔；玻璃不可是一整片沒有分格的純色矩形。入口須可由街道正面與斜角辨識；不得新增可互動門、商店 UI 或招牌文字資產。
- **上層**：較密的商業窗格、水平樓層飾帶、至少兩種立面面材（例如石材色塊與金屬／玻璃色塊），與一樓形成可讀的垂直分區；L 型內凹轉角與外牆接縫不得產生窗格穿幫。
- **立面層次**：以像素明暗、邊框色、接縫、反射色階及遮蔽色表現 2D 深度；**不新增**真實凹窗、凸出雨棚、實體柱、玻璃透明 pass 或任何 geometry。
- **夜景**：商店展示窗可比上層更常亮，但所有亮度**只由同一張 R8 mask 的 `.r`** 及既有夜間 scalar 控制；一樓仍必須有暗窗／暗區，上層亮窗分散，不能整面均勻發光。三級非零亮度都需在 A 的可見窗格中有樣本。

### 2A.2 Building B — Office（辦公用途，十段弧角）

- **辦公帷幕**：以規律、細密的垂直金屬 mullions、連續的水平樓板帶及較大的玻璃窗模組建立辦公用途辨識度；至少兩種玻璃反射色階，避免單一色塊。
- **弧角**：十段弧面 UV 沿實際弧長連續；窗格與金屬分隔沿弧線自然過渡，不得把每個 segment 畫成各自獨立、方向錯亂的平面貼紙；正面與斜角均需可讀。
- **入口與屋頂**：入口以 2D 材質分區顯示商務大廳感，屋頂維持 B1 量體；不得加入新屋頂設備、立柱或真實幾何細節。
- **夜景**：以樓層／辦公室為單位產生**固定 seed 的非均勻**亮暗排列；至少存在相鄰的亮／暗窗組合，三級非零亮度均有樣本；不允許整層全部同步亮滅或整棟一致亮度。日間仍以玻璃材質而非 emissive 發白呈現。

### 2A.3 共通美術硬條件與 ART checkpoint

1. **不用文字或顏色也可辨識用途**：隱藏招牌／文字、改以中性灰階檢視時，A 應仍能由店面大玻璃、入口分割、商業樓層節奏辨識；B 應仍能由帷幕模組、垂直 mullions、樓板帶辨識。這是 Martin 的 ART 驗收項，不以自動測試宣稱「美感 PASS」。
2. **非通用貼圖**：A 與 B 的窗格比例、立面分格、街道層處理及夜間亮暗分布必須有**結構性差異**，不能只替換顏色或將同一 tile 拉伸。窗框、石材／金屬接縫、玻璃反射與陰影均只能使用 atlas 像素或現有 shader；無實體細節。
3. **一致性**：日間、夜間、正面、斜角及可見弧角／L 內凹轉角截圖均需檢查；UV 不得伸展、倒轉、露出 atlas gutter、使窗格穿過牆面邊界，或讓屋頂／街面誤亮。
4. **貼圖密度**：以實際裝置截圖判斷細節是否糊成雜訊或產生明顯鋸齒／摩爾紋；若 1024²／512² 不足以提供所需精度，記為 ART limitation，**不得突破原硬預算**。
5. **住宅留待 B3**：本版沒有 Residential 建築、陽台、住戶窗型或第三種 atlas island 的交付義務；B3 是否增加展示建築及 GPU 預算須另立 spec、另經 Martin 批准。

<!-- CHANGE 4 START: texture density / art limitation -->
**ART LIMITATION（必須向 Martin 揭露）：** 約 **2,900 m²** 外牆共用 1024² atlas，預估有效解析度僅約 **16–19 px/m**（受 island 排列與 gutter 影響）；約 **25 px** 的窗戶仍可辨識，但 mullions／細金屬窗框約 **1 px**，手機近距離觀看可能明顯偏軟。這是 B2 固定貼圖預算下的可預期畫質限制，不得以提高解析度、新增 texture 或幾何偷渡解決；**由 Martin 以實機 ART checkpoint 決定是否接受**，未接受不宣稱 ART PASS。
<!-- CHANGE 4 END -->

### 2A.4 美術專項測試（加入原 §4 測試檔，仍只有一個新測試檔）

- **B2-ART-A**：測試 atlas 上 A 的 ground-floor storefront 區與 upper-floor 區均非空，具有不同窗格尺寸／分格結構；固定 seed 的可見商業窗格抽樣含 0 和三個 lit mask level；故意讓 A 全部使用 B 的 office tile／刪除一樓店面分格 → 指向 ART-A assertion 的 **RED**。
- **B2-ART-B**：測試 B 的 office mullion／floor-band 模組存在且與 A 的模組結構不同，十段弧角 UV 連續，夜間樓層亮暗不均且有相鄰亮暗窗；將 B 全面換成 A storefront tile／弧角 UV 設常數 → 指向 ART-B／UV-B assertion 的 **RED**。
- **B2-ART-VISUAL**：Claude 收集 A/B 日／夜、正面／斜角的固定相機截圖並檢查貼圖取樣與 mask 對位；Martin 決定 ART PASS／REVISE／FAIL。**自動化只能驗證結構與像素條件，不代替美術主觀驗收。**

## 3. GPU、CPU 與硬預算

| 指標 | B2 hard gate | 量測與解讀 |
|---|---|---|
| Atlas GPU 儲存 | 1024² RGBA8 + mips | 約 5.33 MiB（4/3 × 4 MiB） |
| R8 GPU 儲存 | 512² R8 + mips | 約 0.33 MiB（4/3 × 0.25 MiB） |
| **兩張 GPU texture 合計** | **≤5.67 MiB（以 bytes ≤5,947,392 為精確 cap）** | 不計 CPU Canvas 暫存；依格式/尺寸/mip 級數計算並核對實際 GPU internal format |
| 新 texture objects | **≤2** | B1 對照為 0；Atlas 1、mask 1；renderer.info.memory.textures 新增 ≤2（需排除其他場景的非同步載入） |
| 新 mesh / geometry triangles | **0 / 0** | 仍為 B1 6 meshes，A 136、B 320、street 64 triangles（D-044），不以額外幾何做窗戶 |
| 新材質 / 新光源 / shadow casters | **0 / 0 / 0** | 原 B1 5 materials 可替換其 shader/map，但不增加 material instances；每個新增展示 mesh `castShadow=false` |
| Main-pass draw calls | **B2 − B1 ≤0**；Site A ON−OFF **≤+6** | 相同 camera、preset、光照，六 mesh 全入視錐；mirror pass 另列，不把 mirror 重畫誤當主 pass 新增 |
<!-- CHANGE 5 START: headless timing scope -->
| Atlas+mask 初始化時間 | **≤12 ms（Claude headless 暖機後中位數，≥5 次）** | **僅 headless CPU 初始化量測門檻**；既有 G0 約 6–9ms 為參考。測試記錄 Canvas generation + mask population + texture creation 的 CPU elapsed，排除首次 shader compile / GPU upload，另記首次 upload 成本。手機可能發生更慢的一次性載入卡頓；**不宣稱裝置 ≤12ms**，實機需獨立觀察。超標 STOP／修正後重測 |
<!-- CHANGE 5 END -->
| 每幀新資源 | **0** | 無 texture/material/typed array/Canvas/BufferGeometry/closure 配置；允許既有 uniform scalar 更新；用 instrumentation / allocations 抽樣驗證 |
| Physics bodies/shapes delta | **0 / 0** | 不新增碰撞；既有 traffic pool 變化須用固定場景與 fingerprint 區分，不得當成合法新 body |

**記憶體計算：** `1024×1024×4×(1+1/4+…)=5,592,405⅓ bytes`；`512×512×1×(1+1/4+…)=349,525⅓ bytes`；總約 `5,941,930.67 bytes`（≈5.667 MiB）。整數 mip chain 真實加總應由各級整數 texel 計算；上表 5,947,392 bytes 提供少量整數/對齊容差，**不能因此更改 texture 格式或尺寸**。CPU Canvas RGBA backing store、JS arrays 和 driver accounting 應另列，不能宣稱整個 process VRAM 僅 5.67 MiB。

**Render-pass 量測必備：** 在真 Chrome/WebGL 測試設定 `renderer.info.autoReset=false`，每次固定連續 ≥120 frames，先暖機；每 frame 在主 pass 前 `renderer.info.reset()`，主 pass 結束立刻記 `renderer.info.render.calls`，mirror/reflection、shadow、postFX 各自另記或在同一 frame 逐 pass 記差值。不得只讀整幀總 calls 就稱「主 pass」。至少 `PHONE_LOW`、`TABLET_MED`、`DESKTOP_HIGH`；在 B1 baseline 和 B2 PR 用相同 camera / DPR / sky / time / traffic seed 測白天及夜晚，記各 frame、各 pass 的絕對 calls、中位數、delta。mirror pass 可能重畫同一 mesh；須**分開揭露**而非隱藏，不能把 mirror 重畫算作新的 main-pass draw calls。若無法隔離 pass，該 draw-call gate 標為 **INVALID**，不得宣稱 PASS。

<!-- CHANGE 1 START: browser test runner -->
**唯一新增測試檔：** `tools/test/t014b2_site_a_facade_check.py`，以 Python **Playwright** 啟動真 Chrome/WebGL，採 `tools/test/coverage_browser.py` 的瀏覽器測試風格。B2 必須透過實際 Canvas 像素、WebGL R8 readback、shader/render 結果驗證，不能使用 B1 Node VM 充當 GPU。Claude 在原 code-PR branch 的 release commit 新增**獨立 browser CI job** 執行此 Python 測試（不是把它當 Node test 塞進既有無瀏覽器的 job）。Gemini 的 two-file allowlist 為 `index.html` + 此一 Python 檔；Claude release commit 例外可修改 CI workflow 與 `sw.js` CACHE。
<!-- CHANGE 1 END -->

## 4. 測試設計：production path + mutation 必須 RED

測試檔須載入/執行**真實 `index.html` builder、texture/shader 接線、日夜切換、渲染及資源生命週期**；不能只 grep、比對字串或用 stub 假裝真 GPU 渲染。所有固定 seed 和取樣窗格座標須寫入測試輸出，便於 Claude 重播。

| Test ID | PASS assertions | Mutation 必須 RED |
|---|---|---|
| **B2-ATLAS** | 1024² RGBA8 Canvas atlas、512² GPU true R8 + mip、`.r` sampling；≤2 新 texture objects；GPU mip bytes ≤5,947,392；色彩/線性格式正確 | R8 改 RGBA8、改 1024² mask、關 mip、錯 `.g` 通道或多建第三張 texture → RED |
| **B2-NIGHT** | 固定 seed 至少 1 dark + 3 lit level；A/B 各有 dark + 3 lit level 的可見窗格；日間 emissive window = off；夜間 `.r` 驅動三個亮度級且 dark 保持 dark；GPU pixel/readback 或可信 Chrome shader 測試 | 把所有窗改亮、dark 強制發光、三個 level 合併為一級、夜間不讀 mask → RED |
| **B2-ART-A** | A 商業一樓店面與上層分區的 atlas 內容、分格結構及 R8 可見窗格亮暗取樣符合 §2A.1 | 用 B 辦公 tile 全面取代 A、抹除店面分格 → ART-A RED |
| **B2-ART-B** | B 辦公帷幕的 mullion／樓板帶與 A 結構不同；夜間亮暗窗相鄰且三級可見 | 用 A 商業 tile 全面取代 B、將辦公樓層全改同亮度 → ART-B RED |
| **B2-UV-A** | A L polygon 六段（含內凹）+ 退縮外牆 UV 有限、覆蓋正確、方向一致；無 window bleed 到屋頂/街道 | A 凹角 UV 變 NaN、反轉一段、讓內凹面 UV 全重疊或把屋頂貼窗 → RED |
| **B2-UV-B** | B 10 段弧角沿弧長展開，窗格不拉成斜切；UV 連續且各段面積非零 | B 弧段 UV 全設常數、反轉弧段、只映射成一個平面 → RED |
| **B2-DAYNIGHT** | 日→夜→日→夜至少 3 輪，無 shader recompilation leak，顏色/窗亮狀態可逆，sky presets/lighting state 未被修改 | 日間仍亮、切回夜晚後全部黑、每次切換 new material → RED |
| **B2-REPEAT** | 連續快傳、ON/OFF ≥3 輪、日夜切換：6 meshes、5 materials、2 textures、geometry refs、shader program count、scene children 不累積；OFF 時新增 main calls 0 | 每次 ON 或快傳重建 atlas、每次夜間新增 shader program/texture → RED |
| **B2-BUDGET** | Atlas init ≤12ms 中位數、無每幀資源分配、draw calls B2−B1 ≤0 / ON−OFF ≤+6、shadow +0、physics delta 0 | 增加 mesh/calls、每幀 new Canvas/texture、開 castShadow、增加 physics body → RED |
| **B2-COMPAT** | `VH_I18N` 原 keys/EN-ZH 值 fingerprint 不變；`FAST_TRAVEL`、DELIVERY.job 例外、車/步行、`ROAD_NET`、save、LOD、offline PWA 不變；B1 `node tools/test/t014b1_site_a_check.mjs` 全 PASS；AGENTS 全套 PASS | 改 chip 翻譯、取消 B1 delivery bypass、改 save、使 B1 測試失敗 → RED |

**Mutation gate:** 至少 B2-NIGHT、B2-ATLAS、B2-ART-A、B2-ART-B、B2-UV-A、B2-UV-B、B2-REPEAT、B2-BUDGET 各示範一個**有辨識力的 RED**，不接受僅 syntax/parser error；失敗必須指向目標 assertion。Claude 自行執行並記錄。<!-- CHANGE 2 START: immutable B1 test and external facade patch -->
**B1 測試不變更、不跳過：** `tools/test/t014b1_site_a_check.mjs` 原檔完全不修改，必須繼續 PASS。把 atlas/mask 生成與材質 patch 放入 `// T-014B1: visual-only Site A ...` 至 `// T-014B1_END` **標記區塊之外**的獨立函式（例如 `applyShowcaseFacades()`），並於 `buildShowcaseSiteA();` **之後**呼叫。B1 builder 區塊內**只允許新增 UV attributes**，不在其中建立 atlas/mask、patch 材質或修改 B1 預設未貼圖行為；Node VM 執行 B1 builder 時仍為原 B1 的零貼圖狀態。新 Python Playwright B2 測試則在真實瀏覽器中斷言完成 facade patch 後的兩張貼圖、夜窗與 GPU 行為。若 B1 測試仍無法 PASS，STOP 交 Claude 裁決，不能編輯 B1 測試。
<!-- CHANGE 2 END -->

## 5. Gemini Stage 3 §4.3 / §5A 式獨立量測閘門

1. **Baseline / preflight:** Claude 獨立記錄最新 main SHA、B1 renderer/physics baseline、固定 seed、三種 preset、測試工具可執行、`main` 保護與 code-PR 鎖。確認 T-014B1 已經合併/發版且沒有未解 P1 回歸。缺任一條件 → STOP。
2. **Physics hard gate:** `physicsWorld.bodies` 和所有 body `shapes` 的展示增量 **0**，指紋不變。至少 `PHONE_LOW`、`TABLET_MED`、`DESKTOP_HIGH`，各 ≥5 組同 seed/場景的 baseline/PR `cannon-es` step time 配對，逐組公布時間與比值，`median(PR / baseline) ≤1.25`。另以相同方法量測 ≥5 組 baseline/baseline control，若其 `median(ratio)>1.10`，整組物理效能結果 **INVALID、必須重測**；不得把噪音當作超標豁免。若 control 有效但 PR >1.25 → FAIL/修正。
3. **Draw calls:** Chrome 真 WebGL `renderer.info`，`autoReset=false`、≥120 frames、每 frame pass-by-pass；各 preset、day/night、A/B/overview 相機；B2 main-pass 對 B1 **+0**、showcase ON/OFF **≤+6**、shadow +0；mirror 單列。任何 pass 無法辨識 → INVALID，禁止合併。
4. **Texture / performance:** Claude 自行核對 GPU true R8 internalFormat、mip、RGBA8 atlas、texture count +2、計算 byte budget、warm atlas init ≥5 次中位數 ≤12ms、無每幀資源配置；不以 headless CPU 時間冒稱手機 FPS。
5. **CI / ownership:** Gemini code PR **僅能**修改 `index.html` 與新增 `tools/test/t014b2_site_a_facade_check.py`；不得改 `sw.js`、`CACHE`、`.github/workflows/*`、`package.json`、`specs/*`、任何 docs/asset/第三方檔。Claude 審查及量測 PASS 後，**在同一 code-PR branch 上由 Claude 做 release commit**，包含 `sw.js` CACHE bump 與獨立 Playwright browser CI job（可在 `.github/workflows/pwa-cache-check.yml` 增設 job），CI 必須真正安裝瀏覽器、執行 Python 測試並綠燈；不得要求 Gemini 修改上述檔，也不得另開一個更早的 CI PR。Claude 可依 COLLAB 流程獨立登錄已核准 spec；未核准不得登錄。
6. **Independent review:** Claude 必須從 baseline 和 PR 重新執行指令、檢查 diff、完整 AGENTS 回歸與 B1 tests、mutation RED、offline PWA、存檔與地圖；記錄 `code-reviewed`、`headless-measured`、`Chrome-measured`、`device-measured` 的界線。超標、不可測或 CI 未接入 → 不 merge、不 release。

## 6. 裝置驗收與必備 `?showcase=0` debug 入口

- **Martin 實機:** S26 Ultra `PHONE_MED`、Tab S11 `TABLET_MED`，Site A 固定相機、白天／夜晚各 ≥3 組 60 秒，showcase ON 的每組平均 FPS 中位數 **≥30**；記錄平均 FPS、最低 1 秒 FPS、DPR、畫質、時間、溫度/刷新率及 `?fps=1`。每次 <30 須調查，不能只挑最佳一組。
<!-- CHANGE 5 START: required showcase URL debug flag -->
- **必須加入 `?showcase=0`：** 在 `index.html` 使用最小 `URLSearchParams`，於 `buildShowcaseSiteA();` 後呼叫既有 `setShowcaseSiteAVisible(false)`；無參數與 `?showcase=1` 預設 ON。只改啟動時 Site A group 的可見性，不能改存檔、快傳、其他世界、材質建立時機或新增玩家 UI toggle。Playwright 必須驗證三種 URL 與 ON/OFF 可見性；此 debug flag 是 B2 必交項，不再可選。若無法在 two-file allowlist 內安全完成，STOP 退回 Claude，而非省略。相對 FPS 仍須由 Martin 實機量測，不可因存在參數即宣稱通過。
<!-- CHANGE 5 END -->
- **相對性能（使用必備 debug 參數）：** 同位置/相機/設定下 ON/OFF 各 3×60s，`drop=max(0,1-median(FPS_ON)/median(FPS_OFF)) ≤10%`；OFF/OFF ≥3 配對 noise ≤5% 才有效。這兩項是 B1 延續的**待 Martin 校準確認提案**，不能因沒有 OFF 參數就宣稱已通過；若實機未量測，標 `NOT MEASURED`。另外 B2 對 B1 的性能增量應由 Claude 獨立 Chrome/physics 結果與 Martin ART 判斷，不可拿 ON/OFF 當 B2-vs-B1 對照。
- **ART checkpoint:** A L 形與 B 弧角不能被 atlas 破壞；日間立面具可辨樓層/窗格，夜間有部分亮窗、部分暗窗、三段亮度且沒有整棟均勻發光；正面/斜角/鳥瞰、日夜截圖。**新增 §2A 的 A 商業／B 辦公用途辨識度、材質細節、窗格節奏與夜間差異，為 Martin 必須明確判定的 ART checkpoint。**這是 B2 立面貼圖與夜窗的審美驗收，**不代表 B3 完成或全城 ART PASS**。

## 7. G0 待 Claude 明確核對的問題

1. 原 T-014 v2.2 的 B2 atlas island 分配、夜窗三段亮度、R8 WebGL1/2 相容策略，是否與此草案一致？若 v2.2 原文另有硬數值，先比對並修訂，**不得擅自以本草案覆蓋原文**。
2. B1 builder 僅補 UV、B1 marker 區塊外 `applyShowcaseFacades()` 於 build 後執行的隔離方案，能否讓原 `t014b1_site_a_check.mjs` **完全不修改且 PASS**？Claude 必須實際驗證 Node VM 與 Chrome Playwright 的分工。
3. 真 R8 mip 在現行 Chrome/Android WebGL 路徑是否可獨立重現，GPU bytes 與 shader sample `.r` 如何量測？shader 是否僅在夜間更新 scalar uniform 而不重新編譯？
4. `renderer.info.autoReset=false` 後的主 pass / mirror pass 分離測試點能否在 Chrome 穩定收集 120 frames？若不能，先修測試設施，不把累計總 calls 當主 pass。
5. Atlas 初始化 ≤12ms（G0 6–9ms 參考）是否可在 Claude headless 暖機條件下穩定量測？實機載入是否需要另記一次性 upload spike？
6. §2A 的 A 商業、B 辦公兩種 atlas island 與 R8 夜窗是否能在原 2 textures、5 materials、6 meshes、+0 calls、≤12ms init 的預算內達到可辨識的 ART 水準？若不可，請提出不改硬預算的美術取捨並交 Martin 裁決。
7. 必備 `?showcase=0` 是否在 two-file allowlist 與原 B1 group 行為下正常運作？Claude 需測三種 URL；若不成立，退回修正，不得省略。

---

## HANDOFF ChatGPT -> Claude

```text
HANDOFF ChatGPT -> Claude
Task: T-014B2 spec v1.2 DRAFT
Base: T-014B1 released PR #93 / vh-2026-11-23-01 / 2e801b1
Read: COLLAB.md v3.6, TASKS.md, DECISIONS.md D-026/D-027/D-043/D-044, AGENTS.md
Context: B1 Site A has exactly six meshes, five untextured materials, no collision and +6 main-pass calls.
Context: B2 proposes shared 1024² RGBA8 Canvas atlas plus 512² true R8 mipmapped night mask, .r sampling and three lit levels; no B3 geometry.
Context: v1.1 ART direction: Building A Commercial storefront facade; Building B Office curtain-wall facade; Residential deferred to B3. Both use the original six meshes and two textures.
Context: Gemini Stage 3 is requested as HIGH/SMALL routing exception because Codex usage is nearly exhausted; full §4.3 gates remain mandatory.
Deliverable: Independently G0-review §2A art feasibility and structural mutation tests, geometry/UV/shader feasibility, B1 test compatibility, Playwright R8 readback, memory/init budgets, real Chrome pass-separated draw calls, paired physics and browser CI release workflow.
Decision needed: Verify immutable B1 Node VM test passes with facade patch outside B1 markers; verify Playwright GPU test and browser CI job; validate required ?showcase=0 and fixed-budget ART tradeoff.
Status: DRAFT. Await Martin explicit approval: 批准 T-014B2 v1.2. Do not register or implement.
HANDOFF -> Claude G0 review.
```
