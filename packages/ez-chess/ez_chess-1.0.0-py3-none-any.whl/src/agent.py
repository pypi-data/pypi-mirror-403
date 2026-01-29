"""
Chess Analysis Agent
LangGraph-based agent that routes chess analysis questions to appropriate tools
and verbalizes the structured output into natural language.

The agent:
1. Receives a chess question + FEN position
2. Determines which tool(s) to use
3. Calls the tools and gets structured data
4. Uses LLM to verbalize results into natural language

Supports two modes (configured in config.yaml):
- Cloud mode: Uses Groq API (fast, free tier available)
- Local mode: Uses Ollama (runs locally, no API needed)
"""

from typing import TypedDict, Annotated, Sequence, Optional, Tuple
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, ToolMessage
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
import operator
import json
import subprocess
import platform
import re
import os
import chess

from src.tool_schemas import CHESS_TOOLS
from src.move_parser import preprocess_question, get_question_type, contains_move_reference
from src.config import get_config
from src.chess_fundamentals import (
    ALL_FUNDAMENTALS, ConceptCategory,
    TACTICAL_MOTIFS, POSITIONAL_CONCEPTS, OPENING_PRINCIPLES,
    PAWN_STRUCTURE, KING_SAFETY, ATTACKING_PRINCIPLES, PIECE_PLACEMENT,
    DEFENSIVE_PRINCIPLES, ENDGAME_FUNDAMENTALS
)
from src.explanation_framework import CHESS_CONCEPTS


def _get_comprehensive_fundamentals() -> str:
    """Get ALL 60+ chess concepts with definitions for LLM (legacy + new fundamentals)."""
    parts = []
    
    # Part 1: Modern fundamentals (51 concepts)
    categories = [
        ("TACTICAL MOTIFS", TACTICAL_MOTIFS),
        ("POSITIONAL CONCEPTS", POSITIONAL_CONCEPTS),
        ("PAWN STRUCTURE", PAWN_STRUCTURE),
        ("KING SAFETY", KING_SAFETY),
        ("PIECE PLACEMENT", PIECE_PLACEMENT),
        ("ATTACKING PRINCIPLES", ATTACKING_PRINCIPLES),
        ("DEFENSIVE PRINCIPLES", DEFENSIVE_PRINCIPLES),
        ("OPENING PRINCIPLES", OPENING_PRINCIPLES),
        ("ENDGAME FUNDAMENTALS", ENDGAME_FUNDAMENTALS),
    ]
    
    for category_name, concepts_dict in categories:
        concepts = []
        for name, fund in concepts_dict.items():
            brief_def = fund.definition.split('.')[0] if hasattr(fund, 'definition') else fund.description.split('.')[0]
            concepts.append(f"{fund.name} ({brief_def})")
        concepts_str = "; ".join(concepts)
        parts.append(f"{category_name}: {concepts_str}")
    
    # Part 2: Legacy concepts not in modern fundamentals (additional ~9 concepts)
    legacy_only = {k: v for k, v in CHESS_CONCEPTS.items() if k not in ALL_FUNDAMENTALS}
    if legacy_only:
        legacy_concepts = []
        for name, concept in legacy_only.items():
            brief_def = concept.description.split('.')[0]
            legacy_concepts.append(f"{concept.name} ({brief_def})")
        parts.append(f"ADDITIONAL CONCEPTS: {'; '.join(legacy_concepts)}")
    
    return "\n\n".join(parts)


CHESS_FUNDAMENTALS_GUIDE = _get_comprehensive_fundamentals()


# Model configurations optimized for different VRAM sizes
# Format: (model_name, size_gb, min_vram_gb, description)
MODEL_CONFIGS = [
    ("qwen2.5:3b", 1.9, 0, "Ultra-fast, good for CPU/integrated graphics"),
    ("qwen2.5:7b", 4.7, 6, "Optimal balance of speed and quality"),
    ("qwen2.5:14b", 9.0, 12, "Highest quality, requires high-end GPU"),
]


def safe_print(text: str):
    """
    Print text safely, handling Unicode errors on Windows.
    Falls back to ASCII if encoding fails.
    """
    try:
        print(text)
    except UnicodeEncodeError:
        # Remove emojis and special characters for Windows compatibility
        ascii_text = text.encode('ascii', errors='ignore').decode('ascii')
        # Replace common emoji patterns with ASCII equivalents
        replacements = {
            '': '[GPU]', '': '[OK]', '': '[PC]', '': '[WARN]', '': '[TIME]',
        }
        for emoji, replacement in replacements.items():
            ascii_text = ascii_text.replace(emoji, replacement)
        print(ascii_text if ascii_text.strip() else text.encode('ascii', errors='replace').decode('ascii'))


def get_gpu_info() -> Tuple[bool, int, str]:
    """
    Get detailed GPU information for optimal model selection.
    
    Returns:
        Tuple of (has_supported_gpu, vram_mb, gpu_name)
    """
    # Try NVIDIA GPU
    try:
        result = subprocess.run(
            ['nvidia-smi', '--query-gpu=name,memory.total', '--format=csv,noheader,nounits'],
            capture_output=True,
            text=True,
            timeout=3
        )
        if result.returncode == 0:
            output = result.stdout.strip()
            parts = output.split(',')
            if len(parts) >= 2:
                gpu_name = parts[0].strip()
                vram_mb = int(parts[1].strip())
                return True, vram_mb, gpu_name
    except:
        pass
    
    # Try AMD GPU (ROCm)
    try:
        result = subprocess.run(
            ['rocm-smi', '--showmeminfo', 'vram'],
            capture_output=True,
            text=True,
            timeout=3
        )
        if result.returncode == 0:
            # Parse AMD memory info
            match = re.search(r'Total Memory.*?(\d+)', result.stdout)
            if match:
                vram_mb = int(match.group(1))
                return True, vram_mb, "AMD GPU"
    except:
        pass
    
    # Apple Silicon
    if platform.system() == "Darwin":
        try:
            result = subprocess.run(
                ['sysctl', 'hw.memsize'],
                capture_output=True,
                text=True,
                timeout=2
            )
            if result.returncode == 0:
                # Apple Silicon shares memory, estimate 60% for GPU
                match = re.search(r'(\d+)', result.stdout)
                if match:
                    total_mb = int(match.group(1)) // (1024 * 1024)
                    estimated_vram = int(total_mb * 0.6)
                    return True, estimated_vram, "Apple Silicon"
        except:
            pass
    
    return False, 0, "None"


def select_optimal_model(vram_mb: int, has_gpu: bool) -> str:
    """
    Select the optimal model based on available VRAM.
    
    Strategy:
    - Model should fit ENTIRELY in VRAM for maximum speed
    - Leave ~500MB headroom for Ollama overhead
    - For CPU-only, use smallest capable model
    
    Args:
        vram_mb: Available VRAM in megabytes
        has_gpu: Whether a supported GPU is available
    
    Returns:
        Optimal model name
    """
    if not has_gpu:
        # CPU-only: use smallest model for reasonable speed
        return "qwen2.5:3b"
    
    # Convert to GB with headroom
    available_gb = (vram_mb - 500) / 1024
    
    # Find best model that fits
    selected = MODEL_CONFIGS[0]  # Default to smallest
    for model_name, size_gb, min_vram_gb, desc in MODEL_CONFIGS:
        if size_gb <= available_gb:
            selected = (model_name, size_gb, min_vram_gb, desc)
    
    return selected[0]


def ensure_model_available(model_name: str) -> bool:
    """
    Check if model is available, pull if not.
    
    Args:
        model_name: Ollama model name
    
    Returns:
        True if model is available
    """
    try:
        result = subprocess.run(
            ['ollama', 'list'],
            capture_output=True,
            text=True,
            timeout=10
        )
        if model_name in result.stdout:
            return True
        
        # Model not found, try to pull
        print(f"Model {model_name} not found. Pulling... (this may take a few minutes)")
        pull_result = subprocess.run(
            ['ollama', 'pull', model_name],
            capture_output=False,
            timeout=600  # 10 minute timeout for download
        )
        return pull_result.returncode == 0
    except Exception as e:
        print(f"Warning: Could not verify model availability: {e}")
        return True  # Assume available, let Ollama handle errors


class AgentState(TypedDict):
    """State for the chess analysis agent."""
    messages: Annotated[Sequence[BaseMessage], operator.add]
    fen: str  # Current position FEN
    question: str  # User's question
    tool_results: dict  # Results from tools


class ChessAgent:
    """
    Chess analysis agent using LangGraph.
    
    Routes chess questions to appropriate analytical tools and verbalizes
    the structured output into natural language explanations.
    
    Supports two modes (configured in config.yaml):
    - Cloud mode: Uses Groq API with llama-3.1-70b-versatile - fastest, best quality
    - Local mode: Uses Ollama with qwen2.5:7b - runs locally, no API needed
    
    Mode can be switched by editing config.yaml:
        llm:
          mode: "local"  # or "cloud"
    """
    
    def __init__(
        self, 
        model_name: Optional[str] = None, 
        temperature: float = 0.3, 
        verbose: bool = True,
        mode: Optional[str] = None
    ):
        """
        Initialize the chess agent.
        
        Args:
            model_name: Model to use (if None, uses config value)
            temperature: LLM temperature for response generation (0.0-1.0)
            verbose: Print hardware detection and model selection info
            mode: LLM mode - "cloud" or "local" (if None, uses config value)
        """
        self.temperature = temperature
        self.verbose = verbose
        
        # Load configuration
        config = get_config()
        llm_config = config.llm
        
        # Determine mode (parameter > config)
        self.mode = mode or llm_config.mode
        
        # Initialize LLM based on mode
        if self.mode == "cloud":
            self._init_cloud(model_name, llm_config)
        else:
            self._init_local(model_name, llm_config)
        
        # Bind tools to LLM
        self.llm_with_tools = self.llm.bind_tools(CHESS_TOOLS)
        
        # Build the graph
        self.graph = self._build_graph()
    
    def _init_cloud(self, model_name: Optional[str], llm_config):
        """Initialize cloud LLM (Groq)."""
        try:
            from langchain_groq import ChatGroq
        except ImportError:
            raise ImportError(
                "langchain-groq is required for cloud mode. "
                "Install with: pip install langchain-groq"
            )
        
        # Get config for cloud provider
        cloud_config = llm_config.cloud
        
        # Get API key (parameter > config > env var)
        api_key = cloud_config.api_key or os.environ.get("GROQ_API_KEY")
        if not api_key:
            raise ValueError(
                "Groq API key required for cloud mode. "
                "Set GROQ_API_KEY environment variable or add to config.yaml"
            )
        
        # Get model name (parameter > config)
        self.model_name = model_name or cloud_config.model
        
        if self.verbose:
            safe_print(f"[Cloud Mode] Using Groq with {self.model_name}")
        
        self.llm = ChatGroq(
            model=self.model_name,
            api_key=api_key,
            temperature=cloud_config.temperature,
            max_tokens=cloud_config.max_tokens,
        )
    
    def _init_local(self, model_name: Optional[str], llm_config):
        """Initialize local LLM (Ollama)."""
        try:
            from langchain_ollama import ChatOllama
        except ImportError:
            raise ImportError(
                "langchain-ollama is required for local mode. "
                "Install with: pip install langchain-ollama"
            )
        
        # Get config for local provider
        local_config = llm_config.local
        
        # Get model name (parameter > config)
        self.model_name = model_name or local_config.model
        
        if self.verbose:
            safe_print(f"[Local Mode] Using Ollama with {self.model_name}")
        
        # Ensure model is available
        ensure_model_available(self.model_name)
        
        self.llm = ChatOllama(
            model=self.model_name,
            temperature=local_config.temperature,
            num_ctx=local_config.num_ctx,
            num_predict=local_config.num_predict,
            timeout=local_config.timeout,
        )
    
    def _build_graph(self) -> StateGraph:
        """
        Build the LangGraph workflow.
        
        Returns:
            Compiled StateGraph
        """
        # Create graph
        workflow = StateGraph(AgentState)
        
        # Add nodes
        workflow.add_node("agent", self._agent_node)
        workflow.add_node("tools", ToolNode(CHESS_TOOLS))
        
        # Set entry point
        workflow.set_entry_point("agent")
        
        # Add conditional edges
        workflow.add_conditional_edges(
            "agent",
            self._should_continue,
            {
                "continue": "tools",
                "end": END
            }
        )
        
        # Add edge from tools back to agent
        workflow.add_edge("tools", "agent")
        
        # Compile
        return workflow.compile()
    
    def _agent_node(self, state: AgentState) -> AgentState:
        """
        Agent decision node - decides which tools to call or generates final response.
        
        Args:
            state: Current agent state
        
        Returns:
            Updated state with agent's decision
        """
        messages = state["messages"]
        
        # Invoke LLM with tools
        response = self.llm_with_tools.invoke(messages)
        
        return {"messages": [response]}
    
    def _should_continue(self, state: AgentState) -> str:
        """
        Determine if we should continue to tools or end.
        
        Args:
            state: Current agent state
        
        Returns:
            "continue" if we should call tools, "end" if done
        """
        messages = state["messages"]
        last_message = messages[-1]
        
        # If the LLM makes a tool call, continue to tools
        if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
            return "continue"
        
        # Otherwise, end
        return "end"
    
    def analyze(self, fen: str, question: str) -> str:
        """
        Analyze a chess position and answer a question about it.
        
        Args:
            fen: Chess position in FEN notation
            question: User's question about the position
        
        Returns:
            Natural language answer to the question
        """
        # Parse FEN to get turn info
        try:
            board = chess.Board(fen)
            turn_str = "White" if board.turn == chess.WHITE else "Black"
            move_num = board.fullmove_number
        except:
            turn_str = "Unknown"
            move_num = 1
        
        # Get question type hint
        q_type = get_question_type(question)
        
        # Focused system prompt with comprehensive chess knowledge
        system_prompt = f"""You are a chess analysis assistant. You MUST call a tool to analyze positions - you cannot analyze without tools.

POSITION:
FEN: {fen}
Turn: {turn_str} to move (move {move_num})

MANDATORY: You MUST call exactly ONE of these tools:
1. position_overview_tool(fen="{fen}") - for general assessment
2. get_best_move_tool(fen="{fen}") - for best move questions  
3. move_quality_tool(fen="{fen}", move="Nf3") - to evaluate a specific move
4. move_comparison_tool(fen="{fen}", moves="Nf3,d4") - to compare two moves

USER QUESTION: {question}

CRITICAL INSTRUCTIONS:
1. Call the appropriate tool immediately - do NOT write an answer first
2. After the tool returns data, quote the exact evaluation and best move from the tool
3. Then explain why using chess concepts: tactics, pawn structure, king safety, piece activity

If you answer without calling a tool, your response will be rejected."""
        
        # Initialize state
        initial_state = {
            "messages": [HumanMessage(content=system_prompt)],
            "fen": fen,
            "question": question,
            "tool_results": {}
        }
        
        # Run the graph
        final_state = self.graph.invoke(initial_state)
        
        # Validate that a tool was actually called
        tool_called = False
        for msg in final_state["messages"]:
            if hasattr(msg, 'tool_calls') and msg.tool_calls:
                tool_called = True
                if self.verbose:
                    safe_print(f"[DEBUG] Tool called: {msg.tool_calls[0]['name']}")
                break
        
        if not tool_called and self.verbose:
            safe_print("[WARNING] Agent did not call any tool - response may be hallucinated!")
        
        # Extract final answer
        final_message = final_state["messages"][-1]
        
        if isinstance(final_message, AIMessage):
            response = final_message.content
            # Add a warning if no tool was called
            if not tool_called:
                response = "[Warning: No Stockfish analysis used]\n\n" + response
            return response
        else:
            return "I apologize, but I encountered an issue analyzing this position."
    
    def chat(self, fen: str, messages: list) -> str:
        """
        Multi-turn chat about a chess position.
        
        Args:
            fen: Chess position in FEN notation
            messages: List of conversation messages
        
        Returns:
            Agent's response
        """
        # Parse FEN to get turn info
        try:
            board = chess.Board(fen)
            turn_str = "White" if board.turn == chess.WHITE else "Black"
            move_num = board.fullmove_number
        except:
            turn_str = "Unknown"
            move_num = 1
        
        # Get the latest question
        latest_question = messages[-1].content if messages else ""
        q_type = get_question_type(latest_question)
        
        # Focused system prompt with chess knowledge
        system_prompt = f"""You are a chess analyst. Stockfish is your PRIMARY evaluation source.

POSITION: FEN={fen}
{turn_str} to move (move {move_num})

EVAL SCALE: 0=equal, ±1=slight edge, ±2-3=clear advantage, ±4+=winning

CHESS FUNDAMENTALS - Use to explain:
{CHESS_FUNDAMENTALS_GUIDE}

ANALYZE best line using fundamentals: Tactics, positional factors, king safety, pawn structure.

TOOL RULES:
1. BEST MOVE -> get_best_move_tool(fen)
2. MOVE QUALITY -> move_quality_tool(fen, move_in_SAN)
   Convert: "queen takes d4" = Qxd4, "knight to f3" = Nf3
3. COMPARE MOVES -> move_comparison_tool(fen, "move1,move2")
4. GENERAL -> position_overview_tool(fen)

All evaluation from STOCKFISH.

[Type: {q_type.upper()}]
Call ONE tool. Answer in 2 sentences:
1. Stockfish eval + best move
2. WHY (analyze best line for key factors)"""
        
        # Prepend system message
        full_messages = [HumanMessage(content=system_prompt)] + messages
        
        # Initialize state
        initial_state = {
            "messages": full_messages,
            "fen": fen,
            "question": latest_question,
            "tool_results": {}
        }
        
        # Run the graph
        try:
            final_state = self.graph.invoke(initial_state)
        except Exception as e:
            # Better error reporting
            error_msg = f"Graph execution failed: {str(e)}"
            if self.verbose:
                import traceback
                safe_print(f"ERROR: {error_msg}")
                safe_print(traceback.format_exc())
            return f"Error analyzing position: {str(e)}"
        
        # Extract final answer
        final_message = final_state["messages"][-1]
        
        if isinstance(final_message, AIMessage):
            response = final_message.content
            if not response or not str(response).strip():
                return "Error: Agent returned empty response. Please try again."
            return response
        else:
            return "Error: Unexpected response format from agent."

def create_agent(
    model_name: Optional[str] = None, 
    temperature: float = 0.3,
    auto_select: bool = True,
    verbose: bool = True
) -> ChessAgent:
    """
    Factory function to create a chess analysis agent.
    
    Args:
        model_name: Ollama model to use (if None, auto-selects based on hardware)
        temperature: LLM temperature
        auto_select: Whether to auto-select optimal model for your hardware
        verbose: Print hardware and model info
    
    Returns:
        Configured ChessAgent instance
        
    Model Selection (when model_name is None):
        - 6-8GB VRAM: qwen2.5:7b (4.7GB) - fits entirely, fast
        - 12GB+ VRAM: qwen2.5:14b (9GB) - highest quality
        - CPU/integrated: qwen2.5:3b (1.9GB) - reasonable speed
    """
    return ChessAgent(
        model_name=model_name, 
        temperature=temperature,
        auto_select_model=auto_select,
        verbose=verbose
    )


def benchmark_agent(agent: ChessAgent, iterations: int = 3) -> dict:
    """
    Benchmark agent response times.
    
    Args:
        agent: ChessAgent to benchmark
        iterations: Number of test queries
    
    Returns:
        Dictionary with timing statistics
    """
    import time
    
    fen = "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1"
    questions = [
        "What's the material balance?",
        "How safe are the kings?",
        "What should black play?"
    ]
    
    times = []
    for i in range(min(iterations, len(questions))):
        start = time.time()
        agent.analyze(fen, questions[i])
        elapsed = time.time() - start
        times.append(elapsed)
        print(f"  Query {i+1}: {elapsed:.1f}s")
    
    return {
        "model": agent.model_name,
        "avg_time": sum(times) / len(times),
        "min_time": min(times),
        "max_time": max(times),
        "times": times
    }


# Example usage
if __name__ == "__main__":
    import time
    
    print("=" * 60)
    print("Chess Analysis Agent - Performance Test")
    print("=" * 60)
    
    # Create agent with auto-selected model
    print("\nInitializing agent...")
    start = time.time()
    agent = create_agent()
    init_time = time.time() - start
    print(f"Agent initialized in {init_time:.1f}s\n")
    
    # Test position
    fen = "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1"
    
    # Benchmark
    print("Running benchmark (3 queries)...")
    stats = benchmark_agent(agent, 3)
    
    print(f"\n{'=' * 60}")
    print(f"Results for {stats['model']}:")
    print(f"  Average response time: {stats['avg_time']:.1f}s")
    print(f"  Fastest: {stats['min_time']:.1f}s")
    print(f"  Slowest: {stats['max_time']:.1f}s")
    print("=" * 60)
