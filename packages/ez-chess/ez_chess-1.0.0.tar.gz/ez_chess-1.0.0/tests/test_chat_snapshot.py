"""
Quick visual test for the chat panel board snapshot feature.
This demonstrates the mini board appearing in user messages.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import tkinter as tk
from ui.chat_panel import ChatPanel, MiniBoardSnapshot
from ui.theme import BG_DARKEST


def test_mini_board_snapshot():
    """Test the MiniBoardSnapshot widget directly."""
    print("=" * 60)
    print("MINI BOARD SNAPSHOT TEST")
    print("=" * 60)
    
    root = tk.Tk()
    root.title("Board Snapshot Test")
    root.configure(bg=BG_DARKEST)
    root.geometry("400x600")
    
    # Title
    tk.Label(
        root,
        text="Board Snapshots in Chat",
        font=("Segoe UI", 14, "bold"),
        bg=BG_DARKEST,
        fg="#e0e0e0"
    ).pack(pady=10)
    
    # Test positions
    positions = [
        ("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1", 0, "Starting Position"),
        ("rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq - 0 1", 1, "After 1.e4"),
        ("r1bqkb1r/pppp1ppp/2n2n2/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 4 4", 7, "Italian Game"),
    ]
    
    for fen, move_num, name in positions:
        frame = tk.Frame(root, bg=BG_DARKEST)
        frame.pack(pady=10, padx=20, fill="x")
        
        # Label
        tk.Label(
            frame,
            text=name,
            font=("Segoe UI", 10),
            bg=BG_DARKEST,
            fg="#aaaaaa"
        ).pack(anchor="w")
        
        # Snapshot
        snapshot = MiniBoardSnapshot(frame, fen, move_num)
        snapshot.pack(pady=5, anchor="w")
    
    # Instructions
    tk.Label(
        root,
        text="These snapshots appear in chat messages\nto show position context",
        font=("Segoe UI", 9),
        bg=BG_DARKEST,
        fg="#666666"
    ).pack(pady=20)
    
    tk.Label(
        root,
        text="(Window closes automatically in 5 seconds)",
        font=("Segoe UI", 8),
        bg=BG_DARKEST,
        fg="#555555"
    ).pack()
    
    # Auto close
    root.after(5000, root.destroy)
    
    print("\nDisplaying board snapshots...")
    print("(Window will close in 5 seconds)")
    
    try:
        root.mainloop()
    except:
        pass
    
    print("\n✓ MINI BOARD SNAPSHOT TEST PASSED")


if __name__ == "__main__":
    test_mini_board_snapshot()
