# WE-03 v1.0（C+ Hybrid World Streaming Architecture）Claude G0 審查

審查者：Claude；日期：2026-11-28；審查對象：ChatGPT 草案 WE-03 v1.0 全文（已收到完整正文）。
審查依據：main `e8d5250fce0ea5f07f68840481cb95d2eca803fb` 的原始碼、COLLAB v3.6、`specs/we02/district_plan.json`、`specs/we01-final/WE-01_B8_runtime_baseline_appendix.md`。本審查未登記任何任務、未修改任何檔案。

## 結論：APPROVE WITH CONDITIONS

C+ 方向與草案的邊界（不做 HLOD 引擎、不改存檔、不改 WE-01／WE-02 裁定、不授權 WE-04..09）符合 Martin 的選擇。但草案有 5 項會讓系列無法照原樣執行的缺口（B1、B2、B4、B5、B6；原 B3 經複核已撤回並降為 N11），以及 11 項需要在子規格寫清楚的非阻擋項（N1–N11）。建議比照 T-017：Martin 批准時，把本文件的條件列為「Claude conditions（G0-S-C1..）優先於草案」，不必重寫 v1.1；但每個子任務仍須有自己的完整 spec、Martin 批准、單一實作者與單一 PR。

## 一、已核對且通過的事項（有證據）

- 完整 main SHA：`e8d5250fce0ea5f07f68840481cb95d2eca803fb`。`index.html`、`sw.js`、`manifest.webmanifest` 與歷史 Audit BASE `84319439…` 逐位元相同（`git diff` 為空），`CACHE` 仍為 `vh-2026-11-27-02`；其後差異只在 specs／tools／docs／.github。`index.html` 現為 12,560 行（`AGENTS.md` 仍寫約 9,900 行，屬文件過期，Claude 另行修正）。
- `T-018` 尚未被使用（TASKS／DECISIONS／COLLAB／AGENTS 無此編號），可用。
- 合成負載與 WE-02 一致：P1 R01 9／R02 5／R05 22／R08 4 = 40 棟、52 戶；P2 12／7／33／5 = 57 棟、72 戶（直接由 `district_plan.json` 計數）；P2 目標 13／7／34／6 = 60（即 B3 R01、R05、R08 各 +1，R02 不變）；壓力 26／14／68／12 = 60 的兩倍 = 120。
- 草案的 128 m 網格、半開區間、floor 負座標方向正確；128 為 2 的次方，`Math.floor(x/128)` 精確。
- 草案要求「診斷預設關閉、保留 `?fps=1`」可行：`?fps=1` 已存在（`createFpsReadout`），且在該模式下既有的自動降畫質與動態解析度都被停用（`!recordFps` 分支），所以 `?fps=1` + 手動固定畫質正好是「不得以自動降畫質掩蓋」的既有機制。
- 140／180 m 碰撞半徑與 0.5 s 更新有既有先例：`TREE_COLLIDERS = { enter: 140, leave: 180, interval: 0.5 }`，並以 `treeInteracting()` 保護接觸中的車輛、在 `physicsWorld.step` 之前以 `removeBody` ＋ `broadphase.dirty` 增刪。`physicsWorld.step` 只有一個呼叫點（animate 迴圈），安全點明確。
- `window.__VH` 已暴露 `renderer`、`scene`、`physicsWorld`、`STATE`、`WORLD`、`THREE`、`CANNON` 等，所以 headless 的 draw calls／triangles／bodies／shapes／物理 step 都不需要改 `index.html` 就能量（WE-01 B8 即如此）。
- 草案的原型貼圖規格（1024² RGBA8 atlas + 512² R8 夜間遮罩）與既有 Site A 展示區（T-014B2/B3）相同，有實作先例。

## 二、阻擋項（需在批准文字／子規格中修正；B1、B2、B4、B5、B6，原 B3 已撤回）

**B1（G0-S10／S12／S13）有工作無人負責：合成原型資產、測試載入器、重播驅動。**
草案要求四種原型各 3 級 LOD 的合成網格（上限 12,000／20,000 三角形）、共用 atlas、40／57／60／120 棟的遊戲內置放，以及裝置端「可重播路徑」，但 18 節的子任務沒有任何一項負責：A1／F1 禁止改遊戲程式，C1 只做資源登錄。而且 B1／B2／B3 目前沒有道路可達，裝置實測必須有「僅測試用」的傳送或腳本路徑。
→ 新增子任務 **T-018C2「合成原型資產＋測試載入器＋重播驅動」**，Codex，HIGH，index.html 建議 ≤ 500 行，排在 C1 之後。要求：以 URL 參數啟用、預設關閉（關閉時 bodies／shapes／draw calls 新增 0）；不寫入 `vh_save`、不新增任何 localStorage key、參數不得持久化；40／57 棟使用 `district_plan.json` 的地塊座標（唯讀），60／120 棟的額外位置須以確定性規則產生、彼此與 Site A、海灘、既有物件不重疊，且不得寫回或登記為合法地塊；重播驅動只在測試旗標下移動玩家，不改正式車輛操控。

**B2（G0-S13／S14）每個子任務必須自帶測試與 CI 接線，不能把測試集中到 F1。**
COLLAB §5.2.3 要求每段有自己的回歸測試（可辨識的失敗斷言），並由 Claude 接入 CI。草案 20 節的 WS01–WS28 沒有對應到子任務。
→ 在系列文字加入對應表：B：WS01–05、WS25；C1：WS08–10；C2（新）：WS26 與載入器隔離；C3／C4（原 C2 拆分，見 B6）：WS05–07、WS11；D：WS12–13；E1：WS14；E2：WS15–16；F1：跨系統壓力、WS17–22 的自動化、負向控制；F2：WS23–24、WS27–28。每個子任務 PR 的 `tools/test/` 測試須在該任務內交付。

**B3（已撤回，降為非阻擋 N11）。** 初稿曾以「最壞視點三角形 192,650／226,700／230,900 已超過 §22 的 120,000／200,000」判定預算與資產上限矛盾。複核後發現這三個數字是**全方位（360°）常駐上限**，並非單一畫面的繪製三角形；改以水平約 96° 視錐（16:9 約 60° 垂直視角）計算，最壞視點為 PHONE_LOW 106,000、TABLET_MED 143,000、DESKTOP_HIGH 206,000，均低於草案預算。因此「預算互相矛盾」的結論撤回；仍成立的只是 PHONE_LOW 餘裕偏小（約 12%），且未計陰影 pass、建築高度與霧。見 N11。

**B4（G0-S12）§25 裝置門檻與既有 30 FPS 鎖幀矛盾。**
手機與平板預設 `fpsCap` 為 30（`QUALITY_CONFIG.fpsCap`），畫面以 1 秒為單位計數最多約 30，「每次平均 FPS ≥ 30」會因 29／30／31 的量化誤差而不穩定，與 P95 ≤ 40 ms 的寬容度不一致。
→ 改為相對鎖幀：平均 FPS ≥ 鎖幀值的 97%（30 FPS 鎖幀即 ≥ 29.1）；其餘 P95、P99、最低 1 秒、> 100 ms 比例沿用。裝置測試必須使用 `?fps=1`（自動降畫質與動態解析度已停用）並以手動固定畫質；報告須記錄 `resScale`、`fpsCap`、顯示更新率、遊戲版本與 CACHE 名稱。

**B5（G0-S12）A2 需要，但範圍很窄，且應提前。**
詳見第五節：既有 `?fps=1` 只顯示 1 秒分箱的平均與最低值，沒有逐幀時間、P95／P99 或 > 50／100 ms 計數，因此 WS24 目前不可能判定。A2 必須在串流實作之前完成，Martin 才能先取得「沒有串流的 BASE」裝置基準。

**B6（G0-S13）原 C2 超過單一 PR 範圍，須拆分並訂定各子任務行數上限。**
視覺串流／載入卸載／陳舊結果保護／LOD0-2／遲滯／無空白替換合在同一 PR，預期會超過 COLLAB §5.2 的約 600 行與「一個系統邊界」。
→ 拆為 **C3 視覺區塊生命週期**（載入卸載、generation token、重試）與 **C4 LOD 控制器**（LOD0/1/2、遲滯、無空白替換）。建議 index.html 行數上限（新增＋修改）：A2 ≤ 250；B ≤ 350；C1 ≤ 400；C2 ≤ 500；C3 ≤ 450；C4 ≤ 450；D ≤ 500；E1 ≤ 450；E2 ≤ 350。超過須停止並重新拆分。串流核心必須以明確的 begin／end 註解區塊放在 `index.html`，讓 Node 測試可用既有 `section()` 方式擷取（`collision_harness.mjs` 的作法）；不得新增執行期檔案，因此 `sw.js` 的 PRECACHE 不變。

## 三、非阻擋項（寫入子規格即可；N1–N11）

**N1（S02）Engineering BASE。** 目前 main 與歷史 Audit BASE 的遊戲原始碼相同，但每個子任務一旦合併就改變 BASE。每份子 spec 必須列自己的完整 baseline SHA；WE-03A 量到的基準只在原始碼與該 SHA 相同時可沿用，否則重量。

**N2（S06）畫質 preset 與遲滯。** 實際有 11 個 preset（`QUALITY_CONFIG.presets`）：PHONE_LOW／MED、TABLET_LOW／MED／HIGH、DESKTOP_MED／HIGH／ULTRA、IGPU_LOW／MED／HIGH。草案只對應 4 個。未對應的 7 個由 WE-03A 提出映射；映射批准前，串流預設關閉，不得套用「最近列」。FogExp2 在 LOD2 上限處的霧化比例約為 PHONE_LOW 78%（650 m）、TABLET_MED 65%（850 m）、DESKTOP_HIGH 76%（1200 m），WE-03A 應評估 LOD2 半徑是否過大。遲滯 ±10% 在 PHONE_LOW LOD0（100 m）只有 ±10 m，而 250 ms 的更新間隔在 ≥ 80 m/s 時一次移動 ≥ 20 m，會跨過整個遲滯帶；LOD 目標必須考慮速度前瞻，並保證「請求 LOD N 時 LOD N+1 已常駐」，在最高車速下測試無空白。

**N3（S04）「非同步」要先定義。** 合成資產全為程式產生，沒有網路載入，所以 `LOADING` 的非同步只能來自預算切片工作或 Promise 型貼圖建立。子規格須提供可注入延遲的完成函式，WS05（≥ 100 次陳舊完成）才有意義；generation token 須在完成時比對，過期結果釋放而非啟用。

**N4（S05）資源登錄只能管理自己建立的資源。** 不得 dispose Site A 展示區既有 atlas／夜間遮罩或任何世界資源；ref count 為負、仍被引用就 dispose 都須是可偵測的錯誤。以 `renderer.info.memory` 的 geometries／textures 計數驗證 WS10／WS11；貼圖記憶體為估計值，不得稱為實測 VRAM（草案已要求）。

**N5（S07）碰撞。** 安全點採「animate 中 `physicsWorld.step` 之前」，沿用既有 `refreshTreeColliders` 模式與接觸保護。v 必須實測：最高車款 `vmax` 295 km/h ≈ 81.9 m/s，氮氣倍率 1.38 ≈ 113 m/s（升級與空中另計，WE-03A 實測）；113 m/s 時 140 m 只有約 1.24 s，`T_ready` 須包含既有 0.5 s 更新間隔。以 WE-02 地塊計算，最壞視點 140 m 內 18 棟、180 m 內 20 棟、217 m 內 25 棟（皆 ≤ 新增 bodies 預算 32）；若每棟碰撞形狀 > 4 個則 128 shapes 預算會被突破，D 的子規格須明訂每棟形狀數上限。60／120 棟負載須重算。

**N6（S08）預載與排程。** `D_preload` 在 113 m/s 為 516 m，57 棟只佔 16 個區塊，高速時幾乎等於全載入，必須有每幀預算與飢餓上限（aging）數值。1024² atlas 的上傳不可切分：atlas 與夜間遮罩應在測試載入時一次建立並常駐，不得在串流中途建立，否則違反每幀 2 ms 預算。

**N7（S09）快速旅行與重生。** 既有 `fastTravelTo` 是淡出 300 ms 後同步 `teleportTo`，並有外送任務限制（開始與逾時回呼兩次檢查）、`SHOWCASE_SITE_A` 例外、導航點清除；`teleportTo` 還會做 `refreshTreeColliders(0,true)` 與 Site A LOD 重置。`teleportTo` 只有兩個呼叫者（`fastTravelTo`、STUNT 任務起點），另有直接設位置的路徑（約第 9159、9168 行）；FAST_TRAVEL 清單沒有任何目的地在 B1–B3，所以 E2 只能是測試路徑。WE-03A 須盤點所有位置重設路徑。5 秒逾時時須還原淡出（`travel-fade` opacity）並顯示訊息，不得停在黑畫面。

**N8（S11）量測有效性。** B8 的 baseline control 物理中位比 1.033／1.070／0.996，所以 1.20／1.25 的上限可行但餘裕約 0.13；headless SwiftShader 的單幀時間範圍很大（例如 5.3–24.3 ms），幀時間 P95 比 ≤ 1.10 不適合當單獨的放行閘門。→ 硬閘門用確定性數量（bodies、shapes、draw calls、triangles、GPU 資源計數）與物理中位；headless 幀時間 P95 比若 control 不在 1/1.10..1.10 則 INCONCLUSIVE，但不單獨阻擋，由實機結果決定。必須沿用 B8 的「每地點新開頁面、等待 `__phDone`、相同載入狀態」方法（DESKTOP_HIGH 有非同步載入競態）。§24 動態測試約 3,600 幀 × 5 路徑 × 3 preset × 3（BASE／PR／control）≈ 16 萬幀，須分段背景執行；只有確定性部分進 CI。

**N9（S11）串流效益閘門。** 四種原型各一張共用 atlas，在 Control A 與 C+ 都常駐，貼圖節省接近 0；「geometry＋texture 峰值降低 ≥ 20%」可能無法誠實達成。bodies P95 降低則很容易（最多約 25 對 60，≥ 58%）。WE-03A 先算出分析預期值，再由 Martin 確認閘門組成。

**N10（S14）離線／存檔／CI。** 不新增檔案、不改 `sw.js`；每次合併後 `CACHE` 由 Claude 遞增（index.html 變動）。WS18／WS19 使用既有 `pwatest.py` 與存檔檢查。CI：Node 層級測試（索引、生命週期、資源登錄、HLOD 父區塊、負向控制）接入既有 `check` 工作；瀏覽器層級測試比照 `t014b2-facade.yml` 另立 Playwright（固定 1.55.0）工作；時間量測不進 CI，由 Claude 在本機重跑並記錄。測試旗標、診斷與合成物件在正常模式必須不可見、不可碰撞（WS26）。

**N11（S11，取代原 B3）三角形預算的口徑。** 以 `district_plan.json` 的 57 棟、草案 LOD 半徑與三角形上限，視點在 20 m 網格上、以建築中心距離歸類 LOD、不計霧、遮擋、陰影 pass 與建築高度：全方位常駐上限 PHONE_LOW 192,650／TABLET_MED 226,700／DESKTOP_HIGH 230,900；水平 96° 視錐（每個視點取最佳朝向，15° 步進）為 106,000／143,000／206,000。兩組數字都是**分析估算**，不是 renderer 量測；視錐版本才可與 §22「新增三角形 P95」比較，PHONE_LOW 只有約 12% 餘裕。→ WE-03A 必須先以相同方法重現（計算腳本見 `we03_g0_worstcase_reference.py`），再加入實際相機（視角、長寬比）、霧、陰影 pass 與建築高度，並明訂 §22 的三角形口徑（是否含陰影 pass）；§22 在 Martin 確認修訂表之前仍只是暫定值。

## 四、逐項回覆 G0-S01..S16

| 項目 | 結果 |
|---|---|
| S01 架構範圍與 C+ | 通過；不做 HLOD runtime、不遷移既有城市，與 C+ 一致 |
| S02 Engineering BASE | 通過（見 N1，BASE 完整 SHA 如上） |
| S03 區塊所有權與負座標 | 有條件：須定義 owner 規則（見下方 C-S03） |
| S04 生命週期與非同步競態 | 有條件：N3 |
| S05 資源共用與 dispose | 有條件：N4 |
| S06 LOD 與既有 preset | 有條件：N2（7 個 preset 未對應） |
| S07 碰撞與安全點 | 有條件：N5 |
| S08 預載與排程 | 有條件：N6 |
| S09 快速旅行／重生／任務 | 有條件：N7 |
| S10 合成隔離與原型數量 | 數量通過；隔離與載入器缺口見 B1 |
| S11 預算與量測有效性 | 有條件：N8、N9、N11 |
| S12 實機量測 | 有條件：B4、B5 |
| S13 分解、allowlist、行數、路由 | 有條件：B1、B2、B6，路由見下 |
| S14 離線／存檔／CI | 通過方向；N10 |
| S15 HLOD 契約 | 通過；只做資料契約與父區塊推導純函式 |
| S16 不改 WE-01／WE-02、不授權 WE-04..09 | 通過；合成物件不得寫入 `district_plan.json` |

**C-S03 區塊所有權（補充，必須寫入 B 的子規格）。** 草案說「跨區塊物件僅有一個 owner chunk」但未定義 owner。以 WE-02 地塊實算：57 棟中 34 棟（約 60%）的外框跨越至少 1 條區塊邊界，最多跨 4 個區塊，所以這是主要情況而非邊角。建議：owner＝外框中心點所在的區塊（半開區間 `[k·128, (k+1)·128)`）；查詢用的覆蓋範圍＝`floor(min/128)` 到 `ceil(max/128) − 1`（上緣恰在邊界時不進入下一格）；父區塊索引用 `Math.floor(c/2)`（或 `>> 1`），不得用 `|0`、`Math.trunc` 或 `%`。測試向量須含 −1、−2、−3、−128、−128.0001、0、127.9999、128，並以 34 棟跨界地塊作為固定案例。

**路由（S13）。** F1 Gemini（LOW，只改 `tools/test/`）符合 COLLAB §5.1 規則 1。**A1 建議改由 Claude 負責**：A1 的產出是「基準與驗收預算的依據」，若由實作者之一（Gemini）自己量測、自己訂出預算，會削弱 COLLAB 要求的獨立量測；Claude 已有 WE-01 B8 的量測流程可直接沿用，並比照 T-017（Claude 實作文件與離線工具）。Codex 負責 B、C1、C2、C3、C4、D、E1、E2、A2 符合「量小、高風險」預設；Gemini 不承擔任何高風險程式 PR，因此不觸發 §4.3 的階段 3 前置條件。

## 五、其他回覆項目

**建議的正式任務編號**（登記一律待 Martin 批准，且每個子任務在自己的 spec 批准時才登記，比照 T-016 的作法）：

| 編號 | 內容 | 實作者 | 風險／量 |
|---|---|---|---|
| T-018 | WE-03 系列總覽（不是程式任務） | — | — |
| T-018A1 | WE-03A 基準校準＋量測工具＋預算修訂建議（`tools/we03/`、`specs/we03/`，不改 index.html） | Claude（建議；取代 Gemini） | LOW／SMALL |
| T-018A2 | 裝置端幀時間診斷（擴充 `?fps=1`） | Codex | HIGH／SMALL |
| T-018B | 區塊登錄 | Codex | HIGH／SMALL |
| T-018C1 | 資源登錄 | Codex | HIGH／SMALL |
| T-018C2（新） | 合成原型資產＋測試載入器＋重播驅動 | Codex | HIGH／SMALL |
| T-018C3 | 視覺區塊生命週期（原 C2 前半） | Codex | HIGH／SMALL |
| T-018C4 | LOD 控制器（原 C2 後半） | Codex | HIGH／SMALL |
| T-018D | 碰撞串流 | Codex | HIGH／SMALL |
| T-018E1 | 預測排程 | Codex | HIGH／SMALL |
| T-018E2 | 目的地準備（測試路徑） | Codex | HIGH／SMALL |
| T-018F1 | 壓力測試資料與腳本 | Gemini | LOW／LARGE |
| T-018F2 | 整合與裝置驗收 | Claude（Martin 實機） | — |

**A2 是否必要：需要，但只為了裝置端幀時間。** headless 的 draw calls、triangles、bodies、shapes、物理 step 時間都能透過既有 `window.__VH` 量到，不需要 A2。既有 `?fps=1` 只輸出「1 秒分箱平均／最低／preset」，沒有逐幀時間、P50／P95／P99、> 50／100 ms 計數與版本資訊，所以草案 §25 的裝置門檻目前無法判定。A2 範圍（≤ 250 行）：僅在 `?fps=1` 下啟用，環形緩衝記錄幀間隔（不得每幀配置記憶體），在畫面上顯示 P50／P95／P99、> 50／100 ms 計數、最長幀、目前 preset、`resScale`、`fpsCap` 與 CACHE 版本；保留既有「平均／最低」文字與其行為；不改任何幀間距、畫質或物理。**排序：緊接 A1 之後、B 之前**，讓 Martin 先在 BASE 上取得沒有串流的裝置基準。串流系統自己的計數（陳舊完成拒絕、碰撞就緒落差、串流 CPU 時間）放在各自子任務的 `__VH.we03` 命名空間，不放進 A2。

**WE-03A（T-018A1）必須完成的基準校準：**
1. 原始碼盤點：main SHA、`CACHE`、行數、`teleportTo` 與所有位置重設路徑。
2. 11 個 preset 的完整盤點（pixelRatio、fog、鎖幀、traffic、props）與 7 個未對應 preset 的映射建議。
3. 實測最高移動速度（各車款、最高升級、氮氣、空中；玩家跑步 8.8 m/s）與 `T_ready` 的量測方法及上限。
4. 基準表：PHONE_LOW、PHONE_MED、TABLET_MED、DESKTOP_HIGH × 六個固定地點 × 12:00／23:00 的 draw calls、triangles、bodies、shapes、geometry／texture 計數，物理 5 組配對；沿用 B8 方法（每地點新開頁面、等待 `__phDone`）。
5. 以 `district_plan.json` 計算最壞值與路徑 P95：新增三角形、bodies、shapes、draw calls、貼圖估計；與 §22 對照並提出調和後的預算表。
6. 量測穩定度：重複 N 次的 control 區間，決定哪些指標可作為硬閘門。
7. 渲染器能力：最大貼圖尺寸、mipmap、R8 格式支援（headless 結果，標明不代表實機；實機由 A2 之後的診斷或 Martin 回報確認）。
8. 高樓螢幕投影門檻校準資料（需各原型高度）。
9. 合成 60／120 棟的確定性置放提案及地面高度、與 Site A／海灘／既有物件的衝突檢查。
10. Control A 與串流效益閘門的分析預期值。
11. 裝置量測流程草案：熱身、`?fps=1`、固定 preset、每次回報格式。

**第一個可獨立批准的子任務：T-018A1（WE-03A 基準校準＋量測工具）。** 不改 `index.html`、`sw.js`、`CACHE`、存檔；沿用 B8 的 headless 方法；成品放在 `tools/we03/` 與 `specs/we03/baseline_report.md`，並將檢查接入 CI；完成後 ChatGPT、Claude、Martin 才確認或修訂 §22 預算。其後依序 A2 → B → C1 → C2 → C3 → C4 → D → E1 → E2 → F1 → F2，一次只有一個程式 PR。

## 六、未動與未授權

本審查未登記任務、未啟動實作。未修改遊戲檔、`sw.js`、`CACHE`、存檔、道路、地形、建築、WE-01／WE-02 成品。WE-03 結案不自動授權 WE-04..WE-09。限制：本審查以原始碼閱讀與 `district_plan.json` 計算為依據，未執行任何串流原型；最壞三角形與視點數是以草案參數與 WE-02 地塊中心點的分析估算，不是實測，也不是裝置 FPS。
