# AI Model Card: HK Employment Ordinance Compliance Advisor

## 1. Model Overview & System Architecture
* **System Name**: Hong Kong Cap. 57 Employment Ordinance Compliance Advisor
* **System Type**: Deterministic Guardrail + Retrieval-Augmented Generation (RAG) Architecture
* **Primary Language**: Traditional Chinese (zh-HK) & English (en-US)
* **Underlying Embedding Engine**: `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`
* **Vector Store**: FAISS (Facebook AI Similarity Search)
* **Governance Standard**: ISO/IEC 42001 AIMS Clause 6.1 & Annex A.6.2 (AI System Documentation)

## 2. Intended Use & Boundaries
### Intended Use (Primary Scope)
* Enterprise HR compliance pre-checking and risk screening for Hong Kong employment law.
* Instant retrieval and page-level source tracing for official Labour Department guides.
* Decision support for HR professionals regarding statutory benefits and calculations.

### Out-of-Scope & Prohibited Uses
* **Legal Representation**: This tool is NOT a licensed legal advisor and does NOT generate formal legal opinions.
* **Automated Decision-Making (ADM)**: This tool must NEVER execute automated terminations, wage deductions, or disciplinary actions without human review.

## 3. Data Lineage & Vectorization Specifications
* **Base Knowledge Assets**:
  1. `EO_guide_full_tc.pdf` (Concise Guide to the Employment Ordinance - TC)
  2. `EO_guide_full_en.pdf` (Concise Guide to the Employment Ordinance - EN)
  3. `continuous_contract_FAQ_tc.pdf` (Revised Continuous Contract "468" FAQ - TC)
  4. `continuous_contract_FAQ_en.pdf` (Revised Continuous Contract "468" FAQ - EN)
* **Chunking Strategy**: Fixed-size chunking (`chunk_size = 400`, `overlap = 80`) with whitespace normalization via `pdfplumber`.
* **Knowledge Asset Count**: 562 verified vector chunks.

## 4. Safety Controls & Risk Mitigation
* **Deterministic Guardrails**: High-risk statutory queries (Summary Dismissal under s.9, Continuous Contract "468" rules, ADW 713 calculations) bypass probabalistic retrieval and trigger 100% deterministic compliance rules.
* **Confidence Gating**: Queries with similarity confidence < 25.0% are blocked automatically with fallback links to government sources.
* **Audit Trail**: Every query produces a SHA-256 cryptographic Audit ID with UTC timestamps for ISO 42001 verification.
