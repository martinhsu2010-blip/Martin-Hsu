# WE-02 獨立驗證紀錄（we02_validation.md）

由 `tools/we02/we02_verify.py` 產生，不引用產生器，柵格重算使用 WE-01D 的繪製函式；結果由 Claude 負責。

- BASE：`84319439243b51aa8d119e33eb62a0637feea887`；檢查項目數 454；失敗 0。

## 來源與產物雜湊（SHA-256）

- `conditional_parcels.json` 51d8eb8e6ac60b7f36bf0ba86895aa069befe331f37d5d54e04ad1de2ded0124
- `feasibility.json` 6131fb4a11ab2e43ed9799307158b18b61c2e469e97f85ed78e202dbd69832b4
- `internal_streets.json` adfd26957555bffbb7e5a3d9e216a4a1ecd47c871be35bb63fc8a57611c2274e
- `map_geometry.json` c17cc1ce8080627e4744394e5ffefdec7e7b6d516f7eb8fd25c5f2f605e1460e
- `road_survey.json` 4afd52d2b51273f1e890aeda3c3ade22927124926c12a1e3aa3cefe30f3eeb27
- `district_plan.json` e4b74807f1cdb9b8d52539a226bf251ef1c873ef74371b8abbf8615592e81f0f
- `masterplan.svg` 1bb35a4314a24e58e949e523724e6e8e3b7762e232c2dd3290f0fb850389d96c
- `masterplan.md` 67c1d77901559d893139efb01b5f880d90a8b9f0c1d9608e8dcdac2bf933fa99
- `dependency_matrix.md` cedc7f549467aef5b38140d313f488d184c67c132979775c3cff0aae8f8e2830

## 各閘門結果

| 閘門 | 檢查數 | 失敗 |
|---|---|---|
| MP01 | 7 | 0 |
| MP02 | 5 | 0 |
| MP03 | 63 | 0 |
| MP04 | 3 | 0 |
| MP05 | 6 | 0 |
| MP06 | 59 | 0 |
| MP07 | 64 | 0 |
| MP08 | 67 | 0 |
| MP09 | 2 | 0 |
| MP10 | 58 | 0 |
| MP11 | 2 | 0 |
| MP12 | 33 | 0 |
| MP13 | 18 | 0 |
| MP14 | 1 | 0 |
| MP15 | 1 | 0 |
| MP18 | 65 | 0 |
| MP16 | 流程閘門 | Claude G0 已完成（T-017 登記前）；Martin 批准記於 D-061 |
| MP17 | 流程閘門 | 待 Martin 最終規劃驗收 |

## 關鍵數字

- 第一期 40 棟（52 戶）；第二期累計 57 棟（72 戶），B3 缺 R01、R05、R08 各 1 棟。
- 第一期道路 1110.214 m（柵格 8481 格）；第二期累計 1390.214 m（柵格 11589 格），海灘侵占 224 m²。
- 精確多邊形面積（獨立 z 方向切片重算，已裁切至區域外框、扣除海灘）：第1期 B1 2,909.8 m²（柵格 3,177）；第1期 B2 4,850.8 m²（柵格 5,304）；第2期 B1 5,764.3 m²（柵格 6,285）；第2期 B2 4,850.8 m²（柵格 5,304）；驗收仍以柵格值為準。
- B1 第一期 R01 零餘裕：X01 + ENVELOPE_B1_ST_0305 恰好 5 棟；任一塊失敗須加 C02 與一條街道（+280.000 m、海灘 224 m²），已由原始依賴鏈獨立重算。
- 第二期街道選擇：ENVELOPE_B1_ST_0085（兩條對稱，規則為格數較少、其次字典序）。

## 限制與未解問題

- B2 plan is the R05 flat proxy; R06 has no engineering verdict
- all roads and streets are CONDITIONAL_VERIFIED, not built
- Phase 2 B3 target 28 is UNVERIFIED: verified direct parcels 25, short R01 1, R05 1, R08 1
- B1 Phase 1 R01 has zero margin (exactly 5 available with X01 + ENVELOPE_B1_ST_0305)
- headless numbers are not device FPS; 30 FPS on phone and tablet is unverified
- 面積為 1 m 柵格（與 WE-01 相同規則）；新增道路在海灘格不計入，與 WE-01 完整 ENVELOPE 數字（B1 8,013、B2 10,555）逐格重現。
- 通過 MP01–MP18 不代表任何條件工程已完成，也不改變 WE-01 的 D3 CONDITIONAL 裁定。

