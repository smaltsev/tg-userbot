"""
Unit tests for error handling and resilience.
"""

import pytest
import asyncio
import time
from unittest.mock import Mock, AsyncMock, patch
from telethon.errors import FloodWaitError, AuthKeyUnregisteredError

from telegram_scanner.error_handling import (
    ErrorHandler,
    MaxRetriesExceededError,
    SessionExpiredError,
    NetworkConnectivityError,
    RateLimiter,
    HealthMonitor,
    handle_message_processing_errors,
    handle_storage_errors
)


class TestErrorHandler:
    """Unit tests for ErrorHandler class."""
    
    @pytest.mark.asyncio
    async def test_successful_operation_no_retry(self):
        """Test that successful operations complete without retries."""
        error_handler = ErrorHandler(max_retries=3)
        
        async def successful_operation():
            return "success"
        
        result = await error_handler.with_retry(
            successful_operation,
            operation_name="test_success"
        )
        
        assert result == "success"
        
        # Check logs
        logs = error_handler.get_operation_logs("test_success")
        assert len(logs) == 1
        assert logs[0]["status"] == "success"
        assert logs[0]["attempts"] == 1
    
    @pytest.mark.asyncio
    async def test_flood_wait_error_retry(self):
        """Test FloodWaitError handling with exponential backoff."""
        error_handler = ErrorHandler(max_retries=2)
        call_count = 0
        
        async def flood_wait_operation():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                # Create FloodWaitError properly
                error = FloodWaitError(None)
                error.seconds = 1
                raise error
            return "success_after_flood_wait"
        
        start_time = time.time()
        result = await error_handler.with_retry(
            flood_wait_operation,
            operation_name="test_flood_wait",
            flood_wait_multiplier=1.5
        )
        end_time = time.time()
        
        assert result == "success_after_flood_wait"
        assert call_count == 2
        assert end_time - start_time >= 1.0  # Should wait at least 1 second (reduced tolerance)
        
        # Check logs
        logs = error_handler.get_operation_logs("test_flood_wait")
        assert len(logs) == 2  # One retry log, one success log
        assert any(log["status"] == "retry" for log in logs)
        assert any(log["status"] == "success" for log in logs)
    
    @pytest.mark.asyncio
    async def test_connection_error_retry(self):
        """Test connection error handling with exponential backoff."""
        error_handler = ErrorHandler(max_retries=2, base_delay=0.1)
        call_count = 0
        
        async def connection_error_operation():
            nonlocal call_count
            call_count += 1
            if call_count <= 2:
                raise ConnectionError("Network error")
            return "success_after_connection_error"
        
        result = await error_handler.with_retry(
            connection_error_operation,
            operation_name="test_connection_error"
        )
        
        assert result == "success_after_connection_error"
        assert call_count == 3
    
    @pytest.mark.asyncio
    async def test_max_retries_exceeded(self):
        """Test that MaxRetriesExceededError is raised after max retries."""
        error_handler = ErrorHandler(max_retries=2, base_delay=0.01)
        call_count = 0
        
        async def always_failing_operation():
            nonlocal call_count
            call_count += 1
            raise ConnectionError("Persistent network error")
        
        with pytest.raises(NetworkConnectivityError):
            await error_handler.with_retry(
                always_failing_operation,
                operation_name="test_max_retries"
            )
        
        assert call_count == 3  # Initial + 2 retries
        
        # Check logs
        logs = error_handler.get_operation_logs("test_max_retries")
        assert len(logs) >= 2  # At least 2 retry logs
        assert logs[-1]["status"] == "failed"
    
    @pytest.mark.asyncio
    async def test_session_expired_error_no_retry(self):
        """Test that session expired errors are not retried."""
        error_handler = ErrorHandler(max_retries=3)
        call_count = 0
        
        async def session_expired_operation():
            nonlocal call_count
            call_count += 1
            raise AuthKeyUnregisteredError("Session expired")
        
        with pytest.raises(SessionExpiredError):
            await error_handler.with_retry(
                session_expired_operation,
                operation_name="test_session_expired"
            )
        
        assert call_count == 1  # Should not retry
    
    def test_exponential_backoff_calculation(self):
        """Test exponential backoff delay calculation."""
        error_handler = ErrorHandler(base_delay=1.0)
        
        # Test exponential backoff
        assert error_handler._calculate_backoff_delay(0, exponential=True) == 1.0
        assert error_handler._calculate_backoff_delay(1, exponential=True) == 2.0
        assert error_handler._calculate_backoff_delay(2, exponential=True) == 4.0
        assert error_handler._calculate_backoff_delay(3, exponential=True) == 8.0
        
        # Test linear backoff
        assert error_handler._calculate_backoff_delay(0, exponential=False) == 1.0
        assert error_handler._calculate_backoff_delay(1, exponential=False) == 1.0
        assert error_handler._calculate_backoff_delay(5, exponential=False) == 1.0


class TestRateLimiter:
    """Unit tests for RateLimiter class."""
    
    @pytest.mark.asyncio
    async def test_rate_limiter_allows_requests_within_limit(self):
        """Test that rate limiter allows requests within the limit."""
        rate_limiter = RateLimiter(requests_per_minute=10)
        
        # Make 5 requests quickly - should all be allowed
        start_time = time.time()
        for i in range(5):
            await rate_limiter.acquire()
        end_time = time.time()
        
        # Should complete quickly without significant delay
        assert end_time - start_time < 1.0
        assert len(rate_limiter.request_times) == 5
    
    @pytest.mark.asyncio
    async def test_rate_limiter_throttles_excess_requests(self):
        """Test that rate limiter throttles requests exceeding the limit."""
        rate_limiter = RateLimiter(requests_per_minute=3)
        
        # Make requests up to the limit
        for i in range(3):
            await rate_limiter.acquire()
        
        # The next request should be delayed
        start_time = time.time()
        await rate_limiter.acquire()
        end_time = time.time()
        
        # Should have been delayed
        assert end_time - start_time > 0.1
    
    @pytest.mark.asyncio
    async def test_rate_limiter_cleanup_old_requests(self):
        """Test that rate limiter cleans up old request timestamps."""
        rate_limiter = RateLimiter(requests_per_minute=5)
        
        # Manually add old timestamps
        old_time = time.time() - 120  # 2 minutes ago
        rate_limiter.request_times = [old_time, old_time, old_time]
        
        # Make a new request
        await rate_limiter.acquire()
        
        # Old timestamps should be cleaned up
        assert len(rate_limiter.request_times) == 1
        assert rate_limiter.request_times[0] > old_time


class TestHealthMonitor:
    """Unit tests for HealthMonitor class."""
    
    def test_initial_health_status(self):
        """Test initial health status is healthy."""
        monitor = HealthMonitor()
        
        assert monitor.is_healthy()
        assert monitor.health_status == "healthy"
        assert monitor.consecutive_failures == 0
        
        status = monitor.get_health_status()
        assert status["status"] == "healthy"
        assert status["consecutive_failures"] == 0
    
    def test_health_degradation_on_failures(self):
        """Test health status degrades with consecutive failures."""
        monitor = HealthMonitor()
        
        # Record 4 failures - should still be healthy
        for i in range(4):
            monitor.record_failure(f"operation_{i}", Exception(f"Error {i}"))
        
        assert monitor.is_healthy()
        assert monitor.health_status == "healthy"
        assert monitor.consecutive_failures == 4
        
        # 5th failure - should become degraded
        monitor.record_failure("operation_5", Exception("Error 5"))
        assert not monitor.is_healthy()
        assert monitor.health_status == "degraded"
        assert monitor.consecutive_failures == 5
        
        # 10th failure - should become unhealthy
        for i in range(5):
            monitor.record_failure(f"operation_{6+i}", Exception(f"Error {6+i}"))
        
        assert not monitor.is_healthy()
        assert monitor.health_status == "unhealthy"
        assert monitor.consecutive_failures == 10
    
    def test_health_recovery_on_success(self):
        """Test health recovery after successful operation."""
        monitor = HealthMonitor()
        
        # Make system unhealthy
        for i in range(10):
            monitor.record_failure(f"operation_{i}", Exception(f"Error {i}"))
        
        assert monitor.health_status == "unhealthy"
        
        # Record success - should recover
        monitor.record_success("recovery_operation")
        
        assert monitor.is_healthy()
        assert monitor.health_status == "healthy"
        assert monitor.consecutive_failures == 0


class TestErrorHandlingDecorators:
    """Unit tests for error handling decorators."""
    
    @pytest.mark.asyncio
    async def test_message_processing_error_decorator_success(self):
        """Test message processing decorator with successful operation."""
        
        @handle_message_processing_errors
        async def successful_message_processing():
            return "processed_message"
        
        result = await successful_message_processing()
        assert result == "processed_message"
    
    @pytest.mark.asyncio
    async def test_message_processing_error_decorator_failure(self):
        """Test message processing decorator with failed operation."""
        
        @handle_message_processing_errors
        async def failing_message_processing():
            raise Exception("Processing failed")
        
        result = await failing_message_processing()
        assert result is None  # Decorator should return None on failure
    
    @pytest.mark.asyncio
    async def test_storage_error_decorator_success(self):
        """Test storage error decorator with successful operation."""
        
        @handle_storage_errors
        async def successful_storage_operation():
            return "stored_data"
        
        result = await successful_storage_operation()
        assert result == "stored_data"
    
    @pytest.mark.asyncio
    async def test_storage_error_decorator_io_error(self):
        """Test storage error decorator with IO error."""
        
        @handle_storage_errors
        async def failing_storage_operation():
            raise IOError("Disk full")
        
        with pytest.raises(IOError):
            await failing_storage_operation()
    
    @pytest.mark.asyncio
    async def test_storage_error_decorator_unexpected_error(self):
        """Test storage error decorator with unexpected error."""
        
        @handle_storage_errors
        async def unexpected_error_operation():
            raise ValueError("Unexpected error")
        
        with pytest.raises(ValueError):
            await unexpected_error_operation()


class TestIntegratedErrorHandling:
    """Integration tests for error handling across components."""
    
    @pytest.mark.asyncio
    async def test_authentication_error_handling(self):
        """Test error handling in authentication manager."""
        from telegram_scanner.auth import AuthenticationManager
        from telegram_scanner.config import ScannerConfig
        
        config = ScannerConfig(
            api_id="invalid_id",
            api_hash="invalid_hash",
            scan_interval=30,
            max_history_days=7,
            selected_groups=[],
            keywords=[],
            regex_patterns=[],
            logic_operator="OR",
            rate_limit_rpm=20
        )
        
        auth_manager = AuthenticationManager(config)
        
        # Test with invalid credentials
        with pytest.raises(ValueError, match="Authentication failed"):
            await auth_manager.authenticate()
    
    @pytest.mark.asyncio
    async def test_storage_error_handling(self):
        """Test error handling in storage manager."""
        from telegram_scanner.storage import StorageManager
        from telegram_scanner.config import ScannerConfig
        from unittest.mock import patch
        
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
        
        storage_manager = StorageManager(config)
        
        # Test storage failure handling
        with patch('builtins.open', side_effect=IOError("Permission denied")):
            result = await storage_manager.store_message({"id": 1, "content": "test"})
            assert result is False  # Should handle error gracefully
    
    @pytest.mark.asyncio
    async def test_network_error_recovery(self):
        """Test network error recovery scenarios."""
        error_handler = ErrorHandler(max_retries=3, base_delay=0.01)
        
        # Simulate intermittent network issues
        call_count = 0
        
        async def intermittent_network_operation():
            nonlocal call_count
            call_count += 1
            
            if call_count <= 2:
                raise ConnectionError("Network temporarily unavailable")
            return "network_operation_success"
        
        result = await error_handler.with_retry(
            intermittent_network_operation,
            operation_name="network_recovery_test"
        )
        
        assert result == "network_operation_success"
        assert call_count == 3
        
        # Verify logs show recovery
        logs = error_handler.get_operation_logs("network_recovery_test")
        retry_logs = [log for log in logs if log["status"] == "retry"]
        success_logs = [log for log in logs if log["status"] == "success"]
        
        assert len(retry_logs) == 2
        assert len(success_logs) == 1
    
    @pytest.mark.asyncio
    async def test_rate_limiting_integration(self):
        """Test rate limiting integration with error handling."""
        from telegram_scanner.error_handling import default_rate_limiter
        
        # Reset rate limiter
        default_rate_limiter.request_times.clear()
        default_rate_limiter.requests_per_minute = 5
        
        # Make requests that should trigger rate limiting
        start_time = time.time()
        
        for i in range(7):  # More than the limit
            await default_rate_limiter.acquire()
        
        end_time = time.time()
        
        # Should have taken some time due to rate limiting
        assert end_time - start_time > 0.1
        
        # Should not exceed the rate limit
        assert len(default_rate_limiter.request_times) <= 5