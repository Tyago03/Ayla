"""Contexto mínimo em memória, por aba. Expira; não é histórico nem autorização."""
from dataclasses import dataclass, field
import re
import threading
import time
from typing import Any
from .schemas import Comando, clean

SESSION_PATTERN = re.compile(r"^[a-zA-Z0-9_-]{16,64}$")

@dataclass
class Context:
    touched: float = field(default_factory=time.monotonic)
    last_list: str | None = None
    last_public_query: str | None = None  # Already sent to the public search provider.
    awaiting: Comando | None = None
    slot: str | None = None
    history: list[dict[str, str]] = field(default_factory=list)
    tokens: list[str] = field(default_factory=list)
    lock: Any = field(default_factory=threading.RLock)

    def public(self) -> dict:
        return {"ultima_lista": self.last_list,
                "pedido_incompleto": self.awaiting.model_dump() if self.awaiting else None,
                "campo_aguardado": self.slot}

class Conversations:
    def __init__(self, ttl: int = 1200, capacity: int = 128):
        self.ttl, self.capacity = ttl, capacity
        self._items: dict[str, Context] = {}
        self._lock = threading.RLock()

    def get(self, session: str | None) -> Context:
        if not session:
            return Context()  # Clientes antigos continuam sem memória entre chamadas.
        with self._lock:
            now = time.monotonic()
            for key, ctx in list(self._items.items()):
                if now - ctx.touched > self.ttl:
                    del self._items[key]
            if session not in self._items:
                if len(self._items) >= self.capacity:
                    oldest = min(self._items, key=lambda k: self._items[k].touched)
                    del self._items[oldest]
                self._items[session] = Context()
            ctx = self._items[session]
            ctx.touched = now
            return ctx

    def clear(self, session: str | None) -> Context | None:
        with self._lock:
            return self._items.pop(session, None) if session else None


def short_slot_reply(text: str, ctx: Context) -> Comando | None:
    """Completa só campos que a aplicação acabou de pedir, sem inventar ações.

    Texto de ação vai ao interpretador; sim/não não é autorização para gravação.
    Itens compostos ficam a cargo do interpretador para evitar separação incorreta.
    """
    if not ctx.awaiting or ctx.slot not in {"cidade", "lista", "novo_nome"}:
        return None
    value = clean(text).rstrip(".?!")
    if not value or len(value) > 100 or len(value.split()) > 12:
        return None
    if re.search(r"\b(adicione?|inclua|coloque|remova|tire|exclua|apague|crie|renomeie|marque|conclua|reabra|mostre|consulte|ignore|instruç|comando|horas|clima|tempo|quais|qual|onde|como|cancelar|cancele|sim|não|nao|ok|confirmo|obrigado|obrigada|oi|olá|ola|tchau|ajuda)\b", value, re.I):
        return None
    # Sintaxe conservadora: nomes, não URLs, código ou comandos múltiplos.
    if any(c in value for c in "\n\r{}[]<>;=/\\"):
        return None
    data = ctx.awaiting.model_dump()
    data[ctx.slot] = value
    return Comando.model_validate(data)
