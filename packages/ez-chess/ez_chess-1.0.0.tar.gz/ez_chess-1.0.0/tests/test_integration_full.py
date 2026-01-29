"""
Integration Test - Full LLM Context Generation

This test demonstrates the complete flow from question to LLM-ready context.
Does NOT call the LLM - just shows what would be sent.

Run: python tests/test_integration_full.py
"""

import sys
import os
import json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.enhanced_explainability import EnhancedExplainabilityService


def test_integration():
    """Run full integration tests."""
    print("=" * 70)
    print("FULL INTEGRATION TEST - LLM CONTEXT GENERATION")
    print("=" * 70)
    print("\nThis test shows what would be sent to the LLM (no actual LLM calls)")
    
    print("\nInitializing EnhancedExplainabilityService...")
    service = EnhancedExplainabilityService(engine_depth=14)
    print("✓ Service initialized\n")
    
    import atexit
    atexit.register(lambda: service.close())
    
    # Test positions
    positions = {
        "opening": {
            "fen": "r1bqkbnr/pppp1ppp/2n5/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R w KQkq - 2 3",
            "name": "After 1.e4 e5 2.Nf3 Nc6",
        },
        "italian": {
            "fen": "r1bqk2r/pppp1ppp/2n2n2/2b1p3/2B1P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 4 4",
            "name": "Italian Game",
        },
        "middlegame": {
            "fen": "r2qkb1r/pp2pppp/2n2n2/3p1b2/3P4/2N2N2/PPP1BPPP/R1BQK2R w KQkq - 2 7",
            "name": "Middlegame position",
        },
    }
    
    try:
        # ================================================================
        # TEST 1: Explain Move
        # ================================================================
        print("=" * 70)
        print("TEST 1: EXPLAIN MOVE")
        print("=" * 70)
        
        pos = positions["opening"]
        context = service.get_llm_context(
            "Why is Bb5 a good move?",
            pos["fen"],
            move="Bb5"
        )
        
        print(f"\nPosition: {pos['name']}")
        print(f"Question: 'Why is Bb5 a good move?'")
        print(f"Question type: {context.question_type}")
        print(f"Interpreted as: {context.question_interpreted}")
        print(f"\nKey Facts:")
        for fact in context.key_facts:
            print(f"  • {fact}")
        
        print(f"\nFundamentals considered: {context.fundamentals}")
        print(f"\nStockfish eval: {context.stockfish_eval:+.2f}")
        print(f"Best move: {context.best_move}")
        print(f"PV: {' '.join(context.principal_variation[:4])}")
        
        print(f"\nPV Explanations:")
        for i, exp in enumerate(context.pv_explanations[:3]):
            print(f"  {i+1}. {exp['move']} ({exp['role']}): {exp['what']}")
        
        print(f"\nPrompt length: {len(context.prompt)} chars")
        print("\n--- PROMPT PREVIEW (first 1000 chars) ---")
        print(context.prompt[:1000])
        print("...")
        
        # ================================================================
        # TEST 2: Compare Moves
        # ================================================================
        print("\n" + "=" * 70)
        print("TEST 2: COMPARE MOVES")
        print("=" * 70)
        
        context = service.get_llm_context(
            "Which is better, Bb5 or Bc4?",
            pos["fen"],
            move="Bb5",
            compare_move="Bc4"
        )
        
        print(f"\nQuestion: 'Which is better, Bb5 or Bc4?'")
        print(f"Question type: {context.question_type}")
        print(f"\nKey Facts:")
        for fact in context.key_facts:
            print(f"  • {fact}")
        
        print(f"\nPrompt length: {len(context.prompt)} chars")
        
        # ================================================================
        # TEST 3: Why Bad
        # ================================================================
        print("\n" + "=" * 70)
        print("TEST 3: WHY IS THIS BAD")
        print("=" * 70)
        
        context = service.get_llm_context(
            "Why is Qh5 a mistake here?",
            pos["fen"],
            move="Qh5"
        )
        
        print(f"\nQuestion: 'Why is Qh5 a mistake here?'")
        print(f"Question type: {context.question_type}")
        print(f"\nKey Facts:")
        for fact in context.key_facts:
            print(f"  • {fact}")
        
        print(f"\nPrompt length: {len(context.prompt)} chars")
        
        # ================================================================
        # TEST 4: What to Play
        # ================================================================
        print("\n" + "=" * 70)
        print("TEST 4: WHAT TO PLAY")
        print("=" * 70)
        
        pos = positions["italian"]
        context = service.get_llm_context(
            "What should I play here?",
            pos["fen"]
        )
        
        print(f"\nPosition: {pos['name']}")
        print(f"Question: 'What should I play here?'")
        print(f"Question type: {context.question_type}")
        print(f"\nKey Facts:")
        for fact in context.key_facts:
            print(f"  • {fact}")
        
        print(f"\nBest move: {context.best_move}")
        print(f"PV: {' '.join(context.principal_variation[:4])}")
        
        # ================================================================
        # TEST 5: Find Plan
        # ================================================================
        print("\n" + "=" * 70)
        print("TEST 5: FIND THE PLAN")
        print("=" * 70)
        
        context = service.get_llm_context(
            "What is the plan in this position?",
            pos["fen"]
        )
        
        print(f"\nQuestion: 'What is the plan in this position?'")
        print(f"Question type: {context.question_type}")
        print(f"\nKey Facts:")
        for fact in context.key_facts:
            print(f"  • {fact}")
        
        print(f"\nPV Explanations:")
        for i, exp in enumerate(context.pv_explanations[:4]):
            print(f"  {i+1}. {exp['move']} ({exp['role']})")
            print(f"     What: {exp['what']}")
            print(f"     Why: {exp['why']}")
        
        print(f"\nPrompt length: {len(context.prompt)} chars")
        
        # ================================================================
        # TEST 6: Evaluate Position
        # ================================================================
        print("\n" + "=" * 70)
        print("TEST 6: EVALUATE POSITION")
        print("=" * 70)
        
        pos = positions["middlegame"]
        context = service.get_llm_context(
            "Who is better in this position?",
            pos["fen"]
        )
        
        print(f"\nPosition: {pos['name']}")
        print(f"Question: 'Who is better in this position?'")
        print(f"Question type: {context.question_type}")
        print(f"\nKey Facts:")
        for fact in context.key_facts:
            print(f"  • {fact}")
        
        print(f"\nStockfish eval: {context.stockfish_eval:+.2f}")
        
        # ================================================================
        # TEST 7: Explain Concept
        # ================================================================
        print("\n" + "=" * 70)
        print("TEST 7: EXPLAIN CONCEPT")
        print("=" * 70)
        
        context = service.get_llm_context(
            "What is a fork?",
            pos["fen"]
        )
        
        print(f"\nQuestion: 'What is a fork?'")
        print(f"Question type: {context.question_type}")
        print(f"Fundamentals: {context.fundamentals}")
        
        print(f"\nPrompt length: {len(context.prompt)} chars")
        print("\n--- CONCEPT PROMPT PREVIEW ---")
        print(context.prompt[:800])
        print("...")
        
        # ================================================================
        # TEST 8: Simple Analysis (no LLM prompt)
        # ================================================================
        print("\n" + "=" * 70)
        print("TEST 8: SIMPLE ANALYSIS (Structured Data Only)")
        print("=" * 70)
        
        pos = positions["opening"]
        result = service.get_simple_analysis(pos["fen"], move="Nf3")
        
        print(f"\nPosition: {pos['name']}")
        print(f"Eval: {result['eval']:+.2f} ({result['eval_description']})")
        print(f"Best move: {result['best_move']}")
        print(f"PV: {result['principal_variation'][:4]}")
        print(f"Phase: {result['phase']}")
        print(f"Material: {result['material']}")
        print(f"King safety: {result['king_safety']}")
        
        if result.get('move_analysis'):
            ma = result['move_analysis']
            print(f"\nMove Nf3 analysis:")
            print(f"  Quality: {ma['quality']}")
            print(f"  Eval after: {ma['eval_after']:+.2f}")
            print(f"  Continuation: {ma['continuation'][:3]}")
        
        print("\n" + "=" * 70)
        print("ALL INTEGRATION TESTS COMPLETED ✓")
        print("=" * 70)
        
        # Summary
        print("\n--- SUMMARY ---")
        print("The LLM context includes:")
        print("  1. System prompt with coaching instructions")
        print("  2. Position analysis (FEN, eval, material, etc.)")
        print("  3. Multi-move principal variation with explanations")
        print("  4. Alternative moves considered")
        print("  5. Threats and position features")
        print("  6. Relevant chess fundamentals")
        print("  7. Clear task instructions for the LLM")
        print("\nThis provides the LLM with everything needed to give")
        print("accurate, grounded explanations based on Stockfish analysis.")
        
    finally:
        service.close()
        print("\n✓ Service closed")


if __name__ == "__main__":
    test_integration()
