"""
Chess Fundamentals Library - Comprehensive chess concepts from training resources.

Based on Lichess training modules, chess pedagogy, and foundational principles.
These concepts help the LLM explain positions and moves accurately.

Categories:
1. Opening Principles
2. Piece Placement & Activity
3. Pawn Structure
4. King Safety
5. Attacking Principles
6. Defensive Principles
7. Positional Concepts
8. Endgame Fundamentals
9. Tactical Motifs
10. Strategic Themes
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional
from enum import Enum


class ConceptCategory(Enum):
    """Categories of chess concepts."""
    OPENING = "opening_principles"
    PIECE_PLACEMENT = "piece_placement"
    PAWN_STRUCTURE = "pawn_structure"
    KING_SAFETY = "king_safety"
    ATTACKING = "attacking_principles"
    DEFENSIVE = "defensive_principles"
    POSITIONAL = "positional_concepts"
    ENDGAME = "endgame_fundamentals"
    TACTICAL = "tactical_motifs"
    STRATEGIC = "strategic_themes"


@dataclass
class ChessFundamental:
    """A foundational chess concept with teaching context."""
    name: str
    category: ConceptCategory
    definition: str
    why_it_matters: str
    how_to_recognize: List[str]
    how_to_apply: List[str]
    common_mistakes: List[str] = field(default_factory=list)
    related_concepts: List[str] = field(default_factory=list)
    example_explanation: str = ""


# =============================================================================
# OPENING PRINCIPLES
# =============================================================================

OPENING_PRINCIPLES = {
    "control_the_center": ChessFundamental(
        name="Control the Center",
        category=ConceptCategory.OPENING,
        definition="Occupying or controlling the central squares (e4, d4, e5, d5) with pawns and pieces.",
        why_it_matters="Central pieces have maximum mobility and can quickly reach either flank. A piece in the center controls more squares than one on the edge.",
        how_to_recognize=[
            "Pawns on e4/d4 (white) or e5/d5 (black)",
            "Pieces attacking or defending central squares",
            "Knights on c3/f3 or c6/f6 controlling center",
        ],
        how_to_apply=[
            "Open with 1.e4 or 1.d4 to stake a central claim",
            "Develop pieces toward the center, not the rim",
            "Challenge opponent's center if they control it",
        ],
        common_mistakes=[
            "Moving too many pawns in the opening",
            "Developing pieces to passive squares",
            "Ignoring the center to attack on the flank",
        ],
        related_concepts=["development", "piece_activity", "space_advantage"],
        example_explanation="White's e4 and d4 pawns control the center, giving pieces like the knights maximum influence. Black should challenge this with moves like ...d5 or ...e5.",
    ),
    
    "develop_pieces": ChessFundamental(
        name="Develop Your Pieces",
        category=ConceptCategory.OPENING,
        definition="Moving pieces from their starting squares to active positions where they control key squares and are ready to participate in the game.",
        why_it_matters="Undeveloped pieces aren't participating. Each piece left on its starting square is essentially 'missing' from the battle. Development leads to better piece coordination and faster attacks.",
        how_to_recognize=[
            "Knights moved to c3/f3 or c6/f6",
            "Bishops on active diagonals",
            "Rooks connected on the back rank",
            "Queen not out too early but not blocked in",
        ],
        how_to_apply=[
            "Move each piece once before moving any piece twice",
            "Develop knights before bishops (usually)",
            "Don't bring the queen out too early",
            "Connect your rooks by castling and clearing the back rank",
        ],
        common_mistakes=[
            "Moving the same piece multiple times",
            "Bringing the queen out early to grab pawns",
            "Developing pieces to passive squares",
            "Neglecting to castle",
        ],
        related_concepts=["tempo", "piece_activity", "castling"],
        example_explanation="White has developed 4 pieces while Black has only 2. This development advantage means White can start an attack or seize the initiative.",
    ),
    
    "king_safety_opening": ChessFundamental(
        name="Castle Early",
        category=ConceptCategory.OPENING,
        definition="Moving the king to safety via castling, typically within the first 10 moves.",
        why_it_matters="The king in the center is vulnerable to attacks and can block your rooks. Castling connects the rooks and tucks the king behind a pawn shield.",
        how_to_recognize=[
            "King still on e1/e8 after 10+ moves (dangerous)",
            "Open central files with uncastled king (very dangerous)",
            "Pieces developed but king hasn't castled yet",
        ],
        how_to_apply=[
            "Clear pieces between king and rook",
            "Castle kingside (short) in most positions",
            "Castle queenside when planning a kingside attack",
            "Don't delay castling without good reason",
        ],
        common_mistakes=[
            "Waiting too long to castle",
            "Castling into an attack",
            "Moving pawns in front of castled king unnecessarily",
        ],
        related_concepts=["king_safety", "pawn_shield", "open_files"],
        example_explanation="Black hasn't castled and the e-file is open. White can pressure the king with Re1, exploiting Black's delayed development.",
    ),
    
    "dont_move_pawns_unnecessarily": ChessFundamental(
        name="Don't Move Pawns Unnecessarily",
        category=ConceptCategory.OPENING,
        definition="Avoiding excessive pawn moves in the opening that don't contribute to development or center control.",
        why_it_matters="Pawns can't move backward. Every pawn move creates weaknesses and uses tempo that could develop pieces.",
        how_to_recognize=[
            "Multiple flank pawn moves (a3, h3, b4) before development",
            "Pawn moves that don't attack or control the center",
            "Pawns pushed without a clear purpose",
        ],
        how_to_apply=[
            "Limit opening pawn moves to 2-3 central pawns",
            "Only move flank pawns if necessary (preventing Bg5 with h3)",
            "Develop pieces before pushing pawns further",
        ],
        common_mistakes=[
            "Playing h3 and a3 'to prevent pins' before developing",
            "Pushing pawns to attack when pieces aren't developed",
            "Creating holes in your position with careless pawn moves",
        ],
        related_concepts=["tempo", "weak_squares", "pawn_structure"],
    ),
    
    "dont_bring_queen_out_early": ChessFundamental(
        name="Don't Bring the Queen Out Early",
        category=ConceptCategory.OPENING,
        definition="Avoiding early queen development that can be exploited by opponent's developing moves with tempo.",
        why_it_matters="The queen is too valuable to risk. Opponent can develop pieces while attacking your queen, gaining time.",
        how_to_recognize=[
            "Queen on h5/a5 in first 5 moves",
            "Queen being chased around by developing pieces",
            "Wasted moves retreating the queen",
        ],
        how_to_apply=[
            "Develop minor pieces (knights, bishops) first",
            "Only bring the queen out when it can't be attacked with tempo",
            "Exception: Scholar's mate threats (but these are easily defended)",
        ],
        common_mistakes=[
            "Qh5 trying for scholar's mate",
            "Moving the queen multiple times in the opening",
            "Grabbing pawns with the queen at the cost of development",
        ],
        related_concepts=["tempo", "development", "piece_activity"],
    ),
}

# =============================================================================
# PIECE PLACEMENT & ACTIVITY
# =============================================================================

PIECE_PLACEMENT = {
    "piece_activity": ChessFundamental(
        name="Piece Activity",
        category=ConceptCategory.PIECE_PLACEMENT,
        definition="How effectively a piece controls squares and participates in the position. Active pieces do work; passive pieces sit idle.",
        why_it_matters="A piece that controls many squares is worth more than its material value suggests. Active pieces create threats; passive pieces only defend.",
        how_to_recognize=[
            "Count squares the piece attacks",
            "Is the piece blocked by its own pawns?",
            "Can the piece reach important squares quickly?",
            "Is the piece defending or attacking?",
        ],
        how_to_apply=[
            "Place pieces on open lines and diagonals",
            "Avoid putting pieces where your pawns block them",
            "Improve your worst-placed piece",
            "Trade passive pieces for active ones when possible",
        ],
        common_mistakes=[
            "Leaving a piece passive because it's 'safe'",
            "Not recognizing a piece is badly placed",
            "Trading active pieces for passive ones",
        ],
        related_concepts=["centralization", "outposts", "piece_coordination"],
        example_explanation="White's bishop on g2 is 'biting on granite' - blocked by the pawn chain. Black's bishop on c5 is active, pressuring f2.",
    ),
    
    "centralization": ChessFundamental(
        name="Centralization",
        category=ConceptCategory.PIECE_PLACEMENT,
        definition="Placing pieces in or near the center where they have maximum influence over the board.",
        why_it_matters="A centralized piece can reach both flanks quickly. A knight on e5 controls 8 squares; on a1 it controls only 2.",
        how_to_recognize=[
            "Pieces on d4, d5, e4, e5",
            "Knights particularly powerful when centralized",
            "Rooks on central files (d-file, e-file)",
        ],
        how_to_apply=[
            "Knights love outposts in the center",
            "Rooks belong on open central files",
            "Even the king centralizes in the endgame",
        ],
        common_mistakes=[
            "'A knight on the rim is dim' - knights on a/h files",
            "Decentralizing pieces without good reason",
            "Ignoring central squares",
        ],
        related_concepts=["control_the_center", "outposts", "piece_activity"],
        example_explanation="The knight on e5 is powerfully centralized - it attacks 8 squares and can't easily be driven away. Black should challenge it or trade it.",
    ),
    
    "outposts": ChessFundamental(
        name="Outposts",
        category=ConceptCategory.PIECE_PLACEMENT,
        definition="A square where a piece (usually a knight) can be placed without being attacked by enemy pawns.",
        why_it_matters="A piece on an outpost is like a permanent fixture - it can't be chased away by pawns. Knights especially love outposts because they can't be attacked by bishops.",
        how_to_recognize=[
            "No enemy pawns on adjacent files that could attack",
            "Often created after a pawn exchange",
            "Usually in the opponent's half of the board",
            "Ideally protected by a friendly pawn",
        ],
        how_to_apply=[
            "Create outposts by exchanging pawns",
            "Place a knight on the outpost",
            "Support the outpost with a pawn if possible",
            "Use outpost as a base for operations",
        ],
        common_mistakes=[
            "Not recognizing outpost opportunities",
            "Using a bishop instead of knight on outpost",
            "Allowing opponent to create outposts in your position",
        ],
        related_concepts=["weak_squares", "piece_activity", "pawn_structure"],
        example_explanation="After ...dxe5, the d5 square becomes an outpost. White should occupy it with a knight - it can never be attacked by Black's pawns.",
    ),
    
    "piece_coordination": ChessFundamental(
        name="Piece Coordination",
        category=ConceptCategory.PIECE_PLACEMENT,
        definition="Multiple pieces working together toward a common goal, supporting each other's actions.",
        why_it_matters="Coordinated pieces are more powerful than the sum of their parts. A lone queen might be stopped; a queen supported by bishop and knight is deadly.",
        how_to_recognize=[
            "Pieces defending each other",
            "Multiple pieces attacking the same target",
            "Rooks doubled on a file",
            "Bishop and queen on the same diagonal",
        ],
        how_to_apply=[
            "Look for piece batteries (rook + queen, bishop + queen)",
            "Support attacking pieces with defenders",
            "Connect your rooks",
            "Avoid having pieces that can't help each other",
        ],
        common_mistakes=[
            "Attacking with one piece while others watch",
            "Pieces that don't work together",
            "Leaving pieces uncoordinated and vulnerable",
        ],
        related_concepts=["piece_activity", "attacking_principles", "battery"],
    ),
    
    "bad_bishop": ChessFundamental(
        name="Good Bishop vs Bad Bishop",
        category=ConceptCategory.PIECE_PLACEMENT,
        definition="A bad bishop is blocked by its own pawns (on the same color squares). A good bishop has open diagonals over the pawn chain.",
        why_it_matters="A bad bishop is essentially a tall pawn - it's blocked by its own army. A good bishop can be worth more than a knight.",
        how_to_recognize=[
            "Pawns on same color as the bishop (bad)",
            "Pawns on opposite color (good)",
            "Can the bishop move freely or is it blocked?",
        ],
        how_to_apply=[
            "Put pawns on opposite color from your bishop",
            "Trade a bad bishop for opponent's good one",
            "Activate a bad bishop by placing it outside the pawn chain",
        ],
        common_mistakes=[
            "Blocking your own bishop with pawns",
            "Keeping a bad bishop when you could trade it",
            "Not recognizing when your bishop is bad",
        ],
        related_concepts=["pawn_structure", "bishop_pair", "piece_activity"],
        example_explanation="White's light-squared bishop is 'bad' - all pawns are on light squares, blocking its diagonals. Black's dark-squared bishop roams freely.",
    ),
    
    "bishop_pair": ChessFundamental(
        name="The Bishop Pair",
        category=ConceptCategory.PIECE_PLACEMENT,
        definition="Having both bishops when the opponent has traded one (usually bishop vs knight). The two bishops cover all 64 squares.",
        why_it_matters="Two bishops work together to control both color complexes. They're especially strong in open positions with long diagonals. Worth approximately +0.5 pawns.",
        how_to_recognize=[
            "You have both bishops, opponent has bishop + knight",
            "Open position with few pawns",
            "Long diagonals available",
        ],
        how_to_apply=[
            "Keep the position open (don't block diagonals)",
            "Avoid trading one of your bishops",
            "Use bishops to attack on both flanks",
        ],
        common_mistakes=[
            "Trading one bishop unnecessarily",
            "Blocking your own bishops with pawns",
            "Not opening the position to maximize bishop power",
        ],
        related_concepts=["bad_bishop", "piece_activity", "open_position"],
    ),
    
    "knights_vs_bishops": ChessFundamental(
        name="Knights vs Bishops",
        category=ConceptCategory.PIECE_PLACEMENT,
        definition="Understanding when knights are better than bishops and vice versa.",
        why_it_matters="Knights excel in closed positions with outposts. Bishops excel in open positions with long diagonals. Trading the wrong piece can cost the game.",
        how_to_recognize=[
            "Closed position with many pawns → knights better",
            "Open position with few pawns → bishops better",
            "Fixed pawn structure → depends on outposts",
            "Both flanks active → bishops can switch sides faster",
        ],
        how_to_apply=[
            "In closed positions, keep your knights",
            "In open positions, keep your bishops",
            "Create the structure that favors your pieces",
        ],
        common_mistakes=[
            "Trading a bishop for knight in an open position",
            "Trading a knight for bishop in a closed position",
            "Not considering the position type when trading",
        ],
        related_concepts=["bishop_pair", "outposts", "pawn_structure"],
    ),
    
    "rooks_on_open_files": ChessFundamental(
        name="Rooks on Open Files",
        category=ConceptCategory.PIECE_PLACEMENT,
        definition="Placing rooks on files with no pawns (open) or only enemy pawns (semi-open).",
        why_it_matters="Rooks need open lines to be effective. On an open file, a rook can penetrate to the 7th rank and attack pawns and restrict the king.",
        how_to_recognize=[
            "Files with no pawns (open file)",
            "Files with only enemy pawns (semi-open)",
            "Opportunity to double rooks on a file",
        ],
        how_to_apply=[
            "After pawn exchanges, occupy the open file",
            "Double rooks on the file for maximum pressure",
            "Aim for the 7th rank (2nd for Black)",
            "Contest open files if opponent controls them",
        ],
        common_mistakes=[
            "Leaving rooks on closed files",
            "Not contesting opponent's control of open files",
            "Failing to double rooks",
        ],
        related_concepts=["seventh_rank", "piece_activity", "rook_lift"],
        example_explanation="The d-file is open. White should play Rd1 to control it before Black can. Doubling with Rad1 and Rfd1 would dominate the file.",
    ),
    
    "seventh_rank": ChessFundamental(
        name="Rook on the 7th Rank",
        category=ConceptCategory.PIECE_PLACEMENT,
        definition="A rook on the 7th rank (2nd for Black) attacking pawns and restricting the enemy king.",
        why_it_matters="A rook on the 7th is often worth an extra pawn. It attacks multiple pawns simultaneously and traps the king on the back rank. Two rooks on the 7th often lead to perpetual check or mate.",
        how_to_recognize=[
            "Rook penetrated to opponent's 2nd rank",
            "Undefended pawns on that rank",
            "King restricted to back rank",
        ],
        how_to_apply=[
            "Use open files to reach the 7th rank",
            "Coordinate a rook on 7th with other pieces",
            "Two rooks on 7th = 'pigs on the 7th' = devastating",
        ],
        common_mistakes=[
            "Not prioritizing entry to the 7th",
            "Trading a rook on the 7th unnecessarily",
            "Not supporting the rook with other pieces",
        ],
        related_concepts=["rooks_on_open_files", "back_rank_mate", "piece_coordination"],
    ),
}

# =============================================================================
# PAWN STRUCTURE
# =============================================================================

PAWN_STRUCTURE = {
    "pawn_structure_basics": ChessFundamental(
        name="Pawn Structure",
        category=ConceptCategory.PAWN_STRUCTURE,
        definition="The arrangement of pawns, which forms the 'skeleton' of the position and determines long-term plans.",
        why_it_matters="Pawns can't move backward. Their structure determines which squares are strong/weak, where pieces belong, and what plans are possible.",
        how_to_recognize=[
            "Fixed pawn chains",
            "Isolated, doubled, or backward pawns",
            "Pawn majorities (more pawns on one side)",
            "Holes in the pawn structure",
        ],
        how_to_apply=[
            "Plan based on pawn structure",
            "Attack the base of pawn chains",
            "Avoid creating permanent weaknesses",
            "Create passed pawns when possible",
        ],
        common_mistakes=[
            "Ignoring pawn structure when planning",
            "Creating weaknesses without compensation",
            "Not exploiting opponent's weak pawns",
        ],
        related_concepts=["isolated_pawn", "doubled_pawns", "passed_pawn"],
    ),
    
    "isolated_pawn": ChessFundamental(
        name="Isolated Pawn",
        category=ConceptCategory.PAWN_STRUCTURE,
        definition="A pawn with no friendly pawns on adjacent files. It cannot be defended by other pawns.",
        why_it_matters="Isolated pawns must be defended by pieces, tying them down. The square in front of an isolated pawn is an outpost for the opponent.",
        how_to_recognize=[
            "No pawns on files next to this pawn",
            "Pawn must be defended by pieces",
            "Square in front of it is weak",
        ],
        how_to_apply=[
            "If you have an IQP: use its dynamic potential - it supports outposts on c5/e5",
            "Against IQP: blockade the square in front, trade pieces, target it in endgame",
            "IQP positions favor the side with more pieces (middlegame)",
        ],
        common_mistakes=[
            "Allowing an isolated pawn without compensation",
            "Not blockading opponent's isolated pawn",
            "Not using the IQP's dynamic strength",
        ],
        related_concepts=["outposts", "weak_squares", "blockade"],
        example_explanation="White has an isolated d4 pawn (IQP). It controls c5 and e5 and can support piece activity. But if pieces get traded, it becomes a target.",
    ),
    
    "doubled_pawns": ChessFundamental(
        name="Doubled Pawns",
        category=ConceptCategory.PAWN_STRUCTURE,
        definition="Two pawns of the same color on the same file, usually created by a capture.",
        why_it_matters="Doubled pawns are usually weak - they can't defend each other and create holes. But they can also open files for rooks.",
        how_to_recognize=[
            "Two pawns stacked on same file",
            "Usually after ...Bxc3 bxc3 type captures",
            "File is now semi-open",
        ],
        how_to_apply=[
            "Accept doubled pawns only for compensation (bishop pair, center control, open file)",
            "Attack doubled pawns as fixed targets",
            "Use the open file created by doubled pawns",
        ],
        common_mistakes=[
            "Creating doubled pawns without compensation",
            "Over-valuing doubled pawns - sometimes they're fine",
            "Not using the half-open file",
        ],
        related_concepts=["pawn_structure", "open_files", "bishop_pair"],
    ),
    
    "backward_pawn": ChessFundamental(
        name="Backward Pawn",
        category=ConceptCategory.PAWN_STRUCTURE,
        definition="A pawn that cannot advance without being captured, and cannot be defended by other pawns.",
        why_it_matters="Backward pawns are targets, and the square in front of them is an outpost for the opponent. They're often worse than isolated pawns.",
        how_to_recognize=[
            "Pawn behind its neighbors",
            "Cannot safely advance",
            "Square in front is weak",
        ],
        how_to_apply=[
            "Avoid creating backward pawns",
            "Attack opponent's backward pawns",
            "Occupy the square in front with a piece",
        ],
        common_mistakes=[
            "Creating a backward pawn",
            "Not blockading opponent's backward pawn",
            "Pushing a backward pawn when it can be captured",
        ],
        related_concepts=["outposts", "weak_squares", "pawn_structure"],
    ),
    
    "passed_pawn": ChessFundamental(
        name="Passed Pawn",
        category=ConceptCategory.PAWN_STRUCTURE,
        definition="A pawn with no enemy pawns in front of it or on adjacent files that could capture it. Nothing can stop it except pieces.",
        why_it_matters="Passed pawns are dangerous because they can promote. 'A passed pawn is a criminal that must be kept under lock and key' - Nimzowitsch.",
        how_to_recognize=[
            "No enemy pawns blocking or able to capture",
            "Clear path to promotion",
            "Often created in the endgame",
        ],
        how_to_apply=[
            "Push passed pawns! They must be stopped",
            "Support passed pawns with pieces",
            "Use passed pawn to distract opponent's pieces",
            "Create passed pawns by exchanging other pawns",
        ],
        common_mistakes=[
            "Not pushing passed pawns",
            "Blockading your own passed pawn",
            "Leaving passed pawns undefended",
        ],
        related_concepts=["pawn_promotion", "endgame", "piece_activity"],
        example_explanation="White's passed d-pawn is a major asset. Black must use a piece to stop it, while White's other pieces are free to attack.",
    ),
    
    "pawn_majority": ChessFundamental(
        name="Pawn Majority",
        category=ConceptCategory.PAWN_STRUCTURE,
        definition="Having more pawns than the opponent on one side of the board (queenside or kingside).",
        why_it_matters="A pawn majority can create a passed pawn by advancing. The side with the majority should push it forward.",
        how_to_recognize=[
            "Count pawns on each wing",
            "3 vs 2 = queenside majority",
            "Mobile vs fixed majority",
        ],
        how_to_apply=[
            "Advance the pawn majority to create a passed pawn",
            "Push the unopposed pawn first",
            "In endgames, majorities are crucial",
        ],
        common_mistakes=[
            "Not using pawn majority",
            "Creating a crippled majority (doubled pawns)",
            "Advancing the wrong pawn first",
        ],
        related_concepts=["passed_pawn", "endgame", "pawn_structure"],
    ),
    
    "pawn_chain": ChessFundamental(
        name="Pawn Chain",
        category=ConceptCategory.PAWN_STRUCTURE,
        definition="A diagonal line of pawns defending each other (e.g., d4-e5-f6).",
        why_it_matters="Pawn chains determine the character of the position. Attack the base (the most backward pawn) to undermine the whole chain.",
        how_to_recognize=[
            "Pawns forming a diagonal",
            "Each pawn defends the next",
            "Common in French Defense, King's Indian",
        ],
        how_to_apply=[
            "Attack the base of opponent's pawn chain",
            "Support your chain's base",
            "Use the chain to control space",
        ],
        common_mistakes=[
            "Attacking the head instead of base",
            "Leaving the base undefended",
            "Not understanding chain dynamics",
        ],
        related_concepts=["space_advantage", "pawn_breaks", "attacking_principles"],
    ),
    
    "pawn_breaks": ChessFundamental(
        name="Pawn Breaks",
        category=ConceptCategory.PAWN_STRUCTURE,
        definition="Advancing a pawn to challenge and exchange against the opponent's pawn structure, opening lines.",
        why_it_matters="Pawn breaks open the position for your pieces. They're essential for activating rooks and creating attacking chances.",
        how_to_recognize=[
            "Typical breaks: c4-c5, d4-d5, f4-f5, e4-e5",
            "Timing is crucial",
            "Opens files and diagonals",
        ],
        how_to_apply=[
            "Prepare pawn breaks with piece support",
            "Time the break when your pieces are ready",
            "Anticipate opponent's counter-breaks",
        ],
        common_mistakes=[
            "Breaking too early without piece support",
            "Missing the right moment for a break",
            "Not preparing the break properly",
        ],
        related_concepts=["open_files", "piece_activity", "attacking_principles"],
        example_explanation="White should prepare the f4-f5 break. After f5, if ...exf5, the e-file opens for the rook. If ...e5, White has more space.",
    ),
}

# =============================================================================
# KING SAFETY
# =============================================================================

KING_SAFETY = {
    "pawn_shield": ChessFundamental(
        name="Pawn Shield",
        category=ConceptCategory.KING_SAFETY,
        definition="The pawns in front of the castled king that protect it from attacks.",
        why_it_matters="Pawns are the first line of defense. A weakened pawn shield (advanced or missing pawns) exposes the king to attacks.",
        how_to_recognize=[
            "Pawns on f2/g2/h2 (kingside castle) intact",
            "Any pawn moved forward creates weaknesses",
            "Missing pawns = exposed king",
        ],
        how_to_apply=[
            "Keep pawn shield intact unless necessary",
            "If pushed, know which squares are weakened",
            "h3/g3 creates dark square weakness; f3 weakens diagonals",
        ],
        common_mistakes=[
            "Pushing pawns in front of king without reason",
            "h3 + g4 type advances exposing the king",
            "Not recognizing when pawn shield is compromised",
        ],
        related_concepts=["king_safety", "attacking_principles", "weak_squares"],
    ),
    
    "king_exposure": ChessFundamental(
        name="King Exposure",
        category=ConceptCategory.KING_SAFETY,
        definition="A king position where it can be attacked by enemy pieces, often due to missing pawns or being in the center.",
        why_it_matters="An exposed king is a target. Attacks on exposed kings often decide games, even when the attacker is down material.",
        how_to_recognize=[
            "King in center with open files",
            "Pawn shield destroyed",
            "Enemy pieces pointing at king",
            "No defenders near the king",
        ],
        how_to_apply=[
            "Attack exposed kings immediately",
            "Sacrifice material to expose the king",
            "Open files toward the enemy king",
        ],
        common_mistakes=[
            "Leaving your own king exposed",
            "Not exploiting opponent's exposed king",
            "Trading attacking pieces when opponent's king is weak",
        ],
        related_concepts=["pawn_shield", "open_files", "attacking_principles"],
    ),
    
    "opposite_side_castling": ChessFundamental(
        name="Opposite Side Castling",
        category=ConceptCategory.KING_SAFETY,
        definition="When one player castles kingside and the other queenside, leading to mutual pawn storms.",
        why_it_matters="With kings on opposite sides, both players attack with pawns. It becomes a race - whoever reaches the enemy king first often wins.",
        how_to_recognize=[
            "White castled kingside, Black queenside (or vice versa)",
            "Both sides pushing pawns toward enemy king",
            "Sharp, tactical positions",
        ],
        how_to_apply=[
            "Attack with pawns - they cost nothing",
            "Open files toward the enemy king",
            "Speed is essential - don't waste moves",
        ],
        common_mistakes=[
            "Being too slow in the attack",
            "Defending instead of attacking",
            "Trading pieces when you should be attacking",
        ],
        related_concepts=["pawn_storm", "attacking_principles", "piece_coordination"],
    ),
}

# =============================================================================
# ATTACKING PRINCIPLES
# =============================================================================

ATTACKING_PRINCIPLES = {
    "attack_with_pieces_first": ChessFundamental(
        name="Bring Pieces to the Attack",
        category=ConceptCategory.ATTACKING,
        definition="Coordinate multiple pieces toward the enemy king before launching the final assault.",
        why_it_matters="A lone piece can't mate. Successful attacks require piece coordination - usually 3+ pieces should participate.",
        how_to_recognize=[
            "Count attacking pieces vs defending pieces",
            "At least 3 pieces should be attacking",
            "Pieces should support each other",
        ],
        how_to_apply=[
            "Don't attack until you have enough pieces",
            "Open lines for your pieces to reach the king",
            "Keep pieces coordinated",
        ],
        common_mistakes=[
            "Attacking with just the queen",
            "Not bringing all pieces into the attack",
            "Attacking prematurely",
        ],
        related_concepts=["piece_coordination", "development", "initiative"],
    ),
    
    "attack_the_weakest_point": ChessFundamental(
        name="Attack the Weakest Point",
        category=ConceptCategory.ATTACKING,
        definition="Concentrate force on the opponent's weakest defended square or piece.",
        why_it_matters="Spreading attacks everywhere is ineffective. Focus firepower on one weakness until it breaks.",
        how_to_recognize=[
            "Squares defended once or not at all",
            "f7/f2 is weak in the opening (only king defends)",
            "Backward pawns, isolated pawns",
            "Undefended pieces",
        ],
        how_to_apply=[
            "Identify the weakest point",
            "Direct pieces toward it",
            "Add attackers until it falls",
        ],
        common_mistakes=[
            "Attacking everywhere instead of concentrating",
            "Not identifying the actual weakness",
            "Giving up the attack too soon",
        ],
        related_concepts=["weak_squares", "piece_coordination", "prophylaxis"],
    ),
    
    "opening_lines": ChessFundamental(
        name="Open Lines Toward the King",
        category=ConceptCategory.ATTACKING,
        definition="Creating open files and diagonals that point at the enemy king.",
        why_it_matters="Pieces need avenues to reach the king. Opening lines is how rooks, queens, and bishops join the attack.",
        how_to_recognize=[
            "Open files pointing at king",
            "Open diagonals toward king",
            "Pawn breaks that open lines",
        ],
        how_to_apply=[
            "Use pawn breaks to open files (f5, h5)",
            "Exchange pawns that block your pieces",
            "Sacrifice pawns to open lines",
        ],
        common_mistakes=[
            "Keeping the position closed when attacking",
            "Opening lines toward your own king",
            "Not using open lines once created",
        ],
        related_concepts=["pawn_breaks", "piece_activity", "rooks_on_open_files"],
    ),
    
    "sacrifice_to_destroy_defense": ChessFundamental(
        name="Sacrifices to Destroy Defenses",
        category=ConceptCategory.ATTACKING,
        definition="Giving up material to remove defenders, break the pawn shield, or expose the king.",
        why_it_matters="Sometimes the only way to break through is to sacrifice. The compensation is the exposed king.",
        how_to_recognize=[
            "Piece sacrifice exposes king",
            "Exchange sacrifice removes key defender",
            "Pawn shield can be destroyed by piece sac",
        ],
        how_to_apply=[
            "Classic: Bxh7+ (sacrifice on h7)",
            "Exchange sacrifice: Rxc3 to destroy defender",
            "Calculate if the attack works after sacrifice",
        ],
        common_mistakes=[
            "Sacrificing without sufficient attacking pieces",
            "Sacrificing when the attack doesn't work",
            "Not considering sacrifices at all",
        ],
        related_concepts=["piece_coordination", "king_exposure", "calculation"],
    ),
}

# =============================================================================
# DEFENSIVE PRINCIPLES
# =============================================================================

DEFENSIVE_PRINCIPLES = {
    "prophylaxis": ChessFundamental(
        name="Prophylaxis (Prevention)",
        category=ConceptCategory.DEFENSIVE,
        definition="Making moves that prevent the opponent's plans before they can be executed.",
        why_it_matters="The best defense is often to stop the attack before it starts. Ask 'What does my opponent want?' and stop it.",
        how_to_recognize=[
            "Opponent has a clear plan",
            "A move prevents that plan",
            "Often looks passive but is very strong",
        ],
        how_to_apply=[
            "Always ask: what does my opponent want?",
            "Prevent breaks before they happen",
            "Stop piece maneuvers before they complete",
        ],
        common_mistakes=[
            "Only thinking about your own plans",
            "Allowing opponent's plan to succeed",
            "Being too aggressive when prophylaxis is needed",
        ],
        related_concepts=["defensive_principles", "piece_placement", "positional_play"],
        example_explanation="Instead of continuing the attack, White plays h3 - prophylaxis against ...Bg4 which would have pinned the knight.",
    ),
    
    "trade_attackers": ChessFundamental(
        name="Trade Attackers",
        category=ConceptCategory.DEFENSIVE,
        definition="When under attack, exchange pieces to reduce the opponent's attacking force.",
        why_it_matters="Fewer pieces = weaker attack. Trading even one attacking piece can defuse a dangerous situation.",
        how_to_recognize=[
            "You're under attack",
            "Can exchange an attacking piece",
            "Trade reduces opponent's coordination",
        ],
        how_to_apply=[
            "Trade queens when under attack",
            "Exchange aggressive pieces",
            "Simplify to reduce danger",
        ],
        common_mistakes=[
            "Trading defenders instead of attackers",
            "Not trading when under attack",
            "Trading pieces that help your defense",
        ],
        related_concepts=["piece_coordination", "simplification", "endgame"],
    ),
    
    "defend_actively": ChessFundamental(
        name="Active Defense",
        category=ConceptCategory.DEFENSIVE,
        definition="Defending while maintaining counterplay and activity rather than just passively blocking.",
        why_it_matters="Passive defense often fails because the attacker can keep adding pressure. Active defense creates counter-threats.",
        how_to_recognize=[
            "Your pieces are defending but also attacking",
            "You have counter-threats",
            "Defense that improves your position",
        ],
        how_to_apply=[
            "Find defensive moves that also attack",
            "Create counter-threats while defending",
            "Don't just retreat - reposition with threats",
        ],
        common_mistakes=[
            "Pure passive defense",
            "Retreating without creating counterplay",
            "Giving up all activity",
        ],
        related_concepts=["piece_activity", "counterplay", "initiative"],
    ),
    
    "blockade": ChessFundamental(
        name="Blockade",
        category=ConceptCategory.DEFENSIVE,
        definition="Placing a piece (usually a knight) in front of an enemy pawn to stop its advance.",
        why_it_matters="A blockaded pawn is frozen. The blockading piece controls the square and makes the pawn harmless.",
        how_to_recognize=[
            "Enemy passed pawn",
            "Square in front can be occupied",
            "Knight is the ideal blockader",
        ],
        how_to_apply=[
            "Place a knight in front of passed pawns",
            "The blockader should be difficult to remove",
            "Blockade early before the pawn advances",
        ],
        common_mistakes=[
            "Not blockading passed pawns",
            "Using a bishop instead of knight (can be driven away)",
            "Blockading too late",
        ],
        related_concepts=["passed_pawn", "outposts", "piece_placement"],
    ),
}

# =============================================================================
# POSITIONAL CONCEPTS
# =============================================================================

POSITIONAL_CONCEPTS = {
    "space_advantage": ChessFundamental(
        name="Space Advantage",
        category=ConceptCategory.POSITIONAL,
        definition="Controlling more territory on the board, particularly with advanced pawns.",
        why_it_matters="More space = more room for pieces to maneuver. The cramped side struggles to reorganize.",
        how_to_recognize=[
            "Pawns advanced past the 4th rank",
            "Opponent's pieces cramped",
            "More squares available for your pieces",
        ],
        how_to_apply=[
            "Gain space with pawn advances",
            "Restrict opponent's pieces",
            "Use space to maneuver pieces to better squares",
        ],
        common_mistakes=[
            "Overextending (pawns too far forward)",
            "Not using space advantage",
            "Allowing opponent to break through",
        ],
        related_concepts=["pawn_structure", "piece_activity", "control_the_center"],
    ),
    
    "weak_squares": ChessFundamental(
        name="Weak Squares",
        category=ConceptCategory.POSITIONAL,
        definition="Squares that cannot be defended by pawns, usually created by pawn moves.",
        why_it_matters="Weak squares are permanent outposts for enemy pieces. Once created, they can't be fixed.",
        how_to_recognize=[
            "No pawn can defend this square",
            "Often created by pawn advances",
            "Light or dark square 'complex'",
        ],
        how_to_apply=[
            "Occupy weak squares with pieces",
            "Create weak squares in opponent's position",
            "Avoid creating them in your own position",
        ],
        common_mistakes=[
            "Creating weak squares carelessly",
            "Not exploiting opponent's weak squares",
            "Ignoring color complexes",
        ],
        related_concepts=["outposts", "pawn_structure", "bad_bishop"],
    ),
    
    "initiative": ChessFundamental(
        name="Initiative",
        category=ConceptCategory.POSITIONAL,
        definition="Having control of the game - making threats that the opponent must respond to.",
        why_it_matters="The side with initiative dictates the pace. The opponent must react instead of executing their own plans.",
        how_to_recognize=[
            "Creating threats every move",
            "Opponent constantly defending",
            "Your pieces more active",
        ],
        how_to_apply=[
            "Develop with threats",
            "Don't let opponent consolidate",
            "Keep creating problems",
        ],
        common_mistakes=[
            "Giving up initiative without reason",
            "Allowing opponent to take over",
            "Making quiet moves when you have initiative",
        ],
        related_concepts=["tempo", "piece_activity", "attacking_principles"],
    ),
    
    "tempo": ChessFundamental(
        name="Tempo",
        category=ConceptCategory.POSITIONAL,
        definition="A unit of time in chess - one move. Gaining tempo means achieving your goals in fewer moves.",
        why_it_matters="Every move counts. Gaining a tempo means you're a move ahead in development or attack.",
        how_to_recognize=[
            "Developing with attack gains tempo",
            "Opponent moving same piece twice loses tempo",
            "Forcing moves gain tempo",
        ],
        how_to_apply=[
            "Develop pieces with threats",
            "Don't move pieces twice without reason",
            "Force opponent to lose tempo",
        ],
        common_mistakes=[
            "Moving same piece multiple times",
            "Not recognizing tempo gains",
            "Wasting moves on useless threats",
        ],
        related_concepts=["initiative", "development", "attacking_principles"],
        example_explanation="White plays Bb5, developing and threatening the knight. Black must respond, giving White a tempo for development.",
    ),
}

# =============================================================================
# ENDGAME FUNDAMENTALS
# =============================================================================

ENDGAME_FUNDAMENTALS = {
    "king_activity_endgame": ChessFundamental(
        name="King Activity in Endgame",
        category=ConceptCategory.ENDGAME,
        definition="In the endgame, the king transforms from a piece needing protection to an active fighter.",
        why_it_matters="An active king in the endgame is worth a minor piece. It can attack pawns, support its own pawns, and control key squares.",
        how_to_recognize=[
            "Few pieces on board (endgame)",
            "King can safely leave shelter",
            "King needed to support pawns",
        ],
        how_to_apply=[
            "Centralize the king immediately in endgames",
            "King supports pawn advances",
            "King attacks enemy pawns",
        ],
        common_mistakes=[
            "Keeping king passive in endgame",
            "Not centralizing early enough",
            "Letting opponent's king become more active",
        ],
        related_concepts=["passed_pawn", "opposition", "centralization"],
    ),
    
    "opposition": ChessFundamental(
        name="Opposition",
        category=ConceptCategory.ENDGAME,
        definition="Kings facing each other with one square between. The side NOT to move has the opposition (advantage).",
        why_it_matters="In king and pawn endgames, opposition often decides the game. It allows one king to push the other aside.",
        how_to_recognize=[
            "Kings facing each other",
            "Odd number of squares between (1, 3, 5)",
            "Whoever must move gives way",
        ],
        how_to_apply=[
            "Take the opposition when possible",
            "Use it to escort passed pawns",
            "Distant opposition: prepare to take it later",
        ],
        common_mistakes=[
            "Not understanding opposition",
            "Losing the opposition unnecessarily",
            "Not using opposition to advance pawns",
        ],
        related_concepts=["king_activity_endgame", "passed_pawn", "zugzwang"],
    ),
    
    "rook_endgames": ChessFundamental(
        name="Rook Endgame Principles",
        category=ConceptCategory.ENDGAME,
        definition="Key principles for playing rook endgames: activity, passed pawns, and king position.",
        why_it_matters="Rook endgames are the most common. Knowing the principles is essential.",
        how_to_recognize=[
            "Only rooks and pawns remain",
            "Activity and passed pawns matter most",
            "Positions are often drawn with correct play",
        ],
        how_to_apply=[
            "Rooks belong behind passed pawns",
            "Active rook > extra pawn",
            "Cut off enemy king with rook",
            "Know basic drawn positions (Philidor)",
        ],
        common_mistakes=[
            "Passive rook placement",
            "Not knowing theoretical positions",
            "King not active enough",
        ],
        related_concepts=["rooks_on_open_files", "passed_pawn", "king_activity_endgame"],
    ),
    
    "zugzwang": ChessFundamental(
        name="Zugzwang",
        category=ConceptCategory.ENDGAME,
        definition="A position where any move worsens the position - being compelled to move is a disadvantage.",
        why_it_matters="In endgames, zugzwang can decide the game. The defender may have a fortress but must move and destroy it.",
        how_to_recognize=[
            "Position seems stable",
            "All moves weaken something",
            "If you could pass, you'd be fine",
        ],
        how_to_apply=[
            "Put opponent in zugzwang",
            "Use triangulation to lose a tempo",
            "Recognize when you're in zugzwang",
        ],
        common_mistakes=[
            "Not recognizing zugzwang positions",
            "Not knowing how to create zugzwang",
            "Making quick moves when should be careful",
        ],
        related_concepts=["opposition", "endgame", "tempo"],
    ),
}

# =============================================================================
# TACTICAL MOTIFS
# =============================================================================

TACTICAL_MOTIFS = {
    "double_attack": ChessFundamental(
        name="Double Attack",
        category=ConceptCategory.TACTICAL,
        definition="Attacking two things at once - opponent can only save one.",
        why_it_matters="The most fundamental tactic. One threat can be met; two at once usually can't.",
        how_to_recognize=[
            "One move creates two threats",
            "Opponent can't address both",
            "Often wins material",
        ],
        how_to_apply=[
            "Look for moves that attack two pieces",
            "Forks, discovered attacks are double attacks",
            "Create situations where double attacks are possible",
        ],
        common_mistakes=[
            "Not seeing double attack possibilities",
            "Leaving pieces vulnerable to double attacks",
            "Attacking pieces that can both be defended",
        ],
        related_concepts=["fork", "discovered_attack", "calculation"],
    ),
    
    "fork": ChessFundamental(
        name="Fork",
        category=ConceptCategory.TACTICAL,
        definition="One piece attacking two or more enemy pieces simultaneously.",
        why_it_matters="Forks win material because opponent can only save one piece. Knight forks are especially dangerous.",
        how_to_recognize=[
            "Piece attacks multiple targets",
            "Often knight or pawn forks",
            "King + valuable piece is deadly combo",
        ],
        how_to_apply=[
            "Knights can fork pieces that bishops can't",
            "Look for fork squares (where piece attacks multiple targets)",
            "Set up forks with preliminary moves",
        ],
        common_mistakes=[
            "Missing fork opportunities",
            "Leaving pieces on forkable squares",
            "Not setting up forks",
        ],
        related_concepts=["double_attack", "knight_tactics", "calculation"],
    ),
    
    "pin": ChessFundamental(
        name="Pin",
        category=ConceptCategory.TACTICAL,
        definition="Attacking a piece that cannot move without exposing a more valuable piece behind it.",
        why_it_matters="Pins immobilize pieces. An absolute pin (to king) makes the piece illegal to move. A relative pin costs material.",
        how_to_recognize=[
            "Piece between attacker and king/queen",
            "Moving it would expose something valuable",
            "Long-range pieces (bishop, rook, queen) create pins",
        ],
        how_to_apply=[
            "Pin pieces to the king when possible",
            "Pile up on pinned pieces",
            "Use pins to win material or restrict movement",
        ],
        common_mistakes=[
            "Missing pin opportunities",
            "Not exploiting existing pins",
            "Not breaking pins when under one",
        ],
        related_concepts=["skewer", "discovered_attack", "calculation"],
    ),
    
    "skewer": ChessFundamental(
        name="Skewer",
        category=ConceptCategory.TACTICAL,
        definition="Attacking a valuable piece that when it moves, exposes a piece behind it to capture.",
        why_it_matters="Like a reverse pin - the MORE valuable piece is in front. When it moves, you capture what's behind.",
        how_to_recognize=[
            "Valuable piece (king/queen) attacked",
            "Less valuable piece behind it",
            "When front piece moves, back piece is captured",
        ],
        how_to_apply=[
            "Attack king/queen with back piece behind",
            "Set up skewer possibilities",
            "Force pieces onto skewer-able squares",
        ],
        common_mistakes=[
            "Missing skewer opportunities",
            "Leaving king/queen on same line as other pieces",
            "Confusing with pin",
        ],
        related_concepts=["pin", "double_attack", "calculation"],
    ),
    
    "discovered_attack": ChessFundamental(
        name="Discovered Attack",
        category=ConceptCategory.TACTICAL,
        definition="Moving a piece to reveal an attack from another piece behind it.",
        why_it_matters="Creates two threats at once - the moving piece threatens something, while the revealed piece threatens something else.",
        how_to_recognize=[
            "Piece blocking another piece's attack",
            "Moving it reveals attack",
            "Moving piece can create its own threat",
        ],
        how_to_apply=[
            "Discovered check is especially powerful",
            "The moving piece can go anywhere with threat",
            "Set up discovery opportunities",
        ],
        common_mistakes=[
            "Missing discovered attack opportunities",
            "Not recognizing setup positions",
            "Blocking your own pieces unnecessarily",
        ],
        related_concepts=["double_attack", "discovered_check", "calculation"],
    ),
    
    "back_rank_mate": ChessFundamental(
        name="Back Rank Weakness",
        category=ConceptCategory.TACTICAL,
        definition="When a king is trapped on the back rank by its own pawns, vulnerable to mate by a rook or queen.",
        why_it_matters="Common in games. Even strong players get mated on the back rank. Always be aware of it.",
        how_to_recognize=[
            "King on back rank",
            "No escape squares (blocked by own pawns)",
            "Enemy rook/queen can reach back rank",
        ],
        how_to_apply=[
            "Look for back rank mates when opponent's king is trapped",
            "Create luft (h3/h6) for your own king",
            "Use back rank threats to win material",
        ],
        common_mistakes=[
            "Forgetting about back rank weakness",
            "Not creating an escape square",
            "Missing back rank tactics",
        ],
        related_concepts=["king_safety", "rooks_on_open_files", "calculation"],
    ),
    
    "removing_the_defender": ChessFundamental(
        name="Removing the Defender",
        category=ConceptCategory.TACTICAL,
        definition="Capturing, diverting, or chasing away a piece that defends something important.",
        why_it_matters="If only one piece defends something, remove it and the target falls.",
        how_to_recognize=[
            "Key piece with only one defender",
            "Can that defender be removed?",
            "Capture, chase, or deflect the defender",
        ],
        how_to_apply=[
            "Identify what pieces are defending",
            "Find ways to eliminate defenders",
            "Sometimes sacrifice to remove defender",
        ],
        common_mistakes=[
            "Not seeing defensive responsibilities",
            "Attacking the target directly instead",
            "Overloading not recognized",
        ],
        related_concepts=["overloading", "deflection", "calculation"],
    ),
    
    "deflection": ChessFundamental(
        name="Deflection",
        category=ConceptCategory.TACTICAL,
        definition="Forcing an enemy piece away from a square where it performs an important duty.",
        why_it_matters="The deflected piece can no longer defend or guard - opening up tactics.",
        how_to_recognize=[
            "Piece has defensive duty",
            "Can force it to move?",
            "When it moves, something is unguarded",
        ],
        how_to_apply=[
            "Attack defending pieces with threats",
            "Sacrifice to deflect key defenders",
            "Force pieces off critical squares",
        ],
        common_mistakes=[
            "Not recognizing defensive duties",
            "Missing deflection opportunities",
            "Deflection sacrifice not calculated",
        ],
        related_concepts=["removing_the_defender", "decoy", "calculation"],
    ),
    
    "overloading": ChessFundamental(
        name="Overloading",
        category=ConceptCategory.TACTICAL,
        definition="A piece with too many defensive responsibilities - attacking one forces it to abandon another.",
        why_it_matters="If one piece defends two things, it can only save one. Attacking both exploits this.",
        how_to_recognize=[
            "Piece defending multiple things",
            "If it moves, something falls",
            "Often queens are overloaded",
        ],
        how_to_apply=[
            "Identify overloaded pieces",
            "Attack both things it defends",
            "Force it to choose",
        ],
        common_mistakes=[
            "Not recognizing overloaded pieces",
            "Missing the opportunity",
            "Your own pieces getting overloaded",
        ],
        related_concepts=["removing_the_defender", "deflection", "double_attack"],
    ),
    
    "zwischenzug": ChessFundamental(
        name="Zwischenzug (In-Between Move)",
        category=ConceptCategory.TACTICAL,
        definition="An 'in-between' move - instead of the expected response, making a forcing move first.",
        why_it_matters="Changes the evaluation of exchanges. The expected recapture isn't forced if you have a check or threat.",
        how_to_recognize=[
            "Exchange expected to happen",
            "But there's an in-between check or threat",
            "Changes who comes out ahead",
        ],
        how_to_apply=[
            "Before recapturing, look for checks/threats",
            "In-between moves are often checks",
            "Calculate exchanges carefully for zwischenzugs",
        ],
        common_mistakes=[
            "Auto-recapturing without looking",
            "Missing opponent's zwischenzug",
            "Not considering in-between moves",
        ],
        related_concepts=["calculation", "tempo", "forcing_moves"],
    ),
}

# =============================================================================
# COMPILE ALL FUNDAMENTALS
# =============================================================================

ALL_FUNDAMENTALS: Dict[str, ChessFundamental] = {
    **OPENING_PRINCIPLES,
    **PIECE_PLACEMENT,
    **PAWN_STRUCTURE,
    **KING_SAFETY,
    **ATTACKING_PRINCIPLES,
    **DEFENSIVE_PRINCIPLES,
    **POSITIONAL_CONCEPTS,
    **ENDGAME_FUNDAMENTALS,
    **TACTICAL_MOTIFS,
}

# Category index for quick lookup
FUNDAMENTALS_BY_CATEGORY: Dict[ConceptCategory, Dict[str, ChessFundamental]] = {
    ConceptCategory.OPENING: OPENING_PRINCIPLES,
    ConceptCategory.PIECE_PLACEMENT: PIECE_PLACEMENT,
    ConceptCategory.PAWN_STRUCTURE: PAWN_STRUCTURE,
    ConceptCategory.KING_SAFETY: KING_SAFETY,
    ConceptCategory.ATTACKING: ATTACKING_PRINCIPLES,
    ConceptCategory.DEFENSIVE: DEFENSIVE_PRINCIPLES,
    ConceptCategory.POSITIONAL: POSITIONAL_CONCEPTS,
    ConceptCategory.ENDGAME: ENDGAME_FUNDAMENTALS,
    ConceptCategory.TACTICAL: TACTICAL_MOTIFS,
}


def get_fundamental(name: str) -> Optional[ChessFundamental]:
    """Get a fundamental by name."""
    return ALL_FUNDAMENTALS.get(name.lower().replace(' ', '_').replace('-', '_'))


def get_related_fundamentals(concept_name: str) -> List[ChessFundamental]:
    """Get fundamentals related to a given concept."""
    concept = get_fundamental(concept_name)
    if not concept:
        return []
    
    return [
        ALL_FUNDAMENTALS[rel] 
        for rel in concept.related_concepts 
        if rel in ALL_FUNDAMENTALS
    ]


def get_fundamentals_for_position_type(
    is_opening: bool = False,
    is_endgame: bool = False,
    has_attack: bool = False,
    is_defensive: bool = False
) -> List[ChessFundamental]:
    """Get relevant fundamentals based on position characteristics."""
    relevant = []
    
    if is_opening:
        relevant.extend(OPENING_PRINCIPLES.values())
    
    if is_endgame:
        relevant.extend(ENDGAME_FUNDAMENTALS.values())
    else:
        relevant.extend(PIECE_PLACEMENT.values())
        relevant.extend(PAWN_STRUCTURE.values())
    
    if has_attack:
        relevant.extend(ATTACKING_PRINCIPLES.values())
        relevant.extend(KING_SAFETY.values())
    
    if is_defensive:
        relevant.extend(DEFENSIVE_PRINCIPLES.values())
    
    # Always include tactical motifs
    relevant.extend(TACTICAL_MOTIFS.values())
    
    return relevant


def format_fundamental_for_prompt(fundamental: ChessFundamental) -> str:
    """Format a fundamental for inclusion in LLM prompt."""
    return f"""
**{fundamental.name}** ({fundamental.category.value})
Definition: {fundamental.definition}
Why it matters: {fundamental.why_it_matters}
How to apply: {'; '.join(fundamental.how_to_apply[:2])}
"""


def get_all_fundamentals_summary() -> str:
    """Get a summary of all fundamentals for prompts."""
    summary_parts = []
    
    for category in ConceptCategory:
        if category in FUNDAMENTALS_BY_CATEGORY:
            concepts = FUNDAMENTALS_BY_CATEGORY[category]
            concept_names = [c.name for c in concepts.values()]
            summary_parts.append(f"**{category.value}**: {', '.join(concept_names)}")
    
    return "\n".join(summary_parts)
