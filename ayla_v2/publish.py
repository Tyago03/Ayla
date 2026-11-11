"""Clean public-project export. Does NOT create a Git repository, push or change visibility.

Strict allowlist excludes legacy app, .git/history, secrets, databases, recordings,
model weights, local reports and backups. Review the exported tree before publishing.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import re
import shutil
import tempfile

BASE=Path(__file__).resolve().parent
PATTERNS=[
    re.compile(r'\bgh[pousr]_[A-Za-z0-9]{30,}\b'),
    re.compile(r'\bsk-[A-Za-z0-9_-]{24,}\b'),
    re.compile(r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----'),
    re.compile(r'''(?i)(?:APIclima|OLLAMA_API_KEY|api_key|access_token)["']?\s*[:=]\s*["'][A-Za-z0-9._-]{28,}["']'''),
]


def inspect_public(root: Path) -> list[str]:
    """Heuristic, not proof that arbitrary content is free of sensitive information."""
    problems=[]
    for p in root.rglob('*'):
        if '.git' in p.relative_to(root).parts: continue
        if p.is_symlink(): problems.append(str(p.relative_to(root))+': link simbólico');continue
        if not p.is_file(): continue
        rel=str(p.relative_to(root))
        if p.name.startswith('.env') or p.name in {'web-secret.json','google-services.json'} or p.suffix in {'.db','.sqlite3','.wav','.webm','.pem'}:
            problems.append(rel+': arquivo local/sensível');continue
        if p.suffix in {'.py','.md','.json','.yml','.yaml','.js','.html','.txt','.bat'}:
            text=p.read_text(encoding='utf-8',errors='replace')
            if any(pattern.search(text) for pattern in PATTERNS):
                problems.append(rel+': possível credencial; valor omitido')
    return problems


def export_public(destination: Path, base: Path=BASE) -> dict:
    base=base.resolve();destination=destination.resolve()
    project=base.parent
    if destination.exists(): raise ValueError('A pasta de destino já existe. Escolha uma nova para não sobrescrever trabalho.')
    if destination==project or destination.is_relative_to(project):
        raise ValueError('Escolha uma pasta fora do projeto antigo, para não herdar seu histórico.')
    manifest=json.loads((base/'public_manifest.json').read_text(encoding='utf-8'))
    destination.parent.mkdir(parents=True,exist_ok=True)
    staging=Path(tempfile.mkdtemp(prefix='.ayla-export-',dir=destination.parent))
    try:
        copied=[]
        for name in manifest['files']:
            rel=Path(name)
            if rel.is_absolute() or '..' in rel.parts:
                raise ValueError('Manifesto inválido.')
            src=base/rel
            if not src.is_file() or src.is_symlink() or not src.resolve().is_relative_to(base):
                raise ValueError('Arquivo ausente ou link não permitido: '+name)
            target=staging/'ayla_v2'/rel;target.parent.mkdir(parents=True,exist_ok=True)
            shutil.copy2(src,target);copied.append('ayla_v2/'+name)
        # User's brand only, not the legacy application. Preserve provenance in docs.
        for name in ('aylabrancoc.png','logomarcabranco.png'):
            src=base/'static/assets'/name
            if src.is_file() and not src.is_symlink() and src.resolve().is_relative_to(base):
                (staging/'ayla_v2/static/assets').mkdir(parents=True,exist_ok=True)
                shutil.copy2(src,staging/'ayla_v2/static/assets'/name)
        for name in manifest['shortcuts']:
            if Path(name).name != name or not name.endswith('_AYLA.bat'):
                raise ValueError('Atalho inválido no manifesto.')
            src=project/name
            if src.is_file() and not src.is_symlink(): shutil.copy2(src,staging/name)
        for name in manifest['files']:
            rel=Path(name)
            if rel.parts[0] != 'public_template':
                continue
            src=base/rel
            target=staging/rel.relative_to('public_template')
            target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,target)
        problems=inspect_public(staging)
        if problems: raise ValueError('Exportação bloqueada pela verificação preventiva: '+'; '.join(problems))
        staging.rename(destination)
        return {'destino':str(destination),'arquivos':len(copied),
                'git':'Não inicializado; nenhum push foi feito.',
                'nota':'Revise nomes, dados e direitos de autoria. Varredura heurística não substitui auditoria.'}
    except Exception:
        shutil.rmtree(staging,ignore_errors=True);raise


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dest',type=Path)
    parser.add_argument('--check',type=Path)
    args=parser.parse_args()
    if args.check:
        results=inspect_public(args.check.resolve())
        print('\n'.join(results) if results else 'Nenhum indício nas regras preventivas; ainda revise antes de publicar.')
        return 1 if results else 0
    print('AYLA | Preparar projeto limpo para GitHub (NÃO publica)\n')
    print('Não copia histórico Git, Python/dart antigos, bancos, segredos, backups ou modelos.')
    default=BASE.parent.parent/'Ayla-Publica'
    dest=args.dest
    if dest is None:
        raw=input(f'Pasta NOVA fora do projeto antigo [Enter: {default}]: ').strip().strip('"')
        dest=Path(raw) if raw else default
    try:
        result=export_public(dest)
        print(json.dumps(result,ensure_ascii=False,indent=2))
        print('Leia PUBLICAR_NO_GITHUB.md nessa nova pasta antes de criar o repositório.')
        return 0
    except (OSError,ValueError) as exc:
        print('Não exportado: '+str(exc));return 1

if __name__=='__main__':raise SystemExit(main())
