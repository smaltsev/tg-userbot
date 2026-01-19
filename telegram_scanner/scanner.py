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
        self._command_interface = None
        
        # Create rate limiter with config values
        from .error_handling import RateLimiter
        self.rate_limiter = RateLimiter(
            requests_per_minute=config.rate_limit_rpm,
            default_delay=config.default_delay,
            max_wait_time=config.max_wait_time
        )
        
    def set_command_interface(self, command_interface):
        """Set reference to command interface for statistics tracking."""
        self._command_interface = command_interface
        
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
        if not await self.auth_manager.ensure_authenticated():
            raise ValueError("Authentication required before discovering groups")
            
        client = await self.auth_manager.get_client()
        if not client:
            raise ValueError("Telegram client not available")
        
        async def _discover_groups_impl():
            discovered_groups = []
            
            logger.info("Starting group discovery...")
            
            # If we have specific groups selected, try to find them directly first
            if self.config.selected_groups:
                logger.info(f"Searching for {len(self.config.selected_groups)} specific groups: {self.config.selected_groups}")
                
                for group_name in self.config.selected_groups:
                    try:
                        await self.rate_limiter.acquire()
                        
                        # Try to find the group by username first (if it looks like a username)
                        if group_name.startswith('@') or not any(c in group_name for c in [' ', 'а', 'б', 'в', 'г', 'д', 'е', 'ё', 'ж', 'з', 'и', 'й', 'к', 'л', 'м', 'н', 'о', 'п', 'р', 'с', 'т', 'у', 'ф', 'х', 'ц', 'ч', 'ш', 'щ', 'ъ', 'ы', 'ь', 'э', 'ю', 'я']):
                            try:
                                username = group_name.lstrip('@')
                                entity = await client.get_entity(username)
                                if isinstance(entity, (Channel, Chat)):
                                    group_info = await self._extract_group_info(entity, client)
                                    if group_info:
                                        discovered_groups.append(group_info)
                                        logger.info(f"Found group by username: {group_info.title} (ID: {group_info.id})")
                                        continue
                            except Exception as e:
                                logger.debug(f"Could not find group by username '{username}': {e}")
                        
                    except Exception as e:
                        logger.debug(f"Error searching for group '{group_name}': {e}")
                        continue
                
                # If we found all groups by direct search, we're done
                if len(discovered_groups) == len(self.config.selected_groups):
                    logger.info(f"Found all {len(discovered_groups)} selected groups by direct search")
                    self._discovered_groups = discovered_groups
                    await self._display_group_info(discovered_groups)
                    return discovered_groups
                
                # Otherwise, continue with dialog iteration for remaining groups
                found_names = {group.title for group in discovered_groups}
                remaining_groups = [name for name in self.config.selected_groups if not any(name.lower() in found_name.lower() for found_name in found_names)]
                logger.info(f"Found {len(discovered_groups)} groups by direct search, searching dialogs for remaining: {remaining_groups}")
            
            # Apply rate limiting before dialog iteration (lighter for just listing)
            await self.rate_limiter.acquire()
            
            # Get all dialogs (conversations) with timeout and early termination
            dialog_count = 0
            target_group_count = len(self.config.selected_groups) if self.config.selected_groups else float('inf')
            selected_groups_found = set()  # Track which selected groups we've found
            
            try:
                async for dialog in client.iter_dialogs():
                    entity = dialog.entity
                    dialog_count += 1
                    
                    # Add progress logging every 50 dialogs for large accounts
                    if dialog_count % 50 == 0:
                        logger.info(f"Processed {dialog_count} dialogs, found {len(discovered_groups)} groups so far...")
                    
                    # Early termination if we found all selected groups
                    if self.config.selected_groups and len(selected_groups_found) >= target_group_count:
                        logger.info(f"Found all {target_group_count} selected groups, stopping dialog iteration early")
                        break
                    
                    # Process channels and groups only
                    if isinstance(entity, (Channel, Chat)):
                        try:
                            # Only apply rate limiting every 10 groups to speed up discovery
                            if len(discovered_groups) % 10 == 0:
                                await self.rate_limiter.acquire()
                            
                            group_info = await self._extract_group_info(entity, client)
                            if group_info:
                                # Filter by selected groups if specified
                                if self.config.selected_groups:
                                    # Check if group matches any selected group (by title or username)
                                    group_matches = False
                                    matched_name = None
                                    for selected in self.config.selected_groups:
                                        if (selected.lower() in group_info.title.lower() or 
                                            (group_info.username and selected.lower() in group_info.username.lower())):
                                            group_matches = True
                                            matched_name = selected
                                            break
                                    
                                    if not group_matches:
                                        logger.debug(f"Skipping group (not in selected list): {group_info.title}")
                                        continue
                                    
                                    # Track that we found this selected group
                                    if matched_name:
                                        selected_groups_found.add(matched_name)
                                
                                # Check if we already have this group (avoid duplicates)
                                if not any(existing.id == group_info.id for existing in discovered_groups):
                                    discovered_groups.append(group_info)
                                    logger.info(f"Discovered group: {group_info.title} (ID: {group_info.id})")
                                
                        except (ChannelPrivateError, ChatAdminRequiredError) as e:
                            # Handle access restrictions gracefully
                            logger.warning(f"Access denied to group {getattr(entity, 'title', 'Unknown')}: {e}")
                            continue
                            
                        except Exception as e:
                            # Log other errors but continue processing
                            logger.error(f"Error processing group {getattr(entity, 'title', 'Unknown')}: {e}")
                            default_health_monitor.record_failure("group_processing", e)
                            continue
                            
            except Exception as e:
                logger.error(f"Error during dialog iteration: {e}")
                if discovered_groups:
                    logger.info(f"Partial discovery completed with {len(discovered_groups)} groups before error")
                else:
                    raise
                        
            self._discovered_groups = discovered_groups
            logger.info(f"Group discovery completed. Found {len(discovered_groups)} accessible groups from {dialog_count} total dialogs")
            
            # Display group information
            await self._display_group_info(discovered_groups)
            
            return discovered_groups
        
        try:
            # Add timeout to prevent hanging - increase for large accounts
            # For 610 dialogs with rate limiting, we need more time
            timeout_seconds = 1800.0  # 30 minutes for large accounts
            
            result = await asyncio.wait_for(
                self.error_handler.with_retry(
                    _discover_groups_impl,
                    operation_name="group_discovery"
                ),
                timeout=timeout_seconds
            )
            default_health_monitor.record_success("group_discovery")
            return result
            
        except asyncio.TimeoutError:
            logger.error(f"Group discovery timed out after {timeout_seconds/60:.0f} minutes")
            # Return partial results if we have any
            if self._discovered_groups:
                logger.warning(f"Returning {len(self._discovered_groups)} groups discovered before timeout")
                return self._discovered_groups
            raise ValueError(f"Group discovery timed out after {timeout_seconds/60:.0f} minutes. This may be due to rate limiting or network issues.")
            
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
                if hasattr(entity, 'participants_count') and entity.participants_count is not None:
                    member_count = entity.participants_count
                else:
                    # For regular chats, try to get full chat info
                    full_chat = await client.get_entity(entity)
                    if hasattr(full_chat, 'participants_count') and full_chat.participants_count is not None:
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
            member_count_info = f"{group.member_count:,}" if group.member_count is not None else "Unknown"
            
            logger.info(f"{i:2d}. {group.title}")
            logger.info(f"    Type: {group_type} ({privacy})")
            logger.info(f"    Username: {username_info}")
            logger.info(f"    Members: {member_count_info}")
            logger.info(f"    ID: {group.id}")
            logger.info("")
            
        logger.info(f"Total accessible groups: {len(groups)}")
        logger.info(f"{'='*60}")
        
    async def start_monitoring(self):
        """Begin real-time message monitoring."""
        if not await self.auth_manager.ensure_authenticated():
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
            await self.rate_limiter.acquire()
            
            # Process the message
            processed_message = await self.message_processor.process_message(message, client)
            if not processed_message:
                logger.debug(f"Failed to process message {message.id}")
                return
            
            # Apply relevance filtering if available
            is_relevant = True
            keywords_matched = []
            if self.relevance_filter:
                is_relevant = await self.relevance_filter.is_relevant(processed_message)
                # Get matched keywords if available
                if hasattr(self.relevance_filter, '_last_matched_keywords'):
                    keywords_matched = getattr(self.relevance_filter, '_last_matched_keywords', [])
            
            # Update command interface statistics if available
            if hasattr(self, '_command_interface') and self._command_interface:
                self._command_interface.update_message_stats(
                    processed_message.group_id,
                    processed_message.group_name,
                    is_relevant,
                    keywords_matched
                )
            
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