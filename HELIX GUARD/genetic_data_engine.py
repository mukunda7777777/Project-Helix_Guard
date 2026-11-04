"""
=============================================================================
HELIX GUARD: Genetic Variant Data Intelligence Pipeline (Task 4)
=============================================================================
SCIENTIFIC & ETHICAL DISCLAIMER:
- This module implements an in-silico machine-learning data pipeline for
  exploring ClinVar genetic variant records (`clinvar_conflicting.csv`).
- NO CLINICAL DIAGNOSIS OR THERAPEUTIC RECOMMENDATION is provided or implied.
- The underlying dataset comprises genetic variants submitted with conflicting
  or variable assertions across clinical laboratories.
- Numeric `CLASS` labels indicate submission consensus vs. conflict, NOT
  absolute clinical pathogenicity.
- DO NOT interpret in-silico model scores as verified clinical truths.
- Real biological validation requires curated expert registries and wet-lab evaluation.
=============================================================================
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import GroupShuffleSplit, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

# Import modular QNN classifier from quantum engine
from quantum_engine import HybridQuantumClassifier, QuantumFeatureNormalizer

logger = logging.getLogger("HelixGuard.GeneticDataEngine")
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] [HelixGuard-GeneticData]: %(message)s",
        datefmt="%H:%M:%S",
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


# =============================================================================
# 1. DATA SUMMARY & FILTERING REPORT DATASTRUCTURES
# =============================================================================

@dataclass
class DatasetQualityReport:
    """Detailed summary of dataset attributes, missingness, and gene statistics."""
    total_records: int
    num_features: int
    column_names: List[str]
    missingness_summary: Dict[str, float]  # column -> fraction missing
    unique_variant_loci: int
    duplicate_records_detected: int
    unique_genes_count: int
    top_genes: Dict[str, int]
    consequence_distribution: Dict[str, int]
    variant_type_distribution: Dict[str, int]
    class_label_distribution: Dict[Any, int]


@dataclass
class CurationReport:
    """Logs the exact filtering decisions applied during label curation."""
    task_name: str
    description: str
    total_raw_records: int
    accepted_records: int
    excluded_records: int
    exclusion_reasons: Dict[str, int]
    class_distribution: Dict[int, int]
    positive_class_ratio: float


@dataclass
class ModelEvaluationReport:
    """Encapsulates full performance metrics across classical or quantum classifiers."""
    model_name: str
    task_name: str
    train_samples: int
    test_samples: int
    accuracy: float
    precision: float
    recall: float
    f1: float
    roc_auc: Optional[float]
    pr_auc: Optional[float]
    confusion_matrix: List[List[int]]  # [[TN, FP], [FN, TP]]
    feature_count: int
    features_used: List[str]
    additional_notes: str = ""


# =============================================================================
# 2. DATA INGESTION ENGINE
# =============================================================================

class ClinVarDataLoader:
    """
    Ingests and normalizes the ClinVar conflicting variants dataset.
    Preserves original annotations, handles missing values, and detects duplicates.
    """

    DEFAULT_CSV_PATH = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "archive", "clinvar_conflicting.csv"
    )

    def __init__(self, csv_path: Optional[str] = None):
        if csv_path is not None:
            if not os.path.exists(csv_path):
                raise FileNotFoundError(f"ClinVar dataset not found at specified path: {csv_path}")
            self.csv_path = csv_path
        else:
            self.csv_path = self.DEFAULT_CSV_PATH
            if not os.path.exists(self.csv_path):
                # Check relative paths
                alt_path = os.path.join("archive", "clinvar_conflicting.csv")
                if os.path.exists(alt_path):
                    self.csv_path = alt_path
                else:
                    raise FileNotFoundError(
                        f"ClinVar dataset not found at: {self.csv_path}. "
                        "Ensure clinvar_conflicting.csv is located in the archive folder."
                    )

    def load_raw_data(self, nrows: Optional[int] = None) -> pd.DataFrame:
        """
        Loads the CSV file into a pandas DataFrame with normalized data types.
        """
        logger.info(f"Loading ClinVar dataset from: {self.csv_path} (nrows={nrows})")
        # Specify CHROM as str to avoid mixed-type DtypeWarning
        df = pd.read_csv(
            self.csv_path,
            nrows=nrows,
            low_memory=False,
            dtype={"CHROM": str},
        )
        return df

    def generate_quality_report(self, df: pd.DataFrame) -> DatasetQualityReport:
        """
        Computes a comprehensive quality, completeness, and provenance report.
        """
        # Construct unique locus identifier: CHROM:POS:REF>ALT
        locus_series = (
            df["CHROM"].astype(str)
            + ":"
            + df["POS"].astype(str)
            + ":"
            + df["REF"].astype(str)
            + ">"
            + df["ALT"].astype(str)
        )
        unique_loci = locus_series.nunique()
        duplicates = len(df) - unique_loci

        # Missingness per column
        missingness = {col: float(df[col].isnull().mean()) for col in df.columns}

        # Gene distribution
        top_genes = {}
        unique_genes = 0
        if "SYMBOL" in df.columns:
            gene_counts = df["SYMBOL"].dropna().value_counts()
            unique_genes = len(gene_counts)
            top_genes = gene_counts.head(10).to_dict()

        # Consequence distribution
        cons_dist = {}
        if "Consequence" in df.columns:
            cons_dist = df["Consequence"].dropna().value_counts().head(8).to_dict()

        # Variant type distribution
        var_type_dist = {}
        if "CLNVC" in df.columns:
            var_type_dist = df["CLNVC"].dropna().value_counts().to_dict()

        # CLASS label distribution
        class_dist = {}
        if "CLASS" in df.columns:
            class_dist = df["CLASS"].value_counts(dropna=False).to_dict()

        return DatasetQualityReport(
            total_records=len(df),
            num_features=len(df.columns),
            column_names=list(df.columns),
            missingness_summary=missingness,
            unique_variant_loci=unique_loci,
            duplicate_records_detected=duplicates,
            unique_genes_count=unique_genes,
            top_genes=top_genes,
            consequence_distribution=cons_dist,
            variant_type_distribution=var_type_dist,
            class_label_distribution=class_dist,
        )


# =============================================================================
# 3. LABEL CURATION STRATEGY
# =============================================================================

class LabelCurationEngine:
    """
    Defensible label curation engine that extracts valid supervision targets
    while strictly excluding ambiguous, conflicting, or unannotated records.

    Supported Tasks:
    1. 'conflict_prediction': Predicts whether clinical submitters disagree (CLASS = 1 vs 0).
       This is the documented ground truth of clinvar_conflicting.csv.
    2. 'explicit_pathogenicity': Filters for records with explicit CLNSIGINCL annotations
       (Pathogenic / Likely pathogenic = 1, Benign / Likely benign = 0).
       Excludes uncertain, conflicting, or unannotated records.
    3. 'insilico_consensus': Filters for variants where PolyPhen and SIFT consensus agrees
       (probably_damaging + deleterious = 1, benign + tolerated = 0).
    """

    TASK_CONFLICT_PREDICTION = "conflict_prediction"
    TASK_EXPLICIT_PATHOGENICITY = "explicit_pathogenicity"
    TASK_INSILICO_CONSENSUS = "insilico_consensus"

    @classmethod
    def curate_labels(
        cls,
        df: pd.DataFrame,
        task: str = "conflict_prediction",
    ) -> Tuple[pd.DataFrame, pd.Series, CurationReport]:
        """
        Applies rigorous filtering and returns the filtered DataFrame, target labels,
        and an audit CurationReport.
        """
        total_raw = len(df)
        exclusion_reasons = {}

        if task == cls.TASK_CONFLICT_PREDICTION:
            # Task A: Submission Consensus vs Conflict (CLASS = 0 vs 1)
            # Ensure CLASS is present and non-null
            valid_mask = df["CLASS"].notnull() & df["CLASS"].isin([0, 1])
            excluded_count = total_raw - int(valid_mask.sum())
            if excluded_count > 0:
                exclusion_reasons["Missing or non-binary CLASS label"] = excluded_count

            filtered_df = df[valid_mask].copy()
            labels = filtered_df["CLASS"].astype(int)

            report = CurationReport(
                task_name=task,
                description=(
                    "Predicting Conflicting Submissions (CLASS 1) vs. Consistent Submissions (CLASS 0). "
                    "This directly reflects the documented target variable of clinvar_conflicting.csv."
                ),
                total_raw_records=total_raw,
                accepted_records=len(filtered_df),
                excluded_records=excluded_count,
                exclusion_reasons=exclusion_reasons,
                class_distribution=labels.value_counts().to_dict(),
                positive_class_ratio=float(labels.mean()),
            )
            return filtered_df, labels, report

        elif task == cls.TASK_EXPLICIT_PATHOGENICITY:
            # Task B: Curated explicit clinical pathogenicity from CLNSIGINCL
            if "CLNSIGINCL" not in df.columns:
                raise ValueError("Column 'CLNSIGINCL' missing from dataset.")

            sig_series = df["CLNSIGINCL"].fillna("").astype(str).str.lower()

            is_pathogenic = sig_series.str.contains("pathogenic") & (
                ~sig_series.str.contains("benign")
            ) & (~sig_series.str.contains("uncertain"))
            is_benign = sig_series.str.contains("benign") & (
                ~sig_series.str.contains("pathogenic")
            ) & (~sig_series.str.contains("uncertain"))
            is_uncertain = sig_series.str.contains("uncertain") | sig_series.str.contains(
                "conflict"
            )
            is_empty = df["CLNSIGINCL"].isnull() | (sig_series == "")

            exclusion_reasons["Unannotated CLNSIGINCL field"] = int(is_empty.sum())
            exclusion_reasons["Uncertain significance or conflicting assertion in CLNSIGINCL"] = int(is_uncertain.sum())
            exclusion_reasons["Other / Unsupported clinical categories"] = int(
                total_raw - is_pathogenic.sum() - is_benign.sum() - is_empty.sum() - is_uncertain.sum()
            )

            accepted_mask = is_pathogenic | is_benign
            filtered_df = df[accepted_mask].copy()

            # Assign 1 for pathogenic, 0 for benign
            labels = pd.Series(
                np.where(filtered_df["CLNSIGINCL"].str.lower().str.contains("pathogenic"), 1, 0),
                index=filtered_df.index,
                dtype=int,
            )

            report = CurationReport(
                task_name=task,
                description=(
                    "Explicit ClinVar Pathogenicity Curation from CLNSIGINCL. "
                    "Pathogenic/Likely Pathogenic = 1, Benign/Likely Benign = 0. "
                    "Excluded all unannotated, uncertain, or conflicting variants."
                ),
                total_raw_records=total_raw,
                accepted_records=len(filtered_df),
                excluded_records=total_raw - len(filtered_df),
                exclusion_reasons=exclusion_reasons,
                class_distribution=labels.value_counts().to_dict(),
                positive_class_ratio=float(labels.mean()) if len(labels) > 0 else 0.0,
            )
            return filtered_df, labels, report

        elif task == cls.TASK_INSILICO_CONSENSUS:
            # Task C: Functional in-silico consensus (PolyPhen + SIFT agreement)
            pp = df.get("PolyPhen", pd.Series([""] * total_raw)).fillna("").astype(str).str.lower()
            sift = df.get("SIFT", pd.Series([""] * total_raw)).fillna("").astype(str).str.lower()

            damaging_mask = (pp == "probably_damaging") & (sift == "deleterious")
            benign_mask = (pp == "benign") & (sift == "tolerated")
            uncertain_mask = (
                (pp.str.contains("possibly"))
                | (sift.str.contains("low_confidence"))
                | ((pp == "benign") & (sift == "deleterious"))
                | ((pp == "probably_damaging") & (sift == "tolerated"))
            )
            missing_mask = (pp == "") | (sift == "")

            exclusion_reasons["Missing SIFT or PolyPhen annotation"] = int(missing_mask.sum())
            exclusion_reasons["Discordant in-silico predictions (SIFT vs PolyPhen)"] = int(uncertain_mask.sum())

            accepted_mask = damaging_mask | benign_mask
            filtered_df = df[accepted_mask].copy()

            labels = pd.Series(
                np.where(damaging_mask[accepted_mask], 1, 0),
                index=filtered_df.index,
                dtype=int,
            )

            report = CurationReport(
                task_name=task,
                description=(
                    "In-Silico Functional Consensus (Agreement): Damaging (PolyPhen probably_damaging & SIFT deleterious) = 1, "
                    "Tolerated/Benign (PolyPhen benign & SIFT tolerated) = 0. "
                    "CRITICAL SCIENTIFIC SAFEGUARD: Target-defining features SIFT and PolyPhen are strictly purged from model inputs "
                    "to prevent target leakage. This models agreement among other genomic features, NOT clinical pathogenicity."
                ),
                total_raw_records=total_raw,
                accepted_records=len(filtered_df),
                excluded_records=total_raw - len(filtered_df),
                exclusion_reasons=exclusion_reasons,
                class_distribution=labels.value_counts().to_dict(),
                positive_class_ratio=float(labels.mean()) if len(labels) > 0 else 0.0,
            )
            return filtered_df, labels, report

        else:
            raise ValueError(
                f"Unsupported curation task: '{task}'. "
                f"Choose from '{cls.TASK_CONFLICT_PREDICTION}', '{cls.TASK_EXPLICIT_PATHOGENICITY}', "
                f"or '{cls.TASK_INSILICO_CONSENSUS}'."
            )


# =============================================================================
# 4. FEATURE ENGINEERING PIPELINE
# =============================================================================

class ClinVarFeaturePipeline:
    """
    Extracts, imputes, and encodes numerical and categorical genomic variant features.
    Guarantees strict separation from target variables to prevent data leakage.
    """

    NUMERICAL_COLS = [
        "AF_ESP",
        "AF_EXAC",
        "AF_TGP",
        "CADD_PHRED",
        "CADD_RAW",
        "LoFtool",
        "BLOSUM62",
    ]

    CATEGORICAL_COLS = [
        "CLNVC",        # Variant classification type
        "IMPACT",       # HIGH, MODERATE, LOW, MODIFIER
        "BIOTYPE",      # protein_coding, etc.
        "Consequence",  # missense_variant, synonymous_variant, etc.
        "SIFT",         # tolerated, deleterious
        "PolyPhen",     # benign, probably_damaging
    ]

    # Explicit list of columns excluded to prevent target or coordinate leakage
    LEAKAGE_TARGET_COLS = [
        "CLASS",
        "CLNSIGINCL",
        "CLNDISDB",
        "CLNDISDBINCL",
        "CLNDN",
        "CLNDNINCL",
        "CLNHGVS",
        "CLNVI",
    ]

    def __init__(
        self,
        include_categorical: bool = True,
        task: str = "conflict_prediction",
        exclude_cols: Optional[List[str]] = None,
    ):
        self.include_categorical = include_categorical
        self.task = str(task)
        self.exclude_cols = list(exclude_cols) if exclude_cols else []

        # PART 1 FIX: When task defines targets using SIFT/PolyPhen (Task C),
        # strictly purge SIFT and PolyPhen from input features to prevent target leakage.
        if "insilico" in self.task.lower():
            for c in ["SIFT", "PolyPhen"]:
                if c not in self.exclude_cols:
                    self.exclude_cols.append(c)

        self.preprocessor: Optional[ColumnTransformer] = None
        self.feature_names_out_: List[str] = []

    def fit(self, X_df: pd.DataFrame) -> "ClinVarFeaturePipeline":
        """Builds and fits the scikit-learn imputation and scaling preprocessor."""
        available_num = [
            c for c in self.NUMERICAL_COLS if c in X_df.columns and c not in self.exclude_cols
        ]
        available_cat = (
            [c for c in self.CATEGORICAL_COLS if c in X_df.columns and c not in self.exclude_cols]
            if self.include_categorical
            else []
        )

        num_transformer = Pipeline([
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
        ])

        transformers = [("num", num_transformer, available_num)]

        if available_cat:
            cat_transformer = Pipeline([
                ("imputer", SimpleImputer(strategy="constant", fill_value="missing")),
                ("onehot", OneHotEncoder(handle_unknown="ignore", sparse_output=False, max_categories=15)),
            ])
            transformers.append(("cat", cat_transformer, available_cat))

        self.preprocessor = ColumnTransformer(transformers=transformers, remainder="drop")
        self.preprocessor.fit(X_df)

        # Record output feature names
        num_names = [f"num__{c}" for c in available_num]
        cat_names = []
        if available_cat:
            onehot = self.preprocessor.named_transformers_["cat"].named_steps["onehot"]
            try:
                cat_names = list(onehot.get_feature_names_out(available_cat))
            except Exception:
                cat_names = [f"cat__{c}" for c in available_cat]

        self.feature_names_out_ = num_names + cat_names
        return self

    def transform(self, X_df: pd.DataFrame) -> np.ndarray:
        """Transforms raw input features into numerical array."""
        if self.preprocessor is None:
            raise RuntimeError("Pipeline must be fitted before transform.")
        return np.asarray(self.preprocessor.transform(X_df), dtype=np.float64)

    def fit_transform(self, X_df: pd.DataFrame) -> np.ndarray:
        return self.fit(X_df).transform(X_df)

    @classmethod
    def extract_compact_qnn_features(cls, df: pd.DataFrame) -> Tuple[np.ndarray, List[str]]:
        """
        Derives a compact, 4-dimensional biological numerical feature matrix
        explicitly tailored for 4-qubit quantum state encoding without data leakage.

        Features:
        1. allele_frequency_rarity: Log-transformed minimum population AF in [0, 1]
        2. cadd_conservation_score: CADD_PHRED normalized into [0, 1]
        3. lof_tolerance_score: LoFtool score normalized in [0, 1] (or 0.5 default)
        4. molecular_substitution_impact: BLOSUM62 inverted or IMPACT severity in [0, 1]
        """
        feature_names = [
            "allele_frequency_rarity",
            "cadd_conservation_score",
            "lof_tolerance_score",
            "molecular_substitution_impact",
        ]
        n_samples = len(df)
        X_compact = np.zeros((n_samples, 4), dtype=np.float64)

        # 1. Allele frequency rarity
        af_cols = [c for c in ["AF_EXAC", "AF_TGP", "AF_ESP"] if c in df.columns]
        if af_cols:
            af_matrix = df[af_cols].apply(pd.to_numeric, errors="coerce").values
            min_af = np.nanmin(np.where(np.isnan(af_matrix), 1.0, af_matrix), axis=1)
            # Clip between 1e-6 and 0.5, log-scale into [0, 1] (rare -> 1.0)
            clamped_af = np.clip(min_af, 1e-6, 0.5)
            X_compact[:, 0] = np.clip(-np.log10(clamped_af) / 6.0, 0.0, 1.0)
        else:
            X_compact[:, 0] = 0.5

        # 2. CADD Conservation score
        if "CADD_PHRED" in df.columns:
            cadd = pd.to_numeric(df["CADD_PHRED"], errors="coerce").fillna(15.0).values
            X_compact[:, 1] = np.clip(cadd / 40.0, 0.0, 1.0)
        else:
            X_compact[:, 1] = 0.5

        # 3. LoFtool (Loss of Function tolerance)
        if "LoFtool" in df.columns:
            lof = pd.to_numeric(df["LoFtool"], errors="coerce").fillna(0.5).values
            X_compact[:, 2] = np.clip(lof, 0.0, 1.0)
        else:
            X_compact[:, 2] = 0.5

        # 4. Molecular substitution / IMPACT severity
        impact_score = np.full(n_samples, 0.5, dtype=np.float64)
        if "IMPACT" in df.columns:
            impact_map = {"HIGH": 1.0, "MODERATE": 0.65, "LOW": 0.25, "MODIFIER": 0.10}
            impact_vals = df["IMPACT"].map(impact_map).fillna(0.5).values
            impact_score = impact_vals
        elif "BLOSUM62" in df.columns:
            blosum = pd.to_numeric(df["BLOSUM62"], errors="coerce").fillna(0.0).values
            # BLOSUM62: range roughly -4 to +4 -> inverted into [0, 1]
            impact_score = np.clip((4.0 - blosum) / 8.0, 0.0, 1.0)

        X_compact[:, 3] = impact_score
        return X_compact, feature_names


# =============================================================================
# 5. DATASET SPLITTING & LEAKAGE PREVENTION
# =============================================================================

class DataSplitter:
    """
    Partitions datasets into reproducible train and test sets while strictly
    preventing duplicate genomic loci from leaking across partitions.
    """

    @classmethod
    def split_curated_dataframe(
        cls,
        df: pd.DataFrame,
        y: Union[np.ndarray, pd.Series],
        test_size: float = 0.25,
        random_state: int = 42,
        group_by_gene: bool = False,
        stratify: bool = True,
    ) -> Tuple[pd.DataFrame, pd.DataFrame, np.ndarray, np.ndarray, Dict[str, Any]]:
        """
        Splits raw curated DataFrame and target labels BEFORE feature preprocessing.
        Guarantees zero locus overlap, zero gene leakage (when enabled), and
        prevents test-set statistics from leaking into preprocessing pipelines.
        """
        y_arr = np.asarray(y, dtype=int).ravel()
        n_samples = len(df)
        indices = np.arange(n_samples)

        loci = (
            df["CHROM"].astype(str)
            + ":"
            + df["POS"].astype(str)
            + ":"
            + df["REF"].astype(str)
            + ">"
            + df["ALT"].astype(str)
        ).values

        if group_by_gene and "SYMBOL" in df.columns and df["SYMBOL"].nunique() > 5:
            genes = df["SYMBOL"].fillna("UnknownGene").values
            gss = GroupShuffleSplit(n_splits=1, test_size=test_size, random_state=random_state)
            train_idx, test_idx = next(gss.split(indices, y_arr, groups=genes))
            split_method = "GroupShuffleSplit (Grouped by Gene SYMBOL)"
        else:
            strat = y_arr if stratify and len(np.unique(y_arr)) > 1 else None
            train_idx, test_idx = train_test_split(
                indices,
                test_size=test_size,
                random_state=random_state,
                stratify=strat,
            )
            split_method = "Stratified Train-Test Split"

        train_loci = set(loci[train_idx])
        test_loci = set(loci[test_idx])
        locus_overlap = train_loci.intersection(test_loci)

        audit_info = {
            "split_method": split_method,
            "train_samples": len(train_idx),
            "test_samples": len(test_idx),
            "locus_leakage_overlap_count": len(locus_overlap),
            "train_positive_ratio": float(np.mean(y_arr[train_idx])),
            "test_positive_ratio": float(np.mean(y_arr[test_idx])),
        }

        if len(locus_overlap) > 0:
            raise RuntimeError(
                f"Data leakage detected! {len(locus_overlap)} duplicate genomic loci crossed partitions."
            )

        df_train = df.iloc[train_idx].copy().reset_index(drop=True)
        df_test = df.iloc[test_idx].copy().reset_index(drop=True)
        return df_train, df_test, y_arr[train_idx], y_arr[test_idx], audit_info

    @staticmethod
    def train_test_split_secure(
        X: Union[np.ndarray, pd.DataFrame],
        y: Union[np.ndarray, pd.Series],
        df_source: pd.DataFrame,
        test_size: float = 0.25,
        random_state: int = 42,
        stratify: bool = True,
        group_by_gene: bool = False,
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, Dict[str, Any]]:
        """
        Performs leakage-safe splitting with duplicate locus verification.
        """
        X_arr = np.asarray(X, dtype=np.float64)
        y_arr = np.asarray(y, dtype=int).ravel()

        # Check unique genomic locus
        loci = (
            df_source["CHROM"].astype(str)
            + ":"
            + df_source["POS"].astype(str)
            + ":"
            + df_source["REF"].astype(str)
            + ">"
            + df_source["ALT"].astype(str)
        ).values

        if group_by_gene and "SYMBOL" in df_source.columns and df_source["SYMBOL"].nunique() > 5:
            # Gene-grouped splitting: ensures all variants of a gene remain in either train or test
            genes = df_source["SYMBOL"].fillna("UnknownGene").values
            gss = GroupShuffleSplit(n_splits=1, test_size=test_size, random_state=random_state)
            train_idx, test_idx = next(gss.split(X_arr, y_arr, groups=genes))
            split_method = "GroupShuffleSplit (Grouped by Gene SYMBOL)"
        else:
            # Stratified locus-preserving split
            strat = y_arr if stratify and len(np.unique(y_arr)) > 1 else None
            indices = np.arange(len(X_arr))
            train_idx, test_idx = train_test_split(
                indices,
                test_size=test_size,
                random_state=random_state,
                stratify=strat,
            )
            split_method = "Stratified Train-Test Split"

        # Verify zero duplicate locus overlap
        train_loci = set(loci[train_idx])
        test_loci = set(loci[test_idx])
        locus_overlap = train_loci.intersection(test_loci)

        audit_info = {
            "split_method": split_method,
            "train_samples": len(train_idx),
            "test_samples": len(test_idx),
            "locus_leakage_overlap_count": len(locus_overlap),
            "train_positive_ratio": float(np.mean(y_arr[train_idx])),
            "test_positive_ratio": float(np.mean(y_arr[test_idx])),
        }

        if len(locus_overlap) > 0:
            raise RuntimeError(
                f"Data leakage detected! {len(locus_overlap)} duplicate genomic loci crossed partitions."
            )

        return X_arr[train_idx], X_arr[test_idx], y_arr[train_idx], y_arr[test_idx], audit_info


# =============================================================================
# 6. CLASSICAL MACHINE LEARNING BASELINE
# =============================================================================

class ClassicalVariantBaseline:
    """
    Standard classical scikit-learn baselines (Logistic Regression & Random Forest)
    for genetic variant classification with class imbalance handling.
    """

    @staticmethod
    def train_and_evaluate(
        X_train: np.ndarray,
        y_train: np.ndarray,
        X_test: np.ndarray,
        y_test: np.ndarray,
        model_type: str = "random_forest",
        feature_names: Optional[List[str]] = None,
        random_state: int = 42,
    ) -> Tuple[Any, ModelEvaluationReport]:
        """
        Trains model on train split and computes performance metrics on test split.
        """
        if model_type.lower() == "logistic_regression":
            clf = LogisticRegression(
                class_weight="balanced",
                max_iter=1000,
                random_state=random_state,
            )
            name = "Classical Logistic Regression"
        elif model_type.lower() == "random_forest":
            clf = RandomForestClassifier(
                n_estimators=100,
                max_depth=12,
                class_weight="balanced",
                random_state=random_state,
                n_jobs=-1,
            )
            name = "Classical Random Forest Classifier"
        else:
            raise ValueError(f"Unsupported model_type: {model_type}")

        clf.fit(X_train, y_train)

        # Predict labels and continuous probabilities
        y_pred = clf.predict(X_test)
        has_proba = hasattr(clf, "predict_proba")
        y_proba = clf.predict_proba(X_test)[:, 1] if has_proba else None

        acc = float(accuracy_score(y_test, y_pred))
        prec = float(precision_score(y_test, y_pred, zero_division=0))
        rec = float(recall_score(y_test, y_pred, zero_division=0))
        f1 = float(f1_score(y_test, y_pred, zero_division=0))

        roc = None
        pr_auc = None
        if y_proba is not None and len(np.unique(y_test)) > 1:
            try:
                roc = float(roc_auc_score(y_test, y_proba))
                pr_auc = float(average_precision_score(y_test, y_proba))
            except Exception:
                pass

        cm = confusion_matrix(y_test, y_pred).tolist()

        report = ModelEvaluationReport(
            model_name=name,
            task_name="ClinVar Supervised Benchmark",
            train_samples=len(X_train),
            test_samples=len(X_test),
            accuracy=acc,
            precision=prec,
            recall=rec,
            f1=f1,
            roc_auc=roc,
            pr_auc=pr_auc,
            confusion_matrix=cm,
            feature_count=X_train.shape[1],
            features_used=feature_names or [f"feat_{i}" for i in range(X_train.shape[1])],
            additional_notes="Class-weighted classical baseline on curated ClinVar features.",
        )
        return clf, report


# =============================================================================
# 7. QUANTUM NEURAL NETWORK (QNN) CURATED EVALUATOR
# =============================================================================

class QuantumVariantEvaluator:
    """
    Connects curated ClinVar compact features to the existing QNN engine
    (HybridQuantumClassifier) using the exact same data partitions.
    """

    @staticmethod
    def train_and_evaluate(
        X_train_compact: np.ndarray,
        y_train: np.ndarray,
        X_test_compact: np.ndarray,
        y_test: np.ndarray,
        feature_names: Optional[List[str]] = None,
        maxiter: int = 30,
        random_state: int = 42,
        class_weight: Optional[str] = "balanced",
        threshold: float = 0.5,
    ) -> Tuple[HybridQuantumClassifier, ModelEvaluationReport]:
        """
        Trains and evaluates the 4-qubit HybridQuantumClassifier on real curated features.
        Supports class-weighted BCE loss to mitigate majority-class collapse.
        """
        if X_train_compact.shape[1] != 4:
            raise ValueError(
                f"QNN requires exactly 4 compact features, got {X_train_compact.shape[1]}."
            )

        qnn = HybridQuantumClassifier(
            num_qubits=4,
            feature_map_type="zz",
            ansatz_type="real_amplitudes",
            feature_reps=1,
            ansatz_reps=2,
            entanglement="linear",
            optimizer_name="COBYLA",
            maxiter=maxiter,
            random_state=random_state,
        )

        qnn.fit(X_train_compact, y_train, loss_type="bce", class_weight=class_weight, verbose=False)

        y_probs = qnn.predict_proba(X_test_compact)[:, 1]
        y_pred = qnn.predict(X_test_compact, threshold=threshold)

        acc = float(accuracy_score(y_test, y_pred))
        prec = float(precision_score(y_test, y_pred, zero_division=0))
        rec = float(recall_score(y_test, y_pred, zero_division=0))
        f1 = float(f1_score(y_test, y_pred, zero_division=0))

        roc = None
        pr_auc = None
        if len(np.unique(y_test)) > 1:
            try:
                roc = float(roc_auc_score(y_test, y_probs))
                pr_auc = float(average_precision_score(y_test, y_probs))
            except Exception:
                pass

        cm = confusion_matrix(y_test, y_pred).tolist()

        report = ModelEvaluationReport(
            model_name="Hybrid Quantum Classifier (4 Qubits)",
            task_name="ClinVar Real Feature Experiment",
            train_samples=len(X_train_compact),
            test_samples=len(X_test_compact),
            accuracy=acc,
            precision=prec,
            recall=rec,
            f1=f1,
            roc_auc=roc,
            pr_auc=pr_auc,
            confusion_matrix=cm,
            feature_count=4,
            features_used=feature_names or ["f0", "f1", "f2", "f3"],
            additional_notes=(
                f"Evaluated via Qiskit StatevectorEstimator simulation on 4 compact biological features "
                f"(class_weight={class_weight}, threshold={threshold:.2f}). No quantum advantage claimed."
            ),
        )
        return qnn, report


# =============================================================================
# 8. CONVENIENCE BENCHMARK ORCHESTRATOR
# =============================================================================

def run_clinvar_benchmark(
    sample_size: int = 2000,
    task: str = LabelCurationEngine.TASK_CONFLICT_PREDICTION,
    random_state: int = 42,
    group_by_gene: bool = False,
    test_size: float = 0.25,
    qnn_train_limit: int = 120,
    qnn_test_limit: int = 50,
) -> Dict[str, Any]:
    """
    Executes a complete, reproducible, and leakage-free ClinVar machine learning benchmark:
    1. Ingestion & Quality check
    2. Label curation
    3. Splitting raw records FIRST (Zero Preprocessing Leakage)
    4. Feature pipeline fitted exclusively on training records
    5. Controlled Benchmark: Logistic Regression vs Random Forest vs 4-Qubit QNN
       (Identical 4 features, identical train subset, identical test subset)
    6. Exploratory 41-Feature Benchmark on full test partition
    7. Transparent reporting with confusion matrices & class distributions
    """
    loader = ClinVarDataLoader()
    raw_df = loader.load_raw_data(nrows=sample_size)
    quality_report = loader.generate_quality_report(raw_df)

    filtered_df, labels, curation_report = LabelCurationEngine.curate_labels(raw_df, task=task)

    # 1. Split raw curated DataFrame FIRST (Zero Preprocessing Leakage)
    df_tr, df_te, y_tr, y_te, split_audit = DataSplitter.split_curated_dataframe(
        filtered_df,
        labels.values,
        test_size=test_size,
        random_state=random_state,
        group_by_gene=group_by_gene,
    )

    # 2. Fit feature pipeline exclusively on training split
    pipe = ClinVarFeaturePipeline(include_categorical=True, task=task)
    X_tr_full = pipe.fit_transform(df_tr)
    X_te_full = pipe.transform(df_te)

    # 3. Compact 4D biological features extracted independently
    X_tr_compact, q_feat_names = ClinVarFeaturePipeline.extract_compact_qnn_features(df_tr)
    X_te_compact, _ = ClinVarFeaturePipeline.extract_compact_qnn_features(df_te)

    # 4. Controlled Benchmark (Apples-to-Apples: same 4 features, same sample subsets)
    ctrl_X_tr = X_tr_compact[:qnn_train_limit]
    ctrl_y_tr = y_tr[:qnn_train_limit]
    ctrl_X_te = X_te_compact[:qnn_test_limit]
    ctrl_y_te = y_te[:qnn_test_limit]

    _, ctrl_lr_report = ClassicalVariantBaseline.train_and_evaluate(
        ctrl_X_tr,
        ctrl_y_tr,
        ctrl_X_te,
        ctrl_y_te,
        model_type="logistic_regression",
        feature_names=q_feat_names,
        random_state=random_state,
    )
    ctrl_lr_report.model_name = "Controlled Logistic Regression (4 Features)"

    _, ctrl_rf_report = ClassicalVariantBaseline.train_and_evaluate(
        ctrl_X_tr,
        ctrl_y_tr,
        ctrl_X_te,
        ctrl_y_te,
        model_type="random_forest",
        feature_names=q_feat_names,
        random_state=random_state,
    )
    ctrl_rf_report.model_name = "Controlled Random Forest (4 Features)"

    _, ctrl_qnn_report = QuantumVariantEvaluator.train_and_evaluate(
        ctrl_X_tr,
        ctrl_y_tr,
        ctrl_X_te,
        ctrl_y_te,
        feature_names=q_feat_names,
        maxiter=25,
        random_state=random_state,
        class_weight="balanced",
    )
    ctrl_qnn_report.model_name = "Controlled Hybrid QNN (4 Qubits)"

    # 5. Exploratory Classical Benchmark (41 Features, Full Test Partition)
    _, exp_lr_report = ClassicalVariantBaseline.train_and_evaluate(
        X_tr_full,
        y_tr,
        X_te_full,
        y_te,
        model_type="logistic_regression",
        feature_names=pipe.feature_names_out_,
        random_state=random_state,
    )
    exp_lr_report.model_name = "Exploratory Logistic Regression (Full Tabular)"

    _, exp_rf_report = ClassicalVariantBaseline.train_and_evaluate(
        X_tr_full,
        y_tr,
        X_te_full,
        y_te,
        model_type="random_forest",
        feature_names=pipe.feature_names_out_,
        random_state=random_state,
    )
    exp_rf_report.model_name = "Exploratory Random Forest (Full Tabular)"

    return {
        "quality_report": quality_report,
        "curation_report": curation_report,
        "split_audit": split_audit,
        "controlled_benchmark": {
            "features_used": q_feat_names,
            "train_samples": len(ctrl_y_tr),
            "test_samples": len(ctrl_y_te),
            "test_class_distribution": pd.Series(ctrl_y_te).value_counts().to_dict(),
            "logistic_regression": ctrl_lr_report,
            "random_forest": ctrl_rf_report,
            "quantum_neural_network": ctrl_qnn_report,
        },
        "exploratory_41_feature_benchmark": {
            "feature_count": X_tr_full.shape[1],
            "train_samples": len(y_tr),
            "test_samples": len(y_te),
            "test_class_distribution": pd.Series(y_te).value_counts().to_dict(),
            "logistic_regression": exp_lr_report,
            "random_forest": exp_rf_report,
        },
        # Backward-compatible top-level entries
        "logistic_regression": ctrl_lr_report,
        "random_forest": ctrl_rf_report,
        "quantum_neural_network": ctrl_qnn_report,
    }

