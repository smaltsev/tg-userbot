"""
Configuration management for Telegram Group Scanner.
"""

import json
import logging
from dataclasses import dataclass, asdict
from typing import List, Optional, Dict, Any
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class ScannerConfig:
    """Configuration data model for the scanner."""
    api_id: str
    api_hash: str
    scan_interval: int = 30
    max_history_days: int = 7
    selected_groups: List[str] = None
    keywords: List[str] = None
    regex_patterns: List[str] = None
    logic_operator: str = "OR"
    rate_limit_rpm: int = 20
    default_delay: float = 1.0
    max_wait_time: float = 60.0
    debug_mode: bool = False
    
    def __post_init__(self):
        """Initialize default values for mutable fields."""
        if self.selected_groups is None:
            self.selected_groups = []
        if self.keywords is None:
            self.keywords = []
        if self.regex_patterns is None:
            self.regex_patterns = []


class ConfigManager:
    """Manages application configuration loading and validation."""
    
    def __init__(self, config_path: str):
        """Initialize configuration manager with file path."""
        self.config_path = Path(config_path)
        self._config: Optional[ScannerConfig] = None
        
    async def load_config(self) -> ScannerConfig:
        """Load configuration from file or create default."""
        if not self.config_path.exists():
            logger.info(f"Configuration file not found at {self.config_path}")
            await self._create_default_config()
            
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
                
            # Flatten nested structure for dataclass
            flattened = self._flatten_config(config_data)
            self._config = ScannerConfig(**flattened)
            
            logger.info("Configuration loaded successfully")
            return self._config
            
        except (json.JSONDecodeError, TypeError, KeyError) as e:
            logger.error(f"Error loading configuration: {e}")
            raise ValueError(f"Invalid configuration file: {e}")
            
    async def save_config(self, config: ScannerConfig):
        """Save configuration to file."""
        config_data = self._structure_config(asdict(config))
        
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)
                
            self._config = config
            logger.info("Configuration saved successfully")
            
        except (OSError, TypeError) as e:
            logger.error(f"Error saving configuration: {e}")
            raise
            
    async def reload_config(self) -> ScannerConfig:
        """Reload configuration from file."""
        return await self.load_config()
        
    def get_config(self) -> Optional[ScannerConfig]:
        """Get current configuration."""
        return self._config
        
    async def _create_default_config(self):
        """Create default configuration file."""
        default_config = {
            "api_credentials": {
                "api_id": "your_api_id_here",
                "api_hash": "your_api_hash_here"
            },
            "scanning": {
                "scan_interval": 30,
                "max_history_days": 7,
                "selected_groups": [],
                "debug_mode": False
            },
            "relevance": {
                "keywords": ["important", "urgent"],
                "regex_patterns": [],
                "logic": "OR"
            },
            "rate_limiting": {
                "requests_per_minute": 20,
                "flood_wait_multiplier": 1.5,
                "default_delay": 1.0,
                "max_wait_time": 60.0
            }
        }
        
        try:
            # Create directory if it doesn't exist
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(default_config, f, indent=2, ensure_ascii=False)
                
            logger.info(f"Default configuration created at {self.config_path}")
            logger.warning("Please update the configuration file with your API credentials")
            
        except OSError as e:
            logger.error(f"Error creating default configuration: {e}")
            raise
            
    def _flatten_config(self, config_data: Dict[str, Any]) -> Dict[str, Any]:
        """Flatten nested configuration structure for dataclass."""
        flattened = {}
        
        # API credentials
        api_creds = config_data.get("api_credentials", {})
        flattened["api_id"] = api_creds.get("api_id", "")
        flattened["api_hash"] = api_creds.get("api_hash", "")
        
        # Scanning settings
        scanning = config_data.get("scanning", {})
        flattened["scan_interval"] = scanning.get("scan_interval", 30)
        flattened["max_history_days"] = scanning.get("max_history_days", 7)
        flattened["selected_groups"] = scanning.get("selected_groups", [])
        flattened["debug_mode"] = scanning.get("debug_mode", False)
        
        # Relevance settings
        relevance = config_data.get("relevance", {})
        flattened["keywords"] = relevance.get("keywords", [])
        flattened["regex_patterns"] = relevance.get("regex_patterns", [])
        flattened["logic_operator"] = relevance.get("logic", "OR")
        
        # Rate limiting
        rate_limiting = config_data.get("rate_limiting", {})
        flattened["rate_limit_rpm"] = rate_limiting.get("requests_per_minute", 20)
        flattened["default_delay"] = rate_limiting.get("default_delay", 1.0)
        flattened["max_wait_time"] = rate_limiting.get("max_wait_time", 60.0)
        
        return flattened
        
    def _structure_config(self, config_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Structure flat configuration into nested format."""
        return {
            "api_credentials": {
                "api_id": config_dict["api_id"],
                "api_hash": config_dict["api_hash"]
            },
            "scanning": {
                "scan_interval": config_dict["scan_interval"],
                "max_history_days": config_dict["max_history_days"],
                "selected_groups": config_dict["selected_groups"],
                "debug_mode": config_dict.get("debug_mode", False)
            },
            "relevance": {
                "keywords": config_dict["keywords"],
                "regex_patterns": config_dict["regex_patterns"],
                "logic": config_dict["logic_operator"]
            },
            "rate_limiting": {
                "requests_per_minute": config_dict["rate_limit_rpm"],
                "flood_wait_multiplier": 1.5,
                "default_delay": config_dict.get("default_delay", 1.0),
                "max_wait_time": config_dict.get("max_wait_time", 60.0)
            }
        }