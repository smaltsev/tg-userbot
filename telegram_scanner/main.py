"""
Main application entry point for Telegram Group Scanner.
"""

import asyncio
import logging
import json
from typing import Optional

from .config import ConfigManager
from .auth import AuthenticationManager
from .scanner import GroupScanner
from .processor import MessageProcessor
from .filter import RelevanceFilter
from .storage import StorageManager
from .command_interface import CommandInterface

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
        self.command_interface: Optional[CommandInterface] = None
        
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
        
        # Initialize command interface
        self.command_interface = CommandInterface(self)
        
        # Set command interface reference in group scanner for statistics
        self.group_scanner.set_command_interface(self.command_interface)
        
    async def run_with_commands(self):
        """Run the application with command interface support."""
        await self.initialize()
        
        logger.info("Telegram Scanner with Command Interface")
        logger.info("Available commands: start, stop, pause, resume, status, report, quit")
        
        while True:
            try:
                command = input("\nEnter command: ").strip().lower()
                
                if command == "start":
                    result = await self.command_interface.start_scanning()
                    print(f"Result: {result}")
                    
                elif command == "stop":
                    result = await self.command_interface.stop_scanning()
                    print(f"Result: {result}")
                    
                elif command == "pause":
                    result = await self.command_interface.pause_scanning()
                    print(f"Result: {result}")
                    
                elif command == "resume":
                    result = await self.command_interface.resume_scanning()
                    print(f"Result: {result}")
                    
                elif command == "status":
                    status = await self.command_interface.get_status()
                    print(f"Status: {json.dumps(status.to_dict(), indent=2)}")
                    
                elif command == "report":
                    report = await self.command_interface.generate_report()
                    print(f"Report: {json.dumps(report.to_dict(), indent=2)}")
                    
                elif command in ["quit", "exit", "q"]:
                    # Stop scanner if running
                    if self.command_interface.get_current_state().value != "stopped":
                        await self.command_interface.stop_scanning()
                    break
                    
                else:
                    print("Unknown command. Available: start, stop, pause, resume, status, report, quit")
                    
            except KeyboardInterrupt:
                logger.info("Shutdown requested by user")
                if self.command_interface.get_current_state().value != "stopped":
                    await self.command_interface.stop_scanning()
                break
            except Exception as e:
                logger.error(f"Error processing command: {e}")
                
        logger.info("Application terminated")
        
    async def run(self):
        """Main application entry point."""
        await self.initialize()
        
        # Authenticate user
        await self.auth_manager.authenticate()
        
        # Discover and display groups
        groups = await self.group_scanner.discover_groups()
        logger.info(f"Discovered {len(groups)} accessible groups")
        
        # Start monitoring
        try:
            await self.group_scanner.start_monitoring()
            
            # Keep the application running
            logger.info("Monitoring active. Press Ctrl+C to stop...")
            while self.group_scanner.is_monitoring():
                await asyncio.sleep(1)
                
        except KeyboardInterrupt:
            logger.info("Shutdown requested by user")
        finally:
            if self.group_scanner and self.group_scanner.is_monitoring():
                await self.group_scanner.stop_monitoring()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    scanner = TelegramScanner()
    # Use command interface by default
    asyncio.run(scanner.run_with_commands())