"""
Unit tests for relevance filtering functionality.
"""

import pytest
from datetime import datetime
from telegram_scanner.filter import RelevanceFilter
from telegram_scanner.config import ScannerConfig
from telegram_scanner.models import TelegramMessage


class TestRelevanceFilter:
    """Unit tests for relevance filter."""

    @pytest.fixture
    def basic_config(self):
        """Basic configuration for testing."""
        return ScannerConfig(
            api_id="test_id",
            api_hash="test_hash",
            keywords=["important", "urgent", "meeting"],
            regex_patterns=[r'\d{4}-\d{2}-\d{2}', r'[A-Z]{2,}'],
            logic_operator="OR"
        )

    @pytest.fixture
    def sample_message(self):
        """Sample message for testing."""
        return TelegramMessage(
            id=1,
            timestamp=datetime.now(),
            group_id=1,
            group_name="test_group",
            sender_id=1,
            sender_username="test_user",
            content="This is an important message about the meeting on 2024-01-15"
        )

    @pytest.mark.asyncio
    async def test_keyword_matching_basic(self, basic_config):
        """Test keyword matching with known patterns."""
        relevance_filter = RelevanceFilter(basic_config)
        
        # Test exact keyword match
        matches = await relevance_filter.match_keywords("This is important")
        assert "important" in matches
        
        # Test case insensitive matching
        matches = await relevance_filter.match_keywords("This is IMPORTANT")
        assert "important" in matches
        
        # Test multiple keyword matches
        matches = await relevance_filter.match_keywords("urgent important meeting")
        assert len(matches) == 3
        assert "urgent" in matches
        assert "important" in matches
        assert "meeting" in matches
        
        # Test no matches
        matches = await relevance_filter.match_keywords("nothing relevant here")
        assert len(matches) == 0

    @pytest.mark.asyncio
    async def test_regex_pattern_matching(self, basic_config):
        """Test regex pattern matching."""
        relevance_filter = RelevanceFilter(basic_config)
        
        # Test date pattern matching
        matches = await relevance_filter.match_regex("Meeting on 2024-01-15")
        assert r'\d{4}-\d{2}-\d{2}' in matches
        
        # Test uppercase pattern matching
        matches = await relevance_filter.match_regex("This is URGENT")
        assert r'[A-Z]{2,}' in matches
        
        # Test multiple pattern matches
        matches = await relevance_filter.match_regex("URGENT meeting on 2024-01-15")
        assert len(matches) == 2
        
        # Test no matches
        matches = await relevance_filter.match_regex("a b c")  # Single letters, no consecutive uppercase
        assert len(matches) == 0

    @pytest.mark.asyncio
    async def test_or_logic_combinations(self, basic_config):
        """Test AND/OR logic combinations with OR operator."""
        basic_config.logic_operator = "OR"
        relevance_filter = RelevanceFilter(basic_config)
        
        # Test keyword match only
        keyword_matches = ["important"]
        regex_matches = []
        result = await relevance_filter.evaluate_criteria(keyword_matches, regex_matches)
        assert result is True
        
        # Test regex match only
        keyword_matches = []
        regex_matches = [r'\d{4}-\d{2}-\d{2}']
        result = await relevance_filter.evaluate_criteria(keyword_matches, regex_matches)
        assert result is True
        
        # Test both matches
        keyword_matches = ["important"]
        regex_matches = [r'\d{4}-\d{2}-\d{2}']
        result = await relevance_filter.evaluate_criteria(keyword_matches, regex_matches)
        assert result is True
        
        # Test no matches
        keyword_matches = []
        regex_matches = []
        result = await relevance_filter.evaluate_criteria(keyword_matches, regex_matches)
        assert result is False

    @pytest.mark.asyncio
    async def test_and_logic_combinations(self, basic_config):
        """Test AND/OR logic combinations with AND operator."""
        basic_config.logic_operator = "AND"
        relevance_filter = RelevanceFilter(basic_config)
        
        # Test keyword match only (should fail with AND logic when both types configured)
        keyword_matches = ["important"]
        regex_matches = []
        result = await relevance_filter.evaluate_criteria(keyword_matches, regex_matches)
        assert result is False
        
        # Test regex match only (should fail with AND logic when both types configured)
        keyword_matches = []
        regex_matches = [r'\d{4}-\d{2}-\d{2}']
        result = await relevance_filter.evaluate_criteria(keyword_matches, regex_matches)
        assert result is False
        
        # Test both matches (should succeed with AND logic)
        keyword_matches = ["important"]
        regex_matches = [r'\d{4}-\d{2}-\d{2}']
        result = await relevance_filter.evaluate_criteria(keyword_matches, regex_matches)
        assert result is True
        
        # Test no matches
        keyword_matches = []
        regex_matches = []
        result = await relevance_filter.evaluate_criteria(keyword_matches, regex_matches)
        assert result is False

    @pytest.mark.asyncio
    async def test_and_logic_with_only_keywords(self):
        """Test AND logic when only keywords are configured."""
        config = ScannerConfig(
            api_id="test_id",
            api_hash="test_hash",
            keywords=["important", "urgent"],
            regex_patterns=[],  # No regex patterns
            logic_operator="AND"
        )
        relevance_filter = RelevanceFilter(config)
        
        # Should succeed with keyword match when only keywords configured
        keyword_matches = ["important"]
        regex_matches = []
        result = await relevance_filter.evaluate_criteria(keyword_matches, regex_matches)
        assert result is True

    @pytest.mark.asyncio
    async def test_and_logic_with_only_regex(self):
        """Test AND logic when only regex patterns are configured."""
        config = ScannerConfig(
            api_id="test_id",
            api_hash="test_hash",
            keywords=[],  # No keywords
            regex_patterns=[r'\d{4}-\d{2}-\d{2}'],
            logic_operator="AND"
        )
        relevance_filter = RelevanceFilter(config)
        
        # Should succeed with regex match when only regex configured
        keyword_matches = []
        regex_matches = [r'\d{4}-\d{2}-\d{2}']
        result = await relevance_filter.evaluate_criteria(keyword_matches, regex_matches)
        assert result is True

    @pytest.mark.asyncio
    async def test_is_relevant_integration(self, basic_config, sample_message):
        """Test the main is_relevant method integration."""
        relevance_filter = RelevanceFilter(basic_config)
        
        result = await relevance_filter.is_relevant(sample_message)
        
        # Should be relevant (contains "important", "meeting", and date pattern)
        assert result is True
        
        # Check that message was updated with matches
        assert len(sample_message.matched_criteria) > 0
        assert "important" in sample_message.matched_criteria
        assert "meeting" in sample_message.matched_criteria
        assert r'\d{4}-\d{2}-\d{2}' in sample_message.matched_criteria
        
        # Check relevance score
        assert sample_message.relevance_score > 0
        assert sample_message.relevance_score <= 1.0

    @pytest.mark.asyncio
    async def test_empty_content_message(self, basic_config):
        """Test handling of messages with empty content."""
        relevance_filter = RelevanceFilter(basic_config)
        
        empty_message = TelegramMessage(
            id=1,
            timestamp=datetime.now(),
            group_id=1,
            group_name="test_group",
            sender_id=1,
            sender_username="test_user",
            content=""
        )
        
        result = await relevance_filter.is_relevant(empty_message)
        assert result is False
        assert len(empty_message.matched_criteria) == 0
        assert empty_message.relevance_score == 0.0

    @pytest.mark.asyncio
    async def test_message_with_extracted_text(self, basic_config):
        """Test relevance checking with extracted text from media."""
        relevance_filter = RelevanceFilter(basic_config)
        
        message_with_media = TelegramMessage(
            id=1,
            timestamp=datetime.now(),
            group_id=1,
            group_name="test_group",
            sender_id=1,
            sender_username="test_user",
            content="Check this image",
            extracted_text="This image contains important information"
        )
        
        result = await relevance_filter.is_relevant(message_with_media)
        assert result is True
        assert "important" in message_with_media.matched_criteria

    @pytest.mark.asyncio
    async def test_no_criteria_configured(self):
        """Test behavior when no criteria are configured."""
        config = ScannerConfig(
            api_id="test_id",
            api_hash="test_hash",
            keywords=[],
            regex_patterns=[],
            logic_operator="OR"
        )
        relevance_filter = RelevanceFilter(config)
        
        message = TelegramMessage(
            id=1,
            timestamp=datetime.now(),
            group_id=1,
            group_name="test_group",
            sender_id=1,
            sender_username="test_user",
            content="Any content"
        )
        
        result = await relevance_filter.is_relevant(message)
        # Should be relevant when no criteria configured
        assert result is True

    @pytest.mark.asyncio
    async def test_invalid_regex_pattern_handling(self):
        """Test handling of invalid regex patterns."""
        config = ScannerConfig(
            api_id="test_id",
            api_hash="test_hash",
            keywords=[],
            regex_patterns=["[invalid", "valid_pattern"],  # First pattern is invalid
            logic_operator="OR"
        )
        
        # Should not raise exception during initialization
        relevance_filter = RelevanceFilter(config)
        
        # Should handle invalid patterns gracefully
        matches = await relevance_filter.match_regex("test content")
        assert len(matches) == 0  # No matches since patterns are simple

    @pytest.mark.asyncio
    async def test_config_update(self):
        """Test dynamic configuration updates."""
        # Start with config that has no patterns that would match our test content
        initial_config = ScannerConfig(
            api_id="test_id",
            api_hash="test_hash",
            keywords=["important", "urgent"],  # "special" not included
            regex_patterns=[],  # No regex patterns
            logic_operator="OR"
        )
        relevance_filter = RelevanceFilter(initial_config)
        
        # Test with initial config
        message = TelegramMessage(
            id=1,
            timestamp=datetime.now(),
            group_id=1,
            group_name="test_group",
            sender_id=1,
            sender_username="test_user",
            content="this is special"  # lowercase, not in keywords, no regex
        )
        
        result1 = await relevance_filter.is_relevant(message)
        assert result1 is False  # "special" not in initial keywords and no regex patterns
        
        # Update config with new keyword
        new_config = ScannerConfig(
            api_id="test_id",
            api_hash="test_hash",
            keywords=["special"],  # Changed to match our test word
            regex_patterns=[],
            logic_operator="OR"
        )
        
        await relevance_filter.update_config(new_config)
        
        # Test with updated config
        message2 = TelegramMessage(
            id=2,
            timestamp=datetime.now(),
            group_id=1,
            group_name="test_group",
            sender_id=1,
            sender_username="test_user",
            content="this is special"
        )
        
        result2 = await relevance_filter.is_relevant(message2)
        assert result2 is True  # "special" now in keywords
        assert "special" in message2.matched_criteria