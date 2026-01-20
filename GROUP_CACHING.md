# Group Caching Feature

## Overview

The scanner now caches discovered groups to avoid time-consuming re-discovery on every startup. For accounts with hundreds of groups, this saves 5-10 minutes each time you start the scanner.

## How It Works

### Automatic Caching

When you discover groups (either via `start` or `scan` command), the scanner automatically saves the group list to `discovered_groups.json`.

### Automatic Loading

When you run the `start` command, the scanner:
1. Checks if `discovered_groups.json` exists
2. If yes: Loads groups from cache (instant)
3. If no: Discovers groups from Telegram (5-10 minutes)

### Manual Re-Discovery

Use the `scan` command to force re-discovery when:
- You join new groups
- You leave groups
- Group information changes
- You want to refresh the list

## Commands

### `start` - Start with Cached Groups

```
Enter command: start
```

**Behavior:**
- Loads groups from cache if available
- Falls back to discovery if no cache exists
- Begins monitoring immediately

**Output:**
```
✓ Loaded 417 groups from cache
  Use 'scan' command to re-discover groups
```

### `scan` - Force Re-Discovery

```
Enter command: scan
```

**Requirements:**
- Scanner must be stopped first
- If running, use `stop` command first

**Behavior:**
- Clears cached groups
- Discovers all groups from scratch
- Saves new list to cache
- Takes 5-10 minutes for large accounts

**Output:**
```
Scanning for groups...
This will clear cached groups and discover from scratch.
This may take several minutes for large accounts.

✓ Group scan completed: 417 groups discovered
  Groups cached for future use
```

### `list` - View Cached Groups

```
Enter command: list
```

Shows all discovered/cached groups with details.

## Cache File

### Location

`discovered_groups.json` in the project root directory

### Format

```json
[
  {
    "id": 1234567890,
    "title": "Example Group",
    "username": "examplegroup",
    "member_count": 1500,
    "is_private": false,
    "access_hash": 1234567890123456789,
    "last_scanned": null,
    "is_channel": false,
    "is_megagroup": true
  }
]
```

### Security

- File is added to `.gitignore` (not committed to git)
- Contains only group metadata (no messages)
- Safe to delete (will be recreated on next discovery)

## Use Cases

### Daily Use

```
# First time (or after joining new groups)
Enter command: scan
# Wait 5-10 minutes for discovery

# Subsequent uses (instant)
Enter command: start
# Loads from cache immediately
```

### After Joining New Groups

```
Enter command: stop
Enter command: scan
# Wait for re-discovery
Enter command: start
```

### Troubleshooting

If groups seem outdated:
```
Enter command: stop
Enter command: scan
```

## Performance Comparison

### Without Caching (Old Behavior)
- Every `start`: 5-10 minutes for discovery
- 610 dialogs: ~10 minutes
- 299 groups: ~10 minutes

### With Caching (New Behavior)
- First `start` or `scan`: 5-10 minutes
- Subsequent `start`: < 1 second
- **Time saved: 5-10 minutes per startup**

## Example Workflows

### First Time Setup

```
$ python telegram_scanner/main.py

Enter command: start
No cached groups found. Discovering groups...
This may take several minutes for large accounts.
Groups will be cached for future use.

[10 minutes later]
✓ Group scan completed: 417 groups discovered
Scanner started successfully
```

### Daily Use

```
$ python telegram_scanner/main.py

Enter command: start
✓ Loaded 417 groups from cache
  Use 'scan' command to re-discover groups

Scanner started successfully
```

### After Joining New Groups

```
Enter command: stop
Scanner stopped successfully

Enter command: scan
Scanning for groups...
This will clear cached groups and discover from scratch.

[10 minutes later]
✓ Group scan completed: 420 groups discovered
  Groups cached for future use

Enter command: start
✓ Loaded 420 groups from cache
Scanner started successfully
```

## Cache Management

### View Cache Status

Check if cache exists:
```bash
# Windows
dir discovered_groups.json

# Linux/Mac
ls -lh discovered_groups.json
```

### Clear Cache Manually

Delete the cache file:
```bash
# Windows
del discovered_groups.json

# Linux/Mac
rm discovered_groups.json
```

Next `start` will trigger automatic discovery.

### Backup Cache

Save your group list:
```bash
# Windows
copy discovered_groups.json discovered_groups.backup.json

# Linux/Mac
cp discovered_groups.json discovered_groups.backup.json
```

## Automatic Cache Updates

The cache is automatically updated when:
- `scan` command completes successfully
- `start` command discovers groups (when no cache exists)
- Discovery completes (even if timeout with partial results)

## Limitations

### Cache Does Not Include

- Message history
- Real-time updates
- Group member lists (only counts)
- Detailed group settings

### When to Re-Scan

- After joining/leaving groups
- If group names change
- If member counts seem outdated
- After account changes

## Troubleshooting

### Cache Not Loading

**Symptom:** `start` always discovers groups

**Causes:**
1. `discovered_groups.json` doesn't exist
2. File is corrupted
3. File permissions issue

**Solution:**
```bash
# Check if file exists
dir discovered_groups.json  # Windows
ls discovered_groups.json   # Linux/Mac

# If corrupted, delete and re-scan
del discovered_groups.json  # Windows
rm discovered_groups.json   # Linux/Mac

# Then run scan
Enter command: scan
```

### Outdated Groups

**Symptom:** Groups list doesn't match current groups

**Solution:**
```
Enter command: stop
Enter command: scan
```

### Scan Command Fails

**Symptom:** `scan` command returns error

**Causes:**
1. Scanner is running (must be stopped)
2. Network issues
3. Rate limiting

**Solution:**
```
# Stop scanner first
Enter command: stop

# Wait a moment
# Then try scan again
Enter command: scan
```

## Best Practices

1. **Run `scan` weekly** to keep groups updated
2. **Run `scan` after joining new groups** you want to monitor
3. **Backup cache file** if you have a stable group list
4. **Don't edit cache manually** - use `scan` command instead
5. **Check cache size** - should be small (< 1MB for 1000 groups)

## Technical Details

### Cache Format

- JSON array of group objects
- UTF-8 encoding
- Pretty-printed (indent=2)
- Non-ASCII characters preserved (ensure_ascii=False)

### Save Triggers

- After successful `discover_groups()`
- After timeout with partial results
- After `scan` command completion

### Load Behavior

- Loads on `start` if cache exists
- Validates JSON format
- Falls back to discovery on error
- Logs all operations

## Related Commands

- `start` - Start scanner (uses cache)
- `stop` - Stop scanner (required before scan)
- `scan` - Force re-discovery
- `list` - View cached groups
- `status` - Check scanner state

## Related Documentation

- [COMMANDS.md](COMMANDS.md) - All available commands
- [QUICK_START.md](QUICK_START.md) - Getting started guide
- [DISCOVERY_OPTIMIZATION.md](DISCOVERY_OPTIMIZATION.md) - Discovery performance details
