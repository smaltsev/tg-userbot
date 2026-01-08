"""
Data storage and export functionality.
"""

import json
import csv
import logging
import asyncio
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional, Set
from .config import ScannerConfig
from .models import TelegramMessage
from .error_handling import (
    ErrorHandler,
    handle_storage_errors,
    default_error_handler,
    default_health_monitor
)

logger = logging.getLogger(__name__)


class StorageManager:
    """Handles data persistence and export."""
    
    def __init__(self, config: ScannerConfig):
        """Initialize storage manager with configuration."""
        self.config = config
        self.storage_file = Path("telegram_scanner_data.json")
        self.duplicate_hashes: Set[str] = set()
        self._data: List[Dict[str, Any]] = []
        self._lock = asyncio.Lock()
        self.error_handler = ErrorHandler(max_retries=3)
        
    @handle_storage_errors
    async def initialize(self):
        """Initialize storage by loading existing data with error handling."""
        async def _initialize_impl():
            async with self._lock:
                if self.storage_file.exists():
                    try:
                        with open(self.storage_file, 'r', encoding='utf-8') as f:
                            self._data = json.load(f)
                        
                        # Rebuild duplicate hash set
                        for item in self._data:
                            content_hash = self._generate_content_hash(item)
                            self.duplicate_hashes.add(content_hash)
                            
                        logger.info(f"Loaded {len(self._data)} existing messages")
                    except (json.JSONDecodeError, IOError) as e:
                        logger.error(f"Failed to load existing data: {e}")
                        self._data = []
                        raise
                else:
                    logger.info("No existing data file found, starting fresh")
        
        try:
            await self.error_handler.with_retry(
                _initialize_impl,
                operation_name="storage_initialization"
            )
            default_health_monitor.record_success("storage_initialization")
        except Exception as e:
            logger.error(f"Storage initialization failed: {e}")
            default_health_monitor.record_failure("storage_initialization", e)
            # Continue with empty data rather than failing completely
            self._data = []
            self.duplicate_hashes.clear()
        
    @handle_storage_errors
    async def store_message(self, message_data: Dict[str, Any]) -> bool:
        """Save relevant messages with duplicate detection and error handling."""
        async def _store_impl():
            async with self._lock:
                # Check for duplicates first
                if await self._is_duplicate(message_data):
                    logger.debug(f"Duplicate message detected, skipping: {message_data.get('id')}")
                    return False
                
                # Add timestamp if not present
                if 'stored_at' not in message_data:
                    message_data['stored_at'] = datetime.now().isoformat()
                
                # Store the message
                self._data.append(message_data)
                
                # Add to duplicate detection
                content_hash = self._generate_content_hash(message_data)
                self.duplicate_hashes.add(content_hash)
                
                # Persist to file with exponential backoff
                await self._persist_with_retry()
                
                logger.info(f"Stored message {message_data.get('id')} from group {message_data.get('group_name')}")
                return True
        
        try:
            result = await self.error_handler.with_retry(
                _store_impl,
                operation_name="message_storage"
            )
            default_health_monitor.record_success("message_storage")
            return result
        except Exception as e:
            logger.error(f"Failed to store message: {e}")
            default_health_monitor.record_failure("message_storage", e)
            return False
        
    async def check_duplicate(self, message_data: Dict[str, Any]) -> bool:
        """Check if message is a duplicate."""
        return await self._is_duplicate(message_data)
        
    async def _is_duplicate(self, message_data: Dict[str, Any]) -> bool:
        """Internal duplicate detection logic."""
        content_hash = self._generate_content_hash(message_data)
        return content_hash in self.duplicate_hashes
        
    def _generate_content_hash(self, message_data: Dict[str, Any]) -> str:
        """Generate a hash for duplicate detection based on content and metadata."""
        # Use message ID, group ID, and content for uniqueness
        hash_content = f"{message_data.get('id', '')}{message_data.get('group_id', '')}{message_data.get('content', '')}"
        return hashlib.md5(hash_content.encode('utf-8')).hexdigest()
        
    async def _persist_with_retry(self, max_retries: int = 3):
        """Persist data to file with exponential backoff retry."""
        for attempt in range(max_retries):
            try:
                # Create backup of existing file
                if self.storage_file.exists():
                    backup_file = Path(f"{self.storage_file}.backup")
                    self.storage_file.rename(backup_file)
                
                # Write new data
                with open(self.storage_file, 'w', encoding='utf-8') as f:
                    json.dump(self._data, f, indent=2, ensure_ascii=False, default=str)
                
                # Remove backup on success
                backup_file = Path(f"{self.storage_file}.backup")
                if backup_file.exists():
                    backup_file.unlink()
                    
                return
                
            except (IOError, OSError) as e:
                logger.warning(f"Storage attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
                else:
                    logger.error(f"Failed to persist data after {max_retries} attempts")
                    # Restore backup if available
                    backup_file = Path(f"{self.storage_file}.backup")
                    if backup_file.exists():
                        backup_file.rename(self.storage_file)
                    raise
        
    async def export_data(self, format_type: str = "json", output_file: Optional[str] = None) -> str:
        """Export stored data in various formats."""
        async with self._lock:
            if not self._data:
                logger.warning("No data to export")
                return ""
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            if format_type.lower() == "json":
                filename = output_file or f"telegram_export_{timestamp}.json"
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(self._data, f, indent=2, ensure_ascii=False, default=str)
                    
            elif format_type.lower() == "csv":
                filename = output_file or f"telegram_export_{timestamp}.csv"
                with open(filename, 'w', newline='', encoding='utf-8') as f:
                    if self._data:
                        writer = csv.DictWriter(f, fieldnames=self._data[0].keys())
                        writer.writeheader()
                        writer.writerows(self._data)
                        
            elif format_type.lower() == "txt":
                filename = output_file or f"telegram_export_{timestamp}.txt"
                with open(filename, 'w', encoding='utf-8') as f:
                    for item in self._data:
                        f.write(f"Group: {item.get('group_name', 'Unknown')}\n")
                        f.write(f"Sender: {item.get('sender_username', 'Unknown')}\n")
                        f.write(f"Time: {item.get('timestamp', 'Unknown')}\n")
                        f.write(f"Content: {item.get('content', '')}\n")
                        if item.get('extracted_text'):
                            f.write(f"Extracted Text: {item.get('extracted_text')}\n")
                        f.write("-" * 50 + "\n")
                        
            else:
                raise ValueError(f"Unsupported export format: {format_type}")
            
            logger.info(f"Exported {len(self._data)} messages to {filename}")
            return filename
        
    async def get_statistics(self) -> Dict[str, Any]:
        """Return scanning statistics."""
        async with self._lock:
            if not self._data:
                return {
                    "total_messages": 0,
                    "groups_scanned": 0,
                    "date_range": None,
                    "top_groups": [],
                    "media_types": {}
                }
            
            # Calculate statistics
            groups = set(item.get('group_name') for item in self._data if item.get('group_name'))
            
            # Group message counts
            group_counts = {}
            media_types = {}
            
            for item in self._data:
                group_name = item.get('group_name', 'Unknown')
                group_counts[group_name] = group_counts.get(group_name, 0) + 1
                
                media_type = item.get('media_type')
                if media_type:
                    media_types[media_type] = media_types.get(media_type, 0) + 1
            
            # Get date range
            timestamps = [item.get('timestamp') for item in self._data if item.get('timestamp')]
            date_range = None
            if timestamps:
                try:
                    dates = [datetime.fromisoformat(ts.replace('Z', '+00:00')) if isinstance(ts, str) else ts 
                            for ts in timestamps if ts]
                    if dates:
                        date_range = {
                            "earliest": min(dates).isoformat(),
                            "latest": max(dates).isoformat()
                        }
                except (ValueError, TypeError) as e:
                    logger.warning(f"Error processing timestamps for statistics: {e}")
            
            # Top groups by message count
            top_groups = sorted(group_counts.items(), key=lambda x: x[1], reverse=True)[:10]
            
            return {
                "total_messages": len(self._data),
                "groups_scanned": len(groups),
                "date_range": date_range,
                "top_groups": [{"group": group, "count": count} for group, count in top_groups],
                "media_types": media_types,
                "storage_file_size": self.storage_file.stat().st_size if self.storage_file.exists() else 0
            }