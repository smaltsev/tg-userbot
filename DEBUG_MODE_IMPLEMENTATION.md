# Debug Mode Implementation Summary

## Overview
Added debug mode functionality to the Telegram Group Scanner that prints detailed console output for each message being processed.

## Changes Made

### 1. Configuration (`telegram_scanner/config.py`)
- Added `debug_mode: bool = False` field to `ScannerConfig` dataclass
- Updated `_create_default_config()` to include `debug_mode: false` in scanning section
- Updated `_flatten_config()` to read `debug_mode` from config file
- Updated `_structure_config()` to write `debug_mode` to config file

### 2. Filter (`telegram_scanner/filter.py`)
- Added `_last_matched_keywords` attribute to store matched keywords
- Updated `is_relevant()` method to store matched keywords in `_last_matched_keywords`
- This allows the scanner to retrieve which keywords matched for debug output

### 3. Scanner (`telegram_scanner/scanner.py`)
- Updated `handle_new_message()` method to print debug output when `debug_mode` is enabled
- Updated `scan_history()` method to print debug output for historical messages
- Debug output includes:
  - Message ID and metadata (group, sender, timestamp)
  - Message content (truncated to 200 chars)
  - Media type and extracted text (if applicable)
  - Relevance check results
  - Relevance score
  - Matched keywords

### 4. Configuration File (`config.json`)
- Added `"debug_mode": false` to the scanning section

### 5. Documentation
- Created `DEBUG_MODE.md` - Comprehensive guide on using debug mode
- Created `examples/debug-mode-config.json` - Example configuration with debug mode enabled
- Updated `examples/README.md` - Added debug mode example to the list
- Updated `COMMANDS.md` - Added debug_mode to configuration options

## Debug Output Format

When debug mode is enabled, each message prints:

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

## Usage

### Enable Debug Mode

Edit `config.json`:
```json
{
  "scanning": {
    "debug_mode": true
  }
}
```

### Run Scanner
```bash
python telegram_scanner/main.py
```

### Disable Debug Mode
Set `debug_mode` to `false` in config.json

## Use Cases

1. **Testing Keywords**: See which messages match your keywords in real-time
2. **Troubleshooting**: Understand why certain messages aren't matching
3. **Monitoring**: Watch the scanner process messages in real-time
4. **Development**: Debug relevance filtering logic

## Performance Impact

- Minimal performance impact
- Console output is fast
- No additional API calls
- May be overwhelming for high-volume groups (100+ messages/minute)

## Testing

All files compile without syntax errors:
```bash
python -m py_compile telegram_scanner/config.py telegram_scanner/filter.py telegram_scanner/scanner.py
```

## Files Modified

1. `telegram_scanner/config.py` - Added debug_mode configuration
2. `telegram_scanner/filter.py` - Store matched keywords
3. `telegram_scanner/scanner.py` - Print debug output
4. `config.json` - Added debug_mode setting

## Files Created

1. `DEBUG_MODE.md` - User documentation
2. `examples/debug-mode-config.json` - Example configuration
3. `DEBUG_MODE_IMPLEMENTATION.md` - This file

## Files Updated

1. `examples/README.md` - Added debug mode example
2. `COMMANDS.md` - Added debug_mode to configuration options

## Backward Compatibility

- Default value is `false`, so existing configurations work without changes
- If `debug_mode` is missing from config, it defaults to `false`
- No breaking changes to existing functionality

## Next Steps

Users can now:
1. Enable debug mode in their config.json
2. Run the scanner and see detailed output for each message
3. Use debug output to test and refine their keyword configurations
4. Troubleshoot relevance filtering issues
