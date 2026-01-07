"""
Data models for Telegram Group Scanner.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List


@dataclass
class TelegramMessage:
    """Data model for Telegram messages."""
    id: int
    timestamp: datetime
    group_id: int
    group_name: str
    sender_id: int
    sender_username: str
    content: str
    media_type: Optional[str] = None
    extracted_text: Optional[str] = None
    relevance_score: float = 0.0
    matched_criteria: List[str] = None
    
    def __post_init__(self):
        """Initialize default values for mutable fields."""
        if self.matched_criteria is None:
            self.matched_criteria = []


@dataclass
class TelegramGroup:
    """Data model for Telegram groups."""
    id: int
    title: str
    username: Optional[str]
    member_count: int
    is_private: bool
    access_hash: int
    last_scanned: Optional[datetime] = None