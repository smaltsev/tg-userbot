"""
Authentication management for Telegram API.
"""

import logging
import os
import asyncio
from pathlib import Path
from typing import Optional
from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError, PhoneCodeInvalidError, ApiIdInvalidError
from .config import ScannerConfig
from .error_handling import (
    ErrorHandler, 
    SessionExpiredError, 
    NetworkConnectivityError,
    default_error_handler,
    default_health_monitor
)

logger = logging.getLogger(__name__)


class AuthenticationManager:
    """Handles Telegram API authentication and session management."""
    
    def __init__(self, config: ScannerConfig, session_name: str = "telegram_scanner"):
        """Initialize authentication manager with configuration."""
        self.config = config
        self.session_name = session_name
        self.session_path = Path(f"{session_name}.session")
        self._client: Optional[TelegramClient] = None
        self._authenticated = False
        self.error_handler = ErrorHandler(max_retries=3)
        
    async def authenticate(self) -> bool:
        """Manage initial authentication flow with error handling."""
        async def _authenticate_impl():
            # Validate API credentials first
            if not self.config.api_id or not self.config.api_hash:
                raise ValueError("API ID and API hash are required for authentication")
                
            if self.config.api_id == "your_api_id_here" or self.config.api_hash == "your_api_hash_here":
                raise ValueError("Please update configuration with valid API credentials")
            
            # Create Telethon client
            self._client = TelegramClient(
                self.session_name,
                int(self.config.api_id),
                self.config.api_hash
            )
            
            # Connect to Telegram
            await self._client.connect()
            
            # Check if already authenticated
            if await self._client.is_user_authorized():
                self._authenticated = True
                logger.info("Already authenticated with existing session")
                default_health_monitor.record_success("authentication")
                return True
            
            # Start authentication flow
            phone = await self._prompt_phone_number()
            await self._client.send_code_request(phone)
            
            # Get verification code
            code = await self._prompt_verification_code()
            
            try:
                await self._client.sign_in(phone, code)
                self._authenticated = True
                self._set_session_permissions()
                logger.info("Authentication successful")
                default_health_monitor.record_success("authentication")
                return True
                
            except SessionPasswordNeededError:
                # Two-factor authentication required
                password = await self._prompt_2fa_password()
                await self._client.sign_in(password=password)
                self._authenticated = True
                self._set_session_permissions()
                logger.info("Authentication successful with 2FA")
                default_health_monitor.record_success("authentication")
                return True
        
        try:
            return await self.error_handler.with_retry(
                _authenticate_impl,
                operation_name="authentication",
                max_retries=2  # Limited retries for auth
            )
        except (ApiIdInvalidError, ValueError, PhoneCodeInvalidError) as e:
            logger.error(f"Authentication failed: {e}")
            default_health_monitor.record_failure("authentication", e)
            raise ValueError(f"Authentication error: {e}")
        except SessionExpiredError as e:
            logger.error(f"Session expired during authentication: {e}")
            default_health_monitor.record_failure("authentication", e)
            raise ValueError(f"Session expired: {e}")
        except NetworkConnectivityError as e:
            logger.error(f"Network connectivity issues during authentication: {e}")
            default_health_monitor.record_failure("authentication", e)
            raise ValueError(f"Network error: {e}")
        except Exception as e:
            logger.error(f"Unexpected authentication error: {e}")
            default_health_monitor.record_failure("authentication", e)
            raise ValueError(f"Authentication failed: {e}")
            
    async def load_session(self) -> bool:
        """Load existing session if available with error handling."""
        async def _load_session_impl():
            if not self.session_path.exists():
                logger.info("No existing session file found")
                return False
                
            # Validate API credentials
            if not self.config.api_id or not self.config.api_hash:
                logger.error("Cannot load session without API credentials")
                return False
            
            # If we already have a client, disconnect it first to avoid locks
            if self._client is not None:
                try:
                    await self._client.disconnect()
                except:
                    pass
                self._client = None
                
            # Create client with existing session
            self._client = TelegramClient(
                self.session_name,
                int(self.config.api_id),
                self.config.api_hash
            )
            
            await self._client.connect()
            
            if await self._client.is_user_authorized():
                self._authenticated = True
                self._set_session_permissions()
                logger.info("Session loaded successfully")
                default_health_monitor.record_success("session_load")
                return True
            else:
                logger.warning("Session file exists but user is not authorized")
                return False
        
        try:
            return await self.error_handler.with_retry(
                _load_session_impl,
                operation_name="session_load",
                max_retries=2  # Reduce retries for session load
            )
        except SessionExpiredError:
            logger.warning("Session expired, re-authentication required")
            return False
        except NetworkConnectivityError as e:
            logger.error(f"Network issues loading session: {e}")
            default_health_monitor.record_failure("session_load", e)
            return False
        except Exception as e:
            logger.error(f"Error loading session: {e}")
            default_health_monitor.record_failure("session_load", e)
            return False
            
    def is_authenticated(self) -> bool:
        """Check authentication status."""
        return self._authenticated and self._client is not None
    
    def _set_session_permissions(self):
        """Set restrictive permissions on session file for security."""
        import os
        import stat
        if self.session_path.exists():
            try:
                # Set to owner read/write only (0o600)
                os.chmod(self.session_path, stat.S_IRUSR | stat.S_IWUSR)
                logger.debug(f"Set restrictive permissions on {self.session_path}")
            except Exception as e:
                logger.warning(f"Could not set session file permissions: {e}")
        
    async def ensure_authenticated(self) -> bool:
        """Ensure we have a valid authenticated session."""
        # Check if already authenticated
        if self._authenticated and self._client is not None:
            logger.debug("Already authenticated, skipping session load")
            return True
            
        # Try to load existing session
        if await self.load_session():
            return True
            
        # If no valid session, try full authentication
        return await self.authenticate()
        
    async def get_client(self) -> Optional[TelegramClient]:
        """Get the authenticated Telethon client."""
        if self._authenticated and self._client:
            return self._client
        return None
        
    async def disconnect(self):
        """Disconnect from Telegram and cleanup with error handling."""
        async def _disconnect_impl():
            if self._client:
                await self._client.disconnect()
                self._client = None
            self._authenticated = False
            logger.info("Disconnected from Telegram")
            
        try:
            await self.error_handler.with_retry(
                _disconnect_impl,
                operation_name="disconnect",
                max_retries=1
            )
            default_health_monitor.record_success("disconnect")
        except Exception as e:
            logger.warning(f"Error during disconnect: {e}")
            # Force cleanup even if disconnect fails
            self._client = None
            self._authenticated = False
            default_health_monitor.record_failure("disconnect", e)
    
    async def check_session_validity(self) -> bool:
        """Check if current session is still valid."""
        if not self._authenticated or not self._client:
            return False
            
        async def _check_validity():
            return await self._client.is_user_authorized()
        
        try:
            is_valid = await self.error_handler.with_retry(
                _check_validity,
                operation_name="session_check",
                max_retries=2
            )
            
            if not is_valid:
                logger.warning("Session is no longer valid")
                self._authenticated = False
                default_health_monitor.record_failure("session_check", Exception("Session invalid"))
            else:
                default_health_monitor.record_success("session_check")
                
            return is_valid
            
        except SessionExpiredError:
            logger.warning("Session expired during validity check")
            self._authenticated = False
            return False
        except NetworkConnectivityError as e:
            logger.warning(f"Network issues checking session validity: {e}")
            # Don't mark as invalid due to network issues
            return self._authenticated
        except Exception as e:
            logger.error(f"Error checking session validity: {e}")
            default_health_monitor.record_failure("session_check", e)
            return False
        
    async def _prompt_phone_number(self) -> str:
        """Prompt user for phone number."""
        while True:
            try:
                phone = input("Enter your phone number (with country code, e.g., +1234567890): ").strip()
                if phone and phone.startswith('+') and len(phone) > 5:
                    return phone
                else:
                    print("Please enter a valid phone number with country code (e.g., +1234567890)")
            except (EOFError, KeyboardInterrupt):
                raise ValueError("Authentication cancelled by user")
                
    async def _prompt_verification_code(self) -> str:
        """Prompt user for verification code."""
        while True:
            try:
                code = input("Enter the verification code sent to your phone: ").strip()
                if code and code.isdigit() and len(code) >= 4:
                    return code
                else:
                    print("Please enter a valid verification code (numbers only)")
            except (EOFError, KeyboardInterrupt):
                raise ValueError("Authentication cancelled by user")
                
    async def _prompt_2fa_password(self) -> str:
        """Prompt user for 2FA password."""
        try:
            import getpass
            password = getpass.getpass("Enter your 2FA password: ")
            if not password:
                raise ValueError("2FA password is required")
            return password
        except (EOFError, KeyboardInterrupt):
            raise ValueError("Authentication cancelled by user")