# Fabric Monitor

<p align="center">
  <strong>🔍 Lightweight Python Backend Service Monitoring Framework</strong>
</p>

<p align="center">
  <a href="#features">Features</a> •
  <a href="#installation">Installation</a> •
  <a href="#quick-start">Quick Start</a> •
  <a href="#documentation">Documentation</a> •
  <a href="#contributing">Contributing</a>
</p>

---

## Features

- 🚀 **Zero-Intrusion Integration** - Integrates via middleware with minimal impact on existing code
- 📊 **Real-time Monitoring** - Real-time collection of request data, response times, error rates, and more
- 📝 **Auto Documentation** - Automatically extracts API documentation from code
- 🎨 **Visual Dashboard** - Modern monitoring dashboard built with Vue3
- 🔌 **Extensible Architecture** - Plugin-based design supporting FastAPI, Flask, and more frameworks
- 💾 **Multiple Storage Backends** - Supports memory, SQLite(in dev), Redis(in dev), and other storage options

## Installation

```bash
# Using uv
uv pip install fabric-monitor

# Using pip
pip install fabric-monitor

# Install with FastAPI support
uv pip install "fabric-monitor[fastapi]"

# Install with Flask support
uv pip install "fabric-monitor[flask]"

# Install all optional dependencies
uv pip install "fabric-monitor[all]"
```

## Quick Start

### FastAPI

```python
from fastapi import FastAPI
from fabric import Fabric, FabricConfig

app = FastAPI()

# Initialize Fabric
fabric = Fabric(FabricConfig(app_name="My API"))
fabric.setup(app)

@app.get("/users")
async def get_users():
    return [{"id": 1, "name": "Alice"}]

# Visit http://localhost:8000/fabric to view the monitoring dashboard
```

## Configuration Options

```python
from fabric import FabricConfig

config = FabricConfig(
    app_name="My API",           # Application name
    prefix="/fabric",            # Dashboard route prefix
    enabled=True,                # Enable monitoring
    storage_type="memory",       # Storage type: memory | sqlite | redis
    max_requests=10000,          # Maximum request records
    retention_hours=24,          # Data retention time
    sample_rate=1.0,             # Sampling rate (0.0-1.0)
    exclude_paths=["/health"],   # Excluded paths
    enable_auth=False,           # Enable authentication
    auth_token=None,             # Authentication token
)
```

## Documentation

For detailed documentation, see [Development Documentation](docs/DEVELOPMENT.md)

## Supported Frameworks

| Framework | Status |
|-----------|--------|
| FastAPI | ✅ Supported |
| Flask | ✅ Supported |
| Django | 📋 Planned |

## Supported Storage

| Storage | Status |
|-----------|--------|
| Memory | ✅ Supported |
| SQLite | 🚧 In Development |
| Redis | 🚧 In Development |
| MySQL | 📋 Planned |

## License

MIT License
