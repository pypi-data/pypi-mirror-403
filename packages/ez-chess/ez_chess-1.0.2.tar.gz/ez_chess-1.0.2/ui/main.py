"""
EZ Chess GUI - Main Application Window

A stunning dark-mode GUI for the Explainable Chess Engine.
Designed to impress with its modern aesthetics and smooth functionality.

Usage:
    python -m ui.main
    
    Or from code:
        from ui.main import launch_gui
        launch_gui()
"""

import tkinter as tk
from tkinter import ttk, messagebox
import sys
import os
import chess
from typing import Optional

# Add parent directory for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ui.theme import (
    BG_DARKEST, BG_DARK, BG_MEDIUM, BG_LIGHT, BG_LIGHTER,
    TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED,
    ACCENT_PRIMARY, ACCENT_SUCCESS, ACCENT_WARNING, ACCENT_DANGER,
    FONT_FAMILY, FONT_SIZE_SM, FONT_SIZE_MD, FONT_SIZE_LG,
    PADDING_SM, PADDING_MD, PADDING_LG,
    PANEL_LEFT_WIDTH, PANEL_RIGHT_WIDTH, BOARD_SIZE
)
from ui.board import ChessBoardWidget
from ui.game_panel import GamePanel
from ui.analysis_panel import AnalysisPanel
from ui.chat_panel import ChatPanel


class ChessGUI:
    """
    Main application window for EZ Chess.
    
    A beautiful dark-mode interface with:
    - Interactive chess board with drag & drop
    - PGN loading and game navigation
    - Engine analysis with visual eval bar
    - AI-powered Q&A chat
    
    Layout:
    ┌─────────────────────────────────────────────────────────────────┐
    │                         Title Bar                                │
    ├──────────────┬──────────────────────────┬───────────────────────┤
    │              │                          │                       │
    │  Game Panel  │                          │   Analysis Panel      │
    │  ─────────   │                          │   ──────────────      │
    │  • PGN Input │      Chess Board         │   • Evaluation        │
    │  • Game Info │                          │   • Top Moves         │
    │  • Move List │                          │   • Best Line         │
    │  • Navigation│                          │                       │
    │              │                          │                       │
    │              ├──────────────────────────┴───────────────────────┤
    │              │                  Chat Panel                       │
    │              │           (AI Q&A about positions)                │
    └──────────────┴──────────────────────────────────────────────────┘
    """
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("EZ-Chess")
        self.root.geometry("1500x900")
        self.root.minsize(1200, 700)
        self.root.configure(bg=BG_DARKEST)
        
        # Configure dark title bar (Windows 10+)
        try:
            self.root.update()
            from ctypes import windll, byref, sizeof, c_int
            HWND = windll.user32.GetParent(self.root.winfo_id())
            DWMWA_USE_IMMERSIVE_DARK_MODE = 20
            windll.dwmapi.DwmSetWindowAttribute(
                HWND, DWMWA_USE_IMMERSIVE_DARK_MODE,
                byref(c_int(1)), sizeof(c_int)
            )
        except:
            pass  # Not on Windows or older version
        
        # Set window icon
        try:
            pass  # Add icon later if desired
        except:
            pass
        
        # Create the UI
        self._create_menu()
        self._create_layout()
        self._connect_callbacks()
        
        # Handle window close
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        
        # Bind keyboard shortcuts
        self._bind_shortcuts()
    
    def _create_menu(self):
        """Create the menu bar."""
        # Configure menu colors
        menubar = tk.Menu(
            self.root,
            bg=BG_DARK,
            fg=TEXT_PRIMARY,
            activebackground=ACCENT_PRIMARY,
            activeforeground=TEXT_PRIMARY,
            relief="flat"
        )
        self.root.config(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(
            menubar,
            tearoff=0,
            bg=BG_DARK,
            fg=TEXT_PRIMARY,
            activebackground=ACCENT_PRIMARY,
            activeforeground=TEXT_PRIMARY
        )
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="New Position", command=self._new_position, accelerator="Ctrl+N")
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self._on_close, accelerator="Alt+F4")
        
        # View menu
        view_menu = tk.Menu(
            menubar,
            tearoff=0,
            bg=BG_DARK,
            fg=TEXT_PRIMARY,
            activebackground=ACCENT_PRIMARY,
            activeforeground=TEXT_PRIMARY
        )
        menubar.add_cascade(label="View", menu=view_menu)
        view_menu.add_command(label="Flip Board", command=self._flip_board, accelerator="F")
        view_menu.add_command(label="Reset Board", command=self._reset_board, accelerator="R")
        
        # Help menu
        help_menu = tk.Menu(
            menubar,
            tearoff=0,
            bg=BG_DARK,
            fg=TEXT_PRIMARY,
            activebackground=ACCENT_PRIMARY,
            activeforeground=TEXT_PRIMARY
        )
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="How to Use", command=self._show_help)
        help_menu.add_command(label="Keyboard Shortcuts", command=self._show_shortcuts)
        help_menu.add_separator()
        help_menu.add_command(label="About EZ Chess", command=self._show_about)
    
    def _create_layout(self):
        """Create the main layout."""
        # Main container
        main_frame = tk.Frame(self.root, bg=BG_DARKEST)
        main_frame.pack(fill="both", expand=True, padx=PADDING_SM, pady=PADDING_SM)
        
        # ─────────────────────────────────────────────────────────────────────
        #                          LEFT PANEL - Game Controls
        # ─────────────────────────────────────────────────────────────────────
        left_frame = tk.Frame(main_frame, bg=BG_DARKEST, width=PANEL_LEFT_WIDTH)
        left_frame.pack(side="left", fill="y", padx=(0, PADDING_SM))
        left_frame.pack_propagate(False)
        
        self.game_panel = GamePanel(
            left_frame,
            on_position_change=self._on_position_change,
            on_mode_change=self._on_mode_change
        )
        self.game_panel.pack(fill="both", expand=True)
        
        # ─────────────────────────────────────────────────────────────────────
        #                          CENTER - Board + Analysis
        # ─────────────────────────────────────────────────────────────────────
        center_frame = tk.Frame(main_frame, bg=BG_DARKEST)
        center_frame.pack(side="left", fill="both", expand=True, padx=PADDING_SM)
        
        # Board container (centered)
        board_outer = tk.Frame(center_frame, bg=BG_DARKEST)
        board_outer.pack(fill="x", pady=PADDING_MD)
        
        # Board with shadow effect
        board_shadow = tk.Frame(board_outer, bg="#000000", padx=6, pady=6)
        board_shadow.pack()
        
        self.board_widget = ChessBoardWidget(
            board_shadow,
            size=BOARD_SIZE,
            on_move=self._on_board_move,
            on_square_click=self._on_square_click,
            interactive=True
        )
        self.board_widget.pack()
        
        # Turn indicator
        self.turn_frame = tk.Frame(center_frame, bg=BG_DARKEST)
        self.turn_frame.pack(fill="x", pady=PADDING_SM)
        
        self.turn_label = tk.Label(
            self.turn_frame,
            text="● White to move",
            font=(FONT_FAMILY, FONT_SIZE_MD),
            bg=BG_DARKEST,
            fg=TEXT_PRIMARY
        )
        self.turn_label.pack()
        
        # Analysis panel (below board) - compact horizontal layout
        analysis_outer = tk.Frame(center_frame, bg=BG_DARK, height=280)
        analysis_outer.pack(fill="x", pady=(PADDING_MD, PADDING_MD))
        analysis_outer.pack_propagate(False)  # Maintain minimum height for button
        
        self.analysis_panel = AnalysisPanel(
            analysis_outer,
            on_analysis_complete=self._on_analysis_complete
        )
        self.analysis_panel.pack(fill="both", expand=True)
        
        # ─────────────────────────────────────────────────────────────────────
        #                          RIGHT PANEL - Chat
        # ─────────────────────────────────────────────────────────────────────
        right_frame = tk.Frame(main_frame, bg=BG_DARKEST, width=PANEL_RIGHT_WIDTH)
        right_frame.pack(side="right", fill="both", padx=(PADDING_SM, 0))
        right_frame.pack_propagate(False)
        
        self.chat_panel = ChatPanel(right_frame)
        self.chat_panel.pack(fill="both", expand=True)
        
        # ─────────────────────────────────────────────────────────────────────
        #                          STATUS BAR
        # ─────────────────────────────────────────────────────────────────────
        self.status_bar = tk.Frame(self.root, bg=BG_DARK, height=30)
        self.status_bar.pack(fill="x", side="bottom")
        self.status_bar.pack_propagate(False)
        
        self.status_label = tk.Label(
            self.status_bar,
            text="Welcome to EZ Chess! Paste a PGN to start analyzing.",
            font=(FONT_FAMILY, FONT_SIZE_SM),
            bg=BG_DARK,
            fg=TEXT_SECONDARY,
            anchor="w",
            padx=PADDING_MD
        )
        self.status_label.pack(fill="both", expand=True)
        
        # Version info on right
        tk.Label(
            self.status_bar,
            text="EZ Chess v1.0",
            font=(FONT_FAMILY, FONT_SIZE_SM),
            bg=BG_DARK,
            fg=TEXT_MUTED,
            padx=PADDING_MD
        ).pack(side="right")
    
    def _connect_callbacks(self):
        """Connect panel callbacks."""
        self.game_panel.set_flip_callback(self._flip_board)
    
    def _on_analysis_complete(self, analysis_result: dict):
        """Handle analysis completion - show arrows on board."""
        if not analysis_result:
            return
        
        # Show best move arrow on board
        self.board_widget.set_annotations_from_analysis(analysis_result)
    
    def _bind_shortcuts(self):
        """Bind keyboard shortcuts."""
        # Only bind Ctrl+N - removed f/F/r/R as they conflict with typing in textbox
        self.root.bind("<Control-n>", lambda e: self._new_position())
    
    # ─────────────────────────────────────────────────────────────────────────
    #                            EVENT HANDLERS
    # ─────────────────────────────────────────────────────────────────────────
    
    def _on_position_change(self, fen: str, move_number: int, last_move: Optional[chess.Move]):
        """Handle position change from game panel."""
        # Clear analysis arrows when navigating positions
        self.board_widget.clear_arrows()
        
        # Update board
        self.board_widget.set_position(fen, last_move)
        
        # Update analysis panel
        self.analysis_panel.set_position(fen)
        
        # Update chat panel with current position
        self.chat_panel.set_position(fen, move_number)
        
        # Update turn indicator
        board = chess.Board(fen)
        turn_text = "● White to move" if board.turn == chess.WHITE else "● Black to move"
        self.turn_label.config(text=turn_text)
        
        # Update status
        if move_number == 0:
            self.status_label.config(text="Starting position")
        else:
            self.status_label.config(text=f"Move {move_number} • {'White' if board.turn else 'Black'} to move")
    
    def _on_mode_change(self, mode: str):
        """Handle mode change (game line vs exploration)."""
        if mode == "exploration":
            self.status_label.config(text="Exploration mode - making custom moves", fg=ACCENT_WARNING)
        else:
            self.status_label.config(text="Following game line", fg=TEXT_SECONDARY)
    
    def _on_board_move(self, move: chess.Move):
        """Handle a move made on the board."""
        # Clear analysis arrows when a move is played
        self.board_widget.clear_arrows()
        
        # Notify game panel
        self.game_panel.handle_custom_move(move)
        
        # Update analysis and chat with new position
        fen = self.board_widget.get_fen()
        self.analysis_panel.set_position(fen)
        self.chat_panel.set_position(fen, self.game_panel.current_move_index)
        
        # Update turn indicator
        board = self.board_widget.get_board()
        turn_text = "● White to move" if board.turn == chess.WHITE else "● Black to move"
        self.turn_label.config(text=turn_text)
        
        # Update status with move notation (move is already made, use uci)
        if move:
            self.status_label.config(text=f"Played: {move.uci()}")
        else:
            self.status_label.config(text="")
    
    def _on_square_click(self, square_name: str):
        """Handle square click on the board."""
        pass  # Board handles this internally now
    
    def _flip_board(self):
        """Flip the board orientation."""
        self.board_widget.flip()
    
    def _reset_board(self):
        """Reset the board to starting position."""
        self.board_widget.reset()
        self.status_label.config(text="Board reset to starting position")
    
    def _new_position(self):
        """Reset for a new position."""
        self.board_widget.reset()
        self.status_label.config(text="Ready for new game - paste PGN to analyze")
    
    def _show_help(self):
        """Show help dialog."""
        help_text = """
╔══════════════════════════════════════════════════════════════════╗
║                    EZ CHESS - HOW TO USE                         ║
╠══════════════════════════════════════════════════════════════════╣
║                                                                  ║
║  1. LOAD A GAME                                                  ║
║     • Paste PGN into the left panel                              ║
║     • Click "Load Game" to parse and display the game            ║
║                                                                  ║
║  2. NAVIGATE MOVES                                               ║
║     • Use arrow buttons: ← Previous  → Next                      ║
║     • Keyboard shortcuts: ← → Home End                           ║
║     • Click any move in the move list to jump to it              ║
║                                                                  ║
║  3. ANALYZE POSITION (Stockfish Engine)                          ║
║     • Click "Analyze Position" on the right panel                ║
║     • View evaluation bar, best moves, and principal variation   ║
║     • See what Stockfish recommends and why                      ║
║                                                                  ║
║  4. ASK AI QUESTIONS (LLM-Powered Chat)                          ║
║     • Type questions in the chat box below the board             ║
║     • Examples:                                                  ║
║       - "What's the best move?"                                  ║
║       - "Why is this move bad?"                                  ║
║       - "What's the plan in this position?"                      ║
║       - "Explain this tactical pattern"                          ║
║     • AI uses Stockfish + chess knowledge to explain             ║
║     • Response time: 3-8 seconds (with GPU) / 5-15s (CPU)        ║
║                                                                  ║
║  5. MAKE CUSTOM MOVES (Exploration Mode)                         ║
║     • Click and drag pieces on the board                         ║
║     • Automatically enters "exploration" mode                    ║
║     • Can deviate from game line to test variations              ║
║                                                                  ║
║  AI MODEL SELECTION:                                             ║
║  • Auto-selects optimal model based on your GPU                  ║
║  • RTX 3060/4050 (6GB): qwen2.5:7b - fast, high quality          ║
║  • Integrated graphics: qwen2.5:3b - lightweight                 ║
║  • RTX 3080+ (12GB): qwen2.5:14b - maximum quality               ║
║  • All models run 100% locally via Ollama                        ║
║                                                                  ║
║  REQUIREMENTS:                                                   ║
║  • Ollama must be running (download from ollama.ai)              ║
║  • Model will auto-download on first use                         ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
"""
        messagebox.showinfo("How to Use", help_text)
    
    def _show_shortcuts(self):
        """Show keyboard shortcuts."""
        shortcuts = """
Keyboard Shortcuts:
─────────────────────
← / →      Previous/Next move
Home       Go to start
End        Go to last move
F          Flip board
R          Reset board
Ctrl+N     New position
"""
        messagebox.showinfo("Keyboard Shortcuts", shortcuts)
    
    def _show_about(self):
        """Show about dialog."""
        about_text = """
╔════════════════════════════════════════════════╗
║    EZ Chess — Explainable Chess Engine         ║
╠════════════════════════════════════════════════╣
║                                                ║
║  Stockfish tells you WHAT is best.             ║
║  EZ Chess tells you WHY.                       ║
║                                                ║
║  FEATURES:                                     ║
║  • Deep Stockfish engine analysis              ║
║  • AI-powered natural language explanations    ║
║  • 60+ chess fundamentals knowledge base       ║
║  • Beautiful dark mode UI                      ║
║  • PGN game support with navigation            ║
║  • Auto-optimized for your hardware            ║
║                                                ║
║  TECHNOLOGY STACK:                             ║
║  • Engine: Stockfish 16+                       ║
║  • AI Framework: LangGraph + LangChain         ║
║  • LLM Runtime: Ollama (100% local)            ║
║  • Models: Qwen2.5 (3b/7b/14b)                 ║
║  • GUI: Python + Tkinter                       ║
║  • Chess Library: python-chess                 ║
║                                                ║
║  PERFORMANCE:                                  ║
║  • GPU-accelerated responses in 3-8 seconds    ║
║  • Auto model selection based on VRAM          ║
║  • Complete privacy - all processing local     ║
║                                                ║
║  © 2026 EZ Chess Project                       ║
║  Built with ♟️ for chess learners everywhere   ║
║                                                ║
╚════════════════════════════════════════════════╝
"""
        messagebox.showinfo("About EZ Chess", about_text)
    
    def _on_close(self):
        """Handle window close."""
        # Clean up resources
        try:
            self.analysis_panel.cleanup()
        except:
            pass
        
        self.root.destroy()
    
    def run(self):
        """Run the application."""
        self.root.mainloop()


def launch_gui():
    """Launch the EZ Chess GUI."""
    app = ChessGUI()
    app.run()


if __name__ == "__main__":
    launch_gui()
