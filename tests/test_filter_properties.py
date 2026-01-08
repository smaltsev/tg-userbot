"""
Property-based tests for relevance filtering functionality.
Feature: telegram-group-scanner
"""

import pytest
import asyncio
from datetime import datetime
from hypothesis import given, strategies as st, settings
from telegram_scanner.filter import RelevanceFilter
from telegram_scanner.config import ScannerConfig
from telegram_scanner.models import TelegramMessage


class TestRelevanceFilterProperties:
    """Property-based tests for relevance filter."""

    @given(
        content=st.text(min_size=1, max_size=1000),
        keywords=st.lists(st.text(min_size=1, max_size=50), min_size=1, max_size=10),
        regex_patterns=st.lists(
            st.sampled_from([
                r'\d+',  # Numbers
                r'[A-Z]+',  # Uppercase letters
                r'test',  # Simple word
                r'urgent|important',  # OR pattern
                r'\b\w+@\w+\.\w+\b',  # Email-like pattern
            ]),
            min_size=0, max_size=5
        ),
        logic_operator=st.sampled_from(['AND', 'OR'])
    )
    @settings(max_examples=100, deadline=None)
    @pytest.mark.asyncio
    async def test_relevance_filtering_accuracy(self, content, keywords, regex_patterns, logic_operator):
        """
        Property 7: Relevance filtering accuracy
        For any message and any set of configured criteria, the relevance filter should 
        correctly classify the message as relevant or not based on the logical operations 
        (AND/OR) applied to the criteria.
        **Feature: telegram-group-scanner, Property 7: Relevance filtering accuracy**
        **Validates: Requirements 4.3, 4.4**
        """
        # Create config with generated criteria
        config = ScannerConfig(
            api_id="test_id",
            api_hash="test_hash",
            keywords=keywords,
            regex_patterns=regex_patterns,
            logic_operator=logic_operator
        )
        
        # Create test message
        message = TelegramMessage(
            id=1,
            timestamp=datetime.now(),
            group_id=1,
            group_name="test_group",
            sender_id=1,
            sender_username="test_user",
            content=content
        )
        
        # Create filter and test relevance
        relevance_filter = RelevanceFilter(config)
        
        # Get individual matches
        keyword_matches = await relevance_filter.match_keywords(content)
        regex_matches = await relevance_filter.match_regex(content)
        
        # Test the main relevance method
        is_relevant = await relevance_filter.is_relevant(message)
        
        # Verify the logic is applied correctly
        if not keywords and not regex_patterns:
            # No criteria configured - should be relevant
            assert is_relevant == True
        elif logic_operator.upper() == "AND":
            # AND logic: need matches from both types (if both are configured)
            has_keyword_match = bool(keyword_matches) if keywords else True
            has_regex_match = bool(regex_matches) if regex_patterns else True
            expected_relevant = has_keyword_match and has_regex_match
            assert is_relevant == expected_relevant
        else:  # OR logic
            # OR logic: any match is sufficient
            expected_relevant = bool(keyword_matches or regex_matches)
            assert is_relevant == expected_relevant
        
        # Verify message was updated with matches
        all_expected_matches = keyword_matches + regex_matches
        assert set(message.matched_criteria) == set(all_expected_matches)
        
        # Verify relevance score calculation
        total_criteria = len(keywords) + len(regex_patterns)
        if total_criteria > 0:
            expected_score = len(all_expected_matches) / total_criteria
            assert abs(message.relevance_score - expected_score) < 0.001
        else:
            assert message.relevance_score == 0.0

    @given(
        initial_keywords=st.lists(st.text(min_size=1, max_size=20), min_size=1, max_size=5),
        initial_patterns=st.lists(st.just(r'\d+'), min_size=0, max_size=3),
        updated_keywords=st.lists(st.text(min_size=1, max_size=20), min_size=1, max_size=5),
        updated_patterns=st.lists(st.just(r'[A-Z]+'), min_size=0, max_size=3),
        test_content=st.text(min_size=1, max_size=100)
    )
    @settings(max_examples=100, deadline=None)
    @pytest.mark.asyncio
    async def test_configuration_hot_reload_consistency(self, initial_keywords, initial_patterns, 
                                                       updated_keywords, updated_patterns, test_content):
        """
        Property 8: Configuration hot-reload consistency
        For any configuration change made while the agent is running, the new settings 
        should be applied to all future operations without affecting ongoing processes.
        **Feature: telegram-group-scanner, Property 8: Configuration hot-reload consistency**
        **Validates: Requirements 4.5, 7.3**
        """
        # Create initial config
        initial_config = ScannerConfig(
            api_id="test_id",
            api_hash="test_hash",
            keywords=initial_keywords,
            regex_patterns=initial_patterns,
            logic_operator="OR"
        )
        
        # Create filter with initial config
        relevance_filter = RelevanceFilter(initial_config)
        
        # Create test message
        message1 = TelegramMessage(
            id=1,
            timestamp=datetime.now(),
            group_id=1,
            group_name="test_group",
            sender_id=1,
            sender_username="test_user",
            content=test_content
        )
        
        # Test with initial config
        result1 = await relevance_filter.is_relevant(message1)
        initial_matches = message1.matched_criteria.copy()
        
        # Update configuration
        updated_config = ScannerConfig(
            api_id="test_id",
            api_hash="test_hash",
            keywords=updated_keywords,
            regex_patterns=updated_patterns,
            logic_operator="OR"
        )
        
        await relevance_filter.update_config(updated_config)
        
        # Test with updated config on new message
        message2 = TelegramMessage(
            id=2,
            timestamp=datetime.now(),
            group_id=1,
            group_name="test_group",
            sender_id=1,
            sender_username="test_user",
            content=test_content
        )
        
        result2 = await relevance_filter.is_relevant(message2)
        updated_matches = message2.matched_criteria.copy()
        
        # Verify that the filter is using the updated configuration
        assert relevance_filter.config.keywords == updated_keywords
        assert relevance_filter.config.regex_patterns == updated_patterns
        
        # If the configurations are different, the results might be different
        # But the filter should consistently apply the current configuration
        if initial_keywords != updated_keywords or initial_patterns != updated_patterns:
            # The matches should reflect the current configuration
            expected_keyword_matches = [kw for kw in updated_keywords if kw.lower() in test_content.lower()]
            expected_regex_matches = []
            for pattern in updated_patterns:
                try:
                    import re
                    if re.search(pattern, test_content, re.IGNORECASE):
                        expected_regex_matches.append(pattern)
                except re.error:
                    pass  # Skip invalid patterns
            
            expected_all_matches = expected_keyword_matches + expected_regex_matches
            assert set(updated_matches) == set(expected_all_matches)
        
        # Verify consistency: same input with same config should give same result
        message3 = TelegramMessage(
            id=3,
            timestamp=datetime.now(),
            group_id=1,
            group_name="test_group",
            sender_id=1,
            sender_username="test_user",
            content=test_content
        )
        
        result3 = await relevance_filter.is_relevant(message3)
        assert result2 == result3
        assert set(message2.matched_criteria) == set(message3.matched_criteria)
        assert abs(message2.relevance_score - message3.relevance_score) < 0.001