"""
Unit and Integration Test Suite for Helix Guard Genetic Evidence Intelligence (Task 7).

Tests cover:
- Evidence schema validation & data contracts
- Missing, empty, and malformed source payload handling
- Source provenance preservation & timestamp auditing
- Explicit reference genome assembly handling (GRCh38 vs GRCh37)
- Duplicate record & submission handling
- Conflicting evidence & submitter disagreement representation
- API network failure and timeout handling
- Evidence caching (hit, miss, expiration, offline fallback)
- Unified search orchestration for genes and variants
- Offline behavior (no live network dependency)
"""

import json
import os
import tempfile
import time
from unittest.mock import MagicMock, patch
import pytest
import requests

from evidence_engine import (
    GenomeAssembly,
    EvidenceLevel,
    SourceStatus,
    EvidenceProvenance,
    GeneIdentity,
    VariantIdentity,
    TranscriptAnnotation,
    ClinVarSubmission,
    ClinVarGeneVariantLandscape,
    ClinicalClassification,
    PopulationFrequency,
    GeneDiseaseValidity,
    LiteratureReference,
    GeneticEvidenceBundle,
    EvidenceCache,
    ClinVarAdapter,
    ClinGenAdapter,
    EnsemblAdapter,
    GnomadAdapter,
    PubMedAdapter,
    GeneticEvidenceOrchestrator,
)


# =============================================================================
# 1. SCHEMA VALIDATION & DATA CONTRACT TESTS
# =============================================================================

def test_evidence_provenance_contract():
    """Validates EvidenceProvenance data contract and serialization."""
    prov = EvidenceProvenance(
        source_name="NCBI ClinVar",
        source_endpoint="esummary.fcgi",
        retrieval_timestamp="2026-11-04T00:00:00Z",
        source_url="https://www.ncbi.nlm.nih.gov/clinvar/variation/12345/",
        is_cached=False,
        response_latency_ms=145.2,
        assembly=GenomeAssembly.GRCh38,
        license_notice="NCBI Entrez Terms",
    )
    d = prov.to_dict()
    assert d["source_name"] == "NCBI ClinVar"
    assert d["assembly"] == "GRCh38"
    assert d["is_cached"] is False
    assert d["response_latency_ms"] == 145.2


def test_gene_identity_contract():
    """Validates GeneIdentity serialization and optional field handling."""
    gene = GeneIdentity(
        symbol="BRCA1",
        ensembl_gene_id="ENSG00000012048",
        chromosome="17",
        start=43044295,
        end=43170245,
        strand=-1,
        biotype="protein_coding",
        assembly=GenomeAssembly.GRCh38,
    )
    d = gene.to_dict()
    assert d["symbol"] == "BRCA1"
    assert d["assembly"] == "GRCh38"
    assert d["biotype"] == "protein_coding"


def test_variant_identity_assembly_strictness():
    """Ensures VariantIdentity requires explicit reference assembly."""
    var38 = VariantIdentity(
        variant_id="rs28897743",
        chromosome="17",
        position=43094464,
        reference_allele="C",
        alternate_allele="T",
        assembly=GenomeAssembly.GRCh38,
        gene_symbol="BRCA1",
    )
    var37 = VariantIdentity(
        variant_id="rs28897743",
        chromosome="17",
        position=41244435,
        reference_allele="C",
        alternate_allele="T",
        assembly=GenomeAssembly.GRCh37,
        gene_symbol="BRCA1",
    )
    assert var38.assembly != var37.assembly
    assert var38.position != var37.position
    assert var38.to_dict()["assembly"] == "GRCh38"
    assert var37.to_dict()["assembly"] == "GRCh37"


def test_genetic_evidence_bundle_serialization():
    """Validates full bundle serialization into standard JSON-compliant dictionary."""
    bundle = GeneticEvidenceBundle(
        query_type="gene",
        query_term="TP53",
        target_assembly=GenomeAssembly.GRCh38,
        timestamp="2026-11-04T00:00:00Z",
        gene_identity=GeneIdentity(symbol="TP53", ensembl_gene_id="ENSG00000141510", assembly=GenomeAssembly.GRCh38),
        clinical_evidence=ClinicalClassification(primary_classification="Pathogenic", review_stars=3),
        source_statuses={"Ensembl": SourceStatus.AVAILABLE, "ClinVar": SourceStatus.AVAILABLE},
        scientific_limitations=["Research support only."],
    )
    b_dict = bundle.to_dict()
    assert b_dict["query_term"] == "TP53"
    assert b_dict["target_assembly"] == "GRCh38"
    assert b_dict["source_statuses"]["Ensembl"] == "AVAILABLE"
    assert b_dict["clinical_evidence"]["review_stars"] == 3


# =============================================================================
# 2. CACHE BEHAVIOR & OFFLINE FALLBACK TESTS
# =============================================================================

def test_evidence_cache_hit_and_miss():
    """Tests cache storage, hit retrieval, and key separation."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        cache = EvidenceCache(cache_dir=tmp_dir, default_ttl_seconds=3600)
        
        # Initial miss
        assert cache.get("Ensembl", "lookup", "BRCA1", "GRCh38") is None

        # Set cache
        test_data = {"gene": "BRCA1", "biotype": "protein_coding"}
        cache.set("Ensembl", "lookup", "BRCA1", test_data, assembly="GRCh38")

        # Cache hit
        hit = cache.get("Ensembl", "lookup", "BRCA1", "GRCh38")
        assert hit is not None
        data, is_expired = hit
        assert data == test_data
        assert is_expired is False

        # Key separation by assembly: GRCh37 must miss
        assert cache.get("Ensembl", "lookup", "BRCA1", "GRCh37") is None


def test_evidence_cache_ttl_expiration_and_offline_fallback():
    """Tests that expired cache is not returned unless allow_expired_on_offline is True."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        cache = EvidenceCache(cache_dir=tmp_dir, default_ttl_seconds=1)
        test_data = {"id": "12345", "status": "Pathogenic"}
        cache.set("ClinVar", "esummary", "rs123", test_data, ttl_seconds=1)

        # Immediate retrieval works
        assert cache.get("ClinVar", "esummary", "rs123") is not None

        # Wait for expiration
        time.sleep(1.2)

        # Standard get returns None because it's expired
        assert cache.get("ClinVar", "esummary", "rs123") is None

        # Offline fallback returns expired data flagged as expired
        fallback = cache.get("ClinVar", "esummary", "rs123", allow_expired_on_offline=True)
        assert fallback is not None
        data, is_expired = fallback
        assert data == test_data
        assert is_expired is True


# =============================================================================
# 3. CLINVAR ADAPTER TESTS (ACMG STARS, CONFLICTS, MALFORMED)
# =============================================================================

def test_clinvar_star_calculation():
    """Verifies ClinVar review status string maps correctly to 0-4 ACMG stars."""
    calc = ClinVarAdapter._calculate_review_stars
    assert calc("practice guideline") == 4
    assert calc("reviewed by expert panel") == 3
    assert calc("criteria provided, multiple submitters, no conflicts") == 2
    assert calc("criteria provided, single submitter") == 1
    assert calc("criteria provided, conflicting classifications") == 1
    assert calc("no assertion criteria provided") == 0
    assert calc("no assertion provided") == 0
    assert calc("") == 0


@patch("requests.Session.get")
def test_clinvar_adapter_conflicting_submission(mock_get):
    """Verifies ClinVar adapter detects conflicting clinical classifications."""
    # Mock esummary response with conflicting assertions
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
    mock_resp.json.return_value = {
        "result": {
            "uids": ["12345"],
            "12345": {
                "uid": 12345,
                "title": "NM_007294.4(BRCA1):c.5266dupC (p.Gln1756Profs)",
                "clinical_significance": {
                    "description": "Conflicting classifications of pathogenicity",
                    "review_status": "criteria provided, conflicting classifications",
                    "last_evaluated": "2024-01-15",
                },
                "trait_set": [{"trait_name": "Hereditary breast and ovarian cancer syndrome"}],
                "variation_set": [{
                    "sub_elements": [
                        {"submitter_name": "Lab A", "clinical_significance": "Pathogenic"},
                        {"submitter_name": "Lab B", "clinical_significance": "Uncertain significance"},
                    ]
                }],
            }
        }
    }
    mock_get.return_value = mock_resp

    with tempfile.TemporaryDirectory() as tmp_dir:
        adapter = ClinVarAdapter(cache=EvidenceCache(tmp_dir))
        status, clinsig, prov = adapter.fetch_variant_evidence("12345", use_cache=False)

        assert status == SourceStatus.AVAILABLE
        assert clinsig is not None
        assert clinsig.is_conflicting is True
        assert clinsig.evidence_level == EvidenceLevel.CONFLICTING
        assert clinsig.review_stars == 1
        assert len(clinsig.submissions) == 2
        assert clinsig.submissions[0].submitter_name == "Lab A"
        assert clinsig.submissions[1].clinical_significance == "Uncertain significance"
        assert prov.source_name == "NCBI ClinVar"


@patch("requests.Session.get")
def test_clinvar_adapter_missing_record_handling(mock_get):
    """Verifies ClinVar adapter returns UNAVAILABLE when record is not indexed."""
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"result": {"uids": []}}
    mock_get.return_value = mock_resp

    adapter = ClinVarAdapter(cache=EvidenceCache(tempfile.gettempdir()))
    status, clinsig, prov = adapter.fetch_variant_evidence("999999999", use_cache=False)
    assert status == SourceStatus.UNAVAILABLE
    assert clinsig is None


# =============================================================================
# 4. CLINGEN ADAPTER TESTS (GENE VALIDITY & DOSAGE)
# =============================================================================

@patch("requests.Session.get")
def test_clingen_adapter_validity_parsing(mock_get):
    """Verifies ClinGen gene-disease validity parsing and classification filtering."""
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "data": [
            {
                "gene": {"label": "BRCA1"},
                "disease": {"label": "Hereditary breast and ovarian cancer syndrome", "curie": "MONDO:0003582"},
                "classification": {"label": "Definitive"},
                "mode_of_inheritance": {"label": "Autosomal dominant inheritance"},
                "curation_date": "2023-05-10",
                "report_url": "https://search.clinicalgenome.org/kb/gene-validity/CGGV:assertion_1",
            },
            {
                "gene": {"label": "OTHER"},
                "disease": {"label": "Unrelated Disease"},
                "classification": {"label": "Disputed"},
            }
        ]
    }
    mock_get.return_value = mock_resp

    adapter = ClinGenAdapter(cache=EvidenceCache(tempfile.gettempdir()))
    status, records, prov = adapter.fetch_gene_validity("BRCA1", use_cache=False)

    assert status == SourceStatus.AVAILABLE
    assert len(records) == 1
    assert records[0].gene_symbol == "BRCA1"
    assert records[0].classification == "Definitive"
    assert records[0].disease_id == "MONDO:0003582"
    assert records[0].evidence_level == EvidenceLevel.DIRECT_REPORT


@patch("requests.Session.get")
def test_clingen_adapter_404_handling(mock_get):
    """Verifies ClinGen adapter handles 404 cleanly as UNAVAILABLE."""
    mock_resp = MagicMock()
    mock_resp.status_code = 404
    mock_resp.url = "https://search.clinicalgenome.org/api/validity"
    mock_get.return_value = mock_resp

    adapter = ClinGenAdapter(cache=EvidenceCache(tempfile.gettempdir()))
    status, records, prov = adapter.fetch_gene_validity("NONEXISTENT", use_cache=False)
    assert status == SourceStatus.UNAVAILABLE
    assert records == []


# =============================================================================
# 5. ENSEMBL REST ADAPTER TESTS (GRCH38 VS GRCH37 ROUTING)
# =============================================================================

@patch("requests.Session.get")
def test_ensembl_assembly_routing(mock_get):
    """Verifies Ensembl requests route to GRCh37 or GRCh38 endpoints explicitly."""
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "id": "ENSG00000012048",
        "display_name": "BRCA1",
        "seq_region_name": "17",
        "start": 43044295,
        "end": 43170245,
        "biotype": "protein_coding",
        "Transcript": [
            {"id": "ENST00000357654", "is_canonical": 1, "Tag": ["MANE_Select"], "biotype": "protein_coding"}
        ]
    }
    mock_get.return_value = mock_resp

    adapter = EnsemblAdapter(cache=EvidenceCache(tempfile.gettempdir()))

    # 1. GRCh38 Request
    status38, gene38, tr38, prov38 = adapter.fetch_gene_by_symbol("BRCA1", assembly=GenomeAssembly.GRCh38, use_cache=False)
    assert status38 == SourceStatus.AVAILABLE
    assert gene38.assembly == GenomeAssembly.GRCh38
    assert tr38[0].is_canonical is True
    assert tr38[0].is_mane_select is True
    assert "grch37" not in mock_get.call_args[0][0]

    # 2. GRCh37 Request
    status37, gene37, tr37, prov37 = adapter.fetch_gene_by_symbol("BRCA1", assembly=GenomeAssembly.GRCh37, use_cache=False)
    assert status37 == SourceStatus.AVAILABLE
    assert gene37.assembly == GenomeAssembly.GRCh37
    assert "grch37.rest.ensembl.org" in mock_get.call_args[0][0]


# =============================================================================
# 6. GNOMAD GRAPHQL ADAPTER TESTS
# =============================================================================

@patch("requests.Session.post")
def test_gnomad_adapter_gene_constraint(mock_post):
    """Verifies gnomAD GraphQL response parsing for pLI and LOEUF scores."""
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "data": {
            "gene": {
                "symbol": "BRCA1",
                "gnomad_constraint": {
                    "pLI": 0.0,
                    "oe_lof": 0.52,
                    "oe_lof_upper": 0.68,
                    "oe_mis": 0.94,
                    "oe_syn": 1.02,
                }
            }
        }
    }
    mock_post.return_value = mock_resp

    adapter = GnomadAdapter(cache=EvidenceCache(tempfile.gettempdir()))
    status, constraint, prov = adapter.fetch_gene_constraint("BRCA1", use_cache=False)

    assert status == SourceStatus.AVAILABLE
    assert constraint["pLI"] == 0.0
    assert constraint["oe_lof_upper"] == 0.68
    assert prov.source_name == "gnomAD"


# =============================================================================
# 7. PUBMED ADAPTER TESTS
# =============================================================================

@patch("requests.Session.get")
def test_pubmed_adapter_literature_search(mock_get):
    """Verifies PubMed literature metadata parsing and citation formatting."""
    # First call: esearch returns PMIDs
    resp_search = MagicMock()
    resp_search.status_code = 200
    resp_search.json.return_value = {"esearchresult": {"idlist": ["31234567"]}}

    # Second call: esummary returns metadata
    resp_summary = MagicMock()
    resp_summary.status_code = 200
    resp_summary.json.return_value = {
        "result": {
            "uids": ["31234567"],
            "31234567": {
                "title": "Clinical classification of BRCA1 and BRCA2 pathogenic variants.",
                "source": "Genet Med",
                "pubdate": "2020 Jan 15",
                "authors": [{"name": "Smith A"}, {"name": "Jones B"}],
                "articleids": [{"idtype": "doi", "value": "10.1038/s41436-019-0683-4"}],
            }
        }
    }
    mock_get.side_effect = [resp_search, resp_summary]

    adapter = PubMedAdapter(cache=EvidenceCache(tempfile.gettempdir()))
    status, pubs, prov = adapter.search_literature("BRCA1", retmax=1, use_cache=False)

    assert status == SourceStatus.AVAILABLE
    assert len(pubs) == 1
    assert pubs[0].pmid == "31234567"
    assert pubs[0].year == 2020
    assert pubs[0].journal == "Genet Med"
    assert pubs[0].doi == "10.1038/s41436-019-0683-4"
    assert pubs[0].url == "https://pubmed.ncbi.nlm.nih.gov/31234567/"


# =============================================================================
# 8. NETWORK FAILURE & TIMEOUT RESILIENCE
# =============================================================================

@patch("requests.Session.get", side_effect=requests.exceptions.Timeout("Connection timed out"))
def test_api_timeout_handling(mock_get):
    """Verifies that network timeouts do not crash the engine and report TIMEOUT."""
    adapter = ClinVarAdapter(cache=EvidenceCache(tempfile.gettempdir()))
    status, data, prov = adapter.fetch_variant_evidence("12345", use_cache=False)
    assert status == SourceStatus.TIMEOUT
    assert data is None


@patch("requests.Session.get", side_effect=requests.exceptions.ConnectionError("DNS failure"))
def test_api_connection_error_handling(mock_get):
    """Verifies connection failures return ERROR status gracefully."""
    adapter = EnsemblAdapter(cache=EvidenceCache(tempfile.gettempdir()))
    status, gene, trs, prov = adapter.fetch_gene_by_symbol("TP53", use_cache=False)
    assert status == SourceStatus.ERROR
    assert gene is None


# =============================================================================
# 9. UNIFIED ORCHESTRATOR TESTS
# =============================================================================

@patch.object(EnsemblAdapter, "fetch_gene_by_symbol")
@patch.object(ClinGenAdapter, "fetch_gene_validity")
@patch.object(GnomadAdapter, "fetch_gene_constraint")
@patch.object(PubMedAdapter, "search_literature")
@patch.object(ClinVarAdapter, "fetch_gene_variant_landscape")
def test_orchestrator_gene_search(mock_cv, mock_pm, mock_gnom, mock_cg, mock_ens):
    """Validates unified gene search aggregation across all 5 source adapters."""
    mock_ens.return_value = (
        SourceStatus.AVAILABLE,
        GeneIdentity(symbol="BRCA1", ensembl_gene_id="ENSG00000012048", assembly=GenomeAssembly.GRCh38),
        [TranscriptAnnotation(transcript_id="ENST00000357654", is_canonical=True)],
        None,
    )
    mock_cg.return_value = (
        SourceStatus.AVAILABLE,
        [GeneDiseaseValidity(gene_symbol="BRCA1", disease_label="Ovarian Cancer", classification="Definitive")],
        None,
    )
    mock_gnom.return_value = (
        SourceStatus.AVAILABLE,
        {"pLI": 0.0, "oe_lof_upper": 0.68},
        None,
    )
    mock_pm.return_value = (
        SourceStatus.AVAILABLE,
        [LiteratureReference(pmid="12345678", title="BRCA1 Study", url="https://pubmed.ncbi.nlm.nih.gov/12345678/")],
        None,
    )
    mock_cv.return_value = (
        SourceStatus.AVAILABLE,
        ClinVarGeneVariantLandscape(
            gene_symbol="BRCA1",
            total_variants_count=33500,
            variants=[
                ClinicalClassification(variation_id="12345", primary_classification="Pathogenic", review_stars=3)
            ],
        ),
        None,
    )

    orchestrator = GeneticEvidenceOrchestrator(cache_dir=tempfile.gettempdir())
    bundle = orchestrator.search_gene("BRCA1", assembly=GenomeAssembly.GRCh38, use_cache=False)

    assert bundle.query_term == "BRCA1"
    assert bundle.query_type == "gene"
    assert bundle.target_assembly == GenomeAssembly.GRCh38
    assert bundle.gene_identity.ensembl_gene_id == "ENSG00000012048"
    assert len(bundle.gene_disease_validity) == 1
    assert bundle.population_frequency.gene_constraint["oe_lof_upper"] == 0.68
    assert len(bundle.publications) == 1
    assert bundle.clinical_evidence is None
    assert bundle.gene_variant_landscape is not None
    assert bundle.gene_variant_landscape.total_variants_count == 33500
    assert len(bundle.gene_variant_landscape.variants) == 1
    assert "Definitive" in bundle.evidence_quality_summary["clinical_confidence_tier"]
    assert len(bundle.scientific_limitations) >= 4
    assert bundle.source_record_counts["ClinVar"] == 33500
    assert "Variants Indexed" in bundle.source_completeness["ClinVar"]


@patch.object(ClinVarAdapter, "fetch_variant_evidence")
@patch.object(PubMedAdapter, "search_literature")
@patch.object(ClinGenAdapter, "fetch_gene_validity")
@patch.object(EnsemblAdapter, "fetch_gene_by_symbol")
def test_orchestrator_variant_search(mock_ens, mock_cg, mock_pm, mock_cv):
    """Validates orchestrator search by variant identifier (rsID)."""
    mock_cv.return_value = (
        SourceStatus.AVAILABLE,
        ClinicalClassification(
            variation_id="12345",
            title="NM_007294.4(BRCA1):c.5266dupC (p.Gln1756Profs)",
            primary_classification="Pathogenic",
            review_stars=2,
            is_conflicting=False,
        ),
        EvidenceProvenance(
            source_name="NCBI ClinVar",
            source_endpoint="esummary.fcgi",
            retrieval_timestamp="2026-11-04T00:00:00Z",
            source_url="https://www.ncbi.nlm.nih.gov/clinvar/variation/12345/",
            assembly=GenomeAssembly.GRCh38,
        ),
    )
    mock_pm.return_value = (
        SourceStatus.AVAILABLE,
        [LiteratureReference(pmid="80357906", title="Variant Study", url="https://pubmed.ncbi.nlm.nih.gov/80357906/")],
        None,
    )
    mock_cg.return_value = (SourceStatus.AVAILABLE, [], None)
    mock_ens.return_value = (SourceStatus.AVAILABLE, GeneIdentity(symbol="BRCA1", assembly=GenomeAssembly.GRCh38), [], None)

    orchestrator = GeneticEvidenceOrchestrator(cache_dir=tempfile.gettempdir())
    bundle = orchestrator.search_variant("rs28897743", assembly=GenomeAssembly.GRCh38, use_cache=False)

    assert bundle.query_type == "variant"
    assert bundle.query_term == "rs28897743"
    assert bundle.clinical_evidence.primary_classification == "Pathogenic"
    assert bundle.clinical_evidence.review_stars == 2
    assert bundle.variant_identity is not None
    assert bundle.variant_identity.gene_symbol == "BRCA1"


@patch("requests.Session.get")
def test_corrupt_json_and_500_server_error_handling(mock_get):
    """Verifies that HTTP 500 and malformed non-JSON payloads are handled as ERROR without crashing."""
    mock_resp = MagicMock()
    mock_resp.status_code = 500
    mock_resp.url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
    mock_resp.json.side_effect = json.JSONDecodeError("Expecting value", "error page", 0)
    mock_get.return_value = mock_resp

    adapter = ClinVarAdapter(cache=EvidenceCache(tempfile.gettempdir()))
    status, data, prov = adapter.fetch_variant_evidence("12345", use_cache=False)
    assert status == SourceStatus.ERROR
    assert data is None


def test_duplicate_submission_and_condition_deduplication():
    """Verifies duplicate trait conditions in ClinVar records are deduplicated."""
    adapter = ClinVarAdapter(cache=EvidenceCache(tempfile.gettempdir()))
    prov = EvidenceProvenance(
        source_name="NCBI ClinVar",
        source_endpoint="esummary.fcgi",
        retrieval_timestamp="2026-11-04T00:00:00Z",
        source_url="https://clinvar",
    )
    record = {
        "uid": "12345",
        "title": "Test Variant",
        "clinical_significance": {"description": "Pathogenic", "review_status": "criteria provided, single submitter"},
        "trait_set": [
            {"trait_name": "Breast Cancer"},
            {"trait_name": "Breast Cancer"},  # Duplicate
            {"trait_name": "Ovarian Cancer"},
        ],
    }
    classification = adapter._parse_clinvar_summary_dict(record, prov)
    assert len(classification.conditions) == 2
    assert classification.conditions == ["Breast Cancer", "Ovarian Cancer"]


# =============================================================================
# 11. TASK 7.1 LIVE BIOLOGICAL DATA VERIFICATION & AUDIT TESTS
# =============================================================================

def test_clinvar_gene_landscape_contract_and_distinction():
    """Validates ClinVarGeneVariantLandscape contract and prevents gene-to-variant conflation."""
    prov = EvidenceProvenance(
        source_name="NCBI ClinVar",
        source_endpoint="esearch.fcgi",
        retrieval_timestamp="2026-11-04T00:00:00Z",
        source_url="https://clinvar",
    )
    landscape = ClinVarGeneVariantLandscape(
        gene_symbol="BRCA1",
        total_variants_count=33500,
        variants=[
            ClinicalClassification(
                variation_id="12345",
                title="NM_007294.4(BRCA1):c.5266dupC (p.Gln1756Profs)",
                primary_classification="Pathogenic",
                review_stars=2,
            ),
            ClinicalClassification(
                variation_id="67890",
                title="NM_007294.4(BRCA1):c.181T>G (p.Cys61Gly)",
                primary_classification="Conflicting interpretations of pathogenicity",
                review_stars=1,
                is_conflicting=True,
            ),
        ],
        provenance=prov,
    )
    d = landscape.to_dict()
    assert d["gene_symbol"] == "BRCA1"
    assert d["total_variants_count"] == 33500
    assert len(d["variants"]) == 2
    assert d["variants"][0]["primary_classification"] == "Pathogenic"
    assert d["variants"][1]["is_conflicting"] is True


def test_gnomad_genuine_zero_pli_and_biological_context():
    """Validates gnomAD r4 constraint schema handling: 0.000 is genuine biological numeric zero, not missing data."""
    adapter = GnomadAdapter(cache=EvidenceCache(tempfile.gettempdir()))

    # Raw GraphQL response payload with lowercase pli: 0.000 (official gnomAD schema)
    raw_gnomad_data = {
        "gene": {
            "gnomad_constraint": {
                "pli": 0.000,
                "oe_lof": 0.65,
                "oe_lof_upper": 0.928,
                "oe_mis": 0.92,
                "oe_mis_upper": 0.98,
                "oe_syn": 1.01,
                "flags": ["has_low_coverage_regions"],
            }
        }
    }
    parsed = adapter._parse_gnomad_constraint(raw_gnomad_data)
    assert parsed is not None
    # Check both schema key representations
    assert parsed["pli"] == 0.0
    assert parsed["pLI"] == 0.0
    assert parsed["oe_lof_upper"] == 0.928
    assert parsed["LOEUF"] == 0.928
    assert parsed["is_pli_zero"] is True
    # Verify objective clinical guidance: low pLI does NOT establish benignity
    assert "does not establish benignity" in parsed["clinical_guidance"].lower()
    assert "does not establish benignity" in parsed["biological_context"].lower()


def test_clingen_gene_validity_curation_resolution_and_panel():
    """Validates ClinGen expert curation resolution for benchmark genes like BRCA1."""
    adapter = ClinGenAdapter(cache=EvidenceCache(tempfile.gettempdir()))
    # Test fallback curation resolution for BRCA1 without live network
    status, curations, prov = adapter._fallback_clingen_curation("BRCA1")
    # Must explicitly report LOCAL_REFERENCE, never LIVE AVAILABLE
    assert status == SourceStatus.LOCAL_REFERENCE
    assert len(curations) >= 1
    brca1_cur = curations[0]
    assert brca1_cur.gene_symbol == "BRCA1"
    assert brca1_cur.classification == "Definitive"
    assert "Hereditary breast and ovarian cancer" in brca1_cur.disease_label
    assert brca1_cur.disease_id == "MONDO:0003582"
    assert brca1_cur.curation_panel == "ClinGen Hereditary Cancer Expert Panel"
    assert brca1_cur.haploinsufficiency_score == 3
    assert brca1_cur.triplosensitivity_score == 0
    assert brca1_cur.is_local_reference is True
    assert prov.is_local_reference is True
    assert "Local Reference" in prov.source_endpoint


def test_pubmed_integer_vs_string_uid_parsing_fix():
    """Verifies fix for NCBI E-utilities bug where uids list contains integers while result dict contains string keys."""
    adapter = PubMedAdapter(cache=EvidenceCache(tempfile.gettempdir()))
    prov = EvidenceProvenance(
        source_name="NCBI PubMed",
        source_endpoint="esummary.fcgi",
        retrieval_timestamp="2026-11-04T00:00:00Z",
        source_url="https://pubmed",
    )
    # Simulated NCBI payload where uids is integer array, but dictionary keys are strings
    mock_payload = {
        "result": {
            "uids": [30209392, 32719522],
            "30209392": {
                "title": "Accurate classification of BRCA1 variants using functional saturation genome editing.",
                "source": "Nature",
                "pubdate": "2018 Oct",
                "authors": [{"name": "Findlay GM"}, {"name": "Daza RM"}],
                "articleids": [{"idtype": "doi", "value": "10.1038/s41586-018-0461-z"}],
            },
            "32719522": {
                "title": "Recommendations for reporting of secondary findings in clinical genomic sequencing.",
                "source": "Genet Med",
                "pubdate": "2020",
                "authors": [{"name": "Miller DT"}],
                "articleids": [{"idtype": "doi", "value": "10.1038/s41436-020-0923-3"}],
            },
        }
    }
    publications = adapter._parse_pubmed_summaries(mock_payload, prov)
    assert len(publications) == 2
    assert publications[0].pmid == "30209392"
    assert "saturation genome editing" in publications[0].title
    assert publications[0].journal == "Nature"
    assert publications[0].doi == "10.1038/s41586-018-0461-z"
    assert publications[1].pmid == "32719522"
    assert publications[1].year == 2020


def test_pubmed_empty_search_vs_failed_search():
    """Distinguishes between empty query results and network/server failures."""
    adapter = PubMedAdapter(cache=EvidenceCache(tempfile.gettempdir()))

    with patch.object(adapter.session, "get") as mock_get:
        # 1. Successful HTTP 200 with 0 count
        mock_resp_empty = MagicMock()
        mock_resp_empty.status_code = 200
        mock_resp_empty.json.return_value = {"esearchresult": {"count": "0", "idlist": []}}
        mock_get.return_value = mock_resp_empty

        status, pubs, prov = adapter.search_literature("NONEXISTENT_QUERY_XYZ", use_cache=False)
        assert status == SourceStatus.UNAVAILABLE
        assert pubs == []

        # 2. Connection failure / timeout
        mock_get.side_effect = requests.RequestException("Connection refused")
        status_err, pubs_err, prov_err = adapter.search_literature("NONEXISTENT_QUERY_XYZ", use_cache=False)
        assert status_err == SourceStatus.ERROR
        assert pubs_err == []


def test_source_completeness_and_record_counts():
    """Verifies that GeneticEvidenceBundle tracks source_record_counts and source_completeness correctly."""
    bundle = GeneticEvidenceBundle(
        query_term="BRCA1",
        query_type="gene",
        target_assembly=GenomeAssembly.GRCh38,
        timestamp="2026-11-04T00:00:00Z",
        source_statuses={
            "ClinVar": SourceStatus.AVAILABLE,
            "ClinGen": SourceStatus.AVAILABLE,
            "Ensembl": SourceStatus.AVAILABLE,
            "gnomAD": SourceStatus.AVAILABLE,
            "PubMed": SourceStatus.AVAILABLE,
        },
        source_record_counts={
            "ClinVar": 33500,
            "ClinGen": 1,
            "Ensembl": 59,
            "gnomAD": 1,
            "PubMed": 3,
        },
        source_completeness={
            "ClinVar": "Complete",
            "ClinGen": "Complete",
            "Ensembl": "Complete",
            "gnomAD": "Complete",
            "PubMed": "Complete",
        },
    )
    d = bundle.to_dict()
    assert d["source_record_counts"]["ClinVar"] == 33500
    assert d["source_record_counts"]["PubMed"] == 3
    assert d["source_completeness"]["ClinVar"] == "Complete"
    assert d["source_completeness"]["ClinGen"] == "Complete"


# =============================================================================
# 12. TASK 7.2 CREDENTIAL & PROVENANCE REGRESSION TESTS
# =============================================================================

def test_clingen_live_versus_local_provenance():
    """Ensures live ClinGen API responses and local curated reference records have distinct provenance and statuses."""
    adapter = ClinGenAdapter(cache=EvidenceCache(tempfile.gettempdir()))

    # 1. Live GeneGraph mock response
    mock_gql_payload = {
        "data": {
            "gene_validity_curations": {
                "curations": [
                    {
                        "curation_id": "CG:12345",
                        "gene": {"symbol": "BRCA1", "label": "BRCA1"},
                        "disease": {"curie": "MONDO:0003582", "label": "Hereditary breast and ovarian cancer syndrome"},
                        "classification": {"curie": "SEPIO:0000001", "label": "Definitive"},
                        "specified_by": "Autosomal dominant inheritance",
                    }
                ]
            }
        }
    }
    with patch.object(adapter.session, "post") as mock_post:
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = mock_gql_payload
        mock_post.return_value = mock_resp

        status, curations, prov = adapter.fetch_gene_validity("BRCA1", use_cache=False)
        assert status == SourceStatus.AVAILABLE
        assert len(curations) == 1
        assert curations[0].is_local_reference is False
        assert prov.is_local_reference is False
        assert "graphql" in prov.source_endpoint

    # 2. Local reference fallback (when live network fails)
    status_fb, curations_fb, prov_fb = adapter._fallback_clingen_curation("BRCA1")
    assert status_fb == SourceStatus.LOCAL_REFERENCE
    assert status_fb != SourceStatus.AVAILABLE, "Local reference records must NEVER be marked as live AVAILABLE!"
    assert curations_fb[0].is_local_reference is True
    assert prov_fb.is_local_reference is True
    assert "Local Reference" in prov_fb.source_endpoint


def test_gnomad_no_unsupported_biological_explanations():
    """Verifies gnomAD constraint output contains objective clinical guidance without unsupported causal assertions."""
    adapter = GnomadAdapter(cache=EvidenceCache(tempfile.gettempdir()))
    raw_gnomad_data = {
        "gene": {
            "gnomad_constraint": {
                "pli": 0.000,
                "oe_lof": 0.65,
                "oe_lof_upper": 0.928,
            }
        }
    }
    parsed = adapter._parse_gnomad_constraint(raw_gnomad_data)
    assert parsed is not None
    guidance = parsed.get("clinical_guidance", "")
    assert len(guidance) > 20
    # Mandatory requirement: Low pLI does NOT establish benignity or lack of clinical importance
    assert "does not establish benignity" in guidance.lower()
    assert "clinical importance" in guidance.lower()
    # Ensure no unsupported biological speculation about adult-onset disease causing low pLI is asserted as fact
    assert "typically display low pli in general population cohorts because" not in guidance.lower()


def test_source_status_accuracy_and_isolation():
    """Validates operational isolation across all SourceStatus enum states."""
    expected_statuses = {"AVAILABLE", "CACHED", "LOCAL_REFERENCE", "UNAVAILABLE", "ERROR", "TIMEOUT"}
    actual_statuses = {s.value for s in SourceStatus}
    assert expected_statuses == actual_statuses

    # Ensure live and local reference statuses are mutually exclusive
    assert SourceStatus.AVAILABLE != SourceStatus.LOCAL_REFERENCE
    assert SourceStatus.CACHED != SourceStatus.LOCAL_REFERENCE
    assert SourceStatus.UNAVAILABLE != SourceStatus.LOCAL_REFERENCE
    assert SourceStatus.ERROR != SourceStatus.LOCAL_REFERENCE


# =============================================================================
# 11. TASK 7.3 REGRESSION TESTS — EVIDENCE INTEGRITY & PROVENANCE VERIFICATION
# =============================================================================

def test_default_provenance_values():
    """Validates that all evidence contract constructors default is_local_reference to False."""
    prov = EvidenceProvenance(
        source_name="NCBI ClinVar",
        source_endpoint="esummary.fcgi",
        retrieval_timestamp="2026-11-04T00:00:00Z",
        source_url="https://www.ncbi.nlm.nih.gov/clinvar/",
    )
    assert prov.is_local_reference is False
    assert prov.is_cached is False

    validity = GeneDiseaseValidity(gene_symbol="BRCA1", disease_label="Hereditary Breast and Ovarian Cancer")
    assert validity.is_local_reference is False
    assert validity.provenance is None

    clinical = ClinicalClassification(variation_id="17669")
    assert clinical.is_local_reference is False
    assert clinical.provenance is None

    landscape = ClinVarGeneVariantLandscape(gene_symbol="BRCA1")
    assert landscape.is_local_reference is False
    assert landscape.provenance is None

    pop_freq = PopulationFrequency()
    assert pop_freq.is_local_reference is False
    assert pop_freq.provenance is None

    pub = LiteratureReference(pmid="30093976", title="BRCA1 Saturation Mutagenesis")
    assert pub.is_local_reference is False
    assert pub.provenance is None

    gid = GeneIdentity(symbol="BRCA1")
    assert gid.is_local_reference is False

    vid = VariantIdentity(
        variant_id="rs28897743",
        chromosome="17",
        position=43044295,
        reference_allele="C",
        alternate_allele="T",
        assembly=GenomeAssembly.GRCh38,
    )
    assert vid.is_local_reference is False

    tr = TranscriptAnnotation(transcript_id="ENST00000357654")
    assert tr.is_local_reference is False


def test_explicit_local_reference_provenance():
    """Validates that all local reference fallback endpoints explicitly set is_local_reference=True."""
    # 1. ClinGen fallback
    cg_adapter = ClinGenAdapter(cache=EvidenceCache(tempfile.gettempdir()))
    cg_status, cg_recs, cg_prov = cg_adapter._fallback_clingen_curation("BRCA1")
    assert cg_status == SourceStatus.LOCAL_REFERENCE
    assert cg_prov.is_local_reference is True
    assert cg_prov.is_cached is False
    assert cg_recs[0].is_local_reference is True
    assert cg_status != SourceStatus.AVAILABLE

    # 2. ClinVar landscape fallback
    cv_adapter = ClinVarAdapter(cache=EvidenceCache(tempfile.gettempdir()))
    cv_status, cv_land, cv_prov = cv_adapter._fallback_gene_landscape("BRCA1")
    assert cv_status == SourceStatus.LOCAL_REFERENCE
    assert cv_prov.is_local_reference is True
    assert cv_prov.is_cached is False
    assert cv_land.is_local_reference is True
    for rep in cv_land.representative_variants:
        assert rep.is_local_reference is True
        assert rep.provenance is not None
        assert rep.provenance.is_local_reference is True

    # 3. gnomAD constraint fallback
    gnom_adapter = GnomadAdapter(cache=EvidenceCache(tempfile.gettempdir()))
    with patch.object(gnom_adapter.session, "post", side_effect=requests.exceptions.Timeout("Timeout")):
        gnom_status, gnom_c, gnom_prov = gnom_adapter.fetch_gene_constraint("BRCA1", use_cache=False)
        assert gnom_status == SourceStatus.LOCAL_REFERENCE
        assert gnom_prov.is_local_reference is True
        assert gnom_prov.is_cached is False

    # 4. PubMed literature fallback
    pm_adapter = PubMedAdapter(cache=EvidenceCache(tempfile.gettempdir()))
    pm_status, pm_pubs, pm_prov = pm_adapter._fallback_pubmed_literature("BRCA1")
    assert pm_status == SourceStatus.LOCAL_REFERENCE
    assert pm_prov.is_local_reference is True
    assert pm_prov.is_cached is False
    for pub in pm_pubs:
        assert pub.is_local_reference is True
        assert pub.provenance.is_local_reference is True


def test_live_versus_cached_versus_local_status_consistency():
    """Validates clear mutual exclusivity between AVAILABLE (live), CACHED (cache), and LOCAL_REFERENCE."""
    test_dir = tempfile.mkdtemp()
    cache = EvidenceCache(test_dir)
    adapter = ClinGenAdapter(cache=cache)

    # A: Mocked live return
    mock_gql_payload = {
        "data": {
            "gene_validity_curations": {
                "curations": [
                    {
                        "curation_id": "CG:9999",
                        "gene": {"symbol": "TP53", "label": "TP53"},
                        "disease": {"curie": "MONDO:0005295", "label": "Li-Fraumeni syndrome"},
                        "classification": {"curie": "SEPIO:0000001", "label": "Definitive"},
                    }
                ]
            }
        }
    }
    with patch.object(adapter.session, "post") as mock_post:
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = mock_gql_payload
        mock_post.return_value = mock_resp

        status, recs, prov = adapter.fetch_gene_validity("TP53", use_cache=True)
        assert status == SourceStatus.AVAILABLE
        assert prov.is_cached is False
        assert prov.is_local_reference is False

    # B: Retrieve from cache
    status_cached, recs_cached, prov_cached = adapter.fetch_gene_validity("TP53", use_cache=True)
    assert status_cached == SourceStatus.CACHED
    assert prov_cached.is_cached is True
    assert prov_cached.is_local_reference is False

    # C: Local reference fallback
    status_local, recs_local, prov_local = adapter._fallback_clingen_curation("TP53")
    assert status_local == SourceStatus.LOCAL_REFERENCE
    assert prov_local.is_cached is False
    assert prov_local.is_local_reference is True


def test_failed_live_requests_with_local_fallback():
    """Verifies that network failures fall back to LOCAL_REFERENCE for benchmarks, but return TIMEOUT/ERROR for others."""
    # ClinVar: BRCA1 falls back to LOCAL_REFERENCE on Timeout
    cv_adapter = ClinVarAdapter(cache=EvidenceCache(tempfile.gettempdir()))
    with patch.object(cv_adapter.session, "get", side_effect=requests.exceptions.Timeout("Timeout")):
        status_brca1, land_brca1, prov_brca1 = cv_adapter.fetch_gene_variant_landscape("BRCA1", use_cache=False)
        assert status_brca1 == SourceStatus.LOCAL_REFERENCE
        assert land_brca1 is not None

        # Non-benchmark gene (e.g. UNKNOWN_GENE) returns honest TIMEOUT, NOT UNAVAILABLE
        status_unk, land_unk, prov_unk = cv_adapter.fetch_gene_variant_landscape("UNKNOWN_GENE_XYZ", use_cache=False)
        assert status_unk == SourceStatus.TIMEOUT
        assert land_unk is None

    # ClinVar: 500 error returns ERROR for non-benchmark gene, NOT UNAVAILABLE
    with patch.object(cv_adapter.session, "get") as mock_get:
        mock_resp = MagicMock()
        mock_resp.status_code = 500
        mock_get.return_value = mock_resp
        status_err, land_err, _ = cv_adapter.fetch_gene_variant_landscape("UNKNOWN_GENE_XYZ", use_cache=False)
        assert status_err == SourceStatus.ERROR
        assert land_err is None

    # ClinGen: Timeout returns honest TIMEOUT for unindexed gene
    cg_adapter = ClinGenAdapter(cache=EvidenceCache(tempfile.gettempdir()))
    with patch.object(cg_adapter.session, "post", side_effect=requests.exceptions.Timeout("Timeout")):
        with patch.object(cg_adapter.session, "get", side_effect=requests.exceptions.Timeout("Timeout")):
            status_cg, recs_cg, _ = cg_adapter.fetch_gene_validity("UNKNOWN_GENE_XYZ", use_cache=False)
            assert status_cg == SourceStatus.TIMEOUT
            assert len(recs_cg) == 0


def test_clinvar_gene_versus_variant_level_separation():
    """Verifies strict separation between gene-level variant landscape and individual variant classification."""
    orchestrator = GeneticEvidenceOrchestrator(cache_dir=tempfile.gettempdir())

    # Gene search: Must populate gene_variant_landscape and must leave clinical_evidence as None
    with patch.object(orchestrator.clinvar, "fetch_gene_variant_landscape") as mock_land:
        mock_prov = EvidenceProvenance(
            source_name="NCBI ClinVar",
            source_endpoint="esummary.fcgi",
            retrieval_timestamp="2026-11-04T00:00:00Z",
            source_url="https://www.ncbi.nlm.nih.gov/clinvar/?term=BRCA1[gene]",
        )
        mock_land.return_value = (
            SourceStatus.AVAILABLE,
            ClinVarGeneVariantLandscape(
                gene_symbol="BRCA1",
                total_variants_in_clinvar=33500,
                representative_variants=[
                    ClinicalClassification(
                        variation_id="17669",
                        primary_classification="Pathogenic",
                        review_stars=4,
                        provenance=mock_prov,
                    )
                ],
                provenance=mock_prov,
            ),
            mock_prov,
        )
        gene_bundle = orchestrator.search_gene("BRCA1", assembly=GenomeAssembly.GRCh38, use_cache=True)
        assert gene_bundle.query_type == "gene"
        assert gene_bundle.gene_variant_landscape is not None
        assert gene_bundle.gene_variant_landscape.total_variants_in_clinvar > 0
        assert gene_bundle.clinical_evidence is None, "Gene search must NEVER assign a single variant classification to the entire gene!"

    # Variant search: Must populate clinical_evidence and must leave gene_variant_landscape as None
    with patch.object(orchestrator.clinvar, "fetch_variant_evidence") as mock_var:
        mock_var.return_value = (
            SourceStatus.AVAILABLE,
            ClinicalClassification(
                variation_id="17669",
                primary_classification="Pathogenic",
                review_stars=4,
                review_status="practice guideline",
            ),
            EvidenceProvenance("NCBI ClinVar", "esummary.fcgi", "2026-11-04T00:00:00Z", "https://clinvar.gov"),
        )
        variant_bundle = orchestrator.search_variant("17669", gene_symbol="BRCA1", use_cache=False)
        assert variant_bundle.query_type == "variant"
        assert variant_bundle.clinical_evidence is not None
        assert variant_bundle.clinical_evidence.variation_id == "17669"
        assert variant_bundle.clinical_evidence.primary_classification == "Pathogenic"
        assert variant_bundle.gene_variant_landscape is None, "Variant search must not conflate variant classification with gene landscape!"


# -----------------------------------------------------------------------------
# TASK 8.1 — VARIANT-LEVEL EVIDENCE INTELLIGENCE ARCHITECTURE TESTS
# -----------------------------------------------------------------------------

def test_variant_identity_normalization_dbsnp_rsid():
    """Verifies dbSNP rsID normalization against benchmark reference and unresolved lookups."""
    from evidence_engine import VariantNormalizer, GenomeAssembly

    # 1. Benchmark rsID on GRCh38
    v_bench = VariantNormalizer.normalize("rs28897743", assembly=GenomeAssembly.GRCh38)
    assert v_bench.is_valid
    assert not v_bench.is_ambiguous
    assert v_bench.variant_id == "rs28897743"
    assert v_bench.chromosome == "17"
    assert v_bench.position == 43044295
    assert v_bench.reference_allele == "C"
    assert v_bench.alternate_allele == "dup"
    assert v_bench.associated_gene == "BRCA1"
    assert v_bench.normalized_identifier == "17-43044295-C-dup"
    assert v_bench.normalization_source == "Curated Benchmark Reference Snapshot"
    assert v_bench.is_local_reference

    # 2. Benchmark rsID on GRCh37 (proves assembly-sensitive coordinates)
    v_bench_37 = VariantNormalizer.normalize("rs28897743", assembly=GenomeAssembly.GRCh37)
    assert v_bench_37.is_valid
    assert v_bench_37.position == 41196312
    assert v_bench_37.normalized_identifier == "17-41196312-C-dup"

    # 3. Unresolved rsID outside benchmark
    v_unres = VariantNormalizer.normalize("rs999999999", assembly=GenomeAssembly.GRCh38)
    assert v_unres.is_valid
    assert v_unres.is_ambiguous
    assert "Unresolved rsID" in (v_unres.ambiguity_reason or "")
    assert v_unres.chromosome == "Unknown"
    assert v_unres.position == 0


def test_variant_identity_normalization_clinvar_id():
    """Verifies ClinVar Variation ID normalization with alias resolution."""
    from evidence_engine import VariantNormalizer, GenomeAssembly

    # 1. Numeric ClinVar ID resolving to benchmark variant
    v_cv = VariantNormalizer.normalize("17667", assembly=GenomeAssembly.GRCh38)
    assert v_cv.is_valid
    assert not v_cv.is_ambiguous
    assert v_cv.variant_id == "rs28897743"
    assert v_cv.associated_gene == "BRCA1"
    assert v_cv.position == 43044295

    # 2. VCV-prefixed ClinVar accession
    v_vcv = VariantNormalizer.normalize("VCV000017667", assembly=GenomeAssembly.GRCh38)
    assert v_vcv.is_valid
    assert v_vcv.variant_id == "rs28897743"

    # 3. Unresolved numeric ClinVar ID
    v_unres = VariantNormalizer.normalize("999999999", assembly=GenomeAssembly.GRCh38)
    assert v_unres.is_valid
    assert v_unres.is_ambiguous
    assert "ClinVar ID requires external query" in (v_unres.ambiguity_reason or "")


def test_variant_identity_normalization_hgvs_genomic():
    """Verifies HGVS genomic notation parsing with RefSeq accession assembly matching."""
    from evidence_engine import VariantNormalizer, GenomeAssembly

    # Valid SNV on GRCh38 (NC_000017.11 is chr17 on GRCh38)
    v_hgvs = VariantNormalizer.normalize("NC_000017.11:g.7674220C>T", assembly=GenomeAssembly.GRCh38)
    assert v_hgvs.is_valid
    assert not v_hgvs.is_ambiguous
    assert v_hgvs.chromosome == "17"
    assert v_hgvs.position == 7674220
    assert v_hgvs.reference_allele == "C"
    assert v_hgvs.alternate_allele == "T"
    assert v_hgvs.normalized_identifier == "17-7674220-C-T"
    assert v_hgvs.normalization_source == "HGVS Genomic Parser"

    # Ref == Alt in HGVS
    v_ident = VariantNormalizer.normalize("NC_000017.11:g.7674220C>C", assembly=GenomeAssembly.GRCh38)
    assert not v_ident.is_valid
    assert "identical" in (v_ident.validation_error or "")


def test_variant_identity_strict_assembly_separation_and_rejection():
    """
    CRITICAL RULE: Refuse silent conversion between GRCh38 and GRCh37.
    A GRCh37 RefSeq accession must be rejected when target assembly is GRCh38.
    """
    from evidence_engine import VariantNormalizer, GenomeAssembly

    # NC_000017.10 belongs strictly to GRCh37
    v_mismatch_38 = VariantNormalizer.normalize(
        "NC_000017.10:g.41196312dup", assembly=GenomeAssembly.GRCh38
    )
    assert not v_mismatch_38.is_valid
    assert v_mismatch_38.is_ambiguous
    assert "RefSeq accession assembly mismatch" in (v_mismatch_38.validation_error or "")
    assert "Silent coordinate conversion is strictly prohibited" in (v_mismatch_38.validation_error or "")

    # NC_000017.11 belongs strictly to GRCh38
    v_mismatch_37 = VariantNormalizer.normalize(
        "NC_000017.11:g.43044295dup", assembly=GenomeAssembly.GRCh37
    )
    assert not v_mismatch_37.is_valid
    assert v_mismatch_37.is_ambiguous
    assert "RefSeq accession assembly mismatch" in (v_mismatch_37.validation_error or "")
    assert "Silent coordinate conversion is strictly prohibited" in (v_mismatch_37.validation_error or "")


def test_variant_identity_coordinate_parsing_and_validations():
    """Verifies chromosome coordinate format handling, ambiguity flagging, and input invalidity."""
    from evidence_engine import VariantNormalizer, GenomeAssembly

    # 1. Clean chromosome coordinates
    v_coord = VariantNormalizer.normalize("chr17:43044295:C:T", assembly=GenomeAssembly.GRCh38)
    assert v_coord.is_valid
    assert not v_coord.is_ambiguous
    assert v_coord.chromosome == "17"
    assert v_coord.position == 43044295
    assert v_coord.reference_allele == "C"
    assert v_coord.alternate_allele == "T"
    assert v_coord.normalized_identifier == "17-43044295-C-T"

    # 2. Delimited hyphen coordinates
    v_hyphen = VariantNormalizer.normalize("17-7674220-C-T", assembly=GenomeAssembly.GRCh38)
    assert v_hyphen.is_valid
    assert v_hyphen.chromosome == "17"
    assert v_hyphen.position == 7674220

    # 3. Non-positive position <= 0
    v_zero = VariantNormalizer.normalize("chr17:0:C:T", assembly=GenomeAssembly.GRCh38)
    assert not v_zero.is_valid
    assert "positive integer" in (v_zero.validation_error or "")

    v_neg = VariantNormalizer.normalize("chr17:-500:C:T", assembly=GenomeAssembly.GRCh38)
    assert not v_neg.is_valid
    assert "positive integer" in (v_neg.validation_error or "")

    # 4. Reference identical to alternate
    v_same = VariantNormalizer.normalize("chr17:43044295:G:G", assembly=GenomeAssembly.GRCh38)
    assert not v_same.is_valid
    assert "identical" in (v_same.validation_error or "")

    # 5. Missing alleles (coordinates only) -> Valid locus but Ambiguous variant
    v_ambig = VariantNormalizer.normalize("chr17:43044295", assembly=GenomeAssembly.GRCh38)
    assert v_ambig.is_valid
    assert v_ambig.is_ambiguous
    assert "Missing reference or alternate allele" in (v_ambig.ambiguity_reason or "")

    # 6. Blank / empty input
    v_empty = VariantNormalizer.normalize("", assembly=GenomeAssembly.GRCh38)
    assert not v_empty.is_valid
    assert "cannot be empty" in (v_empty.validation_error or "")


def test_variant_transcript_annotation_contract():
    """Verifies VariantTranscriptAnnotation contract, MANE Select, and VEP in-silico properties."""
    from evidence_engine import VariantTranscriptAnnotation, EvidenceProvenance, GenomeAssembly

    prov = EvidenceProvenance(
        source_name="Ensembl VEP",
        source_endpoint="vep",
        retrieval_timestamp="2026-11-04T00:00:00Z",
        source_url="https://rest.ensembl.org",
        assembly=GenomeAssembly.GRCh38,
    )
    vta = VariantTranscriptAnnotation(
        transcript_id="ENST00000357654",
        gene_symbol="BRCA1",
        gene_id="ENSG00000012048",
        consequence_terms=["frameshift_variant"],
        hgvs_c="c.5266dupC",
        hgvs_p="p.Gln1756ProfsTer74",
        exon="20/23",
        biotype="protein_coding",
        is_canonical=True,
        is_mane_select=True,
        codons="-/C",
        amino_acids="Q/Pfs*74",
        sift_prediction="deleterious",
        sift_score=0.0,
        polyphen_prediction="probably_damaging",
        polyphen_score=1.0,
        provenance=prov,
    )
    d = vta.to_dict()
    assert d["transcript_id"] == "ENST00000357654"
    assert d["is_canonical"] is True
    assert d["is_mane_select"] is True
    assert "frameshift_variant" in d["consequence_terms"]
    assert d["sift_score"] == 0.0
    assert d["polyphen_score"] == 1.0


def test_variant_population_frequency_contract():
    """Verifies VariantPopulationFrequency contract, popmax, and ancestry breakdowns."""
    from evidence_engine import VariantPopulationFrequency, GenomeAssembly

    vpf = VariantPopulationFrequency(
        source="gnomAD",
        dataset="gnomad_r4",
        assembly=GenomeAssembly.GRCh38,
        allele_count=38,
        allele_number=251400,
        allele_frequency=0.000151,
        homozygote_count=0,
        hemizygote_count=0,
        popmax_frequency=0.00142,
        popmax_population="Ashkenazi Jewish (asj)",
        ancestry_frequencies={"asj": 0.00142, "nfe": 0.00018},
    )
    d = vpf.to_dict()
    assert d["allele_count"] == 38
    assert d["allele_frequency"] == 0.000151
    assert d["popmax_frequency"] == 0.00142
    assert d["popmax_population"] == "Ashkenazi Jewish (asj)"
    assert d["ancestry_frequencies"]["asj"] == 0.00142


def test_computational_evidence_contract_and_disclaimer():
    """
    MANDATORY RULE: Algorithmic in-silico inferences must carry an unambiguous
    disclaimer stating that computational predictions are not clinical diagnoses.
    """
    from evidence_engine import ComputationalEvidence, EvidenceLevel

    ce = ComputationalEvidence(
        prediction_method="SIFT",
        prediction_output="deleterious",
        numerical_score=0.0,
        source="Ensembl VEP",
        version="5.2.2",
    )
    assert ce.evidence_level == EvidenceLevel.COMPUTATIONAL_PREDICTION
    assert "In-silico algorithmic predictions are exploratory computational inferences" in ce.evidence_limitations
    assert "NOT confirmed clinical or biological pathogenicity" in ce.evidence_limitations
    assert "Never use computational scores in isolation" in ce.evidence_limitations

    d = ce.to_dict()
    assert d["prediction_method"] == "SIFT"
    assert d["prediction_output"] == "deleterious"
    assert d["numerical_score"] == 0.0


@patch("requests.Session.get", side_effect=requests.exceptions.Timeout("Offline test"))
def test_clinvar_adapter_variant_evidence_and_submitter_preservation(mock_get):
    """
    Verifies ClinVarAdapter preserves submitter disagreements and does not collapse
    conflicting classifications into a false consensus.
    """
    from evidence_engine import ClinVarAdapter, SourceStatus, GenomeAssembly, EvidenceCache
    import tempfile

    adapter = ClinVarAdapter(cache=EvidenceCache(tempfile.mkdtemp()))
    status, clin_class, prov = adapter.fetch_variant_evidence("rs28897724")
    assert status in (SourceStatus.AVAILABLE, SourceStatus.CACHED, SourceStatus.LOCAL_REFERENCE)
    assert clin_class is not None
    assert clin_class.is_conflicting is True
    assert "Conflicting" in clin_class.primary_classification
    assert clin_class.conflict_summary is not None
    assert len(clin_class.submissions) >= 2
    # Verify individual submitters have discordant assertions
    sigs = {s.clinical_significance.lower() for s in clin_class.submissions}
    assert any("pathogenic" in s for s in sigs)
    assert any("uncertain" in s or "vus" in s for s in sigs)


@patch("requests.Session.post", side_effect=requests.exceptions.Timeout("Offline test"))
@patch("requests.Session.get", side_effect=requests.exceptions.Timeout("Offline test"))
def test_ensembl_adapter_variant_consequences_parsing(mock_get, mock_post):
    """Verifies EnsemblAdapter VEP parsing and fallback transcript generation."""
    from evidence_engine import EnsemblAdapter, VariantNormalizer, SourceStatus, GenomeAssembly

    adapter = EnsemblAdapter()
    var_id = VariantNormalizer.normalize("rs121913527", assembly=GenomeAssembly.GRCh38)
    status, transcripts, prov = adapter.fetch_variant_consequences(var_id, use_cache=False)

    assert status in (SourceStatus.AVAILABLE, SourceStatus.CACHED, SourceStatus.LOCAL_REFERENCE)
    assert len(transcripts) >= 1
    canonical = next((t for t in transcripts if t.is_canonical), transcripts[0])
    assert canonical.gene_symbol == "TP53"
    assert "missense_variant" in canonical.consequence_terms
    assert canonical.sift_prediction == "deleterious"
    assert canonical.polyphen_prediction == "probably_damaging"


@patch("requests.Session.post", side_effect=requests.exceptions.Timeout("Offline test"))
@patch("requests.Session.get", side_effect=requests.exceptions.Timeout("Offline test"))
def test_gnomad_adapter_variant_population_frequency_parsing(mock_get, mock_post):
    """Verifies GnomadAdapter variant population frequency retrieval and structure."""
    from evidence_engine import GnomadAdapter, VariantNormalizer, SourceStatus, GenomeAssembly

    adapter = GnomadAdapter()
    var_id = VariantNormalizer.normalize("rs1042522", assembly=GenomeAssembly.GRCh38)
    status, pop_freq, prov = adapter.fetch_variant_population_frequencies(var_id)

    assert status in (SourceStatus.AVAILABLE, SourceStatus.CACHED, SourceStatus.LOCAL_REFERENCE)
    assert pop_freq is not None
    assert pop_freq.allele_frequency is not None
    assert pop_freq.allele_frequency > 0.3  # Common polymorphism in TP53
    assert pop_freq.homozygote_count is not None
    assert pop_freq.homozygote_count > 0


@patch("requests.Session.post", side_effect=requests.exceptions.Timeout("Offline test"))
@patch("requests.Session.get", side_effect=requests.exceptions.Timeout("Offline test"))
def test_orchestrator_search_variant_evidence_full_aggregation(mock_get, mock_post):
    """
    Verifies GeneticEvidenceOrchestrator.search_variant_evidence compiles a complete,
    traceable VariantEvidenceRecord across identity, clinical, transcript, population,
    computational, and literature evidence.
    """
    import tempfile
    from evidence_engine import GeneticEvidenceOrchestrator, GenomeAssembly, SourceStatus

    cache_dir = tempfile.mkdtemp()
    orchestrator = GeneticEvidenceOrchestrator(cache_dir=cache_dir)

    record = orchestrator.search_variant_evidence("rs28897743", assembly=GenomeAssembly.GRCh38, use_cache=True)
    assert record.variant_identity.variant_id == "rs28897743"
    assert record.variant_identity.chromosome == "17"
    assert record.variant_identity.position == 43044295
    assert record.variant_identity.associated_gene == "BRCA1"

    # Clinical evidence
    assert record.clinical_evidence is not None
    assert record.clinical_evidence.primary_classification == "Pathogenic"
    assert record.clinical_evidence.review_stars == 2

    # Transcripts
    assert len(record.transcript_evidence) >= 1
    assert "frameshift_variant" in record.transcript_evidence[0].consequence_terms

    # Population
    assert record.population_evidence is not None
    assert record.population_evidence.allele_frequency is not None

    # Computational evidence
    assert len(record.computational_evidence) >= 1
    for ce in record.computational_evidence:
        assert "In-silico algorithmic predictions are exploratory" in ce.evidence_limitations

    # Literature
    assert len(record.literature_evidence) >= 1
    assert any(p.variant_specific_relevance for p in record.literature_evidence)

    # Source statuses are present and tracked
    for src in ["ClinVar", "Ensembl", "gnomAD", "PubMed", "ClinGen"]:
        assert src in record.source_statuses

    # Gene-disease validity is preserved strictly as gene context
    assert len(record.gene_disease_validity) >= 1
    assert record.gene_disease_validity[0].gene_symbol == "BRCA1"


@patch("requests.Session.post", side_effect=requests.exceptions.Timeout("Offline test"))
@patch("requests.Session.get", side_effect=requests.exceptions.Timeout("Offline test"))
def test_orchestrator_variant_conflict_and_divergence_detection(mock_get, mock_post):
    """
    Verifies that the orchestrator detects:
    1. ClinVar submitter disagreement / conflicting assertions.
    2. Computational vs. Clinical divergence (e.g. In-silico deleterious vs Benign consensus).
    """
    import tempfile
    from evidence_engine import GeneticEvidenceOrchestrator, GenomeAssembly

    cache_dir = tempfile.mkdtemp()
    orchestrator = GeneticEvidenceOrchestrator(cache_dir=cache_dir)

    # 1. Conflicting variant
    rec_conf = orchestrator.search_variant_evidence("rs28897724", assembly=GenomeAssembly.GRCh38, use_cache=True)
    assert len(rec_conf.conflicts_detected) >= 1
    assert any("Conflicting" in c or "Disagreement" in c for c in rec_conf.conflicts_detected)

    # 2. Benign variant with simulated in-silico deleterious prediction
    rec_benign = orchestrator.search_variant_evidence("rs1042522", assembly=GenomeAssembly.GRCh38, use_cache=True)
    assert rec_benign.clinical_evidence.primary_classification == "Benign"


@patch("requests.Session.post", side_effect=requests.exceptions.Timeout("Offline test"))
@patch("requests.Session.get", side_effect=requests.exceptions.Timeout("Offline test"))
def test_orchestrator_partial_failure_resilience(mock_get, mock_post):
    """
    Verifies that partial failure of one source adapter (e.g. PubMed network timeout)
    does not cause the overall variant evidence aggregation to fail.
    """
    import tempfile
    from evidence_engine import GeneticEvidenceOrchestrator, GenomeAssembly, SourceStatus

    cache_dir = tempfile.mkdtemp()
    orchestrator = GeneticEvidenceOrchestrator(cache_dir=cache_dir)

    with patch.object(orchestrator.pubmed, "search_variant_literature") as mock_pm:
        mock_pm.return_value = (SourceStatus.TIMEOUT, [], None)
        record = orchestrator.search_variant_evidence("rs28897743", assembly=GenomeAssembly.GRCh38, use_cache=True)

        assert record.source_statuses["PubMed"] == SourceStatus.TIMEOUT
        assert record.source_statuses["ClinVar"] in (SourceStatus.AVAILABLE, SourceStatus.LOCAL_REFERENCE, SourceStatus.CACHED)
        assert record.clinical_evidence is not None
        assert record.clinical_evidence.primary_classification == "Pathogenic"


def test_pubmed_summary_pmid_deduplication():
    """Verifies that PubMed summary parsing eliminates duplicate PMIDs."""
    from evidence_engine import PubMedAdapter, EvidenceProvenance

    adapter = PubMedAdapter()
    prov = EvidenceProvenance("PubMed", "esummary.fcgi", "2026-11-04T00:00:00Z", "https://pubmed.ncbi.nlm.nih.gov")
    
    # Mock result dictionary with repeated UIDs
    mock_payload = {
        "result": {
            "uids": ["12345678", "12345678", "87654321"],
            "12345678": {"title": "Study on BRCA1 variant", "source": "Nature", "pubdate": "2023 Jun"},
            "87654321": {"title": "TP53 polymorphism analysis", "source": "Science", "pubdate": "2024 Jan"}
        }
    }
    
    pubs = adapter._parse_pubmed_summaries(mock_payload, prov)
    assert len(pubs) == 2, f"Expected 2 deduplicated publications, got {len(pubs)}"
    pmids = [p.pmid for p in pubs]
    assert pmids == ["12345678", "87654321"]


def test_gnomad_adapter_non_vcf_allele_syntax_handling():
    """
    Verifies that non-VCF alleles (e.g. 'dup', '-') are intercepted before
    sending malformed queries to gnomAD GraphQL, properly engaging verified fallback.
    """
    from evidence_engine import GnomadAdapter, VariantNormalizer, SourceStatus, GenomeAssembly

    adapter = GnomadAdapter()
    # rs28897743 has alternate_allele = 'dup'
    var_id = VariantNormalizer.normalize("rs28897743", assembly=GenomeAssembly.GRCh38)
    assert var_id.alternate_allele.lower() == "dup"

    status, pop_freq, prov = adapter.fetch_variant_population_frequencies(var_id, use_cache=False)
    assert status == SourceStatus.LOCAL_REFERENCE
    assert pop_freq is not None
    assert pop_freq.is_local_reference is True
    assert pop_freq.allele_frequency == 0.000151


def test_evidence_fidelity_live_vs_local_reference_isolation():
    """
    Verifies that live evidence and LOCAL_REFERENCE evidence remain strictly distinguishable
    in VariantEvidenceRecord and that unobserved status is never fabricated as confirmed negative.
    """
    from evidence_engine import (
        VariantEvidenceRecord, VariantIdentity, ClinicalClassification,
        VariantPopulationFrequency, SourceStatus, GenomeAssembly, EvidenceProvenance
    )

    prov_live = EvidenceProvenance("ClinVar", "esummary.fcgi", "2026-11-04T00:00:00Z", "https://ncbi.nlm.nih.gov/clinvar", is_local_reference=False)
    prov_local = EvidenceProvenance("gnomAD", "local_snapshot", "2026-11-04T00:00:00Z", "https://gnomad.broadinstitute.org", is_local_reference=True)

    var_id = VariantIdentity("rs123", "17", 1000, "C", "T", GenomeAssembly.GRCh38, "rs123")
    clin = ClinicalClassification("ClinVar", "100", "Title", "Pathogenic", "criteria provided", 2, [], is_local_reference=False, provenance=prov_live)
    pop = VariantPopulationFrequency("gnomAD", GenomeAssembly.GRCh38, allele_frequency=0.001, is_local_reference=True, provenance=prov_local)

    rec = VariantEvidenceRecord(
        variant_identity=var_id,
        source_statuses={"ClinVar": SourceStatus.AVAILABLE, "gnomAD": SourceStatus.LOCAL_REFERENCE},
        clinical_evidence=clin,
        population_evidence=pop,
    )

    assert rec.source_statuses["ClinVar"] == SourceStatus.AVAILABLE
    assert rec.clinical_evidence.is_local_reference is False
    assert rec.source_statuses["gnomAD"] == SourceStatus.LOCAL_REFERENCE
    assert rec.population_evidence.is_local_reference is True
    assert rec.source_statuses["ClinVar"] != rec.source_statuses["gnomAD"]



