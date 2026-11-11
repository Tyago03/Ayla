"""Diagnóstico local, sem ler conteúdo de listas ou registrar credenciais."""
from importlib import metadata
import json
import os
from pathlib import Path
import platform
import sqlite3
from .web_tools import WebTools
from .llm import LocalInterpreter
from .speech import LocalSpeech


def collect() -> dict:
    base = Path(__file__).resolve().parent
    packages = {}
    for name in ('fastapi','pydantic','requests','uvicorn','pytest','httpx','faster-whisper'):
        try: packages[name] = metadata.version(name)
        except metadata.PackageNotFoundError: packages[name] = 'não instalado'
    path = Path(os.getenv('AYLA_DB_PATH',str(base/'data/ayla.sqlite3')))
    db = 'ainda não criado; normal antes da primeira execução'
    if path.exists():
        try:
            with sqlite3.connect(path.resolve().as_uri()+'?mode=ro',uri=True,timeout=3) as conn:
                db = conn.execute('PRAGMA quick_check').fetchone()[0]
        except sqlite3.Error:
            db = 'não foi possível verificar; feche o servidor e tente novamente'
    return {'versao':'0.5.3','python':platform.python_version(), 'sistema':platform.system(),
            'pacotes':packages,'ollama':LocalInterpreter().status(),'ditado_local':LocalSpeech().status(),'pesquisa_web':WebTools().status(),
            'integridade_banco':db,'nota':'Não testa microfone físico, qualidade da voz ou compreensão do Qwen.'}

if __name__ == '__main__':
    report=collect()
    dest=Path(__file__).resolve().parent/'data/diagnostico.json'
    dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False,indent=2))
    print('\nRelatório: '+str(dest))
