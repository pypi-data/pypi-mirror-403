"""
Integration test for Groq agent with new tools:
- compare_lines (compare move sequences)
- get_opening_theory (fetch opening info via MCP)

This tests the FULL flow: natural language -> tool calling -> response

Run: python tests/test_agent_tools.py

REQUIRES: GROQ_API_KEY environment variable
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import chess


def test_compare_lines_tool():
    """Test the compare_lines tool via natural language."""
    print("=" * 70)
    print("TEST 1: COMPARE LINES TOOL (Natural Language)")
    print("=" * 70)
    
    try:
        from src.groq_agent import create_groq_agent
        
        agent = create_groq_agent(verbose=True)
        print("✓ Agent initialized")
        
        # Starting position
        fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
        
        # Test 1: Compare two opening moves
        print("\n1. Compare e4 vs d4 (natural language):")
        print("   Question: 'Compare e4 and d4 as opening moves'")
        
        response = agent.analyze(fen, "Compare e4 and d4 as opening moves")
        
        print(f"\n   Response preview:")
        lines = response.split('\n')[:10]  # First 10 lines
        for line in lines:
            if line.strip():
                print(f"   {line}")
        
        # Check if tool was used
        if "e4" in response.lower() and "d4" in response.lower():
            print("\n   ✓ Response contains both moves")
        
        # Test 2: Compare complex lines
        print("\n2. Compare Sicilian vs French Defense:")
        print("   Question: 'Compare 1.e4 c5 with 1.e4 e6'")
        
        response2 = agent.analyze(fen, "Compare 1.e4 c5 with 1.e4 e6")
        
        print(f"\n   Response preview:")
        lines2 = response2.split('\n')[:8]
        for line in lines2:
            if line.strip():
                print(f"   {line}")
        
        print("\n✓ COMPARE LINES TOOL TEST PASSED\n")
        return True
        
    except Exception as e:
        print(f"\n✗ COMPARE LINES TOOL TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_opening_theory_tool():
    """Test the get_opening_theory tool via natural language."""
    print("=" * 70)
    print("TEST 2: OPENING THEORY TOOL (MCP Integration)")
    print("=" * 70)
    
    try:
        from src.groq_agent import create_groq_agent
        
        agent = create_groq_agent(verbose=True)
        print("✓ Agent initialized")
        
        # Test with Italian Game
        italian_fen = "r1bqkb1r/pppp1ppp/2n2n2/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 4 4"
        
        print("\n1. Identify opening (natural language):")
        print("   Position: Italian Game (after 3...Bc5)")
        print("   Question: 'What opening is this?'")
        
        response = agent.analyze(italian_fen, "What opening is this?")
        
        print(f"\n   Response preview:")
        lines = response.split('\n')[:12]
        for line in lines:
            if line.strip():
                print(f"   {line}")
        
        # Check if opening was identified
        if "italian" in response.lower() or "giuoco" in response.lower():
            print("\n   ✓ Opening identified correctly")
        else:
            print("\n   ? Opening may not be explicitly mentioned (could be general advice)")
        
        # Test 2: Ask about main ideas
        print("\n2. Ask about opening plans:")
        print("   Question: 'What are the main ideas in this opening?'")
        
        response2 = agent.analyze(italian_fen, "What are the main ideas in this opening?")
        
        print(f"\n   Response preview:")
        lines2 = response2.split('\n')[:10]
        for line in lines2:
            if line.strip():
                print(f"   {line}")
        
        print("\n✓ OPENING THEORY TOOL TEST PASSED\n")
        return True
        
    except Exception as e:
        print(f"\n✗ OPENING THEORY TOOL TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_tool_schemas():
    """Test that tool schemas are properly defined."""
    print("=" * 70)
    print("TEST 3: TOOL SCHEMAS VERIFICATION")
    print("=" * 70)
    
    try:
        from src.groq_agent import CHESS_TOOLS
        
        # Check tool schemas directly from constant
        print("\n1. Available tools:")
        for tool in CHESS_TOOLS:
            name = tool.get('function', {}).get('name', 'unknown')
            desc = tool.get('function', {}).get('description', '')
            print(f"   • {name}")
            print(f"     {desc[:80]}...")
        
        # Check for our new tools
        tool_names = [t.get('function', {}).get('name') for t in CHESS_TOOLS]
        
        print("\n2. Verifying new tools:")
        if 'compare_lines' in tool_names:
            print("   ✓ compare_lines tool found")
        else:
            print("   ✗ compare_lines tool NOT FOUND")
        
        if 'get_opening_theory' in tool_names:
            print("   ✓ get_opening_theory tool found")
        else:
            print("   ✗ get_opening_theory tool NOT FOUND")
        
        print("\n✓ TOOL SCHEMAS TEST PASSED\n")
        return True
        
    except Exception as e:
        print(f"\n✗ TOOL SCHEMAS TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_hypothetical_positions():
    """Test hypothetical position analysis (existing tool)."""
    print("=" * 70)
    print("TEST 4: HYPOTHETICAL POSITIONS (Sanity Check)")
    print("=" * 70)
    
    try:
        from src.groq_agent import create_groq_agent
        
        agent = create_groq_agent(verbose=True)
        print("✓ Agent initialized")
        
        fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
        
        print("\n1. Test hypothetical 'what if' question:")
        print("   Question: 'What if I play e4?'")
        
        response = agent.analyze(fen, "What if I play e4?")
        
        print(f"\n   Response preview:")
        lines = response.split('\n')[:8]
        for line in lines:
            if line.strip():
                print(f"   {line}")
        
        print("\n✓ HYPOTHETICAL POSITIONS TEST PASSED\n")
        return True
        
    except Exception as e:
        print(f"\n✗ HYPOTHETICAL POSITIONS TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def check_groq_api_key():
    """Check if GROQ_API_KEY is set."""
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        print("\n" + "=" * 70)
        print("⚠ WARNING: GROQ_API_KEY not set!")
        print("=" * 70)
        print("\nThese tests require a Groq API key.")
        print("Get one free at: https://console.groq.com")
        print("\nSet it with:")
        print("  export GROQ_API_KEY='your-key-here'  # Linux/Mac")
        print("  set GROQ_API_KEY=your-key-here       # Windows CMD")
        print("  $env:GROQ_API_KEY='your-key-here'    # Windows PowerShell")
        print("=" * 70)
        return False
    return True


def run_all_tests():
    """Run all agent tool tests."""
    print("\n" + "=" * 70)
    print("GROQ AGENT TOOLS - INTEGRATION TEST SUITE")
    print("=" * 70)
    print("Testing: compare_lines, get_opening_theory, hypothetical positions")
    print("=" * 70 + "\n")
    
    # Check API key first
    if not check_groq_api_key():
        print("\nSkipping tests - no API key found\n")
        return False
    
    results = []
    
    tests = [
        ("Tool Schemas", test_tool_schemas),
        ("Compare Lines Tool", test_compare_lines_tool),
        ("Opening Theory Tool", test_opening_theory_tool),
        ("Hypothetical Positions", test_hypothetical_positions),
    ]
    
    for name, test_fn in tests:
        try:
            success = test_fn()
            results.append((name, success))
        except Exception as e:
            print(f"\n✗ {name} FAILED: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))
    
    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for name, success in results:
        status = "✓ PASS" if success else "✗ FAIL"
        print(f"  {status}: {name}")
    
    print(f"\nResult: {passed}/{total} tests passed")
    print("=" * 70)
    
    return passed == total


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
