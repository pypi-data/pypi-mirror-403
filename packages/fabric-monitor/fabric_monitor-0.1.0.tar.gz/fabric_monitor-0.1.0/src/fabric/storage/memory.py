"""Memory storage backend"""

import asyncio
from collections import deque
from datetime import datetime, timedelta
from typing import List, Optional, Dict
from statistics import mean, quantiles

from fabric.core.models import (
    RequestRecord,
    MetricsSummary,
    EndpointStats,
    TimelineData,
    TimelinePoint
)
from fabric.storage.base import BaseStorage


class MemoryStorage(BaseStorage):
    """Memory storage backend
    
    Stores data in memory, suitable for development and testing environments,
    as well as scenarios that don't require persistence.
    
    Attributes:
        max_size: Maximum number of records, old records are evicted when exceeded
    """
    
    def __init__(self, max_size: int = 10000) -> None:
        """Initialize memory storage
        
        Args:
            max_size: Maximum number of records
        """
        self.max_size = max_size
        self._records: deque[RequestRecord] = deque(maxlen=max_size)
        self._records_by_id: Dict[str, RequestRecord] = {}
        self._lock = asyncio.Lock()
    
    async def initialize(self) -> None:
        """Initialize storage"""
        pass
    
    async def close(self) -> None:
        """Close storage"""
        self._records.clear()
        self._records_by_id.clear()
    
    async def save_request(self, record: RequestRecord) -> None:
        """Save request record"""
        async with self._lock:
            # If max capacity reached, remove the oldest record
            if len(self._records) >= self.max_size:
                old_record = self._records[0]
                self._records_by_id.pop(old_record.id, None)
            
            self._records.append(record)
            self._records_by_id[record.id] = record
    
    async def get_request_by_id(self, request_id: str) -> Optional[RequestRecord]:
        """Get request record by ID"""
        return self._records_by_id.get(request_id)
    
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
        """Query request records"""
        filtered = self._filter_records(
            start_time, end_time, path, method, status_code
        )
        # Sort by timestamp in descending order
        filtered.sort(key=lambda r: r.timestamp, reverse=True)
        return filtered[offset:offset + limit]
    
    async def get_requests_count(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        path: Optional[str] = None,
        method: Optional[str] = None,
        status_code: Optional[int] = None
    ) -> int:
        """Get total count of request records"""
        filtered = self._filter_records(
            start_time, end_time, path, method, status_code
        )
        return len(filtered)
    
    def _filter_records(
        self,
        start_time: Optional[datetime],
        end_time: Optional[datetime],
        path: Optional[str],
        method: Optional[str],
        status_code: Optional[int]
    ) -> List[RequestRecord]:
        """Internal method to filter records"""
        result = []
        
        for record in self._records:
            # Time filter
            if start_time and record.timestamp < start_time:
                continue
            if end_time and record.timestamp > end_time:
                continue
            
            # Path filter (supports prefix matching)
            if path and not record.path.startswith(path):
                continue
            
            # Method filter
            if method and record.method.upper() != method.upper():
                continue
            
            # Status code filter
            if status_code is not None and record.status_code != status_code:
                continue
            
            result.append(record)
        
        return result
    
    async def get_summary(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> MetricsSummary:
        """Get metrics summary"""
        filtered = self._filter_records(start_time, end_time, None, None, None)
        
        if not filtered:
            return MetricsSummary(start_time=start_time, end_time=end_time)
        
        # Calculate basic metrics
        total = len(filtered)
        success = sum(1 for r in filtered if r.is_success)
        errors = total - success
        
        durations = [r.duration_ms for r in filtered]
        avg_duration = mean(durations) if durations else 0
        min_duration = min(durations) if durations else 0
        max_duration = max(durations) if durations else 0
        
        # Calculate percentiles
        p50, p95, p99 = 0.0, 0.0, 0.0
        if len(durations) >= 4:
            try:
                q = quantiles(durations, n=100)
                p50 = q[49] if len(q) > 49 else durations[len(durations) // 2]
                p95 = q[94] if len(q) > 94 else durations[-1]
                p99 = q[98] if len(q) > 98 else durations[-1]
            except Exception:
                p50 = durations[len(durations) // 2]
                p95 = durations[-1]
                p99 = durations[-1]
        elif durations:
            p50 = p95 = p99 = durations[len(durations) // 2]
        
        # Calculate RPS
        if filtered:
            time_range = (
                filtered[-1].timestamp - filtered[0].timestamp
            ).total_seconds()
            rps = total / time_range if time_range > 0 else total
        else:
            rps = 0
        
        # Status code distribution
        status_counts: Dict[int, int] = {}
        for record in filtered:
            code = record.status_code
            status_counts[code] = status_counts.get(code, 0) + 1
        
        # Calculate endpoint statistics
        endpoint_stats = await self._calculate_endpoint_stats(filtered)
        
        return MetricsSummary(
            total_requests=total,
            success_count=success,
            error_count=errors,
            avg_duration_ms=avg_duration,
            min_duration_ms=min_duration,
            max_duration_ms=max_duration,
            p50_duration_ms=p50,
            p95_duration_ms=p95,
            p99_duration_ms=p99,
            requests_per_second=rps,
            error_rate=errors / total if total > 0 else 0,
            start_time=start_time or (filtered[0].timestamp if filtered else None),
            end_time=end_time or (filtered[-1].timestamp if filtered else None),
            status_code_counts=status_counts,
            top_endpoints=endpoint_stats[:10],
            slowest_endpoints=sorted(
                endpoint_stats, 
                key=lambda e: e.avg_duration_ms, 
                reverse=True
            )[:10]
        )
    
    async def _calculate_endpoint_stats(
        self, 
        records: List[RequestRecord]
    ) -> List[EndpointStats]:
        """Calculate endpoint statistics"""
        endpoint_data: Dict[str, Dict] = {}
        
        for record in records:
            key = f"{record.method}:{record.route or record.path}"
            
            if key not in endpoint_data:
                endpoint_data[key] = {
                    "path": record.route or record.path,
                    "method": record.method,
                    "total": 0,
                    "success": 0,
                    "errors": 0,
                    "durations": [],
                    "last_request": None
                }
            
            data = endpoint_data[key]
            data["total"] += 1
            data["durations"].append(record.duration_ms)
            
            if record.is_success:
                data["success"] += 1
            else:
                data["errors"] += 1
            
            if data["last_request"] is None or record.timestamp > data["last_request"]:
                data["last_request"] = record.timestamp
        
        result = []
        for data in endpoint_data.values():
            durations = data["durations"]
            result.append(EndpointStats(
                path=data["path"],
                method=data["method"],
                total_requests=data["total"],
                success_count=data["success"],
                error_count=data["errors"],
                avg_duration_ms=mean(durations) if durations else 0,
                min_duration_ms=min(durations) if durations else 0,
                max_duration_ms=max(durations) if durations else 0,
                last_request_at=data["last_request"]
            ))
        
        # Sort by request count
        result.sort(key=lambda e: e.total_requests, reverse=True)
        return result
    
    async def get_endpoint_stats(
        self,
        path: str,
        method: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> EndpointStats:
        """Get endpoint statistics"""
        filtered = self._filter_records(start_time, end_time, path, method, None)
        
        if not filtered:
            return EndpointStats(path=path, method=method)
        
        durations = [r.duration_ms for r in filtered]
        success = sum(1 for r in filtered if r.is_success)
        
        return EndpointStats(
            path=path,
            method=method,
            total_requests=len(filtered),
            success_count=success,
            error_count=len(filtered) - success,
            avg_duration_ms=mean(durations) if durations else 0,
            min_duration_ms=min(durations) if durations else 0,
            max_duration_ms=max(durations) if durations else 0,
            last_request_at=filtered[-1].timestamp if filtered else None
        )
    
    async def get_timeline(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        interval_seconds: int = 60
    ) -> TimelineData:
        """Get timeline data"""
        filtered = self._filter_records(start_time, end_time, None, None, None)
        
        if not filtered:
            return TimelineData(interval_seconds=interval_seconds)
        
        # Determine time range
        actual_start = start_time or filtered[0].timestamp
        actual_end = end_time or filtered[-1].timestamp
        
        # Create time buckets
        interval = timedelta(seconds=interval_seconds)
        buckets: Dict[datetime, Dict] = {}
        
        current = actual_start.replace(second=0, microsecond=0)
        while current <= actual_end:
            buckets[current] = {
                "requests": 0,
                "errors": 0,
                "durations": []
            }
            current += interval
        
        # Populate data
        for record in filtered:
            bucket_time = record.timestamp.replace(second=0, microsecond=0)
            # Align to interval
            bucket_time = bucket_time - timedelta(
                seconds=bucket_time.second % interval_seconds
            )
            
            if bucket_time in buckets:
                buckets[bucket_time]["requests"] += 1
                buckets[bucket_time]["durations"].append(record.duration_ms)
                if record.is_error:
                    buckets[bucket_time]["errors"] += 1
        
        # Convert to timeline points
        points = []
        for ts in sorted(buckets.keys()):
            data = buckets[ts]
            points.append(TimelinePoint(
                timestamp=ts,
                requests=data["requests"],
                errors=data["errors"],
                avg_duration_ms=mean(data["durations"]) if data["durations"] else 0
            ))
        
        return TimelineData(points=points, interval_seconds=interval_seconds)
    
    async def cleanup(self, before: datetime) -> int:
        """Clean up expired data"""
        async with self._lock:
            original_count = len(self._records)
            
            # Filter out expired records
            new_records = deque(
                (r for r in self._records if r.timestamp >= before),
                maxlen=self.max_size
            )
            
            # Update index
            self._records_by_id = {r.id: r for r in new_records}
            self._records = new_records
            
            return original_count - len(self._records)
