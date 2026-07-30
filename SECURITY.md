# Security & Privacy Policy (SECURITY.md)

## 1. Security Architecture & ISO 27001 Alignment
This project strictly enforces in-memory processing to guarantee data privacy and zero retention for enterprise human resources query logs.

## 2. Privacy-Preserving Mechanisms
* **Zero Data Retention (ZDR)**: User queries and dynamic PDF uploads are held strictly within volatile container memory (RAM) and are automatically destroyed when the browser session terminates or refreshes.
* **Data Minimization (PII Masking)**: Operational logs stored in `compliance_audit.log` write ONLY the SHA-256 cryptographic audit hashes and UTC timestamps. Raw user prompts and sensitive personnel queries are strictly stripped from server storage.
* **Cryptographic Tamper-Evidence**: Auditable outputs are hashed using SHA-256 (`hashlib.sha256().hexdigest()`) with standard UTC time (`datetime.now(timezone.utc)`).

## 3. Vulnerability Reporting
If you discover a potential security vulnerability within this repository, please notify the system maintainer directly via GitHub Security Advisories or private channel. Do NOT open public issues for zero-day vulnerabilities.
