"""
Test script for PGN parsing and board state navigation.
Loads the user's game and demonstrates navigation capabilities.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from pgn_parser import PGNGame
from board_state import BoardState
import chess


def test_pgn_parsing():
    """Test PGN parsing and navigation."""
    
    print("=" * 80)
    print("PGN PARSER & BOARD STATE TEST")
    print("=" * 80)
    print()
    
    # Load the user's game
    pgn_path = os.path.join(
        os.path.dirname(__file__), 
        '..',
        'lichess_pgn_2026.01.17_andrixigo_vs_anubhav95.2U6e4Hau.pgn'
    )
    
    print(f"Loading PGN: {os.path.basename(pgn_path)}")
    print("-" * 80)
    print()
    
    # Test 1: Load and parse PGN
    print("TEST 1: LOADING PGN")
    game = PGNGame(pgn_path)
    print(f"Success: {game}")
    print()
    
    # Test 2: Extract metadata
    print("TEST 2: GAME METADATA")
    metadata = game.get_metadata()
    print(f"Event: {metadata.get('event', 'N/A')}")
    print(f"Site: {metadata.get('site', 'N/A')}")
    print(f"Date: {metadata.get('date', 'N/A')}")
    print(f"White: {metadata.get('white', 'N/A')} ({metadata.get('white_elo', 'N/A')})")
    print(f"Black: {metadata.get('black', 'N/A')} ({metadata.get('black_elo', 'N/A')})")
    print(f"Result: {metadata.get('result', 'N/A')}")
    print(f"Opening: {metadata.get('opening', 'N/A')}")
    print(f"ECO: {metadata.get('eco', 'N/A')}")
    print(f"Time Control: {metadata.get('time_control', 'N/A')}")
    print(f"Total Moves: {game.total_moves()}")
    print()
    
    # Test 3: Get move list
    print("TEST 3: MOVE LIST (first 20 moves)")
    moves_san = game.get_move_list('san')
    for i in range(0, min(20, len(moves_san)), 2):
        move_num = (i // 2) + 1
        white_move = moves_san[i]
        black_move = moves_san[i + 1] if i + 1 < len(moves_san) else ""
        print(f"{move_num}. {white_move} {black_move}")
    if len(moves_san) > 20:
        print("...")
    print()
    
    # Test 4: Position navigation
    print("TEST 4: POSITION AT SPECIFIC MOVES")
    print()
    
    test_positions = [0, 10, 20, game.total_moves()]
    for move_num in test_positions:
        if move_num > game.total_moves():
            continue
        
        fen = game.get_fen_at_move(move_num)
        board = game.get_board_at_move(move_num)
        
        if move_num == 0:
            print("Starting position:")
        else:
            move_info = game.get_move_info(move_num)
            print(f"After move {move_num} ({move_info['san']}):")
        
        print(board)
        print(f"FEN: {fen[:50]}...")
        print()
    
    # Test 5: BoardState navigation
    print("=" * 80)
    print("TEST 5: BOARD STATE NAVIGATION")
    print("=" * 80)
    print()
    
    # Initialize board state with game
    board_state = BoardState()
    boards = [game.get_board_at_move(i) for i in range(game.total_moves() + 1)]
    board_state.set_game_line(boards)
    
    print("Initial state:")
    state_info = board_state.get_state_info()
    print(f"Move: {state_info['move_number']}/{state_info['total_moves']}")
    print(f"Mode: {state_info['mode']}")
    print(f"To move: {state_info['to_move']}")
    print()
    
    # Navigate forward 5 moves
    print("Navigating forward 5 moves...")
    for i in range(5):
        board_state.next_move()
    
    state_info = board_state.get_state_info()
    print(f"Current position: Move {state_info['move_number']}")
    print(f"Legal moves: {', '.join(board_state.get_legal_moves('san')[:8])}...")
    print()
    
    # Jump to move 10
    print("Jumping to move 10...")
    board_state.jump_to_move(10)
    state_info = board_state.get_state_info()
    print(f"Current position: Move {state_info['move_number']}")
    print(board_state.get_board())
    print()
    
    # Test 6: Exploration mode
    print("=" * 80)
    print("TEST 6: EXPLORATION MODE")
    print("=" * 80)
    print()
    
    print("Making a different move (exploration)...")
    current_board = board_state.get_board()
    legal_moves = list(current_board.legal_moves)
    if legal_moves:
        # Make a move different from the game
        test_move = legal_moves[0]
        # Get SAN notation BEFORE making the move
        move_san = current_board.san(test_move)
        
        board_state.make_move(test_move)
        
        state_info = board_state.get_state_info()
        print(f"Made move: {move_san}")
        print(f"Mode: {state_info['mode']}")
        print(f"In game line: {state_info['in_game_line']}")
        print()
        
        print("Resetting to game line...")
        board_state.reset_to_game_line()
        state_info = board_state.get_state_info()
        print(f"Mode: {state_info['mode']}")
        print(f"Move: {state_info['move_number']}")
        print()
    
    print("=" * 80)
    print("ALL TESTS COMPLETED SUCCESSFULLY")
    print("=" * 80)


if __name__ == "__main__":
    try:
        test_pgn_parsing()
    except FileNotFoundError as e:
        print(f"ERROR: {e}")
        print("\nMake sure the PGN file exists in the project root")
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
