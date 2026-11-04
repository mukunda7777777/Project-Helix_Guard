"""
Integration and Verification Test Suite for Helix Guard (Task 3).

Tests cover:
- UI Initialization & Persistent Scientific Disclaimers
- Scientific Transparency Explanations & Model Limitations
- Part 1 Terminology Updates (Classical Sequence Optimization)
- Part 2 Terminology Updates (Synthetic QNN Labels & Metrics)
- Part 4 Security & Credential Isolation (Masking, No Plaintext Leakage, Gitignore Rules)
- Classical Residual CNN Optimization Workflow
- Quantum Intelligence Tab Execution & Training Workflow
- Visualizations Rendering (Loss History, Probabilities, Predictions)
- Interactive Custom Inference
- Model Save and Load Workflows
"""

import os
import re
import tempfile
from unittest.mock import patch
import pytest
from streamlit.testing.v1 import AppTest

# Determine path to app.py and project root
current_dir = os.path.dirname(os.path.abspath(__file__))
helix_guard_dir = os.path.dirname(current_dir)
project_root = os.path.dirname(helix_guard_dir)
app_file = os.path.join(helix_guard_dir, "app.py")

from security import IBMQuantumCredentials, load_ibm_credentials, mask_secret, sanitize_message


class TestStreamlitAppIntegration:
    @pytest.fixture(autouse=True)
    def setup_app(self):
        self.at = AppTest.from_file(app_file, default_timeout=35)

    def test_app_initial_render_and_disclaimers(self):
        """Verifies initial page loads cleanly with persistent scientific disclaimer and tabs."""
        self.at.run()
        assert not self.at.exception, f"App raised exception during initial render: {self.at.exception}"

        # Verify tabs exist
        assert len(self.at.tabs) >= 2
        tab_labels = [t.label for t in self.at.tabs]
        assert any("Classical" in lbl for lbl in tab_labels)
        assert any("Quantum Intelligence" in lbl for lbl in tab_labels)

        # PART 3: Verify persistent scientific disclaimer is visible in warnings
        warning_texts = [w.value for w in self.at.warning]
        expected_persistent_disclaimer = (
            "Helix Guard currently demonstrates experimental machine-learning and "
            "quantum-machine-learning workflows. Its present models have not been validated "
            "for clinical pathogenicity prediction or biological DNA correction."
        )
        assert any(expected_persistent_disclaimer in text for text in warning_texts), (
            "Required persistent scientific research disclaimer is missing from UI."
        )

        # PART 3: Verify markdown explanation in transparency expander
        markdown_texts = " ".join([m.value for m in self.at.markdown])
        assert "not clinical probabilities" in markdown_texts
        assert "computational demonstrations" in markdown_texts
        assert "Real biological validation requirements" in markdown_texts or "validation" in markdown_texts

    def test_part1_classical_scientific_terminology(self):
        """Verifies Part 1 classical scientific terminology replaces unvalidated terms."""
        self.at.run()
        assert not self.at.exception

        # Click classical optimization button
        btn_cnn_list = [b for b in self.at.button if "Run Pathogenicity Optimization" in b.label]
        assert len(btn_cnn_list) == 1
        btn_cnn_list[0].click().run()
        assert not self.at.exception

        # PART 1: "Pathogenicity Risk Score" -> "Model Output Score (Unvalidated)"
        metric_labels = [m.label for m in self.at.metric]
        assert any("Initial Model Output Score (Unvalidated)" in lbl for lbl in metric_labels), (
            f"Expected 'Initial Model Output Score (Unvalidated)', found: {metric_labels}"
        )
        assert any("Pre-Edit Score (Unvalidated)" in lbl for lbl in metric_labels)
        assert any("Post-Edit Score (Unvalidated)" in lbl for lbl in metric_labels)

        # PART 1: "Optimal Edit" -> "Candidate Substitution"
        assert any("Candidate Substitution" in lbl for lbl in metric_labels)

        # PART 1: "Found 5 optimal edit candidates that reduce pathogenicity" ->
        # "Found 5 candidate substitutions that reduce the model output score"
        success_texts = [s.value for s in self.at.success]
        assert any("candidate substitutions that reduce the model output score" in text for text in success_texts)

        # PART 1: "AI-Perfected DNA Output" -> "Hypothetical Sequence Modification"
        subheader_texts = [sh.value for sh in self.at.subheader]
        assert any("Hypothetical Sequence Modification" in text for text in subheader_texts)

        # PART 1: "Perfected Sequence" -> "Candidate Modified Sequence"
        markdown_texts = " ".join([m.value for m in self.at.markdown])
        assert "Candidate Modified Sequence" in markdown_texts

    def test_part2_qnn_synthetic_terminology(self):
        """Verifies Part 2 QNN terminology updates for synthetic demonstration data."""
        self.at.run()
        assert not self.at.exception

        # Click Train button
        btn_qnn_list = [b for b in self.at.button if "Train Quantum Classifier" in b.label]
        assert len(btn_qnn_list) == 1
        btn_qnn_list[0].click().run()
        assert not self.at.exception

        # PART 2: "Test Accuracy" -> "Synthetic Test Accuracy"
        metric_labels = [m.label for m in self.at.metric]
        assert any("Synthetic Test Accuracy" in lbl for lbl in metric_labels), (
            f"Expected 'Synthetic Test Accuracy', found: {metric_labels}"
        )

        # PART 2: Verify dataframe columns and values for synthetic class labeling
        assert len(self.at.dataframe) >= 1
        df_columns = []
        for df_elem in self.at.dataframe:
            if hasattr(df_elem.value, "columns"):
                df_columns.extend(list(df_elem.value.columns))

        # Check column names: "Synthetic Model Output", "True Synthetic Class", "Predicted Synthetic Class"
        assert "Synthetic Model Output" in df_columns or any("Synthetic" in col for col in df_columns)

    def test_quantum_intelligence_training_and_visualizations(self):
        """Verifies synthetic QNN training and rendering of visualizations."""
        self.at.run()
        assert not self.at.exception

        btn_qnn_list = [b for b in self.at.button if "Train Quantum Classifier" in b.label]
        btn_qnn_list[0].click().run()
        assert not self.at.exception

        # Verify charts rendered (loss chart and prob distribution)
        chart_elements = [e for e in self.at.main if e.type == "vega_lite_chart"]
        assert len(chart_elements) >= 2, f"Expected at least 2 vega_lite_chart elements, got {len(chart_elements)}."
        assert len(self.at.dataframe) >= 1

    def test_quantum_interactive_custom_inference(self):
        """Verifies single-variant inference after training uses synthetic labeling."""
        self.at.run()

        btn_qnn = [b for b in self.at.button if "Train Quantum Classifier" in b.label][0]
        btn_qnn.click().run()
        assert not self.at.exception

        score_btn_list = [b for b in self.at.button if "Score Variant with QNN" in b.label]
        score_btn_list[0].click().run()
        assert not self.at.exception

        # Check label uses "Synthetic Model Output"
        metric_labels = [m.label for m in self.at.metric]
        assert any("Synthetic Model Output" in lbl for lbl in metric_labels)

    def test_quantum_model_save_and_load(self):
        """Verifies saving model to disk and loading it back through Streamlit UI."""
        self.at.run()

        btn_qnn = [b for b in self.at.button if "Train Quantum Classifier" in b.label][0]
        btn_qnn.click().run()
        assert not self.at.exception

        with tempfile.TemporaryDirectory() as tmp_dir:
            test_save_name = os.path.join(tmp_dir, "test_ui_qnn.json")

            save_input = [t for t in self.at.text_input if "Destination Filename" in t.label][0]
            save_input.input(test_save_name)

            btn_save = [b for b in self.at.button if "Save Model to Disk" in b.label][0]
            btn_save.click().run()
            assert not self.at.exception
            assert os.path.exists(test_save_name)

            load_input = [t for t in self.at.text_input if "Or Specify Server File Path" in t.label][0]
            load_input.input(test_save_name)

            btn_load = [b for b in self.at.button if "Load Model" in b.label and "Save" not in b.label][0]
            btn_load.click().run()
            assert not self.at.exception

            success_texts = [s.value for s in self.at.success]
            assert any("Successfully loaded QNN model" in text for text in success_texts)

    @patch("evidence_engine.GeneticEvidenceOrchestrator.search_gene")
    def test_evidence_intelligence_tab3_section(self, mock_search):
        """Verifies Section 4 Multi-Source Evidence Intelligence renders cleanly and triggers queries."""
        from evidence_engine import GeneticEvidenceBundle, GenomeAssembly, GeneIdentity, ClinicalClassification, SourceStatus
        mock_bundle = GeneticEvidenceBundle(
            query_type="gene",
            query_term="BRCA1",
            target_assembly=GenomeAssembly.GRCh38,
            timestamp="2026-11-04T00:00:00Z",
            gene_identity=GeneIdentity(symbol="BRCA1", ensembl_gene_id="ENSG00000012048", assembly=GenomeAssembly.GRCh38),
            clinical_evidence=ClinicalClassification(primary_classification="Pathogenic", review_stars=3),
            source_statuses={"Ensembl": SourceStatus.AVAILABLE, "ClinVar": SourceStatus.AVAILABLE},
        )
        mock_search.return_value = mock_bundle

        self.at.run()
        assert not self.at.exception

        # Check section 4 header in markdown
        markdown_texts = " ".join([m.value for m in self.at.markdown])
        assert "Multi-Source Genetic Evidence Intelligence" in markdown_texts

        # Click "Fetch Evidence"
        btn_evidence = [b for b in self.at.button if "Fetch Evidence" in b.label]
        assert len(btn_evidence) == 1
        btn_evidence[0].click().run()
        assert not self.at.exception

        # Verify output rendered
        markdown_texts_after = " ".join([m.value for m in self.at.markdown])
        assert "Evidence Record: `BRCA1` (GRCh38)" in markdown_texts_after
        metric_labels = [m.label for m in self.at.metric]
        assert any("Gene Symbol" in lbl for lbl in metric_labels)
        assert any("Primary Classification" in lbl for lbl in metric_labels)

    @patch("evidence_engine.GeneticEvidenceOrchestrator.search_gene")
    def test_evidence_intelligence_gene_landscape_rendering(self, mock_search):
        """Verifies Task 7.1 gene-level variant landscape, constraint biological context, and ClinGen validity render."""
        from evidence_engine import (
            GeneticEvidenceBundle,
            GenomeAssembly,
            GeneIdentity,
            ClinVarGeneVariantLandscape,
            ClinicalClassification,
            PopulationFrequency,
            GeneDiseaseValidity,
            LiteratureReference,
            SourceStatus,
        )
        mock_bundle = GeneticEvidenceBundle(
            query_type="gene",
            query_term="BRCA1",
            target_assembly=GenomeAssembly.GRCh38,
            timestamp="2026-11-04T00:00:00Z",
            gene_identity=GeneIdentity(symbol="BRCA1", ensembl_gene_id="ENSG00000012048", assembly=GenomeAssembly.GRCh38),
            gene_variant_landscape=ClinVarGeneVariantLandscape(
                gene_symbol="BRCA1",
                total_variants_count=33500,
                variants=[
                    ClinicalClassification(
                        variation_id="12345",
                        title="NM_007294.4(BRCA1):c.5266dupC",
                        primary_classification="Pathogenic",
                        review_stars=2,
                    )
                ],
            ),
            population_frequency=PopulationFrequency(
                gene_constraint={"pLI": 0.0, "oe_lof_upper": 0.928, "is_pli_zero": True},
                constraint_notes="Adult-onset cancer predisposition genes do not exhibit severe depletion of LoF variants.",
            ),
            gene_disease_validity=[
                GeneDiseaseValidity(
                    gene_symbol="BRCA1",
                    disease_label="Hereditary breast and ovarian cancer syndrome",
                    classification="Definitive",
                    curation_panel="ClinGen Expert Panel",
                )
            ],
            publications=[
                LiteratureReference(
                    pmid="30209392",
                    title="Accurate classification of BRCA1 variants using saturation editing",
                    journal="Nature",
                    year=2018,
                    url="https://pubmed.ncbi.nlm.nih.gov/30209392/",
                )
            ],
            source_statuses={
                "ClinVar": SourceStatus.AVAILABLE,
                "ClinGen": SourceStatus.AVAILABLE,
                "Ensembl": SourceStatus.AVAILABLE,
                "gnomAD": SourceStatus.AVAILABLE,
                "PubMed": SourceStatus.AVAILABLE,
            },
            source_record_counts={"ClinVar": 33500, "ClinGen": 1, "Ensembl": 59, "gnomAD": 1, "PubMed": 1},
            source_completeness={"ClinVar": "Complete", "ClinGen": "Complete", "Ensembl": "Complete", "gnomAD": "Complete", "PubMed": "Complete"},
        )
        mock_search.return_value = mock_bundle

        self.at.run()
        assert not self.at.exception

        # Click "Fetch Evidence"
        btn_evidence = [b for b in self.at.button if "Fetch Evidence" in b.label]
        assert len(btn_evidence) == 1
        btn_evidence[0].click().run()
        assert not self.at.exception

        # Verify output rendered
        markdown_texts_after = " ".join([m.value for m in self.at.markdown])
        assert "Gene-Level Variant Landscape (NCBI ClinVar)" in markdown_texts_after
        metric_labels = [m.label for m in self.at.metric]
        assert any("Total ClinVar Variants for Gene" in lbl for lbl in metric_labels)

        # Verify biological context callout
        info_texts = " ".join([i.value for i in self.at.info])
        assert "Biological Constraint Context" in info_texts or "Allele-Centric Repository Notice" in info_texts

        # Verify ClinGen expert consensus banner
        success_texts = " ".join([s.value for s in self.at.success])
        assert "ClinGen Expert Consensus" in success_texts or "Live Available" in success_texts

    @patch("evidence_engine.GeneticEvidenceOrchestrator.search_variant")
    def test_evidence_intelligence_variant_rendering(self, mock_search):
        """Verifies Task 8.1 Variant Evidence Intelligence renders variant identity, VEP, in-silico, and ClinVar."""
        from evidence_engine import (
            GeneticEvidenceBundle,
            GenomeAssembly,
            VariantIdentity,
            VariantTranscriptAnnotation,
            ClinicalClassification,
            VariantPopulationFrequency,
            ComputationalEvidence,
            VariantEvidenceRecord,
            GeneDiseaseValidity,
            LiteratureReference,
            SourceStatus,
        )

        var_id = VariantIdentity(
            variant_id="rs28897743",
            chromosome="17",
            position=43044295,
            reference_allele="C",
            alternate_allele="dup",
            assembly=GenomeAssembly.GRCh38,
            gene_symbol="BRCA1",
            input_identifier="rs28897743",
            normalized_identifier="17-43044295-C-dup",
            associated_gene="BRCA1",
            normalization_source="Curated Benchmark Reference Snapshot",
            is_valid=True,
            is_ambiguous=False,
        )

        ce = ClinicalClassification(
            variation_id="17667",
            title="NM_007294.4(BRCA1):c.5266dupC",
            primary_classification="Pathogenic",
            review_stars=2,
            total_submissions=42,
            vcv_accession="VCV000017667",
        )

        vta = VariantTranscriptAnnotation(
            transcript_id="ENST00000357654",
            gene_symbol="BRCA1",
            consequence_terms=["frameshift_variant"],
            hgvs_c="c.5266dupC",
            hgvs_p="p.Gln1756ProfsTer74",
            is_canonical=True,
            is_mane_select=True,
        )

        vpf = VariantPopulationFrequency(
            allele_count=38,
            allele_number=251400,
            allele_frequency=0.000151,
            popmax_frequency=0.00142,
            popmax_population="Ashkenazi Jewish (asj)",
        )

        comp = [
            ComputationalEvidence(
                prediction_method="SIFT",
                prediction_output="deleterious",
                numerical_score=0.0,
                source="Ensembl VEP",
            ),
            ComputationalEvidence(
                prediction_method="HelixGuard-QNN",
                prediction_output="Synthetic Class 1 (Pathogenic-like)",
                numerical_score=0.942,
                source="Helix Guard Hybrid Quantum Neural Network",
            ),
        ]

        var_rec = VariantEvidenceRecord(
            variant_identity=var_id,
            clinical_evidence=ce,
            transcript_evidence=[vta],
            population_evidence=vpf,
            computational_evidence=comp,
            gene_disease_validity=[GeneDiseaseValidity(gene_symbol="BRCA1", disease_label="Hereditary breast cancer", classification="Definitive")],
            literature_evidence=[LiteratureReference(pmid="30093976", title="Saturation genome editing of BRCA1", variant_specific_relevance="Functional assay calibration")],
            source_statuses={
                "ClinVar": SourceStatus.AVAILABLE,
                "Ensembl": SourceStatus.AVAILABLE,
                "gnomAD": SourceStatus.AVAILABLE,
                "PubMed": SourceStatus.AVAILABLE,
                "ClinGen": SourceStatus.AVAILABLE,
            },
            source_record_counts={"ClinVar": 42, "Ensembl": 1, "gnomAD": 1, "PubMed": 1, "ClinGen": 1},
            source_completeness={"ClinVar": "Pathogenic", "Ensembl": "1 Transcripts", "gnomAD": "AF: 0.000151", "PubMed": "1 Citations", "ClinGen": "1 Gene Validities"},
        )

        mock_bundle = GeneticEvidenceBundle(
            query_type="variant",
            query_term="rs28897743",
            target_assembly=GenomeAssembly.GRCh38,
            timestamp="2026-11-04T00:00:00Z",
            variant_identity=var_id,
            clinical_evidence=ce,
            source_statuses=var_rec.source_statuses,
            source_record_counts=var_rec.source_record_counts,
            source_completeness=var_rec.source_completeness,
            variant_evidence_record=var_rec,
        )
        mock_search.return_value = mock_bundle

        self.at.run()
        assert not self.at.exception

        # Select Variant query type radio
        radios = [r for r in self.at.radio if "Evidence Target Type" in r.label]
        if radios:
            radios[0].set_value("Variant Identifier (rsID / UID)").run()

        # Click Fetch Evidence
        btn_evidence = [b for b in self.at.button if "Fetch Evidence" in b.label]
        if btn_evidence:
            btn_evidence[0].click().run()
        assert not self.at.exception

        # Verify Variant Identity Card and metrics
        markdown_texts_after = " ".join([m.value for m in self.at.markdown])
        assert "Variant Identity & Genomic Locus" in markdown_texts_after
        metric_labels = [m.label for m in self.at.metric]
        assert any("Normalized ID" in lbl for lbl in metric_labels)
        assert any("Ref / Alt Allele" in lbl for lbl in metric_labels)

        # Verify In-silico inferences and VEP sections
        assert "In-Silico Computational Inferences" in markdown_texts_after
        assert "Transcript Consequences" in markdown_texts_after


class TestBackendSecurityAndCredentials:
    def test_secret_masking(self):
        """Verifies secrets are masked and never returned in plaintext."""
        raw_token = "d1ID8jFQurqgily5rg7ILg3FlGy6OLmLOeOdJZCv4NHp"
        masked = mask_secret(raw_token)
        assert raw_token not in masked
        assert masked.startswith("d1ID")
        assert masked.endswith("NHp")
        assert "••••••••" in masked

        # Short and empty tokens
        assert mask_secret("") == "Unconfigured"
        assert mask_secret(None) == "Unconfigured"
        assert mask_secret("short") == "••••••••"

    def test_credentials_object_repr_security(self):
        """Verifies credentials object __repr__ and __str__ never expose raw token."""
        raw_secret = "secret_api_key_1234567890abcdef"
        creds = IBMQuantumCredentials(
            is_configured=True,
            source="Environment Variable",
            masked_token=mask_secret(raw_secret),
            masked_instance="Instance",
            _raw_token=raw_secret,
        )
        repr_str = repr(creds)
        str_str = str(creds)

        assert raw_secret not in repr_str, "Raw token leaked in __repr__!"
        assert raw_secret not in str_str, "Raw token leaked in __str__!"
        assert "masked_token" in repr_str

    def test_sanitization_removes_tokens_and_paths(self):
        """Verifies error/log sanitization redacts long tokens and file paths."""
        sensitive_msg = "Error connecting with token d1ID8jFQurqgily5rg7ILg3FlGy6OLmLOeOdJZCv4NHp at C:\\Users\\secret_user\\app.py"
        sanitized = sanitize_message(sensitive_msg)

        assert "d1ID8jFQurqgily5rg7ILg3FlGy6OLmLOeOdJZCv4NHp" not in sanitized
        assert "secret_user" not in sanitized
        assert "[REDACTED_SECRET]" in sanitized
        assert "<USER_HOME>" in sanitized

    def test_gitignore_contains_secret_patterns(self):
        """Verifies .gitignore excludes credentials, env files, and secrets."""
        gitignore_path = os.path.join(project_root, ".gitignore")
        assert os.path.exists(gitignore_path), "Root .gitignore must exist."

        with open(gitignore_path, "r", encoding="utf-8") as f:
            content = f.read()

        assert "*credentials*.txt" in content or "credentials" in content
        assert ".env" in content
        assert "*secret*" in content or "secret" in content

    def test_environment_variable_precedence(self, monkeypatch):
        """Verifies environment variables override local files."""
        fake_token = "test_env_token_98765432101234567890"
        monkeypatch.setenv("QISKIT_IBM_TOKEN", fake_token)
        creds = load_ibm_credentials(base_dir=helix_guard_dir)

        assert creds.is_configured
        assert creds.source == "Environment Variable"
        assert creds.get_token_for_client() == fake_token
        assert fake_token not in repr(creds)

    def test_missing_credentials_safe_defaults(self, monkeypatch):
        """Verifies missing credentials default safely to simulation without exceptions or leakage."""
        import tempfile
        monkeypatch.delenv("QISKIT_IBM_TOKEN", raising=False)
        monkeypatch.delenv("IBM_QUANTUM_API_KEY", raising=False)
        monkeypatch.delenv("IBM_QUANTUM_TOKEN", raising=False)
        monkeypatch.delenv("IBM_QUANTUM_INSTANCE", raising=False)

        empty_dir = tempfile.mkdtemp()
        creds = load_ibm_credentials(base_dir=empty_dir)

        assert creds.is_configured is False
        assert creds.source == "Unconfigured"
        assert creds.masked_token == "Unconfigured"
        assert creds.hardware_available is False
        assert "Simulation" in creds.execution_mode
        assert creds.get_token_for_client() is None

    def test_env_example_contains_only_placeholders(self):
        """Verifies .env.example files contain only non-sensitive template placeholders."""
        import re
        example_paths = [
            os.path.join(project_root, ".env.example"),
            os.path.join(helix_guard_dir, ".env.example"),
        ]
        for p in example_paths:
            assert os.path.exists(p), f".env.example must exist at {p}"
            with open(p, "r", encoding="utf-8") as f:
                content = f.read()
            # Assert placeholders present
            assert "your_ibm_quantum_api_key_here" in content
            assert "crn:v1:bluemix:public:quantum-computing:..." in content
            # Ensure no genuine 32+ character secrets exist
            for line in content.splitlines():
                if line.startswith("#") or not line.strip():
                    continue
                if "=" in line:
                    val = line.split("=", 1)[1].strip()
                    assert len(val) < 45 or "..." in val or "your_" in val, f"Suspected real secret in {p}: {line}"

    def test_credential_text_files_sanitized(self):
        """Verifies ibm credentials.txt contains zero plaintext API keys and directs to .env."""
        cred_file = os.path.join(helix_guard_dir, "ibm credentials.txt")
        assert os.path.exists(cred_file)
        with open(cred_file, "r", encoding="utf-8") as f:
            content = f.read()

        assert "deprecated and insecure" in content
        assert ".env" in content
        # Ensure no 32+ alphanumeric raw tokens are present
        long_tokens = re.findall(r"[A-Za-z0-9_\-]{32,}", content)
        assert len(long_tokens) == 0, f"Found unredacted tokens in credential text file: {long_tokens}"

    def test_credential_files_not_tracked_and_gitignored(self):
        """Verifies repository-level and nested .gitignore ignore all secret-bearing files."""
        for gitignore_path in [os.path.join(project_root, ".gitignore"), os.path.join(helix_guard_dir, ".gitignore")]:
            assert os.path.exists(gitignore_path), f"Missing {gitignore_path}"
            with open(gitignore_path, "r", encoding="utf-8") as f:
                content = f.read()
            assert "*credentials*.txt" in content
            assert ".env" in content
            assert "*secret*" in content
            assert "*.key" in content
            assert "*.token" in content

    def test_credential_values_masked_in_repr_and_str(self):
        """Verifies IBMQuantumCredentials masks raw keys in __repr__ and __str__ and never logs secrets."""
        dummy_secret = "sensitive_quantum_api_key_xyz1234567890abcdef"
        dummy_crn = "crn:v1:bluemix:public:quantum-computing:us-east:a/dummy:inst::"
        creds = IBMQuantumCredentials(
            is_configured=True,
            source="Test Environment",
            masked_token="sens••••cdef",
            masked_instance="crn:••••inst::",
            hardware_available=True,
            execution_mode="Hardware",
            _raw_token=dummy_secret,
            _raw_instance=dummy_crn,
        )
        repr_str = repr(creds)
        str_str = str(creds)
        assert dummy_secret not in repr_str
        assert dummy_crn not in repr_str
        assert dummy_secret not in str_str
        assert dummy_crn not in str_str
        assert "sens••••cdef" in repr_str

    def test_ui_provenance_accuracy_elements(self):
        """Verifies Streamlit app.py contains UI provenance badges and audit disclosures."""
        app_file = os.path.join(helix_guard_dir, "app.py")
        with open(app_file, "r", encoding="utf-8") as f:
            app_code = f.read()

        # Provenance badge for Local Reference Data
        assert "Local Reference Data" in app_code
        # Explicit provenance disclosure for local reference curations
        assert "Provenance Disclosure" in app_code
        # Explicit Data Origin column distinguishing live vs cached vs local snapshot
        assert "Data Origin" in app_code
        assert "🟣 Local Reference Snapshot" in app_code
        assert "🔵 Validated Cache" in app_code
        assert "🟢 Live Request" in app_code
