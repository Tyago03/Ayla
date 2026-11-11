# Ayla 0.5.3 — assistente local com pesquisa e ferramentas

> Compatibilidade preservada da 0.5.1: os testes não exigem permissão de link simbólico no Windows.
> Leia `VALIDACAO.md` na pasta `ayla_v2` para a distinção entre testes executados e SKIPPED.

A Ayla combina conversa geral com Qwen via Ollama, pesquisa na web, leitura de páginas,
calculadora decimal e ferramentas pessoais com confirmação. A interface mantém o grafite
`#0E1315` e o verde-água `#0DAD9E` do aplicativo original.

**Estado:** protótipo local de usuário único. Código público não significa servidor público.
Não exponha a porta HTTP nem o Ollama à internet. Não há autenticação multiusuário.

## Por que esta versão é diferente

O chat deixou de ser uma classificação obrigatória entre comandos de listas. Um agente chama
o modelo com ferramentas nativas. O modelo pode responder em texto, formular uma pesquisa,
ler uma fonte e pedir um cálculo. O backend controla argumentos, permissões, limites e operações.
Não há fluxo programado por assunto, cidade, site ou pergunta. Os exemplos dos testes são
**fixtures isoladas**, nunca respostas usadas pela aplicação em produção.

## Requisitos e início

Python 3.10+, Ollama em execução e `qwen3:4b-instruct` instalado. Os atalhos Windows ficam
na raiz do projeto. Para novo projeto, INSTALAR_DEPENDENCIAS_AYLA.bat cria a .venv.

1. INSTALAR_DEPENDENCIAS_AYLA.bat — instalar dependências (internet).
2. TESTAR_AYLA.bat — testes determinísticos, sem precisar de Qwen ou chave de busca.
3. INICIAR_AYLA.bat — servidor apenas em 127.0.0.1 e navegador.
4. CONFIGURAR_PESQUISA_WEB_AYLA.bat — abrir página oficial, gravar chave sem eco no terminal.
5. Na interface, autorizar pesquisa. “Pesquisar este pedido” exige uma busca antes de concluir.

O modelo é obtido com `ollama pull qwen3:4b-instruct`. O nome pode ser configurado por
`AYLA_MODEL`; compatibilidade com ferramentas precisa ser medida antes de trocar.

No Linux/macOS, a partir da raiz do projeto:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r ayla_v2/requirements-dev.txt
.venv/bin/python -m ayla_v2.launch
```

## Pesquisa e privacidade

A chave é lida de `OLLAMA_API_KEY` ou de uma configuração fora do repositório: Windows,
`%LOCALAPPDATA%/Ayla/web-secret.json`; nos demais sistemas, `~/.config/Ayla/web-secret.json`.
A variável de ambiente tem precedência. Esse arquivo contém a chave em texto e herda proteção
do usuário do sistema; não é um cofre de credenciais. Não compartilhe nem sincronize esse arquivo.
O atalho usa entrada oculta. Nunca cole credenciais no chat, código, issues ou screenshots.

O modelo continua local. Consultas e URLs são enviadas ao Ollama Web Search/Fetch somente
quando autorizadas. O código não envia o histórico inteiro como payload de pesquisa; o modelo
escolhe os termos. Ele ainda pode incluir informações do contexto nessa consulta, por isso
não pesquise com dados confidenciais. Listas completas não são injetadas automaticamente no
histórico do modelo. A web não é um mecanismo de confidencialidade ou de verificação absoluta.

São permitidas até três buscas e duas leituras por resposta, sete etapas do modelo e
um orçamento de execução. O conteúdo recuperado é truncado para caber no contexto. Sites
podem falhar, impor bloqueios ou exigir JavaScript. Não há navegador automatizado, login
em sites, execução de scripts nem acesso a documentos privados por URL.

As referências vêm de URLs retornadas pelo provedor ou fornecidas pelo usuário. Um marcador
numérico inexistente é removido. Isso **não prova** que a afirmação é sustentada pela fonte;
leia as referências. Conteúdo de busca é um trecho; uma página lida também é truncada.
A interface distingue resposta sem web e resposta com material recuperado.

## Capacidades

- Conversar, explicar, traduzir, ajudar com escrita e programação — geração pelo modelo local.
- Pesquisar assuntos variados, refinar consultas e ler páginas — sem regras específicas por tema.
- Calcular com Decimal e AST restrita: + - * / // % **, sqrt, abs. Sem eval/exec.
- Consultar listas e itens; criar, renomear, adicionar, remover, concluir e reabrir itens,
  sempre mediante confirmação para gravações.
- Clima atual com escolha da cidade; relógio do computador.
- Ditado opcional com Whisper local ou serviço do navegador com consentimento; leitura por
  vozes disponibilizadas pelo navegador. Nenhum áudio real foi validado no ambiente de montagem.

## Ditado indisponível

Erro `network`/`service-not-allowed` do SpeechRecognition é falha do serviço do navegador,
não do Qwen. A interface abre orientação persistente e seleciona o modo local, sem gravar
novamente sozinha. Execute ATIVAR_DITADO_LOCAL_AYLA.bat, reinicie o servidor e use
Voz e microfone → Verificar vozes e ditado local. O preparo baixa dependências e um modelo
separado de reconhecimento de fala; não está dentro deste pacote. O usuário revisa o ditado
antes do envio. Não é possível garantir que um serviço externo de ditado voltará a funcionar.

## Estado e segurança

SQLite guarda listas; contexto curto guarda até quatro pares recentes de mensagens,
limitados por tamanho, última lista e tarefa incompleta por 20 minutos de inatividade.
Reiniciar ou “Nova conversa” limpa contexto, não listas. Não há memória permanente de conversa.

Pesquisa e tarefas pessoais não são encadeadas livremente. Depois de receber conteúdo da web,
o backend bloqueia ferramentas pessoais no mesmo turno. Misturar ferramentas pessoais e web
num mesmo lote é rejeitado antes de acessar os dados pessoais. A ferramenta pessoal termina
o turno com uma resposta controlada; confirmação não é uma ferramenta oferecida ao modelo.
Isso reduz superfície de prompt injection, mas não elimina erros de interpretação ou de fontes.

Nenhuma ferramenta executa código, shell, lê arquivos locais arbitrários ou faz compras.
A calculadora permite apenas uma AST pequena e números de magnitude/expoente limitados.
O backend só acessa os endpoints fixos de busca do Ollama, sem encaminhar a chave para páginas.
Validação de URLs bloqueia esquema, credenciais, portas especiais e endereços locais explícitos;
não constitui auditoria completa do DNS/redirecionamento tratado pelo provedor remoto.

## Arquitetura

`main.py` → `agent.py` → Ollama local (texto ou chamadas nativas)

- `web_tools.py`: pesquisa/leitura externa com chave isolada e erros sanitizados.
- `calculator.py`: cálculo determinístico.
- `service.py`/`storage.py`: regras, confirmação de uso único, SQLite e compatibilidade de nomes.
- `conversation.py`: contexto temporário por aba.
- `speech.py`/`static/voice.js`: voz opt-in.
- `publish.py`: exportação allowlist para repositório novo, sem dados ou histórico antigo.

`llm.py` e `evaluate.py` são a linha de base histórica de classificação de tarefas. O chat
normal usa o agente. AVALIAR_IA_AYLA.bat avalia essa linha de base; AVALIAR_AGENTE_AYLA.bat
exercita a arquitetura nova com seu Qwen real, banco temporário e web opcional.

## Avaliação honesta

Os testes offline validam controle de ferramentas e contratos com provedores simulados.
Não medem precisão do Qwen, qualidade de fontes, desempenho na RTX 4050 ou microfone real.
O relatório de avaliação real deve ser revisado por uma pessoa: relevância, evidência e datas.
Não anuncie testes de software como taxa de acerto da IA ou impacto de negócio.

## Publicar o código

Use PREPARAR_PROJETO_PUBLICO_AYLA.bat. A cópia nova não contém `.git`, app legado `Python/dart`,
bancos, gravações, backups, credenciais ou pesos dos modelos. O exportador NÃO faz push.
Revise a saída antes de iniciar um repositório novo; uma checagem heurística não garante ausência
de todo dado sensível. Tornar o repositório antigo privado não invalida uma credencial exposta:
revogue/rotacione no provedor. Preserve os créditos e confirme direitos dos assets/coautorias.

## Referências técnicas

- https://docs.ollama.com/capabilities/tool-calling
- https://docs.ollama.com/capabilities/web-search
- https://docs.ollama.com/api/chat
- https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/removing-sensitive-data-from-a-repository
- https://developer.mozilla.org/en-US/docs/Web/API/SpeechRecognition/error_event

Desenvolvimento assistido por IA. Tyago deve revisar, testar e compreender as decisões antes de
apresentar o trabalho como experiência. O modelo-base Qwen e as dependências são de terceiros.

## Correção 0.5.3 — pesquisa executada, não apenas disponível

A autorização para web continua obrigatória. A indicação de chave presente é uma
verificação de configuração local: não é uma prova de acesso ao provedor.

Quando o modelo devolve um rascunho sem chamar ferramentas em modo automático,
uma decisão local estruturada verifica se a pergunta precisa de fontes. Se decidir
pesquisar, o backend descarta o rascunho e executa a consulta. Não há roteiros por
cidade, população, instituição ou assunto. Isso pode acrescentar uma chamada ao
modelo; a decisão semântica ainda pode errar e precisa de avaliação real.

Em **Pesquisar este pedido**, o backend realiza a consulta antes da resposta (ou
informa por que não conseguiu). O modelo formula a consulta. Se o planejamento
falhar, a pergunta atual completa de até 500 caracteres pode ser usada como consulta,
com aviso. Não se envia o histórico inteiro nesse fallback. Pedidos maiores exigem
reformulação. O botão não dá permissão para acessar dados locais nem gravar listas.

A autorização expressa é lembrada em `sessionStorage` nesta aba durante a sessão
do navegador; pode ser revogada desmarcando a opção. O histórico continua temporário.
O controle de pesquisa obrigatória é consumido após um envio, para não forçar pesquisa
na próxima tarefa pessoal. O estado efetivo aparece abaixo dos controles.

**VERIFICAR_PESQUISA_AYLA.bat** testa o serviço real com uma consulta pública sobre
documentação do Ollama, após confirmação. Não utiliza Qwen, listas ou conversas.
Também existe **Testar conexão (1 consulta)** no painel de pesquisa. Uma chave
recusada, limite do provedor, ausência de conexão e resultado vazio não são tratados
como sucesso. O relatório local `data/pesquisa_diagnostico.json` não contém a chave.

Arquivos novos: `research.py`, `check_web.py`, testes de regressão. Não são necessárias
novas dependências, outro modelo ou outra chave para aplicar a atualização.

## Diagnóstico de conexão (0.5.3)

`VERIFICAR_PESQUISA_AYLA.bat` executa uma consulta pública consentida, sem o Qwen.
Mostra um código como WEB_TLS, WEB_PROXY, WEB_DNS ou WEB_HTTP_503 e salva
`ayla_v2/data/pesquisa_diagnostico.txt`, sem chave, mensagens, corpos HTTP ou
endereços de proxy. A conexão externa respeita proxy/CA configurados no Requests,
mantendo HTTPS verificado, sem encaminhar credenciais em redirecionamentos e
sem repetição automática. Chave salva não significa acesso validado.

Não há garantia de resolver toda política de rede: primeiro obtenha o código real.
Nunca desative SSL, firewall ou antivírus para contornar um erro sem diagnóstico.
