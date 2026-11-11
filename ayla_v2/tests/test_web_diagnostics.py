"""Network failures are simulated. No key, provider, Qwen or real DNS required."""
import json
import socket
from unittest.mock import Mock

import pytest
import requests
from fastapi.testclient import TestClient

from ayla_v2.check_web import build_report, local_metadata, run_diagnostic
from ayla_v2.main import create_app
from ayla_v2.setup_web import save_key
from ayla_v2.web_errors import WebRequestError
from ayla_v2.web_tools import WebTools, _BearerAuth

SECRET = 'DUMMY-only-for-tests-not-a-real-key'
LEAK = 'private-data-and-user-path-must-never-appear'


def clear_network(monkeypatch):
    for name in ('HTTP_PROXY','HTTPS_PROXY','ALL_PROXY','NO_PROXY',
                 'http_proxy','https_proxy','all_proxy','no_proxy',
                 'REQUESTS_CA_BUNDLE','CURL_CA_BUNDLE'):
        monkeypatch.delenv(name, raising=False)


def response(status=200, payload=None):
    r = requests.Response()
    r.status_code = status
    r._content = json.dumps(payload if payload is not None else {
        'results': [{'title': 'Ollama', 'url': 'https://ollama.com/', 'content': 'Documentação'}]
    }).encode()
    r.headers['Content-Type'] = 'application/json'
    return r


def failing(exc):
    t = Mock()
    t.post.side_effect = exc
    return WebTools(SECRET, t)


@pytest.mark.parametrize('status', [301,307,400,401,402,403,404,407,408,413,422,429,500,502,503,504,599])
def test_http_code_is_preserved_without_response_body(status):
    t = Mock(); t.post.return_value = response(status, {'error': LEAK + SECRET})
    with pytest.raises(WebRequestError) as error:
        WebTools(SECRET, t).search('query')
    details = error.value.public_details()
    assert details['codigo'] == f'WEB_HTTP_{status}'
    assert details['http_status'] == status
    assert LEAK not in json.dumps(details) and SECRET not in json.dumps(details)
    assert t.post.call_count == 1


@pytest.mark.parametrize('error,expected', [
    (requests.exceptions.SSLError(LEAK + SECRET), 'WEB_TLS'),
    (requests.exceptions.ProxyError(LEAK + SECRET), 'WEB_PROXY'),
    (requests.ConnectTimeout(LEAK), 'WEB_CONNECT_TIMEOUT'),
    (requests.ReadTimeout(LEAK), 'WEB_READ_TIMEOUT'),
    (requests.Timeout(LEAK), 'WEB_TIMEOUT'),
    (requests.ConnectionError(LEAK), 'WEB_CONEXAO'),
    (requests.RequestException(LEAK), 'WEB_TRANSPORTE'),
    (requests.exceptions.InvalidSchema(LEAK), 'WEB_CONFIG_REDE'),
    (OSError(LEAK), 'WEB_CA_CONFIG'),
])
def test_transport_error_is_specific_and_sanitized(error, expected):
    web = failing(error)
    with pytest.raises(WebRequestError) as e:
        web.search('public query')
    assert e.value.code == expected
    assert LEAK not in str(e.value) and SECRET not in str(e.value)
    assert e.value.__cause__ is None
    assert web._transport.post.call_count == 1


@pytest.mark.parametrize('underlying,expected',[
    (socket.gaierror(11001, LEAK), 'WEB_DNS'),
    (ConnectionRefusedError(111, LEAK), 'WEB_CONEXAO_RECUSADA'),
    (ConnectionResetError(104, LEAK), 'WEB_CONEXAO_INTERROMPIDA'),
])
def test_nested_network_cause(underlying, expected):
    exc = requests.ConnectionError(LEAK)
    exc.__cause__ = underlying
    with pytest.raises(WebRequestError) as e:
        failing(exc).search('public query')
    assert e.value.code == expected and LEAK not in str(e.value)


def test_200_invalid_json_not_reported_as_internet_failure():
    t = Mock(); t.post.return_value = response()
    t.post.return_value._content = ('<html>' + LEAK + SECRET).encode()
    with pytest.raises(WebRequestError) as e:
        WebTools(SECRET, t).search('public query')
    assert e.value.code == 'WEB_JSON_INVALIDO'
    assert LEAK not in str(e.value) and SECRET not in str(e.value)


@pytest.mark.parametrize('credential', ['key with space', 'key\nsecret', 'chavé-inválida', 'key\x00secret', 'key\x7fsecret'])
def test_bad_header_key_fails_without_network(credential):
    t = Mock()
    with pytest.raises(WebRequestError) as e:
        WebTools(credential, t).search('public query')
    assert e.value.code == 'WEB_FORMATO_CHAVE'
    t.post.assert_not_called()


def test_key_setup_rejects_non_ascii(tmp_path):
    with pytest.raises(ValueError):
        save_key('abcdefghijklmn\u00e9', tmp_path/'secret')
    assert not (tmp_path/'secret').exists()


def test_fixed_endpoint_and_verified_tls_no_redirect_no_retry():
    t = Mock(); t.post.return_value = response()
    WebTools(SECRET, t).search('public query')
    args, kwargs = t.post.call_args
    assert args == ('https://ollama.com/api/web_search',)
    assert kwargs['verify'] is True and kwargs['allow_redirects'] is False
    assert isinstance(kwargs['auth'], _BearerAuth)
    assert t.post.call_count == 1
    assert SECRET not in repr(kwargs['auth'])


def test_environment_proxy_and_ca_are_used_without_netrc(monkeypatch, tmp_path):
    clear_network(monkeypatch)
    monkeypatch.setenv('HTTPS_PROXY', 'http://proxy-user:proxy-password@proxy.test:3128')
    monkeypatch.setenv('REQUESTS_CA_BUNDLE', str(tmp_path/'trusted-ca.pem'))
    # If requests consults .netrc, fail. Auth is supplied explicitly.
    monkeypatch.setattr(requests.sessions, 'get_netrc_auth', lambda *a, **k: pytest.fail('.netrc read'))
    calls=[]
    def send(self, request, **kwargs):
        calls.append((request, kwargs))
        return response()
    monkeypatch.setattr(requests.sessions.Session, 'send', send)
    result = WebTools(SECRET).search('public query')
    assert result
    request, options = calls[0]
    assert request.headers['Authorization'] == 'Bearer ' + SECRET
    assert options['verify'] == str(tmp_path/'trusted-ca.pem')
    assert options['proxies']['https'] == 'http://proxy-user:proxy-password@proxy.test:3128'
    assert options['allow_redirects'] is False
    assert len(calls) == 1


def test_no_custom_ca_still_uses_verification(monkeypatch):
    clear_network(monkeypatch)
    options=[]
    def send(self, request, **kwargs):
        options.append(kwargs); return response()
    monkeypatch.setattr(requests.sessions.Session,'send',send)
    assert WebTools(SECRET).search('public query')
    assert options[0]['verify'] is True


def test_only_external_session_honors_environment(monkeypatch):
    t=Mock();t.post.return_value=response()
    monkeypatch.setattr('ayla_v2.web_tools.requests.Session',lambda:t)
    WebTools(SECRET).search('public query')
    assert t.trust_env is True
    t.close.assert_called_once()


def test_report_excludes_sensitive_details(monkeypatch, tmp_path):
    clear_network(monkeypatch)
    monkeypatch.setenv('OLLAMA_API_KEY', SECRET)
    monkeypatch.setenv('HTTPS_PROXY', 'http://secretuser:secretpass@private-host.test:3128')
    monkeypatch.setenv('REQUESTS_CA_BUNDLE', '/private/user/cert.pem')
    stored=tmp_path/'secret.json';stored.write_text(json.dumps({'ollama_api_key':'DIFFERENT-DUMMY-KEY'}))
    monkeypatch.setattr('ayla_v2.check_web.secret_path',lambda:stored)
    report = build_report(failing(requests.exceptions.ProxyError(LEAK+SECRET)))
    serialized=json.dumps(report)
    assert report['codigo']=='WEB_PROXY'
    assert report['diagnostico']['proxy_detectado'] is True
    assert report['diagnostico']['variavel_sobrepoe_arquivo_diferente'] is True
    for bad in (SECRET, LEAK, 'DIFFERENT-DUMMY-KEY','secretuser','secretpass','private-host.test','/private/user',str(stored)):
        assert bad not in serialized


def test_report_saves_safe_text_and_json(monkeypatch, tmp_path, capsys):
    monkeypatch.setenv('OLLAMA_API_KEY', SECRET)
    report=run_diagnostic(failing(requests.exceptions.SSLError(SECRET+LEAK)),tmp_path)
    assert not report['ok']
    for name in ('pesquisa_diagnostico.json','pesquisa_diagnostico.txt'):
        text=(tmp_path/name).read_text()
        assert 'WEB_TLS' in text and SECRET not in text and LEAK not in text
    printed=capsys.readouterr().out
    assert 'WEB_TLS' in printed and SECRET not in printed


def test_status_does_not_contact_service():
    t=Mock()
    assert WebTools(SECRET,t).status()['validada'] is False
    t.post.assert_not_called()


def test_ui_diagnostic_contains_safe_code_and_http(tmp_path):
    t=Mock(); t.post.return_value=response(503, {'error':SECRET+LEAK})
    app=create_app(tmp_path/'app.db',web_tools=WebTools(SECRET,t))
    with TestClient(app,base_url='http://127.0.0.1') as client:
        res=client.post('/api/pesquisa/testar',json={})
    assert res.status_code==502
    body=res.json()
    assert body['codigo']=='WEB_HTTP_503' and body['http_status']==503
    assert SECRET not in res.text and LEAK not in res.text


def test_check_success_only_after_usable_sources():
    t=Mock();t.post.return_value=response()
    report=build_report(WebTools(SECRET,t))
    assert report['ok'] and report['codigo']=='WEB_OK' and report['fontes_recebidas']==1
    assert t.post.call_count==1
