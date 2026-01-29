"""
EZ-Chess Core Module
====================

Core functionality for chess analysis including:
- ChessEngine: Stockfish integration
- BoardState: Chess board state management
- PGNParser: PGN file parsing
- ChessAgent: LLM-powered analysis agent
- Configuration management
"""

from ez_chess.core.engine import ChessEngine
from ez_chess.core.board_state import BoardState
from ez_chess.core.pgn_parser import PGNParser
from ez_chess.core.config import (
    get_config,
    reload_config,
    update_config,
    AppConfig,
    LLMConfig,
    EngineConfig,
    UIConfig,
    AnalysisConfig,
)

__all__ = [
    "ChessEngine",
    "BoardState", 
    "PGNParser",
    "get_config",
    "reload_config",
    "update_config",
    "AppConfig",
    "LLMConfig",
    "EngineConfig",
    "UIConfig",
    "AnalysisConfig",
]

# Lazy import for agent (requires langchain dependencies)
def __getattr__(name):
    if name == "ChessAgent":
        from ez_chess.core.agent import ChessAgent
        return ChessAgent
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
