"""
AI-powered response generation for Telegram messages.
"""

import logging
import asyncio
import aiohttp
from typing import Optional, Dict, Any, List
from datetime import datetime
from telethon.errors import ChatWriteForbiddenError, UserBannedInChannelError, ChatAdminRequiredError
from .models import TelegramMessage
from .error_handling import ErrorHandler, default_health_monitor

logger = logging.getLogger(__name__)


class AIResponder:
    """Generates intelligent responses using AI APIs (OpenAI or ProxyAPI) and sends them to Telegram."""
    
    def __init__(self, config, auth_manager=None):
        """
        Initialize AI responder with configuration.
        
        Args:
            config: AIConfig object with API settings
            auth_manager: AuthenticationManager for sending messages
        """
        self.config = config
        self.auth_manager = auth_manager
        self.error_handler = ErrorHandler(max_retries=3)
        self._session: Optional[aiohttp.ClientSession] = None
        self._response_cache: Dict[str, str] = {}
        self._sent_responses: Dict[int, str] = {}  # Track sent responses by message ID
        
    async def initialize(self):
        """Initialize HTTP session."""
        if not self._session:
            timeout = aiohttp.ClientTimeout(total=60)
            self._session = aiohttp.ClientSession(timeout=timeout)
            logger.info("AI Responder initialized")
    
    async def close(self):
        """Close HTTP session."""
        if self._session:
            await self._session.close()
            self._session = None
            logger.info("AI Responder closed")
    
    async def generate_and_send_response(self, message: TelegramMessage, context: Optional[List[TelegramMessage]] = None) -> Optional[str]:
        """
        Generate an intelligent response and send it to Telegram.
        
        Args:
            message: The message to respond to
            context: Optional list of previous messages for context
            
        Returns:
            Generated response text or None if generation/sending fails
        """
        if not self.config.enabled:
            logger.debug("AI responder is disabled")
            return None
        
        # Check if we already responded to this message
        if message.id in self._sent_responses:
            logger.debug(f"Already responded to message {message.id}")
            return self._sent_responses[message.id]
        
        # Generate response
        response = await self.generate_response(message, context)
        if not response:
            return None
        
        # Send response
        sent = await self.send_response(message, response)
        if sent:
            self._sent_responses[message.id] = response
            return response
        
        return None
    
    async def send_response(self, original_message: TelegramMessage, response_text: str) -> bool:
        """
        Send AI-generated response to Telegram.
        Tries to reply in group first, falls back to private message if needed.
        
        Args:
            original_message: The message we're responding to
            response_text: The AI-generated response
            
        Returns:
            True if message was sent successfully, False otherwise
        """
        if not self.auth_manager:
            logger.error("No auth_manager provided, cannot send messages")
            return False
        
        client = await self.auth_manager.get_client()
        if not client:
            logger.error("Telegram client not available")
            return False
        
        try:
            # Try to send as reply in the group
            try:
                await client.send_message(
                    entity=original_message.group_id,
                    message=response_text,
                    reply_to=original_message.id
                )
                logger.info(f"Sent AI response as reply in group {original_message.group_name}")
                return True
                
            except (ChatWriteForbiddenError, UserBannedInChannelError, ChatAdminRequiredError) as e:
                # Cannot post in group, try private message
                logger.warning(f"Cannot post in group {original_message.group_name}: {e}")
                logger.info(f"Attempting to send private message to {original_message.sender_username}")
                
                try:
                    # Send private message to the original sender
                    await client.send_message(
                        entity=original_message.sender_id,
                        message=f"📨 Response to your message in {original_message.group_name}:\n\n{response_text}"
                    )
                    logger.info(f"Sent AI response as private message to user {original_message.sender_id}")
                    return True
                    
                except Exception as pm_error:
                    logger.error(f"Failed to send private message: {pm_error}")
                    return False
                    
        except Exception as e:
            logger.error(f"Error sending AI response: {e}")
            default_health_monitor.record_failure("ai_response_sending", e)
            return False
    
    async def generate_response(self, message: TelegramMessage, context: Optional[List[TelegramMessage]] = None) -> Optional[str]:
        """
        Generate an intelligent response to a message.
        
        Args:
            message: The message to respond to
            context: Optional list of previous messages for context
            
        Returns:
            Generated response text or None if generation fails
        """
        if not self.config.enabled:
            logger.debug("AI responder is disabled")
            return None
        
        # Check cache first
        cache_key = self._get_cache_key(message)
        if cache_key in self._response_cache:
            logger.debug(f"Using cached response for message {message.id}")
            return self._response_cache[cache_key]
        
        try:
            await self.initialize()
            
            # Build prompt
            prompt = self._build_prompt(message, context)
            
            # Generate response based on provider
            if self.config.provider.lower() == "openai":
                response = await self._generate_openai_response(prompt)
            elif self.config.provider.lower() == "proxyapi":
                response = await self._generate_proxyapi_response(prompt)
            else:
                logger.error(f"Unknown AI provider: {self.config.provider}")
                return None
            
            # Cache the response
            if response and self.config.cache_responses:
                self._response_cache[cache_key] = response
            
            default_health_monitor.record_success("ai_response_generation")
            return response
            
        except Exception as e:
            logger.error(f"Error generating AI response: {e}")
            default_health_monitor.record_failure("ai_response_generation", e)
            return None
    
    async def _generate_openai_response(self, prompt: str) -> Optional[str]:
        """Generate response using OpenAI API."""
        async def _generate():
            headers = {
                "Authorization": f"Bearer {self.config.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": self.config.model,
                "messages": [
                    {"role": "system", "content": self.config.system_prompt},
                    {"role": "user", "content": prompt}
                ],
                "temperature": self.config.temperature,
                "max_tokens": self.config.max_tokens
            }
            
            async with self._session.post(
                self.config.api_url,
                headers=headers,
                json=payload
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"OpenAI API error {response.status}: {error_text}")
                
                data = await response.json()
                return data["choices"][0]["message"]["content"].strip()
        
        try:
            return await self.error_handler.with_retry(
                _generate,
                operation_name="openai_api_call"
            )
        except Exception as e:
            logger.error(f"OpenAI API call failed: {e}")
            return None
    
    async def _generate_proxyapi_response(self, prompt: str) -> Optional[str]:
        """Generate response using ProxyAPI (uses OpenAI-compatible format)."""
        async def _generate():
            headers = {
                "Authorization": f"Bearer {self.config.api_key}",
                "Content-Type": "application/json"
            }
            
            # ProxyAPI uses the same format as OpenAI Chat Completions
            payload = {
                "model": self.config.model,
                "messages": [
                    {"role": "system", "content": self.config.system_prompt},
                    {"role": "user", "content": prompt}
                ],
                "temperature": self.config.temperature,
                "max_tokens": self.config.max_tokens
            }
            
            async with self._session.post(
                self.config.api_url,
                headers=headers,
                json=payload
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"ProxyAPI error {response.status}: {error_text}")
                
                data = await response.json()
                # ProxyAPI uses OpenAI-compatible response format
                return data["choices"][0]["message"]["content"].strip()
        
        try:
            return await self.error_handler.with_retry(
                _generate,
                operation_name="proxyapi_api_call"
            )
        except Exception as e:
            logger.error(f"ProxyAPI call failed: {e}")
            return None
    
    def _build_prompt(self, message: TelegramMessage, context: Optional[List[TelegramMessage]] = None) -> str:
        """
        Build prompt for AI model.
        
        Args:
            message: The message to respond to
            context: Optional previous messages for context
            
        Returns:
            Formatted prompt string
        """
        # Use custom prompt template if provided
        if self.config.prompt_template:
            return self._format_custom_prompt(message, context)
        
        # Default prompt format
        prompt_parts = []
        
        # Add context if available
        if context and len(context) > 0:
            prompt_parts.append("Previous conversation:")
            for ctx_msg in context[-5:]:  # Last 5 messages for context
                prompt_parts.append(f"[{ctx_msg.sender_username}]: {ctx_msg.content}")
            prompt_parts.append("")
        
        # Add current message
        prompt_parts.append("Current message to respond to:")
        prompt_parts.append(f"From: {message.sender_username}")
        prompt_parts.append(f"Group: {message.group_name}")
        prompt_parts.append(f"Content: {message.content}")
        
        if message.extracted_text:
            prompt_parts.append(f"Extracted from image: {message.extracted_text}")
        
        prompt_parts.append("")
        prompt_parts.append("Generate an appropriate response:")
        
        return "\n".join(prompt_parts)
    
    def _format_custom_prompt(self, message: TelegramMessage, context: Optional[List[TelegramMessage]] = None) -> str:
        """Format prompt using custom template."""
        template = self.config.prompt_template
        
        # Replace placeholders
        replacements = {
            "{message_content}": message.content or "",
            "{sender_username}": message.sender_username or "Unknown",
            "{group_name}": message.group_name or "Unknown",
            "{extracted_text}": message.extracted_text or "",
            "{timestamp}": message.timestamp.isoformat() if message.timestamp else "",
        }
        
        # Add context if available
        if context and len(context) > 0:
            context_text = "\n".join([
                f"[{msg.sender_username}]: {msg.content}"
                for msg in context[-5:]
            ])
            replacements["{context}"] = context_text
        else:
            replacements["{context}"] = "No previous context"
        
        # Replace all placeholders
        formatted = template
        for key, value in replacements.items():
            formatted = formatted.replace(key, value)
        
        return formatted
    
    def _get_cache_key(self, message: TelegramMessage) -> str:
        """Generate cache key for a message."""
        import hashlib
        content = f"{message.id}:{message.content}:{message.extracted_text}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def clear_cache(self):
        """Clear response cache."""
        self._response_cache.clear()
        logger.info("AI response cache cleared")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get responder statistics."""
        return {
            "enabled": self.config.enabled,
            "provider": self.config.provider,
            "model": self.config.model,
            "cached_responses": len(self._response_cache),
            "cache_enabled": self.config.cache_responses,
            "sent_responses": len(self._sent_responses)
        }


class AIConfig:
    """Configuration for AI responder."""
    
    def __init__(self, config_dict: Dict[str, Any]):
        """Initialize from configuration dictionary."""
        self.enabled = config_dict.get("enabled", False)
        self.provider = config_dict.get("provider", "openai")
        self.api_url = config_dict.get("api_url", "https://api.openai.com/v1/chat/completions")
        self.api_key = config_dict.get("api_key", "")
        self.model = config_dict.get("model", "gpt-3.5-turbo")
        self.temperature = config_dict.get("temperature", 0.7)
        self.max_tokens = config_dict.get("max_tokens", 500)
        self.system_prompt = config_dict.get("system_prompt", "You are a helpful assistant responding to Telegram messages.")
        self.prompt_template = config_dict.get("prompt_template", "")
        self.cache_responses = config_dict.get("cache_responses", True)
        self.auto_respond = config_dict.get("auto_respond", False)
    
    def validate(self) -> bool:
        """Validate configuration."""
        if not self.enabled:
            return True
        
        if not self.api_key:
            logger.error("AI responder enabled but no API key provided")
            return False
        
        if not self.api_url:
            logger.error("AI responder enabled but no API URL provided")
            return False
        
        if self.provider not in ["openai", "proxyapi"]:
            logger.error(f"Unknown AI provider: {self.provider}")
            return False
        
        return True
