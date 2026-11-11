"""Avaliação REAL do modelo instalado. Não altera listas nem consulta clima.

Na raiz do repositório:
  python -m ayla_v2.evaluate --split dev
  python -m ayla_v2.evaluate --split holdout
"""
import argparse
from datetime import datetime, timezone
import hashlib
import html
import json
import math
from pathlib import Path
import platform
import statistics
import subprocess
import time
import unicodedata

from .errors import AppError
from .llm import LocalInterpreter, OPTIONS, PROMPT
from .schemas import Comando

BASE = Path(__file__).resolve().parent


def normalize(value):
    if isinstance(value, str):
        value = unicodedata.normalize("NFKD", value.casefold())
        value = "".join(c for c in value if not unicodedata.combining(c))
        return " ".join(value.split()).strip(" .?!")
    return value


def canonical(data):
    return {"intencao": data["intencao"], "cidade": normalize(data["cidade"]),
            "lista": normalize(data["lista"]), "itens": sorted(normalize(x) for x in data["itens"]),
            "novo_nome": normalize(data.get("novo_nome")), "termo": normalize(data.get("termo")),
            "usar_lista_anterior": data.get("usar_lista_anterior", False)}


def run(split: str):
    model = LocalInterpreter()
    status = model.status()
    if not status["ollama"] or not status["instalado"]:
        raise SystemExit("Abra o Ollama e instale o modelo indicado por AYLA_MODEL (padrão: qwen3:4b-instruct).")
    source = BASE / "evaluation" / "cases.jsonl"
    cases = [json.loads(line) for line in source.read_text(encoding="utf-8").splitlines() if line.strip()]
    cases = [case for case in cases if case["split"] == split]
    rows = []
    for index, case in enumerate(cases, 1):
        start = time.perf_counter()
        row = {**case, "resultado": None, "erro": None, "intencao_correta": False, "estrutura_completa_correta": False}
        try:
            result = model(case["texto"]).model_dump()
            row["resultado"] = result
            row["intencao_correta"] = result["intencao"] == case["esperado"]["intencao"]
            row["estrutura_completa_correta"] = canonical(result) == canonical(case["esperado"])
        except AppError as error:
            row["erro"] = error.message
        row["latencia_ms"] = round((time.perf_counter() - start) * 1000)
        rows.append(row)
        print(f"[{index}/{len(cases)}] {case['id']}: {'OK' if row['estrutura_completa_correta'] else 'REVISAR'}", flush=True)
    latencies = sorted(row["latencia_ms"] for row in rows)
    try:
        commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=BASE.parent,
                                capture_output=True, text=True, timeout=5).stdout.strip() or None
    except (OSError, subprocess.TimeoutExpired):
        commit = None
    settings = PROMPT + json.dumps(Comando.model_json_schema(), sort_keys=True) + json.dumps(OPTIONS, sort_keys=True)
    result = {
        "tipo": "execucao_local_real", "escopo": "classificação e extração; não avalia execução de ações",
        "observacao": "Amostra pequena e construída manualmente; não é estimativa de desempenho em produção. "
                      "Latências incluem carga fria quando aplicável. Não use holdout para ajustar o prompt e continuar chamando-o de teste independente.",
        "data_utc": datetime.now(timezone.utc).isoformat(), "modelo": model.model,
        "digest_modelo": status["digest"], "python": platform.python_version(), "sistema": platform.platform(),
        "commit": commit, "config_sha256": hashlib.sha256(settings.encode()).hexdigest(),
        "dataset_sha256": hashlib.sha256(source.read_bytes()).hexdigest(), "split": split,
        "total": len(rows), "intencoes_corretas": sum(r["intencao_correta"] for r in rows),
        "estruturas_completas_corretas": sum(r["estrutura_completa_correta"] for r in rows),
        "latencia_mediana_ms": statistics.median(latencies),
        "latencia_p95_ms": latencies[math.ceil(0.95 * len(latencies)) - 1], "casos": rows,
    }
    folder = BASE / "evaluation" / "results"
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / (datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S") + f"_{split}.json")
    path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    report_path = path.with_suffix(".html")
    safe = html.escape
    table_rows = []
    for row in rows:
        expected = json.dumps(row["esperado"], ensure_ascii=False, indent=2)
        actual = json.dumps(row["resultado"], ensure_ascii=False, indent=2) if row["resultado"] else row["erro"] or "Sem resposta"
        table_rows.append("<tr><td>" + safe(row["id"]) + "</td><td>" + safe(row["texto"]) +
                          "</td><td>" + ("OK" if row["estrutura_completa_correta"] else "Revisar") +
                          "</td><td><pre>" + safe(expected) + "</pre></td><td><pre>" + safe(actual) +
                          "</pre></td><td>" + str(row["latencia_ms"]) + " ms</td></tr>")
    heading = f"{result['estruturas_completas_corretas']}/{len(rows)} estruturas completas corretas"
    doc = "<!doctype html><html lang='pt-BR'><meta charset='utf-8'><meta name='viewport' content='width=device-width, initial-scale=1'>"
    doc += "<title>Ayla — avaliação local</title><style>body{font:15px system-ui;background:#0e1315;color:#e4edef;padding:32px}h1{color:#71d7ca}table{border-collapse:collapse;width:100%}td,th{border:1px solid #34464b;padding:12px;text-align:left;vertical-align:top}pre{white-space:pre-wrap;font-size:12px}p{max-width:1000px;color:#becdd0}.scroll{overflow:auto}</style>"
    doc += "<h1>Ayla · Avaliação do modelo</h1><h2>" + safe(heading) + "</h2><p>" + safe(result["observacao"]) + "</p>"
    doc += "<p>Modelo: " + safe(model.model) + " · conjunto: " + split + " · data: " + safe(result["data_utc"]) + "</p>"
    doc += "<p>Este teste mede interpretação de pedidos isolados. Não mede microfone, timbre de voz, contexto ou resultado de negócio.</p><div class='scroll'><table><thead><tr><th>ID</th><th>Pedido</th><th>Resultado</th><th>Esperado</th><th>Recebido</th><th>Latência</th></tr></thead><tbody>" + "".join(table_rows) + "</tbody></table></div></html>"
    report_path.write_text(doc, encoding="utf-8")
    print(f"Relatório visual: {report_path}")
    print(f"\nIntenção: {result['intencoes_corretas']}/{len(rows)}; estrutura completa: {result['estruturas_completas_corretas']}/{len(rows)}")
    print(f"Relatório: {path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--split", choices=["dev", "holdout"], default="dev")
    run(parser.parse_args().split)
