# COLLAB v3.6 — ChatGPT × Codex × Antigravity (Gemini) × Claude protocol (VICE HORIZON VI)

> **狀態：v3.6，已由 Martin 批准（2026-11-21 19:04，「批准」，依 Claude 起草的 COLLAB-v3.6-DRAFT.md；Martin 決定不經 ChatGPT 交叉審查）。** 起草／登錄：Claude。取代 v3.5；D-027。

## 0. 沿革及本版目的

v3（2026-11-18，D-011）確立固定協作流程；v3.1（D-016）固定各階段、閘門及訊息模板；v3.2（D-018）建立第二實作者；v3.3 曾暫停第二實作者；v3.4（D-020）以 Antigravity Remote Agents 恢復 Gemini，**僅准低風險任務**。

v3.5（D-021）建立可審計的三階段能力升級制度，使 Gemini 在通過實績與測試閘門後，可被指派與 Codex **同等範圍**的程式任務；但**同等範圍不等於自動獲得任務、不等於較少測試，更不等於可以同時開第二個程式 PR**。實績：T-006（階段 1，PR #53）、T-007（階段 2，PR #59）、T-008（階段 2，PR #63）皆已由 Martin 實機驗收；Martin 於 2026-11-21 批准 Gemini 升至階段 3（D-026）。

**v3.6 的新增政策目標**：在 Gemini 已達階段 3 的前提下，加入**任務路由規則**（§5.1）與**分段任務規則**（§5.2），使耗 token 的大量、低風險、可測試的工作預設由 Gemini 承擔，需要判斷力的高風險小任務預設由 Codex 承擔，並把審查瓶頸（Claude）納入考量。**v3.6 不放寬任何既有閘門。**

### v3.6 變更摘要（相對 v3.5）

1. **新增 §5.1 任務路由規則**：依「風險」與「量」兩軸決定預設實作者；**風險優先於量**。
2. **新增 §5.2 分段任務規則**：大型任務必須由 ChatGPT 拆成分階段小任務／小 PR，附建議上限及每段獨立回歸測試。
3. **§5 路由表**更新為與 §5.1 一致（Gemini 已達階段 3 的現況）。
4. **清理 v3.5 過渡性文字**：移除「僅在 v3.5 正式生效後」、「T-006 待批准」、「Ready for Codex 改名須同 PR 同步」、`Gemini qualification` 範例中的「pending」等已過期的描述；T-006／T-007／T-008 改為歷史實績。
5. **更新訊息模板**（§7）與批准用語（§7.4、§4.4）為 v3.6；§11 ChatGPT 專案設定文字更新為現況。
6. **未改動（逐字保留語意）**：唯一共享程式 PR 鎖、一任務一實作者、只有 Martin 明示才可升降階、階段 2→3 門檻（連續 2 項不同範疇、零違規、實機驗收）、§4.3 階段 3 測試閘門與 Claude 獨立量測、D-013 `main` 保護逐 PR 重驗、`sw.js`／協作文件／CI 接線僅限 Claude。

Martin 在 ChatGPT、Claude、Codex 與 Antigravity 間傳遞訊息；AI 不共享其他 AI 的私人對話。**GitHub repo `martinhsu2010-blip/Martin-Hsu` 是唯一共同事實來源**。當 repo 規則與未批准草案衝突時，repo 現行規則優先。

## 1. 角色與永久權限

- **ChatGPT（設計／分析）**：提出功能設計、數值、規格、效能預算、bug 分析及設計審查；不直接撰寫遊戲程式碼。所有程式任務在規格及 `TASKS.md` 均標註 `Implementer: Codex|Gemini` 與選擇理由。
- **Codex（實作者）**：預設實作人，依已批准規格完成一整項任務、執行檢查、從最新 `main` 開 `codex/T-xxx-name` 分支並提交 PR；不得合併、直推 `main`、修改 `sw.js` 或協作文件。
- **Antigravity／Gemini（分階段授權實作者）**：於 `antigravity.google.com` 的 Remote Agents 執行整項任務，分支 `gemini/T-xxx-name`（工具改名須如實記錄）；其**可觸及的系統依 §4 與 `TASKS.md` 中 Martin 批准的現行階段**，其餘 PR、CI、誠實報告與禁止修改檔案規則與 Codex 相同。階段以 `TASKS.md` 的 `Gemini qualification` 為準；沒有該紀錄就視為階段 1。
- **Claude（獨立審查／整合／發布）**：從 GitHub 讀取 PR 及規格，獨立跑測試、對照 baseline、檢查差異與效能、提出 review，經適當核准後 squash merge／發布。**只有 Claude 修改 `sw.js` CACHE 及協作文件**（`COLLAB.md`、`AGENTS.md`、`HANDOFF.md`、`TASKS.md`、`DECISIONS.md`、`LOG.md`、`specs/` 等）；Claude 自身修改仍須走 branch → PR → merge。小缺陷修復須公開說明；較大修復退回原實作者。
- **Martin（Owner／最終閘門）**：決定規格、優先順序、每次 Gemini 升階／降階和任務歸屬；在實機上驗收並以自己的話批准。只有 Martin／Claude 可以執行合併；Codex／Gemini 不合併。

以上角色**不因 Gemini 升級而改變**。尤其 Claude 不得將自己的獨立效能驗證轉交實作者自證。

## 2. Repo 文件與同步

Repo root 是唯一正式位置；忽略舊 `records/` 路徑。

- `COLLAB.md`：現行協作協定。
- `AGENTS.md`：兩名實作者共同的強制限制，升階時由 Claude 配套更新，禁止其與 `COLLAB.md` 相矛盾。
- `specs/T-xxx-spec-vN.md`：經 Martin 批准後原文存檔，格式以 `specs/TEMPLATE.md` 為準。
- `TASKS.md`：任務唯一狀態／單一 Owner／實作者／審查／驗收紀錄。
- `DECISIONS.md`：不可覆寫的決策事件；D-013 保護 `main`，D-021 是 v3.5 的三階段授權，D-023／D-026 是 Gemini 的升階紀錄。新規則經批准應另增新決策並標明取代的範圍；不得改寫既有決策歷史。
- `LOG.md`、`HANDOFF.md`、`CLAUDE.md`、`tools/`、`.github/`：既有用途保持不變。

開始每一項任務前，讀取 GitHub 上的 `COLLAB.md`、`TASKS.md`、`DECISIONS.md`、`AGENTS.md` 及相關 spec；Pages 可能有部署延遲，不能用未刷新頁面代替 GitHub 最新檔案。

## 3. 固定流程（每個功能都必經，不得跳級）

| 階段 | Owner | 成果與下一關閘門 |
|---|---|---|
| 1. Idea | Martin／提案人 | `TASKS.md` Inbox；Martin 同意進入設計 |
| 2. Design/spec | ChatGPT | 一份完整獨立的 `T-xxx-spec-vN.md`，含 `Implementer`、當前 Gemini 階段、回歸測試、風險與硬限制 |
| 3. Spec review | Claude | 審查可行性、手機成本、存檔相容性、任務範圍與測試可行性；Martin 明確說「批准 T-xxx vN」才進下一步 |
| 4. Register | Claude | docs-only PR 將完整核准規格原文寫入 `specs/`，同步 `TASKS`／`DECISIONS`；合併後報告 main SHA |
| 5. Implement | 指定 Codex 或 Gemini | 單一實作者執行整個 task，在獨立分支開**唯一**程式 PR、跑 CI 及規格測試 |
| 6. Review | Claude | 獨立 review、執行指定驗證及效能比較，回報 approve／changes-requested／reject；修正回合最多兩輪後交由 Martin 決定 |
| 7. Release | Claude | 合併 PR、調整 `sw.js` CACHE、確認部署／離線、更新 `DECISIONS`／`TASKS`／`LOG`／`HANDOFF` |
| 8. Accept | Martin | 用指定實機驗收並留下數值、畫面及裁定；通過後才可啟動下一個程式任務 |

**嚴格保留：**

1. 任一時間**最多一個尚未合併的程式 PR**，Codex 和 Gemini 共用同一把鎖；docs-only PR 可另行進行，但不得意外變更遊戲檔案或使程式 PR 的 baseline 失效。
2. **一個任務由一個實作者從頭做到尾。** 不在同一 PR 中途切換、不拆分實作給兩名 AI；下一個任務才可改派。
3. 分支起點是最新 `main`；`main` 受 D-013 保護：只能透過 PR，包含管理員；不可 force-push、不可刪除。PR 若離開當初 baseline，必須重新確認並依需求 rebase 與重跑測試。
4. 程式 PR 的 `sw.js`、協作文件以及規格檔案一律不許實作者修改，這些由 Claude 的獨立 docs／release PR 處理。
5. `index.html` 是單檔 Three.js + cannon-es 遊戲；保持既有存檔 `vh_save`、離線 PWA、單一 renderer 與行動裝置性能優先。除非核准規格明定，任何任務不增加 CDN 或執行時網路依賴。
6. `Verification` 清楚區分 `designed`、`code-reviewed`、`headless-measured` 和 `device-measured`；Claude 的 headless 數據**不得**冒充 Martin 實機數據。

## 4. Gemini 三階段授權制度（D-021 起生效）

**起始狀態：階段 1；現況以 `TASKS.md` 為準（截至本草案：階段 3，D-026）。** 階段紀錄由 Claude 在 `TASKS.md` 的獨立 `Gemini qualification` 區塊或等效明確欄位維護，至少包含 `Current stage`、核准人、日期、證據 PR、測試結果、最新一次回退原因。**Claude 可建議升降階，但只有 Martin 明確批准升階。** 降階若命中保護條件立即停止新任務，交 Martin 確認後由 Claude 登記；不得藉由選擇另一 task 繞過限制。

### 4.1 階段 1 — 限定文字與純靜態 UI（試跑）

**允許整項任務：** `STRINGS`／`tr()` 既有中英文字串、翻譯、任務文字與描述、純靜態 HUD／選單 CSS；只改顯示文字或沒有行為變更的樣式。**（歷史：首項試跑為 T-006 一行字串修改，PR #53，已驗收。）**

**禁止：** JavaScript 邏輯變更、事件、DOM 結構行為、儲存、物理／碰撞、車輛、世界生成、交通／警察 AI、渲染及效能，以及新增檔案／資產。試跑必須是完整獨立任務，不得藉「順手清理」擴大修改。預設程式 PR 僅改 `index.html`。

**階段 1 驗收要求：** PR diff 僅包含核准行；分支與 PR 模板正確；`syntax_check`、`i18n_check`、受影響的 `hud_check`／既有回歸測試 PASS；Claude 核對原始檔案、實際修改、功能及誠實報告，並確認未觸碰 `sw.js`／文件。發布後由 Martin 實機驗收。階段 1 的試跑任務須具體查核**恰好核准的行數**，不得因工具生成大面積重排。

**升至階段 2（缺一不可）：** 該階段 1 試跑任務的規格先獲 Martin 核准；符合階段 1 的 PR 經 Claude 獨立審核通過、CI 綠燈、正式發布、Martin 實機接受；無越權檔案、無多餘 diff、無不實測試宣稱、無規則違反；Claude 記錄 PR/SHA/驗收依據並提出升階建議；Martin **另外明確批准「Gemini 升至階段 2」**。試跑通過本身**不等於自動升階**。

**退回條件：** 階段 1 如發生越權修改、繞過分支保護／PR 鎖、隱瞞失敗或不實量測、重複無法遵守單行 diff，立即**暫停 Gemini 實作資格（階段 0／paused）**；由 Codex 承接後續尚未開始的任務。若只是可修正的一般失誤，依原 PR 最多修正兩輪；無法過關則停止該 PR，仍停在階段 1，試跑重試需重新批准或重新安排。恢復資格須 Martin 明確同意並重新試跑階段 1。

### 4.2 階段 2 — 完整、但不涉及高風險系統的新功能

**開放：** 可獨立完成整個新功能任務，包括選單、設定（**不更改持久化存檔結構**）、任務／互動系統、一般 HUD 行為及 UI 資料流；允許為核准功能修改相關 JavaScript／HTML／CSS，並依測試需求新增或更新 `tools/test/` 自動測試碼。範圍要能從一份 spec、單一 PR 清楚驗收；不得碰觸未列入規格的系統。

**持續禁止：** `cannon-es` 物理、碰撞、車輛操控、世界生成／地形／道路、交通／警察 AI、renderer／draw calls／渲染效能關鍵路徑、存檔格式／`vh_save` schema 的新增、刪除或變更（即使只新增帶預設值欄位也須另行歸給 Codex，或等階段 3）。涉及前述任一項的完整任務**轉給 Codex**，不得拆成 UI 與核心兩個同時進行的 PR 來迴避限制。

**階段 2 首項任務強制試跑：** 升至階段 2 後第一個 Gemini 程式任務一律標為「Stage 2 trial」，限定**單一、小範圍、可獨立驗收的功能**，不涉及任何持久化讀寫、存檔欄位或遷移；不得以多功能或跨系統整合當作首項試跑。Claude 必須採高於一般階段 2 的嚴格審查，逐項檢查 diff、規格、測試有效性、回歸及裝置結果，並於 PR review 明寫「Stage 2 trial：通過／未通過」及證據。只有該試跑通過 Claude 審查、完成發布並由 Martin 驗收後，才可安排後續階段 2 任務；通過的試跑若符合完整任務定義，可列為升階所需的第一項證據。

**階段 2 每個 PR 的閘門：** 已核准的完整獨立 spec、至少一項能在未來抓到這次功能回歸的自動測試（須有可辨識的失敗斷言；不接受只有 smoke test）、AGENTS 所列檢查、Claude 的功能/PR 範圍審核、必要的 headless browser 與 Martin 實機驗收。若新增 `tools/test/` 測試碼，僅視為測試程式；不能修改協作文件或 CI 治理設定。Claude 需獨立重跑測試，並檢查新測試是否真的測得到錯誤。**階段 2 驗收另須確認：新增或更新的 `tools/test/` 測試已由 Claude 在該功能 PR 合併／發版流程中的 docs／release PR 接入 `.github/workflows/pwa-cache-check.yml`，並確認 CI 實際執行且通過；不可只在實作者本機執行。**

**升至階段 3：** 一律要求 **連續 2 項不同範疇**、完整完成的階段 2 功能任務，各自具完整單人 PR、Claude 獨立測試／審查、發布、Martin 實機驗收，且期間**零違規、零未解決回歸、零不實報告**。**沒有僅憑 1 項任務升階的例外。** 升階後首次高風險任務仍需單獨評估測試完備性。不得因完成任務數而自動升級，仍須 Martin 明確批准。

**退回至階段 1：** 任一高風險禁區越權、額外修改 `sw.js`／文件、違反 PR 鎖／任務單人所有權、不實測試或效能宣稱、造成未處理的重要回歸，立即凍結新 Gemini 指派並退回階段 1（嚴重者暫停）。一般可修正 bug 允許同 PR 最多兩輪；兩輪仍無法驗收、或連續兩次階段 2 任務需要重大重寫時，回退階段 1，重新積累資格。已進行中的失敗 PR 由 Claude 決定關閉或要求同實作者修正，不得將另一名 AI 直接加入該 PR。

### 4.3 階段 3 — 與 Codex 同等系統實作範圍，測試優先

**允許：** 視核准 spec 及 `AGENTS.md`，Gemini 可承擔與 Codex **相同類型**的程式任務，包括物理、碰撞、車輛操控、道路／地圖／世界生成、交通／警察 AI、渲染效能及存檔格式遷移。這不放寬共通硬限制：不得破壞既有存檔、離線、行動裝置成本或版本管理；不得擅改未批准規格。

**每一項階段 3 任務的開工前置條件（缺一不可）：**

1. Martin 核准的 self-contained spec 清楚列出 baseline SHA、受影響系統、場景／畫質／裝置配置、**每個風險的回歸自動測試**、量化接受值及超標處理方式。
2. 測試必須能**抓出可預期的回歸**：至少包含變更前後相同輸入的固定種子／可重播情境；測試中的 assertion 要對準目標錯誤。需要的新測試可列入該任務程式 PR，但不可以放寬舊有測試、修改比較基準或刪除失敗案例來換取 PASS；Claude 查閱測試 diff。
3. 對於涉及物理、渲染或世界的任務，spec 必須包含可在 Claude 環境重跑的 headless／瀏覽器量測流程。**即使主要功能不直接改變物理或 draw calls，Claude 也要抽查兩項指標以確認沒有意外回歸。**
4. 在 Claude 確認測試可執行、任務所需 baseline 可取得前，Gemini 不得啟動高風險 PR。若無足夠可自動判定的回歸測試，此任務**不可指派給 Gemini 階段 3**；可改由 Codex 或先規劃獨立測試設施任務，不能以口頭保證代替。

**Claude 獨立驗證，採 T-005B 的量測紀律：**

- **物理**：對同一主程式 baseline 與 PR、相同 seed／場景／畫質進行至少 **5 組成對 `cannon-es` step / headless 量測**，逐組公布時間及相對比率，使用中位數判定；至少含 `PHONE_LOW`、`DESKTOP_HIGH`，相關場景另依 spec 增加。容許上限須在該任務已批准 spec 中明訂；**T-005B 的 1.35 倍是參考方法，不自動套用所有未來任務**。如 spec 未設定可驗收上限則不得放行。
- **Draw calls**：使用相同相機位置、場景、畫質與 renderer 畫面狀態，比較 baseline / PR 的 `renderer.info.render.calls`，報告每個場景和 preset 的絕對值、增減及上限；至少 `PHONE_LOW`、`DESKTOP_HIGH`，必要時補 `TABLET_MED`。結構估算不能冒充實際 Chrome renderer 讀數。上限由已核准 spec 個別制定。
- **其他回歸**：每個任務須執行 AGENTS 檢查及專屬測試，審查離線 PWA、載入錯誤、存檔相容性、碰撞與主路徑的相關行為；`?fps=1` 的手機讀數由 Martin 實機提供，與 headless 數字分開報告。**階段 3 驗收須確認：該 PR 新增或更新的 `tools/test/` 回歸測試已由 Claude 在相應合併／發版 docs／release PR 加入 `.github/workflows/pwa-cache-check.yml`，且 CI 確實執行並通過；未接入不得驗收。**
- **獨立性**：Claude 必須自行取得 baseline、重跑指令、記錄命令／preset／樣本／結果；不得只採信實作者 PR 的「PASS」字樣。結果缺失或超標則不 merge，退回修改；不因 Gemini 升階而豁免。

**維持階段 3 的條件：** 每項均有可重現測試與獨立量測，按一般流程開唯一 PR、通過 Claude review、正式發布並經 Martin 驗收；出現 P1 回歸必須修復與復測才能接受。

**退回至階段 2：** 任一高風險 PR 缺少規定的可重現回歸測試、Claude 無法獨立測得物理/draw calls 仍企圖合併、出現不可解釋的效能超標、嚴重物理／存檔／離線回歸、越權改動或不實測試宣稱，立即停止開新高風險任務並由 Martin 決定退回階段 2；有意繞過分支保護、PR 鎖或偽造證據則暫停全部 Gemini 指派。一般 bug 依兩輪 review 修正；兩輪仍失敗或連續兩個階段 3 PR 有重大品質退件，退回階段 2。**已完成任務不回溯撤銷**，但未開始的任務必須重新路由。

### 4.4 共通升降階紀錄與權限安全

- 只有 **Martin 的獨立明示授權**可以升階；Claude 的建議、綠燈 CI、試跑完成都不是授權。固定用語：「批准 Gemini 升至階段 N，依 COLLAB v3.6，證據 PR #...」（v3.6 生效前沿用 v3.5 字樣）。升降階都由 Martin 以此句式明示；Claude 不以「可以」「好」之類模糊回應代為記錄，會先請 Martin 說出固定句式。
- 執行前，Claude 在 docs-only PR 同步 `COLLAB.md`、`AGENTS.md`、`TASKS.md` 的許可範圍及級別，並於 `DECISIONS.md` 追加決策事件；**規則在 docs PR 合併前不可先行擴權**。
- 禁區、未授權分支操作、偷偷修改 baseline、刪除測試、不實測量屬 hard violation；立即凍結新增 Gemini 任務，交 Martin 裁決。普通可修正缺陷不等同違規，但仍受到 review 回合限制。
- 若 Antigravity 平台暫停、不支援 repo／PR、權限設置不可確認，該次任務**不得**自行轉成未受管理的另一個代理平台。v3.4 的聊天前後對照替代法只可用於經核准的階段 1 微小修改，且由 Claude 明記實際代套者；不得用它執行階段 2/3。

## 5. 任務分配：路由、分段與排隊

**共用鎖代表 Codex 與 Gemini 不會同時寫程式；分工的價值是依風險與工作量選擇適合的實作者，並在一方額度不足或平台不可用時有替手，而不是兩名實作者並行加速。**

### 5.1 任務路由規則（v3.6 新增；Gemini 已達階段 3 為前提）

每份 spec 與 `TASKS.md` 條目都必須標明 `Implementer`、**Risk（high／low）**、**Volume（large／small）**與一行選擇理由，由 ChatGPT 提出、Claude 審查、Martin 批准。預設規則：

1. **量大、低風險、規格明確、可自動測試 → Gemini。** 例：大量內容／資料表、批次 i18n、有測試覆蓋的機械式重構、測試撰寫、整個 UI／HUD 系統。
2. **量小、高風險、靠判斷力 → Codex（預設）。** 例：物理手感、碰撞、交通／警察 AI 調校、存檔格式變更。Gemini 僅在已達階段 3 **且**滿足 §4.3 全部前置條件與 Claude 獨立量測時才可承擔，且須在 spec 的選擇理由中說明為何不給 Codex。
3. **量大且高風險 → 不整包派發。** 由 ChatGPT 依 §5.2 拆成分階段小任務，每個小任務各自套用規則 1 或 2。
4. **風險優先於量。** 任務只要觸及任一高風險系統（物理、碰撞、車輛、世界生成／地形／道路、交通／警察 AI、renderer／draw calls／效能關鍵路徑、存檔／`vh_save` schema），即屬高風險，適用規則 2／3 與 §4.3；不得把高風險部分藏在大型低風險任務內，或拆成同時進行的 PR 迴避。
5. **預設不是永久排他。** Martin 可逐項改派；改派不放寬閘門。分類爭議由 Claude 在 spec review 提出，Martin 裁決。

### 5.2 分段任務規則（v3.6 新增；Claude 審查是瓶頸）

1. **大型任務必須由 ChatGPT 拆成分階段任務**（`T-xxx-P1`、`P2`…或獨立任務編號），每一段是**一個任務、一個實作者、一個程式 PR**，依序經 §3 全流程（spec 批准、登錄、實作、Claude 審查、發布、Martin 驗收），並仍受唯一程式 PR 鎖約束；各段**不得並行**。
2. **每段必須可獨立驗收與發布，且遊戲在每段之後都處於可玩狀態。** 不接受「第 3 段完成前功能不能用」的拆法，除非該段的未完成部分在遊戲內不可見。
3. **每段各有自己的回歸測試**（可辨識的失敗斷言，由 Claude 接入 CI），並重跑 AGENTS 全套檢查；不能把測試延到最後一段。
4. **建議的初始大小上限（建議值，Martin 批准後可調整；超過須在 spec 說明理由並經 Claude 同意）：**
   - 一個程式 PR 的 `index.html` 邏輯／標記／樣式變更：約 **600 行以內**（新增＋修改）；
   - 純資料表／i18n 字串批次：約 **800 行或 150 個 key 以內**，且須有結構性測試（key 兩語一致、無缺漏）；
   - 一段只涉及**一個系統邊界**；
   - Claude 一次審查可在一輪內完成為目標；若某段預期超出，應再拆。
5. **每一段各自套用其路由規則**：同一大型任務的不同段可分給不同實作者，但**一段只有一位實作者**，且不得兩段同時有未合併程式 PR。
6. 拆分只改變任務粒度，**不改變任何閘門**：階段 3 的每個高風險段仍需 §4.3 前置條件及 Claude 獨立量測。

### 5.3 建議分工表（與 §5.1 一致；不是永久排他制度）

| 任務系統 | 預設實作者 | 原因與例外 |
|---|---|---|
| 世界生成、地形道路、城市／郊區、碰撞、車輛動態、交通／警察 AI 的**調校與判斷** | Codex | 高風險、靠判斷；Gemini 僅依 §5.1 規則 2 |
| 上述系統中**量大、可測試、機械式**的子工作（如大量資料表、測試撰寫） | 依 §5.2 拆出後給 Gemini | 須有結構性測試與 Claude 獨立量測；高風險部分仍歸 Codex |
| UI 字串、翻譯、HUD／選單／Game Hub／設定／任務面板／一般遊戲新功能 | Gemini | 變更隔離、可回歸；整項任務一旦碰高風險禁區，依規則 4 改派 |
| 引擎整合、渲染效能、存檔 schema | Codex（預設） | 需固定種子測試、paired 物理與實際 draw call 比對；Gemini 依規則 2 |
| 規格、設計審查、素材授權／美術流程 | ChatGPT 設計；Claude 審核／文件 | 與程式 PR 並行準備，但不破壞唯一程式 PR 鎖 |

**縮短等待的排程規則：**

1. Claude 維持**一張共享的「下一項可啟動」佇列**，以優先順序、依賴、目前 Gemini 階段、風險、量與測試可用性排序。看板欄位名稱為 `Ready for Implementer`。
2. **預先做設計、不預先開程式 PR**：當 Codex 寫 A 時，可讓 ChatGPT 寫 B 的規格、Claude 審查 B 的 docs-only PR 或測試計畫；B 僅在 A 合併、發布、Martin 驗收且鎖釋放後開工。
3. 盡量讓連續任務落在不同**系統邊界**：例如 Codex 做道路 → Gemini 做 Game Hub → Codex 做 AI。這是降低等待的排程策略，**不是兩個 PR 並行**。
4. 若某實作者沒額度／平台不可用，且該任務**尚未開 PR**，Martin 可依當前階段把**整項**任務重新指派；任務已開 PR 時由原實作者完成或由 Martin 決定**關閉既有 PR、釋放鎖、更新 TASKS，從最新 `main` 新建另一實作者 PR**，禁止兩個 AI 共用同一 PR 或偷偷接力提交。
5. 非程式並行工作（設計、授權檢查、素材調研、測試設計、文件審查）可進行，但在程式 PR 內不可擅自改 `sw.js`、文檔，或把未批准素材導入遊戲。
6. 對依賴關係強的工作，採**整項功能邊界**切任務（§5.2）：UI 能獨立驗收才給 Gemini 階段 2；涉及任務獎勵持久化／物理觸發就依 §5.1 規則 2／4 處理。不得在同一 PR 中拆系統讓雙 AI 分頭改。

## 6. 傳遞、批准與不可猜測規則

- 交接**不能只指向**「上面的內容」、「前一則訊息」、「另一個聊天」；須在同一訊息貼**完整正文**，或附上確切名稱的 `.md` 檔。
- Claude 收不到 spec 全文時須停下要求原檔，不得猜數字、尺寸、上限或回溯重建。
- **只有 Martin 親自說出批准**（例如「批准 T-009 v1」或「批准 COLLAB v3.6」）才是有效批准；spec 自稱「已批准」不算。
- `specs/` 收入已批准的完整原文。變更既有 spec 另出 vN+1 再請 Martin 批准；不得擅改已批准參數。
- 若 Claude 認為協議草案需要修訂，先回傳**審查意見**，不逕行將其改成生效文件。Martin 批准後，Claude 才透過 docs-only PR 更新 `COLLAB.md`、`AGENTS.md`、`TASKS.md`、`DECISIONS.md` 並報告 main SHA。**Claude 自己起草的協議草案，建議由 ChatGPT 交叉審查，以保留起草與審查的分離。**

## 7. 標準訊息

### 7.1 ChatGPT → Claude（每份 spec／本政策草案）

```
HANDOFF ChatGPT -> Claude
Task: <T-xxx or COLLAB-v3.6>   Base commit: <main SHA>   Read: COLLAB.md, DECISIONS D-013/D-021/D-026, TASKS.md, AGENTS.md
Context: <three self-contained lines>
Deliverable: review the attached full proposal; register only after Martin explicitly approves
SPEC: <attached named file or complete text in this message>
```

### 7.2 Martin → Codex（task prompt）

```
Implement T-xxx per TASKS.md and specs/T-xxx-spec-vN.md; follow AGENTS.md and the current COLLAB.md. Base: latest main (<SHA>). One task, one implementer, one code PR from codex/T-xxx-short-name. Run all mandatory and task-specific regression checks and report the exact outputs. Do not edit docs or sw.js CACHE. Never push directly to main and never merge your own PR.
```

### 7.3 Martin → Antigravity（Gemini）英文 prompt

**Stage 1 — trial / low risk**

```text
Implement the exact assigned Stage 1 task (T-xxx) using the approved spec in specs/ and TASKS.md. Read COLLAB.md, AGENTS.md, DECISIONS.md and the task spec before editing. Base your branch on the latest main (<SHA>) and use the assigned gemini/T-xxx-short-name. One task, one implementer, one PR; if another code PR is open, do not start.

Your current authorization is Gemini Stage 1 only: localized UI strings, wording, and purely static CSS. Change exactly the approved lines and nothing else. Never change game logic, physics, collisions, vehicles, traffic/police AI, world generation, rendering/performance, save data, sw.js, project documentation, or unrelated code. Do not reformat files. Run the applicable syntax, i18n, and UI checks. Open a PR to main with the repository template, listing the exact changed lines, commands, actual test results, and tests not run. Never push to main or merge. If anything requires a broader edit, stop and report the blocker without opening an out-of-scope PR.
```

**Stage 2 — whole non-critical features (only after a recorded promotion)**

```text
Implement the single approved task T-xxx according to TASKS.md, its complete spec and AGENTS.md. Confirm that the current Gemini authorization recorded in the repository is Stage 2 or higher. Start from latest main (<SHA>), on gemini/T-xxx-short-name; open one code PR only if the shared PR lock is free. Own the whole feature yourself. Stay strictly inside the approved UI, menus, settings, mission/interface scope.

Do not edit cannon-es physics, collisions, vehicle control, world/terrain/road generation, traffic/police AI, renderer/draw-call/performance hot paths, or the vh_save schema. Do not edit sw.js or project documentation. Add or update targeted automated regression tests in tools/test/ where the spec requires them; do not weaken existing tests. Run all AGENTS checks plus task-specific tests and report actual results and limitations. Stop before making any forbidden cross-system change. Never push to main or merge. If the scope cannot be completed without forbidden changes, report the blocker so Martin and Claude can reassign the entire task.
```

**Stage 3 — Codex-equivalent scope (only after recorded promotion and test gate)**

```text
Implement the single approved task T-xxx from TASKS.md and specs/T-xxx-spec-vN.md, following AGENTS.md and COLLAB.md. Confirm the repository records Gemini Stage 3 approval by Martin. Base on latest main (<SHA>), use gemini/T-xxx-short-name, and respect the one-active-code-PR lock. You own the entire task; do not hand off part of the implementation to Codex.

Before coding, verify that the approved spec provides reproducible automated regression tests, fixed baselines, and explicit acceptance budgets for physics and draw calls. If tests, baselines, or budgets are missing, STOP and report the blocker; do not open a high-risk PR. Implement only the approved scope, preserve save compatibility and offline PWA behavior, and never edit sw.js CACHE or collaboration documents. Run all AGENTS checks and task-specific tests; attach commands, exact results, baseline SHA, scene/seed/preset details, and any test limitations to your PR. Do not weaken tests, alter comparison baselines to pass, or claim device measurements from headless runs.

Claude must independently repeat the T-005B-style paired physics measurement and renderer.info.render.calls comparisons; your own numbers are supporting evidence, not the release gate. Never push to main or merge the PR yourself. Stop and report any regression or out-of-scope requirement instead of hiding it.
```

### 7.4 Martin → Claude（review／批准）

- Review request: `PR #n ready`（可補 task id）。
- Task spec approval: `批准 T-xxx vN`，同一對話附完整 spec。
- Protocol approval: `批准 COLLAB v3.6`，同一對話附**這份完整草案**，或貼完整正文。
- Gemini promotion: `批准 Gemini 升至階段 N，依 COLLAB v3.6，證據 PR #...`。
- Claude 給 Martin 的各階段回報：一句話交代操作、PR／main SHA／裁定、Martin 下一步；未經 Martin 實機回報不得稱「device-measured」。

## 8. `TASKS.md` 與紀錄格式

既有欄位維持：`ID, Title, Owner (exactly ONE), Implementer (Codex|Gemini), Reviewer, Priority, Depends on, Base commit, Branch/PR, Acceptance, Verification, Output`。`T-xxx-spec` 需附 `Required Gemini stage`（若 Gemini 實作）、至少一個量化／可自動測的回歸接受條件。程式 PR 一次只有一個。

`TASKS.md` 維護獨立的 `Gemini qualification` 區塊，格式如下（實際內容以 `TASKS.md` 為準）：

```text
## Gemini qualification
Current stage: <1|2|3|paused>
Last approved by Martin: <date time, his exact words, promotion N -> M>
Evidence PRs: <PR numbers with task id, stage, acceptance state>
Promotion candidate: <none | stage N eligible, awaiting Martin>
Rollback / blockers: <none | reason>
```

往後任何升降階須記錄證據 PR、review verdict、CI、release、Martin 驗收。具體證據在 GitHub 可重查。每個任務條目另含 `Risk`（high／low）與 `Volume`（large／small）欄位（§5.1），分段任務標明 `Phase`（§5.2）。

## 9. 決策紀錄、CI 與發布

- `DECISIONS.md` 仍採 `proposed → agreed → implemented | dropped`、append-only；Claude 在 Martin 批准 v3.6 後增加**新編號**決策（預計 D-027），載明新增的路由與分段規則，不改寫既有事件。升階／降階各追加事件或在 `TASKS` 保留可追蹤歷史。
- D-013 的 `main` 保護不變：所有變更（包括 Claude 本人）走 PR；不可 force push 或刪支。管理員沒有例外。**Antigravity Remote Agents 預設可不經使用者逐項確認就執行指令；阻止代理直接改動正式分支的唯一技術保險是 D-013 的 `main` 分支保護。Claude 每次審查 Gemini PR，必須重新查驗 GitHub `main` 的保護設定：要求 PR（required pull request）、`enforce_admins=true`、禁止 force push、禁止刪除、repository rulesets 為空；將實際查核結果與時間／來源記錄在該 PR review。任一設定不符、無法確認或被更動，均視為 hard violation，暫停 Gemini 任務及合併，交 Martin 處置。**
- `sw.js` `PRECACHE` 內任何遊戲檔案變更，都要由 Claude 發布時更新 `CACHE`。PR 對版本提醒、`main` 對版本檢查的現有規則保持。
- 現有 `tools/test/syntax_check.py` 與 `.github/workflows/` CI 不縮減；每個系統的既有測試及新規格指明的測試要執行，不能為讓 Gemini 合格而放寬測試。**CI 執行清單寫在 `.github/workflows/pwa-cache-check.yml`；Codex／Gemini 階段 2/3 如在程式 PR 新增或修改 `tools/test/` 回歸測試，必須在該 PR 內提交可重跑測試，由 Claude 在 review 時獨立跑過；該 PR 合併／發版時，Claude 在自己的 docs／release PR 將新測試接入 workflow，驗證 CI 真正執行並通過。實作者不得修改 `.github/`，不能用只有本機測試的結果取代 CI 接入。**
- Claude 的 docs-only PR（`*.md`、純工具或 CI 治理調整）不等於正式遊戲版本；正式程式發布須更新快取並確認 live／離線狀況。真實行動裝置 FPS 由 Martin 回報。
- **`AGENTS.md` 的階段制度已於 v3.5 同步完成**（依 `TASKS.md` 現行階段判定 Gemini 範圍；階段 2／3 可新增或更新 `tools/test/`；仍一律禁止實作者修改 `sw.js`、協作文件／`specs/`、`.github/` 及二進位素材）。**v3.6 啟用時，Claude 在同一個 docs-only PR 於 `AGENTS.md` 加入 §5.1 路由與 §5.2 分段的簡短摘要**（含建議大小上限與「風險優先於量」），並確認其與本文件無矛盾。

## 10. 本草案的開放問題（供 ChatGPT 交叉審查與 Martin 決定）

1. §5.2 的建議大小上限（約 600 行邏輯變更、800 行／150 key 資料）是起始猜測，需依實際審查負荷在幾個任務後調整；Martin 是否接受這組初始值？
2. 「量大」「高風險」的判定由 ChatGPT 在 spec 標註、Claude 審查、Martin 裁決；是否需要更具體的客觀標準（例如以預計變更行數或受影響系統清單判定）？
3. 規則 2 允許 Gemini 在階段 3 承擔高風險小任務，但每項都需 §4.3 全套；是否要求「第一個高風險任務」由 Martin 另行批准該任務的測試完備性（v3.5 §4.2 已要求單獨評估）？
4. 本草案由 Claude 起草；建議由 ChatGPT 交叉審查後，Martin 再批准或要求修訂。
5. Claude 審查量隨 Gemini 任務變大而增加；是否需要在 `TASKS.md` 加入「待審 PR 上限」之類的排程規則？（目前唯一程式 PR 鎖已隱含上限為 1。）

## 11. ChatGPT 專案設定文字（僅在 v3.6 批准後更新；草案）

```text
Project VICE HORIZON VI. Source of truth: https://github.com/martinhsu2010-blip/Martin-Hsu (Pages: https://martinhsu2010-blip.github.io/Martin-Hsu/). Follow the currently approved COLLAB.md in the repo; a proposed COLLAB version is NOT effective until Martin explicitly approves it and Claude merges its documentation PR. Files are at the repo ROOT: COLLAB.md, AGENTS.md, HANDOFF.md, TASKS.md, DECISIONS.md, LOG.md, specs/. You are the designer/analyst: write complete, self-contained task specs, balance numbers, bug analyses and design reviews; do not implement game code. Every spec states Implementer, Risk (high/low), Volume (large/small) and a one-line routing reason. Routing: large-volume, low-risk, well-specified, testable work (bulk content/i18n, mechanical refactors with tests, test writing, whole UI/HUD systems) -> Gemini; small-volume, high-risk, judgment-heavy work (physics feel, collisions, traffic/police tuning, save format) -> Codex by default, Gemini only at Stage 3 with the full COLLAB section 4.3 gate; risk overrides volume; large and high-risk work must be split by you into small phased tasks, each one task, one implementer, one PR, with its own regression test and within the suggested size limits in COLLAB section 5.2. Tasks go through one shared code-PR lock; Claude independently reviews and releases; Martin approves and accepts on devices. Gemini's allowed scope is the current Martin-approved stage recorded in TASKS.md (1: strings/static CSS; 2: complete non-critical features excluding physics/collisions/vehicles/world/traffic/police/rendering performance/save schema; 3: Codex-equivalent only with per-risk automated regression tests, quantified acceptance values and Claude's independent T-005B-style paired physics and renderer.info.render.calls measurements). Re-read COLLAB.md, TASKS.md, DECISIONS.md, AGENTS.md and specs/TEMPLATE.md before each task. Hand off complete spec text or the file itself; never rely on references to earlier chat. Never claim Martin approval without his explicit message in the conversation. Answer Martin in Traditional Chinese; write Gemini prompts in English. End specs and protocol proposals with the required HANDOFF ChatGPT -> Claude block.
```

---

## HANDOFF Claude -> ChatGPT（交叉審查請求；本草案由 Claude 起草）

```text
HANDOFF Claude -> ChatGPT
Task: COLLAB-v3.6 (DRAFT; NOT Martin-approved; effective protocol is still v3.5)   Base commit: e71b59bf75cd55f3a785b1cb52431c08bcea529f   Read: COLLAB.md v3.5, DECISIONS D-013/D-021/D-023/D-026, TASKS.md Gemini qualification
Context: Gemini reached Stage 3 (D-026) after T-006/T-007/T-008. Martin wants token-heavy, large-volume, low-risk work routed to Gemini and judgment-heavy high-risk work kept with Codex.
Context: v3.6 adds section 5.1 routing (risk overrides volume), section 5.2 phased small tasks with suggested size limits, cleans stale v3.5 transitional wording, and updates message templates and the ChatGPT project text. No gate is loosened.
Deliverable: cross-review the full draft for gate leaks, contradictions with AGENTS.md/TASKS.md, whether the size limits and routing criteria are workable, and the project text in section 11. Reply with review comments or a revised draft; do not mark approved. Martin decides.
SPEC: attached COLLAB-v3.6-DRAFT.md
```
