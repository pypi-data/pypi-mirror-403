"""
EZ-Chess Agent Module
=====================

Re-exports the ChessAgent from the source implementation.
Requires langchain dependencies to be installed.
"""

import sys
from pathlib import Path
import importlib.util

# Add src to path for imports
_src_path = Path(__file__).parent.parent.parent / "src"
if str(_src_path) not in sys.path:
    sys.path.insert(0, str(_src_path))

# Import using importlib to avoid name conflicts
spec = importlib.util.spec_from_file_location("src_agent", _src_path / "agent.py")
_agent_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(_agent_module)

ChessAgent = _agent_module.ChessAgent

__all__ = ["ChessAgent"]
