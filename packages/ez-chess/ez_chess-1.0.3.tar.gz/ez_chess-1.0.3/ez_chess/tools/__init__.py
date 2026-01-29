"""
EZ-Chess Tools Module
=====================

Chess analysis tools that can be used programmatically.
These are the same tools used by the ChessAgent for LLM function calling.

Available Tools:
- get_best_move_tool: Get the best move for a position
- move_quality_tool: Evaluate the quality of a specific move
- move_comparison_tool: Compare two moves
- position_overview_tool: Get a complete position overview

Example:
    >>> from ez_chess.tools import get_best_move_tool, position_overview_tool
    >>> 
    >>> fen = "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq - 0 1"
    >>> result = get_best_move_tool(fen)
    >>> print(result)
"""

import sys
from pathlib import Path
import importlib.util

# Add src to path for imports
_src_path = Path(__file__).parent.parent.parent / "src"
if str(_src_path) not in sys.path:
    sys.path.insert(0, str(_src_path))

# Import using importlib to avoid name conflicts
spec = importlib.util.spec_from_file_location("src_tool_schemas", _src_path / "tool_schemas.py")
_tools_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(_tools_module)

get_best_move_tool = _tools_module.get_best_move_tool
move_quality_tool = _tools_module.move_quality_tool
move_comparison_tool = _tools_module.move_comparison_tool
position_overview_tool = _tools_module.position_overview_tool
CHESS_TOOLS = _tools_module.CHESS_TOOLS

__all__ = [
    "get_best_move_tool",
    "move_quality_tool", 
    "move_comparison_tool",
    "position_overview_tool",
    "CHESS_TOOLS",
]
