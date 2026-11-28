WE-02 v1.0 — World Expansion Masterplan

Project: VICE HORIZON VI
Status: DRAFT FOR G0 REVIEW
Protocol: COLLAB v3.6
Proposed Task ID: T-017
Design Owner: ChatGPT
Reviewer: Claude
Implementer: N/A（本階段為設計及規劃文件，不涉及遊戲程式實作）
Priority: P1
Risk: LOW（本階段）；後續施工任務另行評估

1. 授權及來源

Martin 已選擇方案 B，採用 ENVELOPE 作為世界擴張規劃範圍，並同意進入 WE-02 設計階段。

此決定不等於批准 WE-02 v1.0、施工、遊戲程式修改或 WE-03 至 WE-09。

必讀文件：

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
- tools/fixtures/we01/e_formal/ 中對應的正式 JSON 產物

Audit Game BASE：

84319439243b51aa8d119e33eb62a0637feea887

正式登記前由 Claude 確認最新 main 完整 SHA。

2. 任務目標

WE-02 必須完成：

1. 凍結 ENVELOPE 規劃邊界。
2. 建立三區獨立住宅配置。
3. 選擇第一期40棟住宅配置。
4. 保留第二期60棟住宅發展目標。
5. 建立道路工程依賴關係。
6. 建立土地利用、景觀及保護區規劃。
7. 建立後續區域串流及資產製作需求。
8. 產出可供後續工程任務引用的 Masterplan。

不重新執行完整 WE-01 審計，不改寫既有裁定。

3. 固定規劃範圍

座標順序：[xmin, xmax, zmin, zmax]。

Region| Bounds| Gross area
B1| [-10,490,830,1330]| 250,000 m²
B2| [-1000,-400,720,1170]| 270,000 m²
B3| [-740,-240,-910,-510]| 200,000 m²
TOTAL| Union| 720,000 m²

polygon_revision = 2。

72 ha 為三區規劃外框，不等於新增72 ha 可行走土地，也不等於遊戲世界外部邊界增加72 ha。

禁止將 ENVELOPE 外框直接視為可全部施工區域。

不得自行修改座標或擴張世界邊界。

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

B2 的67棟全部以 R05 平地代理為基礎，不代表山坡住宅工程已驗證。

5. 分期住宅建設計畫

Region| Phase 1| Phase 2 cumulative| Phase 2 additional
B1| 10| 14| 4
B2| 12| 18| 6
B3| 18| 28| 10
TOTAL| 40| 60| 20

Phase 1 為第一期最低建設目標。

Phase 2 為累計理想目標，不是額外60棟。

不得使用其他區域的超額容量抵銷任何單一區域不足。

Phase 2 的 B3 目前只有25棟已驗證直接配置，距28棟尚差3棟，須另行研究。

6. 住宅配置及比例

6.1 B1 Oceanfront Heights

Phase 1：

- R01 Urban Apartment：5棟。
- R02 Curved Luxury Tower：5棟。

Phase 2 累計：

- R01：7棟。
- R02：7棟。

R02 比例不得低於50%。

建築高度方向：30–65 m。

優先採用已審計的5棟直接地塊，其餘地塊由正式條件配置中選擇。

6.2 B2 Vista Hills

Phase 1：12棟。

Phase 2 累計：18棟。

規劃階段全部以 R05 地塊代理進行。

R06 山坡懸挑住宅只能在獨立地基、碰撞及地形工程驗證後替代部分 R05。

不得因外觀相似直接沿用 R05 的工程裁定。

建築高度方向：5–12 m。

6.3 B3 Palmwood Quarter

Phase 1：

- R01：4棟。
- R05：10棟。
- R08：4棟。

Phase 2 累計：

- R01：6棟。
- R05：16棟。
- R08：6棟。

三種原型各不得低於20%。

R08 一棟為四戶，不得計作四棟。

Phase 1 必須從既有合法配置中選取不重疊且比例合格的18棟。

Phase 2 不得宣稱已找到28棟合法配置。

上述比例為 ChatGPT 提出的建設配置，須由 Claude 核對地塊及原型資料。

7. 地塊選擇規則

正式地塊須保留 WE-01 parcel_id、prototype_id、座標、方向、地塊邊界及依賴關係。

優先順序：

1. 已驗證直接地塊。
2. 所需新增道路較少的條件地塊。
3. 可形成連續街景的地塊群。
4. 可保留公園、海岸及景觀的地塊群。
5. 穩定 parcel_id 排序。

選擇過程須符合各區原型比例及最低棟數。

不得為增加容量移動既有直接地塊。

若選定子集無法符合比例、道路或幾何要求，停止並回報，不得自行放寬限制。

Phase 2 可使用預留地塊，但未驗證地塊必須標記 UNVERIFIED。

8. 土地利用規劃

沿用 WE-01 的土地利用參考比例：

Use| Reference
Residential| 25%
Roads and sidewalks| 25%
Parks and landscape| 30%
Public and community facilities| 20%

比例為概念參考，不是硬性可行性門檻。

實際面積以互斥土地分類為準。

禁止將道路、公園、住宅及公共設施重複計算。

海灘、水域、Site A、既有建築、未驗證土地須獨立呈現。

公共設施可預留空間，但不在本階段新增商店、學校、NPC 或任務系統。

9. 外部道路規劃

優先使用 ENVELOPE 正式審計中的合法依賴鏈。

X01

- 長度：362.908 m。
- 車行道：7 m。
- 走廊總寬：11 m。
- 最大設計縱坡：6%。
- 最小曲線半徑：25 m。
- 作為 B1 新增道路接入的重要候選路段。

C02

- 長度：130 m。
- 車行道：7 m。
- 走廊總寬：11 m。
- 最大設計縱坡：6%。
- 最小曲線半徑：25 m。
- 已審計海灘侵占：224 m²。
- 施工前須確認景觀保護方案。

H02

- 長度：597.306 m。
- 車行道：8 m。
- 走廊總寬：12 m。
- 最大設計縱坡：9%。
- 最小曲線半徑：18 m。
- 作為 B2 對外連接的優先候選道路。

C01

保留原始17 m 車行道設計研究。

ENVELOPE 配置因與 B1_R02_005 直接地塊衝突而排除 C01。

不得將 C01 納入第一期施工配置。

未來若要建造，須另案研究改線，不得直接刪除或移動衝突地塊。

H01

NOT_FEASIBLE。

已量測最大坡度135.633%。

不得沿用原始路線施工。

山區連接若需要替代線型，須另行批准研究。

U01

既有道路，優先保留並利用。

不得重複計入新增道路長度。

AVE_110

可選延伸，UNVERIFIED。

不得列為第一期必要道路。

10. 內部街道

ENVELOPE 已選定街道：

B1：

- ENVELOPE_B1_ST_0085
- ENVELOPE_B1_ST_0305
- ENVELOPE_B1_ST_0115

B2：

- ENVELOPE_B2_ST_0010
- ENVELOPE_B2_ST_0040
- ENVELOPE_B2_ST_0140

B3：使用既有道路，不新增已選定街道。

各街道長150 m。

六條候選街道總長900 m。

沿用：

- 車行道7 m。
- 每側人行道2 m。
- 走廊總寬11 m。
- 最大縱坡6%。
- R7 距離≤2 m、連續接近長度≥8 m。

WE-02 須依第一期住宅選定地塊判斷實際需要哪些街道。

不得為追求道路數量而強制建造全部六條。

所有候選道路與街道維持未建造狀態。

11. 道路工程規模

X01、C02、H02 合計候選長度：

1,090.214 m。

加上六條已選定內部街道：

1,990.214 m。

此數字為現有優先候選道路全部採用時的長度參考，不是正式施工工程量。

道路走廊須使用聯集面積，不得直接將重疊走廊面積相加。

新增道路需保持既有主道路網連通。

未來施工任務須獨立驗證路面、地形、碰撞、車輛通行、交通 AI 及導航路線。

12. 景觀及保護規則

Site A 保護範圍：

X：[-561,-441]

Z：[-831,-753]

不得侵占、拆除或移動。

B1 優先保留連續海濱步道與海灘景觀。

C02 的224 m² 海灘侵占須於道路工程規格中明確處理。

B2 保留山體輪廓，不得以大面積削平山區作為預設解法。

B3 保留既有城市格網，使用街廓填充與社區景觀改善。

所有既有建築拆除、海岸填地及地形改造均需獨立授權。

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

第一期優先製作 R01、R02、R05、R08。

其餘原型屬後續資產庫需求，不得自動增加第一期施工範圍。

所有原型必須具有統一尺度、材質規格、LOD、碰撞策略及夜間表現。

既有 Site A 可作為美術技術參考，但不得直接複製其商業及辦公立面作為住宅美術驗收標準。

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

建議量測包含平均 FPS、最近60秒最低1秒 FPS、畫質設定及載入卡頓。

S26 Ultra、Tab S11 為優先驗收裝置。

WE-01 B8 headless 結果僅為現有遊戲基準，不代表新增住宅可達30 FPS。

WE-02 不凍結未經量測的 draw call、三角形、VRAM 或物理時間預算。

正式預算由 WE-03 規格及 Claude 獨立驗證建立。

15. 正式交付物

建議由 Claude 在正式批准後，透過 docs-only PR 登記至：

specs/we02/

交付物：

1. masterplan.md
   完整世界擴張規劃及工程順序。

2. district_plan.json
   三區邊界、地塊 ID、原型、分期、狀態、依賴及預留土地。

3. masterplan.svg
   以正式遊戲 X/Z 座標呈現三區、住宅、道路、景觀及保護範圍。

4. dependency_matrix.md
   每個住宅區、道路、地形、資產及串流系統的前置依賴。

5. we02_validation.md
   Claude 獨立核對結果、來源雜湊、限制及未解決問題。

本階段不新增分析器或遊戲程式。

如正式交付物需要額外自動化工具，須先提出獨立任務規格及取得批准。

16. 驗收閘門

Gate| Requirement
MP01| ENVELOPE 三區座標與 WE-01 一致
MP02| 總規劃面積720,000 m²
MP03| 所有正式地塊 ID 可追溯
MP04| 第一期間各區10／12／18棟配置合法
MP05| 原型比例符合規則
MP06| 住宅地塊無重疊
MP07| Site A 侵占面積為0
MP08| 道路依賴鏈完整
MP09| H01、C01、AVE_110 不誤列為第一期可施工道路
MP10| B2 代理狀態明確保留
MP11| 60棟目標的未驗證部分明確標示
MP12| 土地分類互斥且面積守恆誤差≤1 m²
MP13| 地圖與 JSON 及規劃文件一致
MP14| Production 檔案差異為0
MP15| CACHE、存檔及遊戲行為不變
MP16| Claude G0 審查及 Martin 正式批准
MP17| Martin 最終規劃驗收

MP04 通過代表找到符合既有審計規則的第一期規劃配置，不代表條件工程已完成。

任何缺少工程證據的項目維持 CONDITIONAL 或 UNVERIFIED。

17. 後續任務路線

WE-03：區域串流與效能架構。

WE-04：外部道路工程。

WE-05：地形、地基與內部街道工程。

WE-06：住宅建築原型庫。

WE-07：B1 Oceanfront Heights 建設。

WE-08：B2 Vista Hills 建設。

WE-09：B3 Palmwood Quarter 建設及三區整合驗收。

以上為建議任務分工。

每項工程須另行制定完整規格、實作者、效能預算及回歸測試。

高風險大型工程依 COLLAB §5.2 拆分成小型 PR。

Codex 為小量高風險任務預設實作者；Gemini Stage 3 為大量低風險任務預設實作者。實際指派由 Martin 決定。

18. 禁止事項

本階段禁止：

- 修改 index.html。
- 修改 sw.js 或 CACHE。
- 修改 vh_save。
- 新增遊戲道路或住宅。
- 修改地形或世界邊界。
- 刪除既有建築。
- 修改 WE-01 原始審計裁定。
- 未經批准啟動 WE-03 至 WE-09。
- 以 headless FPS 代替實機效能。

19. G0 審查要求

Claude 須確認：

1. T-017 是否為可用任務編號。
2. 最新 main SHA 與正式審計產物完整性。
3. 第一期間40棟配置是否能從既有合法地塊選取。
4. 各區原型比例與道路依賴是否成立。
5. C01 衝突排除及 C02 海灘侵占是否正確保留。
6. B3 第二期28棟的不足是否正確標示。
7. B2 山坡工程未驗證部分是否完整保留。
8. 交付物是否能在 docs-only 範圍完成。
9. MP01–MP17 是否可獨立驗證。
10. D-013 main 保護及共享 PR 鎖狀態。

Claude 完成 G0 後，回報 APPROVE、APPROVE WITH CONDITIONS 或 REVISE。

只有 Martin 正式批准完整規格後，Claude 才可登記 WE-02。

END OF WE-02 v1.0 DRAFT.