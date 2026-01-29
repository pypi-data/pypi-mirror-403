"""
EZ-Chess Configuration Module
=============================

Re-exports configuration management from the source implementation.
"""

import sys
from pathlib import Path
import importlib.util

# Add src to path for imports
_src_path = Path(__file__).parent.parent.parent / "src"
if str(_src_path) not in sys.path:
    sys.path.insert(0, str(_src_path))

# Import using importlib to avoid name conflicts
spec = importlib.util.spec_from_file_location("src_config", _src_path / "config.py")
_config_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(_config_module)

get_config = _config_module.get_config
reload_config = _config_module.reload_config
update_config = _config_module.update_config
AppConfig = _config_module.AppConfig
LLMConfig = _config_module.LLMConfig
EngineConfig = _config_module.EngineConfig
UIConfig = _config_module.UIConfig
AnalysisConfig = _config_module.AnalysisConfig
CloudLLMConfig = _config_module.CloudLLMConfig
LocalLLMConfig = _config_module.LocalLLMConfig
MCPConfig = _config_module.MCPConfig

__all__ = [
    "get_config",
    "reload_config",
    "update_config",
    "AppConfig",
    "LLMConfig",
    "EngineConfig",
    "UIConfig",
    "AnalysisConfig",
    "CloudLLMConfig",
    "LocalLLMConfig",
    "MCPConfig",
]
