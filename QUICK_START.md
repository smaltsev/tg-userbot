# Quick Start Guide

Get the Telegram Group Scanner up and running in 5 minutes!

## Prerequisites

- Python 3.8+ installed
- A Telegram account
- 5 minutes of your time

## 1. Install Dependencies

**Install Tesseract OCR:**

```bash
# Ubuntu/Debian
sudo apt-get install tesseract-ocr

# macOS
brew install tesseract

# Windows: Download from https://github.com/UB-Mannheim/tesseract/wiki
```

## 2. Install the Scanner

```bash
# Clone and install
git clone <repository-url>
cd telegram-group-scanner
pip install -r requirements.txt
pip install -e .
```

## 3. Get API Credentials

1. Go to https://my.telegram.org/apps
2. Log in with your Telegram account
3. Create new application:
   - App title: "My Scanner"
   - Short name: "scanner"
   - Platform: "Desktop"
4. Save your **API ID** and **API Hash**

## 4. Configure

```bash
# Run once to create config file
telegram-scanner
```

Edit `config.json` with your credentials:

```json
{
  "api_credentials": {
    "api_id": "YOUR_API_ID",
    "api_hash": "YOUR_API_HASH"
  },
  "relevance": {
    "keywords": ["important", "urgent", "breaking"]
  }
}
```

## 5. Run

```bash
telegram-scanner
```

Follow the authentication prompts, then use these commands:

- `start` - Begin scanning
- `status` - Check status
- `quit` - Exit

## Done! 🎉

Your scanner is now monitoring your Telegram groups for relevant messages.

## Next Steps

- Customize keywords in `config.json`
- Try batch mode: `telegram-scanner --batch`
- Read the full [README.md](README.md) for advanced features

## Need Help?

- Check [SETUP_GUIDE.md](SETUP_GUIDE.md) for detailed instructions
- See [API_CREDENTIALS_GUIDE.md](API_CREDENTIALS_GUIDE.md) for credential help
- Look at example configs in `examples/` directory