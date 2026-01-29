"""
Async Analysis Manager - Non-blocking chess analysis for responsive UI.

Provides async wrappers around Stockfish analysis to prevent UI freezing.
Uses thread pools and futures for concurrent analysis.
"""

import asyncio
import threading
from concurrent.futures import ThreadPoolExecutor, Future
from typing import Callable, Any, Optional, Dict, List
from dataclasses import dataclass
from queue import Queue
import time
import chess

from src.config import get_config


@dataclass
class AnalysisRequest:
    """A pending analysis request."""
    request_id: str
    fen: str
    analysis_type: str  # 'eval', 'best_moves', 'full'
    depth: Optional[int] = None
    callback: Optional[Callable] = None
    timestamp: float = 0.0
    
    def __post_init__(self):
        if self.timestamp == 0.0:
            self.timestamp = time.time()


@dataclass
class AnalysisResult:
    """Result of an analysis request."""
    request_id: str
    fen: str
    analysis_type: str
    result: Dict[str, Any]
    elapsed_ms: float
    from_cache: bool = False
    error: Optional[str] = None


class AsyncAnalysisManager:
    """
    Manages asynchronous chess analysis to keep UI responsive.
    
    Features:
    - Thread pool for concurrent analysis
    - Request debouncing (cancel outdated requests)
    - Result caching
    - Callback-based result delivery
    """
    
    def __init__(self, max_workers: int = 2):
        """
        Initialize the async analysis manager.
        
        Args:
            max_workers: Maximum concurrent analysis threads
        """
        self._executor = ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="analysis")
        self._pending: Dict[str, Future] = {}
        self._results: Dict[str, AnalysisResult] = {}
        self._callbacks: Dict[str, List[Callable]] = {}
        self._lock = threading.Lock()
        self._request_counter = 0
        
        # Engine instance (lazy loaded)
        self._engine = None
        self._engine_lock = threading.Lock()
        
        # Position-based debouncing
        self._latest_fen: Optional[str] = None
        self._debounce_timer: Optional[threading.Timer] = None
        
        config = get_config()
        self._debounce_delay = config.analysis.analysis_delay_ms / 1000.0
    
    def _get_engine(self):
        """Get or create the Stockfish engine (thread-safe)."""
        if self._engine is None:
            with self._engine_lock:
                if self._engine is None:
                    from src.engine import StockfishEngine
                    config = get_config()
                    self._engine = StockfishEngine(
                        depth=config.engine.depth,
                        threads=config.engine.threads,
                        hash_size=config.engine.hash_size_mb
                    )
        return self._engine
    
    def _generate_request_id(self) -> str:
        """Generate unique request ID."""
        with self._lock:
            self._request_counter += 1
            return f"req_{self._request_counter}_{time.time()}"
    
    def analyze_position(
        self,
        fen: str,
        callback: Optional[Callable[[AnalysisResult], None]] = None,
        analysis_type: str = 'full',
        depth: Optional[int] = None,
        debounce: bool = True
    ) -> str:
        """
        Request analysis for a position.
        
        Args:
            fen: Position in FEN notation
            callback: Function to call with result
            analysis_type: 'eval', 'best_moves', or 'full'
            depth: Override default depth
            debounce: Whether to debounce rapid requests
            
        Returns:
            Request ID for tracking
        """
        request_id = self._generate_request_id()
        
        request = AnalysisRequest(
            request_id=request_id,
            fen=fen,
            analysis_type=analysis_type,
            depth=depth,
            callback=callback
        )
        
        if debounce and self._debounce_delay > 0:
            self._debounced_submit(request)
        else:
            self._submit_request(request)
        
        return request_id
    
    def _debounced_submit(self, request: AnalysisRequest):
        """Submit request with debouncing."""
        # Cancel any pending debounce timer
        if self._debounce_timer:
            self._debounce_timer.cancel()
        
        # Update latest FEN
        self._latest_fen = request.fen
        
        # Schedule submission after delay
        self._debounce_timer = threading.Timer(
            self._debounce_delay,
            lambda: self._submit_if_still_relevant(request)
        )
        self._debounce_timer.start()
    
    def _submit_if_still_relevant(self, request: AnalysisRequest):
        """Submit request only if it's still the latest position."""
        if request.fen == self._latest_fen:
            self._submit_request(request)
    
    def _submit_request(self, request: AnalysisRequest):
        """Submit analysis request to thread pool."""
        # Cancel any pending request for this position
        self.cancel_pending(request.fen)
        
        # Store callback
        if request.callback:
            with self._lock:
                if request.request_id not in self._callbacks:
                    self._callbacks[request.request_id] = []
                self._callbacks[request.request_id].append(request.callback)
        
        # Submit to thread pool
        future = self._executor.submit(self._do_analysis, request)
        
        with self._lock:
            self._pending[request.request_id] = future
        
        # Add completion callback
        future.add_done_callback(lambda f: self._on_analysis_complete(request, f))
    
    def _do_analysis(self, request: AnalysisRequest) -> AnalysisResult:
        """Perform the actual analysis (runs in thread)."""
        start_time = time.time()
        
        try:
            engine = self._get_engine()
            config = get_config()
            depth = request.depth or config.engine.depth
            
            result_data = {}
            
            if request.analysis_type in ['eval', 'full']:
                eval_result = engine.get_eval(request.fen, depth=depth)
                result_data['eval'] = eval_result
            
            if request.analysis_type in ['best_moves', 'full']:
                best_moves = engine.get_best_moves(
                    request.fen, 
                    n=config.analysis.show_top_moves, 
                    depth=depth
                )
                result_data['best_moves'] = best_moves
                
                # Also get PV for the best move
                if best_moves:
                    pv, _ = engine.get_pv(request.fen, depth=depth)
                    result_data['pv'] = pv
            
            elapsed_ms = (time.time() - start_time) * 1000
            
            return AnalysisResult(
                request_id=request.request_id,
                fen=request.fen,
                analysis_type=request.analysis_type,
                result=result_data,
                elapsed_ms=elapsed_ms,
                from_cache=False
            )
            
        except Exception as e:
            elapsed_ms = (time.time() - start_time) * 1000
            return AnalysisResult(
                request_id=request.request_id,
                fen=request.fen,
                analysis_type=request.analysis_type,
                result={},
                elapsed_ms=elapsed_ms,
                error=str(e)
            )
    
    def _on_analysis_complete(self, request: AnalysisRequest, future: Future):
        """Handle completed analysis."""
        try:
            result = future.result()
        except Exception as e:
            result = AnalysisResult(
                request_id=request.request_id,
                fen=request.fen,
                analysis_type=request.analysis_type,
                result={},
                elapsed_ms=0,
                error=str(e)
            )
        
        # Store result
        with self._lock:
            self._results[request.request_id] = result
            self._pending.pop(request.request_id, None)
            callbacks = self._callbacks.pop(request.request_id, [])
        
        # Invoke callbacks
        for callback in callbacks:
            try:
                callback(result)
            except Exception as e:
                print(f"[AsyncAnalysis] Callback error: {e}")
    
    def cancel_pending(self, fen: Optional[str] = None):
        """
        Cancel pending analysis requests.
        
        Args:
            fen: Cancel only requests for this FEN. If None, cancel all.
        """
        with self._lock:
            to_cancel = []
            for req_id, future in self._pending.items():
                if fen is None or (req_id in self._results and self._results[req_id].fen == fen):
                    to_cancel.append((req_id, future))
            
            for req_id, future in to_cancel:
                future.cancel()
                self._pending.pop(req_id, None)
                self._callbacks.pop(req_id, None)
    
    def get_result(self, request_id: str) -> Optional[AnalysisResult]:
        """Get result for a request ID."""
        with self._lock:
            return self._results.get(request_id)
    
    def is_pending(self, request_id: str) -> bool:
        """Check if a request is still pending."""
        with self._lock:
            return request_id in self._pending
    
    def shutdown(self):
        """Shutdown the analysis manager."""
        # Cancel debounce timer
        if self._debounce_timer:
            self._debounce_timer.cancel()
        
        # Cancel all pending
        self.cancel_pending()
        
        # Shutdown executor
        self._executor.shutdown(wait=False)
        
        # Close engine
        if self._engine:
            try:
                self._engine.close()
            except:
                pass


# =============================================================================
# GLOBAL INSTANCE
# =============================================================================

_async_manager: Optional[AsyncAnalysisManager] = None


def get_async_manager() -> AsyncAnalysisManager:
    """Get global async analysis manager."""
    global _async_manager
    if _async_manager is None:
        _async_manager = AsyncAnalysisManager()
    return _async_manager


def shutdown_async_manager():
    """Shutdown global async manager."""
    global _async_manager
    if _async_manager:
        _async_manager.shutdown()
        _async_manager = None


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def analyze_async(
    fen: str,
    callback: Callable[[AnalysisResult], None],
    analysis_type: str = 'full'
) -> str:
    """
    Convenience function for async analysis.
    
    Args:
        fen: Position to analyze
        callback: Function called with result
        analysis_type: 'eval', 'best_moves', or 'full'
        
    Returns:
        Request ID
    """
    manager = get_async_manager()
    return manager.analyze_position(fen, callback, analysis_type)


def cancel_analysis(fen: Optional[str] = None):
    """Cancel pending analysis."""
    manager = get_async_manager()
    manager.cancel_pending(fen)


if __name__ == "__main__":
    import time
    
    print("=== Async Analysis Manager Test ===\n")
    
    def on_result(result: AnalysisResult):
        print(f"[Callback] Got result for {result.fen[:20]}...")
        print(f"  Elapsed: {result.elapsed_ms:.0f}ms")
        print(f"  From cache: {result.from_cache}")
        if result.error:
            print(f"  Error: {result.error}")
        else:
            print(f"  Eval: {result.result.get('eval', {})}")
            best = result.result.get('best_moves', [])
            if best:
                print(f"  Best move: {best[0].get('san', 'N/A')}")
    
    manager = get_async_manager()
    
    # Test 1: Basic analysis
    print("Test 1: Basic analysis")
    fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
    req_id = manager.analyze_position(fen, on_result, debounce=False)
    print(f"Request ID: {req_id}")
    
    # Wait for result
    time.sleep(3)
    
    # Test 2: Rapid requests (debouncing)
    print("\nTest 2: Rapid requests with debouncing")
    positions = [
        "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1",
        "rnbqkbnr/pppp1ppp/8/4p3/4P3/8/PPPP1PPP/RNBQKBNR w KQkq e6 0 2",
        "rnbqkbnr/pppp1ppp/8/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R b KQkq - 1 2",
    ]
    
    for pos in positions:
        manager.analyze_position(pos, on_result, debounce=True)
        time.sleep(0.1)  # Rapid fire
    
    # Only the last should complete
    time.sleep(3)
    
    print("\nShutting down...")
    manager.shutdown()
    print("Done!")
