import sys

import os

# Add bundled dependencies (e.g., pydantic) to module search path
vendor_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "vendor")
sys.path.insert(0, vendor_dir)

if "pytest" not in sys.modules:
    from .src.addon import setup_addon

    setup_addon()
else:
    # When running under pytest, do nothing
    pass
