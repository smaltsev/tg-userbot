"""
Relevance filtering for message content.
"""

import logging
from typing import List
from .config import ScannerConfig
from .models import TelegramMessage

logger = logging.getLogger(__name__)


class RelevanceFilter:
    """Determines if content matches user-defined criteria."""
    
    def __init__(self, config: ScannerConfig):
        """Initialize relevance filter with configuration."""
        self.config = config
        
    async def is_relevant(self, message: TelegramMessage) -> bool:
        """Main relevance checking method."""
        # Implementation will be added in task 7
        # For now, return True to allow all messages through
        logger.debug(f"Checking relevance for message {message.id}")
        return True
        
    async def match_keywords(self, content: str) -> List[str]:
        """Keyword-based matching."""
        # Implementation will be added in task 7
        return []
        
    async def match_regex(self, content: str) -> List[str]:
        """Regular expression matching."""
        # Implementation will be added in task 7
        return []
        
    async def evaluate_criteria(self, keyword_matches: List[str], regex_matches: List[str]) -> bool:
        """Combine multiple criteria with AND/OR logic."""
        # Implementation will be added in task 7
        return False