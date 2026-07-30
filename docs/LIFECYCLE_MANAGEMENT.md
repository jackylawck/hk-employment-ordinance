# System Lifecycle & Change Management (LIFECYCLE_MANAGEMENT.md)

## 1. Compliance Alignment
* **Standards**: EU AI Act Article 72 (Post-market Monitoring), ISO 42001 Clause 8 & Annex A.10 (Lifecycle & Change Management), NIST AI RMF MANAGE 3.1.

## 2. Regulatory Trigger & Maintenance Lifecycle
When the HKSAR Labour Department issues new statutory amendments (e.g. statutory holiday additions, minimum wage adjustments, or ordinance revisions):
[Legislative Amendment] ➔ [Download Official PDF] ➔ [Drop into Root Repository]
│
▼
[FAISS Index Auto-Rebuild]
│
▼
[Regression Drill Execution]
│
▼
[Deploy to Production]

## 3. Regression Testing Protocol
Prior to approving any code or knowledge base update for production deployment, the AI Governance Officer must execute the standard test suite covering:
1. **High-Risk Guardrail Tests**: Insubordination/summary dismissal query handling.
2. **Formula Accuracy Tests**: 12-Month Average Wage (ADW 713) disregarded period extraction.
3. **Boundary Threshold Tests**: Continuous contract "468" vs "418" rule resolution.
