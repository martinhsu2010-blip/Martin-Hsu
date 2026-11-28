# T-018A1 v1.0（WE-03 基準與架構校準）Claude G0 審查

審查者：Claude；日期：2026-11-28；對象：ChatGPT 草案 T-018A1 v1.0 全文（已收到），並對照 `WE-03_v1.0_G0_review.md`。本審查未登記任務、未修改任何檔案。

## 結論：APPROVE WITH CONDITIONS

範圍（只做唯讀分析與量測工具，不碰 `index.html`、`sw.js`、`CACHE`、存檔、WE-01／WE-02 成品）正確，A01–A11 與先前 G0 的 B1–B6、N1–N11 對得上，48 個 headless 組合與 5,760 幀的算術正確（4 preset × 6 地點 × 2 時段 = 48；48 × 120 = 5,760）。需要 15 項修正（A1-C1..C15），其中 4 項會影響結果可信度（C1、C4、C6、C10）。比照 T-017：Martin 批准時，這些條件寫進登記用的入口 spec，**優先於草案**，不必重寫 v1.1。

## 先更正我自己的一個錯誤

我在 WE-03 G0 審查初稿中把「最壞視點三角形 192,650／226,700／230,900」當成已超過 §22 預算。這三個數字是**全方位（360°）常駐上限**，不是單一畫面的繪製三角形。改用水平約 96° 視錐重算：PHONE_LOW 106,000、TABLET_MED 143,000、DESKTOP_HIGH 206,000，均低於 §22 暫定預算（PHONE_LOW 餘裕約 12%）。因此原 B3「預算互相矛盾」已撤回，降為 N11，審查文件與給 ChatGPT 的回覆都已更新。草案 A08 引用的三個數字須依下方 C1 改標。

## 必須修正（A1-C1..C15）

**A1-C1（A08，影響可信度）參考數字重標。** 草案把 192,650／226,700／230,900 稱為「Claude G0 參考」。須改標為「ANALYTIC_ESTIMATE，全方位常駐上限」，並加入視錐版本 106,000／143,000／206,000。計算方法（20 m 網格視點、建築中心距離分級、草案三角形上限、不計霧／遮擋／陰影 pass／高度）已寫成 `we03_g0_worstcase_reference.py`，A1 須先用同一方法重現這兩組數字，再往下精修（實際相機視角與長寬比、霧、陰影 pass、建築高度、重播路徑 P95）。「渲染三角形」的口徑（含或不含陰影 pass）須明訂。

**A1-C2 禁止修改清單的檔名錯誤。** 草案列 `manifest.json`，但專案裡沒有這個檔案，實際為 `manifest.webmanifest` 與 `manifest.zh-TW.webmanifest`。改正，否則 A1-G18 的檢查會漏掉真正的檔案。

**A1-C3 檔案範圍與 allowlist。** 工具改放 `tools/we03/`（與 Claude 擁有的 `tools/we01/`、`tools/we02/` 一致；`tools/test/` 留給實作者的回歸測試）。成品放 `specs/we03/`。A1-G18 的允許清單須明列：`tools/we03/*`、`specs/we03/*`、登記文件 `specs/WE-03-series-spec-v1.0.md` 與草案／審查原文、`TASKS.md`／`DECISIONS.md`／`LOG.md`／`HANDOFF.md`、`.github/workflows/pwa-cache-check.yml`（Claude 接 CI）。其餘一律視為未批准變更。

**A1-C4（影響可信度）三支工具的分工與獨立性。** 比照 T-017 的做法：`we03_baseline.py`＝瀏覽器量測（Playwright，不進 CI，輸出 `baseline_metrics.json` 原始樣本與環境資訊）；`we03_calibration.py`＝確定性分析產生器（preset 映射、區塊比較、fixture 計畫、三角形與效益分析、預算 JSON）；`we03_calibration_check.py`＝**獨立**檢查（不得 import calibration，自行重算所有分析數字，並對 `baseline_metrics.json` 做結構與出處驗證：48 組合齊全、每組 ≥ 120 幀、4 preset × ≥ 5 組物理配對、SHA、環境欄位）。行數上限沿用 600／500／400（合計 1,500）。CI 只跑 check（讀已提交的 JSON，不重新量測）。

**A1-C5（A04）「BASE 自身對照配對」的定義。** 因為 A1 沒有 PR，配對＝同一 commit 的兩個獨立工作階段（各自新開頁面、交替順序）。沿用 B8 的做法：每個地點新開頁面、等待 `__phDone`、DESKTOP_HIGH 以偽裝 `WEBGL_debug_renderer_info` 進入。PHONE_MED 是 B8 沒量過的 preset（它會載入 Poly Haven 模型，PHONE_LOW 則不會），須同樣等待 `__phDone`。比率定義、控制區間 1/1.10..1.10、INCONCLUSIVE 處理照草案。

**A1-C6（A03，影響可信度）幀時間的定義與統計力。** headless 以手動推進 `animate` 取得的是「CPU 提交時間」，不是實機幀時間；120 個樣本的 P99 實際上是第二大的樣本，統計力低。報告須明寫此限制，並把 draw calls／triangles／bodies／shapes／資源計數當硬性資料。另須做 control：B3 與 CBD 兩處 × 日夜 × 4 preset，各重複一次獨立工作階段（共 16 組），用以決定哪些指標穩定到可作閘門。

**A1-C7（A05）速度與準備時間。** 須分開記錄兩類數字：(a) 由原始碼推導的上限（各車款 `vmax` × 升級倍率 × 氮氣倍率，以及玩家跑步 8.8 m/s），標 SOURCE_CONFIRMED；(b) 在測試軌道實際達到的最高速度，標為「該軌道上的下限」，不得宣稱是遊戲絕對上限。`TREE_COLLIDERS`（enter 140、leave 180、interval 0.5 s）與 `treeInteracting` 護欄作為既有先例列入。每棟碰撞形狀上限須有依據（既有郊區房屋為每 16 棟一個 body、每 body ≤ 16 shapes，見 `collision_check.mjs`），並說明新建築每棟 1 body 的假設。

**A1-C8（A06）footprint 與地塊邊界。** 依 WE-02 G0-W7，地塊多邊形就是 `bounds` 矩形（方向只有 0／90），所以 footprint 與 parcel bounds 的差異預期為空；仍照草案獨立重算 34 個跨區塊地塊與最多 4 區塊覆蓋，並對 64／128／256 m 三種格距各報同樣統計。負座標測試向量採草案列出的 8 個，另加恰在邊界的最大邊（例如 max = 128）以驗證「上緣不進入下一格」。

**A1-C9（A07）合成置放的排除條件不足。** 草案只排除互相重疊與 Site A。須再加：海灘區（`map_geometry.json` 的 `beach_regions`，x 225–465，與 B1 重疊）、WE-02 第一期與第二期所有道路／街道廊道、WE-01 的 protected／unknown／unavailable 格、各區外框範圍、地形高度可站立的檢查，以及與已規劃 57 棟的腳印重疊。構成也要寫明：40 ＝ P1 地塊；57 ＝ WE-02 P2 全部；60 ＝ 57 ＋ 3 個合成（B3 的 R01、R05、R08 各 1）；120 ＝ 60 ＋ 60 個合成，使組成恰為 26／14／68／12。合成物件標 `SYNTHETIC_ONLY`，不寫入 `district_plan.json`。至少 5 條重播情境須含速度、路徑點與固定模擬時間 ≥ 60 s（對應 WE-03 §24）。

**A1-C10（A08／A09，影響可信度）分析與實測的界線。** A08 的住宅負載數字、A09 的節省比例全部是分析估算，必須標 ANALYTIC_ESTIMATE，不得與 A03 的 MEASURED_HEADLESS 混表。我先前提到的「碰撞體節省約 58%」是以 ≤ 25 個活躍 body 對 60 棟估算（217 m 內），若對 57 棟為約 56%，且假設每棟 1 body；A09 須重算並標明假設。四種原型共用 atlas 時貼圖節省接近 0 的情況，要在效益門檻建議中明講，不得靠增加 Control A 重複資源來製造節省。

**A1-C11（A10）裝置協議須涵蓋 WE-03 §25 全部欄位。** 補上：顯示更新率、裝置／系統／瀏覽器版本、解析度與方向、溫度或熱限制資訊、暖機至少 3 分鐘、40／60 棟各 3 次每次 ≥ 120 s、日夜與區塊切換路徑。FPS 門檻採 ≥ 鎖幀值 × 0.97（30 FPS 鎖幀為 29.1）。協議須明列 A2 必須提供的欄位：P50／P95／P99、> 50／100 ms 計數、最長幀、preset、`resScale`、`fpsCap`、CACHE 名稱，並保留既有「平均／最低」文字。A2 完成前，Martin 用 `?fps=1` 只能得到 1 秒平均與最低值，不足以當基準，協議要註明。

**A1-C12（A11）來源分類加一類。** 現有四類（MEASURED_HEADLESS、ANALYTIC_ESTIMATE、PROPOSED_LIMIT、PENDING_DEVICE）無法標示「直接讀自原始碼的常數」（例如 140／180 m、0.5 s、`vmax`）。加入 `SOURCE_CONFIRMED`；不穩定或無有效 control 的量測標 `INCONCLUSIVE`。任何未量測或僅分析的值不得標 MEASURED。

**A1-C13（A03）固定流程沿用 B8。** 暖機 20 幀、記錄 120 幀、固定 dt = 1/60、`dayCycle` 關閉、`fpsCap = 0`、固定相機、視窗 800×450、日 12:00／夜 23:00、六個固定地點座標同草案。原始 JSON 保存所有樣本、命令、瀏覽器與 GPU 回報字串、`page_errors`。

**A1-C14（A01）盤點必須含位置重設路徑清單。** 逐一列出 `teleportTo` 的所有呼叫者（目前 `fastTravelTo`、STUNT 任務起點）以及直接寫 `position.set` 的位置（目前約第 9159、9168 行等），並記錄 `fastTravelTo` 的外送任務檢查（開始與逾時回呼各一次）、`SHOWCASE_SITE_A` 例外、導航點清除、`teleportTo` 的副作用（`refreshTreeColliders(0, true)`、Site A LOD 重置）。草案的「禁止將推測標示為已確認」照單全收，每一項附原始碼行號與 commit。

**A1-C15 治理欄位與驗收順序。** TASKS 條目須含 `Implementer: Claude`、`Reviewer: ChatGPT`（審查方法與預算）、`Risk: LOW`、`Volume: LARGE`、一行理由。Claude 為實作者，因此不自我審查：ChatGPT 唯讀審查（比照 T-017 G0-W3）通過後，才交 Martin 驗收。A1 結案不批准修訂後的預算，也不授權 A2 以後任何任務；A2 仍需自己的 spec 與批准。

## 草案中符合預期、不需修改的部分

- Engineering BASE `e8d5250fce0ea5f07f68840481cb95d2eca803fb` 正確，遊戲原始碼與歷史 Audit BASE 相同；登記 PR 之後 main 會前進，但只增加文件與工具，A1-G01 以該 SHA 與 Audit BASE 比對。
- A04 的物理方法（900 暖機 + 360 記錄、`physicsWorld.step(1/60,1/60,3)`、區間 1/1.10..1.10、不得刪不利樣本）與 B8 一致。
- 「headless 數字不是實機 FPS／VRAM」「A1 不實測 `T_ready`」「不修改車輛操控、物理參數或交通 AI」的限制措辭正確。
- 負向控制的七類（缺 preset、缺組合、重複 object ID、負座標錯誤、合成重疊、原型棟數錯誤、未量測值標成實測）足夠；我另要求加上「把分析估算標成 MEASURED」與「`manifest.webmanifest` 被修改」兩項。

## 登記計畫（待 Martin 批准後才執行）

1. D-065：採用 WE-03 G0 條件（B1、B2、B4、B5、B6 與 N1–N11）為系列約束，並批准修正後的 T-018A1。
2. 新增 `specs/WE-03-series-spec-v1.0.md`（入口：本系列的 Claude conditions 優先於 ChatGPT 草案，含 12 個子任務順序、各子任務行數上限、WS→子任務對應表），原文存 `specs/WE-03-draft-v1.0-chatgpt.md`、`specs/T-018A1-draft-v1.0-chatgpt.md`，並附兩份 G0 審查與 `we03_g0_worstcase_reference.py`。
3. TASKS：只登記 T-018（總覽，非程式任務）與 T-018A1（Claude 實作）；其他子任務在各自 spec 批准時才登記。
4. 同一個 docs PR 更新 TASKS／DECISIONS／LOG／HANDOFF；不改任何遊戲檔、`sw.js`、`CACHE`。

## 未動與未授權

本審查未登記任務、未啟動 A1。未修改遊戲檔、`sw.js`、`CACHE`、存檔、WE-01／WE-02 成品。不授權 A2、B、C1–C4、D、E1–E2、F1–F2 或 WE-04..WE-09。
