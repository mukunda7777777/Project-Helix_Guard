"""
Helix Guard Security Gateway - Repository Root
"""

import os
import sys
import importlib.util

current_dir = os.path.dirname(os.path.abspath(__file__))
target_file = os.path.join(current_dir, "HELIX GUARD", "security.py")

spec = importlib.util.spec_from_file_location("_helix_guard_security", target_file)
if spec is None or spec.loader is None:
    raise ImportError(f"Cannot load security from {target_file}")

_sec_mod = importlib.util.module_from_spec(spec)
sys.modules["_helix_guard_security"] = _sec_mod
spec.loader.exec_module(_sec_mod)

IBMQuantumCredentials = _sec_mod.IBMQuantumCredentials
load_ibm_credentials = _sec_mod.load_ibm_credentials
mask_secret = _sec_mod.mask_secret
sanitize_message = _sec_mod.sanitize_message

__all__ = [
    "IBMQuantumCredentials",
    "load_ibm_credentials",
    "mask_secret",
    "sanitize_message",
]
