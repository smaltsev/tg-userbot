# Configuration Examples

This directory contains example configuration files for different use cases of the Telegram Group Scanner.

## Available Examples

### 1. Basic Configuration (`basic-config.json`)

A minimal configuration suitable for getting started:

- **Use case:** General purpose monitoring
- **Scan interval:** 30 seconds
- **Keywords:** "important", "urgent"
- **Rate limit:** 20 requests/minute

**Best for:** First-time users, general monitoring

### 2. Crypto Monitoring (`crypto-monitoring-config.json`)

Optimized for monitoring cryptocurrency-related groups:

- **Use case:** Cryptocurrency trading and news
- **Scan interval:** 15 seconds (high frequency)
- **Keywords:** Bitcoin, Ethereum, trading terms, market signals
- **Regex patterns:** Price patterns, percentage changes, trading pairs
- **Rate limit:** 15 requests/minute

**Best for:** Crypto traders, market analysis, trading signals

### 3. News Monitoring (`news-monitoring-config.json`)

Configured for monitoring news and current events:

- **Use case:** Breaking news, technology updates
- **Scan interval:** 60 seconds
- **Keywords:** Breaking news terms, tech industry, cybersecurity
- **Regex patterns:** Date formats, time stamps, executive titles
- **Rate limit:** 10 requests/minute (conservative)

**Best for:** Journalists, researchers, staying informed

### 4. High Frequency (`high-frequency-config.json`)

For real-time monitoring with minimal delay:

- **Use case:** Time-sensitive information
- **Scan interval:** 5 seconds (very high frequency)
- **Keywords:** Urgent terms, immediate actions
- **Regex patterns:** Time-sensitive patterns
- **Rate limit:** 30 requests/minute (aggressive)

**Best for:** Emergency monitoring, time-critical applications

**⚠️ Warning:** High frequency scanning may hit rate limits faster

### 5. Conservative (`conservative-config.json`)

Low-impact configuration for minimal API usage:

- **Use case:** Long-term monitoring with minimal resource usage
- **Scan interval:** 5 minutes (300 seconds)
- **Keywords:** Only official announcements
- **Logic:** AND (more restrictive)
- **Rate limit:** 5 requests/minute (very conservative)

**Best for:** Background monitoring, resource-constrained environments

## How to Use These Examples

### Method 1: Copy and Modify

1. Copy an example file to your main directory:
   ```bash
   cp examples/crypto-monitoring-config.json config.json
   ```

2. Edit the file to add your API credentials:
   ```json
   {
     "api_credentials": {
       "api_id": "YOUR_API_ID",
       "api_hash": "YOUR_API_HASH"
     }
   }
   ```

3. Run the scanner:
   ```bash
   telegram-scanner
   ```

### Method 2: Use Directly with --config

Run the scanner with a specific example configuration:

```bash
# First, add your credentials to the example file
telegram-scanner --config examples/crypto-monitoring-config.json
```

### Method 3: Create Multiple Configurations

Set up different configurations for different purposes:

```bash
# Copy and customize for different use cases
cp examples/crypto-monitoring-config.json crypto-config.json
cp examples/news-monitoring-config.json news-config.json

# Edit each file with your credentials and preferences
# Then run with specific configs:
telegram-scanner --config crypto-config.json
telegram-scanner --config news-config.json
```

## Customization Tips

### Keywords

Choose keywords relevant to your monitoring goals:

**For Trading:**
```json
"keywords": ["pump", "dump", "moon", "crash", "bull", "bear", "breakout"]
```

**For Tech News:**
```json
"keywords": ["launch", "release", "update", "vulnerability", "breach", "AI"]
```

**For General News:**
```json
"keywords": ["breaking", "developing", "confirmed", "official", "update"]
```

### Regex Patterns

Use regex patterns for structured data:

**Prices and Numbers:**
```json
"regex_patterns": [
  "\\$[0-9,]+",           // Dollar amounts: $1,000
  "\\b\\d+%\\b",          // Percentages: 15%
  "\\b\\d+\\.\\d+%\\b"    // Decimal percentages: 15.5%
]
```

**Dates and Times:**
```json
"regex_patterns": [
  "\\b\\d{1,2}/\\d{1,2}/\\d{4}\\b",     // Dates: 12/31/2024
  "\\b\\d{1,2}:\\d{2}\\s?(AM|PM)\\b"    // Times: 3:30 PM
]
```

**Cryptocurrency:**
```json
"regex_patterns": [
  "\\b[A-Z]{3,5}/[A-Z]{3,5}\\b",        // Trading pairs: BTC/USD
  "\\b(BTC|ETH|ADA|DOT)\\b"             // Specific coins
]
```

### Scan Intervals

Choose based on your needs and rate limits:

- **Real-time (5-15 seconds):** For time-critical monitoring
- **Frequent (30-60 seconds):** For active monitoring
- **Regular (2-5 minutes):** For general monitoring
- **Periodic (10+ minutes):** For background monitoring

### Rate Limiting

Balance between responsiveness and API limits:

- **Aggressive (30+ rpm):** For high-frequency monitoring
- **Standard (15-20 rpm):** For regular monitoring
- **Conservative (5-10 rpm):** For background monitoring

## Configuration Validation

Before using any configuration:

1. **Validate JSON syntax:**
   ```bash
   python -m json.tool config.json
   ```

2. **Test with dry run:**
   ```bash
   telegram-scanner --config your-config.json
   # Check authentication and group discovery
   ```

3. **Monitor rate limits:**
   - Start with conservative settings
   - Increase frequency gradually
   - Watch for FloodWaitError messages

## Troubleshooting Examples

### Common Issues:

**1. Rate Limiting:**
```
Error: FloodWaitError: Too many requests
```
**Solution:** Reduce `requests_per_minute` or increase `scan_interval`

**2. No Matches:**
```
Status: 0 relevant messages found
```
**Solution:** 
- Check if keywords are too specific
- Try changing logic from "AND" to "OR"
- Add more general keywords

**3. Too Many Matches:**
```
Status: 1000+ relevant messages found
```
**Solution:**
- Make keywords more specific
- Change logic from "OR" to "AND"
- Add more restrictive regex patterns

## Creating Custom Configurations

### Step 1: Start with a Base

Choose the example closest to your use case:

```bash
cp examples/basic-config.json my-custom-config.json
```

### Step 2: Customize Settings

Edit the configuration for your specific needs:

```json
{
  "api_credentials": {
    "api_id": "YOUR_API_ID",
    "api_hash": "YOUR_API_HASH"
  },
  "scanning": {
    "scan_interval": 30,
    "max_history_days": 7,
    "selected_groups": ["SpecificGroup1", "SpecificGroup2"]
  },
  "relevance": {
    "keywords": ["your", "custom", "keywords"],
    "regex_patterns": ["your\\s+regex\\s+patterns"],
    "logic": "OR"
  },
  "rate_limiting": {
    "requests_per_minute": 20,
    "flood_wait_multiplier": 1.5
  }
}
```

### Step 3: Test and Iterate

1. Test with a short duration:
   ```bash
   telegram-scanner --config my-custom-config.json --batch --duration 5
   ```

2. Check the results and adjust as needed

3. Run for longer periods once satisfied

## Best Practices

1. **Start Conservative:** Begin with lower scan frequencies and increase gradually
2. **Test Thoroughly:** Always test new configurations before long-term use
3. **Monitor Performance:** Keep an eye on rate limits and API usage
4. **Backup Configurations:** Keep copies of working configurations
5. **Document Changes:** Note what works for different use cases

## Support

If you need help with configurations:

1. Check the main [README.md](../README.md) for detailed documentation
2. Review [SETUP_GUIDE.md](../SETUP_GUIDE.md) for setup help
3. Validate your JSON syntax
4. Start with the basic example and customize gradually