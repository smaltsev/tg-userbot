"""
Unit tests for authentication functionality.
"""

import pytest
import asyncio
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch, mock_open
from telegram_scanner.auth import AuthenticationManager
from telegram_scanner.config import ScannerConfig
from telethon.errors import SessionPasswordNeededError, PhoneCodeInvalidError, ApiIdInvalidError


class TestAuthenticationManager:
    """Unit tests for AuthenticationManager class."""

    @pytest.fixture
    def valid_config(self):
        """Provide valid configuration for testing."""
        return ScannerConfig(
            api_id="123456",
            api_hash="valid_hash_32_characters_long_test"
        )

    @pytest.fixture
    def invalid_config(self):
        """Provide invalid configuration for testing."""
        return ScannerConfig(
            api_id="your_api_id_here",
            api_hash="your_api_hash_here"
        )

    @pytest.mark.asyncio
    async def test_authenticate_success(self, valid_config):
        """Test successful authentication flow."""
        with patch('telegram_scanner.auth.TelegramClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client
            mock_client.connect = AsyncMock()
            mock_client.is_user_authorized = AsyncMock(return_value=False)
            mock_client.send_code_request = AsyncMock()
            mock_client.sign_in = AsyncMock()

            auth_manager = AuthenticationManager(valid_config, "test_session")
            
            # Mock user input
            with patch('builtins.input', side_effect=['+1234567890', '12345']):
                result = await auth_manager.authenticate()
                
            assert result is True
            assert auth_manager.is_authenticated() is True
            mock_client.connect.assert_called_once()
            mock_client.send_code_request.assert_called_once_with('+1234567890')
            mock_client.sign_in.assert_called_once_with('+1234567890', '12345')

    @pytest.mark.asyncio
    async def test_authenticate_with_2fa(self, valid_config):
        """Test authentication flow with 2FA."""
        with patch('telegram_scanner.auth.TelegramClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client
            mock_client.connect = AsyncMock()
            mock_client.is_user_authorized = AsyncMock(return_value=False)
            mock_client.send_code_request = AsyncMock()
            mock_client.sign_in = AsyncMock(side_effect=[
                SessionPasswordNeededError("2FA required"),
                None  # Success on second call with password
            ])

            auth_manager = AuthenticationManager(valid_config, "test_session")
            
            # Mock user input and getpass
            with patch('builtins.input', side_effect=['+1234567890', '12345']), \
                 patch('getpass.getpass', return_value='2fa_password'):
                result = await auth_manager.authenticate()
                
            assert result is True
            assert auth_manager.is_authenticated() is True
            assert mock_client.sign_in.call_count == 2
            # First call with phone and code
            mock_client.sign_in.assert_any_call('+1234567890', '12345')
            # Second call with password
            mock_client.sign_in.assert_any_call(password='2fa_password')

    @pytest.mark.asyncio
    async def test_authenticate_invalid_credentials(self, invalid_config):
        """Test authentication with invalid API credentials."""
        auth_manager = AuthenticationManager(invalid_config, "test_session")
        
        with pytest.raises(ValueError) as exc_info:
            await auth_manager.authenticate()
            
        assert "API credentials" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_authenticate_empty_credentials(self):
        """Test authentication with empty credentials."""
        config = ScannerConfig(api_id="", api_hash="")
        auth_manager = AuthenticationManager(config, "test_session")
        
        with pytest.raises(ValueError) as exc_info:
            await auth_manager.authenticate()
            
        assert "API ID and API hash are required" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_authenticate_invalid_phone_code(self, valid_config):
        """Test authentication with invalid phone code."""
        with patch('telegram_scanner.auth.TelegramClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client
            mock_client.connect = AsyncMock()
            mock_client.is_user_authorized = AsyncMock(return_value=False)
            mock_client.send_code_request = AsyncMock()
            mock_client.sign_in = AsyncMock(side_effect=PhoneCodeInvalidError("Invalid code"))

            auth_manager = AuthenticationManager(valid_config, "test_session")
            
            with patch('builtins.input', side_effect=['+1234567890', '00000']):
                with pytest.raises(ValueError) as exc_info:
                    await auth_manager.authenticate()
                    
                assert "phone code entered was invalid" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_load_session_success(self, valid_config):
        """Test successful session loading."""
        with tempfile.TemporaryDirectory() as temp_dir:
            session_name = "test_session"
            session_path = Path(temp_dir) / f"{session_name}.session"
            session_path.touch()  # Create session file
            
            with patch('telegram_scanner.auth.TelegramClient') as mock_client_class:
                mock_client = AsyncMock()
                mock_client_class.return_value = mock_client
                mock_client.connect = AsyncMock()
                mock_client.is_user_authorized = AsyncMock(return_value=True)

                auth_manager = AuthenticationManager(valid_config, session_name)
                
                # Change to temp directory
                original_cwd = Path.cwd()
                try:
                    import os
                    os.chdir(temp_dir)
                    result = await auth_manager.load_session()
                finally:
                    os.chdir(original_cwd)
                
                assert result is True
                assert auth_manager.is_authenticated() is True
                mock_client.connect.assert_called_once()
                mock_client.is_user_authorized.assert_called_once()

    @pytest.mark.asyncio
    async def test_load_session_no_file(self, valid_config):
        """Test session loading when no session file exists."""
        auth_manager = AuthenticationManager(valid_config, "nonexistent_session")
        result = await auth_manager.load_session()
        
        assert result is False
        assert auth_manager.is_authenticated() is False

    @pytest.mark.asyncio
    async def test_load_session_unauthorized(self, valid_config):
        """Test session loading when session exists but user is not authorized."""
        with tempfile.TemporaryDirectory() as temp_dir:
            session_name = "test_session"
            session_path = Path(temp_dir) / f"{session_name}.session"
            session_path.touch()  # Create session file
            
            with patch('telegram_scanner.auth.TelegramClient') as mock_client_class:
                mock_client = AsyncMock()
                mock_client_class.return_value = mock_client
                mock_client.connect = AsyncMock()
                mock_client.is_user_authorized = AsyncMock(return_value=False)

                auth_manager = AuthenticationManager(valid_config, session_name)
                
                # Change to temp directory
                original_cwd = Path.cwd()
                try:
                    import os
                    os.chdir(temp_dir)
                    result = await auth_manager.load_session()
                finally:
                    os.chdir(original_cwd)
                
                assert result is False
                assert auth_manager.is_authenticated() is False

    @pytest.mark.asyncio
    async def test_load_session_no_credentials(self):
        """Test session loading without API credentials."""
        config = ScannerConfig(api_id="", api_hash="")
        auth_manager = AuthenticationManager(config, "test_session")
        result = await auth_manager.load_session()
        
        assert result is False
        assert auth_manager.is_authenticated() is False

    @pytest.mark.asyncio
    async def test_get_client_authenticated(self, valid_config):
        """Test getting client when authenticated."""
        with patch('telegram_scanner.auth.TelegramClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client
            
            auth_manager = AuthenticationManager(valid_config, "test_session")
            auth_manager._client = mock_client
            auth_manager._authenticated = True
            
            client = await auth_manager.get_client()
            assert client is mock_client

    @pytest.mark.asyncio
    async def test_get_client_not_authenticated(self, valid_config):
        """Test getting client when not authenticated."""
        auth_manager = AuthenticationManager(valid_config, "test_session")
        client = await auth_manager.get_client()
        assert client is None

    @pytest.mark.asyncio
    async def test_disconnect(self, valid_config):
        """Test disconnection from Telegram."""
        with patch('telegram_scanner.auth.TelegramClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client
            mock_client.disconnect = AsyncMock()
            
            auth_manager = AuthenticationManager(valid_config, "test_session")
            auth_manager._client = mock_client
            auth_manager._authenticated = True
            
            await auth_manager.disconnect()
            
            assert auth_manager.is_authenticated() is False
            assert auth_manager._client is None
            mock_client.disconnect.assert_called_once()

    @pytest.mark.asyncio
    async def test_already_authenticated(self, valid_config):
        """Test authentication when already authenticated."""
        with patch('telegram_scanner.auth.TelegramClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client
            mock_client.connect = AsyncMock()
            mock_client.is_user_authorized = AsyncMock(return_value=True)

            auth_manager = AuthenticationManager(valid_config, "test_session")
            result = await auth_manager.authenticate()
            
            assert result is True
            assert auth_manager.is_authenticated() is True
            # Should not prompt for phone/code when already authenticated
            mock_client.send_code_request.assert_not_called()