# WE-02 依賴矩陣（確定性產生）

## 1. 區域與道路依賴

| 區域 | 期別 | 必要工程 | 依賴鏈終點 | 狀態 |
|---|---|---|---|---|
| B1 | 1 | ENVELOPE_B1_ST_0305, X01 | J:X01->AVE_-240@START, 既有道路（CRS／AVE） | CONDITIONAL |
| B2 | 1 | H02 | J:H02->AVE_-240@END | CONDITIONAL_PROXY |
| B3 | 1 | 無新增工程 | 既有道路（CRS／AVE） | VERIFIED_DIRECT |
| B1 | 2 | C02, ENVELOPE_B1_ST_0085, ENVELOPE_B1_ST_0305, X01 | J:X01->AVE_-240@START, 既有道路（CRS／AVE） | CONDITIONAL |
| B2 | 2 | H02 | J:H02->AVE_-240@END | CONDITIONAL_PROXY |
| B3 | 2 | 無新增工程 | 既有道路（CRS／AVE） | UNVERIFIED |

## 2. 非道路依賴（全部尚未完成）

| 系統 | 依賴 | 負責後續任務 |
|---|---|---|
| 地形與地基 | B2 R05 平地代理、R06 無裁定；各街道與住宅地基需獨立驗證 | WE-05 |
| 建築原型 | R01、R02、R05、R08 優先；其餘後續 | WE-06 |
| 串流與 LOD | 區域載入卸載、碰撞啟用範圍、材質共用 | WE-03 |
| 效能 | 手機與平板實機 30 FPS 尚未驗證；headless 數據不可替代 | WE-03 起 |
| 景觀 | C02 海灘侵占 224 m² 須先有保護方案（第二期） | WE-04 |
