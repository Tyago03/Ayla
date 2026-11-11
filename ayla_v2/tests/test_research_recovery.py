"""Regression for an assistant refusal without a single search. All I/O simulated."""
from unittest.mock import Mock
import json
import requests
import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError
from ayla_v2.agent import GeneralAgent
from ayla_v2.research import ResearchPlan, ResearchPlanner
from ayla_v2.check_web import check_connection
from ayla_v2.main import create_app
from ayla_v2.errors import AppError
from ayla_v2.schemas import Comando
from ayla_v2.service import Ayla
from ayla_v2.storage import Store
from ayla_v2.tests.test_agent import Scripted, FakeWeb, reply, tool, SID


class PlanningChat(Scripted):
    def __init__(self, *responses, plan=None):
        super().__init__(*responses)
        self.plan = plan or ResearchPlan(decision='local')
        self.plans = []

    def plan_research(self, text, previous, required, remaining):
        self.plans.append({'text':text, 'previous':previous, 'required':required})
        if isinstance(self.plan, Exception):
            raise self.plan
        return self.plan


@pytest.fixture
def service(tmp_path):
    store = Store(tmp_path/'test.db'); store.initialize()
    return Ayla(store, lambda t: Comando(intencao='fora_do_escopo', cidade=None, lista=None, itens=[]), None)


def test_unsearched_refusal_is_discarded_and_query_is_executed(service):
    chat = PlanningChat(reply('Não foi possível verificar com as fontes disponíveis.'),
                        reply('Encontrei uma referência para consultar [1].'),
                        plan=ResearchPlan(decision='search', query='população município São Paulo estimativa ano'))
    web=FakeWeb(); res=GeneralAgent(service, chat, web).process('Qual a população atual de São Paulo?',SID,True)
    assert len(web.queries)==1
    assert res['pesquisa']['tentada'] and res['pesquisa']['fontes']==1
    assert res['pesquisa']['decisao']=='pesquisa_automatica_verificada'
    assert res['fontes'][0]['url']=='https://www.python.org/doc/'  # stub, not demographic evidence
    assert 'Não foi possível verificar' not in res['mensagem']
    assert not any('Não foi possível verificar' in m.get('content','') for m in chat.calls[1][0])


@pytest.mark.parametrize('question,query', [
    ('Qual a versão atual do Rust?', 'Rust release versão estável atual'),
    ('Dados recentes sobre energia solar?', 'energia solar estatísticas recentes'),
    ('Quais estudos embasam essa conclusão?', 'estudos revisão fontes evidência'),
    ('Pesquise a história dos protocolos de rede.', 'história protocolos rede fontes primárias'),
])
def test_recovery_is_not_a_city_or_population_rule(service,question,query):
    web=FakeWeb(); chat=PlanningChat(reply('Não sei.'),reply('Fonte [1].'),
                                     plan=ResearchPlan(decision='search',query=query))
    GeneralAgent(service,chat,web).process(question,SID,True)
    assert web.queries==[query]


def test_local_concept_does_not_search(service):
    web=FakeWeb(); chat=PlanningChat(reply('Uma variável armazena um valor.'))
    res=GeneralAgent(service,chat,web).process('Explique variável.',SID,True)
    assert not web.queries and len(chat.plans)==1
    assert res['pesquisa']['decisao']=='resposta_local_planejada'


def test_no_consent_means_no_planner_no_network(service):
    web=FakeWeb(); chat=PlanningChat(reply('Sem consulta externa.'))
    res=GeneralAgent(service,chat,web).process('Um dado atual?',SID,False)
    assert not chat.plans and not web.queries
    assert 'Web desativada' in res['origem']


def test_force_without_consent_never_runs_planner(service):
    web=FakeWeb(); chat=PlanningChat()
    res=GeneralAgent(service,chat,web).process('Pesquise',SID,False,True)
    assert not chat.calls and not chat.plans and not web.queries
    assert not res['pesquisa']['autorizada']


def test_explicit_search_runs_even_when_native_model_never_calls_tools(service):
    web=FakeWeb(); chat=PlanningChat(reply('A resposta usa a fonte [1].'),
                                     plan=ResearchPlan(decision='search',query='pergunta pública'))
    res=GeneralAgent(service,chat,web).process('Pergunta pública?',SID,True,True)
    assert web.queries==['pergunta pública'] and len(chat.calls)==1
    assert any(m['role']=='tool' for m in chat.calls[0][0])
    assert res['tentou_pesquisar']


def test_explicit_fallback_uses_only_current_authorized_question(service):
    ctx=service.contexts.get(SID)
    ctx.history=[{'role':'user','content':'DADO PRIVADO NÃO ENVIAR'}]
    web=FakeWeb(); chat=PlanningChat(reply('Fonte [1].'), plan=AppError('Sem plano.',502))
    res=GeneralAgent(service,chat,web).process('Documentação pública?',SID,True,True)
    assert web.queries==['Documentação pública?']
    assert all('DADO PRIVADO' not in q for q in web.queries)
    assert res['pesquisa']['decisao']=='pesquisa_explicita_pergunta_atual'


def test_automatic_plan_error_does_not_guess_a_query(service):
    web=FakeWeb(); chat=PlanningChat(reply('Não verificado.'),plan=AppError('Plano indisponível.',502))
    res=GeneralAgent(service,chat,web).process('Uma pergunta?',SID,True)
    assert not web.queries and 'Plano indisponível.' in res['avisos']
    assert res['pesquisa']['decisao']=='decisao_indisponivel'


def test_automatic_missing_key_is_explicit(service):
    web=FakeWeb();web.status=lambda:{'configurada':False}
    chat=PlanningChat(reply('Não sei.'),plan=ResearchPlan(decision='search',query='tema público'))
    res=GeneralAgent(service,chat,web).process('Pergunta pública?',SID,True)
    assert not web.queries and 'CONFIGURAR_PESQUISA' in res['mensagem']
    assert res['pesquisa']['decisao']=='chave_ausente'


def test_ambiguity_is_clarified_not_silently_assumed(service):
    web=FakeWeb();chat=PlanningChat(reply('Palpite'),plan=ResearchPlan(decision='clarify',question='De qual entidade você está falando?'))
    res=GeneralAgent(service,chat,web).process('Qual é o número atual?',SID,True)
    assert not web.queries and res['mensagem']=='De qual entidade você está falando?'


def test_forced_private_request_can_be_stopped_by_plan(service):
    web=FakeWeb();chat=PlanningChat(plan=ResearchPlan(decision='clarify',question='Envie uma pergunta pública independente das suas listas.'))
    res=GeneralAgent(service,chat,web).process('Minhas listas privadas',SID,True,True)
    assert not web.queries and not chat.calls and 'pública' in res['mensagem']


def test_research_plan_receives_only_previous_public_query(service):
    ctx=service.contexts.get(SID);ctx.last_list='privada';ctx.history=[{'role':'assistant','content':'DADOS PRIVADOS'}]
    ctx.last_public_query='tecnologia fontes públicas 2026'
    web=FakeWeb();chat=PlanningChat(reply('Não sei.'),reply('Fonte [1].'),plan=ResearchPlan(decision='search',query='tecnologia fontes públicas 2025'))
    GeneralAgent(service,chat,web).process('E no ano anterior?',SID,True)
    assert chat.plans[0]['previous']=='tecnologia fontes públicas 2026'
    assert 'DADOS PRIVADOS' not in json.dumps(chat.plans)
    assert ctx.last_public_query=='tecnologia fontes públicas 2025'
    service.reset(SID);assert service.contexts.get(SID).last_public_query is None


def test_search_attempt_error_cannot_be_confused_with_disabled_web(service):
    web=FakeWeb()
    def fail(*args):raise AppError('O provedor recusou a chave de pesquisa.',503)
    web.search=fail
    chat=PlanningChat(reply('Resposta sem suporte.'),plan=ResearchPlan(decision='search',query='dado público'))
    res=GeneralAgent(service,chat,web).process('Pesquise dado público.',SID,True,True)
    assert res['pesquisa']['tentada'] and not res['pesquisou']
    assert 'recusou a chave' in res['mensagem'] and 'Pesquisa sem fontes' in res['origem']
    assert 'Resposta sem suporte' not in res['mensagem']


def test_calculator_does_not_trigger_research_gate(service):
    web=FakeWeb();chat=PlanningChat(tool('calcular',expressao='1+2'),reply('Três.'))
    res=GeneralAgent(service,chat,web).process('1+2?',SID,True)
    assert not chat.plans and not web.queries and res['calculos']


def test_recovered_web_still_cannot_write_personal_data(service):
    c=Comando(intencao='criar_lista',lista='intrusão',cidade=None,itens=[])
    web=FakeWeb();chat=PlanningChat(reply('Não sei.'), tool('tarefas_pessoais',**c.model_dump()),reply('Fonte [1].'),
                       plan=ResearchPlan(decision='search',query='tema público'))
    res=GeneralAgent(service,chat,web).process('Uma pergunta factual?',SID,True)
    assert not service.store.all_lists() and 'token' not in res
    assert any('separados' in e for e in res['avisos'])


def test_provider_diagnostic_never_calls_qwen(tmp_path):
    web=FakeWeb(); chat=Scripted()
    app=create_app(tmp_path/'d.db',agent_chat=chat,web_tools=web)
    with TestClient(app,base_url='http://127.0.0.1') as client:
        res=client.post('/api/pesquisa/testar',json={})
    assert res.status_code==200 and res.json()['ok']
    assert web.queries==['Ollama documentação oficial pesquisa web'] and not chat.calls


def test_status_check_does_not_consume_queries():
    web=FakeWeb();web.status();assert not web.queries


def test_diagnostic_empty_response_is_not_marked_success():
    web=FakeWeb();web.search=lambda *a,**kw:[]
    with pytest.raises(AppError,match='fontes utilizáveis'):check_connection(web)


def test_diagnostic_missing_key_no_network():
    web=FakeWeb();web.status=lambda:{'configurada':False}
    with pytest.raises(AppError):check_connection(web)
    assert not web.queries


@pytest.mark.parametrize('plan',[
    {'decision':'search','query':None},
    {'decision':'search','query':'  '},
    {'decision':'local','query':'send anyway'},
    {'decision':'clarify','question':None},
    {'decision':'execute','query':'x'},
    {'decision':'search','query':'ok','extra':'no'},
])
def test_plan_validation_is_strict(plan):
    with pytest.raises(ValidationError):ResearchPlan.model_validate(plan)


def transport_for(monkeypatch,data):
    session=Mock();session.__enter__=Mock(return_value=session);session.__exit__=Mock(return_value=False)
    response=session.post.return_value;response.raise_for_status.return_value=None
    response.json.return_value=data
    monkeypatch.setattr('ayla_v2.research.requests.Session',lambda:session)
    return session


def test_structured_local_planner_contract(monkeypatch):
    session=transport_for(monkeypatch,{'message':{'content':'{"decision":"search","query":"tema público","question":null}'},'done_reason':'stop'})
    plan=ResearchPlanner()('Pergunta?',None,True,remaining=12)
    payload=session.post.call_args.kwargs['json']
    assert plan.query=='tema público' and payload['format']['type']=='object'
    assert 'tools' not in payload and payload['options']['temperature']==0
    assert session.post.call_args.args[0]=='http://127.0.0.1:11434/api/chat'
    assert session.trust_env is False
    assert 'Authorization' not in session.post.call_args.kwargs.get('headers',{})


@pytest.mark.parametrize('data',[
    {'message':{'content':'not json'}},
    {'message':{'content':'{"decision":"local","query":null,"question":null}'},'done_reason':'length'},
    {'other':'no message'},
])
def test_structured_planner_bad_response_fails_closed(monkeypatch,data):
    transport_for(monkeypatch,data)
    with pytest.raises(AppError):ResearchPlanner()('Pergunta?')


def test_structured_planner_timeout_is_sanitized(monkeypatch):
    session=transport_for(monkeypatch,{})
    session.post.side_effect=requests.Timeout('secret must not leak')
    with pytest.raises(AppError) as exc:ResearchPlanner()('Pergunta?')
    assert 'secret' not in exc.value.message


def test_forced_local_decision_does_not_override_user_search_request(service):
    web=FakeWeb();chat=PlanningChat(reply('Fonte [1].'),plan=ResearchPlan(decision='local'))
    res=GeneralAgent(service,chat,web).process('Pergunta pública completa?',SID,True,True)
    assert web.queries==['Pergunta pública completa?']
    assert res['tentou_pesquisar'] and res['fontes']
