"""
PGN Parser Module
Loads and parses chess games in PGN (Portable Game Notation) format.
Provides game metadata extraction and position navigation.
"""

import chess
import chess.pgn
from typing import Dict, List, Optional
from pathlib import Path


class PGNGame:
    """
    Represents a chess game loaded from PGN format.
    
    Provides access to:
    - Game metadata (players, date, result, opening, etc.)
    - Move list in multiple formats (SAN, UCI)
    - Position at any move number
    - Move navigation functionality
    """
    
    def __init__(self, pgn_path: str):
        """
        Load a chess game from PGN file.
        
        Args:
            pgn_path: Path to PGN file
            
        Raises:
            FileNotFoundError: If PGN file does not exist
            ValueError: If PGN file is invalid or empty
        """
        pgn_file = Path(pgn_path)
        if not pgn_file.exists():
            raise FileNotFoundError(f"PGN file not found: {pgn_path}")
        
        with open(pgn_path, 'r', encoding='utf-8') as f:
            self.game = chess.pgn.read_game(f)
        
        if self.game is None:
            raise ValueError(f"Invalid or empty PGN file: {pgn_path}")
        
        # Build move list and boards
        self._build_move_list()
    
    def _build_move_list(self):
        """
        Build internal list of moves and board positions.
        Stores both SAN and UCI notation for each move.
        """
        self.moves = []  # List of dicts with move info
        self.boards = []  # List of board states at each position
        
        board = self.game.board()
        self.boards.append(board.copy())  # Starting position
        
        for move in self.game.mainline_moves():
            move_info = {
                'san': board.san(move),
                'uci': move.uci(),
                'move_number': len(self.moves) + 1,
                'color': 'white' if board.turn == chess.WHITE else 'black'
            }
            self.moves.append(move_info)
            
            board.push(move)
            self.boards.append(board.copy())
    
    def get_metadata(self) -> Dict[str, str]:
        """
        Extract game metadata from PGN headers.
        
        Returns:
            Dictionary with game information:
                - event: Tournament/match name
                - site: Location or URL
                - date: Date in YYYY.MM.DD format
                - round: Round number
                - white: White player name
                - black: Black player name
                - result: Game result (1-0, 0-1, 1/2-1/2, or *)
                - white_elo: White player's rating
                - black_elo: Black player's rating
                - eco: ECO opening code
                - opening: Opening name
                - time_control: Time control string
                And any other custom headers
        """
        headers = dict(self.game.headers)
        
        # Normalize common header names to lowercase with underscores
        normalized = {}
        key_mapping = {
            'Event': 'event',
            'Site': 'site',
            'Date': 'date',
            'Round': 'round',
            'White': 'white',
            'Black': 'black',
            'Result': 'result',
            'WhiteElo': 'white_elo',
            'BlackElo': 'black_elo',
            'ECO': 'eco',
            'Opening': 'opening',
            'TimeControl': 'time_control',
            'Termination': 'termination',
            'Variant': 'variant'
        }
        
        for key, value in headers.items():
            normalized_key = key_mapping.get(key, key.lower())
            normalized[normalized_key] = value
        
        return normalized
    
    def get_move_list(self, notation: str = 'san') -> List[str]:
        """
        Get list of all moves in the game.
        
        Args:
            notation: Move notation format - 'san' (default) or 'uci'
        
        Returns:
            List of moves in requested notation
            
        Example:
            >>> game.get_move_list('san')
            ['d4', 'd5', 'c4', 'Nf6', 'Nc3', 'dxc4', ...]
            >>> game.get_move_list('uci')
            ['d2d4', 'd7d5', 'c2c4', 'g8f6', 'b1c3', 'd5c4', ...]
        """
        if notation == 'san':
            return [move['san'] for move in self.moves]
        elif notation == 'uci':
            return [move['uci'] for move in self.moves]
        else:
            raise ValueError(f"Invalid notation: {notation}. Use 'san' or 'uci'")
    
    def get_fen_at_move(self, move_number: int) -> str:
        """
        Get FEN (board position) at specific move number.
        
        Args:
            move_number: Move number (0 = starting position, 1 = after first move, etc.)
        
        Returns:
            FEN string representing the position
            
        Raises:
            IndexError: If move_number is out of range
            
        Example:
            >>> game.get_fen_at_move(0)  # Starting position
            'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1'
        """
        if move_number < 0 or move_number > len(self.moves):
            raise IndexError(f"Move number {move_number} out of range (0-{len(self.moves)})")
        
        return self.boards[move_number].fen()
    
    def get_board_at_move(self, move_number: int) -> chess.Board:
        """
        Get chess.Board object at specific move number.
        
        Args:
            move_number: Move number (0 = starting position)
        
        Returns:
            chess.Board object (copy, safe to modify)
        """
        if move_number < 0 or move_number > len(self.moves):
            raise IndexError(f"Move number {move_number} out of range (0-{len(self.moves)})")
        
        return self.boards[move_number].copy()
    
    def total_moves(self) -> int:
        """
        Get total number of moves in the game.
        
        Returns:
            Number of half-moves (plies) in the game
        """
        return len(self.moves)
    
    def get_move_info(self, move_number: int) -> Dict:
        """
        Get detailed information about a specific move.
        
        Args:
            move_number: Move number (1-indexed for moves)
        
        Returns:
            Dictionary with move information:
                - san: Move in standard algebraic notation
                - uci: Move in UCI notation
                - move_number: Move number
                - color: 'white' or 'black'
        """
        if move_number < 1 or move_number > len(self.moves):
            raise IndexError(f"Move number {move_number} out of range (1-{len(self.moves)})")
        
        return self.moves[move_number - 1].copy()
    
    def __repr__(self) -> str:
        """String representation of the game."""
        metadata = self.get_metadata()
        white = metadata.get('white', 'Unknown')
        black = metadata.get('black', 'Unknown')
        result = metadata.get('result', '*')
        total = self.total_moves()
        
        return f"PGNGame({white} vs {black}, {result}, {total} moves)"
