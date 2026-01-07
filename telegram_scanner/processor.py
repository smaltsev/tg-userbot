"""
Message processing and content extraction.
"""

import logging
from typing import Optional
from .config import ScannerConfig
from .storage import StorageManager

logger = logging.getLogger(__name__)


class MessageProcessor:
    """Extracts and processes message content."""
    
    def __init__(self, config: ScannerConfig, storage_manager: StorageManager):
        """Initialize message processor with dependencies."""
        self.config = config
        self.storage_manager = storage_manager
        
    async def process_message(self, message):
        """Main message processing pipeline."""
        # Implementation will be added in task 5
        logger.info("Message processor initialized")
        
    async def extract_text(self, message):
        """Extract text from messages and media."""
        # Implementation will be added in task 5
        pass
        
    async def extract_metadata(self, message):
        """Get sender, timestamp, group info."""
        # Implementation will be added in task 5
        pass
        
    async def handle_media(self, message):
        """Process images with OCR if needed."""
        # Implementation will be added in task 5
        pass