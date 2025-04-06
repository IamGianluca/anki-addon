import sys

if "pytest" not in sys.modules:
    from .src.addon import setup_addon

    setup_addon()
else:
    # When running under pytest, do nothing
    pass
