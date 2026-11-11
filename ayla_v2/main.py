"""Servidor local. Inicie pela raiz: python -m uvicorn ayla_v2.main:app."""
from contextlib import asynccontextmanager
import logging
import os
from pathlib import Path
import sqlite3
from typing import Callable
from urllib.parse import urlsplit

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.concurrency import run_in_threadpool
from starlette.middleware.trustedhost import TrustedHostMiddleware

from .agent import GeneralAgent
from .branding import find_wordmark
from .conversation import SESSION_PATTERN
from .speech import LocalSpeech, MAX_AUDIO_BYTES
from .errors import AppError
from .llm import LocalInterpreter
from .schemas import Comando, EscolhaCidade, Pedido
from .service import Ayla
from .storage import Store
from .weather import Weather

BASE = Path(__file__).resolve().parent
logger = logging.getLogger("ayla")


def create_app(db_path: Path | None = None,
               interpreter: Callable[[str], Comando] | None = None,
               weather: Weather | None = None,
               speech: LocalSpeech | None = None,
               agent_chat=None, web_tools=None) -> FastAPI:
    path = db_path or Path(os.getenv("AYLA_DB_PATH", str(BASE / "data" / "ayla.sqlite3")))
    store = Store(path)
    parser = interpreter if interpreter is not None else LocalInterpreter()
    service = Ayla(store, parser, weather if weather is not None else Weather())
    agent = GeneralAgent(service, agent_chat, web_tools) if interpreter is None or agent_chat is not None else None
    speech_engine = speech if speech is not None else LocalSpeech()

    @asynccontextmanager
    async def lifespan(application: FastAPI):
        store.initialize()
        yield

    application = FastAPI(title="Ayla • demonstração local", version="0.5.3",
                          lifespan=lifespan, docs_url=None, redoc_url=None)
    application.state.store = store
    application.state.service = service
    application.state.agent = agent
    application.add_middleware(TrustedHostMiddleware, allowed_hosts=["127.0.0.1", "localhost"])

    @application.middleware("http")
    async def local_guards(request: Request, call_next):
        # Proteção adicional para uso no navegador; não substitui autenticação.
        origin = request.headers.get("origin")
        if origin:
            parsed = urlsplit(origin)
            if parsed.scheme != request.url.scheme or parsed.netloc != request.headers.get("host"):
                return JSONResponse({"mensagem": "Origem não permitida nesta instância local."}, status_code=403)
        session = request.headers.get("x-ayla-session")
        if session and not SESSION_PATTERN.fullmatch(session):
            return JSONResponse({"mensagem": "Sessão inválida. Atualize a página."}, status_code=400)
        is_audio = request.url.path == "/api/voz/transcrever"
        if is_audio and request.method == "POST":
            media_type = request.headers.get("content-type", "").split(";")[0].lower()
            if media_type not in {"audio/webm", "audio/ogg", "audio/wav", "audio/mp4", "video/webm"}:
                return JSONResponse({"mensagem": "Formato de áudio não aceito."}, status_code=415)
            if request.headers.get("content-encoding"):
                return JSONResponse({"mensagem": "Envie áudio sem compressão HTTP adicional."}, status_code=415)
            try:
                if int(request.headers.get("content-length", "0")) > MAX_AUDIO_BYTES:
                    return JSONResponse({"mensagem": "Áudio acima de 5 MB."}, status_code=413)
            except ValueError:
                return JSONResponse({"mensagem": "Tamanho inválido."}, status_code=400)
        if request.method in {"POST", "PUT", "PATCH"} and not is_audio:
            content_type = request.headers.get("content-type", "").split(";")[0].strip().lower()
            # Confirmação/cancelamento não exigem corpo. Texto simples não é aceito.
            if content_type and content_type != "application/json":
                return JSONResponse({"mensagem": "Use application/json."}, status_code=415)
            body = await request.body()
            if len(body) > 8192:
                return JSONResponse({"mensagem": "Pedido grande demais."}, status_code=413)
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; script-src 'self'; style-src 'self'; "
            "connect-src 'self'; img-src 'self' data:; frame-ancestors 'none'; base-uri 'none'; form-action 'self'"
        )
        response.headers["Cache-Control"] = "no-store"
        response.headers["Permissions-Policy"] = "microphone=(self), camera=(), geolocation=()"
        return response

    @application.exception_handler(AppError)
    async def app_error(request: Request, exc: AppError):
        from .web_errors import WebRequestError
        details = exc.public_details() if isinstance(exc, WebRequestError) else {}
        return JSONResponse({"estado": "erro", "mensagem": exc.message, **details}, status_code=exc.status_code)

    @application.exception_handler(RequestValidationError)
    async def validation_error(request: Request, exc: RequestValidationError):
        return JSONResponse({"estado": "erro", "mensagem": "Pedido inválido. Envie texto de 1 a 1.000 caracteres, sem campos extras."}, status_code=422)

    @application.exception_handler(sqlite3.Error)
    async def database_error(request: Request, exc: sqlite3.Error):
        # Não registra conteúdo de listas nem texto do usuário.
        logger.error("Falha SQLite: %s", type(exc).__name__)
        return JSONResponse({"estado": "erro", "mensagem": "Não consegui acessar o banco local. Confira a pasta data e tente novamente."}, status_code=503)

    @application.get("/")
    def home():
        return FileResponse(BASE / "static" / "index.html")

    @application.get("/brand/wordmark", include_in_schema=False)
    def brand():
        return FileResponse(find_wordmark(BASE))

    @application.get("/api/versao")
    def version():
        return {"versao": "0.5.3"}

    @application.get("/api/status")
    def status():
        if hasattr(parser, "status"):
            return parser.status()
        return {"ollama": False, "instalado": False, "modelo": "substituto-de-teste", "digest": None}

    @application.get("/api/pesquisa/status")
    def web_status():
        from .web_tools import WebTools
        return (agent.web if agent else WebTools()).status()

    @application.post("/api/pesquisa/testar")
    def test_web_connection():
        from .check_web import check_connection
        from .web_tools import WebTools
        return check_connection(agent.web if agent else WebTools())

    @application.get("/api/listas")
    def lists():
        return {"listas": store.all_lists()}

    @application.get("/api/listas/{list_id}")
    def list_by_id(list_id: int, request: Request):
        data = store.get_list_by_id(list_id)
        if data is None:
            raise AppError("Não encontrei esse registro de lista. Atualize o painel.", 404)
        service.remember_list(data, request.headers.get("x-ayla-session"))
        return {"lista": data}

    @application.post("/api/comandos")
    def command(body: Pedido, request: Request):
        session_id = request.headers.get("x-ayla-session")
        if agent is not None:
            return agent.process(body.texto, session_id, body.permitir_web, body.pesquisar_agora)
        return service.process(body.texto, session_id)

    @application.post("/api/confirmar/{token}")
    def confirm(token: str, request: Request):
        return service.confirm(token, request.headers.get("x-ayla-session"))

    @application.post("/api/cancelar/{token}")
    def cancel(token: str):
        store.cancel(token)
        return {"estado": "respondido", "mensagem": "Solicitação cancelada. Essa proposta não foi aplicada."}

    @application.post("/api/clima/{token}")
    def choose_weather(token: str, body: EscolhaCidade):
        return service.choose_weather(token, body.indice)

    @application.post("/api/conversa/nova")
    def new_conversation(request: Request):
        service.reset(request.headers.get("x-ayla-session"))
        return {"estado": "respondido", "mensagem": "Contexto desta conversa limpo. Listas preservadas."}

    @application.get("/api/voz/status")
    def speech_status():
        return speech_engine.status()

    @application.post("/api/voz/transcrever")
    async def transcribe(request: Request):
        raw = bytearray()
        async for chunk in request.stream():
            if len(raw) + len(chunk) > MAX_AUDIO_BYTES:
                raise AppError("Áudio acima de 5 MB.", 413)
            raw.extend(chunk)
        text = await run_in_threadpool(speech_engine.transcribe, bytes(raw))
        return {"texto": text, "modo": "local", "enviado": False}

    application.mount("/static", StaticFiles(directory=BASE / "static"), name="static")
    return application


app = create_app()
