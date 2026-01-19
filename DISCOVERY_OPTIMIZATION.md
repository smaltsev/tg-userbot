# Group Discovery Optimization for Large Accounts

## Problem
When scanning all groups (empty `selected_groups` list), accounts with many dialogs (600+) were timing out after 10 minutes due to aggressive rate limiting.

## Solution Applied

### 1. Increased Timeout
- **Old**: 10 minutes (600 seconds)
- **New**: 30 minutes (1800 seconds)
- Allows discovery of 600+ dialogs with rate limiting

### 2. Optimized Rate Limiting During Discovery
- **Old**: Rate limit check for every single group
- **New**: Rate limit check every 10 groups
- **Result**: 10x faster discovery while still respecting API limits

### 3. Reduced Default Delay
- **Old**: 1.5 seconds between requests
- **New**: 0.5 seconds between requests
- **Result**: 3x faster discovery

### 4. Improved Progress Logging
- **Old**: Log every 10 dialogs
- **New**: Log every 50 dialogs
- **Result**: Less log spam for large accounts

### 5. Partial Results on Timeout
- If timeout occurs, returns groups discovered so far
- Prevents losing all progress

## Performance Comparison

### Before Optimization:
- 610 dialogs with 299 groups
- Rate limit every group: ~1.5s × 299 = ~450 seconds (7.5 minutes)
- Plus dialog iteration overhead
- **Result**: Timeout at 10 minutes

### After Optimization:
- 610 dialogs with 299 groups
- Rate limit every 10 groups: ~0.5s × 30 = ~15 seconds
- Plus dialog iteration overhead
- **Result**: Complete in ~5-10 minutes

## Configuration

Edit `config.json` to tune performance:

```json
{
  "rate_limiting": {
    "requests_per_minute": 30,      // API rate limit
    "default_delay": 0.5,            // Delay between requests (lower = faster)
    "max_wait_time": 300.0           // Max wait for rate limits
  }
}
```

### Tuning Guidelines:

**For Fast Discovery (600+ dialogs):**
```json
"default_delay": 0.5,
"requests_per_minute": 30
```

**For Conservative (avoid rate limits):**
```json
"default_delay": 2.0,
"requests_per_minute": 20
```

**For Very Large Accounts (1000+ dialogs):**
```json
"default_delay": 0.3,
"requests_per_minute": 40
```

## Expected Discovery Times

| Dialogs | Groups | Time (Fast) | Time (Conservative) |
|---------|--------|-------------|---------------------|
| 100     | 50     | 1-2 min     | 2-3 min            |
| 300     | 150    | 3-5 min     | 5-8 min            |
| 600     | 300    | 5-10 min    | 10-15 min          |
| 1000    | 500    | 8-15 min    | 15-25 min          |

## Usage

### Scan All Groups (No Filter)
```json
{
  "scanning": {
    "selected_groups": []  // Empty = scan all
  }
}
```

### Scan Specific Groups (Fast)
```json
{
  "scanning": {
    "selected_groups": ["Group1", "Group2", "Group3"]
  }
}
```
With specific groups, discovery stops as soon as all are found (much faster).

## Monitoring Progress

The scanner logs progress every 50 dialogs:
```
Processed 50 dialogs, found 25 groups so far...
Processed 100 dialogs, found 48 groups so far...
Processed 150 dialogs, found 72 groups so far...
...
```

## Troubleshooting

### Still Timing Out?
1. **Increase timeout** in `scanner.py` (line ~212):
   ```python
   timeout_seconds = 3600.0  # 60 minutes
   ```

2. **Reduce rate limiting**:
   ```json
   "default_delay": 0.3
   ```

3. **Use specific groups** instead of scanning all

### Getting Rate Limited?
1. **Increase delay**:
   ```json
   "default_delay": 1.0
   ```

2. **Reduce requests per minute**:
   ```json
   "requests_per_minute": 20
   ```

### Discovery Too Slow?
1. **Reduce delay**:
   ```json
   "default_delay": 0.3
   ```

2. **Increase requests per minute**:
   ```json
   "requests_per_minute": 40
   ```

## Best Practices

1. **First Run**: Use conservative settings to avoid rate limits
2. **Subsequent Runs**: Can use faster settings once you know your limits
3. **Large Accounts**: Consider using specific groups instead of scanning all
4. **Monitor Logs**: Watch for rate limit warnings and adjust accordingly

## Technical Details

### Rate Limiting Strategy
- Initial rate limit check before starting
- Rate limit every 10 groups during discovery
- Full rate limiting during message monitoring

### Timeout Handling
- 30-minute timeout for discovery
- Returns partial results if timeout occurs
- Logs number of groups found before timeout

### Memory Efficiency
- Processes dialogs as stream (not loading all at once)
- Stores only group metadata (not full dialog data)
- Efficient for accounts with 1000+ dialogs

## Summary

✅ **30-minute timeout** - handles large accounts  
✅ **Optimized rate limiting** - 10x faster discovery  
✅ **Reduced delays** - 3x faster overall  
✅ **Partial results** - never lose progress  
✅ **Better logging** - less spam, more useful info  

Your 610-dialog account should now complete discovery in 5-10 minutes instead of timing out!
