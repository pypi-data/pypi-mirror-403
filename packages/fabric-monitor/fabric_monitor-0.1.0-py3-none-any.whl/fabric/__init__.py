"""
Fabric Monitor - Python Backend Service Monitoring Framework

Provides automatic API documentation generation, request recording,
response time statistics, and displays monitoring data through
a visualization dashboard.
"""

from fabric.core.config import FabricConfig
from fabric.core.models import RequestRecord, EndpointInfo, MetricsSummary
from fabric.core.collector import MetricsCollector
from fabric.core.fabric import Fabric

__version__ = "0.1.0"
__all__ = [
    "Fabric",
    "FabricConfig",
    "RequestRecord",
    "EndpointInfo",
    "MetricsSummary",
    "MetricsCollector",
]
