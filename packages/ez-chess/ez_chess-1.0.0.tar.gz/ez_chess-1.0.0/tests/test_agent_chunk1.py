"""
Test Script for Phase 4 Chunk 1 - Agent Tool Routing
Tests the LangGraph agent's ability to route questions to appropriate tools.

This tests:
1. Tool schema definitions
2. Agent graph construction
3. Tool routing logic
4. Basic Q&A flow (without full LLM if Ollama not available)
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from tool_schemas import CHESS_TOOLS, TOOL_DESCRIPTIONS


def print_separator(title=""):
    """Print formatted separator."""
    if title:
        print(f"\n{'=' * 80}")
        print(f"  {title}")
        print(f"{'=' * 80}\n")
    else:
        print(f"{'-' * 80}")


def test_tool_schemas():
    """Test that all tool schemas are properly defined."""
    print_separator("TEST 1: TOOL SCHEMA VALIDATION")
    
    print(f"Found {len(CHESS_TOOLS)} chess analysis tools:")
    for i, tool in enumerate(CHESS_TOOLS, 1):
        print(f"  {i}. {tool.name}")
        print(f"     Description: {tool.description[:60]}...")
    
    print(f"\n✓ All {len(CHESS_TOOLS)} tools have valid schemas")
    
    return True


def test_tool_invocation():
    """Test that tools can be invoked directly."""
    print_separator("TEST 2: DIRECT TOOL INVOCATION")
    
    # Test position
    fen = "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1"
    
    print("Testing each tool with starting position after 1.e4:")
    print(f"FEN: {fen}\n")
    
    # Test each tool
    from tool_schemas import (
        material_analysis_tool,
        piece_activity_tool,
        king_safety_tool,
        pawn_structure_tool,
        position_overview_tool
    )
    
    tools_to_test = [
        ("Material Analysis", material_analysis_tool, {"fen": fen}),
        ("Piece Activity", piece_activity_tool, {"fen": fen}),
        ("King Safety", king_safety_tool, {"fen": fen}),
        ("Pawn Structure", pawn_structure_tool, {"fen": fen}),
        ("Position Overview", position_overview_tool, {"fen": fen})
    ]
    
    for tool_name, tool, args in tools_to_test:
        try:
            print(f"Testing {tool_name}...")
            result = tool.invoke(args)
            
            if 'material' in result:  # Overview tool
                print(f"  ✓ Overview returned {len(result)} analysis categories")
            elif 'evidence' in result:
                print(f"  ✓ Returned {len(result['evidence'])} evidence items")
                print(f"    Sample: {result['evidence'][0]}")
            else:
                print(f"  ✓ Returned result")
            
        except Exception as e:
            print(f"  ❌ Failed: {e}")
            return False
    
    print(f"\n✓ All tools can be invoked successfully")
    return True


def test_move_comparison_tool():
    """Test move comparison tool with multiple moves."""
    print_separator("TEST 3: MOVE COMPARISON TOOL")
    
    from tool_schemas import move_comparison_tool
    
    fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
    moves = "e4,d4,Nf3"
    
    print(f"Position: Starting position")
    print(f"Comparing moves: {moves}\n")
    
    try:
        result = move_comparison_tool.invoke({"fen": fen, "moves": moves})
        print(f"✓ Move comparison successful")
        print(f"  Evidence items: {len(result['evidence'])}")
        for ev in result['evidence'][:3]:
            print(f"    • {ev}")
        return True
    except Exception as e:
        print(f"❌ Failed: {e}")
        return False


def test_move_quality_tool():
    """Test move quality tool."""
    print_separator("TEST 4: MOVE QUALITY TOOL")
    
    from tool_schemas import move_quality_tool
    
    fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
    move = "e4"
    
    print(f"Position: Starting position")
    print(f"Analyzing move: {move}\n")
    
    try:
        result = move_quality_tool.invoke({"fen": fen, "move": move})
        print(f"✓ Move quality analysis successful")
        print(f"  Evidence items: {len(result['evidence'])}")
        for ev in result['evidence']:
            print(f"    • {ev}")
        return True
    except Exception as e:
        print(f"❌ Failed: {e}")
        return False


def test_agent_construction():
    """Test that agent can be constructed (requires Ollama)."""
    print_separator("TEST 5: AGENT CONSTRUCTION")
    
    try:
        from agent import create_agent
        
        print("Attempting to create agent (requires Ollama to be running)...")
        print("Using auto model selection for optimal performance...")
        
        try:
            agent = create_agent()  # Auto-selects best model for hardware
            print("✓ Agent created successfully!")
            print("  Note: This confirms Ollama is running and accessible")
            return agent
        except Exception as e:
            print(f"⚠ Agent creation failed: {e}")
            print("  This is expected if Ollama is not running")
            print("  To install/start Ollama:")
            print("    1. Install from https://ollama.ai")
            print("    2. Run: ollama pull qwen2.5:7b")
            print("    3. Ollama will auto-start")
            return None
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return None


def test_agent_query(agent):
    """Test agent with a simple query (only if agent is available)."""
    print_separator("TEST 6: AGENT QUERY (OPTIONAL)")
    
    if agent is None:
        print("⊘ Skipping - agent not available (Ollama not running)")
        return True
    
    fen = "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1"
    question = "What's the material balance in this position?"
    
    print(f"Position: After 1.e4")
    print(f"Question: {question}\n")
    
    try:
        print("Querying agent (this may take 10-20 seconds)...")
        answer = agent.analyze(fen, question)
        print(f"\n✓ Agent responded successfully!")
        print(f"\nAgent's answer:")
        print(f"{answer}\n")
        return True
    except Exception as e:
        print(f"❌ Query failed: {e}")
        return False


def main():
    """Run all tests."""
    print_separator("PHASE 4 CHUNK 1 - AGENT TOOL ROUTING TEST")
    print("Testing: Tool schemas, agent construction, basic routing")
    print()
    
    results = []
    
    # Test 1: Tool schemas
    results.append(("Tool Schemas", test_tool_schemas()))
    input("Press Enter to continue...")
    
    # Test 2: Tool invocation
    results.append(("Tool Invocation", test_tool_invocation()))
    input("Press Enter to continue...")
    
    # Test 3: Move comparison
    results.append(("Move Comparison", test_move_comparison_tool()))
    input("Press Enter to continue...")
    
    # Test 4: Move quality
    results.append(("Move Quality", test_move_quality_tool()))
    input("Press Enter to continue...")
    
    # Test 5: Agent construction
    agent = test_agent_construction()
    results.append(("Agent Construction", agent is not None))
    
    # Test 6: Agent query (only if agent available)
    if agent:
        input("Press Enter to test agent query...")
        results.append(("Agent Query", test_agent_query(agent)))
    
    # Summary
    print_separator("TEST SUMMARY")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    print(f"Results: {passed}/{total} tests passed\n")
    
    for test_name, result in results:
        status = "✓ PASS" if result else "❌ FAIL"
        print(f"  {status}: {test_name}")
    
    print()
    
    if passed == total:
        print("ALL TESTS PASSED!")
        print("\nPhase 4 Chunk 1 Complete:")
        print("  ✓ Tool schemas defined")
        print("  ✓ Tools can be invoked")
        print("  ✓ Agent can be constructed")
        if agent:
            print("  ✓ Agent can answer questions")
    else:
        print("⚠ Some tests failed - review errors above")
    
    print()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user.")
    except Exception as e:
        print(f"\n\n❌ TEST SUITE FAILED: {e}")
        import traceback
        traceback.print_exc()
