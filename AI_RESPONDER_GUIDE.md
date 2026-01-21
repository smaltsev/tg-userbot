# AI Responder Guide

The AI Responder module generates intelligent responses to Telegram messages using OpenAI or ProxyAPI.

---

## Features

- 🤖 **AI-Powered Responses** - Generate intelligent replies using GPT models
- 🔄 **Multiple Providers** - Support for OpenAI and ProxyAPI
- 💾 **Response Caching** - Cache responses to avoid duplicate API calls
- 🎯 **Custom Prompts** - Fully customizable system prompts and templates
- ⚙️ **Flexible Configuration** - Control temperature, max tokens, and more
- 🔒 **Secure** - API keys stored in configuration file

---

## Configuration

### Basic Setup (OpenAI)

```json
{
  "ai_responder": {
    "enabled": true,
    "provider": "openai",
    "api_url": "https://api.openai.com/v1/chat/completions",
    "api_key": "sk-your-openai-api-key-here",
    "model": "gpt-3.5-turbo",
    "temperature": 0.7,
    "max_tokens": 500,
    "system_prompt": "You are a helpful assistant.",
    "prompt_template": "",
    "cache_responses": true,
    "auto_respond": false
  }
}
```

### ProxyAPI Setup

```json
{
  "ai_responder": {
    "enabled": true,
    "provider": "proxyapi",
    "api_url": "https://api.proxyapi.ru/openai/v1/chat/completions",
    "api_key": "your-proxyapi-key-here",
    "model": "gpt-3.5-turbo",
    "temperature": 0.7,
    "max_tokens": 500,
    "system_prompt": "You are a helpful assistant.",
    "prompt_template": "",
    "cache_responses": true,
    "auto_respond": false
  }
}
```

---

## Configuration Options

### enabled
- **Type:** boolean
- **Default:** false
- **Description:** Enable/disable AI responder

### provider
- **Type:** string
- **Options:** "openai", "proxyapi"
- **Default:** "openai"
- **Description:** AI API provider to use

### api_url
- **Type:** string
- **Default:** "https://api.openai.com/v1/chat/completions"
- **Description:** API endpoint URL

### api_key
- **Type:** string
- **Required:** Yes (when enabled)
- **Description:** Your API key

### model
- **Type:** string
- **Default:** "gpt-3.5-turbo"
- **Options:** "gpt-3.5-turbo", "gpt-4", "gpt-4-turbo", etc.
- **Description:** AI model to use

### temperature
- **Type:** float
- **Range:** 0.0 - 2.0
- **Default:** 0.7
- **Description:** Controls randomness (0 = deterministic, 2 = very random)

### max_tokens
- **Type:** integer
- **Default:** 500
- **Description:** Maximum tokens in response

### system_prompt
- **Type:** string
- **Default:** "You are a helpful assistant responding to Telegram messages."
- **Description:** System prompt that defines AI behavior

### prompt_template
- **Type:** string
- **Default:** "" (uses default template)
- **Description:** Custom prompt template with placeholders

### cache_responses
- **Type:** boolean
- **Default:** true
- **Description:** Cache responses to avoid duplicate API calls

### auto_respond
- **Type:** boolean
- **Default:** false
- **Description:** Automatically send responses (future feature)

---

## Custom Prompt Templates

Use placeholders in your prompt template:

- `{message_content}` - The message text
- `{sender_username}` - Username of sender
- `{group_name}` - Name of the group
- `{extracted_text}` - Text extracted from images
- `{timestamp}` - Message timestamp
- `{context}` - Previous messages for context

### Example Template

```json
{
  "prompt_template": "You are responding to a message in the '{group_name}' Telegram group.\n\nUser '{sender_username}' wrote:\n{message_content}\n\nProvide a helpful and professional response:"
}
```

### Advanced Template with Context

```json
{
  "prompt_template": "Previous conversation:\n{context}\n\nNew message from {sender_username}:\n{message_content}\n\nGenerate an appropriate response that considers the conversation history:"
}
```

---

## Usage

### Programmatic Usage

```python
from telegram_scanner.ai_responder import AIResponder, AIConfig
from telegram_scanner.models import TelegramMessage

# Initialize
ai_config = AIConfig(config_dict)
responder = AIResponder(ai_config)
await responder.initialize()

# Generate response
message = TelegramMessage(...)
response = await responder.generate_response(message)
print(f"AI Response: {response}")

# With context
context = [previous_message1, previous_message2]
response = await responder.generate_response(message, context=context)

# Cleanup
await responder.close()
```

### Integration with Scanner

The AI responder can be integrated into the message processing pipeline:

```python
# In scanner.py or processor.py
if self.ai_responder and self.ai_responder.config.enabled:
    response = await self.ai_responder.generate_response(processed_message)
    if response:
        logger.info(f"Generated AI response: {response[:100]}...")
        # Store or send response
```

---

## Examples

### Customer Support Bot

```json
{
  "ai_responder": {
    "enabled": true,
    "provider": "openai",
    "api_key": "sk-...",
    "model": "gpt-3.5-turbo",
    "temperature": 0.7,
    "system_prompt": "You are a customer support assistant. Be helpful, professional, and concise. Provide solutions to problems and answer questions clearly.",
    "prompt_template": "Customer question from {sender_username}:\n{message_content}\n\nProvide a helpful support response:"
  }
}
```

### Technical Assistant

```json
{
  "ai_responder": {
    "enabled": true,
    "provider": "openai",
    "api_key": "sk-...",
    "model": "gpt-4",
    "temperature": 0.5,
    "system_prompt": "You are a technical expert. Provide accurate, detailed technical information. Include code examples when relevant.",
    "prompt_template": "Technical question:\n{message_content}\n\nProvide a detailed technical response:"
  }
}
```

### Casual Chat Bot

```json
{
  "ai_responder": {
    "enabled": true,
    "provider": "openai",
    "api_key": "sk-...",
    "model": "gpt-3.5-turbo",
    "temperature": 0.9,
    "system_prompt": "You are a friendly chat bot. Be casual, fun, and engaging. Use emojis occasionally.",
    "prompt_template": "{sender_username} says:\n{message_content}\n\nRespond in a friendly, casual way:"
  }
}
```

---

## API Providers

### OpenAI

**Setup:**
1. Go to https://platform.openai.com/api-keys
2. Create an API key
3. Add to config: `"api_key": "sk-..."`

**Models:**
- `gpt-3.5-turbo` - Fast, cost-effective
- `gpt-4` - More capable, higher cost
- `gpt-4-turbo` - Latest, best performance

**Pricing:** https://openai.com/pricing

### ProxyAPI

**Setup:**
1. Go to https://proxyapi.ru
2. Register and get API key
3. Add to config: `"api_key": "your-key"`

**URL:** `https://api.proxyapi.ru/openai/v1/chat/completions`

**Benefits:**
- Access to OpenAI models
- Alternative billing
- May work in restricted regions

---

## Performance

### Response Time
- Typical: 1-3 seconds
- Depends on model and token count
- Cached responses: instant

### Cost Optimization

1. **Use caching** - Enable `cache_responses: true`
2. **Limit tokens** - Set appropriate `max_tokens`
3. **Choose model wisely** - gpt-3.5-turbo is cheaper than gpt-4
4. **Filter messages** - Only generate responses for relevant messages
5. **Batch processing** - Process multiple messages efficiently

### Rate Limiting

- OpenAI: 3,500 requests/minute (tier 1)
- ProxyAPI: Check your plan limits
- Built-in retry logic handles rate limits

---

## Security

### Best Practices

1. **Never commit API keys** - Use .gitignore
2. **Use environment variables** - For production
3. **Rotate keys regularly** - Update periodically
4. **Monitor usage** - Check API dashboard
5. **Set spending limits** - On API provider dashboard
6. **Validate responses** - Check for inappropriate content

### Environment Variables

```bash
export OPENAI_API_KEY="sk-..."
export AI_RESPONDER_ENABLED="true"
```

Then in code:
```python
import os
config["ai_responder"]["api_key"] = os.getenv("OPENAI_API_KEY", "")
```

---

## Troubleshooting

### "API key not provided"
- Check `api_key` in config
- Ensure it starts with `sk-` for OpenAI
- Verify key is valid on provider dashboard

### "Rate limit exceeded"
- Wait and retry (automatic)
- Reduce `requests_per_minute`
- Upgrade API plan

### "Model not found"
- Check model name spelling
- Verify model access on your plan
- Try `gpt-3.5-turbo` as fallback

### "Response too slow"
- Reduce `max_tokens`
- Use faster model (gpt-3.5-turbo)
- Enable caching
- Check network latency

### "Invalid response format"
- Check API URL is correct
- Verify provider compatibility
- Enable debug logging

---

## Advanced Features

### Context-Aware Responses

Pass previous messages for context:

```python
context = await get_recent_messages(group_id, limit=5)
response = await responder.generate_response(message, context=context)
```

### Response Caching

Responses are cached by message content hash:

```python
# First call - hits API
response1 = await responder.generate_response(message)

# Second call with same message - uses cache
response2 = await responder.generate_response(message)

# Clear cache
responder.clear_cache()
```

### Statistics

```python
stats = responder.get_stats()
print(f"Cached responses: {stats['cached_responses']}")
print(f"Provider: {stats['provider']}")
print(f"Model: {stats['model']}")
```

---

## Future Enhancements

- ✅ OpenAI support
- ✅ ProxyAPI support
- ✅ Response caching
- ✅ Custom prompts
- 🔄 Auto-respond feature
- 🔄 Multi-language support
- 🔄 Sentiment analysis
- 🔄 Response templates
- 🔄 A/B testing
- 🔄 Analytics dashboard

---

## Support

**Documentation:** See README.md for general setup

**API Issues:** Check provider documentation
- OpenAI: https://platform.openai.com/docs
- ProxyAPI: https://proxyapi.ru/docs

**Logs:** Check `scanner.log` for detailed errors

---

**Status:** ✅ Production Ready  
**Version:** 1.0.0  
**Last Updated:** 2026-01-21
