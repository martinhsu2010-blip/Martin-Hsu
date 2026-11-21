# T-005 spec v2.1 — World coherence cleanup｜市區空地與街廓變化

**狀態：提案，待 Martin 批准。** 作者：ChatGPT。Implementer: Codex（世界生成、渲染批次與靜態碰撞）。Reviewer: Claude。基準 main：`0cc9aff09338ade85fd78826470053d3e5d68208`。本次比較用 PR #47 修訂前提交：`c8e395f0e3981ad53ecfefce7ebe7c6616db0a2c`。

## 1. 目標與排除範圍

讓殘留市區空地有可辨認的用途，讓新增小樓形成可辨別的天際線，同時修正市區碰撞體造成的物理成本。修訂範圍只有 Part 4。排除交通、郊區配置與上限、地標、飯店區、道路、HUD、鏡頭、經濟、存檔與 CACHE。Claude 所提郊區草帶穿地／浮空仍是 PR #47 的獨立審查項，沿用 Part 3 處理。

## 2. 固定條件

D-019 已登錄 v1。本 v2.1 需 Martin 另行批准。維持單一 renderer、離線 PWA、現有存檔與 S26 Ultra／Tab S11 的 30 FPS 目標。城市擴建的整體 draw-call 預算繼續以基準 main 計算。以下 Part 1–3 逐字保留 v1，歷史任務狀態以 TASKS.md 為準。

## 3. 詳細規格

## T-005A

### Part 1 — Remove the yellow car behind the spawn
Facts (main 4c0d8db): the player starts on foot at (98, 22). `spawnVehicles()` parks "Ferrari GT" (red) at (103, 26) and **"Muscle 69" (yellow, `archetype: 'MUSCLE'`, black stripes, no `model`) at (103, -14)**. A vehicle without `model` gets the Ferrari GLB through `applyFerrariModel`, so the yellow Muscle 69 is the "yellow Ferrari". It is not a Kenney traffic car.
Required:
1. Delete the Muscle 69 entry from the parked list in `spawnVehicles()`. Keep Ferrari GT (103, 26), Apex 4x4 and the VCPD Shelby unchanged.
2. Keep the garage "Muscle '69" button and the `MUSCLE` archetype working (a player can still pick it; do not touch garage, saves, i18n strings or vehicle physics).
3. `WORLD.vehicles` indices shift by one for vehicles after index 1. Audit every use of fixed indices and every name lookup; update `tools/test/traffic_check.mjs` (expects the four-entry list) and any other test that assumes the old order.
4. Report every non-traffic, non-police vehicle within 60 units of (98, 22) before and after, with color and model, so no other yellow/Ferrari-looking car remains near spawn. Do not change anything else you find; list it.
Acceptance: fresh load on PHONE_LOW, TABLET_MED, DESKTOP_HIGH has no yellow car within 60 units of spawn; Ferrari GT is still enterable; saves from the current release load; garage still offers Muscle '69.

### Part 2 — Traffic only on legal roads, then more of it
Facts: traffic follows 10 fixed routes in `ROAD_NET.routes` (R0–R4 grid/coastal loops, 2 ring lanes on the elevated road, north and south loops, 1 suburb loop). `recycleTraffic()` and `findInitialTrafficSlot()` place a car on any route sample, so if a route sample is off the drivable surface, cars appear off-road. Candidate causes (hypothesis): (a) route corners rounded with radius 14 (`roundCorners`) plus lane offsets 4–7 leave the road at turns; (b) R0 joins the straight x=110 line to the coastal ribbon with a different offset (7 vs 4); (c) suburb loop lane offset 3.2 on a road of half-width 6.5, plus a loop built by concatenating two roads; (d) a car shoved or flipped by the player stays wherever it ended up (recovery only fires after 5 s stuck, and only off screen).
Required:
1. **Audit first (report before fixing).** Headless script `tools/test/route_legality.mjs` (new): for every sample of every route, test that the car footprint (use the real Kenney bounds from `traffic_harness.mjs`) lies inside the drivable surface of the road the route belongs to (grid road, ribbon, curved road, elevated ring with its own `y`, terrain road, intersection) with >= 1.0 unit margin, and that `p.y` matches the deck/terrain the car is placed on. Print violations per route with coordinates. Commit the script; it must pass at the end.
2. Fix the routes (and only the routes) so the audit has 0 violations. Do not widen roads or move any building to hide a bad route.
3. Placement guard: `findInitialTrafficSlot()` and `recycleTraffic()` must reject a slot that fails the same legality check (cheap, precomputed per route sample at init, no per-frame cost).
4. Drift guard: an AI car whose center is more than 8 units from its route polyline for more than 2 s is flagged `trafficRecovery` exactly like a stuck car (same distance/visibility/clearance gates as today; still never teleports on screen). Add `offRoute` to `__VH.trafficDiagnostics()`.
5. **More traffic** (this is what Martin asked for; legality comes first). New `DENSITY.traffic` values, proposed:

| Preset | now | proposed |
|---|---|---|
| PHONE_LOW | 18 | 22 |
| PHONE_MED | 24 | 30 |
| TABLET_LOW | 22 | 28 |
| TABLET_MED | 32 | 40 |
| TABLET_HIGH | 36 | 46 |
| DESKTOP_MED | 40 | 50 |
| DESKTOP_HIGH | 52 | 64 |
| DESKTOP_ULTRA | 68 | 80 |
| IGPU_LOW | 20 | 24 |
| IGPU_MED | 28 | 34 |
| IGPU_HIGH | 36 | 44 |

   Allowed: up to 3 new legal routes (for example Maple Ave and Valley Loop, which have no traffic today), spacing and rules unchanged (20 units between cars, 25 from the player's car, recycle rules unchanged, ordinary AI stays Kenney-only, 0 Ferrari).
   Performance guard (reviewer-set, adjust only with Claude's approval): report `renderer.info.render.calls` on PHONE_LOW / TABLET_MED / DESKTOP_HIGH before/after in a real browser if one works (otherwise a clearly labelled structural count), and physics step time from `tools/test/traffic_audit.mjs`. If a preset adds more than 12 draw calls or its physics step grows more than 25 %, keep that preset's old count and say so; do not trade away frame rate.
6. Existing tests stay green: `traffic_check.mjs` (update its expected table), `collision_check.mjs`, `i18n_check.mjs`, `syntax_check.py`; offline start unaffected.
Acceptance: `route_legality.mjs` 0 violations; 10-minute headless run per preset (cars only, no player) shows 0 cars beyond 8 units from their route and `offRoute` 0 at the end; counts equal the table (or the per-preset exception above); Martin drives the main loops and the suburb on S26 Ultra and Tab S11 and sees no car off the road surface.

Out of scope for T-005A: buildings, trees, suburbs, camera, HUD, Hub, economy, saves, police, NPC pedestrians.

---
## T-005B (written now so ChatGPT and Martin see the whole plan; Codex starts it only after T-005A is Done)

### Part 3 — Suburb houses face the road, no bare strip in front
Facts: `buildSuburbParcels()` offers each road side two setbacks (12 and 28 from the road edge). Candidates of all setbacks are shuffled by a golden-ratio stride (`h.order`) before the quotas are filled, so a house on the 28-unit row can be chosen while the 12-unit parcel in front of it stays empty (hypothesis for "lots of bare ground between road and houses"). The old `buildSuburbs()` pass also seeds trees with a fixed 12-unit offset.
Required:
1. **Audit first:** per suburban road (Suburb Main, Maple Ave, Hillcrest Loop, Valley Loop) and side, list the continuous road-edge runs with no structure within 14 units of the road edge, why (slope > 3.5, junction, depot/fast-travel/protected clearance, tree, shuffled-away, cap) and the total/maximum run. Report for PHONE_LOW and DESKTOP_HIGH.
2. Fill order: a second-row parcel (setback 28) may only be used if the first-row parcel in front of it along the same road is already used or illegal. Front face of a first-row house should sit 6–12 units from the road edge (compute the setback from the house depth instead of a constant).
3. Remaining bare frontage: add a cheap roadside verge (sidewalk/lawn strip, merged or instanced, no per-house meshes) along suburban roads so the ground between road edge and house front reads as a yard, not raw terrain. Draw-call limit for this part: +4 on PHONE_LOW, +8 on DESKTOP_HIGH.
4. Counts: placed houses must not drop below the T-004D result. The caps (210 phone / 390 desktop) and the Option B shares stay. If the audit shows the cap itself is what leaves frontage bare, report it and propose a new cap; do not raise it silently (that is a Martin decision).
5. Keep every T-004D collider rule (collider from the base bottom to the wall top, <= 16 shapes per body, `WORLD.suburbHouses` for the map) and the tree-trunk clearance rule.
Acceptance: after the fix, max bare frontage run <= 45 units on roads where terrain is legal, down from the reported audit; screenshots from the same camera positions as Martin's.

### Part 4 — 市區剩餘空地、建築變化與物理成本

#### 4.1 凍結基線與保護規則

| PR #47 修訂前，各欄依 CBD／Midtown／Old Town 排列 | PHONE_LOW | DESKTOP_HIGH |
|---|---|---|
| 實際建築棟數 | 225／327／276 | 186／296／204 |
| HARD_EMPTY，通過硬規則、沒有樓的 10×10 中心 | 17／101／27 | 27／101／43 |
| CAN_ADD，能再放入 10×10 或 8×8 樓的中心 | 0／0／0 | 0／0／0 |
| 另計：連續道路幾何檢查排除的中心總數 | 61 | 55 |

145／171 是重疊取樣中心數。審計固定沿用 v1 的街區、2 單位格距、格網原點、10×10 軸對齊矩形和全寬道路幾何。維持立面包絡間距 ≥2；道路邊緣與高架至少 3，既有較嚴的曲線道路 3.5、樹幹與樹帶、路口、任務與傳送點、中央廣場、車庫、跑道與特技起降通道排除條件照舊。以下所有方案均須遵守；地表鋪面也算實際占地。

#### 4.2 三個選項與建議

| 選項 | 具體做法 | 相對 PR #47 的繪製與物理成本 | 判斷 |
|---|---|---|---|
| A 小樓 | 在餘地依序試 8×6、6×8、6×6，中心按 1 單位掃描，仍保留 2 單位間距 | 沿用 shell／立面批次，設計預算 +0 draw；每棟 +1 靜態 Box，併入每組 ≤16 shapes 的剛體，新組 +1 body | 現有 CAN_ADD 沒驗證這三種尺寸；仍可能有狹縫，也會增加碰撞成本 |
| **B 街角小公園（建議採用）** | 保留所有建築，用貼地草坪與淺色步道補足剩餘空地 | 每預設全市共用 1 個不投影的不透明批次，每視角最多 +1 draw；+0 body、+0 shape、每幀 +0 物理更新 | 給空地用途，不增加小樓數，手機目前最差 +7，尚有 1 次餘額 |
| C 只改驗收 | 將 CAN_ADD=0 當作唯一結案條件 | +0 draw、+0 body、+0 shape | 畫面照舊，145／171 個中心仍無用途，與 Martin 的要求不符 |

**提交批准的規格採 B。** A、C 僅供決策比較。B 的通過條件是實際新增地表用途；禁止只改分類、計數器或地圖標籤。

#### 4.3 小公園幾何與覆蓋率

1. 在放完既有樓後，依區將所有 HARD_EMPTY 的 10×10 矩形取聯集，裁掉全部硬排除範圍與既有可見建築占地。相鄰跨街區面也要去重；保護區不得鋪草。保留原始中心清單與排除原因供比對。
2. 將合法區域三角化為水平、可步行的草坪，草色 `#71865B`，內嵌寬 1.2 的步道色 `#B9AE94`。沿每片連通區較長軸通過面積重心，等長時選世界 X 軸；裁切步道到同一區域。步道取代相應草坪面，禁止共面雙層。每個連通區都要有兩種顏色。地面高度取實際可見地表 +0.03 單位。小公園材質另須啟用 `polygonOffset: true`、`polygonOffsetFactor: -2`、`polygonOffsetUnits: -4`（沿用道路材質的深度偏移做法），以避免遠景深度閃爍；不可只靠 +0.03 高度偏移。兩種顏色共用頂點色、單一材質、單一合批 Mesh；所有畫質均顯示。
3. 逐個 10×10 矩形，以實際提交 renderer 的三角形投影聯集計算面積。**中心須落在公園面內或邊界，且矩形內至少 80.0／100.0 平方單位被合法公園面覆蓋**；兩者都成立才算有用途。重疊面積只計一次。未達門檻列出位置和面積，驗收失敗。公園不登錄建築、屋頂、鏡頭阻擋物或碰撞體；實際棟數及既有樓的 X/Z、朝向與占地保持基線值。

#### 4.4 新增小樓的高度與色彩

僅套用於 T-005B 的 coverage shell（手機 758 棟、桌機 538 棟）。高度從立面基底到屋頂，單位與世界座標一致。每區 4 個高度、5 個 sRGB 色值。

| 區域 | 高度集合 | 色盤（依索引 0–4） |
|---|---|---|
| CBD | 12、16、20、24 | `#CBD3D6`、`#AABBC3`、`#BBC1CA`、`#D4CBC0`、`#BAC7BD` |
| Midtown | 12、17、22、27 | `#D8C5AA`、`#BFADA1`、`#B5BEA9`、`#B0C0C5`、`#D5B6A4` |
| Old Town | 9、12、15、18 | `#C58D79`、`#D4B691`、`#BDAB91`、`#ACB59C`、`#C1A19A` |

固定預設 seed=5019。每區獨立，對 UTF-8 字串 `seed|district|x|z|width|depth` 計算無號 32-bit FNV-1a（起值 2166136261，每 byte 先 XOR 再乘 16777619，取低 32 bits）。區碼 CBD、MID、OLD；整數以十進位無前導零表示。按 hash 升序排列，同值按 x、z、width、depth 升序。零起算名次 i 取高度索引 `i % 4`、色索引 `(floor(i/4) + i%4) % 5`。每 20 棟遍歷 20 種組合一次；不使用全域 RNG、載入順序或時間。

沿用現有 InstancedMesh、材質與批次。以 instance Y scale 和置中平移令底部固定、屋頂到達指定高度，透過 setColorAt 設定顏色（sRGB 轉線性一次）。門窗與立面元素須依新高度 `H` 重新計算，不得依舊高度的比例縮放垂直位置：窗戶樓層數為 `floor((H-6)/4.6)`，樓層索引 `floor=0…n-1` 的窗戶中心 Y 相對基底為 `6.2 + floor*4.6`；門依基底高度定位、屋頂位於 `baseY+H`，維持立面 offset 0.06。`H=9` 時 `n=0`，不得強制塞入不合法窗戶。靜態 Box 從基底至新高度，半高 H/2、中心 baseY+H/2，正確換算複合體局部座標。可見殼與碰撞框在三軸各面的最大絕對偏差 ≤0.35。高度／顏色變化本身預算 **+0 draw、+0 材質、+0 body、+0 shape**。

#### 4.5 物理與繪製預算

coverageColliders 優先採 120×120 世界格分組（兩軸皆用 floor），同格超過 16 shapes 時才拆下一組，每棟仍有獨立靜態 Box。可採等效分組，但必須通過相同撞擊與效能門檻。

以同一 revision 的 urban_check 固定場景與既有 `headlessStep.before/after` 工作負載配對比較。相同 Node、機器、預設與暖機／取樣長度，獨占執行，交替順序做 5 對，列出每對 before、after、比值與 p95。**兩預設各自的 5 個 median 比值之中位數 ≤1.35**。此為相對改動前的 +35% 硬上限；禁止以已退化的 40 格版本當分母。Claude 的 120 格實驗為手機 0.18→0.23 ms（+27.8%），桌機 0.41→0.53 ms（+29.3%）。若分母恰為 0.18、0.41，對應上限為 0.243、0.5535 ms；以未四捨五入值判定。

Chromium 同機位同畫質比較完整場景的 renderer.info.render.calls：相對 main，市區每視角 PHONE_LOW ≤+8、DESKTOP_HIGH ≤+16；相對 c8e395f，小公園最多 +1。另在同一候選版靜止場景切換統一高度／顏色與變化版，逐視角驗證變化本身 +0。沿用 Ocean Drive、Midtown、Old Town 三機位，再各選一處可見殘留公園的機位；保存座標、朝向、時間和前後截圖。畫面需含實際公園，不得為達預算關閉圖層。

## 4. 任務順序

| ID | 負責人與相依 | 交付與通過條件 |
|---|---|---|
| T-005A | 已完成 | 保留 Parts 1–2 |
| T-005B | Codex；待 Martin 批准 v2.1、Claude 登錄 | 延續同一個 PR #47。先鎖定兩預設基準，再實作公園、外觀、碰撞分組，依第 5 節交付結果。Claude 複審；Martin 實機驗收。 |

## 5. 驗證計畫

**驗證等級：designed。** c8e395f 的基線及分組實驗屬 Claude 獨立 headless 證據；v2.1 尚無實作或裝置量測。

- 擴充 `tools/test/coverage_audit.mjs --details`。PHONE_LOW／DESKTOP_HIGH 逐區輸出 BUILDINGS、HARD_EMPTY、CAN_ADD、ROAD_EXCLUDED、PARK_COVERED、UNTREATED、HARD_OVERLAP；提供每個原始中心的座標、交集面積與對應公園。逐座標比對 c8e395f（不可刪點或移格）。棟數、HARD_EMPTY 和排除數須吻合 4.1；CAN_ADD=0，PARK_COVERED 分別為 17/101/27、27/101/43，**各區 UNTREATED=0、HARD_OVERLAP=0**。缺公園、遮罩隱藏、用標籤取代幾何或違反任一門檻均退出非零。
- 同一 audit 從 instance matrix、instanceColor、屋頂與 Cannon shape 讀回結果，比對 4.4。逐區輸出高度／色彩直方圖，所有 20 種組合須出現，各組棟數最多相差 1。同 seed 5019 建兩次並打亂輸入順序，依座標比對完全一致；公園新增 body/shape 均為 0。
- 執行 AGENTS.md 全套回歸、route_legality、urban_check、collision_check；保留 20/60/120 km/h 雙方向全棟撞擊、零穿透。報告物理數據、全場 draw calls 與截圖。將一片公園從稽核輸入移除時，至少一個相應中心必須報錯。
- **實機 FPS 診斷工具（T-005B 必要）：** `index.html` 僅於網址查詢參數精確為 `?fps=1`（或其他查詢參數並存時 `fps=1`）時啟用一個不遮擋操作鍵、地圖與任務提示的小型唯讀讀數，顯示「目前平均 FPS」、「最近 60 秒內最低 1 秒 FPS」、「目前畫質預設」。以 `requestAnimationFrame` 實際渲染幀計數，逐個完整 1 秒區間統計 FPS；目前平均取最近最多 60 個完整 1 秒區間的總幀數／總秒數，最低值取相同 60 秒窗口內的最小 1 秒 FPS。尚不足 1 秒時以 `—` 表示，背景分頁／頁面隱藏期間不計入且恢復時重新開始窗口。畫面讀數每秒最多更新一次，禁止額外 WebGL pass 或 renderer。`fps=1` 啟用期間須停用現有自動降畫質／自動降低 resolution scale 的機制，維持當下手動選擇的畫質預設與倍率供公平比較；手動切換仍照原功能執行，但診斷工具本身不得寫入 `vh_save` 或新增持久化欄位。沒有 `fps=1` 時，診斷工具不顯示、不啟動逐幀計數、不改自動降畫質邏輯，既有畫面、操作、畫質及存檔行為完全不變，新增 WebGL draw call 必須為 **0**。此工具僅供量測，不屬於日常 HUD 改版。
- **FPS 工具驗收：** PHONE_LOW 與 TABLET_MED 分別測試有／無 `fps=1` 的同一場景：啟用時三個欄位可讀，切換畫質後預設欄位同步；累積 60 秒後顯示的最低 1 秒 FPS 對得上逐秒原始計數，滾動窗口不含更早數值；啟用期間以模擬掉幀觸發自動降畫質條件時，畫質預設及 resolution scale 不得自動降低。移除參數重新載入後，讀數完全消失、自動調降機制恢復原狀、無新增存檔寫入；以 `renderer.info.render.calls` 比對相同場景，新工具造成 +0 draw call。保留工具開／關截圖及統計記錄。
- **小公園深度閃爍驗收：** 查核小公園共用材質的 `polygonOffset=true`、`factor=-2`、`units=-4`，且地表高度仍為可見地表 +0.03；PHONE_LOW 遠景截圖至少包含一處完整小公園，從兩個相近機位各擷取一張，草坪／步道表面沒有深度競爭造成的條紋、破面或閃爍。不得以隱藏公園或關閉某個畫質的公園通過。
- **門窗驗收：** 由 instance 的實際高度 `H` 讀回每棟樓的窗戶樓層數，必須等於 `floor((H-6)/4.6)`；各樓層窗戶中心相對基底 Y 須為 `6.2 + floor*4.6`（允差 0.01 單位），門依基底定位、屋頂與 `baseY+H` 一致；不可對舊窗戶 Y 做比例縮放。檢查 CBD、Midtown、Old Town 所有高度組合，包含 `H=9` 無窗戶樓層的情況。
- Martin 在 S26 Ultra／PHONE_LOW 與 Tab S11／TABLET_MED 用含 `fps=1` 的網址，於相同日間路線巡覽三區，每區 60 秒；紀錄讀數顯示的目前平均 FPS、最近 60 秒內最低 1 秒 FPS、預設與截圖。每區平均 ≥30 FPS，Tab S11 並須確認小樓高矮／色差可辨、原空地有明確用途且無閃爍或穿模。headless 結果不可代替實機驗收。

## 6. 風險與待決事項

Martin 需要決定是否接受以**可見、可稽核的小公園**完成剩餘空地，而保留原建築空地診斷。80% 面積門檻、+35% 物理上限與三區色盤均為本次提案。若合法裁切後面積不足、全場預算超限或實機觀感不合格，保留失敗記錄，由 Martin 決定是否另修規格。D-019 既有事件保持原文；Claude 僅在 Martin 明確批准後追加 v2.1 事件。

依據：[v1 原文](https://github.com/martinhsu2010-blip/Martin-Hsu/blob/0cc9aff09338ade85fd78826470053d3e5d68208/specs/T-005-spec-v1.md) · [Claude 對 PR #47 的審查與實驗](https://github.com/martinhsu2010-blip/Martin-Hsu/pull/47#issuecomment-7054236978)

```
HANDOFF ChatGPT -> Claude
Task: T-005B / T-005 spec v2.1   Base commit: 0cc9aff09338ade85fd78826470053d3e5d68208   Read: COLLAB.md v3.4, DECISIONS D-019, TASKS T-005B
Context: PR #47 at c8e395f has 145/171 hard-clear residual centers and CAN_ADD=0; Martin rejected the visual shortfall.
Context: Proposed amendment adds FPS diagnostics gated by fps=1, park polygonOffset, and height-recomputed windows; visible parks, deterministic shell variety and the +35% physics budget remain. Parts 1–3 are verbatim.
Context: Proposed only. Keep PR #47 open and its one-code-PR lock in place.
Deliverable: review spec, then (after Martin approves) register it and unlock the T-005B revision in PR #47 for Codex.
SPEC: full text above as T-005-spec-v2.1.md
```