"""
Automated Test Suite for Helix Guard Genetic Data Engine & ClinVar Pipeline (Task 4).

Tests cover:
- CSV loading and schema validation
- Dataset quality reporting and missingness analysis
- Label curation (Conflict prediction, Explicit Pathogenicity, In-Silico Consensus)
- Exclusion of ambiguous, uncertain, and unannotated records
- Feature engineering (imputation, scaling, one-hot encoding)
- Target leakage prevention
- Compact 4D feature extraction for QNN
- Duplicate detection & genomic locus leakage prevention
- Gene-grouped vs. stratified train/test splitting
- Classical ML baselines (Logistic Regression & Random Forest)
- 4-Qubit QNN training and evaluation on real ClinVar features
- Streamlit integration for Genetic Variant Intelligence tab
"""

import os
import pytest
import numpy as np
import pandas as pd
from streamlit.testing.v1 import AppTest

# Determine paths
current_dir = os.path.dirname(os.path.abspath(__file__))
helix_guard_dir = os.path.dirname(current_dir)
app_file = os.path.join(helix_guard_dir, "app.py")

from genetic_data_engine import (
    ClinVarDataLoader,
    LabelCurationEngine,
    ClinVarFeaturePipeline,
    DataSplitter,
    ClassicalVariantBaseline,
    QuantumVariantEvaluator,
    run_clinvar_benchmark,
)


# =============================================================================
# 1. DATA INGESTION & QUALITY REPORT TESTS
# =============================================================================

class TestClinVarDataLoader:
    def test_csv_loading_sample(self):
        loader = ClinVarDataLoader()
        df = loader.load_raw_data(nrows=100)
        assert len(df) == 100
        assert "CHROM" in df.columns
        assert "POS" in df.columns
        assert "REF" in df.columns
        assert "ALT" in df.columns
        assert "CLASS" in df.columns

    def test_quality_report_metrics(self):
        loader = ClinVarDataLoader()
        df = loader.load_raw_data(nrows=200)
        report = loader.generate_quality_report(df)

        assert report.total_records == 200
        assert report.num_features == len(df.columns)
        assert report.unique_variant_loci <= 200
        assert report.duplicate_records_detected == (200 - report.unique_variant_loci)
        assert len(report.missingness_summary) == len(df.columns)
        assert report.unique_genes_count > 0

    def test_nonexistent_file_raises(self):
        with pytest.raises(FileNotFoundError):
            ClinVarDataLoader(csv_path="non_existent_file_99999.csv")

    def test_exact_dataset_counts_verification(self):
        """Verifies reconciled dataset counts directly from source CSV (Phase 1 & Part 5)."""
        loader = ClinVarDataLoader()
        df = loader.load_raw_data(nrows=None)

        assert len(df) == 65188, f"Expected 65,188 total records, got {len(df)}"
        assert "CLNSIG" not in df.columns, "CLNSIG column must not be present in CSV"
        assert "CLNSIGINCL" in df.columns

        class_counts = df["CLASS"].value_counts().to_dict()
        assert class_counts[0] == 48754, f"Expected 48,754 CLASS 0, got {class_counts[0]}"
        assert class_counts[1] == 16434, f"Expected 16,434 CLASS 1, got {class_counts[1]}"

        clnsigincl_nonnull = df["CLNSIGINCL"].dropna()
        assert len(clnsigincl_nonnull) == 167, f"Expected 167 non-null CLNSIGINCL, got {len(clnsigincl_nonnull)}"


# =============================================================================
# 2. LABEL CURATION & FILTERING TESTS
# =============================================================================

class TestLabelCuration:
    def test_curate_conflict_prediction(self):
        loader = ClinVarDataLoader()
        df = loader.load_raw_data(nrows=300)
        filtered_df, labels, report = LabelCurationEngine.curate_labels(
            df, task=LabelCurationEngine.TASK_CONFLICT_PREDICTION
        )

        assert len(filtered_df) == len(labels)
        assert set(labels.unique()).issubset({0, 1})
        assert report.accepted_records == len(filtered_df)
        assert report.total_raw_records == 300
        assert report.task_name == "conflict_prediction"

    def test_curate_explicit_pathogenicity(self):
        loader = ClinVarDataLoader()
        # Load larger sample to capture rows with CLNSIGINCL annotations
        df = loader.load_raw_data(nrows=3000)
        filtered_df, labels, report = LabelCurationEngine.curate_labels(
            df, task=LabelCurationEngine.TASK_EXPLICIT_PATHOGENICITY
        )

        assert len(filtered_df) == len(labels)
        assert report.excluded_records > 0, "Unannotated records must be excluded."
        assert "Unannotated CLNSIGINCL field" in report.exclusion_reasons
        if len(labels) > 0:
            assert set(labels.unique()).issubset({0, 1})

    def test_curate_insilico_consensus(self):
        loader = ClinVarDataLoader()
        df = loader.load_raw_data(nrows=500)
        filtered_df, labels, report = LabelCurationEngine.curate_labels(
            df, task=LabelCurationEngine.TASK_INSILICO_CONSENSUS
        )

        assert len(filtered_df) == len(labels)
        assert report.excluded_records > 0, "Missing or discordant in-silico records must be excluded."
        if len(labels) > 0:
            assert set(labels.unique()).issubset({0, 1})

    def test_unsupported_curation_task_raises(self):
        loader = ClinVarDataLoader()
        df = loader.load_raw_data(nrows=50)
        with pytest.raises(ValueError, match="Unsupported curation task"):
            LabelCurationEngine.curate_labels(df, task="unsupported_task_name")


# =============================================================================
# 3. FEATURE ENGINEERING & LEAKAGE PREVENTION TESTS
# =============================================================================

class TestFeatureEngineering:
    def test_feature_pipeline_transformation(self):
        loader = ClinVarDataLoader()
        df = loader.load_raw_data(nrows=200)
        f_df, _, _ = LabelCurationEngine.curate_labels(df, task="conflict_prediction")

        pipeline = ClinVarFeaturePipeline(include_categorical=True)
        X = pipeline.fit_transform(f_df)

        assert isinstance(X, np.ndarray)
        assert X.shape[0] == len(f_df)
        assert X.shape[1] > 0
        assert not np.any(np.isnan(X)), "Output feature matrix must not contain NaNs."

    def test_zero_target_leakage(self):
        loader = ClinVarDataLoader()
        df = loader.load_raw_data(nrows=100)
        f_df, _, _ = LabelCurationEngine.curate_labels(df, task="conflict_prediction")

        pipeline = ClinVarFeaturePipeline(include_categorical=True)
        pipeline.fit(f_df)

        for col in ClinVarFeaturePipeline.LEAKAGE_TARGET_COLS:
            assert col not in pipeline.feature_names_out_, f"Target column '{col}' leaked into features!"

    def test_task_c_target_defining_features_purged(self):
        """Verifies SIFT and PolyPhen are strictly purged from features in Task C (Part 1)."""
        loader = ClinVarDataLoader()
        df = loader.load_raw_data(nrows=300)
        curated_c, labels_c, _ = LabelCurationEngine.curate_labels(df, task="insilico_consensus")

        pipeline = ClinVarFeaturePipeline(include_categorical=True, task="insilico_consensus")
        pipeline.fit(curated_c)

        for feat in pipeline.feature_names_out_:
            assert "SIFT" not in feat, f"SIFT leaked into features: {feat}"
            assert "PolyPhen" not in feat, f"PolyPhen leaked into features: {feat}"

    def test_compact_qnn_feature_extraction(self):
        loader = ClinVarDataLoader()
        df = loader.load_raw_data(nrows=200)
        X_compact, names = ClinVarFeaturePipeline.extract_compact_qnn_features(df)

        assert X_compact.shape == (200, 4), "Compact QNN features must be exactly 4D."
        assert len(names) == 4
        assert not np.any(np.isnan(X_compact)), "Compact features must not contain NaNs."
        assert np.all(X_compact >= 0.0) and np.all(X_compact <= 1.0), "Features must be normalized in [0, 1]."


# =============================================================================
# 4. DATA SPLITTING & LOCUS LEAKAGE TESTS
# =============================================================================

class TestDataSplitting:
    def test_zero_locus_leakage(self):
        loader = ClinVarDataLoader()
        df = loader.load_raw_data(nrows=300)
        f_df, labels, _ = LabelCurationEngine.curate_labels(df, task="conflict_prediction")

        pipeline = ClinVarFeaturePipeline()
        X = pipeline.fit_transform(f_df)

        X_tr, X_te, y_tr, y_te, audit = DataSplitter.train_test_split_secure(
            X, labels.values, f_df, test_size=0.25, random_state=42
        )

        assert audit["locus_leakage_overlap_count"] == 0, "No duplicate locus must cross partitions."
        assert len(X_tr) + len(X_te) == len(f_df)
        assert len(y_tr) == len(X_tr)
        assert len(y_te) == len(X_te)

    def test_split_reproducibility(self):
        loader = ClinVarDataLoader()
        df = loader.load_raw_data(nrows=150)
        f_df, labels, _ = LabelCurationEngine.curate_labels(df, task="conflict_prediction")
        pipeline = ClinVarFeaturePipeline()
        X = pipeline.fit_transform(f_df)

        X_tr1, X_te1, y_tr1, y_te1, _ = DataSplitter.train_test_split_secure(
            X, labels.values, f_df, test_size=0.20, random_state=99
        )
        X_tr2, X_te2, y_tr2, y_te2, _ = DataSplitter.train_test_split_secure(
            X, labels.values, f_df, test_size=0.20, random_state=99
        )

        assert np.allclose(X_tr1, X_tr2)
        assert np.array_equal(y_tr1, y_tr2)

    def test_gene_grouped_splitting(self):
        loader = ClinVarDataLoader()
        df = loader.load_raw_data(nrows=400)
        f_df, labels, _ = LabelCurationEngine.curate_labels(df, task="conflict_prediction")
        pipeline = ClinVarFeaturePipeline()
        X = pipeline.fit_transform(f_df)

        X_tr, X_te, y_tr, y_te, audit = DataSplitter.train_test_split_secure(
            X, labels.values, f_df, test_size=0.25, random_state=42, group_by_gene=True
        )

        assert "GroupShuffleSplit" in audit["split_method"]
        assert len(X_tr) > 0 and len(X_te) > 0

    def test_split_curated_dataframe_zero_locus_leakage(self):
        """Verifies split_curated_dataframe ensures 0 locus overlap between df_train and df_test (Part 2)."""
        loader = ClinVarDataLoader()
        df = loader.load_raw_data(nrows=300)
        f_df, labels, _ = LabelCurationEngine.curate_labels(df, task="conflict_prediction")

        df_tr, df_te, y_tr, y_te, audit = DataSplitter.split_curated_dataframe(
            f_df, labels.values, test_size=0.25, random_state=42
        )

        assert audit["locus_leakage_overlap_count"] == 0
        assert len(df_tr) + len(df_te) == len(f_df)
        assert len(y_tr) == len(df_tr)
        assert len(y_te) == len(df_te)

    def test_preprocessing_fitted_exclusively_on_train(self):
        """Verifies test set records do not alter preprocessing parameters (Part 2 zero leakage)."""
        loader = ClinVarDataLoader()
        df = loader.load_raw_data(nrows=400)
        f_df, labels, _ = LabelCurationEngine.curate_labels(df, task="conflict_prediction")

        df_tr, df_te, _, _, _ = DataSplitter.split_curated_dataframe(f_df, labels.values, test_size=0.25, random_state=42)

        pipe = ClinVarFeaturePipeline(include_categorical=True)
        pipe.fit(df_tr)
        scaler_mean_orig = pipe.preprocessor.named_transformers_["num"].named_steps["scaler"].mean_.copy()

        # Artificially alter df_te numerical values by 1000x
        df_te_altered = df_te.copy()
        for col in pipe.NUMERICAL_COLS:
            if col in df_te_altered.columns:
                df_te_altered[col] = pd.to_numeric(df_te_altered[col], errors="coerce") * 1000.0

        # Transforming altered df_te must not change pipeline parameters
        X_te = pipe.transform(df_te_altered)
        scaler_mean_after = pipe.preprocessor.named_transformers_["num"].named_steps["scaler"].mean_

        assert np.allclose(scaler_mean_orig, scaler_mean_after), "Pipeline parameters were mutated by test data!"
        assert X_te.shape[1] == len(pipe.feature_names_out_)


# =============================================================================
# 5. CLASSICAL BASELINES & QNN BENCHMARK TESTS
# =============================================================================

class TestModelEvaluations:
    def test_logistic_regression_baseline(self):
        loader = ClinVarDataLoader()
        df = loader.load_raw_data(nrows=300)
        f_df, labels, _ = LabelCurationEngine.curate_labels(df, task="conflict_prediction")
        pipeline = ClinVarFeaturePipeline()
        X = pipeline.fit_transform(f_df)

        X_tr, X_te, y_tr, y_te, _ = DataSplitter.train_test_split_secure(
            X, labels.values, f_df, test_size=0.25, random_state=42
        )

        clf, report = ClassicalVariantBaseline.train_and_evaluate(
            X_tr, y_tr, X_te, y_te, model_type="logistic_regression"
        )

        assert 0.0 <= report.accuracy <= 1.0
        assert 0.0 <= report.f1 <= 1.0
        assert len(report.confusion_matrix) == 2
        assert "Logistic Regression" in report.model_name

    def test_random_forest_baseline(self):
        loader = ClinVarDataLoader()
        df = loader.load_raw_data(nrows=300)
        f_df, labels, _ = LabelCurationEngine.curate_labels(df, task="conflict_prediction")
        pipeline = ClinVarFeaturePipeline()
        X = pipeline.fit_transform(f_df)

        X_tr, X_te, y_tr, y_te, _ = DataSplitter.train_test_split_secure(
            X, labels.values, f_df, test_size=0.25, random_state=42
        )

        clf, report = ClassicalVariantBaseline.train_and_evaluate(
            X_tr, y_tr, X_te, y_te, model_type="random_forest"
        )

        assert 0.0 <= report.accuracy <= 1.0
        assert 0.0 <= report.f1 <= 1.0
        assert report.roc_auc is not None
        assert "Random Forest" in report.model_name

    def test_qnn_training_on_curated_clinvar_features(self):
        loader = ClinVarDataLoader()
        df = loader.load_raw_data(nrows=200)
        f_df, labels, _ = LabelCurationEngine.curate_labels(df, task="conflict_prediction")

        X_compact, names = ClinVarFeaturePipeline.extract_compact_qnn_features(f_df)
        X_tr, X_te, y_tr, y_te, _ = DataSplitter.train_test_split_secure(
            X_compact, labels.values, f_df, test_size=0.25, random_state=42
        )

        qnn, report = QuantumVariantEvaluator.train_and_evaluate(
            X_tr[:80], y_tr[:80], X_te[:30], y_te[:30], feature_names=names, maxiter=15, random_state=42
        )

        assert 0.0 <= report.accuracy <= 1.0
        assert report.feature_count == 4
        assert len(report.confusion_matrix) == 2
        assert "Quantum" in report.model_name

    def test_controlled_benchmark_identical_evaluation_samples(self):
        """Verifies controlled benchmark evaluates all 3 models on the exact same 4 features and samples (Part 3)."""
        res = run_clinvar_benchmark(sample_size=300, qnn_train_limit=40, qnn_test_limit=20, random_state=42)
        ctrl = res["controlled_benchmark"]

        assert len(ctrl["features_used"]) == 4
        assert ctrl["test_samples"] == 20
        assert ctrl["train_samples"] == 40

        lr_rep = ctrl["logistic_regression"]
        rf_rep = ctrl["random_forest"]
        qnn_rep = ctrl["quantum_neural_network"]

        assert lr_rep.test_samples == 20
        assert rf_rep.test_samples == 20
        assert qnn_rep.test_samples == 20

        assert lr_rep.feature_count == 4
        assert rf_rep.feature_count == 4
        assert qnn_rep.feature_count == 4

    def test_qnn_class_weighted_training(self):
        """Verifies QNN supports balanced class-weighted BCE loss to mitigate majority-class collapse (Part 4)."""
        loader = ClinVarDataLoader()
        df = loader.load_raw_data(nrows=150)
        f_df, labels, _ = LabelCurationEngine.curate_labels(df, task="conflict_prediction")
        X_compact, names = ClinVarFeaturePipeline.extract_compact_qnn_features(f_df)

        df_tr, df_te, y_tr, y_te, _ = DataSplitter.split_curated_dataframe(f_df, labels.values, test_size=0.25, random_state=42)
        X_tr, _ = ClinVarFeaturePipeline.extract_compact_qnn_features(df_tr)
        X_te, _ = ClinVarFeaturePipeline.extract_compact_qnn_features(df_te)

        qnn, report = QuantumVariantEvaluator.train_and_evaluate(
            X_tr[:50], y_tr[:50], X_te[:20], y_te[:20],
            feature_names=names, maxiter=15, random_state=42, class_weight="balanced"
        )

        assert 0.0 <= report.accuracy <= 1.0
        assert report.feature_count == 4
        assert "balanced" in report.additional_notes


# =============================================================================
# 6. STREAMLIT APP TAB 3 INTEGRATION TEST
# =============================================================================

class TestStreamlitTab3ClinVarIntegration:
    @pytest.fixture(autouse=True)
    def setup_app(self):
        self.at = AppTest.from_file(app_file, default_timeout=35)

    def test_tab3_presence_and_render(self):
        """Verifies Tab 3 (Genetic Variant Intelligence) renders with ClinVar metrics."""
        self.at.run()
        assert not self.at.exception

        tab_labels = [t.label for t in self.at.tabs]
        assert any("Genetic Variant Intelligence" in lbl for lbl in tab_labels), (
            f"Expected Tab 3 'Genetic Variant Intelligence', found: {tab_labels}"
        )

        # Verify dataset overview headers
        subheader_texts = [sh.value for sh in self.at.subheader]
        assert any("ClinVar" in text for text in subheader_texts)

        # Verify radio button for target strategy exists
        radio_options = [r for r in self.at.radio]
        assert len(radio_options) >= 1

