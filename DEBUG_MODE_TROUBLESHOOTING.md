# Debug Mode Troubleshooting

## Problem: Debug mode enabled but no output in console

### Possible Causes and Solutions

#### 1. No Messages Being Processed

**Symptom:** `messages_processed` is 0 or very low in status output

**Cause:** The scanner isn't actually processing any messages

**Solutions:**
- Check `max_history_days` in config.json - if it's 0, no historical messages will be scanned
- Set `max_history_days` to at least 1 to scan recent messages
- Wait for new messages to arrive if doing real-time monitoring only

**Example:**
```json
{
  "scanning": {
    "max_history_days": 1,  // Scan last 24 hours
    "debug_mode": true
  }
}
```

#### 2. Messages Processed But No Matches

**Symptom:** `messages_processed` > 0 but no debug output

**Cause:** Debug output only shows when messages are actually being processed, not when they're skipped

**Check:**
- Are your keywords matching any messages?
- Run `status` command to see `relevant_messages_found`
- If 0 relevant messages, your keywords might be too specific

**Solution:**
- Temporarily use very common keywords to test debug mode:
```json
{
  "relevance": {
    "keywords": ["the", "a", "и", "в"],  // Very common words
    "logic": "OR"
  }
}
```

#### 3. Config Not Reloaded

**Symptom:** Changed `debug_mode` to true but still no output

**Cause:** Scanner was already running when you changed the config

**Solution:**
1. Stop the scanner: `stop` command
2. Exit and restart: `exit` command, then run again
3. Or use `reload` command (if available)

#### 4. Output Buffering

**Symptom:** Debug output appears all at once after a delay

**Cause:** Console output buffering (should be fixed with `flush=True`)

**Solution:**
- Run Python with unbuffered output:
```bash
python -u telegram_scanner/main.py
```

#### 5. Wrong Log Level

**Symptom:** Only seeing log messages, not debug output

**Cause:** Debug mode uses `print()` to stdout, not logging

**Check:**
- Debug output should look like:
```
================================================================================
DEBUG: Processing Message 12345
================================================================================
```
- Not like:
```
2026-01-20 17:45:30 - telegram_scanner.scanner - INFO - Processing message
```

#### 6. Historical Scan Skipped

**Symptom:** Scanner starts but immediately goes to real-time monitoring

**Cause:** `max_history_days` is 0 or very small

**Solution:**
```json
{
  "scanning": {
    "max_history_days": 7  // Scan last week
  }
}
```

## Verification Steps

### Step 1: Verify Config
```bash
python -c "import json; c=json.load(open('config.json')); print('debug_mode:', c['scanning']['debug_mode']); print('max_history_days:', c['scanning']['max_history_days'])"
```

Expected output:
```
debug_mode: True
max_history_days: 1
```

### Step 2: Check Scanner Startup

When you start the scanner with debug mode enabled, you should see:

```
================================================================================
DEBUG MODE ENABLED
Will print detailed information for each message processed
================================================================================
```

If you don't see this, debug mode is not enabled.

### Step 3: Monitor Status

Run `status` command periodically:
```
Enter command: status
```

Check:
- `messages_processed` - should be increasing
- `relevant_messages_found` - should be > 0 if keywords match

### Step 4: Test with Broad Keywords

Temporarily use very common keywords to ensure messages are being found:

```json
{
  "relevance": {
    "keywords": [""],  // Empty string matches everything
    "logic": "OR"
  }
}
```

**Warning:** This will match ALL messages, use only for testing!

## Expected Debug Output

When working correctly, you should see output like this for EACH message:

```
================================================================================
DEBUG: Processing Message 12345
================================================================================
Group: Marketing Jobs (ID: 1234567890)
Sender: recruiter_bot (ID: 987654321)
Timestamp: 2026-01-20 10:30:15
Content: Нужен маркетолог-практик для работы над проектом...

Relevance Check:
  Is Relevant: True
  Relevance Score: 1.00
  Matched Keywords: Нужен маркетолог-практик
================================================================================
```

## Quick Test

1. Set debug mode and scan 1 day:
```json
{
  "scanning": {
    "max_history_days": 1,
    "debug_mode": true
  },
  "relevance": {
    "keywords": ["а", "и", "в"],  // Common Russian words
    "logic": "OR"
  }
}
```

2. Restart scanner:
```bash
python telegram_scanner/main.py
```

3. Run start command:
```
Enter command: start
```

4. You should immediately see debug output as historical messages are scanned

## Still Not Working?

If debug output still doesn't appear:

1. Check scanner.log for errors
2. Verify Python version (3.7+)
3. Check if stdout is being redirected
4. Try running with: `python -u telegram_scanner/main.py`
5. Check if messages exist in your groups for the time period

## Common Mistakes

❌ **Wrong:** `max_history_days: 0` with no new messages
✅ **Right:** `max_history_days: 1` to scan recent messages

❌ **Wrong:** Very specific keywords that don't match anything
✅ **Right:** Start with common keywords to test

❌ **Wrong:** Changing config while scanner is running
✅ **Right:** Stop scanner, change config, restart

❌ **Wrong:** Expecting debug output in scanner.log file
✅ **Right:** Debug output goes to console (stdout)
