# VICE HORIZON VI — WE-01 最終勘查報告（Final Survey Report）

## 0. 來源溯源與完整性資訊（Provenance）

| 項目 | 數值 |
| --- | --- |
| Audit Game BASE | `84319439243b51aa8d119e33eb62a0637feea887` |
| PHONE_LOW `static_fingerprint` | `e473d222db998487e5fcfb187349e5006e6f619c1d15cca6bae1a2ee380352aa` |
| DESKTOP_HIGH `static_fingerprint` | `52653bc578411a9eda9b314581bb16f45f3cb4eb1be623f9d39dc21ade365482` |
| Preset Mode | `CROSS_PRESET_COMMON` |
| `polygon_revision` | `2` |
| Builder Version | `we01e-1.0` |
| `land_inventory.json` SHA-256 | `e15e600e10a03a5d2a5f042c6e9171155b5df32f267faa5b24f1a87217838f9a` |
| `capacity_inventory.json` SHA-256 | `0efa1a1763b64b91ac3ab671b0d8d7360c939c32c26190d4b16e8a2a5246bc1a` |
| `parcel_candidates.json` SHA-256 | `e27f457a95cbe04d529563f3bc002425e8e818efc7c5571f1b741b0f3722a586` |
| `road_survey.json` SHA-256 | `4afd52d2b51273f1e890aeda3c3ade22927124926c12a1e3aa3cefe30f3eeb27` |
| `internal_streets.json` SHA-256 | `adfd26957555bffbb7e5a3d9e216a4a1ecd47c871be35bb63fc8a57611c2274e` |
| `conditional_parcels.json` SHA-256 | `51d8eb8e6ac60b7f36bf0ba86895aa069befe331f37d5d54e04ad1de2ded0124` |
| `feasibility.json` SHA-256 | `6131fb4a11ab2e43ed9799307158b18b61c2e469e97f85ed78e202dbd69832b4` |
| `map_geometry.json` SHA-256 | `c17cc1ce8080627e4744394e5ffefdec7e7b6d516f7eb8fd25c5f2f605e1460e` |

## 1. 執行摘要（Executive Summary）

本報告為 WE-01（T-016A/B/C/D）已完成唯讀離線審計產物之統整呈現，**未重算任何面積、容量、坡度或裁定**，亦不構成施工授權或世界擴張批准。`ENVELOPE` 之 `CONDITIONAL` 裁定僅表示在調查外框下具備條件可行路徑，不得解讀為已批准全面擴張；`REVISED` 為主要規劃研究情境，目前尚未取得完整可行性證明。

| Scenario | `land_25ha` | `buildings_40` | `buildings_60` (不門控 D3) | `road_connectivity` | `D3` |
| --- | --- | --- | --- | --- | --- |
| `INITIAL` | `NOT FEASIBLE WITHIN AUDITED BOUNDARIES` | `UNVERIFIED` | `NOT FEASIBLE WITHIN AUDITED BOUNDARIES` | `CONDITIONAL` | `NOT FEASIBLE WITHIN AUDITED BOUNDARIES` |
| `ENVELOPE` | `CONDITIONAL` | `CONDITIONAL` | `UNVERIFIED` | `CONDITIONAL` | `CONDITIONAL` |
| `REVISED` | `CONDITIONAL` | `UNVERIFIED` | `UNVERIFIED` | `CONDITIONAL` | `UNVERIFIED` |

## 2. A/B/C/D 分階段審計結果

### 2.1 T-016A 土地分類（`land_inventory.json`, `we01a-1.0`）

跨畫質共同模式 `CROSS_PRESET_COMMON`（網格步長 `5.0 m`，面積守恆容差 `1.0 m²`）：

| 區域 | 範圍 | 總面積 (m²) | L0 | L1 | L2 | L3 | L4 | L5 | LX | 守恆誤差 (m²) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `B1` | `initial` | 90,000 | 60,650 | 0 | 0 | 26,350 | 0 | 3,000 | 0 | 0.000 |
| `B1` | `survey` | 250,000 | 141,200 | 0 | 0 | 41,550 | 0 | 67,250 | 0 | 0.000 |
| `B2` | `initial` | 100,000 | 99,000 | 0 | 0 | 0 | 0 | 1,000 | 0 | 0.000 |
| `B2` | `survey` | 270,000 | 221,900 | 0 | 0 | 0 | 0 | 48,100 | 0 | 0.000 |
| `B3` | `initial` | 60,000 | 10,925 | 0 | 5,575 | 0 | 7,500 | 36,000 | 0 | 0.000 |
| `B3` | `survey` | 200,000 | 37,900 | 0 | 13,875 | 0 | 10,625 | 137,600 | 0 | 0.000 |
| `UNION` | `initial` | 250,000 | 170,575 | 0 | 5,575 | 26,350 | 7,500 | 40,000 | 0 | 0.000 |
| `UNION` | `survey` | 720,000 | 401,000 | 0 | 13,875 | 41,550 | 10,625 | 252,950 | 0 | 0.000 |

### 2.2 T-016B 直接與初步住宅容量（`capacity_inventory.json`, `we01b-1.0`）

T-016B 提供直接容量 `C_direct`、初步容量 `C_preliminary` 與容量上界 `C_upper`（中間階段分析；最終條件容量 `C_conditional` 一律以 T-016D 為準）：

| Scenario | Region | `C_direct` | `units_direct` | `C_preliminary` | `C_upper` | `proxy_used` |
| --- | --- | --- | --- | --- | --- | --- |
| `INITIAL` | `B1` | 0 | 0 | 30 | 50 | `false` |
| `INITIAL` | `B2` | 0 | 0 | 174 | 188 | `PROXY` |
| `INITIAL` | `B3` | 5 | 8 | 5 | 27 | `false` |
| `ENVELOPE` | `B1` | 5 | 5 | 72 | 108 | `false` |
| `ENVELOPE` | `B2` | 0 | 0 | 408 | 483 | `PROXY` |
| `ENVELOPE` | `B3` | 25 | 40 | 25 | 135 | `false` |
| `REVISED` | `B1` | 5 | 5 | 72 | 100 | `false` |
| `REVISED` | `B2` | 0 | 0 | 278 | 329 | `PROXY` |
| `REVISED` | `B3` | 17 | 29 | 25 | 40 | `false` |

### 2.3 T-016C 外部候選道路分析（`road_survey.json`, `we01c-1.0`）

候選道路總新增長度 `1,834.127 m`，總走廊面積 `25,579.012 m²`，總海灘侵占 `5,218 m²`（T-016D 在特定情境配置排除道路時，不改寫 T-016C 自身工程裁定）：

| Road ID | C `state` | `geom_corridor_state` | `new_length_m` | `new_corridor_area_m2` | `max_step_grade_pct` | `beach_encroachment_m2` | `reasons` | `optional_extension_links` |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `C01` | `CONDITIONAL_VERIFIED` | `LEGAL` | 312.492 | 7,812.300 | 0.000% | 4,994 | `none` | `none` |
| `C02` | `CONDITIONAL_VERIFIED` | `LEGAL` | 130.000 | 1,430.000 | 0.000% | 224 | `none` | `AVE_110:UNVERIFIED(AVE110_EXTENSION_REQUIRED)` |
| `H01` | `NOT_FEASIBLE` | `NOT_FEASIBLE` | 431.421 | 5,177.052 | 135.633% | 0 | `CORRIDOR_BLOCKED_ROAD, CORRIDOR_CONSERVATIVE_OBSTACLE, GRADE_LIMIT_EXCEEDED` | `none` |
| `H02` | `CONDITIONAL_VERIFIED` | `LEGAL` | 597.306 | 7,167.672 | 0.000% | 0 | `none` | `none` |
| `U01` | `EXISTING_VERIFIED` | `EXISTING_VERIFIED` | 0.000 | 0.000 | 0.000% | 0 | `none` | `none` |
| `X01` | `CONDITIONAL_VERIFIED` | `LEGAL` | 362.908 | 3,991.988 | 0.000% | 0 | `none` | `AVE_110:UNVERIFIED(AVE110_EXTENSION_REQUIRED)` |

### 2.4 T-016D 內部街道與搜尋限制（`internal_streets.json`, `we01d-1.0`）

T-016D 依已核准候選預算上限（1,280／區／情境；每區最多 3 條、每條 30–150 m）進行確定性貪婪搜尋。保留 D23 規則：`SEARCH_BUDGET_EXHAUSTED` 不等於 `NOT FEASIBLE`，有界搜尋未找到解亦不構成全域不可行證明。

| Scenario | Region | `candidate_count` | `checked_count` | `tier1_passed_count` | `zero_gain_count` | `tier2_verified_count` | `selected_count` | `search_budget_exhausted` |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `INITIAL` | `B1` | 200 | 200 | 80 | 5 | 3 | 3 | `False` |
| `INITIAL` | `B2` | 130 | 130 | 71 | 0 | 3 | 3 | `False` |
| `INITIAL` | `B3` | 280 | 280 | 15 | 15 | 0 | 0 | `False` |
| `ENVELOPE` | `B1` | 330 | 330 | 54 | 9 | 3 | 3 | `False` |
| `ENVELOPE` | `B2` | 170 | 170 | 156 | 5 | 3 | 3 | `False` |
| `ENVELOPE` | `B3` | 1,010 | 1,010 | 36 | 30 | 6 | 0 | `False` |
| `REVISED` | `B1` | 270 | 270 | 45 | 0 | 3 | 3 | `False` |
| `REVISED` | `B2` | 150 | 150 | 109 | 0 | 3 | 3 | `False` |
| `REVISED` | `B3` | 340 | 340 | 14 | 14 | 0 | 0 | `False` |

## 3. 各情境分區土地與住宅容量明細

注意：`C_conditional` **已包含** `C_direct`（`C_additional = C_conditional - C_direct`），嚴禁重複加總；`buildings`（棟數）與 `units_conditional`（戶數，如 R08 為 1 棟 4 戶）分欄呈現；`A_eligible` 與 `A_eligible_final` 以原欄位名分別呈現。土地利用參考帶（residential 15–30%、roads 20–30%）僅供參考（`informational_only: true`, `hard_gate: false`）。

### 3.1 情境 `INITIAL`

#### 土地面積守恆（`feasibility.json` `land_accounting`）

| Region | `A_gross` | `A_direct` | `A_conditional` | `A_new_road` | `A_protected` | `A_unavailable` | `A_unknown` | `A_eligible` | `A_eligible_final` | `A_possible` | `conservation_error_m2` | `beach_encroachment_m2` | 參考占比 res/road (info) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `B1` | 90,000 | 51,966 | 0 | 8,684 | 0 | 29,350 | 0 | 60,650 | 51,966 | 87,000 | 0.000 | 5,218 | 26.787% / 9.649% |
| `B2` | 100,000 | 90,333 | 0 | 9,187 | 0 | 480 | 0 | 99,520 | 90,333 | 99,520 | 0.000 | 0 | 26.400% / 9.187% |
| `B3` | 60,000 | 16,281 | 0 | 0 | 6,840 | 36,879 | 0 | 16,281 | 16,281 | 22,156 | 0.000 | 0 | 6.540% / 0.000% |
| `TOTAL` | 250,000 | 158,580 | 0 | 17,871 | 6,840 | 66,709 | 0 | 176,451 | 158,580 | 208,676 | — | 5,218 | — |

#### 分區住宅容量（`conditional_parcels.json` + B `C_preliminary`）

| Region | `C_direct` | `C_preliminary` | `C_conditional` (棟) | `C_additional` | `units_conditional` (戶) | `C_upper` | `C_phone_low` | `C_desktop_high` | `C_common` (`CROSS_PRESET_COMMON`) | `prototype_counts` | `proxy_used` | 外部道路接入 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `B1` | 0 | 30 | 14 | 14 | 14 | 50 | 14 | 14 | 14 | `R01:7, R02:7` | false | `CONDITIONAL` |
| `B2` | 0 | 174 | 50 | 50 | 50 | 188 | 50 | 50 | 50 | `R05:50` | PROXY（平地代理，非已驗證山坡施工） | `CONDITIONAL` |
| `B3` | 5 | 5 | 5 | 0 | 8 | 27 | 5 | 5 | 5 | `R01:1, R05:3, R08:1` | false | `FEASIBLE` |

### 3.2 情境 `ENVELOPE`

#### 土地面積守恆（`feasibility.json` `land_accounting`）

| Region | `A_gross` | `A_direct` | `A_conditional` | `A_new_road` | `A_protected` | `A_unavailable` | `A_unknown` | `A_eligible` | `A_eligible_final` | `A_possible` | `conservation_error_m2` | `beach_encroachment_m2` | 參考占比 res/road (info) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `B1` | 250,000 | 134,557 | 0 | 8,013 | 0 | 107,430 | 0 | 142,570 | 134,557 | 186,960 | 0.000 | 224 | 14.582% / 3.205% |
| `B2` | 270,000 | 213,525 | 0 | 10,555 | 0 | 45,920 | 0 | 224,080 | 213,525 | 255,513 | 0.000 | 0 | 13.102% / 3.909% |
| `B3` | 200,000 | 53,187 | 0 | 0 | 9,360 | 137,453 | 0 | 53,187 | 53,187 | 106,742 | 0.000 | 0 | 9.810% / 0.000% |
| `TOTAL` | 720,000 | 401,269 | 0 | 18,568 | 9,360 | 290,803 | 0 | 419,837 | 401,269 | 549,215 | — | 224 | — |

#### 分區住宅容量（`conditional_parcels.json` + B `C_preliminary`）

| Region | `C_direct` | `C_preliminary` | `C_conditional` (棟) | `C_additional` | `units_conditional` (戶) | `C_upper` | `C_phone_low` | `C_desktop_high` | `C_common` (`CROSS_PRESET_COMMON`) | `prototype_counts` | `proxy_used` | 外部道路接入 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `B1` | 5 | 72 | 21 | 16 | 21 | 108 | 21 | 21 | 21 | `R01:10, R02:11` | false | `FEASIBLE` |
| `B2` | 0 | 408 | 67 | 67 | 67 | 483 | 67 | 67 | 67 | `R05:67` | PROXY（平地代理，非已驗證山坡施工） | `CONDITIONAL` |
| `B3` | 25 | 25 | 25 | 0 | 40 | 135 | 25 | 25 | 25 | `R01:5, R05:15, R08:5` | false | `FEASIBLE` |

### 3.3 情境 `REVISED`

#### 土地面積守恆（`feasibility.json` `land_accounting`）

| Region | `A_gross` | `A_direct` | `A_conditional` | `A_new_road` | `A_protected` | `A_unavailable` | `A_unknown` | `A_eligible` | `A_eligible_final` | `A_possible` | `conservation_error_m2` | `beach_encroachment_m2` | 參考占比 res/road (info) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `B1` | 180,000 | 129,392 | 0 | 8,013 | 0 | 42,595 | 0 | 137,405 | 129,392 | 172,845 | 0.000 | 224 | 20.253% / 4.452% |
| `B2` | 175,000 | 147,156 | 0 | 9,844 | 0 | 18,000 | 0 | 157,000 | 147,156 | 173,749 | 0.000 | 0 | 17.801% / 5.625% |
| `B3` | 60,000 | 29,310 | 0 | 0 | 9,360 | 21,330 | 0 | 29,310 | 29,310 | 31,720 | 0.000 | 0 | 23.520% / 0.000% |
| `TOTAL` | 415,000 | 305,858 | 0 | 17,857 | 9,360 | 81,925 | 0 | 323,715 | 305,858 | 378,314 | — | 224 | — |

#### 分區住宅容量（`conditional_parcels.json` + B `C_preliminary`）

| Region | `C_direct` | `C_preliminary` | `C_conditional` (棟) | `C_additional` | `units_conditional` (戶) | `C_upper` | `C_phone_low` | `C_desktop_high` | `C_common` (`CROSS_PRESET_COMMON`) | `prototype_counts` | `proxy_used` | 外部道路接入 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `B1` | 5 | 72 | 21 | 16 | 21 | 100 | 21 | 21 | 21 | `R01:10, R02:11` | false | `FEASIBLE` |
| `B2` | 0 | 278 | 59 | 59 | 59 | 329 | 59 | 59 | 59 | `R05:59` | PROXY（平地代理，非已驗證山坡施工） | `CONDITIONAL` |
| `B3` | 17 | 25 | 17 | 0 | 29 | 40 | 17 | 17 | 17 | `R01:4, R05:9, R08:4` | false | `FEASIBLE` |

## 4. 道路、海灘侵占與工程相依報告

- 既有道路幾何（`map_geometry.json`）：共 `19` 條既有路段；Site A 保護區與建物共 `3` 個多邊形；海灘 `1` 區、水域 `1` 區。
- 可選未驗證延伸連接（`optional_extension_links`）：`AVE_110` 僅列為可選且 `status: UNVERIFIED`，非所有候選道路之必要工程。

### 4.1 逐情境排除道路與衝突地塊（`excluded_sources`）

| Scenario | Excluded Road | C 自身狀態 | D 排除原因 | 衝突直接地塊 ID | 說明 |
| --- | --- | --- | --- | --- | --- |
| `INITIAL` | `none` | — | — | — | 本情境無候選道路因直接地塊衝突遭排除 |
| `ENVELOPE` | `C01` | `CONDITIONAL_VERIFIED` | `DIRECT_PARCEL_CONFLICT` | `B1_R02_005` | 保留直接地塊不刪除或移動；C 自身裁定維持 `CONDITIONAL_VERIFIED` |
| `REVISED` | `C01` | `CONDITIONAL_VERIFIED` | `DIRECT_PARCEL_CONFLICT` | `B1_R02_005` | 保留直接地塊不刪除或移動；C 自身裁定維持 `CONDITIONAL_VERIFIED` |

### 4.2 選定內部街道（未建造／候選工程）

| Scenario | Region | `street_id` | `source_road_id` | `length_m` | `max_grade_pct` | `junction_run_m` | `external_connection` | `dependency_chain` | `verification_status` | `existing` |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `INITIAL` | `B1` | `INITIAL_B1_ST_0135` | `C02` | 150.0 | 0.000% | 6.000 | `J:C01->CRS_880@START` | `C02 -> J:C01<->C02 -> C01 -> J:C01->CRS_880@START` | `CONDITIONAL_VERIFIED` | `False` |
| `INITIAL` | `B1` | `INITIAL_B1_ST_0165` | `C02` | 150.0 | 0.000% | 6.000 | `J:C01->CRS_880@START` | `C02 -> J:C01<->C02 -> C01 -> J:C01->CRS_880@START` | `CONDITIONAL_VERIFIED` | `False` |
| `INITIAL` | `B1` | `INITIAL_B1_ST_0103` | `C01` | 90.0 | 0.000% | 15.000 | `J:C01->CRS_880@START` | `C01 -> J:C01->CRS_880@START` | `CONDITIONAL_VERIFIED` | `False` |
| `INITIAL` | `B2` | `INITIAL_B2_ST_0050` | `H02` | 150.0 | 0.000% | 8.824 | `J:H02->AVE_-240@END` | `H02 -> J:H02->AVE_-240@END` | `CONDITIONAL_VERIFIED` | `False` |
| `INITIAL` | `B2` | `INITIAL_B2_ST_0010` | `H02` | 150.0 | 0.000% | 6.000 | `J:H02->AVE_-240@END` | `H02 -> J:H02->AVE_-240@END` | `CONDITIONAL_VERIFIED` | `False` |
| `INITIAL` | `B2` | `INITIAL_B2_ST_0030` | `H02` | 150.0 | 0.000% | 6.000 | `J:H02->AVE_-240@END` | `H02 -> J:H02->AVE_-240@END` | `CONDITIONAL_VERIFIED` | `False` |
| `ENVELOPE` | `B1` | `ENVELOPE_B1_ST_0085` | `C02` | 150.0 | 0.000% | 6.000 | `J:X01->AVE_-240@START` | `C02 -> J:C02<->X01 -> X01 -> J:X01->AVE_-240@START` | `CONDITIONAL_VERIFIED` | `False` |
| `ENVELOPE` | `B1` | `ENVELOPE_B1_ST_0305` | `X01` | 150.0 | 0.000% | 5.882 | `J:X01->AVE_-240@START` | `X01 -> J:X01->AVE_-240@START` | `CONDITIONAL_VERIFIED` | `False` |
| `ENVELOPE` | `B1` | `ENVELOPE_B1_ST_0115` | `C02` | 150.0 | 0.000% | 6.000 | `J:X01->AVE_-240@START` | `C02 -> J:C02<->X01 -> X01 -> J:X01->AVE_-240@START` | `CONDITIONAL_VERIFIED` | `False` |
| `ENVELOPE` | `B2` | `ENVELOPE_B2_ST_0010` | `H02` | 150.0 | 0.000% | 6.000 | `J:H02->AVE_-240@END` | `H02 -> J:H02->AVE_-240@END` | `CONDITIONAL_VERIFIED` | `False` |
| `ENVELOPE` | `B2` | `ENVELOPE_B2_ST_0040` | `H02` | 150.0 | 0.000% | 8.824 | `J:H02->AVE_-240@END` | `H02 -> J:H02->AVE_-240@END` | `CONDITIONAL_VERIFIED` | `False` |
| `ENVELOPE` | `B2` | `ENVELOPE_B2_ST_0140` | `H02` | 150.0 | 0.000% | 9.000 | `J:H02->AVE_-240@END` | `H02 -> J:H02->AVE_-240@END` | `CONDITIONAL_VERIFIED` | `False` |
| `REVISED` | `B1` | `REVISED_B1_ST_0045` | `C02` | 150.0 | 0.000% | 6.000 | `J:X01->AVE_-240@START` | `C02 -> J:C02<->X01 -> X01 -> J:X01->AVE_-240@START` | `CONDITIONAL_VERIFIED` | `False` |
| `REVISED` | `B1` | `REVISED_B1_ST_0245` | `X01` | 150.0 | 0.000% | 5.882 | `J:X01->AVE_-240@START` | `X01 -> J:X01->AVE_-240@START` | `CONDITIONAL_VERIFIED` | `False` |
| `REVISED` | `B1` | `REVISED_B1_ST_0075` | `C02` | 150.0 | 0.000% | 6.000 | `J:X01->AVE_-240@START` | `C02 -> J:C02<->X01 -> X01 -> J:X01->AVE_-240@START` | `CONDITIONAL_VERIFIED` | `False` |
| `REVISED` | `B2` | `REVISED_B2_ST_0010` | `H02` | 150.0 | 0.000% | 6.000 | `J:H02->AVE_-240@END` | `H02 -> J:H02->AVE_-240@END` | `CONDITIONAL_VERIFIED` | `False` |
| `REVISED` | `B2` | `REVISED_B2_ST_0030` | `H02` | 150.0 | 0.000% | 6.000 | `J:H02->AVE_-240@END` | `H02 -> J:H02->AVE_-240@END` | `CONDITIONAL_VERIFIED` | `False` |
| `REVISED` | `B2` | `REVISED_B2_ST_0130` | `H02` | 150.0 | 0.000% | 9.000 | `J:H02->AVE_-240@END` | `H02 -> J:H02->AVE_-240@END` | `CONDITIONAL_VERIFIED` | `False` |

## 5. 可行性裁定（Feasibility Verdicts）

所有裁定原樣取自 `feasibility.json`，不進行重新計算。`buildings_60` 為理想目標，依 `gates_d3` 欄位單獨呈報且**不作為 `D3` 門控條件**。`UNVERIFIED`（如 `SEARCH_INSUFFICIENT_UNPROVEN`）僅代表搜尋不足、尚未完成可行性證明，不等於已證明不可行。

### 5.1 情境 `INITIAL` 裁定與原始證據

| Verdict Item | Verdict | Targets / Evidence | Reasons |
| --- | --- | --- | --- |
| `land_25ha` | `NOT FEASIBLE WITHIN AUDITED BOUNDARIES` | `A_gross_total`=250,000, `A_possible_total`=208,676, `A_direct_total`=158,580, `A_conditional_total`=0 m² | `PROVEN_AREA_BELOW_25HA` |
| `buildings_40` | `UNVERIFIED` | targets=(B1:10, B2:12, B3:18); C_direct_total=5; C_conditional_total=69; regions_short=B3 | `SEARCH_INSUFFICIENT_UNPROVEN` |
| `buildings_60` | `NOT FEASIBLE WITHIN AUDITED BOUNDARIES` | targets=(B1:14, B2:18, B3:28); gates_d3=False; regions_below_c_upper=B3 | `C_UPPER_BELOW_TARGET` |
| `road_connectivity` | `CONDITIONAL` | per_region_external=(B1:CONDITIONAL, B2:CONDITIONAL, B3:FEASIBLE); `uses_conditional_roads_or_streets`=True | `T-016C + D chains` |
| `D3` | `NOT FEASIBLE WITHIN AUDITED BOUNDARIES` | inputs=(buildings_40:UNVERIFIED, land_25ha:NOT FEASIBLE WITHIN AUDITED BOUNDARIES, road_connectivity:CONDITIONAL) | `worst(land_25ha, buildings_40, road_connectivity)` |

### 5.2 情境 `ENVELOPE` 裁定與原始證據

| Verdict Item | Verdict | Targets / Evidence | Reasons |
| --- | --- | --- | --- |
| `land_25ha` | `CONDITIONAL` | `A_gross_total`=720,000, `A_possible_total`=549,215, `A_direct_total`=401,269, `A_conditional_total`=0 m² | `CONDITIONAL_LAND_AND_LAYOUTS_MET` |
| `buildings_40` | `CONDITIONAL` | targets=(B1:10, B2:12, B3:18); C_direct_total=30; C_conditional_total=113 | `ALL_REGIONS_CONDITIONAL_MET` |
| `buildings_60` | `UNVERIFIED` | targets=(B1:14, B2:18, B3:28); gates_d3=False; regions_short=B3 | `SEARCH_INSUFFICIENT_UNPROVEN` |
| `road_connectivity` | `CONDITIONAL` | per_region_external=(B1:FEASIBLE, B2:CONDITIONAL, B3:FEASIBLE); `uses_conditional_roads_or_streets`=True | `T-016C + D chains` |
| `D3` | `CONDITIONAL` | inputs=(buildings_40:CONDITIONAL, land_25ha:CONDITIONAL, road_connectivity:CONDITIONAL) | `worst(land_25ha, buildings_40, road_connectivity)` |

### 5.3 情境 `REVISED` 裁定與原始證據

| Verdict Item | Verdict | Targets / Evidence | Reasons |
| --- | --- | --- | --- |
| `land_25ha` | `CONDITIONAL` | `A_gross_total`=415,000, `A_possible_total`=378,314, `A_direct_total`=305,858, `A_conditional_total`=0 m² | `CONDITIONAL_LAND_AND_LAYOUTS_MET` |
| `buildings_40` | `UNVERIFIED` | targets=(B1:10, B2:12, B3:18); C_direct_total=22; C_conditional_total=97; regions_short=B3 | `SEARCH_INSUFFICIENT_UNPROVEN` |
| `buildings_60` | `UNVERIFIED` | targets=(B1:14, B2:18, B3:28); gates_d3=False; regions_short=B3 | `SEARCH_INSUFFICIENT_UNPROVEN` |
| `road_connectivity` | `CONDITIONAL` | per_region_external=(B1:FEASIBLE, B2:CONDITIONAL, B3:FEASIBLE); `uses_conditional_roads_or_streets`=True | `T-016C + D chains` |
| `D3` | `UNVERIFIED` | inputs=(buildings_40:UNVERIFIED, land_25ha:CONDITIONAL, road_connectivity:CONDITIONAL) | `worst(land_25ha, buildings_40, road_connectivity)` |

## 6. 效能基準狀態（Gate B8）

Gate B8 尚待 Claude 完成正式量測，本報告不代表新增住宅已達效能目標。

T-016E 為純離線唯讀報告建構工具，不執行遊戲 runtime 效能量測，亦不使用估計 FPS 或 headless FPS 取代實測數據。

### 6.1 Gate B8 正式量測附錄引用（待 Claude 合併 E 後獨立量測補附）

- 狀態：`PENDING`（由 Claude 依 WE-01 v1.2 §13 於 `PHONE_LOW` / `TABLET_MED` / `DESKTOP_HIGH` 六處地點量測後另附獨立 B8 附錄，不手改本確定性報告）。

## 7. WE-02–WE-09 後續工程建議（僅為建議，未授權）

以下項目**僅為基於本次審計 JSON 證據之後續研究建議，尚未登記任務，亦未獲任何施工或製作授權**：

1. **低於目標分區之額外合法地塊或候選區邊界研究**：針對處於 `UNVERIFIED`（搜尋不足，未證明不可行）之分區，評估是否以替代街道幾何或候選邊界修訂提升可達容量。
2. **直接地塊衝突道路替代方案**：針對配置衝突遭排除之外部候選道路（`C01`），評估改線或保留既有接點方案。
3. **山坡地形與地基工程研究**：針對平地代理分區（`B2` `PROXY`）及 `NOT_FEASIBLE` 道路（`H01`），另案研究地形整地、地基與線型工程。
4. **海灘景觀保護與可選延伸連接權衡**：檢視候選道路海灘侵占與景觀保留取捨，以及可選未驗證延伸（`AVE_110`）之獨立可行性。
5. **區域串流與住宅 LOD 規劃**：配合未來 Gate B8 實測基準評估行動裝置繪製與物理負載。
6. **`ENVELOPE` 與 `REVISED` 範圍比較**：比較外框條件可行方案與修訂方案之土地與工程需求，再由專案擁有者決定後續方向。

## 8. 附錄：各情境地塊明細（Parcel Appendix）

### 8.1 情境 `INITIAL` 地塊清單

| Region | `parcel_id` | `prototype_id` | `status` | `buildings` | `units` | `source_road_id` | `internal_street_id` | `dependency_chain` |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `B1` | `B1_R02_001` | `R02` | `INTERNAL_STREET_REQUIRED` | 1 | 1 | `C02` | `INITIAL_B1_ST_0135` | `INITIAL_B1_ST_0135 -> C02 -> J:C01<->C02 -> C01 -> J:C01->CRS_880@START` |
| `B1` | `B1_R01_002` | `R01` | `CANDIDATE_ROAD_REQUIRED` | 1 | 1 | `C02` | `none` | `C02 -> J:C01<->C02 -> C01 -> J:C01->CRS_880@START` |
| `B1` | `B1_R02_003` | `R02` | `INTERNAL_STREET_REQUIRED` | 1 | 1 | `C02` | `INITIAL_B1_ST_0135` | `INITIAL_B1_ST_0135 -> C02 -> J:C01<->C02 -> C01 -> J:C01->CRS_880@START` |
| `B1` | `B1_R01_004` | `R01` | `INTERNAL_STREET_REQUIRED` | 1 | 1 | `C02` | `INITIAL_B1_ST_0135` | `INITIAL_B1_ST_0135 -> C02 -> J:C01<->C02 -> C01 -> J:C01->CRS_880@START` |
| `B1` | `B1_R02_005` | `R02` | `INTERNAL_STREET_REQUIRED` | 1 | 1 | `C02` | `INITIAL_B1_ST_0135` | `INITIAL_B1_ST_0135 -> C02 -> J:C01<->C02 -> C01 -> J:C01->CRS_880@START` |
| `B1` | `B1_R01_006` | `R01` | `INTERNAL_STREET_REQUIRED` | 1 | 1 | `C02` | `INITIAL_B1_ST_0135` | `INITIAL_B1_ST_0135 -> C02 -> J:C01<->C02 -> C01 -> J:C01->CRS_880@START` |
| `B1` | `B1_R02_007` | `R02` | `INTERNAL_STREET_REQUIRED` | 1 | 1 | `C02` | `INITIAL_B1_ST_0135` | `INITIAL_B1_ST_0135 -> C02 -> J:C01<->C02 -> C01 -> J:C01->CRS_880@START` |
| `B1` | `B1_R01_008` | `R01` | `INTERNAL_STREET_REQUIRED` | 1 | 1 | `C02` | `INITIAL_B1_ST_0135` | `INITIAL_B1_ST_0135 -> C02 -> J:C01<->C02 -> C01 -> J:C01->CRS_880@START` |
| `B1` | `B1_R02_009` | `R02` | `CANDIDATE_ROAD_REQUIRED` | 1 | 1 | `C01` | `none` | `C01 -> J:C01->CRS_880@START` |
| `B1` | `B1_R01_010` | `R01` | `INTERNAL_STREET_REQUIRED` | 1 | 1 | `C02` | `INITIAL_B1_ST_0165` | `INITIAL_B1_ST_0165 -> C02 -> J:C01<->C02 -> C01 -> J:C01->CRS_880@START` |
| `B1` | `B1_R02_011` | `R02` | `INTERNAL_STREET_REQUIRED` | 1 | 1 | `C01` | `INITIAL_B1_ST_0103` | `INITIAL_B1_ST_0103 -> C01 -> J:C01->CRS_880@START` |
| `B1` | `B1_R01_012` | `R01` | `CANDIDATE_ROAD_REQUIRED` | 1 | 1 | `C01` | `none` | `C01 -> J:C01->CRS_880@START` |
| `B1` | `B1_R02_013` | `R02` | `CANDIDATE_ROAD_REQUIRED` | 1 | 1 | `C01` | `none` | `C01 -> J:C01->CRS_880@START` |
| `B1` | `B1_R01_014` | `R01` | `INTERNAL_STREET_REQUIRED` | 1 | 1 | `C01` | `INITIAL_B1_ST_0103` | `INITIAL_B1_ST_0103 -> C01 -> J:C01->CRS_880@START` |
| `B2` | `B2_R05_001` | `R05` | `INTERNAL_STREET_REQUIRED` | 1 | 1 | `H02` | `INITIAL_B2_ST_0050` | `INITIAL_B2_ST_0050 -> H02 -> J:H02->AVE_-240@END` |
| `B2` | `B2_R05_002` | `R05` | `INTERNAL_STREET_REQUIRED` | 1 | 1 | `H02` | `INITIAL_B2_ST_0030` | `INITIAL_B2_ST_0030 -> H02 -> J:H02->AVE_-240@END` |
| `B2` | `B2_R05_003` | `R05` | `INTERNAL_STREET_REQUIRED` | 1 | 1 | `H02` | `INITIAL_B2_ST_0010` | `INITIAL_B2_ST_0010 -> H02 -> J:H02->AVE_-240@END` |
| `B2` | `B2_R05_004` | `R05` | `INTERNAL_STREET_REQUIRED` | 1 | 1 | `H02` | `INITIAL_B2_ST_0050` | `INITIAL_B2_ST_0050 -> H02 -> J:H02->AVE_-240@END` |
| `B2` | `B2_R05_005` | `R05` | `INTERNAL_STREET_REQUIRED` | 1 | 1 | `H02` | `INITIAL_B2_ST_0030` | `INITIAL_B2_ST_0030 -> H02 -> J:H02->AVE_-240@END` |
| `B2` | `B2_R05_006` | `R05` | `INTERNAL_STREET_REQUIRED` | 1 | 1 | `H02` | `INITIAL_B2_ST_0010` | `INITIAL_B2_ST_0010 -> H02 -> J:H02->AVE_-240@END` |
| `B2` | `B2_R05_007` | `R05` | `INTERNAL_STREET_REQUIRED` | 1 | 1 | `H02` | `INITIAL_B2_ST_0010` | `INITIAL_B2_ST_0010 -> H02 -> J:H02->AVE_-240@END` |
| `B2` | `B2_R05_008` | `R05` | `INTERNAL_STREET_REQUIRED` | 1 | 1 | `H02` | `INITIAL_B2_ST_0050` | `INITIAL_B2_ST_0050 -> H02 -> J:H02->AVE_-240@END` |
| `B2` | `B2_R05_009` | `R05` | `INTERNAL_STREET_REQUIRED` | 1 | 1 | `H02` | `INITIAL_B2_ST_0030` | `INITIAL_B2_ST_0030 -> H02 -> J:H02->AVE_-240@END` |
| `B2` | `B2_R05_010` | `R05` | `INTERNAL_STREET_REQUIRED` | 1 | 1 | `H02` | `INITIAL_B2_ST_0010` | `INITIAL_B2_ST_0010 -> H02 -> J:H02->AVE_-240@END` |
| `B2` | `B2_R05_011` | `R05` | `INTERNAL_STREET_REQUIRED` | 1 | 1 | `H02` | `INITIAL_B2_ST_0010` | `INITIAL_B2_ST_0010 -> H02 -> J:H02->AVE_-240@END` |
| `B2` | `B2_R05_012` | `R05` | `INTERNAL_STREET_REQUIRED` | 1 | 1 | `H02` | `INITIAL_B2_ST_0050` | `INITIAL_B2_ST_0050 -> H02 -> J:H02->AVE_-240@END` |
| `B2` | `B2_R05_013` | `R05` | `INTERNAL_STREET_REQUIRED` | 1 | 1 | `H02` | `INITIAL_B2_ST_0030` | `INITIAL_B2_ST_0030 -> H02 -> J:H02->AVE_-240@END` |
| `B2` | `B2_R05_014` | `R05` | `INTERNAL_STREET_REQUIRED` | 1 | 1 | `H02` | `INITIAL_B2_ST_0010` | `INITIAL_B2_ST_0010 -> H02 -> J:H02->AVE_-240@END` |
| `B2` | `B2_R05_015` | `R05` | `INTERNAL_STREET_REQUIRED` | 1 | 1 | `H02` | `INITIAL_B2_ST_0010` | `INITIAL_B2_ST_0010 -> H02 -> J:H02->AVE_-240@END` |
| `B2` | `B2_R05_016` | `R05` | `INTERNAL_STREET_REQUIRED` | 1 | 1 | `H02` | `INITIAL_B2_ST_0050` | `INITIAL_B2_ST_0050 -> H02 -> J:H02->AVE_-240@END` |
| `B2` | `B2_R05_017` | `R05` | `INTERNAL_STREET_REQUIRED` | 1 | 1 | `H02` | `INITIAL_B2_ST_0030` | `INITIAL_B2_ST_0030 -> H02 -> J:H02->AVE_-240@END` |
| `B2` | `B2_R05_018` | `R05` | `INTERNAL_STREET_REQUIRED` | 1 | 1 | `H02` | `INITIAL_B2_ST_0010` | `INITIAL_B2_ST_0010 -> H02 -> J:H02->AVE_-240@END` |
| `B2` | `B2_R05_019` | `R05` | `INTERNAL_STREET_REQUIRED` | 1 | 1 | `H02` | `INITIAL_B2_ST_0010` | `INITIAL_B2_ST_0010 -> H02 -> J:H02->AVE_-240@END` |
| `B2` | `B2_R05_020` | `R05` | `INTERNAL_STREET_REQUIRED` | 1 | 1 | `H02` | `INITIAL_B2_ST_0050` | `INITIAL_B2_ST_0050 -> H02 -> J:H02->AVE_-240@END` |
| `B2` | `B2_R05_021` | `R05` | `INTERNAL_STREET_REQUIRED` | 1 | 1 | `H02` | `INITIAL_B2_ST_0030` | `INITIAL_B2_ST_0030 -> H02 -> J:H02->AVE_-240@END` |
| `B2` | `B2_R05_022` | `R05` | `INTERNAL_STREET_REQUIRED` | 1 | 1 | `H02` | `INITIAL_B2_ST_0010` | `INITIAL_B2_ST_0010 -> H02 -> J:H02->AVE_-240@END` |
| `B2` | `B2_R05_023` | `R05` | `INTERNAL_STREET_REQUIRED` | 1 | 1 | `H02` | `INITIAL_B2_ST_0010` | `INITIAL_B2_ST_0010 -> H02 -> J:H02->AVE_-240@END` |
| `B2` | `B2_R05_024` | `R05` | `INTERNAL_STREET_REQUIRED` | 1 | 1 | `H02` | `INITIAL_B2_ST_0050` | `INITIAL_B2_ST_0050 -> H02 -> J:H02->AVE_-240@END` |
| `B2` | `B2_R05_025` | `R05` | `INTERNAL_STREET_REQUIRED` | 1 | 1 | `H02` | `INITIAL_B2_ST_0030` | `INITIAL_B2_ST_0030 -> H02 -> J:H02->AVE_-240@END` |
| `B2` | `B2_R05_026` | `R05` | `INTERNAL_STREET_REQUIRED` | 1 | 1 | `H02` | `INITIAL_B2_ST_0010` | `INITIAL_B2_ST_0010 -> H02 -> J:H02->AVE_-240@END` |
| `B2` | `B2_R05_027` | `R05` | `CANDIDATE_ROAD_REQUIRED` | 1 | 1 | `H02` | `none` | `H02 -> J:H02->AVE_-240@END` |
| `B2` | `B2_R05_028` | `R05` | `CANDIDATE_ROAD_REQUIRED` | 1 | 1 | `H02` | `none` | `H02 -> J:H02->AVE_-240@END` |
| `B2` | `B2_R05_029` | `R05` | `CANDIDATE_ROAD_REQUIRED` | 1 | 1 | `H02` | `none` | `H02 -> J:H02->AVE_-240@END` |
| `B2` | `B2_R05_030` | `R05` | `CANDIDATE_ROAD_REQUIRED` | 1 | 1 | `H02` | `none` | `H02 -> J:H02->AVE_-240@END` |
| `B2` | `B2_R05_031` | `R05` | `CANDIDATE_ROAD_REQUIRED` | 1 | 1 | `H02` | `none` | `H02 -> J:H02->AVE_-240@END` |
| `B2` | `B2_R05_032` | `R05` | `CANDIDATE_ROAD_REQUIRED` | 1 | 1 | `H02` | `none` | `H02 -> J:H02->AVE_-240@END` |
| `B2` | `B2_R05_033` | `R05` | `CANDIDATE_ROAD_REQUIRED` | 1 | 1 | `H02` | `none` | `H02 -> J:H02->AVE_-240@END` |
| `B2` | `B2_R05_034` | `R05` | `INTERNAL_STREET_REQUIRED` | 1 | 1 | `H02` | `INITIAL_B2_ST_0010` | `INITIAL_B2_ST_0010 -> H02 -> J:H02->AVE_-240@END` |
| `B2` | `B2_R05_035` | `R05` | `INTERNAL_STREET_REQUIRED` | 1 | 1 | `H02` | `INITIAL_B2_ST_0050` | `INITIAL_B2_ST_0050 -> H02 -> J:H02->AVE_-240@END` |
| `B2` | `B2_R05_036` | `R05` | `INTERNAL_STREET_REQUIRED` | 1 | 1 | `H02` | `INITIAL_B2_ST_0030` | `INITIAL_B2_ST_0030 -> H02 -> J:H02->AVE_-240@END` |
| `B2` | `B2_R05_037` | `R05` | `INTERNAL_STREET_REQUIRED` | 1 | 1 | `H02` | `INITIAL_B2_ST_0010` | `INITIAL_B2_ST_0010 -> H02 -> J:H02->AVE_-240@END` |
| `B2` | `B2_R05_038` | `R05` | `INTERNAL_STREET_REQUIRED` | 1 | 1 | `H02` | `INITIAL_B2_ST_0010` | `INITIAL_B2_ST_0010 -> H02 -> J:H02->AVE_-240@END` |
| `B2` | `B2_R05_039` | `R05` | `CANDIDATE_ROAD_REQUIRED` | 1 | 1 | `H02` | `none` | `H02 -> J:H02->AVE_-240@END` |
| `B2` | `B2_R05_040` | `R05` | `CANDIDATE_ROAD_REQUIRED` | 1 | 1 | `H02` | `none` | `H02 -> J:H02->AVE_-240@END` |
| `B2` | `B2_R05_041` | `R05` | `CANDIDATE_ROAD_REQUIRED` | 1 | 1 | `H02` | `none` | `H02 -> J:H02->AVE_-240@END` |
| `B2` | `B2_R05_042` | `R05` | `CANDIDATE_ROAD_REQUIRED` | 1 | 1 | `H02` | `none` | `H02 -> J:H02->AVE_-240@END` |
| `B2` | `B2_R05_043` | `R05` | `CANDIDATE_ROAD_REQUIRED` | 1 | 1 | `H02` | `none` | `H02 -> J:H02->AVE_-240@END` |
| `B2` | `B2_R05_044` | `R05` | `CANDIDATE_ROAD_REQUIRED` | 1 | 1 | `H02` | `none` | `H02 -> J:H02->AVE_-240@END` |
| `B2` | `B2_R05_045` | `R05` | `CANDIDATE_ROAD_REQUIRED` | 1 | 1 | `H02` | `none` | `H02 -> J:H02->AVE_-240@END` |
| `B2` | `B2_R05_046` | `R05` | `CANDIDATE_ROAD_REQUIRED` | 1 | 1 | `H02` | `none` | `H02 -> J:H02->AVE_-240@END` |
| `B2` | `B2_R05_047` | `R05` | `CANDIDATE_ROAD_REQUIRED` | 1 | 1 | `H02` | `none` | `H02 -> J:H02->AVE_-240@END` |
| `B2` | `B2_R05_048` | `R05` | `CANDIDATE_ROAD_REQUIRED` | 1 | 1 | `H02` | `none` | `H02 -> J:H02->AVE_-240@END` |
| `B2` | `B2_R05_049` | `R05` | `CANDIDATE_ROAD_REQUIRED` | 1 | 1 | `H02` | `none` | `H02 -> J:H02->AVE_-240@END` |
| `B2` | `B2_R05_050` | `R05` | `CANDIDATE_ROAD_REQUIRED` | 1 | 1 | `H02` | `none` | `H02 -> J:H02->AVE_-240@END` |
| `B3` | `B3_R01_001` | `R01` | `DIRECT` | 1 | 1 | `AVE_-420` | `none` | `none` |
| `B3` | `B3_R08_002` | `R08` | `DIRECT` | 1 | 4 | `AVE_-420` | `none` | `none` |
| `B3` | `B3_R05_003` | `R05` | `DIRECT` | 1 | 1 | `AVE_-600` | `none` | `none` |
| `B3` | `B3_R05_004` | `R05` | `DIRECT` | 1 | 1 | `AVE_-600` | `none` | `none` |
| `B3` | `B3_R05_005` | `R05` | `DIRECT` | 1 | 1 | `CRS_-720` | `none` | `none` |

### 8.2 情境 `ENVELOPE` 地塊清單

| Region | `parcel_id` | `prototype_id` | `status` | `buildings` | `units` | `source_road_id` | `internal_street_id` | `dependency_chain` |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `B1` | `B1_R02_001` | `R02` | `DIRECT` | 1 | 1 | `CRS_880` | `none` | `none` |
| `B1` | `B1_R01_002` | `R01` | `DIRECT` | 1 | 1 | `CRS_880` | `none` | `none` |
| `B1` | `B1_R02_003` | `R02` | `DIRECT` | 1 | 1 | `CRS_880` | `none` | `none` |
| `B1` | `B1_R01_004` | `R01` | `DIRECT` | 1 | 1 | `CRS_880` | `none` | `none` |
| `B1` | `B1_R02_005` | `R02` | `DIRECT` | 1 | 1 | `CRS_880` | `none` | `none` |
| `B1` | `B1_R01_006` | `R01` | `CANDIDATE_ROAD_REQUIRED` | 1 | 1 | `X01` | `none` | `X01 -> J:X01->AVE_-240@START` |
| `B1` | `B1_R02_007` | `R02` | `INTERNAL_STREET_REQUIRED` | 1 | 1 | `X01` | `ENVELOPE_B1_ST_0305` | `ENVELOPE_B1_ST_0305 -> X01 -> J:X01->AVE_-240@START` |
| `B1` | `B1_R01_008` | `R01` | `INTERNAL_STREET_REQUIRED` | 1 | 1 | `C02` | `ENVELOPE_B1_ST_0085` | `ENVELOPE_B1_ST_0085 -> C02 -> J:C02<->X01 -> X01 -> J:X01->AVE_-240@START` |
| `B1` | `B1_R02_009` | `R02` | `INTERNAL_STREET_REQUIRED` | 1 | 1 | `X01` | `ENVELOPE_B1_ST_0305` | `ENVELOPE_B1_ST_0305 -> X01 -> J:X01->AVE_-240@START` |
| `B1` | `B1_R01_010` | `R01` | `INTERNAL_STREET_REQUIRED` | 1 | 1 | `C02` | `ENVELOPE_B1_ST_0115` | `ENVELOPE_B1_ST_0115 -> C02 -> J:C02<->X01 -> X01 -> J:X01->AVE_-240@START` |
| `B1` | `B1_R02_011` | `R02` | `INTERNAL_STREET_REQUIRED` | 1 | 1 | `C02` | `ENVELOPE_B1_ST_0085` | `ENVELOPE_B1_ST_0085 -> C02 -> J:C02<->X01 -> X01 -> J:X01->AVE_-240@START` |
| `B1` | `B1_R01_012` | `R01` | `INTERNAL_STREET_REQUIRED` | 1 | 1 | `X01` | `ENVELOPE_B1_ST_0305` | `ENVELOPE_B1_ST_0305 -> X01 -> J:X01->AVE_-240@START` |
| `B1` | `B1_R02_013` | `R02` | `INTERNAL_STREET_REQUIRED` | 1 | 1 | `X01` | `ENVELOPE_B1_ST_0305` | `ENVELOPE_B1_ST_0305 -> X01 -> J:X01->AVE_-240@START` |
| `B1` | `B1_R01_014` | `R01` | `INTERNAL_STREET_REQUIRED` | 1 | 1 | `C02` | `ENVELOPE_B1_ST_0115` | `ENVELOPE_B1_ST_0115 -> C02 -> J:C02<->X01 -> X01 -> J:X01->AVE_-240@START` |
| `B1` | `B1_R02_015` | `R02` | `INTERNAL_STREET_REQUIRED` | 1 | 1 | `X01` | `ENVELOPE_B1_ST_0305` | `ENVELOPE_B1_ST_0305 -> X01 -> J:X01->AVE_-240@START` |
| `B1` | `B1_R01_016` | `R01` | `INTERNAL_STREET_REQUIRED` | 1 | 1 | `C02` | `ENVELOPE_B1_ST_0085` | `ENVELOPE_B1_ST_0085 -> C02 -> J:C02<->X01 -> X01 -> J:X01->AVE_-240@START` |
| `B1` | `B1_R02_017` | `R02` | `INTERNAL_STREET_REQUIRED` | 1 | 1 | `C02` | `ENVELOPE_B1_ST_0085` | `ENVELOPE_B1_ST_0085 -> C02 -> J:C02<->X01 -> X01 -> J:X01->AVE_-240@START` |
| `B1` | `B1_R01_018` | `R01` | `INTERNAL_STREET_REQUIRED` | 1 | 1 | `C02` | `ENVELOPE_B1_ST_0115` | `ENVELOPE_B1_ST_0115 -> C02 -> J:C02<->X01 -> X01 -> J:X01->AVE_-240@START` |
| `B1` | `B1_R02_019` | `R02` | `INTERNAL_STREET_REQUIRED` | 1 | 1 | `X01` | `ENVELOPE_B1_ST_0305` | `ENVELOPE_B1_ST_0305 -> X01 -> J:X01->AVE_-240@START` |
| `B1` | `B1_R01_020` | `R01` | `INTERNAL_STREET_REQUIRED` | 1 | 1 | `X01` | `ENVELOPE_B1_ST_0305` | `ENVELOPE_B1_ST_0305 -> X01 -> J:X01->AVE_-240@START` |
| `B1` | `B1_R02_021` | `R02` | `INTERNAL_STREET_REQUIRED` | 1 | 1 | `C02` | `ENVELOPE_B1_ST_0115` | `ENVELOPE_B1_ST_0115 -> C02 -> J:C02<->X01 -> X01 -> J:X01->AVE_-240@START` |
| `B2` | `B2_R05_001` | `R05` | `INTERNAL_STREET_REQUIRED` | 1 | 1 | `H02` | `ENVELOPE_B2_ST_0140` | `ENVELOPE_B2_ST_0140 -> H02 -> J:H02->AVE_-240@END` |
| `B2` | `B2_R05_002` | `R05` | `INTERNAL_STREET_REQUIRED` | 1 | 1 | `H02` | `ENVELOPE_B2_ST_0140` | `ENVELOPE_B2_ST_0140 -> H02 -> J:H02->AVE_-240@END` |
| `B2` | `B2_R05_003` | `R05` | `INTERNAL_STREET_REQUIRED` | 1 | 1 | `H02` | `ENVELOPE_B2_ST_0040` | `ENVELOPE_B2_ST_0040 -> H02 -> J:H02->AVE_-240@END` |
| `B2` | `B2_R05_004` | `R05` | `INTERNAL_STREET_REQUIRED` | 1 | 1 | `H02` | `ENVELOPE_B2_ST_0140` | `ENVELOPE_B2_ST_0140 -> H02 -> J:H02->AVE_-240@END` |
| `B2` | `B2_R05_005` | `R05` | `INTERNAL_STREET_REQUIRED` | 1 | 1 | `H02` | `ENVELOPE_B2_ST_0010` | `ENVELOPE_B2_ST_0010 -> H02 -> J:H02->AVE_-240@END` |
| `B2` | `B2_R05_006` | `R05` | `INTERNAL_STREET_REQUIRED` | 1 | 1 | `H02` | `ENVELOPE_B2_ST_0040` | `ENVELOPE_B2_ST_0040 -> H02 -> J:H02->AVE_-240@END` |
| `B2` | `B2_R05_007` | `R05` | `INTERNAL_STREET_REQUIRED` | 1 | 1 | `H02` | `ENVELOPE_B2_ST_0140` | `ENVELOPE_B2_ST_0140 -> H02 -> J:H02->AVE_-240@END` |
| `B2` | `B2_R05_008` | `R05` | `INTERNAL_STREET_REQUIRED` | 1 | 1 | `H02` | `ENVELOPE_B2_ST_0010` | `ENVELOPE_B2_ST_0010 -> H02 -> J:H02->AVE_-240@END` |
| `B2` | `B2_R05_009` | `R05` | `INTERNAL_STREET_REQUIRED` | 1 | 1 | `H02` | `ENVELOPE_B2_ST_0040` | `ENVELOPE_B2_ST_0040 -> H02 -> J:H02->AVE_-240@END` |
| `B2` | `B2_R05_010` | `R05` | `INTERNAL_STREET_REQUIRED` | 1 | 1 | `H02` | `ENVELOPE_B2_ST_0140` | `ENVELOPE_B2_ST_0140 -> H02 -> J:H02->AVE_-240@END` |
| `B2` | `B2_R05_011` | `R05` | `INTERNAL_STREET_REQUIRED` | 1 | 1 | `H02` | `ENVELOPE_B2_ST_0010` | `ENVELOPE_B2_ST_0010 -> H02 -> J:H02->AVE_-240@END` |
| `B2` | `B2_R05_012` | `R05` | `INTERNAL_STREET_REQUIRED` | 1 | 1 | `H02` | `ENVELOPE_B2_ST_0040` | `ENVELOPE_B2_ST_0040 -> H02 -> J:H02->AVE_-240@END` |
| `B2` | `B2_R05_013` | `R05` | `INTERNAL_STREET_REQUIRED` | 1 | 1 | `H02` | `ENVELOPE_B2_ST_0140` | `ENVELOPE_B2_ST_0140 -> H02 -> J:H02->AVE_-240@END` |
| `B2` | `B2_R05_014` | `R05` | `INTERNAL_STREET_REQUIRED` | 1 | 1 | `H02` | `ENVELOPE_B2_ST_0010` | `ENVELOPE_B2_ST_0010 -> H02 -> J:H02->AVE_-240@END` |
| `B2` | `B2_R05_015` | `R05` | `INTERNAL_STREET_REQUIRED` | 1 | 1 | `H02` | `ENVELOPE_B2_ST_0040` | `ENVELOPE_B2_ST_0040 -> H02 -> J:H02->AVE_-240@END` |
| `B2` | `B2_R05_016` | `R05` | `INTERNAL_STREET_REQUIRED` | 1 | 1 | `H02` | `ENVELOPE_B2_ST_0140` | `ENVELOPE_B2_ST_0140 -> H02 -> J:H02->AVE_-240@END` |
| `B2` | `B2_R05_017` | `R05` | `INTERNAL_STREET_REQUIRED` | 1 | 1 | `H02` | `ENVELOPE_B2_ST_0010` | `ENVELOPE_B2_ST_0010 -> H02 -> J:H02->AVE_-240@END` |
| `B2` | `B2_R05_018` | `R05` | `INTERNAL_STREET_REQUIRED` | 1 | 1 | `H02` | `ENVELOPE_B2_ST_0040` | `ENVELOPE_B2_ST_0040 -> H02 -> J:H02->AVE_-240@END` |
| `B2` | `B2_R05_019` | `R05` | `INTERNAL_STREET_REQUIRED` | 1 | 1 | `H02` | `ENVELOPE_B2_ST_0140` | `ENVELOPE_B2_ST_0140 -> H02 -> J:H02->AVE_-240@END` |
| `B2` | `B2_R05_020` | `R05` | `INTERNAL_STREET_REQUIRED` | 1 | 1 | `H02` | `ENVELOPE_B2_ST_0010` | `ENVELOPE_B2_ST_0010 -> H02 -> J:H02->AVE_-240@END` |
| `B2` | `B2_R05_021` | `R05` | `INTERNAL_STREET_REQUIRED` | 1 | 1 | `H02` | `ENVELOPE_B2_ST_0040` | `ENVELOPE_B2_ST_0040 -> H02 -> J:H02->AVE_-240@END` |
| `B2` | `B2_R05_022` | `R05` | `INTERNAL_STREET_REQUIRED` | 1 | 1 | `H02` | `ENVELOPE_B2_ST_0140` | `ENVELOPE_B2_ST_0140 -> H02 -> J:H02->AVE_-240@END` |
| `B2` | `B2_R05_023` | `R05` | `INTERNAL_STREET_REQUIRED` | 1 | 1 | `H02` | `ENVELOPE_B2_ST_0010` | `ENVELOPE_B2_ST_0010 -> H02 -> J:H02->AVE_-240@END` |
| `B2` | `B2_R05_024` | `R05` | `INTERNAL_STREET_REQUIRED` | 1 | 1 | `H02` | `ENVELOPE_B2_ST_0040` | `ENVELOPE_B2_ST_0040 -> H02 -> J:H02->AVE_-240@END` |
| `B2` | `B2_R05_025` | `R05` | `INTERNAL_STREET_REQUIRED` | 1 | 1 | `H02` | `ENVELOPE_B2_ST_0140` | `ENVELOPE_B2_ST_0140 -> H02 -> J:H02->AVE_-240@END` |
| `B2` | `B2_R05_026` | `R05` | `INTERNAL_STREET_REQUIRED` | 1 | 1 | `H02` | `ENVELOPE_B2_ST_0010` | `ENVELOPE_B2_ST_0010 -> H02 -> J:H02->AVE_-240@END` |
| `B2` | `B2_R05_027` | `R05` | `INTERNAL_STREET_REQUIRED` | 1 | 1 | `H02` | `ENVELOPE_B2_ST_0040` | `ENVELOPE_B2_ST_0040 -> H02 -> J:H02->AVE_-240@END` |
| `B2` | `B2_R05_028` | `R05` | `INTERNAL_STREET_REQUIRED` | 1 | 1 | `H02` | `ENVELOPE_B2_ST_0140` | `ENVELOPE_B2_ST_0140 -> H02 -> J:H02->AVE_-240@END` |
| `B2` | `B2_R05_029` | `R05` | `INTERNAL_STREET_REQUIRED` | 1 | 1 | `H02` | `ENVELOPE_B2_ST_0010` | `ENVELOPE_B2_ST_0010 -> H02 -> J:H02->AVE_-240@END` |
| `B2` | `B2_R05_030` | `R05` | `INTERNAL_STREET_REQUIRED` | 1 | 1 | `H02` | `ENVELOPE_B2_ST_0040` | `ENVELOPE_B2_ST_0040 -> H02 -> J:H02->AVE_-240@END` |
| `B2` | `B2_R05_031` | `R05` | `INTERNAL_STREET_REQUIRED` | 1 | 1 | `H02` | `ENVELOPE_B2_ST_0140` | `ENVELOPE_B2_ST_0140 -> H02 -> J:H02->AVE_-240@END` |
| `B2` | `B2_R05_032` | `R05` | `INTERNAL_STREET_REQUIRED` | 1 | 1 | `H02` | `ENVELOPE_B2_ST_0010` | `ENVELOPE_B2_ST_0010 -> H02 -> J:H02->AVE_-240@END` |
| `B2` | `B2_R05_033` | `R05` | `INTERNAL_STREET_REQUIRED` | 1 | 1 | `H02` | `ENVELOPE_B2_ST_0040` | `ENVELOPE_B2_ST_0040 -> H02 -> J:H02->AVE_-240@END` |
| `B2` | `B2_R05_034` | `R05` | `INTERNAL_STREET_REQUIRED` | 1 | 1 | `H02` | `ENVELOPE_B2_ST_0140` | `ENVELOPE_B2_ST_0140 -> H02 -> J:H02->AVE_-240@END` |
| `B2` | `B2_R05_035` | `R05` | `INTERNAL_STREET_REQUIRED` | 1 | 1 | `H02` | `ENVELOPE_B2_ST_0010` | `ENVELOPE_B2_ST_0010 -> H02 -> J:H02->AVE_-240@END` |
| `B2` | `B2_R05_036` | `R05` | `INTERNAL_STREET_REQUIRED` | 1 | 1 | `H02` | `ENVELOPE_B2_ST_0040` | `ENVELOPE_B2_ST_0040 -> H02 -> J:H02->AVE_-240@END` |
| `B2` | `B2_R05_037` | `R05` | `CANDIDATE_ROAD_REQUIRED` | 1 | 1 | `H02` | `none` | `H02 -> J:H02->AVE_-240@END` |
| `B2` | `B2_R05_038` | `R05` | `INTERNAL_STREET_REQUIRED` | 1 | 1 | `H02` | `ENVELOPE_B2_ST_0140` | `ENVELOPE_B2_ST_0140 -> H02 -> J:H02->AVE_-240@END` |
| `B2` | `B2_R05_039` | `R05` | `INTERNAL_STREET_REQUIRED` | 1 | 1 | `H02` | `ENVELOPE_B2_ST_0010` | `ENVELOPE_B2_ST_0010 -> H02 -> J:H02->AVE_-240@END` |
| `B2` | `B2_R05_040` | `R05` | `CANDIDATE_ROAD_REQUIRED` | 1 | 1 | `H02` | `none` | `H02 -> J:H02->AVE_-240@END` |
| `B2` | `B2_R05_041` | `R05` | `CANDIDATE_ROAD_REQUIRED` | 1 | 1 | `H02` | `none` | `H02 -> J:H02->AVE_-240@END` |
| `B2` | `B2_R05_042` | `R05` | `CANDIDATE_ROAD_REQUIRED` | 1 | 1 | `H02` | `none` | `H02 -> J:H02->AVE_-240@END` |
| `B2` | `B2_R05_043` | `R05` | `INTERNAL_STREET_REQUIRED` | 1 | 1 | `H02` | `ENVELOPE_B2_ST_0040` | `ENVELOPE_B2_ST_0040 -> H02 -> J:H02->AVE_-240@END` |
| `B2` | `B2_R05_044` | `R05` | `CANDIDATE_ROAD_REQUIRED` | 1 | 1 | `H02` | `none` | `H02 -> J:H02->AVE_-240@END` |
| `B2` | `B2_R05_045` | `R05` | `CANDIDATE_ROAD_REQUIRED` | 1 | 1 | `H02` | `none` | `H02 -> J:H02->AVE_-240@END` |
| `B2` | `B2_R05_046` | `R05` | `CANDIDATE_ROAD_REQUIRED` | 1 | 1 | `H02` | `none` | `H02 -> J:H02->AVE_-240@END` |
| `B2` | `B2_R05_047` | `R05` | `INTERNAL_STREET_REQUIRED` | 1 | 1 | `H02` | `ENVELOPE_B2_ST_0010` | `ENVELOPE_B2_ST_0010 -> H02 -> J:H02->AVE_-240@END` |
| `B2` | `B2_R05_048` | `R05` | `CANDIDATE_ROAD_REQUIRED` | 1 | 1 | `H02` | `none` | `H02 -> J:H02->AVE_-240@END` |
| `B2` | `B2_R05_049` | `R05` | `INTERNAL_STREET_REQUIRED` | 1 | 1 | `H02` | `ENVELOPE_B2_ST_0040` | `ENVELOPE_B2_ST_0040 -> H02 -> J:H02->AVE_-240@END` |
| `B2` | `B2_R05_050` | `R05` | `INTERNAL_STREET_REQUIRED` | 1 | 1 | `H02` | `ENVELOPE_B2_ST_0010` | `ENVELOPE_B2_ST_0010 -> H02 -> J:H02->AVE_-240@END` |
| `B2` | `B2_R05_051` | `R05` | `CANDIDATE_ROAD_REQUIRED` | 1 | 1 | `H02` | `none` | `H02 -> J:H02->AVE_-240@END` |
| `B2` | `B2_R05_052` | `R05` | `CANDIDATE_ROAD_REQUIRED` | 1 | 1 | `H02` | `none` | `H02 -> J:H02->AVE_-240@END` |
| `B2` | `B2_R05_053` | `R05` | `INTERNAL_STREET_REQUIRED` | 1 | 1 | `H02` | `ENVELOPE_B2_ST_0010` | `ENVELOPE_B2_ST_0010 -> H02 -> J:H02->AVE_-240@END` |
| `B2` | `B2_R05_054` | `R05` | `CANDIDATE_ROAD_REQUIRED` | 1 | 1 | `H02` | `none` | `H02 -> J:H02->AVE_-240@END` |
| `B2` | `B2_R05_055` | `R05` | `CANDIDATE_ROAD_REQUIRED` | 1 | 1 | `H02` | `none` | `H02 -> J:H02->AVE_-240@END` |
| `B2` | `B2_R05_056` | `R05` | `CANDIDATE_ROAD_REQUIRED` | 1 | 1 | `H02` | `none` | `H02 -> J:H02->AVE_-240@END` |
| `B2` | `B2_R05_057` | `R05` | `CANDIDATE_ROAD_REQUIRED` | 1 | 1 | `H02` | `none` | `H02 -> J:H02->AVE_-240@END` |
| `B2` | `B2_R05_058` | `R05` | `CANDIDATE_ROAD_REQUIRED` | 1 | 1 | `H02` | `none` | `H02 -> J:H02->AVE_-240@END` |
| `B2` | `B2_R05_059` | `R05` | `CANDIDATE_ROAD_REQUIRED` | 1 | 1 | `H02` | `none` | `H02 -> J:H02->AVE_-240@END` |
| `B2` | `B2_R05_060` | `R05` | `CANDIDATE_ROAD_REQUIRED` | 1 | 1 | `H02` | `none` | `H02 -> J:H02->AVE_-240@END` |
| `B2` | `B2_R05_061` | `R05` | `CANDIDATE_ROAD_REQUIRED` | 1 | 1 | `H02` | `none` | `H02 -> J:H02->AVE_-240@END` |
| `B2` | `B2_R05_062` | `R05` | `CANDIDATE_ROAD_REQUIRED` | 1 | 1 | `H02` | `none` | `H02 -> J:H02->AVE_-240@END` |
| `B2` | `B2_R05_063` | `R05` | `CANDIDATE_ROAD_REQUIRED` | 1 | 1 | `H02` | `none` | `H02 -> J:H02->AVE_-240@END` |
| `B2` | `B2_R05_064` | `R05` | `CANDIDATE_ROAD_REQUIRED` | 1 | 1 | `H02` | `none` | `H02 -> J:H02->AVE_-240@END` |
| `B2` | `B2_R05_065` | `R05` | `CANDIDATE_ROAD_REQUIRED` | 1 | 1 | `H02` | `none` | `H02 -> J:H02->AVE_-240@END` |
| `B2` | `B2_R05_066` | `R05` | `CANDIDATE_ROAD_REQUIRED` | 1 | 1 | `H02` | `none` | `H02 -> J:H02->AVE_-240@END` |
| `B2` | `B2_R05_067` | `R05` | `CANDIDATE_ROAD_REQUIRED` | 1 | 1 | `H02` | `none` | `H02 -> J:H02->AVE_-240@END` |
| `B3` | `B3_R01_001` | `R01` | `DIRECT` | 1 | 1 | `AVE_-420` | `none` | `none` |
| `B3` | `B3_R08_002` | `R08` | `DIRECT` | 1 | 4 | `CRS_-880` | `none` | `none` |
| `B3` | `B3_R05_003` | `R05` | `DIRECT` | 1 | 1 | `CRS_-880` | `none` | `none` |
| `B3` | `B3_R05_004` | `R05` | `DIRECT` | 1 | 1 | `AVE_-600` | `none` | `none` |
| `B3` | `B3_R05_005` | `R05` | `DIRECT` | 1 | 1 | `CRS_-880` | `none` | `none` |
| `B3` | `B3_R01_006` | `R01` | `DIRECT` | 1 | 1 | `CRS_-880` | `none` | `none` |
| `B3` | `B3_R08_007` | `R08` | `DIRECT` | 1 | 4 | `CRS_-880` | `none` | `none` |
| `B3` | `B3_R05_008` | `R05` | `DIRECT` | 1 | 1 | `CRS_-880` | `none` | `none` |
| `B3` | `B3_R05_009` | `R05` | `DIRECT` | 1 | 1 | `CRS_-880` | `none` | `none` |
| `B3` | `B3_R05_010` | `R05` | `DIRECT` | 1 | 1 | `CRS_-880` | `none` | `none` |
| `B3` | `B3_R01_011` | `R01` | `DIRECT` | 1 | 1 | `AVE_-240` | `none` | `none` |
| `B3` | `B3_R08_012` | `R08` | `DIRECT` | 1 | 4 | `AVE_-600` | `none` | `none` |
| `B3` | `B3_R05_013` | `R05` | `DIRECT` | 1 | 1 | `AVE_-420` | `none` | `none` |
| `B3` | `B3_R05_014` | `R05` | `DIRECT` | 1 | 1 | `AVE_-240` | `none` | `none` |
| `B3` | `B3_R05_015` | `R05` | `DIRECT` | 1 | 1 | `AVE_-600` | `none` | `none` |
| `B3` | `B3_R01_016` | `R01` | `DIRECT` | 1 | 1 | `AVE_-420` | `none` | `none` |
| `B3` | `B3_R08_017` | `R08` | `DIRECT` | 1 | 4 | `AVE_-240` | `none` | `none` |
| `B3` | `B3_R05_018` | `R05` | `DIRECT` | 1 | 1 | `AVE_-600` | `none` | `none` |
| `B3` | `B3_R05_019` | `R05` | `DIRECT` | 1 | 1 | `AVE_-240` | `none` | `none` |
| `B3` | `B3_R05_020` | `R05` | `DIRECT` | 1 | 1 | `AVE_-420` | `none` | `none` |
| `B3` | `B3_R01_021` | `R01` | `DIRECT` | 1 | 1 | `CRS_-720` | `none` | `none` |
| `B3` | `B3_R08_022` | `R08` | `DIRECT` | 1 | 4 | `CRS_-720` | `none` | `none` |
| `B3` | `B3_R05_023` | `R05` | `DIRECT` | 1 | 1 | `AVE_-600` | `none` | `none` |
| `B3` | `B3_R05_024` | `R05` | `DIRECT` | 1 | 1 | `CRS_-720` | `none` | `none` |
| `B3` | `B3_R05_025` | `R05` | `DIRECT` | 1 | 1 | `CRS_-720` | `none` | `none` |

### 8.3 情境 `REVISED` 地塊清單

| Region | `parcel_id` | `prototype_id` | `status` | `buildings` | `units` | `source_road_id` | `internal_street_id` | `dependency_chain` |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `B1` | `B1_R02_001` | `R02` | `DIRECT` | 1 | 1 | `CRS_880` | `none` | `none` |
| `B1` | `B1_R01_002` | `R01` | `DIRECT` | 1 | 1 | `CRS_880` | `none` | `none` |
| `B1` | `B1_R02_003` | `R02` | `DIRECT` | 1 | 1 | `CRS_880` | `none` | `none` |
| `B1` | `B1_R01_004` | `R01` | `DIRECT` | 1 | 1 | `CRS_880` | `none` | `none` |
| `B1` | `B1_R02_005` | `R02` | `DIRECT` | 1 | 1 | `CRS_880` | `none` | `none` |
| `B1` | `B1_R01_006` | `R01` | `CANDIDATE_ROAD_REQUIRED` | 1 | 1 | `X01` | `none` | `X01 -> J:X01->AVE_-240@START` |
| `B1` | `B1_R02_007` | `R02` | `INTERNAL_STREET_REQUIRED` | 1 | 1 | `X01` | `REVISED_B1_ST_0245` | `REVISED_B1_ST_0245 -> X01 -> J:X01->AVE_-240@START` |
| `B1` | `B1_R01_008` | `R01` | `INTERNAL_STREET_REQUIRED` | 1 | 1 | `C02` | `REVISED_B1_ST_0045` | `REVISED_B1_ST_0045 -> C02 -> J:C02<->X01 -> X01 -> J:X01->AVE_-240@START` |
| `B1` | `B1_R02_009` | `R02` | `INTERNAL_STREET_REQUIRED` | 1 | 1 | `X01` | `REVISED_B1_ST_0245` | `REVISED_B1_ST_0245 -> X01 -> J:X01->AVE_-240@START` |
| `B1` | `B1_R01_010` | `R01` | `INTERNAL_STREET_REQUIRED` | 1 | 1 | `C02` | `REVISED_B1_ST_0075` | `REVISED_B1_ST_0075 -> C02 -> J:C02<->X01 -> X01 -> J:X01->AVE_-240@START` |
| `B1` | `B1_R02_011` | `R02` | `INTERNAL_STREET_REQUIRED` | 1 | 1 | `C02` | `REVISED_B1_ST_0045` | `REVISED_B1_ST_0045 -> C02 -> J:C02<->X01 -> X01 -> J:X01->AVE_-240@START` |
| `B1` | `B1_R01_012` | `R01` | `INTERNAL_STREET_REQUIRED` | 1 | 1 | `X01` | `REVISED_B1_ST_0245` | `REVISED_B1_ST_0245 -> X01 -> J:X01->AVE_-240@START` |
| `B1` | `B1_R02_013` | `R02` | `INTERNAL_STREET_REQUIRED` | 1 | 1 | `X01` | `REVISED_B1_ST_0245` | `REVISED_B1_ST_0245 -> X01 -> J:X01->AVE_-240@START` |
| `B1` | `B1_R01_014` | `R01` | `INTERNAL_STREET_REQUIRED` | 1 | 1 | `C02` | `REVISED_B1_ST_0075` | `REVISED_B1_ST_0075 -> C02 -> J:C02<->X01 -> X01 -> J:X01->AVE_-240@START` |
| `B1` | `B1_R02_015` | `R02` | `INTERNAL_STREET_REQUIRED` | 1 | 1 | `X01` | `REVISED_B1_ST_0245` | `REVISED_B1_ST_0245 -> X01 -> J:X01->AVE_-240@START` |
| `B1` | `B1_R01_016` | `R01` | `INTERNAL_STREET_REQUIRED` | 1 | 1 | `C02` | `REVISED_B1_ST_0045` | `REVISED_B1_ST_0045 -> C02 -> J:C02<->X01 -> X01 -> J:X01->AVE_-240@START` |
| `B1` | `B1_R02_017` | `R02` | `INTERNAL_STREET_REQUIRED` | 1 | 1 | `C02` | `REVISED_B1_ST_0045` | `REVISED_B1_ST_0045 -> C02 -> J:C02<->X01 -> X01 -> J:X01->AVE_-240@START` |
| `B1` | `B1_R01_018` | `R01` | `INTERNAL_STREET_REQUIRED` | 1 | 1 | `C02` | `REVISED_B1_ST_0075` | `REVISED_B1_ST_0075 -> C02 -> J:C02<->X01 -> X01 -> J:X01->AVE_-240@START` |
| `B1` | `B1_R02_019` | `R02` | `INTERNAL_STREET_REQUIRED` | 1 | 1 | `X01` | `REVISED_B1_ST_0245` | `REVISED_B1_ST_0245 -> X01 -> J:X01->AVE_-240@START` |
| `B1` | `B1_R01_020` | `R01` | `INTERNAL_STREET_REQUIRED` | 1 | 1 | `X01` | `REVISED_B1_ST_0245` | `REVISED_B1_ST_0245 -> X01 -> J:X01->AVE_-240@START` |
| `B1` | `B1_R02_021` | `R02` | `INTERNAL_STREET_REQUIRED` | 1 | 1 | `C02` | `REVISED_B1_ST_0075` | `REVISED_B1_ST_0075 -> C02 -> J:C02<->X01 -> X01 -> J:X01->AVE_-240@START` |
| `B2` | `B2_R05_001` | `R05` | `INTERNAL_STREET_REQUIRED` | 1 | 1 | `H02` | `REVISED_B2_ST_0130` | `REVISED_B2_ST_0130 -> H02 -> J:H02->AVE_-240@END` |
| `B2` | `B2_R05_002` | `R05` | `INTERNAL_STREET_REQUIRED` | 1 | 1 | `H02` | `REVISED_B2_ST_0130` | `REVISED_B2_ST_0130 -> H02 -> J:H02->AVE_-240@END` |
| `B2` | `B2_R05_003` | `R05` | `INTERNAL_STREET_REQUIRED` | 1 | 1 | `H02` | `REVISED_B2_ST_0030` | `REVISED_B2_ST_0030 -> H02 -> J:H02->AVE_-240@END` |
| `B2` | `B2_R05_004` | `R05` | `INTERNAL_STREET_REQUIRED` | 1 | 1 | `H02` | `REVISED_B2_ST_0130` | `REVISED_B2_ST_0130 -> H02 -> J:H02->AVE_-240@END` |
| `B2` | `B2_R05_005` | `R05` | `INTERNAL_STREET_REQUIRED` | 1 | 1 | `H02` | `REVISED_B2_ST_0010` | `REVISED_B2_ST_0010 -> H02 -> J:H02->AVE_-240@END` |
| `B2` | `B2_R05_006` | `R05` | `INTERNAL_STREET_REQUIRED` | 1 | 1 | `H02` | `REVISED_B2_ST_0030` | `REVISED_B2_ST_0030 -> H02 -> J:H02->AVE_-240@END` |
| `B2` | `B2_R05_007` | `R05` | `INTERNAL_STREET_REQUIRED` | 1 | 1 | `H02` | `REVISED_B2_ST_0130` | `REVISED_B2_ST_0130 -> H02 -> J:H02->AVE_-240@END` |
| `B2` | `B2_R05_008` | `R05` | `INTERNAL_STREET_REQUIRED` | 1 | 1 | `H02` | `REVISED_B2_ST_0010` | `REVISED_B2_ST_0010 -> H02 -> J:H02->AVE_-240@END` |
| `B2` | `B2_R05_009` | `R05` | `INTERNAL_STREET_REQUIRED` | 1 | 1 | `H02` | `REVISED_B2_ST_0130` | `REVISED_B2_ST_0130 -> H02 -> J:H02->AVE_-240@END` |
| `B2` | `B2_R05_010` | `R05` | `INTERNAL_STREET_REQUIRED` | 1 | 1 | `H02` | `REVISED_B2_ST_0010` | `REVISED_B2_ST_0010 -> H02 -> J:H02->AVE_-240@END` |
| `B2` | `B2_R05_011` | `R05` | `INTERNAL_STREET_REQUIRED` | 1 | 1 | `H02` | `REVISED_B2_ST_0030` | `REVISED_B2_ST_0030 -> H02 -> J:H02->AVE_-240@END` |
| `B2` | `B2_R05_012` | `R05` | `INTERNAL_STREET_REQUIRED` | 1 | 1 | `H02` | `REVISED_B2_ST_0130` | `REVISED_B2_ST_0130 -> H02 -> J:H02->AVE_-240@END` |
| `B2` | `B2_R05_013` | `R05` | `INTERNAL_STREET_REQUIRED` | 1 | 1 | `H02` | `REVISED_B2_ST_0010` | `REVISED_B2_ST_0010 -> H02 -> J:H02->AVE_-240@END` |
| `B2` | `B2_R05_014` | `R05` | `INTERNAL_STREET_REQUIRED` | 1 | 1 | `H02` | `REVISED_B2_ST_0130` | `REVISED_B2_ST_0130 -> H02 -> J:H02->AVE_-240@END` |
| `B2` | `B2_R05_015` | `R05` | `INTERNAL_STREET_REQUIRED` | 1 | 1 | `H02` | `REVISED_B2_ST_0010` | `REVISED_B2_ST_0010 -> H02 -> J:H02->AVE_-240@END` |
| `B2` | `B2_R05_016` | `R05` | `INTERNAL_STREET_REQUIRED` | 1 | 1 | `H02` | `REVISED_B2_ST_0030` | `REVISED_B2_ST_0030 -> H02 -> J:H02->AVE_-240@END` |
| `B2` | `B2_R05_017` | `R05` | `INTERNAL_STREET_REQUIRED` | 1 | 1 | `H02` | `REVISED_B2_ST_0130` | `REVISED_B2_ST_0130 -> H02 -> J:H02->AVE_-240@END` |
| `B2` | `B2_R05_018` | `R05` | `INTERNAL_STREET_REQUIRED` | 1 | 1 | `H02` | `REVISED_B2_ST_0010` | `REVISED_B2_ST_0010 -> H02 -> J:H02->AVE_-240@END` |
| `B2` | `B2_R05_019` | `R05` | `INTERNAL_STREET_REQUIRED` | 1 | 1 | `H02` | `REVISED_B2_ST_0130` | `REVISED_B2_ST_0130 -> H02 -> J:H02->AVE_-240@END` |
| `B2` | `B2_R05_020` | `R05` | `INTERNAL_STREET_REQUIRED` | 1 | 1 | `H02` | `REVISED_B2_ST_0010` | `REVISED_B2_ST_0010 -> H02 -> J:H02->AVE_-240@END` |
| `B2` | `B2_R05_021` | `R05` | `INTERNAL_STREET_REQUIRED` | 1 | 1 | `H02` | `REVISED_B2_ST_0030` | `REVISED_B2_ST_0030 -> H02 -> J:H02->AVE_-240@END` |
| `B2` | `B2_R05_022` | `R05` | `INTERNAL_STREET_REQUIRED` | 1 | 1 | `H02` | `REVISED_B2_ST_0130` | `REVISED_B2_ST_0130 -> H02 -> J:H02->AVE_-240@END` |
| `B2` | `B2_R05_023` | `R05` | `INTERNAL_STREET_REQUIRED` | 1 | 1 | `H02` | `REVISED_B2_ST_0010` | `REVISED_B2_ST_0010 -> H02 -> J:H02->AVE_-240@END` |
| `B2` | `B2_R05_024` | `R05` | `INTERNAL_STREET_REQUIRED` | 1 | 1 | `H02` | `REVISED_B2_ST_0130` | `REVISED_B2_ST_0130 -> H02 -> J:H02->AVE_-240@END` |
| `B2` | `B2_R05_025` | `R05` | `INTERNAL_STREET_REQUIRED` | 1 | 1 | `H02` | `REVISED_B2_ST_0010` | `REVISED_B2_ST_0010 -> H02 -> J:H02->AVE_-240@END` |
| `B2` | `B2_R05_026` | `R05` | `INTERNAL_STREET_REQUIRED` | 1 | 1 | `H02` | `REVISED_B2_ST_0030` | `REVISED_B2_ST_0030 -> H02 -> J:H02->AVE_-240@END` |
| `B2` | `B2_R05_027` | `R05` | `INTERNAL_STREET_REQUIRED` | 1 | 1 | `H02` | `REVISED_B2_ST_0130` | `REVISED_B2_ST_0130 -> H02 -> J:H02->AVE_-240@END` |
| `B2` | `B2_R05_028` | `R05` | `INTERNAL_STREET_REQUIRED` | 1 | 1 | `H02` | `REVISED_B2_ST_0010` | `REVISED_B2_ST_0010 -> H02 -> J:H02->AVE_-240@END` |
| `B2` | `B2_R05_029` | `R05` | `INTERNAL_STREET_REQUIRED` | 1 | 1 | `H02` | `REVISED_B2_ST_0130` | `REVISED_B2_ST_0130 -> H02 -> J:H02->AVE_-240@END` |
| `B2` | `B2_R05_030` | `R05` | `INTERNAL_STREET_REQUIRED` | 1 | 1 | `H02` | `REVISED_B2_ST_0010` | `REVISED_B2_ST_0010 -> H02 -> J:H02->AVE_-240@END` |
| `B2` | `B2_R05_031` | `R05` | `INTERNAL_STREET_REQUIRED` | 1 | 1 | `H02` | `REVISED_B2_ST_0030` | `REVISED_B2_ST_0030 -> H02 -> J:H02->AVE_-240@END` |
| `B2` | `B2_R05_032` | `R05` | `CANDIDATE_ROAD_REQUIRED` | 1 | 1 | `H02` | `none` | `H02 -> J:H02->AVE_-240@END` |
| `B2` | `B2_R05_033` | `R05` | `INTERNAL_STREET_REQUIRED` | 1 | 1 | `H02` | `REVISED_B2_ST_0130` | `REVISED_B2_ST_0130 -> H02 -> J:H02->AVE_-240@END` |
| `B2` | `B2_R05_034` | `R05` | `INTERNAL_STREET_REQUIRED` | 1 | 1 | `H02` | `REVISED_B2_ST_0010` | `REVISED_B2_ST_0010 -> H02 -> J:H02->AVE_-240@END` |
| `B2` | `B2_R05_035` | `R05` | `CANDIDATE_ROAD_REQUIRED` | 1 | 1 | `H02` | `none` | `H02 -> J:H02->AVE_-240@END` |
| `B2` | `B2_R05_036` | `R05` | `CANDIDATE_ROAD_REQUIRED` | 1 | 1 | `H02` | `none` | `H02 -> J:H02->AVE_-240@END` |
| `B2` | `B2_R05_037` | `R05` | `CANDIDATE_ROAD_REQUIRED` | 1 | 1 | `H02` | `none` | `H02 -> J:H02->AVE_-240@END` |
| `B2` | `B2_R05_038` | `R05` | `CANDIDATE_ROAD_REQUIRED` | 1 | 1 | `H02` | `none` | `H02 -> J:H02->AVE_-240@END` |
| `B2` | `B2_R05_039` | `R05` | `CANDIDATE_ROAD_REQUIRED` | 1 | 1 | `H02` | `none` | `H02 -> J:H02->AVE_-240@END` |
| `B2` | `B2_R05_040` | `R05` | `INTERNAL_STREET_REQUIRED` | 1 | 1 | `H02` | `REVISED_B2_ST_0010` | `REVISED_B2_ST_0010 -> H02 -> J:H02->AVE_-240@END` |
| `B2` | `B2_R05_041` | `R05` | `CANDIDATE_ROAD_REQUIRED` | 1 | 1 | `H02` | `none` | `H02 -> J:H02->AVE_-240@END` |
| `B2` | `B2_R05_042` | `R05` | `CANDIDATE_ROAD_REQUIRED` | 1 | 1 | `H02` | `none` | `H02 -> J:H02->AVE_-240@END` |
| `B2` | `B2_R05_043` | `R05` | `INTERNAL_STREET_REQUIRED` | 1 | 1 | `H02` | `REVISED_B2_ST_0030` | `REVISED_B2_ST_0030 -> H02 -> J:H02->AVE_-240@END` |
| `B2` | `B2_R05_044` | `R05` | `INTERNAL_STREET_REQUIRED` | 1 | 1 | `H02` | `REVISED_B2_ST_0010` | `REVISED_B2_ST_0010 -> H02 -> J:H02->AVE_-240@END` |
| `B2` | `B2_R05_045` | `R05` | `INTERNAL_STREET_REQUIRED` | 1 | 1 | `H02` | `REVISED_B2_ST_0010` | `REVISED_B2_ST_0010 -> H02 -> J:H02->AVE_-240@END` |
| `B2` | `B2_R05_046` | `R05` | `CANDIDATE_ROAD_REQUIRED` | 1 | 1 | `H02` | `none` | `H02 -> J:H02->AVE_-240@END` |
| `B2` | `B2_R05_047` | `R05` | `CANDIDATE_ROAD_REQUIRED` | 1 | 1 | `H02` | `none` | `H02 -> J:H02->AVE_-240@END` |
| `B2` | `B2_R05_048` | `R05` | `CANDIDATE_ROAD_REQUIRED` | 1 | 1 | `H02` | `none` | `H02 -> J:H02->AVE_-240@END` |
| `B2` | `B2_R05_049` | `R05` | `CANDIDATE_ROAD_REQUIRED` | 1 | 1 | `H02` | `none` | `H02 -> J:H02->AVE_-240@END` |
| `B2` | `B2_R05_050` | `R05` | `CANDIDATE_ROAD_REQUIRED` | 1 | 1 | `H02` | `none` | `H02 -> J:H02->AVE_-240@END` |
| `B2` | `B2_R05_051` | `R05` | `CANDIDATE_ROAD_REQUIRED` | 1 | 1 | `H02` | `none` | `H02 -> J:H02->AVE_-240@END` |
| `B2` | `B2_R05_052` | `R05` | `CANDIDATE_ROAD_REQUIRED` | 1 | 1 | `H02` | `none` | `H02 -> J:H02->AVE_-240@END` |
| `B2` | `B2_R05_053` | `R05` | `CANDIDATE_ROAD_REQUIRED` | 1 | 1 | `H02` | `none` | `H02 -> J:H02->AVE_-240@END` |
| `B2` | `B2_R05_054` | `R05` | `CANDIDATE_ROAD_REQUIRED` | 1 | 1 | `H02` | `none` | `H02 -> J:H02->AVE_-240@END` |
| `B2` | `B2_R05_055` | `R05` | `CANDIDATE_ROAD_REQUIRED` | 1 | 1 | `H02` | `none` | `H02 -> J:H02->AVE_-240@END` |
| `B2` | `B2_R05_056` | `R05` | `CANDIDATE_ROAD_REQUIRED` | 1 | 1 | `H02` | `none` | `H02 -> J:H02->AVE_-240@END` |
| `B2` | `B2_R05_057` | `R05` | `CANDIDATE_ROAD_REQUIRED` | 1 | 1 | `H02` | `none` | `H02 -> J:H02->AVE_-240@END` |
| `B2` | `B2_R05_058` | `R05` | `CANDIDATE_ROAD_REQUIRED` | 1 | 1 | `H02` | `none` | `H02 -> J:H02->AVE_-240@END` |
| `B2` | `B2_R05_059` | `R05` | `CANDIDATE_ROAD_REQUIRED` | 1 | 1 | `H02` | `none` | `H02 -> J:H02->AVE_-240@END` |
| `B3` | `B3_R01_001` | `R01` | `DIRECT` | 1 | 1 | `AVE_-420` | `none` | `none` |
| `B3` | `B3_R08_002` | `R08` | `DIRECT` | 1 | 4 | `AVE_-600` | `none` | `none` |
| `B3` | `B3_R05_003` | `R05` | `DIRECT` | 1 | 1 | `AVE_-420` | `none` | `none` |
| `B3` | `B3_R05_004` | `R05` | `DIRECT` | 1 | 1 | `AVE_-240` | `none` | `none` |
| `B3` | `B3_R05_005` | `R05` | `DIRECT` | 1 | 1 | `AVE_-600` | `none` | `none` |
| `B3` | `B3_R01_006` | `R01` | `DIRECT` | 1 | 1 | `AVE_-240` | `none` | `none` |
| `B3` | `B3_R08_007` | `R08` | `DIRECT` | 1 | 4 | `AVE_-420` | `none` | `none` |
| `B3` | `B3_R05_008` | `R05` | `DIRECT` | 1 | 1 | `AVE_-600` | `none` | `none` |
| `B3` | `B3_R05_009` | `R05` | `DIRECT` | 1 | 1 | `AVE_-600` | `none` | `none` |
| `B3` | `B3_R05_010` | `R05` | `DIRECT` | 1 | 1 | `AVE_-240` | `none` | `none` |
| `B3` | `B3_R01_011` | `R01` | `DIRECT` | 1 | 1 | `AVE_-420` | `none` | `none` |
| `B3` | `B3_R08_012` | `R08` | `DIRECT` | 1 | 4 | `AVE_-240` | `none` | `none` |
| `B3` | `B3_R05_013` | `R05` | `DIRECT` | 1 | 1 | `AVE_-600` | `none` | `none` |
| `B3` | `B3_R05_014` | `R05` | `DIRECT` | 1 | 1 | `AVE_-420` | `none` | `none` |
| `B3` | `B3_R05_015` | `R05` | `DIRECT` | 1 | 1 | `AVE_-600` | `none` | `none` |
| `B3` | `B3_R01_016` | `R01` | `DIRECT` | 1 | 1 | `CRS_-720` | `none` | `none` |
| `B3` | `B3_R08_017` | `R08` | `DIRECT` | 1 | 4 | `CRS_-720` | `none` | `none` |
