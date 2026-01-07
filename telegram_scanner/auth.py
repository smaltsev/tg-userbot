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
        
    async def authenticate(self) -> bool:
        """Manage initial authentication flow."""
        try:
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
                return True
            
            # Start authentication flow
            phone = await self._prompt_phone_number()
            await self._client.send_code_request(phone)
            
            # Get verification code
            code = await self._prompt_verification_code()
            
            try:
                await self._client.sign_in(phone, code)
                self._authenticated = True
                logger.info("Authentication successful")
                return True
                
            except SessionPasswordNeededError:
                # Two-factor authentication required
                password = await self._prompt_2fa_password()
                await self._client.sign_in(password=password)
                self._authenticated = True
                logger.info("Authentication successful with 2FA")
                return True
                
        except (ApiIdInvalidError, ValueError) as e:
            logger.error(f"Authentication failed: {e}")
            raise ValueError(f"Authentication error: {e}")
        except PhoneCodeInvalidError:
            logger.error("Invalid verification code provided")
            raise ValueError("Invalid verification code. Please try again.")
        except Exception as e:
            logger.error(f"Unexpected authentication error: {e}")
            raise ValueError(f"Authentication failed: {e}")
            
    async def load_session(self) -> bool:
        """Load existing session if available."""
        try:
            if not self.session_path.exists():
                logger.info("No existing session file found")
                return False
                
            # Validate API credentials
            if not self.config.api_id or not self.config.api_hash:
                logger.error("Cannot load session without API credentials")
                return False
                
            # Create client with existing session
            self._client = TelegramClient(
                self.session_name,
                int(self.config.api_id),
                self.config.api_hash
            )
            
            await self._client.connect()
            
            if await self._client.is_user_authorized():
                self._authenticated = True
                logger.info("Session loaded successfully")
                return True
            else:
                logger.warning("Session file exists but user is not authorized")
                return False
                
        except Exception as e:
            logger.error(f"Error loading session: {e}")
            return False
            
    def is_authenticated(self) -> bool:
        """Check authentication status."""
        return self._authenticated
        
    async def get_client(self) -> Optional[TelegramClient]:
        """Get the authenticated Telethon client."""
        if self._authenticated and self._client:
            return self._client
        return None
        
    async def disconnect(self):
        """Disconnect from Telegram and cleanup."""
        if self._client:
            await self._client.disconnect()
            self._client = None
        self._authenticated = False
        logger.info("Disconnected from Telegram")
        
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