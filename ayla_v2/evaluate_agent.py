"""Live smoke evaluation of the general agent. Results are NOT factual-accuracy scores."""
from datetime import datetime
import json
from pathlib import Path
import tempfile
import time
from .agent import GeneralAgent
from .errors import AppError
from .service import Ayla
from .storage import Store
from .weather import Weather


def main():
    print('AYLA | Avaliação REAL do agente: conversa, cálculo e web opcional.\n')
    print('Usa um banco temporário vazio, não suas listas. A parte web usa sua chave e consome consultas.')
    allow=input('Incluir dois testes de pesquisa pública? [s/N] ').strip().lower()=='s'
    cases=[('Explique a diferença entre processo e thread em poucas palavras.', False, 'conversa'),
           ('Dê um exemplo simples da explicação anterior.',False,'continuidade'),
           ('Quanto é 18% de 2450? Use a calculadora.',False,'calculo'),
           ('Quanto é (14 + 6) * 7?',False,'calculo')]
    if allow:
        cases += [('Pesquise a documentação oficial sobre context managers em Python e cite as fontes.',True,'pesquisa'),
                  ('Pesquise informações recentes sobre energia solar no Brasil. Diferencie o ano dos dados e a publicação.',True,'pesquisa')]
    records=[]
    with tempfile.TemporaryDirectory(prefix='ayla-eval-') as temp:
        store=Store(Path(temp)/'evaluation.sqlite3');store.initialize()
        service=Ayla(store, None, Weather());agent=GeneralAgent(service)
        for text,web,kind in cases:
            print(f'Executando: {kind}');start=time.monotonic()
            try:
                result=agent.process(text,'avaliacao-agente-local-001',web,web)
                records.append({'pergunta':text,'tipo':kind,'resposta':result,'duracao_s':round(time.monotonic()-start,2),
                                'revisao_humana':'PENDENTE: precisão, fontes, relevância e coerência.'})
                print('Resposta recebida; revisão de conteúdo pendente.')
            except AppError as exc:
                records.append({'pergunta':text,'tipo':kind,'erro':exc.message,'duracao_s':round(time.monotonic()-start,2)})
                print('Falha registrada: '+exc.message)
    output=Path(__file__).resolve().parent/'evaluation/results'
    output.mkdir(parents=True,exist_ok=True)
    stamp=datetime.now().strftime('%Y%m%d_%H%M%S')
    report={'modelo_real':True,'web_autorizada':allow,'descricao':'Teste funcional; NÃO é nota de acurácia. Revisão humana obrigatória.','casos':records}
    (output/f'agente_{stamp}.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    lines=['# Avaliação real do agente','\nExecução funcional, não pontuação de qualidade. Conferir as fontes e cada afirmação.\n']
    for r in records:
        lines += ['## '+r['pergunta'],f"\nDuração: {r['duracao_s']} segundos.\n",r.get('resposta',{}).get('mensagem',r.get('erro','')), '\nRevisão humana: pendente.\n']
        for source in r.get('resposta',{}).get('fontes',[]):lines.append(f"Fonte {source['id']}: {source['url']}")
    (output/f'agente_{stamp}.md').write_text('\n'.join(lines),encoding='utf-8')
    print('\nRelatórios: '+str(output))
    return 1 if any('erro' in r for r in records) else 0

if __name__=='__main__':raise SystemExit(main())
