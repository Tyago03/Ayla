# Ayla — assistente local com pesquisa e ferramentas

> Compatibilidade 0.5.1: os testes não exigem permissão de link simbólico no Windows.
> Leia `VALIDACAO.md` na pasta `ayla_v2` para a distinção entre testes executados e SKIPPED.

Aplicação de IA com conversa geral, busca na web, calculadora, ferramentas pessoais controladas
e voz opcional. Qwen via Ollama, FastAPI, Pydantic e SQLite. Modelo-base de terceiros; aplicação
e integrações desenvolvidas com assistência de IA.

## Iniciar

Instale Python 3.10+ e Ollama; baixe `qwen3:4b-instruct`. No Windows, execute
INSTALAR_DEPENDENCIAS_AYLA.bat, TESTAR_AYLA.bat e INICIAR_AYLA.bat. A pesquisa exige uma
chave própria: CONFIGURAR_PESQUISA_WEB_AYLA.bat. O projeto não inclui chave ou banco de usuário.

**[Documentação, arquitetura e limites](ayla_v2/README.md)** ·
**[Validação](ayla_v2/VALIDACAO.md)** · **[Publicação segura](PUBLICAR_NO_GITHUB.md)**

## O que demonstra

O modelo decide entre responder e chamar ferramentas genéricas. Consultas à web são formuladas
pelo modelo, sem uma função por assunto. O backend limita ferramentas, valida argumentos e
mantém gravações atrás de confirmação humana. Cálculos são executados por AST restrita;
fontes exibidas são as realmente recuperadas. Não se trata de um modelo treinado do zero.

## Estado do projeto

Protótipo local de usuário único; não expor na internet. Testes automatizados com fornecedores
simulados não equivalem a precisão medida do modelo. Resultados reais de desempenho, avaliação
factual, número de usuários ou economia de tempo só devem ser publicados depois de medidos.
Não há promessa de qualidade equivalente à de serviços de IA comerciais.

## Origem e créditos

Evolução independente do experimento acadêmico Ayla. O histórico e o código legado não fazem
parte deste repositório limpo. Preservar os créditos da origem e da identidade visual; revisar
coautorias e permissões antes da publicação. As dependências mantêm suas licenças próprias.
Nenhuma licença ampla para assets de terceiros foi atribuída automaticamente por esta exportação.

## Confiabilidade da pesquisa (0.5.3)

Há uma segunda decisão local quando o modelo responde sem ferramentas em modo web
automático. O modo de pesquisa explícita é executado pelo backend, com limites,
sem depender de o modelo optar espontaneamente por chamar a ferramenta. O atalho
`VERIFICAR_PESQUISA_AYLA.bat` verifica a conexão ao provedor sem usar o Qwen.
Nenhuma medição real de acurácia do modelo é inferida a partir dos testes simulados.

## Diagnóstico de conexão (0.5.3)

`VERIFICAR_PESQUISA_AYLA.bat` executa uma consulta pública consentida, sem o Qwen.
Mostra um código como WEB_TLS, WEB_PROXY, WEB_DNS ou WEB_HTTP_503 e salva
`ayla_v2/data/pesquisa_diagnostico.txt`, sem chave, mensagens, corpos HTTP ou
endereços de proxy. A conexão externa respeita proxy/CA configurados no Requests,
mantendo HTTPS verificado, sem encaminhar credenciais em redirecionamentos e
sem repetição automática. Chave salva não significa acesso validado.

Não há garantia de resolver toda política de rede: primeiro obtenha o código real.
Nunca desative SSL, firewall ou antivírus para contornar um erro sem diagnóstico.
