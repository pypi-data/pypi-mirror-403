"""FastAPI adapter"""

import time
import uuid
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Any, Callable, Optional

from fabric.adapters.base import BaseAdapter
from fabric.core.config import FabricConfig
from fabric.core.collector import MetricsCollector
from fabric.core.models import RequestRecord, EndpointInfo, ParameterInfo

logger = logging.getLogger(__name__)


class FastAPIAdapter(BaseAdapter):
    """FastAPI adapter
    
    Provides monitoring support for FastAPI applications.
    """
    
    def setup(self, app: Any) -> None:
        """Setup FastAPI application
        
        Args:
            app: FastAPI application instance
        """
        self._app = app
        
        # Delayed import to avoid import errors when fastapi is not installed
        try:
            from starlette.middleware.base import BaseHTTPMiddleware
        except ImportError:
            raise ImportError(
                "FastAPI/Starlette is not installed. "
                "Install it with: pip install fabric-monitor[fastapi]"
            )
        
        # Add middleware
        app.add_middleware(
            BaseHTTPMiddleware,
            dispatch=self._create_middleware()
        )
        
        # Mount API
        self.mount_api(app)
        
        # Mount dashboard
        self.mount_dashboard(app)
        
        logger.info(
            f"Fabric monitoring enabled at {self.config.prefix}"
        )
    
    def _create_middleware(self) -> Callable:
        """Create monitoring middleware"""
        adapter = self
        
        async def middleware(request: Any, call_next: Callable) -> Any:
            """Monitoring middleware"""
            # Skip requests to the monitor panel itself
            if request.url.path.startswith(adapter.config.prefix):
                return await call_next(request)
            
            start_time = time.perf_counter()
            
            # Build request record
            record = RequestRecord(
                id=str(uuid.uuid4()),
                timestamp=datetime.now(timezone.utc),
                method=request.method,
                path=request.url.path,
                full_url=str(request.url),
                query_params=dict(request.query_params),
                headers={k: v for k, v in request.headers.items()},
                client_ip=request.client.host if request.client else "",
            )
            
            # Get route info
            route = self._get_route_for_request(request)
            if route:
                record.route = route.get("path")
                record.endpoint_name = route.get("name")
            
            # Record request body (if enabled in config)
            if adapter.config.record_request_body:
                try:
                    body = await request.body()
                    if len(body) <= adapter.config.max_body_size:
                        record.body = body.decode("utf-8", errors="replace")
                except Exception:
                    pass
            
            response = None
            error_msg = None
            
            try:
                response = await call_next(request)
                record.status_code = response.status_code
                record.response_headers = dict(response.headers)
                
                # Record response body (if enabled in config)
                if adapter.config.record_response_body:
                    try:
                        # Read response body - need to consume and recreate
                        response_body = b""
                        async for chunk in response.body_iterator:
                            response_body += chunk
                        
                        if len(response_body) <= adapter.config.max_body_size:
                            record.response_body = response_body.decode("utf-8", errors="replace")
                        
                        # Recreate response with the same body
                        from starlette.responses import Response
                        response = Response(
                            content=response_body,
                            status_code=response.status_code,
                            headers=dict(response.headers),
                            media_type=response.media_type
                        )
                    except Exception as e:
                        logger.debug(f"Failed to record response body: {e}")
                        
            except Exception as e:
                record.status_code = 500
                record.error = str(e)
                error_msg = str(e)
                raise
            finally:
                record.duration_ms = (time.perf_counter() - start_time) * 1000
                
                # Async record request
                try:
                    await adapter.collector.record_request(record)
                except Exception as e:
                    logger.error(f"Failed to record request: {e}")
            
            return response
        
        return middleware
    
    def _get_route_for_request(self, request: Any) -> Optional[dict]:
        """Get route info for a request"""
        try:
            from fastapi.routing import APIRoute
            
            for route in self._app.routes:
                if isinstance(route, APIRoute):
                    # Check if path matches
                    match = route.path_regex.match(request.url.path)
                    if match and request.method in route.methods:
                        return {
                            "path": route.path,
                            "name": route.name,
                        }
        except Exception:
            pass
        return None
    
    def get_endpoints(self) -> List[EndpointInfo]:
        """Extract endpoint info from FastAPI"""
        endpoints = []
        
        try:
            from fastapi.routing import APIRoute
            
            for route in self._app.routes:
                if not isinstance(route, APIRoute):
                    continue
                
                # Skip Fabric's own routes
                if route.path.startswith(self.config.prefix):
                    continue
                
                for method in route.methods or ["GET"]:
                    endpoint = EndpointInfo(
                        path=route.path,
                        method=method,
                        name=route.name,
                        description=route.description or "",
                        tags=list(route.tags) if route.tags else [],
                        deprecated=route.deprecated or False,
                    )
                    
                    # Extract parameter info
                    endpoint.parameters = self._extract_parameters(route)
                    
                    # Extract response info
                    if route.response_model:
                        endpoint.responses["200"] = {
                            "model": str(route.response_model)
                        }
                    
                    endpoints.append(endpoint)
                    
        except Exception as e:
            logger.error(f"Failed to extract endpoints: {e}")
        
        return endpoints
    
    def _extract_parameters(self, route: Any) -> List[ParameterInfo]:
        """Extract parameter info from route"""
        parameters = []
        
        try:
            # Extract path parameters from path
            import re
            path_params = re.findall(r"\{(\w+)\}", route.path)
            for param in path_params:
                parameters.append(ParameterInfo(
                    name=param,
                    location="path",
                    required=True
                ))
            
            # Extract query parameters from dependencies (simplified implementation)
            if hasattr(route, "dependant") and route.dependant:
                for dep in getattr(route.dependant, "query_params", []):
                    parameters.append(ParameterInfo(
                        name=dep.name,
                        location="query",
                        type=str(dep.type_annotation) if dep.type_annotation else "string",
                        required=dep.required,
                        default=dep.default if dep.default is not ... else None
                    ))
                    
        except Exception as e:
            logger.debug(f"Failed to extract parameters: {e}")
        
        return parameters
    
    def mount_api(self, app: Any) -> None:
        """Mount Fabric API"""
        from fabric.api.router import create_api_router
        
        api_router = create_api_router(self.collector, self)
        app.include_router(
            api_router,
            prefix=f"{self.config.prefix}/api",
            tags=["Fabric Monitor"]
        )
    
    def mount_dashboard(self, app: Any) -> None:
        """Mount frontend dashboard"""
        from starlette.staticfiles import StaticFiles
        from starlette.responses import FileResponse, HTMLResponse, RedirectResponse
        
        # Find frontend build directory
        dashboard_dist = Path(__file__).parent.parent / "dashboard" / "dist"
        index_html = dashboard_dist / "index.html"
        
        # Redirect to path with trailing slash for correct relative path resolution
        async def redirect_to_dashboard():
            """Redirect to dashboard (with trailing slash)"""
            return RedirectResponse(url=f"{self.config.prefix}/", status_code=302)
        
        async def serve_index():
            """Serve index page"""
            if index_html.exists():
                return FileResponse(index_html)
            return HTMLResponse(self._get_fallback_html())
        
        async def serve_spa(path: str = ""):
            """Handle SPA routing"""
            # API and assets requests are not handled here
            if path.startswith("api/") or path.startswith("assets/"):
                return None
            if index_html.exists():
                return FileResponse(index_html)
            return HTMLResponse(self._get_fallback_html())
        
        if dashboard_dist.exists() and (dashboard_dist / "assets").exists():
            # Mount static assets - must be mounted first
            app.mount(
                f"{self.config.prefix}/assets",
                StaticFiles(directory=dashboard_dist / "assets"),
                name="fabric_assets"
            )
        
        # Register routes
        # /fabric -> redirect to /fabric/
        app.add_api_route(
            self.config.prefix,
            redirect_to_dashboard,
            methods=["GET"],
            include_in_schema=False
        )
        # /fabric/ -> serve index.html
        app.add_api_route(
            f"{self.config.prefix}/",
            serve_index,
            methods=["GET"],
            include_in_schema=False
        )
        # /fabric/{path} -> SPA routing
        app.add_api_route(
            f"{self.config.prefix}/{{path:path}}",
            serve_spa,
            methods=["GET"],
            include_in_schema=False
        )
    
    def _get_fallback_html(self) -> str:
        """Return fallback HTML"""
        return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Fabric Monitor</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background-color: #0f172a;
            color: #e2e8f0;
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 2rem;
        }
        .container {
            text-align: center;
            max-width: 500px;
        }
        .icon {
            font-size: 4rem;
            margin-bottom: 1.5rem;
            display: inline-block;
            animation: pulse 2s ease-in-out infinite;
        }
        @keyframes pulse {
            0%, 100% { transform: scale(1); }
            50% { transform: scale(1.1); }
        }
        h1 {
            font-size: 2rem;
            font-weight: 700;
            margin-bottom: 0.5rem;
            color: #f8fafc;
        }
        .subtitle {
            font-size: 1rem;
            color: #94a3b8;
            margin-bottom: 2rem;
        }
        .card {
            background-color: #1e293b;
            border: 1px solid #334155;
            border-radius: 12px;
            padding: 1.5rem;
            margin-bottom: 1.5rem;
        }
        .card-title {
            font-size: 0.875rem;
            font-weight: 600;
            color: #f59e0b;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            margin-bottom: 1rem;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 0.5rem;
        }
        .code-block {
            background-color: #0f172a;
            border: 1px solid #334155;
            border-radius: 8px;
            padding: 1rem;
            font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
            font-size: 0.875rem;
            color: #a5f3fc;
            text-align: left;
            overflow-x: auto;
        }
        .code-block .comment {
            color: #64748b;
        }
        .code-block .command {
            color: #4ade80;
        }
        .links {
            display: flex;
            gap: 1rem;
            justify-content: center;
            flex-wrap: wrap;
        }
        .btn {
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
            padding: 0.75rem 1.5rem;
            border-radius: 8px;
            font-size: 0.875rem;
            font-weight: 500;
            text-decoration: none;
            transition: all 0.2s ease;
        }
        .btn-primary {
            background-color: #3b82f6;
            color: white;
        }
        .btn-primary:hover {
            background-color: #2563eb;
            transform: translateY(-2px);
        }
        .btn-secondary {
            background-color: #334155;
            color: #e2e8f0;
        }
        .btn-secondary:hover {
            background-color: #475569;
            transform: translateY(-2px);
        }
        .status {
            margin-top: 2rem;
            padding-top: 1.5rem;
            border-top: 1px solid #334155;
        }
        .status-item {
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 0.5rem;
            font-size: 0.875rem;
            color: #94a3b8;
        }
        .status-dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background-color: #22c55e;
            animation: blink 1.5s ease-in-out infinite;
        }
        @keyframes blink {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="icon">🔍</div>
        <h1>Fabric Monitor</h1>
        <p class="subtitle">Dashboard assets not found</p>
        
        <div class="card">
            <div class="card-title">
                <span>⚡</span> Build Instructions
            </div>
            <div class="code-block">
                <div class="comment"># Navigate to dashboard directory</div>
                <div class="command">cd src/fabric/dashboard</div>
                <br>
                <div class="comment"># Install dependencies</div>
                <div class="command">npm install</div>
                <br>
                <div class="comment"># Build for production</div>
                <div class="command">npm run build</div>
            </div>
        </div>
        
        <div class="links">
            <a href="./api/health" class="btn btn-primary">
                <span>✓</span> API Health
            </a>
            <a href="./api/metrics" class="btn btn-secondary">
                <span>📊</span> Metrics
            </a>
        </div>
        
        <div class="status">
            <div class="status-item">
                <span class="status-dot"></span>
                <span>API is running</span>
            </div>
        </div>
    </div>
</body>
</html>
"""
