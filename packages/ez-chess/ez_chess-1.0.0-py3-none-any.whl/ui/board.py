"""
Chessboard Widget - A beautiful, interactive chess board.

Features:
- Stunning dark theme with green squares
- Smooth piece selection and move making
- Legal move indicators
- Last move highlighting
- Check highlighting
- Flip board support
- Drag and drop support
- Arrow annotations for best moves and threats
- Square highlighting for key squares
"""

import tkinter as tk
from tkinter import Canvas
import chess
import math
from typing import Optional, Tuple, List, Callable, Dict
from dataclasses import dataclass
from enum import Enum

from ui.theme import (
    BOARD_LIGHT, BOARD_DARK, BG_DARKEST, BG_DARK,
    HIGHLIGHT_LAST_MOVE, HIGHLIGHT_SELECTED, HIGHLIGHT_LEGAL, HIGHLIGHT_CHECK,
    TEXT_PRIMARY, TEXT_MUTED, ACCENT_PRIMARY, ACCENT_SUCCESS, ACCENT_DANGER, ACCENT_WARNING, ACCENT_PURPLE,
    PIECE_SYMBOLS, FONT_FAMILY
)


# =============================================================================
# ANNOTATION SYSTEM
# =============================================================================

class ArrowType(Enum):
    """Types of arrows that can be drawn on the board."""
    BEST_MOVE = "best_move"      # Blue - engine's best move
    GOOD_MOVE = "good_move"      # Green - good alternative
    THREAT = "threat"            # Red - opponent's threat
    INTERESTING = "interesting"  # Purple - interesting move
    USER = "user"                # Yellow - user-drawn arrow


class HighlightType(Enum):
    """Types of square highlights."""
    WEAKNESS = "weakness"        # Orange - weak square
    KEY_SQUARE = "key_square"    # Purple - strategically important
    ATTACKED = "attacked"        # Red - piece under attack
    DEFENDED = "defended"        # Blue - well-defended


@dataclass
class Arrow:
    """An arrow annotation from one square to another."""
    from_square: chess.Square
    to_square: chess.Square
    arrow_type: ArrowType
    
    @property
    def color(self) -> str:
        """Get hex color for this arrow type."""
        colors = {
            ArrowType.BEST_MOVE: "#58a6ff",      # Blue
            ArrowType.GOOD_MOVE: "#3fb950",      # Green
            ArrowType.THREAT: "#f85149",         # Red
            ArrowType.INTERESTING: "#a371f7",    # Purple
            ArrowType.USER: "#d29922",           # Yellow/Orange
        }
        return colors.get(self.arrow_type, "#58a6ff")
    
    @property
    def width(self) -> int:
        """Get line width for this arrow type."""
        widths = {
            ArrowType.BEST_MOVE: 5,
            ArrowType.GOOD_MOVE: 4,
            ArrowType.THREAT: 4,
            ArrowType.INTERESTING: 3,
            ArrowType.USER: 4,
        }
        return widths.get(self.arrow_type, 4)


@dataclass 
class SquareHighlight:
    """A square highlight annotation."""
    square: chess.Square
    highlight_type: HighlightType
    
    @property
    def color(self) -> str:
        """Get hex color for this highlight type."""
        colors = {
            HighlightType.WEAKNESS: "#ff9500",      # Orange
            HighlightType.KEY_SQUARE: "#a371f7",    # Purple
            HighlightType.ATTACKED: "#f85149",      # Red
            HighlightType.DEFENDED: "#58a6ff",      # Blue
        }
        return colors.get(self.highlight_type, "#a371f7")
    
    @property
    def alpha(self) -> float:
        """Get alpha transparency (0-1) for this highlight."""
        alphas = {
            HighlightType.WEAKNESS: 0.3,
            HighlightType.KEY_SQUARE: 0.25,
            HighlightType.ATTACKED: 0.35,
            HighlightType.DEFENDED: 0.2,
        }
        return alphas.get(self.highlight_type, 0.25)


class AnnotationManager:
    """Manages all board annotations (arrows and highlights)."""
    
    def __init__(self):
        self.arrows: List[Arrow] = []
        self.highlights: List[SquareHighlight] = []
    
    def clear(self):
        """Clear all annotations."""
        self.arrows = []
        self.highlights = []
    
    def clear_arrows(self):
        """Clear only arrows."""
        self.arrows = []
    
    def clear_highlights(self):
        """Clear only highlights."""
        self.highlights = []
    
    def add_arrow(self, from_sq: chess.Square, to_sq: chess.Square, 
                  arrow_type: ArrowType = ArrowType.USER):
        """Add an arrow annotation."""
        self.arrows.append(Arrow(from_sq, to_sq, arrow_type))
    
    def add_best_move_arrow(self, from_sq: chess.Square, to_sq: chess.Square):
        """Add arrow for best move."""
        self.arrows.append(Arrow(from_sq, to_sq, ArrowType.BEST_MOVE))
    
    def add_threat_arrow(self, from_sq: chess.Square, to_sq: chess.Square):
        """Add arrow for opponent threat."""
        self.arrows.append(Arrow(from_sq, to_sq, ArrowType.THREAT))
    
    def add_highlight(self, square: chess.Square, 
                      highlight_type: HighlightType = HighlightType.KEY_SQUARE):
        """Add a square highlight."""
        self.highlights.append(SquareHighlight(square, highlight_type))
    
    def add_from_analysis(self, analysis_result: Dict, board: chess.Board):
        """
        Populate annotations from analysis result.
        
        Args:
            analysis_result: Dict with 'best_moves', 'eval', etc.
            board: Current board position
        """
        self.clear()
        
        # Add best move arrow
        best_moves = analysis_result.get('best_moves', [])
        if best_moves:
            # Best move (blue)
            best = best_moves[0]
            try:
                move = board.parse_uci(best.get('move', ''))
                self.add_arrow(move.from_square, move.to_square, ArrowType.BEST_MOVE)
            except:
                pass
            
            # Second best (green) if significantly different
            if len(best_moves) > 1:
                second = best_moves[1]
                try:
                    move2 = board.parse_uci(second.get('move', ''))
                    self.add_arrow(move2.from_square, move2.to_square, ArrowType.GOOD_MOVE)
                except:
                    pass


class ChessBoardWidget(tk.Frame):
    """
    A beautiful chess board widget with full interactivity.
    
    Supports:
    - Click to select and move pieces
    - Visual feedback for legal moves
    - Last move highlighting
    - Check indication
    - Board flipping
    - Custom move callbacks
    - Arrow annotations for analysis
    - Square highlights for key squares
    """
    
    def __init__(
        self, 
        parent, 
        size: int = 560,
        on_move: Optional[Callable[[chess.Move], None]] = None,
        on_square_click: Optional[Callable[[str], None]] = None,
        interactive: bool = True
    ):
        super().__init__(parent, bg=BG_DARKEST)
        
        self.size = size
        self.square_size = size // 8
        self.on_move = on_move
        self.on_square_click = on_square_click
        self.interactive = interactive
        
        # Current state
        self.board = chess.Board()
        self.flipped = False
        self.last_move: Optional[chess.Move] = None
        self.selected_square: Optional[chess.Square] = None
        self.legal_move_squares: List[chess.Square] = []
        self.arrow_moves: List[chess.Move] = []
        
        # Annotation manager
        self.annotations = AnnotationManager()
        self.show_annotations = True
        
        # Create canvas with border effect
        self.outer_frame = tk.Frame(self, bg="#1a1a1a", padx=4, pady=4)
        self.outer_frame.pack()
        
        self.canvas = Canvas(
            self.outer_frame, 
            width=size, 
            height=size,
            bg=BG_DARK,
            highlightthickness=0
        )
        self.canvas.pack()
        
        # Bind events
        if interactive:
            self.canvas.bind("<Button-1>", self._on_click)
            self.canvas.bind("<B1-Motion>", self._on_drag)
            self.canvas.bind("<ButtonRelease-1>", self._on_release)
        
        # Drag state
        self.dragging = False
        self.drag_piece = None
        self.drag_start_square = None
        
        # Draw initial board
        self._draw_board()
    
    def set_position(self, fen: str, last_move: Optional[chess.Move] = None):
        """Set the board position from FEN."""
        try:
            self.board = chess.Board(fen)
            self.last_move = last_move
            self.selected_square = None
            self.legal_move_squares = []
            self._draw_board()
        except Exception as e:
            print(f"Error setting position: {e}")
    
    def set_board(self, board: chess.Board, last_move: Optional[chess.Move] = None):
        """Set the board directly from a chess.Board object."""
        self.board = board.copy()
        self.last_move = last_move
        self.selected_square = None
        self.legal_move_squares = []
        self._draw_board()
    
    def make_move(self, move: chess.Move) -> bool:
        """Make a move on the board."""
        if move in self.board.legal_moves:
            self.board.push(move)
            self.last_move = move
            self.selected_square = None
            self.legal_move_squares = []
            self._draw_board()
            
            if self.on_move:
                self.on_move(move)
            return True
        return False
    
    def undo_move(self) -> Optional[chess.Move]:
        """Undo the last move."""
        if self.board.move_stack:
            move = self.board.pop()
            self.last_move = self.board.move_stack[-1] if self.board.move_stack else None
            self.selected_square = None
            self.legal_move_squares = []
            self._draw_board()
            return move
        return None
    
    def flip(self):
        """Flip the board orientation."""
        self.flipped = not self.flipped
        self._draw_board()
    
    def show_arrows(self, moves: List[chess.Move]):
        """Show arrow indicators for moves (legacy method)."""
        self.arrow_moves = moves
        self._draw_board()
    
    def clear_arrows(self):
        """Clear all arrow indicators."""
        self.arrow_moves = []
        self.annotations.clear_arrows()
        self._draw_board()
    
    def set_annotations_from_analysis(self, analysis_result: Dict):
        """
        Set annotations from analysis result.
        
        Args:
            analysis_result: Dict with 'best_moves', 'eval', etc.
        """
        self.annotations.add_from_analysis(analysis_result, self.board)
        self._draw_board()
    
    def add_best_move_arrow(self, from_sq: str, to_sq: str):
        """Add arrow for best move using square names."""
        try:
            from_square = chess.parse_square(from_sq)
            to_square = chess.parse_square(to_sq)
            self.annotations.add_arrow(from_square, to_square, ArrowType.BEST_MOVE)
            self._draw_board()
        except:
            pass
    
    def add_threat_arrow(self, from_sq: str, to_sq: str):
        """Add arrow for threat using square names."""
        try:
            from_square = chess.parse_square(from_sq)
            to_square = chess.parse_square(to_sq)
            self.annotations.add_arrow(from_square, to_square, ArrowType.THREAT)
            self._draw_board()
        except:
            pass
    
    def highlight_square(self, square_name: str, highlight_type: HighlightType = HighlightType.KEY_SQUARE):
        """Highlight a square by name."""
        try:
            square = chess.parse_square(square_name)
            self.annotations.add_highlight(square, highlight_type)
            self._draw_board()
        except:
            pass
    
    def clear_annotations(self):
        """Clear all annotations."""
        self.annotations.clear()
        self._draw_board()
    
    def toggle_annotations(self, show: bool = None):
        """Toggle annotation visibility."""
        if show is not None:
            self.show_annotations = show
        else:
            self.show_annotations = not self.show_annotations
        self._draw_board()
    
    def get_fen(self) -> str:
        """Get the current FEN."""
        return self.board.fen()
    
    def get_board(self) -> chess.Board:
        """Get the current board."""
        return self.board.copy()
    
    def reset(self):
        """Reset to starting position."""
        self.board = chess.Board()
        self.last_move = None
        self.selected_square = None
        self.legal_move_squares = []
        self.arrow_moves = []
        self.annotations.clear()
        self._draw_board()
    
    # ─────────────────────────────────────────────────────────────────────────
    #                         COORDINATE CONVERSION
    # ─────────────────────────────────────────────────────────────────────────
    
    def _square_to_coords(self, square: chess.Square) -> Tuple[int, int, int, int]:
        """Convert chess square to canvas coordinates."""
        file = chess.square_file(square)
        rank = chess.square_rank(square)
        
        if self.flipped:
            x = (7 - file) * self.square_size
            y = rank * self.square_size
        else:
            x = file * self.square_size
            y = (7 - rank) * self.square_size
        
        return x, y, x + self.square_size, y + self.square_size
    
    def _coords_to_square(self, x: int, y: int) -> chess.Square:
        """Convert canvas coordinates to chess square."""
        file = min(7, max(0, x // self.square_size))
        rank = 7 - min(7, max(0, y // self.square_size))
        
        if self.flipped:
            file = 7 - file
            rank = 7 - rank
        
        return chess.square(file, rank)
    
    def _square_center(self, square: chess.Square) -> Tuple[int, int]:
        """Get the center coordinates of a square."""
        x1, y1, x2, y2 = self._square_to_coords(square)
        return (x1 + x2) // 2, (y1 + y2) // 2
    
    # ─────────────────────────────────────────────────────────────────────────
    #                              DRAWING
    # ─────────────────────────────────────────────────────────────────────────
    
    def _draw_board(self):
        """Draw the complete board."""
        self.canvas.delete("all")
        
        # Draw squares
        for square in chess.SQUARES:
            self._draw_square(square)
        
        # Draw annotation highlights (before pieces)
        if self.show_annotations:
            for highlight in self.annotations.highlights:
                self._draw_highlight(highlight)
        
        # Draw legal move indicators
        for square in self.legal_move_squares:
            self._draw_legal_indicator(square)
        
        # Draw pieces (hide source piece only when actively dragging)
        for square in chess.SQUARES:
            # Only hide piece if we're in the middle of dragging it
            if self.dragging and square == self.drag_start_square:
                continue
            piece = self.board.piece_at(square)
            if piece:
                self._draw_piece(square, piece)
        
        # Draw arrows for suggested moves (legacy)
        for move in self.arrow_moves:
            self._draw_arrow(move)
        
        # Draw annotation arrows (new system)
        if self.show_annotations:
            for arrow in self.annotations.arrows:
                self._draw_annotation_arrow(arrow)
        
        # Draw file/rank labels
        self._draw_labels()
        
        # Draw check indicator
        if self.board.is_check():
            king_square = self.board.king(self.board.turn)
            if king_square is not None:
                self._draw_check_indicator(king_square)
    
    def _draw_square(self, square: chess.Square):
        """Draw a single square."""
        x1, y1, x2, y2 = self._square_to_coords(square)
        
        # Determine base color
        is_light = (chess.square_file(square) + chess.square_rank(square)) % 2 == 1
        color = BOARD_LIGHT if is_light else BOARD_DARK
        
        # Highlight last move
        if self.last_move:
            if square in [self.last_move.from_square, self.last_move.to_square]:
                color = HIGHLIGHT_LAST_MOVE
        
        # Highlight selected square
        if square == self.selected_square:
            color = HIGHLIGHT_SELECTED
        
        self.canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline="")
    
    def _draw_legal_indicator(self, square: chess.Square):
        """Draw a legal move indicator on a square."""
        x1, y1, x2, y2 = self._square_to_coords(square)
        cx = (x1 + x2) // 2
        cy = (y1 + y2) // 2
        
        piece = self.board.piece_at(square)
        
        if piece:
            # Draw a ring for captures
            padding = self.square_size // 10
            self.canvas.create_oval(
                x1 + padding, y1 + padding, 
                x2 - padding, y2 - padding,
                outline="#3fb950", width=3
            )
        else:
            # Draw a dot for empty squares
            r = self.square_size // 6
            self.canvas.create_oval(
                cx - r, cy - r, cx + r, cy + r,
                fill="#2d7d4a", outline=""
            )
    
    def _draw_piece(self, square: chess.Square, piece: chess.Piece, 
                    offset_x: int = 0, offset_y: int = 0):
        """Draw a piece on a square or at an offset with royal wood aesthetic."""
        x1, y1, x2, y2 = self._square_to_coords(square)
        cx = (x1 + x2) // 2 + offset_x
        cy = (y1 + y2) // 2 + offset_y
        
        symbol = PIECE_SYMBOLS[piece.symbol()]
        font_size = int(self.square_size * 0.75)
        
        # Shadow for depth (larger for better effect)
        shadow_offset = max(2, self.square_size // 35)
        self.canvas.create_text(
            cx + shadow_offset, cy + shadow_offset,
            text=symbol,
            font=(FONT_FAMILY, font_size, "bold"),
            fill="#1a1410"
        )
        
        # Main piece with royal wood colors
        # White pieces: Elegant ivory/cream with warm undertones
        # Black pieces: Rich walnut/mahogany wood
        if piece.color == chess.WHITE:
            # Outer glow for white pieces (golden edge)
            self.canvas.create_text(
                cx - 1, cy - 1,
                text=symbol,
                font=(FONT_FAMILY, font_size, "bold"),
                fill="#d4af37"
            )
            piece_color = "#f5e6d3"  # Ivory
        else:
            # Darker outline for black pieces
            self.canvas.create_text(
                cx - 1, cy - 1,
                text=symbol,
                font=(FONT_FAMILY, font_size, "bold"),
                fill="#1a0f0a"
            )
            piece_color = "#3d2817"  # Dark walnut
        
        # Main piece
        self.canvas.create_text(
            cx, cy,
            text=symbol,
            font=(FONT_FAMILY, font_size, "bold"),
            fill=piece_color
        )
    
    def _draw_labels(self):
        """Draw file and rank labels."""
        font_size = max(9, int(self.square_size * 0.16))
        padding = 3
        
        for i in range(8):
            # File labels (a-h)
            file_idx = 7 - i if self.flipped else i
            file_label = chr(ord('a') + file_idx)
            x = i * self.square_size + self.square_size - padding
            y = self.size - padding
            
            is_light = (file_idx + 0) % 2 == 1
            color = BOARD_DARK if is_light else BOARD_LIGHT
            
            self.canvas.create_text(
                x, y, text=file_label, 
                font=(FONT_FAMILY, font_size, "bold"), 
                fill=color, anchor="se"
            )
            
            # Rank labels (1-8)
            rank_idx = i if self.flipped else 7 - i
            rank_label = str(rank_idx + 1)
            x = padding
            y = i * self.square_size + padding
            
            is_light = (0 + rank_idx) % 2 == 1
            color = BOARD_DARK if is_light else BOARD_LIGHT
            
            self.canvas.create_text(
                x, y, text=rank_label, 
                font=(FONT_FAMILY, font_size, "bold"), 
                fill=color, anchor="nw"
            )
    
    def _draw_check_indicator(self, king_square: chess.Square):
        """Draw a check indicator around the king."""
        x1, y1, x2, y2 = self._square_to_coords(king_square)
        
        # Red glow effect
        self.canvas.create_rectangle(
            x1, y1, x2, y2,
            fill="#6b2222", outline="#f85149", width=2
        )
        
        # Redraw the king on top
        piece = self.board.piece_at(king_square)
        if piece:
            self._draw_piece(king_square, piece)
    
    def _draw_arrow(self, move: chess.Move):
        """Draw an arrow for a suggested move (legacy method)."""
        from_center = self._square_center(move.from_square)
        to_center = self._square_center(move.to_square)
        
        self.canvas.create_line(
            from_center[0], from_center[1],
            to_center[0], to_center[1],
            fill=ACCENT_PRIMARY, width=4, arrow=tk.LAST,
            arrowshape=(12, 15, 5)
        )
    
    def _draw_annotation_arrow(self, arrow: Arrow):
        """Draw an annotation arrow with proper styling."""
        from_center = self._square_center(arrow.from_square)
        to_center = self._square_center(arrow.to_square)
        
        # Calculate arrow geometry
        dx = to_center[0] - from_center[0]
        dy = to_center[1] - from_center[1]
        length = math.sqrt(dx * dx + dy * dy)
        
        if length < 1:
            return
        
        # Normalize direction
        dx /= length
        dy /= length
        
        # Shorten arrow slightly to not overlap with pieces
        offset = self.square_size * 0.25
        start_x = from_center[0] + dx * offset
        start_y = from_center[1] + dy * offset
        end_x = to_center[0] - dx * offset
        end_y = to_center[1] - dy * offset
        
        # Arrow head size based on type
        width = arrow.width
        head_length = 12 + width
        head_width = 15 + width
        
        # Draw arrow line
        self.canvas.create_line(
            start_x, start_y,
            end_x, end_y,
            fill=arrow.color,
            width=width,
            arrow=tk.LAST,
            arrowshape=(head_length, head_width, width + 2),
            capstyle=tk.ROUND
        )
    
    def _draw_highlight(self, highlight: SquareHighlight):
        """Draw a square highlight."""
        x1, y1, x2, y2 = self._square_to_coords(highlight.square)
        
        # Draw semi-transparent overlay
        # Note: Tkinter doesn't support true alpha, so we use stipple
        self.canvas.create_rectangle(
            x1, y1, x2, y2,
            fill=highlight.color,
            outline=highlight.color,
            width=2,
            stipple="gray50"  # 50% transparency approximation
        )
    
    # ─────────────────────────────────────────────────────────────────────────
    #                          EVENT HANDLERS
    # ─────────────────────────────────────────────────────────────────────────
    
    def _on_click(self, event):
        """Handle click on the board."""
        square = self._coords_to_square(event.x, event.y)
        
        if self.on_square_click:
            self.on_square_click(chess.square_name(square))
        
        piece = self.board.piece_at(square)
        
        if self.selected_square is not None:
            # Clicking the same square - deselect
            if square == self.selected_square:
                self._clear_selection()
                return
            
            # Try to make a move
            move = chess.Move(self.selected_square, square)
            
            # Check for promotion
            if self._is_promotion(move):
                move = chess.Move(self.selected_square, square, promotion=chess.QUEEN)
            
            if move in self.board.legal_moves:
                self.make_move(move)
            else:
                # If clicking own piece, select that piece instead
                if piece and piece.color == self.board.turn:
                    self._select_square(square)
                else:
                    self._clear_selection()
        
        elif piece and piece.color == self.board.turn:
            self._select_square(square)
    
    def _on_drag(self, event):
        """Handle dragging a piece."""
        if not self.drag_piece or not self.drag_start_square:
            return
        
        # Start dragging only when mouse actually moves
        if not self.dragging:
            self.dragging = True
            self._draw_board()  # Redraw to hide source piece
        
        # Only update the dragged piece position, don't redraw entire board
        # Delete just the dragged piece tag and redraw it at new position
        self.canvas.delete("drag_piece")
        
        # Draw piece at mouse position
        piece_char = PIECE_SYMBOLS[self.drag_piece.symbol()]
        font_size = int(self.square_size * 0.7)
        
        self.canvas.create_text(
            event.x, event.y,
            text=piece_char,
            font=(FONT_FAMILY, font_size),
            fill="#ffffff" if self.drag_piece.color == chess.WHITE else "#222222",
            tags="drag_piece"
        )
    
    def _on_release(self, event):
        """Handle releasing a dragged piece."""
        if not self.dragging:
            return
        
        # Clean up dragged piece visual
        self.canvas.delete("drag_piece")
        
        target_square = self._coords_to_square(event.x, event.y)
        
        if self.drag_start_square and target_square != self.drag_start_square:
            move = chess.Move(self.drag_start_square, target_square)
            
            if self._is_promotion(move):
                move = chess.Move(self.drag_start_square, target_square, promotion=chess.QUEEN)
            
            if move in self.board.legal_moves:
                self.make_move(move)
            else:
                self._draw_board()
        else:
            self._draw_board()
        
        self.dragging = False
        self.drag_piece = None
        self.drag_start_square = None
    
    def _select_square(self, square: chess.Square):
        """Select a square and show legal moves."""
        self.selected_square = square
        self.legal_move_squares = [
            m.to_square for m in self.board.legal_moves 
            if m.from_square == square
        ]
        # Setup drag state for this piece
        piece = self.board.piece_at(square)
        if piece:
            self.drag_piece = piece
            self.drag_start_square = square
        self._draw_board()
    
    def _clear_selection(self):
        """Clear the current selection."""
        self.selected_square = None
        self.legal_move_squares = []
        self._draw_board()
    
    def _is_promotion(self, move: chess.Move) -> bool:
        """Check if a move is a pawn promotion."""
        piece = self.board.piece_at(move.from_square)
        if piece and piece.piece_type == chess.PAWN:
            to_rank = chess.square_rank(move.to_square)
            if (piece.color == chess.WHITE and to_rank == 7) or \
               (piece.color == chess.BLACK and to_rank == 0):
                return True
        return False
