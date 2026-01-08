"""
Comprehensive error handling and resilience utilities.
"""

import logging
import asyncio
import time
from typing import Callable, Any, Optional, Dict, Type
from functools import wraps
from telethon.errors import (
    FloodWaitError, 
    AuthKeyUnregisteredError,
    SessionPasswordNeededError,
    PhoneCodeInvalidError,
    ApiIdInvalidError,
    ChannelPrivateError,
    ChatAdminRequiredError,
    RPCError
)

logger = logging.getLogger(__name__)


class MaxRetriesExceededError(Exception):
    """Raised when maximum retry attempts are exceeded."""
    pass


class SessionExpiredError(Exception):
    """Raised when Telegram session has expired."""
    pass


class NetworkConnectivityError(Exception):
    """Raised when network connectivity issues are detected."""
    pass


class ErrorHandler:
    """Centralized error handling and retry logic."""
    
    def __init__(self, max_retries: int = 3, base_delay: float = 1.0):
        """Initialize error handler with configuration."""
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.operation_logs: Dict[str, Any] = {}
        
    async def with_retry(self, 
                        func: Callable,
                        operation_name: str = "operation",
                        max_retries: Optional[int] = None,
                        exponential_backoff: bool = True,
                        flood_wait_multiplier: float = 1.5) -> Any:
        """
        Execute function with exponential backoff retry logic.
        
        Args:
            func: Async function to execute
            operation_name: Name for logging purposes
            max_retries: Override default max retries
            exponential_backoff: Use exponential backoff for delays
            flood_wait_multiplier: Multiplier for FloodWaitError delays
            
        Returns:
            Result of successful function execution
            
        Raises:
            MaxRetriesExceededError: When all retry attempts are exhausted
            SessionExpiredError: When session needs re-authentication
        """
        retries = max_retries or self.max_retries
        last_exception = None
        
        for attempt in range(retries + 1):  # +1 for initial attempt
            try:
                start_time = time.time()
                result = await func()
                
                # Log successful operation
                execution_time = time.time() - start_time
                self._log_operation_success(operation_name, attempt, execution_time)
                
                return result
                
            except FloodWaitError as e:
                last_exception = e
                wait_time = e.seconds * flood_wait_multiplier
                
                logger.warning(f"{operation_name} rate limited. Waiting {wait_time:.1f} seconds (attempt {attempt + 1}/{retries + 1})")
                self._log_operation_retry(operation_name, attempt, "FloodWaitError", wait_time)
                
                if attempt < retries:
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    break
                    
            except (OSError, ConnectionError) as e:
                last_exception = e
                
                if attempt < retries:
                    delay = self._calculate_backoff_delay(attempt, exponential_backoff)
                    logger.warning(f"{operation_name} connection error: {e}. Retrying in {delay:.1f}s (attempt {attempt + 1}/{retries + 1})")
                    self._log_operation_retry(operation_name, attempt, "ConnectionError", delay)
                    
                    await asyncio.sleep(delay)
                    continue
                else:
                    logger.error(f"{operation_name} failed after {retries + 1} attempts due to connection issues")
                    self._log_operation_failure(operation_name, retries + 1, e)
                    raise NetworkConnectivityError(f"Network connectivity failed after {retries + 1} attempts: {e}")
                    
            except (AuthKeyUnregisteredError, SessionPasswordNeededError) as e:
                last_exception = e
                logger.error(f"{operation_name} failed due to session expiry: {e}")
                raise SessionExpiredError(f"Session expired during {operation_name}: {e}")
                
            except (ApiIdInvalidError, PhoneCodeInvalidError) as e:
                last_exception = e
                logger.error(f"{operation_name} failed due to authentication error: {e}")
                # Don't retry authentication errors
                raise e
                
            except (ChannelPrivateError, ChatAdminRequiredError) as e:
                last_exception = e
                logger.warning(f"{operation_name} failed due to access permissions: {e}")
                # Don't retry permission errors
                raise e
                
            except Exception as e:
                last_exception = e
                
                if attempt < retries:
                    delay = self._calculate_backoff_delay(attempt, exponential_backoff)
                    logger.warning(f"{operation_name} unexpected error: {e}. Retrying in {delay:.1f}s (attempt {attempt + 1}/{retries + 1})")
                    self._log_operation_retry(operation_name, attempt, type(e).__name__, delay)
                    
                    await asyncio.sleep(delay)
                    continue
                else:
                    logger.error(f"{operation_name} failed after {retries + 1} attempts: {e}")
                    break
        
        # All retries exhausted
        self._log_operation_failure(operation_name, retries + 1, last_exception)
        raise MaxRetriesExceededError(f"{operation_name} failed after {retries + 1} attempts. Last error: {last_exception}")
    
    def _calculate_backoff_delay(self, attempt: int, exponential: bool = True) -> float:
        """Calculate delay for backoff strategy."""
        if exponential:
            return self.base_delay * (2 ** attempt)
        else:
            return self.base_delay
    
    def _log_operation_success(self, operation: str, attempts: int, execution_time: float):
        """Log successful operation."""
        log_entry = {
            'timestamp': time.time(),
            'operation': operation,
            'status': 'success',
            'attempts': attempts + 1,
            'execution_time': execution_time
        }
        
        if operation not in self.operation_logs:
            self.operation_logs[operation] = []
        self.operation_logs[operation].append(log_entry)
        
        if attempts > 0:
            logger.info(f"{operation} succeeded after {attempts + 1} attempts in {execution_time:.2f}s")
        else:
            logger.debug(f"{operation} completed in {execution_time:.2f}s")
    
    def _log_operation_retry(self, operation: str, attempt: int, error_type: str, delay: float):
        """Log retry attempt."""
        log_entry = {
            'timestamp': time.time(),
            'operation': operation,
            'status': 'retry',
            'attempt': attempt + 1,
            'error_type': error_type,
            'delay': delay
        }
        
        if operation not in self.operation_logs:
            self.operation_logs[operation] = []
        self.operation_logs[operation].append(log_entry)
    
    def _log_operation_failure(self, operation: str, total_attempts: int, last_error: Exception):
        """Log operation failure."""
        log_entry = {
            'timestamp': time.time(),
            'operation': operation,
            'status': 'failed',
            'total_attempts': total_attempts,
            'last_error': str(last_error),
            'error_type': type(last_error).__name__
        }
        
        if operation not in self.operation_logs:
            self.operation_logs[operation] = []
        self.operation_logs[operation].append(log_entry)
    
    def get_operation_logs(self, operation: Optional[str] = None) -> Dict[str, Any]:
        """Get operation logs for debugging and monitoring."""
        if operation:
            return self.operation_logs.get(operation, [])
        return self.operation_logs.copy()
    
    def clear_logs(self, operation: Optional[str] = None):
        """Clear operation logs."""
        if operation:
            self.operation_logs.pop(operation, None)
        else:
            self.operation_logs.clear()


class RateLimiter:
    """Rate limiting to prevent API abuse."""
    
    def __init__(self, requests_per_minute: int = 20):
        """Initialize rate limiter."""
        self.requests_per_minute = requests_per_minute
        self.request_times = []
        self._lock = asyncio.Lock()
    
    async def acquire(self):
        """Acquire permission to make a request."""
        async with self._lock:
            now = time.time()
            
            # Remove requests older than 1 minute
            cutoff = now - 60
            self.request_times = [t for t in self.request_times if t > cutoff]
            
            # Check if we're at the limit
            if len(self.request_times) >= self.requests_per_minute:
                # Calculate how long to wait
                oldest_request = min(self.request_times)
                wait_time = 60 - (now - oldest_request)
                
                if wait_time > 0:
                    logger.info(f"Rate limit reached. Waiting {wait_time:.1f} seconds")
                    await asyncio.sleep(wait_time)
                    
                    # Clean up again after waiting
                    now = time.time()
                    cutoff = now - 60
                    self.request_times = [t for t in self.request_times if t > cutoff]
            
            # Record this request
            self.request_times.append(now)


def handle_message_processing_errors(func):
    """Decorator for handling message processing errors gracefully."""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            # Log error but don't stop processing
            logger.error(f"Error in {func.__name__}: {e}")
            logger.debug(f"Error details for {func.__name__}", exc_info=True)
            return None  # Return None to indicate processing failure
    return wrapper


def handle_storage_errors(func):
    """Decorator for handling storage operation errors."""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except (IOError, OSError) as e:
            logger.error(f"Storage error in {func.__name__}: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in {func.__name__}: {e}")
            logger.debug(f"Error details for {func.__name__}", exc_info=True)
            raise
    return wrapper


class HealthMonitor:
    """Monitor system health and connectivity."""
    
    def __init__(self):
        """Initialize health monitor."""
        self.last_successful_operation = time.time()
        self.consecutive_failures = 0
        self.health_status = "healthy"
        
    def record_success(self, operation: str):
        """Record successful operation."""
        self.last_successful_operation = time.time()
        self.consecutive_failures = 0
        if self.health_status != "healthy":
            logger.info(f"System health recovered after successful {operation}")
            self.health_status = "healthy"
    
    def record_failure(self, operation: str, error: Exception):
        """Record failed operation."""
        self.consecutive_failures += 1
        
        if self.consecutive_failures >= 10:
            self.health_status = "unhealthy"
            logger.error(f"System unhealthy after {self.consecutive_failures} consecutive failures")
        elif self.consecutive_failures >= 5:
            self.health_status = "degraded"
            logger.warning(f"System health degraded after {self.consecutive_failures} consecutive failures")
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get current health status."""
        return {
            "status": self.health_status,
            "last_successful_operation": self.last_successful_operation,
            "consecutive_failures": self.consecutive_failures,
            "time_since_last_success": time.time() - self.last_successful_operation
        }
    
    def is_healthy(self) -> bool:
        """Check if system is healthy."""
        return self.health_status == "healthy"


# Global instances for easy access
default_error_handler = ErrorHandler()
default_rate_limiter = RateLimiter()
default_health_monitor = HealthMonitor()