# T-018A2 G0 審查（Claude，獨立）v1.0

審查對象：`specs/T-018A2-draft-v1.0-chatgpt.md`（Device Frame-Time Diagnostics v1.0 DRAFT，原文照存）。
審查基準：main `9538c297fb7cb7dc702a6e5d7d1f21e502bbb251`（D-067 之後，只動文件）。
本審查不登記任務、不批准預算、不授權實作；預算治理與 A2 實作分開審、分開交 Martin 批准。

## 0. 結論

**APPROVE WITH CONDITIONS（有條件通過）。** 方向、範圍、檔案白名單、250 行上限、負向控制清單大致可行。但草案有 4 個「照字面實作會量錯」的缺口（A2-C1..C4），必須寫進正式規格後才能交 Martin 批准。

| 項目 | 結果 |
|---|---|
| 1 D-067、main、A1 基準 | 通過。`index.html`、`sw.js`、兩個 manifest 自 `e8d5250` 起位元組不變，也與 Audit BASE 相同；CACHE 仍為 `vh-2026-11-27-02`。A1 基準可沿用。 |
| 2 方案 C 分類 | 有條件（A2-C13）：草案只定義三類，沒有把現有預算逐項歸類。 |
| 3 治理與實作分開 | 通過（見第 6 節兩段式批准）。 |
| 4 量測點 | 有條件（A2-C1、C2、C5）。 |
| 5 FPS cap 不計入未渲染 rAF | 通過，附條件：取樣點必須在 `animate()` 尾端（沿用 `recordFps(now)` 位置，在 FPS cap 與 `pauseRender` 的 early return 之後）。 |
| 6 CPU 與長幀對齊 | **阻擋**（A2-C2）。 |
| 7 16,384／1 MiB／60 秒／0.2 ms | 容量可行；0.2 ms P95 無法照字面量測（A2-C4、C7）。 |
| 8 冷暖、overflow、背景、設定切換 | **阻擋**（A2-C3、C5）。 |
| 9 G01–G18 與負向控制 | 有條件（A2-C10、C11）。 |
| 10 零回歸、正常模式零取樣 | 有條件（A2-C1、C11）。 |
| 11 250 行 | 有條件可行（A2-C9）。 |
| 12 11 個 preset 不擴大串流 | 通過，附靜態掃描條件（A2-C11）。 |
| 13 實機 B4/B5/B6/N8/N10/N11 | 有條件（A2-C12）。 |
| 14 CACHE metadata | 可行，作法見 A2-C6。 |
| 15 串流效益修訂 | 有條件，且需 Martin 決定（第 6 節）。 |

## 1. 我實際檢查了什麼（`index.html`，行號為 main 9538c29）

- `createFpsReadout()` 12432–12460：只做 1 秒分箱的平均與最低，`visibilitychange` 時清空；`recordFps(now)` 在 `animate()` 最後一行（12552），也就是 FPS cap 與 `pauseRender` early return（12466–12472）之後、渲染之後，所以只會看到真的渲染過的幀。這個位置是對的，A2 應沿用。
- `?fps=1` 時 `recordFps` 為真，自動降畫質（12479）與動態解析度（12493）都被關掉，符合 B4。
- `physicsWorld.step(FIXED_TIME_STEP, dt, 3)` 在 12517；其前還有 `updateTrafficPhysics()` 與 `refreshTreeColliders(dt)`，其後才是玩家、車輛、世界更新；渲染在 12544–12550，`usePostFX && composer` 時走 `composer.render()`，否則 `renderer.render()`。
- 全檔沒有 `renderer.info.autoReset`，也沒有任何地方讀 `renderer.info.render`，所以預設 `autoReset = true`。
- `sw.js` 的 `activate` 會刪除所有名稱不等於 `CACHE` 的快取（114–116）。
- 解析度改變走 `applyResolution()`（2466），`resize` 事件在 10863；`STATE.fpsCap` 由設定改變（10832）；品質由 `applyQualitySetting()` 改變。
- `i18n_check` 只檢查未翻譯的可見 CJK 文字，英文技術標籤不會被擋；現有 HUD 用 `tr()`，新增每個標籤要在每個語言表各加一行。
- `AGENTS.md` 列的必跑檢查檔案都存在；沒有單獨名為「save compatibility」的檢查檔。

## 2. 阻擋項（必須先寫進規格）

**A2-C1 渲染器計數口徑（阻擋）。** 因為 `autoReset` 預設為真，`composer.render()` 內每個 pass 都會呼叫 `renderer.render()` 並重設計數，幀尾讀到的 `calls` 與 `triangles` 只剩最後一個 pass（例如 FXAA），遠小於整幀。草案只說「明確說明是否含所有 pass」，不夠。
→ 診斷模式在初始化時設 `renderer.info.autoReset = false`，每個渲染幀在渲染前呼叫 `renderer.info.reset()`，渲染後讀取，口徑為「整幀所有 pass（含陰影與後處理）」，與 A1 的 headless 表同一口徑。正常模式不得碰 `autoReset`。加負向控制：保留預設 `autoReset` 時 G08／G12 必須變紅。`programs`、`textures`、`geometries` 用 `renderer.info.programs.length` 與 `renderer.info.memory`，不稱為 VRAM。

**A2-C2 幀間隔與 CPU 歸因的對齊（阻擋）。** 草案要求「正確對齊」但沒有定義。規格必須明定：
- `interval_N = now_N − now_{N−1}`，兩者是**連續已渲染幀**的 rAF 時間戳（沿用 `now`，與 FPS cap 邏輯同一時鐘）。
- 每個已渲染幀 N 用 `performance.now()` 量五點：進入、physics step 前、step 後、渲染前、渲染後，得到 `pre`（含 `updateTrafficPhysics`、`refreshTreeColliders`）、`physics`、`update`、`render`、`total`。
- 長幀 `interval_N` 對應的是**前一幀**的工作：`cpu_{N−1}`；`unattributed_N = interval_N − total_{N−1}`（等垂直同步、GPU 背壓、合成器、節流），單獨報告，不得把 `cpu_N` 加進 `interval_N`。rAF 時間戳與回呼起點可差約一個垂直同步週期，規格須寫明此容差。
- 第一個渲染幀、區段起點的第一幀沒有 `interval`，不得補 0。
加負向控制 12（CPU 歸到錯的幀）要有明確失敗斷言。

**A2-C3 冷暖區段的邊界與長幀事件（阻擋）。** 草案沒有定義 COLD 何時結束，且玩家在手機上無法呼叫 API。
→ 以「前景已渲染時間」自動分段：`COLD` 第 0–60 s（凍結為不可覆蓋的快照）、`WARM_UP` 60–120 s（保留、不作正式結果）、`MEASURE_1..n` 每 60 s 一段，每段結束即凍結到固定長度的結果列表（最多 8 段）。這樣 Martin 只要等待並截圖，就能得到「冷啟動、暖機 60 秒、量測 60 秒 ×3」。區段中斷（A2-C5）後從 `WARM_UP` 重新開始（頁面載入的 COLD 證據已保留）。
→ 長幀事件環形緩衝（固定 32 筆，COLD 另有自己的一份）：每個 interval > 100 ms，以及每個 `programs` 增加的幀，記錄 `ts`、`interval`、前一幀 `pre/physics/update/render`、`unattributed`、`Δprograms/Δtextures/Δgeometries`、新增 program 的名稱（A1 就是靠 `Ch03_Body` 這個名稱找到卡頓原因）。第 7.4 節要求的「長幀發生時的資源計數」只能這樣取得。
→ 區段彙總（count、> 50、> 100、max、最長幀時間戳）用執行中累加器，對整個區段精確，不受環形緩衝覆寫影響；百分位數才用 60 秒視窗。

**A2-C5 區段完整性簽章（阻擋）。** 在每個渲染幀比較一組數字：`preset`、`resScale`、`fpsCap`、`usePostFX`、`innerWidth×innerHeight`、有效 pixel ratio；任一改變就關閉區段（不足 60 s 標 INCOMPLETE）。草案缺視窗尺寸與 pixel ratio，平板轉向或摺疊會改變像素數卻不改變上述設定。可見度：沿用 `visibilitychange`，恢復後第一幀不算 interval，並記錄中斷次數與隱藏總時間；**前景長幀一律保留**，另外對「沒有 visibility 事件卻 ≥ 1 s 的 rAF 間隔」加 `foreground_stall` 旗標，只標記、絕不排除。`STATE.pauseRender`（除錯）視同中斷。

## 3. 必要修正

**A2-C6 CACHE 與更新率。** `sw.js` 的 `CACHE` 不會暴露給頁面，也不得為此改 `sw.js`。在診斷初始化時非同步呼叫一次 `caches.keys()`，取名稱符合 `^vh-` 者；因為 `activate` 會刪除其他版本，正常只會剩一個。沒有 `caches`、為空或多於一個就標 `UNAVAILABLE`（附清單），不得 fetch `sw.js`。第一次造訪尚未被 service worker 控制時會是 UNAVAILABLE，報告須在重新載入後再確認。更新率沒有標準網頁 API：可在診斷模式用前 120 個原始 rAF 間隔的中位數做 `refreshRateEstimate`（標 ESTIMATE，非必要）；否則 UNAVAILABLE，並照 B4 由實機報告手動記錄。

**A2-C7 0.2 ms 目標的定義。** `performance.now()` 在未跨來源隔離時解析度約 0.1 ms，單次取樣的 P95 量不出 0.2 ms。改為 SOFT_TARGET：每幀取樣函式的**平均**成本（在頁內以 ≥ 10,000 次批次呼叫量測）；1 Hz 統計更新（排序 ≤ 3,600 筆）成本另報；實機報告記錄計時器解析度估計。超標只報告原因，不作硬性閘門（與 N8、A1 一致）。診斷造成的長幀不得刪除。

**A2-C8 百分位與溢位的精確定義。**
- 樣本緩衝用固定大小 typed arrays（時間戳 Float64、其餘 Float32）。16,384 筆 × 約 7 個欄位約 0.5 MiB，低於 1 MiB；60 秒視窗在 240 Hz 不限幀約 14,400 筆，仍在容量內，高於約 273 fps 持續 60 秒才會 overflow。
- overflow = 「視窗內最舊的有效樣本被覆寫」；環形緩衝丟掉視窗外舊資料不算。
- 百分位在每秒最多一次的更新中，對預配置的暫存陣列複製後原地排序，不得新配置物件。
- `contacts` = 最後一次內部 step 的 `physicsWorld.contacts.length`（接觸方程式數，不是接觸對象數）；另報 `substeps`（`stepnumber` 差值，上限 3），因為 `step(1/60, dt, 3)` 每幀可能跑 0–3 次內部步進。`bodies`、`shapes` 每秒統計一次，不要逐幀掃描。

**A2-C9 行數可行性。** 把 C1–C8 算進去，我估計 `index.html` 新增加修改約 230–265 行，有超出 250 的風險；可行的前提是 HUD 精簡（C10）、不用 `tr()`、不壓縮程式碼。保留草案的 STOP 規則，另要求 Codex 在約 150 行時先回報全案預估；預估超過 250 就停止回報，不得縮減必要量測或測試，也不得自行提高上限。

**A2-C10 HUD。** 草案的 15 行 HUD 在手機橫向約佔 200 px 高，會蓋住畫面。限制為最多 4 行等寬小字：階段與序號、平均／最低 1 秒、P50/P95/P99 與 > 50/> 100 次數、最長幀、CPU 三項 P95、bodies/shapes/contacts、draw/triangles/programs、sample 數與區段狀態。標籤用英文技術縮寫，不加 `tr()` 鍵（`i18n_check` 只擋 CJK），省下約 24 行語系表。Martin 在手機上只能看 HUD 截圖，所以裝置驗收需要的數字（B4 全部欄位）都必須在 HUD 上；完整欄位留在 `__VH.diag.snapshot()`，該 API 為唯讀。

**A2-C11 測試的獨立性與回歸方法。**
- Node：用既有 `section()`（`collision_harness.mjs`）擷取 begin/end banner，預期值以測試內獨立寫的 nearest-rank 與計數產生，不呼叫 production helper。草案固定樣本 `[16,20,30,33,33,40,50,51,100,120]` 我已驗算：P50=33、P95=P99=120、> 50 為 3、> 100 為 1，正確。
- G12／G13：用 A1 風格的外部 harness，BASE 與 A2 分別在診斷關閉與開啟兩種模式下量測 `renderer.info`（外部設 `autoReset=false`，不依賴 A2 自己的計數），差值必須為 0。
- 「確定性 fixture contacts delta = 0」：先證明 BASE 對 BASE 重複兩次的 contacts 完全相同，才能列為硬性；若不成立就降為 INCONCLUSIVE，只用 bodies、shapes。
- G17／非目標：對 diff 做靜態掃描，不得出現 chunk／registry／LOD controller／`renderer.compile`／新 `localStorage` key／新 `fetch`／CDN。
- 負向控制每一個都要有可辨識的失敗斷言，並區分「斷言失敗」與「環境或執行錯誤」；草案的 12 個之外加：預設 `autoReset`（C1）、`>` 改 `>=` 之外的 FPS cap 略過幀（已含）、視窗尺寸變更未切段（C5）。
- G16：指定確切指令（`pwatest.py`；存檔相容性目前沒有獨立檔，須在規格列出要用的檢查，否則 G16 無法判定）。

**A2-C12 實機矩陣與流程。** 草案列的 7 個場景裡，Midtown、Mountain、Highway、Fast Travel 沒有 A1 的固定座標，與「優先沿用 A1 場景」矛盾。核心矩陣定為：S26 Ultra 的 PHONE_LOW、PHONE_MED，Tab S11 的 TABLET_MED；場景為 A1 已有座標的 CBD 白天 12:00、CBD 夜晚 23:00、Suburbs，共 3 組 × 3 場景。依 C3 自動分段，每個場景約 5 分鐘（冷啟動只在第一個場景），整體約 45–60 分鐘，需要分兩次進行以免過熱，並記錄電量／溫度。TABLET_HIGH 與其餘場景為選做。裝置上只能使用遊戲現有控制項到達位置與時間；我在登記時負責逐步核對這些控制項是否存在，並寫成 Martin 可照做的操作單。B4（平均 ≥ cap × 0.97）、B5、B6（250 行）、N8（時間量測不進 CI、headless 不當硬性閘門）、N10（不改 `sw.js`、CACHE 由 Claude 遞增）、N11（三角形口徑）草案均有沿用，通過。

**A2-C13 預算治理分類表。** 草案定義了三類，但沒有把現有項目逐項歸類，G0 無法確認「符合系列規格」。我的建議（需 Martin 確認，見第 6 節）：

| 類別 | 項目 |
|---|---|
| HARD_GATE | A2 結構閘門（bodies／shapes／場景 draw calls／triangles／meshes／材質／貼圖／依賴／localStorage key／逐幀配置／250 行）；離線與存檔相容；碰撞安全與無空白替換（系列 N5、D-065）；B4 裝置平均 FPS ≥ cap × 0.97（D-065 已採納）。 |
| SOFT_TARGET | 診斷取樣成本；P95 ≤ 40 ms、P99 ≤ 66.7 ms、最低 1 秒、> 100 ms 比例（草案 §25 初始值，待 A2 實機基準後由 Martin 確認）；新增 triangles P95 預算（PHONE_MED 為內插）。 |
| PENDING_EVIDENCE | draw-call、資源容量、串流 CPU、LOD 距離、物理時間比、活動碰撞半徑、Geometry／Texture 常駐量。 |

升降級規則：PENDING_EVIDENCE → SOFT_TARGET → HARD_GATE 只能由 Martin 依 MEASURED_DEVICE 證據明確批准，沒有自動升級；SOFT_TARGET 超標必須附原因與改善建議，同一目標連續兩個子任務超標則升級給 Martin 判斷。

## 4. 非阻擋建議

1. 分支名稱、`// === WE03A2-DIAG BEGIN/END ===` banner 命名請照 B6 與 `collision_harness.mjs` 的作法。
2. 診斷旗標用單一 `const diag = recordFps ? createDiag() : null`，熱迴圈內只做 `if (diag)`，便於 G01 以物件是否存在判定「正常模式零配置」。
3. 百分位若日後需要更低成本，可改固定寬度直方圖；本版因 nearest-rank 需要精確值，維持排序。
4. 可考慮在 HUD 長按複製 snapshot JSON，方便 Martin 回傳資料；不在本版範圍，行數吃緊時不做。
5. 手機 30 FPS cap 在 144 Hz 等非整除更新率下，正常間隔會交替約 27.8／34.7 ms，P95 ≤ 40 ms 仍可達成，但報告須註明更新率。
6. 草案的「單一 active code PR lock」與 D-013 分支保護，我在正式登記時才重新確認（需要登記當下的完整 main SHA）。

## 5. 對串流效益修訂（草案 §16）的審查

第 1–8 點與 A1、D-066 一致：不放寬碰撞安全、不把 `GLOBAL_STRESS_ONLY` 當合法土地或 B3 密度證據、半徑由 D/E1 決定（217 m 只是 A1 的分析假設）。有條件接受，條件如下：
- 20% 閘門的對照組必須與串流版使用**同一半徑政策與同一測試物件集合**；A1 在 57 棟、1 body／棟下，半徑 140–350 m 的峰值節省為 56–68%、重播路徑 P95 為 56–77%，所以 20% 很容易達成，**不得因此降低碰撞安全條件**（以系列最高速度上限與 `T_ready` 驗證）。
- 碰撞安全要同時看峰值，不只看 P95。
- 「body 數量降低」不等於「物理時間降低」：A1 的物理時間對照在四個 preset 都是 INCONCLUSIVE。A2 的實機資料請同時記錄 `physicsStepMs` 與 `bodies`，讓 Martin 在進入 B 之前判斷收益是否真實。
- 移除 Geometry／Texture 20% 閘門後，C+ 的收益只剩碰撞體。這是否仍值得做是 Martin 的決定，不是我的。

## 6. 需要 Martin 決定（分開批准）

1. **預算治理（方案 C）：** 是否採納 C13 的分類表與升降級規則。這是治理決定，與 A2 實作無關。
2. **A2 規格：** 是否批准「草案 + A2-C1..C13」為正式 T-018A2 規格（Codex 實作、HIGH／SMALL、`index.html` ≤ 250 行）。
3. **測試行數上限：** 草案的 500 行不夠。依 A1 檢查工具（33 個負向控制用了 446 行）的經驗，13 個 Node 案例、12–15 個負向控制、11 個 preset 的瀏覽器檢查，我估計需要 650–750 行；建議兩份測試合計上限 700 行（A1 的前例是上限調整需 Martin 同意）。
4. **串流效益修訂（草案 §16）：** 是否接受第 5 節的條件版本，並確認「只靠碰撞體收益」的取捨。
5. **實機矩陣（C12）：** 是否接受核心 3×3、約 45–60 分鐘、分兩次進行。

批准後我才會：建立正式 spec、登記 TASKS 與 DECISIONS（預計 D-068）、重新確認完整 main SHA、D-013 分支保護與單一 code PR lock。不授權 T-018B 或任何後續任務。

## 7. 審查限制

靜態審查，未執行瀏覽器或裝置測試；A1 工具未重跑。行數估計為經驗值，不是量測。
