"""Interactive local secret setup. Never echo the key or put it in the repository."""
import argparse
from getpass import getpass
import json
import os
from pathlib import Path
import sys
import webbrowser
from .web_tools import secret_path, WebTools
from .errors import AppError
from .check_web import run_diagnostic


def save_key(value: str, path: Path | None = None) -> Path:
    value=value.strip()
    if not 12 <= len(value) <= 512 or not value.isascii() or any(c.isspace() or ord(c) < 33 or ord(c) == 127 for c in value):
        raise ValueError('Formato inesperado. Cole a chave inteira, sem espaços. Não será exibida.')
    path = path or secret_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp=path.with_suffix('.tmp')
    # POSIX permissions; on Windows the file inherits the user's LocalAppData ACL.
    fd=os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd,'w',encoding='utf-8') as out:
        json.dump({'ollama_api_key':value},out)
    tmp.replace(path)
    try: path.chmod(0o600)
    except OSError: pass
    return path


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--remove',action='store_true')
    args=parser.parse_args()
    if args.remove:
        secret_path().unlink(missing_ok=True)
        print('Configuração local removida. Revogue a chave no provedor para invalidá-la.'); return 0
    if not sys.stdin.isatty():
        print('Abra o atalho num terminal interativo. Não passe chaves na linha de comando.');return 1
    print('AYLA | Configurar pesquisa geral na web\n')
    print('O modelo continua local. Consultas e URLs são enviadas ao Ollama Web Search.')
    print('Crie uma chave na sua conta. A chave ficará fora do projeto e não irá para o Git.')
    print('A pasta protege contra commit acidental, não contra malware ou outros processos do seu usuário.\n')
    if input('Abrir a página oficial de chaves? [S/n] ').strip().lower() not in {'n','nao','não'}:
        webbrowser.open('https://ollama.com/settings/keys')
    try:
        value=getpass('Cole a chave (não será exibida; Enter cancela): ').strip()
        if not value: print('Cancelado.');return 0
        path=save_key(value)
        print('Configuração salva fora do repositório: '+str(path))
        if os.getenv('OLLAMA_API_KEY'):
            print('ATENÇÃO: a variável OLLAMA_API_KEY definida no sistema tem precedência sobre este arquivo.')
        if input('Testar com uma busca pública por documentação do Ollama? [s/N] ').strip().lower()=='s':
            result = run_diagnostic()
            if not result['ok']:
                print('A chave foi salva; o teste de acesso falhou. Não é preciso digitá-la novamente sem analisar o código acima.')
                return 1
        print('Na Ayla, ative Permitir pesquisa web. Não precisa reiniciar para reler a chave.')
        return 0
    except (ValueError,AppError,OSError) as exc:
        print('Não concluído: '+(exc.message if isinstance(exc,AppError) else ('Falha ao salvar configuração.' if isinstance(exc,OSError) else str(exc))))
        return 1

if __name__=='__main__':
    raise SystemExit(main())
