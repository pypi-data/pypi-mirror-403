"""
EZ-Chess Engine Module
======================

Re-exports ChessEngine from the source implementation.
"""

import sys
from pathlib import Path
import importlib.util

# Add src to path for imports
_src_path = Path(__file__).parent.parent.parent / "src"
if str(_src_path) not in sys.path:
    sys.path.insert(0, str(_src_path))

# Import using importlib to avoid name conflicts
spec = importlib.util.spec_from_file_location("src_engine", _src_path / "engine.py")
_engine_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(_engine_module)

# The actual class name in src/engine.py is StockfishEngine
StockfishEngine = _engine_module.StockfishEngine
LRUCache = _engine_module.LRUCache
CachedAnalysis = _engine_module.CachedAnalysis

# Alias for SDK convenience
ChessEngine = StockfishEngine

__all__ = ["ChessEngine", "StockfishEngine", "LRUCache", "CachedAnalysis"]
