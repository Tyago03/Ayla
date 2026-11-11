"""Regressão do bug lista/lista e compatibilidade com bancos antigos."""
from pathlib import Path
import sqlite3

from fastapi.testclient import TestClient
import pytest

from ayla_v2.branding import find_wordmark
from ayla_v2.errors import AppError
from ayla_v2.main import create_app
from ayla_v2.schemas import Comando, key, normalize_list_name
from ayla_v2.storage import Store


@pytest.mark.parametrize("name,expected", [
    (None, None), ("", None), ("   ", None), ("lista", None), ("lista de", None),
    ("lista café da manhã", "café da manhã"), ("Lista de compras", "compras"),
    ("lista lista café da manhã", "café da manhã"),
    ("  lista   café   da manhã?  ", "café da manhã"),
    ('“lista café da manhã”', "café da manhã"),
    ('lista “café da manhã”', "café da manhã"),
    ("playlist", "playlist"), ("lista-negra", "lista-negra"),
    ("tarefas da semana", "tarefas da semana"), ("cafe\u0301 da manhã", "café da manhã"),
])
def test_canonical_name_idempotent(name, expected):
    assert normalize_list_name(name) == expected
    assert normalize_list_name(normalize_list_name(name)) == expected


def command(name, intent="adicionar_item", items=None):
    return Comando(intencao=intent, cidade=None, lista=name,
                   itens=["café", "pão"] if items is None else items)


@pytest.fixture
def store(tmp_path):
    result = Store(tmp_path / "old.sqlite3")
    result.initialize()
    return result


def legacy_list(store, name, item="café"):
    with store.connection() as conn:
        result = conn.execute("INSERT INTO lists(name,name_key) VALUES (?,?)", (name,key(name)))
        list_id = result.lastrowid
        conn.execute("INSERT INTO items(list_id,text,item_key) VALUES (?,?,?)", (list_id,item,key(item)))
    return list_id


def test_city_and_items_are_not_list_normalized():
    cmd = Comando(intencao="adicionar_item", cidade="Lista de cidades", lista="lista de compras",
                  itens=["lista de material", "pão"])
    assert cmd.lista == "compras"
    assert cmd.cidade == "Lista de cidades"
    assert cmd.itens[0] == "lista de material"


@pytest.mark.parametrize("saved,query", [
    ("lista café da manhã", "café da manhã"), ("café da manhã", "lista café da manhã"),
    ("Lista de café da manhã", "CAFÉ DA MANHÃ"), ("lista lista café da manhã", "café da manhã"),
])
def test_legacy_names_resolve_without_modifying_database(store, saved, query):
    original_id = legacy_list(store, saved)
    result = store.get_list(query)
    assert result["id"] == original_id
    assert result["itens"] == ["café"]
    assert result["nome"] == saved
    with store.connection() as conn:
        assert conn.execute("SELECT name FROM lists").fetchone()["name"] == saved


def test_new_items_reuse_legacy_list_without_duplicate(store):
    original_id = legacy_list(store, "lista café da manhã")
    token = store.create_pending("add", command("café da manhã").model_dump())
    result = store.confirm_add(token)
    assert result["id"] == original_id
    assert result["adicionados"] == ["pão"]
    assert result["itens"] == ["café", "pão"]
    assert len(store.all_lists()) == 1


def test_legacy_pending_payload_works(store):
    legacy_list(store, "lista café da manhã")
    payload = {"intencao":"adicionar_item", "cidade":None,
               "lista":"lista café da manhã", "itens":["café", "pão"]}
    token = store.create_pending("add", payload)
    assert store.confirm_add(token)["itens"] == ["café", "pão"]
    assert len(store.all_lists()) == 1


def test_ambiguous_legacy_lists_are_not_merged(store):
    first = legacy_list(store, "lista café da manhã", "café")
    second = legacy_list(store, "café da manhã", "pão")
    with pytest.raises(AppError) as exc:
        store.get_list("café da manhã")
    assert exc.value.status_code == 409
    assert store.get_list_by_id(first)["itens"] == ["café"]
    assert store.get_list_by_id(second)["itens"] == ["pão"]
    token = store.create_pending("add", command("café da manhã", items=["leite"]).model_dump())
    with pytest.raises(AppError):
        store.confirm_add(token)
    assert len(store.all_lists()) == 2
    assert all("leite" not in row["itens"] for row in store.all_lists())


def test_empty_canonical_list_refused(store):
    token = store.create_pending("add", {"intencao":"adicionar_item", "cidade":None,
                                       "lista":"lista de", "itens":["pão"]})
    with pytest.raises(AppError):
        store.confirm_add(token)
    assert store.all_lists() == []


def test_add_then_read_with_different_model_prefix(tmp_path):
    state = {"cmd": command("lista café da manhã")}
    with TestClient(create_app(tmp_path / "flow.db", lambda _: state["cmd"]),
                    base_url="http://127.0.0.1") as client:
        result = client.post("/api/comandos", json={"texto":"Inclua café e pão na lista café da manhã"}).json()
        assert result["proposta"] == {"nome":"café da manhã", "itens":["café", "pão"]}
        client.post("/api/confirmar/" + result["token"], json={})
        state["cmd"] = command("café da manhã", intent="consultar_lista", items=[])
        answer = client.post("/api/comandos", json={"texto":"O que tem na lista café da manhã?"}).json()
        assert answer["lista"]["itens"] == ["café", "pão"]
        assert "não existe" not in answer["mensagem"]
        assert len(client.get("/api/listas").json()["listas"]) == 1


def test_legacy_list_visible_by_name_and_id(tmp_path):
    db = tmp_path / "existing.db"
    store = Store(db); store.initialize()
    list_id = legacy_list(store, "lista café da manhã")
    with TestClient(create_app(db, lambda _: command("café da manhã", "consultar_lista", [])),
                    base_url="http://127.0.0.1") as client:
        result = client.post("/api/comandos", json={"texto":"O que tem na lista café da manhã?"}).json()
        assert result["lista"]["itens"] == ["café"]
        assert client.get(f"/api/listas/{list_id}").json()["lista"]["id"] == list_id
        assert client.get("/api/listas/999").status_code == 404


def test_brand_asset_from_original_repo(tmp_path):
    base = tmp_path / "ayla_v2"; base.mkdir()
    original = tmp_path / "dart" / "assets" / "aylabrancoc.png"
    original.parent.mkdir(parents=True)
    original.write_bytes(b"asset-fixture")
    assert find_wordmark(base) == original


def test_packaged_asset_has_priority(tmp_path):
    base = tmp_path / "ayla_v2"
    packaged = base / "static" / "assets" / "aylabrancoc.png"
    packaged.parent.mkdir(parents=True); packaged.write_bytes(b"asset-fixture")
    assert find_wordmark(base) == packaged


def test_brand_fallback_and_static_resources(tmp_path):
    with TestClient(create_app(tmp_path / "assets.db", lambda _: command("teste")),
                    base_url="http://127.0.0.1") as client:
        for url in ["/brand/wordmark", "/static/icons.svg", "/static/assets/favicon.svg"]:
            assert client.get(url).status_code == 200
        assert "Como posso ajudar" in client.get("/").text
        assert "Como funciona" in client.get("/").text
