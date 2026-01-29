"""Flask adapter"""

import time
import uuid
import logging
import threading
import asyncio
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Any, Optional
from functools import wraps

from fabric.adapters.base import BaseAdapter
from fabric.core.models import RequestRecord, EndpointInfo, ParameterInfo

logger = logging.getLogger(__name__)


class FlaskAdapter(BaseAdapter):
    """Flask adapter
    
    Provides monitoring support for Flask applications.
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._thread: Optional[threading.Thread] = None
    
    def setup(self, app: Any) -> None:
        """Setup Flask application
        
        Args:
            app: Flask application instance
        """
        self._app = app
        
        # Delayed import to avoid import errors when flask is not installed
        try:
            from flask import Flask, request, g
        except ImportError:
            raise ImportError(
                "Flask is not installed. "
                "Install it with: pip install fabric-monitor[flask]"
            )
        
        # Start async event loop in background thread
        self._start_async_loop()
        
        # Register before/after request hooks
        @app.before_request
        def before_request():
            # Skip monitoring panel requests
            if request.path.startswith(self.config.prefix):
                return
            
            g.fabric_start_time = time.perf_counter()
            g.fabric_request_id = str(uuid.uuid4())
        
        @app.after_request
        def after_request(response):
            # Skip monitoring panel requests
            if request.path.startswith(self.config.prefix):
                return response
            
            # Skip if before_request didn't run
            if not hasattr(g, 'fabric_start_time'):
                return response
            
            duration_ms = (time.perf_counter() - g.fabric_start_time) * 1000
            
            # Build request record
            record = RequestRecord(
                id=g.fabric_request_id,
                timestamp=datetime.now(timezone.utc),
                method=request.method,
                path=request.path,
                full_url=request.url,
                query_params=dict(request.args),
                headers={k: v for k, v in request.headers},
                client_ip=request.remote_addr or "",
                status_code=response.status_code,
                response_headers=dict(response.headers),
                duration_ms=duration_ms,
            )
            
            # Get route info
            route_info = self._get_route_for_request(request)
            if route_info:
                record.route = route_info.get("path")
                record.endpoint_name = route_info.get("name")
            
            # Record request body (if enabled in config)
            if self.config.record_request_body and request.data:
                try:
                    if len(request.data) <= self.config.max_body_size:
                        record.body = request.data.decode("utf-8", errors="replace")
                except Exception:
                    pass
            
            # Record response body (if enabled in config)
            if self.config.record_response_body:
                try:
                    response_data = response.get_data()
                    if len(response_data) <= self.config.max_body_size:
                        record.response_body = response_data.decode("utf-8", errors="replace")
                except Exception:
                    pass
            
            # Async record request
            self._run_async(self.collector.record_request(record))
            
            return response
        
        @app.errorhandler(Exception)
        def handle_error(error):
            # Record error if we have context
            if hasattr(g, 'fabric_start_time'):
                duration_ms = (time.perf_counter() - g.fabric_start_time) * 1000
                
                record = RequestRecord(
                    id=getattr(g, 'fabric_request_id', str(uuid.uuid4())),
                    timestamp=datetime.now(timezone.utc),
                    method=request.method,
                    path=request.path,
                    full_url=request.url,
                    query_params=dict(request.args),
                    headers={k: v for k, v in request.headers},
                    client_ip=request.remote_addr or "",
                    status_code=500,
                    duration_ms=duration_ms,
                    error=str(error),
                )
                
                self._run_async(self.collector.record_request(record))
            
            # Re-raise the error for Flask's default handling
            raise error
        
        # Mount API and dashboard
        self.mount_api(app)
        self.mount_dashboard(app)
        
        logger.info(
            f"Fabric monitoring enabled at {self.config.prefix}"
        )
    
    def _start_async_loop(self) -> None:
        """Start async event loop in background thread"""
        def run_loop():
            self._loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._loop)
            self._loop.run_forever()
        
        self._thread = threading.Thread(target=run_loop, daemon=True)
        self._thread.start()
        
        # Wait for loop to start
        while self._loop is None:
            time.sleep(0.01)
    
    def _run_async(self, coro) -> None:
        """Run async coroutine from sync context"""
        if self._loop is not None:
            asyncio.run_coroutine_threadsafe(coro, self._loop)
    
    def _get_route_for_request(self, request: Any) -> Optional[dict]:
        """Get route info for a request"""
        try:
            if request.url_rule:
                return {
                    "path": request.url_rule.rule,
                    "name": request.endpoint,
                }
        except Exception:
            pass
        return None
    
    def get_endpoints(self) -> List[EndpointInfo]:
        """Extract endpoint info from Flask"""
        endpoints = []
        
        try:
            for rule in self._app.url_map.iter_rules():
                # Skip Fabric's own routes
                if rule.rule.startswith(self.config.prefix):
                    continue
                
                # Skip static endpoint
                if rule.endpoint == 'static':
                    continue
                
                # Get methods (exclude HEAD and OPTIONS)
                methods = [m for m in rule.methods 
                          if m not in ('HEAD', 'OPTIONS')]
                
                for method in methods:
                    # Get view function
                    view_func = self._app.view_functions.get(rule.endpoint)
                    description = ""
                    if view_func and view_func.__doc__:
                        description = view_func.__doc__.strip().split('\n')[0]
                    
                    endpoint = EndpointInfo(
                        path=rule.rule,
                        method=method,
                        name=rule.endpoint,
                        description=description,
                    )
                    
                    # Extract parameters
                    endpoint.parameters = self._extract_parameters(rule)
                    
                    endpoints.append(endpoint)
                    
        except Exception as e:
            logger.error(f"Failed to extract endpoints: {e}")
        
        return endpoints
    
    def _extract_parameters(self, rule: Any) -> List[ParameterInfo]:
        """Extract parameter info from route"""
        parameters = []
        
        try:
            # Extract path parameters
            for arg in rule.arguments:
                parameters.append(ParameterInfo(
                    name=arg,
                    location="path",
                    required=True
                ))
        except Exception as e:
            logger.debug(f"Failed to extract parameters: {e}")
        
        return parameters
    
    def mount_api(self, app: Any) -> None:
        """Mount Fabric API"""
        from flask import Blueprint, jsonify, request as flask_request
        
        api_bp = Blueprint('fabric_api', __name__, url_prefix=f"{self.config.prefix}/api")
        
        @api_bp.route('/health')
        def health():
            return jsonify({
                "status": "healthy",
                "version": "0.1.0",
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
        
        @api_bp.route('/metrics')
        def metrics():
            start_time = flask_request.args.get('start_time')
            end_time = flask_request.args.get('end_time')
            hours = int(flask_request.args.get('hours', 1))
            
            from datetime import timedelta
            
            if start_time is None and end_time is None:
                end_time = datetime.now(timezone.utc)
                start_time = end_time - timedelta(hours=hours)
            
            # Run async in sync context
            future = asyncio.run_coroutine_threadsafe(
                self.collector.get_summary(start_time, end_time),
                self._loop
            )
            summary = future.result(timeout=10)
            
            return jsonify({
                "summary": summary.model_dump(),
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
        
        @api_bp.route('/requests')
        def get_requests():
            page = int(flask_request.args.get('page', 1))
            page_size = int(flask_request.args.get('page_size', 50))
            offset = (page - 1) * page_size
            
            # Run async in sync context
            future = asyncio.run_coroutine_threadsafe(
                self.collector.get_requests(limit=page_size, offset=offset),
                self._loop
            )
            requests = future.result(timeout=10)
            
            future = asyncio.run_coroutine_threadsafe(
                self.collector.storage.get_requests_count(),
                self._loop
            )
            total = future.result(timeout=10)
            
            return jsonify({
                "items": [r.model_dump() for r in requests],
                "total": total,
                "page": page,
                "page_size": page_size
            })
        
        @api_bp.route('/requests/<request_id>')
        def get_request_detail(request_id):
            future = asyncio.run_coroutine_threadsafe(
                self.collector.get_request_by_id(request_id),
                self._loop
            )
            record = future.result(timeout=10)
            
            if record is None:
                return jsonify({"error": "Not found"}), 404
            
            return jsonify({"record": record.model_dump()})
        
        @api_bp.route('/endpoints')
        def get_endpoints():
            endpoints = self.get_endpoints()
            return jsonify({
                "endpoints": [e.model_dump() for e in endpoints],
                "total": len(endpoints),
                "endpoint_stats": []
            })
        
        @api_bp.route('/config')
        def get_config():
            return jsonify({
                "app_name": self.config.app_name,
                "prefix": self.config.prefix,
                "storage_type": self.config.storage_type,
                "max_requests": self.config.max_requests,
                "retention_hours": self.config.retention_hours,
                "sample_rate": self.config.sample_rate,
                "exclude_paths": self.config.exclude_paths
            })
        
        @api_bp.route('/metrics/timeline')
        def get_timeline():
            hours = int(flask_request.args.get('hours', 1))
            interval = int(flask_request.args.get('interval', 60))
            
            from datetime import timedelta
            end_time = datetime.now(timezone.utc)
            start_time = end_time - timedelta(hours=hours)
            
            future = asyncio.run_coroutine_threadsafe(
                self.collector.get_timeline(start_time, end_time, interval),
                self._loop
            )
            timeline = future.result(timeout=10)
            
            return jsonify({
                "timeline": timeline.model_dump(),
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat()
            })
        
        app.register_blueprint(api_bp)
    
    def mount_dashboard(self, app: Any) -> None:
        """Mount frontend dashboard"""
        from flask import Blueprint, send_from_directory, redirect, Response
        
        dashboard_bp = Blueprint(
            'fabric_dashboard', 
            __name__, 
            url_prefix=self.config.prefix
        )
        
        # Find frontend build directory
        dashboard_dist = Path(__file__).parent.parent / "dashboard" / "dist"
        index_html = dashboard_dist / "index.html"
        
        @dashboard_bp.route('/')
        def serve_index():
            if index_html.exists():
                return send_from_directory(dashboard_dist, 'index.html')
            return Response(self._get_fallback_html(), mimetype='text/html')
        
        @dashboard_bp.route('/assets/<path:filename>')
        def serve_assets(filename):
            assets_dir = dashboard_dist / "assets"
            if assets_dir.exists():
                return send_from_directory(assets_dir, filename)
            return "Not found", 404
        
        @dashboard_bp.route('/<path:path>')
        def serve_spa(path):
            # Serve static files if they exist
            file_path = dashboard_dist / path
            if file_path.exists() and file_path.is_file():
                return send_from_directory(dashboard_dist, path)
            # Otherwise serve index.html for SPA routing
            if index_html.exists():
                return send_from_directory(dashboard_dist, 'index.html')
            return Response(self._get_fallback_html(), mimetype='text/html')
        
        # Redirect /fabric to /fabric/
        @app.route(self.config.prefix)
        def redirect_to_dashboard():
            return redirect(f"{self.config.prefix}/")
        
        app.register_blueprint(dashboard_bp)
    
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
