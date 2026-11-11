"""Public, allowlisted network diagnostics. Never serialize raw exceptions or headers."""
from __future__ import annotations

import socket
import ssl
import requests
from .errors import AppError


class WebRequestError(AppError):
    def __init__(self, code: str, summary: str, action: str, *, phase: str,
                 http_status: int | None = None, status_code: int = 502):
        self.code = code
        self.summary = summary
        self.action = action
        self.phase = phase
        self.http_status = http_status
        super().__init__(f'[{code}] {summary} {action}', status_code)

    def public_details(self) -> dict:
        return {'codigo': self.code, 'etapa': self.phase,
                'http_status': self.http_status, 'mensagem': self.message,
                'proximo_passo': self.action}


def _chain(exc: BaseException):
    """Walk exception objects, not their potentially sensitive rendered strings."""
    todo = [exc]
    seen = set()
    while todo and len(seen) < 20:
        obj = todo.pop()
        if not isinstance(obj, BaseException) or id(obj) in seen:
            continue
        seen.add(id(obj))
        yield obj
        todo.extend([obj.__cause__, obj.__context__, getattr(obj, 'reason', None)])
        todo.extend(a for a in obj.args if isinstance(a, BaseException))


def transport_error(exc: BaseException) -> WebRequestError:
    if isinstance(exc, requests.exceptions.ProxyError):
        return WebRequestError('WEB_PROXY', 'A conexão com o proxy falhou.',
            'Confira a configuração de proxy/VPN da rede. Não desative proteção de segurança para contornar o erro.', phase='proxy')
    if isinstance(exc, requests.exceptions.SSLError):
        return WebRequestError('WEB_TLS', 'A conexão HTTPS não pôde ser validada.',
            'Confira data/hora do Windows, certificados e eventual inspeção HTTPS da rede. Não desative a verificação SSL.', phase='tls')
    if isinstance(exc, requests.ConnectTimeout):
        return WebRequestError('WEB_CONNECT_TIMEOUT', 'O tempo para conectar ao serviço terminou.',
            'Teste novamente e confira se a rede permite HTTPS para ollama.com. Não há confirmação de que a busca foi processada.', phase='conexao', status_code=504)
    if isinstance(exc, requests.ReadTimeout):
        return WebRequestError('WEB_READ_TIMEOUT', 'A conexão não entregou a resposta dentro do prazo.',
            'O serviço pode ter recebido a consulta. Tente mais tarde; não houve repetição automática.', phase='resposta', status_code=504)
    if isinstance(exc, requests.Timeout):
        return WebRequestError('WEB_TIMEOUT', 'O serviço de pesquisa demorou além do limite.',
            'Tente mais tarde; a consulta não foi repetida automaticamente.', phase='conexao_ou_resposta', status_code=504)
    if isinstance(exc, (requests.exceptions.InvalidURL, requests.exceptions.InvalidSchema,
                        requests.exceptions.MissingSchema)):
        return WebRequestError('WEB_CONFIG_REDE', 'Há uma configuração de endereço ou proxy inválida.',
            'Revise as configurações de rede e o diagnóstico, sem compartilhar valores de proxy ou credenciais.', phase='configuracao')
    nested = list(_chain(exc))
    if any(isinstance(e, socket.gaierror) or type(e).__name__ == 'NameResolutionError' for e in nested):
        return WebRequestError('WEB_DNS', 'Não foi possível resolver um endereço necessário à conexão.',
            'Confira a conexão e o DNS da rede; havendo proxy, o endereço que falhou pode ser o dele.', phase='dns')
    if any(isinstance(e, ConnectionRefusedError) or getattr(e, 'winerror', None) == 10061 for e in nested):
        return WebRequestError('WEB_CONEXAO_RECUSADA', 'A conexão foi recusada antes de obter uma resposta HTTP.',
            'Confira a rota de rede e eventuais regras de firewall ou proxy; ainda não é um diagnóstico de chave inválida.', phase='conexao')
    if any(isinstance(e, ConnectionResetError) or getattr(e, 'winerror', None) in (10053, 10054) for e in nested):
        return WebRequestError('WEB_CONEXAO_INTERROMPIDA', 'A conexão foi interrompida antes de concluir a resposta.',
            'Tente novamente e confira a rede. O erro não identifica sozinho quem interrompeu a conexão.', phase='conexao')
    if isinstance(exc, requests.ConnectionError):
        return WebRequestError('WEB_CONEXAO', 'Não consegui estabelecer ou manter a conexão com o serviço.',
            'Confira o relatório de rede e tente outra rede autorizada para comparar. A causa exata ainda não foi determinada.', phase='conexao')
    if isinstance(exc, OSError) and not isinstance(exc, requests.RequestException):
        return WebRequestError('WEB_CA_CONFIG', 'Não foi possível usar a configuração local de certificados.',
            'Confira o arquivo indicado por REQUESTS_CA_BUNDLE ou CURL_CA_BUNDLE, se configurado. Não desative HTTPS.', phase='configuracao_tls')
    return WebRequestError('WEB_TRANSPORTE', 'A requisição falhou antes de produzir um resultado utilizável.',
        'Envie somente o relatório sanitizado de VERIFICAR_PESQUISA_AYLA.bat. Não envie a chave nem o arquivo de configuração.', phase='transporte')


def http_error(status: int) -> WebRequestError:
    """HTTP evidence is not attributed to a specific server: a proxy may answer."""
    cases = {
        400: ('A requisição recebeu HTTP 400 (pedido inválido).', 'Não é prova de falta de internet. Envie o código do diagnóstico para revisar o contrato da API.'),
        401: ('A autenticação recebeu HTTP 401.', 'Confira a chave e a conta do Ollama. Uma variável OLLAMA_API_KEY antiga tem precedência sobre o arquivo salvo.'),
        402: ('O acesso recebeu HTTP 402.', 'Confira as condições de uso e o limite da conta no provedor antes de trocar o modelo.'),
        403: ('O acesso recebeu HTTP 403 (proibido).', 'Confira as permissões da conta e eventuais bloqueios da rede; isso não prova, sozinho, que a chave esteja errada.'),
        404: ('O endpoint recebeu HTTP 404 (não encontrado).', 'A falha é na API de pesquisa, não no modelo Qwen. Envie o diagnóstico sanitizado.'),
        407: ('A conexão recebeu HTTP 407 (autenticação do proxy).', 'Verifique o acesso ao proxy com o responsável pela rede. Não coloque a chave Ollama como senha do proxy.'),
        408: ('A requisição recebeu HTTP 408 (tempo esgotado).', 'Tente mais tarde; não houve nova tentativa automática.'),
        413: ('A requisição recebeu HTTP 413 (conteúdo grande demais).', 'Tente uma pergunta menor e envie o diagnóstico se ocorrer com a consulta padrão.'),
        422: ('A requisição recebeu HTTP 422 (dados não aceitos).', 'Envie o código do diagnóstico para revisar os parâmetros enviados.'),
        429: ('O limite de pesquisa foi atingido: HTTP 429.', 'Aguarde e confira os limites da conta. Não recrie chaves para contornar a limitação.'),
    }
    if 300 <= status < 400:
        return WebRequestError(f'WEB_HTTP_{status}', f'Redirecionamento HTTP {status} bloqueado.',
            'A chave não foi encaminhada para outro endereço. Confira o diagnóstico e a rede.', phase='http', http_status=status)
    if status in cases:
        summary, action = cases[status]
    elif 500 <= status <= 599:
        summary = f'A conexão recebeu HTTP {status} (falha do serviço ou de um intermediário).'
        action = 'Tente mais tarde. Esse código não demonstra um problema no Qwen e não exige recriar a chave por si só.'
    else:
        summary = f'A conexão recebeu um resultado HTTP inesperado: {status}.'
        action = 'Envie o diagnóstico sanitizado. Não envie a resposta bruta, cabeçalhos ou credenciais.'
    return WebRequestError(f'WEB_HTTP_{status}', summary, action, phase='http',
                           http_status=status, status_code=429 if status == 429 else 502)
