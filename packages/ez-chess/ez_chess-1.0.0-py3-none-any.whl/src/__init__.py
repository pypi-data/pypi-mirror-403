"""
EZ-Chess Source Module
======================

Core implementation modules for EZ-Chess.
These are used internally by the ez_chess package.
"""

from src.engine import StockfishEngine
from src.board_state import BoardState
from src.pgn_parser import PGNGame
from src.config import get_config, reload_config, AppConfig

# Alias for consistency
ChessEngine = StockfishEngine

__all__ = [
    "StockfishEngine",
    "ChessEngine",
    "BoardState", 
    "PGNGame",
    "get_config",
    "reload_config",
    "AppConfig",
]
