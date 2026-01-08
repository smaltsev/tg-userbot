"""
Unit tests for Storage Manager.
"""

import json
import tempfile
import pytest
import asyncio
from pathlib import Path
from datetime import datetime
from telegram_scanner.storage import StorageManager
from telegram_scanner.config import ScannerConfig


class TestStorageManager:
    """Unit tests for storage functionality."""
    
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
        
        # Sample message data for testing
        self.sample_message = {
            "id": 12345,
            "timestamp": "2024-01-07T10:30:00",
            "group_id": 67890,
            "group_name": "Test Group",
            "sender_id": 11111,
            "sender_username": "test_user",
            "content": "This is a test message",
            "media_type": "photo",
            "extracted_text": "Text from image",
            "relevance_score": 0.85,
            "matched_criteria": ["test", "important"]
        }
    
    @pytest.mark.asyncio
    async def test_json_serialization_with_sample_data(self):
        """Test JSON serialization with sample data."""
        with tempfile.TemporaryDirectory() as temp_dir:
            storage = StorageManager(self.config)
            storage.storage_file = Path(temp_dir) / "test_storage.json"
            
            await storage.initialize()
            
            # Store sample message
            success = await storage.store_message(self.sample_message)
            assert success, "Sample message should be stored successfully"
            
            # Verify file exists and contains correct data
            assert storage.storage_file.exists(), "Storage file should exist"
            
            with open(storage.storage_file, 'r', encoding='utf-8') as f:
                stored_data = json.load(f)
            
            assert len(stored_data) == 1, "Should have one stored message"
            stored_msg = stored_data[0]
            
            # Verify all original fields are preserved
            for key, value in self.sample_message.items():
                assert stored_msg[key] == value, f"Field {key} should be preserved"
            
            # Verify stored_at timestamp was added
            assert "stored_at" in stored_msg, "stored_at timestamp should be added"
    
    @pytest.mark.asyncio
    async def test_duplicate_detection_with_known_duplicates(self):
        """Test duplicate detection with known duplicates."""
        with tempfile.TemporaryDirectory() as temp_dir:
            storage = StorageManager(self.config)
            storage.storage_file = Path(temp_dir) / "test_storage.json"
            
            await storage.initialize()
            
            # Store original message
            success1 = await storage.store_message(self.sample_message)
            assert success1, "Original message should be stored"
            
            # Try to store exact duplicate
            success2 = await storage.store_message(self.sample_message)
            assert not success2, "Duplicate message should be rejected"
            
            # Verify only one message is stored
            stats = await storage.get_statistics()
            assert stats['total_messages'] == 1, "Should have only one message stored"
            
            # Test duplicate detection method directly
            is_duplicate = await storage.check_duplicate(self.sample_message)
            assert is_duplicate, "Message should be detected as duplicate"
            
            # Test with different message (different ID)
            different_message = self.sample_message.copy()
            different_message['id'] = 99999
            
            is_different_duplicate = await storage.check_duplicate(different_message)
            assert not is_different_duplicate, "Different message should not be duplicate"
            
            # Store the different message
            success3 = await storage.store_message(different_message)
            assert success3, "Different message should be stored"
            
            # Verify we now have two messages
            final_stats = await storage.get_statistics()
            assert final_stats['total_messages'] == 2, "Should have two messages stored"
    
    @pytest.mark.asyncio
    async def test_export_functionality(self):
        """Test export functionality for multiple formats."""
        with tempfile.TemporaryDirectory() as temp_dir:
            storage = StorageManager(self.config)
            storage.storage_file = Path(temp_dir) / "test_storage.json"
            
            await storage.initialize()
            
            # Store multiple messages
            messages = [
                self.sample_message,
                {
                    "id": 54321,
                    "timestamp": "2024-01-07T11:00:00",
                    "group_id": 67890,
                    "group_name": "Test Group",
                    "sender_id": 22222,
                    "sender_username": "another_user",
                    "content": "Another test message",
                    "media_type": None,
                    "extracted_text": None,
                    "relevance_score": 0.75,
                    "matched_criteria": ["test"]
                }
            ]
            
            for msg in messages:
                await storage.store_message(msg)
            
            # Test JSON export
            json_file = await storage.export_data("json", str(Path(temp_dir) / "export.json"))
            assert Path(json_file).exists(), "JSON export file should exist"
            
            with open(json_file, 'r', encoding='utf-8') as f:
                exported_data = json.load(f)
            assert len(exported_data) == 2, "JSON export should contain both messages"
            
            # Test CSV export
            csv_file = await storage.export_data("csv", str(Path(temp_dir) / "export.csv"))
            assert Path(csv_file).exists(), "CSV export file should exist"
            
            with open(csv_file, 'r', encoding='utf-8') as f:
                csv_content = f.read()
            assert "Test Group" in csv_content, "CSV should contain group name"
            assert "test_user" in csv_content, "CSV should contain username"
            
            # Test TXT export
            txt_file = await storage.export_data("txt", str(Path(temp_dir) / "export.txt"))
            assert Path(txt_file).exists(), "TXT export file should exist"
            
            with open(txt_file, 'r', encoding='utf-8') as f:
                txt_content = f.read()
            assert "Group: Test Group" in txt_content, "TXT should contain formatted group info"
            assert "This is a test message" in txt_content, "TXT should contain message content"
            
            # Test unsupported format
            with pytest.raises(ValueError, match="Unsupported export format"):
                await storage.export_data("xml")
    
    @pytest.mark.asyncio
    async def test_statistics_generation(self):
        """Test statistics generation with various data."""
        with tempfile.TemporaryDirectory() as temp_dir:
            storage = StorageManager(self.config)
            storage.storage_file = Path(temp_dir) / "test_storage.json"
            
            await storage.initialize()
            
            # Test empty statistics
            empty_stats = await storage.get_statistics()
            assert empty_stats['total_messages'] == 0, "Empty storage should have 0 messages"
            assert empty_stats['groups_scanned'] == 0, "Empty storage should have 0 groups"
            
            # Store messages from different groups
            messages = [
                {
                    "id": 1,
                    "timestamp": "2024-01-07T10:00:00",
                    "group_id": 1,
                    "group_name": "Group A",
                    "sender_id": 1,
                    "sender_username": "user1",
                    "content": "Message 1",
                    "media_type": "photo",
                    "extracted_text": None,
                    "relevance_score": 0.8,
                    "matched_criteria": ["test"]
                },
                {
                    "id": 2,
                    "timestamp": "2024-01-07T11:00:00",
                    "group_id": 1,
                    "group_name": "Group A",
                    "sender_id": 2,
                    "sender_username": "user2",
                    "content": "Message 2",
                    "media_type": "video",
                    "extracted_text": None,
                    "relevance_score": 0.9,
                    "matched_criteria": ["important"]
                },
                {
                    "id": 3,
                    "timestamp": "2024-01-07T12:00:00",
                    "group_id": 2,
                    "group_name": "Group B",
                    "sender_id": 3,
                    "sender_username": "user3",
                    "content": "Message 3",
                    "media_type": None,
                    "extracted_text": None,
                    "relevance_score": 0.7,
                    "matched_criteria": ["test"]
                }
            ]
            
            for msg in messages:
                await storage.store_message(msg)
            
            # Get statistics
            stats = await storage.get_statistics()
            
            # Verify basic counts
            assert stats['total_messages'] == 3, "Should have 3 messages"
            assert stats['groups_scanned'] == 2, "Should have 2 groups"
            
            # Verify date range
            assert stats['date_range'] is not None, "Should have date range"
            assert 'earliest' in stats['date_range'], "Should have earliest date"
            assert 'latest' in stats['date_range'], "Should have latest date"
            
            # Verify top groups
            assert len(stats['top_groups']) == 2, "Should have 2 groups in top groups"
            group_a_count = next(g['count'] for g in stats['top_groups'] if g['group'] == 'Group A')
            assert group_a_count == 2, "Group A should have 2 messages"
            
            # Verify media types
            assert stats['media_types']['photo'] == 1, "Should have 1 photo"
            assert stats['media_types']['video'] == 1, "Should have 1 video"
            
            # Verify storage file size
            assert stats['storage_file_size'] > 0, "Storage file should have size"
    
    @pytest.mark.asyncio
    async def test_initialization_with_existing_data(self):
        """Test initialization with existing data file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            storage_file = Path(temp_dir) / "existing_storage.json"
            
            # Create existing data file
            existing_data = [
                {
                    "id": 999,
                    "timestamp": "2024-01-06T10:00:00",
                    "group_id": 888,
                    "group_name": "Existing Group",
                    "sender_id": 777,
                    "sender_username": "existing_user",
                    "content": "Existing message",
                    "media_type": None,
                    "extracted_text": None,
                    "relevance_score": 0.6,
                    "matched_criteria": ["existing"]
                }
            ]
            
            with open(storage_file, 'w', encoding='utf-8') as f:
                json.dump(existing_data, f)
            
            # Initialize storage with existing file
            storage = StorageManager(self.config)
            storage.storage_file = storage_file
            
            await storage.initialize()
            
            # Verify existing data was loaded
            stats = await storage.get_statistics()
            assert stats['total_messages'] == 1, "Should load existing message"
            
            # Verify duplicate detection works with loaded data
            existing_msg = existing_data[0]
            is_duplicate = await storage.check_duplicate(existing_msg)
            assert is_duplicate, "Existing message should be detected as duplicate"
            
            # Add new message
            new_msg = self.sample_message.copy()
            success = await storage.store_message(new_msg)
            assert success, "New message should be stored"
            
            # Verify total count
            final_stats = await storage.get_statistics()
            assert final_stats['total_messages'] == 2, "Should have both existing and new message"