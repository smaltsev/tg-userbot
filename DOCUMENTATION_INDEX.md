# Documentation Index

Quick reference to all documentation files in this project.

---

## Essential Documentation

### 📘 [README.md](README.md)
**Main project documentation**
- Overview and features
- Installation instructions
- Basic usage guide
- Configuration reference
- Project structure

### 🔧 [FIXES_APPLIED.md](FIXES_APPLIED.md)
**Bug fixes and improvements**
- All critical bugs fixed
- Real-time monitoring fix
- Configuration guide
- Troubleshooting tips
- Testing instructions

### 🚀 [QUICK_START.md](QUICK_START.md)
**Get started quickly**
- Fast setup guide
- First-time configuration
- Running your first scan
- Common workflows

---

## Setup Guides

### 🔑 [API_CREDENTIALS_GUIDE.md](API_CREDENTIALS_GUIDE.md)
**Getting Telegram API credentials**
- Step-by-step API setup
- Creating Telegram app
- Security best practices

### ⚙️ [SETUP_GUIDE.md](SETUP_GUIDE.md)
**Detailed setup instructions**
- System requirements
- Installation steps
- Configuration options
- Initial authentication

---

## Usage Guides

### 📋 [COMMANDS.md](COMMANDS.md)
**Command reference**
- All available commands
- Command descriptions
- Usage examples
- Tips and tricks

### 🔍 [SCANNING_EXPLAINED.md](SCANNING_EXPLAINED.md)
**How scanning works**
- Group discovery process
- Message filtering
- Real-time monitoring
- Data storage

### 🐛 [DEBUG_MODE.md](DEBUG_MODE.md)
**Debugging and troubleshooting**
- Enabling debug mode
- Reading debug output
- Common issues
- Performance tips

---

## Configuration Files

### 📄 config.json
**Main configuration file**
- API credentials
- Group selection
- Keywords and filters
- Scanning parameters

### 📦 requirements.txt
**Python dependencies**
- Required packages
- Version specifications

---

## Quick Reference

**Start scanning:**
```bash
python -m telegram_scanner.cli
```

**Enable debug mode:**
Edit `config.json`:
```json
{
  "scanning": {
    "debug_mode": true
  }
}
```

**Check status:**
```
Enter command: status
```

**View help:**
```
Enter command: help
```

---

## Getting Help

1. Check [FIXES_APPLIED.md](FIXES_APPLIED.md) for known issues
2. Review [SCANNING_EXPLAINED.md](SCANNING_EXPLAINED.md) for how it works
3. Enable debug mode in [DEBUG_MODE.md](DEBUG_MODE.md)
4. Check `scanner.log` for detailed logs

---

**Last Updated:** 2026-01-21  
**Status:** All documentation current and accurate
