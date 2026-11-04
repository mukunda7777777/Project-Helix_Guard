# Helix Guard: Genomic Machine Learning & Evidence Intelligence Platform

[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/)
[![PyTest](https://img.shields.io/badge/tests-125%20passed-brightgreen.svg)]()
[![Platform](https://img.shields.io/badge/platform-Streamlit-red.svg)](https://streamlit.io)
[![License](https://img.shields.io/badge/license-Research--Only-lightgrey.svg)]()

**Helix Guard** is a computational research decision-support platform combining classical deep learning, real-world genetic variant intelligence, quantum neural network (QNN) modeling, and an integrated multi-source genetic evidence engine.

---

## Architecture Overview

Helix Guard integrates three primary analytical workflows and an evidence intelligence engine:

1. **Tab 1: Classical Residual 1D-CNN Sequence Optimizer**
   - 101-bp genomic sequence scanning using PyTorch residual convolutional networks.
   - Evaluates candidate single-base substitutions to reduce sequence model output scores (unvalidated research metric).

2. **Tab 2: Quantum Intelligence Engine**
   - 4-qubit parameterized quantum classifier built with native Qiskit 2.x APIs (`ZZFeatureMap` + `RealAmplitudes`).
   - Analyzes compact biological feature vectors on classical simulation backends (`StatevectorEstimator`).
   - Clear synthetic demonstration labeling with zero-leakage IBM Quantum credential security.

3. **Tab 3: Real ClinVar Genetic Variant Intelligence & Controlled Benchmark**
   - End-to-end machine learning pipeline operating on ClinVar conflicting variants (`clinvar_conflicting.csv`, 65,188 records).
   - Pre-split data partitioning ensuring zero preprocessing leakage.
   - Controlled 3-model benchmark (Logistic Regression vs. Random Forest vs. 4-Qubit QNN on identical 120/50 splits).
   - Multi-source Genetic Evidence Intelligence module integrating:
     - **NCBI ClinVar**: Variant-specific classifications, review status, star ratings, and submitter records.
     - **Ensembl VEP**: Transcript consequence annotations, coding DNA/protein changes, SIFT, and PolyPhen scores.
     - **gnomAD v4**: Population allele frequencies, allele counts, and ancestry breakdowns.
     - **NCBI PubMed**: Peer-reviewed citations linked to specific variant loci.
     - **ClinGen**: Gene-disease clinical validity context.

---

## Verification & Test Suite

The platform includes **125 automated tests** across four test modules (100% pass rate):

| Module | Test Count | Scope |
|---|---|---|
| `test_evidence_engine.py` | 48 | Data contracts, assembly isolation, 5-source adapters, normalizer, and conflict detection |
| `test_genetic_data_engine.py` | 23 | ClinVar ingestion, label curation, target-leakage prevention, and feature engineering |
| `test_quantum_engine.py` | 34 | Qiskit circuit construction, feature normalizers, ansatz evaluation, and model persistence |
| `test_streamlit_app.py` | 20 | Streamlit UI integration, security/credential masking, and evidence rendering |
| **Total** | **125** | **Zero failures, zero skips (Exit Code: 0)** |

---

## Quickstart

### 1. Installation
```bash
git clone https://github.com/mukunda7777777/Project-Helix_Guard.git
cd Project-Helix_Guard
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Run Test Suite
```bash
python -m pytest -q --tb=short
```

### 3. Launch the Application
```bash
streamlit run app.py
```
Open `http://localhost:8501` in your browser.

---

## Scientific & Ethical Disclaimers

> **IMPORTANT**: Helix Guard provides in-silico computational research decision-support only. It does not provide clinical diagnoses, therapeutic prescriptions, or autonomous gene-editing recommendations. All assertions are traceable to primary source endpoints with explicit reference assembly isolation (GRCh38 vs. GRCh37).
