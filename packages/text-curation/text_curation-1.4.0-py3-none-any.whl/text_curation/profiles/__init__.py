"""
Profile package initializer.

This module is responsible for discovering and importing all
profile definitions so they can self-register with the global
profile registry.

Profiles rely on import-time side effects (register(PROFILE)),
so explicit discovery is required.
"""

import importlib
from importlib.resources import files

# Dynamically import all profile modules in this package.
# This ensures profiles are registered without manual imports.
for path in files(__name__).iterdir():
    if path.suffix == ".py" and path.name not in {"__init__.py", "base.py"}:
        importlib.import_module(f"{__name__}.{path.stem}")