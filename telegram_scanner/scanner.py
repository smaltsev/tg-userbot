"""
Group discovery and message scanning functionality.
"""

import logging
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from telethon.tl.types import Channel, Chat, User
from telethon.errors import ChannelPrivateError, ChatAdminRequiredError, FloodWaitError
from .config import ScannerConfig
from .auth import AuthenticationManager
from .processor import MessageProcessor
from .filter import RelevanceFilter

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
        
    async def discover_groups(self) -> List[TelegramGroup]:
        """
        Retrieve accessible groups/channels.
        
        Returns:
            List of TelegramGroup objects with metadata
            
        Raises:
            ValueError: If not authenticated or client unavailable
        """
        if not self.auth_manager.is_authenticated():
            raise ValueError("Authentication required before discovering groups")
            
        client = await self.auth_manager.get_client()
        if not client:
            raise ValueError("Telegram client not available")
            
        discovered_groups = []
        
        try:
            logger.info("Starting group discovery...")
            
            # Get all dialogs (conversations)
            async for dialog in client.iter_dialogs():
                entity = dialog.entity
                
                # Process channels and groups only
                if isinstance(entity, (Channel, Chat)):
                    try:
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
                        continue
                        
            self._discovered_groups = discovered_groups
            logger.info(f"Group discovery completed. Found {len(discovered_groups)} accessible groups")
            
            # Display group information
            await self._display_group_info(discovered_groups)
            
            return discovered_groups
            
        except FloodWaitError as e:
            logger.error(f"Rate limited during group discovery. Wait {e.seconds} seconds")
            raise ValueError(f"Rate limited. Please wait {e.seconds} seconds before retrying")
            
        except Exception as e:
            logger.error(f"Unexpected error during group discovery: {e}")
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
        Extract group information from Telegram entity.
        
        Args:
            entity: Telegram Channel or Chat entity
            client: Telethon client
            
        Returns:
            TelegramGroup object or None if extraction fails
        """
        try:
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
            
        except Exception as e:
            logger.error(f"Error extracting group info: {e}")
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
        # Implementation will be added in task 6
        pass
        
    async def scan_history(self):
        """Process historical messages."""
        # Implementation will be added in task 5
        pass
        
    async def handle_new_message(self, message):
        """Process incoming messages."""
        # Implementation will be added in task 6
        pass