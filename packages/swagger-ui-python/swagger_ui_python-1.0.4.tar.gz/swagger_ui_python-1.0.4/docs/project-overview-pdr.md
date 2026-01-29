# Swagger UI Python - Project Overview & Product Development Requirements

**Last Updated:** 2026-01-21
**Project Status:** Active & Maintained
**Python Support:** 3.9, 3.10, 3.11, 3.12

---

## Project Vision & Goals

### Core Vision
Provide seamless Swagger UI (OpenAPI documentation) integration for Python web applications by abstracting framework-specific routing patterns into a unified, framework-agnostic API.

### Primary Goals
1. **Framework Agnosticism** - Single API works across 9+ Python web frameworks
2. **Minimal Friction** - Integrate Swagger UI with one function call
3. **Zero Configuration** - Auto-detect framework, sensible defaults
4. **Extensibility** - Add new framework support by contributing a handler module
5. **Production Ready** - Support async frameworks, proper error handling, CI/CD pipeline

---

## Key Features

### Supported Frameworks (9)
- Flask (Blueprint-based)
- Tornado (RequestHandler-based)
- Sanic (Blueprint-based async)
- aiohttp (Router-based async)
- Quart (Blueprint-based async)
- Starlette (Router-based async)
- Falcon (Sync & async support)
- Bottle (Decorator-based)
- Chalice (AWS Lambda-based)

### Core Capabilities
- **Auto Framework Detection** - Automatically identify and load correct handler
- **Multiple Config Sources** - File (YAML/JSON), URL, Python dict, or string
- **Swagger UI v5.25.3** - Latest stable version with full feature set
- **Swagger Editor v4.14.6** - Optional inline spec editor
- **Static Asset Serving** - Automatic CSS, JS, images, icons delivery
- **Customization Support** - Custom CSS, Swagger UI parameters, OAuth2 config
- **HTML Templating** - Jinja2-based doc.html and editor.html templates

### API Endpoints (Auto-Generated)
Standard routes created at specified url_prefix (default: `/api/doc`):
- `GET /api/doc` - Main Swagger UI documentation page
- `GET /api/doc/swagger.json` - OpenAPI/Swagger spec (if config not external)
- `GET /api/doc/editor` - Swagger Editor (if editor=True)
- `GET /api/doc/static/<path>` - Static assets (CSS, JS, images)

---

## Target Audience

### Primary Users
- Python web developers using Flask, Django, Tornado, Sanic, aiohttp, or other frameworks
- API teams wanting to publish OpenAPI documentation with minimal setup
- Organizations using AWS Lambda + Chalice for serverless APIs

### Use Cases
1. **Auto-Generated API Docs** - Display OpenAPI spec in interactive format
2. **Inline Spec Editor** - Allow testing and editing API specifications
3. **Multi-Framework Support** - Migrate between frameworks without rewriting config
4. **Microservices** - Document services regardless of underlying framework
5. **AWS Serverless** - Add API docs to Lambda-based Chalice applications

---

## Success Metrics

### Adoption Metrics
- **PyPI Downloads** - Target: 10k+ monthly downloads
- **GitHub Stars** - Track community interest
- **Framework Coverage** - Maintain support for 8+ frameworks
- **Python Version Coverage** - Support 3.9+

### Quality Metrics
- **Test Coverage** - Parametrized tests for all frameworks
- **CI/CD Pass Rate** - 100% passing on Python 3.9-3.12
- **Release Cadence** - Timely updates for Swagger UI/Editor versions
- **Zero Breaking Changes** - Backward compatibility maintained

### User Satisfaction
- **Documentation Quality** - Comprehensive guides, examples
- **Issue Response Time** - Address user issues promptly
- **Framework Support** - Handle requests for new framework support

---

## Technical Specifications

### Dependencies
**Runtime (Minimal):**
- jinja2 >=2.0 (HTML templating)
- PyYaml >=5.0 (YAML config parsing)
- packaging >=20.0 (Version comparison)

**Framework Handlers:** Optional (only required for specific framework)
- Flask, Tornado, Sanic, aiohttp, Quart, Starlette, Falcon, Bottle, Chalice

### Python Requirements
- **Minimum:** Python 3.9
- **Tested:** Python 3.9, 3.10, 3.11, 3.12
- **Max:** Python 3.12+ (when released)

### Architecture Style
- **Pattern:** Strategy + Factory/Registry + Adapter
- **Framework Integration:** Handler-based extensible architecture
- **Config Loading:** Multi-source with priority order
- **Auto-Detection:** pkgutil-based module discovery

---

## Functional Requirements

### FR1: Unified API Entry Point
- Single `api_doc()` function works across all frameworks
- Optional `app_type` parameter for explicit framework selection
- Returns None, modifies app in-place

### FR2: Configuration Management
- Support 5 config sources (dict, file, URL, string, external)
- Auto-detect YAML vs JSON format
- Fallback chain: provided > file > URL > string

### FR3: Route Registration
- Dynamically register routes for documentation endpoints
- Serve static assets (CSS, JS, images, etc.)
- Render HTML templates with injected parameters

### FR4: Framework Extensibility
- Handler interface: `handler(doc)` and `match(doc)` functions
- Auto-discovery via pkgutil.iter_modules()
- No core changes needed for new framework support

### FR5: Swagger UI Customization
- Pass parameters dict for SwaggerUIBundle configuration
- Support OAuth2 configuration
- Allow custom CSS injection

---

## Non-Functional Requirements

### NF1: Performance
- Handler detection < 100ms
- Config loading < 500ms
- Static asset serving < 50ms

### NF2: Reliability
- Graceful framework detection (no import errors)
- Proper error messages on misconfiguration
- Works in async and sync contexts

### NF3: Maintainability
- Handler modules < 100 LOC each
- Clear separation of concerns
- Comprehensive test coverage

### NF4: Compatibility
- Backward compatible API (legacy framework-specific functions)
- Support multiple framework versions
- Handle breaking changes (Falcon v2/v3/v4)

---

## Release Strategy

### Current Version
- **Latest:** 5.x.x
- **Swagger UI:** v5.25.3
- **Swagger Editor:** v4.14.6

### Update Process
- Monitor Swagger UI/Editor GitHub releases
- Use `tools/update.py` to extract new versions
- Validate with full test suite
- Tag release on GitHub

### Versioning
- Semantic versioning: MAJOR.MINOR.PATCH
- Minor bumps for framework support additions
- Patch bumps for bug fixes
- Major bumps for breaking changes

---

## Future Roadmap

### Short-term (Q1 2026)
- Add type hints for better IDE support
- Implement request-level caching for config
- Improve error messages and logging

### Medium-term (Q2-Q3 2026)
- Support for FastAPI (built-in Starlette support)
- GraphQL support integration
- Custom handler template system

### Long-term (Q4 2026+)
- OpenAPI v3.1 full support
- Streaming spec updates via WebSocket
- Interactive spec testing

---

## Stakeholders & Roles

| Role | Responsibility |
|------|-----------------|
| **Maintainer** | Release management, quality gate |
| **Contributors** | Framework support, bug fixes |
| **Users** | Bug reports, feature requests |
| **DevOps** | CI/CD pipeline, testing infrastructure |

---

## Acceptance Criteria for Features

All features must meet:
1. Handler works for target framework
2. All framework tests pass (Python 3.9-3.12)
3. No breaking changes to existing API
4. Documentation updated
5. Code review approved
6. Examples provided if applicable

---

## Known Constraints

- No built-in authentication (rely on framework auth)
- Config loading not cached (re-parsed per request for file/URL)
- Limited validation of OpenAPI spec structure
- Templates have inline JavaScript (not extracted)
- No CORS handling (delegated to app developer)

---

## Success Definition

The project is successful when:
1. Works flawlessly across all 9 supported frameworks
2. New framework requests can be fulfilled in < 1 hour
3. Users cite ease of integration in documentation
4. Maintains 100% backward compatibility
5. < 5 minute time-to-integration for new projects
