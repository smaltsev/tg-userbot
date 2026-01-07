"""
Main application entry point for Telegram Group Scanner.
"""

import asyncio
import logging
from typing import Optional

from .config import ConfigManager
from .auth import AuthenticationManager
from .scanner import GroupScanner
from .processor import MessageProcessor
from .filter import RelevanceFilter
from .storage import StorageManager

logger = logging.getLogger(__name__)


class TelegramScanner:
    """Main application class that coordinates all components."""
    
    def __init__(self, config_path: str = "config.json"):
        """Initialize the Telegram Scanner with configuration."""
        self.config_manager = ConfigManager(config_path)
        self.auth_manager: Optional[AuthenticationManager] = None
        self.group_scanner: Optional[GroupScanner] = None
        self.message_processor: Optional[MessageProcessor] = None
        self.relevance_filter: Optional[RelevanceFilter] = None
        self.storage_manager: Optional[StorageManager] = None
        
    async def initialize(self):
        """Initialize all components with configuration."""
        config = await self.config_manager.load_config()
        
        self.auth_manager = AuthenticationManager(config)
        self.storage_manager = StorageManager(config)
        self.relevance_filter = RelevanceFilter(config)
        self.message_processor = MessageProcessor(config, self.storage_manager)
        self.group_scanner = GroupScanner(
            config, 
            self.auth_manager, 
            self.message_processor, 
            self.relevance_filter
        )
        
    async def run(self):
        """Main application entry point."""
        await self.initialize()
        
        # Authenticate user
        await self.auth_manager.authenticate()
        
        # Discover and display groups
        groups = await self.group_scanner.discover_groups()
        logger.info(f"Discovered {len(groups)} accessible groups")
        
        # Start monitoring
        await self.group_scanner.start_monitoring()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    scanner = TelegramScanner()
    asyncio.run(scanner.run())