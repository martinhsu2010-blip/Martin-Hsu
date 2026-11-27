# WE-01 — World Expansion Survey Specification v1.2 (registered text)

> **Registered by Claude 2026-11-27 (D-051).** Approved by Martin ("批准", 2026-11-27 11:24) for **WE-01A only** (T-016A); WE-01B (T-016B) is sequential and needs its own G0 and approval (spec §9, §17.3). The ChatGPT text below is unchanged; the **Claude G0 conditions C1-C6 in this box are binding and win on any conflict.**

## Claude G0 conditions (binding)

**C1 - static physical source.** In addition to the §4.1 sources, `physicsWorld.bodies` filtered to `mass === 0` (cannon STATIC) is an allowed static physical-occupancy source (`source_group = "PHYSICS_STATIC"`, `category = "COLLIDER"` unless a better category is known), cross-checked against the WORLD lists. Evidence (Claude, BASE 84319439, PHONE_LOW, 3 unseeded loads): 573 bodies = 495 static (identical in all 3 loads) + 78 dynamic (cylinders/boxes with mass 1..1200; positions differ by about 0.1 m from physics settling, not randomness). Dynamic (`mass !== 0`) bodies stay excluded from every static dump and fingerprint (§4.2). Spec §4.3 "source unidentified" is resolved by this evidence.

**C2 - ROAD_CORRIDOR extent.** `ROAD_CORRIDOR` height grids (1 m step) cover the union of a +/-60 m band around each candidate route's control polyline (C01, C02, H01, H02, X01, U01), cut into rectangles per route. Candidate curves leaving a corridor are `UNVERIFIED` for that part; no re-sampling pass exists (§4.5). Existing-road footprints come from `ROAD_NET` (avenues/cross streets/ribbons/roundabouts/hillRoad/terrainRoads/suburbRoads/ring/spurs, with `avenueZ`/`avenueHalf` etc.); Claude converts them to polygons in the dump, Gemini never re-implements road generation. Note (corrected 2026-11-27, D-051a): `ROAD_NET.avenueZ = 892` is the north-south length of the avenues (z from -892 to 892; the two western avenues stop at `hillAveZ = 300`), not an east-west road. The existing city grid (avenues x=-600/-420/-240/-120/0/110, cross streets) lies inside the B3 survey area, its east/south-east part reaches the B1 buffer (avenues x=0 and x=110, cross street z=880) and nothing of it enters the B2 survey area.

**C3 - fingerprint contract (JS = Python).**
1. Fingerprint input F is built from the dump *without* `metadata` (except `source_counts`), `issues`, any `source_ref`, `seed`, `generated_at` and the `static_fingerprint` field itself. Included: `world.physical_ground` (bounds, top_y), `world.terrain_regions`, `world.water_regions`, `world.beach_regions`, `regions`, `height_grids`, `footprints`, `roads`, `metadata.source_counts`, `completeness`.
2. Every metric number (coordinates, heights, widths, margins, steps, y_min/y_max, polygon/bounds/centerline values) becomes an integer in millimetres: `floor(x * 1000 + 0.5)` (same in JS `Math.floor` and Python `math.floor`; no banker's rounding). `nx`, `nz` and `source_counts` values are already integers and stay as they are. Booleans, strings and `null` stay.
3. Lists whose items have an `id` are sorted by `id` (ASCII code-point order; all ids and enum strings must be ASCII). All other arrays keep dump order (polygon vertex order is data).
4. Canonical JSON: object keys sorted, no whitespace, separators `,` and `:`. With integer-only numbers and ASCII strings, Python `json.dumps(F, sort_keys=True, separators=(",", ":"))` and the JS canonical stringify are byte-identical.
5. `static_fingerprint` = lowercase hex SHA-256 of the UTF-8 bytes. Dumps store metric values already rounded to 0.001 m. The analyzer recomputes and rejects any mismatch (test A17). Full-file SHA-256 is recorded separately.

**C4 - footprint precision map.** Rotated Box and ConvexPolyhedron: horizontal convex hull polygon -> `EXACT_OUTLINE`. Cylinder, Sphere, Trimesh and any scene `Box3` -> `CONSERVATIVE_AABB`. `WORLD.buildings` (minX/maxX/minZ/maxZ) -> `EXACT_OUTLINE` only if Claude verifies the mesh matches; otherwise `CONSERVATIVE_AABB`. `suburbHouses` (x, z, hx, hz, rot) -> oriented rectangle, `EXACT_OUTLINE`. `cityInfill` (x, z, w, d) -> `EXACT_OUTLINE`. `TREE_COLLIDERS` -> `CONSERVATIVE_AABB`.

**C5 - size.** WE-01A target stays 800 lines (analyzer + check, combined); pre-approved ceiling 1,000 lines. WE-01B ceiling stays 1,000 unless Claude approves more at its own G0.

**C6 - sample dump for Gemini.** Before Gemini starts, Claude commits a trimmed, schema-valid real sample dump (real footprints/roads/terrain, cropped grids, still passing validation incl. its own `static_fingerprint`) to the Claude-owned path `tools/fixtures/we01/` (outside Gemini's allowlist, read-only for Gemini), plus the exact field-by-field schema notes. Full dumps remain Claude-held artifacts (spec §12.5).

**Task IDs.** WE-01A = T-016A, WE-01B = T-016B (T-015 stays reserved for the lighting draft).

---

WE-01 — World Expansion Survey Specification v1.2

0. Task metadata

- Project: VICE HORIZON VI
- Repository: martinhsu2010-blip/Martin-Hsu
- Parent task: WE-01
- Subtasks: WE-01A, WE-01B
- Version: v1.2
- Status: DRAFT FOR CLAUDE G0 (v1.2)
- Previous G0 verdict: APPROVE WITH CHANGES
- BASE: 84319439243b51aa8d119e33eb62a0637feea887
- Game release: vh-2026-11-27-02
- Spec author: ChatGPT
- Analyzer implementer: Gemini Stage 3
- Runtime data provider: Claude
- Reviewer / Maintainer: Claude
- Risk: LOW — isolated read-only analysis
- Priority: P1
- Registration authorization: NONE
- Implementation authorization: NONE

本規格完整取代 WE-01 v1.1。

使用者已選定三區住宅開發、策略 C（品質與規模並重）、D3（內部填補＋外部擴建），以及 Gemini 作為審計工具實作者。

遵守 COLLAB v3.6、AGENTS.md 及現行 DECISIONS.md。

D-050 與 D-050a 的效能及暫定美術接受不構成住宅開發或全面美術套用授權。

0.1 Revision history

v1.2 incorporates all five Claude G0 re-review corrections:

1. 以單階段1 m runtime terrain dump 取代兩階段地形取樣。
2. 修正世界物理地面支撐及 terrain region 的定義。
3. 僅使用靜態世界資料，透過連續兩次 dump fingerprint 驗證確定性。
4. 保留 PHONE_LOW 與 DESKTOP_HIGH 雙畫質分析，採保守容量。
5. 每個 footprint 明確標記 EXACT_OUTLINE 或 CONSERVATIVE_AABB。

保留 v1.1 已接受的內容：

- WE-01A / WE-01B 任務拆分。
- JSON schema version 1。
- WE-01A ≤800行。
- WE-01B ≤1,000行。
- Occupancy prefix sums。
- 25 ha、40棟及60棟可行性標準。
- 住宅土地比例僅供參考。
- Mutation test IDs M-A01 至 M-B12。
- Gemini 僅執行快速分析器測試。
- Claude 負責正式 runtime 資料及重量級驗證。

與已移除的 Pass 2 流程相關測試，改為單階段1 m 資料驗證的等效測試，不降低測試要求。

---

1. Goal and non-goals

1.1 Goal

建立由正式遊戲 runtime 資料支持、可重現的世界審計流程，評估未來三區住宅擴建的土地、容量、道路及效能條件。

WE-01 必須回答：

- 現有世界有哪些可直接使用的土地？
- 哪些土地需要新增地形、道路或建築更新？
- 三區原始候選位置應如何調整？
- 25 ha 規劃面積是否可行？
- 40棟最低容量及60棟理想容量是否可行？
- 三區是否能與既有道路連通？
- 後續開發需要哪些獨立工程？
- 現有世界效能基準為何？

1.2 Non-goals

WE-01 不得：

- 建造住宅。
- 修改地形、海岸線或水域。
- 新增、移除或修改正式道路。
- 修改交通 AI、物理、碰撞或車輛系統。
- 修改材質、貼圖、LOD、陰影或渲染器。
- 修改快速傳送、地圖 UI、任務或存檔系統。
- 修改 Site A。
- 修改正式遊戲初始化流程。
- 新增 production debug hooks。
- 修改 Math.random 或正式世界生成邏輯。
- 引入外部遊戲素材。
- 自動批准後續住宅建設。

---

2. Architecture and responsibility split

2.1 Data flow

Production game at BASE

→ Claude runtime extraction in headless Chrome

→ Single-stage static world dump at PHONE_LOW

→ Single-stage static world dump at DESKTOP_HIGH

→ Static fingerprint verification

→ WE-01A land analyzer

→ WE-01B capacity and road analyzer

→ Claude verification

→ Final feasibility report

不存在 Pass 2、sampling request 或選定地塊後重新取樣的必要工作流程。

每種 preset 的正式 dump 一次包含完整審計所需的1 m 候選區地形資料。

2.2 Claude responsibilities

Claude 負責：

- 從 BASE 啟動正式遊戲。
- 使用既有 window.__VH 暴露介面。
- 取得靜態世界資料。
- 生成兩種 preset 的完整 dumps。
- 驗證各 preset 連續兩次靜態 fingerprint 一致。
- 驗證 dump schema 及資料完整性。
- 比較兩種畫質的世界占地差異。
- 驗證正式1 m 地形取樣。
- 執行 analyzer 於正式 dumps。
- 完成效能基準及既有回歸測試。
- 審查最終可行性裁定。

Claude 使用外部或隔離審計腳本，不得修改 production。

2.3 Gemini responsibilities

Gemini 僅負責：

- 讀取符合 schema 的 JSON dumps。
- 驗證資料結構及來源資訊。
- 土地分類。
- 面積統計及守恆檢查。
- 畫質差異分析。
- 地塊配置及容量分析。
- 道路幾何及連通性分析。
- 可行性裁定。
- SVG、CSV、JSON 及 Markdown 報告。
- 小型 synthetic fixtures。
- 快速單元測試及 mutation tests。
- 完成快速檢查後立即推送工作分支並開啟 PR。

Gemini 不負責 production runtime 擷取。

Gemini 不得重新實作 terrainHeight()、buildTerrainRoad() 或正式世界生成器。

2.4 Prohibited Gemini execution

Gemini VM 不得執行：

- 完整 Playwright。
- 完整 Chromium 遊戲初始化。
- Headless WebGL。
- SwiftShader 重量級測試。
- 完整 Three.js 世界建構。
- 完整 cannon-es 世界建構。
- 長時間物理效能測試。
- 完整遊戲截圖測試。

上述驗證由 Claude 執行。

2.5 Production integrity

正式遊戲檔案必須與 BASE byte-identical。

若必要資料無法透過現有 runtime 介面取得，應標記 UNKNOWN 或 LX。

不得為取得資料而自行修改正式遊戲。

---

3. Survey boundaries

3.1 Initial candidate regions

所有座標使用遊戲世界 X/Z 公尺座標。

Region| Name| X range| Z range| Gross area
B1| Oceanfront Heights| 90 to 390| 930 to 1230| 90,000 m²
B2| Vista Hills| -900 to -500| 820 to 1070| 100,000 m²
B3| Palmwood Quarter| -640 to -340| -810 to -610| 60,000 m²

初始矩形面積合計250,000 m²，即25 ha。

B1、B2、B3 為住宅分區代碼，與 T-014B1、T-014B2、T-014B3 無關。

3.2 Survey buffers

各區向外增加100 m 搜尋緩衝帶，用於：

- 尋找替代住宅地塊。
- 調整候選區多邊形。
- 尋找既有道路接點。
- 評估未來道路走廊。

緩衝帶不得自動計入25 ha 目標。

如需使用緩衝帶土地，必須提供修訂後多邊形、聯集面積及調整原因。

3.3 Verified geographic and physical constraints

以下為 Claude G0 及 G0 re-review 已確認的 production facts。

Global physical ground

正式物理地面為：

CANNON.Box(2400, 0.5, 2400)

Body position Y = -0.5。

上述尺寸為 half-extents。

因此物理地面：

- X 範圍：-2400 至2400。
- Z 範圍：-2400 至2400。
- 頂部高度：Y=0。
- 水平尺寸：4800 × 4800 m。

此物理地面涵蓋目前三區候選範圍及其100 m 緩衝帶。

車輛在這些區域具有平坦物理地面支撐。

只有 ROAD_NET.hill、ROAD_NET.suburb 等既有 terrainRegions 及其20 m margin 具有對應的地形高度及 supportOnTerrain() 行為。

必須區分：

1. 平坦物理地面支撐。
2. 地形區域及非平坦高度。
3. 視覺地面範圍。
4. 實際可遊玩範圍。
5. 水域及土地開發限制。

平坦物理支撐不代表水域可以直接開發，也不代表所有區域均具備完整道路或視覺地形。

B1 — Oceanfront Heights

海灘平面 X 範圍為225至465，Z 延伸至1100。

B1 與海灘平面重疊：

- X：225至390。
- Z：930至1100。
- 面積：28,050 m²。

海洋平面從 X=380 開始。

B1 與海洋平面重疊約3,000 m²。

海灘與海洋平面重疊約1,700 m²。

兩者聯集約29,350 m²。

海灘與水域不得重複扣除。

B1 具有平坦物理地面支撐，但海灘及水域仍須依土地用途限制分類。

Claude re-review 的初始高度取樣顯示 B1 為0 m。

B2 — Vista Hills

現有山區 terrain region 的 Z 範圍為310至810。

B2 的 Z 範圍為820至1070。

B2 原始矩形位於 hill terrain region 核心範圍之外。

考慮20 m terrain margin 時，必須使用正式 runtime 資料判定邊緣區域，不得直接假定整個矩形均不受 margin 影響。

Claude re-review 的初始高度取樣顯示 B2 為0 m。

因此：

- B2 具有平坦物理地面支撐。
- B2 目前不是現成的山坡住宅區。
- 不需要為一般平地車輛支撐新增物理地面。
- 若維持山坡別墅及景觀道路設計，仍需要獨立地形開發工程。
- 山區住宅設計目標可能為 CONDITIONAL，但原因是缺少山區地形，而非缺少平坦物理地面。

B3 — Palmwood Quarter

Site A 原始範圍：

X = [-551,-451]。

Z = [-821,-763]。

加入10 m 保護緩衝帶：

X = [-561,-441]。

Z = [-831,-753]。

B3 與保護區重疊：

- X：-561至-441。
- Z：-810至-753。
- 面積：6,840 m²。

B3 位於既有 suburb terrain region 核心範圍之外，其東側邊界為 X=-650。

應依正式 runtime 資料處理20 m margin。

Claude re-review 的初始高度取樣顯示 B3 為0 m。

B3 具有平坦物理地面支撐。

不得將其分類為缺少物理地面的區域。

Overall conclusion

原始三個矩形雖然合計25 ha，但無法直接提供25 ha 已確認有效規劃土地。

主要原因包括：

- B1 海灘及水域限制。
- B3 Site A 保護區。
- B2 山區地形設計需求。
- 既有占地及道路限制。

修訂候選區多邊形是預期必要成果。

不得透過移除保護區、忽略水域或假設尚未建造的地形來宣稱原始矩形已符合25 ha。

---

4. Runtime data acquisition

4.1 Authoritative static sources

Claude 使用既有 window.__VH 介面及正式靜態世界資料：

- __th：正式 terrainHeight() 取樣入口。
- WORLD.buildings。
- WORLD.cityInfill。
- WORLD.suburbHouses。
- 其他已確認為靜態的 WORLD lists。
- ROAD_NET。
- TREES。
- TREE_COLLIDERS。

實際欄位名稱以 BASE 暴露結構為準。

可使用與上述靜態物件具有明確對應關係的 scene Box3，補充其視覺占地。

不得無差別遍歷整個 scene，將動態物件當作靜態占地。

4.2 Excluded dynamic sources

不得將全部 physicsWorld.bodies 直接用於靜態世界 dump。

不得將以下動態資料納入靜態占地 fingerprint：

- 玩家位置。
- 動態車輛。
- 交通車輛。
- 任務動態物件。
- 動態物理 body 位置。
- 動畫狀態。
- 即時攝影機狀態。
- 其他尚未證明為靜態的物件。

physicsWorld 可由 Claude 用於獨立效能及物理驗證，但不得成為完整靜態占地資料的無差別來源。

若某項必要靜態 collider 無法從允許的靜態來源可靠識別，應標記相關資料缺口。

4.3 Runtime determinism evidence

Claude 已執行三次未設定 seed 的 PHONE_LOW 載入測試。

已確認：

- WORLD.buildings fingerprint 三次一致。
- WORLD.suburbHouses fingerprint 三次一致。
- TREES fingerprint 三次一致。
- Physics body count 三次均為573。
- 全部 physicsWorld.bodies 的位置 fingerprint 在三次載入中有一次不同。
- 造成動態差異的具體來源尚未確認。

因此：

- 不需要 Math.random seeding。
- 不修改 production 隨機數行為。
- 靜態世界確定性與動態物理確定性分開處理。
- 不得因動態 body 位置變化而否定已驗證的靜態世界資料。
- 573 為 Claude 此次 PHONE_LOW 測試觀察值，不是所有場景及 preset 的固定驗收常數。

4.4 Consecutive dump requirement

每個 preset 必須進行至少兩次獨立、連續的正式世界載入及靜態 dump。

兩次 dump 的靜態 fingerprint 必須一致。

不是只在同一個已初始化世界重複讀取同一份資料。

需要驗證：

- PHONE_LOW dump A。
- PHONE_LOW dump B。
- DESKTOP_HIGH dump A。
- DESKTOP_HIGH dump B。

PHONE_LOW A/B fingerprint 必須一致。

DESKTOP_HIGH A/B fingerprint 必須一致。

不同 preset 之間不要求 fingerprint 一致。

若同一 preset 連續兩次 fingerprint 不一致：

1. 停止該 preset 正式資料驗收。
2. 查明不一致欄位。
3. 確認是否錯誤納入動態物件。
4. 修正擷取來源或資料正規化。
5. 重新取得兩次獨立 dump。

不得為取得一致結果而修改正式遊戲。

不得排除真正影響靜態土地占用的差異。

4.5 Single-stage terrain dump

移除 v1.1 的 Pass 1 / Pass 2 流程。

每份正式 dump 包含：

- 全世界20 m 粗略高度網格。
- B1、B2、B3 及其100 m 緩衝帶的完整1 m 高度網格。
- 所有必要靜態 footprint。
- 道路及地形區域資料。
- 物理地面支撐資料。
- 資料完整性及來源標記。

Claude G0 re-review 已測得：

window.__VH.__th 取樣90,000個點約需2 ms。

此數值為高度函式取樣觀察值，不代表完整 JSON 建構、序列化或檔案輸出的總耗時。

因此採用完整1 m 網格，而非先5 m 再針對選定地塊取樣。

4.6 Terrain grid coverage

各區含100 m 緩衝帶的矩形尺寸：

Region| Survey dimensions| 1 m grid points including boundaries
B1| 500 × 500 m| 251,001
B2| 600 × 450 m| 271,051
B3| 500 × 400 m| 200,901

三區合計722,953個高度格點，每個 preset。

兩種 preset 合計1,445,906個候選區高度格點，不包含全世界20 m 網格及必要道路補充資料。

格點包含矩形邊界。

候選道路若超出三區1 m 網格，Claude 應在同一階段的 dump 內提供其必要地形資料。

不得重新引入選定住宅後的 Pass 2 流程。

4.7 Preset comparison

Claude 已確認不同畫質的生成數量存在差異。

Static source| PHONE_LOW| DESKTOP_HIGH
WORLD.buildings| 840| 704
WORLD.cityInfill| 776| 554
WORLD.suburbHouses| 210| 390

上述數值為 BASE 的 G0 觀察結果。

不得將較低畫質一律視為物件較少或土地較多。

每份 dump 必須標記實際 preset。

最終住宅容量採跨畫質保守結果：

- 障礙物使用兩種 preset 的聯集。
- 可用土地使用兩種 preset 的交集。
- 同一住宅配置必須在兩種 preset 均合法。
- 最終共同容量不得高於任一 preset 的對應獨立容量。

不得只比較兩種 preset 的住宅總數而忽略實際地塊位置。

TABLET_MED 不要求獨立完整世界 dump，但仍納入 Claude 效能基準。

---

5. Dump JSON schema v1

5.1 General conventions

- Format: UTF-8 JSON。
- schema_version: integer, fixed 1。
- Coordinate unit: metres。
- X/Z 為水平座標，Y 為高度。
- Bounds 使用 xmin、zmin、xmax、zmax。
- 所有 ID 在各資料類別內唯一。
- 所有數值必須為有限數字。
- 未知數值使用 null。
- 禁止 NaN 或 Infinity。
- 多邊形使用依序排列的 [x,z] 頂點。
- 多邊形不需要重複首點。
- 不允許自相交多邊形。
- 資料缺失不得默認為零或空地。

Schema version 維持1，因 v1.1 尚未正式註冊或實作。

本節為 v1.2 最終提議資料契約。

5.2 Top-level object

Required fields:

- schema_version: integer。
- metadata: object。
- world: object。
- regions: array。
- height_grids: array。
- footprints: array。
- roads: object。
- completeness: object。
- issues: array。

移除以下 v1.1 欄位：

- pass。
- parent_dump_sha256。
- sampling_request_id。
- parcel_samples。
- road_samples。

不需要獨立 Pass 2 dump。

5.3 Metadata object

Required fields:

- base_sha: string, 40-character Git SHA。
- game_release: string。
- preset: enum PHONE_LOW / DESKTOP_HIGH。
- initialization_complete: boolean。
- showcase_visible: boolean。
- night: boolean。
- extraction_version: string。
- generated_at: ISO-8601 string。
- coordinate_unit: string, fixed "m"。
- generation_settings: object。
- static_fingerprint: string, SHA-256 hexadecimal。
- source_counts: object。
- source_fingerprints: object。

Optional fields:

- seed: string, integer or null。

seed 欄位僅供記錄，不要求修改或固定 Math.random。

source_counts 至少記錄：

- WORLD.buildings。
- WORLD.cityInfill。
- WORLD.suburbHouses。
- TREES。
- TREE_COLLIDERS。

無法取得的計數使用 null 並記錄 issue。

5.4 Fingerprint definition

static_fingerprint 必須涵蓋所有影響靜態審計的資料：

- 世界及物理地面邊界。
- Terrain regions。
- 高度網格。
- 靜態 footprint。
- 道路中心線及拓撲。
- 保護區。
- 靜態來源計數。
- 必要的 completeness 狀態。

採 SHA-256。

Fingerprint 輸入使用確定性正規化：

- 物件鍵固定排序。
- 靜態物件陣列使用穩定 ID 或確定性幾何排序。
- 高度網格維持固定 row-major 順序。
- 不使用 runtime UUID 或不穩定動態 body ID 作為唯一排序依據。
- 排除 generated_at、執行時間及動態狀態。
- 不排除影響占地及地形的有效數值。

Claude 與 analyzer 必須使用相同的正規化契約。

G0 應確認 JavaScript 及 Python 的數值序列化相容方式，避免單純格式差異造成 fingerprint 不一致。

完整檔案 SHA-256 與 static_fingerprint 分開記錄。

完整檔案 SHA 可因時間戳不同而不同；靜態 fingerprint 必須一致。

5.5 World object

Required fields:

- ground_bounds: bounds or null。
- playable_bounds: bounds or null。
- physical_ground: object。
- terrain_regions: array。
- water_regions: array of polygons。
- beach_regions: array of polygons。
- map_ui_bounds: bounds or null。
- boundary_obstacles: array of footprint IDs。
- source_refs: array of strings。

physical_ground object:

- shape: string, "BOX"。
- half_extents: array of three numbers [x,y,z]。
- position: array of three numbers [x,y,z]。
- top_y: number。
- bounds: bounds。
- verification: RUNTIME_VERIFIED / UNKNOWN。
- source_ref: string。

BASE 預期 physical_ground：

- half_extents = [2400,0.5,2400]。
- position = [0,-0.5,0]。
- top_y = 0。
- bounds = [-2400,-2400,2400,2400]。

Claude 應核對實際值。

Terrain region object:

- id: string。
- polygon: array of [x,z]。
- margin_m: number。
- source_ref: string。
- terrain_support_status: VERIFIED / UNKNOWN / NOT_APPLICABLE。

terrain_support_status 描述非平坦地形支撐行為，不代表整個世界是否存在平坦物理地面。

5.6 Region object

Required fields:

- id: B1 / B2 / B3。
- name: string。
- initial_polygon: array of [x,z]。
- survey_polygon: array of [x,z]。
- buffer_m: number, fixed 100。
- source_ref: string。

修訂後多邊形由 analyzer 作為獨立輸出，不得覆寫原始 dump。

5.7 Height grid object

Required fields:

- id: string。
- region_id: WORLD / B1 / B2 / B3 / ROAD_CORRIDOR。
- origin_x: number。
- origin_z: number。
- step_m: number。
- nx: integer。
- nz: integer。
- heights: array of numbers or null。
- source: string, fixed "runtime_terrainHeight"。
- sample_method: string, fixed "DIRECT_RUNTIME"。

陣列採 row-major：

index = iz × nx + ix。

對應座標：

x = origin_x + ix × step_m。

z = origin_z + iz × step_m。

heights 長度必須等於 nx × nz。

WORLD 網格 step_m=20。

B1/B2/B3 網格 step_m=1。

ROAD_CORRIDOR 網格 step_m=1，適用於必要的候選道路補充範圍。

物理支撐由 world.physical_ground 及 terrain_regions 判定，不需要為每個平坦地面格點重複儲存相同 support 字串。

若某格點存在特殊支撐限制，應透過 footprint、terrain region 或 issue 記錄。

5.8 Footprint object

Required fields:

- id: string。
- category: enum。
- source_group: string。
- geometry_type: POLYGON / AABB。
- geometry_precision: EXACT_OUTLINE / CONSERVATIVE_AABB。
- polygon: array of [x,z] or null。
- bounds: bounds。
- y_min: number or null。
- y_max: number or null。
- visual: boolean。
- physical: boolean。
- protected: boolean。
- source_ref: string。
- verification: RUNTIME_VERIFIED / UNKNOWN。

Optional field:

- parent_id: string。

Category enum 至少包含：

- BUILDING。
- COLLIDER。
- TREE。
- ROAD。
- SIDEWALK。
- RAMP。
- BRIDGE。
- PARK。
- WATER。
- BEACH。
- SITE_A。
- AIRPORT。
- MISSION。
- FAST_TRAVEL。
- BOUNDARY。
- OTHER。

每個來源必須明確標記幾何精度。

EXACT_OUTLINE：

使用已確認的實際水平占地輪廓。

CONSERVATIVE_AABB：

使用保守世界座標 bounding box。

WORLD list 中的矩形尺寸只有在已確認與實際占地一致時，才能標記 EXACT_OUTLINE。

Scene Box3 原則上標記 CONSERVATIVE_AABB。

TREE_COLLIDERS 若使用外接矩形表示圓形或其他形狀，必須標記 CONSERVATIVE_AABB。

不得因資料來自正式 runtime，就自動將所有 footprint 標記為精確輪廓。

保守 AABB 只能用於保守排除，不能用於證明其內部空間可開發。

5.9 Roads object

Required fields:

- nodes: array。
- segments: array。
- completeness: COMPLETE / PARTIAL / UNKNOWN。

Road node object:

- id: string。
- x: number。
- y: number or null。
- z: number。
- connected_segment_ids: array of strings。
- source_ref: string。

Road segment object:

- id: string。
- start_node_id: string or null。
- end_node_id: string or null。
- centerline: array of [x,y,z]。
- carriageway_width_m: number or null。
- sidewalk_left_m: number or null。
- sidewalk_right_m: number or null。
- corridor_footprint_ids: array of strings。
- elevation_type: GROUND / ELEVATED / RAMP / UNKNOWN。
- traffic_route_ids: array of strings。
- source_ref: string。
- verification: RUNTIME_VERIFIED / UNKNOWN。

交通路線僅使用靜態路線定義，不擷取動態交通車輛位置。

未知交通資料必須明確標記。

空的 traffic_route_ids 不等同已確認沒有交通。

5.10 Completeness object

Required fields:

- world_bounds。
- terrain_heights。
- physical_ground。
- terrain_regions。
- visual_occupancy。
- physical_occupancy。
- trees。
- water_and_beach。
- protected_areas。
- roads。
- traffic_routes。

每項值為 COMPLETE / PARTIAL / UNKNOWN / NOT_APPLICABLE。

NOT_APPLICABLE 必須有明確原因。

必要資料為 PARTIAL 或 UNKNOWN 時，受影響土地不得直接分類為 L0。

5.11 Issue object

Required fields:

- id: string。
- severity: INFO / WARNING / BLOCKER。
- category: string。
- affected_region_ids: array。
- affected_polygon: polygon or null。
- message: string。
- source_ref: string。

若資料缺口無法定位，保守視為影響整個相關審計區域。

5.12 Schema validation

Analyzer 必須拒絕：

- 不支援的 schema_version。
- BASE 不一致。
- Preset 標記不合法。
- 不合法座標。
- 非有限數值。
- 重複 ID。
- 高度網格長度錯誤。
- 不合法多邊形。
- 缺失必要欄位。
- 無法解析的道路引用。
- 不合法 footprint 精度標記。
- Static fingerprint 與內容不一致。
- 1 m 高度網格規格不符。

可接受 schema 合法但資料內容不完整的 dump。

此時保留 UNKNOWN/LX，不得將缺失資料解讀為空地。

---

6. Terrain and land classification

6.1 Terrain sampling levels

Data level| Meaning
DIRECT_RUNTIME_20M| 正式世界粗略高度取樣
DIRECT_RUNTIME_1M| 正式候選區精細高度取樣
INTERPOLATED_1M| 由1 m 網格插值取得
INTERPOLATED_20M| 由20 m 網格插值取得
UNKNOWN| 無有效高度資料

移除 DIRECT_RUNTIME_5M、INTERPOLATED_5M 及 Pass 2 專用分類。

插值可使用 bilinear interpolation。

插值高度不得標記為正式直接取樣。

0.01 m 精度驗證僅適用於直接 runtime 取樣的1 m 格點。

6.2 Slope calculation

格點坡度：

以 X/Z 方向有限差分估算水平梯度大小，再乘以100。

道路縱坡：

以中心線高度差除以累積水平距離，再乘以100。

地形坡度分類：

- S0：0–5%，包含5%。
- S1：大於5%，至10%。
- S2：大於10%，至20%。
- S3：大於20%，至30%。
- S4：大於30%。

S0 為一般直接住宅候選。

S1–S3 需確認地基及住宅設計，列為條件式開發。

S4 不計入一般住宅容量。

1 m 取樣不代表連續地形的無限精度證明。

6.3 Land classes

Code| Definition
L0| 直接可用土地候選
L1| 需要地基或道路調整
L2| 需要另行批准既有建築更新
L3| 需要地形、海岸或其他世界擴建
L4| 保護區
L5| 不可用土地
LX| 資料不足，未確認

L0 土地候選必須：

- 不與已知障礙物重疊。
- 不侵占保護區。
- 不位於水域。
- 不侵占既有道路及人行道。
- 位於已確認可遊玩及物理支撐範圍。
- 具有合理地形條件。
- 必要占地資料完整。

不得因土地位於 terrainRegions 之外，就自動分類為 L3、L5 或 LX。

若土地位於已確認的平坦物理地面範圍，且正式高度為0，應依其他土地條件正常分類。

B2 的平地可具有一般住宅占地容量，但山區住宅設計可行性必須另外考慮所需地形工程。

6.4 Classification priority

主要分類優先順序：

L4 → L5 → LX → L2 → L3 → L1 → L0。

每個土地單元只有一個主要分類。

可保存多重障礙及原因標記。

水域不得分類為 L0。

需要填海或海岸重建的土地可列為 L3 研究候選，但未批准工程前不得計入直接容量。

6.5 Site A protection

Site A 最終保護範圍：

X = [-561,-441]。

Z = [-831,-753]。

任何與保護區重疊的住宅地塊均不得計入直接或條件式住宅容量。

不得移除、移動或縮減 Site A 保護區以達成住宅數量。

6.6 Area conservation

土地分類統計使用5 m × 5 m 網格。

地形資料來源為1 m 正式高度網格。

土地分類網格與地形取樣網格必須明確區分。

邊界格使用與候選多邊形的實際相交面積。

對部分被障礙物占用的格子：

- 可精確計算時使用實際交集。
- 無法精確計算時保守排除整格。
- 記錄保守排除的限制。

不得只檢查格點中心。

分類面積總和與候選多邊形聯集面積差異不得超過1 m²。

三區重疊、海灘與水域重疊、視覺與物理占地重疊不得重複計算。

---

7. Residential capacity and feasibility

7.1 Fixed prototype dimensions

Prototype| Building footprint| Required parcel| Parcel area
R01 Urban Residence| 32 × 24 m| 42 × 34 m| 1,428 m²
R02 Skyline Residence| 36 × 30 m| 48 × 42 m| 2,016 m²
R05 Detached House| 14 × 12 m| 24 × 22 m| 528 m²
R08 Four-unit Terrace Homes| 28 × 14 m| 38 × 24 m| 912 m²

其他六種住宅原型尚未確認完整尺寸，不納入本次精確容量。

R05 作為山坡別墅占地代理，必須標記 PROXY。

不得將 R05 容量視為已確認山坡別墅美術或結構設計。

7.2 Land-use reference — informational only

依 Claude 首次 G0 的容量估算，住宅地塊面積約占25 ha 的15–30%。

此比例僅為規劃參考，不是硬性驗收門檻。

Land use| Reference
Residential parcels| 15–30%
Roads and sidewalks| 20–30%
Parks and landscaping| 25–40%
Public facilities, reserve and other| Remaining area

概念配置：

- 住宅地塊25%。
- 道路及人行道25%。
- 公園及景觀30%。
- 公共設施及保留土地20%。

合計100%。

不得因住宅地塊比例低於15%或高於30%，單獨判定住宅計畫不可行。

實際土地用途仍須互斥、守恆並合計100%。

7.3 Counting and prototype mix

住宅大樓計為一棟，不依樓層或戶數增加棟數。

獨棟住宅計為一棟。

R08 四戶連棟住宅整排計為一棟、四戶。

住宅棟數與住宅戶數分開統計。

B1：

- R02 至少占住宅棟數50%。
- 其餘使用 R01。

B2：

- 使用 R05 作為暫定占地代理。
- 不得以高樓取代山區住宅來增加容量。

B3：

- 使用 R01、R05、R08。
- 三種原型各至少占住宅棟數20%。

比例以整數棟數向上取整檢查。

7.4 Parcel placement

使用1 m 候選中心網格。

允許0°及90°兩種方向。

不得縮小固定地塊尺寸。

所有住宅地塊必須：

- 完整位於候選多邊形內。
- 不侵占障礙物。
- 不侵占保護區。
- 不與其他住宅地塊重疊。
- 具備可驗證道路接近條件。
- 使用完整1 m 地形網格檢查。
- 在兩種 preset 均符合條件。

不需要額外 Pass 2 取樣。

若完整1 m 網格不足以涵蓋地塊，該地塊不得計入直接容量。

7.5 Occupancy prefix sums

WE-01B 必須使用1 m occupancy raster 及二維 summed-area table / prefix sums。

至少建立以下遮罩：

- 不可用土地。
- 保護區。
- 既有視覺占地。
- 既有物理占地。
- 道路及保留走廊。
- 未確認土地。
- 候選區外部。

跨畫質障礙使用 PHONE_LOW 與 DESKTOP_HIGH 聯集。

矩形地塊占地查詢使用 prefix sums，使每次固定矩形障礙查詢為 O(1)。

不得對每個候選地塊重新逐格掃描完整地塊。

Prefix sums 建構成本為 O(W × H)。

已選地塊的動態占地使用額外空間索引、確定性矩形碰撞檢查或合理更新方法。

不得每放置一棟住宅就重新建構整個世界的 prefix sums。

使用緊湊陣列，避免大型 Python object grid。

各區分別建立局部 occupancy raster。

最終選定地塊仍須與原始 footprint 及候選多邊形進行幾何核對。

7.6 Deterministic placement

允許：

- 確定性貪婪配置。
- 固定原型排序。
- 固定座標排序。
- 數個固定配置順序。
- 有界搜尋。

必須記錄配置順序及 tie-breaking 規則。

不使用未固定 seed 的隨機搜尋。

不得引入重量級最佳化套件。

貪婪配置結果是已找到的可配置下界，不是數學最大容量。

搜尋未找到足夠地塊時，若沒有上界證明，不得宣稱不可行。

7.7 Capacity outputs

每區輸出：

- C_preliminary：初步幾何候選容量。
- C_direct：已通過完整1 m 地形、占地及道路驗證的直接容量。
- C_conditional：包含直接容量及具有明確後續工程條件的總容量。
- C_upper：保守容量上界。
- C_unknown：仍待確認的候選地塊數量。

另外輸出：

- C_phone_low。
- C_desktop_high。
- C_common。

最終 C_direct 及 C_conditional 應以跨畫質共同配置為準。

C_common 不得高於任一 preset 的對應獨立容量。

C_conditional 已包含 C_direct，不得重複相加。

C_preliminary 不得與 C_direct 相加。

C_upper 必須是真正不低估可能容量的上界。

可使用尚未被證明排除的土地總面積，除以該區允許原型的最小地塊面積，向下取整。

未確認土地不得在不可行證明中被無故排除。

7.8 Area feasibility — 25 ha

定義：

- A_gross：修訂後三區多邊形聯集面積。
- A_direct：已驗證可直接用於相容規劃用途的土地面積。
- A_conditional：需要後續工程的規劃土地面積。
- A_protected：保護區面積。
- A_unavailable：不可用土地面積。
- A_unknown：未確認土地面積。
- A_eligible：可直接使用土地及具明確工程條件土地的聯集面積。

土地分類與規劃用途分開統計。

既有道路不可作為住宅地塊，但在確認相容時可作為住宅區道路用途。

既有保護公園可在保持原狀且功能相容時計入景觀用途。

Site A 不得用於補足住宅區有效規劃面積。

25 ha 目標為 FEASIBLE，須同時符合：

1. A_gross ≥250,000 m²。
2. 已驗證有效規劃土地 ≥250,000 m²。
3. 三區均存在有效住宅配置。
4. 土地用途配置不存在重疊計算。
5. 不依賴未批准地形改造、建築移除或保護區侵占。
6. 所有計入面積的必要資料已驗證。

不要求符合 §7.2 的參考比例。

若25 ha 需要明確但尚未批准的擴建工程，判定 CONDITIONAL。

若搜尋範圍及面積上界證明無法達成25 ha，判定 NOT FEASIBLE WITHIN AUDITED BOUNDARIES。

若資料不足，判定 UNVERIFIED。

7.9 Housing capacity targets

Region| Minimum| Ideal
B1| 10| 14
B2| 12| 18
B3| 18| 28
Total| 40| 60

最低容量 FEASIBLE：

- B1 C_direct ≥10。
- B2 C_direct ≥12。
- B3 C_direct ≥18。
- 合計 C_direct ≥40。
- 所有配置符合原型比例及地塊限制。

理想容量 FEASIBLE：

- B1 C_direct ≥14。
- B2 C_direct ≥18。
- B3 C_direct ≥28。
- 合計 C_direct ≥60。
- 所有配置符合原型比例及地塊限制。

不得以某區超額容量抵銷其他區不足。

若直接容量不足，但 C_conditional 達到各區目標且具有具體工程條件，判定 CONDITIONAL。

若有效容量上界低於任一區目標，判定 NOT FEASIBLE WITHIN AUDITED BOUNDARIES。

若搜尋未找到足夠地塊但沒有上界證明，判定 UNVERIFIED。

B2 必須分開報告：

- 平地住宅占地容量。
- 維持山區住宅願景所需的地形工程。

不得因平地容量充足，就宣稱山坡住宅設計已可直接實現。

7.10 Final feasibility verdicts

FEASIBLE：

有完整已驗證配置，不依賴未批准工程。

CONDITIONAL：

有具體配置及可追溯的後續工程需求，但尚未達成直接可行條件。

NOT FEASIBLE WITHIN AUDITED BOUNDARIES：

有面積、容量或道路限制證據，足以證明在審計範圍內無法達成目標。

UNVERIFIED：

必要資料或配置證據不足。

整體 D3 裁定順序：

1. 任一必要目標已證明不可行：NOT FEASIBLE WITHIN AUDITED BOUNDARIES。
2. 無已證明不可行項目，但任一必要目標仍未確認：UNVERIFIED。
3. 所有必要目標已有證據，至少一項依賴未批准工程：CONDITIONAL。
4. 所有必要目標直接可行：FEASIBLE。

必要目標為25 ha、40棟最低容量及三區道路連通。

60棟為理想目標，不是最低可行性的必要條件。

由於多數候選道路尚未建造，且 B2 山區願景可能需要新增地形，整體 CONDITIONAL 為預期較可能的結果。

不得以此預期取代實際審計。

7.11 Audit success versus project feasibility

WE-01 通過不代表 D3 必須可行。

正確證明計畫不可行或需要前置工程，仍屬有效審計成果。

不得為取得 FEASIBLE 而修改分類規則、地塊尺寸或驗收標準。

---

8. Road and traffic analysis

8.1 Initial candidate routes

C01 — Coastal Boulevard Extension

(221,890) → (240,960) → (240,1200)

C02 — Coastal Residential Cross Street

(110,960) → (170,960) → (240,960)

H01 — Hillside Scenic Branch

(-635,682) → (-800,800) → (-800,1030)

H02 — Hillside Return Road

(-800,1030) → (-420,1000) → (-240,880)

X01 — Hillside-Coast Connector

(-240,880) → (0,960) → (110,960)

U01 — Existing Urban Cross Street

(-600,-720) → (-510,-720) → (-420,-720)

U01 為既有道路利用及改善候選，不應重複鋪設。

C02 西端尚未確認為既有道路接點。

H01 起點須與 runtime 盤山道路核對。

8.2 Preliminary road standards

Parameter| Proposed value
Coastal arterial carriageway| 14 m
Residential carriageway| 7 m
Hillside carriageway| 7–8 m
Residential sidewalks| 2 m per side
Normal road maximum grade| 6%
Hillside maximum grade| 9%
Normal road minimum curve radius| 25 m
Hillside minimum curve radius| 18 m

既有道路維持 production 尺寸。

上述標準僅適用於候選新道路。

8.3 Road geometry

候選道路控制點不得直接視為已完成道路曲線。

Analyzer 必須定義可重現的平滑曲線或圓弧連接方法。

輸出：

- 控制點。
- 實際候選中心線。
- 曲線生成方法。
- 取樣間距。
- 總長度。
- 最大縱坡。
- 最小曲線半徑。
- 完整道路及人行道走廊。
- 既有障礙物交集。
- 地形及水域衝突。
- 接點座標及高度差。
- 高架道路垂直空間衝突。
- 受影響的靜態交通路線。

中心線取樣間距不超過3 m。

道路高度分析使用單階段 dump 中的1 m 網格。

非整數座標可使用插值，但須標記來源。

20 m 網格插值只能用於粗略道路研究，不足以證明精確道路幾何可行。

缺少必要精細地形資料時，相關道路判定 UNVERIFIED。

不得將尚未建造道路的設計高度冒充正式 runtime 高度。

8.4 Connectivity

既有道路拓撲以 ROAD_NET 為主要來源。

每區至少須具備一個可驗證對外接點及通往既有城市的路徑。

道路平面相交不等於合法連通。

高架道路與地面道路須分開判定。

尚未建造的候選道路即使幾何可行，也只能標記 CONDITIONAL。

若需要新增地形、道路或接點，須列出依賴工程。

最終研究城市—山區—海岸環狀路網，但 WE-01 不實際建設道路。

---

9. Task decomposition

WE-01 拆分為兩個依序執行的獨立子任務。

各自需要 G0 審查、使用者批准、正式 T-ID 及獨立 PR。

不得同時開啟兩個實作 PR。

9.1 WE-01A — Runtime Dump Analysis and Land Classification

Implementer: Gemini。

Risk: LOW。

Scope:

- Dump schema validation。
- Static fingerprint validation。
- 單階段1 m 地形資料讀取。
- PHONE_LOW / DESKTOP_HIGH 差異分析。
- 地形高度分析。
- 土地分類 L0–L5/LX。
- Site A、水域、道路及保護區處理。
- Footprint 精度處理。
- 面積守恆。
- 修訂候選區搜尋範圍。
- 土地分類 SVG。
- 確定性輸出。
- 相關快速測試及 mutation tests。

WE-01A 不負責：

- 完整住宅地塊配置。
- 最終住宅容量。
- 候選道路完整曲線分析。
- 整體 D3 可行性裁定。

WE-01A 必須輸出可供 WE-01B 使用的穩定分類資料。

9.2 WE-01B — Parcel Capacity, Road Analysis and Feasibility

Implementer: Gemini。

Risk: LOW。

Prerequisite:

- WE-01A 已通過審查及合併。
- WE-01A 輸出格式已固定。
- Claude 已提供完整雙 preset dumps。
- WE-01B BASE 已重新確認。
- 使用者已獨立批准 WE-01B。

Scope:

- 1 m occupancy raster。
- Prefix sums。
- 住宅地塊配置。
- 原型比例及棟數檢查。
- 容量下界及上界。
- 跨畫質共同容量。
- 候選道路幾何分析。
- 道路連通性。
- 完整1 m 地形驗證。
- 25 ha、40棟及60棟裁定。
- 最終 SVG 及完整報告。
- 剩餘快速測試及 mutation tests。

WE-01B 不得重新實作 WE-01A 已驗證的分類邏輯。

9.3 Sequential dependency

WE-01A 完成後，Claude 審查其輸出與正式 dumps。

只有在資料契約及土地分類可信時，才進入 WE-01B。

WE-01B 使用合併後的新 BASE。

不得直接沿用舊 SHA 作為實際開發分支基準。

---

10. File allowlists and size limits

10.1 WE-01A allowlist

僅新增：

1. tools/test/we01a_land_analyzer.py
2. tools/test/we01a_land_analyzer_check.py

第一個檔案提供資料讀取、分類、面積分析及 SVG。

第二個檔案提供 synthetic fixtures、單元測試及 mutation tests。

兩檔合計不得超過800行，除非 Claude 另行批准。

10.2 WE-01B allowlist

僅新增：

1. tools/test/we01b_capacity_analyzer.py
2. tools/test/we01b_capacity_analyzer_check.py

第一個檔案使用 WE-01A 模組，完成容量、道路及裁定。

第二個檔案提供快速測試及 mutation tests。

兩檔合計不得超過1,000行，除非 Claude 另行批准。

WE-01B 原則上不得修改已驗收的 WE-01A 檔案。

若需要修正 WE-01A，須提出獨立修正或取得明確 allowlist 更新。

10.3 Size rationale

完整 WE-01 採兩個獨立子任務。

合計程式及測試規模上限1,800行。

不得為符合行數限制而省略必要測試。

若超出上限，須取得 Claude 同意或提出進一步拆分。

10.4 Forbidden files

Gemini 不得修改：

- index.html。
- sw.js。
- COLLAB.md。
- AGENTS.md。
- TASKS.md。
- DECISIONS.md。
- LOG.md。
- HANDOFF.md。
- specs/。
- .github/。
- 既有測試。
- 遊戲資源。
- Binary assets。

不得提交大型 runtime dumps、生成報告、pycache、瀏覽器快取或其他暫存資料。

10.5 Dependencies

Analyzer 僅使用 Python 標準函式庫。

不新增第三方套件。

Claude runtime 擷取使用現有 Playwright / Chromium 環境。

Gemini 不負責撰寫或提交 runtime 擷取腳本。

若 Claude 需要持久保存擷取工具，須依 COLLAB 另行確認檔案權限。

---

11. Analyzer CLI and performance

11.1 Input contract

兩個 analyzer 必須接受：

- --dump <json>，可重複指定。
- --out <directory>。
- --help。

WE-01B 另接受：

- --land-report <json>。

移除：

- --pass2。
- --request-id。

Analyzer 必須能讀取兩種 preset 的正式 dumps。

所有輸入檔案唯讀。

所有輸出寫入指定目錄。

不得覆寫原始 dump。

11.2 Exit behavior

Exit code 0：

分析成功，包括有證據支持的 CONDITIONAL、NOT FEASIBLE 或 UNVERIFIED。

Exit code non-zero：

- Schema 不合法。
- 必要輸入檔案缺失。
- BASE 不匹配。
- Fingerprint 驗證失敗。
- 面積守恆失敗。
- 內部分析錯誤。

住宅計畫不可行不等於 analyzer 執行失敗。

11.3 Full-dump time budget

由 Claude 使用正式 runtime dumps 量測。

WE-01A：

- 讀取兩種 preset 的完整單階段 dumps。
- 完成分類、面積統計及 SVG。
- 單次執行目標不超過60秒。

WE-01B：

- 讀取兩種 preset 的完整 dumps。
- 讀取 WE-01A 分類結果。
- 完成地塊搜尋、道路分析及最終報告。
- 單次執行目標不超過60秒。

時間包含 JSON 讀取及輸出。

不包含 Claude 啟動遊戲、擷取 dumps 或執行重量級效能測試。

記錄：

- CPU。
- RAM。
- Python version。
- Dump 大小。
- 執行時間。
- Peak memory，若可取得。

若超出60秒，Claude 應要求分析原因及最佳化，或明確批准例外。

不得降低資料精度、忽略障礙物或減少必要驗證以符合時間預算。

11.4 Gemini fast-check budget

Gemini 單次快速測試建議不超過60秒。

每個子任務全部快速檢查建議不超過5分鐘。

Gemini 僅使用小型 synthetic fixtures。

正式完整 dumps 的分析時間驗收由 Claude 執行。

---

12. Deliverables

12.1 Claude input artifacts

正式分析輸入：

- world_phone_low.json。
- world_desktop_high.json。

確定性驗證產物：

- PHONE_LOW 連續兩次 dump fingerprint。
- DESKTOP_HIGH 連續兩次 dump fingerprint。
- 完整檔案 SHA-256。
- 靜態來源計數及 fingerprints。
- 擷取環境資訊。

不再需要 Pass 2 檔案或 sampling request。

12.2 WE-01A outputs

land_inventory.json：

- Schema validation。
- 來源資料。
- 靜態 fingerprint。
- 三區候選多邊形。
- 土地分類。
- 面積統計。
- 障礙物。
- Footprint 精度。
- 資料缺口。
- 共同可用土地。

terrain_survey.csv：

- X/Z。
- 高度。
- 坡度。
- 取樣間距。
- 取樣方法。
- 土地分類。

preset_diff.json：

- 靜態來源計數。
- 兩種畫質占地差異。
- 高度差異。
- 共同限制。

land_survey.svg：

- 土地分類。
- 三區及緩衝帶。
- 既有建築。
- 道路。
- 水域。
- Site A。
- 未確認土地。

land_report.md：

- 土地分析。
- 面積守恆。
- 已知限制。
- 修訂候選區建議。
- 待 WE-01B 處理事項。

12.3 WE-01B outputs

parcel_inventory.csv：

- Parcel ID。
- Region。
- Prototype。
- 中心座標。
- 方向。
- 尺寸。
- 土地分類。
- 1 m 地形驗證狀態。
- 跨畫質合法性。
- 道路接近條件。
- 障礙原因。

road_survey.json：

- 道路控制點。
- 候選曲線。
- 長度。
- 坡度。
- 曲率。
- 接點。
- 衝突。
- 連通性。
- 驗證狀態。

feasibility.json：

- 25 ha 裁定。
- 40棟裁定。
- 60棟裁定。
- 各區容量。
- 各 preset 容量。
- 跨畫質共同容量。
- 各區道路裁定。
- 整體 D3 裁定。
- 依賴工程。
- 證據及未確認事項。

world_survey.svg：

- 最終修訂候選區。
- 住宅地塊配置。
- 道路配置。
- 土地分類。
- 保護區。
- 未確認區域。

survey_report.md：

- 完整審計結論。
- 土地面積。
- 住宅容量。
- 道路配置。
- 可行性裁定。
- 效能基準引用。
- 後續工程建議。

12.4 SVG requirements

正式 SVG 必須包含：

- X/Z 座標軸。
- 比例尺。
- 圖例。
- BASE SHA。
- Dump SHA 或 static fingerprint。
- Preset 或跨畫質共同分析標記。
- 既有與候選道路的區別。
- Site A 保護區。
- LX / UNKNOWN。
- 候選地塊 ID，適用時。
- 審計資料與示意資料的明確區別。

不得以概念地圖冒充 runtime 審計結果。

12.5 Artifact storage

大型 dumps、CSV、SVG 及報告屬於測試產物。

不得直接提交至 Gemini 程式 PR。

Claude 應提供可供審查及重現的產物位置、檔案雜湊及保存方式。

---

13. Performance baseline — Claude only

13.1 Presets

- PHONE_LOW。
- TABLET_MED。
- DESKTOP_HIGH。

13.2 Measurement locations

至少涵蓋：

- B1：(240,1080)。
- B2：(-700,945)。
- B3：(-490,-710)。
- Site A：(-501,-790)。
- CBD：(-60,0)。
- Suburbs：(-1060,-238)。

若原始候選位置不適合正常遊玩測試，Claude 應使用最近可驗證位置並記錄原因。

不得因位於 terrainRegions 外部而直接認定缺少物理地面。

13.3 Required metrics

- Draw calls。
- Triangles。
- Physics bodies。
- Physics shapes。
- Physics step time。
- Mesh count。
- Geometry count。
- Geometry buffer bytes。
- Material count。
- Texture count。
- 可取得的 texture memory estimate。
- 世界初始化時間。
- 建築、樹木、道路及碰撞體數量。
- 可取得的 LOD 統計。
- Main pass。
- Water mirror pass。
- 可辨識的 shadow pass。

Physics body count 可用於效能基準，但完整 body 位置 fingerprint 不屬於靜態世界驗收。

13.4 Measurement method

固定可控制的攝影機位置、視角、時間、畫質及 Site A 狀態。

不要求修改 Math.random 或正式世界生成邏輯。

涵蓋固定日間及夜間場景。

渲染：

- 暖機後至少記錄120個完整畫面。
- 報告中位數及範圍。
- 可分離的渲染 pass 分開記錄。
- 無法可靠分離的 pass 明確標記。

物理：

- 至少五組成對量測。
- 每組暖機至少900 steps。
- 每組記錄360 steps。
- 使用既有 physicsWorld.step(1/60,1/60,3) 方法。
- 報告原始樣本及中位數。
- Baseline control 中位數比率須位於1/1.10至1.10之間。
- 超出範圍應重新量測。

13.5 Zero-change constraints

Production metric| Allowed delta
Game source files| 0
Physics bodies, matched state| 0
Physics shapes, matched state| 0
Deterministic draw calls| 0
Deterministic triangles| 0
Materials, matched state| 0
Textures, matched state| 0
Save schema| 0
PWA resources| 0

結構性數量須在相同可比較狀態下驗證。

不得要求不同載入的全部動態 body 位置完全一致。

若存在量測差異，先確認環境、動態狀態及確定性，不得修改基準來取得通過。

13.6 Device FPS

後續住宅開發仍以手機及平板平均 FPS ≥30 為最低目標。

WE-01 不包含新住宅，因此不得宣稱新住宅已達效能目標。

Headless 量測不得冒充實機 FPS。

---

14. Automated acceptance tests

14.1 WE-01A tests

A01 — Schema validation

合法 fixture 可讀取；不合法 schema、BASE、座標及引用必須拒絕。

A02 — Production integrity

正式遊戲資源 SHA-256 與 BASE 一致。

A03 — Determinism

相同輸入執行三次，確定性輸出雜湊一致。

Claude 每個 preset 連續兩次獨立載入的 static fingerprint 必須一致。

A04 — Land classification

L0–L5/LX 分類符合固定 fixture 預期。

A05 — Occupancy

靜態視覺及物理障礙均納入分類。

不得將動態 physics bodies 納入靜態占地。

A06 — Site A protection

Site A 及10 m 緩衝帶不得分類為住宅可用土地。

A07 — Water protection

水域不得分類為 L0。

A08 — Road protection

道路、人行道及保留走廊不得分類為 L0。

A09 — Area conservation

分類面積與候選多邊形聯集面積差異 ≤1 m²。

A10 — Overlap accounting

多重障礙重疊不得重複計算面積。

A11 — Unknown handling

必要資料缺失必須保留 LX。

A12 — Preset comparison

共同可用土地必須使用障礙物聯集及可用土地交集。

A13 — Height provenance

直接取樣及插值高度標記不得混用。

A14 — Full-dump runtime

Claude 執行完整雙 preset dumps，驗證60秒時間目標。

A15 — SVG completeness

SVG 包含必要座標、圖例、保護區及資料來源。

A16 — Footprint precision

EXACT_OUTLINE 與 CONSERVATIVE_AABB 必須明確區分。

A17 — Static fingerprint integrity

內容被修改但 fingerprint 未更新時，analyzer 必須拒絕。

A18 — Flat physical ground

位於 terrainRegions 外、但位於已確認物理地面內的平地，不得因缺少 terrain region 而被判定缺少物理支撐。

14.2 WE-01B tests

B01 — Parcel dimensions

所有住宅地塊符合固定原型尺寸。

B02 — Prefix sums

O(1) 矩形占地查詢與小型 fixture 逐格參考結果一致。

B03 — Parcel non-overlap

選定地塊不得彼此重疊。

B04 — Obstacle protection

選定地塊不得侵占障礙物及保護區。

B05 — Prototype mix

各區原型比例符合 §7.3。

B06 — Building count

R08 整排計為一棟、四戶。

B07 — Dump linkage

WE-01B 使用的 land report 必須對應正確 BASE、preset 及正式 dump fingerprints。

取代原 Pass 2 linkage test。

B08 — Exact height validation

Claude 對每個 preset 至少100個固定1 m 直接取樣點重新呼叫正式 __th。

誤差不得超過0.01 m。

取樣點應涵蓋三區及其必要邊界，並包含非零地形點（若審計範圍內存在）。

此門檻僅適用於 DIRECT_RUNTIME_1M。

插值高度不適用0.01 m 門檻。

B09 — Physical support

無物理支撐或支撐未知的地塊不得計入 C_direct。

已確認的平坦物理地面必須被正確接受。

B10 — Capacity accounting

C_conditional 不得與 C_direct 重複相加。

B11 — Regional capacity

不得以某區超額容量抵銷另一區不足。

B12 — Capacity bound

搜尋失敗不得在缺乏上界證明時被判定不可行。

B13 — Road geometry

候選道路具有可重現曲線、坡度及曲率分析。

B14 — Road connectivity

高架及地面道路平面相交不得自動建立連通。

B15 — Feasibility verdicts

四種裁定與固定測試資料一致。

B16 — Conditional roads

尚未建造的道路不得標記為直接 FEASIBLE。

B17 — Determinism

相同輸入及配置順序執行三次，確定性輸出一致。

B18 — Full-dump runtime

Claude 驗證完整單階段 dump 分析時間。

B19 — Report completeness

25 ha、40棟、60棟及道路均有獨立裁定。

B20 — Land-use reference

住宅土地比例不得被錯誤用作硬性門檻。

B21 — Cross-preset capacity

共同住宅配置必須在兩種 preset 均合法。

共同容量不得高於任一 preset 的對應獨立容量。

14.3 Deterministic hashing

確定性雜湊排除：

- generated_at。
- 執行時間。
- Peak memory。
- FPS。
- 動態物件狀態。
- 其他非確定性效能欄位。

不得排除：

- 地塊配置。
- 土地分類。
- 面積。
- 容量。
- 道路結果。
- 可行性裁定。
- 靜態地形資料。
- 靜態 footprint。
- 資料來源 SHA 及 fingerprint。

---

15. Mutation tests

保留 v1.1 的全部 mutation test IDs。

與 Pass 2 有關的測試改為單階段 dump 的等效資料驗證。

15.1 WE-01A mutations

M-A01：忽略既有建築占地，必須 FAIL。

M-A02：忽略水域，必須 FAIL。

M-A03：忽略 Site A 保護區，必須 FAIL。

M-A04：忽略道路占地，必須 FAIL。

M-A05：重複計算重疊土地面積，必須 FAIL。

M-A06：將 LX 分類為 L0，必須 FAIL。

M-A07：只採用 PHONE_LOW 障礙物，忽略 DESKTOP_HIGH 特有障礙，必須 FAIL。

M-A08：將插值高度標記為直接 runtime 高度，必須 FAIL。

M-A09：接受高度陣列長度錯誤的 dump，必須 FAIL。

15.2 WE-01B mutations

M-B01：單階段1 m 精確高度偏移0.5 m，必須 FAIL。

M-B02：將重疊住宅地塊計入容量，必須 FAIL。

M-B03：將 R08 計為四棟，必須 FAIL。

M-B04：重複加總 C_direct 與 C_conditional，必須 FAIL。

M-B05：以某區超額容量抵銷其他區不足，必須 FAIL。

M-B06：將缺少完整1 m 高度資料的地塊計入 C_direct，必須 FAIL。

M-B07：將未建造道路標記 FEASIBLE，必須 FAIL。

M-B08：搜尋未找到足夠地塊時直接判定 NOT FEASIBLE，必須 FAIL。

M-B09：將不具物理支撐的地塊計入直接容量，必須 FAIL。

M-B10：將住宅土地比例當成硬性門檻，必須 FAIL。

M-B11：接受與 land report 不匹配的 dump fingerprint，必須 FAIL。

M-B12：將高架與地面道路平面相交視為合法連通，必須 FAIL。

15.3 Mutation execution

Gemini 使用小型 synthetic fixtures 及獨立預期結果執行快速 mutation tests。

不得修改 production。

不得只使用與 analyzer 相同的計算邏輯作為唯一測試 oracle。

M-B01 使用獨立固定高度資料。

正式 runtime 高度交叉驗證由 Claude 執行。

---

16. Gemini workflow

16.1 Pre-start

每個子任務開始前確認：

- Claude G0 通過。
- 使用者批准完整子任務規格。
- Claude 登錄正式 T-ID。
- Gemini Stage 3 授權有效。
- BASE 已固定。
- 共享程式 PR 鎖空閒。
- D-013 分支保護有效。
- File allowlist 已確認。
- Dump schema 已確認。
- Synthetic fixture 資料契約完整。

WE-01A 開始前，Claude 應提供至少一份符合 schema 的實際 runtime dump 樣本。

WE-01B 開始前，WE-01A 必須已合併及驗收。

16.2 Implementation

Gemini 僅實作指定 analyzer 及測試。

不負責 production runtime 擷取。

不得自行增加正式遊戲介面。

若 dump 缺少必要資料，應回報 schema 或資料問題，不得重新實作 production world。

16.3 Fast checks

Gemini 執行：

- Python syntax check。
- 快速單元測試。
- Synthetic fixture smoke tests。
- 指定 mutation tests。
- Determinism check。
- File allowlist check。
- Production SHA-256 integrity check。
- Git diff check。

不執行完整 Playwright、WebGL 或物理效能測試。

16.4 Push and PR

快速檢查完成且無阻斷性錯誤後：

- 立即推送工作分支。
- 立即開啟 PR。
- 不等待 Claude 重量級驗證。

PR 必須記錄：

- Task ID。
- BASE SHA。
- 實際修改檔案。
- 快速測試命令。
- 真實測試結果。
- 已完成範圍。
- 已知限制。
- 未執行的重量級測試。
- Claude review 所需資料及執行方式。

不得直接推送 main。

不得自行 merge PR。

---

17. Claude workflow

17.1 G0 for WE-01A

確認：

1. BASE 正確。
2. Production 檔案一致性。
3. window.__VH 相關 runtime 介面可取得。
4. __th 可提供完整1 m 高度取樣。
5. 靜態 WORLD lists、ROAD_NET、TREES、TREE_COLLIDERS 足以支持 dump。
6. 不使用全部 physicsWorld.bodies 作為靜態來源。
7. Dump schema 與實際資料相容。
8. 每個 preset 可取得連續兩次一致的 static fingerprint。
9. Footprint 精度標記正確。
10. 物理地面及 terrain region 分類正確。
11. 不需要 production 修改。
12. 兩檔 allowlist 及800行規模合理。
13. 快速測試與重量級驗證分工可行。

17.2 WE-01A PR review

Claude：

- 審查完整 diff。
- 重跑快速測試及 mutation tests。
- 生成正式雙 preset 單階段 dumps。
- 驗證各 preset 連續兩次 static fingerprint。
- 驗證資料完整性。
- 執行 WE-01A analyzer。
- 檢查面積守恆。
- 檢查畫質差異。
- 檢查 Site A、水域及道路保護。
- 驗證物理地面分類。
- 驗證60秒分析目標。
- 執行適用回歸測試。
- 確認 production 無修改。

完成審查及使用者驗收後，才可依 COLLAB 合併 WE-01A。

17.3 G0 for WE-01B

確認：

- WE-01A 已合併。
- 新 BASE 已固定。
- 分類資料契約穩定。
- Prefix sums 方法可行。
- 地塊搜尋時間預算合理。
- 完整1 m 高度網格足以支持地塊分析。
- 容量上界不會錯誤低估。
- 道路分析及裁定條件完整。
- 兩檔 allowlist 及1,000行規模合理。

WE-01B 必須獨立批准。

17.4 WE-01B PR review

Claude：

- 審查完整 diff。
- 重跑快速測試及 mutation tests。
- 執行完整雙 preset dump 分析。
- 每個 preset 驗證至少100個1 m 精確高度取樣點。
- 核對選定地塊占地及物理支撐。
- 核對 footprint 精度。
- 核對跨畫質共同住宅配置。
- 核對道路接點及連通性。
- 驗證25 ha、40棟及60棟裁定。
- 驗證完整分析時間。
- 完成三種畫質效能基準。
- 執行適用既有回歸測試。
- 確認 production 無修改。

若存在未確認資料，應保留 UNVERIFIED。

17.5 CI and merge

CI 接線由 Claude 負責。

CI 可執行輕量 analyzer tests。

大型 runtime dumps 及完整效能審計不要求加入每次一般 CI，除非 Claude 另行確認。

不得弱化既有測試。

本任務不修改正式遊戲資源，原則上不需要 CACHE bump 或新遊戲版本。

---

18. Final acceptance gates

18.1 WE-01A gates

Gate A1 — Scope integrity

僅新增允許的兩個 analyzer/test 檔案。

Gate A2 — Schema correctness

實際 runtime dumps 與資料契約一致。

Gate A3 — Classification correctness

L0–L5/LX 分類正確。

Gate A4 — Spatial conservation

土地面積守恆，障礙物不重複計算。

Gate A5 — Preset safety

共同土地分析使用跨畫質保守條件。

Gate A6 — Protection

Site A、水域、道路及其他保護區受到完整保護。

Gate A7 — Tests

所有必要快速測試及 mutation tests 通過。

Gate A8 — Performance

完整雙 preset dump 分析符合60秒目標，或取得明確批准例外。

Gate A9 — Deliverables

土地分類資料、SVG 及報告完整。

Gate A10 — User acceptance

使用者接受 WE-01A 結果。

Gate A11 — Static determinism

每個 preset 連續兩次獨立載入的 static fingerprint 一致。

Gate A12 — Source integrity

僅使用允許的靜態世界來源，且所有 footprint 具有明確精度標記。

18.2 WE-01B gates

Gate B1 — Scope integrity

僅新增允許的兩個 analyzer/test 檔案。

Gate B2 — Parcel correctness

地塊尺寸、原型比例、非重疊及障礙物檢查正確。

Gate B3 — Exact terrain validation

單階段1 m 高度及物理支撐驗證完成。

Gate B4 — Road correctness

道路幾何、接點、連通性及依賴工程分析正確。

Gate B5 — Feasibility correctness

25 ha、40棟及60棟均有獨立且有證據支持的裁定。

Gate B6 — Analyzer performance

完整分析符合60秒目標，或取得明確批准例外。

Gate B7 — Tests

所有必要快速測試及 mutation tests 通過。

Gate B8 — Runtime baseline

Claude 完成三種畫質效能基準。

Gate B9 — Production regression

正式遊戲資源無變更，適用回歸測試通過。

Gate B10 — Final report

完整地圖、容量、道路、可行性及後續工程報告已交付。

Gate B11 — User acceptance

使用者接受 WE-01 最終審計結果。

Gate B12 — Conservative capacity

最終住宅配置在兩種 preset 均合法，且容量不高於任一 preset 的對應獨立容量。

18.3 Unknown data acceptance

UNVERIFIED 是合法審計結果，但不能作為跳過必要資料取得工作的理由。

若重要資料無法取得，Claude 必須記錄：

- 已嘗試的取得方法。
- 無法取得的原因。
- 受影響範圍。
- 對可行性裁定的影響。
- 是否需要獨立前置工程。

不得在缺少必要 runtime 驗證時宣稱 FEASIBLE。

---

19. Follow-up decision matrix

Survey result| Proposed next decision
25 ha and 40 houses feasible| 維持 D3 基本規模
25 ha conditional| 優先批准必要土地或道路前置工程
40 feasible, 60 not feasible| 維持最低40棟目標
Urban land insufficient| 分散式填補或另行批准建築更新
Coastal land insufficient| 修訂候選區或研究海岸地形擴建
B2 flat but hillside design required| 優先研究獨立山區 terrain region
Road connection conditional| 制定獨立道路工程規格
Performance headroom insufficient| 研究區域串流及住宅 LOD
Data incomplete| 補足資料，不批准施工

後續 WE-02 至 WE-09 均需獨立規格及使用者批准。

WE-01A 或 WE-01B 通過，不代表已批准任何住宅、道路、地形或美術開發。

---

20. Remaining verification and limitations

Claude G0 re-review 已接受 v1.1 的主要分析架構、任務拆分、行數限制、schema version 及 mutation test coverage。

v1.2 已整合指定五項修正。

正式執行前仍須確認：

1. 單階段完整1 m dump 的實際檔案大小及輸出時間。
2. JavaScript / Python fingerprint 正規化契約。
3. DESKTOP_HIGH 連續兩次獨立載入的 fingerprint 一致性。
4. 各靜態 footprint 來源的精度標記。
5. 完整 analyzer 的60秒分析預算。
6. 修訂候選區多邊形及最終容量。

Claude 提供的90,000點約2 ms、物理地面尺寸、三次 PHONE_LOW 確定性結果及雙 preset 物件計數，均為本次 G0 re-review 的已報告證據。

ChatGPT 未獨立重跑上述 runtime 測試。

本次未取得完整正式 dumps，未執行 analyzer，未修改 repository，未登錄正式任務，未開啟 PR，未啟動 Gemini。

Status: DRAFT FOR CLAUDE G0 (v1.2).

Awaiting explicit user approval.

---

HANDOFF ChatGPT -> Claude

Task: WE-01 World Expansion Survey Specification v1.2 — WE-01A and WE-01B.

Base commit: 84319439243b51aa8d119e33eb62a0637feea887

Read: COLLAB.md, AGENTS.md, TASKS.md, DECISIONS D-013/D-021/D-026/D-027/D-049/D-050/D-050a.

Context:
Claude G0 re-review returned APPROVE WITH CHANGES for v1.1, requiring five corrections before registration.
v1.2 replaces the two-pass flow with single-stage 1 m terrain dumps, corrects global flat physical support, restricts occupancy extraction to static world sources, requires consecutive matching static fingerprints per preset, and uses conservative cross-preset capacity with explicit footprint precision.
The accepted WE-01A/WE-01B split, 800/1,000-line limits, schema version 1, feasibility targets, prefix sums and mutation test IDs M-A01 through M-B12 are retained.

Deliverable:
Confirm that the complete v1.2 specification satisfies all five G0 re-review corrections. Confirm the revised dump schema and fingerprint contract. Register WE-01A only after explicit user approval; WE-01B remains sequential and separately approved.

SPEC: Complete WE-01 World Expansion Survey Specification v1.2, sections 0–20, included in full immediately above this HANDOFF within the same copied text block.

Status: DRAFT FOR CLAUDE G0 (v1.2).

Previous review verdict: APPROVE WITH CHANGES.

Implementer: Gemini Stage 3 — analyzer only.

Runtime data acquisition and heavy verification: Claude.

No registration or implementation authorized.

HANDOFF -> Claude G0 confirmation.
