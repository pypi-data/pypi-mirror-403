"""Data collector module"""

import random
import logging
from datetime import datetime, timezone
from typing import Optional, List, Callable, TYPE_CHECKING

from .config import FabricConfig
from .models import RequestRecord, MetricsSummary, EndpointStats, TimelineData
from .events import EventEmitter

if TYPE_CHECKING:
    from fabric.storage.base import BaseStorage

logger = logging.getLogger(__name__)


class MetricsCollector:
    """Metrics collector
    
    Responsible for collecting, processing and aggregating request metrics data.
    
    Attributes:
        config: Configuration object
        storage: Storage backend
        events: Event emitter
    """
    
    # Event name constants
    EVENT_REQUEST = "request"
    EVENT_ERROR = "error"
    EVENT_SLOW_REQUEST = "slow_request"
    
    def __init__(
        self,
        config: FabricConfig,
        storage: "BaseStorage"
    ) -> None:
        """Initialize collector
        
        Args:
            config: Configuration object
            storage: Storage backend instance
        """
        self.config = config
        self.storage = storage
        self.events = EventEmitter()
        
        # Slow request threshold (milliseconds)
        self.slow_request_threshold_ms: float = 1000.0
    
    def _should_sample(self) -> bool:
        """Decide whether to sample based on sample rate
        
        Returns:
            True if should sample
        """
        if self.config.sample_rate >= 1.0:
            return True
        return random.random() < self.config.sample_rate
    
    def _should_record(self, path: str) -> bool:
        """Check whether to record this request
        
        Args:
            path: Request path
            
        Returns:
            True if should record
        """
        if not self.config.enabled:
            return False
        
        if self.config.should_exclude_path(path):
            return False
        
        return self._should_sample()
    
    async def record_request(self, record: RequestRecord) -> None:
        """Record request
        
        Args:
            record: Request record
        """
        if not self._should_record(record.path):
            return
        
        try:
            # Save record
            await self.storage.save_request(record)
            
            # Emit request event
            await self.events.emit(self.EVENT_REQUEST, record)
            
            # Check if error request
            if record.is_error:
                await self.events.emit(self.EVENT_ERROR, record)
            
            # Check if slow request
            if record.duration_ms > self.slow_request_threshold_ms:
                await self.events.emit(self.EVENT_SLOW_REQUEST, record)
                
        except Exception as e:
            logger.error(f"Failed to record request: {e}")
    
    async def get_requests(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        path: Optional[str] = None,
        method: Optional[str] = None,
        status_code: Optional[int] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[RequestRecord]:
        """Get list of request records
        
        Args:
            start_time: Start time filter
            end_time: End time filter
            path: Path filter
            method: Method filter
            status_code: Status code filter
            limit: Maximum number of records to return
            offset: Offset for pagination
            
        Returns:
            List of request records
        """
        return await self.storage.get_requests(
            start_time=start_time,
            end_time=end_time,
            path=path,
            method=method,
            status_code=status_code,
            limit=limit,
            offset=offset
        )
    
    async def get_request_by_id(self, request_id: str) -> Optional[RequestRecord]:
        """Get request record by ID
        
        Args:
            request_id: Request ID
            
        Returns:
            Request record, or None if not found
        """
        return await self.storage.get_request_by_id(request_id)
    
    async def get_summary(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> MetricsSummary:
        """Get metrics summary
        
        Args:
            start_time: Start time filter
            end_time: End time filter
            
        Returns:
            Metrics summary object
        """
        return await self.storage.get_summary(start_time, end_time)
    
    async def get_endpoint_stats(
        self,
        path: str,
        method: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> EndpointStats:
        """Get endpoint statistics
        
        Args:
            path: Endpoint path
            method: HTTP method
            start_time: Start time filter
            end_time: End time filter
            
        Returns:
            Endpoint statistics object
        """
        return await self.storage.get_endpoint_stats(
            path, method, start_time, end_time
        )
    
    async def get_timeline(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        interval_seconds: int = 60
    ) -> TimelineData:
        """Get timeline data
        
        Args:
            start_time: Start time filter
            end_time: End time filter
            interval_seconds: Time interval in seconds
            
        Returns:
            Timeline data object
        """
        return await self.storage.get_timeline(
            start_time, end_time, interval_seconds
        )
    
    async def cleanup(self) -> int:
        """Clean up expired data
        
        Returns:
            Number of deleted records
        """
        from datetime import timedelta
        cutoff = datetime.now(timezone.utc) - timedelta(hours=self.config.retention_hours)
        return await self.storage.cleanup(cutoff)
    
    def on_request(self, handler: Callable) -> Callable:
        """Decorator: Register request event handler"""
        return self.events.on(self.EVENT_REQUEST)(handler)
    
    def on_error(self, handler: Callable) -> Callable:
        """Decorator: Register error event handler"""
        return self.events.on(self.EVENT_ERROR)(handler)
    
    def on_slow_request(self, handler: Callable) -> Callable:
        """Decorator: Register slow request event handler"""
        return self.events.on(self.EVENT_SLOW_REQUEST)(handler)
