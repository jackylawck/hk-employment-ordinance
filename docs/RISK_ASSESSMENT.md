# ISO 42001 AI Risk Assessment Report / 人工智能風險評估報告

## 1. Governance Scope / 治理範本
* **Compliance Frameworks / 合規框架**: ISO/IEC 42001 Annex A.6.1, EU AI Act Article 9, NIST AI RMF.
* **System Categorization / 系統歸類**: Minimal Risk AI / 低風險輔助診斷系統.

## 2. Risk Control Matrix / 風險控制矩陣

| Risk ID / 風險編號 | Risk Description / 風險描述 | Pre-Control / 控制前 | Control Mechanism / 控制機制 | Post-Control / 控制後 |
|:---|:---|:---|:---|:---|
| **R-01** | **Cap. 57 Misinterpretation / 法條誤讀與幻覺** | HIGH / 高 | Deterministic `ControlGuardrails` for s.9 dismissal & 468 rules.<br>決定性防禦網閘硬化，阻斷高危幻覺。 | **LOW / 低** |
| **R-02** | **PII Leakage / 個人資料外洩** | HIGH / 高 | In-memory execution; raw prompts stripped from logs.<br>純記憶體運算；日誌去識別化脫敏。 | **LOW / 低** |
| **R-03** | **Automation Bias / 自動化偏見與盲從** | CRITICAL / 極高 | Mandatory Human-in-the-Loop cross-verification.<br>強制 HR 專員人工二次交叉核對。 | **LOW / 低** |
