"""
Test Script for Phase 3 Chunk 2 Tools
Tests pawn_structure.py and move_comparison.py, plus integration of all 5 tools

Tests each tool with:
1. Pawn structure positions (isolated, passed, doubled pawns)
2. Move comparison scenarios
3. Full analysis combining all tools
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from tools.pawn_structure import analyze_pawn_structure
from tools.move_comparison import compare_moves, analyze_move_quality
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
    print(f"\n{tool_name.upper()}:")
    print_separator()
    
    print(f"Score: {result['score']}")
    print(f"\nEvidence ({len(result['evidence'])} observations):")
    for i, evidence in enumerate(result['evidence'], 1):
        print(f"  {i}. {evidence}")


def test_pawn_structures():
    """Test pawn structure analysis."""
    print_separator("PART 1: PAWN STRUCTURE ANALYSIS")
    
    positions = [
        {
            "name": "Starting Position",
            "fen": "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
            "description": "Perfect pawn structures, no weaknesses"
        },
        {
            "name": "Isolated Queen Pawn",
            "fen": "r1bqkb1r/pp3ppp/2n1pn2/3p4/2PP4/2N2N2/PP2PPPP/R1BQKB1R w KQkq - 0 7",
            "description": "White has isolated d4 pawn"
        },
        {
            "name": "Passed Pawn Endgame",
            "fen": "8/5pk1/6p1/3P4/8/6P1/5PKR/r7 w - - 0 1",
            "description": "White passed d-pawn"
        },
        {
            "name": "Doubled Pawns",
            "fen": "rnbqkb1r/pp2pppp/5n2/2pp4/3P4/2N2N2/PPP1PPPP/R1BQKB1R w KQkq - 0 5",
            "description": "Black doubled c-pawns"
        },
        {
            "name": "Pawn Majority",
            "fen": "r1bqkb1r/pp3ppp/2n1pn2/2pp4/3P4/2NBPN2/PPP2PPP/R1BQK2R w KQkq - 0 7",
            "description": "White queenside majority, black kingside majority"
        }
    ]
    
    for pos in positions:
        print_separator(f"Testing: {pos['name']}")
        print(f"Description: {pos['description']}")
        
        board = chess.Board(pos['fen'])
        print(f"\n{board}\n")
        
        result = analyze_pawn_structure(pos['fen'])
        print_tool_result("Pawn Structure", result)
        
        input("\nPress Enter to continue...")


def test_move_comparison():
    """Test move comparison analysis."""
    print_separator("PART 2: MOVE COMPARISON ANALYSIS")
    
    test_cases = [
        {
            "name": "Opening Choice - Italian Game",
            "fen": "r1bqkbnr/pppp1ppp/2n5/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 3 3",
            "moves": ["d4", "O-O", "Nc3", "d3"],
            "description": "Compare common 3rd moves for white"
        },
        {
            "name": "Tactical Position",
            "fen": "r1bqk2r/pppp1ppp/2n2n2/2b1p3/2B1P3/3P1N2/PPP2PPP/RNBQK2R w KQkq - 0 6",
            "moves": ["Bxf7+", "O-O", "Nc3", "a3"],
            "description": "Should find the forcing check"
        },
        {
            "name": "Endgame Technique",
            "fen": "8/5pk1/6p1/3P4/8/6P1/5PKR/r7 w - - 0 1",
            "moves": ["d6", "Rh1", "Kf3", "Rd2"],
            "description": "Finding the winning plan"
        }
    ]
    
    for test in test_cases:
        print_separator(f"Testing: {test['name']}")
        print(f"Description: {test['description']}")
        
        board = chess.Board(test['fen'])
        print(f"\n{board}\n")
        print(f"Comparing moves: {', '.join(test['moves'])}")
        
        result = compare_moves(test['fen'], test['moves'], depth=15)
        print_tool_result("Move Comparison", result)
        
        input("\nPress Enter to continue...")


def test_move_quality():
    """Test move quality analysis."""
    print_separator("PART 3: MOVE QUALITY ANALYSIS")
    
    test_cases = [
        {
            "name": "Good Opening Move",
            "fen": "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
            "move": "e4",
            "expected": "Should be rated as excellent or best"
        },
        {
            "name": "User's Game - 10.a3",
            "fen": "r1bqkb1r/1pp2pp1/p1np1n2/4p3/2BPP3/2N2N2/PPP2PPP/R1BQK2R w KQkq - 0 10",
            "move": "a3",
            "expected": "Questionable move, should show better alternatives"
        },
        {
            "name": "Blunder Example",
            "fen": "r1bqk2r/pppp1ppp/2n2n2/2b1p3/2B1P3/3P1N2/PPP2PPP/RNBQK2R w KQkq - 0 6",
            "move": "a3",
            "expected": "Should identify as mistake, missing Bxf7+"
        }
    ]
    
    for test in test_cases:
        print_separator(f"Testing: {test['name']}")
        print(f"Expected: {test['expected']}")
        
        board = chess.Board(test['fen'])
        print(f"\n{board}\n")
        print(f"Analyzing move: {test['move']}")
        
        result = analyze_move_quality(test['fen'], test['move'], depth=15)
        print_tool_result("Move Quality", result)
        
        input("\nPress Enter to continue...")


def test_full_integration():
    """Test all 5 tools working together on one position."""
    print_separator("PART 4: FULL INTEGRATION TEST - ALL 5 TOOLS")
    
    # Use position from user's game
    fen = "r1bqkb1r/1pp2pp1/p1np1n2/4p3/2BPP3/P1N2N2/1PP2PPP/R1BQK2R b KQkq - 0 10"
    
    print("Position: User's Lichess game after 10.a3")
    board = chess.Board(fen)
    print(f"\n{board}\n")
    print(f"FEN: {fen}\n")
    
    print("Running comprehensive analysis with all 5 tools...")
    print()
    
    # Tool 1: Material
    print("=" * 80)
    print("TOOL 1/5: MATERIAL ANALYSIS")
    print("=" * 80)
    material = analyze_material(fen)
    for ev in material['evidence']:
        print(f"  • {ev}")
    
    # Tool 2: Piece Activity
    print("\n" + "=" * 80)
    print("TOOL 2/5: PIECE ACTIVITY ANALYSIS")
    print("=" * 80)
    activity = analyze_piece_activity(fen)
    for ev in activity['evidence']:
        print(f"  • {ev}")
    
    # Tool 3: King Safety
    print("\n" + "=" * 80)
    print("TOOL 3/5: KING SAFETY ANALYSIS")
    print("=" * 80)
    safety = analyze_king_safety(fen)
    for ev in safety['evidence']:
        print(f"  • {ev}")
    
    # Tool 4: Pawn Structure
    print("\n" + "=" * 80)
    print("TOOL 4/5: PAWN STRUCTURE ANALYSIS")
    print("=" * 80)
    pawns = analyze_pawn_structure(fen)
    for ev in pawns['evidence']:
        print(f"  • {ev}")
    
    # Tool 5: Move Comparison
    print("\n" + "=" * 80)
    print("TOOL 5/5: MOVE COMPARISON (Black to move)")
    print("=" * 80)
    print("Comparing candidate moves: b5, Bb7, O-O, Nxe4")
    moves = compare_moves(fen, ["b5", "Bb7", "O-O", "Nxe4"], depth=15)
    for ev in moves['evidence']:
        print(f"  • {ev}")
    
    print("\n" + "=" * 80)
    print("INTEGRATION TEST SUMMARY")
    print("=" * 80)
    print(f"✓ Material Analysis:      Score {material['score']:+d} cp")
    print(f"✓ Piece Activity:         Score {activity['score']:+d}")
    print(f"✓ King Safety:            Score {safety['score']:+d}")
    print(f"✓ Pawn Structure:         Score {pawns['score']:+d}")
    print(f"✓ Move Comparison:        {len(moves['move_evals'])} moves evaluated")
    print()
    print("All 5 tools integrated successfully!")


def main():
    """Run all tests."""
    print_separator("PHASE 3 CHUNK 2 - ADVANCED TOOLS TEST")
    print("Testing: pawn_structure.py, move_comparison.py")
    print("Integration: All 5 tools working together")
    print()
    
    try:
        # Part 1: Pawn structures
        test_pawn_structures()
        
        # Part 2: Move comparison
        test_move_comparison()
        
        # Part 3: Move quality
        test_move_quality()
        
        # Part 4: Full integration
        test_full_integration()
        
        print_separator("ALL TESTS COMPLETED SUCCESSFULLY")
        print("✓ pawn_structure.py - Tested with 5 different pawn formations")
        print("✓ move_comparison.py - Tested move comparison and quality analysis")
        print("✓ Integration - All 5 tools working together on real position")
        print()
        print("PHASE 3 COMPLETE - All feature extraction tools ready!")
        print()
        print("Tools available:")
        print("  1. analyze_material() - Material counting and imbalances")
        print("  2. analyze_piece_activity() - Mobility, centralization, development")
        print("  3. analyze_king_safety() - King exposure, pawn shield, attackers")
        print("  4. analyze_pawn_structure() - Pawn weaknesses and strengths")
        print("  5. compare_moves() - Engine-based move comparison")
        print("  6. analyze_move_quality() - Move quality classification")
        
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user.")
    except Exception as e:
        print(f"\n\n❌ TEST FAILED WITH ERROR: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
