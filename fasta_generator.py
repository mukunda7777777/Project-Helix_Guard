"""
Helix Guard FASTA Generator Gateway - Repository Root
Delegates directly to HELIX GUARD/fasta_generator.py.
"""

import os
import sys

current_dir = os.path.dirname(os.path.abspath(__file__))
helix_guard_dir = os.path.join(current_dir, "HELIX GUARD")
if helix_guard_dir not in sys.path:
    sys.path.insert(0, helix_guard_dir)

from fasta_generator import FASTAGenerator

