# Data Lineage & Governance Specification (DATA_GOVERNANCE.md)

## 1. Compliance Alignment
* **Standards**: EU AI Act Article 10 (Data Governance), ISO 42001 Annex A.7 (Data for AI Systems), NIST AI RMF MAP 2.1 & MEASURE 2.2.

## 2. Data Lineage & Authority
All data ingested into the vector database originates exclusively from official, publicly released Hong Kong Special Administrative Region (HKSAR) Labour Department publications.

* **Primary Corpus**:
  1. *A Concise Guide to the Employment Ordinance (Cap. 57)* [HKSAR Labour Department]
  2. *Frequently Asked Questions on Revised "Continuous Contract" (468 Rule)* [HKSAR Labour Department]

## 3. Data Processing Pipeline & Quality Assurance
1. **Extraction**: Parsed using `pdfplumber` for table-aware, multi-lingual text extraction.
2. **Normalization**: Whitespace collapse, redundant header/footer stripping via regex (`re.sub(r'\s+', ' ', text)`).
3. **Chunking Parameters**: `chunk_size = 400`, `overlap = 80`.
4. **Validation**: Chunks containing less than 10 words or non-character noise are automatically discarded during index construction.
