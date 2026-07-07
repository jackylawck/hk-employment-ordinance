## ⚙️ 技術架構與合規聲明 (Architecture & Compliance Notice)

### 1. 決定性規則引擎 (100% Deterministic Rule-based Engine)
* **無 AI 幻覺 (Zero LLM Hallucinations)**：本系統**無接入**任何第三方公有大語言模型 (如 ChatGPT, Claude 等) 系統 API。所有法規輸出均採用 100% 決定性邏輯與正則表達式 (Regex) 關鍵字精準匹配技術。
* **條文可追溯性 (Statutory Traceability)**：系統拒絕任何「生成式/詮釋性」的法律解答。所有回應均硬編碼 (Hard-coded) 對齊電子版香港法例第 57 章《僱傭條例》官方主體條文與勞工處簡明指南，確保審計軌跡 (Audit Trail) 完全透明可查。

### 2. 數據隱私與零存儲機制 (Zero-Storage Privacy Framework)
* **無 RAG 架構與數據外洩風險 (No RAG / Vector Database)**：系統**無使用**檢索增強生成 (RAG) 技術，企業無需將員工手冊或敏感人事數據上傳至第三方雲端或向量數據庫。
* **記憶體即時清空 (Statutory Privacy Guard)**：本應用採用「無持久性存儲 (Zero Persistent Storage)」設計，不設後台數據庫。用戶輸入的任何情境查詢或勾選的審計指標，均僅在當下瀏覽器 session 密封運行，**網頁一旦關閉或重新整理，所有數據即時在雲端完全清空歸零**，符合國際隱私審計最高標準。
