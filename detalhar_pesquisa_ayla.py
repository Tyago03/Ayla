"""Diagnóstico isolado e opt-in do Ollama Web Search.

Não importa nem modifica o código da Ayla. Reutiliza a credencial local,
sem exibi-la, e envia uma única consulta pública depois da confirmação.
Não registra resposta bruta, cookies, cabeçalhos de autenticação ou resultados.
"""
from __future__ import annotations

from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import sys
import unicodedata
from urllib.parse import quote, quote_plus
import uuid

import requests

ENDPOINT = "https://ollama.com/api/web_search"
QUERY = "Ollama documentação oficial pesquisa web"
BODY_LIMIT = 16_384
PROJECT = Path(__file__).resolve().parent


class ConfigurationError(Exception):
    """Mensagem controlada; não usar dados da configuração no texto."""


class BearerAuth(requests.auth.AuthBase):
    def __init__(self, key: str) -> None:
        self._key = key

    def __call__(self, request):
        request.headers["Authorization"] = "Bearer " + self._key
        return request


def load_credentials() -> tuple[str, str, list[str], bool]:
    """Mesma precedência da Ayla 0.5.3: variável, depois arquivo local."""
    env_key = os.getenv("OLLAMA_API_KEY", "").strip()
    local_key = ""
    path = Path(os.getenv("LOCALAPPDATA", str(Path.home() / ".config"))) / "Ayla" / "web-secret.json"
    if path.exists():
        try:
            if path.stat().st_size > 16_384:
                raise ConfigurationError("Arquivo de configuração acima do limite esperado.")
            payload = json.loads(path.read_text(encoding="utf-8-sig"))
            value = payload.get("ollama_api_key", "") if isinstance(payload, dict) else None
            if value is not None and not isinstance(value, str):
                raise ConfigurationError("Formato inválido na configuração local. Não compartilhe esse arquivo.")
            local_key = (value or "").strip()
        except (OSError, ValueError) as exc:
            if not env_key:
                raise ConfigurationError("Não foi possível ler a configuração local. Não compartilhe esse arquivo.") from None
    key = env_key or local_key
    if not key:
        raise ConfigurationError("Nenhuma chave configurada; use o configurador existente da Ayla.")
    if (not 12 <= len(key) <= 512 or not key.isascii()
            or any(c.isspace() or ord(c) < 33 or ord(c) == 127 for c in key)):
        raise ConfigurationError("Formato inesperado da chave configurada. Ela não foi enviada.")
    return key, ("variavel_OLLAMA_API_KEY" if env_key else "arquivo_local"), [k for k in (env_key, local_key) if k], bool(env_key and local_key and env_key != local_key)


def redact(text: str, secrets: list[str]) -> str:
    """Defesa em camadas; não é garantia de remoção de todo dado pessoal possível."""
    text = unicodedata.normalize("NFKC", text)
    # Remove controles de terminal e marcadores bidirecionais.
    text = re.sub(r"\x1b\[[0-?]*[ -/]*[@-~]", "", text)
    for value in sorted(set(secrets), key=len, reverse=True):
        if not value:
            continue
        variants = {value, json.dumps(value)[1:-1], quote(value, safe=""), quote_plus(value)}
        for variant in sorted(variants, key=len, reverse=True):
            text = text.replace(variant, "[CREDENCIAL REMOVIDA]")
    text = re.sub(r"(?i)\b(?:bearer|basic)\s+[^\s\"'<>;,]+", "[AUTENTICACAO REMOVIDA]", text)
    text = re.sub(r"(?i)\b(?:api[_ -]?key|access[_ -]?token|refresh[_ -]?token|authorization|password|secret)\b\s*[:=]\s*[^\s,;]+", "[SEGREDO REMOVIDO]", text)
    text = re.sub(r"(?i)https?://[^\s<>\"']+", "[URL OMITIDA]", text)
    text = re.sub(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}", "[EMAIL OMITIDO]", text)
    text = re.sub(r"(?i)[A-Z]:\\[^\r\n\"<>]*", "[CAMINHO OMITIDO]", text)
    text = re.sub(r"/(?:home|Users)/[^\s\"<>]+", "[CAMINHO OMITIDO]", text)
    # IDs longos e fragmentos semelhantes a chaves, mesmo sem conhecer a chave.
    text = re.sub(r"(?<![\w])(?:[A-Za-z0-9_+./=\-]{24,})(?![\w])", "[IDENTIFICADOR OMITIDO]", text)
    text = "".join(c if not unicodedata.category(c).startswith("C") else " " for c in text)
    return re.sub(r"\s+", " ", text).strip()[:1200]


def safe_fields(payload: object, secrets: list[str]) -> list[str]:
    """Só campos de erro conhecidos. Não imprime JSON completo ou HTML."""
    if not isinstance(payload, dict):
        return []
    result = []
    for field in ("error", "message", "detail", "code"):
        value = payload.get(field)
        if isinstance(value, (str, int)) and not isinstance(value, bool):
            text = redact(str(value), secrets)
            if text:
                result.append(f"{field}: {text}")
        elif isinstance(value, dict):
            for subfield in ("message", "detail", "code", "type"):
                inner = value.get(subfield)
                if isinstance(inner, (str, int)) and not isinstance(inner, bool):
                    text = redact(str(inner), secrets)
                    if text:
                        result.append(f"{field}.{subfield}: {text}")
    return result[:10]


def response_report(response, secrets: list[str]) -> dict:
    result = {"http": int(response.status_code), "mensagens": [], "json": False,
              "corpo_limitado": False, "request_id": None, "fontes": None}
    # Somente UUID padronizado: útil para suporte e não um cabeçalho arbitrário.
    identifier = response.headers.get("x-request-id", "")
    try:
        if len(identifier) == 36:
            result["request_id"] = str(uuid.UUID(identifier))
    except (ValueError, TypeError, AttributeError):
        pass
    chunks = bytearray()
    for chunk in response.iter_content(chunk_size=1024):
        if not chunk:
            continue
        space = BODY_LIMIT - len(chunks)
        chunks.extend(chunk[:space])
        if len(chunk) > space or len(chunks) >= BODY_LIMIT:
            result["corpo_limitado"] = True
            break
    if not chunks:
        result["observacao"] = "O provedor não enviou corpo de resposta."
        return result
    try:
        payload = json.loads(bytes(chunks).decode("utf-8-sig"))
        result["json"] = True
    except (ValueError, UnicodeError):
        result["observacao"] = "Resposta sem JSON de erro legível ou acima do limite; conteúdo bruto não exibido."
        return result
    if 200 <= response.status_code < 300:
        if isinstance(payload, dict) and isinstance(payload.get("results"), list):
            result["fontes"] = len(payload["results"])
        else:
            result["observacao"] = "HTTP de sucesso, mas sem uma lista results reconhecida."
        return result
    result["mensagens"] = safe_fields(payload, secrets)
    if not result["mensagens"]:
        result["observacao"] = "Nenhum campo textual error/message/detail/code reconhecido."
    return result


def run_request(key: str, secrets: list[str]) -> dict:
    # Uma requisição. Sem retries, sem redirecionamento da credencial.
    with requests.Session() as session:
        session.trust_env = True
        with session.post(ENDPOINT,
                          json={"query": QUERY, "max_results": 1},
                          headers={"Accept": "application/json"},
                          auth=BearerAuth(key), verify=True,
                          allow_redirects=False, stream=True,
                          timeout=(8, 25)) as response:
            return response_report(response, secrets)


def report_text(result: dict, source: str, shadowed: bool) -> str:
    lines = ["AYLA | Mensagem de erro do provedor — teste isolado", "",
             "Data UTC: " + datetime.now(timezone.utc).isoformat(),
             "Destino: " + ENDPOINT,
             "Consulta: documentação pública do Ollama (fixa)",
             "Origem da chave: " + source,
             "Variável sobrepõe chave diferente: " + ("sim" if shadowed else "não"),
             "HTTPS validado; redirecionamentos e repetição automática desativados.",
             "HTTP: " + str(result.get("http", "não recebido")), ""]
    if result.get("request_id"):
        lines += ["ID da requisição para o suporte: " + result["request_id"], ""]
    lines.append("Mensagem do provedor (dados externos, após ocultação automática):")
    messages = result.get("mensagens") or []
    lines.extend(("  " + msg for msg in messages))
    if not messages:
        lines.append("  " + result.get("observacao", "Não há mensagem de erro textual."))
    if result.get("fontes") is not None:
        lines.append("Resultados recebidos: " + str(result["fontes"]))
    if result.get("corpo_limitado"):
        lines.append("Leitura limitada a 16 KiB; resposta bruta não gravada.")
    lines += ["", "Este teste não altera a Ayla, sua chave ou suas listas.",
              "Só campos de erro selecionados foram considerados; não executamos instruções da resposta.",
              "A ocultação automática não garante remover toda informação pessoal possível.",
              "Revise o texto antes de compartilhá-lo. Nunca envie web-secret.json."]
    return "\n".join(lines) + "\n"


def main() -> int:
    print("AYLA | Detalhar a recusa de pesquisa — sem atualizar a aplicação\n")
    print("Usa a chave já configurada. Não precisa colar nenhuma chave.")
    print("Envia UMA consulta pública ao Ollama. Pode consumir uma consulta da sua cota.")
    print("Não envia conversa, listas ou áudio. Não faz novas tentativas automaticamente.")
    print("Exibe somente campos de erro selecionados, com ocultação de credenciais.")
    try:
        answer = input("Executar agora? [s/N] ").strip().casefold()
        if answer != "s":
            print("Cancelado. Nenhuma consulta realizada.")
            return 0
        key, source, secrets, shadowed = load_credentials()
        try:
            result = run_request(key, secrets)
        except requests.exceptions.SSLError:
            result = {"observacao": "Falha TLS/certificado. A validação HTTPS não foi desligada."}
        except requests.exceptions.ProxyError:
            result = {"observacao": "Falha na conexão pelo proxy. Detalhes sensíveis não exibidos."}
        except requests.exceptions.Timeout:
            result = {"observacao": "Tempo esgotado. Nenhuma repetição automática foi realizada."}
        except requests.exceptions.RequestException:
            result = {"observacao": "Falha de transporte. Exceção bruta omitida para proteger credenciais."}
        text = report_text(result, source, shadowed)
        print("\n" + text)
        report = PROJECT / "ayla_v2" / "data" / "pesquisa_motivo_provedor.txt"
        try:
            report.parent.mkdir(parents=True, exist_ok=True)
            report.write_text(text, encoding="utf-8")
            print("Relatório: ayla_v2/data/pesquisa_motivo_provedor.txt")
        except OSError:
            print("Não foi possível salvar o relatório; o resultado permanece no terminal.")
        return 0 if result.get("http") == 200 and result.get("fontes", 0) else 1
    except ConfigurationError as exc:
        print("Não iniciado: " + str(exc))
        return 2
    except (EOFError, KeyboardInterrupt):
        print("\nCancelado.")
        return 130
    except Exception:
        # Nunca mostrar traceback que possa conter a credencial ou uma resposta bruta.
        print("Falha inesperada no teste. Nenhum detalhe bruto ou credencial foi exibido.")
        return 2


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    raise SystemExit(main())
