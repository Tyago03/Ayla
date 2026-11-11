import json
from typing import Literal

import requests
from pydantic import BaseModel, ConfigDict, Field

MODELO = "qwen3:4b-instruct"
URL = "http://127.0.0.1:11434/api/chat"


class Comando(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    intencao: Literal[
        "consultar_clima", "adicionar_item",
        "consultar_lista", "fora_do_escopo"
    ]
    cidade: str | None = Field(max_length=100)
    lista: str | None = Field(max_length=100)
    itens: list[str] = Field(max_length=20)


INSTRUCOES = """
Interprete um único comando para a Ayla. Não execute nenhuma ação.
Use consultar_clima para clima ou temperatura; adicionar_item para
adicionar itens a uma lista; consultar_lista para ler uma lista.
Para pedidos fora dessas funções ou com múltiplas ações,
use fora_do_escopo, cidade=null, lista=null e itens=[].
Extraia somente informações explícitas. Não invente cidade,
nome de lista ou itens. Preserve acentos.
Em pedidos incompletos, mantenha a intenção identificável,
mas preencha os campos ausentes com null e os itens ausentes com [].
Nunca responda a temperatura nem afirme que algo foi adicionado.
Retorne somente JSON conforme este esquema:
"""


def interpretar(texto: str) -> Comando:
    texto = texto.strip()
    if not 1 <= len(texto) <= 1000:
        raise ValueError("Digite entre 1 e 1.000 caracteres.")

    esquema = Comando.model_json_schema()
    resposta = requests.post(
        URL,
        json={
            "model": MODELO,
            "messages": [
                {"role": "system",
                 "content": INSTRUCOES + json.dumps(esquema, ensure_ascii=False)},
                {"role": "user", "content": texto},
            ],
            "format": esquema,
            "stream": False,
            "options": {
                "temperature": 0,
                "num_ctx": 4096,
                "num_predict": 256,
            },
        },
        timeout=(5, 120),
    )
    resposta.raise_for_status()
    conteudo = resposta.json()["message"]["content"]
    return Comando.model_validate_json(conteudo)


if __name__ == "__main__":
    try:
        comando = interpretar(input("Comando para a Ayla: "))
        print(comando.model_dump_json(indent=2))
    except requests.Timeout:
        raise SystemExit("Tempo de espera excedido. Verifique o Ollama.")
    except requests.ConnectionError:
        raise SystemExit("Não consegui conectar. Abra o aplicativo Ollama.")
    except requests.RequestException as erro:
        raise SystemExit(f"Erro HTTP: {erro}. Confira o modelo com ollama list.")
    except (ValueError, KeyError, TypeError) as erro:
        raise SystemExit(f"Entrada ou resposta inválida: {erro}")