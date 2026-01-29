"""Storage backend base class"""

from abc import ABC, abstractmethod
from typing import List, Optional
from datetime import datetime

from fabric.core.models import (
    RequestRecord,
    MetricsSummary,
    EndpointStats,
    TimelineData
)


class BaseStorage(ABC):
    """Abstract base class for storage backends
    
    Defines the interface that all storage backends must implement.
    All storage backends (memory, SQLite, Redis, etc.) must inherit
    from this class and implement all abstract methods.
    """
    
    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the storage
        
        Called before first use of storage to create necessary tables, indexes, etc.
        """
        pass
    
    @abstractmethod
    async def close(self) -> None:
        """Close the storage
        
        Release resources, close connections, etc.
        """
        pass
    
    @abstractmethod
    async def save_request(self, record: RequestRecord) -> None:
        """Save a request record
        
        Args:
            record: The request record object
        """
        pass
    
    @abstractmethod
    async def get_request_by_id(self, request_id: str) -> Optional[RequestRecord]:
        """Get a request record by ID
        
        Args:
            request_id: The request ID
            
        Returns:
            The request record, or None if not found
        """
        pass
    
    @abstractmethod
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
        """Query request records
        
        Args:
            start_time: Start time filter
            end_time: End time filter
            path: Path filter (supports prefix matching)
            method: HTTP method filter
            status_code: Status code filter
            limit: Maximum number of records to return
            offset: Offset for pagination
            
        Returns:
            List of request records
        """
        pass
    
    @abstractmethod
    async def get_requests_count(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        path: Optional[str] = None,
        method: Optional[str] = None,
        status_code: Optional[int] = None
    ) -> int:
        """Get total count of request records
        
        Args:
            start_time: Start time filter
            end_time: End time filter
            path: Path filter
            method: HTTP method filter
            status_code: Status code filter
            
        Returns:
            Total count of records
        """
        pass
    
    @abstractmethod
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
        pass
    
    @abstractmethod
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
        pass
    
    @abstractmethod
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
        pass
    
    @abstractmethod
    async def cleanup(self, before: datetime) -> int:
        """Clean up expired data
        
        Args:
            before: Delete records before this timestamp
            
        Returns:
            Number of deleted records
        """
        pass
