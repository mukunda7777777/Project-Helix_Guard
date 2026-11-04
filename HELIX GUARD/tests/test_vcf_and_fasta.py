"""
Unit and integration tests for HELIX GUARD VCF Pipeline and FASTA Generator.
Validates multi-variant VCF parsing, coordinate gene mapping, and FASTA export formatting.
"""

import pytest
from vcf_pipeline import VCFPipeline
from fasta_generator import FASTAGenerator
from correction_engine import InSilicoCorrectionEngine


@pytest.fixture
def vcf_pipeline():
    return VCFPipeline()


@pytest.fixture
def fasta_generator():
    return FASTAGenerator()


def test_vcf_parsing_preset_cftr_compound_het(vcf_pipeline):
    vcf_text = vcf_pipeline.get_sample_preset_vcf("cftr_compound_het")
    variants = vcf_pipeline.parse_vcf_text(vcf_text)

    assert len(variants) == 2
    assert variants[0].variant_id == "rs121908752"
    assert variants[0].gene_symbol == "CFTR"
    assert variants[0].pathogenicity == "Pathogenic"
    assert variants[1].variant_id == "rs75527207"
    assert variants[1].gene_symbol == "CFTR"


def test_vcf_parsing_preset_5gene_panel(vcf_pipeline):
    vcf_text = vcf_pipeline.get_sample_preset_vcf("complete_5gene_panel")
    variants = vcf_pipeline.parse_vcf_text(vcf_text)

    assert len(variants) == 5
    genes = [v.gene_symbol for v in variants]
    assert "BRCA1" in genes
    assert "HBB" in genes
    assert "CFTR" in genes
    assert "HEXA" in genes
    assert "DMD" in genes


def test_fasta_generation_and_headers(fasta_generator):
    seq = "ATCG" * 25
    fasta_out = fasta_generator.generate_fasta(
        sequence=seq,
        sample_id="PATIENT_001",
        assembly="GRCh38"
    )

    assert fasta_out.startswith(">HELIX_GUARD|PATIENT_001|ASSEMBLY=GRCh38")
    assert "STATUS=IN_SILICO_VALIDATED" in fasta_out
    assert "ATCG" in fasta_out


def test_clinical_report_markdown_generation(fasta_generator):
    corr_engine = InSilicoCorrectionEngine()
    vcf_pipe = VCFPipeline()
    variants = vcf_pipe.parse_vcf_text(vcf_pipe.get_sample_preset_vcf("complete_5gene_panel"))
    result = corr_engine.run_pipeline(variants=variants, include_beneficial_suggestion=True)

    report_md = fasta_generator.generate_clinical_markdown_report(
        sample_id="TEST_SAMPLE_001",
        edit_history=result.edit_history,
        initial_risks=result.initial_risk_profile,
        final_risks=result.final_risk_profile,
        beneficial_suggestions=result.beneficial_suggestions
    )

    assert "HELIX GUARD — CLINICAL IN-SILICO CORRECTION REPORT" in report_md
    assert "Sickle Cell Anemia" in report_md
    assert "CCR5" in report_md
    assert "RESTORED TO LOW RISK" in report_md

