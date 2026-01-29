"""
EZ-Chess Configuration - Unified configuration management.

Supports both YAML and JSON config files.
All settings in one place for easy maintenance and consistency.
"""

import os
import json
from dataclasses import dataclass, field, asdict
from typing import Optional, Dict, Any, Literal
from pathlib import Path

# Try to import yaml, fall back if not available
try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False


# =============================================================================
# CONFIGURATION DATACLASSES
# =============================================================================

@dataclass
class EngineConfig:
    """Stockfish engine configuration."""
    depth: int = 18
    threads: int = 4
    hash_size_mb: int = 256
    multipv: int = 3
    cache_enabled: bool = True
    cache_size: int = 1024  # Number of positions to cache


@dataclass
class CloudLLMConfig:
    """Cloud LLM configuration (Groq)."""
    provider: str = "groq"
    model: str = "llama-3.1-70b-versatile"
    temperature: float = 0.3
    max_tokens: int = 1024
    timeout: int = 60
    api_key: Optional[str] = None
    
    def __post_init__(self):
        # Load API key from environment if not provided
        if self.api_key is None:
            self.api_key = os.environ.get("GROQ_API_KEY")


@dataclass
class LocalLLMConfig:
    """Local LLM configuration (Ollama)."""
    provider: str = "ollama"
    model: str = "qwen2.5:7b"
    temperature: float = 0.3
    num_ctx: int = 4096
    num_predict: int = 512
    timeout: int = 120


@dataclass
class LLMConfig:
    """Combined LLM configuration with mode switching."""
    mode: Literal["cloud", "local"] = "cloud"
    cloud: CloudLLMConfig = field(default_factory=CloudLLMConfig)
    local: LocalLLMConfig = field(default_factory=LocalLLMConfig)
    
    def __post_init__(self):
        # Check environment variable for mode override
        env_mode = os.environ.get("EZCHESS_MODE", "").lower()
        if env_mode in ("cloud", "local"):
            self.mode = env_mode
    
    def get_active_config(self) -> Dict[str, Any]:
        """Get the currently active LLM configuration."""
        if self.mode == "cloud":
            return asdict(self.cloud)
        else:
            return asdict(self.local)
    
    def is_cloud(self) -> bool:
        return self.mode == "cloud"
    
    def is_local(self) -> bool:
        return self.mode == "local"


@dataclass
class UIConfig:
    """UI configuration."""
    theme: str = "dark"
    board_size: int = 560
    show_coordinates: bool = True
    show_annotations: bool = True
    show_best_move_arrow: bool = True
    show_threat_arrows: bool = True
    animation_speed_ms: int = 200
    panel_left_width: int = 300
    panel_right_width: int = 400


@dataclass
class AnalysisConfig:
    """Analysis feature configuration."""
    async_analysis: bool = True
    analysis_delay_ms: int = 300  # Debounce delay before auto-analysis
    show_top_moves: int = 3
    pv_depth: int = 6  # How many moves to show in principal variation
    auto_analyze: bool = True


@dataclass 
class MCPConfig:
    """MCP Server configuration for opening theory."""
    enabled: bool = True
    opening_server_port: int = 8765
    cache_opening_theory: bool = True
    theory_cache_ttl_hours: int = 24
    max_theory_depth: int = 20  # Max moves deep for theory lines


@dataclass
class AppConfig:
    """Complete application configuration."""
    engine: EngineConfig = field(default_factory=EngineConfig)
    llm: LLMConfig = field(default_factory=LLMConfig)
    ui: UIConfig = field(default_factory=UIConfig)
    analysis: AnalysisConfig = field(default_factory=AnalysisConfig)
    mcp: MCPConfig = field(default_factory=MCPConfig)
    
    @classmethod
    def load(cls, path: Optional[str] = None) -> "AppConfig":
        """Load configuration from YAML or JSON file."""
        if path is None:
            # Search for config file in order of preference
            project_root = Path(__file__).parent.parent
            
            # Check for YAML first, then JSON
            yaml_path = project_root / "config.yaml"
            json_path = project_root / "config.json"
            
            if yaml_path.exists() and YAML_AVAILABLE:
                path = yaml_path
            elif json_path.exists():
                path = json_path
            else:
                # Return default config
                return cls()
        else:
            path = Path(path)
        
        if path.exists():
            try:
                with open(path, 'r') as f:
                    if path.suffix == '.yaml' or path.suffix == '.yml':
                        if not YAML_AVAILABLE:
                            print("[Config] Warning: PyYAML not installed, cannot load YAML config")
                            return cls()
                        data = yaml.safe_load(f)
                    else:
                        data = json.load(f)
                
                if data:
                    return cls._from_dict(data)
            except Exception as e:
                print(f"[Config] Warning: Failed to load config from {path}: {e}")
                print("[Config] Using default configuration")
        
        return cls()
    
    @classmethod
    def _from_dict(cls, data: Dict) -> "AppConfig":
        """Create AppConfig from dictionary."""
        engine_data = data.get('engine', {})
        llm_data = data.get('llm', {})
        ui_data = data.get('ui', {})
        analysis_data = data.get('analysis', {})
        mcp_data = data.get('mcp', {})
        
        # Parse LLM config with nested cloud/local
        llm_config = LLMConfig(
            mode=llm_data.get('mode', 'cloud'),
            cloud=CloudLLMConfig(**llm_data.get('cloud', {})) if 'cloud' in llm_data else CloudLLMConfig(),
            local=LocalLLMConfig(**llm_data.get('local', {})) if 'local' in llm_data else LocalLLMConfig()
        )
        
        return cls(
            engine=EngineConfig(**engine_data) if engine_data else EngineConfig(),
            llm=llm_config,
            ui=UIConfig(**ui_data) if ui_data else UIConfig(),
            analysis=AnalysisConfig(**analysis_data) if analysis_data else AnalysisConfig(),
            mcp=MCPConfig(**mcp_data) if mcp_data else MCPConfig()
        )
    
    def save(self, path: Optional[str] = None):
        """Save configuration to JSON file."""
        if path is None:
            project_root = Path(__file__).parent.parent
            path = project_root / "config.json"
        else:
            path = Path(path)
        
        data = {
            'engine': asdict(self.engine),
            'llm': {k: v for k, v in asdict(self.llm).items() if k != 'api_key'},  # Don't save API key
            'ui': asdict(self.ui),
            'analysis': asdict(self.analysis),
            'mcp': asdict(self.mcp)
        }
        
        with open(path, 'w') as f:
            json.dump(data, f, indent=2)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary."""
        return {
            'engine': asdict(self.engine),
            'llm': {k: v for k, v in asdict(self.llm).items() if k != 'api_key'},
            'ui': asdict(self.ui),
            'analysis': asdict(self.analysis),
            'mcp': asdict(self.mcp)
        }


# =============================================================================
# GLOBAL CONFIG SINGLETON
# =============================================================================

_config: Optional[AppConfig] = None


def get_config() -> AppConfig:
    """Get global configuration singleton."""
    global _config
    if _config is None:
        _config = AppConfig.load()
    return _config


def reload_config(path: Optional[str] = None) -> AppConfig:
    """Reload configuration from file."""
    global _config
    _config = AppConfig.load(path)
    return _config


def update_config(**kwargs) -> AppConfig:
    """Update configuration values."""
    global _config
    if _config is None:
        _config = AppConfig.load()
    
    # Update nested config objects
    for key, value in kwargs.items():
        if hasattr(_config, key) and isinstance(value, dict):
            config_obj = getattr(_config, key)
            for k, v in value.items():
                if hasattr(config_obj, k):
                    setattr(config_obj, k, v)
    
    return _config


# =============================================================================
# CONSTANTS (Non-configurable)
# =============================================================================

# Piece values for material calculation (centipawns)
PIECE_VALUES = {
    'P': 100, 'N': 320, 'B': 330, 'R': 500, 'Q': 900, 'K': 0,
    'p': 100, 'n': 320, 'b': 330, 'r': 500, 'q': 900, 'k': 0
}

# Standard starting FEN
STARTING_FEN = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"

# Annotation colors (RGBA)
ARROW_COLORS = {
    'best_move': (88, 166, 255, 200),     # Blue - best move
    'good_move': (63, 185, 80, 180),       # Green - good alternative
    'threat': (248, 81, 73, 180),          # Red - opponent threat
    'interesting': (163, 113, 247, 160),   # Purple - interesting move
    'last_move': (130, 151, 105, 150),     # Muted - last move
}

HIGHLIGHT_COLORS = {
    'weakness': (255, 165, 0, 100),        # Orange - weak square
    'attacked': (255, 0, 0, 80),           # Red - under attack
    'defended': (0, 100, 255, 60),         # Blue - defended
    'key_square': (163, 113, 247, 80),     # Purple - key square
}

# Version info
VERSION = "1.1.0"
VERSION_NAME = "EZ Chess - SOTA Edition"


if __name__ == "__main__":
    # Test config
    config = get_config()
    print("=== EZ Chess Configuration ===")
    print(f"Engine depth: {config.engine.depth}")
    print(f"LLM model: {config.llm.model}")
    print(f"UI board size: {config.ui.board_size}")
    print(f"Async analysis: {config.analysis.async_analysis}")
    print(f"MCP enabled: {config.mcp.enabled}")
    
    # Save default config
    config.save()
    print("\nDefault config saved to config.json")
