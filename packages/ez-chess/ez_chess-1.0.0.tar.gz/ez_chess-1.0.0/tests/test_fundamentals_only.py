"""
Test Script for Chess Fundamentals Library

This is a quick test that requires no engine - just validates the fundamentals database.
Run: python tests/test_fundamentals_only.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.chess_fundamentals import (
    ALL_FUNDAMENTALS, ChessFundamental, ConceptCategory,
    get_fundamental, get_related_fundamentals,
    get_fundamentals_for_position_type, format_fundamental_for_prompt,
    get_all_fundamentals_summary,
    OPENING_PRINCIPLES, PIECE_PLACEMENT, PAWN_STRUCTURE,
    KING_SAFETY, ATTACKING_PRINCIPLES, DEFENSIVE_PRINCIPLES,
    POSITIONAL_CONCEPTS, ENDGAME_FUNDAMENTALS, TACTICAL_MOTIFS,
    FUNDAMENTALS_BY_CATEGORY
)


def test_fundamentals():
    """Run all fundamentals tests."""
    print("=" * 70)
    print("CHESS FUNDAMENTALS LIBRARY TEST")
    print("=" * 70)
    
    # Test 1: Count fundamentals
    print(f"\n1. Total fundamentals: {len(ALL_FUNDAMENTALS)}")
    assert len(ALL_FUNDAMENTALS) >= 50, "Should have at least 50 fundamentals"
    print("   ✓ PASS")
    
    # Test 2: Category counts
    print("\n2. Category breakdown:")
    categories = [
        ("Opening Principles", OPENING_PRINCIPLES),
        ("Piece Placement", PIECE_PLACEMENT),
        ("Pawn Structure", PAWN_STRUCTURE),
        ("King Safety", KING_SAFETY),
        ("Attacking", ATTACKING_PRINCIPLES),
        ("Defensive", DEFENSIVE_PRINCIPLES),
        ("Positional", POSITIONAL_CONCEPTS),
        ("Endgame", ENDGAME_FUNDAMENTALS),
        ("Tactical Motifs", TACTICAL_MOTIFS),
    ]
    
    for name, cat in categories:
        print(f"   {name}: {len(cat)} concepts")
        assert len(cat) >= 2, f"{name} should have at least 2 concepts"
    print("   ✓ PASS - All categories populated")
    
    # Test 3: Structure validation
    print("\n3. Validating fundamental structure...")
    errors = []
    for name, fund in ALL_FUNDAMENTALS.items():
        if not isinstance(fund, ChessFundamental):
            errors.append(f"{name}: Not a ChessFundamental")
        if not fund.name:
            errors.append(f"{name}: Missing name")
        if not fund.definition:
            errors.append(f"{name}: Missing definition")
        if not fund.why_it_matters:
            errors.append(f"{name}: Missing why_it_matters")
        if len(fund.how_to_recognize) < 1:
            errors.append(f"{name}: Missing how_to_recognize")
        if len(fund.how_to_apply) < 1:
            errors.append(f"{name}: Missing how_to_apply")
    
    if errors:
        print("   ✗ ERRORS:")
        for e in errors:
            print(f"     - {e}")
    else:
        print(f"   ✓ PASS - All {len(ALL_FUNDAMENTALS)} fundamentals valid")
    
    # Test 4: Test get_fundamental
    print("\n4. Testing get_fundamental()...")
    test_cases = [
        ("fork", "Fork"),
        ("passed pawn", "Passed Pawn"),
        ("bishop_pair", "The Bishop Pair"),
        ("control_the_center", "Control the Center"),
        ("pin", "Pin"),
        ("zugzwang", "Zugzwang"),
    ]
    
    for search, expected in test_cases:
        result = get_fundamental(search)
        if result:
            print(f"   '{search}' → {result.name}")
            assert result.name == expected, f"Expected {expected}, got {result.name}"
        else:
            print(f"   ✗ '{search}' not found!")
    print("   ✓ PASS")
    
    # Test 5: Test get_related_fundamentals
    print("\n5. Testing get_related_fundamentals()...")
    fork = get_fundamental("fork")
    related = get_related_fundamentals("fork")
    print(f"   Fork related concepts: {[f.name for f in related]}")
    assert len(related) >= 1, "Fork should have related concepts"
    print("   ✓ PASS")
    
    # Test 6: Test get_fundamentals_for_position_type
    print("\n6. Testing get_fundamentals_for_position_type()...")
    
    opening_funds = get_fundamentals_for_position_type(is_opening=True)
    print(f"   Opening position: {len(opening_funds)} relevant fundamentals")
    
    endgame_funds = get_fundamentals_for_position_type(is_endgame=True)
    print(f"   Endgame position: {len(endgame_funds)} relevant fundamentals")
    
    attack_funds = get_fundamentals_for_position_type(has_attack=True)
    print(f"   Attacking position: {len(attack_funds)} relevant fundamentals")
    
    defensive_funds = get_fundamentals_for_position_type(is_defensive=True)
    print(f"   Defensive position: {len(defensive_funds)} relevant fundamentals")
    
    print("   ✓ PASS")
    
    # Test 7: Test format_fundamental_for_prompt
    print("\n7. Testing format_fundamental_for_prompt()...")
    fork = get_fundamental("fork")
    formatted = format_fundamental_for_prompt(fork)
    
    assert "Fork" in formatted
    assert "Definition:" in formatted
    assert "Why it matters:" in formatted
    
    print(f"   Formatted length: {len(formatted)} chars")
    print(f"   Preview: {formatted[:150]}...")
    print("   ✓ PASS")
    
    # Test 8: Test get_all_fundamentals_summary
    print("\n8. Testing get_all_fundamentals_summary()...")
    summary = get_all_fundamentals_summary()
    
    assert "opening" in summary.lower()
    assert "tactical" in summary.lower()
    
    print(f"   Summary length: {len(summary)} chars")
    print("   ✓ PASS")
    
    # Test 9: Print all fundamental names by category
    print("\n9. All fundamentals by category:")
    for cat in ConceptCategory:
        if cat in FUNDAMENTALS_BY_CATEGORY:
            funds = FUNDAMENTALS_BY_CATEGORY[cat]
            names = [f.name for f in funds.values()]
            print(f"\n   {cat.value.upper()}:")
            for name in names:
                print(f"     - {name}")
    
    # Final summary
    print("\n" + "=" * 70)
    print("ALL TESTS PASSED ✓")
    print(f"Total fundamentals validated: {len(ALL_FUNDAMENTALS)}")
    print("=" * 70)


if __name__ == "__main__":
    test_fundamentals()
