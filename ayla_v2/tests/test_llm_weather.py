import json

import pytest
import requests
from pydantic import ValidationError

from ayla_v2.errors import AppError
from ayla_v2.llm import LocalInterpreter
from ayla_v2.schemas import Comando
from ayla_v2.weather import Weather


class Response:
    def __init__(self, payload, code=200):
        self.payload, self.status_code = payload, code
    def json(self):
        return self.payload
    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError("simulated")


def data(**overrides):
    return {"intencao": "adicionar_item", "cidade": None, "lista": "café da manhã", "itens": ["café", "pão"], **overrides}


def test_structured_call_configuration(monkeypatch):
    def fake_post(url, **kwargs):
        body = kwargs["json"]
        assert url == "http://127.0.0.1:11434/api/chat"
        assert body["stream"] is False
        assert body["format"]["additionalProperties"] is False
        assert body["options"]["num_ctx"] == 4096
        assert body["messages"][-1]["content"] == "Pedido de teste"
        return Response({"message": {"content": json.dumps(data())}, "done_reason": "stop"})
    monkeypatch.setattr(requests, "post", fake_post)
    result = LocalInterpreter()("Pedido de teste")
    assert result.itens == ["café", "pão"]


@pytest.mark.parametrize("payload", [
    "not json", json.dumps(data(intencao="executar_shell")), json.dumps(data(executar=True)),
    json.dumps(data(itens=[""])), json.dumps(data(itens=["x" * 121])), json.dumps(data(itens=["x"] * 21)),
    json.dumps(data(cidade=12)), json.dumps(data(itens="arroz")),
])
def test_bad_model_output_is_rejected(monkeypatch, payload):
    monkeypatch.setattr(requests, "post", lambda *a, **kw: Response({"message": {"content": payload}}))
    with pytest.raises(AppError) as exc:
        LocalInterpreter()("teste")
    assert exc.value.status_code == 502


@pytest.mark.parametrize("error,status", [(requests.Timeout(), 504), (requests.ConnectionError(), 503)])
def test_network_errors_and_gate_release(monkeypatch, error, status):
    parser = LocalInterpreter()
    def fail(*args, **kwargs):
        raise error
    monkeypatch.setattr(requests, "post", fail)
    for _ in range(2):
        with pytest.raises(AppError) as exc:
            parser("teste")
        assert exc.value.status_code == status


def test_missing_model(monkeypatch):
    monkeypatch.setattr(requests, "post", lambda *a, **kw: Response({}, 404))
    with pytest.raises(AppError) as exc:
        LocalInterpreter()("teste")
    assert exc.value.status_code == 503
    assert "ollama pull" in exc.value.message


def test_truncated_reply(monkeypatch):
    monkeypatch.setattr(requests, "post", lambda *a, **kw: Response({"done_reason": "length"}))
    with pytest.raises(AppError) as exc:
        LocalInterpreter()("teste")
    assert "limite" in exc.value.message


def test_concurrent_request_is_limited():
    parser = LocalInterpreter()
    parser._gate.acquire()
    try:
        with pytest.raises(AppError) as exc:
            parser("teste")
        assert exc.value.status_code == 429
    finally:
        parser._gate.release()


def test_status_has_no_fake_success(monkeypatch):
    monkeypatch.setattr(requests, "get", lambda *a, **kw: Response({"models": []}))
    assert LocalInterpreter().status()["instalado"] is False


def test_city_search(monkeypatch):
    def get(url, **kwargs):
        assert url.startswith("https://geocoding-api.open-meteo.com/")
        assert kwargs["params"]["name"] == "Goiânia"
        return Response({"results": [{"name": "Goiânia", "admin1": "Goiás", "country": "Brasil",
                                       "latitude": -16.68, "longitude": -49.25}]})
    monkeypatch.setattr(requests, "get", get)
    assert Weather().search("Goiânia")[0]["label"] == "Goiânia · Goiás · Brasil"


def test_city_not_found(monkeypatch):
    monkeypatch.setattr(requests, "get", lambda *a, **kw: Response({}))
    assert Weather().search("cidade inexistente") == []


def test_weather_never_invents_missing_temperature(monkeypatch):
    monkeypatch.setattr(requests, "get", lambda *a, **kw: Response({"current": {}}))
    with pytest.raises(AppError):
        Weather().current({"latitude": 0, "longitude": 0, "label": "Teste"})


def test_weather_upstream_failure(monkeypatch):
    def fail(*args, **kwargs):
        raise requests.Timeout()
    monkeypatch.setattr(requests, "get", fail)
    with pytest.raises(AppError) as exc:
        Weather().search("Goiânia")
    assert exc.value.status_code == 502


def test_weather_numeric_data(monkeypatch):
    monkeypatch.setattr(requests, "get", lambda *a, **kw: Response({
        "timezone": "America/Sao_Paulo", "current": {"temperature_2m": 24.3, "apparent_temperature": 25,
        "time": "2026-01-01T12:00"}}))
    result = Weather().current({"latitude": 0, "longitude": 0, "label": "Teste"})
    assert result["temperatura_c"] == 24.3
    assert result["fonte"] == "Open-Meteo"
