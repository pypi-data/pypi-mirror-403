"""
Why Engine - Core Intent Inference System
Explains the "why" behind chess moves by analyzing multiple dimensions.

The Why Engine works in layers:
1. Observation: What changed? (material, position, control)
2. Threat Detection: What's threatened/defended?
3. Tactical Patterns: Sacrifices, forcing sequences, motifs
4. Strategic Classification: Development, space, structure
5. Intent Inference: The actual "why"
6. Explanation Assembly: Structured output for verbalization

This module provides the complete "why" analysis for any move.
"""

import chess
from typing import Dict, List, Optional, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
try:
    from src.engine import StockfishEngine
except ImportError:
    from engine import StockfishEngine


class MoveIntent(Enum):
    """Primary intent categories for chess moves."""
    ATTACK = "attack"                    # Offensive move targeting opponent
    DEFENSE = "defense"                  # Defensive move protecting own pieces/king
    DEVELOPMENT = "development"          # Getting pieces into play
    CONTROL = "control"                  # Controlling key squares/center
    PREPARATION = "preparation"          # Preparing a plan/threat
    PROPHYLAXIS = "prophylaxis"          # Preventing opponent's plan
    MATERIAL_GAIN = "material_gain"      # Winning material
    SACRIFICE = "sacrifice"              # Giving up material for compensation
    SIMPLIFICATION = "simplification"    # Trading to reduce complexity
    KING_SAFETY = "king_safety"          # Improving king protection
    TEMPO = "tempo"                       # Gaining time/initiative
    ENDGAME_TRANSITION = "endgame"       # Favorable endgame transition
    WAITING = "waiting"                   # Maintaining position (zugzwang, etc.)


class CompensationType(Enum):
    """Types of compensation for sacrifices."""
    ATTACK = "attacking_chances"
    ACTIVITY = "piece_activity"
    KING_EXPOSURE = "exposed_enemy_king"
    DEVELOPMENT_LEAD = "development_advantage"
    STRUCTURAL = "pawn_structure_advantage"
    INITIATIVE = "lasting_initiative"
    MATING_ATTACK = "mating_attack"


@dataclass
class PositionFeatures:
    """Comprehensive features extracted from a position."""
    # Material
    material_balance: int  # centipawns (positive = white ahead)
    white_material: int
    black_material: int
    
    # Piece counts
    white_pieces: Dict[str, int] = field(default_factory=dict)
    black_pieces: Dict[str, int] = field(default_factory=dict)
    
    # Activity
    white_mobility: int = 0
    black_mobility: int = 0
    
    # King safety
    white_king_safety: int = 0
    black_king_safety: int = 0
    white_king_attackers: int = 0
    black_king_attackers: int = 0
    
    # Development (pieces off starting squares)
    white_developed_pieces: int = 0
    black_developed_pieces: int = 0
    
    # Center control (e4, d4, e5, d5)
    white_center_control: int = 0
    black_center_control: int = 0
    
    # Pawn structure
    white_pawn_weaknesses: int = 0
    black_pawn_weaknesses: int = 0
    white_passed_pawns: int = 0
    black_passed_pawns: int = 0


@dataclass
class ThreatInfo:
    """Information about threats in a position."""
    # Pieces under attack
    hanging_pieces: List[str] = field(default_factory=list)
    attacked_pieces: List[str] = field(default_factory=list)
    
    # Active threats
    check_threats: List[str] = field(default_factory=list)  # Moves that give check
    mate_threats: List[str] = field(default_factory=list)  # Moves that threaten mate
    capture_threats: List[str] = field(default_factory=list)  # Valuable captures available
    
    # King threats
    king_in_danger: bool = False
    attackers_near_king: int = 0


@dataclass 
class TacticalPattern:
    """Detected tactical pattern."""
    pattern_type: str  # "fork", "pin", "skewer", "discovery", "sacrifice", etc.
    description: str
    pieces_involved: List[str] = field(default_factory=list)
    target_squares: List[str] = field(default_factory=list)
    eval_swing: float = 0.0  # Evaluation change this tactic causes


@dataclass
class MoveAnalysis:
    """Complete analysis of a move explaining the 'why'."""
    move_san: str
    move_uci: str
    
    # Evaluation data
    eval_before: float
    eval_after: float
    eval_delta: float
    is_best_move: bool
    best_move_san: Optional[str] = None
    
    # Primary and secondary intents
    primary_intent: MoveIntent = MoveIntent.PREPARATION
    secondary_intents: List[MoveIntent] = field(default_factory=list)
    
    # What the move achieves
    achievements: List[str] = field(default_factory=list)
    
    # What the move threatens
    threats_created: List[str] = field(default_factory=list)
    
    # What the move defends
    defenses_added: List[str] = field(default_factory=list)
    
    # If sacrifice, what compensation
    is_sacrifice: bool = False
    sacrifice_material: int = 0  # Material given up
    compensation_types: List[CompensationType] = field(default_factory=list)
    
    # Tactical patterns involved
    tactical_patterns: List[TacticalPattern] = field(default_factory=list)
    
    # Position changes
    position_improvements: List[str] = field(default_factory=list)
    position_drawbacks: List[str] = field(default_factory=list)
    
    # Principal variation (what happens with best play)
    pv_explanation: str = ""
    pv_outcome: str = ""
    
    # If move is bad, why
    refutation: Optional[str] = None
    mistake_reason: Optional[str] = None
    
    # Concrete evidence
    evidence: List[str] = field(default_factory=list)
    
    # Summary explanation (for LLM)
    explanation_summary: str = ""


class WhyEngine:
    """
    The core engine for explaining the 'why' behind chess moves.
    
    Combines multiple analysis layers to produce comprehensive explanations
    grounded in Stockfish evaluation and chess principles.
    """
    
    def __init__(self, depth: int = 20):
        """
        Initialize the Why Engine.
        
        Args:
            depth: Stockfish search depth (higher = more accurate, slower)
        """
        self.depth = depth
        self.engine = None
    
    def _ensure_engine(self):
        """Ensure Stockfish engine is initialized."""
        if self.engine is None:
            self.engine = StockfishEngine(depth=self.depth)
    
    def close(self):
        """Close engine resources."""
        if hasattr(self, 'engine') and self.engine:
            try:
                self.engine.close()
            except Exception:
                pass
            finally:
                self.engine = None
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False
    
    def __del__(self):
        """Destructor - ensure engine is closed."""
        self.close()
    
    # =========================================================================
    # LAYER 1: OBSERVATION - What changed?
    # =========================================================================
    
    def extract_features(self, fen: str) -> PositionFeatures:
        """
        Extract comprehensive features from a position.
        
        Args:
            fen: Position in FEN notation
            
        Returns:
            PositionFeatures dataclass with all extracted features
        """
        board = chess.Board(fen)
        
        # Material calculation
        piece_values = {
            chess.PAWN: 100, chess.KNIGHT: 320, chess.BISHOP: 330,
            chess.ROOK: 500, chess.QUEEN: 900, chess.KING: 0
        }
        
        white_material = 0
        black_material = 0
        white_pieces = {}
        black_pieces = {}
        
        for piece_type in [chess.PAWN, chess.KNIGHT, chess.BISHOP, chess.ROOK, chess.QUEEN]:
            white_count = len(board.pieces(piece_type, chess.WHITE))
            black_count = len(board.pieces(piece_type, chess.BLACK))
            
            white_material += white_count * piece_values[piece_type]
            black_material += black_count * piece_values[piece_type]
            
            piece_name = chess.piece_name(piece_type)
            white_pieces[piece_name] = white_count
            black_pieces[piece_name] = black_count
        
        # Mobility (number of legal moves)
        white_mobility = self._count_mobility(board, chess.WHITE)
        black_mobility = self._count_mobility(board, chess.BLACK)
        
        # King safety
        white_king_safety, white_attackers = self._analyze_king_safety_score(board, chess.WHITE)
        black_king_safety, black_attackers = self._analyze_king_safety_score(board, chess.BLACK)
        
        # Development
        white_developed = self._count_developed_pieces(board, chess.WHITE)
        black_developed = self._count_developed_pieces(board, chess.BLACK)
        
        # Center control
        center_squares = [chess.E4, chess.D4, chess.E5, chess.D5]
        white_center = sum(1 for sq in center_squares if board.is_attacked_by(chess.WHITE, sq))
        black_center = sum(1 for sq in center_squares if board.is_attacked_by(chess.BLACK, sq))
        
        # Pawn structure
        white_weak, white_passed = self._analyze_pawn_structure(board, chess.WHITE)
        black_weak, black_passed = self._analyze_pawn_structure(board, chess.BLACK)
        
        return PositionFeatures(
            material_balance=white_material - black_material,
            white_material=white_material,
            black_material=black_material,
            white_pieces=white_pieces,
            black_pieces=black_pieces,
            white_mobility=white_mobility,
            black_mobility=black_mobility,
            white_king_safety=white_king_safety,
            black_king_safety=black_king_safety,
            white_king_attackers=white_attackers,
            black_king_attackers=black_attackers,
            white_developed_pieces=white_developed,
            black_developed_pieces=black_developed,
            white_center_control=white_center,
            black_center_control=black_center,
            white_pawn_weaknesses=white_weak,
            black_pawn_weaknesses=black_weak,
            white_passed_pawns=white_passed,
            black_passed_pawns=black_passed
        )
    
    def _count_mobility(self, board: chess.Board, color: chess.Color) -> int:
        """Count legal moves for a side (mobility measure)."""
        # Temporarily set turn to the color we want to analyze
        original_turn = board.turn
        board.turn = color
        mobility = len(list(board.legal_moves))
        board.turn = original_turn
        return mobility
    
    def _analyze_king_safety_score(self, board: chess.Board, color: chess.Color) -> Tuple[int, int]:
        """
        Analyze king safety and return (safety_score, attacker_count).
        Higher safety score = safer king.
        """
        king_sq = board.king(color)
        if king_sq is None:
            return (0, 0)
        
        enemy = not color
        
        # Count all attackers to king and nearby squares
        attackers = set()
        king_file = chess.square_file(king_sq)
        king_rank = chess.square_rank(king_sq)
        
        # Check king square and surrounding squares
        for f_offset in [-1, 0, 1]:
            for r_offset in [-1, 0, 1]:
                f = king_file + f_offset
                r = king_rank + r_offset
                if 0 <= f <= 7 and 0 <= r <= 7:
                    sq = chess.square(f, r)
                    for attacker_sq in board.attackers(enemy, sq):
                        attackers.add(attacker_sq)
        
        # Also check direct attackers to king (long-range pieces)
        for attacker_sq in board.attackers(enemy, king_sq):
            attackers.add(attacker_sq)
        
        # Count pawn shield
        pawn_shield = 0
        shield_ranks = [king_rank + 1, king_rank + 2] if color == chess.WHITE else [king_rank - 1, king_rank - 2]
        for f in [king_file - 1, king_file, king_file + 1]:
            if 0 <= f <= 7:
                for r in shield_ranks:
                    if 0 <= r <= 7:
                        sq = chess.square(f, r)
                        piece = board.piece_at(sq)
                        if piece and piece.piece_type == chess.PAWN and piece.color == color:
                            pawn_shield += 1
        
        # Safety score: pawn shield good, attackers bad
        safety = pawn_shield * 30 - len(attackers) * 40
        
        return (safety, len(attackers))
    
    def _count_developed_pieces(self, board: chess.Board, color: chess.Color) -> int:
        """Count pieces that have moved from starting position."""
        developed = 0
        
        # Knights
        starting_knights = [chess.B1, chess.G1] if color == chess.WHITE else [chess.B8, chess.G8]
        for sq in board.pieces(chess.KNIGHT, color):
            if sq not in starting_knights:
                developed += 1
        
        # Bishops
        starting_bishops = [chess.C1, chess.F1] if color == chess.WHITE else [chess.C8, chess.F8]
        for sq in board.pieces(chess.BISHOP, color):
            if sq not in starting_bishops:
                developed += 1
        
        # Rooks connected (both rooks can see each other)
        rooks = list(board.pieces(chess.ROOK, color))
        if len(rooks) == 2:
            # Check if rooks are connected (on same rank/file with nothing between)
            r1, r2 = rooks
            if chess.square_file(r1) == chess.square_file(r2) or chess.square_rank(r1) == chess.square_rank(r2):
                # Check if path is clear
                if len(list(board.attacks(r1) & board.attacks(r2))) > 0:
                    developed += 1
        
        return developed
    
    def _analyze_pawn_structure(self, board: chess.Board, color: chess.Color) -> Tuple[int, int]:
        """Analyze pawn structure: (weaknesses, passed_pawns)."""
        weaknesses = 0
        passed = 0
        
        pawns = list(board.pieces(chess.PAWN, color))
        enemy_pawns = list(board.pieces(chess.PAWN, not color))
        
        for pawn_sq in pawns:
            file = chess.square_file(pawn_sq)
            rank = chess.square_rank(pawn_sq)
            
            # Check for isolated pawn (no friendly pawns on adjacent files)
            isolated = True
            for adj_file in [file - 1, file + 1]:
                if 0 <= adj_file <= 7:
                    for p_sq in pawns:
                        if chess.square_file(p_sq) == adj_file:
                            isolated = False
                            break
            if isolated:
                weaknesses += 1
            
            # Check for doubled pawn
            for p_sq in pawns:
                if p_sq != pawn_sq and chess.square_file(p_sq) == file:
                    weaknesses += 1
                    break
            
            # Check for passed pawn (no enemy pawns can block or capture)
            is_passed = True
            direction = 1 if color == chess.WHITE else -1
            for r in range(rank + direction, 8 if color == chess.WHITE else -1, direction):
                if 0 <= r <= 7:
                    for f in [file - 1, file, file + 1]:
                        if 0 <= f <= 7:
                            sq = chess.square(f, r)
                            if sq in enemy_pawns:
                                is_passed = False
                                break
                if not is_passed:
                    break
            if is_passed:
                passed += 1
        
        return (weaknesses, passed)
    
    # =========================================================================
    # LAYER 2: THREAT DETECTION - What's threatened?
    # =========================================================================
    
    def detect_threats(self, board: chess.Board, for_color: chess.Color) -> ThreatInfo:
        """
        Detect threats available for a color.
        
        Args:
            board: Chess position
            for_color: Color to find threats for
            
        Returns:
            ThreatInfo with all detected threats
        """
        threats = ThreatInfo()
        enemy = not for_color
        
        # Find hanging pieces (attacked but not defended)
        for sq in chess.SQUARES:
            piece = board.piece_at(sq)
            if piece and piece.color == enemy:
                attackers = board.attackers(for_color, sq)
                defenders = board.attackers(enemy, sq)
                if attackers and not defenders:
                    threats.hanging_pieces.append(f"{piece.symbol()} on {chess.square_name(sq)}")
                elif attackers:
                    threats.attacked_pieces.append(f"{piece.symbol()} on {chess.square_name(sq)}")
        
        # Find check threats (moves that give check)
        original_turn = board.turn
        board.turn = for_color
        for move in board.legal_moves:
            # Get SAN before making the move
            move_san = board.san(move)
            board.push(move)
            if board.is_check():
                threats.check_threats.append(move_san)
            board.pop()
        board.turn = original_turn
        
        # Analyze king danger
        enemy_king = board.king(enemy)
        if enemy_king:
            attackers_count = len(list(board.attackers(for_color, enemy_king)))
            threats.attackers_near_king = attackers_count
            if attackers_count > 0:
                threats.king_in_danger = True
        
        return threats
    
    # =========================================================================
    # LAYER 3: TACTICAL PATTERN RECOGNITION
    # =========================================================================
    
    def detect_tactical_patterns(self, board: chess.Board, move: chess.Move, 
                                  eval_before: float, eval_after: float) -> List[TacticalPattern]:
        """
        Detect tactical patterns in a move.
        
        Args:
            board: Position BEFORE the move
            move: The move to analyze
            eval_before: Evaluation before move
            eval_after: Evaluation after move
            
        Returns:
            List of detected tactical patterns
        """
        patterns = []
        moving_piece = board.piece_at(move.from_square)
        captured_piece = board.piece_at(move.to_square)
        
        # Make the move to analyze resulting position
        board_after = board.copy()
        board_after.push(move)
        
        # Pattern 1: Sacrifice detection
        if captured_piece:
            # Normal capture
            pass
        elif moving_piece:
            # Check if piece is now hanging
            attackers = board_after.attackers(not moving_piece.color, move.to_square)
            defenders = board_after.attackers(moving_piece.color, move.to_square)
            
            if attackers and len(list(defenders)) < len(list(attackers)):
                # Piece is sacrificed or hanging
                piece_value = {chess.PAWN: 1, chess.KNIGHT: 3, chess.BISHOP: 3, 
                              chess.ROOK: 5, chess.QUEEN: 9, chess.KING: 0}
                value = piece_value.get(moving_piece.piece_type, 0)
                
                if eval_after > eval_before + 0.5:  # Eval improved despite sacrifice
                    patterns.append(TacticalPattern(
                        pattern_type="sacrifice",
                        description=f"Sacrifices {chess.piece_name(moving_piece.piece_type)} for compensation",
                        pieces_involved=[moving_piece.symbol()],
                        target_squares=[chess.square_name(move.to_square)],
                        eval_swing=eval_after - eval_before
                    ))
        
        # Pattern 2: Fork detection (piece attacks multiple valuable pieces)
        if moving_piece:
            attacked_squares = board_after.attacks(move.to_square)
            valuable_targets = []
            for sq in attacked_squares:
                target = board_after.piece_at(sq)
                if target and target.color != moving_piece.color:
                    if target.piece_type in [chess.KING, chess.QUEEN, chess.ROOK]:
                        valuable_targets.append((target, sq))
            
            if len(valuable_targets) >= 2:
                patterns.append(TacticalPattern(
                    pattern_type="fork",
                    description=f"{chess.piece_name(moving_piece.piece_type).title()} forks multiple pieces",
                    pieces_involved=[t[0].symbol() for t in valuable_targets],
                    target_squares=[chess.square_name(t[1]) for t in valuable_targets]
                ))
        
        # Pattern 3: Discovered attack (moving piece reveals attack by another piece)
        # This is complex - check if any piece now attacks something it didn't before
        
        # Pattern 4: Pin detection
        # Check if any enemy piece is now pinned to king or queen
        enemy_color = not board_after.turn
        enemy_king = board_after.king(enemy_color)
        
        if enemy_king:
            # Look for pieces between our sliding pieces and enemy king
            for piece_type in [chess.BISHOP, chess.ROOK, chess.QUEEN]:
                for attacker_sq in board_after.pieces(piece_type, board_after.turn):
                    # Check if there's exactly one piece between attacker and king
                    between = chess.SquareSet(chess.between(attacker_sq, enemy_king))
                    blockers = []
                    for sq in between:
                        if board_after.piece_at(sq):
                            blockers.append(sq)
                    
                    if len(blockers) == 1:
                        blocked_piece = board_after.piece_at(blockers[0])
                        if blocked_piece and blocked_piece.color == enemy_color:
                            patterns.append(TacticalPattern(
                                pattern_type="pin",
                                description=f"{chess.piece_name(blocked_piece.piece_type).title()} pinned to king",
                                pieces_involved=[blocked_piece.symbol()],
                                target_squares=[chess.square_name(blockers[0])]
                            ))
        
        # Pattern 5: Large eval swing = tactical sequence
        eval_swing = abs(eval_after - eval_before)
        if eval_swing > 1.5:  # More than 1.5 pawns
            patterns.append(TacticalPattern(
                pattern_type="tactical_sequence",
                description="Initiates a tactical sequence with significant evaluation change",
                eval_swing=eval_swing
            ))
        
        return patterns
    
    # =========================================================================
    # LAYER 4: STRATEGIC CLASSIFICATION
    # =========================================================================
    
    def classify_move_strategically(self, board: chess.Board, move: chess.Move,
                                    features_before: PositionFeatures,
                                    features_after: PositionFeatures) -> List[MoveIntent]:
        """
        Classify the strategic nature of a move.
        
        Args:
            board: Position before move
            move: The move
            features_before: Position features before
            features_after: Position features after
            
        Returns:
            List of strategic intents (primary first)
        """
        intents = []
        moving_piece = board.piece_at(move.from_square)
        captured_piece = board.piece_at(move.to_square)
        mover_color = board.turn
        
        # Check for material gain
        if captured_piece:
            intents.append(MoveIntent.MATERIAL_GAIN)
        
        # Check for development
        if moving_piece and moving_piece.piece_type in [chess.KNIGHT, chess.BISHOP]:
            # First few moves - likely development
            if mover_color == chess.WHITE:
                if features_after.white_developed_pieces > features_before.white_developed_pieces:
                    intents.append(MoveIntent.DEVELOPMENT)
            else:
                if features_after.black_developed_pieces > features_before.black_developed_pieces:
                    intents.append(MoveIntent.DEVELOPMENT)
        
        # Check for castling (king safety)
        if board.is_castling(move):
            intents.append(MoveIntent.KING_SAFETY)
        
        # Check for center control improvement
        if mover_color == chess.WHITE:
            if features_after.white_center_control > features_before.white_center_control:
                intents.append(MoveIntent.CONTROL)
        else:
            if features_after.black_center_control > features_before.black_center_control:
                intents.append(MoveIntent.CONTROL)
        
        # Check for attack (pieces moving toward enemy king area)
        enemy_king = board.king(not mover_color)
        if enemy_king and moving_piece:
            # Check if piece moved closer to enemy king
            old_dist = chess.square_distance(move.from_square, enemy_king)
            new_dist = chess.square_distance(move.to_square, enemy_king)
            if new_dist < old_dist and moving_piece.piece_type != chess.KING:
                intents.append(MoveIntent.ATTACK)
        
        # Check for check (immediate attack)
        board_after = board.copy()
        board_after.push(move)
        if board_after.is_check():
            intents.append(MoveIntent.ATTACK)
        
        # Check for tempo gain (attacking something while improving)
        if not captured_piece and moving_piece:
            board_after = board.copy()
            board_after.push(move)
            attacks = board_after.attacks(move.to_square)
            for sq in attacks:
                target = board_after.piece_at(sq)
                if target and target.color != mover_color:
                    if target.piece_type in [chess.QUEEN, chess.ROOK]:
                        intents.append(MoveIntent.TEMPO)
                        break
        
        # Default: preparation if nothing else obvious
        if not intents:
            intents.append(MoveIntent.PREPARATION)
        
        return intents
    
    # =========================================================================
    # LAYER 5: INTENT INFERENCE (THE CORE "WHY")
    # =========================================================================
    
    def infer_sacrifice_compensation(self, board: chess.Board, move: chess.Move,
                                     features_before: PositionFeatures,
                                     features_after: PositionFeatures,
                                     eval_change: float,
                                     pv: List[str]) -> List[CompensationType]:
        """
        If a move is a sacrifice, determine what compensation is gained.
        
        Args:
            board: Position before move
            move: The sacrificial move
            features_before/after: Position features
            eval_change: How evaluation changed
            pv: Principal variation after the move
            
        Returns:
            List of compensation types
        """
        compensation = []
        mover = board.turn
        
        # Check for king exposure (compensation: attacking chances)
        if mover == chess.WHITE:
            if features_after.black_king_attackers > features_before.black_king_attackers:
                compensation.append(CompensationType.KING_EXPOSURE)
            if features_after.black_king_safety < features_before.black_king_safety - 50:
                compensation.append(CompensationType.ATTACK)
        else:
            if features_after.white_king_attackers > features_before.white_king_attackers:
                compensation.append(CompensationType.KING_EXPOSURE)
            if features_after.white_king_safety < features_before.white_king_safety - 50:
                compensation.append(CompensationType.ATTACK)
        
        # Check for activity improvement
        if mover == chess.WHITE:
            if features_after.white_mobility > features_before.white_mobility + 5:
                compensation.append(CompensationType.ACTIVITY)
        else:
            if features_after.black_mobility > features_before.black_mobility + 5:
                compensation.append(CompensationType.ACTIVITY)
        
        # Check for development lead
        if mover == chess.WHITE:
            dev_diff_before = features_before.white_developed_pieces - features_before.black_developed_pieces
            dev_diff_after = features_after.white_developed_pieces - features_after.black_developed_pieces
            if dev_diff_after > dev_diff_before:
                compensation.append(CompensationType.DEVELOPMENT_LEAD)
        else:
            dev_diff_before = features_before.black_developed_pieces - features_before.white_developed_pieces
            dev_diff_after = features_after.black_developed_pieces - features_after.white_developed_pieces
            if dev_diff_after > dev_diff_before:
                compensation.append(CompensationType.DEVELOPMENT_LEAD)
        
        # Analyze PV for forcing sequences (lots of checks = mating attack)
        check_count = 0
        board_copy = board.copy()
        board_copy.push(move)
        
        for pv_move_uci in pv[:6]:  # Check first 6 moves of PV
            try:
                pv_move = chess.Move.from_uci(pv_move_uci)
                if pv_move in board_copy.legal_moves:
                    board_copy.push(pv_move)
                    if board_copy.is_check():
                        check_count += 1
                else:
                    break  # Stop if move is not legal (position diverged)
            except Exception:
                break
        
        if check_count >= 2:
            compensation.append(CompensationType.MATING_ATTACK)
        
        # If eval improved significantly, there's initiative
        if eval_change > 0.5:
            compensation.append(CompensationType.INITIATIVE)
        
        return compensation
    
    # =========================================================================
    # LAYER 6: EXPLANATION ASSEMBLY
    # =========================================================================
    
    def analyze_move(self, fen: str, move_san: str) -> MoveAnalysis:
        """
        Complete analysis of a move - the main entry point.
        
        Explains WHY this move is good, bad, or interesting.
        
        Args:
            fen: Position before the move (FEN notation)
            move_san: The move in SAN notation (e.g., "Nf3", "Bxh7+")
            
        Returns:
            MoveAnalysis with complete explanation
        """
        self._ensure_engine()
        
        board = chess.Board(fen)
        
        # Parse the move
        try:
            move = board.parse_san(move_san)
        except:
            try:
                move = chess.Move.from_uci(move_san)
            except:
                raise ValueError(f"Invalid move: {move_san}")
        
        move_uci = move.uci()
        move_san_clean = board.san(move)
        
        # Get engine evaluation before and after
        eval_before_data = self.engine.get_eval(fen, depth=self.depth)
        
        # Get best move for comparison
        best_moves = self.engine.get_best_moves(fen, n=3, depth=self.depth)
        best_move_san = best_moves[0]['san'] if best_moves else None
        best_eval = best_moves[0]['score'] / 100 if best_moves and best_moves[0]['type'] == 'cp' else 0
        is_best = move_san_clean == best_move_san
        
        # Make the move and evaluate
        board_after = board.copy()
        board_after.push(move)
        eval_after_data = self.engine.get_eval(board_after.fen(), depth=self.depth)
        
        # Get PV from this position
        pv_data = self.engine.get_pv(board_after.fen(), depth=self.depth)
        pv_moves = pv_data[0] if pv_data else []
        
        # Convert evaluations
        eval_before = eval_before_data['score'] / 100 if eval_before_data['type'] == 'cp' else (100 if eval_before_data['score'] > 0 else -100)
        eval_after_raw = eval_after_data['score'] / 100 if eval_after_data['type'] == 'cp' else (100 if eval_after_data['score'] > 0 else -100)
        # Negate because it's opponent's turn
        eval_after = -eval_after_raw
        eval_delta = eval_after - eval_before
        
        # Extract features before and after
        features_before = self.extract_features(fen)
        features_after = self.extract_features(board_after.fen())
        
        # Detect threats before and after
        mover_color = board.turn
        threats_before = self.detect_threats(board, mover_color)
        threats_after = self.detect_threats(board_after, mover_color)
        
        # Detect tactical patterns
        tactical_patterns = self.detect_tactical_patterns(board, move, eval_before, eval_after)
        
        # Classify strategically
        strategic_intents = self.classify_move_strategically(board, move, features_before, features_after)
        
        # Check if sacrifice
        moving_piece = board.piece_at(move.from_square)
        captured_piece = board.piece_at(move.to_square)
        
        piece_values = {chess.PAWN: 100, chess.KNIGHT: 320, chess.BISHOP: 330,
                       chess.ROOK: 500, chess.QUEEN: 900, chess.KING: 0}
        
        is_sacrifice = False
        sacrifice_material = 0
        compensation_types = []
        
        if moving_piece:
            # Check if piece becomes hanging
            attackers = board_after.attackers(not mover_color, move.to_square)
            defenders = board_after.attackers(mover_color, move.to_square)
            
            my_value = piece_values.get(moving_piece.piece_type, 0)
            captured_value = piece_values.get(captured_piece.piece_type, 0) if captured_piece else 0
            
            if attackers:
                # Piece can be captured
                min_attacker_value = min(piece_values.get(board_after.piece_at(sq).piece_type, 0) 
                                        for sq in attackers if board_after.piece_at(sq))
                
                if my_value > min_attacker_value + captured_value + 50:  # More than half pawn sacrifice
                    is_sacrifice = True
                    sacrifice_material = my_value - captured_value
                    
                    if eval_delta > -1.0:  # Eval didn't crash, so there's compensation
                        compensation_types = self.infer_sacrifice_compensation(
                            board, move, features_before, features_after, eval_delta, pv_moves
                        )
        
        # Build achievements list
        achievements = []
        
        if captured_piece:
            achievements.append(f"Captures {chess.piece_name(captured_piece.piece_type)}")
        
        if board_after.is_check():
            achievements.append("Gives check")
        
        if board_after.is_checkmate():
            achievements.append("Checkmate!")
        
        if board.is_castling(move):
            achievements.append("Castles for king safety")
        
        # Threats created
        threats_created = []
        for threat in threats_after.hanging_pieces:
            if threat not in threats_before.hanging_pieces:
                threats_created.append(f"Creates threat to hanging {threat}")
        
        if threats_after.king_in_danger and not threats_before.king_in_danger:
            threats_created.append("Creates threats against enemy king")
        
        # Position improvements
        improvements = []
        drawbacks = []
        
        # Mobility change
        if mover_color == chess.WHITE:
            mob_change = features_after.white_mobility - features_before.white_mobility
        else:
            mob_change = features_after.black_mobility - features_before.black_mobility
        
        if mob_change > 3:
            improvements.append(f"Improves mobility (+{mob_change} moves available)")
        elif mob_change < -3:
            drawbacks.append(f"Reduces mobility ({mob_change} moves)")
        
        # Center control
        if mover_color == chess.WHITE:
            center_change = features_after.white_center_control - features_before.white_center_control
        else:
            center_change = features_after.black_center_control - features_before.black_center_control
        
        if center_change > 0:
            improvements.append(f"Improves center control (+{center_change})")
        
        # Build evidence
        evidence = []
        
        if is_best:
            evidence.append(f"This is the engine's top choice (eval: {eval_after:+.2f})")
        else:
            evidence.append(f"Eval after move: {eval_after:+.2f} (best was {best_move_san} at {best_eval:+.2f})")
        
        if tactical_patterns:
            for pattern in tactical_patterns:
                evidence.append(f"Tactical pattern: {pattern.description}")
        
        if is_sacrifice and compensation_types:
            comp_names = [c.value for c in compensation_types]
            evidence.append(f"Sacrifice compensation: {', '.join(comp_names)}")
        
        # PV explanation
        pv_explanation = ""
        if pv_moves:
            pv_san = []
            temp_board = board_after.copy()
            for pv_uci in pv_moves[:4]:
                try:
                    pv_move = chess.Move.from_uci(pv_uci)
                    if pv_move in temp_board.legal_moves:
                        pv_san.append(temp_board.san(pv_move))
                        temp_board.push(pv_move)
                    else:
                        break  # Stop if move is not legal
                except Exception:
                    break
            
            if pv_san:
                pv_explanation = f"Expected continuation: {' '.join(pv_san)}"
        
        # Determine if move is a mistake and why
        refutation = None
        mistake_reason = None
        
        if eval_delta < -0.5:  # Lost more than half a pawn
            mistake_reason = f"Loses {abs(eval_delta):.2f} pawns compared to best move"
            
            # Get opponent's best response (the refutation)
            try:
                opponent_best = self.engine.get_best_moves(board_after.fen(), n=1, depth=self.depth)
                if opponent_best:
                    refutation = opponent_best[0]['san']
                    # Analyze why refutation hurts
                    ref_board = board_after.copy()
                    ref_move = chess.Move.from_uci(opponent_best[0]['move'])
                    if ref_move in ref_board.legal_moves:
                        ref_board.push(ref_move)
                        
                        if ref_board.is_check():
                            mistake_reason += f" - allows {refutation} with check"
                        elif board_after.piece_at(ref_move.to_square):
                            captured = board_after.piece_at(ref_move.to_square)
                            mistake_reason += f" - loses {chess.piece_name(captured.piece_type)} to {refutation}"
            except Exception:
                pass  # Continue without refutation details
        
        # Build summary explanation
        primary_intent = strategic_intents[0] if strategic_intents else MoveIntent.PREPARATION
        secondary_intents = strategic_intents[1:] if len(strategic_intents) > 1 else []
        
        summary_parts = []
        
        if is_best:
            summary_parts.append(f"{move_san_clean} is the best move in this position")
        
        if is_sacrifice and compensation_types:
            comp_desc = compensation_types[0].value.replace('_', ' ')
            summary_parts.append(f"This is a sacrifice for {comp_desc}")
        elif primary_intent == MoveIntent.ATTACK:
            summary_parts.append("This move builds an attack")
        elif primary_intent == MoveIntent.DEVELOPMENT:
            summary_parts.append("This move develops a piece to an active square")
        elif primary_intent == MoveIntent.MATERIAL_GAIN:
            summary_parts.append("This move wins material")
        elif primary_intent == MoveIntent.KING_SAFETY:
            summary_parts.append("This move improves king safety")
        elif primary_intent == MoveIntent.CONTROL:
            summary_parts.append("This move fights for control of key squares")
        
        if achievements:
            summary_parts.append(f"It {', '.join(achievements).lower()}")
        
        if threats_created:
            summary_parts.append(f"It {threats_created[0].lower()}")
        
        if mistake_reason:
            summary_parts.append(f"However, this is inaccurate: {mistake_reason}")
        
        explanation_summary = ". ".join(summary_parts) + "." if summary_parts else ""
        
        return MoveAnalysis(
            move_san=move_san_clean,
            move_uci=move_uci,
            eval_before=eval_before,
            eval_after=eval_after,
            eval_delta=eval_delta,
            is_best_move=is_best,
            best_move_san=best_move_san,
            primary_intent=primary_intent,
            secondary_intents=secondary_intents,
            achievements=achievements,
            threats_created=threats_created,
            defenses_added=[],  # TODO: implement defense detection
            is_sacrifice=is_sacrifice,
            sacrifice_material=sacrifice_material,
            compensation_types=compensation_types,
            tactical_patterns=tactical_patterns,
            position_improvements=improvements,
            position_drawbacks=drawbacks,
            pv_explanation=pv_explanation,
            pv_outcome="",
            refutation=refutation,
            mistake_reason=mistake_reason,
            evidence=evidence,
            explanation_summary=explanation_summary
        )
    
    def explain_why_move_is_bad(self, fen: str, bad_move: str, best_move: str = None) -> Dict:
        """
        Explain specifically why a move is bad compared to the best.
        
        Args:
            fen: Position
            bad_move: The suboptimal move played
            best_move: The best move (if known, otherwise engine finds it)
            
        Returns:
            Dictionary with detailed comparison
        """
        self._ensure_engine()
        
        board = chess.Board(fen)
        
        # Get best move if not provided
        if best_move is None:
            best_data = self.engine.get_best_moves(fen, n=1, depth=self.depth)
            best_move = best_data[0]['san']
        
        # Analyze both moves
        bad_analysis = self.analyze_move(fen, bad_move)
        best_analysis = self.analyze_move(fen, best_move)
        
        # Compare
        eval_loss = best_analysis.eval_after - bad_analysis.eval_after
        
        comparison = {
            'bad_move': bad_move,
            'best_move': best_move,
            'eval_loss': eval_loss,
            'bad_move_eval': bad_analysis.eval_after,
            'best_move_eval': best_analysis.eval_after,
            'reasons': []
        }
        
        # What does the bad move fail to do?
        if best_analysis.achievements and not bad_analysis.achievements:
            comparison['reasons'].append(f"{best_move} achieves {', '.join(best_analysis.achievements)} while {bad_move} doesn't")
        
        # What threats does the bad move miss?
        if best_analysis.threats_created and not bad_analysis.threats_created:
            comparison['reasons'].append(f"{best_move} creates threats while {bad_move} is passive")
        
        # Does the bad move allow something?
        if bad_analysis.refutation:
            comparison['reasons'].append(f"{bad_move} allows {bad_analysis.refutation}")
            if bad_analysis.mistake_reason:
                comparison['reasons'].append(bad_analysis.mistake_reason)
        
        # Positional differences
        for improvement in best_analysis.position_improvements:
            if improvement not in bad_analysis.position_improvements:
                comparison['reasons'].append(f"{best_move}: {improvement}")
        
        for drawback in bad_analysis.position_drawbacks:
            if drawback not in best_analysis.position_drawbacks:
                comparison['reasons'].append(f"{bad_move}: {drawback}")
        
        # Intent difference
        if best_analysis.primary_intent != bad_analysis.primary_intent:
            comparison['reasons'].append(
                f"{best_move} focuses on {best_analysis.primary_intent.value} while {bad_move} is about {bad_analysis.primary_intent.value}"
            )
        
        return comparison
