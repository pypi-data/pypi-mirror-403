"""
EZ-Chess: AI-Powered Chess Analysis SDK
========================================

A Python SDK that combines Stockfish chess engine analysis with Large Language Models
to provide human-readable explanations of chess positions, moves, and strategies.

Quick Start
-----------

**Launch the GUI:**

.. code-block:: bash

    EZ-Chess run

**Use as a library:**

.. code-block:: python

    from ez_chess import ChessEngine, ChessAgent, analyze_position

    # Quick analysis
    result = analyze_position("rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1")
    print(result)

    # Or use the full engine
    engine = ChessEngine()
    analysis = engine.analyze("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1")
    print(f"Best move: {analysis['best_move']}")
    print(f"Evaluation: {analysis['evaluation']}")

Features
--------

- **Stockfish Integration**: Get professional-grade position analysis
- **LLM Explanations**: Natural language explanations via Groq (cloud) or Ollama (local)
- **PGN Support**: Load and analyze games from PGN files
- **Interactive GUI**: Full-featured chess interface with analysis panel
- **Extensible SDK**: Use individual components to build your own applications

License
-------
MIT License - Copyright (c) 2026 Anubhav Choudhery and Jai Ansh Bindra
"""

__version__ = "1.0.0"
__author__ = "Anubhav Choudhery, Jai Ansh Bindra"
__license__ = "MIT"

# =============================================================================
# PUBLIC API - Core Classes
# =============================================================================

from ez_chess.core.engine import ChessEngine
from ez_chess.core.board_state import BoardState
from ez_chess.core.pgn_parser import PGNGame, PGNParser
from ez_chess.core.config import (
    get_config,
    reload_config,
    AppConfig,
    LLMConfig,
    EngineConfig,
)

# =============================================================================
# PUBLIC API - Agent (requires langchain dependencies)
# =============================================================================

def get_agent(**kwargs):
    """
    Get a ChessAgent instance for AI-powered analysis.
    
    Requires either 'local' or 'cloud' extras to be installed:
        pip install ez-chess[local]   # For Ollama
        pip install ez-chess[cloud]   # For Groq
        pip install ez-chess[all]     # For both
    
    Args:
        **kwargs: Arguments passed to ChessAgent constructor
            - model_name: Override model name
            - temperature: LLM temperature (0.0-1.0)
            - verbose: Print debug info
            - mode: "cloud" or "local"
    
    Returns:
        ChessAgent instance
    
    Example:
        >>> agent = get_agent(mode="local")
        >>> response = agent.analyze(fen, "What's the best move?")
    """
    try:
        from ez_chess.core.agent import ChessAgent
        return ChessAgent(**kwargs)
    except ImportError as e:
        raise ImportError(
            "ChessAgent requires additional dependencies. Install with:\n"
            "  pip install ez-chess[local]   # For Ollama (local)\n"
            "  pip install ez-chess[cloud]   # For Groq (cloud)\n"
            "  pip install ez-chess[all]     # For both"
        ) from e


# =============================================================================
# PUBLIC API - Convenience Functions
# =============================================================================

def analyze_position(fen: str, depth: int = 18, num_moves: int = 3) -> dict:
    """
    Analyze a chess position and return structured results.
    
    This is the simplest way to get Stockfish analysis.
    
    Args:
        fen: Position in FEN notation
        depth: Analysis depth (default: 18)
        num_moves: Number of top moves to return (default: 3)
    
    Returns:
        Dictionary with analysis results:
        {
            "fen": str,
            "evaluation": float,  # In pawns (+ = white better)
            "best_move": str,     # In SAN notation
            "top_moves": [        # List of top moves
                {"move": str, "eval": float, "line": str},
                ...
            ],
            "is_mate": bool,
            "mate_in": int | None
        }
    
    Example:
        >>> result = analyze_position("rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq - 0 1")
        >>> print(f"Best move: {result['best_move']}")
        >>> print(f"Evaluation: {result['evaluation']:+.2f}")
    """
    engine = ChessEngine()
    
    # Get evaluation
    eval_result = engine.get_eval(fen, depth=depth)
    
    # Get top moves
    top_moves = engine.get_best_moves(fen, n=num_moves, depth=depth)
    
    # Build result
    result = {
        "fen": fen,
        "evaluation": eval_result.get("score_pawns", 0.0),
        "best_move": top_moves[0]["move"] if top_moves else "",
        "top_moves": [
            {
                "move": m.get("move", ""),
                "eval": m.get("score_pawns", 0.0),
                "line": " ".join(m.get("pv", []))
            }
            for m in top_moves
        ],
        "is_mate": eval_result.get("is_mate", False),
        "mate_in": eval_result.get("mate_in")
    }
    
    return result


def get_best_move(fen: str, depth: int = 18) -> str:
    """
    Get the best move for a position.
    
    Args:
        fen: Position in FEN notation
        depth: Analysis depth (default: 18)
    
    Returns:
        Best move in SAN notation (e.g., "Nf3", "e4", "O-O")
    
    Example:
        >>> move = get_best_move("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1")
        >>> print(f"Best move: {move}")  # e.g., "e4" or "d4"
    """
    engine = ChessEngine()
    top_moves = engine.get_best_moves(fen, n=1, depth=depth)
    return top_moves[0]["move"] if top_moves else ""


def evaluate_position(fen: str, depth: int = 18) -> float:
    """
    Get the evaluation of a position in pawns.
    
    Positive values favor White, negative values favor Black.
    
    Args:
        fen: Position in FEN notation
        depth: Analysis depth (default: 18)
    
    Returns:
        Evaluation in pawns (e.g., +1.5 means White is better by 1.5 pawns)
        Returns +/- 100.0 for mate positions
    
    Example:
        >>> eval = evaluate_position("rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq - 0 1")
        >>> print(f"Evaluation: {eval:+.2f}")  # e.g., "+0.30"
    """
    engine = ChessEngine()
    result = engine.get_eval(fen, depth=depth)
    return result.get("score_pawns", 0.0)


def parse_pgn(pgn_path: str):
    """
    Parse a PGN file and return a PGNGame object.
    
    Args:
        pgn_path: Path to PGN file
    
    Returns:
        PGNGame object with game data
    
    Example:
        >>> game = parse_pgn("my_game.pgn")
        >>> print(f"{game.get_metadata()['white']} vs {game.get_metadata()['black']}")
    """
    return PGNGame(pgn_path)


def explain_position(fen: str, question: str = "What's the best move and why?") -> str:
    """
    Get an AI-powered explanation of a chess position.
    
    Requires 'local' or 'cloud' extras to be installed.
    
    Args:
        fen: Position in FEN notation
        question: Question to ask about the position
    
    Returns:
        Natural language explanation from the AI
    
    Example:
        >>> explanation = explain_position(
        ...     "r1bqkb1r/pppp1ppp/2n2n2/4p2Q/2B1P3/8/PPPP1PPP/RNB1K1NR w KQkq - 4 4",
        ...     "What's the best move here?"
        ... )
        >>> print(explanation)
    """
    agent = get_agent()
    return agent.analyze(fen, question)


# =============================================================================
# PUBLIC API - GUI
# =============================================================================

def run_gui():
    """
    Launch the EZ-Chess GUI application.
    
    Requires 'gui' or 'all' extras to be installed:
        pip install ez-chess[gui]
        pip install ez-chess[all]
    
    Example:
        >>> import ez_chess
        >>> ez_chess.run_gui()
    """
    try:
        from ez_chess.ui.main import EZChessApp
        app = EZChessApp()
        app.run()
    except ImportError as e:
        raise ImportError(
            "GUI requires additional dependencies. Install with:\n"
            "  pip install ez-chess[gui]\n"
            "  pip install ez-chess[all]"
        ) from e


# =============================================================================
# PUBLIC API EXPORTS
# =============================================================================

__all__ = [
    # Version info
    "__version__",
    "__author__",
    "__license__",
    
    # Core classes
    "ChessEngine",
    "BoardState",
    "PGNGame",
    "PGNParser",
    
    # Configuration
    "get_config",
    "reload_config",
    "AppConfig",
    "LLMConfig", 
    "EngineConfig",
    
    # Agent (lazy loaded)
    "get_agent",
    
    # Convenience functions
    "analyze_position",
    "get_best_move",
    "evaluate_position",
    "parse_pgn",
    "explain_position",
    
    # GUI
    "run_gui",
]
