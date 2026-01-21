# Telegram Group Scanner

A production-ready Python application for monitoring Telegram groups and extracting relevant information in real-time.

## Features

- 🔐 **Secure Authentication** - User-based Telegram API authentication
- 🔍 **Smart Discovery** - Automatic group discovery with caching
- ⚡ **Real-Time Monitoring** - Event-driven message processing
- 🎯 **Intelligent Filtering** - Keyword and regex-based relevance detection
- 💾 **Data Management** - JSON storage with duplicate detection
- 🛡️ **Error Resilience** - Comprehensive error handling and retry logic
- 🎮 **Interactive Control** - Command-line interface for live management
- 📊 **OCR Support** - Text extraction from images using Tesseract
- 🤖 **AI Responder** - Automated intelligent responses using OpenAI or ProxyAPI

---

## Quick Start

### 1. Installation

```bash
# Clone repository
git clone <repository-url>
cd telegram-group-scanner

# Install dependencies
pip install -r requirements.txt

# Install Tesseract OCR
# Ubuntu/Debian: sudo apt-get install tesseract-ocr
# macOS: brew install tesseract
# Windows: Download from https://github.com/UB-Mannheim/tesseract/wiki
```

### 2. Get Telegram API Credentials

1. Go to https://my.telegram.org/auth
2. Log in with your phone number
3. Click "API development tools"
4. Create a new application
5. Copy your `api_id` and `api_hash`

### 3. Configure

Edit `config.json`:

```json
{
  "api_credentials": {
    "api_id": "YOUR_API_ID",
    "api_hash": "YOUR_API_HASH"
  },
  "scanning": {
    "scan_interval": 30,
    "max_history_days": 7,
    "selected_groups": ["GroupName1", "GroupName2"],
    "debug_mode": false
  },
  "relevance": {
    "keywords": ["urgent", "important", "breaking"],
    "regex_patterns": [],
    "logic": "OR"
  },
  "rate_limiting": {
    "requests_per_minute": 30,
    "flood_wait_multiplier": 1.0,
    "default_delay": 0.5,
    "max_wait_time": 300.0
  },
  "ai_responder": {
    "enabled": false,
    "provider": "proxyapi",
    "api_url": "https://api.proxyapi.ru/openai/v1/chat/completions",
    "api_key": "YOUR_API_KEY",
    "model": "gpt-3.5-turbo",
    "temperature": 0.7,
    "max_tokens": 500,
    "system_prompt": "You are a helpful assistant responding to Telegram messages.",
    "prompt_template": "Message from {sender_username} in {group_name}:\n{message_content}\n\nGenerate an appropriate response:",
    "cache_responses": true,
    "auto_respond": false
  }
}
```

### 4. Run

```bash
python -m telegram_scanner.cli
```

---

## Usage

### Interactive Mode

```bash
python -m telegram_scanner.cli
```

**Available Commands:**
- `start` - Start scanning and monitoring
- `stop` - Stop scanning
- `scan` - Re-discover groups (clears cache)
- `pause` - Pause monitoring
- `resume` - Resume monitoring
- `status` - Show current status
- `report` - Generate scanning report
- `list` - List discovered groups
- `config` - Show configuration
- `reload` - Reload configuration
- `help` - Show help
- `quit` - Exit application

### Batch Mode

```bash
# Run indefinitely
python -m telegram_scanner.cli --batch

# Run for specific duration (minutes)
python -m telegram_scanner.cli --batch --duration 60

# Test group discovery only
python -m telegram_scanner.cli --test-discovery
```

---

## Configuration Reference

### API Credentials

```json
{
  "api_credentials": {
    "api_id": "12345678",
    "api_hash": "abcdef1234567890abcdef1234567890"
  }
}
```

**Required:** Get from https://my.telegram.org/auth

### Scanning Options

```json
{
  "scanning": {
    "scan_interval": 30,
    "max_history_days": 7,
    "selected_groups": [],
    "debug_mode": false
  }
}
```

- **scan_interval**: Seconds between scans (not used in real-time mode)
- **max_history_days**: Days of history to scan on startup (0 = skip historical scan)
- **selected_groups**: List of group names to monitor (empty = all groups)
- **debug_mode**: Enable detailed logging

### Relevance Filtering

```json
{
  "relevance": {
    "keywords": ["urgent", "breaking", "alert"],
    "regex_patterns": ["\\d{4}-\\d{2}-\\d{2}"],
    "logic": "OR"
  }
}
```

- **keywords**: List of keywords to match (case-insensitive)
- **regex_patterns**: List of regex patterns
- **logic**: "OR" (any match) or "AND" (all must match)

### Rate Limiting

```json
{
  "rate_limiting": {
    "requests_per_minute": 30,
    "flood_wait_multiplier": 1.0,
    "default_delay": 0.5,
    "max_wait_time": 300.0
  }
}
```

- **requests_per_minute**: Max API requests per minute
- **flood_wait_multiplier**: Multiplier for Telegram flood wait
- **default_delay**: Delay between requests (seconds)
- **max_wait_time**: Maximum wait time for rate limiting (seconds)

### AI Responder

```json
{
  "ai_responder": {
    "enabled": false,
    "provider": "proxyapi",
    "api_url": "https://api.proxyapi.ru/openai/v1/chat/completions",
    "api_key": "YOUR_API_KEY",
    "model": "gpt-3.5-turbo",
    "temperature": 0.7,
    "max_tokens": 500,
    "system_prompt": "You are a helpful assistant responding to Telegram messages.",
    "prompt_template": "Message from {sender_username} in {group_name}:\n{message_content}\n\nGenerate an appropriate response:",
    "cache_responses": true,
    "auto_respond": false
  }
}
```

- **enabled**: Enable/disable AI responder
- **provider**: "openai" or "proxyapi"
- **api_url**: API endpoint URL
- **api_key**: Your API key
- **model**: AI model to use (e.g., "gpt-3.5-turbo", "gpt-4")
- **temperature**: Response creativity (0.0-1.0)
- **max_tokens**: Maximum response length
- **system_prompt**: System instructions for the AI
- **prompt_template**: Template for user prompts (supports placeholders: {message_content}, {sender_username}, {group_name}, {extracted_text}, {timestamp}, {context})
- **cache_responses**: Cache responses to reduce API calls
- **auto_respond**: Automatically respond to relevant messages

**Providers:**

**OpenAI:**
```json
{
  "provider": "openai",
  "api_url": "https://api.openai.com/v1/chat/completions",
  "api_key": "sk-..."
}
```

**ProxyAPI (Russian):**
```json
{
  "provider": "proxyapi",
  "api_url": "https://api.proxyapi.ru/openai/v1/chat/completions",
  "api_key": "YOUR_PROXYAPI_KEY"
}
```

**Response Behavior:**
- Tries to reply in the group first
- Falls back to private message if group posting is restricted
- Handles permissions errors gracefully
- Caches responses to avoid duplicate API calls

---

## Features in Detail

### Real-Time Monitoring

The scanner uses Telegram's event system to detect new messages instantly:

1. Registers event handlers for monitored groups
2. Processes messages in background workers
3. Applies relevance filters
4. Stores matching messages
5. Updates statistics in real-time

**Performance:**
- Message detection: 1-2 seconds
- Concurrent processing: 3 workers
- Non-blocking: Interactive commands work while monitoring

### Group Discovery

Automatically discovers accessible groups:

1. Loads cached groups (if available)
2. Discovers new groups from dialogs
3. Filters by selected groups (if configured)
4. Caches results for fast startup

**Cache Management:**
- Groups cached in `discovered_groups.json`
- Use `scan` command to refresh
- Automatic on first run

### Historical Scanning

Scans past messages on startup:

```json
{
  "scanning": {
    "max_history_days": 7
  }
}
```

**Skip Historical Scan:**
Set `max_history_days: 0` to only monitor new messages (faster startup).

### AI-Powered Responses

Automatically generate and send intelligent responses to relevant messages:

**Features:**
- Support for OpenAI and ProxyAPI
- Custom system prompts and templates
- Response caching to reduce API costs
- Automatic fallback to private messages
- Context-aware responses

**How it works:**
1. Scanner detects relevant message
2. AI generates appropriate response
3. Tries to reply in group
4. Falls back to private message if restricted
5. Caches response to avoid duplicates

**Enable AI Responder:**
```json
{
  "ai_responder": {
    "enabled": true,
    "auto_respond": true,
    "provider": "proxyapi",
    "api_key": "YOUR_KEY"
  }
}
```

**Custom Prompts:**
```json
{
  "system_prompt": "Ты профессиональный маркетолог. Отвечай кратко и по делу.",
  "prompt_template": "Сообщение от {sender_username}:\n{message_content}\n\nОтветь профессионально:"
}
```

**Placeholders:**
- `{message_content}` - Message text
- `{sender_username}` - Sender's username
- `{group_name}` - Group name
- `{extracted_text}` - Text from images
- `{timestamp}` - Message timestamp
- `{context}` - Previous messages

### Data Storage

Messages stored in `telegram_scanner_data.json`:

```json
{
  "id": 12345,
  "timestamp": "2026-01-21T10:30:00",
  "group_id": 67890,
  "group_name": "Example Group",
  "sender_id": 11111,
  "sender_username": "user123",
  "content": "Message text",
  "media_type": "photo",
  "extracted_text": "Text from image",
  "relevance_score": 0.75,
  "matched_criteria": ["urgent", "breaking"]
}
```

**Features:**
- Automatic duplicate detection
- Export to JSON, CSV, or TXT
- Statistics tracking

---

## Troubleshooting

### Authentication Issues

**Problem:** "Authentication required"

**Solution:**
1. Verify API credentials in config.json
2. Delete `telegram_scanner.session` file
3. Restart and re-authenticate

### No Messages Detected

**Problem:** Real-time monitoring not working

**Checklist:**
1. ✅ Check `status` - should show "running"
2. ✅ Verify groups with `list` command
3. ✅ Check keywords match your test messages
4. ✅ Look for worker startup in logs
5. ✅ Ensure `max_history_days` is not 0 if you want historical scan

**Expected Logs:**
```
Real-time monitoring started with 3 processing workers
Monitoring task is now running in background
Client monitoring task started - listening for new messages
Message processing worker worker-0 started
Message processing worker worker-1 started
Message processing worker worker-2 started
```

### Rate Limiting

**Problem:** "FloodWaitError" or slow performance

**Solution:**
1. Increase `default_delay` in config
2. Decrease `requests_per_minute`
3. Wait for rate limit to reset

### Database Locked

**Problem:** "database is locked" error

**Solution:**
1. Close other instances of the scanner
2. Delete `telegram_scanner.session-journal` file
3. Restart the scanner

---

## Debug Mode

Enable detailed logging:

```json
{
  "scanning": {
    "debug_mode": true
  }
}
```

**Output:**
```
================================================================================
DEBUG: Processing Message 12345
================================================================================
Group: Example Group (ID: 67890)
Sender: user123 (ID: 11111)
Timestamp: 2026-01-21 10:30:00
Content: Message text here...

Relevance Check:
  Is Relevant: True
  Relevance Score: 0.75
  Matched Keywords: urgent, breaking
================================================================================
```

---

## Production Deployment

### Environment Variables

For production, use environment variables instead of config.json:

```bash
export TELEGRAM_API_ID="12345678"
export TELEGRAM_API_HASH="abcdef1234567890"
export TELEGRAM_KEYWORDS="urgent,breaking,alert"
```

### Systemd Service (Linux)

Create `/etc/systemd/system/telegram-scanner.service`:

```ini
[Unit]
Description=Telegram Group Scanner
After=network.target

[Service]
Type=simple
User=telegram
WorkingDirectory=/opt/telegram-scanner
ExecStart=/usr/bin/python3 -m telegram_scanner.cli --batch
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable telegram-scanner
sudo systemctl start telegram-scanner
sudo systemctl status telegram-scanner
```

### Docker

```dockerfile
FROM python:3.11-slim

# Install Tesseract
RUN apt-get update && apt-get install -y tesseract-ocr && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY telegram_scanner /app/telegram_scanner
COPY config.json /app/
WORKDIR /app

# Run
CMD ["python", "-m", "telegram_scanner.cli", "--batch"]
```

Build and run:
```bash
docker build -t telegram-scanner .
docker run -d --name scanner -v $(pwd)/config.json:/app/config.json telegram-scanner
```

---

## Security Best Practices

1. **Never commit credentials** - Use `.gitignore` for config.json
2. **Restrict session file permissions** - Automatically set to 0600
3. **Use environment variables** - For production deployments
4. **Rotate API credentials** - Regularly update your API keys
5. **Monitor account activity** - Check for unusual Telegram activity
6. **Limit group access** - Only monitor necessary groups
7. **Secure storage** - Protect `telegram_scanner_data.json`

---

## Performance Tips

1. **Skip historical scan** - Set `max_history_days: 0` for faster startup
2. **Limit groups** - Use `selected_groups` to monitor specific groups only
3. **Optimize keywords** - Use specific keywords to reduce false positives
4. **Adjust rate limits** - Balance speed vs. API limits
5. **Use batch mode** - For unattended operation
6. **Monitor resources** - Check CPU/memory usage with large groups

---

## Project Structure

```
telegram-group-scanner/
├── telegram_scanner/
│   ├── __init__.py
│   ├── main.py              # Application entry point
│   ├── cli.py               # CLI interface
│   ├── auth.py              # Authentication management
│   ├── scanner.py           # Group scanning and monitoring
│   ├── processor.py         # Message processing
│   ├── filter.py            # Relevance filtering
│   ├── storage.py           # Data storage
│   ├── config.py            # Configuration management
│   ├── command_interface.py # Interactive commands
│   ├── error_handling.py    # Error handling utilities
│   └── models.py            # Data models
├── examples/
│   ├── basic-config.json
│   ├── high-frequency-config.json
│   └── news-monitoring-config.json
├── config.json              # Main configuration
├── requirements.txt         # Python dependencies
├── setup.py                 # Package setup
├── .gitignore              # Git ignore rules
└── README.md               # This file
```

---

## Requirements

- Python 3.8+
- Tesseract OCR
- Active Telegram account
- Telegram API credentials

**Python Dependencies:**
- telethon >= 1.30.0
- aiohttp >= 3.9.0
- Pillow >= 10.0.0
- pytesseract >= 0.3.10
- python-dateutil >= 2.8.2

---

## License

MIT License - See LICENSE file for details

---

## Support

**Logs:** Check `scanner.log` for detailed error messages

**Issues:** Common issues and solutions in Troubleshooting section above

**Configuration:** All options documented in Configuration Reference

---

## Changelog

### Version 1.0.0 (2026-01-21)

**Features:**
- ✅ Real-time message monitoring
- ✅ Group discovery with caching
- ✅ Keyword and regex filtering
- ✅ OCR text extraction
- ✅ Interactive command interface
- ✅ Batch mode operation
- ✅ Comprehensive error handling
- ✅ Rate limiting and retry logic
- ✅ Data export (JSON, CSV, TXT)
- ✅ Statistics and reporting
- ✅ AI-powered responses (OpenAI/ProxyAPI)
- ✅ Automatic response fallback (group → private message)

**Bug Fixes:**
- ✅ Fixed blocking input preventing real-time monitoring
- ✅ Fixed race conditions in group discovery
- ✅ Fixed memory leaks in error handler
- ✅ Fixed session file security
- ✅ Fixed syntax errors

**Improvements:**
- ✅ Skip historical scan option (max_history_days: 0)
- ✅ Thread-safe operations
- ✅ Better logging and debug mode
- ✅ Production-ready deployment options
- ✅ AI response caching
- ✅ Custom prompt templates

---

## Quick Reference

**Start monitoring:**
```bash
python -m telegram_scanner.cli
> start
```

**Check status:**
```bash
> status
```

**View found messages:**
```bash
> report
```

**Stop and exit:**
```bash
> stop
> quit
```

---

**Status:** ✅ Production Ready  
**Version:** 1.0.0  
**Last Updated:** 2026-01-21
