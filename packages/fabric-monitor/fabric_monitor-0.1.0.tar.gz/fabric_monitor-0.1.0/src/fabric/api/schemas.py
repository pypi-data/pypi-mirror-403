"""API Schema definitions"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

from fabric.core.models import (
    RequestRecord,
    EndpointInfo,
    MetricsSummary,
    EndpointStats,
    TimelineData
)


class HealthResponse(BaseModel):
    """Health check response"""
    status: str = Field(description="Status")
    version: str = Field(description="Version number")
    timestamp: datetime = Field(description="Timestamp")


class MetricsResponse(BaseModel):
    """Metrics response"""
    summary: MetricsSummary = Field(description="Metrics summary")
    timestamp: datetime = Field(description="Query time")


class TimelineResponse(BaseModel):
    """Timeline response"""
    timeline: TimelineData = Field(description="Timeline data")
    start_time: Optional[datetime] = Field(description="Start time")
    end_time: Optional[datetime] = Field(description="End time")


class RequestListResponse(BaseModel):
    """Request list response"""
    items: List[RequestRecord] = Field(description="Request record list")
    total: int = Field(description="Total count")
    page: int = Field(description="Current page number")
    page_size: int = Field(description="Page size")


class RequestDetailResponse(BaseModel):
    """Request detail response"""
    record: RequestRecord = Field(description="Request record")


class EndpointWithStats(BaseModel):
    """Endpoint info with statistics"""
    endpoint: EndpointInfo = Field(description="Endpoint info")
    stats: EndpointStats = Field(description="Statistics info")


class EndpointListResponse(BaseModel):
    """Endpoint list response"""
    endpoints: List[EndpointInfo] = Field(description="Endpoint list")
    total: int = Field(description="Total count")
    endpoint_stats: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Endpoint statistics list"
    )


class ConfigResponse(BaseModel):
    """Configuration response (security filtered)"""
    app_name: str = Field(description="Application name")
    prefix: str = Field(description="Route prefix")
    storage_type: str = Field(description="Storage type")
    max_requests: int = Field(description="Maximum requests")
    retention_hours: int = Field(description="Data retention time")
    sample_rate: float = Field(description="Sampling rate")
    exclude_paths: List[str] = Field(description="Excluded paths")


class ErrorResponse(BaseModel):
    """Error response"""
    error: str = Field(description="Error type")
    message: str = Field(description="Error message")
    detail: Optional[str] = Field(default=None, description="Detail info")
