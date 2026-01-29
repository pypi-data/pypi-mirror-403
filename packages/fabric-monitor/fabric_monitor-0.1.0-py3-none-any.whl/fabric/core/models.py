"""Data model definitions"""

from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from enum import Enum
from pydantic import BaseModel, Field
import uuid


class RequestMethod(str, Enum):
    """HTTP request method enumeration"""
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    PATCH = "PATCH"
    OPTIONS = "OPTIONS"
    HEAD = "HEAD"
    TRACE = "TRACE"
    CONNECT = "CONNECT"


class RequestRecord(BaseModel):
    """Request record model
    
    Stores complete information about a single HTTP request, including request, response and performance data.
    
    Attributes:
        id: Unique identifier
        timestamp: Request timestamp
        method: HTTP method
        path: Request path
        full_url: Full URL
        query_params: Query parameters
        headers: Request headers
        body: Request body
        client_ip: Client IP
        status_code: Response status code
        response_headers: Response headers
        response_body: Response body
        duration_ms: Response time (milliseconds)
        error: Error message
        tags: Custom tags
        route: Route template (e.g., /users/{id})
        endpoint_name: Endpoint name
    """
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique identifier")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Request timestamp")
    method: str = Field(description="HTTP method")
    path: str = Field(description="Request path")
    full_url: str = Field(default="", description="Full URL")
    
    # Request information
    query_params: Dict[str, Any] = Field(default_factory=dict, description="Query parameters")
    headers: Dict[str, str] = Field(default_factory=dict, description="Request headers")
    body: Optional[str] = Field(default=None, description="Request body")
    client_ip: str = Field(default="", description="Client IP")
    
    # Response information
    status_code: int = Field(default=0, description="Response status code")
    response_headers: Dict[str, str] = Field(default_factory=dict, description="Response headers")
    response_body: Optional[str] = Field(default=None, description="Response body")
    
    # Performance metrics
    duration_ms: float = Field(default=0.0, description="Response time (milliseconds)")
    
    # Extra information
    error: Optional[str] = Field(default=None, description="Error message")
    tags: Dict[str, str] = Field(default_factory=dict, description="Custom tags")
    route: Optional[str] = Field(default=None, description="Route template")
    endpoint_name: Optional[str] = Field(default=None, description="Endpoint name")
    
    @property
    def is_success(self) -> bool:
        """Check if request is successful"""
        return 200 <= self.status_code < 400
    
    @property
    def is_error(self) -> bool:
        """Check if request has error"""
        return self.status_code >= 400 or self.error is not None


class ParameterInfo(BaseModel):
    """Parameter info model"""
    name: str = Field(description="Parameter name")
    location: str = Field(description="Parameter location: path | query | header | body")
    type: str = Field(default="string", description="Parameter type")
    required: bool = Field(default=False, description="Is required")
    description: Optional[str] = Field(default=None, description="Parameter description")
    default: Optional[Any] = Field(default=None, description="Default value")
    example: Optional[Any] = Field(default=None, description="Example value")


class EndpointInfo(BaseModel):
    """Endpoint info model
    
    Stores metadata information about API endpoints.
    
    Attributes:
        path: Path template
        method: HTTP method
        name: Endpoint name
        description: Endpoint description
        tags: Tag list
        parameters: Parameter list
        request_body: Request body definition
        responses: Response definitions
        deprecated: Whether deprecated
    """
    
    path: str = Field(description="Path template")
    method: str = Field(description="HTTP method")
    name: Optional[str] = Field(default=None, description="Endpoint name")
    description: Optional[str] = Field(default=None, description="Endpoint description")
    tags: List[str] = Field(default_factory=list, description="Tags")
    parameters: List[ParameterInfo] = Field(default_factory=list, description="Parameter list")
    request_body: Optional[Dict[str, Any]] = Field(default=None, description="Request body")
    responses: Dict[str, Any] = Field(default_factory=dict, description="Response definitions")
    deprecated: bool = Field(default=False, description="Is deprecated")
    
    @property
    def full_path(self) -> str:
        """Return combination of method and path"""
        return f"{self.method} {self.path}"


class EndpointStats(BaseModel):
    """Endpoint statistics info"""
    path: str
    method: str
    total_requests: int = 0
    success_count: int = 0
    error_count: int = 0
    avg_duration_ms: float = 0
    min_duration_ms: float = 0
    max_duration_ms: float = 0
    last_request_at: Optional[datetime] = None


class MetricsSummary(BaseModel):
    """Metrics summary model
    
    Stores aggregated metrics data over a period of time.
    
    Attributes:
        total_requests: Total request count
        success_count: Success request count
        error_count: Error request count
        avg_duration_ms: Average response time
        min_duration_ms: Minimum response time
        max_duration_ms: Maximum response time
        p50_duration_ms: P50 response time
        p95_duration_ms: P95 response time
        p99_duration_ms: P99 response time
        requests_per_second: Requests per second
        error_rate: Error rate
        start_time: Statistics start time
        end_time: Statistics end time
    """
    
    total_requests: int = Field(default=0, description="Total request count")
    success_count: int = Field(default=0, description="Success request count")
    error_count: int = Field(default=0, description="Error request count")
    
    avg_duration_ms: float = Field(default=0.0, description="Average response time")
    min_duration_ms: float = Field(default=0.0, description="Minimum response time")
    max_duration_ms: float = Field(default=0.0, description="Maximum response time")
    p50_duration_ms: float = Field(default=0.0, description="P50 response time")
    p95_duration_ms: float = Field(default=0.0, description="P95 response time")
    p99_duration_ms: float = Field(default=0.0, description="P99 response time")
    
    requests_per_second: float = Field(default=0.0, description="Requests per second")
    error_rate: float = Field(default=0.0, description="Error rate")
    
    start_time: Optional[datetime] = Field(default=None, description="Statistics start time")
    end_time: Optional[datetime] = Field(default=None, description="Statistics end time")
    
    # Request count grouped by status code
    status_code_counts: Dict[int, int] = Field(default_factory=dict, description="Status code distribution")
    
    # Endpoint statistics
    top_endpoints: List[EndpointStats] = Field(default_factory=list, description="Top endpoints")
    slowest_endpoints: List[EndpointStats] = Field(default_factory=list, description="Slowest endpoints")


class TimelinePoint(BaseModel):
    """Timeline data point"""
    timestamp: datetime
    requests: int = 0
    errors: int = 0
    avg_duration_ms: float = 0


class TimelineData(BaseModel):
    """Timeline data"""
    points: List[TimelinePoint] = Field(default_factory=list)
    interval_seconds: int = Field(default=60, description="Time interval (seconds)")
