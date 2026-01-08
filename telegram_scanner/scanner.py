"""
Group discovery and message scanning functionality.
"""

import logging
import asyncio
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from telethon.tl.types import Channel, Chat, User
from telethon.errors import ChannelPrivateError, ChatAdminRequiredError, FloodWaitError
from telethon import events
from .config import ScannerConfig
from .auth import AuthenticationManager
from .processor import MessageProcessor
from .filter import RelevanceFilter
from .error_handling import (
    ErrorHandler,
    SessionExpiredError,
    NetworkConnectivityError,
    MaxRetriesExceededError,
    default_error_handler,
    default_rate_limiter,
    default_health_monitor,
    handle_message_processing_errors
)

logger = logging.getLogger(__name__)


@dataclass
class TelegramGroup:
    """Data model for Telegram group information."""
    id: int
    title: str
    username: Optional[str]
    member_count: int
    is_private: bool
    access_hash: int
    last_scanned: Optional[str] = None
    is_channel: bool = False
    is_megagroup: bool = False


class GroupScanner:
    """Discovers groups and manages message scanning operations."""
    
    def __init__(self, config: ScannerConfig, auth_manager: AuthenticationManager, 
                 message_processor: Optional[MessageProcessor] = None, 
                 relevance_filter: Optional[RelevanceFilter] = None):
        """Initialize group scanner with dependencies."""
        self.config = config
        self.auth_manager = auth_manager
        self.message_processor = message_processor
        self.relevance_filter = relevance_filter
        self._discovered_groups: List[TelegramGroup] = []
        self._monitoring = False
        self._monitoring_task: Optional[asyncio.Task] = None
        self._message_queue = asyncio.Queue()
        self._processing_tasks: List[asyncio.Task] = []
        self.error_handler = ErrorHandler(max_retries=3)
        
    async def discover_groups(self) -> List[TelegramGroup]:
        """
        Retrieve accessible groups/channels with comprehensive error handling.
        
        Returns:
            List of TelegramGroup objects with metadata
            
        Raises:
            ValueError: If not authenticated or client unavailable
            NetworkConnectivityError: If network issues persist
            SessionExpiredError: If session needs re-authentication
        """
        if not self.auth_manager.is_authenticated():
            raise ValueError("Authentication required before discovering groups")
            
        client = await self.auth_manager.get_client()
        if not client:
            raise ValueError("Telegram client not available")
        
        async def _discover_groups_impl():
            discovered_groups = []
            
            logger.info("Starting group discovery...")
            
            # Apply rate limiting
            await default_rate_limiter.acquire()
            
            # Get all dialogs (conversations)
            async for dialog in client.iter_dialogs():
                entity = dialog.entity
                
                # Process channels and groups only
                if isinstance(entity, (Channel, Chat)):
                    try:
                        # Apply rate limiting for each group
                        await default_rate_limiter.acquire()
                        
                        group_info = await self._extract_group_info(entity, client)
                        if group_info:
                            discovered_groups.append(group_info)
                            logger.debug(f"Discovered group: {group_info.title} (ID: {group_info.id})")
                            
                    except (ChannelPrivateError, ChatAdminRequiredError) as e:
                        # Handle access restrictions gracefully
                        logger.warning(f"Access denied to group {getattr(entity, 'title', 'Unknown')}: {e}")
                        continue
                        
                    except Exception as e:
                        # Log other errors but continue processing
                        logger.error(f"Error processing group {getattr(entity, 'title', 'Unknown')}: {e}")
                        default_health_monitor.record_failure("group_processing", e)
                        continue
                        
            self._discovered_groups = discovered_groups
            logger.info(f"Group discovery completed. Found {len(discovered_groups)} accessible groups")
            
            # Display group information
            await self._display_group_info(discovered_groups)
            
            return discovered_groups
        
        try:
            result = await self.error_handler.with_retry(
                _discover_groups_impl,
                operation_name="group_discovery"
            )
            default_health_monitor.record_success("group_discovery")
            return result
            
        except SessionExpiredError as e:
            logger.error(f"Session expired during group discovery: {e}")
            raise ValueError(f"Session expired. Please re-authenticate: {e}")
            
        except NetworkConnectivityError as e:
            logger.error(f"Network connectivity issues during group discovery: {e}")
            default_health_monitor.record_failure("group_discovery", e)
            raise ValueError(f"Network error during group discovery: {e}")
            
        except MaxRetriesExceededError as e:
            logger.error(f"Group discovery failed after multiple attempts: {e}")
            default_health_monitor.record_failure("group_discovery", e)
            raise ValueError(f"Group discovery failed: {e}")
            
        except Exception as e:
            logger.error(f"Unexpected error during group discovery: {e}")
            default_health_monitor.record_failure("group_discovery", e)
            raise ValueError(f"Group discovery failed: {e}")
            
    async def get_discovered_groups(self) -> List[TelegramGroup]:
        """Get previously discovered groups without re-scanning."""
        return self._discovered_groups.copy()
        
    async def get_group_by_id(self, group_id: int) -> Optional[TelegramGroup]:
        """Get a specific group by ID from discovered groups."""
        for group in self._discovered_groups:
            if group.id == group_id:
                return group
        return None
        
    async def get_groups_by_name(self, name_pattern: str) -> List[TelegramGroup]:
        """Get groups matching a name pattern (case-insensitive)."""
        pattern = name_pattern.lower()
        matching_groups = []
        
        for group in self._discovered_groups:
            if (pattern in group.title.lower() or 
                (group.username and pattern in group.username.lower())):
                matching_groups.append(group)
                
        return matching_groups
        
    async def _extract_group_info(self, entity, client) -> Optional[TelegramGroup]:
        """
        Extract group information from Telegram entity with error handling.
        
        Args:
            entity: Telegram Channel or Chat entity
            client: Telethon client
            
        Returns:
            TelegramGroup object or None if extraction fails
        """
        async def _extract_impl():
            # Get basic information
            group_id = entity.id
            title = getattr(entity, 'title', 'Unknown')
            username = getattr(entity, 'username', None)
            access_hash = getattr(entity, 'access_hash', 0)
            
            # Determine group type and privacy
            if isinstance(entity, Channel):
                is_private = not entity.username  # Channels without username are private
                is_channel = not entity.megagroup
                is_megagroup = entity.megagroup
            else:  # Chat
                is_private = True  # Regular chats are always private
                is_channel = False
                is_megagroup = False
                
            # Get member count
            member_count = 0
            try:
                if hasattr(entity, 'participants_count'):
                    member_count = entity.participants_count
                else:
                    # For regular chats, try to get full chat info
                    full_chat = await client.get_entity(entity)
                    if hasattr(full_chat, 'participants_count'):
                        member_count = full_chat.participants_count
            except (ChannelPrivateError, ChatAdminRequiredError):
                # Re-raise access permission errors to be handled at higher level
                raise
            except Exception as e:
                logger.debug(f"Could not get member count for {title}: {e}")
                member_count = 0
                
            return TelegramGroup(
                id=group_id,
                title=title,
                username=username,
                member_count=member_count,
                is_private=is_private,
                access_hash=access_hash,
                is_channel=is_channel,
                is_megagroup=is_megagroup
            )
        
        try:
            return await self.error_handler.with_retry(
                _extract_impl,
                operation_name="group_info_extraction",
                max_retries=2
            )
        except (ChannelPrivateError, ChatAdminRequiredError):
            # Re-raise permission errors without retry
            raise
        except Exception as e:
            logger.error(f"Error extracting group info: {e}")
            default_health_monitor.record_failure("group_info_extraction", e)
            return None
            
    async def _display_group_info(self, groups: List[TelegramGroup]):
        """Display discovered group information."""
        if not groups:
            logger.info("No accessible groups found")
            return
            
        logger.info(f"\n{'='*60}")
        logger.info("DISCOVERED TELEGRAM GROUPS")
        logger.info(f"{'='*60}")
        
        for i, group in enumerate(groups, 1):
            group_type = "Channel" if group.is_channel else "Megagroup" if group.is_megagroup else "Group"
            privacy = "Private" if group.is_private else "Public"
            username_info = f"@{group.username}" if group.username else "No username"
            
            logger.info(f"{i:2d}. {group.title}")
            logger.info(f"    Type: {group_type} ({privacy})")
            logger.info(f"    Username: {username_info}")
            logger.info(f"    Members: {group.member_count:,}")
            logger.info(f"    ID: {group.id}")
            logger.info("")
            
        logger.info(f"Total accessible groups: {len(groups)}")
        logger.info(f"{'='*60}")
        
    async def start_monitoring(self):
        """Begin real-time message monitoring."""
        if not self.auth_manager.is_authenticated():
            raise ValueError("Authentication required before starting monitoring")
            
        if self._monitoring:
            logger.warning("Monitoring is already active")
            return
            
        client = await self.auth_manager.get_client()
        if not client:
            raise ValueError("Telegram client not available")
            
        if not self._discovered_groups:
            logger.warning("No groups discovered. Run discover_groups() first")
            return
            
        logger.info("Starting real-time message monitoring...")
        self._monitoring = True
        
        # Set up event handler for new messages
        @client.on(events.NewMessage)
        async def new_message_handler(event):
            """Handle new message events."""
            try:
                # Check if message is from a monitored group
                if hasattr(event.message, 'peer_id') and event.message.peer_id:
                    group_id = None
                    if hasattr(event.message.peer_id, 'channel_id'):
                        group_id = event.message.peer_id.channel_id
                    elif hasattr(event.message.peer_id, 'chat_id'):
                        group_id = event.message.peer_id.chat_id
                    
                    if group_id and any(group.id == group_id for group in self._discovered_groups):
                        # Add message to processing queue for consistent handling
                        await self._message_queue.put((event.message, client))
                        logger.debug(f"Queued new message {event.message.id} from group {group_id}")
                        
            except Exception as e:
                logger.error(f"Error in new message handler: {e}")
        
        # Start message processing workers
        num_workers = min(3, len(self._discovered_groups))  # Limit concurrent processing
        for i in range(num_workers):
            task = asyncio.create_task(self._message_processing_worker(f"worker-{i}"))
            self._processing_tasks.append(task)
        
        logger.info(f"Real-time monitoring started with {num_workers} processing workers")
        
    async def stop_monitoring(self):
        """Stop real-time message monitoring."""
        if not self._monitoring:
            logger.warning("Monitoring is not active")
            return
            
        logger.info("Stopping real-time message monitoring...")
        self._monitoring = False
        
        # Cancel all processing tasks
        for task in self._processing_tasks:
            if not task.done():
                task.cancel()
        
        # Wait for tasks to complete
        if self._processing_tasks:
            await asyncio.gather(*self._processing_tasks, return_exceptions=True)
        
        self._processing_tasks.clear()
        
        # Clear any remaining messages in queue
        while not self._message_queue.empty():
            try:
                self._message_queue.get_nowait()
            except asyncio.QueueEmpty:
                break
                
        logger.info("Real-time monitoring stopped")
        
    async def _message_processing_worker(self, worker_name: str):
        """Worker task to process messages from the queue."""
        logger.debug(f"Message processing worker {worker_name} started")
        
        while self._monitoring:
            try:
                # Wait for message with timeout to allow periodic checks
                message, client = await asyncio.wait_for(
                    self._message_queue.get(), 
                    timeout=1.0
                )
                
                # Process the message
                await self.handle_new_message(message, client)
                
            except asyncio.TimeoutError:
                # Timeout is expected, continue monitoring
                continue
            except asyncio.CancelledError:
                logger.debug(f"Worker {worker_name} cancelled")
                break
            except Exception as e:
                logger.error(f"Error in worker {worker_name}: {e}")
                # Continue processing other messages
                continue
                
        logger.debug(f"Message processing worker {worker_name} stopped")
        
    @handle_message_processing_errors
    async def handle_new_message(self, message, client):
        """Process incoming messages with comprehensive error handling."""
        try:
            if not self.message_processor:
                logger.warning("No message processor available")
                return
                
            # Apply rate limiting
            await default_rate_limiter.acquire()
            
            # Process the message
            processed_message = await self.message_processor.process_message(message, client)
            if not processed_message:
                logger.debug(f"Failed to process message {message.id}")
                return
            
            # Apply relevance filtering if available
            is_relevant = True
            if self.relevance_filter:
                is_relevant = await self.relevance_filter.is_relevant(processed_message)
            
            if is_relevant:
                logger.info(f"Relevant message found: {processed_message.id} from {processed_message.group_name}")
                
                # Store the message if storage manager is available
                if hasattr(self.message_processor, 'storage_manager') and self.message_processor.storage_manager:
                    await self.message_processor.storage_manager.store_message(processed_message)
                    
                default_health_monitor.record_success("message_processing")
            else:
                logger.debug(f"Message {processed_message.id} not relevant, skipping storage")
                
        except SessionExpiredError as e:
            logger.error(f"Session expired while processing message {message.id}: {e}")
            # Stop monitoring if session expired
            await self.stop_monitoring()
            raise
        except Exception as e:
            logger.error(f"Error handling new message {message.id}: {e}")
            default_health_monitor.record_failure("message_processing", e)
            # Continue processing - don't let one message failure stop monitoring
            
    def is_monitoring(self) -> bool:
        """Check if real-time monitoring is active."""
        return self._monitoring
        
    async def scan_history(self):
        """Process historical messages."""
        # Implementation will be added in task 5
        pass