#!/usr/bin/env python3
"""
Session transfer utility - helps use existing Telegram sessions.
"""

import os
import shutil
from pathlib import Path

def find_telegram_sessions():
    """Find existing Telegram session files on the system."""
    
    print("Searching for existing Telegram sessions...")
    
    # Common locations for Telegram sessions
    search_paths = [
        Path.home() / "AppData" / "Roaming" / "Telegram Desktop" / "tdata",
        Path.home() / "AppData" / "Local" / "Telegram Desktop" / "tdata", 
        Path.home() / ".local" / "share" / "TelegramDesktop" / "tdata",
        Path.cwd(),  # Current directory
    ]
    
    session_files = []
    
    for search_path in search_paths:
        if search_path.exists():
            print(f"Checking: {search_path}")
            
            # Look for .session files
            for session_file in search_path.glob("*.session"):
                session_files.append(session_file)
                print(f"  Found session: {session_file}")
    
    return session_files

def list_session_options():
    """List available session options."""
    
    print("=" * 60)
    print("Telegram Session Transfer Utility")
    print("=" * 60)
    
    sessions = find_telegram_sessions()
    
    if sessions:
        print(f"\nFound {len(sessions)} existing session files:")
        for i, session in enumerate(sessions, 1):
            print(f"  {i}. {session}")
        
        print("\nYou can try copying one of these sessions to 'telegram_scanner.session'")
        print("But this may not work due to different API credentials.")
    else:
        print("No existing session files found.")
    
    print("\nAlternative approaches:")
    print("1. Use a different phone number temporarily")
    print("2. Try authentication from a different location/network")
    print("3. Wait for SMS delivery to improve")
    print("4. Use Telegram Desktop to get the code")
    print("5. Contact Telegram support")

if __name__ == "__main__":
    list_session_options()