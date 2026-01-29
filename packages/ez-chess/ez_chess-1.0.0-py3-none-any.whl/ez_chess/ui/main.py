"""
EZ-Chess UI Main Module
=======================

Re-exports the main GUI application.
"""

import sys
from pathlib import Path
import importlib.util

# Add paths for imports
_ui_path = Path(__file__).parent.parent.parent / "ui"
_src_path = Path(__file__).parent.parent.parent / "src"

if str(_ui_path) not in sys.path:
    sys.path.insert(0, str(_ui_path))
if str(_src_path) not in sys.path:
    sys.path.insert(0, str(_src_path))

# Import using importlib to avoid name conflicts
spec = importlib.util.spec_from_file_location("ui_main", _ui_path / "main.py")
_ui_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(_ui_module)

# The actual class name is ChessGUI
ChessGUI = _ui_module.ChessGUI

# Alias for SDK naming consistency
EZChessApp = ChessGUI

__all__ = ["EZChessApp", "ChessGUI"]
