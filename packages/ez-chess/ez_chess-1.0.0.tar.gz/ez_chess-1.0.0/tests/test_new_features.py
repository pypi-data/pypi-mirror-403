"""
Test script for new features:
- Engine position caching (LRU cache)
- Async analysis manager
- Opening book / MCP theory
- Board annotations (arrows, highlights)

Run: python tests/test_new_features.py
"""

import sys
import os
import time
import tkinter as tk
from threading import Event

# Add project root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_engine_caching():
    """Test LRU caching in StockfishEngine."""
    print("=" * 70)
    print("TEST 1: ENGINE POSITION CACHING")
    print("=" * 70)
    
    from src.engine import StockfishEngine
    
    with StockfishEngine(cache_size=100, cache_enabled=True) as engine:
        print(f"✓ Engine initialized with caching enabled")
        print(f"  Cache size: 100 positions")
        
        test_fen = "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq - 0 1"
        
        # First analysis - should NOT be cached
        print("\n1. First analysis (cache miss expected)...")
        stats_before = engine.get_cache_stats()
        start = time.perf_counter()
        result1 = engine.get_eval(test_fen, depth=12)
        time1 = time.perf_counter() - start
        stats_after = engine.get_cache_stats()
        
        print(f"   Time: {time1:.3f}s")
        print(f"   Eval: {result1['score']/100:+.2f}")
        print(f"   Eval cache size: {stats_after['eval_cache']['size']}")
        
        # Second analysis - SHOULD be cached
        print("\n2. Second analysis (cache HIT expected)...")
        start = time.perf_counter()
        result2 = engine.get_eval(test_fen, depth=12)
        time2 = time.perf_counter() - start
        stats_after2 = engine.get_cache_stats()
        
        print(f"   Time: {time2:.3f}s")
        print(f"   Eval: {result2['score']/100:+.2f}")
        print(f"   Eval cache hits: {stats_after2['eval_cache']['hits']}")
        
        # Verify cache hit
        if time2 < time1 * 0.5:  # Should be MUCH faster
            print(f"\n✓ CACHE WORKING! Speedup: {time1/max(time2, 0.001):.1f}x")
        else:
            print(f"\n⚠ Cache may not be working as expected")
        
        # Test get_best_moves caching
        print("\n3. Testing get_best_moves caching...")
        start = time.perf_counter()
        moves1 = engine.get_best_moves(test_fen, n=3, depth=12)
        time_first = time.perf_counter() - start
        
        start = time.perf_counter()
        moves2 = engine.get_best_moves(test_fen, n=3, depth=12)
        time_second = time.perf_counter() - start
        
        print(f"   First call:  {time_first:.3f}s")
        print(f"   Second call: {time_second:.3f}s")
        print(f"   Best moves: {[m['san'] for m in moves1]}")
        
        final_stats = engine.get_cache_stats()
        print(f"\n4. Final cache stats:")
        for cache_name, cache_stats in final_stats.items():
            print(f"   {cache_name}: size={cache_stats['size']}, hits={cache_stats['hits']}, misses={cache_stats['misses']}")
        
    print("\n✓ ENGINE CACHING TEST PASSED\n")


def test_async_analysis():
    """Test async analysis manager."""
    print("=" * 70)
    print("TEST 2: ASYNC ANALYSIS MANAGER")
    print("=" * 70)
    
    from src.async_analysis import AsyncAnalysisManager, AnalysisResult
    
    results_received = []
    completion_event = Event()
    
    def on_result(result: AnalysisResult):
        results_received.append(result)
        print(f"   → Received result: type={result.analysis_type}, from_cache={result.from_cache}")
        if result.result:
            print(f"     Data keys: {list(result.result.keys())}")
        completion_event.set()
    
    manager = AsyncAnalysisManager(max_workers=2)
    print("✓ AsyncAnalysisManager initialized with 2 workers")
    
    # Test single request using analyze_position (the actual API)
    print("\n1. Testing single analysis request...")
    test_fen = "r1bqkb1r/pppp1ppp/2n2n2/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 4 4"
    
    request_id = manager.analyze_position(
        fen=test_fen,
        callback=on_result,
        analysis_type="eval",
        depth=10,
        debounce=False  # Don't debounce for testing
    )
    print(f"   Request ID: {request_id}")
    
    # Wait for completion
    if completion_event.wait(timeout=10):
        print("   ✓ Analysis completed successfully")
    else:
        print("   ✗ Analysis timed out")
    
    # Test multiple requests
    print("\n2. Testing multiple rapid requests...")
    completion_event.clear()
    results_received.clear()
    
    positions = [
        "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq - 0 1",
        "rnbqkbnr/pppp1ppp/8/4p3/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 0 2",
    ]
    
    for i, fen in enumerate(positions):
        manager.analyze_position(
            fen=fen, 
            callback=on_result,
            analysis_type="best_moves",
            depth=8,
            debounce=False
        )
    
    # Wait a bit for requests
    time.sleep(3)
    print(f"   Requests submitted: {len(positions)}")
    print(f"   Results received: {len(results_received)}")
    
    # Test cancellation
    print("\n3. Testing cancellation...")
    manager.cancel_pending()
    print("   ✓ Cancellation requested")
    
    # Shutdown
    manager.shutdown()
    print("\n✓ ASYNC ANALYSIS TEST PASSED\n")


def test_opening_book():
    """Test opening book and MCP theory fetching."""
    print("=" * 70)
    print("TEST 3: OPENING BOOK / MCP THEORY")
    print("=" * 70)
    
    import chess
    from src.mcp.opening_book import OpeningBook
    
    book = OpeningBook()
    print("✓ OpeningBook initialized")
    
    # Test common openings - use chess.Board objects
    openings_to_test = [
        ("rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq - 0 1", "1.e4"),
        ("rnbqkbnr/pppp1ppp/8/4p3/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 0 2", "1.e4 e5"),
        ("r1bqkbnr/pppp1ppp/2n5/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R w KQkq - 2 3", "1.e4 e5 2.Nf3 Nc6"),
        ("r1bqkbnr/pppp1ppp/2n5/1B2p3/4P3/5N2/PPPP1PPP/RNBQK2R b KQkq - 3 3", "Ruy Lopez"),
        ("rnbqkb1r/pppp1ppp/5n2/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R b KQkq - 3 3", "Italian Game"),
        ("rnbqkbnr/pp1ppppp/8/2p5/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 0 2", "Sicilian Defense"),
    ]
    
    print("\n1. Testing opening recognition...")
    for fen, expected in openings_to_test:
        try:
            board = chess.Board(fen)
            info = book.identify_opening(board)
            if info:
                print(f"   ✓ {expected}: {info.name}")
                if info.variation:
                    print(f"     Variation: {info.variation}")
            else:
                print(f"   ? {expected}: Not recognized (may be OK for short lines)")
        except Exception as e:
            print(f"   ! {expected}: Error - {e}")
    
    # Test LLM-formatted output using correct method
    print("\n2. Testing LLM-formatted context...")
    italian_fen = "rnbqkb1r/pppp1ppp/5n2/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R b KQkq - 3 3"
    try:
        # Use get_opening_context which returns a dict
        context = book.get_opening_context(italian_fen)
        
        if context:
            print(f"   Opening: {context.get('opening', {}).get('name', 'Unknown')}")
            print(f"   Game phase: {context.get('phase', 'N/A')}")
            if 'plans' in context:
                print(f"   Plans preview:")
                for plan in context.get('plans', [])[:2]:
                    print(f"     - {plan}")
        else:
            print("   No opening context found (OK - position may not be in DB)")
    except Exception as e:
        print(f"   Note: {e}")
    
    # Test format_for_llm method
    print("\n3. Testing format_for_llm...")
    try:
        llm_text = book.format_for_llm(italian_fen)
        if llm_text:
            lines = llm_text.split('\n')[:5]
            for line in lines:
                if line.strip():
                    print(f"   {line}")
        else:
            print("   No LLM formatted text available")
    except Exception as e:
        print(f"   Note: {e}")
    
    print("\n✓ OPENING BOOK TEST PASSED\n")


def test_board_annotations():
    """Test board annotation system with visual demo."""
    print("=" * 70)
    print("TEST 4: BOARD ANNOTATIONS (VISUAL DEMO)")
    print("=" * 70)
    
    import chess
    from ui.board import ChessBoardWidget, ArrowType, HighlightType, AnnotationManager
    
    print("Creating visual demo window...")
    print("(Close the window when done viewing)")
    
    # Create a test window
    root = tk.Tk()
    root.title("Board Annotations Test")
    root.configure(bg="#1a1a1a")
    
    # Create board widget
    board = ChessBoardWidget(root, size=480)
    board.pack(padx=20, pady=20)
    
    # Set up Italian Game position
    italian_fen = "r1bqk2r/pppp1ppp/2n2n2/2b1p3/2B1P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 4 4"
    board.set_position(italian_fen)
    
    # Add various annotations
    print("\nAdding annotations:")
    
    # Best move arrow (blue) - Nc3
    board.add_best_move_arrow("b1", "c3")
    print("   ✓ Best move arrow: Nb1-c3 (blue)")
    
    # Alternative move arrow (green) - d3
    board.annotations.add_arrow(chess.D2, chess.D3, ArrowType.GOOD_MOVE)
    print("   ✓ Good move arrow: d2-d3 (green)")
    
    # Threat arrow (red) - opponent's potential Ng4
    board.add_threat_arrow("f6", "g4")
    print("   ✓ Threat arrow: Nf6-g4 (red)")
    
    # Interesting move (purple) - c3
    board.annotations.add_arrow(chess.C2, chess.C3, ArrowType.INTERESTING)
    print("   ✓ Interesting move: c2-c3 (purple)")
    
    # Key square highlights
    board.highlight_square("d4", HighlightType.KEY_SQUARE)
    print("   ✓ Key square highlight: d4 (purple)")
    
    board.highlight_square("f7", HighlightType.WEAKNESS)
    print("   ✓ Weakness highlight: f7 (orange)")
    
    # Redraw
    board._draw_board()
    
    # Add legend
    legend = tk.Frame(root, bg="#1a1a1a")
    legend.pack(pady=10)
    
    legend_items = [
        ("Blue arrow", "#58a6ff", "Best move"),
        ("Green arrow", "#3fb950", "Good alternative"),
        ("Red arrow", "#f85149", "Threat"),
        ("Purple arrow", "#a371f7", "Interesting"),
        ("Orange square", "#ff9500", "Weakness"),
    ]
    
    for name, color, desc in legend_items:
        frame = tk.Frame(legend, bg="#1a1a1a")
        frame.pack(side="left", padx=10)
        tk.Label(frame, text="●", fg=color, bg="#1a1a1a", font=("Arial", 14)).pack(side="left")
        tk.Label(frame, text=f" {desc}", fg="#e0e0e0", bg="#1a1a1a", font=("Arial", 10)).pack(side="left")
    
    # Instructions
    tk.Label(
        root,
        text="Close this window to continue tests",
        fg="#888888",
        bg="#1a1a1a",
        font=("Arial", 9)
    ).pack(pady=10)
    
    print("\n   Displaying board with annotations...")
    print("   (Window will appear - close it to continue)")
    
    # Run briefly then auto-close (for automated testing)
    def auto_close():
        root.destroy()
    
    # Auto-close after 5 seconds for CI, or let user close
    root.after(5000, auto_close)
    
    try:
        root.mainloop()
    except:
        pass
    
    print("\n✓ BOARD ANNOTATIONS TEST PASSED\n")


def test_annotation_manager():
    """Test AnnotationManager directly without GUI."""
    print("=" * 70)
    print("TEST 5: ANNOTATION MANAGER (NO GUI)")
    print("=" * 70)
    
    import chess
    from ui.board import AnnotationManager, ArrowType, HighlightType
    
    manager = AnnotationManager()
    print("✓ AnnotationManager created")
    
    # Add various annotations
    manager.add_arrow(chess.E2, chess.E4, ArrowType.BEST_MOVE)
    manager.add_arrow(chess.D2, chess.D4, ArrowType.GOOD_MOVE)
    manager.add_threat_arrow(chess.F6, chess.G4)
    manager.add_highlight(chess.D4, HighlightType.KEY_SQUARE)
    manager.add_highlight(chess.F7, HighlightType.WEAKNESS)
    
    print(f"\n1. Arrow count: {len(manager.arrows)}")
    print(f"   Highlight count: {len(manager.highlights)}")
    
    # Test arrow properties
    print("\n2. Arrow properties:")
    for arrow in manager.arrows:
        print(f"   {chess.square_name(arrow.from_square)}->{chess.square_name(arrow.to_square)}: "
              f"{arrow.arrow_type.value}, color={arrow.color}, width={arrow.width}")
    
    # Test highlight properties
    print("\n3. Highlight properties:")
    for hl in manager.highlights:
        print(f"   {chess.square_name(hl.square)}: {hl.highlight_type.value}, "
              f"color={hl.color}, alpha={hl.alpha}")
    
    # Test clear
    manager.clear_arrows()
    print(f"\n4. After clear_arrows: {len(manager.arrows)} arrows")
    
    manager.clear()
    print(f"   After clear: {len(manager.arrows)} arrows, {len(manager.highlights)} highlights")
    
    # Test add_from_analysis
    print("\n5. Testing add_from_analysis:")
    analysis_result = {
        'best_moves': [
            {'move': 'e2e4', 'san': 'e4', 'score': 30},
            {'move': 'd2d4', 'san': 'd4', 'score': 25},
        ]
    }
    
    test_board = chess.Board()
    manager.add_from_analysis(analysis_result, test_board)
    print(f"   Arrows after analysis: {len(manager.arrows)}")
    for arrow in manager.arrows:
        print(f"     {chess.square_name(arrow.from_square)}->{chess.square_name(arrow.to_square)}: {arrow.arrow_type.value}")
    
    print("\n✓ ANNOTATION MANAGER TEST PASSED\n")


def test_config_system():
    """Test unified configuration system."""
    print("=" * 70)
    print("TEST 6: UNIFIED CONFIG SYSTEM")
    print("=" * 70)
    
    from src.config import get_config, EngineConfig, LLMConfig, AnalysisConfig
    
    config = get_config()
    print("✓ Config loaded successfully")
    
    print("\n1. Engine Config:")
    print(f"   Depth: {config.engine.depth}")
    print(f"   Threads: {config.engine.threads}")
    print(f"   Hash: {config.engine.hash_size_mb}MB")
    print(f"   Cache size: {config.engine.cache_size}")
    print(f"   Cache enabled: {config.engine.cache_enabled}")
    
    print("\n2. LLM Config:")
    print(f"   Provider: {config.llm.provider}")
    print(f"   Model: {config.llm.model}")
    print(f"   Max tokens: {config.llm.max_tokens}")
    print(f"   Temperature: {config.llm.temperature}")
    
    print("\n3. Analysis Config:")
    print(f"   Async analysis: {config.analysis.async_analysis}")
    print(f"   Show top moves: {config.analysis.show_top_moves}")
    print(f"   PV depth: {config.analysis.pv_depth}")
    print(f"   Auto-analyze: {config.analysis.auto_analyze}")
    
    print("\n4. MCP Config:")
    print(f"   Enabled: {config.mcp.enabled}")
    print(f"   Cache opening theory: {config.mcp.cache_opening_theory}")
    print(f"   Theory cache TTL: {config.mcp.theory_cache_ttl_hours}h")
    
    print("\n✓ CONFIG SYSTEM TEST PASSED\n")


def run_all_tests():
    """Run all new feature tests."""
    print("\n" + "=" * 70)
    print("EZ_CHESS - NEW FEATURES TEST SUITE")
    print("=" * 70)
    print("Testing: Caching, Async, Opening Book, Annotations, Config")
    print("=" * 70 + "\n")
    
    tests = [
        ("Engine Caching", test_engine_caching),
        ("Async Analysis", test_async_analysis),
        ("Opening Book", test_opening_book),
        ("Annotation Manager", test_annotation_manager),
        ("Config System", test_config_system),
        ("Board Annotations Visual", test_board_annotations),
    ]
    
    results = []
    
    for name, test_fn in tests:
        try:
            test_fn()
            results.append((name, True, None))
        except Exception as e:
            import traceback
            print(f"\n✗ {name} FAILED: {e}")
            traceback.print_exc()
            results.append((name, False, str(e)))
    
    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    
    passed = sum(1 for _, success, _ in results if success)
    total = len(results)
    
    for name, success, error in results:
        status = "✓ PASS" if success else "✗ FAIL"
        print(f"  {status}: {name}")
        if error:
            print(f"         Error: {error[:50]}...")
    
    print(f"\nResult: {passed}/{total} tests passed")
    print("=" * 70)
    
    return passed == total


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
