"""
Helix Guard Genetic Data Engine - Root Gateway
"""

import os
import sys
import importlib.util

current_dir = os.path.dirname(os.path.abspath(__file__))
target_file = os.path.join(current_dir, "HELIX GUARD", "genetic_data_engine.py")

spec = importlib.util.spec_from_file_location("_helix_guard_genetic_data_engine", target_file)
if spec is None or spec.loader is None:
    raise ImportError(f"Cannot load genetic_data_engine from {target_file}")

_g_mod = importlib.util.module_from_spec(spec)
sys.modules["_helix_guard_genetic_data_engine"] = _g_mod
spec.loader.exec_module(_g_mod)

# Re-export public components
ClinVarDataLoader = _g_mod.ClinVarDataLoader
LabelCurationEngine = _g_mod.LabelCurationEngine
ClinVarFeaturePipeline = _g_mod.ClinVarFeaturePipeline
DataSplitter = _g_mod.DataSplitter
ClassicalVariantBaseline = _g_mod.ClassicalVariantBaseline
QuantumVariantEvaluator = _g_mod.QuantumVariantEvaluator
run_clinvar_benchmark = _g_mod.run_clinvar_benchmark
DatasetQualityReport = _g_mod.DatasetQualityReport
CurationReport = _g_mod.CurationReport
ModelEvaluationReport = _g_mod.ModelEvaluationReport

__all__ = [
    "ClinVarDataLoader",
    "LabelCurationEngine",
    "ClinVarFeaturePipeline",
    "DataSplitter",
    "ClassicalVariantBaseline",
    "QuantumVariantEvaluator",
    "run_clinvar_benchmark",
    "DatasetQualityReport",
    "CurationReport",
    "ModelEvaluationReport",
]

