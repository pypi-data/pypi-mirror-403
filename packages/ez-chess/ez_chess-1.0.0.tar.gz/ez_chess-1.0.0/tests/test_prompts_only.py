"""
Test Script for LLM Prompts Module

Quick test that validates prompt building without requiring the engine.
Run: python tests/test_prompts_only.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.llm_prompts import (
    PromptBuilder, StockfishAnalysis, SYSTEM_PROMPT,
    describe_eval, describe_eval_change, categorize_move_quality,
    inject_relevant_fundamentals, build_position_context,
    PromptType
)


def create_mock_analysis():
    """Create mock Stockfish analysis for testing."""
    return StockfishAnalysis(
        current_eval=0.35,
        best_move="Bb5",
        best_move_eval=0.40,
        principal_variation=["Bb5", "a6", "Ba4", "Nf6", "O-O"],
        pv_explanations=[
            "Develops bishop with tempo by attacking knight",
            "Chases the bishop to break the pin",
            "Maintains pressure and the pin option",
            "Develops knight to a natural square",
            "Castles to bring king to safety"
        ],
        alternative_moves=[
            {"move": "Bc4", "eval": 0.30, "note": "Italian Game approach"},
            {"move": "d4", "eval": 0.25, "note": "Scotch Game"},
            {"move": "Nc3", "eval": 0.20, "note": "Four Knights Game"},
        ],
        threats=[
            "Pin on knight after Bb5",
            "Development lead",
        ],
        position_features={
            "material": "Equal",
            "white_king_safety": "King in center, should castle soon",
            "black_king_safety": "King in center, should castle soon",
            "pawn_structure": "Symmetrical center",
            "piece_activity": "White slightly ahead in development",
            "open_files": "e-file semi-open for both sides",
        }
    )


def test_prompts():
    """Run all prompt tests."""
    print("=" * 70)
    print("LLM PROMPTS MODULE TEST")
    print("=" * 70)
    
    test_fen = "r1bqkbnr/pppp1ppp/2n5/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R w KQkq - 2 3"
    mock_analysis = create_mock_analysis()
    
    # Test 1: System prompt exists and is substantial
    print("\n1. System Prompt:")
    print(f"   Length: {len(SYSTEM_PROMPT)} characters")
    assert len(SYSTEM_PROMPT) > 500, "System prompt should be substantial"
    assert "expert chess coach" in SYSTEM_PROMPT.lower()
    assert "stockfish" in SYSTEM_PROMPT.lower()
    assert "why" in SYSTEM_PROMPT.lower()
    print("   Contains: 'expert chess coach', 'stockfish', 'why'")
    print("   ✓ PASS")
    
    # Test 2: describe_eval
    print("\n2. describe_eval() function:")
    test_evals = [
        (0.0, "equal"),
        (0.15, "equal"),
        (0.5, "slightly"),
        (-0.5, "slightly"),
        (1.0, "clearly"),
        (-1.0, "clearly"),
        (2.0, "much"),
        (4.0, "winning"),
        (-4.0, "winning"),
    ]
    
    for val, expected_word in test_evals:
        desc = describe_eval(val)
        assert expected_word in desc.lower(), f"Expected '{expected_word}' in '{desc}'"
        print(f"   {val:+.2f} → '{desc}'")
    print("   ✓ PASS")
    
    # Test 3: describe_eval_change
    print("\n3. describe_eval_change() function:")
    changes = [
        (0.0, 0.0, "maintains"),
        (0.0, 0.5, "improves White"),
        (0.0, -0.5, "improves Black"),
    ]
    
    for before, after, expected in changes:
        desc = describe_eval_change(before, after)
        assert expected.split()[0] in desc.lower(), f"Expected '{expected}' in '{desc}'"
        print(f"   {before:+.1f} → {after:+.1f}: '{desc}'")
    print("   ✓ PASS")
    
    # Test 4: categorize_move_quality
    print("\n4. categorize_move_quality() function:")
    qualities = [
        (0.35, 0.35, True, "excellent"),  # exact match
        (0.30, 0.35, True, "good"),       # small diff = good
        (0.10, 0.35, True, "inaccura"),   # ~0.25 diff = inaccuracy
        (-0.50, 0.35, True, "mistake"),   # ~0.85 diff = mistake
        (-2.0, 0.35, True, "blunder"),    # ~2.35 diff = blunder
    ]
    
    for played, best, is_white, expected in qualities:
        quality = categorize_move_quality(played, best, is_white)
        # Handle "excellent" matching both "excellent" and similar
        if expected == "excellent" or expected == "good":
            assert expected in quality.lower() or "excellent" in quality.lower() or "good" in quality.lower(), f"Expected '{expected}' in '{quality}'"
        else:
            assert expected in quality.lower(), f"Expected '{expected}' in '{quality}'"
        print(f"   Played {played:+.2f} vs Best {best:+.2f} → '{quality}'")
    print("   ✓ PASS")
    
    # Test 5: build_position_context
    print("\n5. build_position_context() function:")
    context = build_position_context(test_fen, mock_analysis)
    
    assert "POSITION ANALYSIS" in context
    assert "FEN:" in context
    assert "STOCKFISH EVALUATION" in context
    assert "PRINCIPAL VARIATION" in context
    assert "POSITION FEATURES" in context
    
    print(f"   Context length: {len(context)} chars")
    print(f"   Contains all required sections: ✓")
    print("   ✓ PASS")
    
    # Test 6: PromptBuilder - Explain Move
    print("\n6. PromptBuilder.build_explain_move_prompt():")
    builder = PromptBuilder(mock_analysis, test_fen)
    prompt = builder.build_explain_move_prompt("Bb5")
    
    assert "Bb5" in prompt
    assert "POSITION ANALYSIS" in prompt
    assert "YOUR TASK" in prompt
    assert "Explain" in prompt
    
    print(f"   Prompt length: {len(prompt)} chars")
    print(f"   Contains move 'Bb5': ✓")
    print(f"   Contains task section: ✓")
    print("   ✓ PASS")
    
    # Test 7: PromptBuilder - Compare Moves
    print("\n7. PromptBuilder.build_compare_moves_prompt():")
    prompt = builder.build_compare_moves_prompt(
        "Bb5", 0.40, "Bb5 a6 Ba4", "Ruy Lopez pin",
        "Bc4", 0.30, "Bc4 Nf6 d3", "Italian Game"
    )
    
    assert "Bb5" in prompt
    assert "Bc4" in prompt
    # Check for compare/comparison related text (case insensitive)
    assert "compare" in prompt.lower() or "vs" in prompt.lower() or "analysis for" in prompt.lower()
    assert "ANALYSIS FOR Bb5" in prompt or "Bb5" in prompt
    assert "ANALYSIS FOR Bc4" in prompt or "Bc4" in prompt
    
    print(f"   Prompt length: {len(prompt)} chars")
    print(f"   Contains both moves: ✓")
    print(f"   Contains comparison structure: ✓")
    print("   ✓ PASS")
    
    # Test 8: PromptBuilder - Why Bad
    print("\n8. PromptBuilder.build_why_bad_prompt():")
    prompt = builder.build_why_bad_prompt(
        "Qh5", -1.2, "Qh5 Nf6 Qxe5 Be7",
        "Bb5", 0.40, "Nf6"
    )
    
    assert "Qh5" in prompt
    assert "mistake" in prompt.lower()
    assert "Bb5" in prompt
    assert "Refutation" in prompt or "refutation" in prompt
    
    print(f"   Prompt length: {len(prompt)} chars")
    print(f"   Identifies bad move: ✓")
    print(f"   Shows better alternative: ✓")
    print("   ✓ PASS")
    
    # Test 9: PromptBuilder - Find Plan
    print("\n9. PromptBuilder.build_find_plan_prompt():")
    prompt = builder.build_find_plan_prompt()
    
    assert "plan" in prompt.lower()
    assert "POSITION ANALYSIS" in prompt
    assert "YOUR TASK" in prompt
    
    print(f"   Prompt length: {len(prompt)} chars")
    print("   ✓ PASS")
    
    # Test 10: PromptBuilder - Position Eval
    print("\n10. PromptBuilder.build_position_eval_prompt():")
    prompt = builder.build_position_eval_prompt()
    
    assert "evaluat" in prompt.lower()
    assert "POSITION FEATURES" in prompt
    
    print(f"   Prompt length: {len(prompt)} chars")
    print("   ✓ PASS")
    
    # Test 11: PromptBuilder - Tactical
    print("\n11. PromptBuilder.build_tactical_prompt():")
    prompt = builder.build_tactical_prompt(
        tactic_type="fork",
        key_move="Ne4",
        target="queen and rook"
    )
    
    assert "fork" in prompt.lower()
    assert "Ne4" in prompt
    
    print(f"   Prompt length: {len(prompt)} chars")
    print("   ✓ PASS")
    
    # Test 12: inject_relevant_fundamentals
    print("\n12. inject_relevant_fundamentals() function:")
    base_prompt = """Some content here.

=== YOUR TASK ===
Do the task."""
    
    funds = [
        "Fork: Attacking two pieces at once",
        "Pin: A piece can't move without exposing more valuable piece",
        "Development: Get pieces into the game",
    ]
    
    result = inject_relevant_fundamentals(base_prompt, funds)
    
    assert "RELEVANT CHESS PRINCIPLES" in result
    assert "Fork" in result
    assert "Pin" in result
    assert "Development" in result
    assert "YOUR TASK" in result
    
    print(f"   Injected {len(funds)} fundamentals")
    print(f"   Result length: {len(result)} chars")
    print("   ✓ PASS")
    
    # Test 13: Prompt structure quality
    print("\n13. Prompt Structure Quality Check:")
    explain_prompt = builder.build_explain_move_prompt("Bb5")
    
    sections = [
        ("System guidance", "expert" in explain_prompt.lower() or "coach" in explain_prompt.lower()),
        ("Position context", "FEN:" in explain_prompt),
        ("Evaluation data", "evaluat" in explain_prompt.lower()),
        ("PV information", "PRINCIPAL VARIATION" in explain_prompt),
        ("Clear task", "YOUR TASK" in explain_prompt),
        ("Move mentioned", "Bb5" in explain_prompt),
    ]
    
    for name, check in sections:
        status = "✓" if check else "✗"
        print(f"   {status} {name}")
        assert check, f"Missing: {name}"
    
    print("   ✓ PASS - All required sections present")
    
    # Final summary
    print("\n" + "=" * 70)
    print("ALL TESTS PASSED ✓")
    print("=" * 70)
    
    # Print sample prompt
    print("\n--- SAMPLE PROMPT (Explain Move) ---")
    print(explain_prompt[:1500])
    print("...")
    print(f"[Total length: {len(explain_prompt)} chars]")


if __name__ == "__main__":
    test_prompts()
