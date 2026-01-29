"""
Chess Concept Explainer - Translates engine analysis into human understanding.

This module contains the vocabulary and frameworks for explaining chess concepts
in natural language. It maps technical analysis to pedagogical explanations.

NOTE: For comprehensive chess concepts with full teaching context, see chess_fundamentals.py
This module provides legacy compatibility and additional explanation templates.
The chess_fundamentals.py module has 60+ concepts from Lichess training resources.
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum

# Import evaluation functions from llm_prompts to avoid duplication
# These are the canonical versions - this module provides aliases for backward compatibility
# Use try/except to handle different import contexts (from src/ vs from project root)
try:
    from src.llm_prompts import (
        describe_eval as _describe_eval_new,
        describe_eval_change as _describe_eval_change_new,
    )
    from src.chess_fundamentals import (
        ALL_FUNDAMENTALS, ChessFundamental, ConceptCategory,
        get_fundamental, get_related_fundamentals, get_fundamentals_for_position_type,
        TACTICAL_MOTIFS, POSITIONAL_CONCEPTS, OPENING_PRINCIPLES, PIECE_PLACEMENT,
        PAWN_STRUCTURE, KING_SAFETY, ATTACKING_PRINCIPLES, DEFENSIVE_PRINCIPLES,
        ENDGAME_FUNDAMENTALS
    )
except ImportError:
    from llm_prompts import (
        describe_eval as _describe_eval_new,
        describe_eval_change as _describe_eval_change_new,
    )
    from chess_fundamentals import (
        ALL_FUNDAMENTALS, ChessFundamental, ConceptCategory,
        get_fundamental, get_related_fundamentals, get_fundamentals_for_position_type,
        TACTICAL_MOTIFS, POSITIONAL_CONCEPTS, OPENING_PRINCIPLES, PIECE_PLACEMENT,
        PAWN_STRUCTURE, KING_SAFETY, ATTACKING_PRINCIPLES, DEFENSIVE_PRINCIPLES,
        ENDGAME_FUNDAMENTALS
    )


class ChessConceptCategory(Enum):
    """High-level categories of chess concepts (legacy - see ConceptCategory in chess_fundamentals.py)."""
    TACTICAL = "tactical"
    STRATEGIC = "strategic"
    POSITIONAL = "positional"
    ENDGAME = "endgame"
    OPENING = "opening"


@dataclass
class ChessConcept:
    """A chess concept with its explanation framework (legacy - see ChessFundamental for full version)."""
    name: str
    category: ChessConceptCategory
    description: str
    typical_signs: List[str]
    how_to_explain: str
    common_patterns: List[str] = field(default_factory=list)
    teaching_examples: List[str] = field(default_factory=list)


# =============================================================================
# CHESS CONCEPT LIBRARY
# =============================================================================

CHESS_CONCEPTS = {
    # =========================================================================
    # TACTICAL CONCEPTS
    # =========================================================================
    
    "fork": ChessConcept(
        name="Fork",
        category=ChessConceptCategory.TACTICAL,
        description="A single piece attacks two or more enemy pieces simultaneously",
        typical_signs=[
            "Knight/pawn/queen moves to square attacking multiple pieces",
            "Attacked pieces include king, queen, or rook",
            "One of the attacked pieces cannot be defended"
        ],
        how_to_explain="Explain which pieces are under attack simultaneously and "
                       "why the opponent cannot save both. Note the piece executing "
                       "the fork and its relative value.",
        common_patterns=["Knight fork on king and queen", "Pawn fork", "Queen fork"],
    ),
    
    "pin": ChessConcept(
        name="Pin",
        category=ChessConceptCategory.TACTICAL,
        description="A piece cannot move because doing so would expose a more valuable piece",
        typical_signs=[
            "Piece is on line between attacker and king/queen",
            "Moving the pinned piece is illegal or loses material",
            "Attacker is a long-range piece (bishop, rook, queen)"
        ],
        how_to_explain="Show the line of attack: which piece is pinned, what it's "
                       "pinned to, and what would happen if it moved. Distinguish "
                       "absolute pin (to king) vs relative pin (to queen/rook).",
        common_patterns=["Bishop pinning knight to king", "Rook pin on back rank"],
    ),
    
    "skewer": ChessConcept(
        name="Skewer",
        category=ChessConceptCategory.TACTICAL,
        description="An attack on a valuable piece that, when it moves, exposes a piece behind it",
        typical_signs=[
            "Long-range piece attacks valuable piece (usually king/queen)",
            "Another piece is behind it on the same line",
            "Valuable piece must move, exposing the piece behind"
        ],
        how_to_explain="Like a reverse pin - the MORE valuable piece is in front. "
                       "When it moves (often forced), the piece behind is captured.",
        common_patterns=["Bishop skewer of king and rook", "Rook skewer on back rank"],
    ),
    
    "discovered_attack": ChessConcept(
        name="Discovered Attack",
        category=ChessConceptCategory.TACTICAL,
        description="Moving one piece reveals an attack by another piece",
        typical_signs=[
            "Piece moves off a line, revealing an attack",
            "Two threats are created with one move",
            "Often creates discovered check"
        ],
        how_to_explain="Explain that by moving piece A, piece B's attack is 'discovered'. "
                       "Often piece A creates its own threat, making two threats at once.",
        common_patterns=["Discovered check", "Discovered attack on queen"],
    ),
    
    "double_attack": ChessConcept(
        name="Double Attack",
        category=ChessConceptCategory.TACTICAL,
        description="Two pieces are attacked simultaneously (not necessarily by the same piece)",
        typical_signs=[
            "Two threats created with one move",
            "Opponent cannot address both threats"
        ],
        how_to_explain="Show both threats and explain why addressing one leaves "
                       "the other undefended.",
    ),
    
    "sacrifice": ChessConcept(
        name="Sacrifice",
        category=ChessConceptCategory.TACTICAL,
        description="Voluntarily giving up material for compensation",
        typical_signs=[
            "Material imbalance after the move",
            "Evaluation remains good despite material loss",
            "Compensation in attack, activity, or position"
        ],
        how_to_explain="Explain what is given up and what is gained. Compensation types: "
                       "1) Attacking chances 2) King safety destruction 3) Piece activity "
                       "4) Pawn structure damage 5) Development lead",
        common_patterns=[
            "Greek gift (Bxh7+)", "Exchange sacrifice (Rxc3)", 
            "Queen sacrifice for mate", "Positional exchange sacrifice"
        ],
    ),
    
    "zwischenzug": ChessConcept(
        name="Zwischenzug (Intermediate Move)",
        category=ChessConceptCategory.TACTICAL,
        description="An 'in-between' move that interrupts an expected sequence",
        typical_signs=[
            "Instead of expected recapture, a threat is made",
            "Often a check or attack on queen",
            "Changes the evaluation of the sequence"
        ],
        how_to_explain="Before the 'obvious' recapture, there's a stronger move. "
                       "Explain what was expected and how the intermediate move improves.",
    ),
    
    "desperado": ChessConcept(
        name="Desperado",
        category=ChessConceptCategory.TACTICAL,
        description="A piece that's about to be lost captures something first",
        typical_signs=[
            "Piece is attacked and will be lost",
            "Before being captured, it takes something",
            "Maximizes the value gotten from a doomed piece"
        ],
        how_to_explain="Since the piece is lost anyway, it goes down swinging "
                       "by capturing the most valuable thing it can first.",
    ),
    
    "back_rank_mate": ChessConcept(
        name="Back Rank Mate",
        category=ChessConceptCategory.TACTICAL,
        description="Checkmate delivered on the back rank when the king is trapped by its own pawns",
        typical_signs=[
            "King on back rank with no escape squares",
            "Own pawns blocking king's escape",
            "Rook or queen delivering mate"
        ],
        how_to_explain="The king is trapped on the back rank by its own pieces/pawns. "
                       "A rook or queen delivers mate because there's no escape.",
    ),
    
    # =========================================================================
    # STRATEGIC CONCEPTS
    # =========================================================================
    
    "development": ChessConcept(
        name="Development",
        category=ChessConceptCategory.STRATEGIC,
        description="Getting pieces off starting squares to active positions",
        typical_signs=[
            "Pieces moving from back rank",
            "Knights to c3/f3 or c6/f6",
            "Bishops to active diagonals",
            "King castled for safety"
        ],
        how_to_explain="Chess is a battle - you need your army in the fight. "
                       "Each piece that hasn't moved is essentially 'missing' from the game. "
                       "Count developed pieces vs opponent to show the lead.",
    ),
    
    "tempo": ChessConcept(
        name="Tempo",
        category=ChessConceptCategory.STRATEGIC,
        description="A unit of time (one move); gaining or losing tempo",
        typical_signs=[
            "Moves that force opponent to react",
            "Attacks that develop while threatening",
            "Opponent moving same piece twice"
        ],
        how_to_explain="Every move counts. Explain how this move 'gains time' by "
                       "forcing a response, or 'loses time' by moving without purpose. "
                       "Compare to achieving two things with one move.",
    ),
    
    "initiative": ChessConcept(
        name="Initiative",
        category=ChessConceptCategory.STRATEGIC,
        description="Having control of the action; forcing opponent to react",
        typical_signs=[
            "Creating threats with every move",
            "Opponent constantly defending",
            "Piece activity advantage"
        ],
        how_to_explain="The player with initiative is 'driving' the game. "
                       "They create threats that must be answered, while the defender "
                       "cannot execute their own plans.",
    ),
    
    "piece_activity": ChessConcept(
        name="Piece Activity",
        category=ChessConceptCategory.STRATEGIC,
        description="How actively placed a piece is; mobility and influence",
        typical_signs=[
            "Pieces controlling many squares",
            "Pieces on outposts",
            "Coordinated piece placement"
        ],
        how_to_explain="An active piece does work; a passive piece is just sitting there. "
                       "Count squares controlled, discuss piece coordination. "
                       "'This bishop is active on the long diagonal vs that one blocked by pawns.'",
    ),
    
    "space_advantage": ChessConcept(
        name="Space Advantage",
        category=ChessConceptCategory.STRATEGIC,
        description="Controlling more squares, especially in the center and enemy territory",
        typical_signs=[
            "Pawns advanced past the 4th rank",
            "Pieces operating in enemy half",
            "Opponent cramped with limited mobility"
        ],
        how_to_explain="More space = more room for pieces to maneuver. "
                       "The side with space can reorganize pieces easily; "
                       "the cramped side struggles to coordinate.",
    ),
    
    "outpost": ChessConcept(
        name="Outpost",
        category=ChessConceptCategory.STRATEGIC,
        description="A square where a piece (usually knight) cannot be attacked by enemy pawns",
        typical_signs=[
            "No enemy pawns on adjacent files",
            "Square is defended by a pawn",
            "Usually in enemy territory"
        ],
        how_to_explain="An outpost is a 'safe house' for a piece, especially knights. "
                       "Once established, the piece dominates because it can't be chased away "
                       "by pawns and must be traded (if possible).",
    ),
    
    "weak_squares": ChessConcept(
        name="Weak Squares",
        category=ChessConceptCategory.STRATEGIC,
        description="Squares that cannot be defended by pawns",
        typical_signs=[
            "Pawns moved/traded from adjacent files",
            "Enemy pieces can occupy without pawn challenge",
            "Often light-square or dark-square complex"
        ],
        how_to_explain="Once a pawn moves, the squares it used to defend become 'holes'. "
                       "These squares become targets for opponent's pieces, especially knights.",
    ),
    
    "pawn_structure": ChessConcept(
        name="Pawn Structure",
        category=ChessConceptCategory.STRATEGIC,
        description="The arrangement of pawns; determines positional character",
        typical_signs=[
            "Isolated pawns (no pawns on adjacent files)",
            "Doubled pawns (two pawns on same file)",
            "Pawn chains (diagonal pawn formation)",
            "Backward pawns (can't advance safely)"
        ],
        how_to_explain="Pawns are the 'skeleton' of the position. They determine "
                       "which squares are strong/weak, where pieces belong, and long-term plans. "
                       "Explain specific weaknesses and how to exploit them.",
    ),
    
    "open_file": ChessConcept(
        name="Open File",
        category=ChessConceptCategory.STRATEGIC,
        description="A file with no pawns; ideal for rooks",
        typical_signs=[
            "No pawns on the file",
            "Rooks can penetrate to 7th/8th rank",
            "Control of the file matters"
        ],
        how_to_explain="Rooks need open files to be effective. An open file is like "
                       "a highway for rooks to invade the enemy position, especially "
                       "the 7th rank where they attack pawns and restrict the king.",
    ),
    
    "prophylaxis": ChessConcept(
        name="Prophylaxis",
        category=ChessConceptCategory.STRATEGIC,
        description="Preventing opponent's plans before they happen",
        typical_signs=[
            "Move that doesn't seem to do much",
            "Blocks a key opponent plan",
            "Improves own position while preventing counterplay"
        ],
        how_to_explain="Ask: 'What does the opponent WANT to do?' Then prevent it. "
                       "The prophylactic move may look passive but it stops a strong threat "
                       "before it materializes.",
    ),
    
    # =========================================================================
    # POSITIONAL CONCEPTS
    # =========================================================================
    
    "good_bad_bishop": ChessConcept(
        name="Good vs Bad Bishop",
        category=ChessConceptCategory.POSITIONAL,
        description="A bishop blocked by its own pawns vs one with open diagonals",
        typical_signs=[
            "Pawns on same color as bishop (bad)",
            "Pawns on opposite color (good)",
            "Bishop's mobility and scope"
        ],
        how_to_explain="A bishop needs open diagonals. If your pawns are on the same "
                       "color squares as your bishop, it's 'bad' - blocked by its own army. "
                       "A 'good' bishop has clear diagonals over the pawns.",
    ),
    
    "bishop_pair": ChessConcept(
        name="Bishop Pair Advantage",
        category=ChessConceptCategory.POSITIONAL,
        description="Having both bishops vs opponent with bishop and knight",
        typical_signs=[
            "Both bishops present",
            "Opponent traded one bishop",
            "Open position with long diagonals"
        ],
        how_to_explain="Two bishops cover all 64 squares; they're especially strong in "
                       "open positions. Worth about half a pawn in most positions. "
                       "They work together to create threats on both color complexes.",
    ),
    
    "piece_coordination": ChessConcept(
        name="Piece Coordination",
        category=ChessConceptCategory.POSITIONAL,
        description="Pieces working together toward a common goal",
        typical_signs=[
            "Pieces protecting each other",
            "Pieces attacking the same target",
            "Harmonious piece placement"
        ],
        how_to_explain="Chess pieces are stronger together. Show how pieces support "
                       "each other: one attacks, another defends, a third cuts off escape. "
                       "Contrast with disconnected pieces that don't work as a team.",
    ),
    
    "king_safety": ChessConcept(
        name="King Safety",
        category=ChessConceptCategory.POSITIONAL,
        description="Protection level of the king",
        typical_signs=[
            "Pawn shield intact",
            "King castled (usually)",
            "Enemy pieces near vs far from king"
        ],
        how_to_explain="The king must be protected - if it falls, game over. "
                       "Discuss pawn shield, piece defenders, and how many attackers "
                       "are aimed at the king. Evaluate trade-offs (e.g., h3 weakens shield but prevents Bg4).",
    ),
    
    "centralization": ChessConcept(
        name="Centralization",
        category=ChessConceptCategory.POSITIONAL,
        description="Placing pieces in the center for maximum influence",
        typical_signs=[
            "Pieces on or near d4, d5, e4, e5",
            "Control of central squares",
            "Pieces radiating influence from center"
        ],
        how_to_explain="The center is the crossroads of the board. A centralized piece "
                       "can quickly reach both flanks. Compare 'a knight on the rim is dim' "
                       "vs a knight on e5 controlling 8 squares.",
    ),
    
    # =========================================================================
    # ENDGAME CONCEPTS
    # =========================================================================
    
    "king_activity": ChessConcept(
        name="King Activity (Endgame)",
        category=ChessConceptCategory.ENDGAME,
        description="Active king participation in the endgame",
        typical_signs=[
            "King leaving shelter",
            "King moving toward center/action",
            "Few pieces remaining"
        ],
        how_to_explain="In the endgame, the king becomes a fighting piece! "
                       "It should move toward the action - attack pawns, support its own pawns, "
                       "control key squares. A passive king often loses.",
    ),
    
    "passed_pawn": ChessConcept(
        name="Passed Pawn",
        category=ChessConceptCategory.ENDGAME,
        description="A pawn with no enemy pawns blocking or able to capture it",
        typical_signs=[
            "No enemy pawns on same or adjacent files ahead",
            "Path to promotion is 'clear'",
            "Often the decisive factor in endgames"
        ],
        how_to_explain="A passed pawn is a 'criminal' that must be watched. "
                       "It can promote to a queen if not stopped. The closer to promotion, "
                       "the more valuable. Passed pawns must be pushed or blockaded!",
    ),
    
    "opposition": ChessConcept(
        name="Opposition",
        category=ChessConceptCategory.ENDGAME,
        description="Kings face each other with odd squares between; who has to move loses",
        typical_signs=[
            "King and pawn endgame",
            "Kings facing each other",
            "One side must give way"
        ],
        how_to_explain="In king-pawn endgames, the side with 'opposition' (not having to move) "
                       "can force the other king to step aside. This tiny advantage often "
                       "decides if a pawn can promote.",
    ),
    
    "zugzwang": ChessConcept(
        name="Zugzwang",
        category=ChessConceptCategory.ENDGAME,
        description="A position where any move worsens the position",
        typical_signs=[
            "Endgame (usually)",
            "All moves are bad",
            "If it weren't for having to move, position would be fine"
        ],
        how_to_explain="'Zugzwang' is German for 'compulsion to move.' "
                       "Every legal move makes things worse, but you MUST move. "
                       "The goal is to put your opponent in zugzwang.",
    ),
}


def get_concept_explanation(concept_name: str) -> Optional[ChessConcept]:
    """Get the teaching framework for a chess concept."""
    return CHESS_CONCEPTS.get(concept_name.lower().replace(' ', '_'))


def get_all_tactical_concepts() -> List[ChessConcept]:
    """Get all tactical concepts for pattern matching."""
    return [c for c in CHESS_CONCEPTS.values() if c.category == ChessConceptCategory.TACTICAL]


def get_all_strategic_concepts() -> List[ChessConcept]:
    """Get all strategic concepts."""
    return [c for c in CHESS_CONCEPTS.values() if c.category == ChessConceptCategory.STRATEGIC]


def get_relevant_concepts_for_intent(intent: str) -> List[ChessConcept]:
    """Given a move intent, return relevant concepts to explain."""
    intent_to_concepts = {
        'attack': ['sacrifice', 'initiative', 'king_safety', 'piece_activity'],
        'defense': ['prophylaxis', 'king_safety', 'pin', 'piece_coordination'],
        'development': ['development', 'tempo', 'piece_activity', 'centralization'],
        'material_gain': ['fork', 'pin', 'skewer', 'discovered_attack', 'double_attack'],
        'sacrifice': ['sacrifice', 'initiative', 'piece_activity', 'king_safety'],
        'control': ['space_advantage', 'outpost', 'centralization', 'pawn_structure'],
    }
    
    concept_names = intent_to_concepts.get(intent.lower(), [])
    return [CHESS_CONCEPTS[name] for name in concept_names if name in CHESS_CONCEPTS]


# =============================================================================
# BRIDGE TO CHESS_FUNDAMENTALS
# For new code, prefer using chess_fundamentals.py directly.
# These helpers provide compatibility with code using this module.
# =============================================================================

def get_fundamental_as_concept(name: str) -> Optional[ChessConcept]:
    """
    Get a ChessFundamental from chess_fundamentals.py and convert to legacy ChessConcept.
    
    This bridges the new comprehensive fundamentals library with legacy code
    expecting ChessConcept objects.
    """
    fundamental = get_fundamental(name)
    if not fundamental:
        return None
    
    # Map ConceptCategory to ChessConceptCategory
    category_map = {
        ConceptCategory.TACTICAL: ChessConceptCategory.TACTICAL,
        ConceptCategory.POSITIONAL: ChessConceptCategory.POSITIONAL,
        ConceptCategory.ENDGAME: ChessConceptCategory.ENDGAME,
        ConceptCategory.OPENING: ChessConceptCategory.OPENING,
        ConceptCategory.PIECE_PLACEMENT: ChessConceptCategory.STRATEGIC,
        ConceptCategory.PAWN_STRUCTURE: ChessConceptCategory.STRATEGIC,
        ConceptCategory.KING_SAFETY: ChessConceptCategory.TACTICAL,
        ConceptCategory.ATTACKING: ChessConceptCategory.TACTICAL,
        ConceptCategory.DEFENSIVE: ChessConceptCategory.STRATEGIC,
        ConceptCategory.STRATEGIC: ChessConceptCategory.STRATEGIC,
    }
    
    return ChessConcept(
        name=fundamental.name,
        category=category_map.get(fundamental.category, ChessConceptCategory.STRATEGIC),
        description=fundamental.definition,
        typical_signs=fundamental.how_to_recognize,
        how_to_explain=fundamental.why_it_matters,
        common_patterns=fundamental.how_to_apply[:3] if fundamental.how_to_apply else [],
    )


def get_all_concept_names() -> List[str]:
    """
    Get all concept names from both legacy CHESS_CONCEPTS and new ALL_FUNDAMENTALS.
    
    Returns a unified list of all available concept names.
    """
    legacy_names = set(CHESS_CONCEPTS.keys())
    fundamental_names = set(ALL_FUNDAMENTALS.keys())
    return sorted(legacy_names | fundamental_names)


# =============================================================================
# EXPLANATION TEMPLATES
# =============================================================================

EXPLANATION_TEMPLATES = {
    # For good moves
    "best_move_tactical": 
        "{move} is the strongest move because it {tactic} ({tactical_details}). "
        "The evaluation improves to {eval} because {reason}.",
    
    "best_move_strategic":
        "{move} is the best choice here, improving {aspect} "
        "({improvement_details}). The position is now {eval_description}.",
    
    "sacrifice_with_compensation":
        "{move} sacrifices {material} for {compensation_type}. "
        "Although material is down, {compensation_details}. "
        "Stockfish evaluates this as {eval} because {reason}.",
    
    # For bad moves
    "mistake_tactical":
        "{move} is a mistake because it allows {refutation}, which {consequence}. "
        "Better was {best_move} which would have {best_move_benefit}.",
    
    "mistake_positional":
        "{move} is inaccurate because it {weakness_created}. "
        "The evaluation drops from {eval_before} to {eval_after}. "
        "Instead, {best_move} was better because {best_move_reason}.",
    
    "blunder_material":
        "{move} loses material to {refutation}. "
        "This {loss_description}. The position goes from {eval_before} to {eval_after}.",
    
    # For instructive explanations
    "concept_introduction":
        "This position features a {concept_name}: {concept_definition}. "
        "Here, {specific_application}.",
    
    "why_this_over_that":
        "Why {chosen_move} instead of {alternative}? "
        "{chosen_move} {chosen_benefit}, while {alternative} {alternative_weakness}.",
}


def format_explanation(template_key: str, **kwargs) -> str:
    """Format an explanation using a template."""
    template = EXPLANATION_TEMPLATES.get(template_key, "{move} is a chess move.")
    try:
        return template.format(**kwargs)
    except KeyError as e:
        return f"Explanation: {kwargs.get('move', 'This move')} - {kwargs}"


# =============================================================================
# EVALUATION DESCRIPTIONS
# NOTE: These functions provide backward compatibility. The canonical versions
# are now in llm_prompts.py. These wrappers have slightly different signatures
# and output formatting to maintain compatibility with existing code.
# =============================================================================

def describe_evaluation(eval_cp: float) -> str:
    """
    Convert a centipawn evaluation to human description.
    
    NOTE: For new code, prefer describe_eval() from llm_prompts.py.
    This function is maintained for backward compatibility with a more
    detailed output format.
    
    Args:
        eval_cp: Evaluation in pawns (positive = white better)
        
    Returns:
        Human-readable description
    """
    abs_eval = abs(eval_cp)
    color = "White" if eval_cp > 0 else "Black"
    
    if abs_eval < 0.15:
        return "Equal position"
    elif abs_eval < 0.5:
        return f"Slight edge for {color}"
    elif abs_eval < 1.0:
        return f"Clear advantage for {color}"
    elif abs_eval < 2.0:
        return f"Significant advantage for {color}"
    elif abs_eval < 3.5:
        return f"Winning advantage for {color}"
    elif abs_eval < 10:
        return f"Completely winning for {color}"
    elif abs_eval >= 90:  # Mate score
        return f"Forced mate for {color}"
    else:
        return f"Decisive advantage for {color}"


def describe_eval_change(before: float, after: float, mover_is_white: bool) -> str:
    """
    Describe the evaluation change after a move.
    
    NOTE: For new code, prefer describe_eval_change() from llm_prompts.py.
    This function takes an additional mover_is_white parameter for more
    nuanced descriptions from the player's perspective.
    
    Args:
        before: Eval before move (from white's perspective)
        after: Eval after move (from white's perspective)
        mover_is_white: True if white made the move
        
    Returns:
        Description of what happened
    """
    # Positive change is good for the mover
    if mover_is_white:
        change = after - before
    else:
        change = before - after  # For black, lower is better
    
    abs_change = abs(change)
    
    if abs_change < 0.1:
        return "maintains the position"
    elif abs_change < 0.3:
        return "is a slight improvement"
    elif abs_change < 0.5:
        return "is a good move"
    elif abs_change < 1.0:
        return "is an excellent move, gaining significant advantage"
    elif change < 0 and abs_change >= 0.5:
        if abs_change < 1.0:
            return "is an inaccuracy, giving up some advantage"
        elif abs_change < 2.0:
            return "is a mistake, significantly worsening the position"
        else:
            return "is a blunder, giving away the game"
    else:
        return "dramatically changes the position"


def describe_material(pieces: dict) -> str:
    """Convert piece dictionary to readable material description."""
    piece_names = {
        'pawn': 'pawn', 'knight': 'knight', 'bishop': 'bishop',
        'rook': 'rook', 'queen': 'queen'
    }
    
    parts = []
    for piece, count in pieces.items():
        if count > 0:
            name = piece_names.get(piece.lower(), piece)
            if count > 1:
                name += 's'
            parts.append(f"{count} {name}")
    
    return ', '.join(parts) if parts else "no pieces"
