# Swagger UI Python - Code Standards & Guidelines

**Last Updated:** 2026-01-21
**Python Versions:** 3.9+
**Style Guide:** PEP 8 (enforced via flake8)

---

## Code Style Guidelines

### Python Style (PEP 8)

**Enforcement:**
```bash
make format-check    # Check without modifying
make format          # Auto-format with autopep8 + isort
```

**Key Rules:**
- **Line Length:** Maximum 100 characters (`.flake8` config)
- **Indentation:** 4 spaces (never tabs)
- **Imports:** Sorted via isort, standard lib first
- **Naming:**
  - Classes: PascalCase (ApplicationDocument)
  - Functions/Variables: snake_case (api_doc, url_prefix)
  - Constants: UPPER_SNAKE_CASE (not used in codebase)
  - Private: Leading underscore (_load_config)

**Ignored Rules** (`.flake8`):
- E402 - Module level import not at top (for optional framework imports)
- W504 - Line break after binary operator

### Code Quality Tools

| Tool | Purpose | Config |
|------|---------|--------|
| **autopep8** | Auto-format to PEP8 | setup.cfg |
| **isort** | Sort imports | .isort.cfg |
| **flake8** | Lint checker | .flake8 |
| **djlint** | HTML template formatter | .djlintrc |

---

## Module Structure & Organization

### Handler Module Pattern

Each framework handler (e.g., `flask.py`) follows this structure:

```python
"""Flask integration for Swagger UI.

Provides handler and match functions for Flask applications using Blueprint.
"""

# 1. Imports (standard lib, third-party, local)
import json
from flask import Blueprint, jsonify, render_template_string

# 2. Optional framework import (wrapped in handler)
# Don't import at module level - frameworks are optional dependencies

# 3. Handler function
def handler(doc):
    """Register Swagger UI routes with Flask app.

    Args:
        doc (ApplicationDocument): Document configuration

    Returns:
        None (modifies doc.app in-place)
    """
    blueprint = Blueprint(
        doc.blueprint_name,
        __name__,
        url_prefix=doc.url_prefix,
        static_folder=doc.static_dir,
        static_url_path='/static'
    )

    @blueprint.route('', methods=['GET'])
    def swagger_ui():
        return doc.doc_html

    @blueprint.route('/swagger.json', methods=['GET'])
    def swagger_json():
        return jsonify(doc.get_config(request.host))

    # Register with app
    doc.app.register_blueprint(blueprint)

# 4. Match function
def match(doc):
    """Return handler if app is Flask instance, else None.

    Args:
        doc (ApplicationDocument): Document configuration

    Returns:
        Callable: handler function or None
    """
    try:
        from flask import Flask
        if isinstance(doc.app, Flask):
            return handler
    except ImportError:
        pass
    return None
```

### Handler Design Principles

1. **Minimal Imports** - Import frameworks only in match() or handler()
2. **No Module-Level Dependencies** - Frameworks are optional
3. **Focused Responsibility** - Route registration only
4. **Similar Structure** - All handlers follow same pattern
5. **No Cross-Handler Calls** - Each handler is independent
6. **Error Handling** - Graceful on framework import failure

### Core Module (core.py) Structure

```python
"""Core ApplicationDocument class."""

# Imports
from jinja2 import Environment, FileSystemLoader
from packaging.version import Version
import json, yaml

# Constants
class ApplicationDocument:
    """Main class handling app configuration and document generation.

    Responsibilities:
    - Store framework app instance
    - Load OpenAPI spec from multiple sources
    - Render HTML templates
    - Build URI paths
    - Match and select framework handler
    """

    # 1. Special methods
    def __init__(self, app, **kwargs):
        """Initialize with app and config."""
        pass

    def __repr__(self):
        return f"ApplicationDocument(url_prefix={self.url_prefix})"

    # 2. Properties (computed values)
    @property
    def blueprint_name(self):
        """Generate blueprint identifier from url_prefix."""
        pass

    @property
    def static_dir(self):
        """Return path to static assets."""
        pass

    # 3. Public methods (alphabetical)
    def get_config(self, host):
        """Get OpenAPI spec with optional host injection."""
        pass

    def match_handler(self):
        """Auto-detect framework and return handler."""
        pass

    def uri(self, suffix=''):
        """Build relative URI."""
        pass

    # 4. Private methods (leading underscore)
    def _load_template(self, name):
        """Load and cache Jinja2 template."""
        pass
```

---

## Function & Method Design

### Function Signature Guidelines

**Parameters:**
- Required parameters first
- Optional parameters with defaults after
- Use meaningful names (avoid x, y, z)
- Max 5 parameters (use dict/object for more)

**Example:**
```python
def api_doc(app, config_path=None, config_url=None,
            config_spec=None, config=None, url_prefix='/api/doc',
            title='API doc', editor=False, **kwargs):
    """Unified entry point for all frameworks.

    Args:
        app: Framework application instance
        config_path: Path to YAML/JSON spec file
        config_url: URL to remote spec
        config_spec: JSON/YAML string spec
        config: Python dict spec
        url_prefix: Base URL path (default: '/api/doc')
        title: HTML page title (default: 'API doc')
        editor: Enable spec editor (default: False)
        **kwargs: Additional config options

    Raises:
        Exception: If no handler matches app type
        RuntimeError: If no config source provided
    """
```

### Return Value Guidelines

- Single return value or tuple, never list for multiple returns
- None if function modifies object in-place (handlers)
- Explicit None (not just `return`)
- Document return type in docstring

**Example:**
```python
def match_handler(self):
    """Find matching framework handler.

    Returns:
        Callable: handler function, or None if no match
    """
    for name in supported_list:
        handler = self._try_load_handler(name)
        if handler:
            return handler
    return None
```

### Error Handling Pattern

```python
def handler(doc):
    """Register routes with app."""
    try:
        import framework_module
        if isinstance(doc.app, framework_module.AppClass):
            # Implementation
            pass
    except ImportError as e:
        # Framework not installed - expected
        pass
    except Exception as e:
        # Unexpected error - raise
        raise RuntimeError(f"Failed to initialize handler: {e}") from e
```

---

## Documentation Requirements

### Docstring Format (Google Style)

All public functions/classes must have docstrings:

```python
def get_config(self, host):
    """Load OpenAPI spec with optional host injection.

    Attempts to load config from multiple sources in priority order:
    1. config dict (provided in __init__)
    2. config_path file (YAML/JSON)
    3. config_url (HTTP/HTTPS)
    4. config_spec (JSON/YAML string)

    Args:
        host (str): Request host (e.g., 'localhost:8000')

    Returns:
        dict: OpenAPI specification

    Raises:
        ValueError: If config format invalid or all sources failed

    Example:
        spec = doc.get_config('localhost:5000')
        # Returns: {'openapi': '3.0.1', ...}
    """
```

### In-Code Comments

- Use for WHY, not WHAT (code shows WHAT)
- Explain non-obvious logic or workarounds
- Mention version-specific code or breaking changes

**Good:**
```python
# Version check for Falcon API compatibility (v3 changed response API)
if Version(falcon.__version__) >= Version('4.0.0'):
    resp.data = doc.doc_html.encode()  # v4.0+ uses resp.data
else:
    resp.body = doc.doc_html  # v2.x, v3.x use resp.body
```

**Bad:**
```python
# Set response data
resp.data = doc.doc_html.encode()  # Don't explain the obvious
```

---

## Testing Conventions

### Test File Organization

```
test/
├── conftest.py              # pytest fixtures
├── common.py                # Shared utilities
├── {framework}_test.py      # Framework-specific tests
└── conf/
    └── test3.yaml          # OpenAPI spec for tests
```

### Test Function Naming

```python
def test_flask_basic():
    """Test basic Flask integration."""
    pass

def test_flask_with_editor():
    """Test Flask with editor enabled."""
    pass

def test_flask_external_config():
    """Test Flask with external config URL."""
    pass
```

### Parametrized Test Pattern

```python
@pytest.mark.parametrize('mode,kwargs', [
    ('auto', {'config_path': 'test/conf/test3.yaml'}),
    ('explicit', {'app_type': 'flask', 'config_path': 'test/conf/test3.yaml'}),
    ('with_editor', {'config_path': 'test/conf/test3.yaml', 'editor': True}),
])
def test_flask(mode, kwargs):
    """Test multiple Flask configurations."""
    app = create_app()
    api_doc(app, **kwargs)
    # assertions...
```

### Test Assertions

```python
# Good - specific, clear
assert response.status_code == 200
assert 'swagger-ui' in response.text
assert 'openapi' in response.json

# Avoid - vague
assert response.ok
assert response  # Just checks truthy
```

### Test Fixtures (conftest.py)

```python
@pytest.fixture
def flask_app():
    """Create Flask app for testing."""
    from flask import Flask
    app = Flask(__name__)
    app.config['TESTING'] = True
    return app

@pytest.fixture
def config_content():
    """Load OpenAPI spec."""
    with open('test/conf/test3.yaml') as f:
        return f.read()
```

---

## Module Size & Complexity Management

### Size Constraints

| Module Type | Max LOC | Target LOC |
|-------------|---------|------------|
| Handler module | 100 | 40-60 |
| Core class | 250 | 150-200 |
| Utility function | 50 | 20-30 |
| Test file | 300 | 150-250 |

### Complexity Management

**When to Split:**
1. Single class > 250 lines
2. Single function > 50 lines
3. Too many responsibilities
4. Hard to test in isolation

**How to Split:**
1. Extract related methods to new class
2. Break function into helpers
3. Use composition over inheritance
4. Move framework-specific logic to handlers

---

## Import Organization

**Order (enforced by isort):**

```python
# 1. Standard library
import json
import sys
from pathlib import Path
from typing import Optional, Callable

# 2. Third-party
import yaml
from jinja2 import Environment, FileSystemLoader
from packaging.version import Version

# 3. Local
from . import core
from .utils import _load_config

# 4. Optional framework (inside function/handler only)
# Don't import at module level
```

**Rules:**
- No wildcard imports (`from X import *`)
- Avoid relative imports beyond package (use absolute)
- Optional frameworks imported only in handler/match
- Grouped by category with blank line between

---

## Type Hints (Future Enhancement)

While not currently implemented, the codebase is structured for easy addition:

```python
from typing import Optional, Dict, Any, Callable

def api_doc(
    app: Any,
    config: Optional[Dict[str, Any]] = None,
    config_path: Optional[str] = None,
    url_prefix: str = '/api/doc',
    editor: bool = False
) -> None:
    """Unified entry point for all frameworks."""
    pass

class ApplicationDocument:
    def __init__(self, app: Any, **kwargs: Any) -> None:
        pass

    @property
    def static_dir(self) -> Path:
        pass

    def get_config(self, host: str) -> Dict[str, Any]:
        pass
```

---

## Security Considerations

### Input Validation

- Validate config_path is readable file
- Validate config_url is proper HTTP(S) URL
- Sanitize html/url template variables
- No eval() or exec() on user input

### File System Safety

```python
# Good - resolved path checked
config_path = Path(config_path).resolve()
if not config_path.is_file():
    raise ValueError(f"Config file not found: {config_path}")

# Avoid - path traversal risk
with open(f"/configs/{user_input}"):  # Dangerous!
    pass
```

### Template Injection Prevention

- Jinja2 templates rendered with autoescape (default)
- Avoid using | safe filter for user input
- Config values properly escaped by template

---

## Performance Considerations

### Caching

**Current (No Caching):**
- Config reloaded on every request if file/URL
- Templates loaded once (Jinja2 auto-caches)

**Future Optimization:**
```python
# Could cache config with TTL
@functools.lru_cache(maxsize=128)
def get_config(self, host):
    # Load config once per host
    pass
```

### Module Loading

- Handlers loaded on first use (match_handler call)
- pkgutil.iter_modules() called once at import
- No overhead for unused frameworks

---

## Backward Compatibility

### API Stability

- Never remove public functions (mark deprecated instead)
- Never change function signatures
- New parameters must be optional with sensible defaults

### Example Compatibility Pattern

```python
# Old API (still works)
from swagger_ui import flask_api_doc
flask_api_doc(app, config_path='./spec.yaml')

# New API (recommended)
from swagger_ui import api_doc
api_doc(app, config_path='./spec.yaml')  # Same functionality

# Both implemented, new preferred
```

---

## Code Review Checklist

Before submitting PR:

- [ ] Code follows PEP 8 (run `make format-check`)
- [ ] All public functions have docstrings
- [ ] Tests pass locally (run `make pytest`)
- [ ] New tests added for new functionality
- [ ] No hardcoded secrets/paths
- [ ] Handler module < 100 LOC
- [ ] Imports organized and sorted
- [ ] Error handling for framework imports
- [ ] Backward compatibility maintained
- [ ] Documentation updated

---

## Common Patterns & Anti-patterns

### Pattern: Optional Framework Dependency

```python
# GOOD - Import in match/handler only
def match(doc):
    try:
        from flask import Flask
        if isinstance(doc.app, Flask):
            return handler
    except ImportError:
        pass
    return None

# BAD - Import at module level
from flask import Flask  # Fails if Flask not installed
```

### Pattern: Configuration Priority

```python
# GOOD - Try multiple sources
config = (
    self.config or  # Provided dict
    self._load_from_path() or  # File
    self._load_from_url() or  # Remote
    self._load_from_spec()  # String
)

# BAD - Ambiguous priority
if self.config_path:
    return load_file(self.config_path)
if self.config:
    return self.config
```

### Anti-pattern: Framework-Specific Core Logic

```python
# BAD - Mixing frameworks in core
if isinstance(doc.app, Flask):
    # Flask specific
    pass
elif isinstance(doc.app, Tornado):
    # Tornado specific
    pass

# GOOD - Each handler handles its framework
# core.py stays framework-agnostic
```

---

## Maintenance Guidelines

### Making Changes

1. **Before Edit:** Understand scope and impact
2. **While Editing:** Keep changes focused
3. **After Edit:** Test all affected areas
4. **Before Commit:** Verify no regressions

### Deprecating Features

1. Add deprecation warning: `warnings.warn("X deprecated, use Y", DeprecationWarning)`
2. Document in docstring: "Deprecated: Use Y instead"
3. Keep working for 2+ releases
4. Remove in major version

### Adding Framework Support

1. Copy existing handler (flask.py recommended)
2. Adapt route registration for framework
3. Add test in test/{framework}_test.py
4. Update README
5. Auto-discovery handles rest

---

## File Organization Rules

**Module files:**
```
swagger_ui/
├── __init__.py     # Public API exports only
├── core.py         # Main class (max 250 LOC)
├── utils.py        # Helpers (max 50 LOC)
└── handlers/       # Framework modules (max 100 LOC each)
```

**Naming:**
- All lowercase with underscore (file_name.py)
- Descriptive (not abbreviated)
- Framework handler = {framework}.py
- Private functions start with underscore

**Size Rules:**
- Keep files focused on single concern
- If > 200 LOC, consider splitting
- Extract repeated logic to utils.py
