#!/usr/bin/env python3
"""
Manual authentication setup for Telegram Scanner.
Handles various authentication scenarios including delayed verification codes.
"""

import asyncio
import logging
import time
from pathlib import Path
from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError, PhoneCodeInvalidError, FloodWaitError
from telegram_scanner.config import ConfigManager

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def setup_authentication():
    """Setup Telegram authentication with various fallback options."""
    
    print("=" * 60)
    print("Telegram Scanner - Authentication Setup")
    print("=" * 60)
    
    try:
        # Load configuration
        config_manager = ConfigManager("config.json")
        config = await config_manager.load_config()
        
        print(f"API ID: {config.api_id}")
        print(f"API Hash: {config.api_hash[:10]}...")
        
        session_name = "telegram_scanner"
        session_path = Path(f"{session_name}.session")
        
        # Check if session exists
        if session_path.exists():
            print(f"\nExisting session file found: {session_path}")
            choice = input("Do you want to (k)eep existing session, (d)elete and recreate, or (t)est existing? [k/d/t]: ").lower()
            
            if choice == 'd':
                session_path.unlink()
                print("Existing session deleted.")
            elif choice == 't':
                print("Testing existing session...")
                client = TelegramClient(session_name, int(config.api_id), config.api_hash)
                await client.connect()
                
                if await client.is_user_authorized():
                    print("✓ Existing session is valid and authorized!")
                    me = await client.get_me()
                    print(f"✓ Logged in as: {me.first_name} {me.last_name or ''} (@{me.username or 'no username'})")
                    await client.disconnect()
                    return True
                else:
                    print("✗ Existing session is not authorized. Need to re-authenticate.")
                    await client.disconnect()
            elif choice == 'k':
                print("Keeping existing session. If it doesn't work, run this script again and choose 'd'.")
                return True
        
        # Create new client
        client = TelegramClient(session_name, int(config.api_id), config.api_hash)
        await client.connect()
        
        # Check if already authorized (shouldn't happen if we deleted session)
        if await client.is_user_authorized():
            print("✓ Already authorized!")
            me = await client.get_me()
            print(f"✓ Logged in as: {me.first_name} {me.last_name or ''} (@{me.username or 'no username'})")
            await client.disconnect()
            return True
        
        # Start authentication process
        print("\nStarting authentication process...")
        
        # Get phone number
        while True:
            phone = input("Enter your phone number (with country code, e.g., +79313384543): ").strip()
            if phone and phone.startswith('+') and len(phone) > 5:
                break
            print("Please enter a valid phone number with country code")
        
        print(f"Sending verification code to {phone}...")
        
        try:
            sent_code = await client.send_code_request(phone)
            print(f"✓ Verification code sent via {sent_code.type}")
            
            # Give user options for code input
            print("\nVerification code options:")
            print("1. Enter code when it arrives")
            print("2. Wait and retry (if code is delayed)")
            print("3. Request code via call")
            
            while True:
                choice = input("Choose option [1/2/3]: ").strip()
                
                if choice == '1':
                    # Standard code input
                    while True:
                        code = input("Enter the verification code: ").strip()
                        if code and code.isdigit():
                            break
                        print("Please enter a valid numeric code")
                    
                    try:
                        await client.sign_in(phone, code)
                        break
                    except PhoneCodeInvalidError:
                        print("Invalid code. Please try again.")
                        continue
                    except SessionPasswordNeededError:
                        # 2FA required
                        print("Two-factor authentication detected.")
                        import getpass
                        password = getpass.getpass("Enter your 2FA password: ")
                        await client.sign_in(password=password)
                        break
                
                elif choice == '2':
                    # Wait and retry
                    print("Waiting 60 seconds for code to arrive...")
                    await asyncio.sleep(60)
                    print("You can now try entering the code.")
                    continue
                
                elif choice == '3':
                    # Request call
                    try:
                        print("Requesting verification call...")
                        await client.send_code_request(phone, force_sms=False)
                        print("Call requested. Please wait for the call and enter the code.")
                        continue
                    except Exception as e:
                        print(f"Could not request call: {e}")
                        continue
                
                else:
                    print("Invalid choice. Please enter 1, 2, or 3.")
        
        except FloodWaitError as e:
            print(f"Rate limited. Please wait {e.seconds} seconds before trying again.")
            await client.disconnect()
            return False
        
        except Exception as e:
            print(f"Error during authentication: {e}")
            await client.disconnect()
            return False
        
        # Verify authentication worked
        if await client.is_user_authorized():
            me = await client.get_me()
            print(f"\n✓ Authentication successful!")
            print(f"✓ Logged in as: {me.first_name} {me.last_name or ''} (@{me.username or 'no username'})")
            print(f"✓ Session saved as: {session_path}")
            
            await client.disconnect()
            return True
        else:
            print("✗ Authentication failed")
            await client.disconnect()
            return False
            
    except Exception as e:
        print(f"Setup failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Main function."""
    success = await setup_authentication()
    
    if success:
        print("\n" + "=" * 60)
        print("✓ Authentication setup completed successfully!")
        print("You can now run the scanner with:")
        print("  python -m telegram_scanner.main --test-discovery")
        print("  python -m telegram_scanner.main --batch")
        print("  python -m telegram_scanner.main  (interactive mode)")
        print("=" * 60)
    else:
        print("\n" + "=" * 60)
        print("✗ Authentication setup failed.")
        print("Please check your API credentials and try again.")
        print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())