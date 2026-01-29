"""Configuration management module"""

from typing import Optional, List
from pydantic import BaseModel, Field


class FabricConfig(BaseModel):
    """Fabric configuration class
    
    Configure various parameters of the monitoring framework, including storage, sampling, path filtering, etc.
    
    Attributes:
        app_name: Application name, displayed on the monitoring dashboard
        prefix: Route prefix for the monitoring dashboard
        enabled: Whether monitoring is enabled
        storage_type: Storage backend type (memory, sqlite, redis)
        storage_url: Storage connection URL
        max_requests: Maximum number of request records
        retention_hours: Data retention time (hours)
        sample_rate: Sampling rate (0.0-1.0)
        exclude_paths: List of paths to exclude
        include_paths: List of paths to include (empty means include all)
        enable_auth: Whether to enable dashboard authentication
        auth_token: Authentication token
        record_request_body: Whether to record request body
        record_response_body: Whether to record response body
        max_body_size: Maximum request/response body size to record (bytes)
    """
    
    # Basic configuration
    app_name: str = Field(default="Fabric Monitor", description="Application name")
    prefix: str = Field(default="/fabric", description="Dashboard route prefix")
    enabled: bool = Field(default=True, description="Whether monitoring is enabled")
    
    # Storage configuration
    storage_type: str = Field(default="memory", description="Storage type: memory | sqlite | redis")
    storage_url: Optional[str] = Field(default=None, description="Storage connection URL")
    
    # Data retention
    max_requests: int = Field(default=10000, ge=100, description="Maximum request records")
    retention_hours: int = Field(default=24, ge=1, description="Data retention time (hours)")
    
    # Sampling configuration
    sample_rate: float = Field(default=1.0, ge=0.0, le=1.0, description="Sampling rate")
    
    # Path filtering
    exclude_paths: List[str] = Field(default_factory=list, description="Excluded paths")
    include_paths: List[str] = Field(default_factory=list, description="Included paths")
    
    # Security configuration
    enable_auth: bool = Field(default=False, description="Whether authentication is enabled")
    auth_token: Optional[str] = Field(default=None, description="Authentication token")
    
    # Recording configuration
    record_request_body: bool = Field(default=False, description="Whether to record request body")
    record_response_body: bool = Field(default=False, description="Whether to record response body")
    max_body_size: int = Field(default=10240, description="Maximum body size (bytes)")
    
    class Config:
        """Pydantic configuration"""
        validate_assignment = True
    
    def should_exclude_path(self, path: str) -> bool:
        """Check if path should be excluded
        
        Args:
            path: Request path
            
        Returns:
            True if should be excluded
        """
        # Exclude the monitoring dashboard's own path
        if path.startswith(self.prefix):
            return True
        
        # Check exclude list
        for exclude in self.exclude_paths:
            if path.startswith(exclude) or path == exclude:
                return True
        
        # If include list is set, check if path is in the include list
        if self.include_paths:
            for include in self.include_paths:
                if path.startswith(include) or path == include:
                    return False
            return True
        
        return False
