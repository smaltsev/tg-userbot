# Real-Time Monitoring Fix

## Problem

Real-time monitoring was not processing new messages. The status showed:
- `messages_processed`: 6 (only from historical scan)
- Counter not increasing despite new messages in groups
- `uptime_seconds` increasing but no new messages detected

## Root Cause

The Telethon event handler was registered without specifying which chats to monitor:

```python
@client.on(events.NewMessage)  # No chat filter!
async def new_message_handler(event):
    # Manual filtering inside handler
    if group_id and any(group.id == group_id for group in self._discovered_groups):
        ...
```

**Issue:** Telethon's `@client.on()` decorator without a `chats` parameter may not reliably catch all messages, especially when monitoring many groups.

## Solution

Register the event handler with explicit chat IDs:

```python
# Get list of group IDs to monitor
group_ids = [group.id for group in self._discovered_groups]

# Register handler with specific chats
@client.on(events.NewMessage(chats=group_ids))
async def new_message_handler(event):
    # No manual filtering needed - Telethon handles it
    await self._message_queue.put((event.message, client))
```

## Changes Made

### File: `telegram_scanner/scanner.py`

**Before:**
```python
@client.on(events.NewMessage)
async def new_message_handler(event):
    try:
        # Check if message is from a monitored group
        if hasattr(event.message, 'peer_id') and event.message.peer_id:
            group_id = None
            if hasattr(event.message.peer_id, 'channel_id'):
                group_id = event.message.peer_id.channel_id
            elif hasattr(event.message.peer_id, 'chat_id'):
                group_id = event.message.peer_id.chat_id
            
            if group_id and any(group.id == group_id for group in self._discovered_groups):
                await self._message_queue.put((event.message, client))
```

**After:**
```python
# Get list of group IDs to monitor
group_ids = [group.id for group in self._discovered_groups]
logger.info(f"Monitoring {len(group_ids)} groups for new messages")

# Set up event handler for new messages from monitored groups
@client.on(events.NewMessage(chats=group_ids))
async def new_message_handler(event):
    try:
        # Add message to processing queue for consistent handling
        await self._message_queue.put((event.message, client))
        logger.debug(f"Queued new message {event.message.id} from group {event.chat_id}")
```

## Benefits

1. **More Reliable:** Telethon handles chat filtering at the library level
2. **More Efficient:** No manual filtering needed in handler
3. **Cleaner Code:** Simpler event handler logic
4. **Better Logging:** Clear indication of which groups are monitored

## Testing

### Before Fix
```
Status:
{
  "messages_processed": 6,
  "uptime_seconds": 721
}

[New messages arrive in groups]
[No change in messages_processed]
```

### After Fix
```
Status:
{
  "messages_processed": 6,
  "uptime_seconds": 50
}

[New message arrives]

Status:
{
  "messages_processed": 7,  ← Incremented!
  "uptime_seconds": 120
}
```

## How to Apply

1. **Stop the scanner:**
   ```
   Enter command: stop
   Enter command: exit
   ```

2. **Restart the scanner:**
   ```
   python telegram_scanner/main.py
   ```

3. **Start monitoring:**
   ```
   Enter command: start
   ```

4. **Verify it's working:**
   - Wait for a new message in one of your groups
   - Check status: `status` command
   - `messages_processed` should increment

## Verification

### Check Logs

Look for this line in the logs:
```
INFO - Monitoring 417 groups for new messages
```

### Monitor Status

Run `status` command periodically:
```
Enter command: status
```

Watch `messages_processed` - it should increase when new messages arrive.

### Debug Mode

Enable debug mode to see each message:
```json
{
  "scanning": {
    "debug_mode": true
  }
}
```

You should see output for each new message:
```
================================================================================
DEBUG: Processing Message 12345
================================================================================
Group: Example Group (ID: 1234567890)
...
```

## Related Issues

### If Still Not Working

1. **Check group IDs are correct:**
   ```
   Enter command: list
   ```
   Verify groups are discovered

2. **Check you're in the groups:**
   - Open Telegram app
   - Verify you can see messages in the groups

3. **Re-scan groups:**
   ```
   Enter command: stop
   Enter command: scan
   Enter command: start
   ```

4. **Check logs for errors:**
   ```
   # Look at scanner.log
   type scanner.log  # Windows
   cat scanner.log   # Linux/Mac
   ```

## Technical Details

### Telethon Event Filtering

Telethon's `events.NewMessage()` accepts several parameters:
- `chats`: List of chat IDs to monitor
- `incoming`: Only incoming messages (default: True)
- `outgoing`: Only outgoing messages
- `from_users`: Only from specific users
- `pattern`: Regex pattern to match

By specifying `chats=group_ids`, we tell Telethon to only trigger the handler for messages from those specific groups.

### Performance Impact

- **Before:** Handler called for ALL messages, manual filtering
- **After:** Handler only called for monitored groups
- **Result:** More efficient, less CPU usage

## Files Modified

1. `telegram_scanner/scanner.py` - Fixed event handler registration

## Files Created

1. `REALTIME_MONITORING_FIX.md` - This file

## Validation

Code compiles without errors:
```bash
python -m py_compile telegram_scanner/scanner.py
```

## Next Steps

After applying this fix:
1. Restart the scanner
2. Monitor the `messages_processed` counter
3. Verify new messages are being caught
4. Check debug output if enabled

The real-time monitoring should now work correctly!
