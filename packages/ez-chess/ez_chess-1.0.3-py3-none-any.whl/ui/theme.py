"""
EZ Chess Theme - A stunning dark mode color palette.

Inspired by modern IDEs and chess platforms.
Designed to be beautiful, accessible, and easy on the eyes.
"""

# ═══════════════════════════════════════════════════════════════════════════════
#                           DARK MODE COLOR PALETTE
# ═══════════════════════════════════════════════════════════════════════════════

# Background colors (darkest to lightest)
BG_DARKEST = "#0d1117"      # Main window background
BG_DARK = "#161b22"         # Panel backgrounds
BG_MEDIUM = "#21262d"       # Card backgrounds
BG_LIGHT = "#30363d"        # Input backgrounds, hover states
BG_LIGHTER = "#484f58"      # Borders, dividers

# Accent colors
ACCENT_PRIMARY = "#58a6ff"   # Primary blue (links, buttons)
ACCENT_SUCCESS = "#3fb950"   # Green (good moves, success)
ACCENT_WARNING = "#d29922"   # Yellow/orange (warnings, inaccuracies)
ACCENT_DANGER = "#f85149"    # Red (blunders, errors)
ACCENT_INFO = "#8b949e"      # Gray (info, secondary text)
ACCENT_PURPLE = "#a371f7"    # Purple (special highlights)

# Text colors
TEXT_PRIMARY = "#e6edf3"     # Main text
TEXT_SECONDARY = "#8b949e"   # Secondary/muted text
TEXT_MUTED = "#6e7681"       # Very muted text
TEXT_WHITE = "#ffffff"       # Pure white for emphasis

# Chess board colors (modern dark theme)
BOARD_LIGHT = "#769656"      # Light squares (green)
BOARD_DARK = "#4a7c3e"       # Dark squares (darker green)
# Alternative: Brown theme
# BOARD_LIGHT = "#b58863"
# BOARD_DARK = "#6d4c3d"

# Board highlights
HIGHLIGHT_LAST_MOVE = "#829769"      # Last move highlight
HIGHLIGHT_SELECTED = "#646f40"       # Selected square
HIGHLIGHT_LEGAL = "#2d7d4a"         # Legal move indicator (darker green)
HIGHLIGHT_CHECK = "#6b2222"         # King in check (dark red)
HIGHLIGHT_BEST = "#2a4a6d"          # Best move suggestion (blue tint)

# Evaluation bar colors
EVAL_WHITE = "#e6edf3"
EVAL_BLACK = "#30363d"
EVAL_WINNING = "#3fb950"
EVAL_LOSING = "#f85149"

# Message colors (for chat)
MSG_USER = "#1f6feb"         # User message bubble
MSG_ASSISTANT = "#238636"    # Assistant message bubble
MSG_SYSTEM = "#30363d"       # System message bubble
MSG_ERROR = "#f85149"        # Error message

# Button colors
BTN_PRIMARY = "#238636"      # Primary action (green)
BTN_PRIMARY_HOVER = "#2ea043"
BTN_SECONDARY = "#21262d"    # Secondary action
BTN_SECONDARY_HOVER = "#30363d"
BTN_DANGER = "#da3633"       # Dangerous action
BTN_DANGER_HOVER = "#f85149"

# Scrollbar colors
SCROLLBAR_BG = "#161b22"
SCROLLBAR_FG = "#484f58"
SCROLLBAR_HOVER = "#6e7681"

# ═══════════════════════════════════════════════════════════════════════════════
#                              FONTS
# ═══════════════════════════════════════════════════════════════════════════════

FONT_FAMILY = "Segoe UI"     # Modern Windows font (falls back gracefully)
FONT_MONO = "Consolas"       # Monospace for code/moves

# Font sizes
FONT_SIZE_XS = 9
FONT_SIZE_SM = 10
FONT_SIZE_MD = 11
FONT_SIZE_LG = 13
FONT_SIZE_XL = 16
FONT_SIZE_XXL = 20
FONT_SIZE_TITLE = 24

# Font tuples
FONT_NORMAL = (FONT_FAMILY, FONT_SIZE_MD)
FONT_SMALL = (FONT_FAMILY, FONT_SIZE_SM)
FONT_LARGE = (FONT_FAMILY, FONT_SIZE_LG)
FONT_TITLE = (FONT_FAMILY, FONT_SIZE_XL, "bold")
FONT_HEADING = (FONT_FAMILY, FONT_SIZE_LG, "bold")
FONT_MONO_NORMAL = (FONT_MONO, FONT_SIZE_MD)
FONT_MONO_SMALL = (FONT_MONO, FONT_SIZE_SM)

# ═══════════════════════════════════════════════════════════════════════════════
#                           DIMENSIONS
# ═══════════════════════════════════════════════════════════════════════════════

PADDING_XS = 2
PADDING_SM = 5
PADDING_MD = 10
PADDING_LG = 15
PADDING_XL = 20

BORDER_RADIUS = 8
BORDER_WIDTH = 1

# Panel widths
PANEL_LEFT_WIDTH = 340
PANEL_RIGHT_WIDTH = 380
BOARD_SIZE = 480

# ═══════════════════════════════════════════════════════════════════════════════
#                        UNICODE SYMBOLS
# ═══════════════════════════════════════════════════════════════════════════════

# Chess pieces (use these for rendering)
PIECE_SYMBOLS = {
    'K': '♔', 'Q': '♕', 'R': '♖', 'B': '♗', 'N': '♘', 'P': '♙',
    'k': '♚', 'q': '♛', 'r': '♜', 'b': '♝', 'n': '♞', 'p': '♟'
}

# UI icons (text-based, no emojis)
ICON_ANALYZE = "Analyze"
ICON_PLAY = "▶"
ICON_PAUSE = "⏸"
ICON_PREV = "◀"
ICON_NEXT = "▶"
ICON_FIRST = "⏮"
ICON_LAST = "⏭"
ICON_FLIP = "Flip"
ICON_COPY = "Copy"
ICON_SEND = "➤"
ICON_SETTINGS = "Settings"
ICON_CHECK = "✓"
ICON_CROSS = "✕"
ICON_WARNING = "!"
ICON_INFO = "i"
ICON_LIGHTBULB = "Hint"
ICON_CHESS = "♟"
ICON_BOOK = "Book"
