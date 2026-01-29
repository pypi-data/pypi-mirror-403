"""
Test Script for Deep Analysis Module

This tests the multi-move lookahead and explanation generation.
Requires the chess engine.

Run: python tests/test_deep_analysis_only.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.deep_analysis import (
    DeepAnalyzer, DeepAnalysis, MoveRole, MoveExplanation,
    format_deep_analysis_for_llm
)


def test_deep_analysis():
    """Run all deep analysis tests."""
    print("=" * 70)
    print("DEEP ANALYSIS MODULE TEST")
    print("=" * 70)
    
    print("\nInitializing DeepAnalyzer...")
    analyzer = DeepAnalyzer()
    print("✓ DeepAnalyzer initialized")
    
    try:
        # Test 1: Basic position analysis
        print("\n1. Basic Position Analysis:")
        fen = "r1bqkbnr/pppp1ppp/2n5/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R w KQkq - 2 3"
        
        analysis = analyzer.analyze_position(fen, depth=14, num_pv_moves=5)
        
        print(f"   FEN: {fen[:40]}...")
        print(f"   Best move: {analysis.best_move}")
        print(f"   Eval: {analysis.current_eval:+.2f}")
        print(f"   PV: {' '.join(analysis.principal_variation[:4])}")
        print(f"   Phase: {analysis.game_phase}")
        
        assert analysis.best_move, "Should find a best move"
        assert isinstance(analysis.current_eval, float), "Should have evaluation"
        assert len(analysis.principal_variation) >= 1, "Should have PV"
        print("   ✓ PASS")
        
        # Test 2: PV Explanations
        print("\n2. PV Move Explanations:")
        print(f"   Number of explained moves: {len(analysis.pv_explanations)}")
        
        for i, exp in enumerate(analysis.pv_explanations[:4]):
            print(f"\n   Move {i+1}: {exp.move_san}")
            print(f"   Role: {exp.role.value}")
            print(f"   What: {exp.what_it_does}")
            print(f"   Why: {exp.why_it_matters}")
            
            assert exp.move_san, "Should have SAN notation"
            assert isinstance(exp.role, MoveRole), "Should have role"
            assert exp.what_it_does, "Should describe action"
        
        print("\n   ✓ PASS")
        
        # Test 3: Position Features
        print("\n3. Position Features:")
        print(f"   Material: {analysis.material_balance}")
        print(f"   Activity: {analysis.piece_activity}")
        print(f"   King Safety (W): {analysis.king_safety.get('White')}")
        print(f"   King Safety (B): {analysis.king_safety.get('Black')}")
        print(f"   Pawn notes: {analysis.pawn_structure_notes}")
        print(f"   Open files: {analysis.open_files}")
        print(f"   Tactical: {analysis.tactical_motifs}")
        
        assert isinstance(analysis.material_balance, str), "Should have material balance"
        assert isinstance(analysis.king_safety, dict), "Should have king safety"
        print("   ✓ PASS")
        
        # Test 4: Alternative Moves
        print("\n4. Alternative Moves:")
        print(f"   Number of alternatives: {len(analysis.alternative_moves)}")
        
        for alt in analysis.alternative_moves:
            print(f"   - {alt['move']}: {alt['eval']:+.2f} ({alt.get('note', '')})")
        
        print("   ✓ PASS")
        
        # Test 5: Threats
        print("\n5. Threat Detection:")
        print(f"   Our threats: {analysis.threats}")
        print(f"   Opponent threats: {analysis.opponent_threats}")
        print("   ✓ PASS")
        
        # Test 6: Analyze Specific Move
        print("\n6. Specific Move Analysis (Bb5):")
        move_result = analyzer.analyze_move(fen, "Bb5", depth=14)
        
        print(f"   Move: {move_result['move']}")
        print(f"   Eval after: {move_result['eval_after']:+.2f}")
        print(f"   Quality: {move_result['quality']}")
        print(f"   Best was: {move_result['best_move']}")
        print(f"   Continuation: {' '.join(move_result['continuation'][:3])}")
        
        if move_result.get('continuation_explained'):
            print(f"   Explained: {move_result['continuation_explained']}")
        
        assert 'move' in move_result, "Should have move"
        assert 'quality' in move_result, "Should have quality"
        print("   ✓ PASS")
        
        # Test 7: Analyze a Sub-optimal Move
        print("\n7. Sub-optimal Move Analysis (a3):")
        move_result = analyzer.analyze_move(fen, "a3", depth=14)
        
        print(f"   Move: {move_result['move']}")
        print(f"   Eval after: {move_result['eval_after']:+.2f}")
        print(f"   Quality: {move_result['quality']}")
        print("   ✓ PASS")
        
        # Test 8: Format for LLM
        print("\n8. Format for LLM:")
        formatted = format_deep_analysis_for_llm(analysis)
        
        print(f"   Output length: {len(formatted)} chars")
        
        assert "POSITION ANALYSIS" in formatted
        assert "BEST MOVE" in formatted
        assert "PRINCIPAL VARIATION" in formatted
        assert "POSITION FEATURES" in formatted
        
        print("   Contains all required sections: ✓")
        print("   ✓ PASS")
        
        # Test 9: Different Position Types
        print("\n9. Testing Different Position Types:")
        
        # Endgame position
        endgame_fen = "8/5pk1/5p1p/8/8/5P1P/5PK1/8 w - - 0 1"
        endgame = analyzer.analyze_position(endgame_fen, depth=12)
        print(f"   Endgame phase: {endgame.game_phase}")
        assert endgame.game_phase == "endgame", "Should detect endgame"
        
        # Opening position
        opening_fen = "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq - 0 1"
        opening = analyzer.analyze_position(opening_fen, depth=12)
        print(f"   Opening phase: {opening.game_phase}")
        
        print("   ✓ PASS")
        
        # Test 10: Move Roles
        print("\n10. Testing Move Role Classification:")
        
        # Castling
        castle_fen = "r1bqk2r/pppp1ppp/2n2n2/2b1p3/2B1P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 4 4"
        castle_analysis = analyzer.analyze_position(castle_fen, depth=12)
        
        print(f"   Position: Italian Game")
        print(f"   Best move: {castle_analysis.best_move}")
        for exp in castle_analysis.pv_explanations[:3]:
            print(f"   - {exp.move_san}: {exp.role.value}")
        
        print("   ✓ PASS")
        
        # Print sample LLM-formatted output
        print("\n" + "=" * 70)
        print("SAMPLE LLM-FORMATTED OUTPUT:")
        print("=" * 70)
        print(formatted[:1500])
        print("...")
        print(f"[Total length: {len(formatted)} chars]")
        
        print("\n" + "=" * 70)
        print("ALL TESTS PASSED ✓")
        print("=" * 70)
        
    finally:
        analyzer.engine.close()
        print("\n✓ Engine closed")


if __name__ == "__main__":
    test_deep_analysis()
