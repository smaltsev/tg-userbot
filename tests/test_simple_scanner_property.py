"""
Simple property test for group scanner.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from hypothesis import given, strategies as st, settings
from telegram_scanner.scanner import GroupScanner, TelegramGroup
from telegram_scanner.auth import AuthenticationManager
from telegram_scanner.config import ScannerConfig
from telethon.tl.types import Channel, Chat


@pytest.mark.asyncio
@given(group_count=st.integers(min_value=0, max_value=5))
@settings(max_examples=10, deadline=None)
async def test_group_discovery_completeness(group_count):
    """
    Property 3: Group discovery completeness
    **Feature: telegram-group-scanner, Property 3: Group discovery completeness**
    **Validates: Requirements 2.1, 2.2**
    """
    # Create config and auth manager
    config = ScannerConfig(api_id="123456", api_hash="test_hash")
    
    mock_auth_manager = MagicMock(spec=AuthenticationManager)
    mock_auth_manager.is_authenticated.return_value = True
    
    mock_client = AsyncMock()
    mock_auth_manager.get_client = AsyncMock(return_value=mock_client)
    
    # Create mock dialogs
    mock_dialogs = []
    for i in range(group_count):
        entity = MagicMock(spec=Channel)
        entity.id = i + 1
        entity.title = f"Group {i + 1}"
        entity.username = f"group{i + 1}"
        entity.participants_count = 100
        entity.megagroup = False
        entity.access_hash = 12345
        
        dialog = MagicMock()
        dialog.entity = entity
        mock_dialogs.append(dialog)
    
    # Mock iter_dialogs
    async def mock_iter_dialogs():
        for dialog in mock_dialogs:
            yield dialog
    
    mock_client.iter_dialogs = mock_iter_dialogs
    mock_client.get_entity = AsyncMock(side_effect=lambda x: x)
    
    # Test discovery
    scanner = GroupScanner(config, mock_auth_manager)
    discovered_groups = await scanner.discover_groups()
    
    # Verify all groups were discovered
    assert len(discovered_groups) == group_count
    
    # Verify metadata completeness
    for i, group in enumerate(discovered_groups):
        assert group.id == i + 1
        assert group.title == f"Group {i + 1}"
        assert group.username == f"group{i + 1}"
        assert group.member_count == 100
        assert group.is_private is False  # Has username, so public
        assert group.access_hash == 12345
        assert group.is_channel is True
        assert group.is_megagroup is False


@pytest.mark.asyncio
@given(
    accessible_groups=st.integers(min_value=0, max_value=3),
    restricted_groups=st.integers(min_value=1, max_value=3)
)
@settings(max_examples=10, deadline=None)
async def test_access_permission_graceful_handling(accessible_groups, restricted_groups):
    """
    Property 4: Access permission graceful handling
    For any group with restricted access, the scanner should handle the restriction 
    without crashing and continue processing other accessible groups.
    **Feature: telegram-group-scanner, Property 4: Access permission graceful handling**
    **Validates: Requirements 2.3, 2.4**
    """
    from telethon.errors import ChannelPrivateError, ChatAdminRequiredError
    
    # Create config and auth manager
    config = ScannerConfig(api_id="123456", api_hash="test_hash")
    
    mock_auth_manager = MagicMock(spec=AuthenticationManager)
    mock_auth_manager.is_authenticated.return_value = True
    
    mock_client = AsyncMock()
    mock_auth_manager.get_client = AsyncMock(return_value=mock_client)
    
    # Create mock dialogs - mix of accessible and restricted
    mock_dialogs = []
    expected_accessible_count = accessible_groups
    
    # Add accessible groups
    for i in range(accessible_groups):
        entity = MagicMock(spec=Channel)
        entity.id = i + 1
        entity.title = f"Accessible Group {i + 1}"
        entity.username = f"accessible{i + 1}"
        entity.participants_count = 100
        entity.megagroup = False
        entity.access_hash = 12345
        
        dialog = MagicMock()
        dialog.entity = entity
        mock_dialogs.append(dialog)
    
    # Add restricted groups (these should cause exceptions during processing)
    for i in range(restricted_groups):
        entity = MagicMock(spec=Channel)
        entity.id = accessible_groups + i + 1
        entity.title = f"Restricted Group {i + 1}"
        entity.username = None  # Private group
        # Remove participants_count attribute to force get_entity call
        if hasattr(entity, 'participants_count'):
            delattr(entity, 'participants_count')
        entity.megagroup = False
        entity.access_hash = 54321
        
        dialog = MagicMock()
        dialog.entity = entity
        mock_dialogs.append(dialog)
    
    # Mock iter_dialogs
    async def mock_iter_dialogs():
        for dialog in mock_dialogs:
            yield dialog
    
    mock_client.iter_dialogs = mock_iter_dialogs
    
    # Mock get_entity to raise exceptions for restricted groups
    def mock_get_entity(entity):
        if "Restricted" in entity.title:
            # Alternate between different types of access errors
            if entity.id % 2 == 0:
                raise ChannelPrivateError("Channel is private")
            else:
                raise ChatAdminRequiredError("Admin required")
        return entity
    
    mock_client.get_entity = AsyncMock(side_effect=mock_get_entity)
    
    # Test discovery - should handle errors gracefully
    scanner = GroupScanner(config, mock_auth_manager)
    
    # This should not raise an exception despite access errors
    discovered_groups = await scanner.discover_groups()
    
    # Verify that only accessible groups were returned
    assert len(discovered_groups) == expected_accessible_count, \
        f"Expected {expected_accessible_count} accessible groups, got {len(discovered_groups)}"
    
    # Verify that all returned groups are the accessible ones
    for group in discovered_groups:
        assert "Accessible" in group.title, \
            f"Found restricted group in results: {group.title}"
        assert group.username is not None, \
            "Accessible groups should have usernames in this test"
    
    # Verify the scanner continued processing despite errors
    # (if it crashed, we wouldn't reach this point)
    assert True, "Scanner handled access restrictions gracefully"