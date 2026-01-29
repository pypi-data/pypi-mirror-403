"""
Stockfish Chess Engine Wrapper
Provides UCI (Universal Chess Interface) interface to Stockfish with platform-specific binary detection.

Terminology:
- UCI: Universal Chess Interface - standard protocol for chess engines
- FEN: Forsyth-Edwards Notation - compact string representation of a chess position
- PV: Principal Variation - the best sequence of moves according to the engine
- SAN: Standard Algebraic Notation - human-readable move notation (e.g., 'Nf3', 'exd5')
- cp: centipawns - evaluation unit where 100 cp = 1 pawn advantage
- Multi-PV: analyzing multiple best moves simultaneously

Performance Features:
- LRU position caching to avoid redundant analysis
- Configurable cache size and depth
"""

import os
import platform
import chess
import chess.engine
import hashlib
import threading
from collections import OrderedDict
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import time


@dataclass
class CachedAnalysis:
    """Cached analysis result with timestamp."""
    result: Dict
    timestamp: float
    depth: int


class LRUCache:
    """Thread-safe LRU cache for position analysis."""
    
    def __init__(self, maxsize: int = 1024):
        self._cache: OrderedDict = OrderedDict()
        self._maxsize = maxsize
        self._lock = threading.Lock()
        self._hits = 0
        self._misses = 0
    
    def get(self, key: str) -> Optional[CachedAnalysis]:
        """Get item from cache, moving it to end (most recently used)."""
        with self._lock:
            if key in self._cache:
                self._cache.move_to_end(key)
                self._hits += 1
                return self._cache[key]
            self._misses += 1
            return None
    
    def put(self, key: str, value: CachedAnalysis):
        """Add item to cache, evicting oldest if full."""
        with self._lock:
            if key in self._cache:
                self._cache.move_to_end(key)
                self._cache[key] = value
            else:
                if len(self._cache) >= self._maxsize:
                    self._cache.popitem(last=False)
                self._cache[key] = value
    
    def clear(self):
        """Clear the cache."""
        with self._lock:
            self._cache.clear()
            self._hits = 0
            self._misses = 0
    
    @property
    def stats(self) -> Dict:
        """Get cache statistics."""
        with self._lock:
            total = self._hits + self._misses
            hit_rate = self._hits / total if total > 0 else 0
            return {
                'size': len(self._cache),
                'maxsize': self._maxsize,
                'hits': self._hits,
                'misses': self._misses,
                'hit_rate': hit_rate
            }


class StockfishEngine:
    """
    Wrapper for Stockfish chess engine with UCI protocol.
    
    Provides high-level methods to analyze chess positions and extract:
    - Evaluations (centipawns or mate scores)
    - Best moves with their evaluations
    - Principal variations (best continuation lines)
    
    Features:
    - LRU caching of analysis results for performance
    - Thread-safe cache operations
    - Cache statistics for monitoring
    """
    
    def __init__(
        self, 
        stockfish_path: Optional[str] = None, 
        depth: int = 18, 
        threads: int = 4, 
        hash_size: int = 256,
        cache_size: int = 1024,
        cache_enabled: bool = True
    ):
        """
        Initialize Stockfish engine.
        
        Args:
            stockfish_path: Path to Stockfish binary. If None, auto-detects based on OS.
            depth: Default search depth (default: 18)
            threads: Number of threads for analysis (default: 4)
            hash_size: Hash table size in MB (default: 256)
            cache_size: Number of positions to cache (default: 1024)
            cache_enabled: Whether to enable position caching (default: True)
        """
        self.depth = depth
        self.threads = threads
        self.hash_size = hash_size
        self.cache_enabled = cache_enabled
        
        # Initialize caches
        self._eval_cache = LRUCache(maxsize=cache_size)
        self._best_moves_cache = LRUCache(maxsize=cache_size)
        self._pv_cache = LRUCache(maxsize=cache_size // 2)
        
        # Auto-detect Stockfish binary if not provided
        if stockfish_path is None:
            stockfish_path = self._get_stockfish_path()
        
        if not os.path.exists(stockfish_path):
            raise FileNotFoundError(f"Stockfish binary not found at: {stockfish_path}")
        
        # Initialize engine
        self.engine = chess.engine.SimpleEngine.popen_uci(stockfish_path)
        
        # Configure engine options
        self.engine.configure({
            "Threads": self.threads,
            "Hash": self.hash_size
        })
    
    def _cache_key(self, fen: str, depth: int, extra: str = "") -> str:
        """Generate cache key from position and parameters."""
        # Normalize FEN by removing move counters for better cache hits
        # Keep only position, turn, castling, and en passant
        fen_parts = fen.split()
        normalized = " ".join(fen_parts[:4]) if len(fen_parts) >= 4 else fen
        key_str = f"{normalized}:{depth}:{extra}"
        return hashlib.md5(key_str.encode()).hexdigest()
    
    def _get_stockfish_path(self) -> str:
        """
        Auto-detect Stockfish binary path based on operating system.
        
        Returns:
            Path to platform-specific Stockfish binary
        """
        # Get project bin directory
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(current_dir)
        bin_dir = os.path.join(project_root, "bin")
        
        # Detect OS and select appropriate binary
        system = platform.system()
        
        if system == "Windows":
            binary_name = "stockfish-windows.exe"
        elif system == "Linux":
            binary_name = "stockfish-linux"
        elif system == "Darwin":  # macOS
            binary_name = "stockfish-mac"
        else:
            raise RuntimeError(f"Unsupported operating system: {system}")
        
        stockfish_path = os.path.join(bin_dir, binary_name)
        
        # Make binary executable on Unix-like systems
        if system in ["Linux", "Darwin"]:
            os.chmod(stockfish_path, 0o755)
        
        return stockfish_path
    
    def get_eval(self, fen: str, depth: Optional[int] = None) -> Dict:
        """
        Get evaluation for a position.
        
        Args:
            fen: Position in FEN notation (e.g., "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1")
            depth: Search depth (number of plies/half-moves to search ahead). Uses default if None.
        
        Returns:
            Dictionary with:
                - score: Evaluation score
                    * For 'cp' type: in centipawns (100 cp = 1 pawn, positive = white better)
                    * For 'mate' type: moves until mate (positive = white mates, negative = black mates)
                - type: 'cp' for centipawns or 'mate' for forced mate
                - depth: Actual search depth reached
                - cached: True if result was from cache
                
        Example:
            >>> engine.get_eval("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1")
            {'type': 'cp', 'score': 25, 'depth': 18}  # White is up about 0.25 pawns
        """
        search_depth = depth if depth is not None else self.depth
        
        # Check cache
        if self.cache_enabled:
            cache_key = self._cache_key(fen, search_depth, "eval")
            cached = self._eval_cache.get(cache_key)
            if cached and cached.depth >= search_depth:
                result = cached.result.copy()
                result['cached'] = True
                return result
        
        board = chess.Board(fen)
        
        info = self.engine.analyse(board, chess.engine.Limit(depth=search_depth))
        
        score = info["score"].white()
        
        result = {
            "depth": info.get("depth", search_depth),
            "cached": False
        }
        
        if score.is_mate():
            result["type"] = "mate"
            result["score"] = score.mate()
        else:
            result["type"] = "cp"
            result["score"] = score.score()
        
        # Store in cache
        if self.cache_enabled:
            self._eval_cache.put(cache_key, CachedAnalysis(
                result=result,
                timestamp=time.time(),
                depth=search_depth
            ))
        
        return result
    
    def get_best_moves(self, fen: str, n: int = 3, depth: Optional[int] = None) -> List[Dict]:
        """
        Get top N best moves for a position using Multi-PV analysis.
        
        Multi-PV (Multiple Principal Variations) allows the engine to analyze several
        candidate moves simultaneously, ranking them by evaluation.
        
        Args:
            fen: Position in FEN notation
            n: Number of best moves to return (Multi-PV count)
            depth: Search depth (uses default if None)
        
        Returns:
            List of dictionaries (sorted best to worst), each containing:
                - move: Move in UCI notation (e.g., 'e2e4' = pawn from e2 to e4)
                - san: Move in SAN notation (e.g., 'e4' - human-readable)
                - score: Evaluation after this move (centipawns or mate moves)
                - type: 'cp' or 'mate'
                - pv: Principal Variation - sequence of best moves following this move
                      (list of UCI moves showing the expected continuation)
                - cached: True if result was from cache
                      
        Example:
            >>> engine.get_best_moves("starting_fen", n=2)
            [
                {'move': 'e2e4', 'san': 'e4', 'type': 'cp', 'score': 30, 'pv': ['e2e4', 'e7e5', 'g1f3']},
                {'move': 'd2d4', 'san': 'd4', 'type': 'cp', 'score': 28, 'pv': ['d2d4', 'd7d5', 'c2c4']}
            ]
        """
        search_depth = depth if depth is not None else self.depth
        
        # Check cache
        if self.cache_enabled:
            cache_key = self._cache_key(fen, search_depth, f"best_{n}")
            cached = self._best_moves_cache.get(cache_key)
            if cached and cached.depth >= search_depth:
                results = []
                for r in cached.result:
                    rc = r.copy()
                    rc['cached'] = True
                    results.append(rc)
                return results
        
        board = chess.Board(fen)
        
        # Analyze with multi-PV
        infos = self.engine.analyse(
            board, 
            chess.engine.Limit(depth=search_depth),
            multipv=n
        )
        
        results = []
        
        for info in infos:
            pv = info.get("pv", [])
            if not pv:
                continue
            
            move = pv[0]
            score = info["score"].white()
            
            result = {
                "move": move.uci(),
                "san": board.san(move),
                "pv": [m.uci() for m in pv],
                "cached": False
            }
            
            if score.is_mate():
                result["type"] = "mate"
                result["score"] = score.mate()
            else:
                result["type"] = "cp"
                result["score"] = score.score()
            
            results.append(result)
        
        # Store in cache
        if self.cache_enabled and results:
            self._best_moves_cache.put(cache_key, CachedAnalysis(
                result=results,
                timestamp=time.time(),
                depth=search_depth
            ))
        
        return results
    
    def get_pv(self, fen: str, depth: Optional[int] = None) -> Tuple[List[str], Dict]:
        """
        Get principal variation (PV) - the best continuation line according to engine.
        
        The PV represents what the engine believes will be the best sequence of moves
        for both sides if perfect play is assumed.
        
        Args:
            fen: Position in FEN notation
            depth: Search depth (uses default if None)
        
        Returns:
            Tuple of:
                - List of moves in UCI notation representing the PV (e.g., ['e2e4', 'e7e5', 'g1f3'])
                - Evaluation dictionary (same format as get_eval):
                    * type: 'cp' or 'mate'
                    * score: evaluation score
                    * depth: search depth reached
                    
        Example:
            >>> pv_moves, eval_dict = engine.get_pv("starting_fen")
            >>> print(pv_moves)
            ['e2e4', 'e7e5', 'g1f3', 'b8c6', 'f1c4']
            >>> print(eval_dict)
            {'type': 'cp', 'score': 30, 'depth': 18}
        """
        board = chess.Board(fen)
        search_depth = depth if depth is not None else self.depth
        
        info = self.engine.analyse(board, chess.engine.Limit(depth=search_depth))
        
        pv = info.get("pv", [])
        pv_moves = [move.uci() for move in pv]
        
        score = info["score"].white()
        
        eval_result = {
            "depth": info.get("depth", search_depth)
        }
        
        if score.is_mate():
            eval_result["type"] = "mate"
            eval_result["score"] = score.mate()
        else:
            eval_result["type"] = "cp"
            eval_result["score"] = score.score()
        
        return pv_moves, eval_result
    
    def get_cache_stats(self) -> Dict:
        """Get statistics for all caches."""
        return {
            'eval_cache': self._eval_cache.stats,
            'best_moves_cache': self._best_moves_cache.stats,
            'pv_cache': self._pv_cache.stats
        }
    
    def clear_cache(self):
        """Clear all caches."""
        self._eval_cache.clear()
        self._best_moves_cache.clear()
        self._pv_cache.clear()
    
    def close(self):
        """Close the engine and release resources."""
        if hasattr(self, 'engine') and self.engine:
            try:
                self.engine.quit()
            except Exception:
                pass  # Ignore errors during cleanup
            finally:
                self.engine = None
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
        return False  # Don't suppress exceptions
    
    def __del__(self):
        """Destructor - ensure engine is closed."""
        self.close()
