[![tests](https://github.com/SkyTik/swagger-ui-py/actions/workflows/lint-and-pytest.yml/badge.svg)](https://github.com/SkyTik/swagger-ui-py/actions/workflows/lint-and-pytest.yml)
[![Version](https://badge.fury.io/gh/SkyTik%2Fswagger-ui-py.svg)](https://github.com/SkyTik/swagger-ui-py/tags)

[Documentation](./docs/)

# swagger-ui-python

Seamless Swagger UI integration for Python web frameworks. A unified, framework-agnostic API for adding interactive OpenAPI documentation to your Python applications with automatic framework detection.

> **Note:** This is a maintained fork of [PWZER/swagger-ui-py](https://github.com/PWZER/swagger-ui-py).

**Status:** Production-ready, actively maintained
**Python:** 3.9, 3.10, 3.11, 3.12
**Swagger UI:** v5.25.3
**Swagger Editor:** v4.14.6

## Key Features

- **Framework Agnostic** - Single API works across 9+ Python frameworks
- **Auto-Detection** - Automatically detects your framework, zero configuration needed
- **Multiple Config Sources** - YAML/JSON files, remote URLs, Python dicts, or strings
- **Swagger Editor** - Optional inline spec editor for live documentation editing
- **Static Assets** - Automatic CSS, JS, images, and icons serving
- **Customization** - Custom CSS, Swagger UI parameters, OAuth2 configuration
- **Well-Tested** - 50+ test cases across all supported frameworks

## Supported Frameworks

- [Tornado](https://www.tornadoweb.org/en/stable/)
- [Flask](https://flask.palletsprojects.com/)
- [Sanic](https://sanicframework.org/en/)
- [AIOHTTP](https://docs.aiohttp.org/en/stable/)
- [Quart](https://pgjones.gitlab.io/quart/)
- [Starlette](https://www.starlette.io/)
- [Falcon](https://falcon.readthedocs.io/en/stable/)
- [Bottle](https://bottlepy.org/docs/dev/)
- [Chalice](https://aws.github.io/chalice/index.html)

Check supported frameworks:

```bash
python3 -c "from swagger_ui import supported_list; print(supported_list)"
# Output: ['flask', 'tornado', 'sanic', 'aiohttp', 'quart', 'starlette', 'falcon', 'bottle', 'chalice']
```

## Quick Start

### Installation

```bash
pip install swagger-ui-python
```

### Basic Example (Flask)

```python
from flask import Flask
from swagger_ui import api_doc

app = Flask(__name__)

# Auto-detects Flask and registers routes
api_doc(app, config_path='./openapi.yaml')

if __name__ == '__main__':
    app.run(debug=True)
    # Visit: http://localhost:5000/api/doc
```

### Basic Example (Tornado)

```python
import tornado.ioloop
from tornado.web import Application
from swagger_ui import api_doc

app = Application()

# Auto-detects Tornado and registers routes
api_doc(app, config_path='./openapi.yaml', url_prefix='/api/doc')

if __name__ == '__main__':
    app.listen(8888)
    tornado.ioloop.IOLoop.current().start()
    # Visit: http://localhost:8888/api/doc
```

## Configuration Options

### 1. Configuration Sources (in priority order)

**Option A: YAML/JSON File**

```python
api_doc(app, config_path='./openapi.yaml')
```

**Option B: Remote URL** (requires CORS)

```python
api_doc(app, config_url='https://petstore.swagger.io/v2/swagger.json')
```

**Option C: Python Dict**

```python
config = {
    "openapi": "3.0.1",
    "info": {"title": "My API", "version": "1.0.0"},
    "paths": { ... }
}
api_doc(app, config=config)
```

**Option D: JSON/YAML String**

```python
spec_string = '{"openapi":"3.0.1","info":{"title":"My API"},...}'
api_doc(app, config_spec=spec_string)
```

**Option E: External Endpoint**

```python
api_doc(app, config_rel_url='/swagger.json')  # App provides endpoint
```

### 2. Common Parameters

```python
api_doc(
    app,
    config_path='./openapi.yaml',      # Config source
    url_prefix='/api/doc',              # Internal route path (default: '/api/doc')
    base_url=None,                      # External URL for assets (defaults to url_prefix)
    title='API Documentation',          # HTML page title
    editor=False,                       # Enable spec editor
    custom_css='https://cdn.../style.css',  # Custom CSS
    host_inject=True,                   # Auto-inject request host
)
```

### 3. Reverse Proxy Support

When deploying behind a reverse proxy, you may need to separate internal route registration from external URL paths.

**Common scenario:** Reverse proxy routes `/api/*` to your backend service at root `/`

**The Problem:**

Without `base_url`, Swagger UI generates incorrect asset URLs:

```python
api_doc(app, config_path='./openapi.yaml', url_prefix='/docs')
```

- Backend registers routes at `/docs` ✓
- Browser requests `/api/docs` → proxy routes to backend `/docs` ✓
- But Swagger UI generates links like `/docs/static/swagger-ui.css`
- Browser requests `/docs/static/swagger-ui.css` → 404 ✗ (missing `/api` prefix)

**The Solution:**

Use `base_url` to include the proxy path prefix in generated URLs:

```python
api_doc(
    app,
    config_path='./openapi.yaml',
    url_prefix='/docs',        # Backend registers routes here
    base_url='/api/docs',      # Browser URLs include proxy prefix
)
```

- Backend registers routes at `/docs` (unchanged)
- Swagger UI generates links like `/api/docs/static/swagger-ui.css` ✓
- Browser requests `/api/docs/static/swagger-ui.css` → proxy routes to backend `/docs/static/swagger-ui.css` ✓

**Key distinction:**

- `url_prefix` - Where your app registers routes (backend/app-side)
- `base_url` - Path prefix for URLs in HTML (browser/client-side, defaults to `url_prefix`)

### 4. Swagger UI Customization

```python
parameters = {
    "deepLinking": "true",
    "displayRequestDuration": "true",
    "layout": "\"StandaloneLayout\"",
    "plugins": "[SwaggerUIBundle.plugins.DownloadUrl]",
}
api_doc(app, config_path='./openapi.yaml', parameters=parameters)
```

See [Swagger UI Parameters](https://swagger.io/docs/open-source-tools/swagger-ui/usage/configuration/) for all options.

### 5. OAuth2 Configuration

```python
oauth2_config = {
    "clientId": "\"your-client-id\"",
    "clientSecret": "\"your-secret\"",
    "realm": "\"your-realm\"",
    "appName": "\"your-app\"",
    "scopeSeparator": "\" \"",
    "scopes": "\"openid profile\"",
}
api_doc(app, config_path='./openapi.yaml', oauth2_config=oauth2_config)
```

See [OAuth2 Configuration](https://swagger.io/docs/open-source-tools/swagger-ui/usage/oauth2/) for details.

### 6. Legacy Framework-Specific APIs

Still supported for backward compatibility:

```python
from swagger_ui import flask_api_doc, tornado_api_doc, sanic_api_doc

# Same as api_doc(app, ...) but explicit
flask_api_doc(app, config_path='./openapi.yaml')
tornado_api_doc(app, config_path='./openapi.yaml')
sanic_api_doc(app, config_path='./openapi.yaml')
```

## Routes Created

The library automatically creates these routes (at `url_prefix=/api/doc`):

- `GET /api/doc` - Interactive Swagger UI documentation
- `GET /api/doc/swagger.json` - OpenAPI specification (JSON)
- `GET /api/doc/editor` - Swagger Editor (if `editor=True`)
- `GET /api/doc/static/{path}` - Static assets (CSS, JS, images)

## Creating OpenAPI Specifications

For details on writing OpenAPI specifications:

- [OpenAPI 3.0 Guide](https://swagger.io/resources/open-api/)
- [OpenAPI 3.1 Spec](https://spec.openapis.org/oas/v3.1.0)
- [Swagger Editor](https://editor.swagger.io/) - Interactive spec editor

## Versions

- **Swagger UI:** v5.25.3 ([GitHub](https://github.com/swagger-api/swagger-ui))
- **Swagger Editor:** v4.14.6 ([GitHub](https://github.com/swagger-api/swagger-editor))

To update to newer versions:

```bash
tox -e update
# or
python tools/update.py --ui-version=v5.25.3 --editor-version=v4.14.6
```

## Extending the Library

### Adding Support for New Frameworks

To add support for a new framework:

1. Create `swagger_ui/handlers/{framework}.py` following the [handler interface](./docs/system-architecture.md)
2. Implement `handler(doc)` and `match(doc)` functions
3. Add tests in `test/{framework}_test.py`
4. Update README with framework name
5. Auto-discovery will handle the rest

See [Code Standards](./docs/code-standards.md) for detailed guidelines.

### Custom Parameters & Configuration

Pass custom parameters and OAuth2 configuration through the `api_doc()` function for full control over Swagger UI behavior.

## Documentation

Full documentation available in the `./docs` directory:

- [Project Overview & PDR](./docs/project-overview-pdr.md) - Vision, goals, requirements
- [Codebase Summary](./docs/codebase-summary.md) - Module structure and responsibilities
- [Code Standards](./docs/code-standards.md) - Coding conventions and patterns
- [System Architecture](./docs/system-architecture.md) - Design patterns and data flow
- [Project Roadmap](./docs/project-roadmap.md) - Planned improvements and timeline

## Development

### Setup

```bash
# Clone repository
git clone https://github.com/SkyTik/swagger-ui-python.git
cd swagger-ui-python

# Install dev dependencies
pip install -e ".[dev]"

# Run tests
make pytest

# Format code
make format

# Build wheel
make whl
```

### Testing

```bash
make pytest              # Run all tests
make format-check        # Check code style
make format              # Auto-format code
```

### Building & Release

```bash
make whl                 # Build wheel
make upload              # Upload to PyPI
```

## Troubleshooting

**Framework not detected:**

- Ensure framework is installed
- Try explicit `app_type` parameter: `api_doc(app, app_type='flask', ...)`

**Config not loading:**

- Check file path exists and is readable
- Validate YAML/JSON format using [Swagger Editor](https://editor.swagger.io/)
- Check CORS headers if using remote URL

**Routes not registered:**

- Ensure `api_doc()` called before app starts
- Check `url_prefix` doesn't conflict with existing routes
- Verify framework-specific setup (e.g., `app.register_blueprint()` for Flask)

For more help:

- Check [examples/](./examples/) directory for working samples
- Review [GitHub Issues](https://github.com/SkyTik/swagger-ui-python/issues)
- Read framework-specific documentation

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure tests pass: `make pytest`
5. Format code: `make format`
6. Submit a pull request

See [Code Standards](./docs/code-standards.md) for contribution guidelines.

## License

Licensed under the Apache License 2.0. See LICENSE file for details.

## Support

- **Issues:** [GitHub Issues](https://github.com/SkyTik/swagger-ui-python/issues)
- **Project:** [SkyTik/swagger-ui-python](https://github.com/SkyTik/swagger-ui-python)
- **PyPI:** [swagger-ui-python](https://pypi.org/project/swagger-ui-python/)
