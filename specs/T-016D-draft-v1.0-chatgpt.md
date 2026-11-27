> Verbatim ChatGPT draft "T-016D — WE-01D Internal Streets, Conditional Capacity & Final Feasibility v1.0" (G0 proposal). Superseded where `specs/T-016D-spec-v1.0.md` (Claude conditions) says so; the body below is unchanged.

T-016D — WE-01D Internal Streets, Conditional Capacity & Final Feasibility v1.0

Status: DRAFT FOR G0
Protocol: COLLAB v3.6
Implementer: Gemini Stage 3 (proposed)
Reviewer: Claude
Risk: LOW
Volume: LARGE
Routing reason: Read-only offline analysis, deterministic algorithms, extensive automated validation, and no production modifications.

---

1. Baseline and dependencies

T-016A：Done，D-051d。
T-016B：Done，D-053，PR #114。
T-016C：Done，D-055，PR #118，merge 9f20b19。

Audit game BASE：

84319439243b51aa8d119e33eb62a0637feea887

Production release：

vh-2026-11-27-02

Development BASE：

Latest main after T-016D registration.

正式開工前由 Claude 確認完整 SHA。

1.1 Source documents

- COLLAB.md v3.6
- AGENTS.md
- TASKS.md
- DECISIONS.md D-013、D-021、D-026、D-027、D-051–D-055
- specs/WE-01-spec-v1.2.md
- specs/WE-01-v1.3-amendment.md
- specs/WE-01-v1.4-amendment.md
- specs/WE-01-v1.4-errata-T016B.md
- specs/T-016B-spec-v1.4.md
- specs/T-016C-spec-v1.0.md
- tools/fixtures/we01/SCHEMA_NOTES.md

已批准的 B/C 規格及 D-052–D-055 正式修正優先於早期草案。

本規格不修改已完成的 T-016A/B/C。

---

2. Scope

T-016D 負責：

1. 有界內部街道生成及驗證。
2. 新道路接入後的住宅容量分析。
3. C_conditional 及完整工程相依鏈。
4. 跨畫質共同住宅配置。
5. 最終土地面積分類與守恆。
6. 25 ha 有效土地裁定。
7. 40棟最低住宅目標裁定。
8. 60棟理想住宅目標裁定。
9. 整體 D3 裁定。
10. 最終 SVG 地圖及審計報告。
11. 完成 WE-01 剩餘驗收閘門。

本階段仍然是唯讀研究工具。

不得建造任何住宅、道路、地形或美術素材。

---

3. Formal evidence from T-016B/C

3.1 REVISED-v2 capacity

Region| Direct| Preliminary| Upper
B1| 5| 72| 100
B2| 0| 278| 329
B3| 17| 25| 40

合計直接容量22棟。

最低目標40棟。

理想目標60棟。

C_preliminary 與 C_upper 不代表實際可建造住宅數量。

3.2 Road results

Road| Length| Max grade| Result
C01| 312.5 m| 0%| Conditional
C02| 130 m| 0%| Conditional
H01| 431 m| 135.6%| NOT_FEASIBLE
H02| 597 m| 0%| Conditional
X01| 363 m| 0%| Conditional
U01| Existing| Existing| EXISTING_VERIFIED

H01 必須排除於合法內部街道來源。

C02、X01 已證明可在不依賴 AVE110 延伸的情況下連至主道路網。

AVE110_EXTENSION_REQUIRED 僅屬可選、尚未驗證的額外連接。

不得將該可選連接錯誤列為所有 C02／X01 地塊的必要工程。

C01 海灘侵占約4,994 m²。

C02 海灘侵占約224 m²。

依 D-054，海灘侵占須報告，但不直接造成道路分析失敗。

上述數值為正式分析證據，不得硬編碼為 T-016D 計算結果。

3.3 Regional external road access

Scenario| B1| B2| B3
INITIAL| CONDITIONAL| CONDITIONAL| FEASIBLE
ENVELOPE| FEASIBLE| CONDITIONAL| FEASIBLE
REVISED| FEASIBLE| CONDITIONAL| FEASIBLE

以上為外部道路接入裁定，不是住宅容量裁定。

---

4. Frozen scenario polygons

座標順序：

[xmin, xmax, zmin, zmax]

Scenario| B1| B2| B3
INITIAL| [90,390,930,1230]| [-900,-500,820,1070]| [-640,-340,-810,-610]
ENVELOPE| [-10,490,830,1330]| [-1000,-400,720,1170]| [-740,-240,-910,-510]
REVISED| [-10,390,880,1330]| [-950,-450,770,1120]| [-640,-240,-860,-710]

Gross area：

INITIAL：250,000 m²。
ENVELOPE：720,000 m²。
REVISED：415,000 m²。

polygon_revision = 2。

唯讀匯入 T-016B 的 SCENARIOS 及座標轉換函式。

不得重新定義或移動候選區。

ENVELOPE 只代表審計上界情境，不代表已批准的施工範圍。

---

5. Internal street design constraints

沿用 v1.4 §D，並採 Claude 前輪 G0 建議修正候選預算。

5.1 Fixed parameters

Parameter| Value
每區每情境最多選定街道| 3
最短候選長度| 30 m
最大候選長度| 150 m
候選長度| 30/60/90/120/150 m
車行道寬度| 7 m
每側人行道| 2 m
走廊總寬| 11 m
走廊半寬| 5.5 m
最大縱坡| 6%
中心線取樣間距| ≤3 m
來源道路起點間距| 25 m
地形資料| 完整1 m runtime grid
R7 最大距離| 2 m
R7 最小連續接近長度| 8 m
候選檢查預算| 1,024 / region / scenario

每區最多450 m 內部街道。

每情境三區最多9條、1,350 m。

不同情境獨立計算。

1,024 候選預算為本輪待 G0 及 Martin 批准的修正。

5.2 Candidate budget justification

Claude 前輪 G0 實測：

Scenario| B1| B2| B3
INITIAL| 210| 130| 280
ENVELOPE| 480| 170| 1,010
REVISED| 420| 150| 340

全網路未過濾候選數約8,480。

原256候選預算會使5個區域情境提前耗盡。

修正：

只評估起點位於對應情境多邊形內（包含邊界）的候選。

不符合區域過濾的候選不計入預算。

每區每情境最多1,024個候選。

實際數量須依已合併 T-016C 幾何重新計算。

不得硬編碼上述預估數量。

若預算耗盡：

SEARCH_BUDGET_EXHAUSTED。

不得將搜尋預算耗盡視為不可行證明。

---

6. Candidate generation

只允許直線街道。

合法來源：

- T-016B 已驗證 AVE_0 主 GROUND 分量的既有道路。
- T-016C 幾何合法且具有完整條件連通鏈的候選道路。
- U01 既有合法重用道路。

來源 ID 必須穩定且去重。

不得使用：

- H01。
- UNVERIFIED 道路。
- ELEVATED／RAMP 的未驗證接點。
- 未驗證 AVE110 延伸工程。
- 已生成的內部街道作為下一層生成來源。

不得遞迴生成街道。

沿來源道路實際中心線每25 m 生成候選起點，保留合法端點。

以局部切線的左右垂直方向生成候選。

候選長度固定30、60、90、120、150 m。

確定性排序：

1. 來源道路 ID。
2. 沿道路累積距離。
3. 左側、右側。
4. 長度由短至長。

Claude G0 須凍結端點、曲線轉折及重複候選的處理方法。

---

7. Internal street legality

每條候選街道必須檢查：

- 完整11 m 走廊。
- 完整1 m 地形覆蓋。
- 物理支撐。
- 最大縱坡≤6%。
- 不侵占 Site A。
- 不穿越水域。
- 不穿越未批准拆除的既有建築。
- 不侵占未知或未驗證土地。
- 不侵占保留的直接住宅地塊。
- 不與其他選定街道非法重疊。
- 合法接點的必要交集。
- 完整連至 AVE_0 主道路分量的相依鏈。

接點及道路重疊處理須沿用 T-016C 已修正的 D-054a 規則。

與接入道路的必要重疊必須為從接點開始的單一連續區段，不得離開後重新進入。

內部街道的最大合法接點重疊長度須由 Claude G0 根據11 m 走廊及垂直接入幾何另行確認，不得直接將100 m 當成無條件許可。

街道走廊原則上須位於對應區域內。

若接入既有道路所需的局部走廊位於區域外，須：

- 有完整審計資料。
- 明確標記外部接入部分。
- 不計入區域有效土地面積。
- 不得以此例外建立長距離區域外街道。

Claude G0 須確認此例外的幾何界線。

海灘規則：

T-016C 已確認的 C01／C02 海灘侵占照實保留。

新生成內部街道不得自動沿用海灘侵占許可；涉及海灘的新增工程須另列條件及待批准事項。

所有街道均為尚未建造的工程。

不得標記為 EXISTING_VERIFIED。

---

8. B/C public interface reuse

不得重新實作 T-016B 的核心容量演算法。

唯讀重用：

- SCENARIOS
- PROTOTYPES
- spec_to_internal
- internal_to_spec
- load_dumps
- build_masks
- geom_valid
- build_road_graph
- corridors_from_graph
- evaluate_access
- place_layout
- common_layout

以上為 T-016B 已登記的公開介面。

Claude G0 必須對照實際合併版本確認函式簽章及可重用範圍。

T-016C 的 road_survey.json 中 candidate_corridors 使用 T-016B corridors_from_graph 相容格式。

新增內部街道須轉換為相容走廊格式。

不得修改原始 B/C 模組或其既有輸出。

若公開介面不足：

停止並回報 Claude。

不得擅自匯入未批准的私有函式或複製整份既有演算法。

---

9. Bounded street selection

採確定性貪婪搜尋。

9.1 Preserve direct layout

先載入並驗證 T-016B 的 C_direct 實際地塊配置。

所有已確認 DIRECT 地塊保留。

新道路及內部街道不得使原有直接地塊失去合法性。

若候選道路與直接地塊發生衝突，須明確記錄，並在保留直接配置的分析方案中排除該道路。

不得悄悄刪除直接地塊以提高條件容量。

9.2 Candidate scoring

對合法候選街道，計算其可新增的 R7 合格幾何合法中心數。

排序：

1. 新增合法候選中心數較多。
2. 街道長度較短。
3. 固定候選排序。

此分數僅用於街道選擇，不是實際住宅容量。

不得將重疊候選中心數直接當成住宅棟數。

9.3 Iterative selection

每次選定一條街道後：

- 更新道路占地遮罩。
- 排除與街道重疊的住宅候選。
- 更新剩餘合法候選街道。
- 更新可新增道路接近候選。
- 保留所有直接地塊。
- 重新確認共同畫質合法性。

每區最多3條。

無新增有效候選時允許提前停止。

不得搜尋所有街道組合。

不得因貪婪方法未找到足夠配置就宣稱不存在其他合法配置。

9.4 Performance

允許：

- Prefix sums。
- Compact raster masks。
- Bitwise masks。
- Spatial pruning。
- 預先計算候選街道走廊占地。
- 重用 T-016B geom_valid。
- 重用 ENVELOPE 遮罩並依完整地塊邊界裁切。
- 快取候選道路接近結果。

不得：

- 對每個候選重新執行完整 B/C analyzer。
- 對每個候選重建完整區域 raster。
- 使用無界全域最佳化。
- 以近似方法高估合法容量。

Claude G0 須確認1,024候選預算下的實際時間複雜度及可行性。

---

10. Conditional residential capacity

10.1 Prototype rules

Prototype| Footprint| Parcel| Area
R01| 32×24 m| 42×34 m| 1,428 m²
R02| 36×30 m| 48×42 m| 2,016 m²
R05| 14×12 m| 24×22 m| 528 m²
R08| 28×14 m| 38×24 m| 912 m²

R08 一整排計為一棟、四戶。

B1：

R02 至少50%，其餘 R01。

B2：

只使用 R05，標記 PROXY。

平地 R05 容量不得被描述為已驗證山坡住宅工程。

B3：

R01、R05、R08 各至少20%。

比例依最終棟數使用整數 ceiling。

10.2 Conditional parcel requirements

條件地塊必須具備：

- 完整合法地塊尺寸。
- 非重疊配置。
- 合法地形及物理支撐。
- 合法道路接近。
- 完整工程相依鏈。
- 原型比例。
- 保護區及障礙物檢查。
- 兩種 preset 的共同合法性。

條件原因可包括：

CANDIDATE_ROAD_REQUIRED。
INTERNAL_STREET_REQUIRED。
FOUNDATION_REQUIRED。

FOUNDATION_REQUIRED 不得因單純有道路接近而自動成為已驗證可建地塊。

若缺乏足夠地基工程證據，仍須保留 UNVERIFIED。

10.3 Inclusive capacity

C_conditional 必須包含 C_direct。

C_additional = C_conditional - C_direct。

不得將 C_direct + C_conditional 當成總容量。

必須輸出實際配置及地塊 ID。

不得只輸出理論數字。

若有多個合法條件配置，須以確定性規則選擇符合原型比例的配置。

原型比例必須針對整個最終配置驗證，而非僅驗證新增地塊。

10.4 Dependencies

每個條件地塊至少記錄：

- parcel_id
- scenario_id
- region_id
- prototype_id
- orientation
- bounds
- source_road_id
- internal_street_id（如適用）
- external_connection_id
- required_engineering
- dependency_chain
- verification_status
- reasons

必要道路或工程相依鏈被移除時，相關地塊不得繼續計入已確認條件容量。

---

11. Cross-preset common layout

共同配置使用：

障礙物聯集。

可用土地交集。

完整地形及物理支撐的共同驗證。

同一共同配置中的道路及住宅須在 PHONE_LOW、DESKTOP_HIGH 均合法。

分別輸出：

C_phone_low。
C_desktop_high。
C_common。

沿用 R5：

各 preset 容量不得低於已驗證共同配置的棟數。

若獨立貪婪結果較低，採已驗證共同配置作為該 preset 的合法下界。

不得直接取兩個獨立配置棟數的最小值冒充共同配置。

C_upper 沿用 T-016B 真正上界。

新增街道可縮小特定配置的可用空間，但不得將單一街道配置造成的容量下降誤當成整體世界不可行的上界證明。

---

12. Land accounting

依 WE-01 v1.2 §7.8 及 T-016B 正式面積契約。

各情境輸出：

- A_gross
- A_direct
- A_conditional
- A_protected
- A_unavailable
- A_unknown
- A_eligible

A_gross 為候選區聯集面積。

A_eligible 為符合用途的直接及條件土地聯集。

A_eligible 不得重複加入面積總和。

面積分類必須互斥。

每區面積守恆誤差≤1 m²。

新增道路、既有道路、住宅地塊、公園及其他用途不得重複計算。

道路走廊占地須由相應住宅可用面積中排除。

Site A 及其保護區不得計入有效住宅規劃土地。

既有道路及符合用途的保留公園可依原規格列入相容土地用途。

海灘侵占須獨立揭露，不得自動將整片海灘轉為可建住宅土地。

住宅15–30%、道路20–30%、公園25–40%等比例維持規劃參考，不是硬性可行性門檻。

---

13. Final feasibility verdicts

每個情境獨立輸出：

FEASIBLE。

CONDITIONAL。

NOT FEASIBLE WITHIN AUDITED BOUNDARIES。

UNVERIFIED。

不得硬編碼預期結果。

13.1 25 ha target

25 ha = 250,000 m²。

須同時考量：

- Gross area。
- 已驗證有效土地面積。
- 三區合法住宅配置。
- 道路及其他必要用途。
- 保護區。
- 工程相依鏈。
- 未驗證資料。

直接有效土地及必要條件皆符合時，才可裁定 FEASIBLE。

依賴具體、已驗證但未批准或未建造的工程時，裁定 CONDITIONAL。

只有可靠上界或明確限制證明不足時，裁定 NOT FEASIBLE。

資料不足或搜尋未完成時，保留 UNVERIFIED。

13.2 Minimum 40-building target

Region| Minimum
B1| 10
B2| 12
B3| 18
Total| 40

三區必須各自達標。

不得以 B2 超額住宅抵銷 B1 或 B3 的不足。

直接容量全部達標，且相關必要條件已驗證，才可裁定 FEASIBLE。

需要條件工程達標時，裁定 CONDITIONAL。

搜尋未找到足夠住宅但上界仍可能達標時，裁定 UNVERIFIED。

13.3 Ideal 60-building target

Region| Ideal
B1| 14
B2| 18
B3| 28
Total| 60

沿用相同的區域獨立裁定規則。

60棟是理想目標，不是最低 D3 必要條件。

13.4 Road access

繼承 T-016C 已驗證外部道路裁定。

加入 T-016D 內部街道及住宅實際接入證據。

區域外部道路 FEASIBLE 不代表所有住宅均可直接接入。

若住宅配置依賴尚未建造道路，必須保留 CONDITIONAL。

13.5 Overall D3

D3 必要條件：

- 25 ha 有效土地。
- 三區最低40棟目標。
- 三區道路連通。

裁定優先順序：

NOT FEASIBLE > UNVERIFIED > CONDITIONAL > FEASIBLE。

60棟理想目標獨立報告。

分析工具驗收 PASS 與 D3 可行性裁定必須分開。

即使最終 D3 為 UNVERIFIED 或 NOT FEASIBLE，只要分析正確、完整且通過測試，T-016D 仍可完成工具驗收。

---

14. Final deliverables

14.1 internal_streets.json

新增獨立產物，避免覆寫 T-016C 的 road_survey.json。

至少包含：

- scenario_id
- region_id
- street_id
- start/end
- source_road_id
- length
- corridor_width
- corridor_geometry
- max_grade
- obstacle_intersections
- external_connection
- dependency_chain
- dependent_parcel_ids
- verification_status
- rejection_reasons
- candidate_count
- checked_count
- selected_count
- search_budget_exhausted

14.2 conditional_parcels.json

完整住宅配置：

DIRECT 與新增條件地塊。

每個地塊的原型、方向、位置、面積、驗證狀態及相依工程。

14.3 feasibility.json

- 三情境土地面積。
- 25 ha 裁定。
- 40棟裁定。
- 60棟裁定。
- 各區容量。
- 各 preset 容量。
- 跨畫質共同容量。
- 道路接入。
- D3 裁定。
- 必要工程。
- 未確認事項。
- 裁定證據。
- BASE、fingerprints、schema_version、polygon_revision。
- A/B/C 正式產物雜湊及版本。

14.4 world_survey.svg

正式 SVG 至少包含：

- X/Z 座標軸。
- 比例尺。
- 圖例。
- 三個住宅區。
- 凍結情境多邊形。
- DIRECT 地塊。
- CONDITIONAL 地塊。
- 既有道路。
- 候選外部道路。
- 選定內部街道。
- H01 失敗路線。
- Site A 保護區。
- 海灘及水域。
- 未確認區域。
- BASE 及 static fingerprints。
- Preset／CROSS_PRESET_COMMON 標記。

建議以 REVISED-v2 為主圖，INITIAL 與 ENVELOPE 另作分區圖或附圖。

不得將示意道路畫成已建造道路。

不得以概念圖冒充 runtime 審計結果。

14.5 survey_report.md

完整最終報告：

- Executive summary。
- A/B/C/D 審計結果。
- 三區土地面積。
- 三區住宅配置。
- 直接與條件容量。
- 外部及內部道路工程。
- 25 ha／40／60裁定。
- 整體 D3。
- 海灘侵占及保護區。
- 必要工程及未確認事項。
- 效能基準引用。
- 後續 WE-02–WE-09 工程建議。

所有數值須與 JSON 產物一致。

---

15. Data integrity

正式資料沿用 D-051e。

PHONE_LOW static_fingerprint：

e473d222db998487e5fcfb187349e5006e6f619c1d15cca6bae1a2ee380352aa

DESKTOP_HIGH static_fingerprint：

52653bc578411a9eda9b314581bb16f45f3cb4eb1be623f9d39dc21ade365482

交接驗證包含：

- Game BASE。
- 兩個 static fingerprints。
- A/B/C analyzer versions。
- Handoff schema versions。
- polygon_revision。
- 正式輸入產物 SHA-256。

Dump file_sha256 不得作為跨載入的唯一相容性判斷鍵。

若實際輸入產物與宣告雜湊不符，須拒絕。

若同一靜態世界重新載入，只因 dump file_sha256 改變，不得錯誤拒絕。

所有確定性產物須可重現。

執行時間、記憶體及其他非確定性量測欄位分開保存。

---

16. Regression tests

保留 v1.2、v1.3、v1.4 中屬於最終容量、內部街道及裁定的所有測試。

重點覆蓋：

D01：固定情境及座標格式。

D02：每區最多3條街道。

D03：30–150 m 候選長度。

D04：1,024候選預算及區域過濾。

D05：確定性候選排序及去重。

D06：合法來源道路及完整外部連通。

D07：H01 排除及 AVE110 可選相依。

D08：11 m 走廊、6%坡度、完整1 m 地形。

D09：障礙物、水域、Site A 及物理支撐。

D10：街道與住宅地塊非重疊。

D11：R7 2 m／8 m 接近規則。

D12：街道選擇及占地更新。

D13：C_direct 保留。

D14：C_conditional 包含 C_direct。

D15：原型比例及 R08 計數。

D16：跨畫質共同配置。

D17：道路及住宅面積互斥。

D18：土地面積守恆。

D19：25 ha 四種裁定。

D20：40棟各區獨立門檻。

D21：60棟理想目標。

D22：D3 優先順序。

D23：搜尋耗盡不得冒充不可行證明。

D24：資料來源及 fingerprints。

D25：JSON、SVG、Markdown 報告完整性及一致性。

D26：三次重跑確定性。

D27：海灘侵占獨立揭露。

D28：FOUNDATION_REQUIRED 不得冒充已驗證地基。

以上可整合至既有測試 ID，但不得省略任何必要斷言。

Claude G0 須確認原 B10、B11、B15、B17–B21、C06–C17 及相關測試的完整分配。

---

17. Mutation tests

至少捕捉：

- 允許第4條街道。
- 允許超過150 m。
- 接受區域外起點。
- 使用 H01 或未驗證來源。
- 允許街道侵占直接地塊。
- 忽略街道坡度。
- 忽略 Site A。
- 將搜尋耗盡判定為不可行。
- 移除必要工程相依鏈。
- 重複加總直接與條件容量。
- 以其他區超額容量抵銷區域缺額。
- 將 R08 計為四棟。
- 將尚未建造道路標記為既有。
- 只驗證單一 preset。
- 忽略道路占地。
- 將住宅比例參考當成硬性門檻。
- 接受錯誤 fingerprint。
- 將60棟理想目標誤當成 D3 必要條件。
- 將未驗證地基工程計入已確認條件容量。

保留原 M-C04–M-C09，以及適用的 M-B02、M-B03、M-B04、M-B05、M-B07、M-B08、M-B09、M-B10、M-B11、M-B13 等回歸要求。

不得使用僅由 analyzer 本身相同邏輯產生的結果作為唯一 oracle。

---

18. Allowlist

Branch：

gemini/T-016D-we01d-final-feasibility

Proposed two-file allowlist：

tools/test/we01d_feasibility_analyzer.py

tools/test/we01d_feasibility_analyzer_check.py

Python standard library only。

唯讀匯入已批准的 A/B/C 公開介面。

檢查腳本可唯讀匯入 E3 已批准的 WE-01A 測試鷹架。

不得修改：

- Existing analyzers。
- Existing checks。
- Fixtures。
- Extractor。
- index.html。
- sw.js。
- CACHE。
- Production assets。
- CI。
- Collaboration documents。

Claude G0 若認為兩檔範圍不足，須在開工前提出獨立方案，不得由實作者自行擴張。

---

19. Proposed line budget

依 D-054a，Claude 對 T-016B/C 的早期行數估計偏低約35–40%。

實際結果：

T-016A：1,043行。
T-016B：1,866行。
T-016C：1,372行。

T-016D 原1,050行上限仍未被正式取代。

本輪建議：

Component| Proposed ceiling
Analyzer| 1,450
Check script| 750
Combined| 2,200

Target：1,900 combined lines。

此為待批准提案，不是現行授權。

若採2,200行，WE-01 全部實際已用行數加 D 上限為6,481行。

Claude G0 須以實際 B/C 介面、街道搜尋複雜度及報告需求重新估算。

不得僅為維持原1,050行而壓縮程式碼或刪除測試。

若2,200行仍不足，應在實作前考慮拆分最終報告或其他可獨立驗收部分。

強制行數回報：

- 約800行。
- 約1,500行。
- 完成前。

超過任何核准子上限或總上限，立即停止並返回 Claude。

---

20. Performance budget

T-016B 正式耗時6.3秒。

T-016C 正式耗時2.1秒。

B+C 約8.4秒。

本輪建議保留原 WE-01 完整 B+C+D 分析60秒目標。

因此 D 階段參考剩餘時間約51.6秒。

正式 Gate 以相同環境下的完整實測為準，不以不同時間的估計值相加取代。

包括：

- 正式雙 preset 輸入。
- 三情境九區域分析。
- 內部街道搜尋。
- 條件住宅配置。
- 最終裁定。
- JSON、SVG、Markdown 輸出。

若無法達成60秒：

Claude 須提出實測時間、瓶頸、優化方案及明確例外。

只有 Martin 可批准效能例外。

不得降低地形、道路或住宅驗證精度以換取時間。

---

21. Claude final independent verification

Claude 負責：

1. 正式雙 preset dumps 及產物鏈驗證。
2. 內部街道幾何、坡度、占地及接點獨立驗證。
3. 所有選定住宅地塊重新驗證。
4. 跨畫質共同配置。
5. 原型比例。
6. 面積守恆。
7. 工程相依鏈。
8. 25 ha／40／60及 D3 裁定。
9. 完整分析時間。
10. Mutation tests。
11. 最終報告及 SVG。
12. Production integrity。
13. D-013 及共享 PR lock。
14. CI wiring。

不得將 Gemini 自報 PASS 當成 Claude 獨立驗證。

21.1 Final Gate B8

完成 WE-01 v1.2 §13 的正式效能基準。

Presets：

PHONE_LOW。
TABLET_MED。
DESKTOP_HIGH。

Locations：

B1：(240,1080)。
B2：(-700,945)。
B3：(-490,-710)。
Site A：(-501,-790)。
CBD：(-60,0)。
Suburbs：(-1060,-238)。

必要時使用最近可驗證位置並記錄原因。

固定日夜、相機、畫質及 Site A 狀態。

保留原120暖機後畫面取樣要求、物理五組成對量測、900步暖機、360步記錄及 baseline control 規則。

記錄：

- Draw calls。
- Triangles。
- Bodies/shapes。
- Physics step time。
- Meshes/geometries。
- Geometry buffer bytes。
- Materials/textures。
- Texture memory estimate。
- World initialization。
- 建築、樹木、道路及碰撞體數量。
- LOD。
- Main/mirror/shadow passes。

Production 零變更限制全部保留。

不得將 headless FPS 冒充實機 FPS。

不得宣稱尚未建造的住宅已達30 FPS。

---

22. Final WE-01 acceptance gates

B1：Scope integrity。
B2：Parcel correctness。
B3：Exact terrain validation。
B4：Road correctness。
B5：Feasibility correctness。
B6：Analyzer performance。
B7：Tests。
B8：Runtime baseline。
B9：Production regression。
B10：Final report。
B11：Martin acceptance。
B12：Conservative capacity。

A/B/C 已完成的證據可引用，但涉及 D 新增配置的部分須重新驗證。

B11 必須在 Martin 收到最終地圖、數據及報告後獨立接受。

不得以 PR merge 自動取代最終研究成果驗收。

---

23. Follow-up decision matrix

若25 ha及40棟可行：

保留 D3 基本規模。

若40棟可行但60棟未達標：

優先40棟方案，不強制擴張至60棟。

若道路條件是主要瓶頸：

優先提出獨立道路工程規格。

若 B2 平地代理容量充足但山坡住宅設計未驗證：

優先研究山區 terrain region 及地基工程。

若 B3 容量不足：

研究分散式填補或另行批准既有建築更新。

若海岸工程涉及海灘：

提供保留海岸景觀與道路改線方案，交 Martin 選擇。

若效能基準顯示餘裕不足：

先研究區域串流、住宅 LOD 及資產預算。

若資料不足：

補足必要資料，不批准施工。

WE-02–WE-09 均須獨立規格、G0 及 Martin 批准。

---

24. G0 confirmation items

Claude 須確認：

1. 已合併 B/C 公開介面足以支援 D。
2. 1,024候選預算及區域過濾。
3. 實際道路來源及 H01 排除。
4. 內部街道接點重疊與區域外局部接入界線。
5. 直接地塊保留及候選道路衝突處理。
6. 共同配置與條件容量演算法。
7. 25 ha 面積分類及守恆。
8. 四種裁定及 D3 邏輯。
9. 新增產物 schema。
10. 2,200行建議上限是否合理。
11. 完整60秒分析目標。
12. 最終 B8 效能量測可行性。
13. 全部測試及 mutation tests 分配。
14. 最新 main SHA、D-013、PR lock。

本規格不授權實作。

---

HANDOFF ChatGPT -> Claude

Task: T-016D — WE-01D Internal Streets, Conditional Capacity & Final Feasibility v1.0

Base commit: latest main containing T-016C merge 9f20b19 and D-055; confirm full SHA before registration.

Read: COLLAB.md v3.6, AGENTS.md, TASKS.md, DECISIONS D-013/D-021/D-026/D-027/D-051–D-055, WE-01 v1.2/v1.3/v1.4, T-016B errata, registered T-016B/T-016C specifications, and merged analyzer interfaces.

Context:

T-016A/B/C are complete. REVISED-v2 direct capacity is 5/0/17, with 18 additional buildings required to reach the regional minimum targets. Four candidate external roads are conditionally viable; H01 fails the grade limit and U01 is existing verified.

T-016D completes the bounded internal-street search, conditional capacity, cross-preset layouts, land accounting, 25 ha/40/60 verdicts, D3, final SVG/report, and remaining WE-01 acceptance gates.

The proposed 1,024 candidate budget incorporates the earlier G0 recommendation. The proposed 2,200-line ceiling accounts for the documented 35–40% estimation bias. Both require G0 confirmation and Martin's approval.

Deliverable:

Perform G0 review, inspect the actual merged interfaces and formal data, resolve the remaining geometry and accounting details, confirm test allocation, line budget and runtime feasibility, and return the review verdict.

Register only after Martin explicitly approves the final specification.

SPEC: Complete T-016D v1.0 proposal in this message.

No implementation, construction, production modification or further WE-02–WE-09 authorization.

HANDOFF -> Claude G0 review.