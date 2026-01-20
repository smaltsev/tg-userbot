"""
Relevance filtering for message content.
"""

import logging
import re
from typing import List, Set
from .config import ScannerConfig
from .models import TelegramMessage

logger = logging.getLogger(__name__)


class RelevanceFilter:
    """Determines if content matches user-defined criteria."""
    
    def __init__(self, config: ScannerConfig):
        """Initialize relevance filter with configuration."""
        self.config = config
        self._compiled_patterns = {}
        self._last_matched_keywords = []
        self._compile_regex_patterns()
        
    def _compile_regex_patterns(self):
        """Compile regex patterns for better performance."""
        self._compiled_patterns = {}
        for pattern in self.config.regex_patterns:
            try:
                self._compiled_patterns[pattern] = re.compile(pattern, re.IGNORECASE)
            except re.error as e:
                logger.warning(f"Invalid regex pattern '{pattern}': {e}")
        
    async def is_relevant(self, message: TelegramMessage) -> bool:
        """Main relevance checking method."""
        logger.debug(f"Checking relevance for message {message.id}")
        
        # Get all content to check (message content + extracted text from media)
        content_to_check = message.content or ""
        if message.extracted_text:
            content_to_check += " " + message.extracted_text
            
        if not content_to_check.strip():
            logger.debug(f"Message {message.id} has no content to check")
            return False
            
        # Get matches from both keyword and regex matching
        keyword_matches = await self.match_keywords(content_to_check)
        regex_matches = await self.match_regex(content_to_check)
        
        # Store matched keywords for later retrieval
        self._last_matched_keywords = keyword_matches + regex_matches
        
        # Evaluate criteria based on logical operator
        is_relevant = await self.evaluate_criteria(keyword_matches, regex_matches)
        
        # Update message with matched criteria and relevance score
        all_matches = keyword_matches + regex_matches
        message.matched_criteria = all_matches
        message.relevance_score = len(all_matches) / max(1, len(self.config.keywords) + len(self.config.regex_patterns))
        
        logger.debug(f"Message {message.id} relevance: {is_relevant}, score: {message.relevance_score}")
        return is_relevant
        
    async def match_keywords(self, content: str) -> List[str]:
        """Keyword-based matching."""
        if not self.config.keywords:
            return []
            
        content_lower = content.lower()
        matches = []
        
        for keyword in self.config.keywords:
            if keyword.lower() in content_lower:
                matches.append(keyword)
                logger.debug(f"Keyword match found: '{keyword}'")
                
        return matches
        
    async def match_regex(self, content: str) -> List[str]:
        """Regular expression matching."""
        if not self.config.regex_patterns:
            return []
            
        matches = []
        
        for pattern, compiled_regex in self._compiled_patterns.items():
            if compiled_regex.search(content):
                matches.append(pattern)
                logger.debug(f"Regex match found: '{pattern}'")
                
        return matches
        
    async def evaluate_criteria(self, keyword_matches: List[str], regex_matches: List[str]) -> bool:
        """Combine multiple criteria with AND/OR logic."""
        all_matches = keyword_matches + regex_matches
        
        # If no criteria are configured, consider everything relevant
        if not self.config.keywords and not self.config.regex_patterns:
            logger.debug("No criteria configured, considering all messages relevant")
            return True
            
        # If no matches found, not relevant
        if not all_matches:
            return False
            
        # Apply logical operator
        if self.config.logic_operator.upper() == "AND":
            # For AND logic, we need matches from both keywords and regex (if both are configured)
            has_keyword_match = bool(keyword_matches) if self.config.keywords else True
            has_regex_match = bool(regex_matches) if self.config.regex_patterns else True
            return has_keyword_match and has_regex_match
        else:  # OR logic (default)
            # For OR logic, any match is sufficient
            return bool(all_matches)
            
    async def update_config(self, config: ScannerConfig):
        """Update filter configuration dynamically."""
        logger.info("Updating relevance filter configuration")
        self.config = config
        self._compile_regex_patterns()
        logger.debug(f"Updated with {len(config.keywords)} keywords and {len(config.regex_patterns)} regex patterns")