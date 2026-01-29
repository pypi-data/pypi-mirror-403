"""
Test script for Stockfish engine integration.
Tests get_eval(), get_best_moves(), and get_pv() functions.
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from engine import StockfishEngine


def test_engine():
    """Test Stockfish engine with various positions."""
    
    print("=" * 80)
    print("STOCKFISH ENGINE TEST")
    print("=" * 80)
    print()
    
    # Test positions
    positions = [
        {
            "name": "Starting Position",
            "fen": "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
        },
        {
            "name": "Position from User's Game (Move 10)",
            "fen": "r1bqkb1r/1pp2pp1/p1np1n2/4p3/2BPP3/2N2N2/PPP2PPP/R1BQK2R w KQkq - 0 10"
        },
        {
            "name": "Tactical Position (White to Move)",
            "fen": "r1bqkb1r/pppp1ppp/2n2n2/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 4 4"
        }
    ]
    
    with StockfishEngine() as engine:
        print(f"✓ Engine initialized successfully")
        print(f"  Depth: {engine.depth}")
        print(f"  Threads: {engine.threads}")
        print(f"  Hash: {engine.hash_size} MB")
        print()
        
        for pos in positions:
            print("-" * 80)
            print(f"Testing: {pos['name']}")
            print(f"FEN: {pos['fen']}")
            print("-" * 80)
            print()
            
            # Test 1: Get evaluation
            print("1. GET EVALUATION:")
            eval_result = engine.get_eval(pos['fen'], depth=15)
            print(f"   Type: {eval_result['type']}")
            if eval_result['type'] == 'cp':
                score = eval_result['score'] / 100
                print(f"   Score: {score:+.2f} (centipawns: {eval_result['score']:+d})")
            else:
                print(f"   Score: Mate in {eval_result['score']}")
            print(f"   Depth: {eval_result['depth']}")
            print()
            
            # Test 2: Get best moves
            print("2. TOP 3 BEST MOVES:")
            best_moves = engine.get_best_moves(pos['fen'], n=3, depth=15)
            for i, move_info in enumerate(best_moves, 1):
                print(f"   {i}. {move_info['san']} ({move_info['move']})")
                if move_info['type'] == 'cp':
                    score = move_info['score'] / 100
                    print(f"      Score: {score:+.2f}")
                else:
                    print(f"      Score: Mate in {move_info['score']}")
                pv_display = " ".join(move_info['pv'][:5])
                if len(move_info['pv']) > 5:
                    pv_display += " ..."
                print(f"      PV: {pv_display}")
            print()
            
            # Test 3: Get principal variation
            print("3. PRINCIPAL VARIATION:")
            pv_moves, pv_eval = engine.get_pv(pos['fen'], depth=15)
            pv_display = " ".join(pv_moves[:8])
            if len(pv_moves) > 8:
                pv_display += " ..."
            print(f"   Line: {pv_display}")
            if pv_eval['type'] == 'cp':
                score = pv_eval['score'] / 100
                print(f"   Eval: {score:+.2f}")
            else:
                print(f"   Eval: Mate in {pv_eval['score']}")
            print()
            print()
    
    print("=" * 80)
    print("✓ ALL TESTS COMPLETED SUCCESSFULLY")
    print("=" * 80)


if __name__ == "__main__":
    try:
        test_engine()
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
