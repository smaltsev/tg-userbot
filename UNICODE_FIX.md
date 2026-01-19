# Unicode Character Display Fix

## Problem
Russian/Cyrillic characters were being escaped in console output:
```
"group_name": "wfm, \u0430\u0440\u0433\u0443\u0441 \u0438 \u043f\u0440\u043e\u0447\u0438\u0435"
```

Instead of readable text:
```
"group_name": "wfm, аргус и прочие"
```

## Root Cause
Python's `json.dumps()` by default uses `ensure_ascii=True`, which escapes all non-ASCII characters (including Cyrillic).

## Solution Applied

Added `ensure_ascii=False` parameter to all `json.dumps()` calls in the codebase.

### Files Modified:

1. **telegram_scanner/main.py**
   - `status` command output
   - `report` command output
   - `config` command output

2. **telegram_scanner/storage.py** (already had the fix)
   - Message storage
   - Export functionality

3. **telegram_scanner/config.py** (already had the fix)
   - Configuration saving
   - Default config creation

## Before and After

### Before (Escaped):
```json
{
  "group_name": "\u041a\u0438\u0431\u0435\u0440\u0422\u043e\u043f\u043e\u0440",
  "message": "\u041d\u0443\u0436\u0435\u043d \u043c\u0430\u0440\u043a\u0435\u0442\u043e\u043b\u043e\u0433",
  "keywords": [
    "\u043c\u0435\u043d\u0435\u0434\u0436\u0435\u0440\u044b \u043d\u0435 \u0441\u043f\u0440\u0430\u0432\u043b\u044f\u044e\u0442\u0441\u044f"
  ]
}
```

### After (Readable):
```json
{
  "group_name": "КиберТопор",
  "message": "Нужен маркетолог",
  "keywords": [
    "менеджеры не справляются"
  ]
}
```

## Commands Affected

All interactive mode commands that display JSON now show readable Unicode:

- `status` - Shows status with readable group names
- `report` - Shows report with readable messages
- `config` - Shows configuration with readable keywords
- `list` - Already used direct printing (not affected)

## Testing

Run the scanner and use any command:
```bash
python -m telegram_scanner.main

Enter command: config
# Will now show:
{
  "keywords": [
    "Нужен маркетолог-практик",
    "нужен маркетолог"
  ],
  "selected_groups": []
}
```

## Technical Details

### Python json.dumps() Parameters:
```python
# Old (escaped Unicode)
json.dumps(data, indent=2)

# New (readable Unicode)
json.dumps(data, indent=2, ensure_ascii=False)
```

### Why ensure_ascii=False is Safe:
- Modern terminals support UTF-8
- Files are opened with `encoding='utf-8'`
- JSON specification allows Unicode characters
- Better readability for international users

## Additional Benefits

1. **Smaller JSON files** - No escape sequences
2. **Better readability** - Native characters
3. **Easier debugging** - Can read logs directly
4. **International support** - Works with any language

## Compatibility

✅ Windows (with UTF-8 console)  
✅ Linux (native UTF-8 support)  
✅ macOS (native UTF-8 support)  
✅ All modern terminals  

## Summary

✅ All `json.dumps()` calls now use `ensure_ascii=False`  
✅ Russian/Cyrillic text displays correctly  
✅ No more escaped Unicode sequences  
✅ Better readability in console and logs  
✅ Smaller file sizes  

The scanner now properly displays all Unicode characters including Russian, Cyrillic, and other international text!
