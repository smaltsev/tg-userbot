# Telegram API Credentials Setup Guide

This guide provides detailed instructions for obtaining and configuring Telegram API credentials for the Group Scanner.

## Overview

To use the Telegram Group Scanner, you need to obtain API credentials from Telegram. These credentials allow your application to authenticate with Telegram's servers and access your account's groups and messages.

## What You'll Need

- A Telegram account (mobile app or web)
- Access to https://my.telegram.org
- Your phone number associated with your Telegram account

## Step-by-Step Instructions

### Step 1: Access Telegram's Developer Portal

1. Open your web browser and go to: **https://my.telegram.org**
2. You'll see the Telegram API development tools login page

### Step 2: Log In with Your Telegram Account

1. **Enter your phone number:**
   - Include the country code (e.g., +1 for US, +44 for UK)
   - Format: `+1234567890` (no spaces or dashes)
   - Example: `+12125551234`

2. **Click "Next"**

3. **Enter the verification code:**
   - Telegram will send a verification code to your Telegram app
   - Open your Telegram app and check for the code
   - Enter the 5-digit code in the web form
   - If you don't receive the code, click "Didn't receive the code?" for alternatives

4. **Enter your password (if 2FA is enabled):**
   - If you have two-factor authentication enabled, enter your password
   - This is the password you set up in Telegram's Privacy & Security settings

### Step 3: Create a New Application

Once logged in, you'll see the "API Development Tools" page.

1. **Click "Create new application"**

2. **Fill out the application form:**

   - **App title:** 
     - Enter a descriptive name like "Telegram Group Scanner"
     - This is just for your reference and can be anything you want

   - **Short name:** 
     - Enter a short identifier like "scanner" or "groupscanner"
     - This must be unique and contain only letters, numbers, and underscores
     - No spaces allowed

   - **URL:** (Optional)
     - You can leave this blank or enter a placeholder like "https://localhost"

   - **Platform:**
     - Select "Desktop" from the dropdown menu

   - **Description:** (Optional)
     - Enter a brief description like "Monitors Telegram groups for relevant content"

3. **Click "Create application"**

### Step 4: Save Your Credentials

After creating the application, you'll see your API credentials:

```
App api_id: 1234567
App api_hash: abcdef1234567890abcdef1234567890
```

**Important Information:**

- **API ID:** This is a numeric identifier (e.g., `1234567`)
- **API Hash:** This is a 32-character hexadecimal string (e.g., `abcdef1234567890abcdef1234567890`)

### Step 5: Secure Your Credentials

⚠️ **CRITICAL SECURITY NOTES:**

1. **Keep credentials private:**
   - Never share these credentials with anyone
   - Don't post them in public forums, GitHub, or other public places
   - Treat them like passwords

2. **Store securely:**
   - Save them in a secure password manager
   - Don't store them in plain text files on shared computers
   - Consider using environment variables in production

3. **Backup safely:**
   - Keep a secure backup of your credentials
   - If you lose them, you'll need to create a new application

## Using Your Credentials

### In Configuration File

Add your credentials to the `config.json` file:

```json
{
  "api_credentials": {
    "api_id": "1234567",
    "api_hash": "abcdef1234567890abcdef1234567890"
  }
}
```

**Note:** The API ID should be entered as a string, even though it's numeric.

### Using Environment Variables (Recommended for Production)

For better security, especially in production environments, use environment variables:

**Linux/macOS:**
```bash
export TELEGRAM_API_ID="1234567"
export TELEGRAM_API_HASH="abcdef1234567890abcdef1234567890"
```

**Windows Command Prompt:**
```cmd
set TELEGRAM_API_ID=1234567
set TELEGRAM_API_HASH=abcdef1234567890abcdef1234567890
```

**Windows PowerShell:**
```powershell
$env:TELEGRAM_API_ID="1234567"
$env:TELEGRAM_API_HASH="abcdef1234567890abcdef1234567890"
```

Then modify your configuration to read from environment variables:

```json
{
  "api_credentials": {
    "api_id": "${TELEGRAM_API_ID}",
    "api_hash": "${TELEGRAM_API_HASH}"
  }
}
```

## Troubleshooting

### Common Issues and Solutions

**1. "Invalid phone number"**
- Ensure you include the country code with a `+` sign
- Remove any spaces, dashes, or parentheses
- Example: `+12125551234` not `(212) 555-1234`

**2. "Verification code not received"**
- Check your Telegram app (not SMS)
- Wait a few minutes and try again
- Click "Didn't receive the code?" for alternative delivery methods
- Ensure your Telegram app is updated

**3. "Invalid verification code"**
- Double-check you're entering the code from your Telegram app
- Make sure you're entering the most recent code
- Codes expire after a few minutes

**4. "App creation failed"**
- Try a different short name (must be unique)
- Ensure short name contains only letters, numbers, and underscores
- Wait a few minutes and try again

**5. "Authentication failed in scanner"**
- Verify you copied the API ID and hash correctly
- Check for extra spaces or characters
- Ensure the API ID is entered as a string in JSON
- Try regenerating credentials if the issue persists

### Verifying Your Credentials

To test if your credentials work, run the scanner:

```bash
telegram-scanner
```

If credentials are correct, you'll be prompted for your phone number for the first-time authentication.

## Managing Multiple Applications

You can create multiple applications for different purposes:

1. **Development Application:**
   - Use for testing and development
   - Can be deleted and recreated as needed

2. **Production Application:**
   - Use for live monitoring
   - Keep credentials extra secure

3. **Backup Application:**
   - Create as a backup in case primary credentials are compromised

## Rate Limits and Usage

**Important Notes:**

- Each application has rate limits imposed by Telegram
- Don't share credentials between multiple instances
- Monitor your usage to avoid hitting limits
- The scanner includes built-in rate limiting to help prevent issues

## Credential Rotation

For security best practices:

1. **Regular rotation:**
   - Consider rotating credentials every 6-12 months
   - Rotate immediately if you suspect compromise

2. **How to rotate:**
   - Create a new application with new credentials
   - Update your configuration
   - Delete the old application
   - Test the new credentials

## Security Checklist

Before using your credentials:

- [ ] Credentials are stored securely
- [ ] Configuration file is not committed to version control
- [ ] Environment variables are used in production
- [ ] Backup of credentials is stored safely
- [ ] You understand the rate limits
- [ ] You've tested the credentials work

## Getting Help

If you encounter issues:

1. **Double-check this guide** - Most issues are due to typos or formatting
2. **Check Telegram's official documentation** - https://core.telegram.org/api
3. **Verify your Telegram account** - Ensure it's not restricted or banned
4. **Try creating a new application** - Sometimes starting fresh helps

## Legal and Compliance

**Important Reminders:**

- Use API credentials only for legitimate purposes
- Respect Telegram's Terms of Service
- Don't use credentials for spam or abuse
- Be mindful of privacy when monitoring groups
- Ensure compliance with local laws and regulations

## Example Complete Setup

Here's what a complete setup looks like:

1. **Obtained credentials:**
   - API ID: `1234567`
   - API Hash: `abcdef1234567890abcdef1234567890`

2. **Configuration file (`config.json`):**
   ```json
   {
     "api_credentials": {
       "api_id": "1234567",
       "api_hash": "abcdef1234567890abcdef1234567890"
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

3. **First run:**
   ```bash
   telegram-scanner
   ```

4. **Authentication prompts:**
   ```
   Enter your phone number: +12125551234
   Enter the verification code: 12345
   ```

5. **Success:**
   ```
   Authentication successful!
   Discovered 5 accessible groups
   Ready to start scanning...
   ```

This completes the API credentials setup process!