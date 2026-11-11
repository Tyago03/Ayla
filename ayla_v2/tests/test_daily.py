from datetime import datetime
import sqlite3
import time
import pytest
from fastapi.testclient import TestClient
from ayla_v2.main import create_app
from ayla_v2.schemas import Comando
from ayla_v2.errors import AppError
from ayla_v2.storage import Store
from ayla_v2.conversation import Conversations

S1={'X-Ayla-Session': 'session_alpha_0123456789'}
S2={'X-Ayla-Session': 'session_beta_0123456789'}

def cmd(intent, name=None, items=None, **kw):
    return Comando(intencao=intent, lista=name, itens=items or [], cidade=kw.pop('cidade',None), **kw)

class Parser:
    value=cmd('ajuda')
    contexts=[]
    def interpret(self,text,context=None):
        self.contexts.append(context)
        return self.value

class Weather:
    def search(self,city): return [{'label':city, 'latitude':0, 'longitude':0}]
    def current(self,p): return {'local':p['label'], 'temperatura_c':25, 'sensacao_c':25, 'horario':'12:00','fuso':'teste'}

@pytest.fixture
def appctx(tmp_path):
    parser=Parser(); parser.contexts=[]
    app=create_app(tmp_path/'test.db',parser,Weather())
    with TestClient(app,base_url='http://127.0.0.1') as c:
        yield c, parser, app.state.store, app.state.service

def ask(ctx,command,text='pedido',session=S1):
    c,p,_,_=ctx;p.value=command
    return c.post('/api/comandos',json={'texto':text},headers=session)

def confirm(ctx,proposal,session=S1):
    return ctx[0].post('/api/confirmar/'+proposal.json()['token'], json={},headers=session)

def seed(ctx,name='mercado',items=None):
    return confirm(ctx,ask(ctx,cmd('adicionar_item',name,items or ['café','pão','leite']))).json()['lista']

def test_empty_list_requires_confirmation(appctx):
    proposal=ask(appctx,cmd('criar_lista','viagem'))
    assert appctx[2].all_lists()==[]
    result=confirm(appctx,proposal)
    assert result.status_code==200 and result.json()['lista']['itens']==[]
    assert appctx[2].list_catalog()[0]['quantidade_itens']==0

def test_duplicate_empty_list_refused(appctx):
    seed(appctx)
    assert ask(appctx,cmd('criar_lista','lista mercado')).status_code==409

def test_create_collision_after_proposal(appctx):
    proposal=ask(appctx,cmd('criar_lista','mercado'))
    seed(appctx)
    assert confirm(appctx,proposal).status_code==409
    assert len(appctx[2].all_lists())==1

def test_remove_requires_confirmation_and_exact_item(appctx):
    seed(appctx)
    proposal=ask(appctx,cmd('remover_item','mercado',['pão']))
    assert appctx[2].get_list('mercado')['itens']==['café','pão','leite']
    result=confirm(appctx,proposal)
    assert result.json()['lista']['itens']==['café','leite']
    assert confirm(appctx,proposal).status_code==409

def test_unknown_item_no_partial_delete(appctx):
    seed(appctx)
    assert ask(appctx,cmd('remover_item','mercado',['pão','banana'])).status_code==404
    assert len(appctx[2].get_list('mercado')['itens'])==3

def test_rename_preserves_id_and_items(appctx):
    old=seed(appctx)
    result=confirm(appctx,ask(appctx,cmd('renomear_lista','mercado',novo_nome='compras'))).json()['lista']
    assert result['id']==old['id'] and result['itens']==old['itens']
    assert appctx[2].get_list('mercado') is None

def test_rename_collision_not_merged(appctx):
    seed(appctx);seed(appctx,'viagem',['passaporte'])
    assert ask(appctx,cmd('renomear_lista','mercado',novo_nome='viagem')).status_code==409
    assert len(appctx[2].all_lists())==2

@pytest.mark.parametrize('intent,kw',[('remover_item',{'items':['pão']}),('concluir_item',{'items':['pão']}),('renomear_lista',{'novo_nome':'compras'})])
def test_stale_change_rejected(appctx,intent,kw):
    seed(appctx)
    proposal=ask(appctx,cmd(intent,'mercado',**kw))
    seed(appctx,items=['arroz'])
    assert confirm(appctx,proposal).status_code==409
    assert 'pão' in appctx[2].get_list('mercado')['itens']

def test_completed_not_deleted_and_reopen(appctx):
    old=seed(appctx)
    data=confirm(appctx,ask(appctx,cmd('concluir_item','mercado',['pão']))).json()['lista']
    assert data['itens']==old['itens'] and data['quantidade_pendentes']==2
    assert next(i for i in data['detalhes_itens'] if i['texto']=='pão')['concluido']
    data=confirm(appctx,ask(appctx,cmd('reabrir_item','mercado',['pão']))).json()['lista']
    assert data['quantidade_pendentes']==3

def test_search_ignores_accents_and_case(appctx):
    seed(appctx);seed(appctx,'trabalho',['Café em pó'])
    result=ask(appctx,cmd('buscar_item',termo='CAFE')).json()
    assert len(result['encontrados'])==2
    assert {r['lista'] for r in result['encontrados']}=={'mercado','trabalho'}

def test_search_wildcards_not_sql(appctx):
    seed(appctx)
    assert ask(appctx,cmd('buscar_item',termo='%')).json()['encontrados']==[]

def test_search_no_results(appctx):
    assert ask(appctx,cmd('buscar_item',termo='café')).json()['encontrados']==[]

@pytest.mark.parametrize('intent',['consultar_data','consultar_hora','ajuda','saudacao'])
def test_non_data_responses(appctx,intent):
    result=ask(appctx,cmd(intent))
    assert result.status_code==200 and result.json()['mensagem']
    assert appctx[2].all_lists()==[]

def test_date_from_computer(appctx):
    result=ask(appctx,cmd('consultar_data')).json()
    assert datetime.now().astimezone().strftime('%d/%m/%Y') in result['mensagem']

@pytest.mark.parametrize('command',[
    cmd('criar_lista','mercado',['inventado']),cmd('renomear_lista','mercado',['inventado'],novo_nome='outro'),
    cmd('buscar_item','mercado',termo='arroz'),cmd('consultar_data',cidade='Goiânia'),
    cmd('consultar_hora',termo='inventado'),cmd('ajuda',novo_nome='inventado'),cmd('listar_listas',usar_lista_anterior=True),
])
def test_new_fields_checked(appctx,command):
    assert ask(appctx,command).status_code==502

@pytest.mark.parametrize('command',[
    cmd('criar_lista'),cmd('renomear_lista','mercado'),cmd('remover_item','mercado'),
    cmd('concluir_item','mercado'),cmd('reabrir_item'),cmd('buscar_item'),
])
def test_incomplete_new_actions_ask(appctx,command):
    result=ask(appctx,command).json()
    assert result['estado']=='precisa_esclarecer' and 'token' not in result

def test_short_city_completion(appctx):
    result=ask(appctx,cmd('consultar_clima'),'Como está o tempo?')
    assert result.json()['estado']=='precisa_esclarecer'
    result=ask(appctx,cmd('fora_do_escopo'),'Goiânia').json()
    assert result['estado']=='escolher_cidade'
    assert result['interpretacao']['cidade']=='Goiânia' and result['contexto_utilizado']

def test_short_list_completion(appctx):
    ask(appctx,cmd('adicionar_item',items=['leite']),'Adicione leite')
    result=ask(appctx,cmd('fora_do_escopo'),'mercado').json()
    assert result['proposta']['nome']=='mercado' and result['proposta']['itens']==['leite']

def test_short_rename_completion(appctx):
    seed(appctx)
    ask(appctx,cmd('renomear_lista','mercado'),'Renomeie a lista mercado')
    result=ask(appctx,cmd('fora_do_escopo'),'compras').json()
    assert result['proposta']['novo_nome']=='compras'

def test_reference_after_confirm(appctx):
    seed(appctx)
    result=ask(appctx,cmd('adicionar_item',items=['arroz'],usar_lista_anterior=True),'Adicione arroz nela').json()
    assert result['proposta']['nome']=='mercado' and result['contexto_utilizado']
    assert 'arroz' not in appctx[2].get_list('mercado')['itens']

def test_reference_no_context_asks(appctx):
    result=ask(appctx,cmd('adicionar_item',items=['leite'],usar_lista_anterior=True),'Adicione leite nela').json()
    assert result['estado']=='precisa_esclarecer' and 'token' not in result

def test_unconfirmed_proposal_not_last_list(appctx):
    ask(appctx,cmd('adicionar_item','mercado',['leite']))
    result=ask(appctx,cmd('adicionar_item',items=['café'],usar_lista_anterior=True),'Adicione café nela').json()
    assert result['estado']=='precisa_esclarecer'

def test_read_panel_sets_reference(appctx):
    data=seed(appctx)
    appctx[0].get(f"/api/listas/{data['id']}",headers=S2)
    result=ask(appctx,cmd('consultar_lista',usar_lista_anterior=True),'O que tem nela?',S2).json()
    assert result['lista']['id']==data['id']

def test_sessions_dont_share_context(appctx):
    seed(appctx)
    result=ask(appctx,cmd('adicionar_item',items=['arroz'],usar_lista_anterior=True),'Adicione arroz nela',S2).json()
    assert result['estado']=='precisa_esclarecer'

def test_new_conversation_cancels_pending_and_context(appctx):
    seed(appctx)
    p=ask(appctx,cmd('remover_item','mercado',['leite']))
    assert appctx[0].post('/api/conversa/nova',json={},headers=S1).status_code==200
    assert confirm(appctx,p).status_code==409
    result=ask(appctx,cmd('consultar_lista',usar_lista_anterior=True),'O que tem nela?').json()
    assert result['estado']=='precisa_esclarecer' and appctx[2].all_lists()

@pytest.mark.parametrize('text',['sim','confirmo','ok','pode confirmar'])
def test_text_never_confirms(appctx,text):
    seed(appctx)
    ask(appctx,cmd('remover_item','mercado',['leite']))
    result=ask(appctx,cmd('remover_item','mercado',['leite']),text).json()
    assert result['estado']=='precisa_esclarecer'
    assert 'leite' in appctx[2].get_list('mercado')['itens']

def test_cancel_word_does_not_undo_confirmed(appctx):
    seed(appctx)
    p=ask(appctx,cmd('remover_item','mercado',['leite']))
    result=ask(appctx,cmd('fora_do_escopo'),'cancelar').json()
    assert result['cancelou_pendentes']
    assert confirm(appctx,p).status_code==409 and 'leite' in appctx[2].get_list('mercado')['itens']

def test_new_full_command_clears_question(appctx):
    ask(appctx,cmd('consultar_clima'),'Como está o tempo?')
    result=ask(appctx,cmd('consultar_hora'),'Que horas são?').json()
    assert result['estado']=='respondido'
    assert appctx[3].contexts.get(S1['X-Ayla-Session']).awaiting is None

def test_context_ttl_and_limit():
    contexts=Conversations(ttl=1,capacity=2)
    first=contexts.get('one');first.last_list='privada';first.touched-=2
    assert contexts.get('one').last_list is None
    contexts.get('two');contexts.get('three')
    assert len(contexts._items)==2

def test_invalid_session_header_rejected(appctx):
    assert appctx[0].post('/api/comandos',json={'texto':'oi'},headers={'X-Ayla-Session':'x'}).status_code==400

def test_old_database_additive_migration(tmp_path):
    path=tmp_path/'old.db'
    with sqlite3.connect(path) as conn:
        conn.executescript('CREATE TABLE lists(id INTEGER PRIMARY KEY,name TEXT,name_key TEXT UNIQUE); CREATE TABLE items(id INTEGER PRIMARY KEY,list_id INTEGER,text TEXT,item_key TEXT,UNIQUE(list_id,item_key));')
        conn.execute('INSERT INTO lists VALUES(1,?,?)',('lista café da manhã','lista café da manhã'))
        conn.execute('INSERT INTO items VALUES(1,1,?,?)',('pão','pão'))
    store=Store(path);store.initialize();store.initialize()
    data=store.get_list('café da manhã')
    assert data['id']==1 and data['itens']==['pão'] and data['quantidade_pendentes']==1
