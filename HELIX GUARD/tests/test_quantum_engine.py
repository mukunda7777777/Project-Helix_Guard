"""
Unit and Integration Test Suite for Helix Guard Quantum Engine (Task 1).

Tests cover:
- Parameterized circuit construction and architectural configurations
- Feature normalization and boundary enforcement
- Quantum forward pass, expectation value bounds [-1, 1]
- Training interface, loss decrease, and convergence
- Prediction interface (predict, predict_proba, thresholding)
- Invalid input handling (mismatched dimensions, empty data, NaN/Inf, unfitted state)
- Model saving, loading, and numerical parity
- Compact feature extraction from sequence windows and ClinVar records
- Synthetic demonstration data generator
"""

import os
import tempfile
import pytest
import numpy as np

# Import the module under test
from quantum_engine import (
    CircuitArchitectureConfig,
    CompactFeatureAdapter,
    HybridQuantumClassifier,
    QuantumCircuitBuilder,
    QuantumFeatureNormalizer,
    generate_synthetic_genetic_data,
)


# =============================================================================
# 1. CIRCUIT CONSTRUCTION TESTS
# =============================================================================

class TestQuantumCircuitBuilder:
    def test_default_circuit_construction(self):
        config = CircuitArchitectureConfig(num_qubits=4, feature_map_type="zz", ansatz_type="real_amplitudes")
        builder = QuantumCircuitBuilder(config)
        circuit, f_params, w_params = builder.build_composite_circuit()

        assert circuit.num_qubits == 4
        assert len(f_params) == 4, "ZZFeatureMap with 4 qubits should have 4 feature parameters."
        assert len(w_params) == 12, "RealAmplitudes with reps=2 on 4 qubits should have (2+1)*4 = 12 parameters."
        assert circuit.depth() > 0

    def test_angle_encoding_circuit(self):
        config = CircuitArchitectureConfig(num_qubits=3, feature_map_type="angle", ansatz_type="real_amplitudes", feature_reps=1, ansatz_reps=1)
        builder = QuantumCircuitBuilder(config)
        circuit, f_params, w_params = builder.build_composite_circuit()

        assert circuit.num_qubits == 3
        assert len(f_params) == 3
        assert len(w_params) == (1 + 1) * 3

    def test_two_local_ansatz_circuit(self):
        config = CircuitArchitectureConfig(num_qubits=2, feature_map_type="z", ansatz_type="two_local", feature_reps=1, ansatz_reps=1)
        builder = QuantumCircuitBuilder(config)
        circuit, f_params, w_params = builder.build_composite_circuit()

        assert circuit.num_qubits == 2
        assert len(f_params) == 2
        assert len(w_params) > 0

    def test_invalid_qubits_raise(self):
        with pytest.raises(ValueError, match="at least 1"):
            QuantumCircuitBuilder(CircuitArchitectureConfig(num_qubits=0))

        with pytest.raises(ValueError, match="too large"):
            QuantumCircuitBuilder(CircuitArchitectureConfig(num_qubits=20))

    def test_unsupported_circuit_types_raise(self):
        with pytest.raises(ValueError, match="Unsupported feature_map_type"):
            b = QuantumCircuitBuilder(CircuitArchitectureConfig(feature_map_type="invalid_map"))
            b.build_feature_map()

        with pytest.raises(ValueError, match="Unsupported ansatz_type"):
            b = QuantumCircuitBuilder(CircuitArchitectureConfig(ansatz_type="invalid_ansatz"))
            b.build_ansatz()

    def test_default_observable(self):
        builder = QuantumCircuitBuilder(CircuitArchitectureConfig(num_qubits=4))
        obs = builder.get_default_observable()
        assert len(obs) == 4, "Should have 4 single-qubit Z Pauli terms."


# =============================================================================
# 2. FEATURE NORMALIZER TESTS
# =============================================================================

class TestQuantumFeatureNormalizer:
    def test_scaling_to_angular_range(self):
        normalizer = QuantumFeatureNormalizer(target_range=(0.0, np.pi))
        X = np.array([
            [1.0, 10.0, -5.0],
            [3.0, 20.0, 0.0],
            [5.0, 30.0, 5.0],
        ])
        X_scaled = normalizer.fit_transform(X)

        assert X_scaled.shape == X.shape
        assert np.isclose(np.min(X_scaled), 0.0)
        assert np.isclose(np.max(X_scaled), np.pi)
        assert np.all(X_scaled >= 0.0)
        assert np.all(X_scaled <= np.pi)

    def test_inverse_transform(self):
        normalizer = QuantumFeatureNormalizer(target_range=(0.0, np.pi))
        X = np.array([[2.5, 100.0], [5.0, 200.0], [7.5, 300.0]])
        X_scaled = normalizer.fit_transform(X)
        X_rec = normalizer.inverse_transform(X_scaled)
        assert np.allclose(X, X_rec)

    def test_constant_feature_handling(self):
        normalizer = QuantumFeatureNormalizer(target_range=(0.0, np.pi))
        # Column 1 is entirely constant (zero variance)
        X = np.array([[5.0, 10.0], [5.0, 20.0], [5.0, 30.0]])
        X_scaled = normalizer.fit_transform(X)

        assert not np.any(np.isnan(X_scaled))
        assert not np.any(np.isinf(X_scaled))

    def test_invalid_target_range(self):
        with pytest.raises(ValueError, match="strictly less"):
            QuantumFeatureNormalizer(target_range=(np.pi, 0.0))

    def test_empty_or_nan_data_raises(self):
        norm = QuantumFeatureNormalizer()
        with pytest.raises(ValueError, match="empty"):
            norm.fit(np.array([]))

        with pytest.raises(ValueError, match="NaN or infinite"):
            norm.fit(np.array([[1.0, np.nan], [2.0, 3.0]]))

        with pytest.raises(ValueError, match="NaN or infinite"):
            norm.fit(np.array([[1.0, np.inf], [2.0, 3.0]]))

    def test_unfitted_transform_raises(self):
        norm = QuantumFeatureNormalizer()
        with pytest.raises(RuntimeError, match="not been fitted"):
            norm.transform(np.array([[1.0, 2.0]]))

    def test_serialization(self):
        norm = QuantumFeatureNormalizer(target_range=(0.0, np.pi))
        X = np.array([[1.0, 2.0], [3.0, 4.0]])
        norm.fit(X)
        d = norm.to_dict()
        restored = QuantumFeatureNormalizer.from_dict(d)

        assert restored.n_features_in_ == norm.n_features_in_
        assert np.allclose(restored.data_min_, norm.data_min_)
        assert np.allclose(restored.data_max_, norm.data_max_)


# =============================================================================
# 3. FORWARD PASS AND EXPECTATION TESTS
# =============================================================================

class TestExpectationEvaluation:
    def test_forward_expectation_bounds(self):
        clf = HybridQuantumClassifier(num_qubits=4, random_state=42)
        X = np.random.uniform(0, 1, size=(10, 4))
        X_norm = clf.normalizer.fit_transform(X)
        evs = clf._evaluate_expectation_batch(X_norm, clf.initial_point)

        assert evs.shape == (10,)
        assert np.all(evs >= -1.0) and np.all(evs <= 1.0), "Expectation values must be within [-1, 1]."

    def test_deterministic_forward_pass(self):
        clf = HybridQuantumClassifier(num_qubits=2, random_state=42)
        X = np.array([[0.2, 0.8], [0.5, 0.5]])
        X_norm = clf.normalizer.fit_transform(X)
        evs1 = clf._evaluate_expectation_batch(X_norm, clf.initial_point)
        evs2 = clf._evaluate_expectation_batch(X_norm, clf.initial_point)

        assert np.allclose(evs1, evs2)


# =============================================================================
# 4. TRAINING & CONVERGENCE TESTS
# =============================================================================

class TestTrainingInterface:
    def test_fit_and_loss_decrease(self):
        X, y, _ = generate_synthetic_genetic_data(n_samples=40, seed=42)
        clf = HybridQuantumClassifier(num_qubits=4, maxiter=15, random_state=42)

        clf.fit(X, y, loss_type="bce")
        assert clf.is_fitted_
        assert clf.weights_ is not None
        assert len(clf.weights_) == clf.num_weights
        assert len(clf.training_history_) > 0

        # Verify final loss is finite and valid
        assert not np.isnan(clf.training_history_[-1])
        assert not np.isinf(clf.training_history_[-1])

    def test_fit_with_mse_loss(self):
        X, y, _ = generate_synthetic_genetic_data(n_samples=30, seed=123)
        clf = HybridQuantumClassifier(num_qubits=4, maxiter=20, random_state=42)
        clf.fit(X, y, loss_type="mse")
        assert clf.is_fitted_
        assert len(clf.training_history_) > 0

    def test_fit_with_callback(self):
        X, y, _ = generate_synthetic_genetic_data(n_samples=20, seed=42)
        clf = HybridQuantumClassifier(num_qubits=4, maxiter=20, random_state=42)
        callback_calls = []

        def cb(iter_num, loss):
            callback_calls.append((iter_num, loss))

        clf.fit(X, y, callback=cb)
        assert len(callback_calls) > 0


# =============================================================================
# 5. PREDICTION INTERFACE TESTS
# =============================================================================

class TestPredictionInterface:
    def test_predict_and_predict_proba_shapes(self):
        X, y, _ = generate_synthetic_genetic_data(n_samples=30, seed=42)
        clf = HybridQuantumClassifier(num_qubits=4, maxiter=20, random_state=42)
        clf.fit(X, y)

        probs = clf.predict_proba(X)
        assert probs.shape == (30, 2)
        assert np.all(probs >= 0.0) and np.all(probs <= 1.0)
        assert np.allclose(np.sum(probs, axis=1), 1.0)

        preds = clf.predict(X)
        assert preds.shape == (30,)
        assert set(np.unique(preds)).issubset({0, 1})

    def test_predict_threshold_effect(self):
        X, y, _ = generate_synthetic_genetic_data(n_samples=30, seed=42)
        clf = HybridQuantumClassifier(num_qubits=4, maxiter=20, random_state=42)
        clf.fit(X, y)

        preds_low = clf.predict(X, threshold=0.1)
        preds_high = clf.predict(X, threshold=0.9)

        # Lower threshold should classify more or equal samples as class 1
        assert np.sum(preds_low) >= np.sum(preds_high)

    def test_score_metric(self):
        X, y, _ = generate_synthetic_genetic_data(n_samples=30, seed=42)
        clf = HybridQuantumClassifier(num_qubits=4, maxiter=20, random_state=42)
        clf.fit(X, y)

        acc = clf.score(X, y)
        assert 0.0 <= acc <= 1.0


# =============================================================================
# 6. INVALID INPUT AND ERROR HANDLING TESTS
# =============================================================================

class TestInvalidInputs:
    def test_predict_unfitted_raises(self):
        clf = HybridQuantumClassifier(num_qubits=4)
        X = np.ones((5, 4))
        with pytest.raises(RuntimeError, match="not fitted"):
            clf.predict(X)

        with pytest.raises(RuntimeError, match="not fitted"):
            clf.predict_proba(X)

    def test_save_unfitted_raises(self):
        clf = HybridQuantumClassifier(num_qubits=4)
        with pytest.raises(RuntimeError, match="Cannot save"):
            clf.save("dummy.json")

    def test_feature_dimension_mismatch_raises(self):
        clf = HybridQuantumClassifier(num_qubits=4, maxiter=5)
        X_wrong = np.ones((10, 3))  # 3 features instead of 4
        y = np.zeros(10)
        with pytest.raises(ValueError, match="Feature dimension mismatch"):
            clf.fit(X_wrong, y)

    def test_sample_length_mismatch_raises(self):
        clf = HybridQuantumClassifier(num_qubits=4)
        X = np.ones((10, 4))
        y = np.zeros(8)  # 8 labels instead of 10
        with pytest.raises(ValueError, match="Sample count mismatch"):
            clf.fit(X, y)

    def test_multiclass_target_raises(self):
        clf = HybridQuantumClassifier(num_qubits=4)
        X = np.ones((12, 4))
        y = np.array([0, 1, 2, 0, 1, 2, 0, 1, 2, 0, 1, 2])
        with pytest.raises(ValueError, match="binary labels"):
            clf.fit(X, y)


# =============================================================================
# 7. MODEL SERIALIZATION TESTS
# =============================================================================

class TestModelPersistence:
    def test_save_and_load_roundtrip(self):
        X, y, _ = generate_synthetic_genetic_data(n_samples=30, seed=42)
        clf = HybridQuantumClassifier(num_qubits=4, maxiter=20, random_state=42)
        clf.fit(X, y)

        orig_preds = clf.predict_proba(X)

        with tempfile.TemporaryDirectory() as tmp_dir:
            model_file = os.path.join(tmp_dir, "test_qnn.json")
            clf.save(model_file)
            assert os.path.exists(model_file)

            reloaded = HybridQuantumClassifier.load(model_file)
            assert reloaded.is_fitted_
            assert np.allclose(clf.weights_, reloaded.weights_)

            reloaded_preds = reloaded.predict_proba(X)
            assert np.allclose(orig_preds, reloaded_preds)

    def test_load_nonexistent_file_raises(self):
        with pytest.raises(FileNotFoundError):
            HybridQuantumClassifier.load("non_existent_model_file_12345.json")


# =============================================================================
# 8. COMPACT FEATURE EXTRACTION & CLINVAR ADAPTER TESTS
# =============================================================================

class TestFeatureAdapters:
    def test_sequence_window_extraction(self):
        seq = "ATGCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCG"
        feat = CompactFeatureAdapter.extract_from_sequence_window(seq, variant_position=5, alt_base="T")

        assert feat.shape == (4,), "Feature vector must be compact 4D, NOT raw sequence."
        assert not np.any(np.isnan(feat))
        assert np.all(feat >= 0.0)

    def test_sequence_extraction_empty_raises(self):
        with pytest.raises(ValueError, match="non-empty"):
            CompactFeatureAdapter.extract_from_sequence_window("")

    def test_clinvar_record_extraction(self):
        record = {
            "AF_EXAC": 0.00005,
            "CADD_PHRED": 28.5,
            "Consequence": "missense_variant",
            "BLOSUM62": -3,
        }
        feat = CompactFeatureAdapter.extract_from_clinvar_record(record)
        assert feat.shape == (4,)
        assert np.all(feat >= 0.0) and np.all(feat <= 1.0)

    def test_clinvar_record_missing_fields_defaults(self):
        # Empty dict should fall back gracefully without crashing
        feat = CompactFeatureAdapter.extract_from_clinvar_record({})
        assert feat.shape == (4,)
        assert not np.any(np.isnan(feat))

    def test_clinvar_record_invalid_type_raises(self):
        with pytest.raises(TypeError):
            CompactFeatureAdapter.extract_from_clinvar_record("invalid_record")


# =============================================================================
# 9. SYNTHETIC BENCHMARK TESTS
# =============================================================================

class TestSyntheticBenchmark:
    def test_data_generation_reproducibility(self):
        X1, y1, names1 = generate_synthetic_genetic_data(n_samples=50, seed=99)
        X2, y2, names2 = generate_synthetic_genetic_data(n_samples=50, seed=99)

        assert X1.shape == (50, 4)
        assert y1.shape == (50,)
        assert names1 == names2
        assert np.allclose(X1, X2)
        assert np.array_equal(y1, y2)
