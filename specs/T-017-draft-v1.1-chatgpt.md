WE-02 v1.1 — World Expansion Masterplan

Project: VICE HORIZON VI
Task ID: T-017
Proposed Decision: D-061
Status: DRAFT FOR G0 RE-REVIEW
Protocol: COLLAB v3.6
Previous version: WE-02 v1.0
G0 verdict on v1.0: APPROVE WITH CONDITIONS (C1–C8)
Priority: P1
Risk: LOW（規劃文件及離線產物工具）

1. 授權、角色及來源

1.1 授權

本規格以方案 B（ENVELOPE）為規劃方向，待 Martin 於登記時以自己的話確認，記為 D-061。

目前尚未正式登記或批准 WE-02 v1.1。

本規格不構成施工、遊戲程式修改或 WE-03 至 WE-09 的授權。

1.2 角色

- ChatGPT：設計擁有者，負責總體規劃、規格及修訂。
- Claude：獨立 G0 審查、規劃產物製作、驗證及 specs/we02/ 正式登記。
- Martin：規劃方向確認、正式批准及最終驗收。
- Codex／Gemini：本階段不指派。

Claude 擁有本階段確定性離線產物工具，不得將其交由 Gemini 實作。

1.3 必讀來源

- COLLAB.md v3.6
- AGENTS.md
- TASKS.md
- DECISIONS.md，尤其 D-013、D-026、D-027、D-051 至 D-060
- specs/WE-01-spec-v1.2.md
- WE-01 v1.3、v1.4 amendments
- specs/we01-final/survey_report.md
- specs/we01-final/feasibility.json
- specs/we01-final/world_survey.svg
- WE-01 B8、B10 正式驗證紀錄
- tools/fixtures/we01/e_formal/ 正式 JSON 產物

Audit Game BASE：

84319439243b51aa8d119e33eb62a0637feea887

正式登記前由 Claude 確認最新 main 完整 SHA、D-013 保護及共享 PR 鎖。

2. 任務目標

1. 凍結 ENVELOPE 規劃邊界。
2. 建立三區獨立住宅配置。
3. 選擇第一期40棟住宅配置。
4. 保留第二期累計60棟發展目標。
5. 建立分期道路工程依賴。
6. 建立土地利用及景觀保護規劃。
7. 建立後續串流及資產製作需求。
8. 產出確定性、可追溯的 Masterplan。

不重新執行完整 WE-01 審計，不改寫既有裁定。

3. 固定規劃範圍及座標契約

3.1 區域範圍

本規格區域表使用：

[xmin, xmax, zmin, zmax]

Region| Bounds| Gross area
B1| [-10,490,830,1330]| 250,000 m²
B2| [-1000,-400,720,1170]| 270,000 m²
B3| [-740,-240,-910,-510]| 200,000 m²
TOTAL| Union| 720,000 m²

polygon_revision = 2。

72 ha 為規劃外框，不等於新增72 ha 可行走土地，亦不等於遊戲世界邊界增加72 ha。

不得自行修改區域邊界。

3.2 座標格式

所有座標單位為 m。

規格格式：

bounds_spec = [xmin, xmax, zmin, zmax]

正式 JSON 內部格式：

bounds = [xmin, zmin, xmax, zmax]

bounds_internal = [xmin, zmin, xmax, zmax]

WE-01 正式地塊 JSON 的 bounds 與 bounds_internal 採內部格式；bounds_spec 採規格格式。

district_plan.json 必須明確區分兩種格式，保留原始欄位語義。

masterplan.md 使用規格格式。

masterplan.svg 使用正式 X/Z 多邊形及明確座標轉換。

不得以 AABB 取代旋轉地塊的實際多邊形。

Claude 須驗證座標轉換及 SVG 幾何一致性。

4. 正式審計基準

Region| A_direct m²| C_direct| C_conditional
B1| 134,557| 5| 21
B2| 213,525| 0| 67
B3| 53,187| 25| 25
TOTAL| 401,269| 30| 113

ENVELOPE D3 = CONDITIONAL。

40棟目標 = CONDITIONAL。

60棟目標 = UNVERIFIED。

C_conditional 已包含 C_direct，不得重複加總。

B2 的67棟均為 R05 平地代理配置，不代表山坡住宅工程已驗證。

5. 分期住宅計畫

Region| Phase 1| Phase 2 cumulative| Phase 2 additional
B1| 10| 14| 4
B2| 12| 18| 6
B3| 18| 28| 10
TOTAL| 40| 60| 20

Phase 1 為最低建設目標。

Phase 2 為累計理想目標，不是額外60棟。

第一期規劃配置已由 Claude G0 確認可從既有合法地塊選取。

實際施工仍受道路、地形、資產及效能等後續閘門限制。

不得使用其他區域超額容量抵銷任一區域不足。

第二期狀態：

- B1：CONDITIONAL。
- B2：CONDITIONAL，保留 PROXY 限制。
- B3：UNVERIFIED。
- 整體60棟目標：UNVERIFIED。

6. 住宅原型及比例

6.1 B1 Oceanfront Heights

面積25 ha。

Phase 1：

- R01：5棟。
- R02：5棟。

Phase 2 累計：

- R01：7棟。
- R02：7棟。

R02 不得低於50%。

建築高度方向：30–65 m。

美術方向：曲面陽台、玻璃、石材、海濱步道及棕櫚樹。

優先保留已審計的5棟直接地塊。

第一期使用 X01 及 ENVELOPE_B1_ST_0305 的道路依賴配置，可取得 R01 5棟、R02 8棟候選容量，滿足第一期5／5需求。

第二期必須增加 C02 及指定的額外內部街道，維持 CONDITIONAL。

6.2 B2 Vista Hills

面積27 ha。

Phase 1：R05 12棟。

Phase 2 累計：R05 18棟。

全部使用 R05 平地代理。

僅依賴 H02 的候選配置已有24棟，足以支援兩期數量需求。

H01 不可行，因此本方案 B2 對外連接只依賴 H02。

R06 山坡懸挑住宅目前無工程裁定。

R06 不得直接沿用 R05 的地塊、地基或碰撞可行性結論。

建築高度方向：5–12 m。

美術方向：階梯式地基、懸挑露台、山景及觀景平台。

兩期均保留 CONDITIONAL 及 PROXY 狀態。

6.3 B3 Palmwood Quarter

面積20 ha。

Phase 1：

- R01：4棟。
- R05：10棟。
- R08：4棟。

Phase 2 累計目標：

- R01：6棟。
- R05：16棟。
- R08：6棟。

三種原型各不得低於20%。

R08 一棟為四戶，不得計作四棟。

建築高度方向：8–30 m。

美術方向：混合住宅、社區公園及林蔭街道。

第一期從既有25棟直接配置中選取18棟。

第二期缺口：

Prototype| Target| Verified| Deficit
R01| 6| 5| 1
R05| 16| 15| 1
R08| 6| 5| 1
TOTAL| 28| 25| 3

第二期維持 UNVERIFIED。

缺口為三種原型各缺1棟，必須另案搜尋。

不得以未驗證預留地塊補足棟數。

7. 地塊選擇規則

保留 WE-01 正式 parcel_id、prototype_id、座標、方向、多邊形及完整依賴鏈。

優先順序：

1. 已驗證直接地塊。
2. 符合該期道路依賴的條件地塊。
3. 可形成連續街景的地塊群。
4. 可保留公園、海岸及景觀的地塊群。
5. 穩定 parcel_id 排序。

每個選定地塊的道路及街道依賴必須包含於該期必要工程集合。

第二期為累計配置，須包含第一期已選地塊。

不得為增加容量移動既有直接地塊。

正式多邊形比對必須正確處理旋轉地塊。G0 已確認正式資料中有22個旋轉地塊。

若無法滿足原型比例、幾何、道路或分期累計條件，停止並回報。

未驗證預留地塊不得計入已確認配置。

8. 土地利用及景觀保留

概念性土地利用參考：

Use| Conceptual reference
Residential| 25%
Roads and sidewalks| 25%
Parks and landscape| 30%
Public and community facilities| 20%

上述比例僅為概念，不是必須達成的比例，亦不是驗收硬門檻。

WE-01 ENVELOPE 實際審計數據：

- A_direct：401,269 m²，占外框約55.7%。
- A_new_road：18,568 m²，占外框約2.6%。

A_direct 不等於已建造住宅面積。

A_new_road 為 WE-01 完整 ENVELOPE 候選配置數據，不得直接沿用為 WE-02 第一期或第二期道路面積。

公園與公共設施不是 WE-01 審計土地分類。

其標籤僅代表對剩餘土地的規劃保留指定，不代表已審計或已建造面積。

規劃保留標籤不得改寫原始土地分類。

分期方案須重新計算道路走廊聯集面積，並以互斥分類驗證面積守恆誤差≤1 m²。

不得重複計算住宅、道路、景觀或公共設施。

海灘、水域、Site A、既有建築及未驗證土地須獨立呈現。

公共設施只預留空間，本階段不新增商店、學校、NPC 或任務系統。

9. 外部道路規劃

X01

- 長度：362.908 m。
- 車行道：7 m。
- 走廊總寬：11 m。
- 最大設計縱坡：6%。
- 最小曲線半徑：25 m。
- 第一期必要。
- 狀態：CONDITIONAL_VERIFIED。

H02

- 長度：597.306 m。
- 車行道：8 m。
- 走廊總寬：12 m。
- 最大設計縱坡：9%。
- 最小曲線半徑：18 m。
- 第一期必要。
- B2 唯一規劃對外接入道路。
- 狀態：CONDITIONAL_VERIFIED。

C02

- 長度：130 m。
- 車行道：7 m。
- 走廊總寬：11 m。
- 最大設計縱坡：6%。
- 最小曲線半徑：25 m。
- 第一期不需要。
- B1 第二期必要。
- 海灘侵占：224 m²。
- 狀態：CONDITIONAL_VERIFIED。

施工前須確認海灘及景觀保護方案。

C01

保留原始17 m 車行道設計研究。

ENVELOPE 配置因與 B1_R02_005 直接地塊衝突而排除。

第一期及第二期均不得納入 C01。

未來改線須另案研究，不得直接刪除或移動衝突地塊。

H01

NOT_FEASIBLE。

最大已量測坡度135.633%。

第一期及第二期均不得使用原始路線。

替代山區道路須另行批准研究。

U01

既有道路，保留並利用。

不得重複計入新增道路長度。

AVE_110

可選延伸，UNVERIFIED。

不列入本規劃兩期必要道路。

10. 內部街道及分期

10.1 WE-01 已驗證候選集合

B1：

- ENVELOPE_B1_ST_0085
- ENVELOPE_B1_ST_0305
- ENVELOPE_B1_ST_0115

B2：

- ENVELOPE_B2_ST_0010
- ENVELOPE_B2_ST_0040
- ENVELOPE_B2_ST_0140

B3：無新增已選定街道。

六條候選街道均長150 m，總長900 m。

全部維持 CONDITIONAL_VERIFIED，尚未建造。

10.2 第一期必要街道

B1：

ENVELOPE_B1_ST_0305。

B2：無新增內部街道。

B3：無新增內部街道。

第一期合計1條內部街道，150 m。

10.3 第二期必要街道

保留第一期街道，另從以下兩條選擇其一：

- ENVELOPE_B1_ST_0085
- ENVELOPE_B1_ST_0115

Claude 依合法地塊配置及完整依賴鏈選擇，正式產物須記錄選定 ID。

不得同時納入兩條作為第二期必要工程。

第二期累計2條內部街道，300 m。

其餘四條候選街道不列入兩期必要工程。

10.4 工程參數

- 車行道：7 m。
- 每側人行道：2 m。
- 走廊總寬：11 m。
- 最大縱坡：6%。
- R7 距離≤2 m。
- R7 連續接近長度≥8 m。

所有道路與街道在正式施工前不得標記為已存在。

11. 分期道路工程量

11.1 第一期

Road| Length
X01| 362.908 m
H02| 597.306 m
ENVELOPE_B1_ST_0305| 150.000 m
TOTAL| 1,110.214 m

第一期不使用 C02。

依現有審計配置，第一期候選道路海灘侵占為0 m²。

11.2 第二期新增

Road| Length
C02| 130.000 m
ST_0085 或 ST_0115| 150.000 m
Additional| 280.000 m
Cumulative| 1,390.214 m

第二期 C02 海灘侵占224 m²。

此數字不代表未來 B3 額外地塊研究不會需要其他工程。

11.3 原始參考數據

WE-01 優先外部候選道路 X01、C02、H02 合計1,090.214 m。

加上六條候選內部街道為1,990.214 m。

此數字保留為原始工程量參考，不是 WE-02 分期施工量。

各期新增道路走廊須重新計算聯集面積，不得直接相加重疊走廊。

未來施工任務須獨立驗證路面、地形、碰撞、車輛通行、交通 AI 及導航路線。

12. 景觀及保護規則

Site A 保護範圍：

X：[-561,-441]

Z：[-831,-753]

保護面積：9,360 m²。

WE-01 ENVELOPE 地塊與保護區重疊面積為0。

WE-02 選定地塊及道路仍須獨立驗證保護區侵占面積為0。

B1 保留海濱步道及海灘景觀。

C02 的224 m² 海灘侵占延至第二期工程處理。

B2 保留山體輪廓，不得預設大面積削平山區。

B3 保留既有城市格網，採用街廓填充及社區景觀改善。

既有建築拆除、海岸填地、地形改造均須獨立授權。

13. 建築原型庫需求

ID| Prototype
R01| Urban Apartment
R02| Curved Luxury Tower
R03| Twin Tower
R04| Terraced Residence
R05| Modern Detached Villa
R06| Cantilever Hillside Villa
R07| Pitched Roof House
R08| Rowhouses
R09| Art Deco Residence
R10| Mixed-use Residence

第一期優先 R01、R02、R05、R08。

其餘原型為後續資產庫需求，不自動增加第一期施工範圍。

所有原型須具備統一尺度、材質規格、LOD、碰撞策略及夜間表現。

Site A 僅作為美術技術參考，不得直接以商業及辦公立面作為住宅美術驗收標準。

14. 效能及串流需求

後續 WE-03 須獨立制定：

- 區域載入與卸載策略。
- Near、Mid、Far LOD。
- Instancing 與材質共用。
- 紋理及 GPU 記憶體預算。
- 碰撞體啟用範圍及池化。
- 載入卡頓控制。
- 日夜光影成本。
- 道路及建築串流一致性。

最低實機效能目標：

PHONE：30 FPS。

TABLET：30 FPS。

優先驗收裝置：S26 Ultra、Tab S11。

量測須包含平均 FPS、最近60秒最低1秒 FPS、畫質及載入卡頓。

WE-01 B8 headless 數據只代表既有遊戲基準，不代表新增住宅達30 FPS。

本階段不凍結未經量測的 draw call、三角形、VRAM 或物理時間預算。

正式預算由後續 WE-03 規格及 Claude 獨立驗證建立。

15. 正式交付物及工具權限

15.1 規劃產物

正式批准後，由 Claude 製作及登記於 specs/we02/：

1. masterplan.md：完整總體規劃及工程順序。
2. district_plan.json：三區邊界、地塊 ID、原型、多邊形、分期、狀態、依賴及預留土地。
3. masterplan.svg：正式 X/Z 座標地圖，區分兩期住宅、道路、保護範圍及未驗證項目。
4. dependency_matrix.md：各區、道路、地形、資產及串流依賴。
5. we02_validation.md：獨立核對、來源雜湊、分期面積、限制及未解決問題。

15.2 確定性產物工具

明文允許 Claude 擁有的 tools/we02/ 離線工具。

用途僅限：

- 讀取 WE-01 正式審計產物。
- 選取符合本規格的地塊配置。
- 驗證分期依賴及多邊形。
- 計算分期道路聯集及土地面積守恆。
- 確定性產生 district_plan.json、masterplan.svg 及相關規劃產物。

限制：

- 僅使用標準函式庫。
- 不由 Codex 或 Gemini 實作。
- 不執行遊戲程式。
- 不修改 WE-01 分析器及原始裁定。
- 不修改遊戲檔案。
- 相同正式輸入應產生相同規劃輸出。
- 保留來源雜湊及驗證紀錄。

本階段仍屬文件及離線產物工具任務，不是 production 實作任務。

如需超出 tools/we02/ 及規劃產物範圍的程式修改，須停止並另行申請批准。

16. 驗收閘門

Gate| Requirement
MP01| ENVELOPE 三區座標與 WE-01 一致，座標格式轉換正確
MP02| 總規劃面積720,000 m²
MP03| 所有正式地塊 ID、原型及來源可追溯
MP04| 第一期各區10／12／18棟配置合法
MP05| 原型比例符合規則
MP06| 使用實際多邊形驗證住宅地塊無重疊，正確處理旋轉
MP07| Site A 侵占面積為0
MP08| 道路依賴鏈完整且連至已驗證主道路網
MP09| C01、H01、AVE_110 不誤列為兩期必要道路
MP10| B2 PROXY 狀態保留，R06 不誤標為已驗證
MP11| 第二期 B1/B2 CONDITIONAL、B3 UNVERIFIED；三種原型各缺1棟
MP12| 分期新增道路聯集面積重新計算，互斥分類守恆誤差≤1 m²
MP13| 地圖、JSON、規劃文件一致
MP14| Production 檔案差異為0
MP15| CACHE、存檔及遊戲行為不變
MP16| Claude G0 複核及 Martin 正式批准
MP17| Martin 最終規劃驗收
MP18| 每個選定地塊依賴鏈只含該期必要道路／街道，且不含 C01、H01

MP04 通過僅代表第一期規劃配置符合既有審計規則，不代表條件工程已完成。

第二期缺少工程證據或合法地塊的部分須保留 CONDITIONAL 或 UNVERIFIED。

不得因 MP01–MP18 通過而將 WE-01 D3 改為 FEASIBLE。

17. 後續任務路線

WE-03：區域串流與效能架構。

WE-04：外部道路工程。

WE-05：地形、地基與內部街道工程。

WE-06：住宅建築原型庫。

WE-07：B1 Oceanfront Heights 建設。

WE-08：B2 Vista Hills 建設。

WE-09：B3 Palmwood Quarter 建設及三區整合驗收。

以上均為建議任務分工，尚未授權。

每項工程須另行制定完整規格、實作者、效能預算及回歸測試。

高風險大型工程依 COLLAB §5.2 拆分成小型 PR。

Codex 為小量高風險任務預設實作者；Gemini Stage 3 為大量低風險任務預設實作者。實際指派由 Martin 決定。

18. 禁止事項

- 修改 index.html。
- 修改 sw.js 或 CACHE。
- 修改 vh_save。
- 新增遊戲道路或住宅。
- 修改地形或世界邊界。
- 刪除既有建築。
- 修改 WE-01 原始審計裁定。
- 未經批准啟動 WE-03 至 WE-09。
- 以 headless FPS 代替實機效能。
- 以未驗證預留地塊補足住宅容量。
- 將 CONDITIONAL_VERIFIED 道路標為已建造。

19. 未解決工程依賴

1. X01、H02、C02 及六條候選內部街道均為 CONDITIONAL_VERIFIED。
2. B2 全部住宅配置使用 R05 平地代理。
3. R06 尚無工程裁定。
4. H01 不可行，B2 本方案只依賴 H02 對外接入。
5. B1 第二期必須使用 C02，須處理224 m² 海灘侵占。
6. B3 第二期缺 R01、R05、R08 各1棟，須另案搜尋。
7. 新增住宅及道路的實機30 FPS 尚未驗證。
8. 第二期道路工程量不包含尚未確認的 B3 額外工程。

20. G0 複核要求

Claude 須確認：

- C1：D-061 正式授權程序。
- C2：座標格式及轉換。
- C3：tools/we02/ 工具範圍。
- C4：ChatGPT、Claude、Martin 角色。
- C5：兩期道路依賴及1,110.214／1,390.214 m 工程量。
- C6：MP04、MP06、MP12、MP18 修正。
- C7：土地利用概念與審計數據區分。
- C8：第二期狀態及三種原型各缺1棟。

同時核對第一期合法地塊選擇、第二期累計配置、保護區、道路聯集面積及正式來源完整性。

Claude 複核後回報 APPROVE、APPROVE WITH CONDITIONS 或 REVISE。

只有 Martin 正式批准完整規格並確認方案 B 後，Claude 才可依 D-061 登記 T-017。

END OF WE-02 v1.1 DRAFT.