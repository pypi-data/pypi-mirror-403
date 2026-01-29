"""
Game Panel - PGN input, move list, and navigation controls.

A stunning dark-mode panel for loading games and navigating through moves.
"""

import tkinter as tk
from tkinter import ttk, scrolledtext
import chess
import chess.pgn
import io
from typing import Optional, Callable, List, Tuple

from ui.theme import (
    BG_DARKEST, BG_DARK, BG_MEDIUM, BG_LIGHT, BG_LIGHTER,
    TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED,
    ACCENT_PRIMARY, ACCENT_SUCCESS, ACCENT_WARNING,
    BTN_PRIMARY, BTN_PRIMARY_HOVER, BTN_SECONDARY, BTN_SECONDARY_HOVER,
    FONT_FAMILY, FONT_MONO, FONT_SIZE_SM, FONT_SIZE_MD, FONT_SIZE_LG,
    PADDING_SM, PADDING_MD, PADDING_LG,
    ICON_FIRST, ICON_PREV, ICON_NEXT, ICON_LAST, ICON_FLIP, ICON_PLAY
)


class GamePanel(tk.Frame):
    """
    Panel for loading PGN games and navigating through moves.
    """
    
    def __init__(
        self, 
        parent,
        on_position_change: Optional[Callable[[str, int, Optional[chess.Move]], None]] = None,
        on_mode_change: Optional[Callable[[str], None]] = None
    ):
        super().__init__(parent, bg=BG_DARKEST)
        
        self.on_position_change = on_position_change
        self.on_mode_change = on_mode_change
        self.flip_callback = None
        
        # Game state
        self.game: Optional[chess.pgn.Game] = None
        self.moves: List[chess.Move] = []
        self.current_move_index = 0
        self.board = chess.Board()
        self.move_positions: List[Tuple[str, str]] = []  # Store positions for click detection
        
        # Exploration mode state
        self.exploration_mode = False
        self.exploration_board: Optional[chess.Board] = None
        self.exploration_moves: List[chess.Move] = []
        
        self._create_widgets()
    
    def _create_widgets(self):
        """Create all widgets."""
        # Title
        title_frame = tk.Frame(self, bg=BG_DARKEST)
        title_frame.pack(fill="x", padx=PADDING_MD, pady=(PADDING_MD, PADDING_SM))
        
        tk.Label(
            title_frame,
            text="♟ Game",
            font=(FONT_FAMILY, FONT_SIZE_LG, "bold"),
            bg=BG_DARKEST,
            fg=TEXT_PRIMARY
        ).pack(side="left")
        
        # Mode indicator
        self.mode_label = tk.Label(
            title_frame,
            text="",
            font=(FONT_FAMILY, FONT_SIZE_SM),
            bg=BG_DARKEST,
            fg=ACCENT_WARNING
        )
        self.mode_label.pack(side="right")
        
        # PGN Input Section
        self._create_pgn_section()
        
        # Game Info Section
        self._create_info_section()
        
        # Move List Section
        self._create_moves_section()
        
        # Navigation Controls
        self._create_navigation()
    
    def _create_pgn_section(self):
        """Create the PGN input section."""
        section = tk.Frame(self, bg=BG_DARK, padx=PADDING_MD, pady=PADDING_MD)
        section.pack(fill="x", padx=PADDING_MD, pady=PADDING_SM)
        
        # Header with collapse button
        header = tk.Frame(section, bg=BG_DARK)
        header.pack(fill="x")
        
        tk.Label(
            header,
            text="📋 Paste PGN",
            font=(FONT_FAMILY, FONT_SIZE_MD, "bold"),
            bg=BG_DARK,
            fg=TEXT_PRIMARY
        ).pack(side="left")
        
        # PGN Text Area
        text_frame = tk.Frame(section, bg=BG_LIGHT, padx=2, pady=2)
        text_frame.pack(fill="x", pady=(PADDING_SM, 0))
        
        self.pgn_text = tk.Text(
            text_frame,
            height=6,
            font=(FONT_MONO, FONT_SIZE_SM),
            bg=BG_MEDIUM,
            fg=TEXT_PRIMARY,
            insertbackground=TEXT_PRIMARY,
            selectbackground=ACCENT_PRIMARY,
            selectforeground=TEXT_PRIMARY,
            relief="flat",
            wrap="word",
            padx=PADDING_SM,
            pady=PADDING_SM
        )
        self.pgn_text.pack(fill="x")
        
        # Placeholder text
        self.pgn_text.insert("1.0", "Paste your PGN here...")
        self.pgn_text.config(fg=TEXT_MUTED)
        self.pgn_text.bind("<FocusIn>", self._on_pgn_focus_in)
        self.pgn_text.bind("<FocusOut>", self._on_pgn_focus_out)
        
        # Buttons
        btn_frame = tk.Frame(section, bg=BG_DARK)
        btn_frame.pack(fill="x", pady=(PADDING_SM, 0))
        
        self.load_btn = tk.Button(
            btn_frame,
            text="Load Game",
            font=(FONT_FAMILY, FONT_SIZE_SM, "bold"),
            bg=BTN_PRIMARY,
            fg=TEXT_PRIMARY,
            activebackground=BTN_PRIMARY_HOVER,
            activeforeground=TEXT_PRIMARY,
            relief="flat",
            cursor="hand2",
            padx=PADDING_MD,
            pady=PADDING_SM,
            command=self._load_pgn
        )
        self.load_btn.pack(side="left", expand=True, fill="x", padx=(0, PADDING_SM))
        
        self.clear_btn = tk.Button(
            btn_frame,
            text="Clear",
            font=(FONT_FAMILY, FONT_SIZE_SM),
            bg=BTN_SECONDARY,
            fg=TEXT_SECONDARY,
            activebackground=BTN_SECONDARY_HOVER,
            activeforeground=TEXT_PRIMARY,
            relief="flat",
            cursor="hand2",
            padx=PADDING_MD,
            pady=PADDING_SM,
            command=self._clear_pgn
        )
        self.clear_btn.pack(side="right")
    
    def _create_info_section(self):
        """Create the game info section."""
        self.info_frame = tk.Frame(self, bg=BG_DARK, padx=PADDING_MD, pady=PADDING_MD)
        self.info_frame.pack(fill="x", padx=PADDING_MD, pady=PADDING_SM)
        
        # Players
        self.white_label = tk.Label(
            self.info_frame,
            text="⬜ White: -",
            font=(FONT_FAMILY, FONT_SIZE_SM),
            bg=BG_DARK,
            fg=TEXT_PRIMARY,
            anchor="w"
        )
        self.white_label.pack(fill="x")
        
        self.black_label = tk.Label(
            self.info_frame,
            text="⬛ Black: -",
            font=(FONT_FAMILY, FONT_SIZE_SM),
            bg=BG_DARK,
            fg=TEXT_PRIMARY,
            anchor="w"
        )
        self.black_label.pack(fill="x")
        
        # Result and opening
        self.result_label = tk.Label(
            self.info_frame,
            text="Result: -",
            font=(FONT_FAMILY, FONT_SIZE_SM),
            bg=BG_DARK,
            fg=TEXT_SECONDARY,
            anchor="w"
        )
        self.result_label.pack(fill="x", pady=(PADDING_SM, 0))
        
        self.opening_label = tk.Label(
            self.info_frame,
            text="",
            font=(FONT_FAMILY, FONT_SIZE_SM),
            bg=BG_DARK,
            fg=ACCENT_PRIMARY,
            anchor="w",
            wraplength=300
        )
        self.opening_label.pack(fill="x")
    
    def _create_moves_section(self):
        """Create the move list section."""
        section = tk.Frame(self, bg=BG_DARKEST)
        section.pack(fill="both", expand=True, padx=PADDING_MD, pady=PADDING_SM)
        
        tk.Label(
            section,
            text="Moves",
            font=(FONT_FAMILY, FONT_SIZE_MD, "bold"),
            bg=BG_DARKEST,
            fg=TEXT_PRIMARY
        ).pack(anchor="w", pady=(0, PADDING_SM))
        
        # Move list with custom styling - limited height
        list_frame = tk.Frame(section, bg=BG_LIGHT, padx=2, pady=2, height=120)
        list_frame.pack(fill="x")
        list_frame.pack_propagate(False)  # Keep fixed height
        
        # Create text widget for moves
        self.moves_text = tk.Text(
            list_frame,
            font=(FONT_MONO, FONT_SIZE_SM),
            bg=BG_MEDIUM,
            fg=TEXT_PRIMARY,
            relief="flat",
            wrap="word",
            padx=PADDING_SM,
            pady=PADDING_SM,
            cursor="hand2",
            state="disabled",
            height=6
        )
        self.moves_text.pack(side="left", fill="both", expand=True)
        
        # Scrollbar
        scrollbar = tk.Scrollbar(
            list_frame,
            orient="vertical",
            command=self.moves_text.yview
        )
        scrollbar.pack(side="right", fill="y")
        self.moves_text.config(yscrollcommand=scrollbar.set)
        
        # Configure tags for highlighting
        self.moves_text.tag_configure("current", background=ACCENT_PRIMARY, foreground=TEXT_PRIMARY)
        self.moves_text.tag_configure("move", foreground=TEXT_PRIMARY)
        self.moves_text.tag_configure("number", foreground=TEXT_MUTED)
        
        # Bind click events
        self.moves_text.bind("<Button-1>", self._on_move_click)
    
    def _create_navigation(self):
        """Create navigation controls."""
        nav_frame = tk.Frame(self, bg=BG_DARK, padx=PADDING_MD, pady=PADDING_MD)
        nav_frame.pack(fill="x", padx=PADDING_MD, pady=PADDING_SM)
        
        # Navigation buttons
        btn_container = tk.Frame(nav_frame, bg=BG_DARK)
        btn_container.pack(fill="x")
        
        buttons = [
            ("⏮", self._go_first, "First move"),
            ("◀", self._go_prev, "Previous"),
            ("▶", self._go_next, "Next"),
            ("⏭", self._go_last, "Last move"),
        ]
        
        for text, command, tooltip in buttons:
            btn = tk.Button(
                btn_container,
                text=text,
                font=(FONT_FAMILY, FONT_SIZE_LG),
                bg=BTN_SECONDARY,
                fg=TEXT_PRIMARY,
                activebackground=BTN_SECONDARY_HOVER,
                activeforeground=TEXT_PRIMARY,
                relief="flat",
                cursor="hand2",
                width=4,
                command=command
            )
            btn.pack(side="left", expand=True, fill="x", padx=2)
        
        # Second row: Flip and Reset
        btn_row2 = tk.Frame(nav_frame, bg=BG_DARK)
        btn_row2.pack(fill="x", pady=(PADDING_SM, 0))
        
        self.flip_btn = tk.Button(
            btn_row2,
            text="🔄 Flip Board",
            font=(FONT_FAMILY, FONT_SIZE_SM),
            bg=BTN_SECONDARY,
            fg=TEXT_SECONDARY,
            activebackground=BTN_SECONDARY_HOVER,
            activeforeground=TEXT_PRIMARY,
            relief="flat",
            cursor="hand2",
            command=self._flip_board
        )
        self.flip_btn.pack(side="left", expand=True, fill="x", padx=(0, 2))
        
        self.reset_btn = tk.Button(
            btn_row2,
            text="↩ Reset",
            font=(FONT_FAMILY, FONT_SIZE_SM),
            bg=BTN_SECONDARY,
            fg=TEXT_SECONDARY,
            activebackground=BTN_SECONDARY_HOVER,
            activeforeground=TEXT_PRIMARY,
            relief="flat",
            cursor="hand2",
            command=self._reset_to_game
        )
        self.reset_btn.pack(side="right", expand=True, fill="x", padx=(2, 0))
        
        # Move counter
        self.move_counter = tk.Label(
            nav_frame,
            text="Move: 0 / 0",
            font=(FONT_FAMILY, FONT_SIZE_SM),
            bg=BG_DARK,
            fg=TEXT_SECONDARY
        )
        self.move_counter.pack(pady=(PADDING_SM, 0))
        
        # Keyboard bindings
        self.bind_all("<Left>", lambda e: self._go_prev())
        self.bind_all("<Right>", lambda e: self._go_next())
        self.bind_all("<Home>", lambda e: self._go_first())
        self.bind_all("<End>", lambda e: self._go_last())
    
    # ─────────────────────────────────────────────────────────────────────────
    #                            EVENT HANDLERS
    # ─────────────────────────────────────────────────────────────────────────
    
    def _on_pgn_focus_in(self, event):
        """Handle PGN text focus in."""
        if self.pgn_text.get("1.0", "end-1c") == "Paste your PGN here...":
            self.pgn_text.delete("1.0", "end")
            self.pgn_text.config(fg=TEXT_PRIMARY)
    
    def _on_pgn_focus_out(self, event):
        """Handle PGN text focus out."""
        if not self.pgn_text.get("1.0", "end-1c").strip():
            self.pgn_text.insert("1.0", "Paste your PGN here...")
            self.pgn_text.config(fg=TEXT_MUTED)
    
    def _on_move_click(self, event):
        """Handle click on move list."""
        # Get click position
        index = self.moves_text.index(f"@{event.x},{event.y}")
        
        # Find which move was clicked
        for i, (start, end) in enumerate(self.move_positions):
            if self.moves_text.compare(start, "<=", index) and \
               self.moves_text.compare(index, "<", end):
                self._go_to_move(i + 1)
                break
    
    def _load_pgn(self):
        """Load PGN from text area."""
        pgn_text = self.pgn_text.get("1.0", "end-1c").strip()
        
        if not pgn_text or pgn_text == "Paste your PGN here...":
            return
        
        try:
            pgn_io = io.StringIO(pgn_text)
            self.game = chess.pgn.read_game(pgn_io)
            
            if self.game is None:
                raise ValueError("Could not parse PGN")
            
            # Extract moves
            self.moves = list(self.game.mainline_moves())
            self.current_move_index = 0
            self.board = chess.Board()
            
            # Update UI
            self._update_game_info()
            self._update_moves_list()
            self._update_position()
            
            # Exit exploration mode
            self.exploration_mode = False
            self.mode_label.config(text="")
            
        except Exception as e:
            self._show_error(f"Error loading PGN: {e}")
    
    def _clear_pgn(self):
        """Clear the PGN text area."""
        self.pgn_text.delete("1.0", "end")
        self.pgn_text.insert("1.0", "Paste your PGN here...")
        self.pgn_text.config(fg=TEXT_MUTED)
    
    def _update_game_info(self):
        """Update game information display."""
        if not self.game:
            return
        
        headers = self.game.headers
        
        white = headers.get("White", "Unknown")
        white_elo = headers.get("WhiteElo", "?")
        self.white_label.config(text=f"⬜ {white} ({white_elo})")
        
        black = headers.get("Black", "Unknown")
        black_elo = headers.get("BlackElo", "?")
        self.black_label.config(text=f"⬛ {black} ({black_elo})")
        
        result = headers.get("Result", "*")
        self.result_label.config(text=f"Result: {result}")
        
        opening = headers.get("Opening", "")
        eco = headers.get("ECO", "")
        if opening:
            self.opening_label.config(text=f"📖 {eco} {opening}" if eco else f"📖 {opening}")
        else:
            self.opening_label.config(text="")
    
    def _update_moves_list(self):
        """Update the moves list display."""
        self.moves_text.config(state="normal")
        self.moves_text.delete("1.0", "end")
        
        self.move_positions = []  # Store positions for click detection
        
        board = chess.Board()
        move_num = 1
        
        for i, move in enumerate(self.moves):
            # Add move number for white moves
            if board.turn == chess.WHITE:
                num_start = self.moves_text.index("end-1c")
                self.moves_text.insert("end", f"{move_num}. ", "number")
            
            # Add the move
            start = self.moves_text.index("end-1c")
            san = board.san(move)
            self.moves_text.insert("end", san, "move")
            end = self.moves_text.index("end-1c")
            self.move_positions.append((start, end))
            
            self.moves_text.insert("end", " ")
            
            if board.turn == chess.BLACK:
                move_num += 1
            
            board.push(move)
        
        self.moves_text.config(state="disabled")
        self._highlight_current_move()
    
    def _highlight_current_move(self):
        """Highlight the current move in the list."""
        self.moves_text.tag_remove("current", "1.0", "end")
        
        if 0 < self.current_move_index <= len(self.move_positions):
            start, end = self.move_positions[self.current_move_index - 1]
            self.moves_text.tag_add("current", start, end)
            self.moves_text.see(start)
    
    def _update_position(self):
        """Update the board position and notify callback."""
        total = len(self.moves)
        self.move_counter.config(text=f"Move: {self.current_move_index} / {total}")
        
        # Get last move for highlighting
        last_move = None
        if self.current_move_index > 0:
            last_move = self.moves[self.current_move_index - 1]
        
        if self.on_position_change:
            self.on_position_change(
                self.board.fen(),
                self.current_move_index,
                last_move
            )
        
        self._highlight_current_move()
    
    # ─────────────────────────────────────────────────────────────────────────
    #                            NAVIGATION
    # ─────────────────────────────────────────────────────────────────────────
    
    def _go_first(self):
        """Go to the first position."""
        self.board = chess.Board()
        self.current_move_index = 0
        self._update_position()
    
    def _go_prev(self):
        """Go to the previous move."""
        if self.current_move_index > 0:
            self.board.pop()
            self.current_move_index -= 1
            self._update_position()
    
    def _go_next(self):
        """Go to the next move."""
        if self.current_move_index < len(self.moves):
            self.board.push(self.moves[self.current_move_index])
            self.current_move_index += 1
            self._update_position()
    
    def _go_last(self):
        """Go to the last position."""
        while self.current_move_index < len(self.moves):
            self.board.push(self.moves[self.current_move_index])
            self.current_move_index += 1
        self._update_position()
    
    def _go_to_move(self, move_index: int):
        """Go to a specific move."""
        # Reset board
        self.board = chess.Board()
        self.current_move_index = 0
        
        # Play moves up to target
        target = min(move_index, len(self.moves))
        for i in range(target):
            self.board.push(self.moves[i])
            self.current_move_index += 1
        
        self._update_position()
    
    def _flip_board(self):
        """Flip the board."""
        if self.flip_callback:
            self.flip_callback()
    
    def _reset_to_game(self):
        """Reset to game line from exploration mode."""
        if self.exploration_mode:
            self.exploration_mode = False
            self.mode_label.config(text="")
            self._update_position()
    
    # ─────────────────────────────────────────────────────────────────────────
    #                           EXPLORATION MODE
    # ─────────────────────────────────────────────────────────────────────────
    
    def enter_exploration(self, board: chess.Board):
        """Enter exploration mode with a custom position."""
        self.exploration_mode = True
        self.exploration_board = board.copy()
        self.mode_label.config(text="🔍 Exploring")
        
        if self.on_mode_change:
            self.on_mode_change("exploration")
    
    def handle_custom_move(self, move: chess.Move):
        """Handle a move made on the board (exploration mode)."""
        if not self.exploration_mode:
            # Check if move matches the game line
            if self.current_move_index < len(self.moves):
                expected = self.moves[self.current_move_index]
                if move == expected:
                    self._go_next()
                    return
            
            # Enter exploration mode
            self.enter_exploration(self.board)
        
        # Update exploration board
        if self.exploration_board and move in self.exploration_board.legal_moves:
            self.exploration_board.push(move)
    
    # ─────────────────────────────────────────────────────────────────────────
    #                              UTILITIES
    # ─────────────────────────────────────────────────────────────────────────
    
    def set_flip_callback(self, callback):
        """Set the flip board callback."""
        self.flip_callback = callback
    
    def get_current_fen(self) -> str:
        """Get the current FEN."""
        if self.exploration_mode and self.exploration_board:
            return self.exploration_board.fen()
        return self.board.fen()
    
    def get_current_move_number(self) -> int:
        """Get the current move number."""
        return self.current_move_index
    
    def _show_error(self, message: str):
        """Show an error message."""
        from tkinter import messagebox
        messagebox.showerror("Error", message)
