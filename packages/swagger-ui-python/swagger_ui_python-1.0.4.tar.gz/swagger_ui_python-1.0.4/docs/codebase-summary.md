# Swagger UI Python - Codebase Summary

**Last Updated:** 2026-01-21
**Core LOC:** ~167 (ApplicationDocument)
**Handlers:** 9 modules (20-83 LOC each)
**Total Test Cases:** 50+ (10 configs × 9 frameworks)

---

## Directory Structure

```
swagger_ui/                          # Main package
├── __init__.py                      # api_doc() entry point + legacy API
├── core.py                          # ApplicationDocument class (167 LOC)
├── utils.py                         # Config loading helper (21 LOC)
├── handlers/                        # Framework-specific handlers
│   ├── __init__.py                 # supported_list via pkgutil
│   ├── flask.py                    # Flask Blueprint (41 LOC)
│   ├── tornado.py                  # Tornado RequestHandler (44 LOC)
│   ├── sanic.py                    # Sanic Blueprint (37 LOC)
│   ├── aiohttp.py                  # aiohttp Router (38 LOC)
│   ├── quart.py                    # Quart Blueprint (43 LOC)
│   ├── starlette.py                # Starlette Router (55 LOC)
│   ├── falcon.py                   # Falcon Sync/Async (83 LOC)
│   ├── bottle.py                   # Bottle Decorator (34 LOC)
│   └── chalice.py                  # Chalice Blueprint (67 LOC)
├── templates/                       # Jinja2 templates
│   ├── doc.html                    # Swagger UI page (48 LOC)
│   └── editor.html                 # Swagger Editor page
└── static/                          # Static assets (26 files)
    ├── swagger-ui-bundle.js
    ├── swagger-editor.js
    ├── swagger-ui.css
    ├── oauth2-redirect.html
    ├── LICENSE
    └── [images, maps, fonts]

test/                               # Test suite
├── conftest.py                     # pytest configuration
├── common.py                       # Shared test utilities
├── *_test.py                       # Framework-specific tests (9)
├── conf/
│   └── test3.yaml                 # OpenAPI spec for tests
└── requirements.txt               # Test dependencies

examples/                           # Minimal working examples
├── flask_test.py
├── tornado_test.py
├── sanic_test.py
├── aiohttp_test.py
├── quart_test.py
├── starlette_test.py
├── falcon_test.py
├── bottle_test.py
├── chalice/app.py
└── conf/test.yaml

tools/                              # Development tools
└── update.py                       # Download & extract Swagger UI/Editor

.github/workflows/                  # CI/CD pipelines
├── lint-and-pytest.yml            # Test matrix (Python 3.9-3.12)
└── release.yml                    # Tag-triggered release
```

---

## Core Modules

### 1. ApplicationDocument (core.py - 167 LOC)

**Responsibilities:**
- Store application instance and configuration
- Load OpenAPI spec from multiple sources
- Render HTML templates with injected parameters
- Build URI paths for routes
- Match and select framework handler

**Key Properties:**
- `blueprint_name` - Generate route blueprint identifier
- `static_dir` - Path to static assets directory
- `doc_html` - Rendered Swagger UI HTML template
- `editor_html` - Rendered Swagger Editor HTML template

**Key Methods:**
- `__init__()` - Initialize with app and configuration
- `get_config(host)` - Load and return OpenAPI spec
- `match_handler()` - Auto-detect framework and return handler
- `uri(suffix)` - Build relative URI for routes
- `root_uri_absolute()`, `swagger_json_uri_absolute()`, etc. - URI builders

**Config Loading Priority:**
1. Provided dict (`config={}`)
2. File path (`config_path='./spec.yaml'`)
3. Remote URL (`config_url='https://...'`)
4. String spec (`config_spec='{"openapi":"3.0.1"...}'`)
5. External URL (`config_rel_url='/swagger.json'`)

### 2. Handler Interface (All frameworks implement)

Each handler module provides two functions:

```python
def handler(doc: ApplicationDocument) -> None:
    """Register routes with framework app instance"""
    # Framework-specific setup code
    pass

def match(doc: ApplicationDocument) -> Optional[Callable]:
    """Return handler if framework matches, else None"""
    try:
        import framework_module
        if isinstance(doc.app, framework_module.AppClass):
            return handler
    except ImportError:
        pass
    return None
```

**Routes Each Handler Creates:**
- `GET {url_prefix}` - Main Swagger UI page
- `GET {url_prefix}/swagger.json` - OpenAPI spec (if config not external)
- `GET {url_prefix}/editor` - Swagger Editor (if editor=True)
- `GET {url_prefix}/static/{path}` - Static assets

### 3. Utils Module (utils.py - 21 LOC)

**Function:** `_load_config(content: Union[str, bytes]) -> dict`

Attempts to parse content as:
1. JSON (json.loads)
2. YAML (yaml.load)
3. Raises exception if both fail

Used for config_path and config_spec sources.

### 4. Handler Discovery (handlers/__init__.py)

**Auto-Discovery Mechanism:**

```python
supported_list = [
    name for _, name, _ in pkgutil.iter_modules(__path__)
    if not name.startswith('_')
]
```

- Dynamically scans package for handler modules
- No hardcoded registry
- Extensible: add module file = new framework support

---

## Framework Handlers Overview

### Flask Handler (41 LOC)
- **Pattern:** Blueprint with url_prefix
- **Routes:** Decorator-based (@blueprint.route)
- **Static:** Blueprint.static_folder/static_url_path
- **Async:** No (sync only)
- **Key API:** Blueprint.register_blueprint()

### Tornado Handler (44 LOC)
- **Pattern:** RequestHandler subclasses
- **Routes:** app.add_handlers() with regex patterns
- **Static:** StaticFileHandler for assets
- **Async:** No (async patterns handled internally)
- **Key API:** RequestHandler, StaticFileHandler

### Sanic Handler (37 LOC)
- **Pattern:** Blueprint with decorators
- **Routes:** @blueprint.get/@blueprint.post
- **Static:** blueprint.static()
- **Async:** Yes (full async support)
- **Key API:** Blueprint.register()

### aiohttp Handler (38 LOC)
- **Pattern:** Router add_get/add_post
- **Routes:** router.add_get(), router.add_post()
- **Static:** router.add_static()
- **Async:** Yes (full async support)
- **Key API:** web.Response, web.json_response

### Quart Handler (43 LOC)
- **Pattern:** Blueprint (similar to Flask)
- **Routes:** @blueprint.get/@blueprint.post
- **Static:** Blueprint.static()
- **Async:** Yes (async/await support)
- **Key API:** Blueprint.register_blueprint()

### Starlette Handler (55 LOC)
- **Pattern:** Router.add_route()
- **Routes:** Direct router methods
- **Static:** StaticFiles middleware
- **Async:** Yes (full async support)
- **Key API:** Request, Response objects

### Falcon Handler (83 LOC - Largest)
- **Pattern:** App.add_route() (Falcon v3+/v2)
- **Routes:** Custom responder methods
- **Static:** No built-in; manual in handler
- **Async:** Dual support (sync + async)
- **Complexity:** Version checking (v2, v3, v4)
- **Key Challenge:** Breaking changes between versions

### Bottle Handler (34 LOC)
- **Pattern:** Decorator-based routing
- **Routes:** @app.get/@app.post decorators
- **Static:** static_file() utility
- **Async:** No (sync only)
- **Key API:** Bottle.route() decorators

### Chalice Handler (67 LOC)
- **Pattern:** Blueprint system
- **Routes:** @blueprint.route() decorators
- **Static:** Manual MIME type detection (no auto-serve)
- **Async:** No (AWS Lambda context)
- **Challenge:** Lambda environment constraints

---

## API Entry Points

### Main Entry Point (swagger_ui/__init__.py)

```python
def api_doc(app, **kwargs) -> None:
    """Unified entry point for all frameworks"""
    doc = ApplicationDocument(app, **kwargs)
    handler = doc.match_handler()
    if not handler:
        raise Exception(f"No handler found for {app}")
    return handler(doc)
```

**Parameters:**
- `app` - Framework application instance
- `app_type` - Optional explicit framework name
- `config` - Python dict spec
- `config_path` - YAML/JSON file path
- `config_url` - Remote spec URL
- `config_spec` - JSON/YAML string spec
- `config_rel_url` - External spec endpoint
- `url_prefix` - Base path (default: '/api/doc')
- `title` - HTML page title
- `editor` - Enable spec editor (default: False)
- `custom_css` - Custom CSS URL
- `parameters` - Swagger UI bundle parameters
- `oauth2_config` - OAuth2 configuration
- `host_inject` - Auto-inject runtime host (default: True)

### Legacy Framework-Specific APIs

**Generated dynamically at module load time:**

```python
from swagger_ui import flask_api_doc, tornado_api_doc, sanic_api_doc, \
                       aiohttp_api_doc, falcon_api_doc, quart_api_doc, \
                       starlette_api_doc, bottle_api_doc, chalice_api_doc

flask_api_doc(app, config_path='./spec.yaml')      # Same as api_doc()
tornado_api_doc(app, config_path='./spec.yaml')    # ...etc
```

Implementation:
```python
for name in supported_list:
    setattr(sys.modules[__name__],
            f'{name}_api_doc',
            create_api_doc(name))
```

---

## Configuration Flow

### 1. Initialization (api_doc call)

```
api_doc(app, config_path='./spec.yaml', url_prefix='/api/doc')
    ↓
ApplicationDocument(app, config_path='./spec.yaml', url_prefix='/api/doc')
    ↓
[Store parameters, resolve static_dir, templates]
```

### 2. Framework Detection (match_handler call)

```
doc.match_handler()
    ↓
if app_type provided: import and use that handler
    ↓
else: iterate supported_list
    ↓
for each: import module, call module.match(doc)
    ↓
return handler function or raise error
```

### 3. Route Registration (handler call)

```
handler(doc)
    ↓
Framework-specific setup:
  - Create route handlers (get_config, get_static, etc.)
  - Register with framework app
  - Return None (modifies app in-place)
```

### 4. Request Handling (user accesses /api/doc)

```
GET /api/doc
    ↓
Route handler invoked
    ↓
Render: doc.doc_html (Jinja2 template with injected parameters)
    ↓
Response: HTML + Swagger UI JavaScript
```

---

## Static Assets & Templates

### Static Directory (swagger_ui/static/ - 26 files)

**Swagger UI v5.25.3:**
- swagger-ui-bundle.js (main library)
- swagger-ui.css, index.css
- swagger-ui-es-bundle.js, swagger-ui-es-bundle-core.js
- swagger-initializer.js

**Swagger Editor v4.14.6:**
- swagger-editor.js, swagger-editor-bundle.js
- swagger-editor-es-bundle.js, swagger-editor-es-bundle-core.js
- swagger-editor-standalone-preset.js
- swagger-editor.css

**Resources:**
- oauth2-redirect.html (OAuth2 flow)
- favicon-16x16.png, favicon-32x32.png
- Source maps (.js.map, .css.map)
- LICENSE (Swagger UI license)

### Templates (swagger_ui/templates/)

**doc.html (48 LOC):**
- Main Swagger UI entry point
- Loads swagger-ui-bundle.js, swagger-ui-standalone-preset.js
- Injects SwaggerUIBundle parameters
- Optionally initializes OAuth2
- Includes custom CSS if provided

**editor.html:**
- Swagger Editor entry point
- Loads swagger-editor.js and dependencies
- Similar parameter injection

### Update Tool (tools/update.py - ~150 LOC)

**Purpose:** Download and extract latest Swagger UI/Editor versions

**Features:**
- Downloads from GitHub releases
- Extracts assets to static/
- Formats HTML templates with djlint
- Version pinning support

**Usage:**
```bash
tox -e update              # Update both
python tools/update.py --ui-version=v5.25.3 --editor-version=v4.14.6
```

---

## Testing Architecture

### Test Structure

- **Framework:** pytest with parametrization
- **Coverage:** 50+ test cases (10 configs × 5+ frameworks)
- **CI/CD:** GitHub Actions, Python 3.9-3.12

### Parametrized Tests

Each framework test includes 10 scenarios:
1. Auto-detect mode + basic config
2. Explicit framework mode
3. With editor enabled
4. With alternate url_prefix
5. With external config URL (config_rel_url)
6. ... (5 more combinations)

### Test Pattern

```python
@pytest.mark.parametrize('mode, kwargs', parametrize_list)
def test_flask(app, mode, kwargs):
    # Setup external config if needed
    if kwargs.get('config_rel_url'):
        @app.route(kwargs['config_rel_url'])
        def get_config():
            return config_content

    # Call api_doc
    api_doc(app, **kwargs) if mode == 'auto' else flask_api_doc(app, **kwargs)

    # Test endpoints
    client = app.test_client()
    assert client.get(url_prefix).status_code == 200
    assert client.get(f'{url_prefix}/swagger.json').status_code == 200
    assert client.get(f'{url_prefix}/static/LICENSE').status_code == 200
```

### CI/CD Pipeline

**GitHub Actions (lint-and-pytest.yml):**

```yaml
matrix:
  python-version: ['3.9', '3.10', '3.11', '3.12']

steps:
  1. format-check (autopep8, isort, flake8)
  2. pytest (run full test suite)
  3. install (build wheel + verify)
```

**Release Pipeline (release.yml):**
- Triggered on tag push
- Build sdist + bdist_wheel
- Generate GitHub release
- Create artifacts

---

## Key Design Patterns

### 1. Strategy Pattern
- Each handler module = isolated strategy
- Common interface (handler, match functions)
- Runtime selection via match()

### 2. Factory/Registry Pattern
- supported_list auto-discovered via pkgutil
- No hardcoded registry
- Extensible by adding module file

### 3. Adapter Pattern
- ApplicationDocument abstracts framework differences
- Unified URI builders and config loading
- Handlers don't deal with framework specifics

### 4. Template Method Pattern
- Core flow in api_doc() and ApplicationDocument
- Handlers implement details, not flow
- Common logic for rendering, config, routing

### 5. Builder Pattern
- ApplicationDocument accepts flexible config
- Multiple sources supported
- Supports builder-style parameter passing

---

## Dependency Graph

```
api_doc()
    ↓
ApplicationDocument.__init__()
    ├─ Jinja2 (templates)
    ├─ PyYaml (config parsing)
    └─ packaging (version checking for Falcon)
    ↓
match_handler()
    ↓
handler(doc)  [framework-specific implementation]
    ├─ Flask, Tornado, Sanic, aiohttp, Quart, Starlette, Falcon, Bottle, Chalice
    └─ Each optionally imported (no hard dependency)
```

---

## Code Quality Metrics

| Metric | Status |
|--------|--------|
| Avg Handler Size | 20-83 LOC (focused) |
| Core Module | 167 LOC (ApplicationDocument) |
| Code Duplication | Minimal (common logic in core.py) |
| Test Coverage | 50+ test cases across frameworks |
| Linting | flake8, autopep8, isort |
| Max Line Length | 100 characters |
| Type Hints | Not present (future enhancement) |
| Documentation | README + docstrings |

---

## Extension Points

### Adding New Framework Support

1. Create handler module in `swagger_ui/handlers/{framework}.py`
2. Implement `handler(doc)` and `match(doc)` functions
3. Reference existing handlers (flask.py, falcon.py) as templates
4. Add test in `test/{framework}_test.py`
5. Update README with framework name
6. Auto-discovery via pkgutil handles rest

### Customizing Swagger UI

- **Custom Parameters:** Pass parameters dict to api_doc()
- **Custom CSS:** Use custom_css parameter
- **OAuth2:** Configure oauth2_config
- **Custom Spec:** Use config_path, config_url, or config_spec

### Custom Static Assets

Use tools/update.py to download latest Swagger UI/Editor versions and extract to static/.
