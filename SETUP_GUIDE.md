# Telegram Group Scanner - Setup Guide

This guide will walk you through setting up the Telegram Group Scanner from scratch.

## Prerequisites

Before you begin, ensure you have:

- Python 3.8 or higher installed
- A Telegram account
- Basic familiarity with command line/terminal

## Step 1: Install System Dependencies

### Tesseract OCR

The scanner uses Tesseract for extracting text from images. Install it for your operating system:

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install tesseract-ocr tesseract-ocr-eng
```

**CentOS/RHEL/Fedora:**
```bash
sudo yum install tesseract tesseract-langpack-eng
# or for newer versions:
sudo dnf install tesseract tesseract-langpack-eng
```

**macOS:**
```bash
# Using Homebrew
brew install tesseract

# Using MacPorts
sudo port install tesseract
```

**Windows:**
1. Download the installer from: https://github.com/UB-Mannheim/tesseract/wiki
2. Run the installer and follow the setup wizard
3. Add Tesseract to your system PATH (usually `C:\Program Files\Tesseract-OCR`)

### Verify Tesseract Installation

```bash
tesseract --version
```

You should see output similar to:
```
tesseract 5.3.0
```

## Step 2: Get Telegram API Credentials

1. **Open Telegram Web:**
   Go to https://my.telegram.org/apps

2. **Log in:**
   - Enter your phone number (with country code, e.g., +1234567890)
   - Enter the verification code sent to your Telegram app

3. **Create New Application:**
   - **App title:** "Telegram Group Scanner" (or any name you prefer)
   - **Short name:** "scanner" (or any short identifier)
   - **Platform:** Select "Desktop"
   - **Description:** Optional - describe what you'll use it for

4. **Save Your Credentials:**
   After creating the app, you'll see:
   - **API ID:** A number (e.g., 1234567)
   - **API Hash:** A string (e.g., "abcdef1234567890abcdef1234567890")

   ⚠️ **IMPORTANT:** Keep these credentials secure and never share them publicly!

## Step 3: Install the Scanner

### Option A: Clone from Repository

```bash
# Clone the repository
git clone <repository-url>
cd telegram-group-scanner

# Create virtual environment (recommended)
python -m venv venv

# Activate virtual environment
# On Linux/macOS:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install the package in development mode
pip install -e .
```

### Option B: Install from Package (if available)

```bash
# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install the package
pip install telegram-group-scanner
```

## Step 4: Initial Configuration

1. **Run the scanner for the first time:**
   ```bash
   telegram-scanner
   ```

   This will create a default `config.json` file and exit with a message asking you to update your credentials.

2. **Edit the configuration file:**
   Open `config.json` in your favorite text editor and update the API credentials:

   ```json
   {
     "api_credentials": {
       "api_id": "1234567",
       "api_hash": "your_actual_api_hash_here"
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

   Replace:
   - `"1234567"` with your actual API ID
   - `"your_actual_api_hash_here"` with your actual API hash

## Step 5: First Run and Authentication

1. **Start the scanner:**
   ```bash
   telegram-scanner
   ```

2. **Complete authentication:**
   - Enter your phone number when prompted (with country code)
   - Enter the verification code sent to your Telegram app
   - If you have 2FA enabled, enter your password

3. **The scanner will:**
   - Authenticate with Telegram
   - Discover your accessible groups
   - Display the interactive command interface

## Step 6: Basic Usage

Once authenticated, you can use these commands:

- `start` - Begin scanning groups
- `status` - Check current status
- `stop` - Stop scanning
- `quit` - Exit the application

### Example First Session:

```
Telegram Group Scanner - Interactive Mode
========================================
Available commands:
  start   - Start scanning groups
  stop    - Stop scanning
  pause   - Pause scanning
  resume  - Resume scanning
  status  - Show current status
  report  - Generate scanning report
  config  - Show current configuration
  reload  - Reload configuration
  quit    - Exit application
========================================

Enter command: start
Result: Scanning started successfully

Enter command: status
Status:
{
  "state": "running",
  "groups_monitored": 5,
  "messages_processed": 0,
  "relevant_messages": 0,
  "last_scan": null,
  "uptime_seconds": 10
}

Enter command: quit
```

## Step 7: Customize Your Configuration

Based on your needs, you can customize the configuration:

### For Crypto Monitoring:
```json
{
  "relevance": {
    "keywords": ["bitcoin", "ethereum", "pump", "dump", "moon"],
    "regex_patterns": ["\\$[0-9,]+", "\\b\\d+%\\b"],
    "logic": "OR"
  },
  "scanning": {
    "scan_interval": 15,
    "selected_groups": ["CryptoNews", "BitcoinTrading"]
  }
}
```

### For News Monitoring:
```json
{
  "relevance": {
    "keywords": ["breaking", "urgent", "developing", "confirmed"],
    "regex_patterns": ["\\b\\d{1,2}/\\d{1,2}/\\d{4}\\b"],
    "logic": "OR"
  },
  "scanning": {
    "scan_interval": 60,
    "max_history_days": 1
  }
}
```

## Step 8: Advanced Usage

### Batch Mode

Run the scanner automatically without interaction:

```bash
# Run for 2 hours
telegram-scanner --batch --duration 120

# Run indefinitely
telegram-scanner --batch
```

### Custom Configuration Files

Use different configurations for different purposes:

```bash
telegram-scanner --config crypto-config.json
telegram-scanner --config news-config.json
```

### Logging

Enable detailed logging for troubleshooting:

```bash
telegram-scanner --log-level DEBUG --log-file scanner.log
```

## Troubleshooting

### Common Issues:

1. **"Authentication failed"**
   - Double-check your API ID and API hash
   - Ensure stable internet connection
   - Try regenerating your API credentials

2. **"Tesseract not found"**
   - Verify Tesseract is installed: `tesseract --version`
   - On Windows, ensure Tesseract is in your PATH

3. **"No groups found"**
   - Make sure you're a member of Telegram groups
   - Check that groups are accessible (not restricted)

4. **Rate limiting errors**
   - Reduce `requests_per_minute` in configuration
   - Increase `scan_interval`

### Getting Help:

1. Check log files for detailed error messages
2. Run with debug logging: `--log-level DEBUG`
3. Verify configuration syntax with a JSON validator
4. Test with minimal configuration first

## Security Best Practices

1. **Protect your credentials:**
   - Never commit `config.json` to version control
   - Use environment variables in production
   - Regularly rotate your API credentials

2. **Monitor usage:**
   - Keep track of API usage to avoid limits
   - Monitor your Telegram account for unusual activity

3. **Use virtual environments:**
   - Always use Python virtual environments
   - Keep dependencies isolated

## Next Steps

- Explore the example configurations in the `examples/` directory
- Read the full documentation in `README.md`
- Customize relevance filters for your specific use case
- Set up automated batch processing for continuous monitoring

## Support

If you encounter issues:

1. Check the troubleshooting section above
2. Review log files with debug logging enabled
3. Verify your configuration against the examples
4. Ensure all dependencies are properly installed