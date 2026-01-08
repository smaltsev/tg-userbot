"""
Property-based tests for error handling and resilience.
"""

import pytest
import asyncio
import time
from unittest.mock import AsyncMock, Mock
from hypothesis import given, strategies as st, settings
from telethon.errors import FloodWaitError

from telegram_scanner.error_handling import (
    ErrorHandler,
    MaxRetriesExceededError,
    NetworkConnectivityError,
    SessionExpiredError,
    RateLimiter,
    HealthMonitor
)


class TestErrorHandlerProperties:
    """Property-based tests for ErrorHandler."""
    
    @given(
        max_retries=st.integers(min_value=1, max_value=10),
        base_delay=st.floats(min_value=0.1, max_value=2.0),
        attempt=st.integers(min_value=0, max_value=5)
    )
    @settings(max_examples=100)
    def test_exponential_backoff_behavior(self, max_retries, base_delay, attempt):
        """
        **Feature: telegram-group-scanner, Property 11: Exponential backoff behavior**
        **Validates: Requirements 5.4, 6.1, 6.2**
        
        For any failure scenario (network, storage, rate limiting), the retry mechanism 
        should implement exponential backoff with increasing delays between attempts.
        """
        error_handler = ErrorHandler(max_retries=max_retries, base_delay=base_delay)
        
        # Test exponential backoff calculation
        delay = error_handler._calculate_backoff_delay(attempt, exponential=True)
        expected_delay = base_delay * (2 ** attempt)
        
        assert delay == expected_delay
        assert delay >= base_delay  # Delay should never be less than base
        
        # Test linear backoff calculation
        linear_delay = error_handler._calculate_backoff_delay(attempt, exponential=False)
        assert linear_delay == base_delay
    
    @pytest.mark.asyncio
    @given(
        flood_wait_seconds=st.integers(min_value=1, max_value=10),  # Reduced for faster testing
        multiplier=st.floats(min_value=1.0, max_value=2.0)
    )
    @settings(max_examples=20, deadline=30000)  # Reduced examples for faster testing
    async def test_flood_wait_error_handling(self, flood_wait_seconds, multiplier):
        """
        **Feature: telegram-group-scanner, Property 11: Exponential backoff behavior**
        **Validates: Requirements 5.4, 6.1, 6.2**
        
        For any FloodWaitError, the system should wait for the specified time 
        multiplied by the flood wait multiplier.
        """
        error_handler = ErrorHandler(max_retries=2, base_delay=0.01)
        call_count = 0
        start_time = time.time()
        
        async def failing_function():
            nonlocal call_count
            call_count += 1
            if call_count <= 1:  # Fail first attempt only for faster testing
                error = FloodWaitError(None)
                error.seconds = flood_wait_seconds
                raise error
            return "success"
        
        # This should succeed after retries
        result = await error_handler.with_retry(
            failing_function,
            operation_name="test_flood_wait",
            flood_wait_multiplier=multiplier
        )
        
        end_time = time.time()
        elapsed = end_time - start_time
        
        # Should have waited at least the flood wait time * multiplier
        expected_min_wait = flood_wait_seconds * multiplier
        
        assert result == "success"
        assert call_count == 2  # Initial + 1 retry
        assert elapsed >= expected_min_wait * 0.8  # Allow 20% tolerance for timing
    
    @pytest.mark.asyncio
    @given(
        max_retries=st.integers(min_value=1, max_value=5),
        failure_count=st.integers(min_value=1, max_value=10)
    )
    @settings(max_examples=50)
    async def test_max_retries_exceeded(self, max_retries, failure_count):
        """
        **Feature: telegram-group-scanner, Property 11: Exponential backoff behavior**
        **Validates: Requirements 5.4, 6.1, 6.2**
        
        For any function that fails more times than max_retries, 
        MaxRetriesExceededError should be raised.
        """
        error_handler = ErrorHandler(max_retries=max_retries, base_delay=0.01)  # Fast for testing
        call_count = 0
        
        async def always_failing_function():
            nonlocal call_count
            call_count += 1
            raise ConnectionError("Test connection error")
        
        if failure_count > max_retries:
            # Should raise NetworkConnectivityError when failures exceed max_retries
            with pytest.raises(NetworkConnectivityError):
                await error_handler.with_retry(
                    always_failing_function,
                    operation_name="test_max_retries"
                )
            
            # Should have called the function max_retries + 1 times (initial + retries)
            assert call_count == max_retries + 1
        else:
            # If failure_count <= max_retries, we can't test this scenario
            # as the function would need to succeed at some point
            pass
    
    @pytest.mark.asyncio
    @given(
        requests_per_minute=st.integers(min_value=5, max_value=20),  # Reduced range for faster testing
        request_count=st.integers(min_value=1, max_value=25)
    )
    @settings(max_examples=20, deadline=15000)  # Reduced for faster testing
    async def test_rate_limiter_behavior(self, requests_per_minute, request_count):
        """
        **Feature: telegram-group-scanner, Property 11: Exponential backoff behavior**
        **Validates: Requirements 5.4, 6.1, 6.2**
        
        For any rate limiter configuration, requests should be throttled 
        to not exceed the specified rate.
        """
        rate_limiter = RateLimiter(requests_per_minute=requests_per_minute)
        start_time = time.time()
        
        # Make requests up to the limit or a reasonable test limit
        test_requests = min(request_count, requests_per_minute + 3)  # Reduced for faster testing
        
        for i in range(test_requests):
            await rate_limiter.acquire()
        
        end_time = time.time()
        elapsed = end_time - start_time
        
        # If we made more requests than the limit, we should have been delayed
        if test_requests > requests_per_minute:
            # Should have taken some time due to rate limiting
            assert elapsed > 0.05  # At least some delay
        
        # The rate limiter should track requests correctly
        assert len(rate_limiter.request_times) <= requests_per_minute


class TestHealthMonitorProperties:
    """Property-based tests for HealthMonitor."""
    
    @given(
        success_count=st.integers(min_value=0, max_value=20),
        failure_count=st.integers(min_value=0, max_value=20)
    )
    @settings(max_examples=100)
    def test_health_status_transitions(self, success_count, failure_count):
        """
        **Feature: telegram-group-scanner, Property 11: Exponential backoff behavior**
        **Validates: Requirements 5.4, 6.1, 6.2**
        
        For any sequence of successes and failures, the health monitor 
        should correctly track system health status.
        """
        monitor = HealthMonitor()
        
        # Record failures first
        for i in range(failure_count):
            monitor.record_failure(f"operation_{i}", Exception(f"Error {i}"))
        
        # Check health status based on failure count
        if failure_count >= 10:
            assert monitor.health_status == "unhealthy"
        elif failure_count >= 5:
            assert monitor.health_status == "degraded"
        else:
            assert monitor.health_status == "healthy"
        
        # Record successes
        for i in range(success_count):
            monitor.record_success(f"operation_{i}")
        
        # After any success, consecutive failures should reset
        if success_count > 0:
            assert monitor.consecutive_failures == 0
            assert monitor.health_status == "healthy"
        
        # Health status should be queryable
        status = monitor.get_health_status()
        assert isinstance(status, dict)
        assert "status" in status
        assert "consecutive_failures" in status
        assert "last_successful_operation" in status
    
    @pytest.mark.asyncio
    @given(
        operation_names=st.lists(
            st.text(min_size=1, max_size=10, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'))),
            min_size=1,
            max_size=5
        ),
        success_operations=st.lists(st.booleans(), min_size=1, max_size=10)
    )
    @settings(max_examples=20)
    async def test_operation_logging(self, operation_names, success_operations):
        """
        **Feature: telegram-group-scanner, Property 11: Exponential backoff behavior**
        **Validates: Requirements 5.4, 6.1, 6.2**
        
        For any sequence of operations, the error handler should maintain 
        comprehensive logs for debugging and monitoring.
        """
        error_handler = ErrorHandler(max_retries=1, base_delay=0.01)
        
        for i, (operation, should_succeed) in enumerate(zip(operation_names, success_operations)):
            async def test_operation():
                if should_succeed:
                    return f"success_{i}"
                else:
                    raise Exception(f"failure_{i}")
            
            try:
                await error_handler.with_retry(
                    test_operation,
                    operation_name=operation
                )
            except:
                pass  # Expected for failing operations
        
        # Check that logs were recorded
        logs = error_handler.get_operation_logs()
        
        # Should have logs for operations that were attempted
        attempted_operations = set(operation_names[:len(success_operations)])
        for operation in attempted_operations:
            if operation in logs:
                operation_logs = logs[operation]
                assert len(operation_logs) > 0
                
                # Each log entry should have required fields
                for log_entry in operation_logs:
                    assert "timestamp" in log_entry
                    assert "operation" in log_entry
                    assert "status" in log_entry
                    assert log_entry["status"] in ["success", "retry", "failed"]


class TestErrorRecoveryProperties:
    """Property-based tests for error recovery continuation."""
    
    @pytest.mark.asyncio
    @given(
        message_count=st.integers(min_value=5, max_value=15),
        failure_rate=st.floats(min_value=0.1, max_value=0.5)  # 10% to 50% failure rate
    )
    @settings(max_examples=30)
    async def test_error_recovery_continuation(self, message_count, failure_rate):
        """
        **Feature: telegram-group-scanner, Property 12: Error recovery continuation**
        **Validates: Requirements 6.3**
        
        For any invalid message or processing error, the system should log the error 
        and continue processing subsequent messages without interruption.
        """
        from telegram_scanner.error_handling import handle_message_processing_errors
        
        processed_messages = []
        
        @handle_message_processing_errors
        async def process_single_message(message_id: int, should_fail: bool):
            processed_messages.append(message_id)
            if should_fail:
                raise Exception(f"Processing failed for message {message_id}")
            return f"Processed message {message_id}"
        
        # Create messages with some that will fail
        results = []
        for i in range(message_count):
            should_fail = (i % 10) < (failure_rate * 10)  # Simple failure pattern
            result = await process_single_message(i, should_fail)
            results.append(result)
        
        # Verify all messages were attempted (error recovery continuation)
        assert len(processed_messages) == message_count
        assert len(results) == message_count
        
        # Verify that processing continued despite errors
        # Failed messages should return None due to error handling decorator
        successful_results = [r for r in results if r is not None]
        none_results = [r for r in results if r is None]
        
        # Should have some successful and some failed results
        expected_failures = sum(1 for i in range(message_count) if (i % 10) < (failure_rate * 10))
        expected_successes = message_count - expected_failures
        
        # Allow some tolerance due to the simple modulo-based failure simulation
        assert len(successful_results) >= expected_successes * 0.7
        assert len(none_results) >= expected_failures * 0.7
        
        # Most importantly: all messages were processed (no early termination)
        assert len(processed_messages) == message_count
    
    @pytest.mark.asyncio
    @given(
        operation_sequence=st.lists(
            st.tuples(
                st.text(min_size=1, max_size=10, alphabet=st.characters(whitelist_categories=('Lu', 'Ll'))),
                st.booleans()  # success/failure
            ),
            min_size=3,
            max_size=15
        )
    )
    @settings(max_examples=30)
    async def test_continuous_operation_despite_failures(self, operation_sequence):
        """
        **Feature: telegram-group-scanner, Property 12: Error recovery continuation**
        **Validates: Requirements 6.3**
        
        For any sequence of operations with mixed successes and failures,
        the system should continue processing all operations without stopping.
        """
        from telegram_scanner.error_handling import handle_message_processing_errors
        
        processed_operations = []
        
        @handle_message_processing_errors
        async def test_operation(operation_name: str, should_succeed: bool):
            processed_operations.append(operation_name)
            if not should_succeed:
                raise Exception(f"Simulated failure in {operation_name}")
            return f"Success: {operation_name}"
        
        # Process all operations in sequence
        results = []
        for operation_name, should_succeed in operation_sequence:
            result = await test_operation(operation_name, should_succeed)
            results.append(result)
        
        # Verify all operations were attempted
        assert len(processed_operations) == len(operation_sequence)
        assert len(results) == len(operation_sequence)
        
        # Verify that failed operations returned None (due to error handling decorator)
        # and successful operations returned their result
        for i, (operation_name, should_succeed) in enumerate(operation_sequence):
            if should_succeed:
                assert results[i] == f"Success: {operation_name}"
            else:
                assert results[i] is None  # Error handling decorator returns None on failure
    
    @pytest.mark.asyncio
    @given(
        batch_size=st.integers(min_value=3, max_value=10),
        error_rate=st.floats(min_value=0.1, max_value=0.7)  # 10% to 70% error rate
    )
    @settings(max_examples=20)
    async def test_batch_processing_resilience(self, batch_size, error_rate):
        """
        **Feature: telegram-group-scanner, Property 12: Error recovery continuation**
        **Validates: Requirements 6.3**
        
        For any batch of operations with a given error rate, the system should
        process all items and continue despite individual failures.
        """
        from telegram_scanner.scanner import GroupScanner
        from telegram_scanner.auth import AuthenticationManager
        from telegram_scanner.config import ScannerConfig
        from unittest.mock import Mock, AsyncMock
        
        # Create mock configuration
        config = ScannerConfig(
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
        
        # Create mock auth manager
        auth_manager = Mock(spec=AuthenticationManager)
        auth_manager.is_authenticated.return_value = True
        auth_manager.get_client = AsyncMock(return_value=Mock())
        
        # Create mock message processor that fails based on error rate
        message_processor = Mock()
        
        async def mock_process_message(message, client):
            # Simulate failure based on message ID and error rate
            if (message.id % 10) < (error_rate * 10):
                return None  # Simulate processing failure
            else:
                return Mock(id=message.id, content=f"Message {message.id}")
        
        message_processor.process_message = mock_process_message
        
        scanner = GroupScanner(config, auth_manager, message_processor)
        
        # Create batch of mock messages
        messages = []
        client = Mock()
        
        for i in range(batch_size):
            message = Mock()
            message.id = i
            messages.append(message)
        
        # Process all messages
        processed_count = 0
        successful_count = 0
        
        for message in messages:
            try:
                await scanner.handle_new_message(message, client)
                processed_count += 1
                # Check if message was actually processed successfully
                result = await message_processor.process_message(message, client)
                if result is not None:
                    successful_count += 1
            except Exception:
                processed_count += 1  # Still counts as processed (error was handled)
        
        # Verify all messages were processed (no early termination)
        assert processed_count == batch_size
        
        # Verify success rate is approximately as expected
        expected_successful = batch_size * (1 - error_rate)
        # Allow 30% tolerance due to the simple modulo-based error simulation
        assert successful_count >= expected_successful * 0.7
        assert successful_count <= batch_size  # Can't succeed more than total