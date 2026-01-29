"""
Query Understanding System - Maps user questions to the right analysis.

This module understands WHAT the user is asking about chess and routes
to the appropriate analysis. It handles questions like:
- "Why is this move good/bad?"
- "What's the idea here?"
- "What should I play?"
- "Is this a sacrifice?"
- "How is my position?"
"""

import re
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

# Import chess concepts from the consolidated fundamentals library
# Use try/except to handle different import contexts
try:
    from src.chess_fundamentals import ALL_FUNDAMENTALS
    _CONCEPT_NAMES_FROM_FUNDAMENTALS = list(ALL_FUNDAMENTALS.keys())
except ImportError:
    try:
        from chess_fundamentals import ALL_FUNDAMENTALS
        _CONCEPT_NAMES_FROM_FUNDAMENTALS = list(ALL_FUNDAMENTALS.keys())
    except ImportError:
        _CONCEPT_NAMES_FROM_FUNDAMENTALS = []


class QueryType(Enum):
    """Types of chess questions users ask."""
    WHY_GOOD = "why_good"              # "Why is Nf3 good?"
    WHY_BAD = "why_bad"                # "Why is h3 bad here?"
    WHAT_TO_PLAY = "what_to_play"      # "What should I play?"
    COMPARE_MOVES = "compare_moves"     # "Is Nf3 better than Nc3?"
    EXPLAIN_POSITION = "explain_pos"    # "What's going on here?"
    EXPLAIN_CONCEPT = "explain_concept" # "What is a pin?"
    EVALUATE = "evaluate"               # "Who's winning?"
    FIND_TACTIC = "find_tactic"        # "Is there a tactic here?"
    CHECK_MOVE = "check_move"          # "Is Nf3 good?"
    EXPLAIN_PLAN = "explain_plan"      # "What's the plan here?"
    GENERAL = "general"                # Catch-all


@dataclass
class ParsedQuery:
    """Result of parsing a user question."""
    query_type: QueryType
    original_question: str
    
    # Extracted moves (if any)
    moves_mentioned: List[str] = None
    
    # Is there a specific move being asked about?
    primary_move: str = None
    comparison_move: str = None
    
    # Sentiment/framing
    assumes_good: bool = False
    assumes_bad: bool = False
    
    # Keywords that influenced parsing
    key_terms: List[str] = None
    
    # Specific concept asked about
    concept_asked: str = None


def _build_chess_concepts_list() -> List[str]:
    """
    Build the list of chess concepts for detection.
    
    Uses concepts from chess_fundamentals.py when available,
    with a fallback list for standalone use.
    """
    # Core concepts that should always be recognized
    core_concepts = [
        'pin', 'fork', 'skewer', 'sacrifice', 'discovered attack', 
        'double attack', 'initiative', 'tempo', 'development',
        'piece activity', 'space', 'pawn structure', 'outpost',
        'weak square', 'open file', 'passed pawn', 'bishop pair',
        'good bishop', 'bad bishop', 'king safety', 'castling',
        'centralization', 'coordination', 'prophylaxis', 'zugzwang',
        'back rank', 'deflection', 'overloading', 'zwischenzug',
        'blockade', 'pawn chain', 'pawn break', 'opposition',
        'rook on seventh', 'control the center'
    ]
    
    # Add concept names from fundamentals (convert underscores to spaces)
    if _CONCEPT_NAMES_FROM_FUNDAMENTALS:
        fundamental_names = [name.replace('_', ' ') for name in _CONCEPT_NAMES_FROM_FUNDAMENTALS]
        # Combine and deduplicate
        all_concepts = list(set(core_concepts + fundamental_names))
        return sorted(all_concepts)
    
    return core_concepts


class QueryParser:
    """
    Parses user chess questions to understand intent.
    
    This is crucial for the explainability system - we need to understand
    WHAT aspect of the position/move the user wants explained.
    """
    
    # Patterns for detecting query types
    WHY_PATTERNS = [
        r"\bwhy\b.*\bgood\b",
        r"\bwhy\b.*\bbest\b",
        r"\bwhy\b.*\bwork[s]?\b",
        r"\bwhy\b.*\bstrong\b",
        r"\bwhat makes\b.*\bgood\b",
        r"\bhow is\b.*\bgood\b",
    ]
    
    WHY_BAD_PATTERNS = [
        r"\bwhy\b.*\bbad\b",
        r"\bwhy\b.*\bwrong\b",
        r"\bwhy\b.*\bmistake\b",
        r"\bwhy\b.*\bweak\b",
        r"\bwhy\b.*\bdoesn'?t work\b",
        r"\bwhat'?s wrong with\b",
        r"\bwhy not\b",
    ]
    
    WHAT_TO_PLAY_PATTERNS = [
        r"\bwhat should\b",
        r"\bwhat do I play\b",
        r"\bwhat'?s the best\b",
        r"\bbest move\b",
        r"\bwhat here\b",
        r"\bwhat now\b",
        r"\bsuggestion\b",
        r"\brecommend\b",
    ]
    
    COMPARE_PATTERNS = [
        r"\bbetter than\b",
        r"\bvs\.?\b",
        r"\bversus\b",
        r"\bor\b.*\?",
        r"\bcompare\b",
        r"\bdifference between\b",
        r"\binstead of\b",
    ]
    
    EVALUATE_PATTERNS = [
        r"\bwho'?s winning\b",
        r"\bwho'?s better\b",
        r"\bevaluation\b",
        r"\bhow'?s the position\b",
        r"\bwhat'?s the position\b",
        r"\bassess\b",
        r"\bequal\b",
    ]
    
    TACTIC_PATTERNS = [
        r"\btactic\b",
        r"\bcombination\b",
        r"\btrick\b",
        r"\btrap\b",
        r"\bwin material\b",
        r"\bcheckmate\b.*\bpattern\b",
    ]
    
    CONCEPT_PATTERNS = [
        r"\bwhat is\b(?:.*\b)(pin|fork|skewer|sacrifice|initiative|tempo)",
        r"\bexplain\b(?:.*\b)(pin|fork|skewer|sacrifice|initiative|tempo|pawn structure)",
        r"\bwhat'?s a\b",
        r"\bdefine\b",
    ]
    
    PLAN_PATTERNS = [
        r"\bplan\b",
        r"\bidea\b",
        r"\bstrategy\b",
        r"\bwhat'?s the goal\b",
        r"\bwhat am I trying\b",
        r"\bhow do I proceed\b",
    ]
    
    # Move pattern (SAN notation)
    MOVE_PATTERN = r'\b([KQRBN]?[a-h]?[1-8]?x?[a-h][1-8](?:=[QRBN])?[+#]?|O-O-O|O-O)\b'
    
    # Chess concepts for detection - dynamically built from chess_fundamentals.py
    CHESS_CONCEPTS = _build_chess_concepts_list()
    
    def parse(self, question: str) -> ParsedQuery:
        """
        Parse a user question about chess.
        
        Args:
            question: The user's question
            
        Returns:
            ParsedQuery with extracted intent and entities
        """
        q_lower = question.lower()
        
        # Extract moves mentioned
        moves = self._extract_moves(question)
        
        # Detect query type
        query_type = self._detect_query_type(q_lower)
        
        # Extract key terms
        key_terms = self._extract_key_terms(q_lower)
        
        # Detect if question assumes the move is good or bad
        assumes_good = any(word in q_lower for word in ['good', 'best', 'strong', 'great', 'brilliant'])
        assumes_bad = any(word in q_lower for word in ['bad', 'mistake', 'blunder', 'wrong', 'weak'])
        
        # Check for specific concept
        concept = self._extract_concept(q_lower)
        
        # Determine primary and comparison moves
        primary_move = None
        comparison_move = None
        
        if moves:
            primary_move = moves[0]
            if len(moves) > 1 and query_type == QueryType.COMPARE_MOVES:
                comparison_move = moves[1]
        
        return ParsedQuery(
            query_type=query_type,
            original_question=question,
            moves_mentioned=moves if moves else None,
            primary_move=primary_move,
            comparison_move=comparison_move,
            assumes_good=assumes_good,
            assumes_bad=assumes_bad,
            key_terms=key_terms if key_terms else None,
            concept_asked=concept
        )
    
    def _extract_moves(self, text: str) -> List[str]:
        """Extract chess moves from text."""
        moves = re.findall(self.MOVE_PATTERN, text)
        # Also check for lowercase algebraic (common in casual speech)
        return list(dict.fromkeys(moves))  # Remove duplicates, preserve order
    
    def _detect_query_type(self, text: str) -> QueryType:
        """Determine the type of question being asked."""
        
        # Check each pattern type
        for pattern in self.WHY_BAD_PATTERNS:
            if re.search(pattern, text):
                return QueryType.WHY_BAD
        
        for pattern in self.WHY_PATTERNS:
            if re.search(pattern, text):
                return QueryType.WHY_GOOD
        
        for pattern in self.COMPARE_PATTERNS:
            if re.search(pattern, text):
                return QueryType.COMPARE_MOVES
        
        for pattern in self.WHAT_TO_PLAY_PATTERNS:
            if re.search(pattern, text):
                return QueryType.WHAT_TO_PLAY
        
        for pattern in self.EVALUATE_PATTERNS:
            if re.search(pattern, text):
                return QueryType.EVALUATE
        
        for pattern in self.TACTIC_PATTERNS:
            if re.search(pattern, text):
                return QueryType.FIND_TACTIC
        
        for pattern in self.CONCEPT_PATTERNS:
            if re.search(pattern, text):
                return QueryType.EXPLAIN_CONCEPT
        
        for pattern in self.PLAN_PATTERNS:
            if re.search(pattern, text):
                return QueryType.EXPLAIN_PLAN
        
        # Check for move-specific questions
        if self._extract_moves(text) and '?' in text:
            return QueryType.CHECK_MOVE
        
        # Position questions
        if any(word in text for word in ['position', 'here', 'situation']):
            return QueryType.EXPLAIN_POSITION
        
        return QueryType.GENERAL
    
    def _extract_key_terms(self, text: str) -> List[str]:
        """Extract important chess terms from the question."""
        terms = []
        
        # Piece names
        pieces = ['king', 'queen', 'rook', 'bishop', 'knight', 'pawn']
        for piece in pieces:
            if piece in text:
                terms.append(piece)
        
        # Chess concepts
        for concept in self.CHESS_CONCEPTS:
            if concept in text:
                terms.append(concept)
        
        # Evaluation words
        eval_words = ['winning', 'losing', 'equal', 'advantage', 'disadvantage']
        for word in eval_words:
            if word in text:
                terms.append(word)
        
        return terms
    
    def _extract_concept(self, text: str) -> Optional[str]:
        """Extract chess concept if the question is about one."""
        for concept in self.CHESS_CONCEPTS:
            # Check for "what is a [concept]" or "explain [concept]"
            patterns = [
                rf"\bwhat(?:'s| is) (?:a |an |the )?{concept}\b",
                rf"\bexplain (?:the )?{concept}\b",
                rf"\btell me about (?:the )?{concept}\b",
            ]
            for pattern in patterns:
                if re.search(pattern, text):
                    return concept
        return None


class ResponseRouter:
    """
    Routes parsed queries to the appropriate analysis function.
    
    Given a ParsedQuery, determines which analysis components to invoke
    and how to structure the response.
    """
    
    @staticmethod
    def get_analysis_plan(query: ParsedQuery) -> Dict:
        """
        Create an analysis plan based on the query.
        
        Args:
            query: Parsed user query
            
        Returns:
            Dict describing what analysis to perform
        """
        plan = {
            'primary_analysis': None,
            'secondary_analysis': [],
            'output_format': 'explanation',
            'include_eval': True,
            'include_pv': False,
            'include_alternatives': False,
            'depth_required': 'standard',  # 'quick', 'standard', 'deep'
        }
        
        if query.query_type == QueryType.WHY_GOOD:
            plan['primary_analysis'] = 'analyze_move'
            plan['secondary_analysis'] = ['detect_tactics', 'explain_concepts']
            plan['include_pv'] = True
            plan['depth_required'] = 'deep'
            
        elif query.query_type == QueryType.WHY_BAD:
            plan['primary_analysis'] = 'explain_mistake'
            plan['secondary_analysis'] = ['compare_to_best', 'show_refutation']
            plan['include_alternatives'] = True
            plan['depth_required'] = 'deep'
            
        elif query.query_type == QueryType.COMPARE_MOVES:
            plan['primary_analysis'] = 'compare_moves'
            plan['secondary_analysis'] = ['feature_comparison']
            plan['include_alternatives'] = False
            plan['depth_required'] = 'deep'
            
        elif query.query_type == QueryType.WHAT_TO_PLAY:
            plan['primary_analysis'] = 'get_best_move'
            plan['secondary_analysis'] = ['analyze_move', 'explain_plan']
            plan['include_alternatives'] = True
            plan['include_pv'] = True
            
        elif query.query_type == QueryType.EVALUATE:
            plan['primary_analysis'] = 'position_evaluation'
            plan['secondary_analysis'] = ['feature_summary']
            plan['output_format'] = 'evaluation_summary'
            
        elif query.query_type == QueryType.FIND_TACTIC:
            plan['primary_analysis'] = 'find_tactics'
            plan['secondary_analysis'] = ['explain_tactic']
            plan['include_pv'] = True
            plan['depth_required'] = 'deep'
            
        elif query.query_type == QueryType.EXPLAIN_CONCEPT:
            plan['primary_analysis'] = 'explain_concept'
            plan['secondary_analysis'] = []
            plan['include_eval'] = False
            plan['output_format'] = 'educational'
            
        elif query.query_type == QueryType.EXPLAIN_PLAN:
            plan['primary_analysis'] = 'position_plans'
            plan['secondary_analysis'] = ['strategic_assessment']
            plan['include_pv'] = True
            
        elif query.query_type == QueryType.CHECK_MOVE:
            plan['primary_analysis'] = 'evaluate_move'
            plan['secondary_analysis'] = ['quick_assessment']
            plan['depth_required'] = 'quick'
            
        elif query.query_type == QueryType.EXPLAIN_POSITION:
            plan['primary_analysis'] = 'full_position_analysis'
            plan['secondary_analysis'] = ['threats', 'plans', 'imbalances']
            plan['output_format'] = 'comprehensive'
            
        else:  # GENERAL
            plan['primary_analysis'] = 'general_response'
            plan['secondary_analysis'] = ['position_assessment']
        
        return plan


# =============================================================================
# QUESTION REFORMULATION
# =============================================================================

def reformulate_for_analysis(query: ParsedQuery) -> str:
    """
    Reformulate the user's question into a clear analysis request.
    
    This helps the system understand exactly what analysis to provide,
    and can also be used to confirm understanding with the user.
    
    Args:
        query: Parsed user query
        
    Returns:
        Clear analysis question
    """
    if query.query_type == QueryType.WHY_GOOD:
        if query.primary_move:
            return f"Explain why {query.primary_move} is a strong move in this position."
        return "Explain why this move is strong."
    
    elif query.query_type == QueryType.WHY_BAD:
        if query.primary_move:
            return f"Explain the problems with {query.primary_move} and what would be better."
        return "Explain why this move is a mistake."
    
    elif query.query_type == QueryType.COMPARE_MOVES:
        if query.primary_move and query.comparison_move:
            return f"Compare {query.primary_move} with {query.comparison_move}: which is better and why?"
        return "Compare these moves and explain the difference."
    
    elif query.query_type == QueryType.WHAT_TO_PLAY:
        return "What is the best move here and why?"
    
    elif query.query_type == QueryType.EVALUATE:
        return "Evaluate this position: who is better and why?"
    
    elif query.query_type == QueryType.FIND_TACTIC:
        return "Find any tactics in this position and explain how they work."
    
    elif query.query_type == QueryType.EXPLAIN_CONCEPT:
        if query.concept_asked:
            return f"Explain the chess concept: {query.concept_asked}"
        return "Explain this chess concept."
    
    elif query.query_type == QueryType.EXPLAIN_PLAN:
        return "What is the strategic plan in this position?"
    
    elif query.query_type == QueryType.CHECK_MOVE:
        if query.primary_move:
            return f"Is {query.primary_move} a good move here? Evaluate it."
        return "Is this move good?"
    
    elif query.query_type == QueryType.EXPLAIN_POSITION:
        return "Give a complete assessment of this position."
    
    return query.original_question


# =============================================================================
# COMMON QUESTION PATTERNS
# =============================================================================

COMMON_QUESTIONS = {
    # These are common question patterns with their optimal analysis approach
    
    "Why didn't I play X?": {
        "interpretation": "Compare the played move with the suggested alternative",
        "analysis_needed": ["move_comparison", "feature_delta"],
    },
    
    "What was wrong with my move?": {
        "interpretation": "Analyze the played move and find its flaws",
        "analysis_needed": ["mistake_analysis", "refutation"],
    },
    
    "Is there a tactic?": {
        "interpretation": "Search for tactical opportunities in the position",
        "analysis_needed": ["tactical_scan", "pattern_detection"],
    },
    
    "What's the idea?": {
        "interpretation": "Explain the strategic or tactical purpose of a move/position",
        "analysis_needed": ["intent_analysis", "plan_detection"],
    },
    
    "Who's winning?": {
        "interpretation": "Evaluate the position and explain the imbalances",
        "analysis_needed": ["evaluation", "feature_summary"],
    },
    
    "What should I focus on?": {
        "interpretation": "Identify the key factors in the current position",
        "analysis_needed": ["critical_factors", "plans"],
    },
}
