"""
Deep Analysis Module - Enhanced Stockfish analysis with multi-move lookahead and explanations.

Provides structured analysis for LLM consumption:
- Principal variation with move-by-move explanations
- Position feature extraction
- Threat detection
- Alternative move analysis
"""

import chess
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum
import os
import sys

# Add parent directory for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from src.engine import StockfishEngine
except ImportError:
    from engine import StockfishEngine


class MoveRole(Enum):
    """Role a move plays in a position."""
    DEVELOPING = "developing"
    ATTACKING = "attacking"
    DEFENDING = "defending"
    EXCHANGING = "exchanging"
    RETREATING = "retreating"
    PROPHYLACTIC = "prophylactic"
    PAWN_BREAK = "pawn_break"
    CASTLING = "castling"
    CONSOLIDATING = "consolidating"
    FORCING = "forcing"


@dataclass
class MoveExplanation:
    """Explanation for a single move in the PV."""
    move_san: str
    move_uci: str
    role: MoveRole
    what_it_does: str
    why_it_matters: str
    threats_created: List[str] = field(default_factory=list)
    threats_addressed: List[str] = field(default_factory=list)


@dataclass
class DeepAnalysis:
    """Complete deep analysis of a position."""
    fen: str
    current_eval: float
    best_move: str
    best_move_eval: float
    
    # Multi-move lookahead
    principal_variation: List[str]
    pv_explanations: List[MoveExplanation]
    
    # Alternatives
    alternative_moves: List[Dict[str, Any]]
    
    # Threats
    threats: List[str]
    opponent_threats: List[str]
    
    # Position features
    material_balance: str
    piece_activity: str
    pawn_structure_notes: List[str]
    king_safety: Dict[str, str]
    key_squares: List[str]
    open_files: List[str]
    
    # For tactical positions
    tactical_motifs: List[str]
    
    # Phase
    game_phase: str  # opening, middlegame, endgame


class DeepAnalyzer:
    """Performs deep multi-move analysis with explanations."""
    
    def __init__(self, engine: Optional[StockfishEngine] = None):
        """Initialize with chess engine."""
        self.engine = engine or StockfishEngine()
    
    def analyze_position(
        self, 
        fen: str, 
        depth: int = 18,
        num_pv_moves: int = 5,
        num_alternatives: int = 3
    ) -> DeepAnalysis:
        """
        Perform deep analysis of a position with multi-move lookahead.
        
        Args:
            fen: Position to analyze
            depth: Engine search depth
            num_pv_moves: Number of moves in principal variation to analyze
            num_alternatives: Number of alternative moves to consider
            
        Returns:
            DeepAnalysis with comprehensive position understanding
        """
        board = chess.Board(fen)
        
        # Get engine analysis using get_best_moves
        analysis = self.engine.get_best_moves(fen, n=max(1, num_alternatives), depth=depth)
        
        # Extract principal variation
        pv_info = analysis[0] if analysis else {}
        pv_moves = pv_info.get('pv', [])[:num_pv_moves]
        score_type = pv_info.get('type', 'cp')
        score_val = pv_info.get('score', 0)
        
        # Convert score to pawns
        if score_type == 'mate':
            current_eval = 100.0 if score_val > 0 else -100.0  # Mate = huge eval
        else:
            current_eval = score_val / 100  # Convert centipawns to pawns
        
        best_move = pv_moves[0] if pv_moves else ""
        
        # Analyze PV moves one by one
        pv_explanations = self._explain_pv_sequence(board.copy(), pv_moves)
        
        # Get alternatives
        alternatives = []
        for i, alt in enumerate(analysis[1:num_alternatives+1] if len(analysis) > 1 else []):
            alt_move = alt.get('move', '')
            alt_pv = alt.get('pv', [])
            alt_score = alt.get('score', 0)
            alt_type = alt.get('type', 'cp')
            
            if alt_move:
                # Convert score
                if alt_type == 'mate':
                    alt_eval = 100.0 if alt_score > 0 else -100.0
                else:
                    alt_eval = alt_score / 100
                    
                alternatives.append({
                    'move': alt_move,
                    'eval': alt_eval,
                    'pv': alt_pv[:3],
                    'note': self._brief_move_description(board, alt_move)
                })
        
        # Position features
        threats = self._detect_threats_by_side(board, board.turn)
        opponent_threats = self._detect_threats_by_side(board, not board.turn)
        
        material = self._analyze_material(board)
        activity = self._analyze_piece_activity(board)
        pawn_notes = self._analyze_pawn_structure(board)
        king_safety = self._analyze_king_safety(board)
        key_squares = self._identify_key_squares(board)
        open_files = self._find_open_files(board)
        tactics = self._detect_tactical_motifs(board)
        phase = self._determine_game_phase(board)
        
        # Calculate eval after best move
        if best_move:
            test_board = board.copy()
            try:
                test_board.push_uci(best_move)
                after_analysis = self.engine.get_best_moves(test_board.fen(), n=1, depth=depth-2)
                if after_analysis:
                    after_score = after_analysis[0].get('score', 0)
                    after_type = after_analysis[0].get('type', 'cp')
                    if after_type == 'mate':
                        best_move_eval = -100.0 if after_score > 0 else 100.0  # Flip for opponent
                    else:
                        best_move_eval = -after_score / 100  # Flip sign for opponent's perspective
                else:
                    best_move_eval = current_eval
            except:
                best_move_eval = current_eval
        else:
            best_move_eval = current_eval
        
        # Convert PV to SAN for readability
        pv_san = []
        temp_board = board.copy()
        for move_uci in pv_moves:
            try:
                move = temp_board.parse_uci(move_uci)
                pv_san.append(temp_board.san(move))
                temp_board.push(move)
            except:
                break
        
        return DeepAnalysis(
            fen=fen,
            current_eval=current_eval,
            best_move=best_move,
            best_move_eval=best_move_eval,
            principal_variation=pv_san,
            pv_explanations=pv_explanations,
            alternative_moves=alternatives,
            threats=threats,
            opponent_threats=opponent_threats,
            material_balance=material,
            piece_activity=activity,
            pawn_structure_notes=pawn_notes,
            king_safety=king_safety,
            key_squares=key_squares,
            open_files=open_files,
            tactical_motifs=tactics,
            game_phase=phase
        )
    
    def _explain_pv_sequence(
        self, 
        board: chess.Board, 
        pv_moves: List[str]
    ) -> List[MoveExplanation]:
        """Explain each move in the principal variation."""
        explanations = []
        
        for i, move_uci in enumerate(pv_moves):
            try:
                move = board.parse_uci(move_uci)
                explanation = self._explain_single_move(board, move, i)
                explanations.append(explanation)
                board.push(move)
            except Exception as e:
                break
        
        return explanations
    
    def _explain_single_move(
        self, 
        board: chess.Board, 
        move: chess.Move,
        move_index: int
    ) -> MoveExplanation:
        """Generate explanation for a single move."""
        move_san = board.san(move)
        move_uci = move.uci()
        
        # Determine move role
        role = self._classify_move_role(board, move)
        
        # What the move does
        what_it_does = self._describe_move_action(board, move)
        
        # Why it matters (context-dependent)
        why_it_matters = self._explain_move_importance(board, move, move_index)
        
        # Threats created by this move
        board_after = board.copy()
        board_after.push(move)
        threats_created = self._detect_threats_by_side(board_after, board.turn)
        
        # What threats it addresses
        threats_addressed = self._find_addressed_threats(board, move)
        
        return MoveExplanation(
            move_san=move_san,
            move_uci=move_uci,
            role=role,
            what_it_does=what_it_does,
            why_it_matters=why_it_matters,
            threats_created=threats_created[:2],  # Top 2
            threats_addressed=threats_addressed[:2]
        )
    
    def _classify_move_role(self, board: chess.Board, move: chess.Move) -> MoveRole:
        """Classify the strategic role of a move."""
        piece = board.piece_at(move.from_square)
        
        # Castling
        if board.is_castling(move):
            return MoveRole.CASTLING
        
        # Capture
        if board.is_capture(move):
            return MoveRole.EXCHANGING
        
        # Check
        board_after = board.copy()
        board_after.push(move)
        if board_after.is_check():
            return MoveRole.FORCING
        
        # Pawn break
        if piece and piece.piece_type == chess.PAWN:
            # Check if pawn move opens lines
            from_file = chess.square_file(move.from_square)
            to_file = chess.square_file(move.to_square)
            if from_file != to_file or chess.square_rank(move.to_square) >= 4:
                return MoveRole.PAWN_BREAK
        
        # Development (minor pieces moving from back ranks)
        if piece and piece.piece_type in [chess.KNIGHT, chess.BISHOP]:
            back_rank = 0 if piece.color else 7
            if chess.square_rank(move.from_square) == back_rank:
                return MoveRole.DEVELOPING
        
        # Check if move is defensive
        if self._is_defensive_move(board, move):
            return MoveRole.DEFENDING
        
        # Check if move creates threats
        board_after = board.copy()
        board_after.push(move)
        if self._detect_threats_by_side(board_after, board.turn):
            return MoveRole.ATTACKING
        
        return MoveRole.CONSOLIDATING
    
    def _describe_move_action(self, board: chess.Board, move: chess.Move) -> str:
        """Describe what a move physically does."""
        piece = board.piece_at(move.from_square)
        captured = board.piece_at(move.to_square)
        
        piece_name = chess.piece_name(piece.piece_type).capitalize() if piece else "Piece"
        from_sq = chess.square_name(move.from_square)
        to_sq = chess.square_name(move.to_square)
        
        if board.is_castling(move):
            if move.to_square > move.from_square:
                return "Castles kingside, connecting the rooks and safeguarding the king"
            else:
                return "Castles queenside, bringing the rook toward the center"
        
        if captured:
            cap_name = chess.piece_name(captured.piece_type)
            return f"{piece_name} takes {cap_name} on {to_sq}"
        
        if move.promotion:
            promo_piece = chess.piece_name(move.promotion)
            return f"Pawn promotes to {promo_piece} on {to_sq}"
        
        # Check if giving check
        board_after = board.copy()
        board_after.push(move)
        if board_after.is_check():
            return f"{piece_name} moves to {to_sq} with check"
        
        return f"{piece_name} moves from {from_sq} to {to_sq}"
    
    def _explain_move_importance(
        self, 
        board: chess.Board, 
        move: chess.Move,
        move_index: int
    ) -> str:
        """Explain why this move matters in context."""
        piece = board.piece_at(move.from_square)
        
        # First move in PV
        if move_index == 0:
            if board.is_check():
                return "Addresses the check while maintaining position"
            if board.is_capture(move):
                return "Initiates an important exchange"
            return "This is the most accurate move in the position"
        
        # Response move (index 1, 3, etc.)
        if move_index % 2 == 1:
            if board.is_capture(move):
                return "Recaptures to restore material balance"
            return "Best defense against the threat"
        
        # Follow-up (index 2, 4)
        board_after = board.copy()
        board_after.push(move)
        
        if board_after.is_check():
            return "Continues the attack with check"
        if board.is_capture(move):
            return "Maintains pressure with the exchange"
        
        return "Continues the plan logically"
    
    def _is_defensive_move(self, board: chess.Board, move: chess.Move) -> bool:
        """Check if a move is primarily defensive."""
        piece = board.piece_at(move.from_square)
        if not piece:
            return False
        
        # Moving the king (not castling) is often defensive
        if piece.piece_type == chess.KING and not board.is_castling(move):
            return True
        
        # Moving a piece to block check
        if board.is_check():
            return True
        
        # Moving to defend an attacked piece
        # (simplified check - piece moves to square that defends attacked piece)
        return False
    
    def _detect_threats_by_side(self, board: chess.Board, color: bool) -> List[str]:
        """Detect threats from the perspective of one side."""
        threats = []
        
        for move in board.legal_moves:
            if board.turn == color:
                # Check if this is a threatening move
                if board.is_capture(move):
                    captured = board.piece_at(move.to_square)
                    if captured and captured.piece_type >= chess.KNIGHT:
                        piece = board.piece_at(move.from_square)
                        cap_name = chess.piece_name(captured.piece_type)
                        threats.append(f"Threatens to take {cap_name} on {chess.square_name(move.to_square)}")
                
                # Check threats
                board_after = board.copy()
                board_after.push(move)
                if board_after.is_checkmate():
                    threats.append(f"Threatens checkmate with {board.san(move)}")
                elif board_after.is_check():
                    threats.append(f"Can give check with {board.san(move)}")
        
        return threats[:3]  # Top 3 threats
    
    def _find_addressed_threats(self, board: chess.Board, move: chess.Move) -> List[str]:
        """Find what threats a move addresses."""
        addressed = []
        
        # If in check, the move addresses the check
        if board.is_check():
            addressed.append("Addresses the check")
        
        # Check if piece was attacked and is now safe
        piece = board.piece_at(move.from_square)
        if piece and board.is_attacked_by(not board.turn, move.from_square):
            addressed.append(f"Saves the attacked {chess.piece_name(piece.piece_type)}")
        
        return addressed
    
    def _analyze_material(self, board: chess.Board) -> str:
        """Analyze material balance."""
        piece_values = {
            chess.PAWN: 1, chess.KNIGHT: 3, chess.BISHOP: 3,
            chess.ROOK: 5, chess.QUEEN: 9
        }
        
        white_material = 0
        black_material = 0
        
        for square in chess.SQUARES:
            piece = board.piece_at(square)
            if piece:
                value = piece_values.get(piece.piece_type, 0)
                if piece.color == chess.WHITE:
                    white_material += value
                else:
                    black_material += value
        
        diff = white_material - black_material
        
        if diff == 0:
            return "Material is equal"
        elif abs(diff) == 1:
            return f"{'White' if diff > 0 else 'Black'} is up a pawn"
        elif abs(diff) == 2:
            return f"{'White' if diff > 0 else 'Black'} is up two pawns"
        elif abs(diff) == 3:
            return f"{'White' if diff > 0 else 'Black'} is up a minor piece"
        elif abs(diff) == 5:
            return f"{'White' if diff > 0 else 'Black'} is up a rook"
        elif abs(diff) > 5:
            return f"{'White' if diff > 0 else 'Black'} has decisive material advantage"
        else:
            return f"{'White' if diff > 0 else 'Black'} has a material advantage of {abs(diff)} points"
    
    def _analyze_piece_activity(self, board: chess.Board) -> str:
        """Analyze overall piece activity."""
        white_activity = 0
        black_activity = 0
        
        for square in chess.SQUARES:
            piece = board.piece_at(square)
            if piece and piece.piece_type != chess.KING:
                # Count attacked squares as activity
                attacks = len(list(board.attacks(square)))
                if piece.color == chess.WHITE:
                    white_activity += attacks
                else:
                    black_activity += attacks
        
        diff = white_activity - black_activity
        
        if abs(diff) < 5:
            return "Piece activity is roughly equal"
        elif diff > 10:
            return "White's pieces are significantly more active"
        elif diff > 0:
            return "White's pieces are slightly more active"
        elif diff < -10:
            return "Black's pieces are significantly more active"
        else:
            return "Black's pieces are slightly more active"
    
    def _analyze_pawn_structure(self, board: chess.Board) -> List[str]:
        """Analyze pawn structure for notable features."""
        notes = []
        
        white_pawns = list(board.pieces(chess.PAWN, chess.WHITE))
        black_pawns = list(board.pieces(chess.PAWN, chess.BLACK))
        
        # Check for doubled pawns
        for color, pawns in [(True, white_pawns), (False, black_pawns)]:
            files = [chess.square_file(sq) for sq in pawns]
            doubled = [f for f in set(files) if files.count(f) > 1]
            if doubled:
                file_names = [chr(ord('a') + f) for f in doubled]
                notes.append(f"{'White' if color else 'Black'} has doubled pawns on {', '.join(file_names)}-file")
        
        # Check for isolated pawns
        for color, pawns in [(True, white_pawns), (False, black_pawns)]:
            for sq in pawns:
                file = chess.square_file(sq)
                adjacent_pawns = any(
                    chess.square_file(p) in [file-1, file+1] 
                    for p in (white_pawns if color else black_pawns)
                )
                if not adjacent_pawns:
                    notes.append(f"{'White' if color else 'Black'} has isolated pawn on {chr(ord('a') + file)}-file")
        
        # Check for passed pawns
        for color, pawns in [(True, white_pawns), (False, black_pawns)]:
            enemy_pawns = black_pawns if color else white_pawns
            for sq in pawns:
                file = chess.square_file(sq)
                rank = chess.square_rank(sq)
                # Check if any enemy pawns can block or capture
                blocking = False
                for ep in enemy_pawns:
                    ef = chess.square_file(ep)
                    er = chess.square_rank(ep)
                    if abs(ef - file) <= 1:
                        if color and er > rank:
                            blocking = True
                        elif not color and er < rank:
                            blocking = True
                if not blocking:
                    notes.append(f"{'White' if color else 'Black'} has passed pawn on {chess.square_name(sq)}")
        
        return notes[:4]  # Limit to 4 most notable
    
    def _analyze_king_safety(self, board: chess.Board) -> Dict[str, str]:
        """Analyze king safety for both sides."""
        result = {}
        
        for color in [chess.WHITE, chess.BLACK]:
            king_sq = board.king(color)
            color_name = "White" if color else "Black"
            
            if king_sq is None:
                result[color_name] = "No king found"
                continue
            
            king_file = chess.square_file(king_sq)
            king_rank = chess.square_rank(king_sq)
            
            # Check if castled
            if color == chess.WHITE:
                if king_file >= 6 and king_rank == 0:
                    safety = "Castled kingside"
                elif king_file <= 2 and king_rank == 0:
                    safety = "Castled queenside"
                elif king_rank == 0:
                    safety = "King in center (may be vulnerable)"
                else:
                    safety = "King exposed"
            else:
                if king_file >= 6 and king_rank == 7:
                    safety = "Castled kingside"
                elif king_file <= 2 and king_rank == 7:
                    safety = "Castled queenside"
                elif king_rank == 7:
                    safety = "King in center (may be vulnerable)"
                else:
                    safety = "King exposed"
            
            # Check attackers near king
            attacks = len(board.attackers(not color, king_sq))
            if attacks > 0:
                safety += f", under direct attack"
            
            result[color_name] = safety
        
        return result
    
    def _identify_key_squares(self, board: chess.Board) -> List[str]:
        """Identify key squares in the position."""
        key_squares = []
        
        # Central squares
        for sq in [chess.E4, chess.D4, chess.E5, chess.D5]:
            piece = board.piece_at(sq)
            if piece:
                key_squares.append(f"{chess.square_name(sq)} (occupied by {chess.piece_name(piece.piece_type)})")
        
        return key_squares[:3]
    
    def _find_open_files(self, board: chess.Board) -> List[str]:
        """Find open and semi-open files."""
        open_files = []
        
        for file in range(8):
            white_pawns_on_file = any(
                board.piece_at(chess.square(file, rank)) == chess.Piece(chess.PAWN, chess.WHITE)
                for rank in range(8)
            )
            black_pawns_on_file = any(
                board.piece_at(chess.square(file, rank)) == chess.Piece(chess.PAWN, chess.BLACK)
                for rank in range(8)
            )
            
            file_name = chr(ord('a') + file)
            if not white_pawns_on_file and not black_pawns_on_file:
                open_files.append(f"{file_name}-file (open)")
            elif not white_pawns_on_file:
                open_files.append(f"{file_name}-file (semi-open for White)")
            elif not black_pawns_on_file:
                open_files.append(f"{file_name}-file (semi-open for Black)")
        
        return open_files[:3]
    
    def _detect_tactical_motifs(self, board: chess.Board) -> List[str]:
        """Detect common tactical motifs."""
        motifs = []
        
        # Check for pins
        for sq in chess.SQUARES:
            piece = board.piece_at(sq)
            if piece and piece.color == board.turn:
                # Check if pinned
                if board.is_pinned(board.turn, sq):
                    motifs.append(f"{chess.piece_name(piece.piece_type).capitalize()} on {chess.square_name(sq)} is pinned")
        
        # Check for forks (simplified)
        for move in board.legal_moves:
            board_after = board.copy()
            board_after.push(move)
            
            # Get the piece that just moved
            piece = board_after.piece_at(move.to_square)
            if piece and piece.piece_type == chess.KNIGHT:
                # Count attacked valuable pieces
                attacked_valuable = 0
                for attacked_sq in board_after.attacks(move.to_square):
                    target = board_after.piece_at(attacked_sq)
                    if target and target.color != piece.color:
                        if target.piece_type in [chess.QUEEN, chess.ROOK, chess.KING]:
                            attacked_valuable += 1
                
                if attacked_valuable >= 2:
                    motifs.append(f"Knight fork possible with {board.san(move)}")
        
        return motifs[:3]
    
    def _determine_game_phase(self, board: chess.Board) -> str:
        """Determine the game phase."""
        # Count pieces
        num_pieces = len(list(board.piece_map()))
        queens = len(list(board.pieces(chess.QUEEN, chess.WHITE))) + len(list(board.pieces(chess.QUEEN, chess.BLACK)))
        
        if num_pieces <= 10:
            return "endgame"
        elif num_pieces >= 28:
            return "opening"
        elif queens == 0:
            return "endgame"
        else:
            return "middlegame"
    
    def _brief_move_description(self, board: chess.Board, move_uci: str) -> str:
        """Get a brief description of a move."""
        try:
            move = board.parse_uci(move_uci)
            san = board.san(move)
            piece = board.piece_at(move.from_square)
            
            if board.is_capture(move):
                return f"Captures with {san}"
            elif board.is_castling(move):
                return "Castles"
            elif piece:
                return f"{chess.piece_name(piece.piece_type).capitalize()} move"
            return "Alternative"
        except:
            return "Alternative"
    
    def analyze_move(
        self, 
        fen: str, 
        move: str,
        depth: int = 16
    ) -> Dict[str, Any]:
        """
        Analyze a specific move in detail.
        
        Returns evaluation, quality assessment, and what happens next.
        """
        board = chess.Board(fen)
        
        # Get analysis of current position
        before_analysis = self.engine.get_best_moves(fen, n=1, depth=depth)
        best_before = before_analysis[0] if before_analysis else {}
        best_move = best_before.get('move', '')
        
        # Extract and convert score
        best_score_val = best_before.get('score', 0)
        best_score_type = best_before.get('type', 'cp')
        if best_score_type == 'mate':
            best_eval = 100.0 if best_score_val > 0 else -100.0
        else:
            best_eval = best_score_val / 100
        
        # Make the move and analyze
        try:
            move_obj = board.parse_san(move) if not move[0].isdigit() else board.parse_uci(move)
        except:
            try:
                move_obj = board.parse_uci(move)
            except:
                return {'error': f"Invalid move: {move}"}
        
        move_san = board.san(move_obj)
        move_uci = move_obj.uci()
        board.push(move_obj)
        
        # Analyze position after move
        after_analysis = self.engine.get_best_moves(board.fen(), n=1, depth=depth)
        after_info = after_analysis[0] if after_analysis else {}
        
        # Extract and convert score (negate because it's from opponent's view)
        after_score_val = after_info.get('score', 0)
        after_score_type = after_info.get('type', 'cp')
        if after_score_type == 'mate':
            after_eval = -(100.0 if after_score_val > 0 else -100.0)
        else:
            after_eval = -after_score_val / 100
        
        # What happens next
        pv_after = after_info.get('pv', [])[:4]
        
        # Convert to SAN
        temp_board = board.copy()
        pv_san = []
        for pv_move in pv_after:
            try:
                m = temp_board.parse_uci(pv_move)
                pv_san.append(temp_board.san(m))
                temp_board.push(m)
            except:
                break
        
        # Determine quality
        if move_uci == best_move:
            quality = "Best move"
        else:
            eval_loss = best_eval - after_eval if board.turn == chess.BLACK else after_eval - best_eval
            if eval_loss < 0.1:
                quality = "Excellent - essentially best"
            elif eval_loss < 0.3:
                quality = "Good - minor inaccuracy"
            elif eval_loss < 0.7:
                quality = "Inaccuracy"
            elif eval_loss < 1.5:
                quality = "Mistake"
            else:
                quality = "Blunder"
        
        return {
            'move': move_san,
            'move_uci': move_uci,
            'eval_after': after_eval,
            'best_move': best_move,
            'best_eval': best_eval,
            'quality': quality,
            'continuation': pv_san,
            'continuation_explained': self._explain_continuation(board, pv_after)
        }
    
    def _explain_continuation(self, board: chess.Board, pv: List[str]) -> List[str]:
        """Explain what happens in the continuation."""
        explanations = []
        temp_board = board.copy()
        
        for i, move_uci in enumerate(pv[:4]):
            try:
                move = temp_board.parse_uci(move_uci)
                san = temp_board.san(move)
                
                # Brief explanation
                if temp_board.is_capture(move):
                    captured = temp_board.piece_at(move.to_square)
                    if captured:
                        explanations.append(f"{san}: Takes {chess.piece_name(captured.piece_type)}")
                    else:
                        explanations.append(f"{san}: Captures")
                elif temp_board.gives_check(move):
                    explanations.append(f"{san}: Check")
                else:
                    piece = temp_board.piece_at(move.from_square)
                    if piece:
                        explanations.append(f"{san}: {chess.piece_name(piece.piece_type).capitalize()} move")
                    else:
                        explanations.append(f"{san}")
                
                temp_board.push(move)
            except:
                break
        
        return explanations


# =============================================================================
# UTILITY FUNCTION FOR LLM CONTEXT
# =============================================================================

def format_deep_analysis_for_llm(analysis: DeepAnalysis) -> str:
    """Format DeepAnalysis into LLM-friendly context."""
    
    context = f"""
=== POSITION ANALYSIS ===
FEN: {analysis.fen}
Game Phase: {analysis.game_phase}
Evaluation: {analysis.current_eval:+.2f} (positive = White advantage)

=== BEST MOVE ===
{analysis.best_move} (eval after: {analysis.best_move_eval:+.2f})

=== PRINCIPAL VARIATION (Next {len(analysis.principal_variation)} moves) ===
{' '.join(analysis.principal_variation)}

Move-by-move breakdown:
"""
    
    for i, exp in enumerate(analysis.pv_explanations):
        context += f"""
  {i+1}. {exp.move_san} ({exp.role.value})
      What: {exp.what_it_does}
      Why: {exp.why_it_matters}
"""
        if exp.threats_created:
            context += f"      Creates: {', '.join(exp.threats_created)}\n"
    
    if analysis.alternative_moves:
        context += "\n=== ALTERNATIVES ===\n"
        for alt in analysis.alternative_moves:
            context += f"  {alt['move']}: {alt['eval']:+.2f} - {alt.get('note', '')}\n"
    
    if analysis.threats or analysis.opponent_threats:
        context += "\n=== THREATS ===\n"
        for t in analysis.threats:
            context += f"  + {t}\n"
        for t in analysis.opponent_threats:
            context += f"  - Opponent: {t}\n"
    
    context += f"""
=== POSITION FEATURES ===
Material: {analysis.material_balance}
Piece Activity: {analysis.piece_activity}
King Safety:
  White: {analysis.king_safety.get('White', 'Unknown')}
  Black: {analysis.king_safety.get('Black', 'Unknown')}
"""
    
    if analysis.pawn_structure_notes:
        context += f"Pawn Structure: {', '.join(analysis.pawn_structure_notes)}\n"
    
    if analysis.open_files:
        context += f"Files: {', '.join(analysis.open_files)}\n"
    
    if analysis.tactical_motifs:
        context += f"Tactical Notes: {', '.join(analysis.tactical_motifs)}\n"
    
    return context
