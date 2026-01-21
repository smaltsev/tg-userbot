# Feature: Skip Historical Scan

**Added:** 2026-01-21  
**Status:** ✅ Implemented

---

## Overview

You can now skip the historical message scan by setting `max_history_days` to 0 in your configuration. This allows the scanner to start monitoring immediately without processing old messages.

---

## Configuration

### Enable Historical Scan (Default)

```json
{
  "scanning": {
    "max_history_days": 7
  }
}
```

This will scan the last 7 days of messages when you run `start`.

### Skip Historical Scan

```json
{
  "scanning": {
    "max_history_days": 0
  }
}
```

This will skip historical scanning and only monitor new messages going forward.

---

## Behavior

### With Historical Scan (max_history_days > 0)

```
1. Start command issued
2. Load/discover groups
3. ✅ Scan historical messages (last N days)
4. Start real-time monitoring
5. Process new messages
```

**Output:**
```
Scanning historical messages...
Historical scan complete: 150 messages scanned, 5 relevant found
Real-time monitoring started
```

### Without Historical Scan (max_history_days = 0)

```
1. Start command issued
2. Load/discover groups
3. ⏭️  Skip historical scan
4. Start real-time monitoring immediately
5. Process new messages
```

**Output:**
```
Skipping historical scan (max_history_days is 0)
Skipping historical scan - will only monitor new messages
Real-time monitoring started
```

---

## Use Cases

### When to Skip Historical Scan

✅ **You only care about new messages**
- Monitoring for breaking news
- Real-time alerts only
- No need for past context

✅ **Faster startup time**
- Large groups with lots of history
- Quick testing/debugging
- Frequent restarts

✅ **Avoid rate limiting**
- Already scanned history once
- Restarting after crash
- Testing configuration changes

### When to Use Historical Scan

✅ **First-time setup**
- Want to see what you missed
- Building initial dataset
- Understanding group activity

✅ **Periodic catch-up**
- Scanner was offline
- Checking for missed messages
- Comprehensive monitoring

✅ **Data collection**
- Research purposes
- Trend analysis
- Historical context needed

---

## Examples

### Real-Time Only Configuration

```json
{
  "api_credentials": {
    "api_id": "your_api_id",
    "api_hash": "your_api_hash"
  },
  "scanning": {
    "scan_interval": 30,
    "max_history_days": 0,
    "selected_groups": ["NewsChannel", "AlertsGroup"],
    "debug_mode": false
  },
  "relevance": {
    "keywords": ["breaking", "urgent", "alert"],
    "logic": "OR"
  }
}
```

**Result:** Starts monitoring immediately, no historical scan.

### Comprehensive Monitoring Configuration

```json
{
  "scanning": {
    "max_history_days": 30,
    "selected_groups": ["ResearchGroup"]
  },
  "relevance": {
    "keywords": ["study", "research", "data"],
    "logic": "OR"
  }
}
```

**Result:** Scans last 30 days of messages, then monitors new ones.

---

## Performance Impact

### Historical Scan Enabled (max_history_days = 7)

- **Startup Time:** 30 seconds - 5 minutes (depends on group size)
- **API Calls:** High (scanning old messages)
- **Initial Results:** Immediate (from history)

### Historical Scan Disabled (max_history_days = 0)

- **Startup Time:** 5-10 seconds
- **API Calls:** Minimal (only setup)
- **Initial Results:** Only after new messages arrive

---

## Implementation Details

### Code Location

**File:** `telegram_scanner/command_interface.py`

**Logic:**
```python
# Check if historical scan should be performed
if self.scanner.config_manager.get_config().max_history_days > 0:
    logger.info("Scanning historical messages...")
    history_result = await self.scanner.group_scanner.scan_history()
    # Process results...
else:
    logger.info("Skipping historical scan (max_history_days is 0)")
    print("Skipping historical scan - will only monitor new messages")
```

### Validation

The configuration value is validated:
- Must be an integer
- Must be >= 0
- Default value: 7 days

---

## Testing

### Test Skip Historical Scan

1. **Set configuration:**
   ```json
   {
     "scanning": {
       "max_history_days": 0
     }
   }
   ```

2. **Start scanner:**
   ```bash
   python -m telegram_scanner.cli
   ```

3. **Run start command:**
   ```
   Enter command: start
   ```

4. **Verify output:**
   ```
   Skipping historical scan (max_history_days is 0)
   Skipping historical scan - will only monitor new messages
   Real-time monitoring started with 3 processing workers
   ```

5. **Post test message:**
   Should be detected immediately

### Test With Historical Scan

1. **Set configuration:**
   ```json
   {
     "scanning": {
       "max_history_days": 1
     }
   }
   ```

2. **Start scanner and run start command**

3. **Verify output:**
   ```
   Scanning historical messages...
   Scanning messages from 2026-01-20 to now
   Historical scan complete: X messages scanned, Y relevant found
   Real-time monitoring started
   ```

---

## Troubleshooting

### Historical Scan Still Running

**Problem:** Set max_history_days to 0 but still scanning history

**Solution:**
1. Verify config.json has the correct value
2. Restart the scanner application
3. Clear Python cache: `Remove-Item -Recurse -Force telegram_scanner/__pycache__`

### No Messages Found

**Problem:** Set max_history_days to 0 and no messages appear

**Expected:** This is normal! With max_history_days = 0, you'll only see NEW messages posted after starting the scanner.

**Solution:** Post a test message or wait for new activity in monitored groups.

---

## Benefits

✅ **Faster Startup:** Skip time-consuming historical scan  
✅ **Lower API Usage:** Fewer requests to Telegram  
✅ **Flexible Configuration:** Choose what works for your use case  
✅ **Better Testing:** Quick restarts during development  
✅ **Resource Efficient:** Less processing for large groups  

---

## Related Configuration

Other scanning options that work with this feature:

- `scan_interval`: How often to check (not affected by max_history_days)
- `selected_groups`: Which groups to monitor
- `keywords`: What to look for in messages
- `debug_mode`: Enable detailed logging

---

**Status:** ✅ Feature implemented and tested  
**Impact:** Improved flexibility and performance  
**Backward Compatible:** Yes (default is 7 days)
