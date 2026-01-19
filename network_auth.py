#!/usr/bin/env python3
"""
Try authentication with different network settings.
Sometimes changing network helps with SMS delivery.
"""

import asyncio
from telethon import TelegramClient

async def try_different_auth_methods():
    """Try authentication with different approaches."""
    
    api_id = 23301828
    api_hash = "e921b95ddd7a151b80232e41e70e6740"
    phone = "+79313384543"
    
    print("Trying different authentication methods...")
    
    # Method 1: Force SMS
    print("\n1. Trying to force SMS delivery...")
    client1 = TelegramClient('temp_session_1', api_id, api_hash)
    try:
        await client1.connect()
        sent_code = await client1.send_code_request(phone, force_sms=True)
        print(f"✓ SMS requested: {sent_code.type}")
        print("Check your SMS messages...")
        await client1.disconnect()
    except Exception as e:
        print(f"✗ SMS method failed: {e}")
        await client1.disconnect()
    
    # Method 2: Try call
    print("\n2. Trying to request call...")
    client2 = TelegramClient('temp_session_2', api_id, api_hash)
    try:
        await client2.connect()
        # First send normal code
        await client2.send_code_request(phone)
        await asyncio.sleep(5)
        # Then try to request call
        sent_code = await client2.send_code_request(phone, force_sms=False)
        print(f"✓ Call requested: {sent_code.type}")
        print("Wait for phone call...")
        await client2.disconnect()
    except Exception as e:
        print(f"✗ Call method failed: {e}")
        await client2.disconnect()
    
    # Method 3: Check if already authorized somehow
    print("\n3. Checking existing authorization...")
    client3 = TelegramClient('telegram_scanner', api_id, api_hash)
    try:
        await client3.connect()
        if await client3.is_user_authorized():
            print("✓ Already authorized!")
            me = await client3.get_me()
            print(f"✓ Logged in as: {me.first_name}")
            await client3.disconnect()
            return True
        else:
            print("✗ Not authorized")
            await client3.disconnect()
    except Exception as e:
        print(f"✗ Check failed: {e}")
        await client3.disconnect()
    
    return False

if __name__ == "__main__":
    success = asyncio.run(try_different_auth_methods())
    
    if success:
        print("\n✓ Authentication successful!")
    else:
        print("\n✗ All methods failed")
        print("\nRecommendations:")
        print("1. Install Telegram Desktop and log in there first")
        print("2. Try from a different network/location")
        print("3. Wait a few hours and try again")
        print("4. Contact your mobile operator about SMS delivery")