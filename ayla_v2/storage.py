"""Persistência SQLite, nomes canônicos e confirmação de uso único.

Compatibilidade com bancos 0.1: nenhum DROP, migração ou fusão automática.
"""
from contextlib import contextmanager
import json
import hashlib
from pathlib import Path
import secrets
import sqlite3
import time
from typing import Any, Iterator

from .errors import AppError
from .schemas import Comando, key, normalize_list_name


class Store:
    def __init__(self, path: Path):
        self.path = Path(path)

    @contextmanager
    def connection(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(self.path, timeout=10)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def initialize(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.connection() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS lists (
                    id INTEGER PRIMARY KEY, name TEXT NOT NULL, name_key TEXT NOT NULL UNIQUE
                );
                CREATE TABLE IF NOT EXISTS items (
                    id INTEGER PRIMARY KEY,
                    list_id INTEGER NOT NULL REFERENCES lists(id),
                    text TEXT NOT NULL, item_key TEXT NOT NULL,
                    UNIQUE(list_id, item_key)
                );
                CREATE TABLE IF NOT EXISTS pending (
                    token TEXT PRIMARY KEY, kind TEXT NOT NULL,
                    payload TEXT NOT NULL, expires REAL NOT NULL
                );
            """)
            columns = {row["name"] for row in conn.execute("PRAGMA table_info(items)")}
            if "completed" not in columns:
                conn.execute("ALTER TABLE items ADD COLUMN completed INTEGER NOT NULL DEFAULT 0")

    @staticmethod
    def _resolve(conn: sqlite3.Connection, name: str) -> sqlite3.Row | None:
        """Mesmo critério na escrita e na leitura, inclusive nomes antigos.

        Se duas listas antigas convergem para o mesmo nome, não escolhe uma
        silenciosamente. O painel permite leitura inequívoca pelo ID.
        """
        normalized = normalize_list_name(name)
        if not normalized:
            return None
        target = key(normalized)
        matches = []
        for row in conn.execute("SELECT id, name, name_key FROM lists ORDER BY id"):
            candidate = normalize_list_name(row["name"])
            if candidate and key(candidate) == target:
                matches.append(row)
        if len(matches) > 1:
            raise AppError(
                "Há mais de uma lista antiga com esse nome equivalente. "
                "Abra a lista desejada no painel Minhas listas. "
                "Nenhum dado foi alterado ou mesclado.", 409,
            )
        return matches[0] if matches else None

    @staticmethod
    def _serialize(conn: sqlite3.Connection, row: sqlite3.Row) -> dict[str, Any]:
        records = [dict(r) for r in conn.execute(
            "SELECT id, text, completed FROM items WHERE list_id = ? ORDER BY id", (row["id"],))]
        return {"id": row["id"], "nome": row["name"],
                "nome_exibicao": normalize_list_name(row["name"]) or row["name"],
                "itens": [r["text"] for r in records],
                "detalhes_itens": [{"id": r["id"], "texto": r["text"], "concluido": bool(r["completed"])} for r in records],
                "quantidade_pendentes": sum(not r["completed"] for r in records)}

    def create_pending(self, kind: str, payload: dict[str, Any], ttl: int = 600) -> str:
        token = secrets.token_urlsafe(32)
        with self.connection() as conn:
            conn.execute("DELETE FROM pending WHERE expires <= ?", (time.time(),))
            conn.execute("INSERT INTO pending VALUES (?, ?, ?, ?)",
                         (token, kind, json.dumps(payload, ensure_ascii=False), time.time() + ttl))
        return token

    def _pending(self, conn: sqlite3.Connection, token: str, kind: str) -> dict[str, Any]:
        row = conn.execute("SELECT * FROM pending WHERE token = ? AND kind = ?", (token, kind)).fetchone()
        if row is None or row["expires"] <= time.time():
            raise AppError("Esta solicitação expirou, foi cancelada ou já foi usada. Faça um novo pedido.", 409)
        return json.loads(row["payload"])

    def confirm_add(self, token: str) -> dict[str, Any]:
        with self.connection() as conn:
            conn.execute("BEGIN IMMEDIATE")
            command = Comando.model_validate(self._pending(conn, token, "add"))
            name = normalize_list_name(command.lista)
            if command.intencao != "adicionar_item" or not name or not command.itens:
                raise AppError("Operação pendente inválida. Nenhuma lista foi alterada.", 400)
            row = self._resolve(conn, name)
            if row is None:
                conn.execute("INSERT INTO lists(name, name_key) VALUES (?, ?)", (name, key(name)))
                row = conn.execute("SELECT id, name FROM lists WHERE name_key = ?", (key(name),)).fetchone()
            if row is None:
                raise AppError("Não consegui acessar a lista. Nenhum item foi salvo.", 500)
            added = []
            for item in command.itens:
                cursor = conn.execute(
                    "INSERT OR IGNORE INTO items(list_id, text, item_key) VALUES (?, ?, ?)",
                    (row["id"], item, key(item)),
                )
                if cursor.rowcount:
                    added.append(item)
            conn.execute("DELETE FROM pending WHERE token = ?", (token,))
            return {**self._serialize(conn, row), "adicionados": added}

    def consume_location(self, token: str, index: int) -> dict[str, Any]:
        with self.connection() as conn:
            conn.execute("BEGIN IMMEDIATE")
            payload = self._pending(conn, token, "weather")
            locations = payload["locations"]
            if index < 0 or index >= len(locations):
                raise AppError("Escolha uma das cidades apresentadas.", 400)
            conn.execute("DELETE FROM pending WHERE token = ?", (token,))
            return locations[index]

    def cancel(self, token: str) -> None:
        with self.connection() as conn:
            cursor = conn.execute("DELETE FROM pending WHERE token = ?", (token,))
            if not cursor.rowcount:
                raise AppError("Esta solicitação não está mais pendente. Nenhuma alteração nova foi feita.", 409)

    def get_list(self, name: str) -> dict[str, Any] | None:
        with self.connection() as conn:
            row = self._resolve(conn, name)
            return self._serialize(conn, row) if row else None

    def get_list_by_id(self, list_id: int) -> dict[str, Any] | None:
        with self.connection() as conn:
            row = conn.execute("SELECT id, name FROM lists WHERE id = ?", (list_id,)).fetchone()
            return self._serialize(conn, row) if row else None

    def list_catalog(self) -> list[dict[str, Any]]:
        """Resumo somente leitura; contagem calculada no banco, nunca pelo LLM.

        Uma linha de item equivale a uma entrada salva, não a uma quantidade física
        extraída do texto. Listas antigas equivalentes continuam separadas por ID.
        """
        with self.connection() as conn:
            rows = conn.execute("""
                SELECT l.id, l.name, COUNT(i.id) AS item_count
                FROM lists AS l LEFT JOIN items AS i ON i.list_id = l.id
                GROUP BY l.id, l.name ORDER BY l.id
            """).fetchall()
            return [{"id": row["id"], "nome": row["name"],
                     "nome_exibicao": normalize_list_name(row["name"]) or row["name"],
                     "quantidade_itens": row["item_count"]} for row in rows]

    def all_lists(self) -> list[dict[str, Any]]:
        with self.connection() as conn:
            rows = conn.execute("SELECT id, name FROM lists ORDER BY id").fetchall()
            return [self._serialize(conn, row) for row in rows]

    @staticmethod
    def _fingerprint(conn: sqlite3.Connection, row: sqlite3.Row) -> str:
        # Uma proposta só vale para o estado que a pessoa revisou.
        items = [tuple(r) for r in conn.execute(
            "SELECT id, text, completed FROM items WHERE list_id=? ORDER BY id", (row["id"],))]
        raw = json.dumps([row["id"], row["name"], items], ensure_ascii=False)
        return hashlib.sha256(raw.encode()).hexdigest()

    def prepare_change(self, command: Comando) -> tuple[dict[str, Any], dict[str, Any]]:
        """Só lê. Devolve payload confiável e proposta visível; não grava itens."""
        if command.intencao not in {"criar_lista", "renomear_lista", "remover_item", "concluir_item", "reabrir_item"}:
            raise AppError("Operação não permitida.", 400)
        with self.connection() as conn:
            row = self._resolve(conn, command.lista)
            if command.intencao == "criar_lista":
                if row:
                    raise AppError("Essa lista já existe. Consulte-a ou escolha outro nome.", 409)
                return {"command": command.model_dump(), "id": None}, {"nome": command.lista, "itens": [], "operacao": "criar_lista"}
            if not row:
                raise AppError("Não encontrei essa lista. Confira o nome no painel.", 404)
            snapshot = self._serialize(conn, row)
            payload = {"command": command.model_dump(), "id": row["id"], "fingerprint": self._fingerprint(conn, row)}
            proposed = {"nome": snapshot["nome_exibicao"], "itens": [], "operacao": command.intencao}
            if command.intencao == "renomear_lista":
                existing = self._resolve(conn, command.novo_nome)
                if existing:
                    raise AppError("O novo nome já está em uso. Escolha um nome diferente; nenhuma lista foi mesclada.", 409)
                proposed["novo_nome"] = command.novo_nome
            else:
                records = list(conn.execute("SELECT id, text, completed FROM items WHERE list_id=? ORDER BY id", (row["id"],)))
                wanted = {key(item) for item in command.itens}
                matched = [r for r in records if key(r["text"]) in wanted]
                missing = wanted - {key(r["text"]) for r in matched}
                if missing:
                    raise AppError("Não encontrei todos os itens com esses nomes exatos. Consulte a lista e use os nomes salvos; nada foi alterado.", 404)
                if not matched:
                    raise AppError("Escolha ao menos um item salvo.", 400)
                payload["item_ids"] = [r["id"] for r in matched]
                proposed["itens"] = [r["text"] for r in matched]
            return payload, proposed

    def confirm_change(self, token: str) -> dict[str, Any]:
        with self.connection() as conn:
            conn.execute("BEGIN IMMEDIATE")
            payload = self._pending(conn, token, "change")
            cmd = Comando.model_validate(payload["command"])
            if cmd.intencao == "criar_lista":
                if not cmd.lista or cmd.itens or self._resolve(conn, cmd.lista):
                    raise AppError("A lista já existe ou a proposta está inválida. Faça um novo pedido.", 409)
                cursor = conn.execute("INSERT INTO lists(name,name_key) VALUES (?,?)", (cmd.lista, key(cmd.lista)))
                row = conn.execute("SELECT id,name FROM lists WHERE id=?", (cursor.lastrowid,)).fetchone()
            else:
                row = conn.execute("SELECT id,name FROM lists WHERE id=?", (payload["id"],)).fetchone()
                if not row or self._fingerprint(conn, row) != payload["fingerprint"]:
                    raise AppError("Essa lista mudou depois da proposta. Nada foi alterado; envie o pedido novamente e revise os dados atuais.", 409)
                if cmd.intencao == "renomear_lista":
                    if not cmd.novo_nome or self._resolve(conn, cmd.novo_nome):
                        raise AppError("O novo nome não está disponível. Faça um novo pedido.", 409)
                    conn.execute("UPDATE lists SET name=?, name_key=? WHERE id=?", (cmd.novo_nome, key(cmd.novo_nome), row["id"]))
                    row = conn.execute("SELECT id,name FROM lists WHERE id=?", (row["id"],)).fetchone()
                elif cmd.intencao in {"remover_item", "concluir_item", "reabrir_item"}:
                    if not payload.get("item_ids"):
                        raise AppError("Proposta inválida.", 400)
                    for item_id in payload["item_ids"]:
                        if cmd.intencao == "remover_item":
                            conn.execute("DELETE FROM items WHERE id=? AND list_id=?", (item_id, row["id"]))
                        else:
                            conn.execute("UPDATE items SET completed=? WHERE id=? AND list_id=?", (int(cmd.intencao == "concluir_item"), item_id, row["id"]))
                else:
                    raise AppError("Operação não permitida.", 400)
            conn.execute("DELETE FROM pending WHERE token=?", (token,))
            return {**self._serialize(conn, row), "operacao": cmd.intencao}

    def pending_kind(self, token: str) -> str:
        with self.connection() as conn:
            row = conn.execute("SELECT kind FROM pending WHERE token=? AND expires>?", (token, time.time())).fetchone()
            if row is None:
                raise AppError("Esta solicitação expirou, foi cancelada ou já foi usada. Faça um novo pedido.", 409)
            return row["kind"]

    def search_items(self, term: str) -> list[dict[str, Any]]:
        # Busca literal (não SQL/regex fornecido pelo modelo), sem distinguir acentos/caixa.
        import unicodedata
        def fold(text: str) -> str:
            return "".join(c for c in unicodedata.normalize("NFD", key(text)) if not unicodedata.combining(c))
        wanted = fold(term)
        with self.connection() as conn:
            rows = conn.execute("SELECT i.text,i.completed,l.id,l.name FROM items i JOIN lists l ON l.id=i.list_id ORDER BY l.id,i.id")
            return [{"lista_id": r["id"], "lista": normalize_list_name(r["name"]) or r["name"],
                     "item": r["text"], "concluido": bool(r["completed"])} for r in rows if wanted in fold(r["text"])]
