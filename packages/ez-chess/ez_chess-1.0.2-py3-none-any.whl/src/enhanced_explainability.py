"""
Enhanced Explainability Service - Integrates deep analysis, fundamentals, and LLM prompts.

This is the RECOMMENDED explainability service for LLM-based explanations.

This module brings together:
1. DeepAnalyzer for multi-move lookahead with explanations
2. Chess Fundamentals library (60+ concepts from Lichess training)
3. Enhanced LLM prompts for thorough responses
4. The existing WhyEngine for move-level analysis

Key improvements over ExplainabilityService (in explainability_service.py):
- Multi-move lookahead: Shows 4-5 moves ahead with explanations for each
- Grounded explanations: Uses comprehensive chess concepts from training resources
- Structured prompts: Provides complete context for LLM to generate accurate responses
- Better analysis: Combines Stockfish evaluation with human-readable interpretations

Usage:
    service = EnhancedExplainabilityService()
    result = service.get_llm_context("Why is Nf3 good?", fen=current_position)
    # result contains structured data + formatted prompt for LLM

For simpler analysis or backward compatibility, use ExplainabilityService
from explainability_service.py.

Module dependencies:
- chess_fundamentals.py: 60+ chess concepts (source of truth for concepts)
- llm_prompts.py: Structured LLM prompts (source of truth for eval descriptions)
- deep_analysis.py: Multi-move lookahead analysis
- why_engine.py: Move-level tactical/strategic analysis
"""

import chess
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field, asdict
import json
import os
import sys

# Add parent for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from src.why_engine import WhyEngine, MoveAnalysis, MoveIntent
    from src.deep_analysis import DeepAnalyzer, DeepAnalysis, format_deep_analysis_for_llm
    from src.chess_fundamentals import (
        ALL_FUNDAMENTALS, ChessFundamental, get_fundamental,
        get_fundamentals_for_position_type, format_fundamental_for_prompt,
        TACTICAL_MOTIFS, POSITIONAL_CONCEPTS, OPENING_PRINCIPLES
    )
    from src.llm_prompts import (
        PromptBuilder, StockfishAnalysis, SYSTEM_PROMPT,
        describe_eval, describe_eval_change, categorize_move_quality,
        inject_relevant_fundamentals
    )
    from src.query_understanding import QueryParser, QueryType
except ImportError:
    from why_engine import WhyEngine, MoveAnalysis, MoveIntent
    from deep_analysis import DeepAnalyzer, DeepAnalysis, format_deep_analysis_for_llm
    from chess_fundamentals import (
        ALL_FUNDAMENTALS, ChessFundamental, get_fundamental,
        get_fundamentals_for_position_type, format_fundamental_for_prompt,
        TACTICAL_MOTIFS, POSITIONAL_CONCEPTS, OPENING_PRINCIPLES
    )
    from llm_prompts import (
        PromptBuilder, StockfishAnalysis, SYSTEM_PROMPT,
        describe_eval, describe_eval_change, categorize_move_quality,
        inject_relevant_fundamentals
    )
    from query_understanding import QueryParser, QueryType


@dataclass
class LLMExplanationContext:
    """Complete context package for LLM to generate explanation."""
    
    # The formatted prompt ready for LLM
    prompt: str
    
    # System prompt
    system_prompt: str
    
    # Structured analysis data
    analysis_data: Dict[str, Any]
    
    # Relevant fundamentals
    fundamentals: List[str]
    
    # Key facts the LLM should know
    key_facts: List[str]
    
    # What question is being answered
    question_type: str
    question_interpreted: str
    
    # Raw data for tools
    stockfish_eval: float
    best_move: str
    principal_variation: List[str]
    pv_explanations: List[Dict]


class EnhancedExplainabilityService:
    """
    Enhanced explainability service with deep analysis and LLM-ready prompts.
    
    Provides:
    1. Multi-move lookahead with explanations for each move
    2. Relevant chess fundamentals for grounding
    3. Comprehensive LLM prompts with all context
    """
    
    def __init__(self, engine_depth: int = 18):
        """Initialize the enhanced service."""
        self.why_engine = WhyEngine(depth=engine_depth)
        self.deep_analyzer = DeepAnalyzer(self.why_engine.engine)
        self.query_parser = QueryParser()
        self.depth = engine_depth
    
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
    
    def get_llm_context(
        self, 
        question: str, 
        fen: str,
        move: Optional[str] = None,
        compare_move: Optional[str] = None
    ) -> LLMExplanationContext:
        """
        Get complete context for LLM to generate an explanation.
        
        Args:
            question: User's question
            fen: Position in FEN
            move: Specific move being asked about (optional)
            compare_move: Second move for comparison (optional)
            
        Returns:
            LLMExplanationContext with prompt and all structured data
        """
        # Parse the question
        parsed = self.query_parser.parse(question)
        
        # Use parsed move if not provided
        if not move and parsed.primary_move:
            move = parsed.primary_move
        if not compare_move and parsed.secondary_move:
            compare_move = parsed.secondary_move
        
        # Get deep analysis
        deep = self.deep_analyzer.analyze_position(
            fen, 
            depth=self.depth,
            num_pv_moves=5,
            num_alternatives=3
        )
        
        # Build stockfish analysis object for prompts
        stockfish = self._build_stockfish_analysis(deep)
        
        # Get relevant fundamentals
        fundamentals = self._get_relevant_fundamentals(deep, parsed.query_type)
        
        # Route to appropriate prompt builder
        if parsed.query_type == QueryType.COMPARE_MOVES and compare_move:
            return self._build_compare_context(
                parsed, fen, move, compare_move, deep, stockfish, fundamentals
            )
        
        elif parsed.query_type == QueryType.WHY_BAD:
            return self._build_why_bad_context(
                parsed, fen, move, deep, stockfish, fundamentals
            )
        
        elif parsed.query_type == QueryType.WHAT_TO_PLAY:
            return self._build_best_move_context(
                parsed, fen, deep, stockfish, fundamentals
            )
        
        elif parsed.query_type == QueryType.EXPLAIN_PLAN:
            return self._build_plan_context(
                parsed, fen, deep, stockfish, fundamentals
            )
        
        elif parsed.query_type == QueryType.EVALUATE:
            return self._build_eval_context(
                parsed, fen, deep, stockfish, fundamentals
            )
        
        elif parsed.query_type == QueryType.FIND_TACTIC:
            return self._build_tactics_context(
                parsed, fen, deep, stockfish, fundamentals
            )
        
        elif parsed.query_type == QueryType.EXPLAIN_CONCEPT:
            return self._build_concept_context(parsed, fen, fundamentals)
        
        else:
            # Default: explain move
            return self._build_explain_move_context(
                parsed, fen, move, deep, stockfish, fundamentals
            )
    
    def _build_stockfish_analysis(self, deep: DeepAnalysis) -> StockfishAnalysis:
        """Convert DeepAnalysis to StockfishAnalysis for prompt builder."""
        pv_explanations = []
        for exp in deep.pv_explanations:
            pv_explanations.append(
                f"{exp.what_it_does} ({exp.role.value})"
            )
        
        return StockfishAnalysis(
            current_eval=deep.current_eval,
            best_move=deep.best_move,
            best_move_eval=deep.best_move_eval,
            principal_variation=deep.principal_variation,
            pv_explanations=pv_explanations,
            alternative_moves=deep.alternative_moves,
            threats=deep.threats + deep.opponent_threats,
            position_features={
                'material': deep.material_balance,
                'white_king_safety': deep.king_safety.get('White', 'Normal'),
                'black_king_safety': deep.king_safety.get('Black', 'Normal'),
                'pawn_structure': ', '.join(deep.pawn_structure_notes) if deep.pawn_structure_notes else 'Normal',
                'piece_activity': deep.piece_activity,
                'open_files': ', '.join(deep.open_files) if deep.open_files else 'None',
            }
        )
    
    def _get_relevant_fundamentals(
        self, 
        deep: DeepAnalysis, 
        query_type: QueryType
    ) -> List[ChessFundamental]:
        """Get fundamentals relevant to this position and question."""
        fundamentals = []
        
        # Based on game phase
        is_opening = deep.game_phase == "opening"
        is_endgame = deep.game_phase == "endgame"
        
        # Check if attacking/defensive
        has_attack = len(deep.threats) > 1
        is_defensive = len(deep.opponent_threats) > 1
        
        # Get phase-appropriate fundamentals
        phase_fundamentals = get_fundamentals_for_position_type(
            is_opening=is_opening,
            is_endgame=is_endgame,
            has_attack=has_attack,
            is_defensive=is_defensive
        )
        
        # Add based on position features
        if deep.tactical_motifs:
            for motif_name in TACTICAL_MOTIFS:
                if motif_name not in [f.name for f in fundamentals]:
                    fund = get_fundamental(motif_name)
                    if fund:
                        fundamentals.append(fund)
        
        # Add positional concepts based on features
        if 'passed pawn' in str(deep.pawn_structure_notes).lower():
            fund = get_fundamental('passed_pawn')
            if fund:
                fundamentals.append(fund)
        
        if 'isolated' in str(deep.pawn_structure_notes).lower():
            fund = get_fundamental('isolated_pawn')
            if fund:
                fundamentals.append(fund)
        
        # Add phase fundamentals
        fundamentals.extend(phase_fundamentals[:5])
        
        # Deduplicate
        seen = set()
        unique = []
        for f in fundamentals:
            if f.name not in seen:
                seen.add(f.name)
                unique.append(f)
        
        return unique[:7]  # Limit to 7 most relevant
    
    def _build_explain_move_context(
        self,
        parsed,
        fen: str,
        move: Optional[str],
        deep: DeepAnalysis,
        stockfish: StockfishAnalysis,
        fundamentals: List[ChessFundamental]
    ) -> LLMExplanationContext:
        """Build context for explaining a move."""
        
        # If no move specified, use best move
        if not move:
            move = deep.best_move
        
        # Get move-specific analysis
        move_analysis = None
        if move:
            try:
                move_analysis = self.deep_analyzer.analyze_move(fen, move, depth=self.depth)
            except:
                pass
        
        # Build the prompt
        prompt_builder = PromptBuilder(stockfish, fen)
        prompt = prompt_builder.build_explain_move_prompt(move or deep.best_move)
        
        # Inject relevant fundamentals
        fund_strings = [f.name + ": " + f.definition for f in fundamentals[:3]]
        prompt = inject_relevant_fundamentals(prompt, fund_strings)
        
        # Key facts
        key_facts = [
            f"Position evaluation: {describe_eval(deep.current_eval)}",
            f"Best move according to engine: {deep.best_move}",
            f"Material: {deep.material_balance}",
            f"Game phase: {deep.game_phase}",
        ]
        
        if move_analysis:
            key_facts.append(f"Move quality: {move_analysis.get('quality', 'Unknown')}")
            if move_analysis.get('continuation'):
                key_facts.append(f"Continuation: {' '.join(move_analysis['continuation'][:3])}")
        
        # PV explanations
        pv_exps = [
            {
                'move': exp.move_san,
                'role': exp.role.value,
                'what': exp.what_it_does,
                'why': exp.why_it_matters
            }
            for exp in deep.pv_explanations
        ]
        
        return LLMExplanationContext(
            prompt=prompt,
            system_prompt=SYSTEM_PROMPT,
            analysis_data={
                'deep_analysis': format_deep_analysis_for_llm(deep),
                'move_analysis': move_analysis,
            },
            fundamentals=[f.name for f in fundamentals],
            key_facts=key_facts,
            question_type="explain_move",
            question_interpreted=f"Explain the move {move or deep.best_move}",
            stockfish_eval=deep.current_eval,
            best_move=deep.best_move,
            principal_variation=deep.principal_variation,
            pv_explanations=pv_exps
        )
    
    def _build_compare_context(
        self,
        parsed,
        fen: str,
        move1: str,
        move2: str,
        deep: DeepAnalysis,
        stockfish: StockfishAnalysis,
        fundamentals: List[ChessFundamental]
    ) -> LLMExplanationContext:
        """Build context for comparing two moves."""
        
        # Analyze both moves
        analysis1 = self.deep_analyzer.analyze_move(fen, move1, depth=self.depth)
        analysis2 = self.deep_analyzer.analyze_move(fen, move2, depth=self.depth)
        
        # Build comparison prompt
        prompt_builder = PromptBuilder(stockfish, fen)
        
        move1_pv = ' '.join(analysis1.get('continuation', [])[:3])
        move2_pv = ' '.join(analysis2.get('continuation', [])[:3])
        
        prompt = prompt_builder.build_compare_moves_prompt(
            move1=move1,
            move1_eval=analysis1.get('eval_after', 0),
            move1_pv=move1_pv,
            move1_idea=analysis1.get('quality', 'Unknown'),
            move2=move2,
            move2_eval=analysis2.get('eval_after', 0),
            move2_pv=move2_pv,
            move2_idea=analysis2.get('quality', 'Unknown')
        )
        
        fund_strings = [f.name + ": " + f.definition for f in fundamentals[:3]]
        prompt = inject_relevant_fundamentals(prompt, fund_strings)
        
        key_facts = [
            f"{move1} evaluation: {analysis1.get('eval_after', 0):+.2f}",
            f"{move2} evaluation: {analysis2.get('eval_after', 0):+.2f}",
            f"Engine's best: {deep.best_move}",
            f"{move1} quality: {analysis1.get('quality', 'Unknown')}",
            f"{move2} quality: {analysis2.get('quality', 'Unknown')}",
        ]
        
        return LLMExplanationContext(
            prompt=prompt,
            system_prompt=SYSTEM_PROMPT,
            analysis_data={
                'move1': analysis1,
                'move2': analysis2,
                'best_move': deep.best_move
            },
            fundamentals=[f.name for f in fundamentals],
            key_facts=key_facts,
            question_type="compare_moves",
            question_interpreted=f"Compare {move1} vs {move2}",
            stockfish_eval=deep.current_eval,
            best_move=deep.best_move,
            principal_variation=deep.principal_variation,
            pv_explanations=[]
        )
    
    def _build_why_bad_context(
        self,
        parsed,
        fen: str,
        move: str,
        deep: DeepAnalysis,
        stockfish: StockfishAnalysis,
        fundamentals: List[ChessFundamental]
    ) -> LLMExplanationContext:
        """Build context for explaining why a move is bad."""
        
        if not move:
            return self._build_explain_move_context(parsed, fen, None, deep, stockfish, fundamentals)
        
        # Analyze the bad move
        move_analysis = self.deep_analyzer.analyze_move(fen, move, depth=self.depth)
        
        # Get the refutation sequence
        continuation = move_analysis.get('continuation', [])
        
        # Build prompt
        prompt_builder = PromptBuilder(stockfish, fen)
        prompt = prompt_builder.build_why_bad_prompt(
            bad_move=move,
            bad_eval=move_analysis.get('eval_after', 0),
            bad_continuation=' '.join(continuation[:4]),
            best_move=deep.best_move,
            best_eval=deep.best_move_eval,
            refutation=continuation[0] if continuation else "N/A"
        )
        
        fund_strings = [f.name + ": " + f.definition for f in fundamentals[:3]]
        prompt = inject_relevant_fundamentals(prompt, fund_strings)
        
        eval_loss = abs(deep.best_move_eval - move_analysis.get('eval_after', 0))
        
        key_facts = [
            f"Move {move} evaluation: {move_analysis.get('eval_after', 0):+.2f}",
            f"Best move {deep.best_move} evaluation: {deep.best_move_eval:+.2f}",
            f"Evaluation loss: {eval_loss:.2f} pawns",
            f"Move quality: {move_analysis.get('quality', 'Unknown')}",
            f"Refutation: {continuation[0] if continuation else 'N/A'}",
        ]
        
        return LLMExplanationContext(
            prompt=prompt,
            system_prompt=SYSTEM_PROMPT,
            analysis_data={
                'bad_move_analysis': move_analysis,
                'best_move': deep.best_move,
                'eval_loss': eval_loss
            },
            fundamentals=[f.name for f in fundamentals],
            key_facts=key_facts,
            question_type="why_bad",
            question_interpreted=f"Why is {move} a mistake?",
            stockfish_eval=deep.current_eval,
            best_move=deep.best_move,
            principal_variation=deep.principal_variation,
            pv_explanations=[]
        )
    
    def _build_best_move_context(
        self,
        parsed,
        fen: str,
        deep: DeepAnalysis,
        stockfish: StockfishAnalysis,
        fundamentals: List[ChessFundamental]
    ) -> LLMExplanationContext:
        """Build context for 'what should I play?' questions."""
        
        # Get the best move explanation
        return self._build_explain_move_context(
            parsed, fen, deep.best_move, deep, stockfish, fundamentals
        )
    
    def _build_plan_context(
        self,
        parsed,
        fen: str,
        deep: DeepAnalysis,
        stockfish: StockfishAnalysis,
        fundamentals: List[ChessFundamental]
    ) -> LLMExplanationContext:
        """Build context for explaining the plan."""
        
        prompt_builder = PromptBuilder(stockfish, fen)
        prompt = prompt_builder.build_find_plan_prompt()
        
        # Add strategic fundamentals
        strategic_funds = [
            get_fundamental('space_advantage'),
            get_fundamental('piece_activity'),
            get_fundamental('pawn_breaks'),
            get_fundamental('initiative'),
        ]
        strategic_funds = [f for f in strategic_funds if f]
        fund_strings = [f.name + ": " + f.how_to_apply[0] for f in strategic_funds[:3]]
        prompt = inject_relevant_fundamentals(prompt, fund_strings)
        
        key_facts = [
            f"Game phase: {deep.game_phase}",
            f"Best continuation: {' '.join(deep.principal_variation[:3])}",
            f"Key threats: {', '.join(deep.threats[:2]) if deep.threats else 'None immediate'}",
            f"Position type: {deep.piece_activity}",
        ]
        
        if deep.open_files:
            key_facts.append(f"Open files: {', '.join(deep.open_files[:2])}")
        
        pv_exps = [
            {
                'move': exp.move_san,
                'role': exp.role.value,
                'what': exp.what_it_does,
                'why': exp.why_it_matters
            }
            for exp in deep.pv_explanations
        ]
        
        return LLMExplanationContext(
            prompt=prompt,
            system_prompt=SYSTEM_PROMPT,
            analysis_data={
                'deep_analysis': format_deep_analysis_for_llm(deep),
            },
            fundamentals=[f.name for f in fundamentals],
            key_facts=key_facts,
            question_type="explain_plan",
            question_interpreted="What is the plan in this position?",
            stockfish_eval=deep.current_eval,
            best_move=deep.best_move,
            principal_variation=deep.principal_variation,
            pv_explanations=pv_exps
        )
    
    def _build_eval_context(
        self,
        parsed,
        fen: str,
        deep: DeepAnalysis,
        stockfish: StockfishAnalysis,
        fundamentals: List[ChessFundamental]
    ) -> LLMExplanationContext:
        """Build context for position evaluation."""
        
        prompt_builder = PromptBuilder(stockfish, fen)
        prompt = prompt_builder.build_position_eval_prompt()
        
        fund_strings = [f.name + ": " + f.definition for f in fundamentals[:3]]
        prompt = inject_relevant_fundamentals(prompt, fund_strings)
        
        key_facts = [
            f"Evaluation: {describe_eval(deep.current_eval)} ({deep.current_eval:+.2f})",
            f"Material: {deep.material_balance}",
            f"Piece activity: {deep.piece_activity}",
            f"White king: {deep.king_safety.get('White', 'Normal')}",
            f"Black king: {deep.king_safety.get('Black', 'Normal')}",
        ]
        
        if deep.pawn_structure_notes:
            key_facts.append(f"Pawn notes: {', '.join(deep.pawn_structure_notes[:2])}")
        
        return LLMExplanationContext(
            prompt=prompt,
            system_prompt=SYSTEM_PROMPT,
            analysis_data={
                'deep_analysis': format_deep_analysis_for_llm(deep),
            },
            fundamentals=[f.name for f in fundamentals],
            key_facts=key_facts,
            question_type="evaluate",
            question_interpreted="Evaluate this position",
            stockfish_eval=deep.current_eval,
            best_move=deep.best_move,
            principal_variation=deep.principal_variation,
            pv_explanations=[]
        )
    
    def _build_tactics_context(
        self,
        parsed,
        fen: str,
        deep: DeepAnalysis,
        stockfish: StockfishAnalysis,
        fundamentals: List[ChessFundamental]
    ) -> LLMExplanationContext:
        """Build context for finding tactics."""
        
        # Get tactical motif fundamentals
        tactical_funds = list(TACTICAL_MOTIFS.values())[:5]
        
        # Analyze best move for tactical content
        move_analysis = self.why_engine.analyze_move(fen, deep.best_move)
        
        tactic_type = "tactical opportunity"
        if move_analysis.tactical_patterns:
            tactic_type = move_analysis.tactical_patterns[0].pattern_type
        elif deep.tactical_motifs:
            tactic_type = deep.tactical_motifs[0]
        
        prompt_builder = PromptBuilder(stockfish, fen)
        prompt = prompt_builder.build_tactical_prompt(
            tactic_type=tactic_type,
            key_move=deep.best_move,
            target="material or checkmate"
        )
        
        fund_strings = [f.name + ": " + f.definition for f in tactical_funds[:4]]
        prompt = inject_relevant_fundamentals(prompt, fund_strings)
        
        key_facts = [
            f"Best move: {deep.best_move}",
            f"Tactical motifs found: {', '.join(deep.tactical_motifs) if deep.tactical_motifs else 'None obvious'}",
            f"Continuation: {' '.join(deep.principal_variation[:4])}",
        ]
        
        return LLMExplanationContext(
            prompt=prompt,
            system_prompt=SYSTEM_PROMPT,
            analysis_data={
                'tactical_patterns': [p.pattern_type for p in move_analysis.tactical_patterns],
                'threats': move_analysis.threats_created,
            },
            fundamentals=[f.name for f in tactical_funds],
            key_facts=key_facts,
            question_type="find_tactics",
            question_interpreted="Find tactics in this position",
            stockfish_eval=deep.current_eval,
            best_move=deep.best_move,
            principal_variation=deep.principal_variation,
            pv_explanations=[]
        )
    
    def _build_concept_context(
        self,
        parsed,
        fen: str,
        fundamentals: List[ChessFundamental]
    ) -> LLMExplanationContext:
        """Build context for explaining a chess concept."""
        
        concept_name = parsed.primary_move or "chess strategy"
        
        # Try to find the concept
        concept = get_fundamental(concept_name.lower().replace(' ', '_'))
        
        if concept:
            concept_text = f"""
Explain the chess concept: **{concept.name}**

Definition: {concept.definition}

Why it matters: {concept.why_it_matters}

How to recognize:
{chr(10).join('- ' + r for r in concept.how_to_recognize)}

How to apply:
{chr(10).join('- ' + a for a in concept.how_to_apply)}

Common mistakes:
{chr(10).join('- ' + m for m in concept.common_mistakes)}

Related concepts: {', '.join(concept.related_concepts)}
"""
            if concept.example_explanation:
                concept_text += f"\nExample: {concept.example_explanation}"
        else:
            concept_text = f"Explain the chess concept: {concept_name}"
        
        prompt = f"""
{SYSTEM_PROMPT}

=== YOUR TASK ===
{concept_text}

Provide a clear, educational explanation that helps the player understand and apply this concept.
"""
        
        return LLMExplanationContext(
            prompt=prompt,
            system_prompt=SYSTEM_PROMPT,
            analysis_data={
                'concept': concept_name,
                'found': concept is not None
            },
            fundamentals=[concept.name] if concept else [],
            key_facts=[concept.definition] if concept else [f"Concept: {concept_name}"],
            question_type="explain_concept",
            question_interpreted=f"Explain the concept: {concept_name}",
            stockfish_eval=0,
            best_move="",
            principal_variation=[],
            pv_explanations=[]
        )
    
    def get_simple_analysis(self, fen: str, move: Optional[str] = None) -> Dict[str, Any]:
        """
        Get simple analysis without LLM prompt building.
        
        Useful for quick checks and testing.
        """
        deep = self.deep_analyzer.analyze_position(fen, depth=self.depth)
        
        result = {
            'fen': fen,
            'eval': deep.current_eval,
            'eval_description': describe_eval(deep.current_eval),
            'best_move': deep.best_move,
            'principal_variation': deep.principal_variation,
            'pv_explanations': [
                {
                    'move': e.move_san,
                    'role': e.role.value,
                    'what': e.what_it_does,
                    'why': e.why_it_matters
                }
                for e in deep.pv_explanations
            ],
            'alternatives': deep.alternative_moves,
            'threats': deep.threats,
            'material': deep.material_balance,
            'phase': deep.game_phase,
            'king_safety': deep.king_safety,
            'pawn_structure': deep.pawn_structure_notes,
            'tactics': deep.tactical_motifs,
        }
        
        if move:
            move_result = self.deep_analyzer.analyze_move(fen, move, depth=self.depth)
            result['move_analysis'] = move_result
        
        return result
