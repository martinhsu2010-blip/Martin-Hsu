T-018A2 — Device Frame-Time Diagnostics v1.1

1. Task Metadata

Project: VICE HORIZON VI
Repository: martinhsu2010-blip/Martin-Hsu
Task: T-018A2
Version: v1.1 DRAFT
Status: Revised following Claude G0 — Pending confirmation and Martin approval
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

Predecessor:
T-018A1 — Accepted under D-067.

Successor:
T-018B — NOT AUTHORIZED.

G0 Review:
specs/T-018A2-g0-review-v1.0.md

G0 PR:
#136 — OPEN, NOT MERGED.

G0 branch:
g0-a2

G0 head:
02c4f50e51b2c08f7968e10f5c38a267c0b0bd7b

G0 verdict:
APPROVE WITH CONDITIONS.

本版整合 Claude A2-C1..C13 條件。

Martin 已選擇方案 C 作為設計方向，但尚未正式批准預算治理、測試行數調整、串流效益修訂、實機矩陣或 A2 實作。

本文件不構成任務登記或開工授權。

2. Required Reading

- COLLAB.md v3.6
- AGENTS.md
- TASKS.md
- DECISIONS.md
- D-013、D-021、D-026、D-027
- D-065、D-066、D-067
- specs/WE-03-series-spec-v1.0.md
- specs/WE-03-draft-v1.0-chatgpt.md
- specs/WE-03-g0-review-v1.0.md
- specs/T-018A1-spec-v1.0.md
- specs/T-018A2-draft-v1.0-chatgpt.md
- specs/T-018A2-g0-review-v1.0.md
- specs/we03/a1_findings.md
- specs/we03/baseline_report.md
- specs/we03/baseline_metrics.json
- specs/we03/calibration_report.md
- specs/we03/calibration_data.json
- specs/we03/proposed_budgets.json

正式系列規格及已批准的 Claude G0 條件優先於未批准草案。

Claude G0 已確認 index.html、sw.js 及兩個 manifest 自 Engineering BASE 起位元組不變，亦與 Audit BASE 相同。

A1 baseline 可沿用，但正式登記時仍須重新確認完整 main SHA 及遊戲原始碼一致性。

3. Objective

建立可信、低成本、可重現的裝置效能診斷工具，供後續 WE-03 世界串流架構使用。

A2 必須：

1. 擴充既有 ?fps=1。
2. 量測真實已渲染幀間隔。
3. 提供 P50、P95、P99。
4. 保留所有有效前景長幀。
5. 提供正確對齊的 CPU attribution。
6. 提供整幀 renderer 計數。
7. 提供物理結構計數。
8. 自動區分 COLD、WARM_UP、MEASURE。
9. 提供唯讀診斷快照。
10. 建立尚未加入世界串流系統的實機基準。

A2 是診斷任務，不是效能最佳化任務。

4. Non-Goals

不得實作：

- Chunk Registry。
- Asset Registry。
- LOD Controller。
- Collision Streaming。
- Predictive Scheduler。
- Destination Readiness。
- HLOD runtime。
- Production shader prewarming。
- 物理引擎最佳化。
- FPS cap 或 frame pacing 修改。
- 自動畫質或動態解析度演算法修改。
- 建築、道路、地形或世界生成修改。
- 既有世界遷移。
- WE-04 至 WE-09。
- 正式世界擴建。
- WE-01 / WE-02 裁定修改。
- 新增 runtime dependencies。
- 新增 binary assets。
- 新增 localStorage keys。
- 修改 vh_save 或 vh_settings schema。

5. Activation and Isolation

沿用既有 ?fps=1 作為唯一診斷啟用入口。

建議採單一診斷物件及啟用判斷。

正常模式：

- 不建立診斷物件或樣本緩衝區。
- 不建立新增診斷 HUD。
- 不執行額外計時。
- 不執行額外物理或資源統計。
- 不新增背景計時器。
- 不修改 renderer.info.autoReset。
- 不執行診斷用 renderer.info.reset()。
- 僅允許必要的啟用狀態判斷。

診斷模式：

- 保留既有 ?fps=1 行為。
- 沿用既有停用自動畫質及動態解析度的行為。
- 不修改 FPS cap。
- 不修改物理步進。
- 不修改遊戲更新順序。
- 不新增場景 mesh、material 或 texture。

6. Frame Interval and CPU Alignment

Implements A2-C2.

6.1 Frame Interval Definition

interval_N = now_N - now_(N-1)

now_N 與 now_(N-1) 為連續已渲染幀的 rAF timestamps。

使用既有 animate(now) 的 now。

取樣位置必須在 animate() 尾端、既有 recordFps(now) 附近，並位於 FPS cap 及 pauseRender early return 之後。

未實際渲染的 rAF callback 不得計入。

不得使用 physics dt clamp 代替真實幀間隔。

第一個已渲染幀與新區段第一幀沒有有效 interval，不得補 0。

6.2 CPU Timing Points

每個已渲染幀 N 使用 performance.now() 量測五個時間點：

t0: 進入有效遊戲幀。
t1: physicsWorld.step() 前。
t2: physicsWorld.step() 後。
t3: rendering 前。
t4: rendering 後。

計算：

pre_N = t1 - t0

physics_N = t2 - t1

update_N = t3 - t2

render_N = t4 - t3

total_N = t4 - t0

pre 包含既有 updateTrafficPhysics() 與 refreshTreeColliders() 等 physics step 前的工作。

不得調整原有工作順序。

6.3 Previous-Frame Attribution

interval_N 必須對應 cpu_(N-1)。

不得將 cpu_N 歸因至 interval_N。

unattributed_N = interval_N - total_(N-1)

Unattributed 可能包含：

- VSync waiting。
- GPU backpressure。
- Browser scheduling。
- Compositor work。
- Browser throttling。
- 未包含在五個量測點內的工作。
- 診斷統計與 HUD 更新等額外成本。

不得將 unattributed 直接稱為 GPU execution time。

rAF timestamp 與 callback 實際進入時間可能存在約一個垂直同步週期的差異。

保留原始 signed residual，不得為使圖表相加一致而強制歸零或捏造數值。

若超出合理容差，應標示 attribution limitation。

6.4 Rendering Paths

必須同時支援：

- renderer.render(scene, camera)。
- composer.render()。

不得只量測直接 renderer.render() 路徑。

7. Full-Frame Rendering Counters

Implements A2-C1.

既有 renderer.info.autoReset 預設為 true。

Composer 多 pass 渲染可能導致幀尾計數僅反映最後一個 pass。

診斷模式必須：

1. 初始化時設定 renderer.info.autoReset = false。
2. 每個有效渲染幀開始渲染前呼叫 renderer.info.reset()。
3. 完成整個 renderer 或 composer 渲染後讀取計數。

計數口徑：

FULL_FRAME_ALL_PASSES。

包含：

- Main scene rendering。
- Shadow passes。
- Post-processing passes。

不得將最後一個 FXAA pass 的計數誤認為整幀計數。

正常模式不得修改 autoReset 或新增 reset 呼叫。

必要欄位：

- renderer.info.render.calls
- renderer.info.render.triangles
- renderer.info.programs.length
- renderer.info.memory.textures
- renderer.info.memory.geometries

若特定欄位不存在，標示 UNAVAILABLE。

renderer.info.memory 為資源數量，不是實測 VRAM。

新增負向控制：

保留 autoReset=true 的錯誤實作，必須使 G08 / G12 對應的整幀計數驗證失敗。

8. Physics Counters

Implements A2-C8.

必要欄位：

- bodies
- shapes
- contacts
- substeps
- physicsStepMs

Bodies：

physicsWorld 中的 body 數量。

Shapes：

所有 body 所含 shape 數量總和。

Bodies 與 shapes 每秒統計一次，不得逐幀掃描整個物理世界。

Contacts：

最後一次內部 physics step 的 physicsWorld.contacts.length。

此數值代表接觸方程式數量，不是不同接觸物件數量。

Substeps：

physicsWorld.stepnumber 在既有 physicsWorld.step() 呼叫前後的差值。

預期範圍：

0 至 3。

若 substeps = 0，contacts 可能是前一次內部 step 的資料，必須標示未更新，不得宣稱本幀產生新的 contacts。

不得：

- 修改 FIXED_TIME_STEP。
- 修改 dt。
- 修改 maxSubSteps。
- 增加額外 physics step。
- 修改物理狀態。

A1 physics timing self-control 四種 preset 均為 INCONCLUSIVE。

因此 A2 不建立新的 physics timing ratio 硬性通過條件。

9. Automatic Cold / Warm Segmentation

Implements A2-C3.

9.1 Automatic Phases

以有效前景已渲染時間自動分段。

COLD：

0–60 秒。

完成後凍結為不可覆蓋的冷啟動快照。

WARM_UP：

60–120 秒。

保留區段結果，但不列為正式暖機後效能結果。

MEASURE_1：

120–180 秒。

MEASURE_2：

180–240 秒。

MEASURE_3：

240–300 秒。

後續每 60 秒建立 MEASURE_4..n。

玩家不需要開啟開發者工具或手動呼叫 API 即可完成自動分段。

9.2 Boundary Handling

區段第一幀不得建立虛假的 interval。

跨越 60 秒邊界的有效長幀不得被截斷或刪除。

完整 interval 歸屬至其起始所在區段，完成記錄後才關閉區段。

下一區段以當前已渲染幀作為新的時間基準。

此邊界歸屬規則須有獨立測試，並由 Claude 確認。

9.3 Frozen Results

使用固定長度結果列表。

最多保存 8 段結果。

COLD 結果必須具有保護機制，不得被後續 MEASURE 結果覆蓋。

若 COLD 因中斷而不足 60 秒，保留原始證據並標示 INCOMPLETE。

後續區段達容量上限時，僅允許依明確規則移除最舊的非 COLD 結果。

須提供結果移除或容量狀態資訊，不得暗示所有歷史結果仍完整保存。

正式測試工具應在每段完成後擷取快照。

9.4 Interruption Recovery

區段中斷後：

- 保留原有區段。
- 不足 60 秒標示 INCOMPLETE。
- 保留 COLD 證據。
- 恢復後重新從 WARM_UP 開始。
- 完成 WARM_UP 後重新建立 MEASURE 序列。

9.5 Shader Prewarming

Shader prewarming 僅允許於獨立測試流程。

不得新增 production renderer.compile()。

不得覆蓋原始 COLD 證據。

10. Long-Frame Event Ring

Implements A2-C3.

建立固定 32 筆長幀事件環形緩衝。

COLD 使用獨立 32 筆事件環形緩衝。

觸發條件：

- interval > 100 ms。
- Shader program count 增加。

每筆事件至少包含：

- Timestamp。
- Frame sequence。
- Interval。
- Previous-frame pre CPU time。
- Previous-frame physics CPU time。
- Previous-frame update CPU time。
- Previous-frame render CPU time。
- Unattributed time。
- Program count delta。
- Texture count delta。
- Geometry count delta。
- 新增 shader program 名稱。
- Foreground stall flag。
- Segment identifier。

Program / texture / geometry delta 必須與實際產生資源變化的渲染幀對齊。

不得將本幀資源事件誤歸因至不相關的前一幀 interval。

新增 program 名稱若可取得，須保留，例如 Ch03_Body。

若名稱無法取得，標示 UNAVAILABLE。

資源數量變化僅代表相關性證據，不等於已證明 shader compilation 或 texture upload 耗時。

事件資料使用固定容量結構。

不得逐幀建立新的 event objects。

事件覆寫須可辨識。

最長幀證據須另行保護，不得因事件環形緩衝覆寫而遺失。

11. Segment Integrity Signature

Implements A2-C5.

每個有效渲染幀比較以下區段簽章：

- preset
- resScale
- fpsCap
- usePostFX
- innerWidth
- innerHeight
- Effective pixel ratio

任一欄位改變：

1. 關閉原區段。
2. 保留原區段資料。
3. 不足 60 秒標示 INCOMPLETE。
4. 不將新舊條件混入同一正式結果。
5. 從 WARM_UP 重新開始。

不得每幀配置新的 signature object 或 array。

11.1 Visibility

沿用 visibilitychange。

記錄：

- Interruption count。
- Total hidden duration。
- Segment interruption reason。

恢復前景後第一個已渲染幀不得計算跨背景期間的 interval。

11.2 Pause

STATE.pauseRender 視同區段中斷。

恢復後不得將暫停期間誤認為正常遊玩長幀。

11.3 Foreground Stall

沒有 visibility interruption 且 rAF interval ≥ 1000 ms：

foreground_stall = true。

此旗標僅用於標記。

不得因此排除、截斷或刪除任何有效前景長幀。

12. Percentiles and Buffer Capacity

Implements A2-C4、A2-C8.

原 G0 review 未提供獨立 C4 小節；本節及第 13 節整合其在 C7 / C8 中描述的量測與容量要求。

12.1 Required Statistics

- P50
- P95
- P99
- Frames > 50 ms
- Frames > 100 ms
- Frames > 50 ms ratio
- Frames > 100 ms ratio
- Longest frame
- Longest frame timestamp
- Valid sample count
- Measurement duration
- Existing average FPS
- Existing lowest 1-second FPS over 60 seconds

12.2 Percentile Definition

Nearest-rank percentile。

Rank = ceil(p × N)。

空樣本標示 UNAVAILABLE / NO_SAMPLES。

不得回報 0 ms 或 PASS。

12.3 Buffer

固定容量：

16,384 samples。

時間戳：

Float64。

其他數值欄位：

Float32，或符合精度需求的等效固定容量數值儲存。

總診斷緩衝區預算：

≤ 1 MiB。

容量須包含：

- Frame samples。
- CPU timing samples。
- Sorting scratch storage。
- Long-frame event rings。
- Frozen segment result storage。

若實作所需欄位使容量超過 1 MiB，停止並回報，不得靜默擴張。

60 秒、240 Hz 不限幀約需 14,400 筆樣本。

持續高於約 273 FPS 時，16,384 筆可能無法涵蓋完整 60 秒視窗。

12.4 Overflow Definition

Overflow：

仍屬有效 60 秒視窗的最舊樣本遭覆寫。

正常移除已超出視窗的樣本不算 overflow。

發生 overflow：

- 明確標示 INCOMPLETE。
- 百分位數不得宣稱代表完整視窗。
- 保留 overflow count。
- 不得靜默丟棄有效樣本。

12.5 Aggregation

每秒最多執行一次統計更新。

將有效樣本複製至預配置 scratch array 後原地排序。

不得每幀排序。

不得在統計過程反覆建立大型新陣列。

不得為符合 3,600 筆成本估算而截斷高更新率裝置的有效樣本。

12.6 Segment Accumulators

以下數值使用整個區段的累加器：

- Count。
- Frames > 50 ms。
- Frames > 100 ms。
- Max interval。
- Longest frame timestamp。

不受環形緩衝覆寫影響。

百分位數使用最近 60 秒有效視窗。

若整段累加器與百分位視窗涵蓋範圍不同，snapshot 必須明確標示。

13. Diagnostic Overhead

Implements A2-C7.

原 v1.0 的 0.2 ms P95 取樣成本改為：

SOFT_TARGET：

Average sampling CPU cost ≤ 0.2 ms per rendered frame。

量測方法：

- 在頁面內進行至少 10,000 次批次呼叫。
- 使用具代表性的預配置測試資料。
- 以批次總經過時間除以呼叫次數。
- 記錄 performance.now() 計時器解析度估計。
- 不得污染正式 COLD / WARM / MEASURE 資料。
- 不得將批次測試加入正常遊戲啟動流程。

1 Hz 統計更新成本另行量測及報告。

排序成本須記錄實際樣本數。

60 FPS 下約 3,600 筆為一般成本參考，不是所有裝置的樣本上限。

超過 0.2 ms：

- 報告原因。
- 提出改善建議。
- 不作 CI 硬性失敗。

所有由診斷工具造成的有效長幀均須保留。

Hot-loop constraints：

- 每幀新增物件配置 = 0。
- 每幀 console output = 0。
- 新增背景計時器 = 0。

14. CACHE and Refresh Rate Metadata

Implements A2-C6.

14.1 CACHE

診斷初始化時非同步呼叫一次 caches.keys()。

篩選符合 ^vh- 的 cache names。

若只有一個候選名稱且頁面已受 service worker 控制：

記錄該名稱，並標示來源為 CacheStorage enumeration。

若：

- caches 不存在。
- 呼叫失敗。
- 沒有符合名稱。
- 存在多個符合名稱。
- 頁面尚未受 service worker 控制。

CACHE = UNAVAILABLE。

同時保留可取得的候選清單及原因。

不得：

- Fetch sw.js。
- 硬編碼 CACHE。
- 修改 sw.js。
- 新增 runtime 網路依賴。

CacheStorage 名稱為版本辨識證據，不是對目前所有已載入頁面資源版本的獨立完整證明。

首次造訪尚未被 service worker 控制時，正式報告應於重新載入後確認。

14.2 Refresh Rate

瀏覽器沒有標準 API 可直接取得實際顯示更新率。

必要欄位允許：

UNAVAILABLE。

實機報告依 B4 手動記錄裝置更新率。

選做：

以最初 120 個原始 rAF intervals 的中位數估算 refreshRateEstimate。

若實作，必須標示 ESTIMATE。

不得將估計值稱為實測面板更新率。

此選做功能不得造成超過 250 行限制。

15. Diagnostic HUD and Read-Only API

Implements A2-C10.

15.1 HUD

擴充既有 FPS HUD。

最多 4 行等寬小字。

採英文技術縮寫。

不新增 tr() keys。

必須容納：

- Phase / segment number。
- Average FPS。
- Lowest 1-second FPS。
- P50 / P95 / P99。
- Frames > 50 / 100 ms。
- Longest frame。
- CPU 三項 P95：physics、game update、render submission。
- Bodies / shapes / contacts。
- Draw calls / triangles / programs。
- Sample count。
- Segment status。
- Preset。
- resScale。
- fpsCap。
- CACHE。
- Refresh rate availability / estimate。
- Release identification。

Game update CPU P95 使用明確定義的 pre + update，不包含 physics 與 render。

HUD 不得使用會誤導使用者的簡寫或截斷必要數值。

若四行內無法完整顯示 B4 所需資訊，須於 G0 確認可行的四行版面或分頁顯示方法，不得擅自增加 HUD 行數。

不得遮蔽主要駕駛畫面或觸控控制。

15.2 Debug API

window.__VH.diag.snapshot()

唯讀快照。

Schema：

we03-diagnostics-v1。

必要欄位：

- schema
- phase
- segmentId
- segmentStatus
- preset
- resScale
- fpsCap
- usePostFX
- viewportWidth
- viewportHeight
- effectivePixelRatio
- refreshRate
- refreshRateEstimate
- cache
- cacheCandidates
- release
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
- preCpuMs
- gameUpdateMs
- renderSubmissionMs
- cpuTotalMs
- unattributedMs
- bodies
- shapes
- contacts
- substeps
- drawCalls
- triangles
- programs
- textures
- geometries
- gpuTime
- gcTime
- overflow
- interruptionCount
- hiddenDurationMs
- foregroundStallCount
- frozenSegments
- coldSnapshot
- longFrameEvents
- coldLongFrameEvents

須明確標示 CPU 指標為單幀值或 P95 彙總值。

Snapshot 不得暴露可修改內部診斷狀態的直接引用。

不得提供修改遊戲物理、畫質或世界狀態的額外能力。

GPU timing / GC timing：

無可靠量測能力時標示 UNAVAILABLE。

不要求新增 GPU timer query 或 CDP profiler 至 runtime。

16. Preset Coverage

全部 11 種既有 preset 均須支援診斷：

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

尚未批准串流映射的 7 種 preset 不得自動套用最接近的串流 preset。

17. Progressive Hybrid Budget Governance

Implements A2-C13.

Status：

PROPOSED — REQUIRES MARTIN APPROVAL。

17.1 HARD_GATE

已批准且具有可靠驗證方法的硬性限制。

候選分類：

- A2 bodies delta = 0。
- A2 shapes delta = 0。
- A2 full-frame draw calls delta = 0。
- A2 full-frame triangles delta = 0。
- A2 added scene meshes = 0。
- A2 added materials = 0。
- A2 added textures = 0。
- A2 added runtime dependencies = 0。
- A2 added localStorage keys = 0。
- A2 hot-loop per-frame object allocations = 0。
- index.html added + changed lines ≤ 250。
- Offline compatibility。
- Save compatibility。
- Collision safety。
- No blank visual replacement。
- B4 device average FPS ≥ fpsCap × 0.97。

B4、碰撞安全及系列既有約束仍依 D-065 生效，不因本治理提案而暫停。

Contacts delta = 0 僅在 BASE-to-BASE fixture 已證明完全可重現時成立。

17.2 SOFT_TARGET

- Average diagnostic sampling CPU cost ≤ 0.2 ms。
- Frame-time P95 ≤ 40 ms。
- Frame-time P99 ≤ 66.7 ms。
- 原系列最低 1 秒 FPS 初始值。
- 原系列 > 100 ms ratio 初始值。
- 新增 triangles P95 預算。

暫定新增 triangles P95：

PHONE_LOW: 120,000
PHONE_MED: 160,000
TABLET_MED: 200,000
DESKTOP_HIGH: 350,000

PHONE_MED 為插值。

以上數值尚未正式批准為硬性驗收門檻。

17.3 PENDING_EVIDENCE

- Streaming draw-call budgets。
- Resource capacity budgets。
- Streaming CPU budgets。
- LOD distances。
- Physics timing ratios。
- Active collision radius。
- Geometry / texture residency。

注意：

A2 的零 draw-call 回歸是結構性限制。

後續串流新增 draw-call 預算仍為 PENDING_EVIDENCE。

兩者不得混淆。

17.4 Promotion Rules

PENDING_EVIDENCE → SOFT_TARGET → HARD_GATE。

只能由 Martin 依 MEASURED_DEVICE 證據明確批准。

不得自動升級。

SOFT_TARGET 超標須提供原因與改善建議。

同一目標連續兩個子任務超標，須提交 Martin 判斷。

任何已生效 HARD_GATE 的放寬亦須經正式決策，不得由實作者自行調整。

17.5 A1 Evidence Limitations

A1 analytic replay P95 including shadow：

PHONE_LOW: 133,000
PHONE_MED: 189,000
TABLET_MED: 193,000
DESKTOP_HIGH: 246,700

以上均為 ANALYTIC_ESTIMATE。

不得直接宣稱 PHONE_LOW 或 PHONE_MED 已正式驗收失敗。

Physics timing self-control：

四種 preset 均為 INCONCLUSIVE。

不得將 headless timing ratio 自動升級為 HARD_GATE。

18. Proposed Streaming Benefit Revision

Status：

PROPOSED — REQUIRES SEPARATE MARTIN APPROVAL。

本節不屬於 A2 實作範圍。

原 v1.0 §16 修訂，納入 Claude G0 §5 條件。

A1 顯示共用 geometry / texture 的常駐節省可能接近零。

57 棟住宅、每棟一個 body、假設 217 m 碰撞半徑：

- Peak-grid body saving: 56.1%。
- Replay P95 body saving: 66.7%。
- Shared geometry / texture saving: approximately 0%。

以上為 ANALYTIC_ESTIMATE。

217 m 不是正式批准半徑。

18.1 Proposed Benefit Gate

Active collision bodies P95 相較全常駐對照組降低至少 20%。

比較必須使用：

- 相同測試物件集合。
- 相同碰撞半徑政策及安全要求。
- 相同路徑。
- 相同測試時間。
- 相同畫質。
- 相同其他可控制條件。

全常駐對照組不因距離卸載碰撞體；串流組依同一安全政策管理活動碰撞體。

不得為改善比較結果而更換測試物件集合或縮小安全範圍。

18.2 Safety Priority

碰撞安全須同時驗證：

- Peak active bodies。
- Peak active shapes。
- P95 active bodies。
- 系列最高速度上限。
- T_ready。
- 預載安全距離。
- 無必要碰撞體缺失。

安全優先於 20% 效益目標。

18.3 Resource Benefit

Geometry / texture residency 及節省比例完整報告。

不再提議強制降低 20%。

此變更需 Martin 明確接受。

18.4 Interpretation

Body 數量下降不等於 physics CPU time 下降。

A2 實機報告須同時記錄 physicsStepMs 與 bodies。

進入 B 前，Claude 應整理證據及剩餘不確定性，供 Martin 判斷架構投入是否合理。

A2 尚未實作串流，因此不能以 A2 本身證明串流已達成 20% 效益。

18.5 Ownership

Collision radius：D / E1。

Resource residency：C1。

LOD triangle validation：C4 / F2。

最終串流效益驗證：後續相關子任務及 F2。

GLOBAL_STRESS_ONLY 不得作為合法土地或 B3 密度證據。

WE-01 / WE-02 限制不放寬。

19. File Allowlist and Line Ceilings

允許修改：

1. index.html
2. tools/test/we03_a2_diagnostics_check.mjs
3. tools/test/we03_a2_browser_check.py

index.html：

HARD CEILING ≤ 250 added + changed lines。

兩份測試檔案：

原 v1.0 建議上限 500 行。

Claude G0 建議修訂至合計 700 行。

700 行仍須 Martin 批准。

不得將其視為已批准額度。

診斷核心使用：

// === WE03A2-DIAG BEGIN ===

// === WE03A2-DIAG END ===

供既有 section() 測試方法擷取。

不得新增 runtime files。

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

Claude 負責正式登記、CI wiring、merge 及 release CACHE update。

20. Implementation Feasibility and STOP Rules

Implements A2-C9.

Claude G0 估計：

230–265 lines。

因此 250 行限制存在實際超額風險。

精簡 HUD、不新增 tr() keys、固定容量資料結構為必要範圍控制方式。

約 150 行時：

Codex 必須回報完整實作行數預估。

若預估超過 250 行：

STOP。

約 225 行時：

再次確認剩餘功能與行數。

不得：

- 壓縮程式碼規避行數限制。
- 刪除必要量測欄位。
- 移除長幀證據。
- 降低統計正確性。
- 刪除必要測試。
- 自行提高上限。
- 擴大 allowlist。

若確實不可行，Claude 與 ChatGPT 重新審查拆分方案，再交 Martin 決定。

21. Automated Acceptance Gates

A2-G01 — Default OFF

正常模式不建立診斷物件、緩衝區或 HUD，不執行額外診斷取樣，不改 autoReset。

A2-G02 — Diagnostic ON

?fps=1 正確啟用診斷並保留原有畫質控制行為。

A2-G03 — Percentiles

P50 / P95 / P99 與獨立 nearest-rank 計算一致。

A2-G04 — Long Frames

所有有效前景長幀均保留，包括多秒長幀。

A2-G05 — Threshold Boundaries

正確區分 > 50 ms、> 100 ms 與等於門檻。

A2-G06 — FPS Cap

Skipped rAF callbacks 不得計入已渲染幀。

A2-G07 — Cold / Warm

自動 COLD、WARM_UP、MEASURE 分段正確。

COLD 不被覆蓋。

跨區段長幀不得遺失。

A2-G08 — Physics and Resource Counters

Bodies、shapes、contacts、substeps 及 renderer counters 與獨立計數一致。

Composer 所有 pass 均納入。

A2-G09 — CPU Attribution

interval_N 對應 cpu_(N-1)。

不得錯配幀、重複計算或捏造 unattributed。

A2-G10 — Unsupported Metrics

GPU / GC 等不支援指標正確標示 UNAVAILABLE。

A2-G11 — Memory

固定容量、總緩衝區 ≤ 1 MiB、每幀新增物件配置 = 0。

A2-G12 — Rendering Regression

獨立外部 harness 驗證：

Full-frame draw calls delta = 0。

Full-frame triangles delta = 0。

A2-G13 — Physics Regression

Bodies delta = 0。

Shapes delta = 0。

Contacts 僅於 BASE-to-BASE 確定性驗證成立後要求 delta = 0。

A2-G14 — Existing FPS HUD

原有平均 FPS 與最近 60 秒最低 1 秒 FPS 功能保留。

新增 HUD 最多 4 行。

A2-G15 — Metadata

Preset、resScale、fpsCap、viewport、pixel ratio、CACHE、release 等資訊正確或明確標示 UNAVAILABLE。

A2-G16 — Offline / Save

既有離線功能及舊存檔相容性保持。

A2-G17 — Preset Coverage

全部 11 種 preset 可啟用診斷。

靜態掃描確認沒有新增串流或其他禁止功能。

A2-G18 — Segment Integrity

Overflow、visibility、pause、設定變更、視窗尺寸及 pixel ratio 變更均正確處理。

22. Independent Test Method

Implements A2-C11.

22.1 Node Tests

使用 collision_harness.mjs 既有 section() 方法擷取診斷核心。

Expected values 必須由測試內獨立計算。

不得呼叫 production helper 產生預期結果。

固定樣本：

[16,20,30,33,33,40,50,51,100,120]

Expected：

N = 10
P50 = 33 ms
P95 = 120 ms
P99 = 120 ms
Frames > 50 ms = 3
Frames > 100 ms = 1
Over50 ratio = 30%
Over100 ratio = 10%
Longest frame = 120 ms

其他必要案例：

- Empty samples。
- Single sample。
- Identical samples。
- Unsorted samples。
- Exactly 50 ms。
- Exactly 100 ms。
- Multi-second foreground frame。
- Ring-buffer wraparound。
- Valid-window overflow。
- FPS cap skipped callback。
- COLD / WARM_UP / MEASURE transition。
- Visibility interruption。
- Pause / resume。
- Preset / fpsCap change。
- Viewport / pixel ratio change。
- Previous-frame CPU attribution。
- Long-frame event ring overwrite。
- COLD snapshot protection。
- Substeps = 0。
- Segment boundary crossing。

22.2 External Rendering Comparison

使用 A1 風格外部 harness。

測試四種組合：

1. BASE — Diagnostics OFF。
2. BASE — Diagnostics ON。
3. A2 — Diagnostics OFF。
4. A2 — Diagnostics ON。

外部 harness 獨立設定 autoReset=false 並執行每幀 reset。

不得依賴 A2 自身 renderer counter 結果作為唯一驗證來源。

相同場景、相機、畫質、時間及可控制條件下比較。

Full-frame draw calls delta = 0。

Full-frame triangles delta = 0。

另須在未被外部 harness 改寫 autoReset 的獨立測試中驗證 A2 正常模式不修改 autoReset。

22.3 Physics Comparison

使用相同可重現 fixture。

先執行 BASE-to-BASE 重複測試兩次。

若 contacts 完全一致：

允許建立 contacts delta = 0 硬性條件。

若 contacts 不一致：

Contacts comparison = INCONCLUSIVE。

不得修改 fixture 或遊戲物理以強迫結果一致。

Bodies、shapes 的結構性零回歸仍須驗證。

22.4 Static Scope Scan

檢查 diff，不得新增：

- Chunk / registry / LOD controller 實作。
- renderer.compile() production calls。
- New localStorage keys。
- New fetch calls。
- CDN dependencies。
- Physics step 修改。
- FPS cap 修改。
- Auto-quality algorithm 修改。
- Dynamic-resolution algorithm 修改。

不得將單純診斷標籤或測試中的禁止項目字串誤判為新增 runtime 功能。

23. Negative Controls

至少驗證以下故意錯誤會觸發對應失敗：

NC01 — Incorrect percentile calculation。

NC02 — Threshold > changed to >=。

NC03 — Long frames removed。

NC04 — Long frames clamped。

NC05 — Skipped rAF callbacks counted as rendered frames。

NC06 — Cold and warm samples mixed。

NC07 — Diagnostics enabled by default。

NC08 — Incorrect physics counters。

NC09 — Incorrect renderer counters。

NC10 — Unsupported GPU timing reported as zero。

NC11 — Overflow hidden。

NC12 — CPU attribution assigned to the wrong frame。

NC13 — autoReset remains true in diagnostic rendering。

NC14 — Viewport size change does not close the segment。

所有負向控制必須有可辨識 failing assertion。

不得將 syntax error、環境錯誤或測試無法啟動當作成功負向控制。

測試工具必須能證明失敗原因對應被注入的錯誤。

24. Mandatory Regression Checks

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

PWA offline：

python3 tools/test/pwatest.py

Claude 登記時須確認 pwatest.py 的實際路徑及必要參數。

Playwright：

沿用既有 1.55.0 測試環境。

24.1 Save Compatibility Check

目前沒有獨立 save compatibility 測試檔。

因此納入 we03_a2_browser_check.py。

使用由 BASE 產生或經 BASE 驗證的既有 vh_save fixture。

至少驗證：

- Existing cash preserved。
- Owned vehicles preserved。
- Jumps data preserved。
- Deliveries data preserved。
- Upgrade data preserved。
- Existing save loads without errors。
- Diagnostics OFF / ON 不新增儲存欄位。
- Diagnostics OFF / ON 不新增 localStorage keys。
- Reload 後既有資料仍可讀取。

測試使用隔離 browser context，不接觸使用者真實存檔。

比較須排除或控制既有正常遊戲自動更新造成的資料變化。

不得為通過測試而停用正式存檔行為。

Claude 須獨立重跑測試並確認 CI wiring。

Timing measurements 不直接作為 CI 硬性通過閘門。

未執行測試須明確報告。

25. Device Measurement Matrix

Implements A2-C12.

Status：

PROPOSED — REQUIRES MARTIN APPROVAL。

25.1 Core Matrix

Device / Preset：

1. Galaxy S26 Ultra — PHONE_LOW。
2. Galaxy S26 Ultra — PHONE_MED。
3. Galaxy Tab S11 — TABLET_MED。

每組執行：

A. CBD — 12:00。
B. CBD — 23:00。
C. Suburbs — 使用 A1 固定測試條件。

Total：

3 preset/device combinations × 3 scenes = 9 scenarios。

25.2 Optional Matrix

- TABLET_HIGH。
- Midtown。
- Mountain。
- Highway。
- Fast Travel。

選做場景不得取代核心矩陣。

25.3 Protocol

使用 ?fps=1。

手動固定畫質。

使用現有遊戲控制項到達測試位置及時間。

不得為實機測試新增正式 teleport、time-control 或世界修改功能。

Claude 正式登記時須核對：

- A1 固定場景座標。
- 既有遊戲操作能否到達。
- 既有遊戲操作能否設定所需時間。
- 裝置畫質切換方式。
- 如何擷取完整四行 HUD。
- 如何確認每個 MEASURE 區段完成。

若某個固定條件無法透過現有控制項達成：

報告 blocker。

不得自行替換測試場景或擴大 A2 功能範圍。

25.4 Timing

每個場景目標取得：

- WARM_UP 60 秒。
- MEASURE_1 60 秒。
- MEASURE_2 60 秒。
- MEASURE_3 60 秒。

每個獨立測試 session 的首次場景另保存 COLD 60 秒。

場景切換後須建立可辨識的新量測區段，不能將前一場景混入下一場景結果。

Claude 須確認可透過現有控制項或重新載入方式建立區段，無須新增遊戲控制功能。

Estimated total：

45–60 分鐘，包含場景切換及操作時間。

分兩次進行，避免持續過熱影響比較。

若裝置出現過熱或明顯不穩定，應停止該次測試並記錄條件。

25.5 Required Metadata

- Device model。
- Browser / version。
- Preset。
- resScale。
- fpsCap。
- Display refresh rate。
- Game release。
- CACHE。
- Battery level / power state。
- Thermal conditions。
- Scene。
- Time of day。
- Phase / segment。
- Sample count。
- Measurement duration。
- Timer resolution estimate。

26. Device Performance Targets

沿用系列 B4：

Average FPS ≥ fpsCap × 0.97。

30 FPS cap：

Average FPS ≥ 29.1。

原始 30 FPS 裝置體驗目標不變。

候選 SOFT_TARGET：

P95 ≤ 40 ms。

P99 ≤ 66.7 ms。

最低 1 秒 FPS 與 > 100 ms ratio 沿用系列草案初始值，待實機基準及 Martin 確認。

不得將 A2 診斷工具驗收與整體 WE-03 效能驗收混為一談。

A2 測得低 FPS 不代表診斷工具本身錯誤。

但不得隱藏效能問題或宣稱整體 WE-03 已通過。

正式串流裝置效能驗收由 F2 負責。

27. Evidence Classification

所有報告須正確使用：

- MEASURED_DEVICE
- MEASURED_HEADLESS
- ANALYTIC_ESTIMATE
- ESTIMATE
- PROPOSED_LIMIT
- PENDING_DEVICE
- INCOMPLETE
- INCONCLUSIVE
- UNAVAILABLE

不得：

- 將 headless FPS 稱為 device FPS。
- 將 renderer memory counters 稱為 VRAM。
- 將 body saving 稱為已證明的 physics time saving。
- 將 program count delta 稱為 shader compilation duration。
- 將 CPU render submission 稱為 GPU execution time。
- 將未批准預算稱為正式 HARD_GATE。

28. Pre-Start Gates

正式開工前：

1. Claude 確認 v1.1 已整合 G0 條件。
2. Martin 正式確認預算治理分類及升降級規則。
3. Martin 決定測試行數上限。
4. Martin 決定串流效益修訂。
5. Martin 決定實機矩陣。
6. Martin 正式批准 A2 規格。
7. Claude 正式登記 TASKS.md。
8. Claude 正式登記 DECISIONS.md。
9. Claude 建立正式 spec entry point。
10. 確認完整 latest main SHA。
11. 確認 A1 game baseline 一致性。
12. 確認 D-013 branch protection。
13. 確認單一 active code PR lock。
14. 確認測試方法、路徑及行數限制。
15. 確認實機操作單可執行。

Suggested branch：

codex/T-018A2-performance-diagnostics

One task。
One implementer。
One code PR。

Codex 不得直接 push main 或自行 merge。

29. Deliverables

Codex：

- index.html diagnostics。
- Node deterministic tests。
- Playwright integration tests。
- Negative-control evidence。
- Mandatory regression outputs。
- Independent BASE comparison evidence。
- Diagnostic overhead evidence。
- PR report with actual results and limitations。

Claude：

- G0 confirmation。
- Formal registration。
- Independent verification。
- CI wiring。
- PR review。
- Merge / release。
- CACHE update。
- Device operation guide。
- Device evidence summary。

Martin：

- Separate governance decisions。
- Final A2 approval。
- Device testing。
- Final acceptance。

30. Completion Criteria

A2 完成須符合：

- A2-G01..G18 通過。
- NC01..NC14 觸發正確失敗。
- 所有 AGENTS mandatory checks 通過。
- 零結構性 physics regression。
- 零結構性 rendering regression。
- 正常模式零新增診斷取樣。
- COLD evidence 正確保護。
- Segment integrity 正確。
- Offline / save compatibility 保持。
- 不超過批准的 line ceilings。
- 不超出 file allowlist。
- Claude 完成獨立驗證。
- Martin 完成正式驗收。

實機基準應於 B 前取得。

若存在實機證據缺口，Claude 須明確報告並由 Martin 決定後續處理，不得自動跳過。

A2 完成不自動授權：

- T-018B。
- T-018C1..F2。
- WE-04..WE-09。
- 正式世界擴建。
- 未批准的預算修訂。
- WE-01 / WE-02 裁定修改。

31. G0 Condition Traceability

A2-C1：

§7、§21、§22、§23。
Full-frame rendering counters、autoReset、independent comparison。

A2-C2：

§6、§10、§21、§22、§23。
Previous-frame CPU attribution。

A2-C3：

§9、§10、§12。
Automatic segmentation、frozen results、long-frame event rings。

A2-C4：

G0 無獨立小節。
相關容量及量測要求整合於 §12、§13。

A2-C5：

§11、§21、§22、§23。
Segment signature、visibility、pause、foreground stall。

A2-C6：

§14、§15。
CACHE enumeration、refresh rate availability。

A2-C7：

§13。
Average sampling cost、10,000-call batch、SOFT_TARGET。

A2-C8：

§8、§12。
Percentile、overflow、contacts、substeps。

A2-C9：

§19、§20。
250-line ceiling、150-line checkpoint、STOP rule。

A2-C10：

§15。
Four-line HUD、English abbreviations、read-only API。

A2-C11：

§21–24。
Independent tests、external harness、negative controls、offline/save checks。

A2-C12：

§25、§26。
Reduced 3×3 device matrix、existing controls、split sessions。

A2-C13：

§17。
HARD_GATE / SOFT_TARGET / PENDING_EVIDENCE、promotion rules。

Claude G0 §5：

§18。
Streaming benefit revision with safety conditions。

Claude G0 §6：

§28、§32。
Separate Martin approvals。

32. Decisions Reserved for Martin

以下五項尚未批准：

Decision 1 — Budget Governance

是否採納 §17 的分類表及升降級規則。

Decision 2 — Test Line Ceiling

是否將兩份測試檔案合計上限由原提案 500 行提高至 700 行。

index.html 250 行上限不變。

Decision 3 — Streaming Benefit Revision

是否採納 §18 的 20% active collision bodies P95 gate。

Geometry / texture residency 改為完整報告，不強制 20%。

碰撞安全優先。

Decision 4 — Device Matrix

是否接受核心 3×3、約 45–60 分鐘、分兩次執行的實機矩陣。

Decision 5 — Final A2 Approval

是否正式批准本 v1.1 規格，由 Codex 實作。

以上決定應在 Claude 審查流程中分別確認。

不得將其中任一項批准解讀為其餘項目自動批准。

---

Claude G0 Follow-Up Request

ChatGPT 已讀取 PR #136 的完整 G0 review，並完成 T-018A2 v1.1 修正版。

請 Claude 確認：

1. A2-C1..C13 是否全部正確整合。
2. Full-frame renderer counters 是否與 A1 一致。
3. CPU interval alignment 是否正確。
4. 自動 COLD / WARM_UP / MEASURE 分段是否可行。
5. 跨 60 秒邊界的長幀歸屬是否保留全部證據。
6. 32 筆事件環形緩衝及 8 段結果保存是否符合 1 MiB 預算。
7. Resource event 與前一幀 CPU attribution 是否正確對齊。
8. 四行 HUD 是否可在手機橫向完整顯示 B4 所需資訊。
9. 250 行 index.html 上限是否仍可行。
10. 700 行測試上限是否足夠。
11. pwatest.py 實際路徑與參數是否正確。
12. Save compatibility fixture 是否可重現。
13. 實機核心矩陣是否能透過現有遊戲控制項完成。
14. 五項 Martin 決策是否保持分離。
15. 是否存在仍需修改的 blocking findings。

若無新增阻擋項，請提交五項待批准決策給 Martin。

不得在批准前：

- 合併 PR #136。
- 登記 T-018A2。
- 建立已批准的預算決策。
- 要求 Codex 開工。
- 授權 T-018B 或後續任務。

ChatGPT 本次僅執行唯讀 repository 查閱及規格修訂。

未修改 GitHub repository。

未執行遊戲、瀏覽器或實機測試。

新增的跨區段長幀歸屬、signed residual 保存、COLD 結果保護及存檔 fixture 細節為 v1.1 的設計明確化，須由 Claude 確認。

---

HANDOFF ChatGPT -> Claude
Task: T-018A2 Spec v1.1 / G0 Follow-Up
Base commit: 9538c297fb7cb7dc702a6e5d7d1f21e502bbb251
Read: COLLAB.md, DECISIONS D-013/D-021/D-026/D-065/D-066/D-067, TASKS.md, AGENTS.md
Context: T-018A1 is accepted under D-067 with documented measurement limitations.
Claude G0 PR #136 remains open and unmerged; v1.1 incorporates A2-C1..C13 and the conditional benefit revision.
Five separate Martin decisions remain pending; no implementation or later subtask is authorized.
Deliverable: confirm the revised specification, resolve any remaining blockers, and register only after Martin explicitly approves.
SPEC: T-018A2 Device Frame-Time Diagnostics v1.1 DRAFT — complete text above.