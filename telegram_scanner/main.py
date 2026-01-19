"""
Main application entry point for Telegram Group Scanner.
"""

import asyncio
import logging
import json
import argparse
import sys
from typing import Optional
from pathlib import Path

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
        self.config_path = config_path
        self.config_manager = ConfigManager(config_path)
        self.auth_manager: Optional[AuthenticationManager] = None
        self.group_scanner: Optional[GroupScanner] = None
        self.message_processor: Optional[MessageProcessor] = None
        self.relevance_filter: Optional[RelevanceFilter] = None
        self.storage_manager: Optional[StorageManager] = None
        self.command_interface: Optional[CommandInterface] = None
        self._initialized = False
        
    async def initialize(self):
        """Initialize all components with configuration."""
        if self._initialized:
            return
            
        try:
            config = await self.config_manager.load_config()
            
            # Initialize components in dependency order
            self.auth_manager = AuthenticationManager(config)
            self.storage_manager = StorageManager(config)
            self.relevance_filter = RelevanceFilter(config)
            
            # Create rate limiter with config values
            from .error_handling import RateLimiter
            rate_limiter = RateLimiter(
                requests_per_minute=config.rate_limit_rpm,
                default_delay=config.default_delay,
                max_wait_time=config.max_wait_time
            )
            
            self.message_processor = MessageProcessor(config, self.storage_manager, rate_limiter)
            self.group_scanner = GroupScanner(
                config, 
                self.auth_manager, 
                self.message_processor, 
                self.relevance_filter
            )
            
            # Set the same rate limiter in the scanner
            self.group_scanner.rate_limiter = rate_limiter
            
            # Initialize command interface
            self.command_interface = CommandInterface(self)
            
            # Set command interface reference in group scanner for statistics
            self.group_scanner.set_command_interface(self.command_interface)
            
            self._initialized = True
            logger.info("All components initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize components: {e}")
            raise
            
    async def shutdown(self):
        """Gracefully shutdown all components."""
        logger.info("Shutting down Telegram Scanner...")
        
        try:
            # Stop scanning if active
            if self.command_interface and self.command_interface.get_current_state().value != "stopped":
                await self.command_interface.stop_scanning()
                
            # Close authentication session
            if self.auth_manager and self.auth_manager._client:
                await self.auth_manager._client.disconnect()
                
            logger.info("Shutdown completed successfully")
            
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")
            
    async def run_interactive(self):
        """Run the application with interactive command interface."""
        await self.initialize()
        
        print("=" * 60)
        print("Telegram Group Scanner - Interactive Mode")
        print("=" * 60)
        print("Available commands:")
        print("  start   - Start scanning groups")
        print("  stop    - Stop scanning")
        print("  pause   - Pause scanning")
        print("  resume  - Resume scanning")
        print("  status  - Show current status")
        print("  report  - Generate scanning report")
        print("  list    - List discovered groups")
        print("  config  - Show current configuration")
        print("  reload  - Reload configuration")
        print("  help    - Show this help message")
        print("  quit    - Exit application")
        print("=" * 60)
        
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
                    print(f"\nStatus:")
                    print(json.dumps(status.to_dict(), indent=2))
                    
                elif command == "report":
                    report = await self.command_interface.generate_report()
                    print(f"\nReport:")
                    print(json.dumps(report.to_dict(), indent=2))
                    
                elif command == "config":
                    config = self.config_manager.get_config()
                    if config:
                        # Hide sensitive information
                        config_dict = {
                            "scan_interval": config.scan_interval,
                            "max_history_days": config.max_history_days,
                            "selected_groups": config.selected_groups,
                            "keywords": config.keywords,
                            "regex_patterns": config.regex_patterns,
                            "logic_operator": config.logic_operator,
                            "rate_limit_rpm": config.rate_limit_rpm
                        }
                        print(f"\nConfiguration:")
                        print(json.dumps(config_dict, indent=2))
                    else:
                        print("Configuration not loaded")
                        
                elif command == "reload":
                    try:
                        await self.config_manager.reload_config()
                        print("Configuration reloaded successfully")
                    except Exception as e:
                        print(f"Error reloading configuration: {e}")
                
                elif command == "list":
                    # List discovered groups
                    if self.group_scanner and self.group_scanner._discovered_groups:
                        groups = self.group_scanner._discovered_groups
                        print(f"\n{'='*60}")
                        print(f"DISCOVERED GROUPS ({len(groups)} total)")
                        print(f"{'='*60}")
                        
                        for i, group in enumerate(groups, 1):
                            group_type = "Channel" if group.is_channel else "Megagroup" if group.is_megagroup else "Group"
                            privacy = "Private" if group.is_private else "Public"
                            username_info = f"@{group.username}" if group.username else "No username"
                            member_count_info = f"{group.member_count:,}" if group.member_count is not None else "Unknown"
                            
                            print(f"{i:2d}. {group.title}")
                            print(f"    Type: {group_type} ({privacy})")
                            print(f"    Username: {username_info}")
                            print(f"    Members: {member_count_info}")
                            print(f"    ID: {group.id}")
                            print("")
                        
                        print(f"{'='*60}")
                    else:
                        print("No groups discovered yet. Run 'start' command first.")
                
                elif command == "help":
                    # Show detailed help
                    print(f"\n{'='*60}")
                    print("TELEGRAM GROUP SCANNER - COMMAND HELP")
                    print(f"{'='*60}")
                    print("\nCOMMANDS:")
                    print("\n  start")
                    print("    Start scanning the configured Telegram groups.")
                    print("    This will discover groups and begin monitoring for")
                    print("    messages matching your keywords.")
                    print("\n  stop")
                    print("    Stop the scanner and end monitoring.")
                    print("\n  pause")
                    print("    Temporarily pause monitoring without stopping.")
                    print("    Use 'resume' to continue.")
                    print("\n  resume")
                    print("    Resume monitoring after pausing.")
                    print("\n  status")
                    print("    Display current scanner status including:")
                    print("    - Current state (running/stopped/paused)")
                    print("    - Groups being monitored")
                    print("    - Messages found")
                    print("    - Statistics")
                    print("\n  report")
                    print("    Generate a detailed scanning report with:")
                    print("    - Summary of activity")
                    print("    - Relevant messages found")
                    print("    - Group statistics")
                    print("\n  list")
                    print("    List all discovered Telegram groups with details:")
                    print("    - Group name and type")
                    print("    - Member count")
                    print("    - Username (if public)")
                    print("    - Group ID")
                    print("\n  config")
                    print("    Show current configuration settings:")
                    print("    - Selected groups to monitor")
                    print("    - Keywords to search for")
                    print("    - Scan interval and other settings")
                    print("\n  reload")
                    print("    Reload configuration from config.json file.")
                    print("    Useful after making changes to the config.")
                    print("\n  help")
                    print("    Show this help message.")
                    print("\n  quit (or exit, q)")
                    print("    Exit the application.")
                    print(f"\n{'='*60}")
                    print("\nCONFIGURATION:")
                    print("  Edit config.json to change:")
                    print("  - selected_groups: Groups to monitor")
                    print("  - keywords: Keywords to search for")
                    print("  - scan_interval: How often to check for messages")
                    print("  - rate_limiting: API rate limit settings")
                    print(f"\n{'='*60}")
                    print("\nEXAMPLE WORKFLOW:")
                    print("  1. Type 'start' to begin scanning")
                    print("  2. Type 'status' to check progress")
                    print("  3. Type 'list' to see discovered groups")
                    print("  4. Type 'report' to see found messages")
                    print("  5. Type 'stop' when done")
                    print(f"{'='*60}\n")
                    
                elif command in ["quit", "exit", "q"]:
                    break
                    
                else:
                    print("Unknown command. Type 'help' for available commands.")
                    
            except KeyboardInterrupt:
                print("\nShutdown requested by user")
                break
            except EOFError:
                print("\nEOF received, shutting down")
                break
            except Exception as e:
                logger.error(f"Error processing command: {e}")
                print(f"Error: {e}")
                
        await self.shutdown()
        
    async def run_discovery_test(self):
        """Run group discovery test only."""
        await self.initialize()
        
        logger.info("Starting group discovery test")
        
        try:
            # Ensure authentication (will try session first, then full auth if needed)
            authenticated = await self.auth_manager.ensure_authenticated()
            if not authenticated:
                logger.error("Authentication failed")
                return False
                
            # Discover and display groups
            import time
            start_time = time.time()
            groups = await self.group_scanner.discover_groups()
            end_time = time.time()
            
            duration = end_time - start_time
            logger.info(f"Discovery completed in {duration:.1f} seconds")
            logger.info(f"Discovered {len(groups)} accessible groups")
            
            return True
                
        except KeyboardInterrupt:
            logger.info("Discovery test interrupted by user")
        except Exception as e:
            logger.error(f"Error in discovery test: {e}")
            return False
        finally:
            await self.shutdown()
            
        return True
        
    async def run_batch(self, duration_minutes: Optional[int] = None):
        """Run the application in batch mode for a specified duration."""
        await self.initialize()
        
        logger.info("Starting Telegram Scanner in batch mode")
        
        try:
            # Ensure authentication (will try session first, then full auth if needed)
            authenticated = await self.auth_manager.ensure_authenticated()
            if not authenticated:
                logger.error("Authentication failed")
                return False
                
            # Discover and display groups
            groups = await self.group_scanner.discover_groups()
            logger.info(f"Discovered {len(groups)} accessible groups")
            
            # Start monitoring
            result = await self.command_interface.start_scanning()
            logger.info(f"Scanning started: {result}")
            
            # Run for specified duration or until interrupted
            if duration_minutes:
                logger.info(f"Running for {duration_minutes} minutes...")
                await asyncio.sleep(duration_minutes * 60)
                logger.info("Duration completed, stopping scanner")
            else:
                logger.info("Running indefinitely. Press Ctrl+C to stop...")
                while self.command_interface.get_current_state().value == "running":
                    await asyncio.sleep(1)
                    
        except KeyboardInterrupt:
            logger.info("Shutdown requested by user")
        except Exception as e:
            logger.error(f"Error in batch mode: {e}")
            return False
        finally:
            await self.shutdown()
            
        return True
        
    async def run_with_commands(self):
        """Legacy method - use run_interactive instead."""
        await self.run_interactive()
        
    async def run(self):
        """Legacy method - use run_batch instead."""
        await self.run_batch()


def setup_logging(log_level: str = "INFO", log_file: Optional[str] = None):
    """Setup logging configuration."""
    level = getattr(logging, log_level.upper(), logging.INFO)
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Setup console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    
    # Setup root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    root_logger.addHandler(console_handler)
    
    # Setup file handler if specified
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
        
    # Reduce telethon logging noise
    logging.getLogger('telethon').setLevel(logging.WARNING)


def create_parser() -> argparse.ArgumentParser:
    """Create command line argument parser."""
    parser = argparse.ArgumentParser(
        description="Telegram Group Scanner - Monitor Telegram groups for relevant content",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                          # Run in interactive mode
  %(prog)s --batch                  # Run in batch mode indefinitely
  %(prog)s --batch --duration 60    # Run in batch mode for 60 minutes
  %(prog)s --config custom.json     # Use custom configuration file
  %(prog)s --log-level DEBUG        # Enable debug logging
        """
    )
    
    parser.add_argument(
        '--config', '-c',
        default='config.json',
        help='Configuration file path (default: config.json)'
    )
    
    parser.add_argument(
        '--batch', '-b',
        action='store_true',
        help='Run in batch mode (non-interactive)'
    )
    
    parser.add_argument(
        '--test-discovery', '-t',
        action='store_true',
        help='Test group discovery only (no monitoring)'
    )
    
    parser.add_argument(
        '--duration', '-d',
        type=int,
        help='Duration in minutes for batch mode (default: run indefinitely)'
    )
    
    parser.add_argument(
        '--log-level', '-l',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        default='INFO',
        help='Logging level (default: INFO)'
    )
    
    parser.add_argument(
        '--log-file', '-f',
        help='Log file path (default: console only)'
    )
    
    parser.add_argument(
        '--version', '-v',
        action='version',
        version='Telegram Group Scanner 1.0.0'
    )
    
    return parser


async def main():
    """Main entry point with command line interface."""
    parser = create_parser()
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.log_level, args.log_file)
    
    # Validate configuration file path
    config_path = Path(args.config)
    if not config_path.parent.exists():
        logger.error(f"Configuration directory does not exist: {config_path.parent}")
        sys.exit(1)
        
    # Create scanner instance
    scanner = TelegramScanner(str(config_path))
    
    try:
        if args.test_discovery:
            logger.info("Starting discovery test mode")
            success = await scanner.run_discovery_test()
            sys.exit(0 if success else 1)
        elif args.batch:
            logger.info("Starting in batch mode")
            success = await scanner.run_batch(args.duration)
            sys.exit(0 if success else 1)
        else:
            logger.info("Starting in interactive mode")
            await scanner.run_interactive()
            
    except KeyboardInterrupt:
        logger.info("Application interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Application error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())