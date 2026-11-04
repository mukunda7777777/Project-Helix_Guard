"""
Unit and integration tests for HELIX GUARD Epistasis Engine.
Validates compound heterozygosity, cis/trans phasing, and non-additive epistatic interactions.
"""

import pytest
from epistasis_engine import (
    EpistasisEngine,
    GenotypePhase,
    InheritanceMode,
    VariantLocus,
    MultiVariantConflictReport,
)


@pytest.fixture
def engine():
    return EpistasisEngine()


def test_epistasis_engine_initialization(engine):
    assert engine is not None
    assert "CFTR" in engine.gene_inheritance
    assert engine.gene_inheritance["CFTR"] == InheritanceMode.AUTOSOMAL_RECESSIVE
    assert engine.gene_inheritance["BRCA1"] == InheritanceMode.AUTOSOMAL_DOMINANT


def test_phasing_evaluation_homozygous(engine):
    v1 = VariantLocus(
        variant_id="rs121908752",
        gene_symbol="CFTR",
        chromosome="chr7",
        position=117559590,
        ref_allele="CTT",
        alt_allele="",
        pathogenicity="Pathogenic",
        zygosity="HOMOZYGOUS",
    )
    v2 = VariantLocus(
        variant_id="rs75527207",
        gene_symbol="CFTR",
        chromosome="chr7",
        position=117559600,
        ref_allele="G",
        alt_allele="A",
        pathogenicity="VUS",
        zygosity="HETEROZYGOUS",
    )
    phase = engine.evaluate_phasing(v1, v2)
    # Since v1 is homozygous, both alleles carry disruption
    assert phase == GenotypePhase.TRANS


def test_phasing_evaluation_explicit(engine):
    v1 = VariantLocus(
        variant_id="rs121908752",
        gene_symbol="CFTR",
        chromosome="chr7",
        position=117559590,
        ref_allele="CTT",
        alt_allele="",
        pathogenicity="Pathogenic",
    )
    v2 = VariantLocus(
        variant_id="rs75527207",
        gene_symbol="CFTR",
        chromosome="chr7",
        position=117559600,
        ref_allele="G",
        alt_allele="A",
        pathogenicity="Pathogenic",
    )
    assert engine.evaluate_phasing(v1, v2, explicit_phase=GenotypePhase.CIS) == GenotypePhase.CIS
    assert engine.evaluate_phasing(v1, v2, explicit_phase=GenotypePhase.TRANS) == GenotypePhase.TRANS


def test_compound_heterozygosity_in_trans(engine):
    # Two pathogenic CFTR variants in TRANS
    v1 = VariantLocus(
        variant_id="rs121908752",
        gene_symbol="CFTR",
        chromosome="chr7",
        position=117559590,
        ref_allele="CTT",
        alt_allele="",
        pathogenicity="Pathogenic",
    )
    v2 = VariantLocus(
        variant_id="rs75527207",
        gene_symbol="CFTR",
        chromosome="chr7",
        position=117559600,
        ref_allele="G",
        alt_allele="A",
        pathogenicity="Pathogenic",
    )
    phase_map = {("rs121908752", "rs75527207"): GenotypePhase.TRANS}
    results = engine.detect_compound_heterozygosity([v1, v2], phase_map=phase_map)

    assert len(results) == 1
    comp = results[0]
    assert comp.is_compound_heterozygous is True
    assert comp.phase == GenotypePhase.TRANS
    assert comp.clinical_risk == "HIGH_RECESSIVE_RISK"
    assert "Biallelic disruption" in comp.explanation


def test_compound_heterozygosity_in_cis(engine):
    # Two pathogenic CFTR variants on the SAME allele (CIS)
    v1 = VariantLocus(
        variant_id="rs121908752",
        gene_symbol="CFTR",
        chromosome="chr7",
        position=117559590,
        ref_allele="CTT",
        alt_allele="",
        pathogenicity="Pathogenic",
    )
    v2 = VariantLocus(
        variant_id="rs75527207",
        gene_symbol="CFTR",
        chromosome="chr7",
        position=117559600,
        ref_allele="G",
        alt_allele="A",
        pathogenicity="Pathogenic",
    )
    phase_map = {("rs121908752", "rs75527207"): GenotypePhase.CIS}
    results = engine.detect_compound_heterozygosity([v1, v2], phase_map=phase_map)

    assert len(results) == 1
    comp = results[0]
    assert comp.is_compound_heterozygous is False
    assert comp.phase == GenotypePhase.CIS
    assert comp.clinical_risk == "CARRIER_ONLY"
    assert "One functional wild-type allele remains" in comp.explanation


def test_autosomal_dominant_no_compound_heterozygote(engine):
    # Two BRCA1 variants should NOT trigger compound heterozygosity evaluation
    v1 = VariantLocus(
        variant_id="rs80357906",
        gene_symbol="BRCA1",
        chromosome="chr17",
        position=43044295,
        ref_allele="C",
        alt_allele="T",
        pathogenicity="Pathogenic",
    )
    v2 = VariantLocus(
        variant_id="rs80357714",
        gene_symbol="BRCA1",
        chromosome="chr17",
        position=43045000,
        ref_allele="A",
        alt_allele="G",
        pathogenicity="Pathogenic",
    )
    results = engine.detect_compound_heterozygosity([v1, v2])
    assert len(results) == 0


def test_epistatic_interactions_synthetic_lethality(engine):
    # TP53 + BRCA1
    v1 = VariantLocus(
        variant_id="rs1042522",
        gene_symbol="TP53",
        chromosome="chr17",
        position=7676154,
        ref_allele="C",
        alt_allele="G",
        pathogenicity="Pathogenic",
    )
    v2 = VariantLocus(
        variant_id="rs80357906",
        gene_symbol="BRCA1",
        chromosome="chr17",
        position=43044295,
        ref_allele="C",
        alt_allele="T",
        pathogenicity="Pathogenic",
    )
    interactions = engine.detect_epistatic_interactions([v1, v2])
    assert len(interactions) == 1
    assert interactions[0].interaction_type == "SYNTHETIC_LETHALITY"
    assert interactions[0].severity_delta == 0.35


def test_multi_variant_conflict_report(engine):
    v1 = VariantLocus(
        variant_id="rs121908752",
        gene_symbol="CFTR",
        chromosome="chr7",
        position=117559590,
        ref_allele="CTT",
        alt_allele="",
        pathogenicity="Pathogenic",
    )
    v2 = VariantLocus(
        variant_id="rs75527207",
        gene_symbol="CFTR",
        chromosome="chr7",
        position=117559600,
        ref_allele="G",
        alt_allele="A",
        pathogenicity="Pathogenic",
    )
    v3 = VariantLocus(
        variant_id="rs1042522",
        gene_symbol="TP53",
        chromosome="chr17",
        position=7676154,
        ref_allele="C",
        alt_allele="G",
        pathogenicity="Pathogenic",
    )
    v4 = VariantLocus(
        variant_id="rs80357906",
        gene_symbol="BRCA1",
        chromosome="chr17",
        position=43044295,
        ref_allele="C",
        alt_allele="T",
        pathogenicity="Pathogenic",
    )

    phase_map = {("rs121908752", "rs75527207"): GenotypePhase.TRANS}
    base_risks = {"CFTR": 0.60, "TP53": 0.50, "BRCA1": 0.50}

    report = engine.analyze_multi_variant_profile(
        variants=[v1, v2, v3, v4],
        phase_map=phase_map,
        base_risks=base_risks
    )

    assert isinstance(report, MultiVariantConflictReport)
    assert len(report.compound_heterozygotes) == 1
    assert len(report.epistatic_interactions) == 1
    assert report.aggregate_disease_risks["CFTR"] >= 0.95
    assert report.aggregate_disease_risks["TP53"] > 0.50
    assert report.aggregate_disease_risks["BRCA1"] > 0.50
    assert len(report.conflicts_identified) >= 2

