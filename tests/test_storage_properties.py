"""
Property-based tests for Storage Manager.
Feature: telegram-group-scanner
"""

import json
import tempfile
import asyncio
import hashlib
from pathlib import Path
from datetime import datetime
from hypothesis import given, strategies as st, settings
from telegram_scanner.storage import StorageManager
from telegram_scanner.config import ScannerConfig


# Test data generators
@st.composite
def message_data_strategy(draw):
    """Generate realistic message data for testing."""
    return {
        "id": draw(st.integers(min_value=1, max_value=999999)),
        "timestamp": draw(st.datetimes(min_value=datetime(2020, 1, 1), max_value=datetime(2024, 12, 31))).isoformat(),
        "group_id": draw(st.integers(min_value=1, max_value=99999)),
        "group_name": draw(st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd', 'Pc', 'Pd', 'Zs')))),
        "sender_id": draw(st.integers(min_value=1, max_value=999999)),
        "sender_username": draw(st.text(min_size=1, max_size=32, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd', 'Pc')))),
        "content": draw(st.text(min_size=0, max_size=4000)),
        "media_type": draw(st.one_of(st.none(), st.sampled_from(["photo", "video", "document", "audio"]))),
        "extracted_text": draw(st.one_of(st.none(), st.text(min_size=0, max_size=1000))),
        "relevance_score": draw(st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False)),
        "matched_criteria": draw(st.lists(st.text(min_size=1, max_size=20), min_size=0, max_size=5))
    }


class TestStorageProperties:
    """Property-based tests for storage functionality."""
    
    def setup_method(self):
        """Set up test environment."""
        self.config = ScannerConfig(
            api_id="test_id",
            api_hash="test_hash",
            scan_interval=30,
            max_history_days=7,
            selected_groups=[],
            keywords=[],
            regex_patterns=[],
            logic_operator="OR",
            rate_limit_rpm=20
        )
    
    @given(message_data_strategy())
    @settings(max_examples=100, deadline=5000)
    def test_data_serialization_round_trip(self, message_data):
        """
        Property 9: Data serialization round-trip
        For any extracted message data, serializing to JSON and then deserializing 
        should produce equivalent data structures.
        **Validates: Requirements 5.2**
        """
        async def run_test():
            with tempfile.TemporaryDirectory() as temp_dir:
                # Create storage manager with temporary file
                storage = StorageManager(self.config)
                storage.storage_file = Path(temp_dir) / "test_storage.json"
                
                await storage.initialize()
                
                # Store the message
                success = await storage.store_message(message_data)
                assert success, "Message should be stored successfully"
                
                # Read the stored data directly from file
                with open(storage.storage_file, 'r', encoding='utf-8') as f:
                    stored_data = json.load(f)
                
                # Verify we have exactly one message
                assert len(stored_data) == 1, "Should have exactly one stored message"
                
                stored_message = stored_data[0]
                
                # Verify all original fields are preserved (excluding added fields like stored_at)
                for key, value in message_data.items():
                    assert key in stored_message, f"Key {key} should be preserved"
                    
                    # Handle datetime serialization
                    if isinstance(value, datetime):
                        assert stored_message[key] == value.isoformat()
                    else:
                        assert stored_message[key] == value, f"Value for {key} should be preserved"
                
                # Verify the data can be deserialized back to equivalent structure
                # by loading it again in a new storage manager
                new_storage = StorageManager(self.config)
                new_storage.storage_file = storage.storage_file
                await new_storage.initialize()
                
                # The new storage should have loaded the same data
                assert len(new_storage._data) == 1, "New storage should load the same data"
                
                loaded_message = new_storage._data[0]
                
                # Verify round-trip consistency
                for key, value in message_data.items():
                    assert key in loaded_message, f"Key {key} should survive round-trip"
                    
                    if isinstance(value, datetime):
                        assert loaded_message[key] == value.isoformat()
                    else:
                        assert loaded_message[key] == value, f"Value for {key} should survive round-trip"
        
        # Run the async test
        asyncio.run(run_test())
    
    @given(st.lists(message_data_strategy(), min_size=2, max_size=10))
    @settings(max_examples=100, deadline=5000)
    def test_duplicate_detection_accuracy(self, messages):
        """
        Property 10: Duplicate detection accuracy
        For any set of messages containing duplicates, the storage system should 
        identify and prevent storage of redundant information while preserving unique content.
        **Validates: Requirements 5.3**
        """
        async def run_test():
            with tempfile.TemporaryDirectory() as temp_dir:
                storage = StorageManager(self.config)
                storage.storage_file = Path(temp_dir) / "test_storage.json"
                
                await storage.initialize()
                
                # First, determine how many unique messages we actually have
                # by using the same hash function the storage manager uses
                unique_hashes = set()
                unique_messages = []
                
                for msg in messages:
                    content_hash = f"{msg.get('id', '')}{msg.get('group_id', '')}{msg.get('content', '')}"
                    hash_value = hashlib.md5(content_hash.encode('utf-8')).hexdigest()
                    
                    if hash_value not in unique_hashes:
                        unique_hashes.add(hash_value)
                        unique_messages.append(msg)
                
                expected_unique_count = len(unique_messages)
                
                # Now create some intentional duplicates by copying unique messages
                test_messages = unique_messages.copy()  # Start with unique messages
                
                # Add some intentional duplicates with modified non-key fields
                for i, msg in enumerate(unique_messages[:len(unique_messages)//2]):
                    duplicate = msg.copy()
                    # Modify non-key fields that shouldn't affect duplicate detection
                    duplicate['timestamp'] = datetime.now().isoformat()
                    duplicate['stored_at'] = datetime.now().isoformat()
                    duplicate['relevance_score'] = 0.99  # Different score
                    test_messages.append(duplicate)
                
                # Store all messages (unique + intentional duplicates)
                stored_count = 0
                for msg in test_messages:
                    success = await storage.store_message(msg)
                    if success:
                        stored_count += 1
                
                # Verify that only unique messages were stored
                assert stored_count == expected_unique_count, f"Expected {expected_unique_count} unique messages, but stored {stored_count}"
                
                # Verify duplicate detection works for individual checks
                for msg in unique_messages:
                    is_duplicate = await storage.check_duplicate(msg)
                    # All unique messages should now be considered duplicates since they're stored
                    assert is_duplicate, "Message should be detected as duplicate after storage"
                
                # Test that genuinely different messages are not considered duplicates
                different_msg = {
                    "id": max(msg.get('id', 0) for msg in messages) + 1000,  # Ensure different ID
                    "timestamp": datetime.now().isoformat(),
                    "group_id": max(msg.get('group_id', 0) for msg in messages) + 1000,  # Ensure different group
                    "group_name": "Completely Different Group",
                    "sender_id": 999999,
                    "sender_username": "different_user",
                    "content": "This is completely different content that should not match any existing message",
                    "media_type": None,
                    "extracted_text": None,
                    "relevance_score": 0.5,
                    "matched_criteria": []
                }
                
                is_different_duplicate = await storage.check_duplicate(different_msg)
                assert not is_different_duplicate, "Genuinely different message should not be considered duplicate"
                
                # Store the different message and verify it's accepted
                success = await storage.store_message(different_msg)
                assert success, "Different message should be stored successfully"
                
                # Final count should be expected_unique_count + 1
                final_stats = await storage.get_statistics()
                assert final_stats['total_messages'] == expected_unique_count + 1, "Final count should include the different message"
        
        # Run the async test
        asyncio.run(run_test())