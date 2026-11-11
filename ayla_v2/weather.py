"""Consulta de clima atual ao Open-Meteo (internet necessária; sem chave)."""
import math
from typing import Any

import requests

from .errors import AppError


def get_json(url: str, params: dict[str, Any]) -> dict[str, Any]:
    try:
        response = requests.get(url, params=params, timeout=(5, 15))
        response.raise_for_status()
        result = response.json()
        if not isinstance(result, dict) or result.get("error"):
            raise ValueError("Resposta inválida")
        return result
    except (requests.RequestException, ValueError) as exc:
        raise AppError("O serviço de clima não respondeu corretamente. As listas continuam disponíveis.", 502) from exc


class Weather:
    def search(self, city: str) -> list[dict[str, Any]]:
        payload = get_json("https://geocoding-api.open-meteo.com/v1/search",
                           {"name": city, "count": 5, "language": "pt", "format": "json"})
        results = []
        try:
            for row in payload.get("results", []):
                lat, lon = float(row["latitude"]), float(row["longitude"])
                if not math.isfinite(lat) or not math.isfinite(lon) or not -90 <= lat <= 90 or not -180 <= lon <= 180:
                    continue
                label = " · ".join(str(row[k]) for k in ("name", "admin1", "country") if row.get(k))
                results.append({"label": label, "latitude": lat, "longitude": lon})
        except (KeyError, TypeError, ValueError) as exc:
            raise AppError("Recebi dados de localização inválidos. Tente novamente.", 502) from exc
        return results

    def current(self, location: dict[str, Any]) -> dict[str, Any]:
        payload = get_json("https://api.open-meteo.com/v1/forecast", {
            "latitude": location["latitude"], "longitude": location["longitude"],
            "current": "temperature_2m,apparent_temperature,weather_code",
            "timezone": "auto", "forecast_days": 1,
        })
        try:
            current = payload["current"]
            temperature = float(current["temperature_2m"])
            apparent = float(current["apparent_temperature"])
            if not math.isfinite(temperature) or not math.isfinite(apparent):
                raise ValueError("Temperatura não finita")
            timestamp = str(current["time"])
            zone = str(payload.get("timezone", "fuso não informado"))
            return {"local": location["label"], "temperatura_c": temperature,
                    "sensacao_c": apparent, "horario": timestamp, "fuso": zone,
                    "fonte": "Open-Meteo", "url_fonte": "https://open-meteo.com/"}
        except (KeyError, TypeError, ValueError) as exc:
            raise AppError("O serviço retornou dados incompletos. Não vou inventar a temperatura.", 502) from exc
