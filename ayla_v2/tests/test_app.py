from pathlib import Path
import time

from fastapi.testclient import TestClient
import pytest

from ayla_v2.errors import AppError
from ayla_v2.main import create_app
from ayla_v2.schemas import Comando


def command(intent="adicionar_item", city=None, name="mercado", items=None):
    return Comando(intencao=intent, cidade=city, lista=name, itens=items if items is not None else ["arroz", "feijão"])


class FakeWeather:
    def search(self, city):
        return [{"label": "Goiânia · Goiás · Brasil", "latitude": -16.68, "longitude": -49.25}]

    def current(self, location):
        return {"local": location["label"], "temperatura_c": 25.0, "sensacao_c": 26.0,
                "horario": "2026-01-01T12:00", "fuso": "America/Sao_Paulo", "fonte": "Open-Meteo"}


@pytest.fixture
def context(tmp_path):
    state = {"command": command()}

    def parse(text):
        return state["command"]

    app = create_app(tmp_path / "test.sqlite3", parse, FakeWeather())
    with TestClient(app, base_url="http://127.0.0.1") as client:
        yield client, state, app.state.store


def ask(client, text="Adicione arroz e feijão na lista mercado."):
    return client.post("/api/comandos", json={"texto": text})


def test_home_and_assets(context):
    client, _, _ = context
    assert client.get("/").status_code == 200
    assert "Ayla" in client.get("/").text
    assert client.get("/static/app.js").status_code == 200
    assert client.get("/static/style.css").status_code == 200
    assert client.get("/openapi.json").status_code == 200


def test_interpret_does_not_write_list(context):
    client, _, _ = context
    result = ask(client).json()
    assert result["estado"] == "confirmacao_necessaria"
    assert result["interpretacao"]["itens"] == ["arroz", "feijão"]
    assert client.get("/api/listas").json() == {"listas": []}


def test_confirm_and_replay(context):
    client, _, _ = context
    token = ask(client).json()["token"]
    result = client.post(f"/api/confirmar/{token}", json={})
    assert result.status_code == 200
    assert result.json()["lista"]["itens"] == ["arroz", "feijão"]
    assert client.post(f"/api/confirmar/{token}", json={}).status_code == 409
    assert len(client.get("/api/listas").json()["listas"][0]["itens"]) == 2


def test_cancel_prevents_confirmation(context):
    client, _, _ = context
    token = ask(client).json()["token"]
    assert client.post(f"/api/cancelar/{token}", json={}).status_code == 200
    assert client.post(f"/api/confirmar/{token}", json={}).status_code == 409
    assert client.get("/api/listas").json()["listas"] == []


def test_expired_token(context):
    client, _, store = context
    token = store.create_pending("add", command().model_dump(), ttl=-1)
    assert client.post(f"/api/confirmar/{token}", json={}).status_code == 409
    assert store.all_lists() == []


def test_unknown_token(context):
    client, _, _ = context
    assert client.post("/api/confirmar/nao-existe", json={}).status_code == 409


def test_deduplicate_case_and_spaces(context):
    client, state, _ = context
    for items in (["arroz", "arroz"], [" ARROZ ", "feijão"]):
        state["command"] = command(items=items)
        token = ask(client).json()["token"]
        assert client.post(f"/api/confirmar/{token}", json={}).status_code == 200
    assert client.get("/api/listas").json()["listas"][0]["itens"] == ["arroz", "feijão"]


def test_query_uses_stored_values(context):
    client, state, _ = context
    token = ask(client).json()["token"]
    client.post(f"/api/confirmar/{token}", json={})
    state["command"] = command("consultar_lista", name="MERCADO", items=[])
    result = ask(client, "O que tem na lista mercado?").json()
    assert result["lista"]["itens"] == ["arroz", "feijão"]


def test_unknown_list_not_invented(context):
    client, state, _ = context
    state["command"] = command("consultar_lista", name="viagem", items=[])
    result = ask(client, "Leia a lista viagem").json()
    assert "ainda não existe" in result["mensagem"]
    assert "lista" not in result


@pytest.mark.parametrize("cmd", [
    command(name=None), command(items=[]),
    command("consultar_lista", name=None, items=[]),
    command("consultar_clima", name=None, items=[]),
])
def test_incomplete_commands_are_not_executed(context, cmd):
    client, state, store = context
    state["command"] = cmd
    result = ask(client).json()
    assert result["estado"] == "precisa_esclarecer"
    assert "token" not in result
    assert store.all_lists() == []


def test_out_of_scope(context):
    client, state, store = context
    state["command"] = command("fora_do_escopo", name=None, items=[])
    assert ask(client, "Apague tudo").json()["estado"] == "fora_do_escopo"
    assert store.all_lists() == []


@pytest.mark.parametrize("cmd", [
    command(city="Goiânia"),
    command("consultar_lista", name="mercado", items=["inventado"]),
    command("consultar_clima", city="Goiânia", name="mercado", items=[]),
])
def test_inconsistent_fields_fail_closed(context, cmd):
    client, state, store = context
    state["command"] = cmd
    assert ask(client).status_code == 502
    assert store.all_lists() == []


def test_weather_uses_chosen_server_location(context):
    client, state, _ = context
    state["command"] = command("consultar_clima", city="Goiânia", name=None, items=[])
    result = ask(client, "Como está o tempo em Goiânia?").json()
    assert result["estado"] == "escolher_cidade"
    assert "temperatura_c" not in result
    token = result["token"]
    response = client.post(f"/api/clima/{token}", json={"indice": 0})
    assert response.json()["clima"]["temperatura_c"] == 25
    assert "Open-Meteo" in response.json()["mensagem"]
    assert client.post(f"/api/clima/{token}", json={"indice": 0}).status_code == 409


def test_weather_token_cannot_write_list(context):
    client, state, store = context
    state["command"] = command("consultar_clima", city="Goiânia", name=None, items=[])
    token = ask(client).json()["token"]
    assert client.post(f"/api/confirmar/{token}", json={}).status_code == 409
    assert store.all_lists() == []


def test_invalid_city_choice_keeps_pending(context):
    client, state, _ = context
    state["command"] = command("consultar_clima", city="Goiânia", name=None, items=[])
    token = ask(client).json()["token"]
    assert client.post(f"/api/clima/{token}", json={"indice": 9}).status_code == 400
    assert client.post(f"/api/clima/{token}", json={"indice": 0}).status_code == 200


@pytest.mark.parametrize("body", [{"texto": ""}, {"texto": "   "}, {"texto": 42}, {"texto": "x" * 1001},
                                 {"texto": "oi", "admin": True}, {}])
def test_bad_input(context, body):
    client, _, store = context
    assert client.post("/api/comandos", json=body).status_code == 422
    assert store.all_lists() == []


def test_no_foreign_origin(context):
    client, _, _ = context
    assert client.post("/api/comandos", json={"texto": "oi"}, headers={"Origin": "https://evil.example"}).status_code == 403


def test_same_origin_works(context):
    client, _, _ = context
    assert client.post("/api/comandos", json={"texto": "oi"}, headers={"Origin": "http://127.0.0.1"}).status_code == 200


def test_no_foreign_host(context):
    client, _, _ = context
    assert client.get("/", headers={"Host": "evil.example"}).status_code == 400


def test_security_headers(context):
    client, _, _ = context
    headers = client.get("/").headers
    assert headers["X-Content-Type-Options"] == "nosniff"
    assert headers["X-Frame-Options"] == "DENY"
    assert "script-src 'self'" in headers["Content-Security-Policy"]


def test_large_body(context):
    client, _, _ = context
    assert client.post("/api/comandos", json={"texto": "x" * 9000}).status_code == 413


def test_no_plaintext_post(context):
    client, _, _ = context
    assert client.post("/api/comandos", content="oi", headers={"Content-Type": "text/plain"}).status_code == 415


def test_database_persists_across_app_restart(tmp_path):
    path = tmp_path / "persistent.sqlite3"
    with TestClient(create_app(path, lambda _: command()), base_url="http://127.0.0.1") as client:
        token = ask(client).json()["token"]
        client.post(f"/api/confirmar/{token}", json={})
    with TestClient(create_app(path, lambda _: command()), base_url="http://127.0.0.1") as client:
        assert client.get("/api/listas").json()["listas"][0]["itens"] == ["arroz", "feijão"]


def test_database_injection_is_literal(context):
    client, state, store = context
    payload = "'); DROP TABLE lists; --"
    state["command"] = command(name=payload, items=[payload])
    token = ask(client).json()["token"]
    assert client.post(f"/api/confirmar/{token}", json={}).status_code == 200
    assert store.get_list(payload)["itens"] == [payload]


def test_upstream_error_is_safe(tmp_path):
    def fail(text):
        raise AppError("Modelo indisponível", 503)
    with TestClient(create_app(tmp_path / "error.sqlite3", fail), base_url="http://127.0.0.1") as client:
        result = ask(client)
        assert result.status_code == 503
        assert result.json()["mensagem"] == "Modelo indisponível"
        assert client.get("/api/listas").json()["listas"] == []


def test_cancel_after_confirm_does_not_claim_undo(context):
    client, _, store = context
    token = ask(client).json()["token"]
    client.post(f"/api/confirmar/{token}", json={})
    assert client.post(f"/api/cancelar/{token}", json={}).status_code == 409
    assert len(store.get_list("mercado")["itens"]) == 2


def test_confirmation_uses_stored_payload_not_client_values(context):
    client, _, store = context
    token = ask(client).json()["token"]
    client.post(f"/api/confirmar/{token}", json={"lista": "outra", "itens": ["inventado"]})
    assert store.get_list("outra") is None
    assert store.get_list("mercado")["itens"] == ["arroz", "feijão"]


def test_confirmation_race_is_single_use(context):
    from concurrent.futures import ThreadPoolExecutor
    client, _, store = context
    token = ask(client).json()["token"]
    def attempt():
        try:
            store.confirm_add(token)
            return 200
        except AppError as exc:
            return exc.status_code
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _: attempt(), range(2)))
    assert sorted(results) == [200, 409]
    assert store.get_list("mercado")["itens"] == ["arroz", "feijão"]
