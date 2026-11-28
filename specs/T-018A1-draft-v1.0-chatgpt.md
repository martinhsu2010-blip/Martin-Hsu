T-018A1 v1.0 — WE-03 Performance Baseline and Architecture Calibration

Status: DRAFT — Pending Martin Approval

Author: ChatGPT

Owner: Claude

Risk: LOW（唯讀分析與獨立測試工具）

Volume: LARGE

Engineering BASE:
e8d5250fce0ea5f07f68840481cb95d2eca803fb

Historical Audit BASE:
84319439243b51aa8d119e33eb62a0637feea887

Release: vh-2026-11-27-02

1. Objective

建立 WE-03 C+ 架構的可重現效能基準，校準 LOD、碰撞、資源管理及串流效能預算。

本任務不實作串流系統，不修改正式遊戲內容。

依據：

- WE-03 v1.0。
- Claude G0 B1–B6、N1–N10。
- COLLAB.md v3.6。
- AGENTS.md。
- TASKS.md。
- DECISIONS.md D-057、D-060–D-064。
- specs/we02/ 正式規劃產物。
- WE-01 B8 runtime baseline appendix。

2. File Scope

建議新增：

- tools/test/we03_baseline.py
- tools/test/we03_calibration.py
- tools/test/we03_calibration_check.py
- specs/we03/baseline_report.md
- specs/we03/baseline_metrics.json
- specs/we03/calibration_report.md
- specs/we03/proposed_budgets.json
- specs/we03/fixture_plan.json

測試工具建議上限：

- Baseline：600行。
- Calibration：500行。
- Independent checks：400行。

合計1500行。

若無法在範圍內完成，停止並提出拆分方案。

Claude 依正式維護者權限處理任務登記、文件及必要 CI 接線。

禁止修改：

- index.html。
- sw.js。
- CACHE。
- manifest.json。
- 遊戲資產。
- vh_save schema。
- WE-01／WE-02 正式產物。

3. A01 — Source Inventory

盤點現有：

1. 世界初始化及生成流程。
2. Renderer 與動畫迴圈。
3. Physics step 呼叫位置。
4. TREE_COLLIDERS。
5. 既有 LOD 系統。
6. 材質、幾何及貼圖生命週期。
7. 快速旅行及重生流程。
8. 畫質切換與 reset 路徑。
9. window.__VH 診斷介面。
10. ?fps=1 現有行為。

每個項目須記錄：

- 實際函式或變數名稱。
- 原始碼位置。
- 相關呼叫路徑。
- WE-03 潛在整合風險。
- 是否需要後續子任務修改。

禁止將推測標示為原始碼已確認行為。

4. A02 — Preset Inventory

盤點全部11個畫質 preset：

- PHONE_LOW
- PHONE_MED
- TABLET_LOW
- TABLET_MED
- TABLET_HIGH
- DESKTOP_MED
- DESKTOP_HIGH
- DESKTOP_ULTRA
- IGPU_LOW
- IGPU_MED
- IGPU_HIGH

每個 preset 記錄實際：

- Pixel ratio / resolution scale。
- Shadow resolution。
- Fog。
- Post-processing。
- Traffic / NPC density。
- Props density。
- FPS cap。
- 既有 LOD 行為。

提出全部11個 preset 的 C+ 映射。

映射至少包含：

- LOD0/1/2 距離。
- Hysteresis。
- 更新頻率。
- 預載時間。
- CPU 工作預算。
- 資源預算。

未經批准的 preset 映射不得啟用串流。

5. A03 — Headless Baseline

必要 preset：

PHONE_LOW、PHONE_MED、TABLET_MED、DESKTOP_HIGH。

固定場景：

- B1 (240,1080)
- B2 (-700,945)
- B3 (-490,-710)
- Site A (-501,-790)
- CBD (-60,0)
- Suburbs (-1060,-238)

時段：

12:00、23:00。

共48個 preset／場景／時段組合。

Viewport：800 × 450。

每個組合：

- 暖機至少20幀。
- 記錄120個完整幀。
- 固定相機、模擬時間及載入狀態。

合計至少5760個正式記錄幀。

記錄：

- Draw calls。
- Render triangles。
- Frame time P50/P95/P99。
- Bodies / shapes。
- Meshes / InstancedMeshes。
- Materials / geometries / textures。
- Geometry buffer estimate。
- Texture memory estimate。
- Renderer capability。

所有資源計量須去除重複引用。

貼圖估計須明列 mipmap、格式與估算限制。

Headless 數據不得標示為實機 FPS 或實際 VRAM。

6. A04 — Physics Baseline

沿用 WE-01 B8 方法。

四個必要 preset 均執行至少5組 BASE 自身對照配對。

每組：

- 900步暖機。
- 360步正式量測。
- physicsWorld.step(1/60,1/60,3)。

記錄所有樣本及比率。

初始控制穩定區間：

1/1.10 至 1.10。

控制組不穩定時：

- 記錄載入狀態。
- 排查量測競態。
- 不得刪除不利樣本。
- 無法解決時標記 INCONCLUSIVE。

Headless frame-time P95 若無有效控制組，標記 INCONCLUSIVE，不單獨作為阻擋條件。

確定性資源數量及物理中位數仍為必要硬性閘門。

7. A05 — Movement and Readiness Calibration

在遊戲模擬環境量測：

- 既有車輛最大速度。
- Nitro 狀態最大速度。
- 玩家及相關動態物件速度。
- 更新週期造成的最大移動距離。

Claude 提出的約113 m/s 僅為理論估計，須與實際遊戲量測區分。

提出 T_ready 量測方法，包含：

- 工作排隊時間。
- 排程更新延遲。
- 碰撞體建立時間。
- 物理安全點等待時間。

由於 A1 尚無實際串流系統，T_ready 不得宣稱已完成正式實測。

最終碰撞準備時間須由 T-018D／E1 驗證。

提出碰撞 shapes-per-building 初始上限及其依據。

不得修改車輛操控、物理參數或正式交通 AI。

8. A06 — Chunk and Fixture Calibration

初始 grid：

128 × 128 m。

比較64、128、256 m 三種尺寸的：

- 住宅覆蓋區塊數。
- 跨區塊物件數。
- 每區塊物件分布。
- 潛在載入工作量。

Owner：

住宅 footprint 中心所在區塊。

半開區間：

[k × 128, (k+1) × 128)。

Coverage：

floor(min/128) 至 ceil(max/128)-1。

Parent index：

Math.floor(c/2)。

驗證負座標及邊界案例：

-1、-2、-3、-128、-128.0001、0、127.9999、128。

獨立重算 Claude 報告中的34個跨區塊地塊及最多4區塊覆蓋結果。

若結果不同，報告 footprint 與 parcel bounds 定義差異，不得直接修改正式地塊。

9. A07 — Synthetic Fixture Plan

提出確定性測試配置：

40棟：R01 9、R02 5、R05 22、R08 4。

57棟：R01 12、R02 7、R05 33、R08 5。

60棟：R01 13、R02 7、R05 34、R08 6。

120棟：R01 26、R02 14、R05 68、R08 12。

40／57棟使用 WE-02 對應規劃資料。

60／120棟額外測試位置須：

- 確定性生成。
- 不互相重疊。
- 不侵入 Site A 保護區。
- 明確標記為 SYNTHETIC_ONLY。
- 不寫入 district_plan.json。

此配置不是合法地塊、道路可達性或施工可行性證據。

提出至少5條可重播測試情境，包含區塊邊界、反向移動、遠景觀察及測試專用目的地切換。

實際 fixture loader、測試模型與 replay driver 由 T-018C2 負責。

10. A08 — LOD and Triangle Budget Calibration

沿用 WE-03 v1.0 初始模型面數。

獨立重算57棟負載的最差視角三角形數量。

Claude G0 參考：

PHONE_LOW：192650。

TABLET_MED：226700。

DESKTOP_HIGH：230900。

上述為待重現的分析值。

比較：

- Worst-case viewpoint。
- Replay path P95。
- 各原型及 LOD 的貢獻。
- 高樓螢幕投影大小。
- 相機及 fog 影響。
- 高速移動時跳過 hysteresis 的風險。

提出調整後的 LOD 距離及模型預算。

不得藉移除必要碰撞或應顯示的建築取得較低數字。

A1 所得住宅負載數字為分析估算，不是實際新增住宅的 renderer 量測。

11. A09 — Streaming Benefit Calibration

建立兩個分析對照：

Control A：住宅資源常駐，使用相同 LOD 策略。

Candidate C+：住宅資源區域串流，使用相同 LOD 策略。

分別估算：

- Geometry 資源節省。
- Texture 資源節省。
- 活躍碰撞體節省。
- 物件實例數。
- 常駐及快取資源。

四種原型共用 atlas，因此貼圖節省可能接近0。

不得刻意增加 Control A 的重複資源。

Claude G0 所述碰撞體節省至少58%屬待重現的分析預期，不能直接視為正式驗收結果。

提出修訂後的效益門檻，交 ChatGPT 審查及 Martin 批准。

12. A10 — Device Measurement Protocol

制定 S26 Ultra 與 Tab S11 實機量測流程。

使用 ?fps=1。

手動固定 preset。

禁止自動降畫質及動態解析度掩蓋效能問題。

記錄：

- Release / CACHE。
- FPS cap。
- Preset。
- Resolution scale。
- Frame time P50/P95/P99。
- 超過50 ms及100 ms的幀數。
- 1秒 FPS 統計。

FPS 驗收採 G0 修正：

平均 FPS ≥ FPS cap × 0.97。

若 FPS cap 為30，門檻為29.1 FPS。

30 FPS 仍為目標，29.1 為計時容差，不代表降低長期效能目標。

A1 僅交付量測協議。

A2 完成後，Martin 才執行無串流的正式實機基準量測。

13. A11 — Proposed Performance Budgets

輸出 proposed_budgets.json。

至少包含：

- 11個 preset 的映射。
- LOD thresholds。
- Draw calls。
- Triangles。
- Geometry / texture estimates。
- Active bodies / shapes。
- Physics step ratio。
- Streaming CPU budget。
- Device frame-time thresholds。
- Streaming benefit targets。

每項數值標記來源：

MEASURED_HEADLESS

ANALYTIC_ESTIMATE

PROPOSED_LIMIT

PENDING_DEVICE

不得將未量測的預算標記為已驗證。

A1 結案不自動批准修訂後的預算。

14. Automated Verification

A1-G01：正式遊戲檔案差異為0。

A1-G02：11個 preset 盤點完整。

A1-G03：48個必要 headless 組合完整。

A1-G04：每組至少120個正式記錄幀。

A1-G05：四個 preset 各至少5組物理配對。

A1-G06：原始量測樣本及環境資訊完整。

A1-G07：負座標與邊界索引測試通過。

A1-G08：40／57／60／120棟數量及原型組成正確。

A1-G09：合成配置重疊數為0。

A1-G10：Site A 測試配置侵占為0。

A1-G11：WE-02 正式產物未修改。

A1-G12：三角形預算分析可重現。

A1-G13：Control A 無刻意重複資源。

A1-G14：全部預算數值具有來源分類。

A1-G15：實機協議與 A2 診斷需求完整。

A1-G16：所有失敗及 INCONCLUSIVE 結果均有紀錄。

A1-G17：測試工具具有獨立檢查與負向控制。

A1-G18：未批准檔案變更為0。

負向控制至少覆蓋：

- 缺少 preset。
- 缺少量測組合。
- 重複 object ID。
- 負座標錯誤。
- 合成住宅重疊。
- 原型棟數錯誤。
- 未量測數值被錯標為實測。

確定性檢查接入適用 CI。

耗時效能量測不在 CI 中設置不穩定的時間硬閘門。

15. Acceptance and Next Step

Claude 提交：

- 完整 baseline report。
- 原始量測 JSON。
- Calibration report。
- Proposed budgets。
- Fixture plan。
- 測試結果及實際執行命令。
- 未完成項目及風險。
- T-018A2 必要診斷需求。

ChatGPT 審查分析方法及預算。

Martin 接受 A1 結果後，才進入 A2 的獨立規格批准流程。

A1 不授權 B、C1–C4、D、E1–E2、F1–F2 或 WE-04–WE-09。

END OF T-018A1 v1.0