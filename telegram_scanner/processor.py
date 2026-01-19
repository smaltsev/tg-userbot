"""
Message processing and content extraction.
"""

import logging
import asyncio
import io
from datetime import datetime
from typing import Optional, List, Dict, Any
from PIL import Image
import pytesseract
from telethon.tl.types import (
    MessageMediaPhoto, MessageMediaDocument, 
    DocumentAttributeFilename, DocumentAttributeImageSize
)
from .config import ScannerConfig
from .storage import StorageManager
from .models import TelegramMessage
from .error_handling import (
    ErrorHandler,
    handle_message_processing_errors,
    default_error_handler,
    default_rate_limiter,
    default_health_monitor
)

logger = logging.getLogger(__name__)


class MessageProcessor:
    """Extracts and processes message content."""
    
    def __init__(self, config: ScannerConfig, storage_manager: StorageManager, rate_limiter=None):
        """Initialize message processor with dependencies."""
        self.config = config
        self.storage_manager = storage_manager
        self.error_handler = ErrorHandler(max_retries=2)
        self.rate_limiter = rate_limiter or default_rate_limiter
        
    @handle_message_processing_errors
    async def process_message(self, message, client) -> Optional[TelegramMessage]:
        """Main message processing pipeline with error handling."""
        async def _process_impl():
            # Extract metadata first
            metadata = await self.extract_metadata(message)
            if not metadata:
                logger.warning(f"Failed to extract metadata for message {message.id}")
                return None
            
            # Extract text content
            text_content = await self.extract_text(message)
            
            # Handle media if present
            media_type = None
            extracted_text = None
            if message.media:
                media_type = await self._get_media_type(message.media)
                extracted_text = await self.handle_media(message, client)
            
            # Create TelegramMessage object
            telegram_message = TelegramMessage(
                id=message.id,
                timestamp=metadata['timestamp'],
                group_id=metadata['group_id'],
                group_name=metadata['group_name'],
                sender_id=metadata['sender_id'],
                sender_username=metadata['sender_username'],
                content=text_content or "",
                media_type=media_type,
                extracted_text=extracted_text
            )
            
            logger.debug(f"Processed message {message.id} from {metadata['group_name']}")
            return telegram_message
        
        try:
            result = await self.error_handler.with_retry(
                _process_impl,
                operation_name="message_processing"
            )
            default_health_monitor.record_success("message_processing")
            return result
        except Exception as e:
            logger.error(f"Error processing message {message.id}: {e}")
            default_health_monitor.record_failure("message_processing", e)
            return None
        
    async def extract_text(self, message) -> Optional[str]:
        """Extract text from messages and media."""
        try:
            if hasattr(message, 'message') and message.message:
                return message.message.strip()
            return None
        except Exception as e:
            logger.error(f"Error extracting text from message: {e}")
            return None
        
    async def extract_metadata(self, message) -> Optional[Dict[str, Any]]:
        """Get sender, timestamp, group info."""
        try:
            # Extract timestamp
            timestamp = message.date if hasattr(message, 'date') and message.date else datetime.now()
            
            # Extract sender information
            sender_id = 0
            if hasattr(message, 'sender_id') and message.sender_id is not None:
                sender_id = message.sender_id
            
            sender_username = ""
            if hasattr(message, 'sender') and message.sender:
                if hasattr(message.sender, 'username') and message.sender.username:
                    sender_username = message.sender.username
                elif hasattr(message.sender, 'first_name'):
                    sender_username = message.sender.first_name or ""
            
            # Extract group information
            group_id = 0
            if hasattr(message, 'peer_id') and message.peer_id and hasattr(message.peer_id, 'channel_id'):
                group_id = message.peer_id.channel_id
            
            group_name = ""
            if hasattr(message, 'chat') and message.chat and hasattr(message.chat, 'title'):
                group_name = message.chat.title or ""
            
            return {
                'timestamp': timestamp,
                'sender_id': sender_id,
                'sender_username': sender_username,
                'group_id': group_id,
                'group_name': group_name
            }
            
        except Exception as e:
            logger.error(f"Error extracting metadata: {e}")
            return None
        
    @handle_message_processing_errors
    async def handle_media(self, message, client) -> Optional[str]:
        """Process images with OCR if needed with error handling."""
        async def _handle_media_impl():
            if not message.media:
                return None
                
            # Apply rate limiting for media downloads
            await self.rate_limiter.acquire()
                
            # Handle photo messages
            if isinstance(message.media, MessageMediaPhoto):
                return await self._extract_text_from_photo(message, client)
            
            # Handle document messages (images as documents)
            elif isinstance(message.media, MessageMediaDocument):
                document = message.media.document
                if document.mime_type and document.mime_type.startswith('image/'):
                    return await self._extract_text_from_document(message, client)
                else:
                    # For non-image documents, return filename or description
                    filename = self._get_document_filename(document)
                    return f"Document: {filename}" if filename else "Document"
            
            return None
        
        try:
            return await self.error_handler.with_retry(
                _handle_media_impl,
                operation_name="media_processing",
                max_retries=2
            )
        except Exception as e:
            logger.error(f"Error handling media: {e}")
            default_health_monitor.record_failure("media_processing", e)
            return None
    
    async def _extract_text_from_photo(self, message, client) -> Optional[str]:
        """Extract text from photo using OCR."""
        try:
            # Download the photo
            photo_bytes = await client.download_media(message, file=bytes)
            if not photo_bytes:
                return None
                
            # Convert to PIL Image
            image = Image.open(io.BytesIO(photo_bytes))
            
            # Extract text using OCR
            extracted_text = pytesseract.image_to_string(image).strip()
            
            return extracted_text if extracted_text else None
            
        except Exception as e:
            logger.error(f"Error extracting text from photo: {e}")
            return None
    
    async def _extract_text_from_document(self, message, client) -> Optional[str]:
        """Extract text from image document using OCR."""
        try:
            # Download the document
            document_bytes = await client.download_media(message, file=bytes)
            if not document_bytes:
                return None
                
            # Convert to PIL Image
            image = Image.open(io.BytesIO(document_bytes))
            
            # Extract text using OCR
            extracted_text = pytesseract.image_to_string(image).strip()
            
            return extracted_text if extracted_text else None
            
        except Exception as e:
            logger.error(f"Error extracting text from document: {e}")
            return None
    
    async def _get_media_type(self, media) -> str:
        """Determine the type of media."""
        if isinstance(media, MessageMediaPhoto):
            return "photo"
        elif isinstance(media, MessageMediaDocument):
            document = media.document
            if document.mime_type:
                if document.mime_type.startswith('image/'):
                    return "image"
                elif document.mime_type.startswith('video/'):
                    return "video"
                elif document.mime_type.startswith('audio/'):
                    return "audio"
                else:
                    return "document"
            return "document"
        else:
            return "unknown"
    
    def _get_document_filename(self, document) -> Optional[str]:
        """Extract filename from document attributes."""
        try:
            for attribute in document.attributes:
                if isinstance(attribute, DocumentAttributeFilename):
                    return attribute.file_name
            return None
        except Exception:
            return None
    
    async def process_message_history(self, client, entity, limit: int = 100) -> List[TelegramMessage]:
        """Handle message history pagination with error handling."""
        async def _process_history_impl():
            messages = []
            processed_count = 0
            
            async for message in client.iter_messages(entity, limit=limit):
                if processed_count >= limit:
                    break
                    
                # Apply rate limiting
                await self.rate_limiter.acquire()
                
                processed_message = await self.process_message(message, client)
                if processed_message:
                    messages.append(processed_message)
                
                processed_count += 1
                
                # Add small delay to avoid rate limiting
                if processed_count % 10 == 0:
                    await asyncio.sleep(0.1)
            
            logger.info(f"Processed {len(messages)} messages from history")
            return messages
        
        try:
            result = await self.error_handler.with_retry(
                _process_history_impl,
                operation_name="message_history_processing"
            )
            default_health_monitor.record_success("message_history_processing")
            return result
        except Exception as e:
            logger.error(f"Error processing message history: {e}")
            default_health_monitor.record_failure("message_history_processing", e)
            return []