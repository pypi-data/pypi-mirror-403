"""API routes"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from fabric.core.collector import MetricsCollector
    from fabric.adapters.base import BaseAdapter


def create_api_router(
    collector: "MetricsCollector",
    adapter: "BaseAdapter"
):
    """Create API router
    
    Args:
        collector: Metrics collector
        adapter: Framework adapter
        
    Returns:
        FastAPI Router instance
    """
    from fastapi import APIRouter, Query, HTTPException
    from fastapi.responses import JSONResponse
    from datetime import datetime, timedelta, timezone
    from typing import Optional, List
    
    from fabric.api.schemas import (
        HealthResponse,
        MetricsResponse,
        RequestListResponse,
        RequestDetailResponse,
        EndpointListResponse,
        TimelineResponse,
        ConfigResponse
    )
    
    router = APIRouter()
    
    @router.get("/health", response_model=HealthResponse)
    async def health_check():
        """Health check"""
        return HealthResponse(
            status="healthy",
            version="0.1.0",
            timestamp=datetime.now(timezone.utc)
        )
    
    @router.get("/metrics", response_model=MetricsResponse)
    async def get_metrics(
        start_time: Optional[datetime] = Query(None, description="Start time"),
        end_time: Optional[datetime] = Query(None, description="End time"),
        hours: Optional[int] = Query(1, description="Past N hours", ge=1, le=168)
    ):
        """Get metrics summary"""
        # If no time range specified, use past N hours
        if start_time is None and end_time is None:
            end_time = datetime.now(timezone.utc)
            start_time = end_time - timedelta(hours=hours)
        
        summary = await collector.get_summary(start_time, end_time)
        
        return MetricsResponse(
            summary=summary,
            timestamp=datetime.now(timezone.utc)
        )
    
    @router.get("/metrics/timeline", response_model=TimelineResponse)
    async def get_timeline(
        start_time: Optional[datetime] = Query(None, description="Start time"),
        end_time: Optional[datetime] = Query(None, description="End time"),
        hours: Optional[int] = Query(1, description="Past N hours", ge=1, le=168),
        interval: int = Query(60, description="Time interval (seconds)", ge=10, le=3600)
    ):
        """Get timeline data"""
        if start_time is None and end_time is None:
            end_time = datetime.now(timezone.utc)
            start_time = end_time - timedelta(hours=hours)
        
        timeline = await collector.get_timeline(start_time, end_time, interval)
        
        return TimelineResponse(
            timeline=timeline,
            start_time=start_time,
            end_time=end_time
        )
    
    @router.get("/requests", response_model=RequestListResponse)
    async def get_requests(
        start_time: Optional[datetime] = Query(None),
        end_time: Optional[datetime] = Query(None),
        path: Optional[str] = Query(None, description="Path filter"),
        method: Optional[str] = Query(None, description="HTTP method"),
        status_code: Optional[int] = Query(None, description="Status code"),
        page: int = Query(1, ge=1, description="Page number"),
        page_size: int = Query(50, ge=1, le=200, description="Page size")
    ):
        """Get request records list"""
        offset = (page - 1) * page_size
        
        requests = await collector.get_requests(
            start_time=start_time,
            end_time=end_time,
            path=path,
            method=method,
            status_code=status_code,
            limit=page_size,
            offset=offset
        )
        
        # Get total count (simplified implementation, may need optimization)
        total = await collector.storage.get_requests_count(
            start_time=start_time,
            end_time=end_time,
            path=path,
            method=method,
            status_code=status_code
        )
        
        return RequestListResponse(
            items=requests,
            total=total,
            page=page,
            page_size=page_size
        )
    
    @router.get("/requests/{request_id}", response_model=RequestDetailResponse)
    async def get_request_detail(request_id: str):
        """Get request detail"""
        record = await collector.get_request_by_id(request_id)
        
        if record is None:
            raise HTTPException(status_code=404, detail="Request not found")
        
        return RequestDetailResponse(record=record)
    
    @router.get("/endpoints", response_model=EndpointListResponse)
    async def get_endpoints():
        """Get endpoint list"""
        endpoints = adapter.get_endpoints()
        
        # Add statistics for each endpoint
        endpoint_stats = []
        for endpoint in endpoints:
            stats = await collector.get_endpoint_stats(
                endpoint.path,
                endpoint.method
            )
            endpoint_stats.append({
                "endpoint": endpoint,
                "stats": stats
            })
        
        return EndpointListResponse(
            endpoints=endpoints,
            total=len(endpoints),
            endpoint_stats=endpoint_stats
        )
    
    @router.get("/config", response_model=ConfigResponse)
    async def get_config():
        """Get configuration (security filtered)"""
        config = adapter.config
        
        return ConfigResponse(
            app_name=config.app_name,
            prefix=config.prefix,
            storage_type=config.storage_type,
            max_requests=config.max_requests,
            retention_hours=config.retention_hours,
            sample_rate=config.sample_rate,
            exclude_paths=config.exclude_paths
        )
    
    @router.post("/cleanup")
    async def cleanup_data(
        hours: int = Query(24, description="Clean data older than N hours", ge=1)
    ):
        """Clean up expired data"""
        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
        deleted = await collector.storage.cleanup(cutoff)
        
        return {"deleted": deleted, "cutoff": cutoff.isoformat()}
    
    return router
