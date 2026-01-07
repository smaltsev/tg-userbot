"""
Tests for configuration management functionality.
"""

import pytest
import json
import tempfile
from pathlib import Path
from telegram_scanner.config import ConfigManager, ScannerConfig


class TestConfigManager:
    """Test cases for ConfigManager class."""
    
    @pytest.mark.asyncio
    async def test_load_existing_config(self, config_manager, sample_config):
        """Test loading an existing configuration file."""
        loaded_config = await config_manager.load_config()
        
        assert loaded_config.api_id == sample_config.api_id
        assert loaded_config.api_hash == sample_config.api_hash
        assert loaded_config.scan_interval == sample_config.scan_interval
        assert loaded_config.keywords == sample_config.keywords
        
    @pytest.mark.asyncio
    async def test_create_default_config(self):
        """Test creation of default configuration file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "test_config.json"
            manager = ConfigManager(str(config_path))
            
            # Load config should create default file
            config = await manager.load_config()
            
            assert config_path.exists()
            assert config.api_id == "your_api_id_here"
            assert config.scan_interval == 30
            
    @pytest.mark.asyncio
    async def test_save_config(self, sample_config):
        """Test saving configuration to file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_path = f.name
            
        try:
            manager = ConfigManager(temp_path)
            await manager.save_config(sample_config)
            
            # Verify file was created and contains correct data
            with open(temp_path, 'r') as f:
                saved_data = json.load(f)
                
            assert saved_data["api_credentials"]["api_id"] == sample_config.api_id
            assert saved_data["scanning"]["scan_interval"] == sample_config.scan_interval
            
        finally:
            Path(temp_path).unlink(missing_ok=True)
            
    @pytest.mark.asyncio
    async def test_reload_config(self, config_manager):
        """Test reloading configuration from file."""
        original_config = await config_manager.load_config()
        reloaded_config = await config_manager.reload_config()
        
        assert original_config.api_id == reloaded_config.api_id
        assert original_config.keywords == reloaded_config.keywords


class TestScannerConfig:
    """Test cases for ScannerConfig dataclass."""
    
    def test_config_initialization(self):
        """Test proper initialization of ScannerConfig."""
        config = ScannerConfig(
            api_id="123456",
            api_hash="test_hash"
        )
        
        assert config.api_id == "123456"
        assert config.api_hash == "test_hash"
        assert config.scan_interval == 30  # default value
        assert config.selected_groups == []  # default empty list
        assert config.keywords == []  # default empty list
        
    def test_config_with_custom_values(self):
        """Test ScannerConfig with custom values."""
        config = ScannerConfig(
            api_id="123456",
            api_hash="test_hash",
            scan_interval=60,
            keywords=["test", "important"],
            logic_operator="AND"
        )
        
        assert config.scan_interval == 60
        assert config.keywords == ["test", "important"]
        assert config.logic_operator == "AND"