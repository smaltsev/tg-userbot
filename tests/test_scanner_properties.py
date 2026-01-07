"""
Property-based tests for group scanner functionality.
Feature: telegram-group-scanner
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from hypothesis import given, strategies as st, settings, HealthCheck
from telegram_scanner.scanner import GroupScanner, TelegramGroup
from telegram_scanner.auth import AuthenticationManager
from telegram_scanner.config import ScannerConfig
from telethon.tl.types import Channel, Chat


class MockDialog:
    """Mock dialog for testing."""
    def __init__(self, entity):
        self.entity = entity


class TestGroupScannerProperties:
    """Property-based tests for GroupScanner class."""

    @given(
        groups_data=st.lists(
            st.tuples(
                st.integers(min_value=1, max_value=999999999),  # group_id
                st.text(min_size=1, max_size=50),  # title
                st.one_of(st.none(), st.text(min_size=1, max_size=20)),  # username
                st.integers(min_value=0, max_value=100000),  # member_count
                st.booleans(),  # is_channel
                st.booleans()   # is_megagroup
            ),
            min_size=0,
            max_size=10
        )
    )
    @settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @pytest.mark.asyncio
    async def test_group_discovery_completeness(self, groups_data):
        """
        Property 3: Group discovery completeness
        For any authenticated session, group discovery should return all accessible groups 
        with complete metadata (name, member count, access permissions).
        **Feature: telegram-group-scanner, Property 3: Group discovery completeness**
        **Validates: Requirements 2.1, 2.2**
        """
        # Create config and auth manager for this test
        sample_config = ScannerConfig(api_id="123456", api_hash="test_hash")
        
        mock_auth_manager = MagicMock(spec=AuthenticationManager)
        mock_auth_manager.is_authenticated.return_value = True
        
        # Create mock client
        mock_client = AsyncMock()
        mock_auth_manager.get_client = AsyncMock(return_value=mock_client)
        
        # Ensure unique group IDs
        seen_ids = set()
        unique_groups_data = []
        for group_data in groups_data:
            group_id = group_data[0]
            if group_id not in seen_ids:
                seen_ids.add(group_id)
                unique_groups_data.append(group_data)
        
        # Create mock entities based on test data
        mock_dialogs = []
        expected_groups = []
        
        for group_id, title, username, member_count, is_channel, is_megagroup in unique_groups_data:
            if is_channel:
                # Create Channel entity mock
                entity = MagicMock(spec=Channel)
                entity.id = group_id
                entity.title = title
                entity.username = username
                entity.participants_count = member_count
                entity.megagroup = is_megagroup
                entity.access_hash = abs(hash(title)) % (10**10)
            else:
                # Create Chat entity mock
                entity = MagicMock(spec=Chat)
                entity.id = group_id
                entity.title = title
                entity.participants_count = member_count
                entity.access_hash = abs(hash(title)) % (10**10)
            
            mock_dialogs.append(MockDialog(entity))
            
            # Create expected group info
            expected_group = TelegramGroup(
                id=group_id,
                title=title,
                username=username,
                member_count=member_count,
                is_private=not username if is_channel else True,
                access_hash=entity.access_hash,
                is_channel=is_channel and not is_megagroup,
                is_megagroup=is_megagroup if is_channel else False
            )
            expected_groups.append(expected_group)
        
        # Mock the client's iter_dialogs method
        async def mock_iter_dialogs():
            for dialog in mock_dialogs:
                yield dialog
        
        mock_client = await mock_auth_manager.get_client()
        mock_client.iter_dialogs = mock_iter_dialogs
        mock_client.get_entity = AsyncMock(side_effect=lambda x: x)
        
        # Create scanner and discover groups
        scanner = GroupScanner(sample_config, mock_auth_manager)
        discovered_groups = await scanner.discover_groups()
        
        # Verify completeness: all accessible groups should be discovered
        assert len(discovered_groups) == len(expected_groups), \
            f"Expected {len(expected_groups)} groups, got {len(discovered_groups)}"
        
        # If no groups, test passes (empty case is valid)
        if not expected_groups:
            return
        
        # Verify each discovered group has complete metadata
        discovered_ids = {group.id for group in discovered_groups}
        expected_ids = {group.id for group in expected_groups}
        
        assert discovered_ids == expected_ids, \
            f"Discovered group IDs {discovered_ids} don't match expected {expected_ids}"
        
        # Verify metadata completeness for each group
        for discovered_group in discovered_groups:
            # Find corresponding expected group
            expected_group = next(g for g in expected_groups if g.id == discovered_group.id)
            
            # Verify all required metadata is present and correct
            assert discovered_group.title == expected_group.title
            assert discovered_group.username == expected_group.username
            assert discovered_group.member_count == expected_group.member_count
            assert discovered_group.is_private == expected_group.is_private
            assert discovered_group.access_hash == expected_group.access_hash
            assert discovered_group.is_channel == expected_group.is_channel
            assert discovered_group.is_megagroup == expected_group.is_megagroup
            
            # Verify no critical metadata is None
            assert discovered_group.id is not None
            assert discovered_group.title is not None
            assert discovered_group.member_count is not None
            assert discovered_group.is_private is not None
            assert discovered_group.access_hash is not None