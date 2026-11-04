"""
Helix Guard Streamlit Gateway - Repository Root
Delegates directly to HELIX GUARD/app.py.
"""

import os
import sys

current_dir = os.path.dirname(os.path.abspath(__file__))
helix_guard_dir = os.path.join(current_dir, "HELIX GUARD")
if helix_guard_dir not in sys.path:
    sys.path.insert(0, helix_guard_dir)

app_path = os.path.join(helix_guard_dir, "app.py")

with open(app_path, "r", encoding="utf-8") as f:
    code = f.read()

# Execute app.py in global context
exec(compile(code, app_path, "exec"), globals())

