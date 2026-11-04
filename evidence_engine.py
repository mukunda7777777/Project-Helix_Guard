"""
Helix Guard Genetic Evidence Intelligence Engine - Root Gateway
"""

import os
import sys
import importlib.util

current_dir = os.path.dirname(os.path.abspath(__file__))
target_file = os.path.join(current_dir, "HELIX GUARD", "evidence_engine.py")

spec = importlib.util.spec_from_file_location("_helix_guard_evidence_engine", target_file)
if spec is None or spec.loader is None:
    raise ImportError(f"Cannot load evidence_engine from {target_file}")

_e_mod = importlib.util.module_from_spec(spec)
sys.modules["_helix_guard_evidence_engine"] = _e_mod
spec.loader.exec_module(_e_mod)

# Re-export public components
GenomeAssembly = _e_mod.GenomeAssembly
EvidenceLevel = _e_mod.EvidenceLevel
SourceStatus = _e_mod.SourceStatus
EvidenceProvenance = _e_mod.EvidenceProvenance
GeneIdentity = _e_mod.GeneIdentity
VariantIdentity = _e_mod.VariantIdentity
TranscriptAnnotation = _e_mod.TranscriptAnnotation
VariantTranscriptAnnotation = _e_mod.VariantTranscriptAnnotation
ClinVarSubmission = _e_mod.ClinVarSubmission
ClinVarGeneVariantLandscape = _e_mod.ClinVarGeneVariantLandscape
ClinicalClassification = _e_mod.ClinicalClassification
PopulationFrequency = _e_mod.PopulationFrequency
VariantPopulationFrequency = _e_mod.VariantPopulationFrequency
GeneDiseaseValidity = _e_mod.GeneDiseaseValidity
ComputationalEvidence = _e_mod.ComputationalEvidence
LiteratureReference = _e_mod.LiteratureReference
VariantEvidenceRecord = _e_mod.VariantEvidenceRecord
GeneticEvidenceBundle = _e_mod.GeneticEvidenceBundle
EvidenceCache = _e_mod.EvidenceCache
BaseSourceAdapter = _e_mod.BaseSourceAdapter
ClinVarAdapter = _e_mod.ClinVarAdapter
ClinGenAdapter = _e_mod.ClinGenAdapter
EnsemblAdapter = _e_mod.EnsemblAdapter
GnomadAdapter = _e_mod.GnomadAdapter
PubMedAdapter = _e_mod.PubMedAdapter
VariantNormalizer = _e_mod.VariantNormalizer
VARIANT_BENCHMARK_CURATIONS = _e_mod.VARIANT_BENCHMARK_CURATIONS
GeneticEvidenceOrchestrator = _e_mod.GeneticEvidenceOrchestrator

__all__ = [
    "GenomeAssembly",
    "EvidenceLevel",
    "SourceStatus",
    "EvidenceProvenance",
    "GeneIdentity",
    "VariantIdentity",
    "TranscriptAnnotation",
    "VariantTranscriptAnnotation",
    "ClinVarSubmission",
    "ClinVarGeneVariantLandscape",
    "ClinicalClassification",
    "PopulationFrequency",
    "VariantPopulationFrequency",
    "GeneDiseaseValidity",
    "ComputationalEvidence",
    "LiteratureReference",
    "VariantEvidenceRecord",
    "GeneticEvidenceBundle",
    "EvidenceCache",
    "BaseSourceAdapter",
    "ClinVarAdapter",
    "ClinGenAdapter",
    "EnsemblAdapter",
    "GnomadAdapter",
    "PubMedAdapter",
    "VariantNormalizer",
    "VARIANT_BENCHMARK_CURATIONS",
    "GeneticEvidenceOrchestrator",
]

