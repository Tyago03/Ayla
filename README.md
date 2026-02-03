# Ayla - Assistente Virtual

Ayla é uma assistente virtual desenvolvida em Python que processa comandos por voz/texto e executa diversas funcionalidades através de uma API RESTful construída com FastAPI.

## Funcionalidades

- **Informações de Data e Hora**: Consulta do dia da semana, data atual e horário
- **Previsão do Tempo**: Integração com OpenWeatherMap API para consultas climáticas em tempo real
- **Gerenciamento de Listas**: 
  - Criação e gerenciamento de lista de compras
  - Criação de listas personalizadas pelo usuário
- **Sistema de Alarmes**: Configuração de alarmes com data, horário e nome personalizado
- **Processamento de Linguagem Natural**: Extração inteligente de entidades (cidades, horários, datas) dos comandos do usuário

## Tecnologias Utilizadas

- **Python 3.x**
- **FastAPI**: Framework web moderno e de alta performance
- **Pydantic**: Validação de dados
- **Uvicorn**: Servidor ASGI
- **Requests**: Requisições HTTP para APIs externas
- **CORS Middleware**: Suporte para requisições cross-origin

## Instalação

1. Clone o repositório:
```bash
git clone https://github.com/Tyago03/Ayla.git
cd Ayla/Python
````

2. Instale as dependências:

````bash
pip install fastapi uvicorn pydantic requests
````

3. Configure sua chave API do OpenWeatherMap no arquivo main.py:

````python
APIclima = "sua_chave_api_aqui"
````

## Como Usar

1. Inicie o servidor FastAPI:

````bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
````

2. (Opcional) Para acesso externo, utilize ngrok:

````bash
ngrok http 8000
````

3. Envie requisições POST para o endpoint `/command/`:

````json
{
  "text": "qual a temperatura em São Paulo"
}
````
## Exemplos de Comandos

- "Qual dia é hoje?"

- "Que horas são?"

- "Qual a temperatura em Goiânia?"

- "Adicione leite na lista de compras"

- "Crie uma lista chamada mercado"

- "Crie um alarme chamado reuniao para o dia 05/02/2026 às 14:30"

- "Limpe a lista de compras"

## Endpoints da API
`GET /`
Endpoint de teste que retorna uma mensagem de boas-vindas.

`POST /command/`
Processa comandos de texto e retorna a resposta da assistente.

**Request Body:**

````json
{
  "text": "seu comando aqui"
}
````

**Response:**

````json
{
  "message": "resposta da assistente"
}
````

## Estrutura do Projeto
````text
Ayla/
├── Python/
│   ├── main.py      # API principal com FastAPI
│   └── teste.py     # Arquivo de testes
├── dart/            # Implementações em Dart (em desenvolvimento)
└── README.md
````

## Recursos de Processamento
A Ayla utiliza expressões regulares (regex) para extrair informações dos comandos:

- Horários: Formato HH:MM

- Datas: Formato DD/MM/YYYY

- Cidades: Extração contextual após preposições

## Configurações de Segurança
- CORS habilitado para todas as origens (`["*"]`)

- Logging configurado para monitoramento de requisições

- Tratamento de exceções com códigos HTTP apropriados

## Licença

Este projeto foi desenvolvido para fins educacionais como parte de um trabalho acadêmico em grupo.

© 2026 Tyago, Christian e Marcos. Todos os direitos reservados.

Este software é disponibilizado apenas para fins de demonstração em portfólio acadêmico. 
Nenhuma parte deste projeto pode ser reproduzida, distribuída ou utilizada sem 
autorização prévia por escrito de todos os autores.









