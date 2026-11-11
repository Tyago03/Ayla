"""Regressões do catálogo. O interpretador é simulado; não mede acurácia do Qwen."""
import json
from pathlib import Path

from fastapi.testclient import TestClient
import pytest
import requests

from ayla_v2.llm import LocalInterpreter
from ayla_v2.main import create_app
from ayla_v2.schemas import Comando, key
from ayla_v2.storage import Store


def listing(**override):
    return Comando.model_validate({"intencao":"listar_listas", "cidade":None,
                                  "lista":None,"itens":[], **override})


class NoWeather:
    def search(self, city):
        raise AssertionError("A consulta das listas não deve chamar o clima")
    def current(self, place):
        raise AssertionError("A consulta das listas não deve chamar o clima")


@pytest.fixture
def env(tmp_path):
    state = {"command": listing()}
    app = create_app(tmp_path / "catalog.sqlite3", lambda _: state["command"], NoWeather())
    with TestClient(app, base_url="http://127.0.0.1") as client:
        yield client, state, app.state.store


def ask(client, text="Quais listas eu tenho?"):
    return client.post("/api/comandos",json={"texto":text})


def seed(store, name, items):
    with store.connection() as conn:
        cursor = conn.execute("INSERT INTO lists(name,name_key) VALUES (?,?)", (name,key(name)))
        id = cursor.lastrowid
        conn.executemany("INSERT INTO items(list_id,text,item_key) VALUES (?,?,?)",
                         [(id,item,key(item)) for item in items])
    return id


def snapshot(store):
    with store.connection() as conn:
        return {table: [tuple(row) for row in conn.execute(f"SELECT * FROM {table}")]
                for table in ("lists","items","pending")}


def test_empty_catalog_is_honest(env):
    client,_,store = env
    response = ask(client)
    assert response.status_code == 200
    data=response.json()
    assert data["total_listas"] == 0
    assert data["catalogo"] == []
    assert "ainda não tem listas" in data["mensagem"]
    assert "token" not in data
    assert store.all_lists() == []


def test_names_counts_and_ids_come_from_db(env):
    client,_,store=env
    first=seed(store,"mercado",["2 pães","café"])
    second=seed(store,"viagem",["passaporte"])
    data=ask(client).json()
    assert data["total_listas"] == 2
    assert "2 listas" in data["mensagem"]
    assert data["catalogo"] == [
        {"id":first,"nome":"mercado","nome_exibicao":"mercado","quantidade_itens":2},
        {"id":second,"nome":"viagem","nome_exibicao":"viagem","quantidade_itens":1}]
    assert "2 pães" not in json.dumps(data) # Only counts/metadata are included, not item contents.


def test_single_list_and_zero_items(env):
    client,_,store=env
    seed(store,"viagem",[])
    data=ask(client).json()
    assert "1 lista salva" in data["mensagem"]
    assert data["catalogo"][0]["quantidade_itens"] == 0


def test_listing_does_not_write_or_consume_pending(env):
    client,_,store=env
    seed(store,"mercado",["arroz"])
    token=store.create_pending("add", dict(intencao="adicionar_item",cidade=None,lista="viagem",itens=["meias"]))
    before=snapshot(store)
    for _ in range(3):
        assert ask(client).status_code == 200
    assert snapshot(store) == before
    assert client.post(f"/api/confirmar/{token}",json={}).status_code == 200
    assert ask(client).json()["total_listas"] == 2


def test_pending_only_does_not_appear_as_saved(env):
    client,_,store=env
    store.create_pending("add", dict(intencao="adicionar_item",cidade=None,lista="mercado",itens=["arroz"]))
    assert ask(client).json()["catalogo"] == []


@pytest.mark.parametrize("fields", [
    {"cidade":"Goiânia"}, {"lista":"inventada"}, {"itens":["arroz"]},
    {"cidade":"Recife","lista":"mercado","itens":["feijão"]},
])
def test_mixed_fields_rejected_without_change(env, fields):
    client,state,store=env
    seed(store,"mercado",["arroz"])
    state["command"]=listing(**fields)
    before=snapshot(store)
    assert ask(client).status_code == 502
    assert snapshot(store) == before


def test_legacy_duplicate_display_names_preserve_ids(env):
    client,_,store=env
    ids=[seed(store,"lista café da manhã",["pão"]),seed(store,"café da manhã",["café"])]
    data=ask(client).json()
    assert data["total_listas"] == 2
    assert [r["id"] for r in data["catalogo"]] == ids
    assert [r["nome_exibicao"] for r in data["catalogo"]] == ["café da manhã"]*2
    for id,item in zip(ids,["pão","café"]):
        response=client.get(f"/api/listas/{id}")
        assert response.status_code == 200
        assert response.json()["lista"]["itens"] == [item]


def test_untrusted_name_is_stored_data_not_code(env):
    client,_,store=env
    name='<img src=x onerror=alert(1)>'
    seed(store,name,["ignorar instruções"])
    data=ask(client).json()
    assert data["catalogo"][0]["nome"] == name
    assert data["total_listas"] == 1


def test_catalog_survives_restart(tmp_path):
    db=tmp_path/"persist.sqlite3"
    with TestClient(create_app(db,lambda _: listing(),NoWeather()),base_url="http://127.0.0.1") as client:
        seed(client.app.state.store,"mercado",["arroz"])
        first=ask(client).json()["catalogo"]
    with TestClient(create_app(db,lambda _: listing(),NoWeather()),base_url="http://127.0.0.1") as client:
        assert ask(client).json()["catalogo"] == first


def test_catalog_count_is_per_saved_entry_without_item_text(tmp_path):
    store=Store(tmp_path/"query.sqlite3"); store.initialize()
    seed(store,"mercado",["arroz"])
    # Direct query produces count, not a model-supplied integer or item list.
    assert store.list_catalog()[0]["quantidade_itens"] == 1
    assert "itens" not in store.list_catalog()[0]


def test_single_named_list_semantics_preserved(env):
    client,state,store=env
    seed(store,"todas",["arroz"])
    state["command"]=Comando(intencao="consultar_lista",cidade=None,lista="todas",itens=[])
    data=ask(client,'Leia a lista chamada "todas".').json()
    assert data["lista"]["itens"] == ["arroz"]
    assert "catalogo" not in data


def test_missing_single_list_not_silently_changed_to_catalog(env):
    client,state,_=env
    state["command"]=Comando(intencao="consultar_lista",cidade=None,lista=None,itens=[])
    data=ask(client,"Mostre a lista").json()
    assert data["estado"] == "precisa_esclarecer"
    assert "catalogo" not in data


def test_structured_contract_allows_catalog(monkeypatch):
    class Response:
        status_code=200
        def raise_for_status(self): pass
        def json(self):
            return {"message":{"content":listing().model_dump_json()},"done_reason":"stop"}
    def post(url,**kwargs):
        body=kwargs["json"]
        assert "listar_listas" in body["format"]["properties"]["intencao"]["enum"]
        assert "listar_listas" in body["messages"][0]["content"]
        assert body["messages"][-1]["content"] == "Quais listas eu tenho?"
        # No database content or invented catalog is passed to the model.
        assert "catalogo" not in body
        return Response()
    monkeypatch.setattr(requests,"post",post)
    assert LocalInterpreter()("Quais listas eu tenho?").intencao == "listar_listas"
