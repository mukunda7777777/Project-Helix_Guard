# app.py
"""
=============================================================================
HELIX GUARD: Genomic AI & Quantum Intelligence Research Platform
=============================================================================
Integrates:
1. Classical Residual 1D-CNN Sequence Optimizer (Task 3 Scientific Terminology)
2. Experimental Quantum Neural Network (QNN) Engine (Task 3 Synthetic Labelling)
3. Real Genetic Variant Data Intelligence Pipeline (Task 4 ClinVar ML & QNN)
4. Backend Security & Credential Management (Task 3 Secure Isolation)

SCIENTIFIC DISCLAIMER:
Helix Guard currently demonstrates experimental machine-learning and
quantum-machine-learning workflows. Its present models have not been validated
for clinical pathogenicity prediction or biological DNA correction.
=============================================================================
"""

import io
import json
import os
import sys

# Ensure UTF-8 output encoding on Windows consoles
if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")

import numpy as np
import pandas as pd
import streamlit as st

# Ensure HELIX GUARD directory is in path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# Import existing classical model engine
from model_engine import MLDrivenSequentialOptimizer

# Import modular QNN engine components
from quantum_engine import (
    CircuitArchitectureConfig,
    CompactFeatureAdapter,
    HybridQuantumClassifier,
    QuantumCircuitBuilder,
    generate_synthetic_genetic_data,
)

# Import secure backend credentials loader
from security import load_ibm_credentials, sanitize_message

# Import Task 4 Genetic Variant Data Intelligence Pipeline
from genetic_data_engine import (
    ClinVarDataLoader,
    ClinVarFeaturePipeline,
    ClassicalVariantBaseline,
    DataSplitter,
    LabelCurationEngine,
    QuantumVariantEvaluator,
)

# Import Task 7 & 8 Genetic Evidence Intelligence Engine
from evidence_engine import (
    GenomeAssembly,
    GeneticEvidenceOrchestrator,
    SourceStatus,
    EvidenceLevel,
    VariantIdentity,
    VariantTranscriptAnnotation,
    VariantPopulationFrequency,
    ComputationalEvidence,
    VariantEvidenceRecord,
    VariantNormalizer,
)

# Import Task 9-11 Epistasis, In-Silico Correction & VCF/FASTA Pipelines
from epistasis_engine import (
    EpistasisEngine,
    GenotypePhase,
    InheritanceMode,
    VariantLocus,
    CompoundHeterozygoteResult,
    EpistaticInteraction,
    MultiVariantConflictReport,
)
from correction_engine import (
    InSilicoCorrectionEngine,
    CorrectionStrategy,
    EditingModality,
    ProposedEdit,
    EditAuditRecord,
    BeneficialVariantSuggestion,
    CorrectionPipelineResult,
    PRIORITY_PANEL,
)
from vcf_pipeline import VCFPipeline
from fasta_generator import FASTAGenerator

# -----------------------------------------------------------------------------
# Page Configuration
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Helix Guard | Genomic AI & Quantum Intelligence",
    page_icon="🧬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Load IBM Quantum credentials securely (never exposes raw keys)
ibm_creds = load_ibm_credentials(base_dir=current_dir)

# -----------------------------------------------------------------------------
# Cached Classical Model Loader (Preserved with resilient path handling)
# -----------------------------------------------------------------------------
@st.cache_resource
def load_classical_engine():
    weights_path = os.path.join(current_dir, "genocorrect_cnn.pt")
    if not os.path.exists(weights_path):
        weights_path = "genocorrect_cnn.pt"
    return MLDrivenSequentialOptimizer(model_path=weights_path)

classical_engine = load_classical_engine()

# Cached ClinVar Loader
@st.cache_data
def load_clinvar_sample(n_rows: int = 5000):
    loader = ClinVarDataLoader()
    df = loader.load_raw_data(nrows=n_rows)
    report = loader.generate_quality_report(df)
    return df, report

# Cached Evidence Orchestrator Loader
@st.cache_resource
def load_evidence_orchestrator():
    cache_path = os.path.join(current_dir, ".cache", "evidence")
    return GeneticEvidenceOrchestrator(cache_dir=cache_path)

evidence_orchestrator = load_evidence_orchestrator()

# -----------------------------------------------------------------------------
# Header & Persistent Scientific Transparency Banner (Part 3)
# -----------------------------------------------------------------------------
st.title("🧬 Helix Guard: Genomic Machine Learning & Quantum Intelligence")
st.markdown(
    "Experimental Computational Research Platform combining "
    "**Residual 1D-CNN Sequence Modeling**, **Real ClinVar Variant Intelligence**, "
    "and **Parameterized Quantum Neural Networks (QNN)**."
)

# Persistent Scientific Disclaimer across the application
st.warning(
    "⚠️ **Scientific Research Notice**: Helix Guard currently demonstrates experimental "
    "machine-learning and quantum-machine-learning workflows. Its present models have not "
    "been validated for clinical pathogenicity prediction or biological DNA correction."
)

with st.expander("ℹ️ Scientific Transparency & Model Limitations (Mandatory Guidance)", expanded=False):
    st.markdown(
        "- **Model scores are not clinical probabilities**: Computational outputs represent numerical "
        "function scores from an in-silico model and must not be used for medical diagnostic or clinical decisions.\n"
        "- **Candidate substitutions are computational demonstrations**: In-silico modifications are "
        "synthetic algorithmic demonstrations, not biological gene-editing protocols or therapeutic recommendations.\n"
        "- **Real biological validation requirements**: Clinical validity requires rigorously curated datasets "
        "(e.g., benchmarked ClinVar/gnomAD panels) and independent experimental wet-lab validation."
    )

# -----------------------------------------------------------------------------
# Sidebar: Backend Security & Execution Status
# -----------------------------------------------------------------------------
with st.sidebar:
    st.header("🔐 Backend & Security Status")

    if ibm_creds.is_configured:
        st.success(f"🟢 **IBM Quantum**: Detected ({ibm_creds.source})")
        st.caption(f"**Masked Token**: `{ibm_creds.masked_token}`")
        st.caption(f"**Instance**: `{ibm_creds.masked_instance}`")
    else:
        st.info("⚪ **IBM Quantum**: Unconfigured (Local Mode)")

    st.markdown("---")
    st.markdown("**Execution Mode:**")
    st.info("💻 **Local Simulation**: Circuits execute via Qiskit `StatevectorEstimator`.")
    st.caption("Hardware execution is inactive; experimental simulation runs on local CPU.")

    st.markdown("---")
    st.markdown("**Data Provenance Guide:**")
    st.caption(
        "- **Tab 1**: Classical Residual 1D-CNN (Target DNA sequence)\n"
        "- **Tab 2**: Quantum Intelligence (Synthetic benchmark)\n"
        "- **Tab 3**: Real ClinVar Intelligence (`clinvar_conflicting.csv`)\n"
        "- **Tab 4**: Five-Gene Sequential Correction & Epistasis Pipeline"
    )

# High-level Platform Navigation Tabs
tab_classical, tab_quantum_demo, tab_clinvar, tab_correction_pipeline = st.tabs([
    "🧬 Classical Gene Optimization (Residual CNN)",
    "⚛️ Quantum Intelligence (Synthetic Demonstration)",
    "🔬 Genetic Variant Intelligence (Real ClinVar Pipeline)",
    "🛡️ Five-Gene Correction Pipeline & Epistasis (Milestones 9–11)",
])


# =============================================================================
# TAB 1: CLASSICAL RESIDUAL CNN OPTIMIZER (PRESERVED WITH TASK 3 TERMINOLOGY)
# =============================================================================
with tab_classical:
    st.subheader("📋 Target DNA Sequence")
    default_sequence = (
        "ATGCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCG"
        "GGGGGGGGGG"  # Poly-G stretch triggers higher risk score
        "CGACTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTA"
    )

    user_dna_input = st.text_area(
        "Paste 101-bp Genomic Target Window (A, C, G, T)",
        value=default_sequence,
        height=90,
        key="classical_dna_input",
    ).upper().strip()

    def seq_to_matrix(seq, length=101):
        mapping = {"A": 0, "C": 1, "G": 2, "T": 3}
        matrix = np.zeros((4, length), dtype=np.float32)
        seq = (seq + "A" * length)[:length]
        for i, char in enumerate(seq):
            if char in mapping:
                matrix[mapping[char], i] = 1.0
        return matrix

    base_matrix = seq_to_matrix(user_dna_input)

    st.divider()

    st.markdown("### ⚡ AI Automated Sequence Optimization")
    st.write(
        "Click below to run the residual CNN model across all base positions, "
        "identify candidate substitutions, and output the hypothetical sequence modification."
    )

    if st.button("🚀 Run Pathogenicity Optimization", type="primary", use_container_width=True, key="btn_run_cnn"):
        with st.spinner("Analyzing sequence with Residual CNN..."):
            init_score, top_candidates = classical_engine.auto_optimize_sequence(base_matrix)

        # Scientific Terminology Updates
        st.metric("Initial Model Output Score (Unvalidated)", f"{init_score:.4f}")

        if top_candidates:
            best = top_candidates[0]
            perfected_seq = classical_engine.generate_perfected_sequence(user_dna_input, best)

            st.success(f"Found {len(top_candidates)} candidate substitutions that reduce the model output score")

            results_df = pd.DataFrame(top_candidates)
            results_df = results_df.rename(columns={
                "position": "Base Position",
                "original_base": "Original",
                "suggested_base": "Mutated To",
                "new_score": "New Model Output Score",
                "score_drop": "Score Reduction (Δ)",
            })
            st.dataframe(results_df, use_container_width=True)

            st.divider()
            st.subheader("🔬 Hypothetical Sequence Modification")

            m1, m2, m3 = st.columns(3)
            m1.metric("Pre-Edit Score (Unvalidated)", f"{init_score:.4f}")
            m2.metric(
                "Post-Edit Score (Unvalidated)",
                f"{best['new_score']:.4f}",
                delta=f"-{best['score_drop']:.4f}",
            )
            m3.metric(
                "Candidate Substitution",
                f"Pos {best['position']}: {best['original_base']} ➔ {best['suggested_base']}",
            )

            st.markdown("**Original Target Sequence:**")
            st.code(user_dna_input, language="text")

            st.markdown(f"**Candidate Modified Sequence (Modified at Position {best['position']}):**")
            st.code(perfected_seq, language="text")

        else:
            st.info("No single-base substitution reduced the model output score further for this sequence.")


# =============================================================================
# TAB 2: QUANTUM INTELLIGENCE (SYNTHETIC DEMONSTRATION WORKFLOW)
# =============================================================================
with tab_quantum_demo:
    st.info(
        "🧪 **Demonstration Notice**: The Quantum Intelligence engine currently trains and tests "
        "on synthetic demonstration data for algorithm validation. Predictions are synthetic "
        "demonstration results and do not represent verified biological findings."
    )

    c_d1, c_d2, c_d3 = st.columns(3)
    with c_d1:
        st.info("🧪 **Synthetic Demonstration Data**: Artificially generated feature distributions for algorithmic verification.")
    with c_d2:
        st.info("⚛️ **Experimental QNN Predictions**: Variational statevector expectation-value model (no quantum advantage claimed).")
    with c_d3:
        st.info("🔬 **Curated Biological Evidence**: ClinVar benchmark data pipeline available in Tab 3.")

    st.divider()

    if "qnn_data" not in st.session_state:
        X_init, y_init, f_names = generate_synthetic_genetic_data(n_samples=80, seed=42)
        st.session_state["qnn_data"] = {
            "X": X_init,
            "y": y_init,
            "feature_names": f_names,
            "split_ratio": 0.25,
        }

    if "qnn_model" not in st.session_state:
        st.session_state["qnn_model"] = None

    if "qnn_results" not in st.session_state:
        st.session_state["qnn_results"] = None

    st.subheader("⚙️ 1. Synthetic Quantum Experiment Configuration")

    with st.expander("🛠️ Configure Hyperparameters & Quantum Circuit Architecture", expanded=True):
        col_c1, col_c2, col_c3 = st.columns(3)

        with col_c1:
            n_samples = st.slider("Synthetic Samples", min_value=40, max_value=160, value=80, step=20)
            test_split = st.slider("Test Set Split Ratio", min_value=0.15, max_value=0.40, value=0.25, step=0.05)
            seed_val = st.number_input("Random Seed", value=42, step=1)

        with col_c2:
            optimizer_choice = st.selectbox("Classical Optimizer", options=["COBYLA", "SLSQP"], index=0)
            max_iter = st.slider("Max Optimization Iterations", min_value=15, max_value=60, value=30, step=5)
            loss_choice = st.selectbox("Loss Function", options=["bce", "mse"], format_func=lambda x: "Binary Cross-Entropy (BCE)" if x == "bce" else "Mean Squared Error (MSE)")

        with col_c3:
            fmap_choice = st.selectbox("Feature Encoding Map", options=["zz", "angle", "z"], format_func=lambda x: f"{x.upper()} Feature Map")
            ansatz_choice = st.selectbox("Variational Ansatz", options=["real_amplitudes", "two_local"], format_func=lambda x: "RealAmplitudes" if x == "real_amplitudes" else "TwoLocal")
            qubits_count = 4
            st.caption(f"Qubit Register: **{qubits_count} Qubits** (compact biological feature encoding)")

        if st.button("🎲 Generate / Refresh Synthetic Dataset", use_container_width=True):
            X_new, y_new, f_names_new = generate_synthetic_genetic_data(n_samples=n_samples, seed=seed_val)
            st.session_state["qnn_data"] = {
                "X": X_new,
                "y": y_new,
                "feature_names": f_names_new,
                "split_ratio": test_split,
            }
            st.session_state["qnn_results"] = None
            st.success(f"Generated new synthetic dataset with {n_samples} samples across 4 compact biological features.")

    q_data = st.session_state["qnn_data"]
    X_curr, y_curr = q_data["X"], q_data["y"]
    split_idx = int(len(X_curr) * (1.0 - q_data["split_ratio"]))
    X_train, X_test = X_curr[:split_idx], X_curr[split_idx:]
    y_train, y_test = y_curr[:split_idx], y_curr[split_idx:]

    col_stat1, col_stat2, col_stat3, col_stat4 = st.columns(4)
    col_stat1.metric("Total Synthetic Samples", f"{len(X_curr)}")
    col_stat2.metric("Synthetic Train Set", f"{len(X_train)}")
    col_stat3.metric("Synthetic Test Set", f"{len(X_test)}")
    col_stat4.metric("Synthetic Class 1 Balance", f"{(np.mean(y_curr) * 100):.1f}%")

    with st.expander("🔍 View Synthetic Feature Inputs (First 8 Samples)"):
        df_preview = pd.DataFrame(X_curr[:8], columns=q_data["feature_names"])
        df_preview["synthetic_label"] = [
            "Synthetic Class 1 (Pathogenic-like)" if y == 1 else "Synthetic Class 0 (Benign-like)"
            for y in y_curr[:8]
        ]
        st.dataframe(df_preview, use_container_width=True)

    st.divider()

    st.subheader("⚡ 2. Quantum Neural Network Training (Synthetic Simulation)")

    col_train_btn, col_train_info = st.columns([1, 2])
    with col_train_btn:
        train_clicked = st.button("🚀 Train Quantum Classifier", type="primary", use_container_width=True)
    with col_train_info:
        if st.session_state["qnn_model"] is not None and st.session_state["qnn_model"].is_fitted_:
            st.success("✅ QNN Model is trained and cached in session memory.")
        else:
            st.info("ℹ️ Click 'Train Quantum Classifier' to simulate the circuit on the synthetic dataset.")

    if train_clicked:
        with st.spinner("Simulating parameterized circuit on synthetic dataset via StatevectorEstimator..."):
            clf = HybridQuantumClassifier(
                num_qubits=qubits_count,
                feature_map_type=fmap_choice,
                ansatz_type=ansatz_choice,
                feature_reps=1,
                ansatz_reps=2,
                entanglement="linear",
                optimizer_name=optimizer_choice,
                maxiter=max_iter,
                random_state=seed_val,
            )

            clf.fit(X_train, y_train, loss_type=loss_choice, verbose=False)

            train_acc = clf.score(X_train, y_train)
            test_acc = clf.score(X_test, y_test)
            test_probs = clf.predict_proba(X_test)
            test_preds = clf.predict(X_test)

            st.session_state["qnn_model"] = clf
            st.session_state["qnn_results"] = {
                "train_acc": train_acc,
                "test_acc": test_acc,
                "test_probs": test_probs,
                "test_preds": test_preds,
                "X_test": X_test,
                "y_test": y_test,
                "loss_history": clf.training_history_,
                "summary": clf.summary(),
            }

        st.success(
            f"Training completed! Synthetic Test Accuracy: {test_acc * 100:.2f}% | "
            f"Final Loss: {clf.training_history_[-1]:.4f}"
        )

    res = st.session_state["qnn_results"]
    if res is not None:
        st.divider()
        st.subheader("📊 3. Quantum Experiment Visualizations (Synthetic Demonstration)")

        m_c1, m_c2, m_c3, m_c4 = st.columns(4)
        m_c1.metric("Final Synthetic Loss", f"{res['loss_history'][-1]:.4f}")
        m_c2.metric("Synthetic Train Accuracy", f"{res['train_acc'] * 100:.1f}%")
        m_c3.metric("Synthetic Test Accuracy", f"{res['test_acc'] * 100:.1f}%")
        m_c4.metric("Trainable Parameters", f"{res['summary']['ansatz_trainable_parameters']}")

        viz_col1, viz_col2 = st.columns(2)

        with viz_col1:
            st.markdown("##### 📉 Training Loss Convergence (Synthetic Iterations)")
            loss_df = pd.DataFrame({
                "Iteration": list(range(1, len(res["loss_history"]) + 1)),
                "Loss": res["loss_history"],
            }).set_index("Iteration")
            st.line_chart(loss_df, use_container_width=True)

        with viz_col2:
            st.markdown("##### 🎯 Synthetic Model Output Distribution (Test Samples)")
            prob_df = pd.DataFrame({
                "Sample Index": list(range(1, len(res["test_probs"]) + 1)),
                "P(Synthetic Class 0)": res["test_probs"][:, 0],
                "P(Synthetic Class 1)": res["test_probs"][:, 1],
            }).set_index("Sample Index")
            st.bar_chart(prob_df, use_container_width=True)

        st.markdown("##### 🔬 Actual vs. Predicted Synthetic Classification (Test Partition)")
        y_t = res["y_test"]
        y_p = res["test_preds"]
        probs_p = res["test_probs"][:, 1]

        test_analysis_df = pd.DataFrame(res["X_test"], columns=q_data["feature_names"])
        test_analysis_df["True Synthetic Class"] = [
            "Synthetic Class 1 (Pathogenic-like)" if yt == 1 else "Synthetic Class 0 (Benign-like)"
            for yt in y_t
        ]
        test_analysis_df["Predicted Synthetic Class"] = [
            "Synthetic Class 1 (Pathogenic-like)" if yp == 1 else "Synthetic Class 0 (Benign-like)"
            for yp in y_p
        ]
        test_analysis_df["Synthetic Model Output"] = [f"{p:.3f}" for p in probs_p]
        test_analysis_df["Synthetic Match"] = [
            "✅ Correct" if yt == yp else "❌ Discrepant" for yt, yp in zip(y_t, y_p)
        ]

        st.dataframe(test_analysis_df, use_container_width=True)

        # Section 4: Quantum Circuit Topology & Information
        st.divider()
        st.subheader("⚛️ 4. Quantum Circuit Topology & Architecture")

        circ_col1, circ_col2 = st.columns([1, 2])

        with circ_col1:
            summ = res["summary"]
            st.markdown("**Circuit Specifications:**")
            st.write(f"- **Qubits**: {summ['num_qubits']}")
            st.write(f"- **Circuit Depth**: {summ['circuit_depth']}")
            st.write(f"- **Total Operations**: {summ['num_circuit_operations']}")
            st.write(f"- **Feature Encoding Map**: {summ['feature_map_parameters']} parameters")
            st.write(f"- **Variational Ansatz**: {summ['ansatz_trainable_parameters']} trainable weights")
            st.write(r"- **Measurement Observable**: $\hat{O} = \frac{1}{4} \sum_{i=0}^3 Z_i$")
            st.caption("Expectation values are evaluated via Qiskit's `StatevectorEstimator` simulation.")

        with circ_col2:
            st.markdown("**Circuit Schematic (Qiskit Diagram):**")
            current_clf = st.session_state["qnn_model"]
            if current_clf is not None:
                circuit_ascii = current_clf.circuit.draw(output="text")
                st.code(str(circuit_ascii), language="text")

    # Section 5: Interactive Custom Variant Risk Scoring (PART 2 Terminology)
    st.divider()
    st.subheader("🔬 5. Interactive Synthetic Inference Demonstration")
    st.write(
        "Evaluate the trained quantum model on custom numerical inputs, "
        "or derive compact features from the target DNA sequence for algorithmic demonstration."
    )

    col_inf1, col_inf2 = st.columns(2)

    with col_inf1:
        st.markdown("**Feature Inputs for Single Variant:**")
        af_input = st.slider("Allele Frequency Metric", min_value=0.0001, max_value=0.50, value=0.005, step=0.005, format="%.4f")
        cons_input = st.slider("Conservation / Tolerance Score", min_value=0.0, max_value=1.0, value=0.85, step=0.05)
        gc_input = st.slider("Flanking GC Content", min_value=0.0, max_value=1.0, value=0.55, step=0.05)
        impact_input = st.slider("Molecular Substitution Impact", min_value=0.0, max_value=1.0, value=0.75, step=0.05)

        use_seq_features = st.checkbox("Derive features from Target DNA Sequence in Tab 1")
        if use_seq_features:
            seq_feats = CompactFeatureAdapter.extract_from_sequence_window(user_dna_input)
            st.info(f"Extracted from 101-bp window: CpG Density={seq_feats[0]:.2f}, Entropy={seq_feats[1]:.2f}, GC={seq_feats[2]:.2f}, Impact={seq_feats[3]:.2f}")

    with col_inf2:
        st.markdown("**Synthetic Model Prediction:**")
        if st.session_state["qnn_model"] is None:
            st.warning("Please train or load a QNN model above before running custom inference.")
        else:
            if st.button("🔮 Score Variant with QNN", use_container_width=True):
                if use_seq_features:
                    query_vec = CompactFeatureAdapter.extract_from_sequence_window(user_dna_input).reshape(1, -1)
                else:
                    query_vec = np.array([[af_input, cons_input, gc_input, impact_input]], dtype=np.float64)

                clf = st.session_state["qnn_model"]
                p_res = clf.predict_proba(query_vec)[0]
                label_res = clf.predict(query_vec)[0]

                # PART 2: "Pathogenic Risk" -> "Synthetic Model Output"
                st.metric("Synthetic Model Output (Probability)", f"{p_res[1]:.4f}")
                st.metric(
                    "Predicted Synthetic Label",
                    "Synthetic Class 1 (Pathogenic-like)" if label_res == 1 else "Synthetic Class 0 (Benign-like)",
                )
                st.caption(f"Complementary P(Synthetic Class 0): {p_res[0]:.4f}")

    # Section 6: Model Persistence (Save & Load)
    st.divider()
    st.subheader("💾 6. Model Persistence (Save & Load)")

    col_s1, col_s2 = st.columns(2)

    with col_s1:
        st.markdown("**Save Trained Model:**")
        save_filename = st.text_input("Destination Filename", value="qnn_helix_guard_model.json")
        if st.button("💾 Save Model to Disk", use_container_width=True):
            if st.session_state["qnn_model"] is None:
                st.error("No model is currently trained in memory. Train a model first.")
            else:
                try:
                    save_path = os.path.join(current_dir, save_filename)
                    st.session_state["qnn_model"].save(save_path)
                    st.success(f"Model saved successfully to: `{save_path}`")
                except Exception as e:
                    st.error(f"Failed to save model: {sanitize_message(str(e))}")

        if st.session_state["qnn_model"] is not None and st.session_state["qnn_model"].is_fitted_:
            model_dict = {
                "version": "1.0.0",
                "weights": st.session_state["qnn_model"].weights_.tolist(),
                "history": st.session_state["qnn_model"].training_history_,
                "summary": st.session_state["qnn_model"].summary(),
            }
            json_str = json.dumps(model_dict, indent=2)
            st.download_button(
                label="📥 Download Model JSON",
                data=json_str,
                file_name=save_filename,
                mime="application/json",
                use_container_width=True,
            )

    with col_s2:
        st.markdown("**Load Saved Model:**")
        uploaded_file = st.file_uploader("Upload Saved Model JSON", type=["json"])
        load_path_input = st.text_input("Or Specify Server File Path", value=os.path.join(current_dir, "demo_qnn_model.json"))

        if st.button("📂 Load Model", use_container_width=True):
            try:
                target_to_load = None
                if uploaded_file is not None:
                    temp_load_path = os.path.join(current_dir, "temp_uploaded_qnn.json")
                    with open(temp_load_path, "wb") as f:
                        f.write(uploaded_file.getbuffer())
                    target_to_load = temp_load_path
                elif os.path.exists(load_path_input):
                    target_to_load = load_path_input
                else:
                    st.error("Specified model path does not exist.")

                if target_to_load:
                    reloaded_clf = HybridQuantumClassifier.load(target_to_load)
                    st.session_state["qnn_model"] = reloaded_clf

                    test_acc = reloaded_clf.score(X_test, y_test)
                    test_probs = reloaded_clf.predict_proba(X_test)
                    test_preds = reloaded_clf.predict(X_test)

                    st.session_state["qnn_results"] = {
                        "train_acc": reloaded_clf.score(X_train, y_train),
                        "test_acc": test_acc,
                        "test_probs": test_probs,
                        "test_preds": test_preds,
                        "X_test": X_test,
                        "y_test": y_test,
                        "loss_history": reloaded_clf.training_history_ if reloaded_clf.training_history_ else [0.0],
                        "summary": reloaded_clf.summary(),
                    }
                    st.success(
                        f"Successfully loaded QNN model! Synthetic Test Accuracy: {test_acc * 100:.2f}%"
                    )

            except Exception as e:
                st.error(f"Error loading model: {sanitize_message(str(e))}")


# =============================================================================
# TAB 3: GENETIC VARIANT INTELLIGENCE (TASK 4 REAL CLINVAR PIPELINE)
# =============================================================================
with tab_clinvar:
    st.subheader("🔬 Real ClinVar Genetic Variant Intelligence Pipeline")
    st.markdown(
        "Supervised machine learning and exploratory quantum neural modeling "
        "trained on actual ClinVar variant records (`clinvar_conflicting.csv`)."
    )

    # Transparency Notice on the nature of clinvar_conflicting.csv
    st.info(
        "📖 **Dataset Provenance & Interpretation Notice**: The source file `clinvar_conflicting.csv` "
        "contains 65,188 variants collected to study clinical interpretation conflict across laboratories. "
        "The ground-truth target `CLASS` represents whether clinical assertions were conflicting (1) vs. consistent (0). "
        "Do not interpret `CLASS` as absolute clinical pathogenicity."
    )

    # 1. Dataset Loading & Inspection Section
    st.markdown("### 📊 1. ClinVar Dataset Overview & Completeness")

    col_load1, col_load2 = st.columns([1, 2])
    with col_load1:
        n_rows_inspect = st.select_slider(
            "Records to Load for Analysis",
            options=[1000, 5000, 10000, 20000, 65188],
            value=5000,
            help="Higher record counts provide complete distributions but take slightly longer to process.",
        )

    clinvar_raw_df, quality_report = load_clinvar_sample(n_rows_inspect)

    col_d1, col_d2, col_d3, col_d4 = st.columns(4)
    col_d1.metric("Loaded Records", f"{quality_report.total_records:,}")
    col_d2.metric("Total Unique Loci", f"{quality_report.unique_variant_loci:,}")
    col_d3.metric("Duplicate Loci", f"{quality_report.duplicate_records_detected}")
    col_d4.metric("Annotated Genes", f"{quality_report.unique_genes_count:,}")

    # Top Genes & Consequence Breakdown Charts
    col_ch1, col_ch2 = st.columns(2)
    with col_ch1:
        st.markdown("##### 🧬 Top Genes by Variant Count")
        top_genes_df = pd.DataFrame(
            list(quality_report.top_genes.items()), columns=["Gene Symbol", "Variant Count"]
        ).set_index("Gene Symbol")
        st.bar_chart(top_genes_df, use_container_width=True)

    with col_ch2:
        st.markdown("##### 🔬 Molecular Consequences")
        cons_df = pd.DataFrame(
            list(quality_report.consequence_distribution.items()),
            columns=["Consequence", "Count"],
        ).set_index("Consequence")
        st.bar_chart(cons_df, use_container_width=True)

    # 2. Label Curation & Exclusion Auditing
    st.divider()
    st.markdown("### 🎯 2. Label Curation & Exclusion Strategy")

    curation_task = st.radio(
        "Select Supervised Target Strategy",
        options=[
            LabelCurationEngine.TASK_CONFLICT_PREDICTION,
            LabelCurationEngine.TASK_EXPLICIT_PATHOGENICITY,
            LabelCurationEngine.TASK_INSILICO_CONSENSUS,
        ],
        format_func=lambda x: {
            "conflict_prediction": "Task A: Clinical Conflict Prediction (CLASS 1=Conflicting vs 0=Consistent) [Documented Truth]",
            "explicit_pathogenicity": "Task B: Explicit ClinVar Pathogenicity Subsetting (CLNSIGINCL: Pathogenic=1, Benign=0) [Extreme 97.8% Positive Imbalance]",
            "insilico_consensus": "Task C: In-Silico Functional Consensus (SIFT + PolyPhen Agreement; Target-Defining Features Purged from Inputs)",
        }[x],
        index=0,
    )

    curated_df, target_labels, curation_report = LabelCurationEngine.curate_labels(
        clinvar_raw_df, task=curation_task
    )

    col_cur1, col_cur2, col_cur3 = st.columns(3)
    col_cur1.metric("Accepted Records", f"{curation_report.accepted_records:,}")
    col_cur2.metric("Excluded Records", f"{curation_report.excluded_records:,}")
    col_cur3.metric("Positive Class Ratio", f"{curation_report.positive_class_ratio * 100:.1f}%")

    with st.expander("📋 View Curation Audit & Exclusion Reasons", expanded=False):
        st.write(f"**Task Description**: {curation_report.description}")
        st.write("**Exclusion Breakdown:**")
        for reason, count in curation_report.exclusion_reasons.items():
            st.write(f"- {reason}: **{count:,} records**")

    # 3. Model Training & Evaluation (Zero Preprocessing Leakage)
    st.divider()
    st.subheader("⚡ 3. Supervised Model Training on Curated Features")

    st.info(
        "🔒 **Zero Preprocessing Leakage Protocol**: Raw curated variants are split FIRST into Train and Test sets. "
        "All imputers, scalers, and encoders are fitted exclusively on training data (`df_train`). "
        "Test variants never influence preprocessing statistics."
    )

    if curation_report.accepted_records < 20:
        st.warning(
            f"Insufficient accepted records ({curation_report.accepted_records}) in this sample for robust ML training. "
            "Please select a larger sample size or choose Task A (Conflict Prediction)."
        )
    else:
        col_m_ctrl1, col_m_ctrl2 = st.columns(2)
        with col_m_ctrl1:
            test_ratio_curated = st.slider("Test Partition Ratio", 0.15, 0.35, 0.25, 0.05, key="test_ratio_curated")
        with col_m_ctrl2:
            gene_grouping = st.checkbox("Group by Gene Symbol (Prevents Cross-Partition Gene Leakage)", value=False)

        # 1. Zero Preprocessing Leakage Splitting
        df_tr, df_te, y_tr, y_te, split_audit = DataSplitter.split_curated_dataframe(
            curated_df,
            target_labels.values,
            test_size=test_ratio_curated,
            random_state=42,
            group_by_gene=gene_grouping,
        )

        # 2. Fit feature pipeline exclusively on training records
        pipe_clinvar = ClinVarFeaturePipeline(include_categorical=True, task=curation_task)
        X_tr_tab = pipe_clinvar.fit_transform(df_tr)
        X_te_tab = pipe_clinvar.transform(df_te)

        # 3. Extract compact 4D features independently
        X_tr_q, q_feature_names = ClinVarFeaturePipeline.extract_compact_qnn_features(df_tr)
        X_te_q, _ = ClinVarFeaturePipeline.extract_compact_qnn_features(df_te)

        st.caption(
            f"Partitioning: **{len(y_tr):,} train samples**, **{len(y_te):,} test samples**. "
            f"Split Strategy: `{split_audit['split_method']}` (Genomic locus leakage overlap: 0)."
        )

        # ---------------------------------------------------------------------
        # Controlled Benchmark Section (Apples-to-Apples)
        # ---------------------------------------------------------------------
        st.markdown("#### ⚖️ Controlled Classical ML vs. QNN Benchmark (4 Compact Features)")
        st.caption(
            "Controlled comparison: All 3 models use the **exact same 4 features**, "
            "the **exact same training subset (120 variants)**, and the **exact same test subset (50 variants)**."
        )

        if "controlled_benchmark_results" not in st.session_state:
            st.session_state["controlled_benchmark_results"] = None

        if st.button("⚖️ Run Controlled 3-Model Benchmark (4 Features)", type="primary", use_container_width=True):
            with st.spinner("Executing controlled benchmark on identical 120 train / 50 test samples..."):
                ctrl_tr_X = X_tr_q[:120]
                ctrl_tr_y = y_tr[:120]
                ctrl_te_X = X_te_q[:50]
                ctrl_te_y = y_te[:50]

                _, rep_ctrl_lr = ClassicalVariantBaseline.train_and_evaluate(
                    ctrl_tr_X, ctrl_tr_y, ctrl_te_X, ctrl_te_y,
                    model_type="logistic_regression", feature_names=q_feature_names, random_state=42,
                )
                rep_ctrl_lr.model_name = "Controlled Logistic Regression (4 Feats)"

                _, rep_ctrl_rf = ClassicalVariantBaseline.train_and_evaluate(
                    ctrl_tr_X, ctrl_tr_y, ctrl_te_X, ctrl_te_y,
                    model_type="random_forest", feature_names=q_feature_names, random_state=42,
                )
                rep_ctrl_rf.model_name = "Controlled Random Forest (4 Feats)"

                _, rep_ctrl_qnn = QuantumVariantEvaluator.train_and_evaluate(
                    ctrl_tr_X, ctrl_tr_y, ctrl_te_X, ctrl_te_y,
                    feature_names=q_feature_names, maxiter=25, random_state=42, class_weight="balanced",
                )
                rep_ctrl_qnn.model_name = "Controlled Hybrid QNN (4 Qubits)"

                st.session_state["controlled_benchmark_results"] = {
                    "models": [rep_ctrl_lr, rep_ctrl_rf, rep_ctrl_qnn],
                    "test_class_dist": pd.Series(ctrl_te_y).value_counts().to_dict(),
                    "test_count": len(ctrl_te_y),
                }

        ctrl_res = st.session_state.get("controlled_benchmark_results")
        if ctrl_res:
            ctrl_rows = []
            for rep in ctrl_res["models"]:
                ctrl_rows.append({
                    "Model": rep.model_name,
                    "Features": f"{rep.feature_count} features",
                    "Samples (Train/Test)": f"{rep.train_samples} / {rep.test_samples}",
                    "Accuracy": f"{rep.accuracy * 100:.2f}%",
                    "Precision": f"{rep.precision:.3f}",
                    "Recall": f"{rep.recall:.3f}",
                    "F1-Score": f"{rep.f1:.3f}",
                    "ROC-AUC": f"{rep.roc_auc:.3f}" if rep.roc_auc else "N/A",
                    "PR-AUC": f"{rep.pr_auc:.3f}" if rep.pr_auc else "N/A",
                    "Confusion Matrix [[TN, FP], [FN, TP]]": str(rep.confusion_matrix),
                })
            st.dataframe(pd.DataFrame(ctrl_rows).set_index("Model"), use_container_width=True)

            st.warning(
                "⚠️ **QNN Majority-Class Collapse & Imbalance Analysis**: "
                "With unweighted loss on imbalanced genetic data (~25% positive rate), gradient-free COBYLA optimization "
                "rapidly settles into predicting near the negative prior, causing low positive recall at threshold 0.5. "
                "Applying balanced class weighting improves positive recall but introduces false positives in this compressed 4D state space. "
                "Classical Logistic Regression and Random Forest on the exact same 4 features achieve superior discrimination. "
                "**No quantum advantage is observed.**"
            )

        # ---------------------------------------------------------------------
        # Exploratory 41-Feature Benchmark Section
        # ---------------------------------------------------------------------
        st.divider()
        st.markdown("#### 🔬 Exploratory Tabular Benchmark (41 Features, Full Test Partition)")
        st.caption(
            "Higher-dimensional classical benchmark: Evaluates Random Forest and Logistic Regression "
            "on all 41 enriched categorical and numerical features across the full test partition."
        )

        if "exploratory_benchmark_results" not in st.session_state:
            st.session_state["exploratory_benchmark_results"] = None

        if st.button("🚀 Run Full Tabular Benchmark (41 Features)", use_container_width=True):
            with st.spinner(f"Training on {len(y_tr):,} variants, testing on {len(y_te):,} variants..."):
                _, exp_lr = ClassicalVariantBaseline.train_and_evaluate(
                    X_tr_tab, y_tr, X_te_tab, y_te,
                    model_type="logistic_regression", feature_names=pipe_clinvar.feature_names_out_, random_state=42,
                )
                exp_lr.model_name = "Exploratory Logistic Regression (41 Feats)"

                _, exp_rf = ClassicalVariantBaseline.train_and_evaluate(
                    X_tr_tab, y_tr, X_te_tab, y_te,
                    model_type="random_forest", feature_names=pipe_clinvar.feature_names_out_, random_state=42,
                )
                exp_rf.model_name = "Exploratory Random Forest (41 Feats)"

                st.session_state["exploratory_benchmark_results"] = [exp_lr, exp_rf]

        exp_res = st.session_state.get("exploratory_benchmark_results")
        if exp_res:
            exp_rows = []
            for rep in exp_res:
                exp_rows.append({
                    "Model": rep.model_name,
                    "Features": f"{rep.feature_count} features",
                    "Samples (Train/Test)": f"{rep.train_samples:,} / {rep.test_samples:,}",
                    "Accuracy": f"{rep.accuracy * 100:.2f}%",
                    "Precision": f"{rep.precision:.3f}",
                    "Recall": f"{rep.recall:.3f}",
                    "F1-Score": f"{rep.f1:.3f}",
                    "ROC-AUC": f"{rep.roc_auc:.3f}" if rep.roc_auc else "N/A",
                    "PR-AUC": f"{rep.pr_auc:.3f}" if rep.pr_auc else "N/A",
                })
            st.dataframe(pd.DataFrame(exp_rows).set_index("Model"), use_container_width=True)

    # -------------------------------------------------------------------------
    # 4. Multi-Source Genetic Evidence Intelligence & Traceability (Task 7)
    # -------------------------------------------------------------------------
    st.divider()
    st.markdown("### 🔎 4. Multi-Source Genetic Evidence Intelligence & Traceability")
    st.markdown(
        "Traceable evidence collection, normalization, and conflict auditing across "
        "**NCBI ClinVar**, **ClinGen**, **Ensembl**, **gnomAD**, and **PubMed** with "
        "strict reference assembly isolation (GRCh38 vs. GRCh37) and zero credential exposure."
    )

    st.info(
        "🛡️ **Decision-Support & Integrity Notice**: Evidence records provide computational research support only. "
        "Helix Guard does not provide clinical diagnoses, therapeutic prescriptions, or autonomous gene-editing recommendations. "
        "Every assertion is traceable to its primary source endpoint, timestamp, and review status."
    )

    col_qtype, col_qasm = st.columns([1, 1])
    with col_qtype:
        evidence_query_type = st.radio(
            "Evidence Target Type",
            options=["Gene Symbol", "Variant Identifier (rsID / UID)"],
            horizontal=True,
            key="evidence_query_type",
        )
    with col_qasm:
        selected_assembly_str = st.radio(
            "Reference Genome Assembly",
            options=["GRCh38 (Default / Latest)", "GRCh37 (hg19 / Archival)"],
            horizontal=True,
            key="evidence_assembly",
        )
        selected_assembly = (
            GenomeAssembly.GRCh37 if "GRCh37" in selected_assembly_str else GenomeAssembly.GRCh38
        )

    col_inp, col_btn = st.columns([3, 1])
    with col_inp:
        if evidence_query_type == "Gene Symbol":
            default_query = "BRCA1"
            query_label = "Human Gene Symbol (e.g., BRCA1, TP53, LDLR, MYH7, CFTR, MSH2)"
        else:
            default_query = "rs28897743"
            query_label = "Variant Identifier (rsID, ClinVar ID, HGVS, Coordinates e.g. rs28897743, 17667, NC_000017.11:g.43044295dup, 17-7674220-C-T)"

        target_query_input = st.text_input(
            query_label,
            value=default_query,
            key="evidence_target_query",
        ).strip()

    with col_btn:
        st.write("")
        st.write("")
        use_cache_toggle = st.checkbox("Use Local Cache", value=True, help="Prevents API rate limiting and provides offline resilience.")
        search_evidence_btn = st.button("🔎 Fetch Evidence", type="primary", use_container_width=True)

    if "evidence_bundle" not in st.session_state:
        st.session_state["evidence_bundle"] = None

    if search_evidence_btn and target_query_input:
        with st.spinner(f"Querying connected evidence repositories for '{target_query_input}' ({selected_assembly.value})..."):
            try:
                if evidence_query_type == "Gene Symbol":
                    bundle = evidence_orchestrator.search_gene(
                        gene_symbol=target_query_input,
                        assembly=selected_assembly,
                        use_cache=use_cache_toggle,
                    )
                else:
                    bundle = evidence_orchestrator.search_variant(
                        variant_identifier=target_query_input,
                        assembly=selected_assembly,
                        use_cache=use_cache_toggle,
                    )
                st.session_state["evidence_bundle"] = bundle
            except Exception as e:
                st.error(f"Evidence query failed: {sanitize_message(str(e))}")

    active_bundle = st.session_state.get("evidence_bundle")
    if active_bundle:
        st.markdown("---")
        st.markdown(f"#### 🧬 Evidence Record: `{active_bundle.query_term}` ({active_bundle.target_assembly.value})")

        # 1. Source Connectivity & Operational Status Badges
        st.markdown("##### 📡 Source Repository Connectivity & Latency")
        status_cols = st.columns(5)
        sources_meta = [
            ("NCBI ClinVar", "ClinVar"),
            ("ClinGen", "ClinGen"),
            ("Ensembl", "Ensembl"),
            ("gnomAD", "gnomAD"),
            ("NCBI PubMed", "PubMed"),
        ]

        for i, (disp_name, src_key) in enumerate(sources_meta):
            status = active_bundle.source_statuses.get(src_key, SourceStatus.UNAVAILABLE)
            rec_count = active_bundle.source_record_counts.get(src_key, 0)
            comp_status = active_bundle.source_completeness.get(src_key, "")
            with status_cols[i]:
                if status == SourceStatus.AVAILABLE:
                    st.success(f"🟢 **{disp_name}**\n\nLive Available\n\n`{rec_count} records ({comp_status})`")
                elif status == SourceStatus.CACHED:
                    st.info(f"🔵 **{disp_name}**\n\nValidated Cache\n\n`{rec_count} records ({comp_status})`")
                elif status == SourceStatus.LOCAL_REFERENCE:
                    st.info(f"🟣 **{disp_name}**\n\nLocal Reference Data\n\n`{rec_count} records ({comp_status})`")
                elif status == SourceStatus.TIMEOUT:
                    st.warning(f"🟡 **{disp_name}**\n\nTimed Out\n\n`0 records (Empty)`")
                elif status == SourceStatus.UNAVAILABLE:
                    st.caption(f"⚪ **{disp_name}**\n\nNot Indexed / Absent\n\n`0 records (Empty)`")
                else:
                    st.error(f"🔴 **{disp_name}**\n\nEndpoint Error\n\n`0 records (Error)`")

        var_rec = getattr(active_bundle, "variant_evidence_record", None)

        # 2A. Variant Identity Card (if querying a variant)
        if active_bundle.variant_identity:
            vid = active_bundle.variant_identity
            st.markdown("##### 🧬 Variant Identity & Genomic Locus")
            col_v1, col_v2, col_v3, col_v4, col_v5 = st.columns(5)
            col_v1.metric("Normalized ID", vid.normalized_identifier or vid.variant_id)
            col_v2.metric("Chromosome", f"chr{vid.chromosome}" if vid.chromosome != "Unknown" else "Unknown")
            pos_disp = f"{vid.position:,}" if vid.position > 0 else "Unmapped"
            col_v3.metric("Position (1-based)", pos_disp)
            col_v4.metric("Ref / Alt Allele", f"{vid.reference_allele} > {vid.alternate_allele}")
            col_v5.metric("Associated Gene", vid.associated_gene or vid.gene_symbol or "Unassigned")

            st.caption(
                f"**Normalization Source**: {vid.normalization_source} | "
                f"**Input Identifier**: `{vid.input_identifier}` | "
                f"**Assembly**: `{vid.assembly.value}`"
            )

            if not vid.is_valid:
                st.error(f"❌ **Invalid Variant Definition**: {vid.validation_error}")
            elif vid.is_ambiguous:
                st.warning(f"⚠️ **Ambiguous Variant Definition**: {vid.ambiguity_reason}")

        # 2B. Gene Identity Card (if querying a gene)
        elif active_bundle.gene_identity:
            gid = active_bundle.gene_identity
            st.markdown("##### 🧬 Gene Identity & Genomic Localization")
            col_g1, col_g2, col_g3, col_g4, col_g5 = st.columns(5)
            col_g1.metric("Gene Symbol", gid.symbol)
            col_g2.metric("Ensembl ID", gid.ensembl_gene_id or "Unassigned")
            col_g3.metric("Chromosome", f"chr{gid.chromosome}" if gid.chromosome else "Unknown")
            locus_str = f"{gid.start:,} - {gid.end:,}" if gid.start and gid.end else "Unannotated"
            col_g4.metric("Coordinates (1-based)", locus_str)
            col_g5.metric("Reference Assembly", gid.assembly.value)

            if gid.description:
                st.caption(f"**Gene Description**: {gid.description}")

            # Transcripts Table for Gene
            if active_bundle.transcripts:
                with st.expander(f"📑 Ensembl Transcripts ({len(active_bundle.transcripts)} isoforms)", expanded=False):
                    tr_rows = []
                    for t in active_bundle.transcripts:
                        tr_rows.append({
                            "Transcript ID": t.transcript_id,
                            "Canonical": "✅ Yes" if t.is_canonical else "No",
                            "MANE Select": "⭐ MANE" if t.is_mane_select else "-",
                            "Biotype": t.biotype or "Unknown",
                            "Protein ID": t.protein_id or "-",
                        })
                    st.dataframe(pd.DataFrame(tr_rows), use_container_width=True)

        # 3. Clinical Classification & Conflict Auditing (ClinVar)
        if active_bundle.gene_variant_landscape:
            landscape = active_bundle.gene_variant_landscape
            st.markdown("##### ⚖️ Gene-Level Variant Landscape (NCBI ClinVar)")
            st.info(
                "ℹ️ **Allele-Centric Repository Notice**: ClinVar indexes individual genetic variants and their submitter assertions, "
                "rather than an aggregate classification for the entire gene. Genes do not possess a single 'pathogenic' or 'benign' status; "
                "individual variants within this locus range from benign polymorphisms to severe pathogenic alleles."
            )
            col_l1, col_l2, col_l3 = st.columns(3)
            col_l1.metric("Total ClinVar Variants for Gene", f"{landscape.total_variants_count:,}")
            col_l2.metric("Curated Benchmark Variants", len(landscape.variants))
            col_l3.metric("Locus Assembly", active_bundle.target_assembly.value)

            if landscape.variants:
                v_rows = []
                for v in landscape.variants:
                    stars_visual = "⭐" * v.review_stars if v.review_stars > 0 else "0 stars"
                    v_rows.append({
                        "ClinVar ID": v.variation_id,
                        "Variant Title": v.title,
                        "Clinical Significance": v.primary_classification,
                        "Review Stars": stars_visual,
                        "Review Status": v.review_status,
                        "Conditions": ", ".join(v.conditions) if v.conditions else "Not specified",
                        "Submissions": len(v.submissions),
                    })
                st.dataframe(pd.DataFrame(v_rows), use_container_width=True)
        elif active_bundle.clinical_evidence:
            st.markdown("##### ⚖️ Clinical Classification & Review Status (NCBI ClinVar)")
            ce = active_bundle.clinical_evidence
            col_c1, col_c2, col_c3, col_c4 = st.columns(4)
            col_c1.metric("Primary Classification", ce.primary_classification)
            stars_visual = "⭐" * ce.review_stars if ce.review_stars > 0 else "0 stars (No assertion criteria)"
            col_c2.metric("ACMG Review Stars", stars_visual)
            col_c3.metric("Review Status", ce.review_status)
            col_c4.metric("Total Submissions", ce.total_submissions if ce.total_submissions else len(ce.submissions))

            if ce.conditions:
                st.markdown(f"**Associated Phenotypes / Conditions**: {', '.join(ce.conditions)}")
            if ce.vcv_accession or ce.rcv_accessions:
                acc_info = []
                if ce.vcv_accession:
                    acc_info.append(f"VCV: `{ce.vcv_accession}`")
                if ce.rcv_accessions:
                    acc_info.append(f"RCV: `{', '.join(ce.rcv_accessions)}`")
                st.caption(f"**ClinVar Accessions**: {' | '.join(acc_info)}")

            if ce.is_conflicting:
                st.warning(
                    f"⚠️ **Submitter Disagreement Detected**: {ce.conflict_summary or 'Conflicting laboratory classifications reported'}. "
                    "In accordance with Helix Guard scientific guidelines, submitter disagreement indicates lack of consensus and "
                    "must **not** be interpreted as verified biological pathogenicity."
                )

            # Task 8.3: Submitter Concordance vs. Discordance Breakdown Metrics
            if ce.submissions:
                sig_counts = {}
                for s in ce.submissions:
                    sig_label = s.clinical_significance or "Unspecified"
                    sig_counts[sig_label] = sig_counts.get(sig_label, 0) + 1

                p_count = sum(c for k, c in sig_counts.items() if "pathogenic" in k.lower())
                b_count = sum(c for k, c in sig_counts.items() if "benign" in k.lower())
                v_count = sum(c for k, c in sig_counts.items() if "uncertain" in k.lower() or "vus" in k.lower())
                o_count = sum(c for k, c in sig_counts.items() if not any(x in k.lower() for x in ["pathogenic", "benign", "uncertain", "vus"]))

                col_sb1, col_sb2, col_sb3 = st.columns(3)
                col_sb1.metric("Pathogenic / Likely Pathogenic", f"{p_count} reports")
                col_sb2.metric("Uncertain Significance (VUS)", f"{v_count} reports")
                col_sb3.metric("Benign / Likely Benign", f"{b_count} reports" if b_count > 0 else f"{o_count} other/risk reports")

                with st.expander(f"📋 Individual Submissions & Assertion Criteria ({len(ce.submissions)} laboratory reports)", expanded=False):
                    sub_rows = []
                    for s in ce.submissions:
                        sub_rows.append({
                            "Submitter": s.submitter_name,
                            "Clinical Significance": s.clinical_significance,
                            "Review Status": s.review_status,
                            "Date Evaluated": s.evaluation_date or "Not specified",
                            "Assertion Details": s.description or "Criteria provided according to laboratory guidelines",
                        })
                    st.dataframe(pd.DataFrame(sub_rows), use_container_width=True)
                    if ce.vcv_accession or ce.variation_id:
                        v_id_link = ce.variation_id or ce.vcv_accession
                        st.caption(f"🔗 [View Live Variation Record in NCBI ClinVar](https://www.ncbi.nlm.nih.gov/clinvar/variation/{v_id_link}/)")
        else:
            st.markdown("##### ⚖️ Clinical Classification (NCBI ClinVar)")
            st.caption("⚪ No clinical classification or variant landscape record retrieved for this query.")

        # 4. Transcript Consequences & Functional Impact (Ensembl VEP)
        if var_rec and var_rec.transcript_evidence:
            st.markdown("##### 🧬 Transcript Consequences & Functional Annotations (Ensembl VEP)")
            vep_rows = []
            for t in var_rec.transcript_evidence:
                vep_rows.append({
                    "Transcript ID": t.transcript_id,
                    "Gene": t.gene_symbol or "-",
                    "Canonical": "✅ Yes" if t.is_canonical else "No",
                    "MANE Select": "⭐ MANE" if t.is_mane_select else "-",
                    "Consequence": ", ".join(t.consequence_terms),
                    "HGVS.c": t.hgvs_c or "-",
                    "HGVS.p": t.hgvs_p or "-",
                    "Codons": t.codons or "-",
                    "Amino Acids": t.amino_acids or "-",
                    "Exon": t.exon or "-",
                    "SIFT": f"{t.sift_prediction} ({t.sift_score})" if t.sift_prediction else "-",
                    "PolyPhen": f"{t.polyphen_prediction} ({t.polyphen_score})" if t.polyphen_prediction else "-",
                })
            st.dataframe(pd.DataFrame(vep_rows), use_container_width=True)

        # 5. In-Silico Computational Inferences (Task 8.3 Enhanced Cards)
        if var_rec and var_rec.computational_evidence:
            st.markdown("##### 💻 In-Silico Computational Inferences")
            st.warning(
                "⚠️ **In-Silico Hypothesis-Generation Notice**: Algorithmic predictions (SIFT, PolyPhen, CADD, QNN) "
                "are exploratory mathematical models based on sequence conservation and physicochemical modeling. "
                "They do **not** constitute clinical diagnoses or confirmed biological pathogenicity. "
                "Never use computational scores in isolation for diagnostic or therapeutic decisions."
            )

            # Extract key predictors for visual metric cards
            comp_map = {c.prediction_method.lower(): c for c in var_rec.computational_evidence}
            c_sift = comp_map.get("sift")
            c_pph = comp_map.get("polyphen-2") or comp_map.get("polyphen")
            c_qnn = comp_map.get("helixguard-qnn") or comp_map.get("qnn")

            col_p1, col_p2, col_p3 = st.columns(3)
            with col_p1:
                if c_sift:
                    s_score_txt = f"{c_sift.numerical_score:.3f}" if c_sift.numerical_score is not None else "Score N/A"
                    col_p1.metric(
                        "SIFT (Conservation)",
                        c_sift.prediction_output.capitalize(),
                        f"Score: {s_score_txt}",
                        help="SIFT score <= 0.05 is predicted deleterious based on evolutionary amino acid conservation."
                    )
                else:
                    col_p1.metric("SIFT (Conservation)", "Not Available", help="SIFT score not reported for this coordinate.")

            with col_p2:
                if c_pph:
                    pp_score_txt = f"{c_pph.numerical_score:.3f}" if c_pph.numerical_score is not None else "Score N/A"
                    col_p2.metric(
                        "PolyPhen-2 (Structural)",
                        c_pph.prediction_output.replace("_", " ").capitalize(),
                        f"Score: {pp_score_txt}",
                        help="PolyPhen-2 assesses structural disruption: probably damaging (score close to 1.0) vs benign."
                    )
                else:
                    col_p2.metric("PolyPhen-2 (Structural)", "Not Available", help="PolyPhen score not reported for this coordinate.")

            with col_p3:
                if c_qnn:
                    q_score_txt = f"{c_qnn.numerical_score:.3f}" if c_qnn.numerical_score is not None else "N/A"
                    col_p3.metric(
                        "HelixGuard Hybrid QNN",
                        c_qnn.prediction_output,
                        f"Expectation: {q_score_txt}",
                        help="Exploratory 4-qubit variational quantum neural network expectation value (synthetic benchmark)."
                    )
                else:
                    col_p3.metric("HelixGuard QNN", "Synthetic Demo", help="Experimental variational statevector classifier.")

            # Comprehensive computational table
            comp_rows = []
            for c in var_rec.computational_evidence:
                comp_rows.append({
                    "Method": c.prediction_method,
                    "Prediction Output": c.prediction_output,
                    "Numerical Score": f"{c.numerical_score:.3f}" if c.numerical_score is not None else "N/A",
                    "Score Interpretation": "≤0.05 Deleterious" if "sift" in c.prediction_method.lower() else ("≥0.5 Damaging" if "polyphen" in c.prediction_method.lower() else "Hypothesis Score"),
                    "Version": c.version or "Current",
                    "Source": c.source,
                })
            st.dataframe(pd.DataFrame(comp_rows), use_container_width=True)

        # 6. gnomAD Intelligence: Gene Constraint & Variant Population Frequency
        if active_bundle.query_type == "gene" and active_bundle.population_frequency and active_bundle.population_frequency.gene_constraint:
            st.markdown("##### 📊 Gene-Level Constraint Metrics (gnomAD)")
            cons = active_bundle.population_frequency.gene_constraint
            col_p1, col_p2, col_p3 = st.columns(3)
            pli = cons.get("pli") if "pli" in cons else cons.get("pLI")
            oe_lof = cons.get("oe_lof_upper") if "oe_lof_upper" in cons else cons.get("LOEUF")
            col_p1.metric(
                "pLI (LoF Intolerance)",
                f"{pli:.3f}" if pli is not None else "N/A",
                help="pLI >= 0.9 suggests extreme intolerance to heterozygous loss-of-function variation in reference cohorts.",
            )
            col_p2.metric(
                "LOEUF (oe_lof_upper)",
                f"{oe_lof:.3f}" if oe_lof is not None else "N/A",
                help="Lower LOEUF values indicate stronger selective constraint against truncating mutations.",
            )
            col_p3.metric("Reference Dataset", "gnomAD r4 (GRCh38)" if active_bundle.target_assembly == GenomeAssembly.GRCh38 else "gnomAD r2.1 (GRCh37)")

            st.warning(
                "⚠️ **Scientific Guidance**: Gene constraint scores reflect depletion of loss-of-function variants in general population "
                "reference cohorts relative to neutral expectation. **A low pLI score (e.g., 0.000) or elevated LOEUF does NOT establish "
                "benignity, absence of clinical risk, or lack of clinical importance.** Well-established pathogenic mutations "
                "(including in adult-onset disease and tumor suppressor genes) frequently occur in genes with low pLI. "
                "Constraint metrics must never be used in isolation to dismiss variant pathogenicity."
            )

        # Variant-Level Population Frequency & Ancestry Distribution (Task 8.3 Enhanced Visualizer)
        if active_bundle.query_type == "variant" or (active_bundle.population_frequency and active_bundle.population_frequency.allele_frequency is not None):
            st.markdown("##### 🌐 Variant-Level Population Frequencies & Ancestry Distribution (gnomAD)")
            pf = active_bundle.population_frequency
            if pf:
                col_v1, col_v2, col_v3, col_v4 = st.columns(4)
                col_v1.metric("Global Allele Frequency (AF)", f"{pf.allele_frequency:.6f}" if pf.allele_frequency is not None else "Unobserved")
                col_v2.metric("Allele Count (AC)", f"{pf.allele_count:,}" if pf.allele_count is not None else "0")
                col_v3.metric("Allele Number (AN)", f"{pf.allele_number:,}" if pf.allele_number is not None else "0")
                col_v4.metric("Homozygote Count", f"{pf.homozygote_count:,}" if pf.homozygote_count is not None else "0")

                if var_rec and var_rec.population_evidence and var_rec.population_evidence.popmax_frequency is not None:
                    pe = var_rec.population_evidence
                    st.info(
                        f"📍 **Popmax Subpopulation Callout**: Maximum subpopulation frequency is **`{pe.popmax_frequency:.6f}`** "
                        f"observed in **`{pe.popmax_population}`**. Popmax is critical for filtering out common founder variants."
                    )

                if var_rec and var_rec.population_evidence and var_rec.population_evidence.ancestry_frequencies:
                    st.markdown("###### 📊 Interactive Continental Ancestry Frequency Distribution")
                    st.caption(
                        "💡 **Scientific Guidance**: Population frequency differences reflect demographic history, bottleneck events, "
                        "and genetic drift. An elevated frequency in an isolated or founder population (e.g. Ashkenazi Jewish or Finnish) "
                        "must never be conflated with differential intrinsic pathogenicity."
                    )

                    anc_dict = var_rec.population_evidence.ancestry_frequencies
                    anc_labels = {
                        "afr": "African / African American (AFR)",
                        "amr": "Admixed American / Latino (AMR)",
                        "asj": "Ashkenazi Jewish (ASJ)",
                        "eas": "East Asian (EAS)",
                        "fin": "European (Finnish) (FIN)",
                        "nfe": "European (Non-Finnish) (NFE)",
                        "sas": "South Asian (SAS)",
                        "mid": "Middle Eastern (MID)",
                        "ami": "Amish (AMI)",
                        "remaining": "Other / Remaining",
                    }
                    chart_data = []
                    table_data = []
                    for k, v in anc_dict.items():
                        clean_k = k.lower()
                        lbl = anc_labels.get(clean_k, clean_k.upper())
                        chart_data.append({"Continental Ancestry": lbl, "Allele Frequency": v})
                        table_data.append({
                            "Continental Ancestry": lbl,
                            "Allele Frequency (Decimal)": f"{v:.6f}",
                            "Frequency Percentage": f"{v * 100:.4f}%",
                            "Frequency Magnitude": f"{v:.2e}",
                        })

                    chart_df = pd.DataFrame(chart_data).set_index("Continental Ancestry")
                    st.bar_chart(chart_df)

                    with st.expander("📋 Detailed Subpopulation Breakdown Table", expanded=False):
                        st.dataframe(pd.DataFrame(table_data), use_container_width=True)
                else:
                    st.caption("⚪ Subpopulation ancestry breakdown unobserved or not reported for this variant coordinate in gnomAD.")
            else:
                st.caption("⚪ gnomAD variant population frequencies unobserved or unavailable for this query.")

        # 7. Gene-Disease Validity (ClinGen)
        st.markdown("##### 🛡️ Gene-Disease Clinical Validity (ClinGen)")
        if active_bundle.gene_disease_validity:
            if active_bundle.query_type == "variant":
                associated_gene_name = active_bundle.variant_identity.associated_gene or active_bundle.query_term
                st.info(
                    f"ℹ️ **Gene-Level Validity Context**: ClinGen curations evaluate the clinical validity and dosage sensitivity "
                    f"of the associated gene locus (`{associated_gene_name}`), NOT individual variant pathogenicity."
                )

            is_local = any(getattr(vg, "is_local_reference", False) for vg in active_bundle.gene_disease_validity) or \
                       active_bundle.source_statuses.get("ClinGen") == SourceStatus.LOCAL_REFERENCE
            if is_local:
                st.info(
                    "📋 **Provenance Disclosure**: Gene-disease clinical validity assertions below are displayed from "
                    "**Local Curated Reference Data** (curated reference snapshot based on ClinGen Gene Curation Registry records), "
                    "not from a live ClinGen API response."
                )
            else:
                st.success("🟢 **Live ClinGen Integration**: Data retrieved from live ClinGen / GeneGraph service.")

            vg_rows = []
            for vg in active_bundle.gene_disease_validity:
                vg_rows.append({
                    "Gene": vg.gene_symbol,
                    "Disease / Condition": vg.disease_label,
                    "Disease ID (MONDO/OMIM)": vg.disease_id or "Unassigned",
                    "Validity Classification": vg.classification,
                    "Mode of Inheritance": vg.mode_of_inheritance or "Not specified",
                    "Curation Panel": vg.curation_panel or "ClinGen Expert Panel",
                    "HI Score": f"HI: {vg.haploinsufficiency_score}" if vg.haploinsufficiency_score is not None else "Unscored",
                    "Assertion Date": vg.assertion_date or "Unspecified",
                    "Provenance Origin": "Local Reference Snapshot" if getattr(vg, "is_local_reference", False) else "Live API",
                })
            st.dataframe(pd.DataFrame(vg_rows), use_container_width=True)
        else:
            st.caption("⚪ No ClinGen gene-disease validity curations indexed for this gene.")

        # 8. Peer-Reviewed Publications (PubMed)
        st.markdown("##### 📚 Peer-Reviewed Scientific Literature (NCBI PubMed)")
        if active_bundle.publications:
            pub_rows = []
            for p in active_bundle.publications:
                row = {
                    "PMID": p.pmid,
                    "Title": p.title,
                    "Journal": p.journal or "Unspecified",
                    "Year": p.year or "Unspecified",
                    "DOI": p.doi or "-",
                    "URL": p.url,
                }
                if p.variant_specific_relevance:
                    row["Relevance / Clinical Context"] = p.variant_specific_relevance
                pub_rows.append(row)
            st.dataframe(pd.DataFrame(pub_rows), use_container_width=True)
        else:
            pubmed_status = active_bundle.source_statuses.get("PubMed", SourceStatus.UNAVAILABLE)
            if pubmed_status == SourceStatus.AVAILABLE or pubmed_status == SourceStatus.CACHED:
                st.caption("ℹ️ Search completed: No indexed citations matched the query criteria in NCBI PubMed.")
            elif pubmed_status == SourceStatus.TIMEOUT:
                st.warning("🟡 NCBI PubMed search timed out. Check network connection.")
            else:
                st.caption("⚪ No indexed PubMed citations retrieved for this query.")

        # 9. Conflicting Evidence & Disagreement Audit
        if var_rec and var_rec.conflicts_detected:
            st.markdown("##### ⚠️ Conflict & Discordance Audit")
            for conf in var_rec.conflicts_detected:
                st.warning(f"⚠️ {conf}")

        # 10. Missing Evidence Disclosures
        if var_rec and var_rec.missing_evidence:
            st.markdown("##### 📋 Missing Evidence & Unindexed Dimensions")
            for miss in var_rec.missing_evidence:
                st.info(f"⚪ {miss}")

        # 11. Traceability, Retrieval Provenance & Metadata Expander
        with st.expander("🔍 Traceability, Source Provenance & Retrieval Audit", expanded=False):
            st.markdown(f"**Query Target**: `{active_bundle.query_term}` ({active_bundle.query_type})")
            st.markdown(f"**Retrieval Timestamp (UTC)**: `{active_bundle.timestamp}`")
            st.markdown(f"**Explicit Assembly**: `{active_bundle.target_assembly.value}`")

            prov_records = []
            if active_bundle.gene_identity and active_bundle.gene_identity.provenance:
                prov_records.append(active_bundle.gene_identity.provenance)
            if active_bundle.variant_identity and active_bundle.variant_identity.provenance:
                prov_records.append(active_bundle.variant_identity.provenance)
            if active_bundle.clinical_evidence and active_bundle.clinical_evidence.provenance:
                prov_records.append(active_bundle.clinical_evidence.provenance)
            if active_bundle.gene_variant_landscape and active_bundle.gene_variant_landscape.provenance:
                prov_records.append(active_bundle.gene_variant_landscape.provenance)
            if active_bundle.population_frequency and active_bundle.population_frequency.provenance:
                prov_records.append(active_bundle.population_frequency.provenance)
            if var_rec:
                for t in var_rec.transcript_evidence:
                    if t.provenance and t.provenance not in prov_records:
                        prov_records.append(t.provenance)
                for c in var_rec.computational_evidence:
                    if c.provenance and c.provenance not in prov_records:
                        prov_records.append(c.provenance)
            for vg in active_bundle.gene_disease_validity:
                if vg.provenance and vg.provenance not in prov_records:
                    prov_records.append(vg.provenance)
            for pub in active_bundle.publications:
                if pub.provenance and pub.provenance not in prov_records:
                    prov_records.append(pub.provenance)

            if prov_records:
                prov_table = []
                for pr in prov_records:
                    if pr.is_local_reference:
                        origin_label = "🟣 Local Reference Snapshot"
                    elif pr.is_cached:
                        origin_label = "🔵 Validated Cache"
                    else:
                        origin_label = "🟢 Live Request"

                    prov_table.append({
                        "Source": pr.source_name,
                        "Endpoint": pr.source_endpoint,
                        "Source URL": pr.source_url,
                        "Data Origin": origin_label,
                        "Latency (ms)": pr.response_latency_ms,
                        "License Notice": pr.license_notice or "Standard API Usage",
                    })
                st.dataframe(pd.DataFrame(prov_table), use_container_width=True)

        # 12. Scientific Limitations & Quality Guidance Expander
        with st.expander("⚠️ Scientific Limitations & Defense Against Biological Fallacies", expanded=False):
            st.markdown(
                "Helix Guard enforces strict epistemological boundaries to ensure computational models "
                "are never conflated with verified clinical facts:\n"
                "- **Submitter disagreement is not pathogenicity**: Conflicting laboratory submissions in ClinVar reflect divergent criteria or evidence interpretation, not proof that a variant is disease-causing.\n"
                "- **Population rarity is not proof of pathogenicity**: Extremely rare or unobserved variants in gnomAD may simply be private benign polymorphisms.\n"
                "- **High population frequency is not proof of benignity**: Mild or late-onset disease alleles can persist at measurable population frequencies.\n"
                "- **Computational predictions are not clinical confirmations**: In-silico scores (CADD, SIFT, PolyPhen, QNN, CNN) are exploratory hypothesis generators that require wet-lab experimental confirmation.\n"
                "- **Literature citations reflect published hypotheses**: Article titles and abstracts report study observations and do not represent verified consensus."
            )
            st.markdown("**Active Limitations for this Record:**")
            for lim in active_bundle.scientific_limitations:
                st.write(f"- {lim}")


# =============================================================================
# TAB 4: FIVE-GENE CORRECTION PIPELINE & EPISTASIS CONFLICT RESOLUTION
# =============================================================================
with tab_correction_pipeline:
    st.header("🛡️ Five-Gene Sequential In-Silico Correction & Epistasis Pipeline")
    st.info(
        "🔬 **Milestones 9–11 Computational Architecture**: Integrates multi-variant VCF parsing, "
        "compound heterozygosity detection, cis/trans phasing analysis, epistatic cross-effect modeling, "
        "and sequential priority-based in-silico repair with FASTA sequence export."
    )

    st.warning(
        "⚠️ **Ethical & Clinical Boundary Notice**: HELIX GUARD is strictly a computational simulation and "
        "predictive model. No wet-lab procedures, embryonic editing, clinical interventions, or polygenic "
        "enhancements are performed or recommended."
    )

    # 1. Genotype Ingestion & Preset Selector
    st.subheader("1. 📥 Multi-Variant Genotype & VCF Ingestion")
    vcf_pipeline = VCFPipeline()
    epistasis_engine = EpistasisEngine()
    correction_engine = InSilicoCorrectionEngine(epistasis_engine=epistasis_engine)
    fasta_generator = FASTAGenerator()

    col_preset, col_opts = st.columns([2, 1])
    with col_preset:
        preset_choice = st.selectbox(
            "Select Clinical Genotype Profile:",
            [
                "Complete 5-Gene Priority Panel (BRCA1, HBB, CFTR, HEXA, DMD)",
                "CFTR Compound Heterozygous in Trans (Biallelic Disruption)",
                "TP53 + BRCA1 Synthetic Lethality Multi-Locus Interaction",
                "Custom VCF Text Input",
            ],
            index=0,
            key="vcf_preset_choice"
        )

    with col_opts:
        include_beneficial = st.checkbox(
            "Include Investigative Beneficial Suggestion (CCR5-Δ32)",
            value=True,
            help="Displays well-characterized beneficial alleles with documented trade-offs.",
            key="vcf_include_beneficial"
        )

    # Determine default VCF text
    if "5-Gene" in preset_choice:
        default_vcf = vcf_pipeline.get_sample_preset_vcf("complete_5gene_panel")
    elif "CFTR" in preset_choice:
        default_vcf = vcf_pipeline.get_sample_preset_vcf("cftr_compound_het")
    elif "TP53" in preset_choice:
        default_vcf = vcf_pipeline.get_sample_preset_vcf("synthetic_lethality_tp53_brca1")
    else:
        default_vcf = "##fileformat=VCFv4.2\n#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\tFORMAT\tSAMPLE\n"

    vcf_input = st.text_area(
        "VCF (Variant Call Format) Stream:",
        value=default_vcf,
        height=150,
        key="vcf_stream_input"
    )

    sample_id = st.text_input("Patient / Sample Identifier:", value="HG_CLINICAL_SIM_001", key="vcf_sample_id")

    if st.button("🚀 Run Sequential Correction & Epistasis Pipeline", type="primary", key="btn_run_pipeline"):
        parsed_variants = vcf_pipeline.parse_vcf_text(vcf_input)

        if not parsed_variants:
            st.error("No valid variant records detected in the provided VCF input.")
        else:
            st.success(f"Successfully ingested and parsed {len(parsed_variants)} variant locus records.")

            # Display parsed variants
            st.markdown("##### 🧬 Ingested Variant Inventory")
            var_summary = []
            for v in parsed_variants:
                var_summary.append({
                    "Variant ID": v.variant_id,
                    "Gene": v.gene_symbol,
                    "Locus": f"{v.chromosome}:{v.position}",
                    "Ref / Alt": f"{v.ref_allele} > {v.alt_allele}",
                    "Pathogenicity": v.pathogenicity,
                    "Zygosity": v.zygosity,
                })
            st.dataframe(pd.DataFrame(var_summary), use_container_width=True)

            # 2. Epistasis & Phasing Analysis (Milestone 9)
            st.divider()
            st.subheader("2. 🧩 Epistasis, Phasing & Compound Heterozygosity Analysis")
            phase_map = {}
            if "CFTR" in preset_choice:
                phase_map = {("rs121908752", "rs75527207"): GenotypePhase.TRANS}

            epistasis_report = epistasis_engine.analyze_multi_variant_profile(
                variants=parsed_variants,
                phase_map=phase_map,
                base_risks={p["gene"]: 0.10 for p in correction_engine.priority_panel}
            )

            c_epi1, c_epi2 = st.columns(2)
            with c_epi1:
                st.markdown("**Compound Heterozygosity Findings:**")
                if not epistasis_report.compound_heterozygotes:
                    st.info("No compound heterozygosity detected among input variants.")
                else:
                    for comp in epistasis_report.compound_heterozygotes:
                        if comp.is_compound_heterozygous:
                            st.error(f"🚨 **{comp.gene_symbol}**: Compound Heterozygous ({comp.phase.value})")
                        else:
                            st.warning(f"⚠️ **{comp.gene_symbol}**: Phase {comp.phase.value}")
                        st.caption(comp.explanation)

            with c_epi2:
                st.markdown("**Epistatic & Modifier Relationships:**")
                if not epistasis_report.epistatic_interactions:
                    st.info("No inter-genic epistatic interactions detected.")
                else:
                    for epi in epistasis_report.epistatic_interactions:
                        st.warning(f"⚡ **{epi.interaction_type}**: {epi.gene_a} ({epi.variant_a}) ⟷ {epi.gene_b} ({epi.variant_b})")
                        st.caption(f"**Severity Delta**: {epi.severity_delta:+.2f} | {epi.biological_rationale}")

            if epistasis_report.conflicts_identified:
                with st.expander("📋 Detailed Interaction Conflict Log", expanded=True):
                    for conf in epistasis_report.conflicts_identified:
                        st.write(f"- {conf}")

            # 3. Sequential 5-Gene In-Silico Correction Execution (Milestone 10)
            st.divider()
            st.subheader("3. 🔧 Sequential Priority-Based In-Silico Repair Execution")
            pipeline_result = correction_engine.run_pipeline(
                variants=parsed_variants,
                initial_sequence="ATGCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATC" * 10,
                include_beneficial_suggestion=include_beneficial
            )

            # Before / After Risk Profiles
            st.markdown("##### 📊 Pre-Edit vs Post-Edit Disease Risk Profile (5-Gene Panel)")
            risk_comparison = []
            for item in correction_engine.priority_panel:
                g = item["gene"]
                risk_comparison.append({
                    "Priority": item["priority"],
                    "Gene": g,
                    "Condition": item["condition"],
                    "Pre-Edit Risk": pipeline_result.initial_risk_profile.get(g, 0.10),
                    "Post-Edit Risk": pipeline_result.final_risk_profile.get(g, 0.10),
                })
            risk_df = pd.DataFrame(risk_comparison).set_index("Gene")
            st.bar_chart(risk_df[["Pre-Edit Risk", "Post-Edit Risk"]])

            # Step-by-step edit audit table
            st.markdown("##### 📝 Molecular Edit Audit Trail")
            if not pipeline_result.edit_history:
                st.info("No sequence modifications required; all variants clear or benign.")
            else:
                audit_rows = []
                for edit in pipeline_result.edit_history:
                    pe = edit.proposed_edit
                    audit_rows.append({
                        "Step": edit.step_number,
                        "Gene": edit.gene_symbol,
                        "Variant": edit.variant_id,
                        "Strategy": pe.strategy.value,
                        "Modality": pe.recommended_modality.value,
                        "Guide RNA Candidate": pe.guide_rna_candidate,
                        "Predicted Efficiency": f"{pe.predicted_efficiency * 100:.1f}%",
                        "Pre Risk": f"{edit.original_risk:.2f}",
                        "Post Risk": f"{edit.post_edit_risk:.2f}",
                        "Status": edit.status,
                    })
                st.dataframe(pd.DataFrame(audit_rows), use_container_width=True)

            # 4. Beneficial Variant Suggestions (Stretch Goal)
            if pipeline_result.beneficial_suggestions:
                st.divider()
                st.subheader("4. 🌟 Investigative Single-Locus Beneficial Allele Exploration")
                for ben in pipeline_result.beneficial_suggestions:
                    with st.expander(f"🧬 {ben.gene_symbol} ({ben.allele_name}) — Investigative Profile", expanded=True):
                        st.markdown(f"**Beneficial Phenotype**: {ben.beneficial_phenotype}")
                        st.markdown("**Documented Biological Trade-Offs**:")
                        for t in ben.documented_trade_offs:
                            st.write(f"- ⚠️ {t}")
                        st.caption(f"🛡️ *Ethical Safeguard*: {ben.ethical_safeguard_notice}")

            # 5. FASTA Sequence Export & Clinical Report Download (Milestone 11)
            st.divider()
            st.subheader("5. 💾 Validated FASTA Sequence & Clinical Report Export")

            fasta_content = fasta_generator.generate_fasta(
                sequence="ATGCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATC" * 10,
                sample_id=sample_id,
                edit_history=pipeline_result.edit_history
            )

            clinical_report_md = fasta_generator.generate_clinical_markdown_report(
                sample_id=sample_id,
                edit_history=pipeline_result.edit_history,
                initial_risks=pipeline_result.initial_risk_profile,
                final_risks=pipeline_result.final_risk_profile,
                beneficial_suggestions=pipeline_result.beneficial_suggestions
            )

            c_exp1, c_exp2 = st.columns(2)
            with c_exp1:
                st.markdown("**FASTA Sequence Preview:**")
                st.code(fasta_content[:350] + "\n... [sequence truncated for preview] ...", language="text")
                st.download_button(
                    label="📥 Download Validated FASTA File",
                    data=fasta_content,
                    file_name=f"{sample_id}_helix_guard_corrected.fasta",
                    mime="text/plain",
                    key="dl_fasta_btn"
                )

            with c_exp2:
                st.markdown("**Clinical Audit Report Preview:**")
                st.text_area("Markdown Report:", value=clinical_report_md[:400] + "\n...", height=150, disabled=True)
                st.download_button(
                    label="📄 Download Clinical Markdown Report",
                    data=clinical_report_md,
                    file_name=f"{sample_id}_clinical_report.md",
                    mime="text/markdown",
                    key="dl_report_btn"
                )

