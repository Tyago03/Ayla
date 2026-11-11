"""Validação de estrutura. JSON válido não garante interpretação correta."""
import re
import unicodedata
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, field_validator


def clean(value: str) -> str:
    return re.sub(r"\s+", " ", unicodedata.normalize("NFC", value)).strip()


def key(value: str) -> str:
    """Acentos são preservados; caixa e espaços não criam itens duplicados."""
    return clean(value).casefold()



def normalize_list_name(value: str | None) -> str | None:
    """Nome canônico, idempotente. Não muda acentos nem os nomes dos itens.

    Nesta interface, `lista` / `lista de` no início são marcadores, não
    parte do nome. Uma lista antiga continua intacta; o Store a resolve
    pelo mesmo nome canônico, sem migrar ou mesclar dados.
    """
    if value is None:
        return None
    value = clean(value)
    previous = None
    while value != previous:
        previous = value
        value = value.rstrip(".?! ")
        if len(value) >= 2 and (value[0], value[-1]) in {
            ('"', '"'), ("'", "'"), ('“', '”'), ('‘', '’'),
        }:
            value = value[1:-1].strip()
        value = re.sub(r"^lista(?:\s+de)?(?:\s+|$)", "", value, count=1,
                       flags=re.IGNORECASE).strip()
    return clean(value) or None


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


Item = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=120)]


class Comando(StrictModel):
    intencao: Literal["consultar_clima", "adicionar_item", "consultar_lista", "listar_listas", "criar_lista", "renomear_lista", "remover_item", "concluir_item", "reabrir_item", "buscar_item", "consultar_hora", "consultar_data", "ajuda", "saudacao", "fora_do_escopo"]
    cidade: str | None = Field(max_length=100)
    lista: str | None = Field(max_length=100)
    itens: list[Item] = Field(max_length=20)

    novo_nome: str | None = Field(default=None, max_length=100)
    termo: str | None = Field(default=None, max_length=120)
    usar_lista_anterior: bool = False

    @field_validator("termo")
    @classmethod
    def normalize_term(cls, value: str | None) -> str | None:
        return (clean(value) or None) if value is not None else None

    @field_validator("cidade")
    @classmethod
    def normalize_optional(cls, value: str | None) -> str | None:
        return (clean(value) or None) if value is not None else None

    @field_validator("lista", "novo_nome")
    @classmethod
    def normalize_list(cls, value: str | None) -> str | None:
        return normalize_list_name(value)

    @field_validator("itens")
    @classmethod
    def normalize_items(cls, values: list[str]) -> list[str]:
        result = []
        for value in values:
            value = clean(value)
            if not value:
                raise ValueError("O item não pode estar vazio.")
            result.append(value)
        return result


class Pedido(StrictModel):
    permitir_web: bool = False
    pesquisar_agora: bool = False
    texto: str = Field(min_length=1, max_length=1000)

    @field_validator("texto")
    @classmethod
    def nonblank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Digite um pedido.")
        return value


class EscolhaCidade(StrictModel):
    indice: int = Field(ge=0, le=9)
