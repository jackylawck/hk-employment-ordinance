# System Lifecycle & Change Management Protocol / 生命週期與變更管理協議

---

## 1. Compliance Alignment / 合規框架對齊
This Lifecycle Management Protocol enforces continuous monitoring and change control based on global AI standards:
本生命週期管理協議嚴格對齊國際 AI 控制與變更標準：
* **EU AI Act**: Article 72 (Post-market Monitoring & Continuous Compliance System)
* **ISO/IEC 42001 (AIMS)**: Clause 8 & Annex A.10 (AI System Lifecycle & Operational Control)
* **NIST AI RMF**: MANAGE 3.1 (System Maintenance, Degradation Prevention & Regression Testing)

---

## 2. Trigger-Based Maintenance Workflow / 變更觸發與維護工作流

When the HKSAR Legislative Council (LegCo) or Labour Department issues statutory updates (e.g. "468" continuous contract rule revisions or Statutory Minimum Wage adjustments), the system follows a mandatory 4-step update protocol:
當香港立法會或勞工處發布最新法定修訂（例如「468」連續性合約修訂或法定最低工資調整）時，系統必須執行標準 4 步維護流程：


```

[1. Regulatory Update Trigger / 官方修例觸發]
│
▼
[2. Knowledge Base Update / 知識庫 PDF 替換與擴充]
│
▼
[3. FAISS Re-indexing & In-Memory Rebuild / 向量庫重構]
│
▼
[4. Mandatory Regression Testing / 迴歸測試與防衛驗證]
│
▼
[Production Deployment & ISO Audit Logging / 生產環境上線與審計備案]

```

---

## 3. Step-by-Step Update Protocol / 變更管理詳細步驟

### Step 1: Legal Document Ingestion / 第一步：權威文件注入
* Download the newly published official PDF guides or FAQs directly from the **HKSAR Labour Department portal**.
  直接從**特區政府勞工處官網**下載最新發布的官方指南或 FAQ PDF 文件。
* Place the new document into the root repository directory (e.g. `continuous_contract_FAQ_tc.pdf`).
  將新文件存入 Repository 根目錄。

### Step 2: Vector Index Auto-Rebuilding / 第二步：向量索引自動重構
* The system executes `process_pdf_to_chunks()` to re-segment text (`chunk_size = 400`, `overlap = 80`).
  系統調用 `process_pdf_to_chunks()` 重新進行文本切片（預設切片 400 字，重疊 80 字）。
* `@st.cache_resource` triggers automatic cache invalidation and rebuilds the FAISS vector store in RAM.
  `@st.cache_resource` 機制自動失效舊快取，於記憶體內完成 FAISS 向量資料庫之構建。

### Step 3: Automated Regression Testing / 第三步：強制迴歸測試
Before code approval, the AI Governance Lead must execute standard regression drills covering 3 critical compliance boundaries:
在上線前，AI 治理負責人必須執行包含 3 大核心合規邊界之迴歸測試：

1. **Guardrail Integrity Test / 網閘完整性測試**: Verify `ControlGuardrails` intercepts s.9 summary dismissal queries without fallback.
   驗證即時解僱（第 9 條）觸發時，`ControlGuardrails` 是否 100% 啟動硬化攔截。
2. **Formula Accuracy Test / 公式精算測試**: Verify 12-Month Average Wage (ADW 713) formulas correctly exclude unpaid/less-than-full-pay leave periods.
   驗證 12 個月平均工資 (ADW 713) 公式是否精確剔除少於全薪之假期款額與天數。
3. **Threshold Accuracy Test / 法規門檻測試**: Verify the RAG engine correctly distinguishes between historical "418" and current "468" rules based on date context.
   驗證 RAG 引擎能否依據時間脈絡，精準區分舊制「418」與最新「468」門檻。

---

## 4. Model & Vector Store Retirement / 模型與向量庫退役與銷毀

* **In-Memory Volatility / 記憶體即時銷毀**: Runtime sessions and temporary user-uploaded PDFs operate strictly within volatile RAM and are permanently destroyed upon session termination (Zero Data Retention).
  所有會話運行狀態與用戶臨時上傳之 PDF 嚴格存於 volatile RAM，會話關閉即刻銷毀。
* **Deprecation Management / 舊版本退役**: When base PDF guides are superseded by new Labour Department publications, outdated files are moved to an archive branch to prevent deprecated data retrieval.
  當勞工處發布全新主體指南時，舊版文件將移至歸檔區，防止 RAG 檢索過期法條。

```
