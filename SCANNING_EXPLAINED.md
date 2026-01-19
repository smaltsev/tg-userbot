# Telegram Scanner - How Scanning Works

## Understanding Scanner Status

When you see this status:
```json
{
  "state": "running",
  "last_scan_time": null,
  "messages_processed": 0,
  "groups_monitored": 417,
  "relevant_messages_found": 0,
  "uptime_seconds": 46
}
```

This means the scanner is in **real-time monitoring mode** only.

## Two Types of Scanning

### 1. **Historical Message Scanning** (Now Implemented!)
- Scans past messages from the last N days (configured in `max_history_days`)
- Processes existing messages in groups
- Updates `messages_processed` counter
- Sets `last_scan_time`
- Finds relevant messages from history

### 2. **Real-Time Monitoring**
- Listens for new messages as they arrive
- Processes messages in real-time
- Continuously updates counters
- Runs indefinitely until stopped

## How It Works Now

When you type `start`, the scanner now:

1. **Discovers Groups** (if not already done)
   - Finds all your Telegram groups
   - Takes 5-10 minutes for 600+ dialogs

2. **Scans Historical Messages** ⭐ NEW!
   - Scans last 7 days of messages (configurable)
   - Processes up to 1000 messages per group
   - Updates `messages_processed` counter
   - Sets `last_scan_time`
   - Finds relevant messages

3. **Starts Real-Time Monitoring**
   - Listens for new messages
   - Processes them as they arrive
   - Continues indefinitely

## Configuration

Edit `config.json` to control historical scanning:

```json
{
  "scanning": {
    "scan_interval": 30,
    "max_history_days": 7,      // How many days back to scan
    "selected_groups": []
  }
}
```

### Recommended Settings:

**For Quick Testing:**
```json
"max_history_days": 1  // Scan last 24 hours only
```

**For Thorough Scanning:**
```json
"max_history_days": 7  // Scan last week
```

**For Deep Historical Search:**
```json
"max_history_days": 30  // Scan last month
```

## Expected Behavior

### After Starting Scanner:

**Phase 1: Group Discovery (5-10 minutes)**
```
Processed 50 dialogs, found 25 groups so far...
Processed 100 dialogs, found 48 groups so far...
...
Group discovery completed. Found 417 groups
```

**Phase 2: Historical Scan (NEW - 5-30 minutes)**
```
Starting historical message scan for last 7 days...
Scanning history for group: КиберТопор
Scanned 100 messages, found 2 relevant
Scanning history for group: Топор Live
...
Historical scan complete: 5000 messages scanned, 15 relevant found
```

**Phase 3: Real-Time Monitoring (Continuous)**
```
Real-time monitoring started
Relevant message found: [message details]
...
```

### Status After Historical Scan:

```json
{
  "state": "running",
  "last_scan_time": "2026-01-19T22:30:00Z",  // ✅ Now set!
  "messages_processed": 5000,                 // ✅ Now counting!
  "groups_monitored": 417,
  "relevant_messages_found": 15,              // ✅ Found messages!
  "uptime_seconds": 1800
}
```

## Performance Estimates

| Groups | Days | Messages | Time |
|--------|------|----------|------|
| 100    | 1    | ~1,000   | 2-5 min |
| 100    | 7    | ~7,000   | 10-15 min |
| 417    | 1    | ~4,000   | 5-10 min |
| 417    | 7    | ~30,000  | 20-40 min |

*Note: Actual time depends on message volume and rate limiting*

## Why Was It Zero Before?

**Before the fix:**
- Scanner only did real-time monitoring
- No historical messages were scanned
- Counters only updated when new messages arrived
- If no new messages came in, counters stayed at 0

**After the fix:**
- Scanner scans historical messages first
- Counters update immediately
- You see results even if no new messages arrive
- More useful for finding existing relevant content

## Monitoring Progress

### Check Status Regularly:
```
Enter command: status
```

### Generate Report:
```
Enter command: report
```

### List Groups:
```
Enter command: list
```

## Troubleshooting

### "messages_processed" Still Zero?

**Possible reasons:**
1. Historical scan hasn't completed yet (wait longer)
2. No messages in the last N days
3. Scanner stopped before historical scan
4. Error during historical scan (check logs)

**Solutions:**
- Wait for historical scan to complete
- Check `scanner.log` for errors
- Increase `max_history_days` if groups are inactive
- Use `status` command to monitor progress

### "last_scan_time" Still Null?

**Possible reasons:**
1. Historical scan not started yet
2. Historical scan failed
3. Scanner in real-time mode only (old behavior)

**Solutions:**
- Restart scanner (type `stop` then `start`)
- Check logs for errors
- Verify configuration is valid

### Historical Scan Taking Too Long?

**Solutions:**
1. Reduce `max_history_days`:
   ```json
   "max_history_days": 1  // Faster
   ```

2. Use specific groups instead of all:
   ```json
   "selected_groups": ["Group1", "Group2"]
   ```

3. Reduce message limit per group (edit scanner.py line ~560):
   ```python
   limit=100  // Instead of 1000
   ```

## Best Practices

1. **Start with 1 day** of history for testing
2. **Monitor progress** with `status` command
3. **Check logs** if counters don't update
4. **Be patient** - historical scan takes time
5. **Use specific groups** for faster scanning

## Summary

✅ **Historical scanning now implemented**  
✅ **Counters update properly**  
✅ **last_scan_time gets set**  
✅ **Finds relevant messages from history**  
✅ **Then continues with real-time monitoring**  

The scanner now provides complete coverage: both historical messages and real-time monitoring!
