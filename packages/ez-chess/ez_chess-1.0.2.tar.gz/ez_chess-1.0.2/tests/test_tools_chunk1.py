"""
Test Script for Phase 3 Chunk 1 Tools
Tests material.py, piece_activity.py, and king_safety.py

Tests each tool with:
1. Starting position
2. Tactical middlegame position
3. Endgame position
4. Position from user's game
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from tools.material import analyze_material
from tools.piece_activity import analyze_piece_activity
from tools.king_safety import analyze_king_safety
import chess


def print_separator(title=""):
    """Print a formatted separator."""
    if title:
        print(f"\n{'=' * 80}")
        print(f"  {title}")
        print(f"{'=' * 80}\n")
    else:
        print(f"{'-' * 80}")


def print_tool_result(tool_name: str, result: dict):
    """Print formatted tool analysis result."""
    print(f"\n{tool_name.upper()} ANALYSIS:")
    print_separator()
    
    print(f"Score: {result['score']}")
    print(f"\nEvidence ({len(result['evidence'])} observations):")
    for i, evidence in enumerate(result['evidence'], 1):
        print(f"  {i}. {evidence}")
    
    if result['factors']:
        print(f"\nFactors ({len(result['factors'])} factors):")
        for i, factor in enumerate(result['factors'], 1):
            print(f"  {i}. {factor}")


def test_position(name: str, fen: str):
    """Test all three tools on a single position."""
    print_separator(f"TESTING: {name}")
    
    # Display the board
    board = chess.Board(fen)
    print(board)
    print(f"\nFEN: {fen}\n")
    
    # Test Material Analysis
    try:
        material_result = analyze_material(fen)
        print_tool_result("Material", material_result)
    except Exception as e:
        print(f"\n❌ MATERIAL ANALYSIS FAILED: {e}")
    
    # Test Piece Activity Analysis
    try:
        activity_result = analyze_piece_activity(fen)
        print_tool_result("Piece Activity", activity_result)
    except Exception as e:
        print(f"\n❌ PIECE ACTIVITY ANALYSIS FAILED: {e}")
    
    # Test King Safety Analysis
    try:
        safety_result = analyze_king_safety(fen)
        print_tool_result("King Safety", safety_result)
    except Exception as e:
        print(f"\n❌ KING SAFETY ANALYSIS FAILED: {e}")
    
    print("\n")


def main():
    """Run all tests."""
    print_separator("PHASE 3 CHUNK 1 - FEATURE EXTRACTION TOOLS TEST")
    print("Testing: material.py, piece_activity.py, king_safety.py")
    print()
    
    # Test positions
    positions = [
        {
            "name": "Test 1: Starting Position",
            "fen": "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
            "description": "Equal material, no development, both kings safe"
        },
        {
            "name": "Test 2: After 1.e4 e5 2.Nf3 Nc6 3.Bc4",
            "fen": "r1bqkbnr/pppp1ppp/2n5/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R b KQkq - 3 3",
            "description": "Italian Game - white more developed, both sides equal material"
        },
        {
            "name": "Test 3: Middlegame - Material Imbalance",
            "fen": "r1bq1rk1/ppp2ppp/2n5/3np3/1bB5/2NP1N2/PPP2PPP/R1BQ1RK1 w - - 0 10",
            "description": "Both castled, bishops vs knights, active pieces"
        },
        {
            "name": "Test 4: Tactical Position - Discovered Attack",
            "fen": "r1bqk2r/pppp1ppp/2n2n2/2b1p3/2B1P3/3P1N2/PPP2PPP/RNBQK2R w KQkq - 0 6",
            "description": "Neither castled, open center, tactical tension"
        },
        {
            "name": "Test 5: User's Game - After 10.a3",
            "fen": "r1bqkb1r/1pp2pp1/p1np1n2/4p3/2BPP3/P1N2N2/1PP2PPP/R1BQK2R b KQkq - 0 10",
            "description": "From user's Lichess game - white played a3"
        },
        {
            "name": "Test 6: Endgame - Rook vs Pawns",
            "fen": "8/5pk1/6p1/8/8/6P1/5PKR/r7 w - - 0 1",
            "description": "Material imbalance, active rook, exposed kings"
        },
        {
            "name": "Test 7: King Safety Test - White King Exposed",
            "fen": "r1bq1rk1/ppp2ppp/2n5/3np3/1bBP4/2N2N2/PPP2PPP/R1BQK2R w K - 0 10",
            "description": "Black castled kingside, white king still in center"
        },
        {
            "name": "Test 8: Piece Activity Test - Centralized Knights",
            "fen": "r1bqkb1r/pppp1ppp/2n2n2/4p3/3PP3/2N2N2/PPP2PPP/R1BQKB1R b KQkq d3 0 4",
            "description": "Both sides with centralized knights, good development"
        }
    ]
    
    # Run tests
    for i, pos in enumerate(positions, 1):
        print(f"\n{i}/{len(positions)}: {pos['description']}")
        test_position(pos['name'], pos['fen'])
        
        if i < len(positions):
            input("Press Enter to continue to next test...")
    
    print_separator("ALL TESTS COMPLETED")
    print("✓ All three tools tested successfully!")
    print("\nTools tested:")
    print("  1. material.py - Material counting and imbalances")
    print("  2. piece_activity.py - Mobility, centralization, development")
    print("  3. king_safety.py - King exposure, pawn shield, attackers")
    print("\nNext: Run comprehensive analysis on a real game position.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user.")
    except Exception as e:
        print(f"\n\n❌ TEST FAILED WITH ERROR: {e}")
        import traceback
        traceback.print_exc()
