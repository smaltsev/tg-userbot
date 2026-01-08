"""
Unit tests for command interface functionality.
"""

import pytest
import asyncio
import json
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from telegram_scanner.command_interface import (
    CommandInterface, 
    ScannerState, 
    ScannerStatus, 
    ScanningReport
)
from telegram_scanner.main import TelegramScanner


class MockScanner:
    """Mock scanner for testing command interface."""
    
    def __init__(self):
        self.auth_manager = MagicMock()
        self.group_scanner = MagicMock()
        self.message_processor = MagicMock()
        self.relevance_filter = MagicMock()
        self.storage_manager = MagicMock()
        
        # Set up async methods
        self.initialize = AsyncMock()
        self.auth_manager.authenticate = AsyncMock()
        self.auth_manager.is_authenticated = MagicMock(return_value=True)
        self.group_scanner.discover_groups = AsyncMock(return_value=[])
        self.group_scanner.start_monitoring = AsyncMock()
        self.group_scanner.stop_monitoring = AsyncMock()
        self.group_scanner.is_monitoring = MagicMock(return_value=False)
        self.group_scanner._discovered_groups = []


@pytest.fixture
def mock_scanner():
    """Create a mock scanner for testing."""
    return MockScanner()


@pytest.fixture
def command_interface(mock_scanner):
    """Create a command interface with mock scanner."""
    return CommandInterface(mock_scanner)


class TestCommandExecution:
    """Test command execution with known sequences."""
    
    @pytest.mark.asyncio
    async def test_start_command_from_stopped_state(self, command_interface):
        """Test starting scanner from stopped state."""
        # Initial state should be stopped
        assert command_interface.get_current_state() == ScannerState.STOPPED
        
        # Start command should succeed
        result = await command_interface.start_scanning()
        
        assert result['success'] is True
        assert result['state'] == ScannerState.RUNNING.value
        assert 'groups_monitored' in result
        assert command_interface.get_current_state() == ScannerState.RUNNING
    
    @pytest.mark.asyncio
    async def test_start_command_from_running_state(self, command_interface):
        """Test starting scanner when already running."""
        # Start scanner first
        await command_interface.start_scanning()
        assert command_interface.get_current_state() == ScannerState.RUNNING
        
        # Second start command should fail
        result = await command_interface.start_scanning()
        
        assert result['success'] is False
        assert "Cannot start scanner from running state" in result['message']
        assert result['state'] == ScannerState.RUNNING.value
        assert command_interface.get_current_state() == ScannerState.RUNNING
    
    @pytest.mark.asyncio
    async def test_stop_command_from_running_state(self, command_interface):
        """Test stopping scanner from running state."""
        # Start scanner first
        await command_interface.start_scanning()
        assert command_interface.get_current_state() == ScannerState.RUNNING
        
        # Stop command should succeed
        result = await command_interface.stop_scanning()
        
        assert result['success'] is True
        assert result['state'] == ScannerState.STOPPED.value
        assert command_interface.get_current_state() == ScannerState.STOPPED
    
    @pytest.mark.asyncio
    async def test_stop_command_from_stopped_state(self, command_interface):
        """Test stopping scanner when already stopped."""
        # Initial state should be stopped
        assert command_interface.get_current_state() == ScannerState.STOPPED
        
        # Stop command should fail
        result = await command_interface.stop_scanning()
        
        assert result['success'] is False
        assert "Scanner is already stopped" in result['message']
        assert result['state'] == ScannerState.STOPPED.value
        assert command_interface.get_current_state() == ScannerState.STOPPED
    
    @pytest.mark.asyncio
    async def test_pause_command_from_running_state(self, command_interface):
        """Test pausing scanner from running state."""
        # Start scanner first
        await command_interface.start_scanning()
        assert command_interface.get_current_state() == ScannerState.RUNNING
        
        # Pause command should succeed
        result = await command_interface.pause_scanning()
        
        assert result['success'] is True
        assert result['state'] == ScannerState.PAUSED.value
        assert command_interface.get_current_state() == ScannerState.PAUSED
    
    @pytest.mark.asyncio
    async def test_pause_command_from_stopped_state(self, command_interface):
        """Test pausing scanner from stopped state."""
        # Initial state should be stopped
        assert command_interface.get_current_state() == ScannerState.STOPPED
        
        # Pause command should fail
        result = await command_interface.pause_scanning()
        
        assert result['success'] is False
        assert "Cannot pause scanner in stopped state" in result['message']
        assert result['state'] == ScannerState.STOPPED.value
        assert command_interface.get_current_state() == ScannerState.STOPPED
    
    @pytest.mark.asyncio
    async def test_resume_command_from_paused_state(self, command_interface):
        """Test resuming scanner from paused state."""
        # Start and then pause scanner
        await command_interface.start_scanning()
        await command_interface.pause_scanning()
        assert command_interface.get_current_state() == ScannerState.PAUSED
        
        # Resume command should succeed
        result = await command_interface.resume_scanning()
        
        assert result['success'] is True
        assert result['state'] == ScannerState.RUNNING.value
        assert command_interface.get_current_state() == ScannerState.RUNNING
    
    @pytest.mark.asyncio
    async def test_resume_command_from_stopped_state(self, command_interface):
        """Test resuming scanner from stopped state."""
        # Initial state should be stopped
        assert command_interface.get_current_state() == ScannerState.STOPPED
        
        # Resume command should fail
        result = await command_interface.resume_scanning()
        
        assert result['success'] is False
        assert "Cannot resume scanner from stopped state" in result['message']
        assert result['state'] == ScannerState.STOPPED.value
        assert command_interface.get_current_state() == ScannerState.STOPPED
    
    @pytest.mark.asyncio
    async def test_command_sequence_start_pause_resume_stop(self, command_interface):
        """Test a complete command sequence."""
        # Start
        result = await command_interface.start_scanning()
        assert result['success'] is True
        assert command_interface.get_current_state() == ScannerState.RUNNING
        
        # Pause
        result = await command_interface.pause_scanning()
        assert result['success'] is True
        assert command_interface.get_current_state() == ScannerState.PAUSED
        
        # Resume
        result = await command_interface.resume_scanning()
        assert result['success'] is True
        assert command_interface.get_current_state() == ScannerState.RUNNING
        
        # Stop
        result = await command_interface.stop_scanning()
        assert result['success'] is True
        assert command_interface.get_current_state() == ScannerState.STOPPED


class TestStatusReporting:
    """Test status reporting accuracy."""
    
    @pytest.mark.asyncio
    async def test_initial_status(self, command_interface):
        """Test initial status values."""
        status = await command_interface.get_status()
        
        assert isinstance(status, ScannerStatus)
        assert status.state == ScannerState.STOPPED
        assert status.last_scan_time is None
        assert status.messages_processed == 0
        assert status.groups_monitored == 0
        assert status.relevant_messages_found == 0
        assert status.uptime_seconds == 0.0
        assert status.last_error is None
    
    @pytest.mark.asyncio
    async def test_status_after_start(self, command_interface):
        """Test status after starting scanner."""
        await command_interface.start_scanning()
        status = await command_interface.get_status()
        
        assert status.state == ScannerState.RUNNING
        assert status.uptime_seconds > 0.0
        assert status.groups_monitored == 0  # Mock scanner has no groups
    
    @pytest.mark.asyncio
    async def test_status_to_dict(self, command_interface):
        """Test status serialization to dictionary."""
        status = await command_interface.get_status()
        status_dict = status.to_dict()
        
        assert isinstance(status_dict, dict)
        assert 'state' in status_dict
        assert 'last_scan_time' in status_dict
        assert 'messages_processed' in status_dict
        assert 'groups_monitored' in status_dict
        assert 'relevant_messages_found' in status_dict
        assert 'uptime_seconds' in status_dict
        assert 'last_error' in status_dict
    
    @pytest.mark.asyncio
    async def test_message_stats_update(self, command_interface):
        """Test message statistics updating."""
        # Update stats
        command_interface.update_message_stats(
            group_id=123,
            group_name="Test Group",
            is_relevant=True,
            keywords_matched=["test", "keyword"]
        )
        
        status = await command_interface.get_status()
        
        assert status.messages_processed == 1
        assert status.relevant_messages_found == 1
        assert status.last_scan_time is not None
    
    @pytest.mark.asyncio
    async def test_multiple_message_stats_updates(self, command_interface):
        """Test multiple message statistics updates."""
        # Update stats multiple times
        for i in range(5):
            command_interface.update_message_stats(
                group_id=123,
                group_name="Test Group",
                is_relevant=i % 2 == 0,  # Every other message is relevant
                keywords_matched=["test"] if i % 2 == 0 else []
            )
        
        status = await command_interface.get_status()
        
        assert status.messages_processed == 5
        assert status.relevant_messages_found == 3  # 0, 2, 4 are relevant


class TestReportGeneration:
    """Test report generation functionality."""
    
    @pytest.mark.asyncio
    async def test_basic_report_generation(self, command_interface):
        """Test basic report generation."""
        report = await command_interface.generate_report()
        
        assert isinstance(report, ScanningReport)
        assert report.report_generated is not None
        assert report.scan_period_start is not None
        assert report.scan_period_end is not None
        assert report.total_messages_processed == 0
        assert report.relevant_messages_found == 0
        assert isinstance(report.groups_scanned, list)
        assert isinstance(report.top_keywords, list)
        assert isinstance(report.error_summary, dict)
        assert isinstance(report.performance_metrics, dict)
    
    @pytest.mark.asyncio
    async def test_report_with_custom_dates(self, command_interface):
        """Test report generation with custom date range."""
        start_date = "2024-01-01T00:00:00Z"
        end_date = "2024-01-02T00:00:00Z"
        
        report = await command_interface.generate_report(start_date, end_date)
        
        assert report.scan_period_start == start_date
        assert report.scan_period_end == end_date
    
    @pytest.mark.asyncio
    async def test_report_to_dict(self, command_interface):
        """Test report serialization to dictionary."""
        report = await command_interface.generate_report()
        report_dict = report.to_dict()
        
        assert isinstance(report_dict, dict)
        assert 'report_generated' in report_dict
        assert 'scan_period_start' in report_dict
        assert 'scan_period_end' in report_dict
        assert 'total_messages_processed' in report_dict
        assert 'relevant_messages_found' in report_dict
        assert 'groups_scanned' in report_dict
        assert 'top_keywords' in report_dict
        assert 'error_summary' in report_dict
        assert 'performance_metrics' in report_dict
    
    @pytest.mark.asyncio
    async def test_report_with_message_stats(self, command_interface):
        """Test report generation with message statistics."""
        # Add some message statistics
        command_interface.update_message_stats(
            group_id=123,
            group_name="Test Group",
            is_relevant=True,
            keywords_matched=["important", "urgent"]
        )
        command_interface.update_message_stats(
            group_id=456,
            group_name="Another Group",
            is_relevant=False,
            keywords_matched=[]
        )
        
        report = await command_interface.generate_report()
        
        assert report.total_messages_processed == 2
        assert report.relevant_messages_found == 1
        assert len(report.top_keywords) == 2
        assert report.top_keywords[0]['keyword'] in ['important', 'urgent']
        assert report.top_keywords[0]['count'] == 1


class TestErrorHandling:
    """Test error handling in command interface."""
    
    @pytest.mark.asyncio
    async def test_start_command_with_scanner_error(self, mock_scanner):
        """Test start command when scanner initialization fails."""
        # Make scanner initialization fail
        mock_scanner.initialize.side_effect = Exception("Initialization failed")
        
        # Ensure the scanner doesn't have auth_manager initially to trigger initialization
        delattr(mock_scanner, 'auth_manager')
        
        command_interface = CommandInterface(mock_scanner)
        result = await command_interface.start_scanning()
        
        assert result['success'] is False
        assert "Failed to start scanner" in result['message']
        assert result['state'] == ScannerState.ERROR.value
        assert command_interface.get_current_state() == ScannerState.ERROR
    
    @pytest.mark.asyncio
    async def test_stop_command_with_scanner_error(self, mock_scanner):
        """Test stop command when scanner stopping fails."""
        command_interface = CommandInterface(mock_scanner)
        
        # Start scanner first
        await command_interface.start_scanning()
        
        # Make the scanner appear to be monitoring so stop_monitoring gets called
        mock_scanner.group_scanner.is_monitoring.return_value = True
        
        # Make stop monitoring fail
        mock_scanner.group_scanner.stop_monitoring.side_effect = Exception("Stop failed")
        
        result = await command_interface.stop_scanning()
        
        assert result['success'] is False
        assert "Failed to stop scanner" in result['message']
    
    @pytest.mark.asyncio
    async def test_error_recording(self, command_interface):
        """Test error recording functionality."""
        # Record some errors
        command_interface._record_error("test_error", "Test error message")
        command_interface._record_error("test_error", "Another test error")
        command_interface._record_error("different_error", "Different error")
        
        # Generate report to check error summary
        report = await command_interface.generate_report()
        
        assert "test_error" in report.error_summary
        assert report.error_summary["test_error"] == 2
        assert "different_error" in report.error_summary
        assert report.error_summary["different_error"] == 1


class TestConcurrency:
    """Test concurrent command execution."""
    
    @pytest.mark.asyncio
    async def test_concurrent_start_commands(self, command_interface):
        """Test multiple concurrent start commands."""
        # Execute multiple start commands concurrently
        tasks = [
            asyncio.create_task(command_interface.start_scanning())
            for _ in range(3)
        ]
        
        results = await asyncio.gather(*tasks)
        
        # Only one should succeed, others should fail
        success_count = sum(1 for result in results if result['success'])
        assert success_count == 1
        
        # Final state should be running
        assert command_interface.get_current_state() == ScannerState.RUNNING
    
    @pytest.mark.asyncio
    async def test_concurrent_mixed_commands(self, command_interface):
        """Test concurrent execution of different commands."""
        # Start scanner first
        await command_interface.start_scanning()
        
        # Execute mixed commands concurrently
        tasks = [
            asyncio.create_task(command_interface.pause_scanning()),
            asyncio.create_task(command_interface.stop_scanning()),
            asyncio.create_task(command_interface.get_status())
        ]
        
        results = await asyncio.gather(*tasks)
        
        # All should complete without exceptions
        assert len(results) == 3
        
        # Status result should be a ScannerStatus object
        status_result = None
        for result in results:
            if isinstance(result, ScannerStatus):
                status_result = result
                break
        
        assert status_result is not None
        assert isinstance(status_result, ScannerStatus)