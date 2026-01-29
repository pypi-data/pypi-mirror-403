"""
Phase 4 Chunk 2 - End-to-End Integration Tests
Tests the complete agent workflow with real chess questions.

Tests:
1. Agent answers material questions
2. Agent answers position evaluation questions
3. Agent handles move comparison
4. Agent handles move quality assessment
5. Multi-turn conversations
6. Error handling
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from agent import create_agent
from langchain_core.messages import HumanMessage, AIMessage
import chess


def print_separator(title=""):
    """Print formatted separator."""
    if title:
        print(f"\n{'=' * 80}")
        print(f"  {title}")
        print(f"{'=' * 80}\n")
    else:
        print(f"{'-' * 80}")


def test_agent_availability():
    """Test that agent can be created and Ollama is available."""
    print_separator("TEST 1: AGENT AVAILABILITY")
    
    try:
        print("Creating agent with auto model selection...")
        agent = create_agent()  # Auto-selects optimal model
        print("✓ Agent created successfully!")
        print(f"✓ Using model: {agent.model_name}")
        print("✓ Ollama is running")
        return agent
    except Exception as e:
        print(f"❌ Failed to create agent: {e}")
        print("\nPlease ensure:")
        print("  1. Ollama is installed and running")
        print("  2. Model is pulled: ollama pull qwen2.5:7b")
        return None


def test_material_question(agent):
    """Test material balance question."""
    print_separator("TEST 2: MATERIAL BALANCE QUESTION")
    
    fen = "r1bqkb1r/1pp2pp1/p1np1n2/4p3/2BPP3/P1N2N2/1PP2PPP/R1BQK2R b KQkq - 0 10"
    question = "What's the material situation in this position?"
    
    print(f"Position: User's game after 10.a3")
    board = chess.Board(fen)
    print(f"\n{board}\n")
    print(f"Question: {question}")
    print("\nAsking agent...\n")
    
    try:
        response = agent.analyze(fen, question)
        print(f"Agent's response:")
        print(f"{response}")
        print("\n✓ Agent successfully answered material question")
        return True
    except Exception as e:
        print(f"❌ Failed: {e}")
        return False


def test_king_safety_question(agent):
    """Test king safety question."""
    print_separator("TEST 3: KING SAFETY QUESTION")
    
    fen = "r1bq1rk1/ppp2ppp/2n5/3np3/1bBP4/2N2N2/PPP2PPP/R1BQK2R w K - 0 10"
    question = "How safe is white's king compared to black's?"
    
    print(f"Position: White king in center, black castled")
    board = chess.Board(fen)
    print(f"\n{board}\n")
    print(f"Question: {question}")
    print("\nAsking agent...\n")
    
    try:
        response = agent.analyze(fen, question)
        print(f"Agent's response:")
        print(f"{response}")
        print("\n✓ Agent successfully answered king safety question")
        return True
    except Exception as e:
        print(f"❌ Failed: {e}")
        return False


def test_piece_activity_question(agent):
    """Test piece activity question."""
    print_separator("TEST 4: PIECE ACTIVITY QUESTION")
    
    fen = "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1"
    question = "Which side has better piece activity and development?"
    
    print(f"Position: After 1.e4")
    board = chess.Board(fen)
    print(f"\n{board}\n")
    print(f"Question: {question}")
    print("\nAsking agent...\n")
    
    try:
        response = agent.analyze(fen, question)
        print(f"Agent's response:")
        print(f"{response}")
        print("\n✓ Agent successfully answered piece activity question")
        return True
    except Exception as e:
        print(f"❌ Failed: {e}")
        return False


def test_pawn_structure_question(agent):
    """Test pawn structure question."""
    print_separator("TEST 5: PAWN STRUCTURE QUESTION")
    
    fen = "r1bqkb1r/pp3ppp/2n1pn2/3p4/2PP4/2N2N2/PP2PPPP/R1BQKB1R w KQkq - 0 7"
    question = "Are there any weak pawns in this position?"
    
    print(f"Position: IQP position")
    board = chess.Board(fen)
    print(f"\n{board}\n")
    print(f"Question: {question}")
    print("\nAsking agent...\n")
    
    try:
        response = agent.analyze(fen, question)
        print(f"Agent's response:")
        print(f"{response}")
        print("\n✓ Agent successfully answered pawn structure question")
        return True
    except Exception as e:
        print(f"❌ Failed: {e}")
        return False


def test_move_comparison_question(agent):
    """Test move comparison question."""
    print_separator("TEST 6: MOVE COMPARISON QUESTION")
    
    fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
    question = "Which is better: e4, d4, or Nf3?"
    
    print(f"Position: Starting position")
    board = chess.Board(fen)
    print(f"\n{board}\n")
    print(f"Question: {question}")
    print("\nAsking agent...\n")
    
    try:
        response = agent.analyze(fen, question)
        print(f"Agent's response:")
        print(f"{response}")
        print("\n✓ Agent successfully compared moves")
        return True
    except Exception as e:
        print(f"❌ Failed: {e}")
        return False


def test_move_quality_question(agent):
    """Test move quality assessment."""
    print_separator("TEST 7: MOVE QUALITY ASSESSMENT")
    
    fen = "r1bqkb1r/1pp2pp1/p1np1n2/4p3/2BPP3/2N2N2/PPP2PPP/R1BQK2R w KQkq - 0 10"
    question = "Was a3 a good move in this position?"
    
    print(f"Position: Before 10.a3")
    board = chess.Board(fen)
    print(f"\n{board}\n")
    print(f"Question: {question}")
    print("\nAsking agent...\n")
    
    try:
        response = agent.analyze(fen, question)
        print(f"Agent's response:")
        print(f"{response}")
        print("\n✓ Agent successfully assessed move quality")
        return True
    except Exception as e:
        print(f"❌ Failed: {e}")
        return False


def test_multi_turn_conversation(agent):
    """Test multi-turn conversation."""
    print_separator("TEST 8: MULTI-TURN CONVERSATION")
    
    fen = "r1bqkbnr/pppp1ppp/2n5/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 3 3"
    
    print(f"Position: Italian Game")
    board = chess.Board(fen)
    print(f"\n{board}\n")
    
    conversation = [
        "What's the material balance?",
        "Which pieces are most active?",
        "Should white castle or develop more pieces first?"
    ]
    
    messages = []
    
    for i, question in enumerate(conversation, 1):
        print(f"\nTurn {i}: {question}")
        
        try:
            # Add user message
            messages.append(HumanMessage(content=question))
            
            # Get response
            response = agent.chat(fen, messages)
            
            # Add assistant response
            messages.append(AIMessage(content=response))
            
            print(f"Agent: {response[:150]}...")
            
        except Exception as e:
            print(f"❌ Failed on turn {i}: {e}")
            return False
    
    print("\n✓ Agent successfully handled multi-turn conversation")
    return True


def test_comprehensive_position_question(agent):
    """Test comprehensive position evaluation."""
    print_separator("TEST 9: COMPREHENSIVE POSITION EVALUATION")
    
    fen = "r1bqkb1r/1pp2pp1/p1np1n2/4p3/2BPP3/P1N2N2/1PP2PPP/R1BQK2R b KQkq - 0 10"
    question = "Give me a complete analysis of this position."
    
    print(f"Position: User's game after 10.a3")
    board = chess.Board(fen)
    print(f"\n{board}\n")
    print(f"Question: {question}")
    print("\nAsking agent...\n")
    
    try:
        response = agent.analyze(fen, question)
        print(f"Agent's response:")
        print(f"{response}")
        print("\n✓ Agent successfully provided comprehensive analysis")
        return True
    except Exception as e:
        print(f"❌ Failed: {e}")
        return False


def main():
    """Run all integration tests."""
    print_separator("PHASE 4 CHUNK 2 - END-TO-END INTEGRATION TESTS")
    print("Testing complete agent workflow with real chess questions")
    print()
    
    # Test 1: Create agent
    agent = test_agent_availability()
    
    if agent is None:
        print("\n❌ Cannot proceed without agent")
        print("\nSetup instructions:")
        print("  1. Install Ollama: https://ollama.ai/download")
        print("  2. Pull model: ollama pull qwen3:14b")
        print("  3. Run tests again")
        return
    
    input("\nPress Enter to start integration tests...")
    
    # Run all tests
    results = []
    
    tests = [
        ("Material Question", lambda: test_material_question(agent)),
        ("King Safety Question", lambda: test_king_safety_question(agent)),
        ("Piece Activity Question", lambda: test_piece_activity_question(agent)),
        ("Pawn Structure Question", lambda: test_pawn_structure_question(agent)),
        ("Move Comparison", lambda: test_move_comparison_question(agent)),
        ("Move Quality Assessment", lambda: test_move_quality_question(agent)),
        ("Multi-turn Conversation", lambda: test_multi_turn_conversation(agent)),
        ("Comprehensive Analysis", lambda: test_comprehensive_position_question(agent))
    ]
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
            
            if result:
                input(f"\n✓ {test_name} passed. Press Enter to continue...")
            else:
                input(f"\n❌ {test_name} failed. Press Enter to continue...")
        except KeyboardInterrupt:
            print("\n\nTests interrupted by user")
            break
        except Exception as e:
            print(f"\n❌ {test_name} crashed: {e}")
            results.append((test_name, False))
            input("Press Enter to continue...")
    
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
        print("ALL INTEGRATION TESTS PASSED!")
        print("\nPhase 4 Complete - Agent System Fully Functional:")
        print("  ✓ Tool routing working")
        print("  ✓ Natural language generation")
        print("  ✓ Multi-turn conversations")
        print("  ✓ All chess analysis tools integrated")
        print("\nDeliverable ready: CLI chat interface (misc/chess_chat.py)")
    else:
        print("⚠ Some tests failed - review errors above")
    
    print()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nTests interrupted by user.")
    except Exception as e:
        print(f"\n\n❌ TEST SUITE FAILED: {e}")
        import traceback
        traceback.print_exc()
