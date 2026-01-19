#!/usr/bin/env python3
"""
Simplified authentication for Telegram Scanner.
"""

import asyncio
from telethon import TelegramClient

async def simple_auth():
    """Simple authentication test."""
    
    # Your API credentials
    api_id = 23301828
    api_hash = "e921b95ddd7a151b80232e41e70e6740"
    
    print("Attempting simple authentication...")
    
    client = TelegramClient('telegram_scanner', api_id, api_hash)
    
    try:
        await client.start()
        
        if await client.is_user_authorized():
            me = await client.get_me()
            print(f"✓ Successfully authenticated as: {me.first_name} {me.last_name or ''}")
            print(f"✓ Username: @{me.username or 'no username'}")
            print(f"✓ Phone: {me.phone or 'no phone'}")
            
            # Test getting dialogs
            print("\nTesting dialog access...")
            dialog_count = 0
            async for dialog in client.iter_dialogs(limit=5):
                dialog_count += 1
                print(f"  Dialog {dialog_count}: {dialog.name}")
            
            print(f"✓ Can access dialogs (tested {dialog_count})")
            
            await client.disconnect()
            return True
        else:
            print("✗ Not authorized")
            await client.disconnect()
            return False
            
    except Exception as e:
        print(f"Error: {e}")
        await client.disconnect()
        return False

if __name__ == "__main__":
    asyncio.run(simple_auth())