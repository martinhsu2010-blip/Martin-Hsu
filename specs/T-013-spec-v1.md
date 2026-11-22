# T-013 spec v1 DRAFT — C+ Midtown Architectural Art-Quality Recovery Pilot

> **Status: PROPOSED / NOT MARTIN-APPROVED.** 本文件是 ChatGPT 提議的下一階段規格，非程式實作許可。必須經 Claude 規格審查、Martin 明確批准 **T-013 v1**、Claude docs-only 登錄後，才可啟動 Codex。
>
> **Design baseline:** GitHub `main` **`ed95ead47e8e488d3f1b4fee480da68051829485`**（2026-11-22 查核）。實作者開工時須重取最新 `main` SHA，若程式碼差異影響本規格，退回 review。
>
> **Source of truth:** repo root `COLLAB.md` v3.6 (§3、§4.3、§5)、`TASKS.md`、`DECISIONS.md`（D-013、D-027、D-031–D-038）、`AGENTS.md`、`specs/TEMPLATE.md`、`specs/T-010-spec-v1.1.md`、`specs/T-012-spec-v1.1.md`。
>
> **Owner/Implementer:** Codex。**Reviewer/Release:** Claude。**Design approval/device acceptance:** Martin。**Risk: HIGH**（3D 世界立面與 renderer draw calls）。**Volume: SMALL**（既有試點中的 2 棟，單一 façade 系統）。**Priority: P1**。**Routing rationale:** 本次是審美比例、遮擋和材質選擇等 judgment-heavy 小型高風險任務，依 COLLAB v3.6 §5.1 指派 Codex；不是將大量低風險資料機械式交 Gemini。
>
> **Branch (after approval):** `codex/T-013-midtown-art-quality`。**Code PR allowlist:** `index.html` 與一個新測試 `tools/test/midtown_art_quality_check.mjs`。不准修改舊測試、`specs/`、`TASKS.md`、`DECISIONS.md`、`AGENTS.md`、`LOG.md`、`HANDOFF.md`、`sw.js`、`.github/` 或二進位資產；Claude 負責 CI 接線與發版。

## 1. Problem, art goal, and non-goals

### 1.1 影片觀察與原因（非自動驗收數據）

Martin 提供約 21.7 秒、1728×1080 的實機遊戲錄影 `7877.mp4`。在 **00:06–00:08** 可見許多平坦、單色、重複窗位的中低樓；**00:14–00:18** 比較精細的淺色傳統建築與周邊方塊建築形成強烈落差，強光也使淺色牆面細節不易分辨；**00:20** 仍可看到連續、缺少材質差異的方塊建築。影片含開啟世界地圖及移動鏡頭，**不能僅憑錄影判定每個入鏡建築都是 T-012 選中的兩棟**，Claude 必須做 G0 實際映射。

根據現行程式，T-010 增加窗框/窗台，T-012 `buildMidtownStreetscape()` 增加店面玻璃、窄立柱、水平層帶和前庭；**大面積基礎立面仍沿用單色 `coverage` 外牆**。玩家覺得細節不足，反映既有「新增幾條線條即 PASS」的規格過於偏重技術而缺少真正的美術審查。

### 1.2 唯一可交付的下一階段成果

**在同一個 T-012 兩棟試點，不擴展建築數量**，改善 **東向主立面**的牆面材質、結構分區與立體感。玩家從 `MIDTOWN_W` 或指定固定鏡頭看見的應是**兩棟有不同建築身份、可辨識樓層/窗間牆/底層商用入口**的中低樓，而不是同色方盒子。保留 VICE HORIZON VI 原有明亮、略風格化的特色，不追求複製特定遊戲或攝影級材質。

**必須有肉眼可見差異的三個層次**：A) 原單色東牆改為低對比的建築表面質感；B) 窗間牆、垂直側框/柱帶與層間面板呈現前後關係；C) 地面店面/門口有對比明確的底座分區。不得以增加細碎線條、顆粒/噪點或任意加亮取代 A–C 的完整組合。

### 1.3 不做的事

不擴充到六棟或全城；不變更 `CITY_COVERAGE_LOTS`、`WORLD.cityInfill`、原建築尺寸/高度、道路/人行道/forecourt、collider、車流/警察 AI、車輛/相機、任務/存檔/語言、日夜/天空/霧、`renderer.toneMappingExposure`、Bloom、全域後處理、HUD/UI。**影片中過曝是獨立的後續 T-014 候選任務**，T-013 不用降低曝光掩蓋立面問題。不得新增 GLB、外部貼圖、CDN、二進位素材或新的 PWA 網路依賴。

## 2. G0 prerequisite — Claude must verify before Martin approval

1. 在 `PHONE_LOW`（390×844）、`TABLET_MED`（Android Tablet UA，800×1280）、`DESKTOP_HIGH`（1280×800）實際運行，讀取 `WORLD.midtownFacadePilot.selected.slice(0,2)`，核對兩棟是同一輪 T-012 `WORLD.midtownStreetscapePilot.selected`，且 `coverage===true`；**不可重新排序，也不可根據影片猜另一批建築的位置**。對每 preset 記錄兩棟 `(x,z,w,d,h)`、原有材質/窗戶與可見東面。
2. G0 確認兩棟的東牆 `east=b.x+b.w/2`（預期 x=-263）、既有玻璃中心面 `east+0.06`、T-010 框/窗台、T-012 門店面/立柱/鋪面，既有一樓 cornice `y=2.99..3.21`。取得原始 T-012 版的日/夜正面、45° 斜視固定鏡頭截圖，列出表面互相遮擋的區域。**若候選或幾何不同，先修訂 spec，不准 Codex 自選替代。**
3. 區分「影片裏的其他 coverage 方盒子」與這兩棟試點；該問題留到 T-013 驗證成功後的**另立**覆蓋工作，不在本 PR 順便美化相鄰建築。

## 3. Visual direction and exact implementation contract

### 3.1 Two differentiated identities, not one repeated skin

- **Building A = selected[0]：Warm Limestone / 商業街**。底層深暖灰/石材基座 `#5E564D`；上層暖石色 `#A99B83`；窗間牆/收邊 `#827665`。材質 `roughness≥0.78, metalness≤0.05, emissive=0`；不可純白或發光。
- **Building B = selected[1]：Muted Sage / 城市住宅**。底層深石綠 `#4D584D`；上層灰綠 `#818775`；窗間牆/收邊 `#626A5C`。同樣禁止純白/發光。
- 這些顏色為 **設計初始值**，不是允許任意改全城的材質；在單一固定鏡頭對照中，Claude 檢查兩棟有**可辨識的不同明暗和色相結構**。若 G0 指出重度過曝使上述顏色全不可分，先記錄阻擋並要求規格修訂，不擅改全域曝光。

### 3.2 Rebuild visible *façade reading*, preserve existing tested features

- **Wall treatment:** 在每棟的**東向外牆**增加低成本的主牆材質/面板，覆蓋可見上層牆面而不動原建築 shell、其碰撞或原 mesh instanceColor。可使用 **一張共用、初始化時一次產生的 ≤256×256 CanvasTexture** 作為極淡的細砂漿/石面紋理（固定 seed、無可辨識大塊隨機噪點），並由同一張材質以 per-instance 顏色區分兩棟；或改用等效的極少量幾何/色彩，但 Claude 應於 G0 對比確認不再是純色大片牆。不得每幀重建或下載素材；不得新增大量獨立貼圖或 bump/normal maps。
- **Architectural depth:** 每棟須有可在斜視角辨識的 **至少兩種深度層級**：貼牆面板與突出牆柱/窗間牆/橫向 spandrel，外凸構件**不得超過東原牆 `east+0.25 m`**。裝飾只在外側，不能伸入室內或街道。不可把窗框、立柱與主牆一律做在同一平面。
- **Upper levels:** 新增側向 pilaster/窗間立面分割（每棟至少兩個有效段），以及至少兩個**不遮擋原有玻璃**的 spandrel/樓層細節區。用現有 `windowData`/`WORLD.coverageWindows` 取得玻璃真實高度與矩陣；不得假設 PHONE/TABLET 和 DESKTOP 具有相同高度。任何新的上層區域須低於 `b.h-0.5`，且不遮住 T-010 原窗框/窗台或 T-012 楼層帶。**不可亂蓋原窗造成「窗戶消失」**。
- **Ground floor:** 保留 T-012 已存在的中央門與左右兩側玻璃，讓兩棟的首層基座/牆面深淺明確區分上層（界線位置不跨既有 cornice）。任何新增店面面板/門口裝飾**頂緣 ≤2.95 m**；新上層立柱 **起點 ≥3.25 m**；既有 cornice `2.99..3.21` 不得穿插。**不得新增第二個門**或宣稱店面可進入。
- **Forecourt:** T-012 前庭 `x=-262.8..-257.0`、頂面 `y=0.18`、有效 sidewalk 段與所有既有 apron/街緣細節保持**完全不變**。不新增地面物理或修改已有設定；T-012 的已知 apron 無 collider 是既有已接受的權衡，本任務不得擴大。

### 3.3 Exact cost and lifecycle boundary

- **最多 2 個新增 `THREE.InstancedMesh` + 2 個新增共享 `MeshStandardMaterial`，面向**兩棟共用批次**，不允許每層/每窗用獨立 Mesh。新 CanvasTexture 最多 1 張、解析度 ≤256×256、無外部依賴；每棟色彩由 setColorAt 實現。`castShadow=false`，必要時 receiveShadow=true。
- 新 mesh 必須註冊 `FACADE.chunks` 沿用 `FACADE.nearDist`，不新增 per-frame callback、強制更新、動畫、listener、DOM 或另一個 LOD 系統。允許記錄 `WORLD.midtownArtPilot={selected,meshes,...}` 的測試 debug handle（非 save）；舊 T-010/T-012 debug handle 和 mesh data 必須保持不變。
- 完成後 T-010 的原 2 個 batch、T-012 的原 3 個 batch**一律保留**；新增最多 2 個 batch，不能更改/刪除過去的舊測試或既有 scene object 以換取通過。Production index.html 目標 ≤300 行新增／變更；測試 ≤350 行；超過須 Claude review 並評估拆 task。
- 如果實際需要以破壞既有 T-010/T-012 幾何方式才能做出美術品質，**STOP / spec v1.1**，不能私下解除本限制。

## 4. One-task workflow

| Gate | Owner | Deliverable |
|---|---|---|
| G0 site/art review | Claude | 三 preset 確認兩棟真實選址；T-012 baseline 日/夜與斜視鏡頭截圖；檢查新牆面不會擋住原玻璃及 T-012 店面 |
| G1 spec approval | Martin → Claude | Martin 明確說「批准 T-013 v1」；Claude docs-only PR 原文登錄 spec/TASKS/DECISIONS，提供新 main SHA |
| G2 pre-start | Claude | baseline 可 checkout、測試設計能失敗、無其他 code PR；先確認成對 physics/render 量測可重現 |
| Implementation | Codex | 唯一 `codex/T-013-midtown-art-quality` PR；只修改 allowlist、跑全部 AGENTS 與專屬測試，附實際結果及固定鏡頭前後圖 |
| Review / release | Claude | 獨立測試與視覺比較、效能門檻、D-013 保護重查、CI 接新測試、cache/PWA release |
| Device acceptance | Martin | S26 Ultra、Tab S11：近距與斜視日/夜，比較 T-012 before/after，獨立接受**美術**與 **30 FPS** |

## 5. Regression plan — failure-capable, production geometry

新測試：`node tools/test/midtown_art_quality_check.mjs`。用既有 Three.js / VM / collisionHarness 在三 preset **執行真正 `buildCityInfill` 與 production 新 façade builder**；可在測試中讀 production mesh instance matrices、材質及窗矩陣，不能複製一套假的 builder，也不能只 grep 關鍵字。

| Risk | Mandatory assertion | Example temporary mutation that MUST fail |
|---|---|---|
| R1 scope | `WORLD.midtownArtPilot.selected` 身分、次序恰等於 `WORLD.midtownStreetscapePilot.selected` 兩棟；非選中地塊無新增 art instances；同 preset 固定 seed 再跑結果相同 | 選取 `slice(1,3)` 或覆蓋所有 coverage → FAIL |
| R2 original preservation | baseline/PR 對照：`WORLD.midtownFacadePilot`、`WORLD.midtownStreetscapePilot` 的 selected、instance matrices、材質屬性、場景原建築 placement、windowData 和兩棟 apron 均不變 | 改 T-012 apron y、移動原 T-010 窗框 → FAIL |
| R3 visible structure | 新 wall treatment / pilaster / spandrel 的 bbox 逐棟在 east wall ±0.25m 與 b.z ±b.d/2 範圍內、沒有越 roof；有**至少兩種有效外凸深度**、至少兩段上層分區和兩個有效 spandrel；不侵入玻璃/原窗框或 T-012 店面；新店面頂 ≤2.95、上柱起 ≥3.25，保留 cornice | 將 spandrel 移到玻璃中心、把新玻璃外牆設 0.30m、上柱從 3.0m 起 → FAIL |
| R4 style + batch | 2 棟不同 palette (`A`/`B`)，前後材質無 emissive；共用材質、≤2 新 InstancedMesh、≤2 新材質、≤1 共用 CanvasTexture(≤256²)，`castShadow=false`，`FACADE.chunks` 註冊；傳送/切語言不重建 | 全棟一個色、改為數十 Mesh、啟用陰影、移除 LOD registration → FAIL |
| R5 collision/traffic/save | `physicsWorld.bodies` 和 shapes +0；路網、車流、建築碰撞、存檔鍵與 payload 不變；舊 T-010/T-012 測試仍 PASS | 加 collider 或更改 WORLD.cityInfill → FAIL |
| R6 visual (Claude browser, not fake unit test) | 三 preset、相同近景固定相機、日夜以及 45° 斜視：兩棟顏色/材質不同，牆面有可見質感與至少兩層立面深度，原窗戶、店面和 apron 不消失；0 網格閃爍、0 材質錯誤/貼圖遺失 | 將新增 batches `visible=false` 應失去新材質與深度；同場景原樣即不算可見改善 |

**不能用技術 PASS 代替美術 PASS：** Claude 必須將 baseline vs PR 的固定相機**四組**（日正、夜正、日斜、夜斜，至少）同尺寸圖片並排交 Martin，標出每棟新增的牆面、窗間牆與底層分段。Martin 若認為仍像方塊、沒有值得擴大的美術品質，可以 **ART REJECTED**，即使所有單元測試/效能 PASS，任務仍不進入大規模複製。Claude 不得以「新增 N 個 mesh」或其他 proxy 取代此裁定。

Claude 至少臨時注入三種**獨立** mutation（選址、遮窗、批次/材質）證明新測試能 FAIL；修改需還原，不准弱化舊測試/fixtures。Baseline 不存在 T-013 功能，因此新測試對 baseline 應 FAIL，舊測試在 baseline/PR 應保持 PASS。

## 6. Independent benchmarking — COLLAB §4.3 / T-012 measurement discipline

### 6.1 Reproducible scenes and profiles

- 三 preset：`PHONE_LOW` 390×844、`TABLET_MED` Android tablet UA 800×1280、`DESKTOP_HIGH` 1280×800。報 UA、profile、quality、DPR、postFX、shader readiness 與是否模擬；**headless ≠ Martin 真實裝置**。
- 固定 seed **5019**、清理相同 localStorage、相同天氣/時間、無輸入。**近景:** `camera=(-232,5,-292)`, `lookAt=(-268,7,-310)`；**斜景:** 由 Claude 在 G0 固定拍攝座標及矩陣、以兩棟都清楚可見且不在 collider 裏為準，註冊到 spec review 記錄。**Control:** `teleportTo(110,650,0)`，遠離 pilot、固定 camera。**白天和夜晚**各取 baseline/PR 相同場景、構圖、LOD state、後製設定；不能在 PR 後任意移動相機來通過。
- 如果 G0 發現前方鏡頭遮擋或不在兩棟可見位置，先請 Martin 核准修訂 v1.1；不要讓實作者自己改 scene 選址。

### 6.2 Physics — regression guard, not art metric

- **主要硬 gate:** 每 preset/scene 的 baseline → PR `physicsWorld.bodies.length` 和 `Σbody.shapes.length` **delta=0**；每個原 collider 的 type/transform、道路與路線摘要不變，任一不符 **FAIL / no merge**。
- 由 **Claude 獨立**做每 preset × near/control 的 baseline/baseline **5 組成對校準**（A/B、B/A 交替），頁面載入與 teleport 後，各 sample 直接同步 `__VH.physicsWorld.step(1/60,1/60,3)` **warmup≥900 次**，用 `performance.now()` 計量 **360 次 step 的總耗時**；逐組公布 `A_ms/B_ms/ratio`。校準中位數必須在 **[0.75,1.33]**，否則 **MEASUREMENT BLOCKER**，修環境重測。
- 正式 baseline/PR **5 組交替配對**、報每組時間和 ratio `PR/base`；**median ≤1.25**；若 5 組超標，保留 5 組並補到 **9 組**再判，不可降低上限。9 組仍 >1.25 → FAIL，不得 merge。此計時不可冒稱真實 rAF FPS。

### 6.3 Draw calls, memory, and startup

- Claude 在**真實 Chromium renderer** 同一 preset × near/control × day/night，baseline 與 PR 各取 **≥60 幀 `renderer.info.render.calls` 的中位數**，記錄絕對值與 delta；若使用 software GPU 或禁用真實 GL，標明限制，不能冒稱 device-measured。貼圖需要等待完全初始化。
- **Near draw-call delta 上限:** `PHONE_LOW +2`、`TABLET_MED +2`、`DESKTOP_HIGH +2`；**control +0**。新批次總數 ≤2、不新增陰影投射。任何 preset 或場景超標、不一致或 renderer 計數缺失 → FAIL / BLOCKER，不能以更改 preset、降低 quality、關閉其他 pass 來過關。
- 新 CanvasTexture **最多 1×256×256**；額外貼圖的理論 RGBA 原始像素記憶體 **≤256 KiB**（不含 GPU mipmap/driver overhead）。不得宣稱此值是實際 GPU RAM 量測；Claude 檢查沒有新 asset request、重複貼圖或每幀 allocations。

### 6.4 Required checks and device quality gate

- Codex 執行所有 `AGENTS.md` 指定檢查：`python3 tools/test/syntax_check.py`、`python3 tools/test/i18n_check.py && node tools/test/i18n_check.mjs`、`node tools/test/hud_check.mjs`、`node tools/test/camera_check.mjs <base SHA>`、`node tools/test/traffic_check.mjs`、`node tools/test/collision_check.mjs`、`node tools/test/suburb_check.mjs`、`node tools/test/urban_check.mjs`；另 `node tools/test/route_legality.mjs`、既有 `midtown_facade_pilot_check.mjs` / `midtown_streetscape_quality_check.mjs` 和新 `midtown_art_quality_check.mjs`。如未執行，註明原因，不能推測 PASS。
- Claude 獨立重跑，確保 D-013 main branch protection（需 PR、enforce_admins、禁 force push/delete、rulesets 依現況查核）、CI 在 Claude-owned release/docs PR 接入本新測試並真正執行 PASS；`sw.js` CACHE 由 Claude 更新並確認離線 PWA。任一舊檢查/新測試失敗、console error、asset 404、版本不明 → 不 merge。
- Martin 在 **S26 Ultra 與 Tab S11** 用 `MIDTOWN_W` 進入試點，依 Claude 截圖同位置日夜各觀察一次：兩棟必須一眼可以分辨不同建築身份、窗間牆/層級陰影/一樓基座；既有窗戶/店面與 apron 正常，沒有細節閃爍或大片發白。**ART PASS** 由 Martin 獨立確認，不能由程式測試替代。
- 使用 `?fps=1`，兩裝置各在同畫質路線記錄 **60 秒平均 FPS≥30** 及最近 60 秒最低 1 秒 FPS；記錄裝置、quality、scene、average FPS、low 1s。沒有數據一律記 **device FPS: unmeasured**，不能誤寫 PASS。

## 7. Stop and next-phase decisions

1. **立即停下修 spec 的情況：** G0 找不到兩棟、需更換樓房、原窗/裝飾無法避讓、不得不修改 T-010/T-012 原 batches、需要超過 2 個新增 draw calls、需要動 tone mapping/後處理或新增 collider。不得自行調整基準、降低測試數字、放寬質感標準。
2. **嚴格區分「功能已實作」「技術 PASS」「Martin 美術 PASS」「device-measured FPS PASS」**。其中任何一項不可冒名替代另一項。若 Martin 不滿意美術，即使 CI 綠燈也不應立即大規模推出；依 review 程序請求修正，或停止擴散並重新設計。
3. **後續候選（均未批准）：** T-014 `Exposure/Bloom & Color Grading`，固定日夜鏡頭矯正淺色牆面與車身強光／色彩層次；T-015 `coverage façade rollout`，僅在 T-013 實機 ART PASS 後分街區批次導入，按 §5.2 一段一 PR 並保留各自的 regression/performance gate。名稱/編號屬預留意向，後續以 `TASKS.md` 最新任務編號為準。

## HANDOFF ChatGPT -> Claude

```text
HANDOFF ChatGPT -> Claude
Task: T-013 C+ Midtown Architectural Art-Quality Recovery Pilot v1
Base commit: ed95ead47e8e488d3f1b4fee480da68051829485
Read: COLLAB.md v3.6 §§3,4.3,5; AGENTS.md; TASKS.md;
      DECISIONS D-013/D-027/D-031–D-038; specs/TEMPLATE.md;
      specs/T-010-spec-v1.1.md; specs/T-012-spec-v1.1.md
Context: Martin provided 7877.mp4 (21.7s, 1728x1080). Numerous
         coverage buildings remain flat and repetitive; the more detailed
         historic buildings are visibly better and sunlight washes detail.
         The video does NOT establish that every sampled building belongs
         to T-012's two-building selection: Claude must verify G0 in browser.
Context: This proposal revises only architectural art quality for the
         first two existing T-012 buildings (same actual selected objects).
         Do not expand city coverage or touch global lighting in this PR.
Context: HIGH risk/SMALL volume -> Codex (judgment-heavy facade art).
         <=2 extra InstancedMesh/materials, <=1 generated 256px texture,
         zero new physics. Preserve T-010/T-012 old batches/tests.
Context: New gate: Martin must explicitly ART PASS comparative day/night
         and oblique screenshots; technical test PASS alone is insufficient.
Deliverable: Review full attached spec, inspect selected buildings and
             original glass/decor collision safety (G0), verify the new
             regression test plan, scene reproducibility and physics/draw
             measurements. Propose v1.1 corrections if any G0 fails.
             Register only after Martin explicitly approves T-013 v1;
             do not open a code PR or declare approval now.
SPEC: T-013-spec-v1-DRAFT.md (complete attachment)
```
