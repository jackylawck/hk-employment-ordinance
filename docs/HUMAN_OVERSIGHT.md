# Human Oversight & Governance Protocol / 人工監督與申訴管治協議

---

## 1. Compliance & Governance Alignment / 合規框架對齊
This Human Oversight Protocol is anchored in international AI governance standards:
本人工監督協議嚴格對齊國際 AI 治理標準：
* **EU AI Act**: Article 14 (Human Oversight Mandate for Decision-Support AI)
* **ISO/IEC 42001 (AIMS)**: Annex A.8.3 (Human-in-the-Loop Technical & Operational Controls)
* **NIST AI RMF**: GOVERN 4.1 & MANAGE 4.1 (Human-AI Decision-Making Integrity)

---

## 2. Core Principle: Class-2 Decision Support System / 核心原則：第二類決策輔助系統
The Cap. 57 Compliance Advisor operates strictly as a **non-autonomous, advisory-only Decision Support System**.
本系統嚴格定位為**非自主、僅供諮詢之第二類決策輔助系統**。

* **No Automated Execution / 零自動化執行**: The AI system lacks API hooks or execution rights to perform automated personnel actions (e.g., dispatching termination notices, modifying payroll software, or locking attendance records).
  AI 系統不具備任何執行權限，絕不自動執行解僱、扣薪或變更考勤等人力資源操作。
* **Mandatory Human Accountability / 最終責任歸屬**: All statutory calculations, contract interpretations, and HR actions remain under the sole accountability of licensed human HR professionals and corporate management.
  所有法定薪酬精算、合約詮釋與人力資源決策，其法律責任完全歸屬於 HR 專業人員及企業管理層。

---

## 3. Human-in-the-Loop (HITL) Workflow / 人機協同與監督流程

To prevent **Automation Bias** (blind reliance on AI outputs), all internal HR users must follow the standard 4-step governance workflow:
為防止 **自動化偏見 (Automation Bias)**（盲目信任 AI 輸出），所有 HR 人員必須執行標準 4 步管治流程：


```

[1. User Query / 用戶提問]
│
▼
[2. AI Guardrail & RAG Engine / 網閘與語意檢索]
│
▼
[3. AI Advisory Output + SHA-256 Audit ID / AI 建議 + 密碼學審計 ID]
│
▼
[4. Mandatory Human Verification / 必須經 HR 人工二次核對]
│
├─────────────────────────────────┐
▼                                 ▼
[Verified Compliant / 確認無誤]     [Discrepancy / 存在疑慮或重大風險]
│                                 │
▼                                 ▼
[Execute HR Action / 執行處置]     [Escalate to Legal/Labour Dept / 人工接管與外求專證]

```

---

## 4. Human Verification & Escalation Protocol / 人工核對與接管申訴機制

### Step 1: Verification Against Primary Sources / 第一步：查驗官方原始條文
Before finalizing any personnel decision, the HR professional must click the **Traceability Link (審計追溯鏈)** provided in the system output to cross-check the matched page number against the original Labour Department PDF document.
在敲定任何 HR 決策前，HR 專員必須點擊系統輸出的**審計追溯鏈**，親自核對勞工處官方 PDF 原始頁碼之條文內容。

### Step 2: Risk Escalation Trigger / 第二步：高風險升級處置機制
Human takeover and professional escalation are **MANDATORY** under the following statutory conditions:
遇到以下法定高風險情境時，必須**強制進行人工接管**並尋求專業法律意見：

1. **Summary Dismissal (Cap. 57 s.9) / 即時解僱 (第 9 條)**: Allegations of serious misconduct requiring warning letter review.
   涉及員工嚴重過失、需審查書面警告信及 PIP 紀錄之即時解僱情境。
2. **Protected Employees / 法定保障期僱員**: Terminations involving pregnant employees, those on paid sick leave, or work injury period.
   涉及懷孕生育保障期、有薪病假期間或工傷休假期間之解僱申索。
3. **Complex ADW Calculations / 複雜 12 個月平均工資精算**: Calculations involving fluctuating contractual commission, discretionary bonuses, or extended unpaid leaves.
   涉及浮動佣金、酌情花紅或長時間無薪假之 713 條例 ADW 剔除期精算。

---

## 5. Official Help & External Escalation Channels / 官方權威諮詢與外部申訴渠道

When AI confidence is low (<25%) or legal ambiguities arise, HR personnel must escalate directly to official government bodies:
當 AI 置信度過低 (<25%) 或遇到重大法律不確定性時，必須直接轉介特區政府官方渠道：

* **HKSAR Labour Department Hotline / 勞工處查詢熱線**: 2717 1771 (Handled by 1823 / 由 1823 接聽)
* **Breach Reporting Hotline / 舉報違反《僱傭條例》熱線**: 2815 2200
* **Official Web Portal / 官方網站**: [www.labour.gov.hk](https://www.labour.gov.hk/)

```
