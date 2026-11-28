> Verbatim ChatGPT draft "T-016E — WE-01E Final Survey Map & Report Builder v1.0" (G0 proposal). Superseded where `specs/T-016E-spec-v1.0.md` (Claude conditions) says so; the body below is unchanged.

T-016E — WE-01E Final Survey Map & Report Builder v1.0

Status: DRAFT FOR G0
Protocol: COLLAB v3.6
Implementer: Gemini Stage 3 (proposed)
Reviewer: Claude
Risk: LOW
Volume: SMALL

Routing reason: Deterministic, read-only artifact generation using previously verified JSON outputs. No new world analysis or production modifications.

---

1. Baseline and dependencies

T-016A：Done，D-051d。
T-016B：Done，D-053。
T-016C：Done，D-055。
T-016D：Done，D-057，PR #121，merge e0afd90。

Audit game BASE：

84319439243b51aa8d119e33eb62a0637feea887

Production release：

vh-2026-11-27-02

Development BASE：

Latest main after T-016E registration.

Claude 須在正式登記前確認完整 SHA、D-013 及共享 PR 鎖。

1.1 Source documents

- COLLAB.md v3.6
- AGENTS.md
- TASKS.md
- DECISIONS.md D-013、D-021、D-026、D-027、D-051–D-057
- specs/WE-01-spec-v1.2.md
- specs/WE-01-v1.3-amendment.md
- specs/WE-01-v1.4-amendment.md
- specs/WE-01-v1.4-errata-T016B.md
- specs/T-016B-spec-v1.4.md
- specs/T-016C-spec-v1.0.md
- specs/T-016D-spec-v1.0.md
- tools/fixtures/we01/SCHEMA_NOTES.md
- T-016E_request_for_chatgpt.md（E1–E10）

已批准的 A/B/C/D 規格及正式決策優先於早期草案。

---

2. Scope

T-016E 是純唯讀的產物建構器。

唯一主要交付：

1. world_survey.svg
2. survey_report.md

允許另行輸出非確定性執行資訊至 report_meta.json。

T-016E 不負責：

- 土地重新分類。
- 容量重新計算。
- 道路可行性重新分析。
- 內部街道生成。
- 住宅地塊重新配置。
- 可行性裁定重新計算。
- 修改任何既有 verdict。
- Runtime 效能量測。
- 任何世界建造或遊戲內容修改。

所有分析結果必須來自 A/B/C/D 已驗證產物。

---

3. Input artifacts

必要輸入：

Artifact| Source
land_inventory.json| T-016A
capacity_inventory.json| T-016B
parcel_candidates.json| T-016B
road_survey.json| T-016C
internal_streets.json| T-016D
conditional_parcels.json| T-016D
feasibility.json| T-016D

必要時允許讀取正式 dumps，以取得已存在的：

- 道路幾何。
- Site A 保護區。
- 海灘。
- 水域。
- 已記錄的 UNKNOWN 幾何。
- 其他必要地圖背景幾何。

不得利用 dumps 重新執行土地、道路或住宅容量分析。

允許的幾何處理僅限：

座標轉換、SVG 路徑組裝、視窗裁切、比例縮放及標註位置安排。

不得因此改變分析結果或創造新的可行性證據。

3.1 Input authority

資料權威順序依欄位用途決定：

A：原始土地審計。

B：直接住宅容量、初步容量、容量上界。

C：候選外部道路幾何及道路自身裁定。

D：最終選定街道、條件住宅配置、土地面積及最終裁定。

D 對某道路的配置排除，不得改寫 C 對該道路本身的工程可行性裁定。

例如：

C01 在 C 中為條件可行道路，但可在 D 的特定住宅配置中因地塊衝突而被排除。

報告須同時保留兩種不同層次的結果。

B 的 PENDING_T016D 為歷史中間狀態，不得覆蓋 D 的最終 C_conditional。

3.2 Integrity checks

驗證：

- Game BASE。
- 正式 static fingerprints。
- 各產物 schema version。
- Analyzer version。
- polygon_revision。
- Scenario IDs。
- Region IDs。
- 產物間的 ID 引用。
- 已宣告的輸入 SHA-256。

PHONE_LOW：

e473d222db998487e5fcfb187349e5006e6f619c1d15cca6bae1a2ee380352aa

DESKTOP_HIGH：

52653bc578411a9eda9b314581bb16f45f3cb4eb1be623f9d39dc21ade365482

D 正式 JSON schema_version = 1。

不得假定 A/B/C 全部採用完全相同的 schema 欄位結構；Claude G0 須確認各產物實際契約。

Dump file_sha256 不得取代 static fingerprint 作為跨載入相容性判定。

若必要輸入缺失、資料來源不一致或引用無效，停止建構並以非零 exit code 回報。

不得以零、空字串或自造資料填補缺失數值。

---

4. CLI and output contract

建議 CLI：

python3 -B tools/test/we01e_report_builder.py --input-dir INPUT_DIR --out OUT_DIR

必要時提供：

--dump PHONE_LOW.json
--dump DESKTOP_HIGH.json

支援 --help。

Claude G0 須確認是否需要獨立的輸入產物雜湊清單。

正式輸出：

- world_survey.svg
- survey_report.md
- report_meta.json（如需保存耗時及非確定性資訊）

所有產物寫入指定 OUT_DIR。

不得修改 INPUT_DIR 或原始 JSON。

輸入資料與輸出路徑不得發生覆寫衝突。

失敗時不得留下可能被誤認為本次成功建構的完整正式成果。

不得提交正式 dumps 或生成產物至 Gemini PR。

---

5. Truthful presentation

以下為 D-057 正式結果的驗收參考，不得硬編碼於建構器。

5.1 D3 verdicts

INITIAL：

NOT FEASIBLE WITHIN AUDITED BOUNDARIES。

25 ha 有效土地上界208,676 m²，小於250,000 m²。

ENVELOPE：

CONDITIONAL。

REVISED：

UNVERIFIED。

REVISED-v2 為主要規劃研究情境，但尚未取得完整可行性證明。

5.2 B3 limitation

REVISED B3：

直接住宅容量17棟。

最低目標18棟。

D 的搜尋未找到可增加容量的合法街道或額外地塊。

因此屬於搜尋不足及未完成可行性證明，不是已證明不可行。

不得使用：

「B3 無法建造第18棟」

等超出證據範圍的結論。

5.3 C01 conflict

B1 的 C01 因與直接地塊 B1_R02_005 發生衝突，在 D 的相應配置中被排除。

須同時呈現：

- C01 自身道路分析結果。
- D 配置中的排除狀態。
- 衝突地塊 ID。
- 保留直接地塊的原因。

不得刪除衝突地塊以美化地圖。

5.4 H01

H01：

NOT_FEASIBLE。

最大步長坡度135.6%。

Reason：

GRADE_LIMIT_EXCEEDED。

不得畫成已建造或可供住宅接入的道路。

5.5 B2 proxy

B2 的 R05 容量為 PROXY。

平地代理住宅容量不得被描述為已驗證的山坡住宅施工能力。

5.6 Search limitations

保留 D23：

SEARCH_BUDGET_EXHAUSTED 不等於 NOT FEASIBLE。

即使未耗盡候選預算，有界搜尋未找到解也不構成全域不可行證明。

所有 verdict、reason codes 及相依工程均照原始 JSON 呈現。

---

6. SVG design specification

6.1 Deliverable format

唯一正式 SVG：

world_survey.svg

建議採單一 SVG 文件、多面板配置。

包含：

- REVISED-v2 主圖。
- INITIAL 附圖。
- ENVELOPE 附圖。
- 全域圖例。
- 情境裁定比較。
- 資料來源及限制。

三個情境各自呈現 B1、B2、B3。

不得將不同情境的住宅地塊疊加為同一個施工配置。

6.2 Recommended layout

REVISED-v2 主圖：

B1、B2、B3 三個獨立區域詳細面板。

INITIAL 與 ENVELOPE：

各包含三區縮小附圖。

另設全域道路連通示意面板，呈現三區及 AVE_0 主道路網的空間關係。

全域面板必須以已知審計幾何為基礎。

未取得的世界區域不得自行補畫。

若全域面板僅供示意，須清楚標示「示意／非完整審計覆蓋」。

建議 SVG viewBox 約2400×2000，屬版面建議，不是分析資料。

Claude G0 可依標註密度調整。

6.3 Coordinates

- 明確標示 X/Z 軸。
- 所有區域面板使用一致方向。
- 建議 +X 向右、+Z 向下。
- 不得無證據地將 Z 軸標記為地理北方。
- 每個不同縮放比例的面板須有獨立比例尺。
- 保留原始世界座標及地塊 ID。
- 不得為美觀而移動實際地塊或道路幾何。

6.4 Visual encoding

建議配色：

Category| Visual encoding
Existing verified road| 深灰實線
Selected conditional external road| 藍色虛線
Selected internal street| 紫色實線及明確未建標註
Rejected/conflicting road| 紅色點線
DIRECT parcel| 綠色填色
CONDITIONAL parcel| 橙色填色
Site A protection| 紫灰斜線
Beach| 淡沙色
Water| 淺藍色
LX/UNKNOWN| 灰色交叉斜線

不得只依顏色區分重要狀態。

須搭配線型、圖例及文字。

所有尚未建造道路均須清楚標示為候選或條件工程。

C01 在 D 排除的配置中不得使用已選定道路樣式。

H01 須保留失敗路線樣式及原因。

6.5 Parcel labels

每個已選定地塊保留：

- Parcel ID。
- Prototype ID。
- DIRECT／CONDITIONAL 狀態。
- 對應情境及區域。

地塊 ID 不得以任意流水號取代。

標註密集時允許：

- 引線。
- 區域內索引。
- 對應面板旁的地塊 ID 清單。
- SVG title 元素。

不得為避免文字重疊而省略必要 ID。

主要標註須在靜態閱讀或列印時仍可辨識。

6.6 Unknown geometry

只有具有實際空間資料的 UNKNOWN 區域才能畫出確定邊界。

若 JSON 只有未知面積或原因，沒有對應幾何：

以面板警示及數據註記呈現。

不得隨意繪製未知區域形狀。

若必須取得額外的唯讀幾何資料，交 Claude G0 確認來源。

不得修改 A/B/C/D 以補足地圖資料。

6.7 Provenance

SVG 必須包含：

- 完整 BASE SHA。
- PHONE_LOW static fingerprint。
- DESKTOP_HIGH static fingerprint。
- CROSS_PRESET_COMMON 或實際 preset 標記。
- polygon_revision。
- Scenario ID。
- 資料來源說明。
- 審計資料與示意資料區別。

6.8 Technical requirements

- 合法 XML。
- UTF-8。
- 靜態 SVG。
- 不含 JavaScript。
- 不含事件處理器。
- 不含 foreignObject。
- 不含外部圖片、字型或網路依賴。
- 不含外部 stylesheet。
- 不含 DOCTYPE 或外部實體。
- 所有文字與屬性須正確 XML escaping。
- ID 唯一。
- 本地引用有效。

允許使用系統字型 fallback。

不得內嵌外部字型檔。

---

7. Markdown report specification

正式輸出：

survey_report.md

語言：

繁體中文。

識別碼、JSON key、檔名及正式 verdict 保留英文。

7.1 Executive summary

呈現：

- WE-01 審計目的。
- A/B/C/D 已完成狀態。
- 三情境 D3 裁定。
- 最主要容量及土地限制。
- 已驗證工程與未確認事項。
- 研究完成與施工授權的區別。

不得將 ENVELOPE CONDITIONAL 解讀為已批准全面擴張。

7.2 A/B/C/D results

分章呈現：

A：土地分類及跨畫質結果。

B：直接、初步及容量上界。

C：道路長度、坡度、接點及道路自身裁定。

D：選定街道、條件容量、土地守恆及最終裁定。

B/C 的中間分析結果與 D 最終配置必須清楚區分。

7.3 Regional land and capacity

每個情境分別列出 B1、B2、B3。

依 JSON 實際欄位呈現：

- A_gross。
- A_direct。
- A_conditional。
- A_protected。
- A_unavailable。
- A_unknown。
- A_eligible。
- C_direct。
- C_preliminary。
- C_conditional。
- C_additional（若已有來源欄位）。
- C_upper。
- 各 preset 容量。
- CROSS_PRESET_COMMON。
- 原型比例及代理住宅限制。
- 道路接入狀態。

不得將 C_conditional 與 C_direct 重複加總。

不得由建構器自行推導缺失容量欄位。

7.4 Road and engineering report

呈現：

- 既有道路。
- 候選外部道路。
- 選定內部街道。
- 排除道路及原因。
- 海灘侵占。
- 必要工程相依鏈。
- 可選工程相依鏈。
- 未驗證連接。

AVE110 延伸為可選、尚未驗證的額外連接，不得錯誤列為所有 C02/X01 的必要工程。

7.5 Feasibility verdicts

每個情境完整呈現：

- 25 ha。
- 40棟。
- 60棟。
- 三區道路裁定。
- 整體 D3。
- 各裁定的原始證據與 reasons。

不得重新計算裁定。

60棟理想目標不得被誤寫為 D3 必要條件。

7.6 Performance baseline

B8 由 Claude 於 E 合併後另行量測。

T-016E 不執行 runtime 效能測試。

若正式效能基準尚未提供：

明確標記：

「Gate B8 尚待 Claude 完成正式量測，本報告不代表新增住宅已達效能目標。」

建議保留可供 Claude 附加正式基準引用的獨立章節。

不得使用估計 FPS 取代實測。

不得將 headless FPS 冒充實機 FPS。

7.7 Follow-up recommendations

章節標題：

「WE-02–WE-09 後續工程建議（僅為建議，未授權）」

建議須以現有 JSON 證據為依據。

可包含：

- B3 額外合法地塊或候選區修訂研究。
- B1 C01 與直接地塊衝突的替代道路方案。
- B2 山區地形及地基工程研究。
- 海灘景觀保護與道路配置。
- 區域串流及住宅 LOD。
- ENVELOPE 條件擴張方案的範圍比較。

不得登記任何後續任務。

不得自行指定施工方案已獲批准。

---

8. Numeric and semantic consistency

E4／D25 為本任務核心要求。

所有審計結果數值、容量、面積、坡度、道路長度及裁定證據必須從正式 JSON 讀出。

不得將 D-057 數字直接寫入建構器模板。

固定版面尺寸、章節編號、SVG stroke width 等呈現參數不屬於審計結果數值。

25 ha／40／60 等研究目標亦應優先讀取 JSON 已記錄的門檻。

若必要目標值未存在於 JSON，Claude G0 須指定正式來源或允許的唯讀資料契約，不得由 Gemini 猜測。

8.1 Formatting

允許：

- 千分位格式。
- 明確單位。
- 已定義的小數位數格式化。
- 不改變數值含義的文字呈現。

不得：

- 將四捨五入後的數值用於重新裁定。
- 將缺失數值顯示為0。
- 將 UNKNOWN 改成 FEASIBLE。
- 將 NOT_FEASIBLE 改成 CONDITIONAL。
- 將原始證據替換為更有利的數字。

8.2 Independent consistency verification

建議 SVG 使用可追溯的 data-* attributes，記錄：

- Source artifact。
- Scenario。
- Region。
- Entity ID。
- Source field。

Markdown 可使用穩定表格列鍵及欄位名稱。

測試必須獨立解析 SVG／Markdown 的實際可見文字與來源 JSON。

不得只檢查隱藏 metadata，而忽略實際呈現的數值。

不得使用建構器本身的格式化函式作為唯一測試 oracle。

---

9. Determinism and performance

相同輸入產物執行三次：

world_survey.svg SHA-256 相同。

survey_report.md SHA-256 相同。

固定排序：

Scenario：

INITIAL、ENVELOPE、REVISED。

Region：

B1、B2、B3。

Road／Street／Parcel：

穩定 ID 排序。

不得依 Python set 或未定義字典順序產生輸出。

SVG／Markdown 不得包含：

- generated_at。
- 執行時間。
- 隨機 ID。
- 機器特定絕對路徑。
- 其他非確定性欄位。

執行時間另存 report_meta.json。

完整正式輸入讀取、驗證及輸出目標≤10秒。

不包含 Claude 的 B8 runtime 量測。

相同靜態世界但不同 dump file hashes 的輸入，允許來源雜湊標註不同；分析內容不得無故改變。

不得為取得跨載入完全相同的雜湊而刪除必要 provenance。

---

10. Allowlist

Proposed branch：

gemini/T-016E-we01e-report-builder

Only two new files：

tools/test/we01e_report_builder.py

tools/test/we01e_report_builder_check.py

Python standard library only。

允許使用：

json、hashlib、pathlib、argparse、xml.etree.ElementTree、html、tempfile 等標準函式庫。

不得修改：

- A/B/C/D analyzers。
- A/B/C/D checks。
- Fixtures。
- Extractor。
- index.html。
- sw.js。
- CACHE。
- Production assets。
- CI。
- Collaboration documents。

不需要重新執行 A/B/C/D analyzer 來產生報告內容。

Claude 負責提供正式輸入及必要的唯讀測試資料。

---

11. Line budget

沿用 Claude E8：

Component| Hard ceiling
Report builder| 600
Check script| 400
Combined| 1,000

ChatGPT 初步工作量估算：

Builder：

約430–560行。

Check：

約260–340行。

合計：

約690–900行。

考量前期估算曾偏低35–40%，壓力估算約930–1,260行。

因此1,000行有可行性，但不能保證足夠。

Claude G0 應確認：

- 正式 JSON 結構是否易於直接呈現。
- UNKNOWN 幾何來源是否完整。
- SVG 多面板標註複雜度。
- 逐項數值一致性測試的實際工作量。

強制回報：

- 約500行時。
- 完成前。

回報兩檔各自行數、測試完成度及預計最終行數。

超過任一子上限或合計上限：

STOP AND RETURN TO CLAUDE。

不得壓縮程式碼、刪除必要測試或省略報告內容。

本草案不自行提高 E8 上限。

---

12. Automated acceptance tests

新增 E01–E20。

E01 — Input validation

七份必要 JSON 可讀取；缺失、錯誤 schema、錯誤 BASE 必須拒絕。

E02 — Provenance

Fingerprints、polygon_revision、版本及來源雜湊一致。

E03 — Read-only integrity

執行前後輸入產物 SHA-256 完全一致。

E04 — Verdict fidelity

SVG／Markdown 的正式裁定與 feasibility.json 一致。

E05 — Numeric fidelity

逐項驗證報告可見數字與來源 JSON。

E06 — Capacity presentation

C_direct、C_conditional、C_upper、各 preset 及共同容量正確呈現，不重複加總。

E07 — Road state fidelity

既有道路、候選道路、選定道路及排除道路樣式與原始狀態一致。

E08 — Conflict preservation

C01 配置排除及衝突地塊 ID 正確呈現。

E09 — Search limitation

UNVERIFIED 不得被改寫為不可行。

E10 — XML validity

SVG 可由標準 XML parser 正常解析。

E11 — SVG security and portability

無腳本、外部資源、事件處理器、DOCTYPE 或外部實體。

E12 — SVG completeness

座標軸、比例尺、圖例、BASE、fingerprints、preset 標記完整。

E13 — Scenario coverage

REVISED 主圖及 INITIAL／ENVELOPE 附圖皆存在，各包含三區。

E14 — Geometry fidelity

SVG 中道路、街道、地塊及保護區幾何與來源資料經座標轉換後一致。

E15 — Parcel identity

所有必要地塊 ID、原型及狀態可追溯，無重複或遺漏。

E16 — Unknown handling

UNKNOWN 無空間資料時不得捏造幾何。

E17 — Report completeness

Executive summary、A/B/C/D、三區容量、道路、25 ha／40／60、D3、海灘、工程相依及限制完整。

E18 — Authorization and B8

WE-02–WE-09 明確標記未授權；B8 未量測時保留待完成狀態。

E19 — Determinism

相同輸入三次建構，兩份正式產物雜湊一致。

E20 — Performance and failure behavior

快速 fixture 測試、輸入錯誤 exit code、輸出路徑安全及完整產物交付。

正式≤10秒由 Claude 獨立驗證。

---

13. Mutation tests

M-E01：接受錯誤 BASE 或 fingerprint。

M-E02：修改一個來源 JSON 數值，但保留舊報告值。

M-E03：修改 Markdown 可見數字，但保留正確來源 metadata。

M-E04：修改 SVG 可見標註，但保留正確 data-* attributes。

M-E05：將 REVISED UNVERIFIED 改為 FEASIBLE。

M-E06：將搜尋不足改為 NOT FEASIBLE。

M-E07：將候選道路畫成既有道路。

M-E08：移除 C01 排除狀態或衝突地塊 ID。

M-E09：移除 H01 失敗原因。

M-E10：重複加總 C_direct 與 C_conditional。

M-E11：遺漏某個情境或住宅區。

M-E12：移除 Site A、海灘、水域或 UNKNOWN 必要資訊。

M-E13：刪除必要地塊 ID。

M-E14：加入外部資源、腳本或事件處理器。

M-E15：加入非確定性時間戳。

M-E16：將 B8 未完成改成 PASS。

M-E17：將 WE-02–WE-09 建議改成已授權施工。

M-E18：將 B2 R05 PROXY 改為已驗證山坡住宅。

M-E19：修改實際 SVG 幾何位置，但保留正確 ID。

M-E20：將必要欄位缺失替換成0。

所有適用 mutants 必須 RED。

M-E02 應區分兩種情況：

1. 輸入被竄改但未更新正式雜湊：完整性驗證失敗。
2. 合法 synthetic fixture 數值改變：建構器必須反映新值，若仍輸出舊值，一致性測試必須失敗。

不得因正式數字與 synthetic fixture 不同而硬編碼拒絕合法測試資料。

---

14. Complete D/E test allocation

本節依 D-056 G0-D16 及 E1–E10。

注意：

Gate B10 與 Test B10 是不同要求。

14.1 B-series

Original ID| T-016D responsibility| T-016E responsibility
B10| D14/D17：條件容量及面積不得重複計算| E05/E06：報告不得重複呈現或加總
B15| D19–D22：四種裁定及 D3 邏輯| E04/E09：原樣呈現裁定，不重算
B17| D26：分析 JSON 確定性| E19：SVG／Markdown 確定性
B18| Claude 正式分析時間驗證| E20：報告建構≤10秒，由 Claude 驗證
B19| D25 JSON 完整性| E12/E13/E17：最終 SVG／報告完整性
B20| D17/D18：土地比例不作硬性門檻| E04/E17：報告不得將參考比例改為硬性門檻
B21| D16：共同配置合法性| E06/E14/E15：共同配置忠實呈現

14.2 C-series

Original ID| T-016D responsibility| T-016E responsibility
C06| D12/D14：內部街道及條件容量| E06/E07：結果完整呈現
C07| D19–D22：三情境裁定| E04/E13/E17
C08| 不屬 D 的 SVG 實作| E10–E16：完整 SVG
C09| D02/D03：最多3條、30–150 m| E05/E07：實際選定街道資料
C10| D04/D05：候選預算1,280及確定性排序| E05/E09：預算及搜尋限制
C11| D06/D07：來源道路及外部相依| E07/E17：相依鏈
C12| D08：11 m、6%、1 m 地形| E05/E07：實際驗證結果
C13| D09/D10/D13：障礙物及直接地塊保護| E08/E14/E16
C14| D11及相依鏈測試：R7接近及條件地塊| E06/E15/E17
C15| D17/D18：面積互斥及守恆| E05/E06
C16| D23：搜尋不足不得冒充不可行| E09
C17| D14–D16：包含直接容量、比例及共同合法性| E06/E14/E15

C10 使用 D-056 已批准的1,280候選預算，不得回退至256或1,024。

14.3 D25

D25 JSON 部分：

已由 T-016D 負責。

D25 SVG／Markdown 部分：

由 T-016E 的 E04–E08、E10–E17 完成。

14.4 Mutation allocation

D 保留：

M-C04–M-C09。

M-B02、M-B03、M-B04、M-B05、M-B07、M-B08、M-B09、M-B10、M-B11、M-B13 等已分配的分析 mutations。

E 不重做上述分析演算法。

E 以 M-E01–M-E20 驗證：

已完成的分析證據沒有在最終呈現階段被修改、遺漏或誤解。

Claude G0 須確認此分配與已合併 D 測試實際覆蓋一致。

---

15. Claude independent verification

Claude 負責：

1. 提供正式七份 JSON。
2. 提供必要 dumps 或已驗證唯讀幾何資料。
3. 驗證所有來源雜湊。
4. 獨立比對 SVG／Markdown 與 JSON。
5. 確認三情境及三區均完整。
6. 確認 D-057 正式裁定未改寫。
7. 確認 C01、H01、B3、B2 PROXY 及海灘資訊。
8. 驗證 XML 及外部資源限制。
9. 檢查 SVG 實際渲染效果及標註重疊。
10. 重跑全部快速測試及適用 mutants。
11. 三次建構雜湊一致。
12. 正式完整建構≤10秒。
13. A/B/C/D 回歸測試。
14. Production SHA-256 一致。
15. D-013、PR lock、allowlist。
16. CI wiring。

不得只依 Gemini 自報 PASS 完成驗收。

---

16. Final gates

Gate B10 — Final report

由 Claude 驗證：

最終地圖、數據、道路、容量、裁定及後續工程建議完整交付。

T-016E 負責報告建構器與正式報告內容的驗證。

Gate B8 — Runtime baseline

由 Claude 在 E 合併後依 WE-01 v1.2 §13 量測。

不屬於 E 程式碼。

效能量測完成後，由 Claude 提供正式基準引用及最終交付版本。

建議將待補 B8 的報告內容與正式完成 B8 的附錄分開保存，避免手動修改確定性建構產物。

Gate B11 — User acceptance

Martin 必須收到：

- 最終 world_survey.svg。
- 最終 survey_report.md。
- 正式 feasibility.json。
- 必要的分析數據。
- B8 正式效能基準及引用。

收到完整成果後獨立接受。

不得以 E 的 PR merge 自動取代 B11。

不得以 B10 PASS 宣稱世界擴張已獲施工批准。

16.1 Final state

T-016E 工具驗收完成：

不等於 WE-01 全部驗收完成。

WE-01 全部驗收完成：

不等於 D3 FEASIBLE。

D3 CONDITIONAL：

不等於已授權施工。

---

17. G0 confirmation items

Claude 須確認：

1. 七份正式 JSON 的實際 schema 及權威欄位。
2. SVG 所需 Site A、道路、海灘、水域及 UNKNOWN 幾何是否完整。
3. 缺少幾何時的忠實呈現方式。
4. 來源雜湊驗證及跨載入相容性。
5. 多面板 SVG 版面。
6. 全部可見數字的來源及一致性測試方法。
7. D/E 測試分配。
8. 600／400／1,000行上限是否可行。
9. 完整建構≤10秒。
10. B8 後續附錄及最終報告交付流程。
11. B10／B11 的獨立驗收順序。
12. 最新 main SHA、D-013、共享 PR 鎖。

本規格不授權實作。

---

HANDOFF ChatGPT -> Claude

Task: T-016E — WE-01E Final Survey Map & Report Builder v1.0

Base commit: latest main containing T-016D merge e0afd90 and D-057; confirm full SHA before registration.

Read: COLLAB.md v3.6, AGENTS.md, TASKS.md, DECISIONS D-013/D-021/D-026/D-027/D-051–D-057, WE-01 v1.2/v1.3/v1.4, registered T-016B/C/D specifications, and T-016E_request_for_chatgpt.md E1–E10.

Context:

T-016A/B/C/D are complete. T-016E is a read-only artifact builder for the final SVG and Markdown report; no new analysis or verdict computation is permitted.

The final report must preserve INITIAL NOT FEASIBLE, ENVELOPE CONDITIONAL and REVISED UNVERIFIED, including the B3 search limitation, C01 configuration conflict, H01 grade failure and B2 PROXY limitation.

The proposed layout is one standalone SVG with REVISED as the primary view and INITIAL/ENVELOPE as supplementary panels. The original 600/400/1,000-line ceilings remain unchanged pending G0.

Deliverable:

Review the complete specification, verify the actual JSON contracts and available geometry, confirm D/E test allocation, assess line budget and deterministic report generation, and resolve the B8/B10/B11 delivery sequence.

Register only after Martin explicitly approves.

SPEC: Complete T-016E v1.0 proposal in this message.

No WE-02–WE-09 registration, production modification, construction, CACHE bump or implementation authorization.

HANDOFF -> Claude G0 review.