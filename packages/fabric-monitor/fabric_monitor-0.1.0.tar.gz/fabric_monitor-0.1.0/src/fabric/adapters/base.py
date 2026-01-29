"""Adapter base class"""

from abc import ABC, abstractmethod
from typing import Any, List, TYPE_CHECKING

from fabric.core.config import FabricConfig
from fabric.core.models import EndpointInfo

if TYPE_CHECKING:
    from fabric.core.collector import MetricsCollector


class BaseAdapter(ABC):
    """Abstract base class for framework adapters
    
    Defines the interface that adapters must implement. Each supported Web framework
    needs to implement its own adapter.
    
    Attributes:
        config: Fabric configuration object
        collector: Metrics collector
    """
    
    def __init__(
        self,
        config: FabricConfig,
        collector: "MetricsCollector"
    ) -> None:
        """Initialize adapter
        
        Args:
            config: Configuration object
            collector: Metrics collector
        """
        self.config = config
        self.collector = collector
        self._app: Any = None
    
    @property
    def app(self) -> Any:
        """Get application instance"""
        return self._app
    
    @abstractmethod
    def setup(self, app: Any) -> None:
        """Setup adapter
        
        Integrate monitoring functionality into the application, including:
        - Register middleware
        - Mount API routes
        - Mount static resources
        
        Args:
            app: Web application instance
        """
        pass
    
    @abstractmethod
    def get_endpoints(self) -> List[EndpointInfo]:
        """Get all API endpoint information
        
        Extract endpoint definition information from the application.
        
        Returns:
            List of endpoint information
        """
        pass
    
    @abstractmethod
    def mount_api(self, app: Any) -> None:
        """Mount internal API
        
        Mount Fabric's API endpoints to the application.
        
        Args:
            app: Web application instance
        """
        pass
    
    @abstractmethod
    def mount_dashboard(self, app: Any) -> None:
        """Mount monitoring dashboard
        
        Mount frontend static resources to the application.
        
        Args:
            app: Web application instance
        """
        pass
