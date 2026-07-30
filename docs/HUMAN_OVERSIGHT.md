# Human Oversight & Governance Escalation (HUMAN_OVERSIGHT.md)

## 1. Compliance Alignment
* **Standards**: EU AI Act Article 14 (Human Oversight), ISO 42001 Annex A.8.3 (Human-in-the-Loop Controls), NIST AI RMF GOVERN 4.1.

## 2. Human-in-the-Loop (HITL) Mandate
The Cap. 57 Compliance Advisor operates strictly as a **Class-2 Decision Support System**.
1. **No Automatic Action**: The AI system lacks API hooks to execute HR actions (e.g., sending termination emails, altering payroll entries).
2. **Mandatory Human Verification**: HR professionals must cross-verify retrieved statutory page numbers against original Labour Department documents prior to locking any formal employee dispute or calculation file.

## 3. Escalation & Audit Trail Workflow
[User Query] ➔ [Guardrail / RAG Engine] ➔ [AI Output + SHA-256 Audit ID]
│
▼
[HR Manager Cross-Verification]
│
┌─────────────┴─────────────┐
▼                           ▼
[Verified Compliant]        [Discrepancy / Uncertainty]
│                           │
▼                           ▼
[Execute HR Decision]       [Escalate to Legal Advisor / 1823]
