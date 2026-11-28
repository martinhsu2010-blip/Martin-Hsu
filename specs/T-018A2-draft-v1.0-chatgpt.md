T-018A2 — Device Frame-Time Diagnostics v1.0

1. Task Metadata

Project: VICE HORIZON VI
Repository: martinhsu2010-blip/Martin-Hsu
Task ID: T-018A2
Version: v1.0 DRAFT
Status: Pending Claude G0 Review
Design Owner: ChatGPT
Implementer: Codex
Reviewer / Releaser: Claude
Final Approver: Martin
Priority: P1
Risk: HIGH
Volume: SMALL

Observed main:
9538c297fb7cb7dc702a6e5d7d1f21e502bbb251

Historical Audit Game BASE:
84319439243b51aa8d119e33eb62a0637feea887

WE-03 Engineering BASE:
e8d5250fce0ea5f07f68840481cb95d2eca803fb

Current CACHE:
vh-2026-11-27-02

Predecessor: T-018A1 — Accepted under D-067.
Successor: T-018B — NOT AUTHORIZED.

Martin 已選擇方案 C（Progressive Hybrid Performance Budget Governance）作為設計方向，但尚未正式批准修訂預算或授權 A2 實作。

選擇 Codex 的理由：本任務涉及 animate()、物理更新與 renderer 的效能量測路徑，屬於小量高風險任務，符合 COLLAB v3.6 分工原則。

2. Required Reading

- COLLAB.md v3.6
- AGENTS.md
- TASKS.md
- DECISIONS.md
- D-013、D-021、D-026
- D-065、D-066、D-067
- specs/WE-03-series-spec-v1.0.md
- specs/WE-03-draft-v1.0-chatgpt.md
- specs/WE-03-g0-review-v1.0.md
- specs/T-018A1-spec-v1.0.md
- specs/we03/a1_findings.md
- specs/we03/baseline_report.md
- specs/we03/baseline_metrics.json
- specs/we03/calibration_report.md
- specs/we03/calibration_data.json
- specs/we03/proposed_budgets.json

系列正式規格及 Claude G0 條件優先於原始草案。

Claude 必須在正式登記及開工前重新確認完整 main SHA，並驗證遊戲原始碼是否與 A1 基準一致。

3. Objective

建立可信、低成本、可重現的裝置效能診斷功能，供後續 WE-03 世界串流架構使用。

A2 必須：

1. 擴充既有 ?fps=1。
2. 提供真實渲染幀間隔統計。
3. 保留冷啟動及暖機後的長幀證據。
4. 提供可取得的 CPU 時間歸因。
5. 提供物理及渲染計數。
6. 提供自動化測試可讀取的診斷快照。
7. 建立串流實作前的裝置效能基準。
8. 維持原有遊戲行為及效能設定。

A2 是診斷工具，不是效能最佳化任務。

4. Non-Goals

本任務不得實作：

- Chunk Registry。
- Asset Registry。
- LOD Controller。
- Collision Streaming。
- Predictive Scheduler。
- Destination Readiness。
- Shader production prewarming。
- 建築、道路或地形擴建。
- 物理引擎最佳化。
- FPS cap 或 frame pacing 修改。
- 自動畫質演算法修改。
- 動態解析度演算法修改。
- WE-04 至 WE-09。
- 既有世界遷移。
- 新增正式遊戲內容。
- 修改 WE-01 或 WE-02 裁定。
- 新增存檔欄位或 localStorage key。
- 新增外部依賴或 CDN。

5. Activation and Isolation

沿用既有 ?fps=1 作為唯一診斷啟用入口。

正常模式：

- 不顯示新增診斷 HUD。
- 不配置診斷樣本緩衝區。
- 不執行額外效能計時。
- 不執行額外物理或資源統計。
- 不新增背景計時器。
- 不新增診斷事件紀錄。
- 僅允許必要的啟用狀態判斷。

診斷模式：

- 沿用既有 ?fps=1 行為。
- 維持既有停用自動畫質及動態解析度的診斷設定。
- 不改變 FPS cap。
- 不改變物理步進。
- 不改變遊戲更新順序。
- 不新增場景物件。
- 不新增任何遊戲材質或貼圖。

6. Frame Interval Measurement

6.1 Definition

Frame interval 必須量測連續實際渲染幀之間的時間間隔。

不得將所有 requestAnimationFrame callback 視為已渲染幀。

例如：

- Display refresh rate = 120 Hz。
- Game fpsCap = 30。
- 正確的正常 frame interval 應接近 33.33 ms，而非 8.33 ms。

必須尊重既有 FPS cap early-return 邏輯。

不得為診斷功能修改原有 frame pacing。

6.2 Required Statistics

必須提供：

- Frame-time P50。
- Frame-time P95。
- Frame-time P99。
- Frames > 50 ms。
- Frames > 100 ms。
- Frames > 50 ms ratio。
- Frames > 100 ms ratio。
- Longest frame interval。
- Longest frame sequence / timestamp。
- Valid sample count。
- Measurement duration。
- Existing average FPS。
- Existing lowest 1-second FPS over the last 60 seconds。

保留原有 FPS HUD 的平均 FPS 與最低 1 秒 FPS 功能。

6.3 Percentile Definition

使用 nearest-rank percentile。

Rank = ceil(p × N)。

空樣本不得回報為 0 ms 或 PASS，應標示無有效樣本。

所有有效長幀均須納入統計。

禁止：

- 刪除異常長幀。
- 將長幀截斷至固定上限。
- 使用遊戲物理 dt clamp 作為真實 frame interval。
- 將冷啟動長幀混入暖機後統計而不加區分。
- 使用平滑平均取代原始幀間隔。

6.4 Time Alignment

必須明確定義 frame interval 與 CPU attribution 的時間邊界。

連續渲染起點間隔與前一幀 CPU 工作的關係必須正確對齊。

若部分時間無法可靠歸因，應分開報告或標示 UNATTRIBUTED。

不得強行將不相容的時間區段相加。

7. CPU Attribution

在不改變既有執行順序的前提下，提供：

7.1 Physics

量測既有 physicsWorld.step() 的 CPU elapsed time。

不得：

- 修改 FIXED_TIME_STEP。
- 修改 dt。
- 修改 maxSubSteps。
- 新增額外 physicsWorld.step()。
- 改變物理更新順序。

7.2 Game Update

量測既有遊戲更新區段 CPU elapsed time。

如包含 physics 或 render 時間，必須清楚標示包含關係，避免重複計算。

7.3 Render Submission

量測 renderer.render() 呼叫的 CPU elapsed time。

此指標只能稱為 CPU render submission / elapsed time。

不得將其稱為 GPU execution time。

7.4 Resource Events

在瀏覽器及 renderer 可提供資訊的範圍內，記錄：

- Shader program count。
- Shader program count delta。
- Texture count。
- Texture count delta。
- Geometry count。
- 相關長幀發生時的資源計數。

Program 或 texture count 增加只能作為事件相關性證據。

不得直接認定為 shader compilation 或 texture upload 的實際耗時。

7.5 Unsupported Metrics

GPU timing 與 GC timing 若無可靠支援，必須標示 UNAVAILABLE。

不得以 0 ms 代替不支援的指標。

不要求新增 GPU timer query、CDP profiler 或其他高成本診斷機制至 production runtime。

獨立測試工具可使用既有瀏覽器能力進行額外分析。

8. Physics and Rendering Counters

提供以下計數：

- Physics bodies。
- Physics shapes。
- Physics contacts per step。
- Draw calls。
- Triangles。
- Shader programs。
- Textures。
- Geometries。

Bodies 與 shapes 必須使用明確且一致的計數口徑。

Contacts 必須定義為實際可取得的物理步進接觸資料，不得將其誤稱為不同接觸物件數量。

Draw calls 與 triangles 採 renderer.info 可取得的計數口徑，並明確說明是否包含所有渲染 pass。

不得將 renderer.info.memory 稱為實測 VRAM。

A1 已證明 headless physics timing self-control 在四個 preset 均為 INCONCLUSIVE。

因此：

- A2 必須提供物理時間。
- 不得將未驗證的 physics timing ratio 設為新的硬性通過條件。
- 優先使用可重現的 bodies、shapes、contacts 計數進行結構性回歸驗證。

9. Cold and Warm Measurement

9.1 COLD

新頁面載入後的首次渲染及初次資源使用。

必須保留：

- 首次有效渲染後的幀間隔。
- 首次資源使用相關事件。
- Shader program count 變化。
- 長幀。
- 最長幀相關 CPU attribution。

首次渲染前的頁面啟動時間若可取得，應獨立報告，不得當作兩個渲染幀之間的 interval。

9.2 WARM

完成指定暖機流程後，建立獨立量測區段。

不得覆蓋或刪除 COLD 證據。

9.3 Shader Prewarming

Shader prewarming 僅允許作為獨立測試流程。

不得：

- 加入正常遊戲啟動程序。
- 自動執行 renderer.compile() 作為 production 最佳化。
- 刪除原始 cold series。
- 將暖機後的結果冒充冷啟動結果。

10. Diagnostic Data Contract

透過既有 window.__VH debug handle 提供唯讀診斷快照。

建議 schema：we03-diagnostics-v1。

必要欄位：

- schema
- phase
- preset
- resScale
- fpsCap
- refreshRate
- cache
- sampleCount
- durationMs
- frameP50
- frameP95
- frameP99
- over50
- over100
- over50Ratio
- over100Ratio
- longestFrame
- physicsStepMs
- gameUpdateMs
- renderSubmissionMs
- bodies
- shapes
- contacts
- drawCalls
- triangles
- programs
- textures
- geometries
- gpuTime
- gcTime
- overflow
- segmentStatus

Metadata 必須反映實際量測條件。

CACHE 必須來自可驗證的真實釋出版本。

不得硬編碼可能與實際 service worker 版本不一致的 CACHE 值。

若無法可靠取得 CACHE 或 refresh rate，允許標示 UNAVAILABLE，並由測試報告補充經獨立驗證的值。

Debug API 不得提供修改遊戲物理、畫質或世界狀態的額外能力。

11. Sampling and Memory Budget

以下為待 Claude G0 確認的工程提案：

- HUD 更新頻率：每秒最多 1 次。
- 即時統計視窗：最近 60 秒。
- 預配置樣本容量：16,384 筆。
- 診斷緩衝區總容量：不超過 1 MiB。
- Hot loop 每幀新增物件配置：0。
- 每幀 console output：0。
- 新增背景計時器：0。

允許使用固定容量 typed arrays 或其他等效預配置結構。

百分位數計算及 HUD 字串更新不得在每一幀執行。

若樣本容量不足以涵蓋完整量測視窗，必須明確標示 overflow / incomplete。

正常環形緩衝區移除已超出統計視窗的舊資料，不等於量測 overflow。

不得默默丟棄仍屬有效視窗的資料後宣稱統計完整。

COLD 與 WARM 證據必須分離。長時間測試應透過低頻率快照或獨立測試工具保存完整區段證據，不要求無限增加 runtime 記憶體。

12. Segment Integrity

以下事件必須能辨識為量測區段邊界：

- Background tab / visibility change。
- Pause / resume。
- Preset change。
- FPS cap change。
- Resolution scale change。
- Cold-to-warm transition。

不同設定的樣本不得混入同一正式量測結果。

背景暫停時間不得被誤認為正常遊玩長幀，但必須保留中斷事件證據。

正常前景遊玩中發生的多秒長幀不得被當作背景暫停而排除。

若區段不完整，應標示 INCOMPLETE 或 INCONCLUSIVE。

13. Diagnostic HUD

擴充既有 FPS HUD，採精簡文字設計。

必要顯示內容：

VICE HORIZON VI — PERFORMANCE

Preset / Resolution scale / FPS cap
COLD or WARM
Average FPS
Lowest 1s FPS over 60s
P50 / P95 / P99
Frames > 50 ms
Frames > 100 ms
Longest frame
Physics step CPU time
Game update CPU time
Render submission CPU time
Bodies / Shapes / Contacts
Draw calls / Triangles
GPU / GC availability
Sample count / Segment status

不要求新增圖表、動畫或複雜 UI。

若 HUD 空間不足，可將完整欄位保留於 debug snapshot。

不得影響正常遊玩 HUD、Game Hub 或觸控控制。

14. Preset Coverage

診斷功能必須支援全部 11 種既有 preset：

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

診斷支援不等於串流支援。

尚未批准串流映射的 7 種 preset 不得因此自動啟用串流。

15. Progressive Hybrid Budget Governance

Martin 選擇方案 C 作為設計方向。

以下治理制度須由 Claude G0 審查及 Martin 正式確認。

15.1 HARD_GATE

已正式批准且具備可靠驗證方法的硬性限制。

超標阻擋合併或驗收。

15.2 SOFT_TARGET

暫定工程目標。

超標必須報告原因及改善建議，但不得自動宣稱整個架構失敗。

15.3 PENDING_EVIDENCE

尚缺可靠量測證據。

不得宣稱 PASS。

15.4 A2 Proposed Structural Gates

在相同可重現場景、相機、畫質、時間及物理初始狀態下：

- Added physics bodies = 0。
- Added physics shapes = 0。
- Deterministic fixture contacts delta = 0。
- Added scene draw calls = 0。
- Added scene triangles = 0。
- Added scene meshes = 0。
- Added game materials = 0。
- Added game textures = 0。
- Added runtime dependencies = 0。
- Added localStorage keys = 0。
- Added hot-loop per-frame object allocations = 0。
- index.html added + changed lines ≤ 250。

不得要求所有非確定性自由遊玩過程的 contacts 完全相同。

15.5 Diagnostic Overhead

診斷取樣 CPU 成本 P95 暫定目標 ≤ 0.2 ms。

此數值為 SOFT_TARGET，並非已驗證硬性閘門。

低頻率統計更新成本須另行報告。

診斷工具自身造成的長幀不得從結果刪除。

A1 headless timing validity 為 INCONCLUSIVE，因此不得將不可靠的時間比較作為 CI 硬性通過依據。

15.6 Existing Series Triangle Budgets

維持原始暫定值：

PHONE_LOW: 120,000
PHONE_MED: 160,000
TABLET_MED: 200,000
DESKTOP_HIGH: 350,000

以上為新增 triangles P95 暫定預算。

PHONE_MED 為插值，尚未正式批准。

A1 analytic replay P95 including shadow：

PHONE_LOW: 133,000
PHONE_MED: 189,000
TABLET_MED: 193,000
DESKTOP_HIGH: 246,700

以上為 ANALYTIC_ESTIMATE，不是實際 renderer P95。

不得據此直接宣稱 PHONE_LOW 或 PHONE_MED 驗收失敗。

正式驗證由 C4 / F2 負責。

其他 draw-call、資源容量、物理時間、LOD 距離及串流 CPU 預算維持 PROPOSED_NOT_APPROVED。

16. Proposed Streaming Benefit Revision

本節為系列預算治理提案，不屬於 A2 實作範圍。

A1 顯示四種共用原型及 atlas 架構下，Geometry / Texture 常駐節省可能接近零。

57 棟住宅、每棟一個 body、假設 217 m 碰撞半徑：

- Peak-grid body saving: 56.1%。
- Replay P95 body saving: 66.7%。
- Shared geometry / texture saving: approximately 0%。

以上均為 ANALYTIC_ESTIMATE。

217 m 不是正式批准的碰撞半徑。

建議修訂串流效益閘門：

1. Active collision bodies P95 相較同一測試物件集合的全常駐對照組降低至少 20%。
2. Geometry / Texture 常駐量及節省比例完整報告，不強制降低 20%。
3. 碰撞安全及載入正確性優先於節省比例。
4. 不得為達成效益目標縮小必要安全碰撞範圍。
5. 不得使用 GLOBAL_STRESS_ONLY 物件作為合法土地或 B3 密度證據。
6. Collision radius 由 D / E1 確定。
7. Resource residency 由 C1 確定。
8. 實際 LOD triangle validation 由 C4 / F2 負責。

此修訂須與 A2 授權分開批准。

17. File Allowlist

允許修改：

1. index.html
2. tools/test/we03_a2_diagnostics_check.mjs
3. tools/test/we03_a2_browser_check.py

index.html hard ceiling：

250 added + changed lines。

兩份測試檔案合計建議上限：

500 lines，待 G0 確認。

診斷核心須使用明確 begin/end banner，供 Node 測試擷取。

不得新增 runtime files。

不得新增 binary assets。

不得修改：

- sw.js
- CACHE
- PRECACHE
- .github/
- COLLAB.md
- AGENTS.md
- TASKS.md
- DECISIONS.md
- HANDOFF.md
- LOG.md
- specs/
- WE-01 / WE-02 artifacts
- Existing save schema

Claude 負責正式文件登記、CI wiring 及釋出 CACHE 更新。

18. Automated Acceptance Gates

A2-G01 — Default OFF

正常模式不配置診斷緩衝區、不執行診斷取樣、不顯示新增診斷 HUD。

A2-G02 — Diagnostic ON

?fps=1 正確啟用診斷，維持原有診斷設定。

A2-G03 — Percentiles

P50、P95、P99 與獨立 nearest-rank 計算一致。

A2-G04 — Long Frames

所有有效長幀均保留，不得截斷或刪除。

A2-G05 — Threshold Boundaries

正確區分等於與大於 50 ms / 100 ms。

A2-G06 — FPS Cap

未渲染的 rAF callback 不得被計為渲染幀。

A2-G07 — Cold / Warm

冷暖區段分離，冷啟動證據保留。

A2-G08 — Physics Counters

Bodies、shapes、contacts 與獨立計數一致。

A2-G09 — CPU Attribution

量測區段正確，不重複計算、不錯配幀。

A2-G10 — Unsupported Metrics

不支援的 GPU / GC timing 標示 UNAVAILABLE。

A2-G11 — Memory

固定容量，無每幀新增物件配置。

A2-G12 — Rendering Regression

固定情境下 scene draw calls delta = 0，triangles delta = 0。

A2-G13 — Physics Regression

固定情境下 bodies delta = 0，shapes delta = 0；確定性 fixture contacts delta = 0。

A2-G14 — Existing FPS HUD

原有 average FPS 與 lowest 1-second FPS 功能保留。

A2-G15 — Metadata

Preset、resScale、fpsCap、版本及可取得的裝置 metadata 正確。

A2-G16 — Offline / Save

既有離線功能與存檔相容性不變。

A2-G17 — Preset Coverage

全部 11 種 preset 均可啟用診斷，不擴大串流授權。

A2-G18 — Segment Integrity

Overflow、背景暫停及設定切換正確辨識。

19. Deterministic Test Fixtures

固定幀間隔樣本：

[16, 20, 30, 33, 33, 40, 50, 51, 100, 120]

Expected:

Sample count = 10
P50 = 33 ms
P95 = 120 ms
P99 = 120 ms
Frames > 50 ms = 3
Frames > 100 ms = 1
Frames > 50 ms ratio = 30%
Frames > 100 ms ratio = 10%
Longest frame = 120 ms

其他必要案例：

- Empty sample set。
- Single sample。
- Identical samples。
- Unsorted samples。
- Exactly 50 ms。
- Exactly 100 ms。
- Multi-second frame。
- Ring-buffer wraparound。
- Valid-window capacity overflow。
- FPS-cap skipped callback。
- Cold-to-warm transition。
- Background-to-foreground transition。
- Preset / fpsCap change。

測試不得只依賴 production helper 的相同演算法產生預期值。

20. Negative Controls

至少驗證以下故意錯誤會觸發對應失敗：

1. Incorrect percentile calculation。
2. Threshold > changed to >=。
3. Long frames removed。
4. Long frames clamped。
5. Skipped rAF callbacks counted as rendered frames。
6. Cold and warm samples mixed。
7. Diagnostics enabled by default。
8. Incorrect physics counters。
9. Incorrect renderer counters。
10. Unsupported GPU timing reported as zero。
11. Overflow hidden。
12. CPU attribution assigned to the wrong frame。

所有負向控制須有可識別的 failing assertion。

不得將測試執行失敗或環境錯誤當成成功的負向控制。

21. Mandatory Regression Checks

依 AGENTS.md 執行：

python3 tools/test/syntax_check.py

python3 tools/test/i18n_check.py

node tools/test/i18n_check.mjs

node tools/test/hud_check.mjs

node tools/test/camera_check.mjs <BASE_SHA>

node tools/test/traffic_check.mjs

node tools/test/collision_check.mjs

node tools/test/suburb_check.mjs

node tools/test/urban_check.mjs

新增任務測試：

node tools/test/we03_a2_diagnostics_check.mjs

python3 tools/test/we03_a2_browser_check.py

沿用既有 Playwright 1.55.0 測試環境。

另須執行既有 PWA offline 與 save compatibility checks。

Claude 負責獨立重跑、確認負向控制及 CI wiring。

Timing measurements 不直接納入 CI 硬性通過閘門。

所有未執行或無法完成的測試須明確報告。

22. Device Measurement Protocol

Primary devices:

Samsung Galaxy S26 Ultra
Samsung Galaxy Tab S11

Primary presets:

S26 Ultra:
PHONE_LOW
PHONE_MED

Tab S11:
TABLET_MED

Supplementary:
TABLET_HIGH

Device tests 使用 ?fps=1。

手動固定 preset。

停用自動畫質與動態解析度，沿用既有診斷模式行為。

記錄：

- Device model。
- Browser / version。
- Preset。
- resScale。
- fpsCap。
- Display refresh rate。
- Game release。
- CACHE。
- Power state。
- Thermal conditions。
- Scene。
- Time of day。
- Cold / warm phase。
- Measurement duration。
- Valid sample count。

建議測試情境：

- CBD daytime。
- CBD nighttime。
- Midtown。
- Suburbs。
- Mountain。
- Highway。
- Fast Travel。

優先沿用 A1 已記錄的場景位置及測試條件。

不得自行更改固定基準以取得較佳結果。

建議流程：

1. 獨立冷啟動紀錄。
2. 暖機 60 秒。
3. 正式暖機後量測 60 秒。
4. 暖機後正式測試至少重複 3 次。

具體測試矩陣與重複次數由 Claude G0 確認可行性。

23. Device Performance Targets

沿用系列 B4 條件：

Average FPS ≥ fpsCap × 0.97。

30 FPS cap：

Average FPS ≥ 29.1。

原始 30 FPS 裝置體驗目標不變。

既有 frame-time 草案目標：

P95 ≤ 40 ms。
P99 ≤ 66.7 ms。

既有最低 1 秒 FPS 與 > 100 ms ratio 條件沿用系列規格，不得由 A2 擅自修改。

A2 的工具正確性驗收與整體 WE-03 裝置效能驗收必須分開。

未達整體裝置效能目標不得被隱藏，但也不得直接認定診斷工具本身錯誤。

正式串流裝置效能驗收由 F2 負責。

24. Evidence Classification

所有效能報告須使用適當分類：

MEASURED_DEVICE
MEASURED_HEADLESS
ANALYTIC_ESTIMATE
PROPOSED_LIMIT
PENDING_DEVICE
INCONCLUSIVE
UNAVAILABLE

不得將 headless FPS 當作裝置 FPS。

不得將估算資源容量稱為實測 VRAM。

不得將不支援的指標當作 0。

不得將 A1 不穩定的 physics timing ratio 宣稱為已驗證回歸閘門。

25. Implementation Line Budget

index.html maximum: 250 added + changed lines。

建議分配：

Initialization / activation: 25
Sampling / fixed buffers: 55
Statistics: 45
CPU / physics / render counters: 45
HUD: 30
Debug API / segment management: 25
Reserve: 25

Total: 250

Checkpoint 1: approximately 150 lines。
Checkpoint 2: approximately 225 lines。

以上分配為工程估算，並非要求實作者以壓縮程式碼方式符合各子額度。

若預估無法在 250 行內完成全部必要功能：

STOP。

向 Claude 回報阻擋原因。

不得：

- 壓縮程式碼以規避限制。
- 刪除必要測試。
- 降低量測準確性。
- 擅自提高行數上限。
- 擴大 allowlist。

26. Pre-Start Gates

正式開工前必須：

1. Claude 完成 G0 review。
2. Martin 正式確認預算治理方案。
3. Martin 正式批准 A2 spec。
4. Claude 登記 TASKS.md 與 DECISIONS.md。
5. Claude 建立正式 spec 文件。
6. 確認完整 latest main SHA。
7. 驗證 A1 game baseline 是否可沿用。
8. 確認 D-013 branch protection。
9. 確認單一 active code PR lock。
10. 確認測試、基準及結構性預算具備可重現性。

Suggested branch:

codex/T-018A2-performance-diagnostics

One task.
One implementer.
One code PR.

Codex 不得直接 push main 或自行 merge PR。

27. Deliverables

Codex：

- index.html 診斷功能。
- Node 確定性測試。
- Playwright 整合測試。
- Negative-control evidence。
- Mandatory regression outputs。
- Fixed baseline comparison。
- Diagnostic overhead evidence。
- PR description with actual results and limitations。

Claude：

- G0 review。
- 正式規格登記。
- 獨立回歸測試。
- CI wiring。
- PR review。
- Merge / release。
- CACHE update。
- 裝置測試指引。

Martin：

- 正式批准。
- 實機測試。
- 最終驗收。

28. Completion Criteria

A2 完成須符合：

- A2-G01 至 G18 通過。
- 所有必要負向控制觸發正確失敗。
- 所有 AGENTS mandatory checks 通過。
- 零結構性物理回歸。
- 零結構性渲染回歸。
- 正常模式無新增診斷取樣。
- Offline / save compatibility 保持。
- 不超過批准的行數及 allowlist。
- Claude 完成獨立審查。
- Martin 完成正式驗收。

實機效能基準須於進入 B 前取得，或由 Claude 明確提出證據缺口及處理方式，交 Martin 決定。

A2 完成不自動授權：

- T-018B。
- T-018C1 至 F2。
- WE-04 至 WE-09。
- 正式世界擴建。
- 修訂後的所有效能數值。
- WE-01 / WE-02 裁定修改。

---

Claude G0 Review Request

請 Claude 對 T-018A2 v1.0 DRAFT 進行獨立審查。

重點：

1. 確認 D-067 與最新 main 狀態。
2. 確認 A1 game baseline 可否沿用。
3. 確認方案 C 的預算治理分類符合系列規格。
4. 分開處理預算治理批准與 A2 實作批准。
5. 檢查 animate()、FPS cap early return、physicsWorld.step、renderer.render 的實際量測點。
6. 確認 frame interval 與 CPU attribution 正確對齊。
7. 確認 renderer.info 計數口徑。
8. 審查 16,384 筆樣本、1 MiB 容量及 60 秒視窗的可行性。
9. 審查 0.2 ms 診斷取樣成本目標及量測方法。
10. 確認 COLD / WARM 保存方式。
11. 確認背景暫停與真實多秒長幀可正確區分。
12. 確認 CACHE metadata 取得方式不需新增 runtime 網路依賴或修改 sw.js。
13. 確認 250 行 index.html 上限是否可行。
14. 確認兩份測試合計 500 行是否足夠。
15. 確認 A2-G01 至 G18 及負向控制具備可重現性。
16. 確認所有 11 種 preset 診斷支援不會擴大串流授權。
17. 確認實機測試矩陣及重複次數。
18. 確認系列 B4、B5、B6、N8、N10、N11 均受到遵守。
19. 審查串流效益修訂：Active collision bodies P95 降低至少 20%，Geometry / Texture 節省完整報告但不強制 20%。
20. 確認碰撞安全及 WE-01 / WE-02 土地限制不放寬。

Requested verdict:

APPROVE
APPROVE WITH CONDITIONS
REQUEST CHANGES

請區分：

- Blocking findings。
- Required corrections。
- Non-blocking recommendations。
- Decisions requiring Martin's approval。

ChatGPT 已重新查閱 repository 協作文件、系列規格、A1 findings 及 index.html 主迴圈相關位置。

ChatGPT 未修改 repository、未撰寫遊戲程式碼、未重新執行瀏覽器或裝置效能測試。

本規格新增的緩衝區容量、測試行數、診斷成本目標、測試時長及串流效益修訂均為待審設計提案。

正式批准前不得要求 Codex 開始實作。

---

HANDOFF ChatGPT -> Claude
Task: T-018A2 / WE-03 Budget Governance
Base commit: 9538c297fb7cb7dc702a6e5d7d1f21e502bbb251
Read: COLLAB.md, DECISIONS D-013/D-021/D-026/D-065/D-066/D-067, TASKS.md, AGENTS.md
Context: T-018A1 is accepted with documented measurement limitations.
Martin selected progressive hybrid budget governance as the design direction only.
T-018A2 extends diagnostics without changing production gameplay, frame pacing, quality or physics.
Deliverable: review the attached full proposal; register only after Martin explicitly approves.
SPEC: T-018A2 Device Frame-Time Diagnostics v1.0 DRAFT — complete text above.
