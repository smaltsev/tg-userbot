"""
Property-based tests for message processing functionality.
Feature: telegram-group-scanner
"""

import pytest
import asyncio
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from hypothesis import given, strategies as st, settings
from telegram_scanner.processor import MessageProcessor
from telegram_scanner.config import ScannerConfig
from telegram_scanner.storage import StorageManager
from telegram_scanner.models import TelegramMessage


class TestMessageProcessorProperties:
    """Property-based tests for message processor."""

    @given(
        message_id=st.integers(min_value=1, max_value=999999),
        message_text=st.text(min_size=0, max_size=1000),
        sender_id=st.integers(min_value=1, max_value=999999),
        sender_username=st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=('Ll', 'Lu', 'Nd', 'Pc'))),
        group_id=st.integers(min_value=1, max_value=999999),
        group_name=st.text(min_size=1, max_size=100),
        has_media=st.booleans()
    )
    @settings(max_examples=100, deadline=None)
    @pytest.mark.asyncio
    async def test_message_extraction_completeness(self, message_id, message_text, sender_id, sender_username, group_id, group_name, has_media):
        """
        Property 5: Message extraction completeness
        For any message in a monitored group, the processor should extract all available 
        content (text, media descriptions, metadata) without data loss.
        **Feature: telegram-group-scanner, Property 5: Message extraction completeness**
        **Validates: Requirements 3.3, 5.1**
        """
        # Create mock config and storage manager
        config = ScannerConfig(
            api_id="123456",
            api_hash="test_hash"
        )
        storage_manager = MagicMock(spec=StorageManager)
        
        # Create processor
        processor = MessageProcessor(config, storage_manager)
        
        # Create mock message with all the generated data
        mock_message = MagicMock()
        mock_message.id = message_id
        mock_message.message = message_text
        mock_message.date = datetime.now(timezone.utc)
        mock_message.sender_id = sender_id
        
        # Mock sender
        mock_sender = MagicMock()
        mock_sender.username = sender_username
        mock_sender.first_name = sender_username
        mock_message.sender = mock_sender
        
        # Mock peer_id and chat
        mock_peer_id = MagicMock()
        mock_peer_id.channel_id = group_id
        mock_message.peer_id = mock_peer_id
        
        mock_chat = MagicMock()
        mock_chat.title = group_name
        mock_message.chat = mock_chat
        
        # Mock media if needed
        if has_media:
            mock_media = MagicMock()
            mock_message.media = mock_media
        else:
            mock_message.media = None
        
        # Mock client
        mock_client = AsyncMock()
        
        # Mock media handling methods
        with patch.object(processor, '_get_media_type', return_value="photo" if has_media else None):
            with patch.object(processor, 'handle_media', return_value="extracted_media_text" if has_media else None):
                
                # Process the message
                result = await processor.process_message(mock_message, mock_client)
                
                # Verify completeness - all available data should be extracted
                assert result is not None, "Message processing should not return None for valid messages"
                assert isinstance(result, TelegramMessage), "Result should be a TelegramMessage instance"
                
                # Verify all metadata is preserved
                assert result.id == message_id, "Message ID should be preserved"
                assert result.sender_id == sender_id, "Sender ID should be preserved"
                assert result.sender_username == sender_username, "Sender username should be preserved"
                assert result.group_id == group_id, "Group ID should be preserved"
                assert result.group_name == group_name, "Group name should be preserved"
                assert isinstance(result.timestamp, datetime), "Timestamp should be a datetime object"
                
                # Verify text content is preserved (accounting for whitespace stripping)
                expected_content = message_text.strip() if message_text else ""
                if expected_content:
                    assert result.content == expected_content, "Message text should be preserved with whitespace stripped"
                else:
                    assert result.content == "", "Empty or whitespace-only message text should result in empty string"
                
                # Verify media handling
                if has_media:
                    assert result.media_type is not None, "Media type should be set when media is present"
                    assert result.extracted_text is not None, "Extracted text should be set when media is present"
                else:
                    assert result.media_type is None, "Media type should be None when no media is present"
                    assert result.extracted_text is None, "Extracted text should be None when no media is present"
                
                # Verify no data loss - all non-None input data should be reflected in output
                # This ensures completeness of extraction (accounting for whitespace stripping)
                input_data = [attr.strip() if isinstance(attr, str) else attr for attr in [message_text, sender_username, group_name] if attr and (not isinstance(attr, str) or attr.strip())]
                output_data = [attr for attr in [result.content, result.sender_username, result.group_name] if attr]
                assert len(output_data) >= len(input_data), "No significant data should be lost during extraction"