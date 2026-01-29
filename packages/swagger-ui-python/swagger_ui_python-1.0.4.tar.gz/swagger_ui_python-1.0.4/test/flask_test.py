import pytest
from flask import Flask

from swagger_ui import api_doc, flask_api_doc

from .common import config_content, config_path, parametrize_list


@pytest.fixture
def app():
    app = Flask(__name__)

    @app.route(r'/hello/world')
    def hello():
        return 'Hello World!!!'

    return app


@pytest.mark.parametrize('mode, kwargs', parametrize_list)
def test_flask(app, mode, kwargs):
    if kwargs['url_prefix'] in ('/', ''):
        return

    if kwargs.get('config_rel_url'):

        @app.route(kwargs['config_rel_url'])
        def swagger_config():
            return config_content

    if mode == 'auto':
        api_doc(app, **kwargs)
    else:
        flask_api_doc(app, **kwargs)

    url_prefix = kwargs['url_prefix']
    if url_prefix.endswith('/'):
        url_prefix = url_prefix[:-1]

    client = app.test_client()

    resp = client.get('/hello/world')
    assert resp.status_code == 200, resp.data

    resp = client.get(url_prefix)
    assert resp.status_code == 200, resp.data

    resp = client.get(f'{url_prefix}/static/LICENSE')
    assert resp.status_code == 200, resp.data

    resp = client.get(f'{url_prefix}/editor')
    if kwargs.get('editor'):
        assert resp.status_code == 200, resp.data
    else:
        assert resp.status_code == 404, resp.data

    if kwargs.get('config_rel_url'):
        resp = client.get(kwargs['config_rel_url'])
        assert resp.status_code == 200, resp.data
    else:
        resp = client.get(f'{url_prefix}/swagger.json')
        assert resp.status_code == 200, resp.data


def test_flask_base_url(app):
    """Test base_url parameter for reverse proxy support."""
    api_doc(app, config_path=config_path, url_prefix='/docs', base_url='/service/docs')
    client = app.test_client()

    # Routes should be registered at url_prefix
    resp = client.get('/docs')
    assert resp.status_code == 200, resp.data

    resp = client.get('/docs/swagger.json')
    assert resp.status_code == 200, resp.data

    # HTML should contain external URLs (base_url)
    html = resp.data.decode() if hasattr(resp, 'data') else resp.text
    resp = client.get('/docs')
    html = resp.data.decode()
    assert '/service/docs/static/swagger-ui.css' in html, html
    assert '/service/docs/swagger.json' in html, html
