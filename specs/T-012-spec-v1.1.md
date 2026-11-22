# T-012 spec v1.1 DRAFT — C+ Midtown 街景品質精修試點（兩棟建築＋人行道接合）

> **Status: PROPOSED / NOT MARTIN-APPROVED.** 這份文件是 ChatGPT 設計草案，**不是**實作許可。Martin 的「可以」代表同意朝更完整的街景品質設計前進，Claude 已完成 v1 的 G0 瀏覽器審查（PHONE_LOW／TABLET_MED／DESKTOP_HIGH），其具體幾何勘誤已納入 v1.1；仍尚未完成 COLLAB §3 對 **v1.1** 的規格審查、Martin 明示「批准 T-012 v1.1」與 docs-only 登錄。
>
> **Design baseline:** `cabec9a9b7587745c41457be039b995f2fbdcc49`（GitHub `main`，2026-11-22；實作者開工前必須重新確認最新 SHA）。
>
> **Source of truth:** `COLLAB.md` v3.6、`AGENTS.md`、`TASKS.md`、`DECISIONS.md`（D-013、D-026、D-027、D-031–D-035）、`specs/T-010-spec-v1.1.md`、`specs/TEMPLATE.md`。
>
> **Owner / Implementer:** Codex；**Reviewer & Releaser:** Claude；**Approver & device acceptance:** Martin。**Risk: HIGH**（世界幾何與 draw-call 路徑），**Volume: SMALL**（既有試點內的 2 棟及相鄰人行道視覺層），**Priority: P1**。**Routing:** 視覺比例、立面避讓與場景判斷工作，依 COLLAB v3.6 §5.1 指派 Codex；不得由 Gemini 與 Codex 同時開 PR。
>
> **Branch (after approval):** `codex/T-012-midtown-streetscape-quality`。**Code-PR allowlist:** `index.html` ＋一個新回歸測試 `tools/test/midtown_streetscape_quality_check.mjs`；`.github/`、`sw.js`、`specs/` 及協作文件只有 Claude 可編修。

## 1. Problem, goal, and non-goals

### 1.1 玩家截圖觀察（2026-11-22）

Martin 由已發布的 `MIDTOWN_W` 快速旅行到 T-010 現場拍照。截圖可見：低層 coverage 建築的大片平面單色牆、重複的少量窗格、一樓入口／店面表現不足、建築與亮藍灰色人行道的銜接很薄弱；相較後方高樓與右側較精細的建築，質感落差明顯。小地圖顯示 **Downtown CBD** 是現行 `districtName()` 以 x 座標判斷的結果（並非 T-010 試點未到達），本任務**不**修正地區命名。

T-010 通過的是「六棟、東面窗框／窗台／屋簷、至多兩個新增 InstancedMesh」的技術試點；**並未**承諾形成完整商業街立面。因此 T-012 的設計目的是提升**同一現場的玩家可見完成度**，而不是複製 T-010 的窗框到更多街區。

### 1.2 單一可交付成果

在 T-010 的同一 Midtown 西側試點區域、從 T-011 `MIDTOWN_W` 觀察的**兩棟** coverage 建築之**東向、面向 x≈-240 大道**立面上，建立一套可辨認的 C+ ground-floor／façade-frontage 細節：

1. **真正可辨識的一樓門廊與兩側店面窗**（純視覺、不可進入），減少空白牆面。
2. **垂直牆柱、樓層收邊與底層材質分段**，讓整棟建築呈現樓層與結構比例，而不只是視窗外框。
3. **既有門前裸地跨接鋪面（forecourt apron）、貼著人行道表面的低成本鋪面接縫及街緣收邊**，建立建築到街道的連續感；前庭鋪面仍為純視覺，沒有碰撞體。

風格方向是 **VICE HORIZON VI 既有辨識度 + 更可信的街景尺度**；「30% 自有風格、70% 真實感」僅為審美優先順序，不是可自動驗收的素材比例。

### 1.3 明確不做

不改既有 T-010 的 6 棟選擇邏輯／網格或測試、不重做整座城市、不擴建地圖、不改路寬／柏油／交通標線、沒有新的建築開口／真正可進入商店、不修改道路 collider／Cannon body／世界生成／AI、車輛、相機、存檔 `vh_save`、光照／天空、HUD、i18n、渲染架構、模型／貼圖二進位素材、CDN 或 PWA cache。也不更改先前存在的 windowShader、日夜窗戶及模組化非 coverage 建築。

## 2. Baseline and exact site

1. **已存在結構：** `WORLD.midtownFacadePilot.selected` 是 `buildMidtownFacadePilot()` 在 `WORLD.cityInfill` 中，針對 `coverage === true && district === 'MID' && -420 < x < -240 && -360 < z < -240` 以固定排序取得的 6 棟；這些不是所有未落地候選地塊。選擇結果會隨裝置 preset 有差異。
2. **本任務固定建築選法：** 從前項已存在、已實際放置的 `WORLD.midtownFacadePilot.selected` 取**前兩棟**；不得重新排序、從 `CITY_COVERAGE_LOTS` 虛構候選、改 T-010 範圍或用隨機選擇。兩棟各自的 `(x,z,w,d,h)` 由執行中的資料取得。若某 preset 不能看見或安全裝飾其中一棟，視為 G0 阻擋，不可自行替換第 3 棟。
3. **同一對照場景：** 使用 `MIDTOWN_W` 的現有最終落點（由 T-011 已發布資料實際讀取，**不可假設**恰好是某個估計座標）；Claude 固定日／夜、步行視角及前後相機矩陣，外加 T-010 測試鏡頭 `(-232, 5, -292)` → `(-268, 7, -310)`。後者的可見性必須在 G0 重新確認，不得假裝每個 preset 自動都看得到兩棟。
4. **街道幾何基準（Claude G0 已查證）：** 兩棟的東牆基準 `b.x=-268, b.w=10`，故 `east=-263`（外牆實際立面為 `east+0.06=-262.94`）；既有 x=-240 大道**西側**人行道中央 `sx=-254.5`，寬 5 m，範圍約 `x∈[-257,-252]`，頂面 `y=0.18`。兩者中間 `x∈[-263,-257]` 是 `y=0` 的裸地，**沒有**既有鋪面可直接貼附。`visitAvenueSidewalks(-240, …)` 依路口與曲線道路截斷；Claude 推算該街區有效 sidewalk z 段約 `[-344,-252]`，**此區間仍須由新測試執行 production `visitAvenueSidewalks()` 並以實際輸出確認**，不能硬編碼當作必然。現有 sidewalk 網格已合併成單一 `BufferGeometry`，測試**不得從 scene mesh 反推路段**。所有 sidewalk 表層必須位於真實回傳路段內；前庭鋪面按 §3.3 連接兩棟牆面與其對應人行道邊緣。
5. **規格審查 G0 — Claude 已在瀏覽器獨立查核三個 preset：** `PHONE_LOW`、`TABLET_MED`、`DESKTOP_HIGH` 均檢查過兩棟東立面、裸地前庭及 sidewalk。G0 發現既有裝飾帶佔據 `y=2.99–3.21`，且兩棟高度依 preset 不同（**PHONE_LOW 與 TABLET_MED：22/27 m；DESKTOP_HIGH：17/27 m**）；所有樓層帶必須以**各棟真實 `b.h`** 套用高度上限，不能假定兩棟相同。Claude 在 review／測試時仍須留存各 preset 的 `(x,z,w,d,h)`、實際 production 人行道路段、T-011 到場距離及日夜截圖。若 production sidewalk 段、門面與新增前庭無法合法銜接、兩棟被遮擋或店面配比不能成立，**先要求後續 spec v1.2 + Martin 明示批准，不能由 Codex 默默改範圍**。

## 3. Visual design contract (one façade-frontage visual subsystem)

### 3.1 每棟東面店面，頂緣 y≤2.95 m（避開原有 cornice）

- 面向大道的正面為 `east = b.x + b.w/2`，沿 z 軸的建築面寬 `b.d`；所有新幾何基於該棟實際 footprint／高度，**不是**把固定尺寸塞進不同大小建築。
- 入口在東立面中央，淨視覺門寬 **1.4–1.8 m**、高 **2.3–2.8 m**（實際門底／門框位置應使**最上緣 ≤2.95 m**；例如底緣 y=0.18 時高度最多 **2.77 m**）；兩側至少各一面深色店面玻璃，單面可見寬 **≥1.2 m**，**玻璃／門框／橫梁的最上緣均 ≤2.95 m**，不得使用原 v1 的 3.1 m 上限。保留門框／兩側窗之間 **≥0.15 m** 的立柱，至牆角 **≥0.25 m**。若實際 `b.d` 無法同時滿足，G0 阻擋而非擅改最小寬度。
- 一樓門與玻璃是**貼在現有牆上的視覺面板**，不應偽稱真正可進入的空間；使用深灰、暖褐／灰泥及低飽和玻璃色，不使用大面積高發光材質。門片、窗玻璃、門框的相對進退要至少可辨識 **0.06 m**，所有新立面構件最外緣距**原始牆面 `east=b.x+b.w/2=-263`** **≤0.25 m**（即最東端 `x≤east+0.25=-262.75`；**不能**把 +0.25 從既有 `east+0.06` 立面再算一次）。`buildCoverageFacades()` 原有東面 cornice 的中心 `y=3.1`、高 `0.22`，實際跨 `y=2.99–3.21`，從原牆面外伸至約 **+0.24 m**；新增一樓店面須完全在它下方，不能與其相交／閃爍。原有門片只在 N/S 立面（`face%2===0`），東面尚無門，**不得**在 N/S 面新增重複門。保留現有牆體、交通碰撞與可達性。
- 禁止新增店面文字、商標、售貨互動、門事件、夜間自發光 shader；原本 night windows 完全保留。

### 3.2 二樓以上牆面層次

- 每棟東面兩側各加入一道**窄垂直立柱**（寬 **0.16–0.28 m**；向牆外突出 **0.10–0.22 m**），從 **y≥3.25 m** 起始（避開既有 cornice `y≤3.21`），向上延伸到既有屋頂線下方至少 **0.25 m**，不得擋住原 T-010 窗框和玻璃。
- 樓層分隔水平帶在 **y=4.4、9.0、13.6 m** 中，**逐棟、逐 preset** 只對 `y < b.h - 0.5` 且不壓住現有玻璃／窗台的有效位置建立；`PHONE_LOW`／`TABLET_MED` 的兩棟高度為 **22/27 m**，`DESKTOP_HIGH` 為 **17/27 m**，不可用固定 22/27 代替實際 `b.h`；每道高度 **0.10–0.22 m**、深度 **≤0.22 m**。以真實窗戶中心與 bounding boxes 計算避讓，不允許讓線條穿過窗面。
- 不新增與 T-010 第 1、2 排完全重疊的窗框；不刪除或替換舊 `FACADE.chunks`。兩棟已有的屋頂收邊保持不變，避免加第二道重疊屋簷造成閃爍。
- 建築配色採低對比的暖中性色、局部深灰基座，保留原建築牆體主色；**不能**透過整棟材質換色假裝增加了幾何細節。

### 3.3 門前 forecourt apron ＋相鄰人行道「視覺表層」，不是道路改建

- **前庭跨接鋪面（新增、視覺限定）：** 每棟東牆 `east=-263` 與人行道西緣 `x=-257.0` 之間原本是裸地；在 **`x∈[-262.8,-257.0]`** 鋪設與現有人行道相接的薄型 forecourt apron，**可見頂面固定 `y=0.18 m`，與既有人行道頂面齊平**，不可留懸空中斷或產生高於該高度的台階。每塊 apron 的 `z` 僅能在**其各自建築實際 footprint `[b.z-b.d/2,b.z+b.d/2]` 與 production 有效 sidewalk segment 的交集**內；禁止跨越其他建築前方、路口或曲線道路。裸地仍保持原始地形與碰撞資料，apron 不加 Cannon body、shape 或地面碰撞，不改道路、路面高度或原 sidewalk mesh。apron 納入本 §3.4 的 **同一 3-InstancedMesh／3-material／draw-call 預算**，禁止加第 4 個批次／材質。
- **原有人行道表層：** 僅兩棟面前、真實 `visitAvenueSidewalks(-240, …)` 確認存在的路段；West sidewalk 回傳 `sx=-254.5`，有效 z 段 **預估為 `[-344,-252]`，但必須由 production harness 取得實值**。人行道表層 x 必須在 **[-257.0, -252.0]** 內，z 不超過對應建築 footprint 範圍及有效 segment 的交集。現有 sidewalk 為合併過的 `BufferGeometry`，測試**須執行原 `visitAvenueSidewalks(-240, callback)`** 並以 callback 資料作為唯一判斷來源，不可從 scene mesh 反推或單靠字串 grep。不得覆蓋路口、柏油、斑馬線、車道或路邊既有物件。
- 增加**每 2.0–3.0 m 一道**低對比鋪面接縫，及靠近 x≈-252 的一條細街緣亮暗過渡；**僅接縫與街緣等疊加表層**略高於現有人行道頂面 **0.015–0.035 m**，**forecourt apron 的完整可見頂面仍固定 y=0.18 m、與 sidewalk 齊平**，且不改碰撞／人行走路高度。若相機距離造成 z-fighting，允許在此上下界內微調，不可改原 sidewalk 高度。
- 鋪面線條應略深於現有 sidewalk，避免高反差棋盤紋；不得跨越建築門片區產生突兀「浮空」面板。

### 3.4 性能與生命週期限制

- 所有新增細節統一使用**最多 3 個新的 `THREE.InstancedMesh` 與 3 個共享材質**（建築不透明飾條／深色玻璃與門片／**含 forecourt apron 在內的鋪面、接縫及街緣共用第三批次**），整體最多 **3 個新可提交 draw-call 的 mesh**。單實例可透過 `setColorAt` 變化色彩；無額外獨立普通 Mesh。`castShadow=false`、`roughness ≥0.72`、`metalness≤0.08`，不新增發光／透明混合 pass。
- 新網格在初始化時建立，依現有 `FACADE.chunks` 註冊近距離顯示與隱藏；不可建立新的 LOD manager、`requestAnimationFrame`、每幀 allocations、每幀新計算或 debug interval。原 T-010 的 2 個 mesh 原樣保留。離開試點時新增 draw-call 數必須為 0。
- 所有新物件為純視覺：Cannon `bodies` 與 `sum(shapes)` **delta=0**；`WORLD.cityInfill`、`CITY_COVERAGE_LOTS`、屋頂與道路位置、交通路線、原有玻璃矩陣與保存資料都不得修改。
- 新增只供審查使用的非持久化 debug 資料（例如 `WORLD.midtownStreetscapePilot`）可列兩棟的座標、各 batch instance count 和 mesh references；不得增設 save 欄位。

## 4. Delivery steps and stop gates

| Gate | Owner | Deliverable / pass condition |
|---|---|---|
| G0 — on-site audit | Claude | v1 G0 已由 Claude 在 PHONE_LOW／TABLET_MED／DESKTOP_HIGH 瀏覽器查驗；提供兩棟 `(x,z,w,d,h)`（各 preset 高度 22/27、22/27、17/27）、**門前 x=-263..-257 裸地**、實際 `visitAvenueSidewalks()` 西側路段、日夜基準圖與鏡頭可見性；新 test 必須重驗；不符合即改新版規格 |
| G1 — spec approval | Martin → Claude | Claude review 後 Martin 明確說「批准 T-012 v1.1」；Claude docs-only PR 登錄 `specs/`、`TASKS`、`DECISIONS` 並回報合併後 `main` SHA |
| G2 — benchmark readiness | Claude | 確認 baseline 可取、唯一 code PR 鎖空閒、固定種子／相機／畫質和 `renderer.info.render.calls` 可重測、專屬回歸測試可執行；不滿足不可開工 |
| Implement | Codex | 最新 `main` 建 branch，僅 `index.html` + `tools/test/midtown_streetscape_quality_check.mjs`，PR 不含 docs/cache/CI；production 建議 ≤350 變更行，測試 ≤300 行，超出請 Claude 先評估分段 |
| Review → release | Claude | 重跑功能、變異測試、物理、draw calls、AGENTS、D-013、CI；Claude 單獨接入測試與更新 cache，合併／發布，記錄未量測部分 |
| Device acceptance | Martin | S26 Ultra + Tab S11 開啟 `MIDTOWN_W`，同位置日夜對照；以 `?fps=1` 記錄 FPS，無法確認視覺提升則不算 C+ 目標完成 |

## 5. Regression — failure-capable, production-derived

新增 `node tools/test/midtown_streetscape_quality_check.mjs`；使用既有真實 `index.html` production builder + Three.js/Cannon harness，不可只 grep、抄一份假 builder 或用永久硬編碼建築座標代替實際 `WORLD.cityInfill`。測試至少驗證：

| Risk | Required assertion | Temporary mutation (must FAIL) |
|---|---|---|
| R1 目標選擇漂移 | 每 preset 恰好 2 棟、等於 T-010 `WORLD.midtownFacadePilot.selected.slice(0,2)` 的物件、座標和次序；多次相同 seed 相同 | 改為 `slice(1,3)`／選非 coverage → FAIL |
| R2 店面與樓層比例 | 從真實 instanceMatrix 還原面板／門框／立柱／樓層帶；東面門＋雙窗頂緣 **≤2.95**、立柱起點 **≥3.25**、任何新構件外緣 **≤east+0.25**（從牆面而非 +0.06 起算），且與原有 y=2.99–3.21 cornice 不交疊；樓層帶 `4.4/9.0/13.6` 必須逐棟滿足 `y<b.h-0.5`，兩棟按 profile 為 22/27 或 17/27；不越出 b.d、不蓋窗、不高出屋頂 | 移動門到西面／頂緣改 3.1m／立柱起點改 3.1m／把 `east+0.25` 誤算為 `east+0.06+0.25`／移除 `b.h` 條件 → FAIL |
| R3 sidewalk 安全 | 人行道表層 instance bbox 位於實際 `visitAvenueSidewalks(-240,callback)` 回傳的西側有效段（預估 `[-344,-252]` 須以 harness 實值確認），而非從合併 scene mesh 推測；每棟 forecourt bbox **x∈[-262.8,-257.0]**、z 受該棟 footprint∩有效段限制，頂面 **y=0.18** 並與 sidewalk 邊緣相接；兩類鋪面均無新 collider、不得侵犯路口或既有物件 | 把人行道線移到車道 x=-249／把 forecourt 縮成 x=-260..-258 留缺口／把 apron 頂面改 y=0.35／超出建築 footprint 或有效 z 段／從 scene mesh 假造 sidewalk 段 → FAIL |
| R4 cost / lifecycle | 新增 mesh ≤3、材質 ≤3（**forecourt 必須計在第三鋪面批次內**）、castShadow false、被 `FACADE.chunks` 管理；傳送／切換語言不重建或重複 instance | 改每棟數十個 Mesh／啟用 castShadow／重複生成 → FAIL |
| R5 回歸相容 | baseline 與 PR 的實際 physics body/shape、樓房名單及變換、道路路線、T-010 兩個原 mesh instanceMatrix、既有測試輸出保持不變 | 新增 CANNON.Box／改 T-010 6 棟排序 → FAIL |
| R6 目視品質（Claude 真瀏覽器） | 三 preset、近景日夜固定相機對照，兩棟正面可辨認入口、左右店面玻璃、垂直結構與**頂面 y=0.18、完整銜接到 sidewalk 的 forecourt**；一樓店面不得與 y=2.99–3.21 舊 cornice 打架，上層結構不遮窗；無 z-fighting、穿模、浮空、大面積遮窗，沒有 console errors | 暫時移除新增批次時基準圖必須失去這些特徵；屬 browser visual gate，不等於 Node 自動斷言 |

**測試可靠性：** 新測試在 baseline 上應因新功能不存在而 FAIL；Claude 至少實施 3 種獨立 mutation（包括視覺幾何、選址及 sidewalk）確認能抓錯。不得刪除／削弱舊測試、修改 fixture baseline 或跳過失敗；舊 T-010 regression 仍 PASS。

## 6. Independent measurement — COLLAB v3.6 §4.3

**量測由 Claude 獨立負責**；Codex 負責實作／測試、實際命令／結果及 PR 報告。未驗證不 merge。

### 6.1 Reproducible fixed configurations

- `PHONE_LOW`：390×844（手機 profile），`TABLET_MED`：800×1280（**真正模擬 TABLET profile**，不可把手機橫放誤稱平板），`DESKTOP_HIGH`：1280×800；記錄 UA／profile／quality／postFX／像素比例。
- Seed **5019**，相同 localStorage、同一主程式版本初始狀態、無操作輸入、相同時間／天氣。**Near:** T-010 固定鏡頭 `(-232,5,-292)` 看向 `(-268,7,-310)`；**Control:** `teleportTo(110,650,0)` 並以固定相機朝向測試區域之外。兩場景都驗證日夜，before/after 相機矩陣相同；若不能看到兩棟，先修訂規格而不是在 PR 後調整相機。
- 對基準 commit 與 PR 各用乾淨 context，不能混用快取／不同 shader 狀態；保存實際截圖、preset、場景、樣本、命令、headless 註記。

### 6.2 Physics and world invariants

1. **主要硬門檻：** 各 preset / scene 的 `physicsWorld.bodies.length` 與所有 `body.shapes.length` 總和，各自 baseline vs PR **delta=0**；建築與道路 layout／路線摘要不變。非零直接 FAIL。
2. Claude 以 baseline vs baseline **5 組**校準（交替 A/B 順序）；每次載入及 teleport 後**頁內直接** `__VH.physicsWorld.step(1/60,1/60,3)`，各 sample warmup **≥900 steps**，`performance.now()` 測 **360 steps 的總毫秒數**，不依賴 rAF。校準 ratio 中位數應在 **[0.75,1.33]**，否則 MEASUREMENT BLOCKER、修復環境再跑。
3. PR vs baseline 在完全相同條件下 **5 組成對**、交替 A/B，逐組公布 base ms、PR ms 與 `PR/base`；**median ≤1.25**。若前 5 組超限，補至 **9 組**（保留原組）才判定；9 組仍超標 FAIL。此時間檢查是意外 CPU 回歸防線，不可代替 body/shape=0 的主要門檻。

### 6.3 Renderer draw calls

- Claude 在 Chromium 真實頁面使用 `__VH.renderer.info.render.calls`；每一版／preset／near or control／day or night 取 **≥60 個真實渲染 frame 的中位數**，列 baseline、PR 絕對值及 delta；不得只估算靜態 mesh 數量或把 headless 值冒稱手機 FPS。
- **Near scene max delta:** PHONE_LOW **+3**、TABLET_MED **+4**、DESKTOP_HIGH **+5**；**Control max delta +0**（三 preset、日／夜）；新增 mesh 本身總數 **≤3**。任一超限 FAIL，不得以降低畫質、縮小距離或更換基準圖掩蓋。
- 不新增 material texture network request、物理或渲染 hot path；場景出現 shader error、asset 404、z-fighting 或新 LOD 異常均不得 merge。

### 6.4 Existing checks + real-device gate

- Codex 運行並回報所有 `AGENTS.md` 強制命令：`python3 tools/test/syntax_check.py`；`python3 tools/test/i18n_check.py && node tools/test/i18n_check.mjs`；`node tools/test/hud_check.mjs`；`node tools/test/camera_check.mjs <base SHA>`；`node tools/test/traffic_check.mjs && node tools/test/collision_check.mjs`；`node tools/test/suburb_check.mjs && node tools/test/urban_check.mjs`；另執行 `node tools/test/route_legality.mjs`、T-010 舊測試、新 T-012 測試。每項列 PASS/FAIL/未執行原因。
- Claude 必須獨立重跑、確認 CI 接線由 Claude-owned docs/release PR 完成且 CI 已真正執行；重查 D-013 `main` 保護（需要 PR、enforce_admins、不得 force push/delete、rulesets 狀況）；發布／`sw.js` cache／離線工作模式由 Claude 執行。
- Martin 在 **S26 Ultra** 與 **Tab S11** 用 T-011 到場，白天／夜晚從相同方向和距離各拍 **before/after**。視覺接受至少包括：兩棟的一樓有可辨認門與雙店窗、上層可讀出牆柱與樓層分割、門口至人行道的 forecourt 無裸地缺口、頂面與人行道齊平、不浮空；cornice／店面頂緣無重疊；對照既有 T-010 版本確有清楚提升；沒有窗被擋住或裝飾閃爍。
- 用 `?fps=1` 同畫質、同路線於兩裝置各量 **60 秒平均 FPS ≥30**，報裝置／quality／平均 FPS／最近 60s 最低 1s FPS；沒有數字標記 **device FPS: unmeasured**，不可稱達標。

## 7. Stop conditions and project boundary

1. 若 G0 的兩棟、由 production 函式查出的 sidewalk 段或 forecourt 橋接不符合實際場景、需要修改原牆材質／窗 shader／道路碰撞才能完成、須增加超過 3 個 draw batches、不能公平量測、或目視改善不明顯 → **先退回 spec revision / Claude review，不得擅自擴充**。
2. 若任一 regression、性能、CI、offline PWA、D-013 或 visual gate 未通過，**不得合併**。Claude 最多兩輪 changes requested，仍不符則交 Martin 決定。所有結論區分 code-reviewed、headless-measured 與 device-measured。
3. T-012 對應**已發表的 T-010 和 T-011 後續新任務**；T-010 文件中的 T-012「其他城區擴張」只是未批准 roadmap 預想，不是被登錄的任務。其他城區、材質 atlas、Higgsfield 貼圖以及全面道路美術升級都另立 task，不能塞入此 PR。

## HANDOFF ChatGPT -> Claude

```text
HANDOFF ChatGPT -> Claude
Task: T-012 C+ Midtown Streetscape Quality Pilot v1.1 (PROPOSED)
Base commit: cabec9a9b7587745c41457be039b995f2fbdcc49
Read: COLLAB.md v3.6 §§3,4.3,5; AGENTS.md; TASKS.md;
      DECISIONS D-013/D-026/D-027/D-031–D-035;
      specs/T-010-spec-v1.1.md; specs/TEMPLATE.md
Context: T-010 was technically accepted, but Martin's actual screenshot
         shows the two nearest coverage facades and streetscape still look
         noticeably too simple for the proposed C+ visual direction.
Context: T-012 upgrades only the FIRST TWO existing T-010 selected coverage
         buildings, their east frontage, plus a visual-only forecourt apron
         (x -262.8..-257.0, top y=0.18) to the production sidewalk.
Context: Claude G0 checked PHONE/TABLET/DESKTOP: existing cornice spans
         y=2.99..3.21; storefront top <=2.95, upper posts start >=3.25;
         all protrusion measured from bare east wall x=-263 (not +0.06).
Context: Production visitAvenueSidewalks(-240,callback) must validate the
         west sidewalk z segment (estimated -344..-252); merged scene mesh
         cannot determine valid segments. Building heights differ by preset:
         PHONE/TABLET 22/27, DESKTOP 17/27; floor bands require y<b.h-0.5.
         No physics, roads, or fourth draw batch.
Context: HIGH risk + SMALL volume -> Codex per v3.6. Claude completed the
         in-browser G0 review on all three presets; verify callback-derived
         sidewalk segments and geometry assertions in the test review.
Deliverable: Review the complete attached proposal; verify G0, test
             practicality and physical/draw-call budgets. Register only
             after Martin explicitly approves T-012 v1.1. Do not start a
             code PR or claim a device FPS pass on the basis of this draft.
SPEC: T-012-spec-v1.1-DRAFT.md (this complete attachment)
```
