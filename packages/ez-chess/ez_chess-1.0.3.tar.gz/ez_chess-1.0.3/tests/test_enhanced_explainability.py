"""
Test Suite for Enhanced Explainability System

This comprehensive test suite validates:
1. Chess Fundamentals Library - All 60+ concepts load correctly
2. Deep Analysis Module - Multi-move lookahead and explanations
3. LLM Prompts - Prompt building and formatting
4. Enhanced Explainability Service - Full integration

NOTE: This test does NOT call the LLM - it only validates that all data
is correctly gathered and formatted for LLM consumption.

Run: python tests/test_enhanced_explainability.py
"""

import sys
import os
import unittest
import json
from typing import Dict, Any

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.chess_fundamentals import (
    ALL_FUNDAMENTALS, ChessFundamental, ConceptCategory,
    get_fundamental, get_related_fundamentals,
    get_fundamentals_for_position_type, format_fundamental_for_prompt,
    get_all_fundamentals_summary,
    OPENING_PRINCIPLES, PIECE_PLACEMENT, PAWN_STRUCTURE,
    KING_SAFETY, ATTACKING_PRINCIPLES, DEFENSIVE_PRINCIPLES,
    POSITIONAL_CONCEPTS, ENDGAME_FUNDAMENTALS, TACTICAL_MOTIFS
)


class TestChessFundamentals(unittest.TestCase):
    """Test the chess fundamentals library."""
    
    def test_fundamentals_count(self):
        """Verify we have a substantial number of fundamentals."""
        total = len(ALL_FUNDAMENTALS)
        print(f"\n✓ Total fundamentals loaded: {total}")
        self.assertGreaterEqual(total, 50, "Should have at least 50 fundamentals")
    
    def test_category_coverage(self):
        """Verify all categories have fundamentals."""
        categories = [
            ("Opening Principles", OPENING_PRINCIPLES),
            ("Piece Placement", PIECE_PLACEMENT),
            ("Pawn Structure", PAWN_STRUCTURE),
            ("King Safety", KING_SAFETY),
            ("Attacking", ATTACKING_PRINCIPLES),
            ("Defensive", DEFENSIVE_PRINCIPLES),
            ("Positional", POSITIONAL_CONCEPTS),
            ("Endgame", ENDGAME_FUNDAMENTALS),
            ("Tactical Motifs", TACTICAL_MOTIFS),
        ]
        
        print("\n✓ Category coverage:")
        for name, cat in categories:
            count = len(cat)
            print(f"  - {name}: {count} concepts")
            self.assertGreaterEqual(count, 3, f"{name} should have at least 3 concepts")
    
    def test_fundamental_structure(self):
        """Verify each fundamental has required fields."""
        print("\n✓ Validating fundamental structure...")
        
        for name, fund in ALL_FUNDAMENTALS.items():
            self.assertIsInstance(fund, ChessFundamental)
            self.assertTrue(fund.name, f"{name} should have a name")
            self.assertTrue(fund.definition, f"{name} should have a definition")
            self.assertTrue(fund.why_it_matters, f"{name} should have why_it_matters")
            self.assertIsInstance(fund.how_to_recognize, list)
            self.assertIsInstance(fund.how_to_apply, list)
            self.assertGreaterEqual(len(fund.how_to_recognize), 1)
            self.assertGreaterEqual(len(fund.how_to_apply), 1)
        
        print(f"  All {len(ALL_FUNDAMENTALS)} fundamentals have valid structure")
    
    def test_get_fundamental(self):
        """Test retrieving fundamentals by name."""
        # Test exact match
        fork = get_fundamental("fork")
        self.assertIsNotNone(fork)
        self.assertEqual(fork.name, "Fork")
        
        # Test with spaces
        passed_pawn = get_fundamental("passed pawn")
        self.assertIsNotNone(passed_pawn)
        
        # Test with underscores
        bishop_pair = get_fundamental("bishop_pair")
        self.assertIsNotNone(bishop_pair)
        
        print("\n✓ get_fundamental() works correctly")
    
    def test_get_related_fundamentals(self):
        """Test getting related fundamentals."""
        related = get_related_fundamentals("fork")
        self.assertIsInstance(related, list)
        print(f"\n✓ Fork is related to: {[f.name for f in related]}")
    
    def test_fundamentals_for_position_type(self):
        """Test getting fundamentals based on position type."""
        # Opening
        opening_funds = get_fundamentals_for_position_type(is_opening=True)
        self.assertGreaterEqual(len(opening_funds), 5)
        print(f"\n✓ Opening fundamentals: {len(opening_funds)}")
        
        # Endgame
        endgame_funds = get_fundamentals_for_position_type(is_endgame=True)
        self.assertGreaterEqual(len(endgame_funds), 5)
        print(f"✓ Endgame fundamentals: {len(endgame_funds)}")
        
        # Attack
        attack_funds = get_fundamentals_for_position_type(has_attack=True)
        self.assertGreaterEqual(len(attack_funds), 5)
        print(f"✓ Attack fundamentals: {len(attack_funds)}")
    
    def test_format_for_prompt(self):
        """Test formatting fundamentals for LLM prompts."""
        fork = get_fundamental("fork")
        formatted = format_fundamental_for_prompt(fork)
        
        self.assertIn("Fork", formatted)
        self.assertIn("Definition:", formatted)
        self.assertIn("Why it matters:", formatted)
        
        print(f"\n✓ Formatted fundamental sample:\n{formatted[:200]}...")
    
    def test_summary_generation(self):
        """Test generating summary of all fundamentals."""
        summary = get_all_fundamentals_summary()
        
        self.assertIn("opening", summary.lower())
        self.assertIn("tactical", summary.lower())
        
        print(f"\n✓ Summary length: {len(summary)} characters")
        print(f"  First 300 chars:\n{summary[:300]}...")


class TestLLMPrompts(unittest.TestCase):
    """Test the LLM prompt building system."""
    
    def setUp(self):
        """Set up test fixtures."""
        from src.llm_prompts import (
            PromptBuilder, StockfishAnalysis, SYSTEM_PROMPT,
            describe_eval, describe_eval_change, categorize_move_quality,
            inject_relevant_fundamentals
        )
        self.PromptBuilder = PromptBuilder
        self.StockfishAnalysis = StockfishAnalysis
        self.SYSTEM_PROMPT = SYSTEM_PROMPT
        self.describe_eval = describe_eval
        self.describe_eval_change = describe_eval_change
        self.categorize_move_quality = categorize_move_quality
        self.inject_relevant_fundamentals = inject_relevant_fundamentals
        
        # Test position
        self.test_fen = "r1bqkbnr/pppp1ppp/2n5/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R w KQkq - 2 3"
        
        # Mock stockfish analysis
        self.mock_analysis = self.StockfishAnalysis(
            current_eval=0.3,
            best_move="Bb5",
            best_move_eval=0.35,
            principal_variation=["Bb5", "a6", "Ba4", "Nf6", "O-O"],
            pv_explanations=[
                "Develops bishop and pins knight",
                "Chases the bishop",
                "Maintains pin",
                "Develops knight",
                "Castles to safety"
            ],
            alternative_moves=[
                {"move": "Bc4", "eval": 0.25, "note": "Italian Game"},
                {"move": "d4", "eval": 0.2, "note": "Scotch Game"},
            ],
            threats=["Knight on c6 is pinned to the king after Bb5"],
            position_features={
                "material": "Equal",
                "white_king_safety": "King in center, should castle",
                "black_king_safety": "King in center, should castle",
                "pawn_structure": "Normal",
                "piece_activity": "White slightly more developed",
                "open_files": "e-file half-open for both",
            }
        )
    
    def test_system_prompt_exists(self):
        """Verify system prompt is defined."""
        self.assertIsNotNone(self.SYSTEM_PROMPT)
        self.assertGreater(len(self.SYSTEM_PROMPT), 500)
        self.assertIn("expert chess coach", self.SYSTEM_PROMPT.lower())
        print(f"\n✓ System prompt: {len(self.SYSTEM_PROMPT)} chars")
    
    def test_describe_eval(self):
        """Test evaluation description."""
        test_cases = [
            (0.0, "equal"),
            (0.5, "slightly better for White"),
            (-0.5, "slightly better for Black"),
            (2.0, "better for White"),
            (-3.5, "winning for Black"),
        ]
        
        print("\n✓ Evaluation descriptions:")
        for eval_val, expected_word in test_cases:
            desc = self.describe_eval(eval_val)
            self.assertIn(expected_word.split()[-1].lower(), desc.lower())
            print(f"  {eval_val:+.1f} → {desc}")
    
    def test_categorize_move_quality(self):
        """Test move quality categorization."""
        # Best move
        quality = self.categorize_move_quality(0.3, 0.3, True)
        self.assertIn("excellent", quality.lower())
        
        # Inaccuracy
        quality = self.categorize_move_quality(-0.2, 0.3, True)
        self.assertIn("inaccura", quality.lower())
        
        # Blunder
        quality = self.categorize_move_quality(-2.0, 0.3, True)
        self.assertIn("blunder", quality.lower())
        
        print("\n✓ Move quality categorization works")
    
    def test_prompt_builder_explain_move(self):
        """Test building explain move prompt."""
        builder = self.PromptBuilder(self.mock_analysis, self.test_fen)
        prompt = builder.build_explain_move_prompt("Bb5")
        
        self.assertIn("Bb5", prompt)
        self.assertIn("POSITION ANALYSIS", prompt)
        self.assertIn("PRINCIPAL VARIATION", prompt)
        self.assertIn("YOUR TASK", prompt)
        
        print(f"\n✓ Explain move prompt: {len(prompt)} chars")
        print(f"  Contains key sections: ✓")
    
    def test_prompt_builder_compare_moves(self):
        """Test building compare moves prompt."""
        builder = self.PromptBuilder(self.mock_analysis, self.test_fen)
        prompt = builder.build_compare_moves_prompt(
            "Bb5", 0.35, "Bb5 a6 Ba4", "Ruy Lopez",
            "Bc4", 0.25, "Bc4 Nf6 d3", "Italian Game"
        )
        
        self.assertIn("Bb5", prompt)
        self.assertIn("Bc4", prompt)
        self.assertIn("Compare", prompt.lower())
        
        print(f"\n✓ Compare moves prompt: {len(prompt)} chars")
    
    def test_prompt_builder_why_bad(self):
        """Test building why bad move prompt."""
        builder = self.PromptBuilder(self.mock_analysis, self.test_fen)
        prompt = builder.build_why_bad_prompt(
            "Qh5", -1.5, "Qh5 Nf6 Qxe5 Be7",
            "Bb5", 0.35, "Nf6"
        )
        
        self.assertIn("Qh5", prompt)
        self.assertIn("mistake", prompt.lower())
        self.assertIn("Bb5", prompt)
        
        print(f"\n✓ Why bad prompt: {len(prompt)} chars")
    
    def test_prompt_builder_find_plan(self):
        """Test building find plan prompt."""
        builder = self.PromptBuilder(self.mock_analysis, self.test_fen)
        prompt = builder.build_find_plan_prompt()
        
        self.assertIn("plan", prompt.lower())
        self.assertIn("POSITION ANALYSIS", prompt)
        
        print(f"\n✓ Find plan prompt: {len(prompt)} chars")
    
    def test_prompt_builder_eval(self):
        """Test building position eval prompt."""
        builder = self.PromptBuilder(self.mock_analysis, self.test_fen)
        prompt = builder.build_position_eval_prompt()
        
        self.assertIn("evaluat", prompt.lower())
        self.assertIn("POSITION FEATURES", prompt)
        
        print(f"\n✓ Position eval prompt: {len(prompt)} chars")
    
    def test_inject_fundamentals(self):
        """Test injecting fundamentals into prompts."""
        base_prompt = "Some content\n=== YOUR TASK ===\nDo something"
        funds = ["Development: Move pieces out", "Center control: Control d4/e4"]
        
        result = self.inject_relevant_fundamentals(base_prompt, funds)
        
        self.assertIn("RELEVANT CHESS PRINCIPLES", result)
        self.assertIn("Development", result)
        
        print(f"\n✓ Fundamental injection works")


class TestDeepAnalysis(unittest.TestCase):
    """Test the deep analysis module."""
    
    @classmethod
    def setUpClass(cls):
        """Set up deep analyzer once for all tests."""
        from src.deep_analysis import DeepAnalyzer, MoveRole, format_deep_analysis_for_llm
        cls.DeepAnalyzer = DeepAnalyzer
        cls.MoveRole = MoveRole
        cls.format_deep_analysis_for_llm = format_deep_analysis_for_llm
        
        print("\n\nInitializing DeepAnalyzer for tests...")
        cls.analyzer = cls.DeepAnalyzer()
        print("✓ DeepAnalyzer initialized")
    
    @classmethod
    def tearDownClass(cls):
        """Clean up."""
        if hasattr(cls, 'analyzer'):
            cls.analyzer.engine.close()
    
    def test_analyze_position_basic(self):
        """Test basic position analysis."""
        fen = "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq - 0 1"
        
        analysis = self.analyzer.analyze_position(fen, depth=12, num_pv_moves=4)
        
        self.assertEqual(analysis.fen, fen)
        self.assertIsInstance(analysis.current_eval, float)
        self.assertTrue(analysis.best_move)
        self.assertGreaterEqual(len(analysis.principal_variation), 1)
        
        print(f"\n✓ Basic position analysis:")
        print(f"  Best move: {analysis.best_move}")
        print(f"  Eval: {analysis.current_eval:+.2f}")
        print(f"  PV: {' '.join(analysis.principal_variation[:4])}")
        print(f"  Phase: {analysis.game_phase}")
    
    def test_pv_explanations(self):
        """Test that PV moves have explanations."""
        fen = "r1bqkbnr/pppp1ppp/2n5/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R w KQkq - 2 3"
        
        analysis = self.analyzer.analyze_position(fen, depth=14, num_pv_moves=5)
        
        self.assertGreaterEqual(len(analysis.pv_explanations), 1)
        
        print(f"\n✓ PV Explanations:")
        for i, exp in enumerate(analysis.pv_explanations[:4]):
            print(f"  {i+1}. {exp.move_san} ({exp.role.value})")
            print(f"     What: {exp.what_it_does}")
            print(f"     Why: {exp.why_it_matters}")
            self.assertIsNotNone(exp.move_san)
            self.assertIsNotNone(exp.role)
            self.assertIsNotNone(exp.what_it_does)
    
    def test_position_features(self):
        """Test position feature extraction."""
        fen = "r1bqk2r/pppp1ppp/2n2n2/2b1p3/2B1P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 4 4"
        
        analysis = self.analyzer.analyze_position(fen, depth=12)
        
        self.assertIsInstance(analysis.material_balance, str)
        self.assertIsInstance(analysis.piece_activity, str)
        self.assertIsInstance(analysis.king_safety, dict)
        self.assertIn('White', analysis.king_safety)
        self.assertIn('Black', analysis.king_safety)
        
        print(f"\n✓ Position Features:")
        print(f"  Material: {analysis.material_balance}")
        print(f"  Activity: {analysis.piece_activity}")
        print(f"  King safety: {analysis.king_safety}")
        print(f"  Phase: {analysis.game_phase}")
        if analysis.open_files:
            print(f"  Open files: {analysis.open_files}")
        if analysis.pawn_structure_notes:
            print(f"  Pawn notes: {analysis.pawn_structure_notes}")
    
    def test_alternative_moves(self):
        """Test alternative move extraction."""
        fen = "rnbqkbnr/pppp1ppp/8/4p3/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 0 2"
        
        analysis = self.analyzer.analyze_position(fen, depth=12, num_alternatives=3)
        
        self.assertIsInstance(analysis.alternative_moves, list)
        
        print(f"\n✓ Alternatives found: {len(analysis.alternative_moves)}")
        for alt in analysis.alternative_moves:
            print(f"  {alt['move']}: {alt['eval']:+.2f} - {alt.get('note', '')}")
    
    def test_analyze_specific_move(self):
        """Test analyzing a specific move."""
        fen = "rnbqkbnr/pppp1ppp/8/4p3/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 0 2"
        
        result = self.analyzer.analyze_move(fen, "Nf3", depth=12)
        
        self.assertIn('move', result)
        self.assertIn('eval_after', result)
        self.assertIn('quality', result)
        self.assertIn('continuation', result)
        
        print(f"\n✓ Move analysis (Nf3):")
        print(f"  Move: {result['move']}")
        print(f"  Eval after: {result['eval_after']:+.2f}")
        print(f"  Quality: {result['quality']}")
        print(f"  Continuation: {' '.join(result['continuation'][:3])}")
    
    def test_analyze_bad_move(self):
        """Test analyzing a bad move."""
        # Position where f3 is bad
        fen = "rnbqkbnr/pppp1ppp/8/4p3/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 0 2"
        
        result = self.analyzer.analyze_move(fen, "f3", depth=12)  # Weakening move
        
        self.assertIn('quality', result)
        print(f"\n✓ Bad move analysis (f3):")
        print(f"  Quality: {result['quality']}")
        print(f"  Eval: {result['eval_after']:+.2f}")
    
    def test_format_for_llm(self):
        """Test formatting analysis for LLM."""
        fen = "r1bqkbnr/pppp1ppp/2n5/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R w KQkq - 2 3"
        
        analysis = self.analyzer.analyze_position(fen, depth=12, num_pv_moves=4)
        formatted = self.format_deep_analysis_for_llm(analysis)
        
        self.assertIn("POSITION ANALYSIS", formatted)
        self.assertIn("BEST MOVE", formatted)
        self.assertIn("PRINCIPAL VARIATION", formatted)
        self.assertIn("POSITION FEATURES", formatted)
        
        print(f"\n✓ LLM formatted output: {len(formatted)} chars")
        print(f"  First 500 chars:\n{formatted[:500]}...")
    
    def test_threat_detection(self):
        """Test threat detection."""
        # Position with clear threats
        fen = "r1bqkb1r/pppp1ppp/2n2n2/4p2Q/2B1P3/8/PPPP1PPP/RNB1K1NR w KQkq - 4 4"
        
        analysis = self.analyzer.analyze_position(fen, depth=12)
        
        print(f"\n✓ Threat detection:")
        print(f"  Our threats: {analysis.threats}")
        print(f"  Their threats: {analysis.opponent_threats}")
    
    def test_tactical_motifs(self):
        """Test tactical motif detection."""
        # Position with fork possibility
        fen = "r1bqkbnr/pppp1ppp/2n5/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R w KQkq - 2 3"
        
        analysis = self.analyzer.analyze_position(fen, depth=12)
        
        print(f"\n✓ Tactical motifs: {analysis.tactical_motifs}")


class TestEnhancedExplainability(unittest.TestCase):
    """Test the enhanced explainability service."""
    
    @classmethod
    def setUpClass(cls):
        """Set up service once."""
        from src.enhanced_explainability import EnhancedExplainabilityService, LLMExplanationContext
        cls.EnhancedService = EnhancedExplainabilityService
        cls.LLMContext = LLMExplanationContext
        
        print("\n\nInitializing EnhancedExplainabilityService...")
        cls.service = cls.EnhancedService(engine_depth=14)
        print("✓ Service initialized")
    
    @classmethod
    def tearDownClass(cls):
        """Clean up."""
        if hasattr(cls, 'service'):
            cls.service.close()
    
    def test_get_llm_context_explain_move(self):
        """Test getting LLM context for explaining a move."""
        fen = "r1bqkbnr/pppp1ppp/2n5/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R w KQkq - 2 3"
        
        context = self.service.get_llm_context(
            "Why is Bb5 a good move?",
            fen,
            move="Bb5"
        )
        
        self.assertIsInstance(context, self.LLMContext)
        self.assertTrue(context.prompt)
        self.assertTrue(context.system_prompt)
        self.assertIsInstance(context.analysis_data, dict)
        self.assertIsInstance(context.key_facts, list)
        
        print(f"\n✓ Explain move context:")
        print(f"  Question type: {context.question_type}")
        print(f"  Interpreted: {context.question_interpreted}")
        print(f"  Prompt length: {len(context.prompt)} chars")
        print(f"  Fundamentals: {context.fundamentals}")
        print(f"  Key facts: {context.key_facts[:3]}...")
    
    def test_get_llm_context_compare(self):
        """Test getting LLM context for comparing moves."""
        fen = "r1bqkbnr/pppp1ppp/2n5/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R w KQkq - 2 3"
        
        context = self.service.get_llm_context(
            "Compare Bb5 and Bc4",
            fen,
            move="Bb5",
            compare_move="Bc4"
        )
        
        self.assertEqual(context.question_type, "compare_moves")
        self.assertIn("Bb5", context.prompt)
        self.assertIn("Bc4", context.prompt)
        
        print(f"\n✓ Compare moves context:")
        print(f"  Question type: {context.question_type}")
        print(f"  Key facts: {context.key_facts[:3]}")
    
    def test_get_llm_context_why_bad(self):
        """Test getting LLM context for why a move is bad."""
        fen = "rnbqkbnr/pppp1ppp/8/4p3/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 0 2"
        
        context = self.service.get_llm_context(
            "Why is f3 a bad move?",
            fen,
            move="f3"
        )
        
        self.assertEqual(context.question_type, "why_bad")
        self.assertIn("f3", context.prompt)
        
        print(f"\n✓ Why bad context:")
        print(f"  Question type: {context.question_type}")
        print(f"  Key facts: {context.key_facts}")
    
    def test_get_llm_context_plan(self):
        """Test getting LLM context for finding the plan."""
        fen = "r1bqk2r/pppp1ppp/2n2n2/2b1p3/2B1P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 4 4"
        
        context = self.service.get_llm_context(
            "What is the plan here?",
            fen
        )
        
        self.assertEqual(context.question_type, "explain_plan")
        self.assertTrue(len(context.pv_explanations) > 0)
        
        print(f"\n✓ Plan context:")
        print(f"  Question type: {context.question_type}")
        print(f"  PV: {context.principal_variation[:3]}")
        print(f"  PV explanations: {len(context.pv_explanations)}")
    
    def test_get_llm_context_evaluate(self):
        """Test getting LLM context for position evaluation."""
        fen = "r1bqk2r/pppp1ppp/2n2n2/2b1p3/2B1P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 4 4"
        
        context = self.service.get_llm_context(
            "Evaluate this position",
            fen
        )
        
        self.assertEqual(context.question_type, "evaluate")
        self.assertIsInstance(context.stockfish_eval, float)
        
        print(f"\n✓ Evaluate context:")
        print(f"  Eval: {context.stockfish_eval:+.2f}")
        print(f"  Key facts: {context.key_facts[:3]}")
    
    def test_get_llm_context_concept(self):
        """Test getting LLM context for explaining a concept."""
        fen = "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq - 0 1"
        
        context = self.service.get_llm_context(
            "What is a fork?",
            fen
        )
        
        self.assertEqual(context.question_type, "explain_concept")
        self.assertIn("Fork", context.prompt)
        
        print(f"\n✓ Concept context:")
        print(f"  Question type: {context.question_type}")
        print(f"  Fundamentals: {context.fundamentals}")
    
    def test_get_simple_analysis(self):
        """Test simple analysis without prompt building."""
        fen = "r1bqkbnr/pppp1ppp/2n5/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R w KQkq - 2 3"
        
        result = self.service.get_simple_analysis(fen)
        
        self.assertIn('eval', result)
        self.assertIn('best_move', result)
        self.assertIn('principal_variation', result)
        self.assertIn('pv_explanations', result)
        
        print(f"\n✓ Simple analysis:")
        print(f"  Eval: {result['eval']:+.2f}")
        print(f"  Best: {result['best_move']}")
        print(f"  Phase: {result['phase']}")
        print(f"  PV: {result['principal_variation'][:3]}")
    
    def test_get_simple_analysis_with_move(self):
        """Test simple analysis with specific move."""
        fen = "r1bqkbnr/pppp1ppp/2n5/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R w KQkq - 2 3"
        
        result = self.service.get_simple_analysis(fen, move="Bb5")
        
        self.assertIn('move_analysis', result)
        move_result = result['move_analysis']
        self.assertIn('quality', move_result)
        
        print(f"\n✓ Simple analysis with move:")
        print(f"  Move: {move_result['move']}")
        print(f"  Quality: {move_result['quality']}")
        print(f"  Continuation: {move_result['continuation'][:3]}")


class TestQueryParsing(unittest.TestCase):
    """Test query parsing for different question types."""
    
    def setUp(self):
        """Set up parser."""
        from src.query_understanding import QueryParser, QueryType
        self.parser = QueryParser()
        self.QueryType = QueryType
    
    def test_parse_why_good(self):
        """Test parsing 'why is this good' questions."""
        queries = [
            "Why is Nf3 good?",
            "Explain why Bb5 is the best move",
            "What's good about castling?",
        ]
        
        print("\n✓ Why good queries:")
        for q in queries:
            parsed = self.parser.parse(q)
            print(f"  '{q}' → {parsed.query_type}")
    
    def test_parse_why_bad(self):
        """Test parsing 'why is this bad' questions."""
        queries = [
            "Why is f3 a bad move?",
            "What's wrong with Qh5?",
            "Why is that a mistake?",
        ]
        
        print("\n✓ Why bad queries:")
        for q in queries:
            parsed = self.parser.parse(q)
            print(f"  '{q}' → {parsed.query_type}")
    
    def test_parse_compare(self):
        """Test parsing comparison questions."""
        queries = [
            "Compare Bb5 and Bc4",
            "Which is better, Nf3 or Nc3?",
            "Bb5 vs Bc4",
        ]
        
        print("\n✓ Compare queries:")
        for q in queries:
            parsed = self.parser.parse(q)
            print(f"  '{q}' → {parsed.query_type}")
    
    def test_parse_what_to_play(self):
        """Test parsing 'what to play' questions."""
        queries = [
            "What should I play?",
            "What's the best move here?",
            "What do you recommend?",
        ]
        
        print("\n✓ What to play queries:")
        for q in queries:
            parsed = self.parser.parse(q)
            print(f"  '{q}' → {parsed.query_type}")
    
    def test_parse_plan(self):
        """Test parsing plan questions."""
        queries = [
            "What's the plan?",
            "What should my strategy be?",
            "What's the idea in this position?",
        ]
        
        print("\n✓ Plan queries:")
        for q in queries:
            parsed = self.parser.parse(q)
            print(f"  '{q}' → {parsed.query_type}")
    
    def test_parse_evaluate(self):
        """Test parsing evaluation questions."""
        queries = [
            "Who is better?",
            "Evaluate this position",
            "What's the assessment?",
        ]
        
        print("\n✓ Evaluate queries:")
        for q in queries:
            parsed = self.parser.parse(q)
            print(f"  '{q}' → {parsed.query_type}")


def run_all_tests():
    """Run all test suites."""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test classes
    suite.addTests(loader.loadTestsFromTestCase(TestChessFundamentals))
    suite.addTests(loader.loadTestsFromTestCase(TestLLMPrompts))
    suite.addTests(loader.loadTestsFromTestCase(TestDeepAnalysis))
    suite.addTests(loader.loadTestsFromTestCase(TestEnhancedExplainability))
    suite.addTests(loader.loadTestsFromTestCase(TestQueryParsing))
    
    # Run with verbosity
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success: {result.wasSuccessful()}")
    
    return result.wasSuccessful()


if __name__ == "__main__":
    import atexit
    import gc
    atexit.register(gc.collect)
    success = run_all_tests()
    sys.exit(0 if success else 1)
