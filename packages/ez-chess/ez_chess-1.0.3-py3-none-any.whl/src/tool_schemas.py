"""
LangGraph Tool Schemas
Defines tool schemas compatible with LangGraph for chess analysis.

Each tool returns structured data that the LLM agent can interpret and verbalize.
"""

from langchain_core.tools import tool
from typing import List, Dict, Optional
import sys
import os

# Add paths for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from tools import (
    analyze_material,
    analyze_piece_activity,
    analyze_king_safety,
    analyze_pawn_structure,
    compare_moves,
    analyze_move_quality
)
from src.engine import StockfishEngine


@tool
def get_best_move_tool(fen: str, num_moves: int = 3) -> Dict:
    """
    Get the best move(s) for a position using Stockfish engine WITH visual analysis.
    
    THIS IS THE PRIMARY TOOL FOR ANSWERING "What's the best move?" or "What should I play?"
    
    Use this when the user asks:
    - "What's the best move?"
    - "What should I play here?"
    - "What's the engine recommendation?"
    - "Find the best continuation"
    - Any question about what move to make
    
    Args:
        fen: Chess position in FEN notation
        num_moves: Number of top moves to return (default 3)
    
    Returns:
        Dictionary with visual board, best moves, evaluations, and line analysis
    """
    import chess
    
    # Create board for visualization
    board = chess.Board(fen)
    
    with StockfishEngine(depth=18) as engine:
        best_moves = engine.get_best_moves(fen, n=num_moves, depth=18)
        evaluation = engine.get_eval(fen, depth=18)
    
    # Extract principal variation
    pv_moves = []
    if best_moves and 'pv' in best_moves[0]:
        pv_moves = best_moves[0]['pv'][:6]
    
    # Generate visual representations
    board_visual = _get_board_visual(board)
    piece_locations = _get_piece_locations(board)
    line_analysis = _analyze_best_line(board, pv_moves)
    
    # Format evaluation (engine returns 'score' not 'value')
    if evaluation['type'] == 'mate':
        eval_desc = f"Mate in {abs(evaluation['score'])} for {'White' if evaluation['score'] > 0 else 'Black'}"
    else:
        eval_pawns = evaluation['score'] / 100
        eval_desc = f"{eval_pawns:+.2f}"
    
    turn = "White" if board.turn else "Black"
    
    visual_analysis = f"""
=== BEST MOVE ANALYSIS ===

BOARD:
{board_visual}

TURN: {turn} to move

PIECES: {piece_locations}

STOCKFISH EVALUATION: {eval_desc}
BEST MOVE: {best_moves[0]['san'] if best_moves else 'N/A'}

WHY THIS MOVE? Here's what happens:
{line_analysis}

ALTERNATIVES: {', '.join([m['san'] for m in best_moves[1:3]]) if len(best_moves) > 1 else 'None'}

=== END ANALYSIS ===
"""
    
    return {
        'visual_analysis': visual_analysis,
        'best_moves': best_moves,
        'evaluation': evaluation,
        'top_move': best_moves[0] if best_moves else None,
        'best_line': " ".join(pv_moves) if pv_moves else "N/A",
        'turn': turn
    }


@tool
def material_analysis_tool(fen: str) -> Dict:
    """
    Analyze material balance in a chess position.
    
    Use this when the user asks about:
    - Material count or imbalance
    - Who is ahead in material
    - Piece advantages
    - Trading recommendations
    
    Args:
        fen: Chess position in FEN notation
    
    Returns:
        Dictionary with material analysis including score, factors, and evidence
    """
    return analyze_material(fen)


@tool
def piece_activity_tool(fen: str) -> Dict:
    """
    Analyze piece activity, mobility, and development in a chess position.
    
    Use this when the user asks about:
    - Piece mobility or activity
    - Development
    - Center control
    - Piece positioning quality
    - Which pieces are well-placed or poorly placed
    
    Args:
        fen: Chess position in FEN notation
    
    Returns:
        Dictionary with activity analysis including mobility, development, and piece observations
    """
    return analyze_piece_activity(fen)


@tool
def king_safety_tool(fen: str) -> Dict:
    """
    Analyze king safety in a chess position.
    
    Use this when the user asks about:
    - King safety or exposure
    - Castling status
    - Pawn shield quality
    - Attacks on the king
    - King vulnerability
    
    Args:
        fen: Chess position in FEN notation
    
    Returns:
        Dictionary with king safety analysis including pawn shield, attackers, and escape squares
    """
    return analyze_king_safety(fen)


@tool
def pawn_structure_tool(fen: str) -> Dict:
    """
    Analyze pawn structure in a chess position.
    
    Use this when the user asks about:
    - Pawn structure or pawn weaknesses
    - Passed pawns
    - Isolated, doubled, or backward pawns
    - Pawn islands
    - Pawn majorities
    
    Args:
        fen: Chess position in FEN notation
    
    Returns:
        Dictionary with pawn structure analysis including weaknesses and strengths
    """
    return analyze_pawn_structure(fen)


@tool
def move_comparison_tool(fen: str, moves: str) -> Dict:
    """
    Compare multiple candidate moves using chess engine evaluation.
    
    Use this when the user asks about:
    - Which move is best among several options
    - Comparing different moves
    - Why one move is better than another
    - Alternative moves
    
    Args:
        fen: Chess position in FEN notation
        moves: Comma-separated list of moves to compare (e.g., "e4,d4,Nf3")
    
    Returns:
        Dictionary with move comparison including evaluations and differences
    """
    move_list = [m.strip() for m in moves.split(',')]
    return compare_moves(fen, move_list)


@tool
def move_quality_tool(fen: str, move: str) -> Dict:
    """
    Analyze the quality of a specific move that was played.
    
    Use this when the user asks about:
    - Whether a move is good or bad
    - Move quality (blunder, mistake, inaccuracy, etc.)
    - Why a particular move was played
    - What would have been better
    
    Args:
        fen: Chess position BEFORE the move in FEN notation
        move: The move to analyze (in SAN or UCI notation)
    
    Returns:
        Dictionary with move quality classification and better alternatives
    """
    return analyze_move_quality(fen, move)


def _get_board_visual(board: 'chess.Board') -> str:
    """Generate ASCII board with coordinates for LLM visualization."""
    lines = []
    lines.append("  a b c d e f g h")
    lines.append("  ---------------")
    
    board_str = str(board).split('\n')
    for rank_idx, rank_str in enumerate(board_str):
        rank_num = 8 - rank_idx
        lines.append(f"{rank_num}|{rank_str}|{rank_num}")
    
    lines.append("  ---------------")
    lines.append("  a b c d e f g h")
    return '\n'.join(lines)


def _get_piece_locations(board: 'chess.Board') -> str:
    """Describe where key pieces are located."""
    import chess
    
    descriptions = []
    
    # Kings
    wk = board.king(chess.WHITE)
    bk = board.king(chess.BLACK)
    if wk:
        descriptions.append(f"White King: {chess.square_name(wk)}")
    if bk:
        descriptions.append(f"Black King: {chess.square_name(bk)}")
    
    # Queens
    for sq in board.pieces(chess.QUEEN, chess.WHITE):
        descriptions.append(f"White Queen: {chess.square_name(sq)}")
    for sq in board.pieces(chess.QUEEN, chess.BLACK):
        descriptions.append(f"Black Queen: {chess.square_name(sq)}")
    
    # Rooks
    white_rooks = [chess.square_name(sq) for sq in board.pieces(chess.ROOK, chess.WHITE)]
    black_rooks = [chess.square_name(sq) for sq in board.pieces(chess.ROOK, chess.BLACK)]
    if white_rooks:
        descriptions.append(f"White Rooks: {', '.join(white_rooks)}")
    if black_rooks:
        descriptions.append(f"Black Rooks: {', '.join(black_rooks)}")
    
    # Knights and Bishops (combined)
    white_knights = [chess.square_name(sq) for sq in board.pieces(chess.KNIGHT, chess.WHITE)]
    black_knights = [chess.square_name(sq) for sq in board.pieces(chess.KNIGHT, chess.BLACK)]
    white_bishops = [chess.square_name(sq) for sq in board.pieces(chess.BISHOP, chess.WHITE)]
    black_bishops = [chess.square_name(sq) for sq in board.pieces(chess.BISHOP, chess.BLACK)]
    
    if white_knights:
        descriptions.append(f"White Knights: {', '.join(white_knights)}")
    if white_bishops:
        descriptions.append(f"White Bishops: {', '.join(white_bishops)}")
    if black_knights:
        descriptions.append(f"Black Knights: {', '.join(black_knights)}")
    if black_bishops:
        descriptions.append(f"Black Bishops: {', '.join(black_bishops)}")
    
    return " | ".join(descriptions)


def _analyze_best_line(board: 'chess.Board', pv_moves: List[str]) -> str:
    """Analyze what happens in the best line, move by move - Kasparov style."""
    import chess
    
    if not pv_moves:
        return "No continuation available."
    
    analysis = []
    temp_board = board.copy()
    
    for i, move_san in enumerate(pv_moves[:5]):  # Analyze first 5 moves
        try:
            move = temp_board.parse_san(move_san)
            
            # Get info about this move
            moving_piece = temp_board.piece_at(move.from_square)
            piece_name = chess.piece_name(moving_piece.piece_type).capitalize() if moving_piece else "Piece"
            from_sq = chess.square_name(move.from_square)
            to_sq = chess.square_name(move.to_square)
            
            # Check if it's a capture
            is_capture = temp_board.is_capture(move)
            captured = temp_board.piece_at(move.to_square)
            captured_name = chess.piece_name(captured.piece_type).capitalize() if captured else ""
            
            # Check for special moves
            gives_check = temp_board.gives_check(move)
            
            # Build move description
            turn = "White" if temp_board.turn else "Black"
            move_num = (i // 2) + 1 if i % 2 == 0 else ""
            
            if is_capture and captured_name:
                desc = f"{turn}'s {piece_name} takes {captured_name} on {to_sq}"
            else:
                desc = f"{turn}'s {piece_name} moves {from_sq}->{to_sq}"
            
            if gives_check:
                desc += " (CHECK!)"
            
            # Make the move
            temp_board.push(move)
            
            analysis.append(f"  {i+1}. {move_san}: {desc}")
            
        except Exception:
            analysis.append(f"  {i+1}. {move_san}")
    
    return '\n'.join(analysis)


@tool
def position_overview_tool(fen: str) -> Dict:
    """
    Get comprehensive visual analysis of a chess position using Stockfish.
    
    Use this when the user asks for:
    - General position evaluation
    - Overall assessment
    - "What's happening in this position?"
    - "Who is better?"
    
    Returns Stockfish eval WITH visual board representation for LLM understanding.
    
    Args:
        fen: Chess position in FEN notation
    
    Returns:
        Dictionary with visual board, Stockfish eval, and detailed line analysis
    """
    import chess
    
    # Create board for visualization
    board = chess.Board(fen)
    
    with StockfishEngine(depth=18) as engine:
        evaluation = engine.get_eval(fen, depth=18)
        best_moves = engine.get_best_moves(fen, n=3, depth=18)
    
    # Extract principal variation (best line)
    pv_moves = []
    if best_moves and 'pv' in best_moves[0]:
        pv_moves = best_moves[0]['pv'][:6]  # First 6 moves of best line
    
    # Format evaluation
    if evaluation['type'] == 'mate':
        eval_desc = f"Mate in {abs(evaluation['score'])} for {'White' if evaluation['score'] > 0 else 'Black'}"
        eval_pawns = 999 if evaluation['score'] > 0 else -999
    else:
        eval_centipawns = evaluation['score']
        eval_pawns = eval_centipawns / 100
        if abs(eval_pawns) < 0.5:
            advantage = "Equal"
        elif abs(eval_pawns) < 1.5:
            advantage = f"Slight edge {'White' if eval_pawns > 0 else 'Black'}"
        elif abs(eval_pawns) < 3.0:
            advantage = f"Clear advantage {'White' if eval_pawns > 0 else 'Black'}"
        else:
            advantage = f"Winning for {'White' if eval_pawns > 0 else 'Black'}"
        eval_desc = f"{advantage} ({eval_pawns:+.2f})"
    
    # Generate visual representations
    board_visual = _get_board_visual(board)
    piece_locations = _get_piece_locations(board)
    line_analysis = _analyze_best_line(board, pv_moves)
    
    # Build comprehensive evidence for LLM
    turn = "White" if board.turn else "Black"
    
    visual_analysis = f"""
=== POSITION ANALYSIS ===

BOARD:
{board_visual}

TURN: {turn} to move

PIECES: {piece_locations}

STOCKFISH EVALUATION: {eval_desc}
BEST MOVE: {best_moves[0]['san'] if best_moves else 'N/A'}
TOP 3 MOVES: {', '.join([m['san'] for m in best_moves[:3]]) if best_moves else 'N/A'}

BEST LINE ANALYSIS:
{line_analysis}

=== END ANALYSIS ===
"""
    
    return {
        'visual_analysis': visual_analysis,
        'eval': eval_pawns,
        'eval_description': eval_desc,
        'best_move': best_moves[0]['san'] if best_moves else "N/A",
        'best_line': " ".join(pv_moves) if pv_moves else "N/A",
        'top_moves': [m['san'] for m in best_moves[:3]],
        'turn': turn,
        'board_visual': board_visual
    }


# Export tools for LangGraph - SIMPLIFIED: Only Stockfish-based tools
CHESS_TOOLS = [
    get_best_move_tool,      # For "what's the best move?"
    move_quality_tool,       # For "is this move good/bad?"
    move_comparison_tool,    # For "which is better, X or Y?"
    position_overview_tool   # For general assessment - PURE STOCKFISH
]


# Tool name to description mapping
TOOL_DESCRIPTIONS = {
    'get_best_move_tool': 'Gets best move(s) from Stockfish',
    'move_quality_tool': 'Evaluates if a specific move is good/bad',
    'move_comparison_tool': 'Compares multiple candidate moves',
    'position_overview_tool': 'Position evaluation using Stockfish + best line analysis'
}
