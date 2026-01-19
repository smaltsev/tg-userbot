# Telegram Group Scanner - Command Reference

## Interactive Mode Commands

When running the scanner in interactive mode (`python -m telegram_scanner.main`), you can use the following commands:

### Core Commands

#### `start`
Start scanning the configured Telegram groups.
- Discovers groups from your account
- Begins monitoring for messages matching your keywords
- Runs continuously until stopped

**Example:**
```
Enter command: start
```

#### `stop`
Stop the scanner and end monitoring.
- Stops all monitoring activities
- Saves current state
- Can be restarted with `start` command

**Example:**
```
Enter command: stop
```

#### `pause`
Temporarily pause monitoring without stopping.
- Keeps connection alive
- Stops processing new messages
- Use `resume` to continue

**Example:**
```
Enter command: pause
```

#### `resume`
Resume monitoring after pausing.
- Continues from where it was paused
- Resumes message processing

**Example:**
```
Enter command: resume
```

### Information Commands

#### `status`
Display current scanner status.

Shows:
- Current state (running/stopped/paused/error)
- Number of groups being monitored
- Total messages processed
- Relevant messages found
- Uptime and statistics

**Example:**
```
Enter command: status
```

**Sample Output:**
```json
{
  "state": "running",
  "groups_monitored": 5,
  "messages_processed": 1234,
  "relevant_messages": 12,
  "uptime_seconds": 3600
}
```

#### `report`
Generate a detailed scanning report.

Includes:
- Summary of scanning activity
- List of relevant messages found
- Group-by-group statistics
- Keyword match details

**Example:**
```
Enter command: report
```

#### `list`
List all discovered Telegram groups.

Shows for each group:
- Group name
- Type (Channel/Megagroup/Group)
- Privacy (Public/Private)
- Username (if public)
- Member count
- Group ID

**Example:**
```
Enter command: list
```

**Sample Output:**
```
============================================================
DISCOVERED GROUPS (5 total)
============================================================
 1. КиберТопор
    Type: Megagroup (Public)
    Username: @cybertopor
    Members: 15,420
    ID: 1966291562

 2. Топор Live
    Type: Channel (Public)
    Username: @toporlive
    Members: 8,930
    ID: 1754252633
...
```

#### `config`
Show current configuration settings.

Displays:
- Selected groups to monitor
- Keywords to search for
- Scan interval
- Rate limiting settings
- Other configuration options

**Example:**
```
Enter command: config
```

**Sample Output:**
```json
{
  "scan_interval": 30,
  "max_history_days": 7,
  "selected_groups": ["КиберТопор", "Топор Live", "Рыбарь"],
  "keywords": ["менеджеры не справляются", "нужен умный бот"],
  "rate_limit_rpm": 30
}
```

### Configuration Commands

#### `reload`
Reload configuration from config.json file.
- Useful after making changes to config.json
- Does not restart the scanner
- New settings take effect immediately

**Example:**
```
Enter command: reload
```

### Help Commands

#### `help`
Show detailed help message with all available commands.
- Lists all commands with descriptions
- Shows configuration options
- Provides example workflow

**Example:**
```
Enter command: help
```

#### `quit` (or `exit`, `q`)
Exit the application.
- Stops all monitoring
- Closes connections
- Saves state

**Example:**
```
Enter command: quit
```

## Command Line Options

### Interactive Mode (Default)
```bash
python -m telegram_scanner.main
```
Starts the scanner in interactive mode where you can use all the commands above.

### Batch Mode
```bash
python -m telegram_scanner.main --batch
```
Runs the scanner in batch mode (non-interactive) indefinitely.

```bash
python -m telegram_scanner.main --batch --duration 60
```
Runs the scanner in batch mode for 60 minutes.

### Test Discovery
```bash
python -m telegram_scanner.main --test-discovery
```
Tests group discovery only without starting monitoring.

### Configuration File
```bash
python -m telegram_scanner.main --config custom.json
```
Uses a custom configuration file instead of config.json.

### Logging
```bash
python -m telegram_scanner.main --log-level DEBUG
```
Sets logging level (DEBUG, INFO, WARNING, ERROR).

```bash
python -m telegram_scanner.main --log-file scanner.log
```
Saves logs to a file.

## Example Workflows

### Basic Workflow
1. Start the scanner:
   ```
   python -m telegram_scanner.main
   ```

2. Begin scanning:
   ```
   Enter command: start
   ```

3. Check status:
   ```
   Enter command: status
   ```

4. View discovered groups:
   ```
   Enter command: list
   ```

5. Generate report:
   ```
   Enter command: report
   ```

6. Stop when done:
   ```
   Enter command: stop
   ```

7. Exit:
   ```
   Enter command: quit
   ```

### Configuration Change Workflow
1. Edit config.json (add new keywords or groups)

2. In running scanner, reload config:
   ```
   Enter command: reload
   ```

3. Restart scanning with new config:
   ```
   Enter command: stop
   Enter command: start
   ```

### Monitoring Workflow
1. Start scanner:
   ```
   Enter command: start
   ```

2. Let it run, periodically check status:
   ```
   Enter command: status
   ```

3. When you see relevant messages, generate report:
   ```
   Enter command: report
   ```

4. Continue monitoring or stop:
   ```
   Enter command: stop
   ```

## Configuration File (config.json)

Edit `config.json` to customize scanner behavior:

```json
{
  "api_credentials": {
    "api_id": "your_api_id",
    "api_hash": "your_api_hash"
  },
  "scanning": {
    "scan_interval": 30,
    "max_history_days": 7,
    "selected_groups": [
      "КиберТопор",
      "Топор Live",
      "Рыбарь",
      "КБ плюс",
      "artjockey"
    ]
  },
  "relevance": {
    "keywords": [
      "менеджеры не справляются",
      "нужен умный бот"
    ],
    "regex_patterns": [],
    "logic": "OR"
  },
  "rate_limiting": {
    "requests_per_minute": 30,
    "flood_wait_multiplier": 1.0,
    "default_delay": 1.5,
    "max_wait_time": 300.0
  }
}
```

### Configuration Options

- **scan_interval**: Seconds between scans (default: 30)
- **max_history_days**: Days of history to scan (default: 7)
- **selected_groups**: List of group names to monitor
- **keywords**: Keywords to search for in messages
- **regex_patterns**: Regular expressions for advanced matching
- **logic**: "OR" or "AND" for keyword matching
- **requests_per_minute**: API rate limit (default: 30)
- **default_delay**: Delay between requests in seconds (default: 1.5)
- **max_wait_time**: Maximum wait time for rate limiting (default: 300)

## Troubleshooting

### Session Lock Issues
If you get "database is locked" errors:
```bash
python fix_session_lock.py
```

### Authentication Issues
If authentication fails:
1. Delete session file: `del telegram_scanner.session`
2. Run scanner again and re-authenticate

### Rate Limiting
If you hit rate limits frequently:
1. Increase `default_delay` in config.json
2. Decrease `requests_per_minute`
3. Reduce number of `selected_groups`

## Tips

1. **Use `list` command** after starting to verify which groups were discovered
2. **Check `status` regularly** to monitor progress
3. **Generate `report` periodically** to see found messages
4. **Use `pause/resume`** instead of stop/start to avoid re-discovery
5. **Edit config.json and `reload`** to change settings without restarting
6. **Use `help` command** anytime you forget available commands

## Support

For more information, see:
- `README.md` - General overview
- `QUICK_START.md` - Quick start guide
- `API_CREDENTIALS_GUIDE.md` - How to get API credentials
- `SETUP_GUIDE.md` - Detailed setup instructions
