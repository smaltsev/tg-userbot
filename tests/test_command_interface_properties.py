"""
Property-based tests for command interface functionality.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from hypothesis import given, strategies as st, settings
from telegram_scanner.command_interface import CommandInterface, ScannerState
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


class TestCommandStateConsistency:
    """Test command state consistency property."""
    
    @given(st.lists(
        st.sampled_from(['start', 'stop', 'pause', 'resume']),
        min_size=1,
        max_size=10
    ))
    @settings(max_examples=100, deadline=5000)
    @pytest.mark.asyncio
    async def test_command_state_consistency_property(self, command_sequence):
        """
        **Feature: telegram-group-scanner, Property 13: Command state consistency**
        **Validates: Requirements 7.2, 7.4**
        
        For any sequence of valid commands (start, stop, pause, resume), 
        the agent's operational state should always reflect the most recent 
        command and be queryable.
        """
        # Create fresh command interface for each test
        mock_scanner = MockScanner()
        command_interface = CommandInterface(mock_scanner)
        
        # Track expected state based on command sequence
        expected_state = ScannerState.STOPPED  # Initial state
        
        for command in command_sequence:
            # Execute command
            if command == 'start':
                result = await command_interface.start_scanning()
                if expected_state == ScannerState.STOPPED:
                    expected_state = ScannerState.RUNNING
                    assert result['success'] is True
                    assert result['state'] == expected_state.value
                else:
                    # Starting from non-stopped state should fail
                    assert result['success'] is False
                    # State should remain unchanged
                    
            elif command == 'stop':
                result = await command_interface.stop_scanning()
                if expected_state != ScannerState.STOPPED:
                    expected_state = ScannerState.STOPPED
                    assert result['success'] is True
                    assert result['state'] == expected_state.value
                else:
                    # Stopping already stopped scanner should fail
                    assert result['success'] is False
                    
            elif command == 'pause':
                result = await command_interface.pause_scanning()
                if expected_state == ScannerState.RUNNING:
                    expected_state = ScannerState.PAUSED
                    assert result['success'] is True
                    assert result['state'] == expected_state.value
                else:
                    # Pausing from non-running state should fail
                    assert result['success'] is False
                    
            elif command == 'resume':
                result = await command_interface.resume_scanning()
                if expected_state == ScannerState.PAUSED:
                    expected_state = ScannerState.RUNNING
                    assert result['success'] is True
                    assert result['state'] == expected_state.value
                else:
                    # Resuming from non-paused state should fail
                    assert result['success'] is False
            
            # Verify state consistency after each command
            current_state = command_interface.get_current_state()
            assert current_state == expected_state, (
                f"State inconsistency after command '{command}': "
                f"expected {expected_state.value}, got {current_state.value}"
            )
            
            # Verify status query returns consistent state
            status = await command_interface.get_status()
            assert status.state == expected_state, (
                f"Status query inconsistency after command '{command}': "
                f"expected {expected_state.value}, got {status.state.value}"
            )
    
    @given(st.lists(
        st.sampled_from(['start', 'stop', 'pause', 'resume']),
        min_size=5,
        max_size=20
    ))
    @settings(max_examples=50, deadline=10000)
    @pytest.mark.asyncio
    async def test_concurrent_command_consistency(self, command_sequence):
        """
        Test that concurrent command execution maintains state consistency.
        
        For any sequence of commands executed concurrently, the final state
        should be deterministic and queryable.
        """
        # Create fresh command interface for each test
        mock_scanner = MockScanner()
        command_interface = CommandInterface(mock_scanner)
        
        # Execute all commands concurrently
        tasks = []
        for command in command_sequence:
            if command == 'start':
                task = asyncio.create_task(command_interface.start_scanning())
            elif command == 'stop':
                task = asyncio.create_task(command_interface.stop_scanning())
            elif command == 'pause':
                task = asyncio.create_task(command_interface.pause_scanning())
            elif command == 'resume':
                task = asyncio.create_task(command_interface.resume_scanning())
            tasks.append(task)
        
        # Wait for all commands to complete
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Verify final state is consistent and queryable
        final_state = command_interface.get_current_state()
        status = await command_interface.get_status()
        
        # State should be one of the valid states
        assert final_state in [ScannerState.STOPPED, ScannerState.RUNNING, 
                              ScannerState.PAUSED, ScannerState.ERROR]
        
        # Status query should match current state
        assert status.state == final_state
        
        # All results should be dictionaries with required keys
        for result in results:
            if not isinstance(result, Exception):
                assert isinstance(result, dict)
                assert 'success' in result
                assert 'state' in result
                assert 'message' in result
    
    @given(st.integers(min_value=1, max_value=100))
    @settings(max_examples=20, deadline=5000)
    @pytest.mark.asyncio
    async def test_state_query_consistency(self, num_queries):
        """
        Test that multiple state queries return consistent results.
        
        For any number of consecutive state queries, all should return
        the same state value when no commands are executed between them.
        """
        # Create fresh command interface for each test
        mock_scanner = MockScanner()
        command_interface = CommandInterface(mock_scanner)
        
        # Set initial state
        await command_interface.start_scanning()
        
        # Perform multiple state queries
        states = []
        statuses = []
        
        for _ in range(num_queries):
            state = command_interface.get_current_state()
            status = await command_interface.get_status()
            states.append(state)
            statuses.append(status.state)
        
        # All queries should return the same state
        assert all(state == states[0] for state in states), (
            f"Inconsistent state queries: {[s.value for s in states]}"
        )
        
        assert all(status == statuses[0] for status in statuses), (
            f"Inconsistent status queries: {[s.value for s in statuses]}"
        )
        
        # State and status should match
        for i in range(num_queries):
            assert states[i] == statuses[i], (
                f"State/status mismatch at query {i}: "
                f"state={states[i].value}, status={statuses[i].value}"
            )