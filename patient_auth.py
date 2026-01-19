#!/usr/bin/env python3
"""
Patient authentication that waits for delayed verification codes.
"""

import asyncio
import time
from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError, PhoneCodeInvalidError

async def patient_authentication():
    """Authentication with extended waiting periods."""
    
    api_id = 23301828
    api_hash = "e921b95ddd7a151b80232e41e70e6740"
    
    print("Patient Authentication for Telegram Scanner")
    print("=" * 50)
    
    client = TelegramClient('telegram_scanner', api_id, api_hash)
    await client.connect()
    
    if await client.is_user_authorized():
        print("✓ Already authenticated!")
        me = await client.get_me()
        print(f"✓ Logged in as: {me.first_name} {me.last_name or ''}")
        await client.disconnect()
        return True
    
    phone = "+79313384543"  # Your phone number
    print(f"Sending code to {phone}...")
    
    sent_code = await client.send_code_request(phone)
    print(f"✓ Code sent via: {sent_code.type}")
    print("\nWaiting for verification code...")
    print("Please check:")
    print("- Telegram mobile app notifications")
    print("- Telegram Desktop app") 
    print("- Chat with 'Telegram' in any Telegram app")
    print("- SMS (sometimes takes 5-10 minutes)")
    
    # Give user multiple attempts with waiting
    for attempt in range(5):
        print(f"\nAttempt {attempt + 1}/5")
        
        # Wait a bit between attempts
        if attempt > 0:
            wait_time = 60 * attempt  # 1, 2, 3, 4 minutes
            print(f"Waiting {wait_time} seconds for code to arrive...")
            for i in range(wait_time, 0, -10):
                print(f"  {i} seconds remaining...", end='\r')
                await asyncio.sleep(10)
            print("\n")
        
        code = input("Enter verification code (or 'wait' to wait longer): ").strip()
        
        if code.lower() == 'wait':
            continue
            
        if not code.isdigit():
            print("Please enter only numbers")
            continue
            
        try:
            await client.sign_in(phone, code)
            print("✓ Authentication successful!")
            
            me = await client.get_me()
            print(f"✓ Logged in as: {me.first_name} {me.last_name or ''}")
            
            await client.disconnect()
            return True
            
        except PhoneCodeInvalidError:
            print("✗ Invalid code, please try again")
            continue
            
        except SessionPasswordNeededError:
            print("Two-factor authentication required")
            import getpass
            password = getpass.getpass("Enter 2FA password: ")
            await client.sign_in(password=password)
            print("✓ Authentication successful with 2FA!")
            
            me = await client.get_me()
            print(f"✓ Logged in as: {me.first_name} {me.last_name or ''}")
            
            await client.disconnect()
            return True
    
    print("✗ Authentication failed after 5 attempts")
    await client.disconnect()
    return False

if __name__ == "__main__":
    success = asyncio.run(patient_authentication())
    
    if success:
        print("\n" + "=" * 50)
        print("✓ Ready to run scanner!")
        print("Try: python -m telegram_scanner.main --test-discovery")
    else:
        print("\n" + "=" * 50)
        print("✗ Authentication failed")
        print("Please check your phone and Telegram apps for the code")