"""
Helix Guard VCF Pipeline Gateway - Repository Root
Delegates directly to HELIX GUARD/vcf_pipeline.py.
"""

import os
import sys

current_dir = os.path.dirname(os.path.abspath(__file__))
helix_guard_dir = os.path.join(current_dir, "HELIX GUARD")
if helix_guard_dir not in sys.path:
    sys.path.insert(0, helix_guard_dir)

from vcf_pipeline import VCFPipeline

