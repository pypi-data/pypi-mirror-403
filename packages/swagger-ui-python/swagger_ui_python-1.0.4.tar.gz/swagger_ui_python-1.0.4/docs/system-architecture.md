# Swagger UI Python - System Architecture

**Last Updated:** 2026-01-21
**Architecture Pattern:** Strategy + Factory/Registry + Adapter
**Current Version:** 5.x.x

---

## High-Level Architecture Overview

```
┌──────────────────────────────────────────────────────────────┐
│                   Application Code (User)                      │
│         from swagger_ui import api_doc                        │
│         api_doc(app, config_path='./spec.yaml')              │
└────────────────────────────┬─────────────────────────────────┘
                             │
                             ↓
┌──────────────────────────────────────────────────────────────┐
│                   Unified Entry Point                          │
│              api_doc() in __init__.py                         │
│  - Validate parameters                                        │
│  - Create ApplicationDocument instance                        │
│  - Call match_handler() for framework detection              │
│  - Execute handler(doc) to register routes                   │
└────────────────────────────┬─────────────────────────────────┘
                             │
                             ↓
┌──────────────────────────────────────────────────────────────┐
│            ApplicationDocument (core.py - 167 LOC)            │
│  Responsibilities:                                             │
│  - Store app instance & configuration                        │
│  - Load OpenAPI spec (multiple sources)                      │
│  - Render HTML templates (Jinja2)                            │
│  - Build URI paths (framework-agnostic)                      │
│  - Match & select framework handler                          │
└────────────────────────────┬─────────────────────────────────┘
                             │
                             ↓
        ┌────────────────────┴────────────────────┐
        │                                         │
        ↓                                         ↓
┌──────────────────────────────────┐   ┌────────────────────────┐
│   Config Loading & Templating    │   │  Framework Detection   │
│ (utils.py + templates/)          │   │  (handlers/__init__.py)│
│                                  │   │                        │
│ - JSON parsing (json module)     │   │ - pkgutil.iter_modules│
│ - YAML parsing (yaml module)     │   │ - Dynamic module import
│ - Template rendering (Jinja2)    │   │ - Handler matching    │
│ - Static asset resolution        │   │ - Priority fallback   │
└──────────────────────────────────┘   └────────────────────────┘
                                                 │
                                                 ↓
        ┌────────────────────────────────────────┴────────────────────────────┐
        │                     Framework Handler Selection                     │
        │  (Strategy Pattern - one handler per framework)                    │
        │                                                                     │
        ├──────────┬──────────┬──────────┬──────────┬──────────┬──────────┐
        │          │          │          │          │          │          │
        ↓          ↓          ↓          ↓          ↓          ↓          ↓
    ┌─────┐  ┌────────┐ ┌─────┐  ┌────────┐ ┌──────┐ ┌──────────┐ ┌───────┐
    │Flask│  │Tornado │ │Sanic│  │aiohttp │ │Quart │ │Starlette│ │Falcon │
    │v2.x+│  │v5.x+   │ │v21+ │  │v3.x+   │ │v0.x+ │ │v0.x+    │ │v3,4  │
    └──┬──┘  └────┬───┘ └──┬──┘  └────┬───┘ └──┬───┘ └────┬─────┘ └───┬───┘
       │           │        │          │        │           │          │
       └───────────┼────────┼──────────┼────────┼───────────┼──────────┘
                   │ (9 handlers, 20-83 LOC each)
                   │
                   ↓
    ┌──────────────────────────────────────────────────────────┐
    │              Route Registration Layer                     │
    │                                                           │
    │ Framework-specific route setup:                         │
    │ - GET {url_prefix}             → Swagger UI HTML       │
    │ - GET {url_prefix}/swagger.json → OpenAPI spec JSON    │
    │ - GET {url_prefix}/editor      → Swagger Editor       │
    │ - GET {url_prefix}/static/...  → Static assets        │
    │                                                           │
    │ Registered with: Blueprint, RequestHandler,            │
    │ Router, Decorator, etc. (framework-dependent)          │
    └──────────────────────────────────────────────────────────┘
                             │
                             ↓
    ┌──────────────────────────────────────────────────────────┐
    │            Static Assets & Templates Layer               │
    │                                                           │
    │ Templates (Jinja2):                                      │
    │ - doc.html (48 LOC)       → Swagger UI bundle          │
    │ - editor.html             → Swagger Editor bundle      │
    │                                                           │
    │ Static Assets (26 files):                               │
    │ - swagger-ui-bundle.js (v5.25.3)                       │
    │ - swagger-editor.js (v4.14.6)                          │
    │ - CSS, fonts, icons, LICENSE                           │
    └──────────────────────────────────────────────────────────┘
                             │
                             ↓
    ┌──────────────────────────────────────────────────────────┐
    │         HTTP Response to Browser/Client                  │
    │                                                           │
    │ 1. GET /api/doc      → Rendered doc.html               │
    │ 2. GET /api/doc/swagger.json → JSON response           │
    │ 3. GET /api/doc/editor       → Rendered editor.html    │
    │ 4. GET /api/doc/static/*     → Assets (CSS/JS/images) │
    └──────────────────────────────────────────────────────────┘
```

---

## Component Architecture

### 1. Entry Point Layer (swagger_ui/__init__.py)

**Responsibility:** Public API gateway

```python
def api_doc(app, **kwargs) -> None:
    """Unified entry point for all frameworks."""
    doc = ApplicationDocument(app, **kwargs)
    handler = doc.match_handler()
    if not handler:
        raise Exception(f"No handler found for {app}")
    return handler(doc)
```

**Features:**
- Parameter validation
- Configuration normalization
- Legacy API generation (framework_api_doc functions)

**Exported API:**
- `api_doc()` - Main entry point
- `{framework}_api_doc()` - Legacy framework-specific functions
- `supported_list` - Available framework handlers

### 2. Core Document Class (swagger_ui/core.py - 167 LOC)

**Responsibility:** Application document configuration and rendering

**Key Responsibilities:**

1. **Configuration Management**
   - Store app instance and all parameters
   - Normalize configuration sources
   - Priority-based config loading

2. **Template Rendering**
   - Load Jinja2 templates from disk
   - Inject parameters into templates
   - Render HTML for Swagger UI and Editor

3. **URI Management**
   - Build framework-agnostic URIs
   - Generate absolute and relative paths
   - Construct static asset URLs

4. **Handler Matching**
   - Auto-detect framework
   - Select and return appropriate handler
   - Fall back gracefully on error

**Key Properties:**

```python
@property
def blueprint_name(self) -> str:
    """Generate unique blueprint identifier"""
    return f"bp{self.url_prefix.replace('/', '_')}"

@property
def static_dir(self) -> Path:
    """Path to static assets directory"""
    return Path(__file__).parent / 'static'

@property
def doc_html(self) -> str:
    """Rendered Swagger UI HTML"""
    # Jinja2 template rendering with injected parameters

@property
def editor_html(self) -> str:
    """Rendered Swagger Editor HTML"""
```

**Key Methods:**

```python
def get_config(self, host: str) -> dict:
    """Load OpenAPI spec with optional host injection"""
    # Config priority: dict → file → URL → string

def match_handler(self) -> Optional[Callable]:
    """Auto-detect framework and return handler function"""
    # Uses supported_list and match() function

def uri(self, suffix: str = '') -> str:
    """Build relative URI"""
    # Returns f"{self.url_prefix}{suffix}"

def root_uri_absolute(self, slashes: bool = False) -> str:
    """Build absolute root URI"""
```

### 3. Configuration Loading (swagger_ui/utils.py - 21 LOC)

**Responsibility:** Parse config from multiple formats

```python
def _load_config(content: Union[str, bytes]) -> dict:
    """Parse JSON or YAML content.

    Attempts JSON first, then YAML, raises on failure.
    """
```

**Used by:**
- `config_path` - Load from file
- `config_spec` - Parse string spec
- `config_url` - Parse remote response

### 4. Handler Discovery (swagger_ui/handlers/__init__.py)

**Responsibility:** Dynamic framework handler registry

```python
supported_list = [
    name for _, name, _ in pkgutil.iter_modules(__path__)
    if not name.startswith('_')
]
# Result: ['flask', 'tornado', 'sanic', 'aiohttp', 'quart',
#          'starlette', 'falcon', 'bottle', 'chalice']
```

**Features:**
- No hardcoded registry
- Auto-discovers handler modules
- Extensible: add module file = new framework support

### 5. Framework Handlers (swagger_ui/handlers/{framework}.py)

**Pattern:** Strategy pattern - one handler per framework

**Interface (All handlers implement):**

```python
def handler(doc: ApplicationDocument) -> None:
    """Register routes with framework app.

    Framework-specific setup:
    - Create request handlers (HTML, JSON, static)
    - Register routes with app
    - Modifies doc.app in-place
    """

def match(doc: ApplicationDocument) -> Optional[Callable]:
    """Return handler if framework matches, else None.

    Tests if doc.app is instance of framework's app class.
    """
```

**Framework-Specific Patterns:**

| Framework | Pattern | Route Registration | Static Files |
|-----------|---------|-------------------|--------------|
| Flask | Blueprint | @blueprint.route() | static_folder |
| Tornado | RequestHandler | app.add_handlers() | StaticFileHandler |
| Sanic | Blueprint | @blueprint.get() | blueprint.static() |
| aiohttp | Router | router.add_get() | router.add_static() |
| Quart | Blueprint | @blueprint.get() | Blueprint.static() |
| Starlette | Router | router.add_route() | StaticFiles |
| Falcon | App | app.add_route() | Manual in handler |
| Bottle | Decorator | @app.get() | static_file() |
| Chalice | Blueprint | @blueprint.route() | Manual MIME type |

### 6. Templates Layer (swagger_ui/templates/)

**Files:**
- `doc.html` - Swagger UI entry point (48 LOC)
- `editor.html` - Swagger Editor entry point

**Features:**
- Jinja2 templating
- Parameter injection for SwaggerUIBundle()
- OAuth2 configuration support
- Custom CSS injection

**Template Variables:**
- `url_prefix` - Base documentation path
- `title` - HTML page title
- `parameters` - Swagger UI bundle parameters
- `oauth2_config` - OAuth2 settings
- `custom_css` - Custom CSS URL

### 7. Static Assets Layer (swagger_ui/static/)

**Contents (26 files):**

**Swagger UI v5.25.3:**
- swagger-ui-bundle.js (main library)
- swagger-ui.css
- swagger-initializer.js
- oauth2-redirect.html

**Swagger Editor v4.14.6:**
- swagger-editor.js, swagger-editor-bundle.js
- swagger-editor.css

**Resources:**
- favicon-16x16.png, favicon-32x32.png
- Source maps (.js.map, .css.map)
- LICENSE

---

## Configuration Flow

### Configuration Loading Pipeline

```
User calls: api_doc(app, config_path='./spec.yaml', ...)
                    │
                    ↓
ApplicationDocument.__init__()
    │
    ├─ Store: app, config_path, url_prefix, title, etc.
    │
    └─ Later, on first request to GET /api/doc:
                    │
                    ↓
        handler(doc) → Route handler called
                    │
                    ↓
        doc.get_config(host='localhost:8000')
                    │
        Priority chain:
        ├─ Is config dict provided? Use it
        │
        ├─ Else, is config_path provided?
        │   ├─ File exists? Load & parse (JSON or YAML)
        │   └─ Success? Use it
        │
        ├─ Else, is config_url provided?
        │   ├─ Fetch URL
        │   ├─ Parse response (JSON or YAML)
        │   └─ Success? Use it
        │
        ├─ Else, is config_spec provided?
        │   ├─ Parse string (JSON or YAML)
        │   └─ Success? Use it
        │
        ├─ Else, config_rel_url pointing to external?
        │   └─ Return from ApplicationDocument (no serving)
        │
        └─ Else, FAIL - No config source
                    │
                    ↓
        Optionally inject host:
        ├─ If 'host' not in config AND host_inject=True
        │   └─ Add: config['host'] = request.host
        │
        └─ Return config dict
```

### Template Rendering Pipeline

```
ApplicationDocument.doc_html property:
                    │
                    ↓
1. Load Jinja2 templates (once, cached)
                    │
                    ↓
2. Build parameters dict:
   - dom_id: "#swagger-ui"
   - url: swagger_json_uri_absolute()
   - deepLinking: true
   - displayRequestDuration: true
   - ... (from default + user-provided)
                    │
                    ↓
3. Build oauth2_config dict (if provided):
   - clientId, clientSecret, realm, etc.
                    │
                    ↓
4. Render doc.html template:
   - Inject parameters into SwaggerUIBundle()
   - Inject oauth2_config if present
   - Inject custom_css URL if provided
   - Inject title, url_prefix, etc.
                    │
                    ↓
5. Return rendered HTML string
```

---

## Handler Matching Algorithm

```
api_doc(app, config_path='./spec.yaml', app_type=None, ...)
                    │
                    ↓
ApplicationDocument(app, app_type=None, ...)
                    │
                    ↓
match_handler() called:
                    │
    Step 1: Explicit match (if app_type provided)
    ├─ Try to import: swagger_ui.handlers.{app_type}
    ├─ Get: module.handler function
    └─ Return handler (or raise if not found)
                    │
    Step 2: Auto-detect (if app_type=None)
    ├─ For each name in supported_list:
    │   ├─ Import: swagger_ui.handlers.{name}
    │   ├─ Call: module.match(self)
    │   ├─ If returns handler, return it
    │   └─ Otherwise, continue loop
    │
    └─ After loop: Raise "No handler found" exception
```

---

## Request Flow (GET /api/doc)

```
1. User visits: http://localhost:5000/api/doc
                    │
                    ↓
2. Framework routes to registered handler
   (Flask: blueprint route decorator)
   (Tornado: RequestHandler)
   (Sanic: blueprint handler)
   etc.
                    │
                    ↓
3. Handler function called:
   get_html = doc.doc_html  # Rendered template
                    │
                    ↓
4. ApplicationDocument.doc_html property:
   ├─ Render Jinja2 template
   ├─ Inject SwaggerUIBundle parameters
   ├─ Inject oauth2_config if present
   └─ Return HTML string
                    │
                    ↓
5. Framework returns HTML response:
   ├─ Status: 200 OK
   ├─ Content-Type: text/html
   └─ Body: rendered HTML
                    │
                    ↓
6. Browser receives HTML:
   ├─ Parses SwaggerUIBundle() call
   ├─ Loads swagger-ui-bundle.js from /api/doc/static/
   ├─ Fetches spec from /api/doc/swagger.json
   └─ Renders interactive documentation
```

---

## Design Patterns Used

### 1. Strategy Pattern
**Each framework = independent strategy**

```
ApplicationDocument holds reference to framework app
        │
        ├─ Flask? Use Flask strategy (Blueprint)
        ├─ Tornado? Use Tornado strategy (RequestHandler)
        ├─ Sanic? Use Sanic strategy (Blueprint + async)
        └─ etc.
```

**Benefit:** Easy to add new frameworks without core changes

### 2. Factory/Registry Pattern
**Auto-discovery of available handlers**

```
supported_list = [auto-discovered module names]
        │
        ├─ No hardcoded list
        ├─ pkgutil.iter_modules() finds them
        └─ Dynamic at runtime
```

**Benefit:** Add framework = add file, no registry update

### 3. Adapter Pattern
**ApplicationDocument adapts to framework differences**

```
Normalizes:
├─ Route registration APIs
├─ Static file serving
├─ Response generation
└─ URI building
```

**Benefit:** Handlers don't need framework knowledge

### 4. Template Method Pattern
**Core flow defined once, details in handlers**

```
api_doc():
├─ Create ApplicationDocument
├─ Call match_handler()
├─ Call handler(doc)
└─ handlers fill in details
```

**Benefit:** Consistent flow for all frameworks

### 5. Builder Pattern
**Flexible configuration**

```
api_doc(app,
    config_path='./spec.yaml',
    url_prefix='/api/doc',
    title='API docs',
    editor=True,
    parameters={...},
    oauth2_config={...})
```

**Benefit:** Easy to add new config options

---

## Data Flow Diagram

```
┌─────────────────────────────────────────────────────────┐
│  User Request Flow                                       │
└─────────────────────────────────────────────────────────┘

1. GET /api/doc
   │
   ├─ Route handler in framework (registered by handler())
   │
   ├─ Calls: doc.doc_html (property)
   │   │
   │   ├─ Load Jinja2 templates
   │   │
   │   ├─ Render with parameters:
   │   │   ├─ Swagger UI bundle params
   │   │   ├─ url_prefix
   │   │   ├─ title
   │   │   └─ oauth2_config
   │   │
   │   └─ Return rendered HTML
   │
   └─ Response: 200 OK with HTML

2. GET /api/doc/swagger.json
   │
   ├─ Route handler in framework
   │
   ├─ Calls: doc.get_config(request.host)
   │   │
   │   ├─ Load config from:
   │   │   ├─ dict (if provided)
   │   │   ├─ config_path file (if provided)
   │   │   ├─ config_url remote (if provided)
   │   │   └─ config_spec string (if provided)
   │   │
   │   ├─ Parse JSON/YAML
   │   │
   │   ├─ Optionally inject host
   │   │
   │   └─ Return spec dict
   │
   └─ Response: 200 OK with JSON

3. GET /api/doc/static/{path}
   │
   ├─ Route handler for static files
   │
   ├─ Framework serves from:
   │   └─ {static_dir}/{path}
   │
   └─ Response: 200 OK with asset (CSS/JS/image)

4. GET /api/doc/editor (if editor=True)
   │
   ├─ Route handler in framework
   │
   ├─ Calls: doc.editor_html (property)
   │   │
   │   ├─ Load editor.html template
   │   │
   │   ├─ Render with parameters
   │   │
   │   └─ Return rendered HTML
   │
   └─ Response: 200 OK with HTML
```

---

## Extension Points

### 1. Adding New Framework Support

**Process:**
1. Create `swagger_ui/handlers/{framework}.py`
2. Implement `handler(doc)` and `match(doc)`
3. Auto-discovery finds it via pkgutil
4. Add test in `test/{framework}_test.py`
5. Update README

**Example:**
```python
# swagger_ui/handlers/fastapi.py
def handler(doc):
    """Register routes with Starlette app."""
    # FastAPI uses Starlette under the hood
    # Implement route registration

def match(doc):
    try:
        from fastapi import FastAPI
        if isinstance(doc.app, FastAPI):
            return handler
    except ImportError:
        pass
    return None
```

### 2. Customizing Swagger UI

```python
# Custom parameters
parameters = {
    "deepLinking": "true",
    "displayRequestDuration": "true",
    "layout": "\"StandaloneLayout\"",
}
api_doc(app, config_path='./spec.yaml', parameters=parameters)

# Custom CSS
api_doc(app, custom_css='https://example.com/style.css')

# OAuth2 configuration
oauth2_config = {
    "clientId": "\"your-id\"",
    "clientSecret": "\"your-secret\"",
}
api_doc(app, oauth2_config=oauth2_config)
```

### 3. Custom Config Sources

Extend `_load_config()` or `ApplicationDocument.get_config()`:

```python
# Could support additional formats
def get_config(self, host):
    if self.config:
        return self.config

    # Could add: TOML, XML, etc.
    # Could add: database, API, etc.
```

---

## Deployment Architecture

### Single-Host Deployment

```
┌─────────────────────┐
│  Python Web App     │
│  (Flask/Tornado/etc)│
│                     │
│  api_doc(app, ...)  │
│  Registers routes   │
└────────┬────────────┘
         │
         ├─ GET /api/doc        → Swagger UI
         ├─ GET /api/doc/swagger.json → Spec
         ├─ GET /api/doc/editor → Editor
         └─ GET /api/doc/static/* → Assets
         │
         ↓
Browser: localhost:5000/api/doc
```

### Multi-Server Deployment

```
Load Balancer
    │
    ├─ Server 1: Flask + api_doc()
    ├─ Server 2: Flask + api_doc()
    └─ Server 3: Flask + api_doc()

Each server registers same routes
Load balancer distributes requests
```

### Serverless Deployment (Chalice)

```
AWS Lambda + API Gateway + Chalice
    │
    api_doc(app, ...)
    │
    ├─ GET /api/doc → Handler returns HTML
    ├─ GET /api/doc/swagger.json → Handler returns JSON
    └─ GET /api/doc/static/* → Manual MIME handling
```

---

## Performance Considerations

### Load Time
- Handler detection: < 100ms (first request only)
- Template rendering: < 50ms
- Static asset serving: < 10ms (framework-dependent)

### Caching
- **Jinja2 templates:** Auto-cached by Jinja2
- **Static assets:** Framework-level caching
- **Config:** Currently not cached (loads on each request)

### Optimization Opportunities
1. Cache config with TTL for remote URLs
2. Minify static assets
3. Bundle static assets as single file
4. Use gzip compression for responses

---

## Scalability

**Stateless Design:**
- No server-side session
- Each request independent
- Safe for horizontal scaling
- No database dependency

**Resource Requirements:**
- Minimal: ~5MB disk (static assets)
- CPU: Negligible (template rendering)
- Memory: < 10MB per process

**Horizontal Scaling:**
- Deploy on multiple servers
- Use load balancer
- No coordination needed
- Each server independent
