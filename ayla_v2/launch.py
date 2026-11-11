"""Inicia a instância local e abre o navegador quando o servidor estiver pronto."""
import json
import os
import socket
import threading
import time
import urllib.request
import webbrowser


def main() -> None:
    import uvicorn
    host = "127.0.0.1"
    port = int(os.getenv("AYLA_PORT", "8000"))
    if not 1024 <= port <= 65535:
        raise SystemExit("AYLA_PORT deve ser um número entre 1024 e 65535.")
    with socket.socket() as sock:
        try:
            sock.bind((host, port))
        except OSError:
            raise SystemExit(f"A porta {port} já está em uso. Encerre a instância antiga e tente novamente.")
    url=f"http://{host}:{port}"
    done=threading.Event()
    def open_browser() -> None:
        # Só abre depois de a aplicação correta estar pronta. Sem tráfego externo.
        for _ in range(60):
            if done.is_set(): return
            try:
                with urllib.request.urlopen(url+"/api/versao", timeout=1) as response:
                    if json.load(response).get("versao") == "0.5.0":
                        webbrowser.open(url)
                        return
            except (OSError, ValueError):
                pass
            time.sleep(.25)
    threading.Thread(target=open_browser, daemon=True).start()
    print(f"Ayla local: {url}\nPara encerrar, pressione Ctrl+C. Não feche o Ollama.")
    try:
        uvicorn.run("ayla_v2.main:app", host=host, port=port, log_level="info")
    finally:
        done.set()


if __name__ == "__main__":
    main()
