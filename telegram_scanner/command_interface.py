"""
Command and control interface for Telegram Group Scanner.
"""

import asyncio
import logging
import json
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from enum import Enum
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


class ScannerState(Enum):
    """Scanner operational states."""
    STOPPED = "stopped"
    RUNNING = "running"
    PAUSED = "paused"
    ERROR = "error"


@dataclass
class ScannerStatus:
    """Scanner status information."""
    state: ScannerState
    last_scan_time: Optional[str]
    messages_processed: int
    groups_monitored: int
    relevant_messages_found: int
    uptime_seconds: float
    last_error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert status to dictionary."""
        result = asdict(self)
        # Convert enum to its value for JSON serialization
        if isinstance(result.get('state'), ScannerState):
            result['state'] = result['state'].value
        return result


@dataclass
class ScanningReport:
    """Comprehensive scanning activity report."""
    report_generated: str
    scan_period_start: str
    scan_period_end: str
    total_messages_processed: int
    relevant_messages_found: int
    groups_scanned: List[Dict[str, Any]]
    top_keywords: List[Dict[str, Any]]
    error_summary: Dict[str, int]
    performance_metrics: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert report to dictionary."""
        return asdict(self)


class CommandInterface:
    """Command and control interface for the Telegram Scanner."""
    
    def __init__(self, scanner_instance):
        """Initialize command interface with scanner instance."""
        self.scanner = scanner_instance
        self._state = ScannerState.STOPPED
        self._start_time: Optional[datetime] = None
        self._last_scan_time: Optional[datetime] = None
        self._messages_processed = 0
        self._relevant_messages_found = 0
        self._last_error: Optional[str] = None
        self._command_lock = asyncio.Lock()
        
        # Statistics tracking
        self._group_stats: Dict[int, Dict[str, Any]] = {}
        self._keyword_stats: Dict[str, int] = {}
        self._error_stats: Dict[str, int] = {}
        
    async def start_scanning(self) -> Dict[str, Any]:
        """
        Start the scanning operation.
        
        Returns:
            Dict containing operation result and status
        """
        async with self._command_lock:
            if self._state != ScannerState.STOPPED:
                return {
                    "success": False,
                    "message": f"Cannot start scanner from {self._state.value} state. Must be stopped first.",
                    "state": self._state.value
                }
                
            try:
                logger.info("Starting scanner via command interface...")
                
                # Initialize scanner if needed
                if not hasattr(self.scanner, 'auth_manager') or not self.scanner.auth_manager:
                    await self.scanner.initialize()
                
                # Authenticate if not already done
                if not self.scanner.auth_manager.is_authenticated():
                    await self.scanner.auth_manager.authenticate()
                
                # Discover groups if not already done
                if not hasattr(self.scanner, 'group_scanner') or not self.scanner.group_scanner._discovered_groups:
                    await self.scanner.group_scanner.discover_groups()
                
                # Scan historical messages first
                logger.info("Scanning historical messages...")
                history_result = await self.scanner.group_scanner.scan_history()
                if history_result:
                    self._messages_processed += history_result.get('total_messages', 0)
                    self._relevant_messages_found += history_result.get('relevant_messages', 0)
                    self._last_scan_time = datetime.now(timezone.utc)
                
                # Start real-time monitoring
                await self.scanner.group_scanner.start_monitoring()
                
                self._state = ScannerState.RUNNING
                self._start_time = datetime.now(timezone.utc)
                self._last_error = None
                
                logger.info("Scanner started successfully")
                
                return {
                    "success": True,
                    "message": "Scanner started successfully",
                    "state": self._state.value,
                    "groups_monitored": len(self.scanner.group_scanner._discovered_groups)
                }
                
            except Exception as e:
                error_msg = f"Failed to start scanner: {str(e)}"
                logger.error(error_msg)
                self._state = ScannerState.ERROR
                self._last_error = error_msg
                self._record_error("start_command", str(e))
                
                return {
                    "success": False,
                    "message": error_msg,
                    "state": self._state.value
                }
    
    async def stop_scanning(self) -> Dict[str, Any]:
        """
        Stop the scanning operation.
        
        Returns:
            Dict containing operation result and status
        """
        async with self._command_lock:
            if self._state == ScannerState.STOPPED:
                return {
                    "success": False,
                    "message": "Scanner is already stopped",
                    "state": self._state.value
                }
                
            try:
                logger.info("Stopping scanner via command interface...")
                
                # Stop monitoring if active
                if (hasattr(self.scanner, 'group_scanner') and 
                    self.scanner.group_scanner and 
                    self.scanner.group_scanner.is_monitoring()):
                    await self.scanner.group_scanner.stop_monitoring()
                
                self._state = ScannerState.STOPPED
                self._last_error = None
                
                logger.info("Scanner stopped successfully")
                
                return {
                    "success": True,
                    "message": "Scanner stopped successfully",
                    "state": self._state.value
                }
                
            except Exception as e:
                error_msg = f"Failed to stop scanner: {str(e)}"
                logger.error(error_msg)
                self._last_error = error_msg
                self._record_error("stop_command", str(e))
                
                return {
                    "success": False,
                    "message": error_msg,
                    "state": self._state.value
                }
    
    async def pause_scanning(self) -> Dict[str, Any]:
        """
        Pause the scanning operation.
        
        Returns:
            Dict containing operation result and status
        """
        async with self._command_lock:
            if self._state != ScannerState.RUNNING:
                return {
                    "success": False,
                    "message": f"Cannot pause scanner in {self._state.value} state",
                    "state": self._state.value
                }
                
            try:
                logger.info("Pausing scanner via command interface...")
                
                # Stop monitoring but keep session active
                if (hasattr(self.scanner, 'group_scanner') and 
                    self.scanner.group_scanner and 
                    self.scanner.group_scanner.is_monitoring()):
                    await self.scanner.group_scanner.stop_monitoring()
                
                self._state = ScannerState.PAUSED
                self._last_error = None
                
                logger.info("Scanner paused successfully")
                
                return {
                    "success": True,
                    "message": "Scanner paused successfully",
                    "state": self._state.value
                }
                
            except Exception as e:
                error_msg = f"Failed to pause scanner: {str(e)}"
                logger.error(error_msg)
                self._last_error = error_msg
                self._record_error("pause_command", str(e))
                
                return {
                    "success": False,
                    "message": error_msg,
                    "state": self._state.value
                }
    
    async def resume_scanning(self) -> Dict[str, Any]:
        """
        Resume scanning from paused state.
        
        Returns:
            Dict containing operation result and status
        """
        async with self._command_lock:
            if self._state != ScannerState.PAUSED:
                return {
                    "success": False,
                    "message": f"Cannot resume scanner from {self._state.value} state",
                    "state": self._state.value
                }
                
            try:
                logger.info("Resuming scanner via command interface...")
                
                # Resume monitoring
                if (hasattr(self.scanner, 'group_scanner') and 
                    self.scanner.group_scanner):
                    await self.scanner.group_scanner.start_monitoring()
                
                self._state = ScannerState.RUNNING
                self._last_error = None
                
                logger.info("Scanner resumed successfully")
                
                return {
                    "success": True,
                    "message": "Scanner resumed successfully",
                    "state": self._state.value
                }
                
            except Exception as e:
                error_msg = f"Failed to resume scanner: {str(e)}"
                logger.error(error_msg)
                self._state = ScannerState.ERROR
                self._last_error = error_msg
                self._record_error("resume_command", str(e))
                
                return {
                    "success": False,
                    "message": error_msg,
                    "state": self._state.value
                }
    
    async def get_status(self) -> ScannerStatus:
        """
        Get current scanner status.
        
        Returns:
            ScannerStatus object with current information
        """
        uptime_seconds = 0.0
        if self._start_time:
            uptime_seconds = (datetime.now(timezone.utc) - self._start_time).total_seconds()
        
        groups_monitored = 0
        if (hasattr(self.scanner, 'group_scanner') and 
            self.scanner.group_scanner and 
            hasattr(self.scanner.group_scanner, '_discovered_groups')):
            groups_monitored = len(self.scanner.group_scanner._discovered_groups)
        
        last_scan_time = None
        if self._last_scan_time:
            last_scan_time = self._last_scan_time.isoformat()
        
        return ScannerStatus(
            state=self._state,
            last_scan_time=last_scan_time,
            messages_processed=self._messages_processed,
            groups_monitored=groups_monitored,
            relevant_messages_found=self._relevant_messages_found,
            uptime_seconds=uptime_seconds,
            last_error=self._last_error
        )
    
    async def generate_report(self, start_date: Optional[str] = None, 
                            end_date: Optional[str] = None) -> ScanningReport:
        """
        Generate comprehensive scanning activity report.
        
        Args:
            start_date: Start date for report period (ISO format)
            end_date: End date for report period (ISO format)
            
        Returns:
            ScanningReport object with activity summary
        """
        now = datetime.now(timezone.utc)
        
        # Default to last 24 hours if no dates provided
        if not start_date:
            start_date = (now.replace(hour=0, minute=0, second=0, microsecond=0)).isoformat()
        if not end_date:
            end_date = now.isoformat()
        
        # Get group statistics
        groups_scanned = []
        if (hasattr(self.scanner, 'group_scanner') and 
            self.scanner.group_scanner and 
            hasattr(self.scanner.group_scanner, '_discovered_groups')):
            
            for group in self.scanner.group_scanner._discovered_groups:
                group_stats = self._group_stats.get(group.id, {
                    "messages_processed": 0,
                    "relevant_messages": 0,
                    "last_activity": None
                })
                
                groups_scanned.append({
                    "group_id": group.id,
                    "group_name": group.title,
                    "messages_processed": group_stats["messages_processed"],
                    "relevant_messages": group_stats["relevant_messages"],
                    "last_activity": group_stats["last_activity"]
                })
        
        # Get top keywords
        top_keywords = [
            {"keyword": keyword, "count": count}
            for keyword, count in sorted(self._keyword_stats.items(), 
                                       key=lambda x: x[1], reverse=True)[:10]
        ]
        
        # Performance metrics
        performance_metrics = {
            "average_processing_time": 0.0,  # Would be calculated from actual metrics
            "messages_per_minute": 0.0,
            "uptime_percentage": 100.0 if self._state == ScannerState.RUNNING else 0.0
        }
        
        return ScanningReport(
            report_generated=now.isoformat(),
            scan_period_start=start_date,
            scan_period_end=end_date,
            total_messages_processed=self._messages_processed,
            relevant_messages_found=self._relevant_messages_found,
            groups_scanned=groups_scanned,
            top_keywords=top_keywords,
            error_summary=dict(self._error_stats),
            performance_metrics=performance_metrics
        )
    
    def get_current_state(self) -> ScannerState:
        """Get current scanner state."""
        return self._state
    
    def update_message_stats(self, group_id: int, group_name: str, 
                           is_relevant: bool, keywords_matched: List[str] = None):
        """
        Update message processing statistics.
        
        Args:
            group_id: ID of the group where message was processed
            group_name: Name of the group
            is_relevant: Whether the message was relevant
            keywords_matched: List of keywords that matched
        """
        self._messages_processed += 1
        self._last_scan_time = datetime.now(timezone.utc)
        
        # Update group statistics
        if group_id not in self._group_stats:
            self._group_stats[group_id] = {
                "messages_processed": 0,
                "relevant_messages": 0,
                "last_activity": None
            }
        
        self._group_stats[group_id]["messages_processed"] += 1
        self._group_stats[group_id]["last_activity"] = self._last_scan_time.isoformat()
        
        if is_relevant:
            self._relevant_messages_found += 1
            self._group_stats[group_id]["relevant_messages"] += 1
            
            # Update keyword statistics
            if keywords_matched:
                for keyword in keywords_matched:
                    self._keyword_stats[keyword] = self._keyword_stats.get(keyword, 0) + 1
    
    def _record_error(self, error_type: str, error_message: str):
        """Record error for statistics."""
        self._error_stats[error_type] = self._error_stats.get(error_type, 0) + 1
        logger.debug(f"Recorded error: {error_type} - {error_message}")