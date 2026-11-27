> Verbatim ChatGPT draft "T-016C — WE-01C Road Feasibility Survey v1.0" (G0 proposal). Superseded where `specs/T-016C-spec-v1.0.md` (Claude conditions) says so; the body below is unchanged.

T-016C — WE-01C Road Feasibility Survey v1.0

Status: DRAFT FOR G0
Protocol: COLLAB v3.6
Implementer: Gemini Stage 3 (proposed)
Reviewer: Claude
Risk: LOW
Volume: SMALL
Routing reason: Deterministic, read-only offline geometry analysis with no production modifications.

1. Baseline and dependencies

T-016A：Done，D-051d。
T-016B：Done，D-053，PR #114 merged as 215ba1b。

T-016C 須從正式登記後的最新 main 開始。

Audit game BASE：

84319439243b51aa8d119e33eb62a0637feea887

Production release：

vh-2026-11-27-02

繼承 WE-01 v1.2、v1.3、v1.4 及相關勘誤中所有道路分析規則。

以 D-051e、D-052、D-053 的正式資料及已合併 T-016B 公開介面為準。

Claude G0 須核對 T-016B 實際公開函式及簽章，不得依未驗證的草案介面進行實作。

2. T-016B evidence

REVISED-v2：

Region| C_direct| C_preliminary| C_upper
B1| 5| 72| 100
B2| 0| 278| 329
B3| 17| 25| 40

正式分析耗時6.3秒。

全部57個 DIRECT 地塊經 Claude 獨立驗證，零錯誤。

上述結果只作道路分析的輸入及基準，不是最終住宅可行性裁定。

C_conditional 維持 PENDING_T016D。

3. Scope

T-016C 僅負責：

- 六條固定候選道路。
- 圓弧倒角及中心線。
- 道路坡度。
- 完整走廊幾何。
- 地形、障礙物、保護區及物理支撐。
- 既有道路接點。
- 候選道路間的接點。
- 道路高程及連通圖。
- 工程相依鏈。
- 三情境、三區的外部道路接入裁定。
- road_survey.json。
- 道路專屬自動測試。

不包含：

- 內部街道生成。
- 新住宅地塊配置。
- C_conditional 計算。
- 最終25 ha／40棟／60棟裁定。
- 最終 D3 裁定。
- 最終 world_survey.svg。
- 最終世界擴張報告。

以上留待 T-016D。

4. Fixed candidate roads

所有座標為 X/Z，單位 m。

ID| Control points
C01| (221,890) → (240,960) → (240,1200)
C02| (110,960) → (170,960) → (240,960)
H01| (-635,682) → (-800,800) → (-800,1030)
H02| (-800,1030) → (-420,1000) → (-240,880)
X01| (-240,880) → (0,960) → (110,960)
U01| (-600,-720) → (-510,-720) → (-420,-720)

不得移動控制點或自行增加第七條候選道路。

U01 為既有道路重用，不是新建道路。

5. Geometry parameters

Road| Carriageway| Corridor half-width| Min radius| Max grade
C01| 17 m| 12.5 m| 25 m| 6%
C02| 7 m| 5.5 m| 25 m| 6%
H01| 8 m| 6 m| 18 m| 9%
H02| 8 m| 6 m| 18 m| 9%
X01| 7 m| 5.5 m| 25 m| 6%
U01| Existing| Existing| Existing geometry| Report actual

C01 車行道17 m 已由 Martin 確認。

C01 每側4 m 附加空間為已接受的保守設計假設。

其他道路沿用 v1.4 分類及尺寸。

6. Road curve construction

採固定控制折線加圓弧倒角。

不得使用無界曲線最佳化、任意樣條或重新尋路。

- 一般道路最小半徑25 m。
- 山區道路最小半徑18 m。
- 圓弧切線長度不得超過相鄰線段長度的一半。
- 無法容納合法圓弧時回報幾何不符合或 UNVERIFIED，依實際證據裁定。
- 中心線取樣間距不得超過3 m。
- 必須保留端點及必要曲線轉折取樣點。
- 報告原控制點、實際中心線、曲線半徑、長度及取樣間距。

U01 使用既有道路幾何，不得以新建道路標準強制重新設計。

7. Terrain and corridor validation

正式資料使用 ROAD_CORRIDOR 的1 m grid，控制折線外接範圍加±60 m。

沿用 D-051e 正式 dumps。

- 非整數位置使用雙線性高度插值。
- 標記 INTERPOLATED_1M。
- 不得以設計高度取代 runtime 高度。
- 完整走廊須位於有效審計資料內。
- 走廊外緣距 COR 網格邊界至少5 m。
- 超出資料覆蓋範圍回報 UNVERIFIED。
- 檢查完整道路走廊，不只中心線。
- 檢查物理支撐、水域、建築、保護區及障礙物。
- Site A 保護區不得侵占。
- 檢查與既有道路及其他候選道路的交會。
- 合法接點的必要交集須明確識別。
- 缺少高程或支撐證據不得自動通過。

Claude G0 須確認完整走廊的地形及障礙物檢查可由現有 dump 欄位完成。

若資料不足，先回報缺口，不得自行修改 extractor。

8. ROAD_NET and external connections

唯讀重用 T-016B 的既有道路圖、穩定道路 ID、去重處理及 AVE_0 主 GROUND 連通分量。

沿用 R8：

- GROUND 中心線相交，或端點距接入道路中心線 ≤ 接入道路半幅寬 + 1 m。
- 必須有相容的高程證據。
- ELEVATED、RAMP、UNKNOWN 不得僅因平面相交而連通。
- 審計視窗外的道路不得推測或補猜。
- 無法證明連至主分量者維持 UNVERIFIED。

候選道路圖須與既有道路圖分開標記。

尚未建造的候選道路即使幾何及連通合法，仍屬條件工程，不得視為 production 已存在道路。

9. Known road-specific findings

C01

RIB_0 已確認為 GROUND。

半幅寬8.5 m。

C01 起點距 RIB_0 中心線0 m。

必須重新驗證合法接點，不得硬編碼 PASS。

C01 全程仍須完成坡度、走廊、障礙物及連通檢查。

C02 and X01

共同端點 (110,960)。

距 AVE_110 北端約68 m。

保留：

AVE110_EXTENSION_REQUIRED。

不得自行生成、驗證或建造該延伸道路。

須區分：

- 候選道路本身幾何是否合法。
- 經其他已驗證道路形成的替代連通路徑。
- 需要 AVE110 延伸工程才能成立的路徑。

不得因其中一個接點缺失而忽略其他合法連通路徑。

H01

Claude 預先實測：

起點約62.3 m，終點0 m，控制折線約433 m，平均縱坡約14.4%，最陡3 m 步長約134.9%。

山區道路上限9%。

預期固定路線不通過坡度檢查。

Reason：GRADE_LIMIT_EXCEEDED。

此為有效審計結果，不是程式缺陷。

不得調整控制點、坡度上限或地形以強行通過。

不得硬編碼上述實測數字作為正式分析結果。

H02

保留 B2 的替代道路候選。

東端 (-240,880) 接入既有 GROUND 道路網。

預先實測高度0 m。

仍須驗證完整幾何、走廊、接點及連通。

H01 失敗不得自動使 H02 或 B2 失敗。

U01

驗證既有道路重用及其主道路網連通。

不得將 U01 計入新增道路工程長度或新增道路占地。

10. Regional road-access verdicts

分析 D-052 凍結的三個情境：

INITIAL。
ENVELOPE。
REVISED，polygon_revision = 2。

每個情境分別分析 B1、B2、B3。

區域道路接入必須具備：

- 實際區域邊界接入或合法區域內道路走廊。
- 可追溯的道路連通路徑。
- 連至 AVE_0 主 GROUND 分量的證據。
- 完整工程相依鏈。

不得僅因道路接近區域中心或平面穿越區域，就宣稱住宅地塊已具有合法道路接入。

區域道路接入裁定：

FEASIBLE：
具有已驗證的既有道路接入。

CONDITIONAL：
具有幾何及連通均已驗證、但尚待建造的道路接入方案。

UNVERIFIED：
缺少必要資料、接點或工程驗證。

NOT FEASIBLE WITHIN AUDITED BOUNDARIES：
具有充分不可行證據，而非單純候選搜尋失敗。

單一路線失敗不得直接導致整區失敗。

本階段只裁定區域外部道路接入，不代表區內住宅容量已達標。

11. Data handoff to T-016D

正式輸出：

road_survey.json

至少包含：

- schema_version。
- analyzer_version。
- game BASE。
- 兩個 static_fingerprint。
- polygon_revision。
- T-016B analyzer version。
- T-016B 產物來源及 SHA-256。
- 六條道路 ID。
- 控制點及實際中心線。
- 完整走廊幾何。
- 道路長度及半幅寬。
- 最大坡度及最小半徑。
- 地形、物理支撐及障礙物結果。
- 接點座標及高程證據。
- 既有／候選道路連通關係。
- 工程相依鏈。
- 各道路裁定及原因。
- 三情境、三區道路接入結果。
- 可供 T-016D 使用的合法候選走廊清單。
- 未驗證資料及限制。

T-016D 必須能辨識：

1. 已存在且已驗證的道路。
2. 幾何合法且具有完整條件連通鏈的候選道路。
3. 尚未驗證的道路。
4. 已證明不符合的道路。

不得將第3、4類輸出為已驗證內部街道來源。

H01 不得作為合法來源。

C02／X01 必須保留適用的 AVE110 工程相依關係。

C_conditional = PENDING_T016D。

12. Regression tests

繼承 v1.2、v1.3、v1.4 中屬於道路分析的測試。

本輪至少涵蓋：

R01：六條固定控制點及道路分類。

R02：C01 17 m 車行道及12.5 m 走廊半寬。

R03：一般／山區道路圓弧半徑及切線長度。

R04：中心線取樣間距≤3 m。

R05：1 m grid 插值及坡度邊界。

R06：完整走廊與 COR 5 m 邊界。

R07：障礙物、保護區、水域及物理支撐。

R08：GROUND 接點距離及高程相容性。

R09：ELEVATED／RAMP／UNKNOWN 平面交叉不得自動連通。

R10：C01／RIB_0 正式接點。

R11：AVE110_EXTENSION_REQUIRED。

R12：H01 坡度失敗及 H02 替代路徑。

R13：U01 既有道路重用。

R14：未建造道路不得標記為既有道路或直接 FEASIBLE。

R15：三情境三區道路接入裁定。

R16：資料交接鍵、fingerprint 及 schema 驗證。

R17：road_survey.json 完整性及工程相依鏈。

R18：確定性輸出及三次重跑一致性。

以上為測試覆蓋項目，可合併於既有測試 ID，不得因此刪除原規格道路相關斷言。

13. Mutation tests

至少捕捉：

- C01 寬度被改回14 m。
- 圓弧半徑低於門檻仍通過。
- 取樣間距超標。
- H01 坡度超標仍通過。
- 只檢查中心線而忽略走廊。
- 忽略 Site A。
- 忽略 COR 邊界。
- 缺少高程證據仍建立接點。
- 高架平面交叉被視為 GROUND 連通。
- AVE110 相依鏈被移除。
- H01 失敗直接使整個 B2 失敗。
- 未建造道路被標為已存在。
- 錯誤 fingerprint 被接受。
- U01 被重複計入新增道路。

Claude 須在 G0 對照原有 B13–B16、C01–C08、C18 及相關 mutation tests，確認道路部分沒有遺漏。

內部街道及最終裁定相關測試移交 T-016D，不得取消。

14. Allowlist

Branch：

gemini/T-016C-we01c-road-analyzer

Only two new files：

tools/test/we01c_road_analyzer.py

tools/test/we01c_road_analyzer_check.py

Python standard library only。

允許唯讀使用已批准的 T-016A／T-016B 公開介面。

檢查腳本可依 E3 唯讀匯入 WE-01A 合成測試鷹架。

不得修改任何既有 analyzer、測試、fixture、extractor 或 production 檔案。

15. Line budget and performance

Target：900 combined lines。

Hard ceiling：1,050 combined lines。

超過900行部分僅限測試。

此為 Martin 原先選定的 T-016C 上限。

D-052a／D-052b 的 T-016B 行數例外不得自動套用。

考量 T-016B 實際行數大幅高於早期估計，Claude G0 必須依已合併介面重新評估 T-016C 行數可行性。

若1,050行不足，須於開工前提出具體分配及新上限建議，交 Martin 決定。

保留實作約一半及完成前兩次強制行數回報。

完整雙 preset、三情境道路分析目標≤60秒。

若實測超標，依原 Gate B6 申請明確例外，不得弱化分析規則。

記錄 B+C 累計耗時。

16. Claude independent verification

Claude 負責：

- 正式雙 preset dumps。
- 六條道路實際幾何及坡度。
- 完整走廊獨立驗證。
- 接點及道路圖獨立驗證。
- H01 預期失敗及 H02 替代路徑。
- C01／RIB_0。
- AVE110 工程相依鏈。
- 三情境三區裁定。
- road_survey.json 完整性。
- 測試及 mutation tests。
- 完整分析耗時。
- Allowlist、D-013 及 PR lock。
- 既有 A/B 測試回歸。
- Production 檔案一致性。
- CI wiring。

本階段主要完成 Gate B4，並重驗適用的 B1、B6、B7、B9。

B5、B10、B11 及最終 B8 仍留待 T-016D。

不修改 CACHE，不發布新的遊戲內容。

17. G0 confirmation

Claude 須確認：

1. T-016B 實際公開介面足以支援道路分析。
2. 六條道路所需1 m COR 資料及正式 fixtures 完整。
3. 高程相容性、道路走廊及物理支撐的具體判定方法。
4. C02／X01 替代路徑與 AVE110 相依鏈。
5. 測試覆蓋與原規格一致。
6. 1,050行上限是否可行。
7. 60秒效能目標及例外流程。
8. 最新 main 完整 SHA、D-013、共享 PR 鎖。
9. T-016D 所需道路交接資料是否充分。

Martin 明確批准後，Claude 才可正式登記。

---

HANDOFF ChatGPT -> Claude

Task: T-016C — WE-01C Road Feasibility Survey v1.0

Base commit: latest main containing T-016B merge 215ba1b and D-053; confirm exact full SHA before registration.

Read: COLLAB.md v3.6, AGENTS.md, TASKS.md, DECISIONS D-013/D-021/D-026/D-027/D-051–D-053, specs/WE-01-spec-v1.2.md, WE-01 v1.3/v1.4 amendments, T-016B errata, specs/T-016B-spec-v1.4.md, and merged T-016B public interfaces.

Context:

T-016B is complete and merged. REVISED-v2 direct capacity is 5/0/17, while preliminary capacity is 72/278/25. External road access and future internal streets are the principal remaining capacity dependencies.

Martin approved splitting the previous T-016C into road analysis (T-016C) and internal streets/conditional capacity/final verdicts (T-016D), and confirmed C01 carriageway width of 17 m.

This proposal covers T-016C only. No internal-street generation or final residential feasibility verdict is authorised.

Deliverable: Perform G0 review of this complete proposal, inspect the merged T-016B interfaces, confirm the road geometry and data contracts, and assess the 1,050-line ceiling using actual implementation evidence. Register only after Martin explicitly approves.

SPEC: Complete T-016C v1.0 proposal in this message.

HANDOFF -> Claude G0 review.