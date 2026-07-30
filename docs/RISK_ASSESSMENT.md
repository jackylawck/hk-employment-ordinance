# ISO 42001 AI Risk Assessment Report (RISK_ASSESSMENT.md)

## 1. Governance Context
* **Compliance Frameworks**: ISO/IEC 42001 Annex A.6.1, EU AI Act Article 9 (Risk Management System), NIST AI RMF (GOVERN 3.1 & MANAGE 2.1).
* **System Categorization**: Minimal Risk AI (Decision Support Tool for Internal HR Operations).

## 2. Quantified Risk Control Matrix

| Risk ID | Hazard / Risk Description | Severity | Probability | Pre-Control Risk | Control Mechanism | Post-Control Risk | ISO 42001 Clause |
|:---|:---|:---|:---|:---|:---|:---|:---|
| **R-01** | **Hallucination / Misinterpretation of Cap. 57** (e.g. unlawful termination advice) | High | Medium | **CRITICAL** | Deterministic `ControlGuardrails` intercept s.9 summary dismissal and forced fallback for low-confidence queries (<25%). | **LOW** | Annex A.6.1.2 |
| **R-02** | **PII Leakage via Prompt Logging** | High | Medium | **HIGH** | Log sanitization: raw queries stripped; only SHA-256 hashes logged. In-memory ZDR architecture. | **LOW** | Annex A.9.1 |
| **R-03** | **Automation Bias (Blind Reliance by HR)** | High | High | **CRITICAL** | Mandatory UI免責宣告, Human-in-the-Loop approval mandatory before executing personnel files. | **LOW** | Annex A.8.3 |
| **R-04** | **Outdated Regulatory Data** | Medium | Medium | **MEDIUM** | Dynamic minimum wage看板 alerts & continuous contract FAQ ingestion. | **LOW** | Annex A.10.1 |

## 3. Monitoring & Re-evaluation Plan
This risk matrix is subject to quarterly review or immediately upon any legislative amendment passed by the Hong Kong Legislative Council (LegCo).
