"""
Board State Manager
Manages current position state with move navigation and position exploration.
"""

import chess
from typing import List, Optional, Dict
from enum import Enum


class MoveMode(Enum):
    """Mode for move tracking."""
    GAME_LINE = "game_line"  # Following the original game
    EXPLORATION = "exploration"  # User exploring variations


class BoardState:
    """
    Manages the current chess position with navigation capabilities.
    
    Supports:
    - Move navigation (next, previous, jump to position)
    - Temporary exploration branches (user can move pieces freely)
    - Legal move generation
    - Position history tracking
    """
    
    def __init__(self, starting_fen: Optional[str] = None):
        """
        Initialize board state.
        
        Args:
            starting_fen: FEN string for starting position.
                         If None, uses standard chess starting position.
        """
        if starting_fen:
            self.board = chess.Board(starting_fen)
        else:
            self.board = chess.Board()
        
        # Track position history
        self.history = [self.board.copy()]
        self.current_index = 0
        
        # Track mode
        self.mode = MoveMode.GAME_LINE
        
        # Store game line (for returning from exploration)
        self.game_line_history = []
        self.game_line_index = 0
    
    def set_game_line(self, boards: List[chess.Board]):
        """
        Set the main game line from PGN.
        
        Args:
            boards: List of board positions from the game
        """
        self.game_line_history = [board.copy() for board in boards]
        self.history = [board.copy() for board in boards]
        self.current_index = 0
        self.game_line_index = 0
        self.board = self.history[0].copy()
        self.mode = MoveMode.GAME_LINE
    
    def next_move(self) -> bool:
        """
        Navigate to the next position in history.
        
        Returns:
            True if successful, False if already at the end
        """
        if self.mode == MoveMode.EXPLORATION:
            # Cannot navigate forward in exploration mode
            return False
        
        if self.current_index < len(self.history) - 1:
            self.current_index += 1
            self.game_line_index = self.current_index
            self.board = self.history[self.current_index].copy()
            return True
        return False
    
    def previous_move(self) -> bool:
        """
        Navigate to the previous position in history.
        
        Returns:
            True if successful, False if already at the start
        """
        if self.current_index > 0:
            # If in exploration mode, this takes us back in the exploration
            # until we reach the point where exploration started
            self.current_index -= 1
            self.board = self.history[self.current_index].copy()
            
            # Check if we've returned to the game line
            if self.current_index <= self.game_line_index:
                self.mode = MoveMode.GAME_LINE
                self.game_line_index = self.current_index
            
            return True
        return False
    
    def jump_to_move(self, move_number: int) -> bool:
        """
        Jump directly to a specific move number in the game line.
        
        Args:
            move_number: Move number (0 = starting position)
        
        Returns:
            True if successful, False if move number invalid
        """
        # Can only jump within game line
        if move_number < 0 or move_number >= len(self.game_line_history):
            return False
        
        # Exit exploration mode and return to game line
        self.mode = MoveMode.GAME_LINE
        self.current_index = move_number
        self.game_line_index = move_number
        
        # Restore game line history
        self.history = [board.copy() for board in self.game_line_history]
        self.board = self.history[move_number].copy()
        
        return True
    
    def make_move(self, move: chess.Move) -> bool:
        """
        Make a move on the board (enters exploration mode).
        
        Args:
            move: chess.Move object
        
        Returns:
            True if move is legal and was made, False otherwise
        """
        if move not in self.board.legal_moves:
            return False
        
        # If we're in game line and not at the end, we're creating a variation
        if self.mode == MoveMode.GAME_LINE and self.current_index < len(self.game_line_history) - 1:
            # Enter exploration mode
            self.mode = MoveMode.EXPLORATION
            # Truncate history at current point
            self.history = self.history[:self.current_index + 1]
        
        # Make the move
        self.board.push(move)
        self.history.append(self.board.copy())
        self.current_index += 1
        
        # Mark as exploration if not following game line
        if self.mode == MoveMode.GAME_LINE:
            # Check if this move matches the next move in game line
            if self.current_index < len(self.game_line_history):
                game_line_board = self.game_line_history[self.current_index]
                if self.board.fen() != game_line_board.fen():
                    self.mode = MoveMode.EXPLORATION
                else:
                    self.game_line_index = self.current_index
            else:
                # Beyond the end of the game
                self.mode = MoveMode.EXPLORATION
        
        return True
    
    def make_uci_move(self, uci_move: str) -> bool:
        """
        Make a move using UCI notation.
        
        Args:
            uci_move: Move in UCI format (e.g., 'e2e4')
        
        Returns:
            True if move is legal and was made, False otherwise
        """
        try:
            move = chess.Move.from_uci(uci_move)
            return self.make_move(move)
        except ValueError:
            return False
    
    def get_legal_moves(self, notation: str = 'san') -> List[str]:
        """
        Get list of legal moves in current position.
        
        Args:
            notation: 'san' for standard notation or 'uci' for UCI notation
        
        Returns:
            List of legal moves in requested notation
        """
        if notation == 'san':
            return [self.board.san(move) for move in self.board.legal_moves]
        elif notation == 'uci':
            return [move.uci() for move in self.board.legal_moves]
        else:
            raise ValueError(f"Invalid notation: {notation}")
    
    def get_fen(self) -> str:
        """
        Get FEN of current position.
        
        Returns:
            FEN string
        """
        return self.board.fen()
    
    def get_board(self) -> chess.Board:
        """
        Get copy of current board.
        
        Returns:
            chess.Board object (copy, safe to modify)
        """
        return self.board.copy()
    
    def is_game_over(self) -> bool:
        """
        Check if the game is over (checkmate, stalemate, etc.).
        
        Returns:
            True if game is over
        """
        return self.board.is_game_over()
    
    def get_result(self) -> Optional[str]:
        """
        Get game result if game is over.
        
        Returns:
            Result string ('1-0', '0-1', '1/2-1/2') or None if game not over
        """
        if not self.board.is_game_over():
            return None
        
        result = self.board.result()
        return result
    
    def get_state_info(self) -> Dict:
        """
        Get information about current state.
        
        Returns:
            Dictionary with:
                - fen: Current position FEN
                - move_number: Current move number
                - total_moves: Total moves in history
                - mode: Current mode (game_line or exploration)
                - to_move: 'white' or 'black'
                - is_check: Boolean
                - is_checkmate: Boolean
                - is_stalemate: Boolean
        """
        return {
            'fen': self.board.fen(),
            'move_number': self.current_index,
            'total_moves': len(self.history) - 1,
            'mode': self.mode.value,
            'to_move': 'white' if self.board.turn == chess.WHITE else 'black',
            'is_check': self.board.is_check(),
            'is_checkmate': self.board.is_checkmate(),
            'is_stalemate': self.board.is_stalemate(),
            'in_game_line': self.mode == MoveMode.GAME_LINE
        }
    
    def reset_to_game_line(self):
        """
        Exit exploration mode and return to the game line at the last game position.
        """
        if self.mode == MoveMode.EXPLORATION:
            self.jump_to_move(self.game_line_index)
