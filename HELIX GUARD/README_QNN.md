# Helix Guard: Genomic Machine Learning & Quantum Intelligence Research Platform

## 1. Overview & Architecture
The **Helix Guard** platform combines classical deep learning, real-world genetic variant intelligence, and an independent **Quantum Neural Network (QNN)** research engine for computational genetic-variant analysis:

1. **Classical Residual 1D-CNN (Sequence Optimizer)**: Scans 101-bp genomic target windows, computes model output scores (unvalidated), and identifies candidate single-base substitutions to reduce sequence scores.
2. **Quantum Intelligence Engine (Task 1 & Task 2)**: Parameterized 4-qubit quantum classifier integrated via Streamlit. Analyzes compact biological feature vectors using non-linear quantum feature maps and variational ansatz circuits.
3. **Scientific Integrity & Backend Security (Task 3)**: Rigorous scientific terminology, persistent transparency disclaimers, clear synthetic demonstration labeling, and zero-leakage credential management for IBM Quantum.
4. **Real ClinVar Genetic Variant Intelligence Pipeline (Task 4 & Task 6)**: End-to-end machine learning and quantum evaluation pipeline operating on actual ClinVar records (`clinvar_conflicting.csv`), featuring:
   - Reconciled dataset counts and confirmed **GRCh37 (hg19)** assembly.
   - Pre-split data partitioning ensuring **zero preprocessing leakage**.
   - Strict target-leakage prevention (purging `SIFT` and `PolyPhen` from Task C inputs).
   - **Controlled Apples-to-Apples Benchmark** (Logistic Regression vs Random Forest vs 4-Qubit QNN on the exact same 4 compact features and identical 120/50 sample partitions).
   - Balanced class-weighted QNN loss addressing majority-class collapse.
5. **Genetic Evidence Intelligence Engine (Task 7)**: Multi-source evidence collection, normalization, quality evaluation, and transparent provenance tracking across **NCBI ClinVar**, **ClinGen**, **Ensembl**, **gnomAD**, and **PubMed** with strict reference assembly isolation (GRCh38 vs. GRCh37).

```
+-------------------------------------------------------------------------------------------------------------+
|                                           HELIX GUARD PLATFORM                                              |
|                                                                                                             |
|   Tab 1: 🧬 Classical Optimizer       Tab 2: ⚛️ Quantum Intelligence      Tab 3: 🔬 Real ClinVar Pipeline   |
|   +-----------------------------+     +-----------------------------+     +-----------------------------+   |
|   | Target DNA Sequence (101-bp)|     | Synthetic 4D Features       |     | clinvar_conflicting.csv     |   |
|   | One-Hot Matrix: 4 x 101     |     | [AF, Cons, GC, Impact]      |     | (65,188 Real ClinVar Rows)  |   |
|   +--------------+--------------+     +--------------+--------------+     +--------------+--------------+   |
|                  |                                   |                                   |                  |
|                  v                                   v                                   v                  |
|   +-----------------------------+     +-----------------------------+     +-----------------------------+   |
|   | Residual 1D-CNN (PyTorch)   |     | Synthetic 4-Qubit QNN       |     | Zero Preprocessing Leakage  |   |
|   | 2 Residual Blocks           |     | ZZFeatureMap + RealAmps     |     | Task C Leakage Purged       |   |
|   +--------------+--------------+     +--------------+--------------+     +--------------+--------------+   |
|                  |                                   |                                   |                  |
|                  v                                   v                                   v                  |
|   +-----------------------------+     +-----------------------------+     +-----------------------------+   |
|   | Candidate Substitutions     |     | Synthetic Demonstration     |     | Controlled 3-Model Benchmark|   |
|   | Unvalidated Output Score    |     | Probability Distribution    |     | LR vs RF vs 4-Qubit QNN     |   |
|   +-----------------------------+     +-----------------------------+     +-----------------------------+   |
+-------------------------------------------------------------------------------------------------------------+
|   🔐 Zero-Leakage Security Layer:                                                                            |
|   - Precedence: Environment Variables > .env > Local Protected > Safe Unconfigured Local Simulation         |
|   - Masked token introspection (d1ID••••••••NHp); zero plaintext display or logging                         |
|   - Local CPU simulation default (Qiskit StatevectorEstimator)                                              |
+-------------------------------------------------------------------------------------------------------------+
```

---

## 2. Scientific & Ethical Disclaimers
> [!IMPORTANT]
> **Persistent Research Notice**: Helix Guard demonstrates experimental machine-learning and quantum-machine-learning workflows. Its models have not been validated for clinical pathogenicity diagnosis or biological DNA correction.

- **Model Scores Are Not Clinical Probabilities**: Computational outputs represent numerical function scores from an in-silico model and must not be used for medical diagnostic or clinical decisions.
- **Candidate Substitutions Are Computational Demonstrations**: In-silico modifications are synthetic algorithmic demonstrations, not biological gene-editing protocols or therapeutic recommendations.
- **Validation Requirements**: Clinical validity requires rigorously curated datasets (e.g., benchmarked ClinVar/gnomAD panels) and independent experimental wet-lab validation.
- **No Claim of Quantum Advantage**: The parameterized quantum circuit is evaluated on classical simulators (`StatevectorEstimator`). No claim of quantum supremacy or empirical advantage over classical deep learning models is made or implied.

---

## 3. Scientific Terminology Guidelines

To maintain scientific integrity, unvalidated claims have been replaced with precise research terminology:

| Classical Legacy Term | Scientifically Accurate Replacement |
|---|---|
| AI-Perfected DNA Output | **Hypothetical Sequence Modification** |
| Perfected Sequence | **Candidate Modified Sequence** |
| Pathogenicity Risk Score | **Model Output Score (Unvalidated)** |
| Found 5 optimal edit candidates that reduce pathogenicity | **Found 5 candidate substitutions that reduce the model output score** |
| Optimal Edit | **Candidate Substitution** |

| QNN Legacy Label | Scientifically Accurate Replacement |
|---|---|
| Pathogenic (1) | **Synthetic Class 1 (Pathogenic-like)** |
| Benign (0) | **Synthetic Class 0 (Benign-like)** |
| Pathogenic Risk | **Synthetic Model Output** |
| Test Accuracy | **Synthetic Test Accuracy** |

---

## 4. Quantum Circuit Architecture

The QNN is built using native **Qiskit 2.x** APIs and consists of two primary stages:

```
|0> ---[ H ]---[ Rz(x0) ]---*---------*---[ Ry(θ0) ]---*---------*---[ Ry(θ4) ]---( M: Z0 )
                            |         |                |         |
|1> ---[ H ]---[ Rz(x1) ]---X---*-----|---[ Ry(θ1) ]---X---*-----|---[ Ry(θ5) ]---( M: Z1 )
                                |     |                    |     |
|2> ---[ H ]---[ Rz(x2) ]-------X---*-|---[ Ry(θ2) ]-------X---*-|---[ Ry(θ6) ]---( M: Z2 )
                                    | |                        | |
|3> ---[ H ]---[ Rz(x3) ]-----------X-X---[ Ry(θ3) ]-----------X-X---[ Ry(θ7) ]---( M: Z3 )
       \______________________________/   \______________________________/
             Feature Map (ZZ)                     Ansatz (RealAmplitudes)
```

- **Qubits**: 4 (compact biological feature space).
- **Feature Map**: Non-linear `zz_feature_map(feature_dimension=4, reps=1, entanglement='linear')` or modular `AngleEncoding`.
- **Variational Ansatz**: `real_amplitudes(num_qubits=4, reps=2, entanglement='linear')`.
- **Parameters**: 4 feature parameters ($x_0 \dots x_3$), 12 trainable ansatz weights ($\theta_0 \dots \theta_{11}$), total = 16.
- **Circuit Depth**: 18 operations.
- **Measurement Observable**: Total average Pauli-$Z$ expectation value: $\hat{O} = \frac{1}{N} \sum_{i=0}^{N-1} Z_i$.

---

## 5. Real ClinVar Genetic Variant Pipeline & Defect Corrections (Task 4 & Task 6)

### 5.1 Reconciled Dataset Semantics & Provenance
- **Dataset File**: `HELIX GUARD/archive/clinvar_conflicting.csv`.
- **Verified Row Count**: Exactly **65,188 records** across 46 columns.
- **Ground Truth Target (`CLASS`)**:
  - `CLASS = 0`: **48,754 records (74.790%)** — Submitters concordant.
  - `CLASS = 1`: **16,434 records (25.210%)** — Submitters discordant/conflicting.
  - **Critical Caveat**: `CLASS` denotes clinical submission conflict, NOT clinical pathogenicity.
- **Column Status**: `CLNSIG` is absent from this dataset. `CLNSIGINCL` is present in only **167 records (0.256%)** (134 Pathogenic/Likely Pathogenic, 4 Benign/Likely Benign, 29 Uncertain/Other).
- **Confirmed Reference Assembly**: **GRCh37 (hg19)** (RefSeq chromosome accessions `NC_000001.10`, `NC_000002.11`, `NC_000017.10`). Coordinates must be lifted over before comparing against GRCh38 callsets.

### 5.2 Corrected Curation Strategies
1. **Task A: Conflict Prediction (`CLASS`)**: Predicts inter-laboratory clinical classification discordance across 65,188 variants (48,754 concordant vs. 16,434 conflicting).
2. **Task B: Explicit ClinVar Pathogenicity Subsetting (`CLNSIGINCL`)**: Curates explicit clinical significance determinations. Retains 136 records (133 Pathogenic, 3 Benign); transparently excludes 65,052 unannotated/conflicting records.
3. **Task C: In-Silico Consensus Classification (Target Leakage Corrected)**: Models functional predictor agreement between PolyPhen and SIFT.
   - **Scientific Safeguard**: Target-defining features `SIFT` and `PolyPhen` are strictly purged from model inputs, eliminating target leakage.

### 5.3 Zero Preprocessing Leakage Architecture
- **Splitting First**: Raw curated variants are partitioned into `df_train` and `df_test` using `DataSplitter.split_curated_dataframe()` prior to any transformation.
- **Training-Only Fitting**: Imputers, scalers, and one-hot encoders are fitted exclusively on `df_train`. Test variants never influence preprocessing statistics.
- **Locus & Gene Leakage Prevention**: Verified 0 duplicate loci across partitions (`locus_overlap == 0`). Optional `GroupShuffleSplit` on `SYMBOL` enforces strict out-of-gene generalization.

### 5.4 Controlled Benchmark: Classical ML vs. 4-Qubit QNN
All models are evaluated on the **exact same 4 compact biological features** (`AF_rarity`, `CADD/40`, `LoFtool`, `Impact/BLOSUM`) across the **exact same 120 training and 50 test variants**:

```
========================================================================================================================
Model Architecture (Controlled)       Features   Train/Test Split   Accuracy   Precision   Recall   F1-Score   ROC-AUC
========================================================================================================================
Controlled Logistic Regression               4            120 / 50     56.00%      0.3333   0.6923     0.4500    0.6133
Controlled Random Forest                     4            120 / 50     52.00%      0.2617   0.3846     0.2941    0.5270
Controlled Hybrid 4-Qubit QNN (Balanced)     4            120 / 50     42.00%      0.2778   0.7692     0.4082    0.5156
Hybrid 4-Qubit QNN (Unweighted Baseline)     4            120 / 50     62.00%      0.1250   0.0769     0.0952    0.4678
========================================================================================================================
```

- **QNN Failure Analysis**: With unweighted BCE, the QNN falls into majority-class collapse (F1: 0.0952, ROC-AUC: 0.4678) due to the 75% negative class imbalance. Incorporating balanced class weighting increases recall to **0.7692** and F1 to **0.4082**, though false positives lower overall accuracy to 42.0%. Classical linear models outperform the QNN on this compressed 4D representation. **No quantum advantage is observed.**

---

## 6. Backend Security & Credential Isolation (Task 3)

The application incorporates a zero-leakage security layer in [`security.py`](file:///p:/projects/HELIX%20GUARD-20260822T181751Z-1-001/HELIX%20GUARD/security.py):

1. **Precedence Hierarchy**:
   - Environment variables (`QISKIT_IBM_TOKEN` / `IBM_QUANTUM_API_KEY`, `IBM_QUANTUM_INSTANCE`)
   - Local `.env` configuration file
   - Protected local configuration fallback
   - Safe unconfigured local simulation mode
2. **Strict Masking**:
   - Tokens are masked on ingestion (e.g. `d1ID••••••••NHp`). Plaintext secrets are never exposed in UI widgets, logs, or string representations (`__repr__` and `__str__`).
3. **Repository Cleanliness**:
   - Both root `.gitignore` and `HELIX GUARD/.gitignore` exclude `*credentials*.txt`, `.env`, `*.env`, `*secret*`, `*.key`, and `*.token`.
   - `.env.example` provides a safe template for local configuration.
4. **Error Sanitization**:
   - `sanitize_message()` automatically strips suspected API keys and filesystem paths from any exception before display.
5. **Hardware Status Transparency**:
   - The UI clearly indicates that hardware execution is inactive, and all circuits currently execute via local `StatevectorEstimator` simulation.

---

## 7. Genetic Evidence Intelligence Engine (Task 7)

The Genetic Evidence Intelligence module ([`evidence_engine.py`](file:///p:/projects/HELIX%20GUARD-20260822T181751Z-1-001/HELIX%20GUARD/evidence_engine.py)) provides structured multi-source evidence collection, empirical quality auditing, and transparent provenance tracking:

1. **Integrated Source Repositories**:
   - **NCBI ClinVar**: Variant clinical classifications, star ratings (0-4), ACMG review status, and full submitter assertion breakdowns.
   - **ClinGen**: Gene-disease clinical validity curations (Definitive, Strong, Moderate, Limited, Disputed) and dosage sensitivity.
   - **Ensembl**: Gene identity, locus coordinates, canonical and MANE Select transcripts, biotypes, and sequence consequence mappings with strict assembly isolation (`GRCh38` vs `GRCh37`).
   - **gnomAD**: Population allele frequencies (AC, AN, AF), ancestry breakdowns, and loss-of-function intolerance constraint scores (`pLI`, `oe_lof_upper` / LOEUF).
   - **NCBI PubMed**: Peer-reviewed scientific literature citations, author lists, journals, publication years, DOIs, and direct links.
2. **Traceable Provenance**:
   - Every piece of data records its source repository, exact API endpoint, UTC retrieval timestamp, source URL, network latency, and cache status.
3. **Defense Against Biological Fallacies**:
   - Submitter disagreement in ClinVar is explicitly flagged as a lack of laboratory consensus, NOT proof of pathogenicity.
   - Population allele rarity in gnomAD is never treated as proof of pathogenicity.
   - Computational predictions are never conflated with clinical confirmation.
   - Genomic coordinates and transcripts from `GRCh37` and `GRCh38` are never combined implicitly.
4. **Resilient Local Caching**:
   - Two-tier storage (memory + formatted JSON on disk) with SHA-256 key derivation (`source:endpoint:query:assembly`), 24-hour TTL, and offline fallback mode.

---

## 8. Verification & Automated Test Suite

Helix Guard includes an **89-test** automated suite:
- **20 tests** in `test_evidence_engine.py`: Schema validation, source contracts, provenance tracking, assembly routing (GRCh38 vs GRCh37), ClinVar review stars, submitter conflicts, ClinGen validity, gnomAD GraphQL constraint, PubMed citations, timeout/connection error resilience, cache hit/miss/expiration, and unified orchestrator search.
- **23 tests** in `test_genetic_data_engine.py`: Reconciled dataset counts, Task C target-purging verification, pre-split zero preprocessing leakage, locus/gene leakage prevention, controlled benchmark equivalence, QNN class weighting, and Tab 3 UI rendering.
- **34 tests** in `test_quantum_engine.py`: Circuit topology, normalizer boundaries, expectation bounds $[-1, 1]$, training convergence, persistence, adapters, and synthetic benchmarks.
- **12 tests** in `test_streamlit_app.py`: UI rendering, persistent disclaimers, classical terminology, QNN synthetic labeling, visualizations, interactive inference, model save/load, security token isolation, and Section 4 multi-source evidence queries.

```bash
# Run all tests
.\HELIX GUARD\.venv\Scripts\python.exe -m pytest "HELIX GUARD\tests" -v
```

**Result:** `89 passed in 34.11s` (100% passing).

---

## 9. Application Launch Instructions

### Option A: From Repository Root
```powershell
& ".\HELIX GUARD\.venv\Scripts\streamlit.exe" run app.py
```

### Option B: From `HELIX GUARD` Directory
```powershell
cd "HELIX GUARD"
& ".\.venv\Scripts\streamlit.exe" run app.py
```

Open `http://localhost:8501` in your browser. Navigate across:
- **Tab 1: Classical Gene Optimization** (1D Residual CNN sequence modification)
- **Tab 2: Quantum Intelligence** (Synthetic 4-qubit QNN demonstration)
- **Tab 3: Genetic Variant Intelligence**:
  - Section 1: ClinVar Dataset Overview & Completeness
  - Section 2: Label Curation & Exclusion Strategy
  - Section 3: Supervised Model Training on Curated Features (Controlled 3-Model Benchmark + Exploratory Tabular Classical Baselines)
  - Section 4: Multi-Source Genetic Evidence Intelligence & Traceability (ClinVar, ClinGen, Ensembl, gnomAD, PubMed)
