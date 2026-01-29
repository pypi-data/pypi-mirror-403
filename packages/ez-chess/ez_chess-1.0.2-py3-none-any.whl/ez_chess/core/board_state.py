"""
EZ-Chess Board State Module
===========================

Re-exports BoardState from the source implementation.
"""

import sys
from pathlib import Path
import importlib.util

# Add src to path for imports
_src_path = Path(__file__).parent.parent.parent / "src"
if str(_src_path) not in sys.path:
    sys.path.insert(0, str(_src_path))

# Import using importlib to avoid name conflicts
spec = importlib.util.spec_from_file_location("src_board_state", _src_path / "board_state.py")
_board_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(_board_module)

BoardState = _board_module.BoardState
MoveMode = _board_module.MoveMode

__all__ = ["BoardState", "MoveMode"]
