# Debug Mode

## Overview

Debug mode provides detailed console output for every message being processed by the scanner. This is useful for:
- Understanding what messages are being scanned
- Troubleshooting relevance filtering
- Verifying keyword matching
- Monitoring scanner behavior in real-time

## Enabling Debug Mode

Edit your `config.json` file and set `debug_mode` to `true`:

```json
{
  "scanning": {
    "scan_interval": 30,
    "max_history_days": 1,
    "selected_groups": [],
    "debug_mode": true
  }
}
```

## Debug Output Format

When debug mode is enabled, each message will be printed to the console with the following information:

```
================================================================================
DEBUG: Processing Message 12345
================================================================================
Group: Example Group (ID: 1234567890)
Sender: username (ID: 987654321)
Timestamp: 2026-01-20 17:45:30
Content: This is the message content...
Media Type: photo
Extracted Text: Text extracted from image...

Relevance Check:
  Is Relevant: True
  Relevance Score: 0.50
  Matched Keywords: keyword1, keyword2
================================================================================
```

## Output Fields

- **Message ID**: Unique identifier for the message
- **Group**: Name and ID of the group/channel
- **Sender**: Username and ID of the message sender
- **Timestamp**: When the message was sent
- **Content**: Message text (truncated to 200 characters if longer)
- **Media Type**: Type of media attached (photo, video, document, etc.)
- **Extracted Text**: Text extracted from images via OCR (if applicable)
- **Is Relevant**: Whether the message matches your keywords/patterns
- **Relevance Score**: Score from 0.0 to 1.0 indicating match strength
- **Matched Keywords**: List of keywords/patterns that matched

## Use Cases

### 1. Testing Keyword Configuration

Enable debug mode to see which messages match your keywords:

```json
"relevance": {
  "keywords": ["маркетолог", "нужен"],
  "logic": "OR"
}
```

Run the scanner and watch the console to see which messages match.

### 2. Troubleshooting False Negatives

If you expect certain messages to match but they don't:
1. Enable debug mode
2. Run historical scan
3. Check the "Matched Keywords" field to see why messages aren't matching

### 3. Monitoring Real-Time Scanning

During real-time monitoring, debug mode shows each incoming message as it's processed, helping you verify the scanner is working correctly.

### 4. Performance Analysis

Debug output includes timestamps, allowing you to measure processing speed and identify bottlenecks.

## Performance Impact

Debug mode has minimal performance impact:
- Console output is fast
- Only active when messages are being processed
- No additional API calls or processing

However, for very high-volume groups (100+ messages/minute), the console output may become overwhelming.

## Disabling Debug Mode

To disable debug mode, set it to `false` in `config.json`:

```json
{
  "scanning": {
    "debug_mode": false
  }
}
```

Or use the `config` command in the interactive interface:

```
Enter command: config
Current configuration:
{
  "scanning": {
    "debug_mode": false
  }
}
```

## Tips

1. **Use with Historical Scan**: Enable debug mode before running historical scan to see all messages from the past N days
2. **Redirect Output**: Save debug output to a file for later analysis:
   ```
   python telegram_scanner/main.py > debug_output.txt 2>&1
   ```
3. **Combine with Logging**: Debug mode works alongside the normal logging system (scanner.log)
4. **Test Keywords**: Use debug mode to test new keywords before committing to long-term monitoring

## Example Session

```
$ python telegram_scanner/main.py

Welcome to Telegram Group Scanner!
Available commands: start, stop, status, report, list, help, config, exit

Enter command: start
Starting scanner...

================================================================================
DEBUG: Processing Historical Message 14936
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

Relevant message found: 14936 from Marketing Jobs
```

## Troubleshooting

If debug mode is enabled but you're not seeing output:

1. **Check `max_history_days`**: If set to 0, no historical messages will be scanned
2. **Verify keywords match**: Use `status` command to check if any messages are being found
3. **Restart scanner**: Stop and restart after changing config
4. **Check message count**: Run `status` to see if `messages_processed` is increasing

See [DEBUG_MODE_TROUBLESHOOTING.md](DEBUG_MODE_TROUBLESHOOTING.md) for detailed troubleshooting steps.

## Related Documentation

- [COMMANDS.md](COMMANDS.md) - Interactive command reference
- [SCANNING_EXPLAINED.md](SCANNING_EXPLAINED.md) - How scanning works
- [QUICK_START.md](QUICK_START.md) - Getting started guide
