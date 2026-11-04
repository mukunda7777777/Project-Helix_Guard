# Helix Guard — Task 5: Independent Data Pipeline, Scientific Validity & Benchmark Audit Report

**Date of Audit**: November 3, 2026  
**Auditor**: Independent Technical & Scientific Codebase Auditor  
**Audit Scope**: ClinVar Data Ingestion, Label Curation Strategies, Feature Engineering & Preprocessing, Leakage Prevention, Splitting Protocols, Classical & QNN Baselines, Streamlit Dashboard (Tabs 1–3), Backend Security, and Test Suite.

---

## 1. Executive Summary

An exhaustive, empirical technical and scientific audit of the newly implemented **Genetic Variant Intelligence Pipeline** (`genetic_data_engine.py`, `app.py` Tab 3, `tests/test_genetic_data_engine.py`) and its interactions with the existing classical Residual 1D-CNN and 4-qubit Quantum Neural Network (`quantum_engine.py`) was conducted.

### Key Audit Findings

1. **Dataset Semantics & Ground Truth (`clinvar_conflicting.csv`)**:
   - The dataset contains **65,188 rows** and **46 columns**.
   - Verified exact class distribution for `CLASS`: **`CLASS 0` = 48,754 records (74.79%)**, **`CLASS 1` = 16,434 records (25.21%)**. *(Note: Previous documentation reported 48,800 vs 16,388, an approximation discrepancy of 46 records).*
   - `CLASS` represents whether clinical laboratories submit conflicting interpretations (`CLASS=1`) vs. consistent interpretations (`CLASS=0`). **`CLASS` is NOT clinical pathogenicity.**
   - Column `CLNSIG` does NOT exist in the CSV file. Column `CLNSIGINCL` is present in only **167 records (0.26%)**, with 65,021 null values (99.74% missing).
   - Reference assembly verification: Genomic coordinates (`CHROM`, `POS`) and RefSeq accessions (`NC_000001.10`, `NC_000002.11`, `NC_000017.10`) establish that variants are aligned to **GRCh37 (hg19)**, not GRCh38.

2. **Critical Vulnerability — Target Leakage in Task C (In-Silico Consensus)**:
   - In `LabelCurationEngine.TASK_INSILICO_CONSENSUS`, the target label $y$ is defined as $1$ if `PolyPhen == 'probably_damaging' & SIFT == 'deleterious'` and $0$ if `PolyPhen == 'benign' & SIFT == 'tolerated'`.
   - However, `ClinVarFeaturePipeline.CATEGORICAL_COLS` includes `SIFT` and `PolyPhen` as input features.
   - Consequently, models trained on Task C achieve an artificial **100.0% Accuracy, 1.000 ROC-AUC, and 1.000 F1-Score** by directly memorizing the target-defining features. This is a severe target leakage defect in Task C.

3. **Preprocessing Leakage in Benchmarking & Dashboard**:
   - In `run_clinvar_benchmark()` (`genetic_data_engine.py:796`) and in `app.py` (`app.py:695`), `pipe.fit_transform(curated_df)` is executed on the entire dataset **prior to** the train/test split.
   - Median imputation statistics, standard scaler means/variances, and one-hot category vocabularies computed on test samples leak into the training feature matrix.

4. **Split Strategy & Reported Benchmark Divergence**:
   - `DataSplitter.train_test_split_secure` implements both standard stratified splitting and gene-grouped splitting (`GroupShuffleSplit` on `SYMBOL`).
   - The reported 5,000-record benchmark in the Task 4 report and README used **standard stratified splitting (`group_by_gene=False`)**, NOT gene-grouped splitting.
   - When gene-grouped splitting is enabled, Random Forest ROC-AUC drops from **0.7725 to 0.7438**, reflecting the true difficulty of out-of-gene generalization.

5. **Methodological Asymmetry between Classical and Quantum Models**:
   - Classical models (Random Forest, Logistic Regression) are evaluated on **41 enriched tabular features** across the full test set (1,250 test samples).
   - The 4-qubit QNN is evaluated on **4 compact summary features** across a subsample of **only 50 test samples**.
   - When classical models are restricted to the exact same 4 compact features and 50 test samples, Random Forest achieves ROC-AUC **0.527**, Logistic Regression achieves **0.613**, while the 4-qubit QNN achieves **0.468** (F1: 0.095). The current comparison between 41-feature classical models and 4-feature QNN is methodologically asymmetric.

6. **Test Suite & System Verification**:
   - The complete test suite contains **62 tests** across three test modules (`test_genetic_data_engine.py`, `test_quantum_engine.py`, `test_streamlit_app.py`). All **62 tests pass** (100% passing in 27.70 seconds).

---

## 2. Verified Implementation Inventory

| Module / Component | File Location | Line Numbers | Verified Capabilities | Audit Status |
|---|---|---|---|---|
| **ClinVar Data Ingestion** | `genetic_data_engine.py` | L115–L209 | Ingests CSV, detects locus duplicates, aggregates gene & consequence distributions. | Verified (65,188 rows, 0 duplicate loci). |
| **Label Curation Engine** | `genetic_data_engine.py` | L214–L371 | Implements 3 tasks: `conflict_prediction` (A), `explicit_pathogenicity` (B), `insilico_consensus` (C). | Defect identified in Task C (Target Leakage). |
| **Feature Pipeline** | `genetic_data_engine.py` | L377–L522 | Numerical scaling, categorical one-hot, 4D compact QNN projection. | Verified, but fitted before split in benchmarks. |
| **Data Splitter** | `genetic_data_engine.py` | L528–L600 | Locus collision verification, `GroupShuffleSplit` on `SYMBOL`. | Verified (0 locus collisions, gene-grouped functional). |
| **Classical Baselines** | `genetic_data_engine.py` | L605–L683 | Logistic Regression and Random Forest with class-weighted balancing. | Verified. |
| **Quantum Evaluator** | `genetic_data_engine.py` | L689–L766 | Parameterized 4-qubit `HybridQuantumClassifier` training on 4D ClinVar features. | Verified. |
| **Benchmark Function** | `genetic_data_engine.py` | L772–L835 | End-to-end benchmark execution script. | Preprocessing leakage identified at L796. |
| **Streamlit Tab 3** | `app.py` | L585–L797 | Dataset inspection, curation audit, model training, and performance comparison. | Preprocessing leakage at L695; asymmetric sample sizing. |
| **Security Layer** | `security.py` | L1–L145 | Token masking, log sanitization, env var precedence, `.gitignore` secret exclusion. | Verified (0 credential leaks). |
| **Automated Tests** | `tests/test_genetic_data_engine.py` | L1–L300 | 17 tests covering ingestion, curation, splitting, models, and UI. | All 17 passed. |

---

## 3. Dataset Audit (`clinvar_conflicting.csv`)

### 3.1 Dimensions, Schema, and Missingness
- **Total Records**: 65,188
- **Total Columns**: 46
- **Total Missing Cells**: 898,429 out of 2,998,648 total cells (**29.96% missingness across the matrix**).
- **Columns with Extreme Missingness (>85%)**:
  - `HIGH_INF_POS`, `MOTIF_SCORE_CHANGE`, `MOTIF_NAME`, `MOTIF_POS`: 65,186 missing (99.997%)
  - `DISTANCE`: 65,080 missing (99.83%)
  - `SSR`: 65,058 missing (99.80%)
  - `CLNDNINCL`, `CLNSIGINCL`, `CLNDISDBINCL`: 65,021 missing (99.74%)
  - `INTRON`: 56,385 missing (86.50%)

### 3.2 Genomic Locus Verification & Deduplication
- Locus constructed as: `CHROM:POS:REF>ALT`.
- **Total Unique Loci**: Exactly **65,188 unique loci**.
- **Duplicate Loci**: Exactly **0**.
- **Full Row Duplicates**: Exactly **0**.

### 3.3 Reference Assembly Determination
The genomic coordinates are confirmed to be aligned to **GRCh37 (hg19)**:
- Chromosome 1 RefSeq ID in `CLNHGVS` is `NC_000001.10` (GRCh37 build; GRCh38 is `NC_000001.11`).
- Chromosome 2 RefSeq ID is `NC_000002.11` (GRCh37 build; GRCh38 is `NC_000002.12`).
- Chromosome 17 RefSeq ID is `NC_000017.10` (GRCh37 build; GRCh38 is `NC_000017.11`).
- Coordinates in `POS` cannot be directly compared against GRCh38 genomic data without lift-over conversion.

### 3.4 Gene Symbol Distribution
- Annotated gene records: **65,172 (99.98%)**
- Missing gene symbol (`SYMBOL` is NaN): **16 records (0.02%)**
- Unique genes: **2,328 genes**
- Top 5 most mutated genes in dataset:
  1. `TTN`: 2,765 variants (4.24%)
  2. `BRCA2`: 1,934 variants (2.97%)
  3. `ATM`: 1,909 variants (2.93%)
  4. `APC`: 1,228 variants (1.88%)
  5. `BRCA1`: 1,075 variants (1.65%)

### 3.5 Molecular Consequence & Variant Type Distribution
- **Variant Classification (`CLNVC`)**:
  - `single_nucleotide_variant`: 61,281 (94.01%)
  - `Deletion`: 2,509 (3.85%)
  - `Duplication`: 1,034 (1.59%)
  - `Indel`: 247 (0.38%)
  - `Insertion`: 95 (0.15%)
  - `Inversion`: 17 (0.03%)
  - `Microsatellite`: 5 (0.01%)
- **Top Molecular Consequences (`Consequence`)**:
  - `missense_variant`: 31,444 (48.24%)
  - `synonymous_variant`: 17,668 (27.10%)
  - `intron_variant`: 4,403 (6.75%)
  - `splice_region_variant&intron_variant`: 3,393 (5.21%)
  - `frameshift_variant`: 1,774 (2.72%)
  - `stop_gained`: 1,702 (2.61%)

---

## 4. Label Semantics & Curation Strategy Audit

### 4.1 Provenance and Actual Meaning of `CLASS`
- The column `CLASS` originates from the 2018 Kaggle/Arvai ClinVar Conflicting benchmark.
- In ClinVar, variants submitted by multiple laboratories may have discordant classifications (e.g. one lab classifies a variant as *Pathogenic* while another submits *VUS* or *Likely Benign*).
- `CLASS=1` indicates that clinical submissions from different submitters were **conflicting**.
- `CLASS=0` indicates that clinical submissions were **concordant** (consistent).
- **CRITICAL SCIENTIFIC DISTINCTION**: `CLASS=0` variants are NOT necessarily benign. A variant with `CLASS=0` may be concordantly *Pathogenic* or concordantly *Benign*. Therefore, predicting `CLASS` is predicting **clinical submission discordance**, not pathogenicity.

### 4.2 Exact Count Verification

| Field / Assertion | Reported in Previous Documentation | Verified Empirical Count | Discrepancy / Audit Observation |
|---|---|---|---|
| **Total Records** | 65,188 | **65,188** | Exact match. |
| **`CLASS = 0`** | 48,800 | **48,754** (74.79%) | Previous report rounded or approximated by 46 records. |
| **`CLASS = 1`** | 16,388 | **16,434** (25.21%) | Previous report rounded or approximated by 46 records. |
| **`CLNSIG` column** | Implied in discussion | **ABSENT (0 records)** | Column `CLNSIG` does not exist in the CSV. |
| **`CLNSIGINCL` non-null** | 167 | **167** (0.26%) | Exact match. |
| **Pathogenic (`CLNSIGINCL`)** | 134 | **134** (101 pure + 33 likely) | Exact match. |
| **Likely Benign / Benign** | 4 | **4** (2 pure + 2 likely) | Exact match. |
| **Uncertain / Other** | 29 | **29** (15 uncertain + 14 other) | Exact match. |

### 4.3 Curation Strategies Evaluation
1. **Task A: Conflict Prediction (`CLASS`)**:
   - Accurately captures the true data distribution (48,754 class 0 vs. 16,434 class 1).
   - Valid supervised classification problem for modeling inter-laboratory clinical conflict.
2. **Task B: Explicit ClinVar Pathogenicity Subsetting (`CLNSIGINCL`)**:
   - Isolates 134 Pathogenic vs. 4 Benign records, excluding 65,050 records (99.79% exclusion rate).
   - While biologically pure, the extreme positive class ratio (97.1% positive; 133 vs. 3 after cleaning) renders standard supervised binary classification statistically unviable.
3. **Task C: In-Silico Consensus Classification**:
   - Filters variants where SIFT and PolyPhen agree (damaging/deleterious = 1 vs. benign/tolerated = 0).
   - Retains ~2,796 records out of 5,000.
   - Sits on a critical feature leakage defect (see Section 5.1).

---

## 5. Feature Engineering & Leakage Audit

### 5.1 Critical Severity Defect: Target Leakage in Task C
In `genetic_data_engine.py`:
- `LabelCurationEngine.curate_labels(df, task="insilico_consensus")` (L327–L347) constructs the target label:
  ```python
  damaging_mask = (pp == "probably_damaging") & (sift == "deleterious")
  benign_mask = (pp == "benign") & (sift == "tolerated")
  labels = pd.Series(np.where(damaging_mask[accepted_mask], 1, 0), ...)
  ```
- Meanwhile, `ClinVarFeaturePipeline.CATEGORICAL_COLS` (L398–L399) includes:
  ```python
  CATEGORICAL_COLS = ["CLNVC", "IMPACT", "BIOTYPE", "Consequence", "SIFT", "PolyPhen"]
  ```
- **Empirical Proof of Leakage**: When evaluated, a classical Random Forest classifier achieves:
  - Accuracy: **1.000 (100.0%)**
  - ROC-AUC: **1.000**
  - F1-Score: **1.000**
- **Impact**: The model learns an identity mapping on the input features rather than learning any generalizable biological property.
- **Proposed Correction**: Whenever `task == LabelCurationEngine.TASK_INSILICO_CONSENSUS`, `SIFT` and `PolyPhen` must be dynamically removed from `CATEGORICAL_COLS`.

### 5.2 Medium Severity Defect: Preprocessing Leakage (Fit Before Split)
In `run_clinvar_benchmark()` (`genetic_data_engine.py:795–804`) and in `app.py` (`app.py:694–707`):
```python
# CURRENT CODE (LEAKAGE):
pipe = ClinVarFeaturePipeline(include_categorical=True)
X_full = pipe.fit_transform(filtered_df)  # <--- FITS ON TRAIN + TEST COMBINED

X_tr, X_te, y_tr, y_te, split_audit = DataSplitter.train_test_split_secure(
    X_full, labels.values, filtered_df, test_size=0.25, random_state=random_state
)
```
- **Empirical Measurement of Discrepancy**:
  - Imputer median on `CADD_PHRED`: Full = 23.400 vs. Train-Only = 23.300 ($\Delta = 0.100$).
  - Imputer median on `LoFtool`: Full = 0.1290 vs. Train-Only = 0.1440 ($\Delta = 0.0150$).
  - Scaler mean on `CADD_PHRED`: Full = 20.1138 vs. Train-Only = 20.1944 ($\Delta = 0.0806$).
- **Impact**: Information from test records influences the normalization and median imputation of training features.
- **Proposed Correction**: Split the raw DataFrame first, fit the pipeline on `df_train`, and transform `df_test`:
  ```python
  df_tr, df_te, y_tr, y_te, split_audit = DataSplitter.split_dataframe(curated_df, labels, ...)
  pipe = ClinVarFeaturePipeline(include_categorical=True)
  X_tr = pipe.fit_transform(df_tr)
  X_te = pipe.transform(df_te)
  ```

### 5.3 Target and Metadata Leakage Exclusion Verification
`ClinVarFeaturePipeline.LEAKAGE_TARGET_COLS` explicitly excludes:
`['CLASS', 'CLNSIGINCL', 'CLNDISDB', 'CLNDISDBINCL', 'CLNDN', 'CLNDNINCL', 'CLNHGVS', 'CLNVI']`.
- Because `ColumnTransformer(transformers=..., remainder="drop")` is used, any column not explicitly declared in `NUMERICAL_COLS` or `CATEGORICAL_COLS` is automatically dropped.
- Tested: Columns `ORIGIN`, `SSR`, `MC`, `BAM_EDIT`, `CLNVI` do not enter the feature matrix.

---

## 6. Data Splitting & Partition Integrity Audit

### 6.1 Locus Duplicate Verification
- In `DataSplitter.train_test_split_secure` (L580–L596), the set of training loci and test loci are compared:
  `locus_overlap = train_loci.intersection(test_loci)`
- Verified: `len(locus_overlap) == 0`. Exact genomic loci cannot cross partitions.

### 6.2 Gene-Grouped Splitting Verification
- When `group_by_gene=True`, `GroupShuffleSplit` groups variants by `SYMBOL`.
- Handling of missing gene symbols: L563 assigns `df_source["SYMBOL"].fillna("UnknownGene")`.
  - Because only 16 rows out of 65,188 lack a gene symbol, grouping all 16 into `"UnknownGene"` places all 16 into either train or test, preventing locus or gene leakage across partitions.
- **Gene Overlap Verification**: Verified that `set(train_genes).intersection(set(test_genes)) == set()`. Zero gene leakage occurs when gene grouping is enabled.

### 6.3 Audit of Reported 5,000-Record Benchmark Split
- **Question**: Did the reported 5,000-record benchmark use gene-grouped splitting?
- **Finding**: **NO.**
- In `run_clinvar_benchmark()` (`genetic_data_engine.py:802`), `group_by_gene` is omitted and defaults to `False`.
- In `app.py` (`app.py:691`), `gene_grouping` is an unchecked checkbox defaulting to `False`.
- **Performance Comparison on 5,000 Records (Task A)**:
  - **Stratified Split (`group_by_gene=False`)**: Random Forest Accuracy = 72.1%, ROC-AUC = **0.7725**, PR-AUC = 0.5270.
  - **Gene-Grouped Split (`group_by_gene=True`)**: Random Forest Accuracy = 69.3%, ROC-AUC = **0.7438**, PR-AUC = 0.4831.
- **Scientific Significance**: The drop in ROC-AUC from 0.7725 to 0.7438 demonstrates that classical models benefit from learning gene-level characteristics when the same genes appear in train and test sets. Gene-grouped splitting provides a more rigorous evaluation of out-of-gene generalization.

---

## 7. Model Benchmark Audit (Classical Models)

### 7.1 Metric Calculations & Class Weighting
- `accuracy_score`, `precision_score`, `recall_score`, `f1_score` (with `zero_division=0`), `roc_auc_score`, and `average_precision_score` (PR-AUC) are correctly calculated.
- Class weighting is correctly configured:
  - `LogisticRegression(class_weight="balanced")`
  - `RandomForestClassifier(class_weight="balanced", n_estimators=100, max_depth=12)`
- Decision threshold: Standard $0.5$ threshold is applied.

### 7.2 Empirical Verification on 5,000 Records (Task A)

```
====================================================================================================
Model Architecture                      Features   Train/Test Split   Accuracy   ROC-AUC    PR-AUC   F1-Score
====================================================================================================
Random Forest (All Features)                  41         3750 / 1250     72.08%     0.7725   0.5270    0.5830
Logistic Regression (All Features)            41         3750 / 1250     51.44%     0.6460   0.3641    0.5077
Random Forest (4 Compact Features)             4         3750 / 1250     65.52%     0.7065   0.4460    0.5152
Logistic Regression (4 Compact Features)       4         3750 / 1250     53.84%     0.5620   0.2962    0.3983
====================================================================================================
```

---

## 8. Quantum Neural Network (QNN) Technical Audit

### 8.1 Complete QNN Data Path Verification

```
[Raw ClinVar Record]
        │
        ▼
[extract_compact_qnn_features()]
        │  Features: [AF_rarity, CADD/40, LoFtool, Impact/BLOSUM] -> shape: (N, 4) in [0, 1]
        ▼
[QuantumFeatureNormalizer]
        │  Min-Max fitted on training features, rescaled to [0, π]
        ▼
[zz_feature_map(4 qubits, reps=1)]
        │  Hadamard gates + Rz rotations + CNOT-Rz-CNOT entanglement gates
        ▼
[real_amplitudes(4 qubits, reps=2)]
        │  12 trainable Ry parameters (θ0 ... θ11) + CNOT linear entanglement
        ▼
[StatevectorEstimator Simulation]
        │  Evaluates expectation of observable Ô = 1/4 Σ(Zi) -> output in [-1, +1]
        ▼
[P(y=1) = (⟨Ô⟩ + 1) / 2] -> Probability in [0, 1]
        ▼
[COBYLA Optimizer (maxiter=25)] -> Minimizes Binary Cross-Entropy Loss
```

- **Feature Ordering**:
  - Qubit 0: `allele_frequency_rarity`
  - Qubit 1: `cadd_conservation_score`
  - Qubit 2: `lof_tolerance_score`
  - Qubit 3: `molecular_substitution_impact`
- **Genuine Training**: Verified that `QuantumVariantEvaluator` fits the QNN directly on `X_train_compact` and `y_train` from ClinVar, not on synthetic data or an accidental fallback.
- **Reproducibility**: Parameter initialization is fixed via `random_state=42`.

### 8.2 Evaluation Sample Asymmetry Audit
In `app.py` (`app.py:750–753`) and in `run_clinvar_benchmark()` (`genetic_data_engine.py:819–823`), the QNN is trained on 120 samples and tested on **only 40 to 50 samples**, while classical models are trained on 3,750 samples and tested on **1,250 samples**.

### 8.3 Apples-to-Apples Comparison (Exact Same 4 Features & 120/50 Sample Subset)

To eliminate both feature space asymmetry and sample size asymmetry, all three models were independently trained on the exact same 120 training variants and evaluated on the exact same 50 test variants using the 4 compact features:

```
====================================================================================================
Model (Controlled 120/50 Subset)        Features   Train/Test Split   Accuracy   ROC-AUC    PR-AUC   F1-Score
====================================================================================================
Logistic Regression (Fair Baseline)            4            120 / 50     56.00%     0.6133   0.3323    0.4500
Random Forest (Fair Baseline)                  4            120 / 50     52.00%     0.5270   0.2617    0.2941
Hybrid 4-Qubit QNN                             4            120 / 50     62.00%     0.4678   0.2706    0.0952
====================================================================================================
```

- **Scientific Finding**:
  - The 4-qubit QNN achieved an Accuracy of 62.0% but an F1-Score of **0.0952** and ROC-AUC of **0.4678** (below random chance).
  - The QNN learned a near-constant predictor predicting Class 0 for almost all samples, which yielded 62% accuracy purely due to the 72% negative class majority in the test set.
  - Classical Logistic Regression on the exact same 4 features and 50 samples achieved superior discrimination (ROC-AUC **0.6133**, F1 **0.4500**).
  - **Conclusion**: There is no quantum advantage. Presenting the QNN alongside full 41-feature classical models without explaining the sample size and feature count asymmetry is misleading.

---

## 9. Scientific Terminology & Dashboard Audit

### 9.1 Tab 1: Classical Gene Optimization
- Legacy terms (*"AI-Perfected DNA Output"*, *"Optimal Edit"*, *"Pathogenicity Risk Score"*) have been completely replaced with:
  - **"Hypothetical Sequence Modification"**
  - **"Candidate Substitution"**
  - **"Initial Model Output Score (Unvalidated)"**
- Candidate substitutions are presented as in-silico scoring minimizations, with no claims of clinical validity or therapeutic gene-editing protocols.

### 9.2 Tab 2: Quantum Intelligence (Synthetic Demonstration)
- Persistent banners explicitly declare: *"Demonstration results use synthetic data and must NOT be interpreted as clinical or biological findings."*
- Class labels are strictly designated as **"Synthetic Class 1 (Pathogenic-like)"** and **"Synthetic Class 0 (Benign-like)"**.
- Outputs are designated as **"Synthetic Model Output"**.

### 9.3 Tab 3: Genetic Variant Intelligence (Real ClinVar)
- Persistent notice: *"The ground-truth target CLASS represents whether clinical assertions were conflicting (1) vs. consistent (0). Do not interpret CLASS as absolute clinical pathogenicity."*
- Tasks A, B, and C are clearly distinguished.
- Model scores are described as computational probability outputs, not clinical diagnosis probabilities.

---

## 10. Security & Credential Management Observations

- In accordance with Critical Rule 7, no IBM Quantum credentials or `.env` files were opened, read, logged, or exposed during this audit.
- In `HELIX GUARD/security.py`, `mask_secret()` successfully masks tokens (e.g. `d1ID••••••••NHp`).
- In `HELIX GUARD/.gitignore` and root `.gitignore`, patterns `*credentials*.txt`, `.env`, `*.key`, `*.token` are strictly enforced.
- Error sanitization (`sanitize_message()`) redacts secrets and paths from UI exception banners.

---

## 11. Defect Classification & Severity Matrix

```
+----------+-------------------------------------------------------------+-------------------------------+
| Severity | Issue Description                                           | Exact File & Location         |
+----------+-------------------------------------------------------------+-------------------------------+
| CRITICAL | Target Leakage in Task C (SIFT/PolyPhen present as features)| genetic_data_engine.py:398    |
| HIGH     | Preprocessing Leakage (Pipeline fitted on Train + Test)    | genetic_data_engine.py:796    |
|          |                                                             | app.py:695                    |
| HIGH     | Methodological Asymmetry (41 vs 4 feats; 1250 vs 50 samples)| genetic_data_engine.py:819    |
|          |                                                             | app.py:750                    |
| MEDIUM   | Extreme Class Imbalance in Task B (133 vs 3 samples)       | genetic_data_engine.py:272    |
| MEDIUM   | Reported Benchmark Split Divergence (Stratified vs Grouped) | README_QNN.md:148             |
| LOW      | CLASS Count Discrepancy (48,800/16,388 vs 48,754/16,434)   | README_QNN.md:128             |
| LOW      | Streamlit deprecation warnings (`use_container_width`)      | app.py:217, 431, 627, 786     |
+----------+-------------------------------------------------------------+-------------------------------+
```

---

## 12. Recommended Corrections in Priority Order

### Priority 1 (Critical): Eliminate Target Leakage in Task C
In `ClinVarFeaturePipeline.fit()`, dynamically exclude `SIFT` and `PolyPhen` when curating under `TASK_INSILICO_CONSENSUS`:
```python
# Proposed Minimal Correction in genetic_data_engine.py:
def fit(self, X_df: pd.DataFrame, exclude_cols: Optional[List[str]] = None) -> "ClinVarFeaturePipeline":
    exclude = set(exclude_cols or [])
    available_cat = [c for c in self.CATEGORICAL_COLS if c in X_df.columns and c not in exclude]
    ...
```

### Priority 2 (High): Eliminate Preprocessing Leakage (Fit Split Correctly)
In `run_clinvar_benchmark()` and `app.py`, partition the raw DataFrame first, fit the pipeline exclusively on training variants, and transform test variants:
```python
# Proposed Minimal Correction in genetic_data_engine.py & app.py:
train_df, test_df, y_tr, y_te, split_audit = DataSplitter.split_dataframe(
    curated_df, labels.values, test_size=0.25, random_state=42
)
pipe = ClinVarFeaturePipeline(include_categorical=True)
X_tr = pipe.fit_transform(train_df)
X_te = pipe.transform(test_df)
```

### Priority 3 (High): Provide Defensible Apples-to-Apples Baselines in Dashboard
In `app.py` Tab 3 and `run_clinvar_benchmark()`, include a 4-feature classical baseline evaluated on the exact same test records as the QNN to provide an honest, scientifically valid comparison:
- Classical Logistic Regression (4 Compact Features) on 50 test samples.
- Classical Random Forest (4 Compact Features) on 50 test samples.
- Hybrid 4-Qubit QNN (4 Compact Features) on 50 test samples.

### Priority 4 (Medium): Clarify Task B Viability & Sample Sizing
Add an explicit warning in Tab 3 that Task B (`CLNSIGINCL`) contains only 136 total records across the entire 65,188 dataset (133 Pathogenic, 3 Benign) and cannot be reliably modeled without specialized few-shot or anomaly detection techniques.

### Priority 5 (Low): Correct Documentation Counts & Update Deprecated Streamlit Arguments
Update `README_QNN.md` to reflect the exact counts (`48,754` Class 0, `16,434` Class 1) and note that the reference genome is **GRCh37 (hg19)**. Replace `use_container_width=True` with `width="stretch"` in `app.py` to address Streamlit 2026 deprecation notices.

---

## 13. Test Suite Verification Summary

```
============================= test session starts =============================
platform win32 -- Python 3.12.10, pytest-9.2.0, pluggy-1.7.0
rootdir: P:\projects\HELIX GUARD-20260822T181751Z-1-001
collected 62 items

HELIX GUARD/tests/test_genetic_data_engine.py (17 tests)  ... 17 PASSED [ 27%]
HELIX GUARD/tests/test_quantum_engine.py (34 tests)       ... 34 PASSED [ 82%]
HELIX GUARD/tests/test_streamlit_app.py (11 tests)        ... 11 PASSED [100%]

====================== 62 passed, 44 warnings in 27.70s =======================
```
- **Tests Passed**: 62
- **Tests Failed**: 0
- **Warnings**: 44 (42 Streamlit `use_container_width` / pandas deprecation warnings; 2 pandas index warnings).
- **All existing functionality preserved.**

