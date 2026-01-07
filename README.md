# Telegram Group Scanner

A Python application for monitoring Telegram groups and extracting relevant information using the Telethon library.

## Features

- Authenticate with Telegram API using user credentials
- Discover and monitor accessible Telegram groups
- Real-time message processing and filtering
- OCR text extraction from images
- Configurable relevance filtering with keywords and regex
- Data storage and export capabilities
- Robust error handling and rate limiting

## Installation

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Install the package:
   ```bash
   pip install -e .
   ```

## Configuration

The application uses a JSON configuration file. On first run, a default configuration will be created at `config.json`. Update this file with your Telegram API credentials and preferences.

## Usage

```bash
python -m telegram_scanner.main
```

Or if installed as a package:

```bash
telegram-scanner
```

## Requirements

- Python 3.8+
- Telegram API credentials (API ID and API hash)
- Tesseract OCR (for image text extraction)

## License

MIT License