"""
EZ-Chess Command Line Interface
===============================

Main entry point for the EZ-Chess CLI.

Usage:
    EZ-Chess run           Launch the GUI application
    EZ-Chess analyze FEN   Analyze a position
    EZ-Chess --version     Show version
    EZ-Chess --help        Show help
"""

import argparse
import sys
from typing import Optional


def main(args: Optional[list] = None):
    """
    Main CLI entry point for EZ-Chess.
    
    Args:
        args: Command line arguments (uses sys.argv if None)
    """
    parser = argparse.ArgumentParser(
        prog="EZ-Chess",
        description="AI-Powered Chess Analysis SDK",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  EZ-Chess run                    Launch the GUI
  EZ-Chess analyze "FEN_STRING"   Analyze a position
  EZ-Chess analyze "FEN" -q "What's the best plan?"
  
For more information, visit: https://github.com/AnubhavChoudhery/EZ-Chess
        """
    )
    
    parser.add_argument(
        "--version", "-v",
        action="store_true",
        help="Show version and exit"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Run command - launch GUI
    run_parser = subparsers.add_parser(
        "run",
        help="Launch the EZ-Chess GUI application"
    )
    run_parser.add_argument(
        "--mode",
        choices=["cloud", "local"],
        help="Override LLM mode (cloud=Groq, local=Ollama)"
    )
    run_parser.add_argument(
        "--pgn",
        type=str,
        help="Path to PGN file to load on startup"
    )
    
    # Analyze command - CLI analysis
    analyze_parser = subparsers.add_parser(
        "analyze",
        help="Analyze a chess position from the command line"
    )
    analyze_parser.add_argument(
        "fen",
        type=str,
        help="Position in FEN notation"
    )
    analyze_parser.add_argument(
        "-d", "--depth",
        type=int,
        default=18,
        help="Analysis depth (default: 18)"
    )
    analyze_parser.add_argument(
        "-n", "--num-moves",
        type=int,
        default=3,
        help="Number of top moves to show (default: 3)"
    )
    analyze_parser.add_argument(
        "-q", "--question",
        type=str,
        help="Ask the AI a question about the position"
    )
    analyze_parser.add_argument(
        "--mode",
        choices=["cloud", "local"],
        help="LLM mode for AI questions (cloud=Groq, local=Ollama)"
    )
    analyze_parser.add_argument(
        "--json",
        action="store_true",
        help="Output results as JSON"
    )
    
    # Config command - show/edit configuration
    config_parser = subparsers.add_parser(
        "config",
        help="Show or edit configuration"
    )
    config_parser.add_argument(
        "--show",
        action="store_true",
        help="Show current configuration"
    )
    config_parser.add_argument(
        "--path",
        action="store_true",
        help="Show path to config file"
    )
    
    # Parse arguments
    parsed = parser.parse_args(args)
    
    # Handle --version
    if parsed.version:
        from ez_chess import __version__
        print(f"EZ-Chess version {__version__}")
        return 0
    
    # Handle commands
    if parsed.command == "run":
        return cmd_run(parsed)
    elif parsed.command == "analyze":
        return cmd_analyze(parsed)
    elif parsed.command == "config":
        return cmd_config(parsed)
    else:
        # No command specified, show help
        parser.print_help()
        return 0


def cmd_run(args):
    """Launch the GUI application."""
    import os
    
    # Override mode if specified
    if args.mode:
        os.environ["EZCHESS_MODE"] = args.mode
    
    try:
        from ez_chess.ui.main import EZChessApp
        
        print("=" * 50)
        print("  EZ-Chess - AI-Powered Chess Analysis")
        print("=" * 50)
        print()
        
        app = EZChessApp()
        
        # Load PGN if specified
        if args.pgn:
            print(f"Loading PGN: {args.pgn}")
            app.load_pgn(args.pgn)
        
        app.run()
        return 0
        
    except ImportError as e:
        print("Error: GUI dependencies not installed.")
        print()
        print("Install with:")
        print("  pip install ez-chess[gui]")
        print("  pip install ez-chess[all]")
        print()
        print(f"Details: {e}")
        return 1


def cmd_analyze(args):
    """Analyze a chess position."""
    import json
    
    try:
        from ez_chess import analyze_position, get_agent
        import chess
        
        # Validate FEN
        try:
            board = chess.Board(args.fen)
        except ValueError as e:
            print(f"Error: Invalid FEN string")
            print(f"  {e}")
            return 1
        
        # Get Stockfish analysis
        print("Analyzing position...")
        result = analyze_position(args.fen, depth=args.depth, num_moves=args.num_moves)
        
        if args.json and not args.question:
            # Output as JSON
            print(json.dumps(result, indent=2))
            return 0
        
        # Pretty print results
        print()
        print("=" * 50)
        print("  POSITION ANALYSIS")
        print("=" * 50)
        print()
        print(f"FEN: {args.fen}")
        print()
        
        # Show board
        print("Board:")
        print(board)
        print()
        
        # Evaluation
        eval_score = result.get("evaluation", 0)
        if result.get("is_mate"):
            mate_in = result.get("mate_in", 0)
            eval_str = f"Mate in {mate_in}" if mate_in > 0 else f"Mated in {-mate_in}"
        else:
            eval_str = f"{eval_score:+.2f}"
        
        print(f"Evaluation: {eval_str}")
        print(f"Best Move:  {result.get('best_move', 'N/A')}")
        print()
        
        # Top moves
        print("Top Moves:")
        for i, move_info in enumerate(result.get("top_moves", []), 1):
            move = move_info.get("move", "?")
            mv_eval = move_info.get("eval", 0)
            line = move_info.get("line", "")
            print(f"  {i}. {move:6s} ({mv_eval:+.2f})  {line}")
        print()
        
        # AI question if specified
        if args.question:
            print("=" * 50)
            print("  AI ANALYSIS")
            print("=" * 50)
            print()
            print(f"Question: {args.question}")
            print()
            
            try:
                import os
                if args.mode:
                    os.environ["EZCHESS_MODE"] = args.mode
                
                agent = get_agent(verbose=False)
                response = agent.analyze(args.fen, args.question)
                print("Answer:")
                print(response)
            except ImportError:
                print("Error: AI features require additional dependencies.")
                print("Install with: pip install ez-chess[all]")
                return 1
            except Exception as e:
                print(f"Error: {e}")
                return 1
        
        return 0
        
    except Exception as e:
        print(f"Error: {e}")
        return 1


def cmd_config(args):
    """Show or edit configuration."""
    from pathlib import Path
    
    if args.path:
        # Show config file path
        config_path = Path(__file__).parent.parent / "config.yaml"
        if config_path.exists():
            print(f"Config file: {config_path.absolute()}")
        else:
            print(f"Config file not found at: {config_path.absolute()}")
            print("Using default configuration.")
        return 0
    
    if args.show:
        # Show current configuration
        try:
            from ez_chess import get_config
            import yaml
            
            config = get_config()
            config_dict = config.to_dict()
            
            print("=" * 50)
            print("  CURRENT CONFIGURATION")
            print("=" * 50)
            print()
            print(yaml.dump(config_dict, default_flow_style=False, sort_keys=False))
            return 0
        except ImportError:
            print("Error: PyYAML not installed")
            return 1
    
    # Default: show help
    print("Usage:")
    print("  EZ-Chess config --show    Show current configuration")
    print("  EZ-Chess config --path    Show config file path")
    return 0


if __name__ == "__main__":
    sys.exit(main())
