"""Opt-in provider test with allowlisted diagnostics, independent of Qwen.

Never save raw exceptions, credentials, query results, user paths, proxy URLs,
response bodies or headers. The query used here is fixed and public.
"""
from datetime import datetime, timezone
from importlib import metadata
import json
import os
from pathlib import Path
import platform

import requests
from .errors import AppError
from .web_errors import WebRequestError
from .web_tools import WebTools, API_ROOT, secret_path


def check_connection(web=None) -> dict:
    web = web if web is not None else WebTools()
    if not web.status()['configurada']:
        raise WebRequestError('WEB_SEM_CHAVE', 'Não há chave configurada.',
            'Execute CONFIGURAR_PESQUISA_WEB_AYLA.bat. Não cole a chave no chat.', phase='configuracao', status_code=503)
    results = web.search('Ollama documentação oficial pesquisa web', timeout=25)
    if not results:
        raise WebRequestError('WEB_SEM_FONTES', 'O serviço respondeu, mas não retornou fontes utilizáveis neste teste.',
            'O acesso não foi declarado validado. Tente novamente mais tarde.', phase='conteudo')
    return {'ok': True, 'codigo': 'WEB_OK', 'etapa': 'concluido',
            'fontes_recebidas': len(results),
            'mensagem': 'Conexão testada: o serviço retornou fontes nesta consulta. Isso não testa a decisão do Qwen nem garante disponibilidade futura.',
            'verificado_em': datetime.now(timezone.utc).isoformat()}


def local_metadata() -> dict:
    packages = {}
    for name in ('requests', 'certifi', 'urllib3'):
        try:
            packages[name] = metadata.version(name)
        except metadata.PackageNotFoundError:
            packages[name] = 'não instalado'
    environment_key = os.getenv('OLLAMA_API_KEY', '').strip()
    stored_key = ''
    try:
        config = json.loads(secret_path().read_text(encoding='utf-8'))
        value = config.get('ollama_api_key', '')
        if isinstance(value, str):
            stored_key = value.strip()
    except (OSError, ValueError, TypeError, AttributeError):
        pass
    source = 'variavel_OLLAMA_API_KEY' if environment_key else ('arquivo_local' if stored_key else 'ausente')
    try:
        proxies = requests.utils.get_environ_proxies(API_ROOT + '/web_search')
        proxy_present = bool(requests.utils.select_proxy(API_ROOT + '/web_search', proxies))
    except (OSError, ValueError):
        proxy_present = 'não determinado'
    return {'versao': '0.5.3', 'python': platform.python_version(), 'sistema': platform.system(),
            'pacotes': packages, 'origem_chave': source,
            'variavel_sobrepoe_arquivo_diferente': bool(environment_key and stored_key and environment_key != stored_key),
            'proxy_detectado': proxy_present,
            'certificado_personalizado_configurado': bool(os.getenv('REQUESTS_CA_BUNDLE') or os.getenv('CURL_CA_BUNDLE')),
            'verificacao_https': True,
            'destino_fixo': API_ROOT + '/web_search',
            'repeticao_automatica': False}


def build_report(web=None) -> dict:
    report = {'diagnostico': local_metadata(), 'verificado_em': datetime.now(timezone.utc).isoformat()}
    try:
        report.update(check_connection(web))
    except WebRequestError as exc:
        report.update({'ok': False, **exc.public_details()})
    except AppError:
        report.update({'ok': False, 'codigo': 'WEB_FALHA_NAO_CLASSIFICADA', 'etapa': 'aplicacao',
            'mensagem': 'A aplicação não concluiu o teste. Nenhum detalhe bruto foi incluído neste relatório.'})
    return report


def report_text(report: dict) -> str:
    env = report['diagnostico']
    lines = ['AYLA 0.5.3 | Diagnóstico de pesquisa', '',
             f"Resultado: {report['codigo']}", f"Etapa: {report.get('etapa', 'não determinada')}",
             f"HTTP: {report.get('http_status') if report.get('http_status') is not None else 'não registrado'}",
             '', report['mensagem'], '',
             'Origem da chave: ' + env['origem_chave'],
             'Variável antiga sobrepõe chave salva diferente: ' + ('sim' if env['variavel_sobrepoe_arquivo_diferente'] else 'não'),
             'Proxy configurado detectado: ' + str(env['proxy_detectado']),
             'Certificado personalizado configurado: ' + str(env['certificado_personalizado_configurado']),
             'Verificação HTTPS: ATIVADA',
             'Python: ' + env['python'] + ' | Sistema: ' + env['sistema'],
             'Bibliotecas: ' + json.dumps(env['pacotes'], ensure_ascii=False),
             '', 'Este relatório não contém chave, mensagens, listas, áudio, corpos HTTP, endereços de proxy ou caminhos pessoais.',
             'Ele não prova a compreensão do Qwen. Não houve repetição automática da consulta.',
             'Não envie web-secret.json, .env ou outros arquivos de credenciais.']
    return '\n'.join(lines) + '\n'


def run_diagnostic(web=None, destination: Path | None = None) -> dict:
    report = build_report(web)
    text = report_text(report)
    print('\n' + text)
    directory = destination or (Path(__file__).resolve().parent / 'data')
    try:
        directory.mkdir(parents=True, exist_ok=True)
        for name, content in (
                ('pesquisa_diagnostico.json', json.dumps(report, ensure_ascii=False, indent=2)),
                ('pesquisa_diagnostico.txt', text)):
            dest = directory / name
            temp = dest.with_suffix(dest.suffix + '.tmp')
            temp.write_text(content, encoding='utf-8')
            temp.replace(dest)
        print('Relatório para compartilhar: ayla_v2/data/pesquisa_diagnostico.txt')
    except OSError:
        print('Não consegui salvar o relatório. O resultado acima continua válido.')
    return report


def main() -> int:
    print('AYLA | Teste da pesquisa real, independente do Qwen.\n')
    print('Envia UMA consulta pública sobre documentação do Ollama. Pode consumir uma consulta da conta.')
    print('Não envia suas mensagens, listas ou áudio. Nunca cole a chave aqui.')
    print('Usa o proxy/certificados já configurados na rede, sem desligar HTTPS nem alterar o Windows.\n')
    if input('Executar o teste agora? [s/N] ').strip().lower() != 's':
        print('Cancelado; nenhuma pesquisa realizada.'); return 0
    result = run_diagnostic()
    return 0 if result['ok'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
