# Data Lineage Specification / 數據血統與治理規範

## 1. Data Source Authority / 數據源權威性
All ingested data originates strictly from official HKSAR Labour Department publications:
所有向量庫數據嚴格萃取自香港特別行政區勞工處官方權威出版物：
1. *A Concise Guide to the Employment Ordinance (Cap. 57)* / 《僱傭條例簡明指南》
2. *FAQ on Revised Continuous Contract (468 Rule)* / 《修訂連續性合約 FAQ》

## 2. Processing Parameters / 數據處理參數
* **Extraction Engine / 提取引擎**: `pdfplumber` (Table-aware)
* **Chunking Metrics / 切片參數**: `chunk_size = 400`, `overlap = 80`
* **Total Asset Chunks / 數據切片總數**: 562 Verified Vector Chunks / 562 個已驗證向量切片
