WE-03 v1.0 — C+ Hybrid World Streaming Architecture

Project: VICE HORIZON VI

Proposed Task: T-018 Series（正式編號由 Claude 確認）

Status: DRAFT — Pending Claude G0 Review

Author: ChatGPT

Architecture: C+ Hybrid Streaming with Future HLOD Compatibility

Risk: HIGH

Volume: LARGE — Mandatory Sequential Decomposition

Design Owner: ChatGPT

Reviewer / Releaser: Claude

Final Approver: Martin

1. Source of Truth

Repository: martinhsu2010-blip/Martin-Hsu

Required reading:

- COLLAB.md v3.6
- AGENTS.md
- TASKS.md
- DECISIONS.md
- D-013、D-021、D-026、D-027
- D-057、D-060、D-061、D-062、D-063、D-064
- specs/T-017-spec-v1.0.md
- specs/we02/masterplan.md
- specs/we02/district_plan.json
- specs/we02/dependency_matrix.md
- specs/we01-final/WE-01_B8_runtime_baseline_appendix.md

Historical Audit Game BASE:

84319439243b51aa8d119e33eb62a0637feea887

WE-03 Engineering BASE 必須由 Claude 在正式登記時取得完整 main SHA，並確認實際遊戲原始碼與歷史基準的差異。

不得直接假定歷史 Audit BASE 等於最新 Engineering BASE。

2. Goal

建立可擴張的混合式世界串流架構，使新增住宅區具備：

1. 確定性空間索引。
2. 區域化視覺載入與卸載。
3. 多層級建築 LOD。
4. 材質、幾何及貼圖資源共用。
5. 獨立碰撞體生命週期管理。
6. 高速遊戲移動預載。
7. 快速旅行目的地準備。
8. 可量測的主執行緒排程。
9. 未來 HLOD 擴充相容性。
10. 手機與平板至少30 FPS的實機驗收目標。

3. Non-Goals

WE-03 不包含：

- 完整 Quadtree 或 HLOD 引擎。
- 實際遠景合併資產生成。
- WE-04 至 WE-09 工程。
- 新增正式住宅、道路或地形。
- 遷移整座既有城市。
- 重構交通或警察 AI。
- 更換 Three.js 或 cannon-es。
- 新增外部 CDN、第三方函式庫或二進位資產。
- 修改 vh_save schema。
- 擴張世界邊界。
- 修改 WE-01 或 WE-02 裁定。

測試建築不得成為正式世界內容。

4. Fixed World Planning Constraints

沿用 D-064：

- B1 規劃外框：250,000 m²。
- B2 規劃外框：270,000 m²。
- B3 規劃外框：200,000 m²。
- 總規劃外框：720,000 m²。
- 第一期：40棟、52戶。
- 第二期：57棟已規劃、72戶。
- 第二期60棟目標仍為 UNVERIFIED。
- B3 缺 R01、R05、R08 各1棟。
- B2 R05 為平地代理。
- R06 尚無工程裁定。

不得將測試用60棟或120棟視為新增合法地塊證據。

Site A 保護範圍維持：

X [-561,-441]；Z [-831,-753]。

正式世界內不得新增侵占。

5. World Layer Architecture

L0 — Terrain

既有地形及地基支撐常駐，不參與 WE-03 串流卸載。

L1 — Persistent World Skeleton

既有道路、主要地標、導航基礎及必要遠景維持現行行為。

L2 — Collision Layer

新增串流住宅的碰撞體獨立管理，不由視覺 LOD 直接決定。

L3 — Building Visual Layer

住宅主體依區塊及距離管理。

L4 — Detail Layer

陽台、窗框、屋頂裝飾及其他非必要細節可依 LOD 切換。

既有建築、道路、地形及物理系統不進行全面遷移。

6. Chunk Registry

6.1 Grid

初始測試尺寸：128 × 128 m。

Grid origin：世界座標 (0,0)。

X/Z cell index 使用 floor 座標除以128。

負座標必須正確處理。

採半開區間，避免邊界重複歸屬。

6.2 Object Ownership

每個串流物件具備：

- object_id
- chunk_id
- prototype_id
- bounds
- visual_state
- collision_state
- resource_handles
- generation_token

跨區塊物件僅有一個 owner chunk。

其他相交區塊可保存查詢索引，但不得重複建立物件。

可見性及碰撞查詢須考慮完整 bounds，而非僅以 owner chunk 或中心點決定。

6.3 Determinism

相同輸入資料、seed、畫質及座標必須產生相同的 ID 與所有權。

區塊資料不得依隨機載入順序改變。

至少10,000筆合成空間索引測試。

允許重複 ID：0。

允許錯誤 owner：0。

7. Chunk Lifecycle

視覺狀態：

UNLOADED → QUEUED → LOADING → READY → ACTIVE → EVICTING → UNLOADED

另設 FAILED 狀態。

要求：

- 重複載入請求必須合併。
- 過期非同步結果不得重新啟用已卸載物件。
- 使用 generation token 或等效機制阻止 stale completion。
- ACTIVE 前必要視覺資源必須完整。
- 替換 LOD 時，舊模型須保留至新模型準備完成。
- 不得同時長期顯示兩個 LOD。
- 資源建立失敗不得導致既有遊戲崩潰。
- 每次載入失敗最多自動重試2次。
- 重試間隔初始為1秒、2秒。
- 超過重試上限保留安全的既有視覺表示，記錄錯誤，不得無限重試。

8. LOD Controller

8.1 LOD Levels

LOD0：近距離完整住宅。

LOD1：簡化立面及主要建築結構。

LOD2：低細節主體及天際線表示。

OUT：超出核准可見範圍的非必要視覺物件。

既有世界遠景不得因本系統而被移除。

8.2 Initial Preset Parameters

Preset| LOD0| LOD1| LOD2
PHONE_LOW| 100 m| 250 m| 650 m
PHONE_MED| 120 m| 300 m| 750 m
TABLET_MED| 140 m| 350 m| 850 m
DESKTOP_HIGH| 200 m| 500 m| 1200 m

以上為初始測試參數，不是既有引擎參數的描述。

其他實際存在的畫質 preset 必須由 WE-03A 完整盤點並提出映射，經批准後使用。

8.3 Hysteresis

升級門檻：基準距離 × 0.90。

降級門檻：基準距離 × 1.10。

總遲滯區間為基準距離的20%。

同一物件正常 LOD 切換冷卻時間：500 ms。

快速旅行及必要資源恢復可例外，但必須記錄。

8.4 Update Interval

PHONE_LOW：250 ms。

PHONE_MED：200 ms。

TABLET_MED：200 ms。

DESKTOP_HIGH：100 ms。

高樓須考慮完整 bounds 與螢幕投影大小。

螢幕投影門檻由 WE-03A 校準，WE-03C 子規格正式確定；不得由實作者自行決定。

8.5 Visual Continuity

正常載入條件下：

- 近距離必要建築空白幀：0。
- 重複建築：0。
- 錯誤 LOD 所有權：0。
- 既有天際線移除：0。

不要求第一版實作 crossfade shader。

9. Future HLOD Compatibility

C+ 必須保留未來階層式遠景擴充契約，但不得實作完整 HLOD。

概念階層：

- Level 0：128 m。
- Level 1：256 m。
- Level 2：512 m。

基礎區塊 ID 必須可穩定推導未來父區塊 ID。

預留：

- parent_chunk_id
- hierarchy_level
- aggregate_bounds
- representation_type

第一版只需驗證資料契約及父區塊推導。

不得建立未使用的完整 Quadtree runtime、HLOD shader 或合併資產生成器。

10. Asset Registry

資源共用單位：

- Geometry
- Material
- Texture

資源使用穩定 key 管理。

不同物件引用相同資源時不得重複建立等價資源。

資源 reference count 不得為負。

仍有引用的資源不得 dispose。

零引用的非快取資源應於卸載完成後5秒內釋放。

可保留受預算限制的快取資源；快取資源必須獨立計量，不能被當作已釋放。

不允許新增外部資產依賴。

貼圖估計須列出尺寸、格式、mipmap 與重複引用去重方式。

不得將估算值標示為實測 VRAM。

11. Provisional Asset Budgets

以下為合成測試模型的初始上限，不是正式 WE-06 建築資產批准值。

Prototype| LOD0 triangles| LOD1 triangles| LOD2 triangles
R01| 12000| 3000| 300
R02| 20000| 5000| 600
R05| 5000| 1200| 150
R08| 8000| 2000| 240

建議每種原型共用：

- Base atlas：最多1張1024 × 1024 RGBA8。
- Night mask：最多1張512 × 512 R8。
- Material：最多3種共用材質。

以上尺寸須經 WE-03A 驗證實際裝置及 renderer 支援。

不允許每棟住宅各自建立相同貼圖。

正式 WE-06 美術品質及模型預算另案批准。

12. Collision Streaming

12.1 Isolation

碰撞體生命週期與視覺生命週期分離。

既有地形、道路、住宅及樹木碰撞系統保持原行為。

WE-03 只驗證新串流物件的碰撞管理。

12.2 Initial Radius

基礎啟用距離：140 m。

基礎卸載距離：180 m。

實際啟用距離不得小於：

max(140 m, v × T_ready + 64 m)

其中：

v 為相關遊戲動態物件的速度，單位 m/s。

T_ready 為經量測確認的碰撞準備時間上限，包含排程及更新延遲。

卸載距離至少為啟用距離 +40 m。

140/180 m 不得被視為任何車速下均充分的固定安全距離。

12.3 Physics Integrity

禁止在 physics step 執行中修改 bodies/shapes。

碰撞體新增及移除須於明確安全點執行。

玩家及相關交通動態物件仍可能與碰撞體接觸時，不得卸載。

LOD 切換不得改變碰撞外框。

不允許：

- 重複 body。
- 未登錄 body。
- 玩家穿越應啟用的碰撞體。
- 卸載仍受接觸或約束保護的 body。

每項允許次數：0。

碰撞準備未完成時，測試區不得宣告 READY。

若不能確保正常移動前的碰撞準備，該測試不通過；不得以改變正式車輛操控來掩蓋問題。

13. Predictive Streaming

預載距離初始公式：

D_preload = max(128 m, v × 4 s + 64 m)

v 使用遊戲世界速度，單位 m/s。

預載時間4秒為初始校準值。

須涵蓋：

- 正常前進。
- 急轉向。
- 反向移動。
- 低速移動。
- 靜止。
- 跨區塊邊界。
- 快速旅行。
- 重生。

優先順序：

P0：必要碰撞與目的地準備。

P1：玩家附近必要視覺資源。

P2：預測移動方向的資源。

P3：遠景及非必要細節。

P4：卸載與資源回收。

同優先級採確定性排序。

低優先級工作不得無限飢餓。

在資源壓力過高時，先降低非必要視覺工作，不得移除必要碰撞。

14. Performance Scheduler

初始主執行緒串流預算：

PHONE_LOW：2 ms/frame。

PHONE_MED：2 ms/frame。

TABLET_MED：2 ms/frame。

DESKTOP_HIGH：4 ms/frame。

單次同步工作初始上限：

手機／平板：4 ms。

桌機：8 ms。

上述上限針對串流管理器可歸因的同步 CPU 工作，不代表 GPU 完成時間。

無法拆分的工作必須記錄超時。

禁止以無上限同步迴圈一次建立所有區塊。

在正常負載下，排程工作時間 P95 須不高於各 preset 的每幀預算。

單次工作超出上限不得靜默忽略。

實際裝置上的不可分割資源上傳或編譯成本須獨立量測。

15. Fast Travel and Respawn

快速旅行與重生必須保留既有任務及狀態規則。

WE-03E 須先在隔離測試路徑驗證目的地準備。

流程：

1. 驗證既有快速旅行限制。
2. 準備目的地必要資源。
3. 確認必要碰撞 READY。
4. 才執行原有傳送行為。
5. 目的地啟用後再釋放舊區域非必要資源。

測試準備逾時初始值：5秒。

逾時時不得傳送至未準備區域。

保留原位置及原有任務狀態。

不新增永久存檔欄位。

既有非串流目的地行為不得被改變。

16. Diagnostics

診斷功能預設關閉。

須記錄：

- Active / queued / loading chunks。
- 各 LOD 物件數量。
- 活躍及快取資源數量。
- Asset reference counts。
- Draw calls。
- Render triangles。
- Physics bodies / shapes。
- Physics step time。
- Geometry buffer estimate。
- Texture memory estimate。
- Streaming CPU time。
- Frame time P50 / P95 / P99。
- 超過50 ms及100 ms的幀數。
- 資源載入失敗及重試次數。
- Stale completion 拒絕次數。
- Collision readiness misses。

診斷不得修改正常畫質、交通密度或遊戲物理。

既有 ?fps=1 行為須保留。

17. Synthetic Test Loads

測試場景使用確定性 seed 與原型資產。

Load| R01| R02| R05| R08| Total
P1| 9| 5| 22| 4| 40
P2 verified plan| 12| 7| 33| 5| 57
P2 target| 13| 7| 34| 6| 60
Stress| 26| 14| 68| 12| 120

40及57棟的原型組成對應 WE-02。

60及120棟僅為合成負載。

不得將額外合成物件登記為合法住宅地塊。

測試資料不得改寫 district_plan.json。

18. Sequential Implementation Plan

所有 ID 為暫定，由 Claude 正式登記。

每個子任務均需獨立完整 spec、Martin 批准、單一實作者、單一 PR、Claude review 及必要實機驗收。

WE-03A1 — Baseline Test Harness

Proposed: T-018A1

Implementer: Gemini

Risk: LOW

Volume: SMALL

理由：獨立測試工具及確定性資料採集，不修改遊戲程式。

交付：

- 固定 seed 與測試場景。
- 資源及效能統計。
- Baseline 配對測試。
- 測試輸出格式。

Allowlist：經子規格確認的 tools/test/ 檔案。

不得修改 index.html。

若既有診斷介面不足，停止並提出 A2 需求。

WE-03A2 — Runtime Diagnostics

Proposed: T-018A2

Implementer: Codex

Risk: HIGH

Volume: SMALL

理由：可能涉及 renderer 與物理效能關鍵路徑。

僅在 A1 無法透過既有介面取得必要資料時執行。

預設關閉診斷，驗證無功能回歸。

WE-03B — Chunk Registry

Proposed: T-018B

Implementer: Codex

Risk: HIGH

Volume: SMALL

交付：

- 128 m 空間索引。
- 唯一所有權。
- 確定性 ID。
- 生命週期資料契約。
- 未來父區塊推導。

不得啟用正式世界串流。

WE-03C1 — Asset Registry

Proposed: T-018C1

Implementer: Codex

Risk: HIGH

Volume: SMALL

交付：

- Resource keys。
- Reference counting。
- Shared geometry/material/texture。
- 安全 dispose。
- 資源快取計量。

使用隔離測試資產。

WE-03C2 — Visual Streaming and LOD

Proposed: T-018C2

Implementer: Codex

Risk: HIGH

Volume: SMALL

交付：

- 視覺區塊載入卸載。
- LOD0/1/2。
- Hysteresis。
- Stale completion protection。
- 無空白幀替換。

不得遷移既有城市。

WE-03D — Collision Streaming

Proposed: T-018D

Implementer: Codex

Risk: HIGH

Volume: SMALL

交付：

- 新住宅碰撞體啟用卸載。
- 物理安全點。
- 動態物件接觸保護。
- 碰撞與視覺分離。

不得修改正式交通 AI。

WE-03E1 — Predictive Scheduler

Proposed: T-018E1

Implementer: Codex

Risk: HIGH

Volume: SMALL

交付：

- 速度相關預載。
- 優先級佇列。
- 每幀工作預算。
- 取消過期工作。

WE-03E2 — Destination Readiness

Proposed: T-018E2

Implementer: Codex

Risk: HIGH

Volume: SMALL

交付：

- 隔離快速旅行測試。
- 重生目的地準備。
- 逾時保護。
- 原有任務限制回歸。

WE-03F1 — Stress Test Fixtures

Proposed: T-018F1

Implementer: Gemini

Risk: LOW

Volume: LARGE

交付：

- 40／57／60／120棟確定性測試資料。
- 路徑及壓力測試腳本。
- 自動判定與負向控制。

不得修改遊戲 runtime。

若測試資料需要 runtime 功能，另案拆分，不得擴權。

WE-03F2 — Integration and Device Acceptance

Proposed: T-018F2

Owner: Claude

Scope: 獨立驗證及驗收報告。

Martin 負責實機測試與最終接受。

若整合測試失敗，退回對應原實作者或另立經批准的修正任務，不得直接擴大 F2 修改範圍。

19. PR Size and Governance

遵守 COLLAB v3.6。

每個程式 PR：

- index.html 新增及修改建議不超過600行。
- 一個主要系統邊界。
- 僅修改子規格明列的 index.html 與 tools/test/ 檔案。
- 不得修改 sw.js、協作文件、CI 或二進位資產。
- 超出範圍時停止，重新拆分並審查。

Claude 負責 CI 接線、文件登記及發布。

同一時間僅一個程式 PR。

不得以本總規格取代每個子任務的正式批准。

20. Automated Acceptance Gates

WS01：相同 seed 與輸入的索引結果一致。

WS02：10,000筆空間索引測試，錯誤 owner 為0。

WS03：跨區塊物件重複生成為0。

WS04：至少1,000次合成生命週期事件，非法狀態轉移為0。

WS05：至少100次過期非同步完成測試，錯誤重新啟用為0。

WS06：正常 LOD 替換空白幀為0。

WS07：固定遲滯區間內往返100次，不得產生非預期 LOD 切換。

WS08：負 reference count 為0。

WS09：仍有引用的資源被 dispose 次數為0。

WS10：完整卸載及清除快取後，串流專屬 geometry/material/texture/body/shape 數量回到初始值。

WS11：100次載入卸載循環後，無持續性資源數量成長。

WS12：物理 step 期間修改 bodies/shapes 次數為0。

WS13：碰撞重複 body、接觸中卸載、必要碰撞未就緒次數均為0。

WS14：至少100次區塊邊界穿越及反向移動測試，必要資源缺失為0。

WS15：至少30次目的地準備測試，未就緒傳送為0。

WS16：至少10次注入逾時測試，玩家位置及原有任務狀態保持正確。

WS17：正常模式下無新增 console error 或 unhandled rejection。

WS18：既有存檔 schema、載入及保存行為不變。

WS19：PWA 離線載入及既有快取功能正常。

WS20：所有新增測試具有可辨識的失敗斷言及負向控制。

WS21：未批准的遊戲世界內容變更為0。

WS22：未批准檔案變更為0。

WS23：Claude 獨立效能驗證通過。

WS24：Martin 實機效能驗收通過。

WS25：未來 HLOD 父區塊 ID 推導測試通過，無實際 HLOD runtime 擴權。

WS26：合成測試住宅在正常遊戲中不可見、不可碰撞且不影響正式世界。

WS27：所有測試由 Claude 接入適用 CI 並實際執行通過。

WS28：原有回歸測試全部通過。

21. Baseline Regression Budgets

測試功能關閉時，以該子任務 BASE 進行比較。

相同 seed、相機、畫質、時間及載入狀態：

- 既有世界新增 bodies：0。
- 既有世界新增 shapes：0。
- 既有世界新增 draw calls：0。
- 既有世界新增 render triangles：0。
- 串流測試資產在正常模式新增 GPU 資源：0。

物理 step 配對中位比率：≤1.10。

主執行緒 frame time P95 比率：≤1.10。

Baseline 自身對照中位比率須介於 1/1.10 與1.10。

若對照不穩定，量測結果標記 INCONCLUSIVE，不得直接放行。

以上為草案上限，G0 須確認可重現性。

22. Active Streaming Load Budgets

以下為40／57／60棟合成負載的初始驗收上限。

相對相同場景、相同測試路徑且未啟用測試住宅的 BASE：

指標| PHONE_LOW| TABLET_MED| DESKTOP_HIGH
新增 draw calls P95| 30| 45| 75
新增 triangles P95| 120000| 200000| 350000
新增 geometry buffer estimate| 16 MiB| 24 MiB| 48 MiB
新增 texture estimate| 32 MiB| 48 MiB| 96 MiB
新增 active bodies| 32| 40| 60
新增 active shapes| 128| 160| 240
Physics step median ratio| 1.20| 1.20| 1.25
Streaming CPU P95| 2 ms| 2 ms| 4 ms

所有資源上限均為新增量，不是全遊戲總量。

上述數字不是既有實測結論，而是初始工程預算。

WE-03A 完成後必須由 ChatGPT、Claude、Martin 確認或修訂。

若必要碰撞數超出預算，不得為達成數字而卸載必要碰撞，應判定容量不足並重新設計。

120棟為擴張壓力測試：

- 記錄全部效能數據。
- 必須維持功能正確、無崩潰、無必要碰撞缺失。
- 不得有持續性資源洩漏。
- 不要求直接套用60棟效能預算。
- 不得宣稱120棟已達30 FPS，除非另有實機證據。

23. Streaming Benefit Gate

以相同60棟測試住宅、相同資產品質、相同相機路徑，比較：

Control A：全部測試住宅資源常駐，使用相同 LOD 策略。

Candidate C+：區域串流及相同 LOD 策略。

在分散住宅負載路徑中，初始要求：

- 新增住宅 geometry + texture 常駐估計峰值至少降低20%。
- 新增住宅活躍碰撞 bodies P95 至少降低20%。
- 相同 LOD 表示下，draw calls P95 不得增加超過5%。
- Frame time P95 不得增加超過10%。
- 所有功能正確性測試通過。

須公布絕對數字及比例。

若資源共用導致串流無法達成20%節省，不得透過刻意製造低效率 Control A 來取得 PASS。

應提交原因及替代指標，經 G0 修訂與 Martin 批准後重測。

24. Claude Independent Measurement

沿用 WE-01 B8 的配對方法。

至少包含：

PHONE_LOW、TABLET_MED、DESKTOP_HIGH。

固定地點：

- B1 (240,1080)
- B2 (-700,945)
- B3 (-490,-710)
- Site A (-501,-790)
- CBD (-60,0)
- Suburbs (-1060,-238)

固定時段：

12:00、23:00。

Headless viewport：800 × 450。

固定相機與載入完成狀態。

靜態渲染測試：

每場景暖機至少20幀，記錄120幀。

物理測試：

至少5組 BASE/PR 配對。

每組暖機900步，記錄360步。

physicsWorld.step(1/60,1/60,3)。

動態串流測試：

至少5組可重播路徑。

每組記錄至少60秒的固定模擬時間。

同時記錄實際執行時間，兩者不得混淆。

動態測試須覆蓋區塊邊界、載入、卸載、LOD 切換及目的地準備。

不得使用 headless FPS 代替實機 FPS。

25. Martin Device Acceptance

必要裝置：

Samsung Galaxy S26 Ultra。

Samsung Galaxy Tab S11。

必要 preset：

PHONE_LOW、PHONE_MED、TABLET_MED，依裝置及既有支援配置執行。

固定記錄：

- 遊戲版本及 SHA。
- 裝置及畫質。
- 解析度及方向。
- FPS cap。
- 是否自動降畫質。
- 測試時段。
- 測試負載。
- 裝置溫度狀態或可取得的熱限制資訊。

每個必要裝置／preset：

- 暖機至少3分鐘。
- 40棟及60棟負載各測試3次。
- 每次至少120秒。
- 包含日間、夜間及區塊切換路徑。
- 使用遊戲內診斷資料，不以錄影幀率代替遊戲 FPS。

初始驗收：

- 每次平均 FPS ≥30。
- Frame time P95 ≤40 ms。
- Frame time P99 ≤66.7 ms。
- 最近60秒最低1秒 FPS ≥24。
- 超過100 ms的幀數占比 ≤0.5%。
- 崩潰、必要碰撞缺失、永久資源錯誤均為0。

上述門檻允許少量瞬間波動，不代表每一幀都達到30 FPS。

不得以自動降低畫質掩蓋固定 preset 的效能不足。

實機資料缺失則 WS24 為 PENDING，不得宣稱完整 WE-03 驗收完成。

26. Failure and Rollback

以下任一情況阻止該子任務驗收：

- 必要碰撞缺失。
- 玩家穿越應存在的碰撞體。
- 重複資源或持續性洩漏。
- 既有存檔損壞。
- 既有玩法回歸。
- PWA 離線功能失效。
- 效能超出正式批准預算。
- Claude 無法獨立重現必要測試。
- 缺少必要實機資料。

所有測試功能必須可停用。

停用後不得留下串流專屬活躍資源。

正式發布的回退由 Claude 依協作規則處理。

禁止實作者自行修改 CACHE 或直推 main。

27. Final Deliverables

建議 Claude 建立：

specs/we03/architecture.md

specs/we03/streaming_contract.md

specs/we03/performance_budget.md

specs/we03/baseline_report.md

specs/we03/stress_test_report.md

specs/we03/device_acceptance.md

specs/we03/we03_validation.md

各檔案由相應子任務逐步產生。

文件不得宣稱未完成的測試或未批准的工程已完成。

28. Final Acceptance

WE-03 結案須同時具備：

1. 全部正式登記子任務完成。
2. WS01–WS28 通過。
3. Claude 獨立驗證。
4. CI 接線及通過證據。
5. Martin 實機接受。
6. 正式效能預算完成。
7. WE-01／WE-02 裁定不變。
8. 正式世界無未批准建設。

WE-03 結案不自動授權 WE-04。

29. G0 Open Questions

Claude 須審查：

- T-018 系列編號是否可用。
- Engineering BASE 完整 SHA。
- 既有診斷介面是否足以省略 A2。
- 所有實際畫質 preset 的映射。
- 128 m grid 與完整 bounds 查詢契約。
- 合成測試場景隔離方式。
- 碰撞預載與遊戲最高速度的關係。
- 量化預算是否可重現及合理。
- 手機實機 frame time 資料採集能力。
- 測試資源及 PWA 相容性。
- 子任務行數與檔案 allowlist。
- Gemini Stage 3 指派是否符合 COLLAB。
- WE-03A 校準後的預算修訂及批准流程。

Claude 應回傳 APPROVE、APPROVE WITH CONDITIONS 或 REVISE。

本草案不是開工授權。

END OF WE-03 v1.0