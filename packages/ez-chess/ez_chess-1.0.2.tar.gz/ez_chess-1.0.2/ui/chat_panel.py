"""
Chat Panel - AI-powered Q&A about chess positions.

A modern chat interface for asking questions about positions.
Includes mini board snapshots for user reference when navigating.
"""

import tkinter as tk
from tkinter import ttk, Canvas
import threading
import chess
from typing import Optional, List, Dict
from datetime import datetime

from ui.theme import (
    BG_DARKEST, BG_DARK, BG_MEDIUM, BG_LIGHT, BG_LIGHTER,
    TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED, TEXT_WHITE,
    ACCENT_PRIMARY, ACCENT_SUCCESS, ACCENT_WARNING, ACCENT_DANGER, ACCENT_PURPLE,
    MSG_USER, MSG_ASSISTANT, MSG_SYSTEM, MSG_ERROR,
    BTN_PRIMARY, BTN_PRIMARY_HOVER, BTN_SECONDARY, BTN_SECONDARY_HOVER,
    FONT_FAMILY, FONT_MONO, FONT_SIZE_SM, FONT_SIZE_MD, FONT_SIZE_LG,
    PADDING_SM, PADDING_MD, PADDING_LG,
    ICON_SEND, ICON_LIGHTBULB, PIECE_SYMBOLS,
    BOARD_LIGHT, BOARD_DARK
)


class MiniBoardSnapshot(tk.Frame):
    """
    A small, non-interactive chess board snapshot for embedding in chat.
    Shows the position at the time a question was asked.
    """
    
    SNAPSHOT_SIZE = 160  # 160x160 pixels
    
    def __init__(self, parent, fen: str, move_number: int = 0):
        super().__init__(parent, bg=BG_DARK, padx=2, pady=2)
        
        self.fen = fen
        self.move_number = move_number
        self.square_size = self.SNAPSHOT_SIZE // 8
        
        # Header with move number
        header = tk.Frame(self, bg=BG_DARK)
        header.pack(fill="x")
        
        move_text = f"Move {move_number}" if move_number > 0 else "Starting position"
        tk.Label(
            header,
            text=move_text,
            font=(FONT_FAMILY, 8),
            bg=BG_DARK,
            fg=TEXT_MUTED
        ).pack(side="left")
        
        # Canvas for the board
        self.canvas = Canvas(
            self,
            width=self.SNAPSHOT_SIZE,
            height=self.SNAPSHOT_SIZE,
            bg=BG_DARK,
            highlightthickness=1,
            highlightbackground="#333333"
        )
        self.canvas.pack()
        
        # Draw the board
        self._draw_board()
    
    def _draw_board(self):
        """Draw the mini board with pieces."""
        try:
            board = chess.Board(self.fen)
        except:
            return
        
        # Draw squares and pieces
        for square in chess.SQUARES:
            file = chess.square_file(square)
            rank = chess.square_rank(square)
            
            x1 = file * self.square_size
            y1 = (7 - rank) * self.square_size
            x2 = x1 + self.square_size
            y2 = y1 + self.square_size
            
            # Square color
            is_light = (file + rank) % 2 == 1
            color = BOARD_LIGHT if is_light else BOARD_DARK
            
            self.canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline="")
            
            # Piece
            piece = board.piece_at(square)
            if piece:
                symbol = PIECE_SYMBOLS[piece.symbol()]
                cx = (x1 + x2) // 2
                cy = (y1 + y2) // 2
                font_size = int(self.square_size * 0.7)
                
                # Piece color
                if piece.color == chess.WHITE:
                    piece_color = "#f5e6d3"  # Ivory
                else:
                    piece_color = "#3d2817"  # Dark walnut
                
                # Shadow
                self.canvas.create_text(
                    cx + 1, cy + 1,
                    text=symbol,
                    font=(FONT_FAMILY, font_size),
                    fill="#1a1410"
                )
                
                # Main piece
                self.canvas.create_text(
                    cx, cy,
                    text=symbol,
                    font=(FONT_FAMILY, font_size),
                    fill=piece_color
                )
        
        # Draw side to move indicator
        turn = board.turn
        indicator_color = "#f5e6d3" if turn == chess.WHITE else "#3d2817"
        self.canvas.create_oval(
            self.SNAPSHOT_SIZE - 12, 2,
            self.SNAPSHOT_SIZE - 2, 12,
            fill=indicator_color,
            outline="#555555"
        )


class ChatPanel(tk.Frame):
    """
    Chat panel for AI-powered chess Q&A.
    Modern LLM-style chat with scrollable message history.
    """
    
    def __init__(self, parent):
        super().__init__(parent, bg=BG_DARKEST)
        
        # Start with default position
        self.current_fen: Optional[str] = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
        self.current_move: int = 0
        self.agent = None
        self.is_processing = False
        self.messages = []  # Store message history
        
        self._create_widgets()
        self._init_agent()
    
    def _create_widgets(self):
        """Create all widgets with proper layout."""
        # Use grid for precise control
        self.grid_rowconfigure(1, weight=1)  # Chat area expands
        self.grid_columnconfigure(0, weight=1)
        
        # ═══════════════════════════════════════════════════════════════
        # ROW 0: Header
        # ═══════════════════════════════════════════════════════════════
        header = tk.Frame(self, bg=BG_DARKEST)
        header.grid(row=0, column=0, sticky="ew", padx=PADDING_MD, pady=(PADDING_SM, 0))
        
        tk.Label(
            header,
            text="AI Chess Assistant",
            font=(FONT_FAMILY, FONT_SIZE_MD, "bold"),
            bg=BG_DARKEST,
            fg=TEXT_PRIMARY
        ).pack(side="left")
        
        self.status_indicator = tk.Label(
            header,
            text="●",
            font=(FONT_FAMILY, FONT_SIZE_SM),
            bg=BG_DARKEST,
            fg=ACCENT_WARNING
        )
        self.status_indicator.pack(side="right")
        
        self.status_label = tk.Label(
            header,
            text="Loading...",
            font=(FONT_FAMILY, FONT_SIZE_SM),
            bg=BG_DARKEST,
            fg=TEXT_MUTED
        )
        self.status_label.pack(side="right", padx=(0, PADDING_SM))
        
        # ═══════════════════════════════════════════════════════════════
        # ROW 1: Chat Messages Area (scrollable) - THIS EXPANDS
        # ═══════════════════════════════════════════════════════════════
        chat_container = tk.Frame(self, bg=BG_DARK)
        chat_container.grid(row=1, column=0, sticky="nsew", padx=PADDING_MD, pady=PADDING_SM)
        
        # Scrollable text widget for messages (simpler than canvas)
        self.chat_text = tk.Text(
            chat_container,
            font=(FONT_FAMILY, FONT_SIZE_SM),
            bg=BG_DARK,
            fg=TEXT_PRIMARY,
            wrap="word",
            state="disabled",
            cursor="arrow",
            padx=PADDING_MD,
            pady=PADDING_MD,
            relief="flat",
            highlightthickness=0
        )
        
        scrollbar = tk.Scrollbar(chat_container, command=self.chat_text.yview)
        self.chat_text.configure(yscrollcommand=scrollbar.set)
        
        scrollbar.pack(side="right", fill="y")
        self.chat_text.pack(side="left", fill="both", expand=True)
        
        # Configure text tags for styling
        self.chat_text.tag_configure("user_name", foreground=ACCENT_PRIMARY, font=(FONT_FAMILY, FONT_SIZE_SM, "bold"))
        self.chat_text.tag_configure("user_msg", foreground=TEXT_PRIMARY, background=MSG_USER, 
                                      font=(FONT_FAMILY, FONT_SIZE_SM), lmargin1=10, lmargin2=10, rmargin=50)
        self.chat_text.tag_configure("assistant_name", foreground=ACCENT_SUCCESS, font=(FONT_FAMILY, FONT_SIZE_SM, "bold"))
        self.chat_text.tag_configure("assistant_msg", foreground=TEXT_PRIMARY, 
                                      font=(FONT_FAMILY, FONT_SIZE_SM), lmargin1=10, lmargin2=10, rmargin=50)
        self.chat_text.tag_configure("system_msg", foreground=TEXT_MUTED, justify="center",
                                      font=(FONT_FAMILY, FONT_SIZE_SM, "italic"))
        self.chat_text.tag_configure("error_msg", foreground=ACCENT_DANGER, font=(FONT_FAMILY, FONT_SIZE_SM))
        self.chat_text.tag_configure("timestamp", foreground=TEXT_MUTED, font=(FONT_FAMILY, 8))
        self.chat_text.tag_configure("spacing", font=(FONT_FAMILY, 4))
        
        # Welcome message
        self._add_system_message("Welcome! Ask questions about the current position.")
        
        # ═══════════════════════════════════════════════════════════════
        # ROW 2: Quick suggestion buttons
        # ═══════════════════════════════════════════════════════════════
        suggestions_frame = tk.Frame(self, bg=BG_DARKEST)
        suggestions_frame.grid(row=2, column=0, sticky="ew", padx=PADDING_MD, pady=(0, PADDING_SM))
        
        suggestions = ["What's the best move?", "Why is this bad?", "What's the plan?"]
        for text in suggestions:
            btn = tk.Button(
                suggestions_frame,
                text=text,
                font=(FONT_FAMILY, 9),
                bg=BG_MEDIUM,
                fg=TEXT_SECONDARY,
                activebackground=BG_LIGHT,
                activeforeground=TEXT_PRIMARY,
                relief="flat",
                cursor="hand2",
                padx=PADDING_SM,
                pady=2,
                command=lambda t=text: self._use_suggestion(t)
            )
            btn.pack(side="left", padx=(0, PADDING_SM))
        
        # ═══════════════════════════════════════════════════════════════
        # ROW 3: Input area
        # ═══════════════════════════════════════════════════════════════
        input_frame = tk.Frame(self, bg=BG_DARK, padx=PADDING_SM, pady=PADDING_SM)
        input_frame.grid(row=3, column=0, sticky="ew", padx=PADDING_MD, pady=(0, PADDING_SM))
        
        # Text input
        self.input_text = tk.Text(
            input_frame,
            height=2,
            font=(FONT_FAMILY, FONT_SIZE_SM),
            bg=BG_MEDIUM,
            fg=TEXT_PRIMARY,
            insertbackground=TEXT_PRIMARY,
            selectbackground=ACCENT_PRIMARY,
            relief="flat",
            wrap="word",
            padx=PADDING_SM,
            pady=PADDING_SM
        )
        self.input_text.pack(side="left", fill="x", expand=True, padx=(0, PADDING_SM))
        
        # Placeholder
        self.input_text.insert("1.0", "Ask a question...")
        self.input_text.config(fg=TEXT_MUTED)
        self.input_text.bind("<FocusIn>", self._on_input_focus_in)
        self.input_text.bind("<FocusOut>", self._on_input_focus_out)
        self.input_text.bind("<Return>", self._on_enter)
        self.input_text.bind("<Shift-Return>", lambda e: None)
        
        # Send button
        self.send_btn = tk.Button(
            input_frame,
            text="Send",
            font=(FONT_FAMILY, FONT_SIZE_SM, "bold"),
            bg=BTN_PRIMARY,
            fg=TEXT_WHITE,
            activebackground=BTN_PRIMARY_HOVER,
            activeforeground=TEXT_WHITE,
            relief="flat",
            cursor="hand2",
            width=8,
            command=self._send_message
        )
        self.send_btn.pack(side="right", fill="y")
    
    def _on_input_focus_in(self, event):
        """Handle focus in on input."""
        if self.input_text.get("1.0", "end-1c") == "Ask a question...":
            self.input_text.delete("1.0", "end")
            self.input_text.config(fg=TEXT_PRIMARY)
    
    def _on_input_focus_out(self, event):
        """Handle focus out on input."""
        if not self.input_text.get("1.0", "end-1c").strip():
            self.input_text.delete("1.0", "end")
            self.input_text.insert("1.0", "Ask a question...")
            self.input_text.config(fg=TEXT_MUTED)
    
    def _on_enter(self, event):
        """Handle Enter key."""
        if not (event.state & 1):  # Shift not pressed
            self._send_message()
            return "break"
    
    def _init_agent(self):
        """Initialize the chess agent in background."""
        thread = threading.Thread(target=self._load_agent)
        thread.daemon = True
        thread.start()
    
    def _load_agent(self):
        """Load the agent (background thread)."""
        try:
            # Use Groq agent with tool calling for hypothetical analysis
            from src.groq_agent import create_groq_agent
            self.agent = create_groq_agent(verbose=True)
            self.after(0, self._agent_loaded)
        except Exception as e:
            error_msg = str(e)
            self.after(0, lambda: self._agent_error(error_msg))
    
    def _agent_loaded(self):
        """Called when agent is loaded."""
        self.status_label.config(text="Ready")
        self.status_indicator.config(fg=ACCENT_SUCCESS)
        self._add_system_message("AI Assistant ready! Ask about the position, hypothetical moves, or compare lines.")
    
    def _agent_error(self, error: str):
        """Called when agent fails to load."""
        self.status_label.config(text="Error")
        self.status_indicator.config(fg=ACCENT_DANGER)
        self._add_message("System", f"Failed to load AI: {error}\nSet GROQ_API_KEY env variable (free at console.groq.com)", "error")
    
    def set_position(self, fen: str, move_number: int):
        """Set the current position for context."""
        self.current_fen = fen
        self.current_move = move_number
    
    def _use_suggestion(self, text: str):
        """Use a suggestion chip."""
        self.input_text.delete("1.0", "end")
        self.input_text.config(fg=TEXT_PRIMARY)
        self.input_text.insert("1.0", text)
        self._send_message()
    
    def _send_message(self):
        """Send the user's message."""
        question = self.input_text.get("1.0", "end-1c").strip()
        
        # Ignore placeholder or empty
        if not question or question == "Ask a question...":
            return
        
        if not self.agent:
            self._add_message("System", "Agent not loaded yet. Please wait...", "error")
            return
        
        if not self.current_fen:
            self._add_message("System", "No position loaded. Load a game first!", "error")
            return
        
        if self.is_processing:
            return
        
        # Capture current position for snapshot
        snapshot_fen = self.current_fen
        snapshot_move = self.current_move
        
        # Clear input
        self.input_text.delete("1.0", "end")
        self.input_text.config(fg=TEXT_PRIMARY)
        
        # Add user message with board snapshot
        self._add_message("You", question, "user", fen=snapshot_fen, move_number=snapshot_move)
        
        # Process in background
        self.is_processing = True
        self.send_btn.config(state=tk.DISABLED)
        self.status_label.config(text="Thinking...")
        self.status_indicator.config(fg=ACCENT_WARNING)
        
        thread = threading.Thread(target=self._process_question, args=(question,))
        thread.daemon = True
        thread.start()
    
    def _process_question(self, question: str):
        """Process the question (background thread)."""
        try:
            answer = self.agent.analyze(self.current_fen, question)
            self.after(0, lambda: self._show_answer(answer))
        except Exception as e:
            error_msg = str(e)
            self.after(0, lambda: self._show_error(error_msg))
    
    def _show_answer(self, answer: str):
        """Display the answer."""
        self.is_processing = False
        self.send_btn.config(state=tk.NORMAL)
        self.status_label.config(text="Ready")
        self.status_indicator.config(fg=ACCENT_SUCCESS)
        
        if not answer or not str(answer).strip():
            self._add_message("Assistant", "I couldn't generate a response. Please try again.", "assistant")
        else:
            self._add_message("Assistant", str(answer), "assistant")
    
    def _show_error(self, error: str):
        """Display an error."""
        self.is_processing = False
        self.send_btn.config(state=tk.NORMAL)
        self.status_label.config(text="Error")
        self.status_indicator.config(fg=ACCENT_DANGER)
        
        self._add_message("System", f"Error: {error}", "error")
    
    def _add_message(self, sender: str, message: str, msg_type: str = "user", 
                     fen: Optional[str] = None, move_number: int = 0):
        """
        Add a message to the chat display.
        
        For user messages, includes a mini board snapshot showing the position
        at the time of asking (for user reference when navigating).
        """
        self.chat_text.config(state="normal")
        
        timestamp = datetime.now().strftime("%H:%M")
        
        # Add spacing if not first message
        if self.chat_text.get("1.0", "end-1c").strip():
            self.chat_text.insert("end", "\n", "spacing")
        
        if msg_type == "user":
            self.chat_text.insert("end", f"You ", "user_name")
            self.chat_text.insert("end", f"({timestamp})\n", "timestamp")
            self.chat_text.insert("end", f"{message}\n", "user_msg")
            
            # Add board snapshot for user messages (for reference when navigating)
            if fen:
                self._add_board_snapshot(fen, move_number)
                
        elif msg_type == "assistant":
            self.chat_text.insert("end", f"Assistant ", "assistant_name")
            self.chat_text.insert("end", f"({timestamp})\n", "timestamp")
            self.chat_text.insert("end", f"{message}\n", "assistant_msg")
        elif msg_type == "system":
            self.chat_text.insert("end", f"{message}\n", "system_msg")
        elif msg_type == "error":
            self.chat_text.insert("end", f"Error: {message}\n", "error_msg")
        
        self.chat_text.config(state="disabled")
        
        # Scroll to bottom
        self.chat_text.see("end")
        
        # Store in history (include FEN for user messages)
        self.messages.append({
            "sender": sender, 
            "message": message, 
            "type": msg_type, 
            "time": timestamp,
            "fen": fen if msg_type == "user" else None,
            "move_number": move_number
        })
    
    def _add_board_snapshot(self, fen: str, move_number: int):
        """Add a mini board snapshot to the chat."""
        try:
            # Create a frame to hold the snapshot
            snapshot_frame = tk.Frame(self.chat_text, bg=BG_DARK)
            
            # Create the mini board
            snapshot = MiniBoardSnapshot(snapshot_frame, fen, move_number)
            snapshot.pack(pady=(4, 8))
            
            # Store reference to prevent garbage collection
            if not hasattr(self, '_snapshots'):
                self._snapshots: List[tk.Widget] = []
            self._snapshots.append(snapshot_frame)
            
            # Insert into text widget as a window
            self.chat_text.window_create("end", window=snapshot_frame)
            self.chat_text.insert("end", "\n")
        except Exception as e:
            # Silently fail - snapshot is just for reference
            pass
    
    def _add_system_message(self, message: str):
        """Add a system message."""
        self._add_message("System", message, "system")
