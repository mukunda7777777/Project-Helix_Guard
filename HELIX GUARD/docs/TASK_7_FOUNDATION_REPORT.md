# HELIX GUARD — TASK 7 FOUNDATION REPORT
## Genetic Evidence Intelligence: Foundation & Data Architecture

**Platform**: Helix Guard Genomic AI & Quantum Intelligence Research Platform  
**Module**: `evidence_engine.py` (Genetic Evidence Intelligence Engine)  
**Status**: COMPLETE — 89 Automated Tests Passing (100% Success)  
**Date**: November 2026  

---

### 1. Executive Summary & Objective

Helix Guard has expanded from static offline dataset modeling (`clinvar_conflicting.csv`) toward a traceable, evidence-backed computational genetic research platform. Task 7 establishes the foundation of the **Genetic Evidence Intelligence Engine**, providing normalized data schemas, source adapters, rate-limited and cached network connectors, empirical quality audits, and conflict-detection mechanisms across five authoritative biomedical knowledge repositories.

#### Core Design Mandates Followed
1. **Zero Credential Exposure**: No API keys or tokens are embedded in source code. Optional environment variables (`NCBI_API_KEY`) are supported with safe fallback.
2. **Explicit Assembly Discipline**: Reference assemblies (`GRCh38` vs. `GRCh37`) are strictly isolated and tracked. Genomic coordinates and transcript structures from different assemblies are never silently merged.
3. **Traceable Evidence Provenance**: Every piece of data displayed to the researcher preserves its primary source repository, exact API endpoint, UTC retrieval timestamp, source URL, cache status, and response latency.
4. **Epistemological Integrity & Non-Fallacy Rules**: Explicit architectural guardrails prevent treating ClinVar submitter disagreement as pathogenicity, population frequency as proof of benignity, or computational predictions as clinical proof.
5. **No Data Fabrication**: If a source is unavailable or an entity is unindexed, the engine reports an honest status (`UNAVAILABLE`, `TIMEOUT`, `ERROR`) without generating hallucinated or synthetic surrogate data.
6. **Full System Preservation**: All existing functionality (Task 1–3 QNN and CNN, Task 4 ClinVar ML pipeline, Task 6 defect corrections, and all Streamlit tabs) remains 100% operational.

---

### 2. Architecture & Component Responsibilities

The Genetic Evidence Intelligence architecture is organized into four modular layers:

```
+-----------------------------------------------------------------------------------------+
|                              STREAMLIT RESEARCH PLATFORM                                |
|  Tab 1: Classical CNN  |  Tab 2: Quantum Demo  |  Tab 3: Genetic Variant Intelligence   |
|                                                +-- Section 1: Dataset Inspection        |
|                                                +-- Section 2: Label Curation            |
|                                                +-- Section 3: Controlled Benchmarking   |
|                                                +-- Section 4: Evidence Intelligence     |
+-----------------------------------------------------------------------------------------+
                                             |
                                             v
+-----------------------------------------------------------------------------------------+
|                         GENETIC EVIDENCE ORCHESTRATOR                                   |
|                          (evidence_engine.py)                                           |
|  - search_gene(symbol, assembly)                                                        |
|  - search_variant(variant_id, assembly)                                                 |
|  - Assembly Guardrail (GRCh38 vs GRCh37 routing)                                        |
|  - Evidence Quality Assessment (ACMG Stars, Confidence Tiers)                           |
|  - Submitter Disagreement Auditing                                                      |
+-----------------------------------------------------------------------------------------+
         |                     |                   |                 |               |
         v                     v                   v                 v               v
+-----------------+   +----------------+   +---------------+   +------------+   +-----------+
| ClinVarAdapter  |   | ClinGenAdapter |   | EnsemblAdapter|   |GnomadAdapter|  |PubMedAdapt|
| (E-utilities)   |   | (Search REST)  |   | (REST v15)    |   | (GraphQL)  |   |(E-utilitie|
| - Classification|   | - Validity     |   | - Gene ID     |   | - pLI      |   | - Citations
| - Review Stars  |   | - Dosage       |   | - Transcripts |   | - LOEUF    |   | - PMIDs   |
| - Submissions   |   | - HI/TS Scores |   | - Coordinates |   | - Pop AF   |   | - DOIs    |
+-----------------+   +----------------+   +---------------+   +------------+   +-----------+
         |                     |                   |                 |               |
         +---------------------+-------------------+-----------------+---------------+
                                             |
                                             v
+-----------------------------------------------------------------------------------------+
|                                EVIDENCE CACHE LAYER                                     |
|  - SHA-256 Key Derivation: (Source + Endpoint + Query + Assembly)                       |
|  - Configurable TTL (Default: 24 Hours)                                                 |
|  - Persistent Disk Storage (.cache/evidence/*.json) + In-Memory Fallback                |
|  - Offline Mode Fallback with is_expired_fallback flag                                  |
+-----------------------------------------------------------------------------------------+
```

---

### 3. Data Contracts & Normalized Evidence Schemas

The engine defines standardized, strongly-typed data contracts using Python dataclasses and enums:

#### Enums
- `GenomeAssembly`: `GRCh38` (default), `GRCh37` (archival/hg19), `UNKNOWN`.
- `EvidenceLevel`:
  - `DIRECT_REPORT`: Empirical data directly reported by an authoritative repository (e.g., ClinVar submission, ClinGen validity).
  - `DERIVED`: Deterministic mathematical transformation (e.g., calculating global AF from AC/AN).
  - `COMPUTATIONAL_PREDICTION`: In-silico algorithmic inference (CADD, SIFT, PolyPhen, QNN).
  - `RESEARCH_HYPOTHESIS`: Hypothetical sequence modification or exploratory query.
  - `UNKNOWN_UNAVAILABLE`: Field absent or service unindexed.
  - `CONFLICTING`: Contradictory assertions between submitters or independent sources.
- `SourceStatus`: `AVAILABLE`, `CACHED`, `UNAVAILABLE`, `ERROR`, `TIMEOUT`.

#### Standardized Contracts
1. `EvidenceProvenance`:
   - `source_name: str`: Identifying name of the repository.
   - `source_endpoint: str`: Endpoint path accessed (e.g. `esummary.fcgi`, `lookup/symbol`).
   - `retrieval_timestamp: str`: ISO 8601 UTC timestamp of retrieval.
   - `source_url: str`: Web-accessible link to the record or query.
   - `is_cached: bool`: Whether record was served from local cache.
   - `response_latency_ms: float`: Roundtrip network latency in milliseconds.
   - `assembly: GenomeAssembly`: Explicit genome reference assembly.
   - `license_notice: str`: Applicable open-access licensing terms.
2. `GeneIdentity`:
   - Ensembl stable gene ID (`ENSG...`), Entrez gene ID, HGNC ID, biotype, chromosome, start, end, strand, description, and aliases.
3. `VariantIdentity`:
   - Variant ID (rsID, ClinVar variation UID), genomic chromosome, 1-based position, reference allele, alternate allele, explicit assembly, HGVS nomenclature.
4. `TranscriptAnnotation`:
   - Ensembl transcript ID (`ENST...`), canonical flag (`is_canonical`), MANE Select flag (`is_mane_select`), consequence terms, protein translation ID (`ENSP...`).
5. `ClinicalClassification` & `ClinVarSubmission`:
   - Primary clinical classification, ACMG review status, review stars (0–4), associated phenotypes/conditions, evaluation date, and full list of per-submitter records (`submitter_name`, `clinical_significance`, `review_status`).
   - Conflict detection: `is_conflicting: bool`, `conflict_summary: Optional[str]`.
6. `PopulationFrequency`:
   - Allele count (AC), allele number (AN), global allele frequency (AF), homozygote count, ancestry frequency breakdowns, and gene constraint metrics (`pLI`, `oe_lof_upper` / LOEUF).
7. `GeneDiseaseValidity`:
   - Gene symbol, disease label, disease identifier (MONDO/OMIM CURIE), clinical validity classification (Definitive, Strong, Moderate, Limited, Disputed, Refuted), mode of inheritance, haploinsufficiency and triplosensitivity scores (0–3), curation date, and ClinGen report link.
8. `LiteratureReference`:
   - PubMed ID (PMID), article title, author list, journal abbreviation, publication year, DOI, and direct link (`https://pubmed.ncbi.nlm.nih.gov/{pmid}/`).
9. `GeneticEvidenceBundle`:
   - Unified aggregator uniting all the above records for a target query, including overall query metadata, source operational statuses, quality tier summary, and explicit scientific limitations.

---

### 4. Supported Evidence Sources & Endpoints

| Source Repository | Access Protocol | Endpoints Used | Key Extracted Fields | Rate Limit Policy |
|---|---|---|---|---|
| **NCBI ClinVar** | REST / XML / JSON (E-utilities) | `esearch.fcgi?db=clinvar`<br>`esummary.fcgi?db=clinvar` | Primary classification, ACMG review status, 0–4 stars, conditions, per-submitter assertions, conflict flags | Max 3 req/sec without key; 10 req/sec with `NCBI_API_KEY` |
| **ClinGen** | REST / JSON | `search.clinicalgenome.org/api/validity`<br>`search.clinicalgenome.org/api/dosage` | Gene-disease validity status (Definitive, Strong, etc.), mode of inheritance, haploinsufficiency & triplosensitivity scores (0–3) | Max 3 req/sec |
| **Ensembl** | REST / JSON | `rest.ensembl.org/lookup/symbol/homo_sapiens/{symbol}`<br>`grch37.rest.ensembl.org/lookup/symbol/...`<br>`/variation/human/{id}` | Gene stable ID (ENSG), canonical transcript, MANE Select transcript, coordinates, biotype, strand, assembly | Max 15 req/sec (throttled to 10 req/sec) |
| **gnomAD** | GraphQL / JSON | `gnomad.broadinstitute.org/api` | Gene constraint metrics (`pLI`, `oe_lof_upper` / LOEUF), variant allele frequencies (AC, AN, AF), ancestry breakdowns | Max 3 req/sec |
| **NCBI PubMed** | REST / JSON (E-utilities) | `esearch.fcgi?db=pubmed`<br>`esummary.fcgi?db=pubmed` | PMIDs, article titles, author lists, journal, publication date, DOI, direct article URLs | Max 3 req/sec without key; 10 req/sec with `NCBI_API_KEY` |

---

### 5. Source Limitations & Unavailable Field Handling

1. **NCBI ClinVar**:
   - `clinvar_conflicting.csv` records in the local archive represent historical snapshot variants. Live ClinVar E-utilities queries retrieve the current, up-to-date consensus record and latest laboratory submissions.
   - Star calculations follow standard ACMG/ClinVar guidelines:
     - 4 Stars: Practice guideline (`practice guideline`)
     - 3 Stars: Reviewed by expert panel (`reviewed by expert panel`)
     - 2 Stars: Criteria provided, multiple submitters, no conflicts (`multiple submitters... no conflict`)
     - 1 Star: Criteria provided, single submitter, or conflicting classifications (`criteria provided...`)
     - 0 Stars: No assertion criteria provided (`no assertion criteria provided` or `no assertion provided`)
2. **ClinGen**:
   - Not all human genes have undergone expert panel curation. If a gene has not been reviewed by a ClinGen Gene Curation Expert Panel (GCEP), the endpoint returns empty records. The engine reports this honestly as `⚪ No ClinGen gene-disease validity curations indexed for this gene` without inventing dummy curation data.
3. **Ensembl**:
   - Primary human reference queries default to `GRCh38`.
   - When the user selects `GRCh37`, requests are routed to `grch37.rest.ensembl.org`. Coordinates, exon boundaries, and transcript IDs are strictly matched to the selected assembly.
4. **gnomAD**:
   - `gnomad_r4` is queried for GRCh38; `gnomad_r2_1` is queried for GRCh37.
   - For non-coding variants or unobserved alleles, gnomAD will return null frequency data. The engine displays "Not observed in gnomAD" rather than asserting a frequency of zero.
5. **NCBI PubMed**:
   - Queries retrieve up to 5 of the most relevant peer-reviewed citations matching the target gene or variant.

---

### 6. Caching & Failure-Handling Strategy

#### SHA-256 Key Derivation
To guarantee absolute partition isolation between queries and assemblies, cache keys are computed as:
$$\text{Key} = \text{SHA256}(\text{Source} : \text{Endpoint} : \text{QueryTerm} : \text{Assembly})$$
This ensures a query for `BRCA1` on `GRCh38` can never collide with or return cached data for `BRCA1` on `GRCh37`.

#### Two-Tier Storage Architecture
- **In-Memory Cache**: Rapid dictionary lookup for repeat accesses within the same execution session.
- **Persistent Disk Cache**: Stored as human-readable, formatted JSON files in `HELIX GUARD/.cache/evidence/`. If file writes are disallowed by host permissions, the cache falls back gracefully to in-memory mode without errors.
- **Time-to-Live (TTL)**: Default TTL is 24 hours (86,400 seconds).

#### Offline & Network Failure Resilience
- If the network experiences an unexpected timeout, connection refusal, or DNS failure:
  - If a cached record exists (even if past TTL), the adapter returns `SourceStatus.CACHED` with `is_expired_fallback = True`.
  - If no cached record exists, the adapter catches the exception, logs the sanitized message, and returns `SourceStatus.TIMEOUT` or `SourceStatus.ERROR`.
  - The application UI never raises unhandled HTTP exceptions or crashes.

---

### 7. Scientific Integrity & Defense Against Biological Fallacies

Helix Guard is an in-silico computational research and decision-support tool. To prevent misuse, the interface and data models enforce the following epistemological rules:

1. **Submitter Disagreement $\neq$ Pathogenicity**: In ClinVar, when submitters assert discordant classifications (e.g. 1 Pathogenic vs 2 VUS), the engine marks the record as `is_conflicting=True` and issues a prominent warning:
   > *"Submitter disagreement indicates lack of laboratory consensus and must not be interpreted as verified biological pathogenicity."*
2. **Population Rarity $\neq$ Pathogenicity**: Extremely rare or unobserved variants in gnomAD are not assumed to be pathogenic. Private benign polymorphisms frequently appear as unique singleton observations.
3. **Population Frequency $\neq$ Benignity**: Measurable population frequency does not definitively rule out disease causality, particularly for late-onset, variable-penetrance, or recessive phenotypes.
4. **Computational Prediction $\neq$ Clinical Confirmation**: Scores from in-silico predictors (CADD, SIFT, PolyPhen, CNN, QNN) are exploratory research hypothesis generators that require independent wet-lab functional validation.
5. **Literature Citations $\neq$ Verified Consensus**: Published article titles and abstracts report study findings and experimental hypotheses, not definitive clinical truth.
6. **Prohibited Clinical & Biological Workflows**:
   - No human embryo editing protocols.
   - No wet-lab execution steps or recipe generation.
   - No autonomous therapeutic decisions.
   - No claims that a variant can be safely corrected in human subjects.

---

### 8. Streamlit User Interface Integration

The Genetic Evidence Intelligence Explorer is integrated into **Tab 3 ("Genetic Variant Intelligence")** as **Section 4: Multi-Source Genetic Evidence Intelligence & Traceability**:

- **Target Query Selector**: Toggle between "Gene Symbol" (e.g. `BRCA1`, `TP53`, `LDLR`, `MYH7`, `CFTR`) and "Variant Identifier" (e.g. `rs28897743`, `rs80357906`, `12345`).
- **Assembly Selector**: Radio button allowing explicit selection between `GRCh38 (Default / Latest)` and `GRCh37 (hg19 / Archival)`.
- **Cache Toggle**: Checkbox allowing the researcher to bypass or utilize local cache.
- **Source Status Indicators**: Five live badges indicating the real-time operational status of each repository (`🟢 Live Available`, `🔵 Validated Cache`, `🟡 Timed Out`, `⚪ Not Indexed`, `🔴 Endpoint Error`).
- **Gene & Variant Identity Card**: Displays Ensembl gene stable ID, chromosome locus, 1-based start-end coordinates, biotype, and explicit assembly. Expandable table of canonical and MANE Select transcripts.
- **ClinVar Classification & Submitter Conflict Auditing**: Primary classification badge, ACMG 0–4 star rating metric, associated condition list, conflict warning banner, and full table of individual submitters and evaluation dates.
- **gnomAD Population Metrics**: Metrics for `pLI` (loss-of-function intolerance) and `LOEUF` (oe_lof_upper) with hover tooltips explaining interpretive thresholds.
- **ClinGen Gene-Disease Validity**: Table of curated gene-disease relationships, expert panel classification, and mode of inheritance.
- **PubMed Scientific Literature**: Interactive table of peer-reviewed publications with PMIDs, titles, journals, publication years, DOIs, and clickable links.
- **Traceability Drawer**: Expandable table listing each source's exact URL, endpoint, UTC timestamp, network latency (ms), and licensing notice.
- **Scientific Limitations Expander**: Expandable disclosure listing all active epistemological limitations for the record.

---

### 9. Automated Testing & Verification Suite

A comprehensive test suite of 20 new tests was implemented in `HELIX GUARD/tests/test_evidence_engine.py`, alongside a new UI test in `HELIX GUARD/tests/test_streamlit_app.py`. All external HTTP requests are mocked using `unittest.mock.patch`, ensuring tests execute with 0 network dependency and 100% determinism.

#### Test Execution Summary

```text
============================= test session starts =============================
platform win32 -- Python 3.12.10, pytest-9.2.0, pluggy-1.7.0
rootdir: P:\projects\HELIX GUARD-20260822T181751Z-1-001
collected 89 items

HELIX GUARD/tests/test_evidence_engine.py ....................           [ 22%]
HELIX GUARD/tests/test_genetic_data_engine.py .......................    [ 48%]
HELIX GUARD/tests/test_quantum_engine.py .................................. [ 86%]
HELIX GUARD/tests/test_streamlit_app.py ............                     [100%]

======================== 89 passed, 48 warnings in 34.11s =======================
```

#### Detailed Evidence Engine Tests (20 Tests)
1. `test_evidence_provenance_contract`: Validates data contract, ISO timestamps, and dictionary serialization.
2. `test_gene_identity_contract`: Validates gene identity, coordinates, and optional fields.
3. `test_variant_identity_assembly_strictness`: Proves that GRCh38 and GRCh37 variant identities maintain distinct coordinate spaces.
4. `test_genetic_evidence_bundle_serialization`: Verifies complete bundle JSON-compliant export.
5. `test_evidence_cache_hit_and_miss`: Tests key derivation, initial cache miss, and subsequent hit.
6. `test_evidence_cache_ttl_expiration_and_offline_fallback`: Verifies cache expiration and offline fallback mode.
7. `test_clinvar_star_calculation`: Validates mapping of ACMG review status strings to 0–4 stars, properly prioritizing "no assertion criteria" to 0.
8. `test_clinvar_adapter_conflicting_submission`: Validates parsing of conflicting laboratory submissions and conflict flag assertion.
9. `test_clinvar_adapter_missing_record_handling`: Verifies unindexed variants return `SourceStatus.UNAVAILABLE`.
10. `test_clingen_adapter_validity_parsing`: Tests gene-disease validity parsing and target gene filtering.
11. `test_clingen_adapter_404_handling`: Verifies 404 responses are caught and handled as `UNAVAILABLE`.
12. `test_ensembl_assembly_routing`: Validates that GRCh38 routes to `rest.ensembl.org` while GRCh37 routes to `grch37.rest.ensembl.org`.
13. `test_gnomad_adapter_gene_constraint`: Verifies GraphQL response parsing for `pLI` and `oe_lof_upper`.
14. `test_pubmed_adapter_literature_search`: Tests two-stage search (`esearch` -> `esummary`), author list parsing, and DOI extraction.
15. `test_api_timeout_handling`: Verifies network timeouts report `TIMEOUT` without crashing.
16. `test_api_connection_error_handling`: Verifies connection/DNS errors report `ERROR` cleanly.
17. `test_orchestrator_gene_search`: Tests multi-source aggregation across all 5 adapters for gene queries.
18. `test_orchestrator_variant_search`: Tests multi-source aggregation for variant queries.
19. `test_corrupt_json_and_500_server_error_handling`: Verifies HTTP 500 and malformed JSON payloads return `ERROR` without throwing exceptions.
20. `test_duplicate_submission_and_condition_deduplication`: Verifies redundant disease traits are deduplicated.

#### Regression Testing
- **Genetic Data Engine**: All 23 tests pass (pre-split zero leakage, target-defining feature purging, controlled benchmarks).
- **Quantum Engine**: All 34 tests pass (circuit construction, class-weighted BCE loss, save/load, simulation).
- **Streamlit App**: All 12 tests pass (UI rendering, terminology checks, credential security, interactive inference, Section 4 evidence queries).

---

### 10. Summary of Changed & Created Files

1. `HELIX GUARD/evidence_engine.py` *(New)*: Comprehensive Genetic Evidence Intelligence Engine containing data contracts, caching layer, 5 source adapters, and the orchestrator.
2. `evidence_engine.py` *(New)*: Root gateway cleanly re-exporting all components from `HELIX GUARD/evidence_engine.py`.
3. `HELIX GUARD/tests/test_evidence_engine.py` *(New)*: 20 unit and integration tests covering all evidence schemas, source adapters, error conditions, and caching.
4. `HELIX GUARD/app.py` *(Updated)*: Integrated Section 4 Multi-Source Evidence Intelligence into Tab 3 with live status badges, identity cards, conflict tables, and provenance drawer.
5. `HELIX GUARD/tests/test_streamlit_app.py` *(Updated)*: Added UI integration test for Section 4 evidence query execution.
6. `HELIX GUARD/docs/TASK_7_FOUNDATION_REPORT.md` *(New)*: This comprehensive architectural and operational documentation.
7. `HELIX GUARD/README_QNN.md` & `README_QNN.md` *(Updated)*: Main documentation updated with Task 7 evidence architecture.

---

### 11. Known Limitations & Next Implementation Steps

- **Batch Variant Processing**: The current interface executes single-entity searches (one gene or one variant at a time). Future tasks can expand this to support batch variant callset (VCF) annotation.
- **Variant Effect Predictor (VEP) REST Integration**: Deep consequence annotations (e.g. SIFT/PolyPhen live scores, splice site proximity) can be integrated via Ensembl VEP REST endpoints.
- **ClinGen Dosage Sensitivity Direct Query**: The current adapter implements gene-disease validity; dosage sensitivity (HI/TS) can be expanded to parse full regional haploinsufficiency evidence tables.
- **Automated Evidence Synthesis**: Subsequent tasks will bridge this evidence layer with the ML/QNN classifiers to perform evidence-weighted multi-modal variant scoring.

