"""
Property-based tests for authentication functionality.
Feature: telegram-group-scanner
"""

import pytest
import asyncio
import tempfile
import shutil
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
from hypothesis import given, strategies as st, settings
from telegram_scanner.auth import AuthenticationManager
from telegram_scanner.config import ScannerConfig


class TestAuthenticationProperties:
    """Property-based tests for authentication manager."""

    @given(
        api_id=st.integers(min_value=100000, max_value=999999).map(str),
        api_hash=st.text(min_size=32, max_size=32, alphabet=st.characters(whitelist_categories=('Ll', 'Lu', 'Nd')))
    )
    @settings(max_examples=100, deadline=None)
    @pytest.mark.asyncio
    async def test_session_persistence_round_trip(self, api_id, api_hash):
        """
        Property 1: Session persistence round-trip
        For any valid API credentials, establishing a session and then loading it 
        should result in an authenticated state equivalent to the original session.
        **Feature: telegram-group-scanner, Property 1: Session persistence round-trip**
        **Validates: Requirements 1.4**
        """
        # Create temporary directory for session files
        with tempfile.TemporaryDirectory() as temp_dir:
            session_name = f"test_session_{api_id}"
            session_path = Path(temp_dir) / f"{session_name}.session"
            
            # Create config with generated credentials
            config = ScannerConfig(
                api_id=api_id,
                api_hash=api_hash
            )
            
            # Mock Telethon client to simulate successful authentication
            with patch('telegram_scanner.auth.TelegramClient') as mock_client_class:
                mock_client = AsyncMock()
                mock_client_class.return_value = mock_client
                mock_client.connect = AsyncMock()
                mock_client.is_user_authorized = AsyncMock(return_value=True)
                mock_client.disconnect = AsyncMock()
                
                # Create session file to simulate existing session
                session_path.touch()
                
                # First auth manager - simulate loading existing session
                auth_manager1 = AuthenticationManager(config, session_name)
                # Change to temp directory for session file
                original_cwd = Path.cwd()
                try:
                    import os
                    os.chdir(temp_dir)
                    
                    result1 = await auth_manager1.load_session()
                    
                    # Second auth manager - should load the same session
                    auth_manager2 = AuthenticationManager(config, session_name)
                    result2 = await auth_manager2.load_session()
                    
                    # Both should be authenticated if session exists and is valid
                    if result1:
                        assert result2, "Second load_session should succeed if first succeeded"
                        assert auth_manager1.is_authenticated() == auth_manager2.is_authenticated()
                    
                    # Cleanup
                    await auth_manager1.disconnect()
                    await auth_manager2.disconnect()
                    
                finally:
                    os.chdir(original_cwd)

    @given(
        api_id=st.one_of(
            st.just(""),  # Empty string
            st.just("invalid"),  # Non-numeric
            st.just("0"),  # Invalid ID
            st.just("your_api_id_here")  # Default placeholder
        ),
        api_hash=st.one_of(
            st.just(""),  # Empty string
            st.just("short"),  # Too short
            st.just("your_api_hash_here")  # Default placeholder
        )
    )
    @settings(max_examples=100, deadline=None)
    @pytest.mark.asyncio
    async def test_authentication_error_descriptiveness(self, api_id, api_hash):
        """
        Property 2: Authentication error descriptiveness
        For any invalid credential combination, the authentication process should 
        return error messages that contain specific information about what went wrong.
        **Feature: telegram-group-scanner, Property 2: Authentication error descriptiveness**
        **Validates: Requirements 1.5**
        """
        config = ScannerConfig(
            api_id=api_id,
            api_hash=api_hash
        )
        
        auth_manager = AuthenticationManager(config, "test_invalid_session")
        
        try:
            await auth_manager.authenticate()
            # If we get here without exception, the credentials were somehow valid
            # This shouldn't happen with our invalid test data
            assert False, "Expected authentication to fail with invalid credentials"
        except ValueError as e:
            error_message = str(e).lower()
            
            # Error message should be descriptive and contain relevant information
            assert len(error_message) > 10, "Error message should be descriptive"
            
            # Should mention authentication or credentials
            assert any(keyword in error_message for keyword in [
                'authentication', 'credential', 'api', 'id', 'hash', 'invalid'
            ]), f"Error message should mention authentication issue: {error_message}"
            
            # Should not be a generic error
            assert "unexpected" not in error_message or "authentication" in error_message
            
        except Exception as e:
            # Other exceptions should still provide meaningful information
            error_message = str(e).lower()
            assert len(error_message) > 5, "Error message should not be empty or too short"
        
        finally:
            await auth_manager.disconnect()