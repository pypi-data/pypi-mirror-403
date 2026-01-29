"""
EZ-Chess PGN Parser Module
==========================

Re-exports PGN parsing functionality from the source implementation.
"""

import sys
from pathlib import Path
import importlib.util

# Add src to path for imports
_src_path = Path(__file__).parent.parent.parent / "src"
if str(_src_path) not in sys.path:
    sys.path.insert(0, str(_src_path))

# Import using importlib to avoid name conflicts
spec = importlib.util.spec_from_file_location("src_pgn_parser", _src_path / "pgn_parser.py")
_pgn_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(_pgn_module)

PGNGame = _pgn_module.PGNGame

# Alias for convenience
PGNParser = PGNGame

__all__ = ["PGNGame", "PGNParser"]
