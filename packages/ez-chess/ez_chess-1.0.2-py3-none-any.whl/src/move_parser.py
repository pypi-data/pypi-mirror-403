"""
Natural Language Move Parser
Simple utility to help identify if a question contains move references.

We keep this minimal and let the LLM handle the actual interpretation,
as LLMs are quite good at understanding chess notation from context.
"""

import chess
import re
from typing import Optional, List, Tuple


def contains_move_reference(text: str) -> bool:
    """
    Check if text likely contains a move reference.
    
    This is a simple heuristic to help the agent decide which tool to use.
    """
    text_lower = text.lower()
    
    # Check for piece names with movement words
    move_indicators = [
        'takes', 'captures', 'capture', 'to', 'plays', 'play', 
        'move', 'moving', 'castle', 'castles'
    ]
    piece_names = ['king', 'queen', 'rook', 'bishop', 'knight', 'pawn']
    
    for piece in piece_names:
        for indicator in move_indicators:
            if piece in text_lower and indicator in text_lower:
                return True
    
    # Check for SAN-like patterns (Nf3, Qxd4, e4, O-O, etc.)
    san_pattern = r'\b[KQRBN]?[a-h]?[1-8]?x?[a-h][1-8](?:=[QRBN])?[+#]?\b'
    if re.search(san_pattern, text):
        return True
    
    # Check for castling
    if 'castle' in text_lower or 'o-o' in text_lower or '0-0' in text_lower:
        return True
    
    return False


def get_question_type(question: str) -> str:
    """
    Determine the type of chess question being asked.
    
    Returns one of:
    - 'best_move': User wants to know the best move
    - 'move_quality': User is asking about a specific move's quality
    - 'compare_moves': User wants to compare moves
    - 'general': General position question
    """
    q_lower = question.lower()
    
    # Best move questions
    best_move_patterns = [
        'best move', 'what should i play', 'what to play', 
        'what move', 'recommend', 'suggestion', 'what do you suggest',
        'what would you play', 'engine says', 'stockfish'
    ]
    for pattern in best_move_patterns:
        if pattern in q_lower:
            return 'best_move'
    
    # Move quality questions (contains a move reference + quality words)
    quality_words = [
        'good', 'bad', 'blunder', 'mistake', 'inaccuracy', 
        'why', 'how', 'would', 'should', 'if i play', 'what if',
        'is this', 'is that'
    ]
    if contains_move_reference(question):
        for word in quality_words:
            if word in q_lower:
                return 'move_quality'
    
    # Compare moves (multiple moves mentioned or explicit comparison)
    compare_patterns = ['compare', 'vs', 'versus', 'or', 'better', 'between']
    if any(p in q_lower for p in compare_patterns) and contains_move_reference(question):
        return 'compare_moves'
    
    # Default to general
    return 'general'


def preprocess_question(question: str, fen: str) -> str:
    """
    Preprocess a question - now just adds question type hint.
    
    We let the LLM handle move interpretation directly.
    """
    q_type = get_question_type(question)
    
    hints = {
        'best_move': '[Question type: BEST_MOVE - use get_best_move_tool]',
        'move_quality': '[Question type: MOVE_QUALITY - use move_quality_tool with the move in SAN notation]',
        'compare_moves': '[Question type: COMPARE_MOVES - use move_comparison_tool]',
        'general': '[Question type: GENERAL]'
    }
    
    return f"{question}\n{hints.get(q_type, '')}"


# Keep these for backwards compatibility but they're now simple
def extract_moves_from_text(text: str, fen: str) -> List[Tuple[str, str]]:
    """Deprecated - returns empty list. Let LLM handle move parsing."""
    return []


def parse_natural_language_move(text: str, fen: str, strict: bool = True) -> Optional[str]:
    """Deprecated - returns None. Let LLM handle move parsing."""
    return None


# Quick test
if __name__ == "__main__":
    tests = [
        "What's the best move?",
        "Why is Qxd4 bad?",
        "Is queen takes d4 good?",
        "Compare Nc6 and Nf6",
        "How is my king safety?",
    ]
    
    print("Question Type Detection:")
    for test in tests:
        q_type = get_question_type(test)
        has_move = contains_move_reference(test)
        print(f"  '{test}'")
        print(f"    -> Type: {q_type}, Has move ref: {has_move}")
        print()
