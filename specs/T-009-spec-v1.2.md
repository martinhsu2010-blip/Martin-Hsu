# T-009 spec v1 — Midtown 路口斑馬線試點（Gemini 首項 Stage 3 world/render task）

> **狀態：PROPOSED／提案，供 Claude 審查；未經 Martin 批准，禁止登錄或開工。**
>
> **Author / design owner：** ChatGPT　**Implementer / task owner：** Gemini（Antigravity，Stage 3）　**Independent reviewer / integrator / releaser：** Claude　**Acceptance：** Martin　**Priority：** P2
>
> **Design baseline / confirmed main SHA：** `182a09e227049f99e3b46c4a76e3d27671cc1595`（2026-11-21 查核：與 `main` identical）。**User-provided earlier reference：** `e71b59bf75cd55f3a785b1cb52431c08bcea529f`（D-026 Stage 3 promotion commit；其後 main 已追加 D-027 / COLLAB v3.6 docs commit `182a09e`）。實作時若 `main` 已推進，Claude 須再次記錄起點、重檢 spec，不能隱藏變更。
>
> **Protocol：** repo 已批准 **COLLAB v3.6**（D-027；§4.3 沿用 v3.5 Stage 3 強制閘門）；D-013、D-021、D-026、D-027；`AGENTS.md`、`TASKS.md`、`specs/TEMPLATE.md`。**Branch：** `gemini/T-009-crosswalks` → PR `main`，只有一個程式 PR。
>
> **Verification at authorship：** `designed`。沒有聲稱已量測、已修改遊戲、已跑 CI、已實機確認或獲得批准。

## 0. 兩個候選與選擇理由

| 候選 | 玩家能看到／感受到 | 一行取捨 |
|---|---|---|
| **A. Midtown 斑馬線試點（推薦、本文正式規格）** | 指定兩個十字路口有連續、清楚的行人穿越道，改善現有過於空曠的道路觀感 | 世界／渲染系統新增極少量靜態幾何；容易以真實 Chrome draw calls、場景及碰撞不變性驗證 |
| B. R4 北區車流停滯點修復 | 改善先前記錄的 R4 約 `(-4,629)` 一帶車流停頓 | 直接改善交通但需要分析轉向、路面與 AI 重播，首次 Stage 3 的判斷性與回歸風險較高，Codex 更合適 |

**推薦 A。** 這是 Stage 2 原本禁止的「世界／渲染內容」，因此足以驗證 Stage 3 權限及 §4.3 嚴格測量；同時不碰核心物理或改路網。這是 C+ 街道改造的**可獨立交付小試點**，不是完整 C+ 地圖／建築升級任務。

## 1. 目標與明確非目標

在現有 Midtown 道路網的 **2 個固定十字路口**，各於南、北入口新增 1 組白色斑馬線，共 **4 組 × 每組 8 條 = 32 條**。玩家開車經過與步行時都能看到新的道路標記，白天／夜晚均須可辨認。此斑馬線是**純視覺靜態世界物件**，沒有互動、交通優先權或行人 AI 意義。

**不做：** 新道路、新路口、新地形、新車款、車流路由或優先權變更、紅綠燈控制、NPC 動線、行人碰撞、角色／車輛動力、輪胎摩擦或車速、任務／獎金、導航／傳送、地圖資料、camera、renderer pipeline、後製參數、材質總庫重構、存檔欄位、語系字串、音效、動畫、其他街區斑馬線、大量街道翻新。沒有新增外部素材／CDN／離線下載依賴。**不得把「車輛遇到斑馬線會停」混入本 PR。**

## 2. 現況依據與設計錨點

- `ROAD_NET.avenuesX` 包含 `-240`、`0`，大道半寬 `12`；`ROAD_NET.crossZ` 包含 `-360`，橫街半寬 `11`（目前 `index.html` 約 2735–2740 行）。
- 平面大道 mesh 高度 `y=0.06`；橫街 `y=0.068`；路口修補平面 `y=0.074`，路口大小 `24.4 × 22.4`（約 5900–5975 行）。
- 既有 `buildRoadNetwork()` 會產生曲線路、郊區路與山區道路（約 3468 行）；`buildCityDetails()` 已有路口紅綠燈、長椅等共用 `InstancedMesh`，但目前全檔沒有 `crosswalk` / `zebra` 標記。
- `window.__VH` 已暴露 `scene`、`renderer`、`physicsWorld`、`STATE`、`ROAD_NET`、`WORLD`、`camera`、`teleportTo`（目前末端 debug export）；**直接量測真實 `renderer.info.render.calls`，不得只用靜態場景 Mesh 數量代替。**
- 已有 `tools/test/route_legality.mjs`、`traffic_check.mjs`、`collision_check.mjs` 等路徑／物理相關測試；需要新增的功能測試不可替代既有測試。

## 3. 明確變更範圍與內容

### 3.1 唯一允許的新增世界內容

1. 交叉口座標**固定**為 `(-240,-360)`、`(0,-360)`，單位沿用 world `x/z` 公尺。須先檢查兩組均在 `ROAD_NET.avenuesX` / `crossZ` 中，且非圓環、坡地、斜向或高架匝道的特殊路面。不得因視覺上覺得更好而自行換座標；若現場路面有特殊結構／遮蔽使本規格不合適，停下附截圖供 Claude／Martin 修訂規格。
2. 每個路口 **南北兩側**，橫跨**南北向大道**新增各 8 條橫向排列的白色條紋（條紋幾何相對 x 軸分散、沿 z 軸延伸）。每組 8 條 `PlaneGeometry` 等效貼地矩形：沿 `x` 寬 `1.6 m`，沿 `z` 長 `2.8 m`，x 中心 `ax + (i - 3.5) × 2.6 m`（`i=0..7`），z 中心 `cz ± 14.0 m`。每條 y 基準 `0.085 m`，與平坦大道 `y=0.06` 保持 `0.025 m` 可見間距；不允許超過 `y=0.12`，不得在道路上產生可碰撞厚度。
3. 32 條條紋必須**共用單一 `THREE.InstancedMesh`**（一份單純矩形平面幾何、一份不透明粗糙的離線內建白色材質），不要逐條建立 32 個 `Mesh` 或 32 個材質。建議顏色 `#ece9df`，粗糙度 `≥0.85`、metalness `0`，不發光、不透明、不 castShadow；可使用安全的 polygon offset 防止 z-fighting。關閉 shadow casting；不得新增 PBR 外部貼圖或使用遠端素材。
4. 在路面與路口 patch 已完成後**只建一次**，推薦新增單一 `buildMidtownCrosswalks()` 並於現有世界初始化／路面產生附近呼叫。把唯一網格註冊至 `WORLD.midtownCrosswalks`（供功能測試及 Claude headless 對照）；不增加每幀更新函式、timer、observer、重複 scene.add。保留正常 frustum culling／bounding sphere。
5. 本次只加**靜態可見幾何**：**增加 0 個 Cannon body、0 個 shape、0 個 RaycastVehicle、0 條交通 AI 路線；新增 `vh_save` 欄位數 = 0**。不得改變任何其他世界 seed、地形高度、路網／行人可達性、城市建築數量與 placements。不得修改既有 collider、車流生成或碰撞調校。
6. 對體驗而言，斑馬線是標線，不是高起的減速帶；車輛駛過應感覺與原本同一位置完全相同，不可發生跳動、輪胎支撐改變或加速異常。夜晚可讀，但不可使用自發光大面積白光造成刺眼。

### 3.2 檔案、PR 與實作限制

**Gemini 程式 PR allowlist：** 只修改 `index.html` 並**新增** `tools/test/midtown_crosswalk_check.mjs`。如果 Claude 確認重播測量必須以程式腳本保存，可另**新增** `tools/test/midtown_crosswalk_bench.mjs`，但該檔只可執行 headless 比較、不可修改遊戲原始碼、不得引入執行期依賴；其是否需要以及工具可用性由 Claude 在開工前確認。

**明確禁止**：修改 `sw.js`、`COLLAB.md`、`AGENTS.md`、`TASKS.md`、`DECISIONS.md`、`HANDOFF.md`、`LOG.md`、`specs/`、`.github/`、`css/app.css`、任何圖片／模型／貼圖／字型與二進位素材，以及原有測試的斷言／基準。由 Claude 在 release/docs PR 唯一負責 `sw.js` cache、文件及新增測試接入 `.github/workflows/pwa-cache-check.yml`。禁止重排 `index.html` 其他段落。

**PR 大小建議**：本功能 production diff 約 `≤120` 行、專屬測試約 `≤240` 行；優先遵守 v3.6 §5.2 的大型任務審查上限。若需要超過一個世界子系統的改造，表示任務不夠小，**停止並回報**，不能擴大成道路重製。

## 4. 開工前必須通過的 Stage 3 Gate（缺一不可）

1. Claude 先審完本規格並確認可執行；Martin 明確以「批准 T-009 v1.1」批准**完整同一版**，Claude 再 docs-only PR 原文登錄 `specs/T-009-spec-v1.1.md`、`TASKS.md` 和對應決策，回報最新 main SHA。D-026 升階及 D-027 協作規則批准**均不等於 T-009 規格批准**。此 v1.1 **僅替換 v1 的 §4／§6 測量條文**，其他驗收、程式範圍與測試義務全部保留；舊版引用若與 §4／§6 的量測角色、900／360 步、校準或 9 組複測相牴觸，以本版 §4／§6 為準。其他章節的 `v1` 字樣因本次限定修改範圍而原文保留；轉交實作或登錄時須明確識別完整規格版本為 **v1.1**，不得把 v1 誤認為已獲批准。
2. `TASKS.md` 中 Gemini `Current stage: 3`、沒有 paused／rollback；唯一共享 code-PR 鎖空閒。以當時最新 main 為 branch base；一個 task、一個 Gemini 實作者、一個程式 PR。若存在其他未合併程式 PR，不得開工。
3. **Claude 在 Gemini 寫任何高風險程式碼前，獨立完成測試完備性檢查：** 從 baseline 實際確認現有 `AGENTS.md` 檢查可執行；Chrome/headless 可以載入本機 vendored 資產、讀取真實 `__VH.renderer.info.render.calls` 和在頁內直接呼叫 `__VH.physicsWorld.step(1/60,1/60,3)`；可取得 `PHONE_LOW`、`TABLET_MED`、`DESKTOP_HIGH` 的固定場景、對應 baseline 與物理 body/shape 計數。**先執行 §6.2 所述每 preset × scene 的 5 組「baseline vs baseline」校準，逐組記錄 ratio 分布**，確認程序可重跑；此校準不是 PR 通過的替代品。`main` 所需 git history、Chromium/Playwright/CDP 與相關設備必須可用。若某 preset 無法驗證、校準或原始數據不可取得，或只能給結構估算／截圖，**不准啟動**；先修復測試設施或改派 Codex。
4. 同一可重播情境的固定隨機種子 `5019`、瀏覽器版本、UA／畫質、viewport、初始 localStorage、world 座標、時間條件皆需確定。若 headless 只能偵測到 `IGPU` 而無法覆蓋 `DESKTOP_HIGH`，不可把 `IGPU_HIGH` 冒稱 `DESKTOP_HIGH`；測試環境若用只改 UA / WebGL 報告字串的測試專用設定強制 profile，必須逐步揭露、兩版同法、不能當實體 GPU 性能數據。物理 benchmark **不依靠 requestAnimationFrame（rAF）實際驅動模擬**，頁面載入和 teleport 完成後由同一頁內同步迴圈直接 step；不可把 renderer FPS 或整幀耗時當作物理數據。
5. **每項風險均須有會失敗的自動測試：** 新測試對準實際已載入的 production function／網格，不得在測試中複製假的 builder 取代真實程式。Claude 在 review 時對至少**兩種實際故障變異**確認測試變紅，且不更改既有測試或放寬 assertion。**增加 0 個 Cannon bodies、0 個 shapes（delta = 0）**是本視覺功能**主要且不可豁免的物理驗收條件**；即使 timing 比率合格，增加 body/shape 仍 FAIL。若無法做到以上要求，該任務不符合 Stage 3，停工。
6. **職責分界：** Gemini 只負責批准範圍內的功能實作、新的失敗斷言回歸測試、AGENTS 與 task-specific 檢查、如實 PR 報告；**Gemini 不必自行執行或提交 physics benchmark、baseline/baseline 校準、renderer draw-call benchmark**。所有 §6 校準、PR/baseline 量測、ratio／draw-call 判定由 **Claude 獨立執行並留存可重跑證據**；不得因 Gemini 未自行量測而把它視為測試缺失，也不得因 Claude 尚未完成而宣稱已驗收。

## 5. 回歸測試：固定 seed、真實程式與失敗斷言

### 5.1 `node tools/test/midtown_crosswalk_check.mjs`

實作者編寫 test runner：**直接擷取／載入 `index.html` 中真實 `buildMidtownCrosswalks()` 產物並執行**（可用 repo 既有 `collision_harness.mjs`／`traffic_harness.mjs` 的 VM／Three.js fake scene 方式），用受控但實際的 `THREE.InstancedMesh`、`ROAD_NET`、`WORLD`、`scene`、`physicsWorld` 環境；另核對 production builder **真的呼叫**此函式。不接受僅 grep 出函式名稱、斷言 `32` 常數或把期望座標的另寫一份函式拿來測。

| Risk | 真實測試輸入與斷言（錯誤時要紅燈） | 應抓到的故障變異 |
|---|---|---|
| R1 位置／方向錯誤 | 從實際 `instanceMatrix` 逐條還原 `(x,y,z)` 與平面朝向、尺寸；32 條全部對應 **2 路口 × 2 端 × 8 條**，坐標與 3.1 完全一致（浮點誤差 ≤0.005m），絕不位於 intersection pad 內或越過 `avenueHalf`。 | 改一組 z `±14→±7` 或旋轉錯誤，即 FAIL。 |
| R2 真正批次化與生命週期 | 僅一個 `THREE.InstancedMesh`、`count=32`、一種材質、`castShadow=false`、`transparent=false`、測試場景中 scene 新增恰好一個 draw-submitting mesh；世界初始化恰好一次、手動重建／傳送不得自動重複生成。 | 拆成 32 個普通 meshes 或加陰影，即 FAIL。 |
| R3 道路／物理／交通不變 | 執行 builder 前後取 `physicsWorld.bodies` 與各 body 的 `shapes` 數量、`ROAD_NET.routes`（各點 x/z/y）、`ROAD_NET.avenuesX`／`crossZ`、既有路口參數序列化摘要；全數深度相等，總新 body/shape = 0。另跑 baseline vs PR `route_legality` 和原 traffic／collision 測試。 | 加任一靜態碰撞箱、調一個 AI 路線點或變更路寬，即 FAIL。 |
| R4 確定性／低成本 | 同一 seed `5019` 連續初始化兩次，32 個矩陣與材質參數完全相等；`geometry` 個數 1、材質 1；不可有畫面更新循環／事件處理；無任何外部 texture URL。 | 隨機擺放、動態創建新 meshes 或新 CDN 引用，即 FAIL。 |
| R5 真實遊戲場景 | Headless Chromium 啟動本地 `index.html`，使用 `window.__VH.WORLD.midtownCrosswalks` 真實網格驗證 count、visible 與 camera/frustum；前後同一地點的真實瀏覽器截圖清晰可見斑馬線且無明顯 z-fighting；產生 console errors、載入失敗就 FAIL。 | 只有 VM 看得到網格、真正建世界時沒呼叫，或網格低於路面，即 FAIL。 |

新測試須能在沒有 T-009 功能的 baseline 上因**缺少 production crosswalk**而 FAIL；但 baseline 原有既有測試仍需 PASS。Claude 在 PR review 透過臨時修改 PR 工作樹（**不提交 mutation**）測試至少 R1 的 `z=±7` 和 R3 的額外 body / R2 的 shadow 任選兩種，確認各會 FAIL，並記錄測試名稱、故障、輸出。

**注意：** 5.1 的 structural scene 新增一個 mesh 不等於真實渲染只增加一個 draw call；**效能驗收只能用 §6 的真實 Chrome renderer 讀數**。

### 5.2 AGENTS 與任務專屬命令（全部逐項報告）

```sh
python3 tools/test/syntax_check.py
python3 tools/test/i18n_check.py
node tools/test/i18n_check.mjs
node tools/test/hud_check.mjs
node tools/test/camera_check.mjs 182a09e227049f99e3b46c4a76e3d27671cc1595
node tools/test/traffic_check.mjs
node tools/test/collision_check.mjs
node tools/test/suburb_check.mjs
node tools/test/urban_check.mjs
node tools/test/route_legality.mjs
node tools/test/explore_picks_check.mjs
node tools/test/zone_arrival_check.mjs
node tools/test/midtown_crosswalk_check.mjs
```

`camera_check` 的參數正式開工時用 **當次已核准且已確認的 main base SHA**，上列為設計 baseline；若變更，Claude 在 task register 中更新。任何測試因環境缺少 git history / browser / dependency 不能跑，Gemini 在 PR 必須註明 **NOT RUN + reason**，不得寫 PASS；Claude 需獨立補驗，未補驗不可合併／驗收。所有 AGENTS 原有檢查不可被新增測試取代或刪除。

## 6. Claude 可重跑的真實 headless 量測程序與硬上限

### 6.1 同環境雙版本、固定情境

1. Claude 從 GitHub checkout **兩份獨立 worktree**：baseline SHA `182a09e227049f99e3b46c4a76e3d27671cc1595` 與 Gemini PR head；依各自工作樹以 `python3 -m http.server` 於不同 localhost port 服務，所有 `./libs/`、`./models/`、`./textures/` 皆由原生本地靜態伺服器供應。若二者不是同一 main base，先 rebase 或重訂 baseline，禁止使用不同世界版次比較。**校準另取同一 baseline 版本的兩個獨立頁面／context，比較 baseline A vs baseline B；不得把一次測量與自己相比。**
2. 每次開新的 headless Chromium **乾淨隔離 context（service workers blocked，cache empty）**；同一 Chrome binary/build、WebGL backend、CPU／GPU／headless flags、DPR、UA、localStorage、seed=5019、fps cap=unlimited。使用 init script 在頁面載入前設定相同 seed 的 `Math.random` 重播序列及 `vh_settings` 所需的 profile／quality；此 init script 只用於測試，兩版本一致，不得修改 repo 產品碼。**不得**修改 `vh_save` 格式；以空白或同一份合法舊 save 設定，並另以既有 save 驗證一次。
3. 下列 preset 必測且**不得互相冒充**：

| 項目 | PHONE_LOW | TABLET_MED | DESKTOP_HIGH |
|---|---|---|---|
| 模擬 viewport | 390 × 844 CSS px | 800 × 1280 CSS px | 1280 × 800 CSS px |
| UA／pointer | Android mobile / touch | Android tablet / touch | desktop / fine pointer |
| `__VH.STATE.profile` | `PHONE` | `TABLET` | `DESKTOP` |
| `__VH.STATE.quality` | `LOW` | `MED` | `HIGH` |
| `auto quality` | 手動指定／不允許自動換檔 | 同左 | 同左 |
| 驗證平台 | Claude headless + Martin S26 Ultra | Claude headless + Martin Tab S11 | Claude headless desktop |

4. 頁面載入等 `window.__VH`, 實際 world/vehicle 初始化完成後，記錄其 profile、`quality`、UA、WebGL renderer，排除 JS console error、資產 404。調成相同天候與日照（建議白天 13:00；須使用原有 day cycle／weather 公開控制，記錄實際值，不要偷偷改產品碼）。固定 input-free、無人為操控、無警方追逐；自動品質降檔需關閉或明確確認一直沒發生。**物理**以 §6.2 的 ≥900 同步 step 為 warmup，**draw-call** 測試則在相機穩定後另外預熱至少 **180 個實際 rendering frame**；兩套量測不得混用。
5. **兩個「目標 camera／玩家位置」**：`__VH.teleportTo(0,-408,0)` 和 `__VH.teleportTo(-240,-408,0)`（接近對應路口的南側，允許 camera 重新穩定後取得比較）；**一個未改區域控制場景**：`__VH.teleportTo(110,650,0)`。同場景、相同 `CAM`/zoom/mode、renderer state 與快取狀況下 baseline／PR 成對截圖；測量前人工確認兩張影像真正看到相同路口與車道，否則先修正場景錨點並一致重跑，不能把看不到新斑馬線的截圖稱為功能驗收。

### 6.2 物理成本：頁內直接 step、同版本校準及 5→9 組判定

**v1.2 判定原則與主要硬條件：** 本功能只新增靜態視覺斑馬線，**`physicsWorld.bodies` 總數與所有 body 的 `shapes` 總數，PR − baseline 必須各為 0**；既有 collider 內容及交通路線亦不得更動。這是**主要、不可放寬的物理驗收依據**，且不受任何計時結果或 9 組複測豁免。同步 physics step 計時只用來攔截非預期的 CPU 效能回歸；**PR/baseline 中位數固定上限為 ≤ 1.25**。baseline/baseline 校準僅檢查量測有效性，**不再以 `calibration_median + 0.10` 計算允許上限**。**本節 v1.2 判定數值優先於未修改章節中的舊 `≤1.10` 表述（包含 A09、舊 Prompt／HANDOFF）；其餘要求與驗收項目不變。**

1. **場景與重播：** Claude 對 `PHONE_LOW`、`TABLET_MED`、`DESKTOP_HIGH`，分別在路口近景 `__VH.teleportTo(0,-408,0)`、未改區域 `__VH.teleportTo(110,650,0)` 量測；每 preset × scene 分開校準與配對，不得互相借數據。每個樣本均使用全新、獨立、乾淨的瀏覽器 context，載入真實遊戲頁面，等待 `__VH`／世界初始化，固定 seed、profile、quality、存檔、日照和無輸入狀態，再執行 `teleportTo`。於 baseline／PR 的相同階段記錄 physics world bodies 和所有 shapes 數量及 delta；非零即 FAIL，不得以測量雜訊解釋。另依 §5.1 對真實 builder 執行前／後直接驗證 +0。
2. **物理計時方法（不靠 rAF）：** 每個單獨樣本在頁面內以一次同步瀏覽器評估（例如 Playwright `page.evaluate`）直接迴圈呼叫 `__VH.physicsWorld.step(1/60, 1/60, 3)`。**每個樣本**先 warmup **至少 900 步**，再以 `performance.now()` 計算連續 **360 步總時間** `360_step_total_ms = t1 - t0`，附 warmup/timed 步數、body/shape 計數。這不是 360 個 rAF、FPS 或整幀耗時；不得用 Node VM 假物理取代真實頁面。同步區段不插入 rendering、玩家／AI 更新或其他操作；背景負載／非同步干擾必須排除，無法公平重播則標記量測阻擋。
3. **baseline vs baseline 校準（只驗證環境）：** 每個 preset × scene 使用同一 baseline SHA 的**兩個獨立乾淨頁面／context**，進行 **5 組**成對樣本；每個 A／B 樣本都各自 warmup ≥900、計時 360 步。**交替執行順序**：第 1／3／5 組為 `A → B`，第 2／4 組為 `B → A`；一律以身份固定計算 `calibration_ratio = baseline_B_total_ms / baseline_A_total_ms`，不可因執行次序反轉分子分母。記錄每組執行順序、雙方毫秒、ratio、完整 ratio 分布、最小／最大及中位數。**校準有效性硬條件：`0.75 ≤ calibration_median ≤ 1.33`（含端點）**。若超出此區間，結果記為 **MEASUREMENT BLOCKER**：不得判定 PR PASS／FAIL；先排查／修復 Chrome、CPU 負載、context 或測試環境，再重新完成該 preset × scene 的校準與正式量測。校準即使有效也**不得**放寬或收緊固定 `1.25` PR 上限。
4. **PR vs baseline 正式成對計時：** 每個 preset × scene 先執行 **5 組**全新 baseline／PR context 配對；每個樣本均有 warmup ≥900、同步計時 360 步。**交替執行順序**：第 1／3／5 組 `baseline → PR`，第 2／4 組 `PR → baseline`；如需補至第 9 組，第 6／8 組 `PR → baseline`，第 7／9 組 `baseline → PR`。每組固定以 `ratio = PR_total_ms / baseline_total_ms` 計算，不因順序調換而反轉；逐組記錄順序、雙方時間及 ratio，不得刪除慢樣本或混用 preset／場景。
5. **固定正式上限與判定：** 在該 preset × scene 的 baseline/baseline 校準**有效**（中位數在 `0.75–1.33` 內）且 bodies delta = shapes delta = **0** 的前提下，以 PR/baseline ratio 的中位數對照唯一固定時間上限 **`≤ 1.25`**。**`calibration_median + 0.10` 不再是通過條件**，也不需要另滿足 `≤1.10`；`1.25` 專屬本次不新增物理內容的 T-009 CPU 回歸防線，不能外推成其他 Stage 3 任務的預設上限。bodies/shapes +0 與碰撞內容不變仍是首要硬閘門。
6. **初次超標先補至 9 組：** 若有效校準下某 preset × scene 的初始 **5 組** PR/baseline ratio 中位數 **> 1.25**，先標記 **PROVISIONAL EXCEEDANCE（待複測）**，在相同環境新增 4 組並保留原 5 組，累計 **9 組**，依 9 個 ratio 的中位數與**同一固定 `1.25` 上限**做最終時間判定。9 組中位數仍 >1.25 即 **FAIL／不得 merge**；≤1.25 才算時間閘門通過，需完整報告全部 9 組與執行順序。校準無效為 measurement blocker（先修復環境重新量測）；**任何 bodies/shapes delta 非零、回歸測試失敗均直接獨立 FAIL**，不因補到 9 組而豁免。
7. **Claude 獨立報告：** 對每個 preset × scene 列出 (a) 5 組 baseline/baseline 校準雙時間、A/B 順序、ratio 分布、中位數及是否落在 `[0.75,1.33]`；(b) PR/baseline 5 組（必要時 9 組）雙時間、執行順序、ratio、中位數、**固定 `1.25`** 判定、PASS／FAIL／MEASUREMENT BLOCKER；(c) baseline／PR 的 bodies/shapes 實值、delta 及 collider/route 不變驗證；(d) Chrome、viewport、profile、quality、seed、teleport、warmup 與計時步數、採樣時間戳及重跑方式。**所有 §6 量測由 Claude 執行；Gemini 不須自行做物理或 draw-call benchmark**。

### 6.3 draw calls：真實 `renderer.info.render.calls`，逐場景逐 preset

- 對上表三 preset、上述**兩個改動近景與一個未改場景**，在穩定相機後讀取每個已完成 rendering frame 的 `__VH.renderer.info.render.calls`；每組截取 **至少 60 幀**原始值，取每組中位數。每個場景在 baseline 與 PR 各執行至少 5 個相同 seed/context 的成對組合，記錄所有 paired medians 與 delta。
- **只允許下列「PR − baseline 真實 draw calls」硬上限：**

| Preset | 斑馬線可見的任一近景 | 未修改遠景 `(110,650)` |
|---|---:|---:|
| `PHONE_LOW` | **≤ +2** | **≤ +0** |
| `TABLET_MED` | **≤ +4** | **≤ +0** |
| `DESKTOP_HIGH` | **≤ +6** | **≤ +0** |

- 每個近景另要求新標線 **在真實截圖中可見**，且在至少一個不被其他畫面因素遮蔽的量測組別中，draw calls 的差異 **≥ +1**；若功能本應可見卻差異 0 且看不到標線即 FAIL。若因多重 postFX passes 導致 delta 超上限，仍 FAIL，不能以「只有一個 InstancedMesh」要求豁免。
- **對每個 preset/場景，每一組的 paired-median delta 都必須在該列上限內**；附五組原始結果及最高值。若 pre-existing 場景雜訊使無法公平比較，先修正 benchmark 可重播性，**不能改成只報結構估算**。
- 本節仍以**真實 renderer render loop** 的已完成畫格來讀 draw calls（和 §6.2 物理同步 step 測量完全分開）；此處不以同步 physics step 取代渲染測試。**Claude 獨立執行並判定**，Gemini 無須跑這些測量。

### 6.4 例外及復測處理

- **Claude 負責全部 §6 量測，Gemini 不須做。** 若缺少任一 baseline/baseline 校準或 baseline/PR 物理數字、preset 不正確、draw-call 每組不足 60 個實際完成畫格、缺乏可重跑流程，或任何 9 組後仍超物理時間硬上限、bodies/shapes delta ≠ 0、draw 超標、截圖看不到目標、P1 回歸 → **不得 merge / release**。初始 5 組物理時間超標先依 §6.2 延長至 9 組再定最終 FAIL，不可直接放寬限值或剔除不利樣本。遇到 measurement blocker 先修復 benchmark 環境；需要程式修正則在原 PR 由原 Gemini 實作者完成（一般問題最多兩輪）後，Claude 重新執行相關完整測量和回歸測試。重大 hard violation 仍依 COLLAB §4.3 處理。
- Martin 於 S26 Ultra / Tab S11 實際開車穿越兩個路口（白天／夜晚各一次），確認兩組路口的南北兩側共四處斑馬線可辨識、無跳車／碰撞／路面閃爍、車道未錯位。`?fps=1` 使用同一 preset、同一位置、連續約 60 秒；**兩裝置各平均 FPS ≥30**，數據由 Martin 自行提供，Claude 的 headless 結果不能冒充 device-measured。若 Martin 未提供 FPS，須標為「未量測」，不得宣稱 FPS 驗收完成。
- 舊 save 可載入、任務／收入正常、PWA 線上及離線啟動正常、沒有新資產 404；Claude 發布前更新 `sw.js` CACHE，並在自身 docs/release PR 將 `node tools/test/midtown_crosswalk_check.mjs` 接入 `.github/workflows/pwa-cache-check.yml`，確認**CI 真的執行並綠燈**，不可只聲稱「測試存在」。

## 7. 完整 Acceptance Criteria（全部達成才算完成）

| ID | 要求 | 驗證角色／證據 |
|---|---|---|
| A01 | 完整 spec 先經 Claude review + Martin 明示批准，Claude 原文登錄；Stage 3 與 single PR lock 經確認 | Claude，docs PR / TASKS / D-026 |
| A02 | 只改 `index.html` 與允許的新 `tools/test/` 檔案；一個 PR、一位 Gemini、禁止 docs/sw/assets/CI 修改 | Claude，diff |
| A03 | **兩個**核准路口 `(−240,−360)`／`(0,−360)`，**四組**斑馬線、**32** 條；世界位置與尺寸對應 §3.1，夜間能辨識 | 失敗斷言 + 真 Chrome 截圖 + Martin |
| A04 | 只有一個 shared `InstancedMesh`，一次建立，零 timer／per-frame 更新，零新 texture URL / runtime network | 自動測試 + code review |
| A05 | `physicsWorld` body/shape **+0**、路網資料與 AI 路線 **完全一致**、save schema 新欄位 **+0** | 直接執行 builder、序列化摘要、route/traffic/collision regression |
| A06 | 專屬測試會觸發 production 函式且有可辨認失敗 assertion；Claude 至少兩種 mutation 讓測試變紅 | 新測試 log / Claude mutation log |
| A07 | **完整執行／如實列出** §5.2 的 AGENTS 及所有相關專屬檢查；無 FAIL/假 PASS；UI、startup console 無新錯 | Gemini PR + Claude replay |
| A08 | 先達成 §4 gate：baseline 實測可取得，完全可重播的 Chrome scene，畫質精確匹配 | Claude pre-start audit log |
| A09 | 每個 preset × 近景／遠景 **5 組 physics paired**，逐組數字、中位數比率 ≤1.10； bodies/shapes +0 | Claude headless-measured 表 |
| A10 | 每個 preset × **3 場景**真實 `renderer.info.render.calls`、每組 60 幀／5 組，全部 delta 在 §6.3 上限內；同位置截圖 | Claude headless-measured 表 |
| A11 | 新測試由 Claude 在 docs/release PR 接入 CI，CI 實際跑且 PASS；`sw.js` cache、離線／舊存檔與部署通過 | Claude CI + release 記錄 |
| A12 | Martin 實機日夜驗收四組斑馬線／無物理異常，S26 Ultra 與 Tab S11 `?fps=1` 各平均 ≥30 FPS | Martin device-measured，未提供不得假稱通過 |
| A13 | Claude 每次 Gemini PR 查驗 D-013：required PR、`enforce_admins=true`、無 force push、無 delete、repository rulesets **0**；記錄時間／來源；任一無法驗證停止 | Claude PR review |

## 8. PR 測試回報格式（Gemini 必填，不能冒充 Claude）

PR description 必須有以下四區：

1. **Changes / scope**：實際檔案、函式、4 組座標、32 條分布、body/shape delta、未改動的系統、baseline SHA、Gemini Stage 3 資格、PR lock 狀態。
2. **Tests I RAN**：每條 §5.2 命令、實際 PASS/FAIL、短輸出或可核查 log；含新 test、Chrome（若 Gemini 自己真跑）的 config/seed/camera/preset。**即使某項 CI 綠燈也不能把它列為 Gemini 自己跑過。**
3. **Tests NOT RUN / limitations**：未執行的 AGENTS、route、headless、phone/tablet device、offline、FPS、paired physics、real draw calls 各項明列未執行原因及需 Claude 補驗事項。沒有跑的數字不可填估計值當作 PASS。
4. **CI vs Claude vs Martin**：CI 狀態單列；Claude independent measurement 註記 **pending until Claude actually measures**；device-measured 註記 **pending until Martin reports**。不以測試計畫當成已完成測試。

Claude review 對上述實測證據、實際 diff、兩種 mutation、每一個 preset 的五組配對數值逐一核對；不接受只寫「全部測試通過」。

## 9. 依賴／風險與 Claude 待審點

1. 兩組十字路口的實際道路貼圖及障礙物是否使 32 條白線不可見？**須於開工前實際 Chrome 截圖確認**；必要時由 ChatGPT 出 v1.1 並請 Martin 批准，Gemini 不得自行更改座標／範圍。
2. Headless GPU 被偵測成 `IGPU` 時，Claude 可否穩定重播 `DESKTOP_HIGH`？不可以假裝 preset；先做 Stage 3 baseline 可重播性 gate。
3. `renderer.info.render.calls` 在多 pass composer 和自動品質切換時是否穩定？Chrome 基線試跑必須能分辨特定 scene +1 差異，否則測量程序先修正，不得宣稱只有一個 mesh 就一定 +1 draw。
4. 局部紙面美術改善不代表 C+ 世界改造完成；本功能不得擴張為全城街道標線工作。

## 10. Martin → Antigravity（English Prompt；僅在核准後傳送）

```text
Implement T-009, Gemini's first Stage 3 world/render trial, ONLY after Martin explicitly approves the COMPLETE T-009 spec v1, Claude registers it at specs/T-009-spec-v1.md, confirms the shared code-PR lock is free, and independently confirms the COLLAB v3.6 §4.3 baseline/test-completeness gate. Read COLLAB.md, AGENTS.md, TASKS.md, DECISIONS.md, and the complete registered T-009 specification.

Current design baseline: 182a09e227049f99e3b46c4a76e3d27671cc1595 (the earlier D-026 promotion commit e71b59bf75cd55f3a785b1cb52431c08bcea529f is NOT the latest main). Verify latest main again before starting; record any base change and request Claude's revalidation. Use gemini/T-009-crosswalks, one implementer, one task, one PR to main. Never push to main or merge.

Implement exactly one visual-only Midtown crosswalk feature. Add exactly four zebra-crossing bands at existing intersections (-240,-360) and (0,-360), one band on each north/south avenue approach, eight white stripes per band (32 total). Use the exact sizes, coordinates, orientation, y offsets and material constraints in spec §3.1; exactly one THREE.InstancedMesh, zero new colliders or Cannon bodies, zero traffic/AI route edits, and no per-frame updates. Expose WORLD.midtownCrosswalks for independent inspection; preserve existing roads, physics, handling, camera, saves, rendering pipeline and offline assets. Do not add features such as traffic stopping for pedestrians.

You may edit only index.html and add the focused production-code regression test tools/test/midtown_crosswalk_check.mjs (plus an optional tools/test/midtown_crosswalk_bench.mjs if Claude has preapproved it). The regression test MUST execute the real production crosswalk builder, assert the actual instance matrices/count, physical-road alignment, batch/material properties, no new bodies/shapes and unchanged traffic routes, and fail on intentional production mutations; do not reproduce the builder's logic in the test. Do not weaken old tests or alter baselines. Do not edit sw.js, docs/specs, .github, CSS files or binary assets.

Run every mandatory AGENTS check, plus the task-specific route_legality, Next Stop, Zone Arrival and crosswalk regression tests. Report each command actually run and its observed result, then explicitly list everything NOT run with reasons. If you perform real Chromium benchmarks, record the exact preset, viewport, seed, positions, paired physics and renderer.info.render.calls values; NEVER claim headless values are device measurements. All Stage 3 physical/draw-call pass/fail judgments require Claude's OWN independent five-pair comparisons and the per-preset ceilings in spec §6. If the measurements are not reproducible, exceed a limit, or need any out-of-scope modification, STOP and report the blocker; do not relax limits, invent numbers or broaden the PR.

Claude alone independently reviews, verifies D-013 main protection, repeats failure-injection and physics/draw-call benchmarks, wires the new regression test into GitHub Actions CI, updates sw.js CACHE and governance/docs via separate PRs, and releases. Martin alone accepts on real devices. This task is PROPOSED until expressly approved; Stage 3 authorization does not approve this particular task.
```

## HANDOFF ChatGPT -> Claude

```text
HANDOFF ChatGPT -> Claude
Task: T-009 spec v1 (PROPOSED / NOT Martin-approved; Gemini first Stage 3 world/render task)
Base commit: 182a09e227049f99e3b46c4a76e3d27671cc1595 (confirmed latest main at drafting)
Earlier user-supplied SHA: e71b59bf75cd55f3a785b1cb52431c08bcea529f (D-026 promotion; superseded by docs-only D-027 commit)
Read: COLLAB.md v3.6 (D-027, preserves v3.5 §4.3 gate), AGENTS.md, TASKS.md qualification Stage 3, DECISIONS D-013/D-021/D-026/D-027, specs/TEMPLATE.md
Context: T-007 PR #59 and T-008 PR #63 are different-category Stage 2 evidence; both Martin-accepted. D-026 explicitly promoted Gemini to Stage 3. This is a proposed individual task, NOT automatically approved by that promotion.
Context: Prefer bounded world detail over judgment-heavy R4 traffic stall fix. Exactly 32 non-colliding zebra stripes in 4 bands at two Midtown intersections, batched into one InstancedMesh; no AI routes, physics, save or renderer pipeline edits.
Context: §4.3 remains a strict prerequisite: Claude first validates baseline/headless/presets, per-risk failure-capable production test, five paired Cannon step runs and real renderer.info.render.calls by PHONE_LOW/TABLET_MED/DESKTOP_HIGH and scene. Physics median ratio <=1.10; nearby draw delta <=+2/+4/+6 respectively, remote +0. Exceed/missing = no merge.
Deliverable: Review the FULL attached T-009-spec-v1.md for geometry viability, instrumentation, baseline stability, safety, risk coverage and perf budget before Martin approval; do not register or start Gemini until Martin explicitly approves this exact spec. After approval: Claude-only docs registration, pre-start test-completeness confirmation, then single Gemini code PR; Claude independently reviews and wires CI/cache during release. No user-device claim without Martin measurement.
SPEC: attached T-009-spec-v1.md (complete proposal, English Antigravity prompt and this handoff).
```
