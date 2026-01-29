"""
Explainability Service - The main orchestrator for chess explanations.

This is the primary interface for the "why" system. It:
1. Understands user questions (query_understanding)
2. Performs appropriate analysis (why_engine)
3. Contextualizes with chess concepts (explanation_framework)
4. Produces structured output for LLM verbalization

Usage:
    service = ExplainabilityService()
    result = service.explain("Why is Nf3 good?", fen=current_position)

NOTE: This is the original explainability service. For new development,
consider using EnhancedExplainabilityService from enhanced_explainability.py,
which provides:
- Multi-move lookahead with per-move explanations (DeepAnalyzer)
- Access to 60+ chess fundamentals from Lichess training
- Enhanced LLM prompts with structured context
- Better grounding of explanations in Stockfish analysis

The EnhancedExplainabilityService is the recommended service for LLM-based
explanations. This service is maintained for backward compatibility and
can be used for simpler analysis tasks.
"""

import chess
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict
import json

from why_engine import WhyEngine, MoveAnalysis, MoveIntent, CompensationType
from query_understanding import QueryParser, ParsedQuery, QueryType, ResponseRouter, reformulate_for_analysis
from explanation_framework import (
    get_concept_explanation, describe_evaluation, describe_eval_change,
    CHESS_CONCEPTS, ChessConcept, get_relevant_concepts_for_intent,
    format_explanation
)


@dataclass
class ExplanationResult:
    """Complete explanation result ready for verbalization."""
    
    # What was asked
    question_type: str
    question_interpreted: str
    
    # The core answer
    answer_summary: str
    
    # Detailed breakdown
    detailed_analysis: Dict = field(default_factory=dict)
    
    # Chess concepts involved
    concepts_involved: List[str] = field(default_factory=list)
    concept_explanations: Dict = field(default_factory=dict)
    
    # Evidence and reasoning
    evidence: List[str] = field(default_factory=list)
    
    # Concrete data
    evaluation: float = 0.0
    evaluation_description: str = ""
    best_move: str = ""
    principal_variation: str = ""
    
    # For comparisons
    comparison: Dict = field(default_factory=dict)
    
    # Teaching notes (why this matters, what to learn)
    learning_points: List[str] = field(default_factory=list)
    
    # Raw data for tools
    raw_analysis: Dict = field(default_factory=dict)


class ExplainabilityService:
    """
    Main service for explaining chess moves and positions.
    
    This is the interface between user questions and deep analysis.
    It orchestrates all analysis components and produces structured
    explanations ready for LLM verbalization.
    """
    
    def __init__(self, engine_depth: int = 18):
        """
        Initialize the explainability service.
        
        Args:
            engine_depth: Stockfish depth for analysis
        """
        self.why_engine = WhyEngine(depth=engine_depth)
        self.query_parser = QueryParser()
        self.response_router = ResponseRouter()
    
    def close(self):
        """Release resources."""
        if hasattr(self, 'why_engine') and self.why_engine:
            try:
                self.why_engine.close()
            except Exception:
                pass
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False
    
    def __del__(self):
        """Destructor - ensure cleanup."""
        self.close()
    
    def explain(self, question: str, fen: str, 
                played_move: str = None, 
                context: Dict = None) -> ExplanationResult:
        """
        Generate a comprehensive explanation for a chess question.
        
        Args:
            question: User's question (e.g., "Why is Nf3 good?")
            fen: Current position in FEN notation
            played_move: The move that was played (if any)
            context: Additional context (game phase, player level, etc.)
            
        Returns:
            ExplanationResult with complete explanation data
        """
        # Parse the question
        parsed = self.query_parser.parse(question)
        
        # Get analysis plan
        plan = self.response_router.get_analysis_plan(parsed)
        
        # Route to appropriate handler
        if parsed.query_type == QueryType.WHY_GOOD:
            return self._explain_why_good(parsed, fen, played_move)
        
        elif parsed.query_type == QueryType.WHY_BAD:
            return self._explain_why_bad(parsed, fen, played_move)
        
        elif parsed.query_type == QueryType.COMPARE_MOVES:
            return self._compare_moves(parsed, fen)
        
        elif parsed.query_type == QueryType.WHAT_TO_PLAY:
            return self._what_to_play(parsed, fen)
        
        elif parsed.query_type == QueryType.EVALUATE:
            return self._evaluate_position(parsed, fen)
        
        elif parsed.query_type == QueryType.FIND_TACTIC:
            return self._find_tactics(parsed, fen)
        
        elif parsed.query_type == QueryType.EXPLAIN_CONCEPT:
            return self._explain_concept(parsed, fen)
        
        elif parsed.query_type == QueryType.EXPLAIN_PLAN:
            return self._explain_plan(parsed, fen)
        
        elif parsed.query_type == QueryType.CHECK_MOVE:
            return self._check_move(parsed, fen)
        
        elif parsed.query_type == QueryType.EXPLAIN_POSITION:
            return self._explain_position(parsed, fen)
        
        else:
            return self._general_response(parsed, fen, played_move)
    
    def _explain_why_good(self, query: ParsedQuery, fen: str, 
                          played_move: str = None) -> ExplanationResult:
        """Explain why a move is good."""
        move = query.primary_move or played_move
        
        if not move:
            # Find the best move to explain
            self.why_engine._ensure_engine()
            best = self.why_engine.engine.get_best_moves(fen, n=1, depth=self.why_engine.depth)
            if best:
                move = best[0]['san']
            else:
                return ExplanationResult(
                    question_type="why_good",
                    question_interpreted="Explain why a move is good",
                    answer_summary="Could not determine which move to analyze."
                )
        
        # Analyze the move
        analysis = self.why_engine.analyze_move(fen, move)
        
        # Build explanation
        answer_parts = []
        
        if analysis.is_best_move:
            answer_parts.append(f"{move} is the best move in this position.")
        else:
            answer_parts.append(f"{move} is a reasonable move.")
        
        # Primary intent
        intent_desc = self._describe_intent(analysis.primary_intent)
        answer_parts.append(f"The main idea is {intent_desc}.")
        
        # Achievements
        if analysis.achievements:
            answer_parts.append(f"It {', '.join(analysis.achievements).lower()}.")
        
        # If sacrifice, explain compensation
        if analysis.is_sacrifice and analysis.compensation_types:
            comp_desc = [c.value.replace('_', ' ') for c in analysis.compensation_types]
            answer_parts.append(f"This sacrifice is justified by {', '.join(comp_desc)}.")
        
        # Tactical patterns
        if analysis.tactical_patterns:
            for pattern in analysis.tactical_patterns:
                answer_parts.append(f"Tactical element: {pattern.description}.")
        
        # Evaluation
        eval_desc = describe_evaluation(analysis.eval_after)
        answer_parts.append(f"Position assessment: {eval_desc}.")
        
        # Get relevant concepts
        concepts = get_relevant_concepts_for_intent(analysis.primary_intent.value)
        concept_names = [c.name for c in concepts[:2]]
        
        return ExplanationResult(
            question_type="why_good",
            question_interpreted=f"Why is {move} a good move?",
            answer_summary=" ".join(answer_parts),
            detailed_analysis={
                'move': move,
                'is_best': analysis.is_best_move,
                'intent': analysis.primary_intent.value,
                'achievements': analysis.achievements,
                'threats_created': analysis.threats_created,
                'is_sacrifice': analysis.is_sacrifice,
                'compensation': [c.value for c in analysis.compensation_types],
                'tactical_patterns': [p.pattern_type for p in analysis.tactical_patterns],
            },
            concepts_involved=concept_names,
            concept_explanations={c.name: c.description for c in concepts[:2]},
            evidence=analysis.evidence,
            evaluation=analysis.eval_after,
            evaluation_description=eval_desc,
            best_move=analysis.best_move_san or move,
            principal_variation=analysis.pv_explanation,
            learning_points=self._generate_learning_points(analysis),
            raw_analysis=asdict(analysis)
        )
    
    def _explain_why_bad(self, query: ParsedQuery, fen: str, 
                         played_move: str = None) -> ExplanationResult:
        """Explain why a move is bad."""
        move = query.primary_move or played_move
        
        if not move:
            return ExplanationResult(
                question_type="why_bad",
                question_interpreted="Explain why a move is bad",
                answer_summary="No move specified to analyze."
            )
        
        # Analyze the move
        analysis = self.why_engine.analyze_move(fen, move)
        
        # Get comparison to best move
        comparison = self.why_engine.explain_why_move_is_bad(fen, move)
        
        # Build explanation
        answer_parts = []
        
        if analysis.eval_delta < -2.0:
            answer_parts.append(f"{move} is a serious mistake (blunder).")
        elif analysis.eval_delta < -0.5:
            answer_parts.append(f"{move} is an inaccurate move.")
        else:
            answer_parts.append(f"{move} is not the best, though not terrible.")
        
        # What's wrong with it
        if analysis.mistake_reason:
            answer_parts.append(analysis.mistake_reason)
        
        # Refutation
        if analysis.refutation:
            answer_parts.append(f"The problem is that it allows {analysis.refutation}.")
        
        # Better alternative
        if comparison.get('best_move'):
            answer_parts.append(f"Better was {comparison['best_move']}.")
            
            # Why is it better?
            reasons = comparison.get('reasons', [])
            if reasons:
                answer_parts.append(reasons[0])
        
        # Evaluation loss
        answer_parts.append(
            f"This loses approximately {abs(analysis.eval_delta):.1f} pawns worth of advantage."
        )
        
        return ExplanationResult(
            question_type="why_bad",
            question_interpreted=f"Why is {move} a mistake?",
            answer_summary=" ".join(answer_parts),
            detailed_analysis={
                'move': move,
                'eval_loss': comparison.get('eval_loss', 0),
                'refutation': analysis.refutation,
                'mistake_category': self._categorize_mistake(analysis),
            },
            comparison={
                'bad_move': move,
                'best_move': comparison.get('best_move'),
                'reasons': comparison.get('reasons', []),
            },
            evidence=analysis.evidence,
            evaluation=analysis.eval_after,
            evaluation_description=describe_evaluation(analysis.eval_after),
            best_move=comparison.get('best_move', ''),
            learning_points=[
                "Before playing a move, check what your opponent can do in response",
                f"Consider {comparison.get('best_move', 'the engine suggestion')} and compare the ideas",
            ],
            raw_analysis=asdict(analysis)
        )
    
    def _compare_moves(self, query: ParsedQuery, fen: str) -> ExplanationResult:
        """Compare two moves and explain the difference."""
        move1 = query.primary_move
        move2 = query.comparison_move
        
        if not move1 or not move2:
            return ExplanationResult(
                question_type="compare_moves",
                question_interpreted="Compare two moves",
                answer_summary="Please specify two moves to compare."
            )
        
        # Analyze both moves
        analysis1 = self.why_engine.analyze_move(fen, move1)
        analysis2 = self.why_engine.analyze_move(fen, move2)
        
        # Determine which is better
        better_move = move1 if analysis1.eval_after > analysis2.eval_after else move2
        worse_move = move2 if better_move == move1 else move1
        better_analysis = analysis1 if better_move == move1 else analysis2
        worse_analysis = analysis2 if better_move == move1 else analysis1
        
        eval_diff = abs(analysis1.eval_after - analysis2.eval_after)
        
        # Build comparison explanation
        answer_parts = []
        
        if eval_diff < 0.2:
            answer_parts.append(f"Both {move1} and {move2} are roughly equal.")
        else:
            answer_parts.append(f"{better_move} is better than {worse_move} by about {eval_diff:.1f} pawns.")
        
        # What does the better move achieve that the worse doesn't?
        better_achievements = set(better_analysis.achievements) - set(worse_analysis.achievements)
        if better_achievements:
            answer_parts.append(f"{better_move} {', '.join(better_achievements).lower()}.")
        
        # Intent comparison
        if better_analysis.primary_intent != worse_analysis.primary_intent:
            answer_parts.append(
                f"{better_move} focuses on {better_analysis.primary_intent.value} "
                f"while {worse_move} is about {worse_analysis.primary_intent.value}."
            )
        
        # Key differences
        differences = []
        
        if better_analysis.threats_created and not worse_analysis.threats_created:
            differences.append(f"{better_move} creates threats while {worse_move} doesn't")
        
        if better_analysis.is_sacrifice and not worse_analysis.is_sacrifice:
            differences.append(f"{better_move} involves a sacrifice for compensation")
        
        if differences:
            answer_parts.append("Key difference: " + differences[0] + ".")
        
        return ExplanationResult(
            question_type="compare_moves",
            question_interpreted=f"Compare {move1} with {move2}",
            answer_summary=" ".join(answer_parts),
            detailed_analysis={
                'move1': move1,
                'move1_eval': analysis1.eval_after,
                'move1_intent': analysis1.primary_intent.value,
                'move2': move2,
                'move2_eval': analysis2.eval_after,
                'move2_intent': analysis2.primary_intent.value,
            },
            comparison={
                'better_move': better_move,
                'eval_difference': eval_diff,
                'key_differences': differences,
            },
            evaluation=better_analysis.eval_after,
            evaluation_description=describe_evaluation(better_analysis.eval_after),
            best_move=better_move,
            learning_points=[
                "When comparing moves, consider not just evaluation but also the ideas behind them",
                "Sometimes a slightly worse evaluation is fine if the position is easier to play",
            ]
        )
    
    def _what_to_play(self, query: ParsedQuery, fen: str) -> ExplanationResult:
        """Recommend the best move and explain why."""
        self.why_engine._ensure_engine()
        
        # Get top 3 moves
        top_moves = self.why_engine.engine.get_best_moves(fen, n=3, depth=self.why_engine.depth)
        
        if not top_moves:
            return ExplanationResult(
                question_type="what_to_play",
                question_interpreted="What is the best move?",
                answer_summary="Unable to analyze this position."
            )
        
        best = top_moves[0]
        best_move = best['san']
        
        # Analyze the best move
        analysis = self.why_engine.analyze_move(fen, best_move)
        
        # Build recommendation
        answer_parts = []
        
        answer_parts.append(f"The best move is {best_move}.")
        
        # Why this move?
        intent_desc = self._describe_intent(analysis.primary_intent)
        answer_parts.append(f"The idea is {intent_desc}.")
        
        # What it achieves
        if analysis.achievements:
            answer_parts.append(f"It {', '.join(analysis.achievements).lower()}.")
        
        # Expected continuation
        if analysis.pv_explanation:
            answer_parts.append(analysis.pv_explanation)
        
        # Alternatives
        alternatives = []
        if len(top_moves) > 1:
            for alt in top_moves[1:3]:
                alt_eval = alt['score'] / 100 if alt['type'] == 'cp' else 0
                eval_diff = abs(best['score'] / 100 - alt_eval) if best['type'] == 'cp' else 0
                alternatives.append({
                    'move': alt['san'],
                    'eval': alt_eval,
                    'eval_diff': eval_diff,
                })
            
            if alternatives[0]['eval_diff'] < 0.3:
                answer_parts.append(
                    f"{alternatives[0]['move']} is also good, nearly equal to {best_move}."
                )
        
        return ExplanationResult(
            question_type="what_to_play",
            question_interpreted="What should I play here?",
            answer_summary=" ".join(answer_parts),
            detailed_analysis={
                'best_move': best_move,
                'intent': analysis.primary_intent.value,
                'achievements': analysis.achievements,
                'alternatives': alternatives,
            },
            evaluation=analysis.eval_after,
            evaluation_description=describe_evaluation(analysis.eval_after),
            best_move=best_move,
            principal_variation=analysis.pv_explanation,
            learning_points=[
                f"Look for moves that {intent_desc}",
                "Consider what each candidate move achieves before choosing",
            ],
            raw_analysis=asdict(analysis)
        )
    
    def _evaluate_position(self, query: ParsedQuery, fen: str) -> ExplanationResult:
        """Give a position evaluation with explanation."""
        self.why_engine._ensure_engine()
        
        # Get evaluation
        eval_data = self.why_engine.engine.get_eval(fen, depth=self.why_engine.depth)
        
        # Extract features
        features = self.why_engine.extract_features(fen)
        
        # Build evaluation
        if eval_data['type'] == 'cp':
            eval_score = eval_data['score'] / 100
        else:
            eval_score = 100 if eval_data['score'] > 0 else -100
        
        eval_desc = describe_evaluation(eval_score)
        
        answer_parts = [eval_desc + "."]
        
        # Material
        mat_diff = features.material_balance
        if abs(mat_diff) >= 100:
            piece = "pawn" if abs(mat_diff) < 300 else "piece"
            side = "White" if mat_diff > 0 else "Black"
            answer_parts.append(f"{side} is up a {piece}.")
        elif abs(mat_diff) < 50:
            answer_parts.append("Material is equal.")
        
        # Development
        dev_diff = features.white_developed_pieces - features.black_developed_pieces
        if abs(dev_diff) >= 2:
            side = "White" if dev_diff > 0 else "Black"
            answer_parts.append(f"{side} has a significant development advantage.")
        
        # King safety
        white_king_ok = features.white_king_attackers < 2
        black_king_ok = features.black_king_attackers < 2
        if not white_king_ok:
            answer_parts.append("White's king is under pressure.")
        if not black_king_ok:
            answer_parts.append("Black's king is under pressure.")
        
        # Activity
        activity_diff = features.white_mobility - features.black_mobility
        if abs(activity_diff) > 10:
            side = "White" if activity_diff > 0 else "Black"
            answer_parts.append(f"{side} has more active pieces.")
        
        return ExplanationResult(
            question_type="evaluate",
            question_interpreted="Who is better and why?",
            answer_summary=" ".join(answer_parts),
            detailed_analysis={
                'evaluation': eval_score,
                'material_balance': mat_diff,
                'white_mobility': features.white_mobility,
                'black_mobility': features.black_mobility,
                'white_development': features.white_developed_pieces,
                'black_development': features.black_developed_pieces,
                'white_king_attackers': features.white_king_attackers,
                'black_king_attackers': features.black_king_attackers,
            },
            evaluation=eval_score,
            evaluation_description=eval_desc,
            learning_points=[
                "Evaluation considers material, piece activity, king safety, and pawn structure",
                "A position can be equal in material but winning due to other factors",
            ]
        )
    
    def _find_tactics(self, query: ParsedQuery, fen: str) -> ExplanationResult:
        """Find tactical opportunities in the position."""
        self.why_engine._ensure_engine()
        
        board = chess.Board(fen)
        
        # Get best moves (tactics usually show up as best moves)
        top_moves = self.why_engine.engine.get_best_moves(fen, n=3, depth=self.why_engine.depth)
        
        if not top_moves:
            return ExplanationResult(
                question_type="find_tactic",
                question_interpreted="Is there a tactic here?",
                answer_summary="Unable to analyze this position."
            )
        
        best = top_moves[0]
        best_move = best['san']
        best_eval = best['score'] / 100 if best['type'] == 'cp' else (100 if best['score'] > 0 else -100)
        
        # Get current eval
        current_eval_data = self.why_engine.engine.get_eval(fen, depth=self.why_engine.depth)
        current_eval = current_eval_data['score'] / 100 if current_eval_data['type'] == 'cp' else 0
        
        # Analyze for tactics
        analysis = self.why_engine.analyze_move(fen, best_move)
        
        # Check if there's a significant tactic
        is_tactical = len(analysis.tactical_patterns) > 0 or analysis.is_sacrifice
        eval_jump = abs(best_eval - current_eval) > 1.0  # Big eval swing suggests tactic
        
        answer_parts = []
        
        if is_tactical or eval_jump:
            answer_parts.append(f"Yes! There's a tactical opportunity: {best_move}.")
            
            if analysis.tactical_patterns:
                for pattern in analysis.tactical_patterns:
                    answer_parts.append(f"This involves a {pattern.pattern_type}: {pattern.description}.")
            
            if analysis.is_sacrifice:
                answer_parts.append("This involves a sacrifice.")
                if analysis.compensation_types:
                    comp = analysis.compensation_types[0].value.replace('_', ' ')
                    answer_parts.append(f"The compensation is {comp}.")
            
            if analysis.achievements:
                answer_parts.append(f"It {', '.join(analysis.achievements).lower()}.")
        else:
            answer_parts.append("No obvious tactics in this position.")
            answer_parts.append(f"The best move is {best_move}, which is more positional.")
        
        return ExplanationResult(
            question_type="find_tactic",
            question_interpreted="Are there any tactics here?",
            answer_summary=" ".join(answer_parts),
            detailed_analysis={
                'has_tactic': is_tactical or eval_jump,
                'tactical_move': best_move if (is_tactical or eval_jump) else None,
                'patterns': [p.pattern_type for p in analysis.tactical_patterns],
            },
            evaluation=best_eval,
            evaluation_description=describe_evaluation(best_eval),
            best_move=best_move,
            principal_variation=analysis.pv_explanation,
            learning_points=[
                "Look for checks, captures, and threats - especially in combination",
                "Big evaluation swings often indicate tactical opportunities",
            ]
        )
    
    def _explain_concept(self, query: ParsedQuery, fen: str) -> ExplanationResult:
        """Explain a chess concept."""
        concept_name = query.concept_asked
        
        if not concept_name:
            return ExplanationResult(
                question_type="explain_concept",
                question_interpreted="Explain a chess concept",
                answer_summary="Please specify which concept you'd like explained."
            )
        
        # Get concept definition
        concept = get_concept_explanation(concept_name)
        
        if not concept:
            # Try variations
            normalized = concept_name.lower().replace(' ', '_')
            concept = CHESS_CONCEPTS.get(normalized)
        
        if not concept:
            return ExplanationResult(
                question_type="explain_concept",
                question_interpreted=f"Explain: {concept_name}",
                answer_summary=f"I don't have a detailed explanation for '{concept_name}' in my knowledge base."
            )
        
        answer_parts = [
            f"A {concept.name.lower()} is when {concept.description.lower()}.",
            concept.how_to_explain
        ]
        
        if concept.typical_signs:
            answer_parts.append("You can recognize it by: " + concept.typical_signs[0] + ".")
        
        return ExplanationResult(
            question_type="explain_concept",
            question_interpreted=f"What is a {concept_name}?",
            answer_summary=" ".join(answer_parts),
            detailed_analysis={
                'concept_name': concept.name,
                'category': concept.category.value,
                'typical_signs': concept.typical_signs,
                'common_patterns': concept.common_patterns,
            },
            concepts_involved=[concept.name],
            concept_explanations={concept.name: concept.description},
            learning_points=[
                f"Practice recognizing {concept.name.lower()} patterns",
                "Look for these signs in your games",
            ]
        )
    
    def _explain_plan(self, query: ParsedQuery, fen: str) -> ExplanationResult:
        """Explain the strategic plan in a position."""
        self.why_engine._ensure_engine()
        
        # Get features
        features = self.why_engine.extract_features(fen)
        board = chess.Board(fen)
        
        # Get best move for plan indication
        top_moves = self.why_engine.engine.get_best_moves(fen, n=2, depth=self.why_engine.depth)
        
        answer_parts = []
        plans = []
        
        # Analyze pawn structure for plans
        if features.white_passed_pawns > 0 and board.turn == chess.WHITE:
            plans.append("Push and support the passed pawn(s)")
        if features.black_passed_pawns > 0 and board.turn == chess.BLACK:
            plans.append("Push and support the passed pawn(s)")
        
        # Analyze king safety for attack plans
        if board.turn == chess.WHITE and features.black_king_attackers > 0:
            plans.append("Continue the attack on the enemy king")
        if board.turn == chess.BLACK and features.white_king_attackers > 0:
            plans.append("Continue the attack on the enemy king")
        
        # Development plans
        if board.turn == chess.WHITE and features.white_developed_pieces < 4:
            plans.append("Complete development and castle")
        if board.turn == chess.BLACK and features.black_developed_pieces < 4:
            plans.append("Complete development and castle")
        
        # Activity plans
        if board.turn == chess.WHITE and features.white_mobility < features.black_mobility:
            plans.append("Improve piece activity and coordination")
        if board.turn == chess.BLACK and features.black_mobility < features.white_mobility:
            plans.append("Improve piece activity and coordination")
        
        # Default plan
        if not plans:
            plans.append("Improve the worst-placed piece")
            plans.append("Look for pawn breaks to create activity")
        
        answer_parts.append("The main plans in this position are:")
        for i, plan in enumerate(plans[:3], 1):
            answer_parts.append(f"{i}. {plan}")
        
        if top_moves:
            answer_parts.append(f"The engine suggests {top_moves[0]['san']} as the best way forward.")
        
        return ExplanationResult(
            question_type="explain_plan",
            question_interpreted="What is the plan here?",
            answer_summary=" ".join(answer_parts),
            detailed_analysis={
                'plans': plans,
                'suggested_move': top_moves[0]['san'] if top_moves else None,
            },
            best_move=top_moves[0]['san'] if top_moves else "",
            learning_points=[
                "Always have a plan - chess is more than just reacting to threats",
                "The best plans address your weaknesses while exploiting opponent's",
            ]
        )
    
    def _check_move(self, query: ParsedQuery, fen: str) -> ExplanationResult:
        """Quick check if a move is good."""
        move = query.primary_move
        
        if not move:
            return ExplanationResult(
                question_type="check_move",
                question_interpreted="Is this move good?",
                answer_summary="Please specify a move to check."
            )
        
        analysis = self.why_engine.analyze_move(fen, move)
        
        if analysis.is_best_move:
            verdict = f"Yes! {move} is the best move here."
        elif analysis.eval_delta >= -0.2:
            verdict = f"{move} is a good move, very close to the best."
        elif analysis.eval_delta >= -0.5:
            verdict = f"{move} is playable but not the best. {analysis.best_move_san} is better."
        else:
            verdict = f"{move} is not recommended. It loses about {abs(analysis.eval_delta):.1f} pawns."
        
        return ExplanationResult(
            question_type="check_move",
            question_interpreted=f"Is {move} a good move?",
            answer_summary=verdict,
            detailed_analysis={
                'move': move,
                'is_best': analysis.is_best_move,
                'eval_delta': analysis.eval_delta,
            },
            evaluation=analysis.eval_after,
            evaluation_description=describe_evaluation(analysis.eval_after),
            best_move=analysis.best_move_san or move,
        )
    
    def _explain_position(self, query: ParsedQuery, fen: str) -> ExplanationResult:
        """Give a comprehensive position explanation."""
        # Combine multiple analyses
        eval_result = self._evaluate_position(query, fen)
        plan_result = self._explain_plan(query, fen)
        
        answer_parts = [
            eval_result.answer_summary,
            plan_result.answer_summary,
        ]
        
        return ExplanationResult(
            question_type="explain_position",
            question_interpreted="Explain this position",
            answer_summary=" ".join(answer_parts),
            detailed_analysis={
                **eval_result.detailed_analysis,
                **plan_result.detailed_analysis,
            },
            evaluation=eval_result.evaluation,
            evaluation_description=eval_result.evaluation_description,
            best_move=plan_result.best_move,
            learning_points=eval_result.learning_points + plan_result.learning_points,
        )
    
    def _general_response(self, query: ParsedQuery, fen: str, 
                          played_move: str = None) -> ExplanationResult:
        """Handle general/unclear questions."""
        # Try to be helpful by providing a position summary
        return self._evaluate_position(query, fen)
    
    # =========================================================================
    # HELPER METHODS
    # =========================================================================
    
    def _describe_intent(self, intent: MoveIntent) -> str:
        """Convert MoveIntent to natural language."""
        descriptions = {
            MoveIntent.ATTACK: "to build an attack on the enemy position",
            MoveIntent.DEFENSE: "to defend against opponent's threats",
            MoveIntent.DEVELOPMENT: "to develop a piece to an active square",
            MoveIntent.CONTROL: "to control key squares in the center",
            MoveIntent.PREPARATION: "to prepare for future plans",
            MoveIntent.PROPHYLAXIS: "to prevent the opponent's plan",
            MoveIntent.MATERIAL_GAIN: "to win material",
            MoveIntent.SACRIFICE: "to sacrifice material for compensation",
            MoveIntent.SIMPLIFICATION: "to simplify toward a favorable endgame",
            MoveIntent.KING_SAFETY: "to improve king safety",
            MoveIntent.TEMPO: "to gain time by creating threats",
            MoveIntent.ENDGAME_TRANSITION: "to transition to a favorable endgame",
            MoveIntent.WAITING: "to maintain the position and pass the move",
        }
        return descriptions.get(intent, "to improve the position")
    
    def _categorize_mistake(self, analysis: MoveAnalysis) -> str:
        """Categorize the type of mistake."""
        if analysis.eval_delta < -3.0:
            return "blunder"
        elif analysis.eval_delta < -1.0:
            return "mistake"
        elif analysis.eval_delta < -0.5:
            return "inaccuracy"
        else:
            return "slight_inaccuracy"
    
    def _generate_learning_points(self, analysis: MoveAnalysis) -> List[str]:
        """Generate educational takeaways from an analysis."""
        points = []
        
        if analysis.is_sacrifice:
            points.append("Sacrifices can be powerful when you get compensation in activity, attack, or structure")
        
        if analysis.tactical_patterns:
            points.append("Always look for tactical patterns - they can change the game instantly")
        
        if analysis.primary_intent == MoveIntent.DEVELOPMENT:
            points.append("Developing pieces quickly gives you more options and activity")
        
        if analysis.primary_intent == MoveIntent.ATTACK:
            points.append("Coordinating pieces toward the enemy king creates powerful threats")
        
        if not points:
            points.append("Consider the purpose of each move - what does it achieve?")
        
        return points[:2]  # Limit to 2 points
    
    def to_llm_context(self, result: ExplanationResult) -> str:
        """
        Convert an explanation result to context for LLM verbalization.
        
        This creates a structured prompt that the LLM can use to generate
        natural language explanations.
        """
        context = f"""
Chess Analysis Results:
======================
Question Type: {result.question_type}
Interpreted As: {result.question_interpreted}

Answer Summary:
{result.answer_summary}

Evaluation: {result.evaluation:.2f} pawns ({result.evaluation_description})
Best Move: {result.best_move}

Detailed Analysis:
{json.dumps(result.detailed_analysis, indent=2)}

Key Evidence:
{chr(10).join('- ' + e for e in result.evidence)}

Learning Points:
{chr(10).join('- ' + p for p in result.learning_points)}

Instructions: Use this analysis to generate a clear, helpful explanation for the user.
Be conversational but accurate. Use the evidence to support your explanation.
"""
        return context
