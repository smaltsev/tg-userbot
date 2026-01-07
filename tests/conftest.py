"""
Pytest configuration and fixtures for Telegram Group Scanner tests.
"""

import pytest
import asyncio
from pathlib import Path
import tempfile
import json
from telegram_scanner.config import ScannerConfig, ConfigManager


@pytest.fixture
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def sample_config():
    """Provide a sample configuration for testing."""
    return ScannerConfig(
        api_id="123456",
        api_hash="test_hash",
        scan_interval=30,
        max_history_days=7,
        selected_groups=["test_group"],
        keywords=["important", "urgent"],
        regex_patterns=[r"\d{4}-\d{2}-\d{2}"],
        logic_operator="OR",
        rate_limit_rpm=20
    )


@pytest.fixture
def temp_config_file():
    """Create a temporary configuration file for testing."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        config_data = {
            "api_credentials": {
                "api_id": "123456",
                "api_hash": "test_hash"
            },
            "scanning": {
                "scan_interval": 30,
                "max_history_days": 7,
                "selected_groups": ["test_group"]
            },
            "relevance": {
                "keywords": ["important", "urgent"],
                "regex_patterns": [r"\d{4}-\d{2}-\d{2}"],
                "logic": "OR"
            },
            "rate_limiting": {
                "requests_per_minute": 20,
                "flood_wait_multiplier": 1.5
            }
        }
        json.dump(config_data, f, indent=2)
        temp_path = f.name
    
    yield temp_path
    
    # Cleanup
    Path(temp_path).unlink(missing_ok=True)


@pytest.fixture
def config_manager(temp_config_file):
    """Provide a ConfigManager instance with temporary config file."""
    return ConfigManager(temp_config_file)