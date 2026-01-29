"""Fabric main class"""

from typing import Any, Optional, TYPE_CHECKING, Callable, List

from .config import FabricConfig
from .collector import MetricsCollector
from .models import EndpointInfo

if TYPE_CHECKING:
    from fabric.storage.base import BaseStorage
    from fabric.adapters.base import BaseAdapter


class Fabric:
    """Fabric monitoring main class
    
    Main entry class for initializing and managing monitoring functionality.
    
    Example:
        >>> from fabric import Fabric, FabricConfig
        >>> from fastapi import FastAPI
        >>> 
        >>> app = FastAPI()
        >>> config = FabricConfig(app_name="My API")
        >>> fabric = Fabric(config)
        >>> fabric.setup(app)
    """
    
    def __init__(
        self,
        config: Optional[FabricConfig] = None,
        storage: Optional["BaseStorage"] = None
    ) -> None:
        """Initialize Fabric
        
        Args:
            config: Configuration object, uses default if not provided
            storage: Storage backend, auto-created based on config if not provided
        """
        self.config = config or FabricConfig()
        self._storage = storage
        self._adapter: Optional["BaseAdapter"] = None
        self._collector: Optional[MetricsCollector] = None
        self._app: Any = None
    
    @property
    def storage(self) -> "BaseStorage":
        """Get storage backend"""
        if self._storage is None:
            self._storage = self._create_storage()
        return self._storage
    
    @property
    def collector(self) -> MetricsCollector:
        """Get metrics collector"""
        if self._collector is None:
            self._collector = MetricsCollector(self.config, self.storage)
        return self._collector
    
    @property
    def adapter(self) -> Optional["BaseAdapter"]:
        """Get framework adapter"""
        return self._adapter
    
    def _create_storage(self) -> "BaseStorage":
        """Create storage backend based on config"""
        storage_type = self.config.storage_type.lower()
        
        if storage_type == "memory":
            from fabric.storage.memory import MemoryStorage
            return MemoryStorage(max_size=self.config.max_requests)
        
        # elif storage_type == "sqlite":
        #     from fabric.storage.sqlite import SQLiteStorage
        #     url = self.config.storage_url or "sqlite:///fabric.db"
        #     return SQLiteStorage(url)
        
        # elif storage_type == "redis":
        #     from fabric.storage.redis import RedisStorage
        #     if not self.config.storage_url:
        #         raise ValueError("Redis storage requires storage_url")
        #     return RedisStorage(self.config.storage_url)
        
        else:
            raise ValueError(f"Unknown storage type: {storage_type}")
    
    def _detect_framework(self, app: Any) -> str:
        """Detect web framework type
        
        Args:
            app: Application instance
            
        Returns:
            Framework type string
        """
        app_class = type(app).__name__
        app_module = type(app).__module__
        
        if "fastapi" in app_module.lower() or app_class == "FastAPI":
            return "fastapi"
        elif "flask" in app_module.lower() or app_class == "Flask":
            return "flask"
        elif "starlette" in app_module.lower() or app_class == "Starlette":
            return "starlette"
        else:
            raise ValueError(f"Unsupported framework: {app_class}")
    
    def _create_adapter(self, framework: str) -> "BaseAdapter":
        """Create framework adapter
        
        Args:
            framework: Framework type
            
        Returns:
            Adapter instance
        """
        if framework == "fastapi":
            from fabric.adapters.fastapi import FastAPIAdapter
            return FastAPIAdapter(self.config, self.collector)
        
        elif framework == "flask":
            from fabric.adapters.flask import FlaskAdapter
            return FlaskAdapter(self.config, self.collector)
        
        elif framework == "starlette":
            from fabric.adapters.fastapi import FastAPIAdapter
            return FastAPIAdapter(self.config, self.collector)
        
        else:
            raise ValueError(f"Unsupported framework: {framework}")
    
    def setup(self, app: Any, framework: Optional[str] = None) -> "Fabric":
        """Setup monitoring
        
        Integrate monitoring functionality into the web application.
        
        Args:
            app: Web application instance
            framework: Framework type, auto-detected if not provided
            
        Returns:
            self, supports method chaining
        """
        if not self.config.enabled:
            return self
        
        self._app = app
        
        # Detect or verify framework
        detected = self._detect_framework(app)
        if framework and framework != detected:
            raise ValueError(
                f"Framework mismatch: specified {framework}, detected {detected}"
            )
        framework = framework or detected
        
        # Create adapter
        self._adapter = self._create_adapter(framework)
        
        # Setup adapter
        self._adapter.setup(app)
        
        return self
    
    def get_endpoints(self) -> List[EndpointInfo]:
        """Get all API endpoint information
        
        Returns:
            List of endpoint information
        """
        if self._adapter is None:
            return []
        return self._adapter.get_endpoints()
    
    def on_request(self, handler: Callable) -> Callable:
        """Decorator: Register request event handler
        
        Example:
            >>> @fabric.on_request
            ... async def log_request(record):
            ...     print(f"Request: {record.path}")
        """
        return self.collector.on_request(handler)
    
    def on_error(self, handler: Callable) -> Callable:
        """Decorator: Register error event handler"""
        return self.collector.on_error(handler)
    
    def on_slow_request(self, handler: Callable) -> Callable:
        """Decorator: Register slow request event handler"""
        return self.collector.on_slow_request(handler)
