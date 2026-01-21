# Telegram Group Scanner

A Python application for monitoring Telegram groups and extracting relevant information using the Telethon library. The scanner authenticates as a user, discovers accessible groups, and monitors messages in real-time to identify and extract content matching specified criteria.

## Features

- **User Authentication**: Secure authentication with Telegram API using user credentials
- **Group Discovery**: Automatic discovery and monitoring of accessible Telegram groups
- **Real-time Processing**: Live message monitoring with event-driven architecture
- **Content Extraction**: Text extraction from messages and OCR from images
- **Smart Filtering**: Configurable relevance filtering with keywords and regex patterns
- **Data Management**: JSON-based storage with duplicate detection and export capabilities
- **Error Resilience**: Robust error handling, rate limiting, and automatic retry mechanisms
- **Interactive Control**: Command-line interface for real-time control and monitoring

## Table of Contents

- [Installation](#installation)
- [Getting Telegram API Credentials](#getting-telegram-api-credentials)
- [Configuration](#configuration)
- [Usage](#usage)
- [Command Reference](#command-reference)
- [Configuration Reference](#configuration-reference)
- [Examples](#examples)
- [Troubleshooting](#troubleshooting)
- [Development](#development)
- [License](#license)

## Installation

### Prerequisites

- Python 3.8 or higher
- Tesseract OCR (for image text extraction)

### Install Tesseract OCR

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install tesseract-ocr
```

**macOS:**
```bash
brew install tesseract
```

**Windows:**
Download and install from: https://github.com/UB-Mannheim/tesseract/wiki

### Install the Scanner

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd telegram-group-scanner
   ```

2. **Create a virtual environment (recommended):**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Install the package:**
   ```bash
   pip install -e .
   ```

## Getting Telegram API Credentials

Before using the scanner, you need to obtain Telegram API credentials:

1. **Visit the Telegram API Development Tools:**
   Go to https://my.telegram.org/apps

2. **Log in with your Telegram account:**
   Use your phone number and verification code

3. **Create a new application:**
   - App title: "Telegram Group Scanner" (or any name you prefer)
   - Short name: "scanner" (or any short identifier)
   - Platform: Choose "Desktop"
   - Description: Optional

4. **Save your credentials:**
   - **API ID**: A numeric identifier (e.g., 1234567)
   - **API Hash**: A string hash (e.g., "abcdef1234567890abcdef1234567890")

⚠️ **Important**: Keep these credentials secure and never share them publicly.

## Configuration

### Initial Setup

On first run, the scanner creates a default configuration file at `config.json`. You must update this file with your API credentials before the scanner can function.

### Configuration File Structure

The configuration file uses a nested JSON structure:

```json
{
  "api_credentials": {
    "api_id": "your_api_id_here",
    "api_hash": "your_api_hash_here"
  },
  "scanning": {
    "scan_interval": 30,
    "max_history_days": 7,
    "selected_groups": []
  },
  "relevance": {
    "keywords": ["important", "urgent"],
    "regex_patterns": [],
    "logic": "OR"
  },
  "rate_limiting": {
    "requests_per_minute": 20,
    "flood_wait_multiplier": 1.5
  }
}
```

## Usage

### Interactive Mode (Default)

Start the scanner in interactive mode for real-time control:

```bash
telegram-scanner
```

Or using Python module:

```bash
python -m telegram_scanner.main
```

### Batch Mode

Run the scanner in batch mode for automated operation:

```bash
# Run indefinitely
telegram-scanner --batch

# Run for specific duration (60 minutes)
telegram-scanner --batch --duration 60
```

### Custom Configuration

Use a custom configuration file:

```bash
telegram-scanner --config /path/to/custom-config.json
```

### Logging Options

Control logging level and output:

```bash
# Debug logging to console
telegram-scanner --log-level DEBUG

# Log to file
telegram-scanner --log-file scanner.log

# Both console and file with custom level
telegram-scanner --log-level INFO --log-file scanner.log
```

## Command Reference

### Command Line Arguments

| Argument | Short | Description | Default |
|----------|-------|-------------|---------|
| `--config` | `-c` | Configuration file path | `config.json` |
| `--batch` | `-b` | Run in batch mode (non-interactive) | Interactive mode |
| `--duration` | `-d` | Duration in minutes for batch mode | Run indefinitely |
| `--log-level` | `-l` | Logging level (DEBUG/INFO/WARNING/ERROR) | `INFO` |
| `--log-file` | `-f` | Log file path | Console only |
| `--version` | `-v` | Show version information | - |
| `--help` | `-h` | Show help message | - |

### Interactive Commands

When running in interactive mode, use these commands:

| Command | Description |
|---------|-------------|
| `start` | Start scanning groups |
| `stop` | Stop scanning |
| `pause` | Pause scanning (can be resumed) |
| `resume` | Resume paused scanning |
| `status` | Show current status and statistics |
| `report` | Generate detailed scanning report |
| `config` | Display current configuration |
| `reload` | Reload configuration from file |
| `quit` | Exit application |

## Configuration Reference

### API Credentials

```json
"api_credentials": {
  "api_id": "1234567",
  "api_hash": "abcdef1234567890abcdef1234567890"
}
```

- **api_id**: Your Telegram API ID (numeric)
- **api_hash**: Your Telegram API hash (string)

### Scanning Settings

```json
"scanning": {
  "scan_interval": 30,
  "max_history_days": 7,
  "selected_groups": ["group1", "group2"]
}
```

- **scan_interval**: Seconds between scans (default: 30)
- **max_history_days**: Days of message history to scan (default: 7)
- **selected_groups**: Specific groups to monitor (empty = all accessible groups)

### Relevance Filtering

```json
"relevance": {
  "keywords": ["important", "urgent", "breaking"],
  "regex_patterns": ["\\d{4}-\\d{2}-\\d{2}", "USD \\$\\d+"],
  "logic": "OR"
}
```

- **keywords**: List of keywords to match (case-insensitive)
- **regex_patterns**: Regular expression patterns for advanced matching
- **logic**: Logical operator for multiple criteria ("OR" or "AND")

### Rate Limiting

```json
"rate_limiting": {
  "requests_per_minute": 20,
  "flood_wait_multiplier": 1.5
}
```

- **requests_per_minute**: Maximum API requests per minute (default: 20)
- **flood_wait_multiplier**: Multiplier for Telegram's flood wait time (default: 1.5)

## Examples

### Example 1: Basic Setup

1. **Create configuration:**
   ```bash
   telegram-scanner  # Creates default config.json
   ```

2. **Edit config.json:**
   ```json
   {
     "api_credentials": {
       "api_id": "1234567",
       "api_hash": "your_actual_api_hash"
     },
     "relevance": {
       "keywords": ["bitcoin", "crypto", "trading"],
       "logic": "OR"
     }
   }
   ```

3. **Start scanning:**
   ```bash
   telegram-scanner
   ```

### Example 2: Advanced Filtering

Configuration for monitoring specific patterns:

```json
{
  "api_credentials": {
    "api_id": "1234567",
    "api_hash": "your_api_hash"
  },
  "scanning": {
    "scan_interval": 15,
    "max_history_days": 3,
    "selected_groups": ["CryptoNews", "TechUpdates"]
  },
  "relevance": {
    "keywords": ["breaking", "urgent", "alert"],
    "regex_patterns": [
      "\\$[0-9,]+",
      "\\b\\d{1,2}/\\d{1,2}/\\d{4}\\b",
      "\\b[A-Z]{3,4}\\b"
    ],
    "logic": "OR"
  }
}
```

### Example 3: Batch Processing

Run for 2 hours with debug logging:

```bash
telegram-scanner --batch --duration 120 --log-level DEBUG --log-file scanner.log
```

### Example 4: Multiple Configurations

Use different configurations for different purposes:

```bash
# Monitor crypto groups
telegram-scanner --config crypto-config.json

# Monitor news groups
telegram-scanner --config news-config.json
```

## Troubleshooting

### Common Issues

**1. Authentication Failed**
```
Error: Authentication failed
```
- Verify your API ID and API hash are correct
- Ensure you have a stable internet connection
- Check if your Telegram account is not restricted

**2. No Groups Found**
```
Warning: No accessible groups found
```
- Make sure you're a member of Telegram groups
- Check if groups are public or if you have proper access
- Verify your account is not restricted from accessing groups

**3. Rate Limiting**
```
Error: FloodWaitError: Too many requests
```
- Reduce `requests_per_minute` in configuration
- Increase `scan_interval` to scan less frequently
- The scanner automatically handles rate limits with exponential backoff

**4. OCR Not Working**
```
Error: Tesseract not found
```
- Install Tesseract OCR (see Installation section)
- Ensure Tesseract is in your system PATH
- On Windows, you may need to specify the Tesseract path

**5. Configuration Errors**
```
Error: Invalid configuration file
```
- Validate your JSON syntax using a JSON validator
- Ensure all required fields are present
- Check for trailing commas or syntax errors

### Debug Mode

Enable debug logging for detailed troubleshooting:

```bash
telegram-scanner --log-level DEBUG --log-file debug.log
```

### Getting Help

1. Check the log files for detailed error messages
2. Verify your configuration against the examples
3. Ensure all dependencies are properly installed
4. Test with a minimal configuration first

## Development

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=telegram_scanner

# Run property-based tests only
pytest -k "properties"
```

### Code Quality

```bash
# Format code
black telegram_scanner/

# Lint code
flake8 telegram_scanner/

# Type checking
mypy telegram_scanner/
```

### Project Structure

```
telegram_scanner/
├── __init__.py
├── main.py              # Main application entry point
├── cli.py               # Command-line interface
├── auth.py              # Authentication management
├── scanner.py           # Group scanning and monitoring
├── processor.py         # Message processing and extraction
├── filter.py            # Relevance filtering
├── storage.py           # Data storage and export
├── config.py            # Configuration management
├── command_interface.py # Interactive command interface
├── error_handling.py    # Error handling utilities
└── models.py            # Data models and structures
```

## License

MIT License - see LICENSE file for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

## Security

- Never commit API credentials to version control
- Use environment variables for sensitive configuration in production
- Regularly rotate your API credentials
- Monitor your Telegram account for unusual activity

## Recent Bug Fixes

All critical bugs have been fixed! See [FIXES_APPLIED.md](FIXES_APPLIED.md) for details on:
- Real-time monitoring now works correctly
- Race conditions resolved
- Memory leaks fixed
- Session security improved

The scanner is now production-ready and fully functional.
