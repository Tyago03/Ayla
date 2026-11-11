"""Generic web tools: fixed Ollama HTTPS endpoints, public URLs only, bounded text.

No topic-specific handlers. A configured key is never exposed to the browser/model.
Retrieved text is untrusted evidence, not permission to execute actions.
"""
from __future__ import annotations
from datetime import datetime, timezone
import ipaddress
import json
import os
from pathlib import Path
import re
from urllib.parse import urlsplit, urlunsplit
import requests
from .errors import AppError
from .web_errors import WebRequestError, transport_error, http_error

API_ROOT = 'https://ollama.com/api'


def secret_path() -> Path:
    # Outside the repository and usual OneDrive Documents folder on Windows.
    root = Path(os.getenv('LOCALAPPDATA', str(Path.home() / '.config')))
    return root / 'Ayla' / 'web-secret.json'


def load_key() -> str:
    value = os.getenv('OLLAMA_API_KEY', '').strip()
    if value:
        return value
    try:
        return str(json.loads(secret_path().read_text(encoding='utf-8')).get('ollama_api_key', '')).strip()
    except (OSError, ValueError, TypeError, AttributeError):
        return ''


class _BearerAuth(requests.auth.AuthBase):
    """Explicit auth prevents .netrc from silently overriding our Bearer header."""
    def __init__(self, credential: str):
        self._credential = credential

    def __call__(self, request):
        request.headers['Authorization'] = 'Bearer ' + self._credential
        return request


def public_url(value: str) -> str:
    if not isinstance(value, str) or len(value) > 2048 or any(ord(c) < 33 for c in value):
        raise AppError('URL inválida.', 400)
    try:
        parts = urlsplit(value)
        host = (parts.hostname or '').rstrip('.').lower()
        if parts.scheme not in ('https', 'http') or not host or parts.username or parts.password or parts.port not in (None, 80, 443):
            raise ValueError()
        if '%' in host or '\\' in value or host in {'localhost', 'metadata.google.internal'} or host.endswith(('.local', '.localhost', '.internal', '.lan', '.home', '.test', '.example', '.invalid')):
            raise ValueError()
        try:
            address = ipaddress.ip_address(host)
        except ValueError:
            if re.fullmatch(r'[0-9.xXa-fA-F]+', host) and (host.startswith(('0x', '0X')) or host.replace('.', '').isdigit()):
                raise ValueError()
            if '.' not in host or not re.fullmatch(r'[a-z0-9.-]+', host):
                raise ValueError()
        else:
            if not address.is_global:
                raise ValueError()
        return urlunsplit((parts.scheme, parts.netloc, parts.path or '/', parts.query, ''))
    except (ValueError, TypeError) as exc:
        raise AppError('Somente endereços públicos HTTP/HTTPS são aceitos; sem rede local, portas especiais ou credenciais.', 400) from exc


class WebTools:
    def __init__(self, key: str | None = None, transport=None):
        self._key = key
        self._transport = transport

    def status(self) -> dict:
        return {'configurada': bool(self._key if self._key is not None else load_key()),
                'provedor': 'Ollama Web Search', 'validada': False,
                'nota': 'Configuração presente não garante validade, saldo ou disponibilidade.'}

    def _post(self, endpoint: str, data: dict, timeout: float = 25) -> dict:
        if endpoint not in {'web_search', 'web_fetch'}:
            raise AppError('Endpoint de pesquisa não permitido.', 400)
        credential = self._key if self._key is not None else load_key()
        if not credential:
            raise WebRequestError('WEB_SEM_CHAVE', 'Pesquisa não configurada.',
                'Execute CONFIGURAR_PESQUISA_WEB_AYLA.bat. Não cole a chave no chat.',
                phase='configuracao', status_code=503)
        if not isinstance(credential, str) or not credential.isascii() or any(c.isspace() or ord(c) < 33 or ord(c) == 127 for c in credential):
            raise WebRequestError('WEB_FORMATO_CHAVE', 'A chave contém caracteres incompatíveis com o cabeçalho HTTP.',
                'Configure novamente pelo atalho usando somente a chave, sem espaços ou caracteres extras.',
                phase='configuracao', status_code=503)
        session = self._transport if self._transport is not None else requests.Session()
        if self._transport is None:
            # External HTTPS only: honor configured proxies/CA bundles. Local Qwen
            # requests continue to bypass proxies. Auth is explicit; no .netrc auth.
            session.trust_env = True
        try:
            response = session.post(API_ROOT + '/' + endpoint, json=data,
                headers={'Authorization': 'Bearer ' + credential, 'Accept': 'application/json'},
                auth=_BearerAuth(credential), verify=True,
                timeout=(8, max(1, min(timeout, 30))), allow_redirects=False)
            if not 200 <= response.status_code < 300:
                raise http_error(response.status_code)
            if len(response.content) > 2_000_000:
                raise WebRequestError('WEB_RESPOSTA_GRANDE', 'Resposta da pesquisa acima do limite desta versão.',
                    'Tente uma consulta mais específica.', phase='conteudo', http_status=response.status_code)
            result = response.json()
            if not isinstance(result, dict):
                raise ValueError()
            return result
        except WebRequestError:
            raise
        except (requests.RequestException, OSError) as exc:
            # JSONDecodeError also inherits RequestException in Requests.
            if isinstance(exc, requests.exceptions.JSONDecodeError):
                raise WebRequestError('WEB_JSON_INVALIDO', 'O serviço não retornou JSON válido.',
                    'Pode haver uma página intermediária de bloqueio. Confira a rede e envie o diagnóstico.', phase='conteudo') from None
            raise transport_error(exc) from None
        except (ValueError, TypeError) as exc:
            raise WebRequestError('WEB_RESPOSTA_INVALIDA', 'O serviço de pesquisa retornou dados inválidos.',
                'Confira o diagnóstico. A resposta não foi usada como fonte.', phase='conteudo') from None
        finally:
            if self._transport is None:
                session.close()

    def search(self, query: str, timeout: float = 25) -> list[dict]:
        if not isinstance(query, str) or not 2 <= len(query.strip()) <= 500:
            raise AppError('A consulta deve ter de 2 a 500 caracteres.', 400)
        payload = self._post('web_search', {'query': query.strip(), 'max_results': 4}, timeout)
        results = payload.get('results', [])
        if not isinstance(results, list):
            raise AppError('Formato de resultados inesperado.', 502)
        normalized = []
        for item in results[:4]:
            if not isinstance(item, dict):
                continue
            try:
                url = public_url(item.get('url'))
            except AppError:
                continue
            normalized.append({'titulo': str(item.get('title') or url)[:200], 'url': url,
                               'conteudo': str(item.get('content') or '')[:1800],
                               'tipo': 'trecho de busca', 'acesso': datetime.now(timezone.utc).isoformat()})
        return normalized

    def fetch(self, url: str, timeout: float = 25) -> dict:
        url = public_url(url)
        # Local backend NEVER requests the arbitrary target URL itself.
        payload = self._post('web_fetch', {'url': url}, timeout)
        return {'titulo': str(payload.get('title') or url)[:200], 'url': url,
                'conteudo': str(payload.get('content') or '')[:6500],
                'tipo': 'página lida', 'acesso': datetime.now(timezone.utc).isoformat()}
