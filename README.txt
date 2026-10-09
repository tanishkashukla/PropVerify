PROPV​ERIFY — REALISTIC SYNTHETIC TEST DOCUMENT SET

These are fictional, realistic-format documents created ONLY for software development and testing.

Documents:
1. Sale Deed — multi-section, multi-page legal-style document
2. Property Card — registry-style property record
3. Index II — registration summary
4. 7/12 Extract — land-record-style document
5. Identity Proof — fictional identity document

Common data:
Owner: Aarav Mehta
Address: Flat 704, Lakeview Residency, Mahatma Phule Road, Andheri East, Mumbai, Maharashtra - 400069
Survey/Gat Number: 124/3A
Area: 111.48 sq. m. (1,200 sq. ft.)
Registration Number: MUM/REG/2026/04821

INTENTIONAL TEST MISMATCH:
Index II has Survey/Gat Number = 124/8.
All other property records use Survey/Gat Number = 124/3A.

Expected PropVerify behavior:
- Classify each document.
- Extract owner/name, address, survey/gat number, area, registration number, dates where available.
- Match common fields across documents.
- Flag the Index II survey/gat number as a POSSIBLE MISMATCH.
- If the 7/12 Extract is removed before upload, flag it as a MISSING DOCUMENT.

IMPORTANT:
All names, addresses, numbers, dates, and records are fictional.
These files are not legal documents and must not be used for real transactions.
