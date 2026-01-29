"""
LLM Prompts for Chess Explanation - Thorough, structured prompts for high-quality explanations.

These prompts ensure the LLM provides accurate, insightful chess analysis by:
1. Providing comprehensive Stockfish analysis context
2. Structuring responses clearly
3. Grounding explanations in chess fundamentals
4. Using multi-move lookahead for deeper understanding
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum


class PromptType(Enum):
    """Types of prompts for different explanation scenarios."""
    EXPLAIN_MOVE = "explain_move"
    COMPARE_MOVES = "compare_moves"
    POSITION_EVAL = "position_eval"
    FIND_PLAN = "find_plan"
    WHY_BAD = "why_bad"
    TACTICAL_EXPLANATION = "tactical_explanation"
    STRATEGIC_OVERVIEW = "strategic_overview"


@dataclass
class StockfishAnalysis:
    """Structured Stockfish analysis for LLM context."""
    current_eval: float
    best_move: str
    best_move_eval: float
    principal_variation: List[str]  # 4-5 moves ahead
    pv_explanations: List[str]  # What each move accomplishes
    alternative_moves: List[Dict[str, Any]]  # Other good options
    threats: List[str]  # Opponent's threats to address
    position_features: Dict[str, Any]  # Material, king safety, etc.


# =============================================================================
# SYSTEM PROMPT - Core instructions for the LLM
# =============================================================================

SYSTEM_PROMPT = """You are an expert chess coach with deep understanding of strategy and tactics. 
Your goal is to explain chess positions and moves in a way that helps players UNDERSTAND WHY, not just WHAT.

CRITICAL GUIDELINES:
1. **Ground explanations in Stockfish analysis** - Use the engine's evaluation and principal variation as your factual foundation
2. **Explain the WHY** - Don't just say "this is best" - explain what makes it best
3. **Use chess fundamentals** - Reference opening principles, piece activity, pawn structure, king safety, tactical motifs
4. **Look ahead** - Use the provided multi-move sequence to explain what happens next and why
5. **Be specific** - Mention specific squares, pieces, and variations
6. **Acknowledge complexity** - If a position is unclear or the best move isn't obviously better, say so
7. **Match the audience** - Explain clearly for improving players (1200-1800 level)

RESPONSE FORMAT:
- Write in plain text paragraphs without any Markdown formatting
- Do NOT use headers (###, ##, #), bold (**text**), or italics (*text*)
- Do NOT use bullet points or numbered lists with special characters
- Write naturally as if speaking to a student
- Use line breaks to separate ideas, but keep it conversational

RESPONSE STRUCTURE:
- Start with the key insight (1 sentence)
- Explain the reasoning (2-3 sentences with specifics)
- Reference the follow-up variation when relevant
- Connect to chess principles when applicable

AVOID:
- Vague statements like "this is good for development"
- Overly complex variations the user didn't ask for
- Contradicting the Stockfish evaluation without explanation
- Generic advice that doesn't fit this specific position
- Any Markdown formatting (###, **, *, -, etc.)
"""


# =============================================================================
# POSITION CONTEXT TEMPLATE
# =============================================================================

def build_position_context(
    fen: str,
    stockfish: StockfishAnalysis,
    game_context: Optional[Dict] = None
) -> str:
    """Build comprehensive position context for the LLM."""
    
    context = f"""
=== POSITION ANALYSIS ===
FEN: {fen}
Side to move: {"White" if " w " in fen else "Black"}

=== STOCKFISH EVALUATION ===
Current evaluation: {stockfish.current_eval:+.2f} (positive = White advantage)
Best move: {stockfish.best_move} (eval after: {stockfish.best_move_eval:+.2f})

=== PRINCIPAL VARIATION (Next 4-5 moves) ===
{' '.join(stockfish.principal_variation)}

What happens in this line:
"""
    
    for i, explanation in enumerate(stockfish.pv_explanations):
        if i < len(stockfish.principal_variation):
            context += f"  {i+1}. {stockfish.principal_variation[i]}: {explanation}\n"
    
    if stockfish.alternative_moves:
        context += "\n=== ALTERNATIVE MOVES ===\n"
        for alt in stockfish.alternative_moves[:3]:
            context += f"  {alt['move']}: eval {alt['eval']:+.2f} - {alt.get('note', '')}\n"
    
    if stockfish.threats:
        context += f"\n=== THREATS TO ADDRESS ===\n"
        for threat in stockfish.threats:
            context += f"  - {threat}\n"
    
    context += f"""
=== POSITION FEATURES ===
Material balance: {stockfish.position_features.get('material', 'Equal')}
King safety (White): {stockfish.position_features.get('white_king_safety', 'Normal')}
King safety (Black): {stockfish.position_features.get('black_king_safety', 'Normal')}
Pawn structure: {stockfish.position_features.get('pawn_structure', 'Normal')}
Piece activity: {stockfish.position_features.get('piece_activity', 'Normal')}
Open files: {stockfish.position_features.get('open_files', 'None')}
"""
    
    if game_context:
        context += f"""
=== GAME CONTEXT ===
Opening: {game_context.get('opening', 'Unknown')}
Move number: {game_context.get('move_number', '?')}
Previous move: {game_context.get('last_move', 'Unknown')}
"""
    
    return context


# =============================================================================
# EXPLAIN MOVE PROMPT
# =============================================================================

EXPLAIN_MOVE_PROMPT = """
{system_prompt}

{position_context}

=== USER QUESTION ===
Explain the move: {move}

=== YOUR TASK ===
Explain why {move} is played and what it accomplishes. Consider:

1. **Immediate effects**: What does this move attack/defend/threaten?
2. **Strategic purpose**: How does it improve the position?
3. **Follow-up plan**: What happens next based on the principal variation?
4. **Comparison to alternatives**: Why is this better than other options (if it is)?

If the move is not the engine's first choice, acknowledge the difference and explain both perspectives.

Use the Stockfish analysis as your factual foundation, but explain it in human terms.

Relevant chess principles to consider:
- Piece activity and centralization
- Control of key squares and files
- Pawn structure implications
- King safety
- Tactical motifs (pins, forks, threats)

Provide a clear, educational explanation (3-5 sentences).
"""


# =============================================================================
# COMPARE MOVES PROMPT
# =============================================================================

COMPARE_MOVES_PROMPT = """
{system_prompt}

{position_context}

=== USER QUESTION ===
Compare these moves: {move1} vs {move2}

=== ANALYSIS FOR {move1} ===
Evaluation: {move1_eval}
Follow-up: {move1_pv}
Key idea: {move1_idea}

=== ANALYSIS FOR {move2} ===
Evaluation: {move2_eval}
Follow-up: {move2_pv}
Key idea: {move2_idea}

=== YOUR TASK ===
Compare these two moves clearly:

1. **Which is objectively better?** (use the evaluations)
2. **What's the key difference?** (strategic purpose, consequences)
3. **What does each move give up?** (trade-offs)
4. **When might the other be preferable?** (context matters)

If they're very close in evaluation, acknowledge that both are reasonable.
Focus on what makes them DIFFERENT rather than just evaluating each independently.

Provide a focused comparison (3-5 sentences).
"""


# =============================================================================
# WHY BAD MOVE PROMPT
# =============================================================================

WHY_BAD_PROMPT = """
{system_prompt}

{position_context}

=== USER QUESTION ===
Why is {bad_move} a mistake?

=== ANALYSIS ===
{bad_move} evaluation: {bad_eval}
Best move was: {best_move} (eval: {best_eval})
Evaluation loss: {eval_diff}

What happens after {bad_move}:
{bad_continuation}

Refutation line: {refutation}

=== YOUR TASK ===
Explain clearly why {bad_move} is a mistake:

1. **What's wrong with it?** (the concrete problem)
2. **What does opponent do?** (the refutation/punishment)
3. **What is lost?** (material, position, time)
4. **What should have been played?** (brief mention of the better option)

Be specific about the problem. Don't just say "it's bad" - show exactly what goes wrong.

Focus on the most instructive lesson for the player (2-4 sentences).
"""


# =============================================================================
# FIND PLAN PROMPT
# =============================================================================

FIND_PLAN_PROMPT = """
{system_prompt}

{position_context}

=== USER QUESTION ===
What is the plan in this position?

=== YOUR TASK ===
Based on the position and Stockfish's suggested continuation, explain the strategic plan:

1. **The main idea**: What are we trying to achieve? (1 sentence)
2. **The method**: How do we achieve it? (specific moves/maneuvers)
3. **Key moves**: Reference the principal variation to show the plan in action
4. **What to avoid**: Any pitfalls or opponent's counter-plans

Consider these strategic themes:
- Pawn breaks to open lines
- Piece improvements (worst piece first)
- Attacking the king or weak pawns
- Creating/exploiting weaknesses
- Endgame preparation if applicable

Provide a practical plan (3-5 sentences) that the player can follow.
"""


# =============================================================================
# TACTICAL EXPLANATION PROMPT
# =============================================================================

TACTICAL_PROMPT = """
{system_prompt}

{position_context}

=== TACTICAL SITUATION ===
Type: {tactic_type}
Key move: {key_move}
Target: {target}

=== YOUR TASK ===
Explain this tactical opportunity:

1. **What's the tactic?** (fork, pin, skewer, discovered attack, etc.)
2. **How does it work?** (step-by-step)
3. **What's the result?** (material won, checkmate threat, etc.)
4. **How to recognize it?** (pattern for future games)

Be concrete: mention specific squares and pieces.

Make it educational - help the player spot this pattern in the future (2-4 sentences).
"""


# =============================================================================
# POSITION EVALUATION PROMPT
# =============================================================================

POSITION_EVAL_PROMPT = """
{system_prompt}

{position_context}

=== USER QUESTION ===
Evaluate this position. Who stands better and why?

=== YOUR TASK ===
Provide a clear assessment:

1. **The verdict**: Who stands better? (White/Black/Equal)
2. **Material**: Any imbalances?
3. **Positional factors**:
   - Piece activity and placement
   - Pawn structure (strengths/weaknesses)
   - King safety
   - Space and control
4. **The key factor**: What's the most important element?
5. **Outlook**: What should each side aim for?

Base your assessment on the Stockfish evaluation but explain it in human terms.
The evaluation is {eval_assessment} ({eval_number:+.2f}).

Provide a balanced, informative assessment (4-6 sentences).
"""


# =============================================================================
# HELPER FUNCTIONS FOR BUILDING PROMPTS
# =============================================================================

def describe_eval(eval_cp: float) -> str:
    """Describe evaluation in human terms."""
    if abs(eval_cp) < 0.3:
        return "approximately equal"
    elif abs(eval_cp) < 0.7:
        return f"slightly better for {'White' if eval_cp > 0 else 'Black'}"
    elif abs(eval_cp) < 1.5:
        return f"clearly better for {'White' if eval_cp > 0 else 'Black'}"
    elif abs(eval_cp) < 3.0:
        return f"much better for {'White' if eval_cp > 0 else 'Black'}"
    else:
        return f"winning for {'White' if eval_cp > 0 else 'Black'}"


def describe_eval_change(before: float, after: float) -> str:
    """Describe how evaluation changed."""
    diff = after - before
    
    if abs(diff) < 0.2:
        return "maintains the current evaluation"
    elif diff > 0:
        return f"improves White's position by about {abs(diff):.1f} pawns"
    else:
        return f"improves Black's position by about {abs(diff):.1f} pawns"


def categorize_move_quality(played_eval: float, best_eval: float, player_is_white: bool) -> str:
    """Categorize move quality."""
    # From player's perspective
    if player_is_white:
        diff = best_eval - played_eval
    else:
        diff = played_eval - best_eval
    
    if diff < 0.1:
        return "Excellent - best or nearly best"
    elif diff < 0.3:
        return "Good - minor inaccuracy"
    elif diff < 0.7:
        return "Inaccuracy - not the best but playable"
    elif diff < 1.5:
        return "Mistake - significantly worse"
    else:
        return "Blunder - serious error"


# =============================================================================
# PROMPT BUILDER CLASS
# =============================================================================

class PromptBuilder:
    """Builds prompts for different explanation types."""
    
    def __init__(self, stockfish_analysis: StockfishAnalysis, fen: str):
        self.stockfish = stockfish_analysis
        self.fen = fen
        self.position_context = build_position_context(fen, stockfish_analysis)
    
    def build_explain_move_prompt(self, move: str) -> str:
        """Build prompt for explaining a specific move."""
        return EXPLAIN_MOVE_PROMPT.format(
            system_prompt=SYSTEM_PROMPT,
            position_context=self.position_context,
            move=move
        )
    
    def build_compare_moves_prompt(
        self, 
        move1: str, move1_eval: float, move1_pv: str, move1_idea: str,
        move2: str, move2_eval: float, move2_pv: str, move2_idea: str
    ) -> str:
        """Build prompt for comparing two moves."""
        return COMPARE_MOVES_PROMPT.format(
            system_prompt=SYSTEM_PROMPT,
            position_context=self.position_context,
            move1=move1, move1_eval=f"{move1_eval:+.2f}", 
            move1_pv=move1_pv, move1_idea=move1_idea,
            move2=move2, move2_eval=f"{move2_eval:+.2f}",
            move2_pv=move2_pv, move2_idea=move2_idea
        )
    
    def build_why_bad_prompt(
        self,
        bad_move: str, bad_eval: float, bad_continuation: str,
        best_move: str, best_eval: float, refutation: str
    ) -> str:
        """Build prompt for explaining why a move is bad."""
        return WHY_BAD_PROMPT.format(
            system_prompt=SYSTEM_PROMPT,
            position_context=self.position_context,
            bad_move=bad_move,
            bad_eval=f"{bad_eval:+.2f}",
            best_move=best_move,
            best_eval=f"{best_eval:+.2f}",
            eval_diff=f"{abs(best_eval - bad_eval):.2f}",
            bad_continuation=bad_continuation,
            refutation=refutation
        )
    
    def build_find_plan_prompt(self) -> str:
        """Build prompt for finding the plan."""
        return FIND_PLAN_PROMPT.format(
            system_prompt=SYSTEM_PROMPT,
            position_context=self.position_context
        )
    
    def build_tactical_prompt(
        self,
        tactic_type: str,
        key_move: str,
        target: str
    ) -> str:
        """Build prompt for tactical explanation."""
        return TACTICAL_PROMPT.format(
            system_prompt=SYSTEM_PROMPT,
            position_context=self.position_context,
            tactic_type=tactic_type,
            key_move=key_move,
            target=target
        )
    
    def build_position_eval_prompt(self) -> str:
        """Build prompt for position evaluation."""
        eval_number = self.stockfish.current_eval
        return POSITION_EVAL_PROMPT.format(
            system_prompt=SYSTEM_PROMPT,
            position_context=self.position_context,
            eval_assessment=describe_eval(eval_number),
            eval_number=eval_number
        )


# =============================================================================
# FUNDAMENTALS INJECTION
# =============================================================================

def inject_relevant_fundamentals(prompt: str, fundamentals: List[str]) -> str:
    """Inject relevant chess fundamentals into a prompt."""
    if not fundamentals:
        return prompt
    
    fundamentals_section = """
=== RELEVANT CHESS PRINCIPLES ===
Consider these fundamentals when explaining:
"""
    for fund in fundamentals[:5]:  # Limit to 5 most relevant
        fundamentals_section += f"- {fund}\n"
    
    # Insert before "YOUR TASK"
    if "=== YOUR TASK ===" in prompt:
        return prompt.replace(
            "=== YOUR TASK ===",
            fundamentals_section + "\n=== YOUR TASK ==="
        )
    return prompt + fundamentals_section


# =============================================================================
# MULTI-MOVE LOOKAHEAD EXPLANATION
# =============================================================================

def generate_pv_explanations(pv_moves: List[str], board_fen: str) -> List[str]:
    """
    Generate explanations for each move in the principal variation.
    
    This function should be called with the actual board to analyze each move.
    Returns brief explanations of what each move accomplishes.
    """
    # This is a template - actual implementation needs the board
    explanations = []
    
    templates = [
        "Initiates the main plan",
        "Forces opponent's response",
        "Continues the pressure/plan",
        "Consolidates the advantage",
        "Completes the idea"
    ]
    
    for i, move in enumerate(pv_moves[:5]):
        if i < len(templates):
            explanations.append(f"{templates[i]}")
        else:
            explanations.append("Continues play")
    
    return explanations
