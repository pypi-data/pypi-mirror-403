"""
Analysis Panel - Engine evaluation and best moves display.

A beautiful dark-mode panel showing Stockfish analysis.
"""

import tkinter as tk
from tkinter import ttk
import threading
import chess
from typing import Optional, List, Dict, Tuple, Callable

from ui.theme import (
    BG_DARKEST, BG_DARK, BG_MEDIUM, BG_LIGHT, BG_LIGHTER,
    TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED, TEXT_WHITE,
    ACCENT_PRIMARY, ACCENT_SUCCESS, ACCENT_WARNING, ACCENT_DANGER, ACCENT_PURPLE,
    EVAL_WHITE, EVAL_BLACK,
    BTN_PRIMARY, BTN_PRIMARY_HOVER, BTN_SECONDARY, BTN_SECONDARY_HOVER,
    FONT_FAMILY, FONT_MONO, FONT_SIZE_SM, FONT_SIZE_MD, FONT_SIZE_LG, FONT_SIZE_XL,
    PADDING_SM, PADDING_MD, PADDING_LG,
    ICON_ANALYZE
)


class EvalBar(tk.Canvas):
    """A visual evaluation bar showing the position balance."""
    
    def __init__(self, parent, width: int = 30, height: int = 300):
        super().__init__(
            parent, 
            width=width, 
            height=height, 
            bg=BG_DARK,
            highlightthickness=0
        )
        self.width = width
        self.height = height
        self.eval_score = 0.0
        self.is_mate = False
        self.mate_in = 0
        
        self._draw()
    
    def set_eval(self, score: float, is_mate: bool = False, mate_in: int = 0):
        """Set the evaluation score."""
        self.eval_score = score
        self.is_mate = is_mate
        self.mate_in = mate_in
        self._draw()
    
    def _draw(self):
        """Draw the evaluation bar."""
        self.delete("all")
        
        # Calculate white's portion (0-1)
        if self.is_mate:
            white_portion = 1.0 if self.mate_in > 0 else 0.0
        else:
            # Sigmoid-like scaling for smoother visualization
            # Clamp between -10 and +10 pawns
            clamped = max(-10, min(10, self.eval_score))
            white_portion = 0.5 + (clamped / 20)
        
        # Draw black portion (top)
        black_height = int(self.height * (1 - white_portion))
        self.create_rectangle(
            0, 0, self.width, black_height,
            fill=EVAL_BLACK, outline=""
        )
        
        # Draw white portion (bottom)
        self.create_rectangle(
            0, black_height, self.width, self.height,
            fill=EVAL_WHITE, outline=""
        )
        
        # Draw center line
        center_y = self.height // 2
        self.create_line(
            0, center_y, self.width, center_y,
            fill=BG_LIGHTER, width=1
        )
        
        # Draw eval text
        if self.is_mate:
            text = f"M{abs(self.mate_in)}"
            color = ACCENT_SUCCESS if self.mate_in > 0 else ACCENT_DANGER
        else:
            text = f"{self.eval_score:+.1f}"
            if self.eval_score > 0.5:
                color = TEXT_PRIMARY
            elif self.eval_score < -0.5:
                color = TEXT_PRIMARY
            else:
                color = TEXT_MUTED
        
        # Position text
        text_y = black_height - 15 if white_portion > 0.5 else black_height + 15
        text_y = max(15, min(self.height - 15, text_y))
        
        self.create_text(
            self.width // 2, text_y,
            text=text,
            font=(FONT_FAMILY, 9, "bold"),
            fill=color if white_portion > 0.5 else BG_DARK
        )


class AnalysisPanel(tk.Frame):
    """
    Panel showing Stockfish analysis results.
    
    Features:
    - Evaluation bar with score
    - Top 3 moves with evaluations
    - Principal variation (best line)
    - Async analysis support for responsive UI
    - Callbacks for board annotations
    """
    
    def __init__(self, parent, on_analysis_complete=None):
        super().__init__(parent, bg=BG_DARKEST)
        
        self.current_fen: Optional[str] = None
        self.engine = None
        self.is_analyzing = False
        self.last_analysis: Optional[Dict] = None
        
        # Callback for when analysis completes (for board arrows)
        self.on_analysis_complete = on_analysis_complete
        
        self._init_engine()
        self._create_widgets()
    
    def _init_engine(self):
        """Initialize the Stockfish engine."""
        try:
            from src.engine import StockfishEngine
            self.engine = StockfishEngine()
        except Exception as e:
            print(f"Engine init error: {e}")
            self.engine = None
    
    def _create_widgets(self):
        """Create all widgets in compact horizontal layout."""
        # Use grid for precise horizontal layout
        self.grid_columnconfigure(0, weight=0, minsize=80)   # Eval bar
        self.grid_columnconfigure(1, weight=1, minsize=200)  # Top moves
        self.grid_columnconfigure(2, weight=1, minsize=200)  # Best line
        self.grid_rowconfigure(0, weight=0)  # Header
        self.grid_rowconfigure(1, weight=0, minsize=180)  # Content - fixed min height
        self.grid_rowconfigure(2, weight=0)  # Button
        
        # Header
        header = tk.Frame(self, bg=BG_DARKEST)
        header.grid(row=0, column=0, columnspan=3, sticky="ew", padx=PADDING_MD, pady=(PADDING_SM, 0))
        
        tk.Label(
            header,
            text="Stockfish Analysis",
            font=(FONT_FAMILY, FONT_SIZE_MD, "bold"),
            bg=BG_DARKEST,
            fg=TEXT_PRIMARY
        ).pack(side="left")
        
        self.depth_label = tk.Label(
            header,
            text="Depth: -",
            font=(FONT_FAMILY, FONT_SIZE_SM),
            bg=BG_DARKEST,
            fg=TEXT_MUTED
        )
        self.depth_label.pack(side="right")
        
        # Column 0: Eval Bar + Score
        self._create_eval_column()
        
        # Column 1: Top Moves (compact)
        self._create_moves_column()
        
        # Column 2: Best Line
        self._create_pv_column()
    
    def _create_eval_column(self):
        """Create eval bar column."""
        col = tk.Frame(self, bg=BG_DARK, padx=PADDING_SM, pady=PADDING_SM)
        col.grid(row=1, column=0, sticky="n", padx=(PADDING_MD, PADDING_SM))  # Stick to top
        
        tk.Label(
            col,
            text="Eval",
            font=(FONT_FAMILY, FONT_SIZE_SM, "bold"),
            bg=BG_DARK,
            fg=TEXT_MUTED
        ).pack()
        
        # Eval bar
        self.eval_bar = EvalBar(col, width=30, height=140)
        self.eval_bar.pack(pady=PADDING_SM)
        
        # Score
        self.eval_label = tk.Label(
            col,
            text="+0.0",
            font=(FONT_MONO, FONT_SIZE_MD, "bold"),
            bg=BG_DARK,
            fg=TEXT_PRIMARY
        )
        self.eval_label.pack()
        
        self.eval_desc = tk.Label(
            col,
            text="Equal",
            font=(FONT_FAMILY, 9),
            bg=BG_DARK,
            fg=TEXT_MUTED,
            wraplength=60
        )
        self.eval_desc.pack()
    
    def _create_moves_column(self):
        """Create top moves column (compact)."""
        col = tk.Frame(self, bg=BG_DARK, padx=PADDING_SM, pady=PADDING_SM)
        col.grid(row=1, column=1, sticky="new", padx=PADDING_SM)  # Stick to top
        
        tk.Label(
            col,
            text="Top Moves",
            font=(FONT_FAMILY, FONT_SIZE_SM, "bold"),
            bg=BG_DARK,
            fg=TEXT_PRIMARY
        ).pack(anchor="w", pady=(0, PADDING_SM))
        
        # Compact move list
        self.move_labels = []
        colors = [ACCENT_SUCCESS, ACCENT_PRIMARY, ACCENT_WARNING]
        
        for i in range(3):
            move_frame = tk.Frame(col, bg=BG_MEDIUM, padx=PADDING_SM, pady=4)
            move_frame.pack(fill="x", pady=3)
            
            # Rank
            rank = tk.Label(
                move_frame,
                text=f"#{i+1}",
                font=(FONT_FAMILY, 9, "bold"),
                bg=colors[i],
                fg=TEXT_WHITE if i < 2 else BG_DARK,
                padx=4,
                pady=1
            )
            rank.pack(side="left")
            
            # Move
            move_label = tk.Label(
                move_frame,
                text="-",
                font=(FONT_MONO, FONT_SIZE_SM, "bold"),
                bg=BG_MEDIUM,
                fg=TEXT_PRIMARY,
                padx=PADDING_SM
            )
            move_label.pack(side="left")
            
            # Eval
            eval_label = tk.Label(
                move_frame,
                text="",
                font=(FONT_MONO, 9),
                bg=BG_MEDIUM,
                fg=TEXT_SECONDARY
            )
            eval_label.pack(side="right")
            
            self.move_labels.append((move_label, eval_label))
    
    def _create_pv_column(self):
        """Create principal variation column."""
        col = tk.Frame(self, bg=BG_DARK, padx=PADDING_SM, pady=PADDING_SM)
        col.grid(row=1, column=2, sticky="new", padx=(PADDING_SM, PADDING_MD))  # Stick to top
        
        tk.Label(
            col,
            text="Best Line",
            font=(FONT_FAMILY, FONT_SIZE_SM, "bold"),
            bg=BG_DARK,
            fg=TEXT_PRIMARY
        ).pack(anchor="w", pady=(0, PADDING_SM))
        
        # PV text
        pv_frame = tk.Frame(col, bg=BG_LIGHT, padx=2, pady=2)
        pv_frame.pack(fill="x")
        
        self.pv_text = tk.Text(
            pv_frame,
            height=3,
            font=(FONT_MONO, FONT_SIZE_SM),
            bg=BG_MEDIUM,
            fg=TEXT_PRIMARY,
            relief="flat",
            wrap="word",
            padx=PADDING_SM,
            pady=PADDING_SM,
            state="disabled"
        )
        self.pv_text.pack(fill="x")
        
        # Analyze button (compact, inline with Best Line section)
        self.analyze_btn = tk.Button(
            col,
            text="Analyze Position",
            font=(FONT_FAMILY, FONT_SIZE_SM, "bold"),
            bg=BTN_PRIMARY,
            fg=TEXT_PRIMARY,
            activebackground=BTN_PRIMARY_HOVER,
            activeforeground=TEXT_PRIMARY,
            relief="flat",
            cursor="hand2",
            pady=6,
            command=self._start_analysis
        )
        self.analyze_btn.pack(fill="x", pady=(PADDING_SM, 0))
        
        # Status label
        self.status_label = tk.Label(
            col,
            text="Click to analyze",
            font=(FONT_FAMILY, 9),
            bg=BG_DARK,
            fg=TEXT_MUTED
        )
        self.status_label.pack(pady=(4, 0))
    
    def set_position(self, fen: str):
        """Set the current position to analyze."""
        self.current_fen = fen
        self.status_label.config(text="Position updated - click to analyze", fg=ACCENT_PRIMARY)
    
    def _start_analysis(self):
        """Start analyzing the current position."""
        if not self.current_fen or not self.engine:
            self.status_label.config(text="No position or engine", fg=ACCENT_DANGER)
            return
        
        if self.is_analyzing:
            return
        
        self.is_analyzing = True
        self.analyze_btn.config(state=tk.DISABLED, text="⏳ Analyzing...")
        self.status_label.config(text="Calculating...", fg=ACCENT_WARNING)
        
        # Run in background
        thread = threading.Thread(target=self._run_analysis)
        thread.daemon = True
        thread.start()
    
    def _run_analysis(self):
        """Run the analysis in background thread."""
        try:
            depth = 18
            
            # Get evaluation
            eval_result = self.engine.get_eval(self.current_fen, depth=depth)
            
            # Get best moves
            best_moves = self.engine.get_best_moves(self.current_fen, n=3, depth=depth)
            
            # Get PV
            pv, pv_eval = self.engine.get_pv(self.current_fen, depth=depth)
            
            # Update UI in main thread
            self.after(0, lambda: self._update_analysis(eval_result, best_moves, pv, depth))
            
        except Exception as e:
            error_msg = str(e)
            self.after(0, lambda msg=error_msg: self._analysis_error(msg))
    
    def _update_analysis(self, eval_result: dict, best_moves: list, pv: list, depth: int):
        """Update the UI with analysis results."""
        self.is_analyzing = False
        self.analyze_btn.config(state=tk.NORMAL, text="Analyze Position")
        self.status_label.config(text="Analysis complete", fg=ACCENT_SUCCESS)
        
        # Update evaluation
        eval_type = eval_result.get('type', 'cp')
        score = eval_result.get('score', 0)
        
        if eval_type == 'mate':
            self.eval_label.config(text=f"M{score}", fg=ACCENT_SUCCESS if score > 0 else ACCENT_DANGER)
            self.eval_desc.config(text=f"Mate in {abs(score)}")
            self.eval_bar.set_eval(0, is_mate=True, mate_in=score)
        else:
            eval_pawns = score / 100
            self.eval_label.config(
                text=f"{eval_pawns:+.2f}",
                fg=self._get_eval_color(eval_pawns)
            )
            self.eval_desc.config(text=self._describe_eval(eval_pawns))
            self.eval_bar.set_eval(eval_pawns)
        
        self.depth_label.config(text=f"Depth: {depth}")
        
        # Update best moves
        board = chess.Board(self.current_fen)
        for i, (move_label, eval_label) in enumerate(self.move_labels):
            if i < len(best_moves):
                move_info = best_moves[i]
                san = move_info.get('san', move_info.get('move', '-'))
                move_score = move_info.get('score', 0)
                move_type = move_info.get('type', 'cp')
                
                move_label.config(text=san)
                
                if move_type == 'mate':
                    eval_label.config(text=f"M{move_score}")
                else:
                    eval_label.config(text=f"{move_score/100:+.2f}")
            else:
                move_label.config(text="-")
                eval_label.config(text="")
        
        # Update PV
        self.pv_text.config(state="normal")
        self.pv_text.delete("1.0", "end")
        
        if pv:
            # Convert to SAN
            pv_board = chess.Board(self.current_fen)
            pv_san = []
            move_num = pv_board.fullmove_number
            
            for uci in pv[:10]:  # Limit to 10 moves
                try:
                    move = pv_board.parse_uci(uci)
                    if pv_board.turn == chess.WHITE:
                        pv_san.append(f"{move_num}.")
                    pv_san.append(pv_board.san(move))
                    if pv_board.turn == chess.BLACK:
                        move_num += 1
                    pv_board.push(move)
                except:
                    break
            
            self.pv_text.insert("1.0", " ".join(pv_san))
        
        self.pv_text.config(state="disabled")
        
        # Store analysis for external use
        self.last_analysis = {
            'eval': eval_result,
            'best_moves': best_moves,
            'pv': pv,
            'depth': depth,
            'fen': self.current_fen
        }
        
        # Notify callback (for board arrows)
        if self.on_analysis_complete and best_moves:
            self.on_analysis_complete(self.last_analysis)
    
    def _analysis_error(self, error: str):
        """Handle analysis error."""
        self.is_analyzing = False
        self.analyze_btn.config(state=tk.NORMAL, text="Analyze Position")
        self.status_label.config(text=f"Error: {error}", fg=ACCENT_DANGER)
    
    def _get_eval_color(self, eval_pawns: float) -> str:
        """Get color for evaluation display."""
        if eval_pawns > 2:
            return ACCENT_SUCCESS
        elif eval_pawns > 0.5:
            return TEXT_PRIMARY
        elif eval_pawns < -2:
            return ACCENT_DANGER
        elif eval_pawns < -0.5:
            return TEXT_PRIMARY
        else:
            return TEXT_SECONDARY
    
    def _describe_eval(self, eval_pawns: float) -> str:
        """Get description for evaluation."""
        abs_eval = abs(eval_pawns)
        side = "White" if eval_pawns > 0 else "Black"
        
        if abs_eval < 0.2:
            return "Equal position"
        elif abs_eval < 0.5:
            return f"Slight edge for {side}"
        elif abs_eval < 1.0:
            return f"{side} is slightly better"
        elif abs_eval < 2.0:
            return f"{side} has an advantage"
        elif abs_eval < 4.0:
            return f"{side} is clearly winning"
        else:
            return f"Decisive advantage for {side}"
    
    def show_best_move_arrow(self) -> Optional[Tuple[str, str]]:
        """
        Get the best move squares for arrow display.
        
        Returns:
            Tuple of (from_square, to_square) as strings, or None
        """
        if self.last_analysis and self.last_analysis.get('best_moves'):
            best_move = self.last_analysis['best_moves'][0]
            uci = best_move.get('move', '')
            if len(uci) >= 4:
                return (uci[:2], uci[2:4])
        return None
    
    def get_analysis_result(self) -> Optional[Dict]:
        """Get the last analysis result."""
        return self.last_analysis
    
    def cleanup(self):
        """Clean up resources."""
        if self.engine:
            try:
                self.engine.close()
            except:
                pass
