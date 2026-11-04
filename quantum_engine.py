"""
Helix Guard Quantum Engine - Root Gateway Module.
Enables transparent importing of the core quantum engine located in HELIX GUARD/.
"""

import os
import sys
import importlib.util

current_dir = os.path.dirname(os.path.abspath(__file__))
target_file = os.path.join(current_dir, "HELIX GUARD", "quantum_engine.py")

spec = importlib.util.spec_from_file_location("_helix_guard_quantum_engine", target_file)
if spec is None or spec.loader is None:
    raise ImportError(f"Cannot load quantum_engine from {target_file}")

_q_mod = importlib.util.module_from_spec(spec)
sys.modules["_helix_guard_quantum_engine"] = _q_mod
spec.loader.exec_module(_q_mod)

# Re-export all public attributes
CircuitArchitectureConfig = _q_mod.CircuitArchitectureConfig
CompactFeatureAdapter = _q_mod.CompactFeatureAdapter
HybridQuantumClassifier = _q_mod.HybridQuantumClassifier
QuantumCircuitBuilder = _q_mod.QuantumCircuitBuilder
QuantumFeatureNormalizer = _q_mod.QuantumFeatureNormalizer
generate_synthetic_genetic_data = _q_mod.generate_synthetic_genetic_data
run_simulation_demonstration = _q_mod.run_simulation_demonstration

__all__ = [
    "CircuitArchitectureConfig",
    "CompactFeatureAdapter",
    "HybridQuantumClassifier",
    "QuantumCircuitBuilder",
    "QuantumFeatureNormalizer",
    "generate_synthetic_genetic_data",
    "run_simulation_demonstration",
]

if __name__ == "__main__":
    run_simulation_demonstration()
