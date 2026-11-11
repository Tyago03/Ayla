# Validação — Ayla 0.5.3

Ambiente de execução: Linux. Não equivale a execução nativa no Windows.

## Resultados observados nesta entrega

- Base 0.5.2: 272 testes aprovados antes da alteração.
- Aplicação 0.5.3: **317 testes aprovados**, incluindo 45 novos casos.
- Windows 1314 simulado no teste de link: **316 aprovados e 1 skipped**.
- Atualizador: **9 testes aprovados**.
- Atualização 0.5.2 para 0.5.3 com banco e arquivos sintéticos: preservados banco/itens,
  cache de voz, ambiente virtual, configuração local, .env e código legado; backup criado.
- Exportação pública limpa: manifesto atualizado com o módulo novo; **317 testes aprovados
  na cópia exportada**. Sem banco, configuração local ou histórico Git nessa cópia.
- Sintaxe: compileall nos módulos Python e node --check em app.js e voice.js aprovados.

## Cobertura adicionada

Códigos HTTP distintos (redirecionamento, 400, 401, 402, 403, 404, 407, 408, 413, 422,
429 e falhas 5xx), TLS, proxy, DNS, conexão recusada/interrompida, timeout de conexão e
leitura, JSON inválido com HTTP 200 e rejeição local de chaves incompatíveis com cabeçalho.

O teste de Requests verifica que o proxy e o CA bundle configurados chegam ao transporte,
que a chave Bearer explícita não é substituída por .netrc, que HTTPS permanece verificado,
que redirecionamentos não são seguidos e que não há repetição automática.

Os testes de sanitização incluem dados fictícios semelhantes a segredos em exceções, corpos
HTTP, variáveis de proxy e caminhos de certificados. Confirmam que esses valores não
aparecem nos códigos, mensagens, JSON/TXT de diagnóstico ou no endpoint de teste da interface.
Nenhuma exceção bruta, corpo do provedor ou cabeçalho de autorização é serializado.

## O que não foi executado

- API de pesquisa com uma chave válida; nenhuma chave do usuário foi acessada.
- Qwen real, Whisper real, microfone ou serviço real de clima.
- Atalhos .bat, interface do seletor de pastas ou rede reais no Windows.
- Renderização visual nova da interface: houve apenas ajuste CSS de quebra do botão.
- Certificação/auditoria completa de segurança.

Esta validação comprova o tratamento das falhas simuladas e a preservação de dados sintéticos.
Não comprova que o erro específico do notebook foi eliminado. O diagnóstico precisa rodar ali
para identificar a categoria concreta. Não usar o número de testes como métrica de acerto da IA.

Logs: validacao/correcao_0.5.3 dentro do pacote. Diretórios de versões anteriores são históricos.
