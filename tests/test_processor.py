"""
Unit tests for message processing functionality.
"""

import pytest
import asyncio
import io
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from PIL import Image
from telegram_scanner.processor import MessageProcessor
from telegram_scanner.config import ScannerConfig
from telegram_scanner.storage import StorageManager
from telegram_scanner.models import TelegramMessage
from telethon.tl.types import MessageMediaPhoto, MessageMediaDocument, DocumentAttributeFilename


class TestMessageProcessor:
    """Unit tests for MessageProcessor class."""

    @pytest.fixture
    def config(self):
        """Create test configuration."""
        return ScannerConfig(
            api_id="123456",
            api_hash="test_hash"
        )

    @pytest.fixture
    def storage_manager(self):
        """Create mock storage manager."""
        return MagicMock(spec=StorageManager)

    @pytest.fixture
    def processor(self, config, storage_manager):
        """Create message processor instance."""
        return MessageProcessor(config, storage_manager)

    @pytest.fixture
    def mock_message(self):
        """Create a mock Telegram message."""
        message = MagicMock()
        message.id = 12345
        message.message = "Test message content"
        message.date = datetime.now(timezone.utc)
        message.sender_id = 67890
        
        # Mock sender
        sender = MagicMock()
        sender.username = "testuser"
        sender.first_name = "Test"
        message.sender = sender
        
        # Mock peer_id and chat
        peer_id = MagicMock()
        peer_id.channel_id = 11111
        message.peer_id = peer_id
        
        chat = MagicMock()
        chat.title = "Test Group"
        message.chat = chat
        
        message.media = None
        return message

    @pytest.mark.asyncio
    async def test_extract_text_with_content(self, processor, mock_message):
        """Test text extraction with sample messages."""
        # Test with normal message
        mock_message.message = "Hello, this is a test message!"
        result = await processor.extract_text(mock_message)
        assert result == "Hello, this is a test message!"
        
        # Test with message containing whitespace
        mock_message.message = "  Whitespace message  "
        result = await processor.extract_text(mock_message)
        assert result == "Whitespace message"
        
        # Test with empty message
        mock_message.message = ""
        result = await processor.extract_text(mock_message)
        assert result is None
        
        # Test with None message
        mock_message.message = None
        result = await processor.extract_text(mock_message)
        assert result is None

    @pytest.mark.asyncio
    async def test_extract_metadata_accuracy(self, processor, mock_message):
        """Test metadata extraction accuracy."""
        result = await processor.extract_metadata(mock_message)
        
        assert result is not None
        assert result['sender_id'] == 67890
        assert result['sender_username'] == "testuser"
        assert result['group_id'] == 11111
        assert result['group_name'] == "Test Group"
        assert isinstance(result['timestamp'], datetime)

    @pytest.mark.asyncio
    async def test_extract_metadata_with_missing_fields(self, processor):
        """Test metadata extraction with missing fields."""
        # Create message with minimal fields
        message = MagicMock()
        message.date = datetime.now(timezone.utc)
        message.sender_id = None
        message.sender = None
        message.peer_id = None
        message.chat = None
        
        result = await processor.extract_metadata(message)
        
        assert result is not None
        assert result['sender_id'] == 0
        assert result['sender_username'] == ""
        assert result['group_id'] == 0
        assert result['group_name'] == ""

    @pytest.mark.asyncio
    async def test_process_message_complete_flow(self, processor, mock_message):
        """Test complete message processing flow."""
        mock_client = AsyncMock()
        
        result = await processor.process_message(mock_message, mock_client)
        
        assert result is not None
        assert isinstance(result, TelegramMessage)
        assert result.id == 12345
        assert result.content == "Test message content"
        assert result.sender_id == 67890
        assert result.sender_username == "testuser"
        assert result.group_id == 11111
        assert result.group_name == "Test Group"
        assert result.media_type is None
        assert result.extracted_text is None

    @pytest.mark.asyncio
    async def test_handle_media_photo(self, processor, mock_message):
        """Test OCR functionality with photo media."""
        mock_client = AsyncMock()
        
        # Create mock photo media
        photo_media = MagicMock(spec=MessageMediaPhoto)
        mock_message.media = photo_media
        
        # Create a simple test image
        test_image = Image.new('RGB', (100, 50), color='white')
        img_bytes = io.BytesIO()
        test_image.save(img_bytes, format='PNG')
        img_bytes.seek(0)
        
        # Mock client download
        mock_client.download_media.return_value = img_bytes.getvalue()
        
        # Mock OCR to return predictable text
        with patch('pytesseract.image_to_string', return_value="Test OCR Text"):
            result = await processor.handle_media(mock_message, mock_client)
            assert result == "Test OCR Text"

    @pytest.mark.asyncio
    async def test_handle_media_document(self, processor, mock_message):
        """Test handling of document media."""
        mock_client = AsyncMock()
        
        # Create mock document media
        document = MagicMock()
        document.mime_type = "image/jpeg"
        document.attributes = [MagicMock(spec=DocumentAttributeFilename, file_name="test.jpg")]
        
        document_media = MagicMock(spec=MessageMediaDocument)
        document_media.document = document
        mock_message.media = document_media
        
        # Create a simple test image
        test_image = Image.new('RGB', (100, 50), color='white')
        img_bytes = io.BytesIO()
        test_image.save(img_bytes, format='JPEG')
        img_bytes.seek(0)
        
        # Mock client download
        mock_client.download_media.return_value = img_bytes.getvalue()
        
        # Mock OCR to return predictable text
        with patch('pytesseract.image_to_string', return_value="Document OCR Text"):
            result = await processor.handle_media(mock_message, mock_client)
            assert result == "Document OCR Text"

    @pytest.mark.asyncio
    async def test_handle_media_non_image_document(self, processor, mock_message):
        """Test handling of non-image documents."""
        mock_client = AsyncMock()
        
        # Create mock non-image document
        document = MagicMock()
        document.mime_type = "application/pdf"
        document.attributes = [MagicMock(spec=DocumentAttributeFilename, file_name="test.pdf")]
        
        document_media = MagicMock(spec=MessageMediaDocument)
        document_media.document = document
        mock_message.media = document_media
        
        result = await processor.handle_media(mock_message, mock_client)
        assert result == "Document: test.pdf"

    @pytest.mark.asyncio
    async def test_get_media_type(self, processor):
        """Test media type detection."""
        # Test photo media
        photo_media = MagicMock(spec=MessageMediaPhoto)
        result = await processor._get_media_type(photo_media)
        assert result == "photo"
        
        # Test image document
        document = MagicMock()
        document.mime_type = "image/png"
        document_media = MagicMock(spec=MessageMediaDocument)
        document_media.document = document
        result = await processor._get_media_type(document_media)
        assert result == "image"
        
        # Test video document
        document.mime_type = "video/mp4"
        result = await processor._get_media_type(document_media)
        assert result == "video"
        
        # Test audio document
        document.mime_type = "audio/mp3"
        result = await processor._get_media_type(document_media)
        assert result == "audio"
        
        # Test other document
        document.mime_type = "application/pdf"
        result = await processor._get_media_type(document_media)
        assert result == "document"

    @pytest.mark.asyncio
    async def test_process_message_history(self, processor):
        """Test message history pagination."""
        mock_client = AsyncMock()
        mock_entity = MagicMock()
        
        # Create mock messages for iteration
        mock_messages = []
        for i in range(5):
            msg = MagicMock()
            msg.id = i + 1
            msg.message = f"Message {i + 1}"
            msg.date = datetime.now(timezone.utc)
            msg.sender_id = 100 + i
            msg.sender = MagicMock()
            msg.sender.username = f"user{i}"
            msg.peer_id = MagicMock()
            msg.peer_id.channel_id = 12345
            msg.chat = MagicMock()
            msg.chat.title = "Test Group"
            msg.media = None
            mock_messages.append(msg)
        
        # Mock iter_messages to return our test messages
        async def mock_iter_messages(entity, limit):
            for msg in mock_messages[:limit]:
                yield msg
        
        mock_client.iter_messages = mock_iter_messages
        
        # Test processing history
        result = await processor.process_message_history(mock_client, mock_entity, limit=3)
        
        assert len(result) == 3
        assert all(isinstance(msg, TelegramMessage) for msg in result)
        assert result[0].content == "Message 1"
        assert result[1].content == "Message 2"
        assert result[2].content == "Message 3"

    @pytest.mark.asyncio
    async def test_error_handling_in_process_message(self, processor):
        """Test error handling during message processing."""
        mock_client = AsyncMock()
        
        # Create a message that will cause an error in extract_metadata
        bad_message = MagicMock()
        bad_message.id = 999
        
        # Mock extract_metadata to raise an exception
        with patch.object(processor, 'extract_metadata', side_effect=Exception("Test error")):
            result = await processor.process_message(bad_message, mock_client)
            assert result is None  # Should return None on error

    @pytest.mark.asyncio
    async def test_ocr_error_handling(self, processor, mock_message):
        """Test OCR error handling."""
        mock_client = AsyncMock()
        
        # Create mock photo media
        photo_media = MagicMock(spec=MessageMediaPhoto)
        mock_message.media = photo_media
        
        # Mock client download to return invalid image data
        mock_client.download_media.return_value = b"invalid image data"
        
        result = await processor.handle_media(mock_message, mock_client)
        assert result is None  # Should return None on OCR error