"""
Helix Guard Epistasis Engine Gateway - Repository Root
Delegates directly to HELIX GUARD/epistasis_engine.py.
"""

import os
import sys

current_dir = os.path.dirname(os.path.abspath(__file__))
helix_guard_dir = os.path.join(current_dir, "HELIX GUARD")
if helix_guard_dir not in sys.path:
    sys.path.insert(0, helix_guard_dir)

from epistasis_engine import (
    GenotypePhase,
    InheritanceMode,
    VariantLocus,
    CompoundHeterozygoteResult,
    EpistaticInteraction,
    MultiVariantConflictReport,
    EpistasisEngine,
    GENE_INHERITANCE_MODELS,
    KNOWN_EPISTATIC_RULES,
)

