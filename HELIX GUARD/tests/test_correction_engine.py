"""
Unit and integration tests for HELIX GUARD In-Silico Correction Engine.
Validates sequential priority-based screening, repair strategy generation,
cross-edit conflict detection, and beneficial variant trade-off modeling.
"""

import pytest
from correction_engine import (
    InSilicoCorrectionEngine,
    CorrectionStrategy,
    EditingModality,
    ProposedEdit,
    CorrectionPipelineResult,
    PRIORITY_PANEL,
)
from epistasis_engine import VariantLocus


@pytest.fixture
def correction_engine():
    return InSilicoCorrectionEngine()


def test_priority_panel_structure(correction_engine):
    panel = correction_engine.priority_panel
    assert len(panel) == 5
    assert panel[0]["gene"] == "BRCA1"
    assert panel[1]["gene"] == "HBB"
    assert panel[2]["gene"] == "CFTR"
    assert panel[3]["gene"] == "HEXA"
    assert panel[4]["gene"] == "DMD"


def test_strategy_determination_snv(correction_engine):
    # HBB Sickle cell point substitution (A > T)
    var = VariantLocus(
        variant_id="rs334",
        gene_symbol="HBB",
        chromosome="chr11",
        position=5227002,
        ref_allele="A",
        alt_allele="T",
        pathogenicity="Pathogenic",
    )
    strategy, modality = correction_engine.determine_strategy(var)
    assert strategy == CorrectionStrategy.SUBSTITUTION_REPAIR
    assert modality == EditingModality.BASE_EDITING


def test_strategy_determination_deletion(correction_engine):
    # CFTR deltaF508 (CTT deletion)
    var = VariantLocus(
        variant_id="rs121908752",
        gene_symbol="CFTR",
        chromosome="chr7",
        position=117559590,
        ref_allele="CTT",
        alt_allele="",
        pathogenicity="Pathogenic",
    )
    strategy, modality = correction_engine.determine_strategy(var)
    assert strategy == CorrectionStrategy.INDEL_DELETION_REPAIR
    assert modality == EditingModality.PRIME_EDITING


def test_strategy_determination_insertion(correction_engine):
    # HEXA 4bp insertion (c.1274_1277dupTATC)
    var = VariantLocus(
        variant_id="rs387906309",
        gene_symbol="HEXA",
        chromosome="chr15",
        position=72346580,
        ref_allele="",
        alt_allele="TATC",
        pathogenicity="Pathogenic",
    )
    strategy, modality = correction_engine.determine_strategy(var)
    assert strategy == CorrectionStrategy.INDEL_INSERTION_REPAIR
    assert modality == EditingModality.PRIME_EDITING


def test_strategy_determination_dmd(correction_engine):
    # DMD frame restoration
    var = VariantLocus(
        variant_id="rs121913527",
        gene_symbol="DMD",
        chromosome="chrX",
        position=31165000,
        ref_allele="A",
        alt_allele="C",
        pathogenicity="Pathogenic",
    )
    strategy, modality = correction_engine.determine_strategy(var)
    assert strategy == CorrectionStrategy.FRAME_RESTORATION
    assert modality == EditingModality.ANTISENSE_OLIGO


def test_generate_correction(correction_engine):
    var = VariantLocus(
        variant_id="rs334",
        gene_symbol="HBB",
        chromosome="chr11",
        position=5227002,
        ref_allele="A",
        alt_allele="T",
        pathogenicity="Pathogenic",
    )
    edit = correction_engine.generate_correction(var)
    assert isinstance(edit, ProposedEdit)
    assert edit.gene_symbol == "HBB"
    assert edit.original_allele == "T"
    assert edit.corrected_allele == "A"
    assert edit.predicted_efficiency > 0.80
    assert edit.guide_rna_candidate is not None


def test_sequential_pipeline_execution(correction_engine):
    # Multi-variant panel run
    variants = [
        VariantLocus("rs334", "HBB", "chr11", 5227002, "A", "T", "Pathogenic"),
        VariantLocus("rs121908752", "CFTR", "chr7", 117559590, "CTT", "", "Pathogenic"),
    ]
    result = correction_engine.run_pipeline(
        variants=variants,
        initial_sequence="ATCG" * 50,
        include_beneficial_suggestion=True
    )

    assert isinstance(result, CorrectionPipelineResult)
    assert len(result.edit_history) == 2
    # Verify HBB is screened and edited according to priority order
    assert result.initial_risk_profile["HBB"] >= 0.90
    assert result.initial_risk_profile["CFTR"] >= 0.90
    assert result.final_risk_profile["HBB"] < 0.20
    assert result.final_risk_profile["CFTR"] < 0.20
    assert result.sequence_modified is True
    # Beneficial suggestion
    assert len(result.beneficial_suggestions) >= 1
    assert result.beneficial_suggestions[0].gene_symbol == "CCR5"
    assert len(result.beneficial_suggestions[0].documented_trade_offs) >= 2

