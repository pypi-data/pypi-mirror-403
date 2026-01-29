"""
Chess Analysis Agent - Groq Edition (Unified)
==============================================
State-of-the-art chess analysis using Groq's free API tier.

Features:
- Visual board representation force-fed to LLM
- Tool calling for hypothetical analysis ("what if I play Nf6?")
- Clear piece notation (UPPERCASE=White, lowercase=Black)
- Turn tracking for correct move sequences
- Clean plain-text responses (no markdown)
"""

import os
import sys
import re
import json
import chess
import requests
from typing import Optional, Dict, List, Any

# Add parent directory for imports when running as script
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.engine import StockfishEngine
from src.chess_fundamentals import (
    TACTICAL_MOTIFS, POSITIONAL_CONCEPTS, OPENING_PRINCIPLES,
    PAWN_STRUCTURE, KING_SAFETY, ATTACKING_PRINCIPLES, PIECE_PLACEMENT,
    DEFENSIVE_PRINCIPLES, ENDGAME_FUNDAMENTALS, ALL_FUNDAMENTALS
)


# =============================================================================
# VISUAL BOARD GENERATION
# =============================================================================

def get_visual_board(board: chess.Board) -> str:
    """Generate clear ASCII board with piece notation legend."""
    lines = []
    lines.append("BOARD POSITION:")
    lines.append("WHITE (UPPERCASE): K=King, Q=Queen, R=Rook, B=Bishop, N=Knight, P=Pawn")
    lines.append("BLACK (lowercase): k=king, q=queen, r=rook, b=bishop, n=knight, p=pawn")
    lines.append("")
    lines.append("    a   b   c   d   e   f   g   h")
    lines.append("  +---+---+---+---+---+---+---+---+")
    
    for rank in range(7, -1, -1):
        row = f"{rank + 1} |"
        for file in range(8):
            square = chess.square(file, rank)
            piece = board.piece_at(square)
            if piece:
                symbol = piece.symbol()
                row += f" {symbol} |"
            else:
                row += "   |"
        lines.append(row)
        lines.append("  +---+---+---+---+---+---+---+---+")
    
    lines.append("    a   b   c   d   e   f   g   h")
    return "\n".join(lines)


def get_piece_inventory(board: chess.Board) -> str:
    """Get detailed piece locations for both sides."""
    inventory = []
    
    white_pieces = []
    for piece_type in [chess.KING, chess.QUEEN, chess.ROOK, chess.BISHOP, chess.KNIGHT, chess.PAWN]:
        squares = list(board.pieces(piece_type, chess.WHITE))
        if squares:
            name = chess.piece_name(piece_type).capitalize()
            if len(squares) > 1:
                name += "s"
            locs = ", ".join([chess.square_name(sq) for sq in squares])
            white_pieces.append(f"{name}: {locs}")
    
    black_pieces = []
    for piece_type in [chess.KING, chess.QUEEN, chess.ROOK, chess.BISHOP, chess.KNIGHT, chess.PAWN]:
        squares = list(board.pieces(piece_type, chess.BLACK))
        if squares:
            name = chess.piece_name(piece_type).capitalize()
            if len(squares) > 1:
                name += "s"
            locs = ", ".join([chess.square_name(sq) for sq in squares])
            black_pieces.append(f"{name}: {locs}")
    
    inventory.append("WHITE PIECES: " + " | ".join(white_pieces))
    inventory.append("BLACK PIECES: " + " | ".join(black_pieces))
    return "\n".join(inventory)


def analyze_best_line(board: chess.Board, pv_moves: List[str]) -> str:
    """Generate move-by-move explanation of the best line."""
    if not pv_moves:
        return "No continuation available."
    
    analysis = []
    temp_board = board.copy()
    
    for i, move_san in enumerate(pv_moves[:6]):
        try:
            move = temp_board.parse_san(move_san)
            moving_piece = temp_board.piece_at(move.from_square)
            piece_name = chess.piece_name(moving_piece.piece_type).capitalize() if moving_piece else "Piece"
            from_sq = chess.square_name(move.from_square)
            to_sq = chess.square_name(move.to_square)
            is_capture = temp_board.is_capture(move)
            captured = temp_board.piece_at(move.to_square)
            captured_name = chess.piece_name(captured.piece_type).capitalize() if captured else ""
            gives_check = temp_board.gives_check(move)
            side = "White" if temp_board.turn else "Black"
            
            if is_capture and captured_name:
                desc = f"{side} {piece_name} captures {captured_name} on {to_sq}"
            else:
                desc = f"{side} {piece_name} from {from_sq} to {to_sq}"
            
            if gives_check:
                desc += " CHECK!"
            
            temp_board.push(move)
            analysis.append(f"  {i+1}. {move_san}: {desc}")
        except Exception:
            analysis.append(f"  {i+1}. {move_san}")
    
    return "\n".join(analysis)


def get_stockfish_analysis(fen: str) -> Dict:
    """Get comprehensive Stockfish analysis for the position."""
    board = chess.Board(fen)
    
    with StockfishEngine(depth=18) as engine:
        evaluation = engine.get_eval(fen, depth=18)
        best_moves = engine.get_best_moves(fen, n=3, depth=18)
    
    # Convert UCI PV moves to SAN notation
    pv_san = []
    if best_moves and 'pv' in best_moves[0]:
        pv_uci = best_moves[0]['pv'][:6]
        temp_board = board.copy()
        for uci_move in pv_uci:
            try:
                move = temp_board.parse_uci(uci_move)
                pv_san.append(temp_board.san(move))
                temp_board.push(move)
            except:
                pv_san.append(uci_move)
    
    # Format evaluation
    if evaluation['type'] == 'mate':
        mate_in = evaluation['score']
        winner = "White" if mate_in > 0 else "Black"
        eval_desc = f"MATE IN {abs(mate_in)} FOR {winner.upper()}"
        eval_numeric = 999 if mate_in > 0 else -999
    else:
        eval_numeric = evaluation['score'] / 100
        if abs(eval_numeric) < 0.3:
            eval_desc = f"EQUAL POSITION ({eval_numeric:+.2f})"
        elif abs(eval_numeric) < 1.0:
            side = "White" if eval_numeric > 0 else "Black"
            eval_desc = f"SLIGHT EDGE FOR {side.upper()} ({eval_numeric:+.2f})"
        elif abs(eval_numeric) < 2.5:
            side = "White" if eval_numeric > 0 else "Black"
            eval_desc = f"CLEAR ADVANTAGE FOR {side.upper()} ({eval_numeric:+.2f})"
        else:
            side = "White" if eval_numeric > 0 else "Black"
            eval_desc = f"WINNING FOR {side.upper()} ({eval_numeric:+.2f})"
    
    line_analysis = analyze_best_line(board, pv_san)
    
    return {
        'eval_numeric': eval_numeric,
        'eval_description': eval_desc,
        'best_move': best_moves[0]['san'] if best_moves else None,
        'top_3_moves': [m['san'] for m in best_moves[:3]],
        'best_line': " ".join(pv_san),
        'line_analysis': line_analysis,
        'pv_moves': pv_san
    }


def get_compact_fundamentals() -> str:
    """Get compact list of chess concepts for reference."""
    sections = []
    tactical = [f.name for f in TACTICAL_MOTIFS.values()]
    sections.append(f"TACTICS: {', '.join(tactical)}")
    positional = [f.name for f in POSITIONAL_CONCEPTS.values()]
    sections.append(f"POSITIONAL: {', '.join(positional)}")
    pawns = [f.name for f in PAWN_STRUCTURE.values()]
    sections.append(f"PAWN STRUCTURE: {', '.join(pawns)}")
    king = [f.name for f in KING_SAFETY.values()]
    sections.append(f"KING SAFETY: {', '.join(king)}")
    pieces = [f.name for f in PIECE_PLACEMENT.values()]
    sections.append(f"PIECE PLAY: {', '.join(pieces)}")
    return "\n".join(sections)


def get_opening_context(fen: str) -> str:
    """Get opening theory context for the position."""
    try:
        from src.mcp.opening_book import get_opening_book
        book = get_opening_book()
        return book.format_for_llm(fen)
    except ImportError:
        return "Opening book not available."
    except Exception as e:
        return f"Could not get opening context: {e}"


def clean_markdown(text: str) -> str:
    """Remove markdown formatting from response."""
    text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)
    text = re.sub(r'\*([^*]+)\*', r'\1', text)
    text = re.sub(r'__([^_]+)__', r'\1', text)
    text = re.sub(r'_([^_]+)_', r'\1', text)
    text = re.sub(r'^#+\s*', '', text, flags=re.MULTILINE)
    text = re.sub(r'^[\-\*]\s+', '', text, flags=re.MULTILINE)
    text = re.sub(r'^\d+\.\s+', '', text, flags=re.MULTILINE)
    text = re.sub(r'```[^`]*```', '', text)
    text = re.sub(r'`([^`]+)`', r'\1', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


# =============================================================================
# TOOL DEFINITIONS
# =============================================================================

CHESS_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "analyze_line",
            "description": """Analyze a sequence of chess moves from the current position.
Use this when the user asks about a specific line or sequence of moves, like:
- "What if I play e4 then Nf3?"
- "Analyze the line Nf6 d4 e6"
- "What happens after Bxf7+ Kxf7 Ng5+"
The moves will be played in alternating order starting from whoever's turn it is.""",
            "parameters": {
                "type": "object",
                "properties": {
                    "moves": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of moves in SAN notation (e.g., ['e4', 'e5', 'Nf3']). Moves alternate: first move is by whoever's turn it currently is."
                    }
                },
                "required": ["moves"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "analyze_single_move",
            "description": """Analyze the position after playing a single move.
Use this when the user asks about one specific move, like:
- "What if I play Nf6?"
- "Is Bb5 a good move?"
- "What happens after castling?"
Returns the evaluation and best response after that move.""",
            "parameters": {
                "type": "object",
                "properties": {
                    "move": {
                        "type": "string",
                        "description": "The move to analyze in SAN notation (e.g., 'Nf3', 'O-O', 'Bxf7+')"
                    }
                },
                "required": ["move"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "compare_moves",
            "description": """Compare two different moves to see which is better.
Use this when the user asks to compare options, like:
- "Is Bb5 better than Bc4?"
- "Should I play Nf3 or d4?"
- "Compare castling kingside vs queenside"
Returns evaluation for both moves.""",
            "parameters": {
                "type": "object",
                "properties": {
                    "move1": {
                        "type": "string",
                        "description": "First move to compare in SAN notation"
                    },
                    "move2": {
                        "type": "string",
                        "description": "Second move to compare in SAN notation"
                    }
                },
                "required": ["move1", "move2"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "compare_lines",
            "description": """Compare two different move sequences (lines) to see which leads to a better position.
Use this when the user asks to compare different continuations or lines, like:
- "Is e4 e5 Nf3 better than e4 c5?"
- "Compare the line d4 d5 c4 with d4 Nf6 c4"
- "Which is better: Nf3 Nc6 Bb5 or Nf3 Nc6 Bc4?"
Returns detailed analysis of both lines.""",
            "parameters": {
                "type": "object",
                "properties": {
                    "line1": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "First line as a list of moves in SAN notation (e.g., ['e4', 'e5', 'Nf3'])"
                    },
                    "line2": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Second line as a list of moves in SAN notation (e.g., ['d4', 'd5', 'c4'])"
                    }
                },
                "required": ["line1", "line2"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_opening_theory",
            "description": """Get opening theory and typical plans for the current position.
Use this when the user asks about:
- "What opening is this?"
- "What are the main ideas in this position?"
- "What's the theory here?"
Returns opening name, typical plans, and key squares.""",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    }
]


# =============================================================================
# TOOL EXECUTION
# =============================================================================

def execute_tool(tool_name: str, arguments: Dict, current_fen: str) -> str:
    """Execute a tool and return the result as a string."""
    board = chess.Board(current_fen)
    
    if tool_name == "analyze_line":
        return _execute_analyze_line(board, arguments.get("moves", []))
    elif tool_name == "analyze_single_move":
        return _execute_analyze_single_move(board, arguments.get("move", ""))
    elif tool_name == "compare_moves":
        return _execute_compare_moves(board, arguments.get("move1", ""), arguments.get("move2", ""))
    elif tool_name == "compare_lines":
        return _execute_compare_lines(board, arguments.get("line1", []), arguments.get("line2", []))
    elif tool_name == "get_opening_theory":
        return _execute_get_opening_theory(current_fen)
    else:
        return f"Unknown tool: {tool_name}"


def _execute_analyze_line(board: chess.Board, moves: List[str]) -> str:
    """Analyze a sequence of moves."""
    if not moves:
        return "Error: No moves provided."
    
    temp_board = board.copy()
    move_log = []
    starting_turn = "White" if temp_board.turn else "Black"
    
    move_log.append(f"ANALYZING LINE FROM CURRENT POSITION")
    move_log.append(f"Starting turn: {starting_turn}")
    move_log.append(f"Moves to play: {' '.join(moves)}")
    move_log.append("")
    
    for i, move_san in enumerate(moves):
        whose_turn = "White" if temp_board.turn else "Black"
        try:
            move = temp_board.parse_san(move_san)
            moving_piece = temp_board.piece_at(move.from_square)
            piece_name = chess.piece_name(moving_piece.piece_type).capitalize() if moving_piece else "Piece"
            is_capture = temp_board.is_capture(move)
            captured = temp_board.piece_at(move.to_square)
            captured_name = chess.piece_name(captured.piece_type).capitalize() if captured else ""
            
            temp_board.push(move)
            
            if is_capture and captured_name:
                move_log.append(f"Move {i+1}: {whose_turn} plays {move_san} ({piece_name} captures {captured_name})")
            else:
                move_log.append(f"Move {i+1}: {whose_turn} plays {move_san} ({piece_name})")
            
            if temp_board.is_checkmate():
                move_log.append(f"  -> CHECKMATE! {whose_turn} wins!")
                break
            elif temp_board.is_check():
                move_log.append(f"  -> Check!")
                
        except chess.IllegalMoveError:
            move_log.append(f"Move {i+1}: {whose_turn} CANNOT play {move_san} - ILLEGAL MOVE")
            move_log.append(f"  -> Legal moves: {', '.join([temp_board.san(m) for m in list(temp_board.legal_moves)[:10]])}...")
            return "\n".join(move_log)
        except chess.InvalidMoveError:
            move_log.append(f"Move {i+1}: {whose_turn} - {move_san} is INVALID notation")
            return "\n".join(move_log)
        except Exception as e:
            move_log.append(f"Move {i+1}: Error parsing {move_san}: {str(e)}")
            return "\n".join(move_log)
    
    move_log.append("")
    move_log.append("=== RESULTING POSITION ===")
    move_log.append(get_visual_board(temp_board))
    move_log.append("")
    
    final_turn = "White" if temp_board.turn else "Black"
    move_log.append(f"Turn: {final_turn} to move")
    move_log.append("")
    
    try:
        sf_analysis = get_stockfish_analysis(temp_board.fen())
        move_log.append(f"EVALUATION: {sf_analysis['eval_description']}")
        move_log.append(f"BEST CONTINUATION: {sf_analysis['best_move']}")
        move_log.append(f"BEST LINE: {sf_analysis['best_line']}")
    except Exception as e:
        move_log.append(f"Could not get Stockfish analysis: {e}")
    
    return "\n".join(move_log)


def _execute_analyze_single_move(board: chess.Board, move_san: str) -> str:
    """Analyze a single move."""
    if not move_san:
        return "Error: No move provided."
    
    temp_board = board.copy()
    whose_turn = "White" if temp_board.turn else "Black"
    
    result = []
    result.append(f"ANALYZING MOVE: {move_san} (played by {whose_turn})")
    result.append("")
    
    try:
        move = temp_board.parse_san(move_san)
        
        before_analysis = get_stockfish_analysis(temp_board.fen())
        temp_board.push(move)
        after_analysis = get_stockfish_analysis(temp_board.fen())
        
        result.append(f"BEFORE {move_san}: {before_analysis['eval_description']}")
        result.append(f"AFTER {move_san}: {after_analysis['eval_description']}")
        result.append("")
        
        eval_change = after_analysis['eval_numeric'] - before_analysis['eval_numeric']
        
        if whose_turn == "White":
            if eval_change > 0.5:
                result.append(f"VERDICT: {move_san} IMPROVES White's position by {eval_change:+.2f}")
            elif eval_change < -0.5:
                result.append(f"VERDICT: {move_san} WORSENS White's position by {eval_change:+.2f}")
            else:
                result.append(f"VERDICT: {move_san} maintains the balance (change: {eval_change:+.2f})")
        else:
            if eval_change < -0.5:
                result.append(f"VERDICT: {move_san} IMPROVES Black's position by {-eval_change:+.2f}")
            elif eval_change > 0.5:
                result.append(f"VERDICT: {move_san} WORSENS Black's position by {-eval_change:+.2f}")
            else:
                result.append(f"VERDICT: {move_san} maintains the balance (change: {eval_change:+.2f})")
        
        result.append("")
        result.append(f"Best response for opponent: {after_analysis['best_move']}")
        result.append(f"Best line continues: {after_analysis['best_line']}")
        
        result.append("")
        result.append("=== POSITION AFTER " + move_san + " ===")
        result.append(get_visual_board(temp_board))
        
    except chess.IllegalMoveError:
        result.append(f"ERROR: {move_san} is ILLEGAL for {whose_turn} in this position.")
        result.append(f"Legal moves: {', '.join([temp_board.san(m) for m in list(temp_board.legal_moves)[:15]])}...")
    except chess.InvalidMoveError:
        result.append(f"ERROR: {move_san} is not valid move notation.")
    except Exception as e:
        result.append(f"ERROR: {str(e)}")
    
    return "\n".join(result)


def _execute_compare_moves(board: chess.Board, move1: str, move2: str) -> str:
    """Compare two moves."""
    if not move1 or not move2:
        return "Error: Need two moves to compare."
    
    whose_turn = "White" if board.turn else "Black"
    
    result = []
    result.append(f"COMPARING MOVES FOR {whose_turn.upper()}")
    result.append(f"Option A: {move1}")
    result.append(f"Option B: {move2}")
    result.append("")
    
    analyses = {}
    
    for label, move_san in [("A", move1), ("B", move2)]:
        temp_board = board.copy()
        try:
            move = temp_board.parse_san(move_san)
            temp_board.push(move)
            sf_analysis = get_stockfish_analysis(temp_board.fen())
            analyses[label] = {
                'move': move_san,
                'eval': sf_analysis['eval_numeric'],
                'eval_desc': sf_analysis['eval_description'],
                'best_response': sf_analysis['best_move'],
                'valid': True
            }
            result.append(f"Option {label} ({move_san}):")
            result.append(f"  Resulting evaluation: {sf_analysis['eval_description']}")
            result.append(f"  Opponent's best response: {sf_analysis['best_move']}")
            result.append("")
        except chess.IllegalMoveError:
            analyses[label] = {'move': move_san, 'valid': False, 'error': 'Illegal move'}
            result.append(f"Option {label} ({move_san}): ILLEGAL MOVE")
            result.append("")
        except Exception as e:
            analyses[label] = {'move': move_san, 'valid': False, 'error': str(e)}
            result.append(f"Option {label} ({move_san}): Error - {e}")
            result.append("")
    
    result.append("=== VERDICT ===")
    if analyses.get("A", {}).get("valid") and analyses.get("B", {}).get("valid"):
        eval_a = analyses["A"]["eval"]
        eval_b = analyses["B"]["eval"]
        
        if whose_turn == "White":
            if eval_a > eval_b + 0.2:
                result.append(f"BETTER MOVE: {move1} (Option A)")
                result.append(f"  {move1} gives White a better position ({eval_a:+.2f} vs {eval_b:+.2f})")
            elif eval_b > eval_a + 0.2:
                result.append(f"BETTER MOVE: {move2} (Option B)")
                result.append(f"  {move2} gives White a better position ({eval_b:+.2f} vs {eval_a:+.2f})")
            else:
                result.append(f"ROUGHLY EQUAL: Both moves are similar")
                result.append(f"  {move1}: {eval_a:+.2f}, {move2}: {eval_b:+.2f}")
        else:
            if eval_a < eval_b - 0.2:
                result.append(f"BETTER MOVE: {move1} (Option A)")
                result.append(f"  {move1} gives Black a better position ({eval_a:+.2f} vs {eval_b:+.2f})")
            elif eval_b < eval_a - 0.2:
                result.append(f"BETTER MOVE: {move2} (Option B)")
                result.append(f"  {move2} gives Black a better position ({eval_b:+.2f} vs {eval_a:+.2f})")
            else:
                result.append(f"ROUGHLY EQUAL: Both moves are similar")
                result.append(f"  {move1}: {eval_a:+.2f}, {move2}: {eval_b:+.2f}")
    elif analyses.get("A", {}).get("valid"):
        result.append(f"Only {move1} is legal. {move2} cannot be played.")
    elif analyses.get("B", {}).get("valid"):
        result.append(f"Only {move2} is legal. {move1} cannot be played.")
    else:
        result.append("Neither move is legal in this position.")
    
    return "\n".join(result)


def _execute_compare_lines(board: chess.Board, line1: List[str], line2: List[str]) -> str:
    """Compare two move sequences (lines)."""
    if not line1 or not line2:
        return "Error: Need two lines to compare."
    
    whose_turn = "White" if board.turn else "Black"
    
    result = []
    result.append(f"COMPARING LINES FOR {whose_turn.upper()}")
    result.append(f"Line A: {' '.join(line1)}")
    result.append(f"Line B: {' '.join(line2)}")
    result.append("=" * 50)
    result.append("")
    
    analyses = {}
    
    for label, moves in [("A", line1), ("B", line2)]:
        temp_board = board.copy()
        move_log = []
        all_valid = True
        
        result.append(f"=== LINE {label}: {' '.join(moves)} ===")
        
        for i, move_san in enumerate(moves):
            current_turn = "White" if temp_board.turn else "Black"
            try:
                move = temp_board.parse_san(move_san)
                temp_board.push(move)
                move_log.append(f"  {i+1}. {current_turn}: {move_san}")
            except chess.IllegalMoveError:
                result.append(f"  Move {i+1}: {move_san} is ILLEGAL for {current_turn}")
                all_valid = False
                break
            except chess.InvalidMoveError:
                result.append(f"  Move {i+1}: {move_san} is invalid notation")
                all_valid = False
                break
        
        if all_valid:
            for log in move_log:
                result.append(log)
            
            try:
                sf_analysis = get_stockfish_analysis(temp_board.fen())
                analyses[label] = {
                    'eval': sf_analysis['eval_numeric'],
                    'eval_desc': sf_analysis['eval_description'],
                    'best_continuation': sf_analysis['best_move'],
                    'board': temp_board.copy(),
                    'valid': True
                }
                result.append(f"\n  Resulting evaluation: {sf_analysis['eval_description']}")
                result.append(f"  Best continuation: {sf_analysis['best_move']}")
                result.append(f"  Line continues: {sf_analysis['best_line']}")
            except Exception as e:
                result.append(f"  Could not analyze: {e}")
                analyses[label] = {'valid': False}
        else:
            analyses[label] = {'valid': False}
        
        result.append("")
    
    # Verdict
    result.append("=" * 50)
    result.append("=== VERDICT ===")
    
    if analyses.get("A", {}).get("valid") and analyses.get("B", {}).get("valid"):
        eval_a = analyses["A"]["eval"]
        eval_b = analyses["B"]["eval"]
        
        # Adjust for perspective
        if whose_turn == "White":
            better = "A" if eval_a > eval_b else "B" if eval_b > eval_a else "EQUAL"
            diff = abs(eval_a - eval_b)
        else:
            # For Black, lower eval is better
            better = "A" if eval_a < eval_b else "B" if eval_b < eval_a else "EQUAL"
            diff = abs(eval_a - eval_b)
        
        if diff < 0.2:
            result.append("RESULT: Both lines are approximately equal.")
            result.append(f"  Line A: {eval_a:+.2f}")
            result.append(f"  Line B: {eval_b:+.2f}")
        else:
            result.append(f"BETTER LINE: Line {better} ({' '.join(line1 if better == 'A' else line2)})")
            result.append(f"  Line A evaluation: {eval_a:+.2f}")
            result.append(f"  Line B evaluation: {eval_b:+.2f}")
            result.append(f"  Difference: {diff:.2f} pawns")
    else:
        if analyses.get("A", {}).get("valid"):
            result.append(f"Only Line A is playable. Line B contains illegal moves.")
        elif analyses.get("B", {}).get("valid"):
            result.append(f"Only Line B is playable. Line A contains illegal moves.")
        else:
            result.append("Neither line is fully playable from this position.")
    
    return "\n".join(result)


def _execute_get_opening_theory(fen: str) -> str:
    """Get opening theory for the current position."""
    try:
        from src.mcp.opening_book import get_opening_book
        book = get_opening_book()
        return book.format_for_llm(fen)
    except ImportError:
        return "Opening book module not available."
    except Exception as e:
        return f"Error getting opening theory: {e}"


# =============================================================================
# GROQ CLIENT
# =============================================================================

class GroqClient:
    """Groq API client with tool calling support."""
    
    BASE_URL = "https://api.groq.com/openai/v1/chat/completions"
    
    def __init__(self, api_key: str, model: str = "openai/gpt-oss-120b"):
        self.api_key = api_key
        self.model = model
    
    def chat(self, system_prompt: str, user_prompt: str, temperature: float = 0.3) -> str:
        """Simple chat without tools."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": temperature,
            "max_tokens": 1024
        }
        
        response = requests.post(self.BASE_URL, headers=headers, json=payload, timeout=60)
        
        if response.status_code == 429:
            raise Exception("Rate limit reached. Please wait a moment and try again.")
        
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"]
    
    def chat_with_tools(
        self, 
        messages: List[Dict], 
        tools: List[Dict],
        temperature: float = 0.3
    ) -> Dict:
        """Chat with tool calling support. Returns the full response."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "messages": messages,
            "tools": tools,
            "tool_choice": "auto",
            "temperature": temperature,
            "max_tokens": 1024
        }
        
        response = requests.post(self.BASE_URL, headers=headers, json=payload, timeout=60)
        
        if response.status_code == 429:
            raise Exception("Rate limit reached. Please wait a moment and try again.")
        
        response.raise_for_status()
        return response.json()


# =============================================================================
# GROQ CHESS AGENT
# =============================================================================

class GroqChessAgent:
    """
    Chess analysis agent with tool calling for hypothetical analysis.
    
    Handles:
    - Direct questions (who's better, what's the best move) → Force-fed answer
    - Hypothetical questions (what if, analyze line) → Tool calling
    """
    
    GROQ_MODELS = {
        "llama-3.3-70b-versatile": "Best for tool calling (default)",
        "llama-3.1-8b-instant": "Fast, good quality",
        "mixtral-8x7b-32768": "Good for long context",
    }
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "openai/gpt-oss-120b",
        temperature: float = 0.3,
        verbose: bool = True
    ):
        self.verbose = verbose
        self.model = model
        
        api_key = api_key or os.environ.get("GROQ_API_KEY")
        if not api_key:
            raise ValueError(
                "Groq API key required. Set GROQ_API_KEY environment variable "
                "or pass api_key parameter. Get free key at: https://console.groq.com"
            )
        
        self.client = GroqClient(api_key=api_key, model=model)
        
        # if verbose:
        #     print(f"[GroqAgent] Initialized with model: {model}")
        #     print(f"[GroqAgent] Tool calling ENABLED")
    
    def analyze(self, fen: str, question: str) -> str:
        """
        Analyze a chess position and answer a question.
        Uses tool calling when the question involves hypothetical analysis.
        """
        try:
            board = chess.Board(fen)
        except:
            return "Error: Invalid FEN position."
        
        visual_board = get_visual_board(board)
        piece_inventory = get_piece_inventory(board)
        
        try:
            sf_analysis = get_stockfish_analysis(fen)
        except Exception as e:
            return f"Error getting Stockfish analysis: {e}"
        
        turn = "White" if board.turn else "Black"
        move_number = board.fullmove_number
        fundamentals = get_compact_fundamentals()
        opening_context = get_opening_context(fen)
        
        system_prompt = f"""You are a chess grandmaster analyst with access to analysis tools.

CURRENT POSITION INFO:
- It is {turn}'s turn to move (Move {move_number})
- Moves alternate: {turn} plays first, then {'Black' if turn == 'White' else 'White'}, and so on.

PIECE NOTATION (CRITICAL):
- UPPERCASE letters = WHITE pieces (K, Q, R, B, N, P)
- lowercase letters = BLACK pieces (k, q, r, b, n, p)

WHEN TO USE TOOLS:
- Use "analyze_line" when user asks about a SEQUENCE of moves (e.g., "what if e4 e5 Nf3")
- Use "analyze_single_move" when user asks about ONE specific move (e.g., "what if Nf6?")
- Use "compare_moves" when user wants to compare TWO moves (e.g., "is Bb5 better than Bc4?")
- Use "compare_lines" when user wants to compare TWO LINES (e.g., "is e4 e5 better than d4 d5?")
- Use "get_opening_theory" when user asks about the opening or typical plans
- Do NOT use tools for questions about the current position (best move, evaluation, etc.)

RULES FOR RESPONSES:
- Plain text only - NO markdown, asterisks, or bullet points
- Be concise: 3-5 sentences maximum
- Reference specific squares and pieces
- Use chess concepts when relevant (fork, pin, weak square, etc.)
- When discussing openings, mention typical plans and ideas"""

        user_prompt = f"""
=== CHESS POSITION ===

{visual_board}

{piece_inventory}

TURN: {turn} to move (Move {move_number})

=== OPENING/PHASE CONTEXT ===

{opening_context}

=== STOCKFISH ANALYSIS OF CURRENT POSITION ===

EVALUATION: {sf_analysis['eval_description']}
BEST MOVE: {sf_analysis['best_move']}
TOP 3 MOVES: {', '.join(sf_analysis['top_3_moves'])}

BEST LINE:
{sf_analysis['line_analysis']}

=== CHESS CONCEPTS ===
{fundamentals}

=== QUESTION ===

{question}

If this question requires analyzing a hypothetical move or line, use the appropriate tool.
Otherwise, answer directly based on the position data above."""

        # if self.verbose:
        #     print(f"[GroqAgent] Analyzing: {turn} to move")
        #     print(f"[GroqAgent] Current eval: {sf_analysis['eval_description']}")
        #     print(f"[GroqAgent] Question: {question[:50]}...")
        
        try:
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
            
            response = self.client.chat_with_tools(messages, CHESS_TOOLS)
            
            choice = response["choices"][0]
            message = choice["message"]
            
            if message.get("tool_calls"):
                return self._handle_tool_calls(messages, message, fen)
            else:
                answer = message.get("content", "")
                return clean_markdown(answer)
                
        except Exception as e:
            error_msg = str(e)
            if "rate_limit" in error_msg.lower() or "429" in error_msg:
                return "Rate limit reached. Please wait a moment and try again."
            return f"Error: {error_msg}"
    
    def _handle_tool_calls(self, messages: List[Dict], assistant_message: Dict, fen: str) -> str:
        """Handle tool calls and get final response."""
        tool_calls = assistant_message.get("tool_calls", [])
        
        # if self.verbose:
        #     print(f"[GroqAgent] Tool calls requested: {len(tool_calls)}")
        
        messages.append(assistant_message)
        
        for tool_call in tool_calls:
            tool_name = tool_call["function"]["name"]
            try:
                arguments = json.loads(tool_call["function"]["arguments"])
            except:
                arguments = {}
            
            # if self.verbose:
            #     print(f"[GroqAgent] Executing tool: {tool_name}")
            #     print(f"[GroqAgent] Arguments: {arguments}")
            
            tool_result = execute_tool(tool_name, arguments, fen)
            
            # if self.verbose:
            #     print(f"[GroqAgent] Tool result length: {len(tool_result)} chars")
            
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call["id"],
                "content": tool_result
            })
        
        try:
            final_response = self.client.chat_with_tools(messages, CHESS_TOOLS)
            final_content = final_response["choices"][0]["message"].get("content", "")
            return clean_markdown(final_content)
        except Exception as e:
            return tool_result
    
    def get_best_move(self, fen: str) -> str:
        """Quick method to get best move explanation."""
        return self.analyze(fen, "What is the best move and why?")
    
    def evaluate_position(self, fen: str) -> str:
        """Quick method to evaluate position."""
        return self.analyze(fen, "Who has the advantage and why?")


# =============================================================================
# FACTORY FUNCTIONS
# =============================================================================

def create_groq_agent(
    api_key: Optional[str] = None,
    model: str = "openai/gpt-oss-120b",
    verbose: bool = True
) -> GroqChessAgent:
    """
    Create a Groq chess agent.
    
    Args:
        api_key: Groq API key (or set GROQ_API_KEY env var)
        model: Model to use (llama-3.3-70b-versatile recommended)
        verbose: Print debug info
    
    Returns:
        GroqChessAgent instance
    """
    return GroqChessAgent(api_key=api_key, model=model, verbose=verbose)


# Alias for backwards compatibility
def create_groq_agent_v2(
    api_key: Optional[str] = None,
    model: str = "openai/gpt-oss-120b",
    verbose: bool = True
) -> GroqChessAgent:
    """Alias for create_groq_agent (backwards compatibility)."""
    return create_groq_agent(api_key=api_key, model=model, verbose=verbose)


# =============================================================================
# TEST
# =============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("GROQ CHESS AGENT TEST")
    print("=" * 70)
    
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        print("\nNo GROQ_API_KEY found in environment.")
        print("Set it with: export GROQ_API_KEY='your-key-here'")
        exit(1)
    
    agent = create_groq_agent(verbose=True)
    
    # Test position: Italian Game
    fen = "r1bqk2r/pppp1ppp/2n2n2/2b1p3/2B1P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 4 4"
    
    print("\n" + "=" * 70)
    print("TEST 1: Direct question (no tool needed)")
    print("=" * 70)
    print("Question: What is the best move?")
    response = agent.analyze(fen, "What is the best move?")
    print(f"\nResponse:\n{response}")
    
    print("\n" + "=" * 70)
    print("TEST 2: Single move hypothetical")
    print("=" * 70)
    print("Question: What if I play d3?")
    response = agent.analyze(fen, "What if I play d3?")
    print(f"\nResponse:\n{response}")
    
    print("\n" + "=" * 70)
    print("TEST 3: Line analysis")
    print("=" * 70)
    print("Question: Analyze this line: d3 d6 O-O")
    response = agent.analyze(fen, "Analyze this line: d3 d6 O-O")
    print(f"\nResponse:\n{response}")
    
    print("\n" + "=" * 70)
    print("TEST 4: Compare moves")
    print("=" * 70)
    print("Question: Is c3 better than d3?")
    response = agent.analyze(fen, "Is c3 better than d3?")
    print(f"\nResponse:\n{response}")
    
    print("\n" + "=" * 70)
    print("ALL TESTS COMPLETED")
    print("=" * 70)
