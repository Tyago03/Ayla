from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timedelta
import requests
import re
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)

# comando: uvicorn main:app --host 0.0.0.0 --port 8000 --reload
# segundo comando: nesse diretório 'ngrok http 8000'
app = FastAPI()

origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Lista de compras global
compras = []
# Lista de alarmes global
alarmes = []
# Dicionário para armazenar listas criadas pelo usuário
listas = {}

# Regex patterns
time_pattern = re.compile(r'\b\d{1,2}:\d{2}\b')
date_pattern = re.compile(r'\b\d{1,2}/\d{1,2}/\d{4}\b')

def extract_city(text):
    match = re.search(r"(em|na|no|de)\s+([A-Za-z\s]+)", text)
    if match:
        return match.group(2).strip()
    return None

def extract_time(text):
    match = time_pattern.search(text)
    if match:
        return match.group()
    return None

def extract_date(text):
    match = date_pattern.search(text)
    if match:
        return match.group()
    return None

def process_user_command(text):
    global compras, alarmes
    text = text.lower()
    if not text:
        return "Não entendi. Dê o comando novamente."

    hora = datetime.now()
    data = datetime.today().date()  # Certifique-se de que 'data' seja inicializado corretamente
    ds = data.weekday()
    dias = ['Segunda-feira', 'Terça-feira', 'Quarta-feira', 'Quinta-feira', 'Sexta-feira', 'Sábado', 'Domingo']
    meses = ['Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho', 'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro']
    APIclima = "3fa1b2a2653d17190c4a1f574d8a259a"

    if ('qual dia' in text or 'que dia' in text) and 'hoje' in text:
        return f"Hoje é {dias[ds]}, dia {data.day} de {meses[data.month - 1]} de {data.year}"
    
    elif 'command' in text:
        return "deu certo, mas deu errado"
    
    elif 'que horas são' in text:
        if hora.minute == 0:
            return f"Agora são {hora.hour} horas em ponto."
        else:
            return f"Agora são {hora.hour} horas e {hora.minute} minutos."
        
    elif any(keyword in text for keyword in ['temperatura', 'clima', 'tempo']):
        cidade_usuario = extract_city(text)
        if cidade_usuario:
            cid = f"https://api.openweathermap.org/data/2.5/weather?q={cidade_usuario}&appid={APIclima}&lang=pt_br"
            req = requests.get(cid)
            dic = req.json()
            if req.status_code == 200:
                temp = dic['main']['temp'] - 273.15
                descr = dic['weather'][0]['description']
                return f"A temperatura em {cidade_usuario} é de {round(temp, 0)} graus, e o clima é {descr}"
            else:
                return f"Não consegui obter a temperatura para {cidade_usuario}."
        else:
            return "Por favor, informe o nome da cidade."
    
    elif ('adicione' in text or 'coloque' in text) and 'lista de compras' in text:
        item = text.split(' ', 1)[1].replace('na lista de compras', '').replace('lista de compras', '').strip()
        if item in compras:
            return f"{item} já está na lista de compras."
        else:
            compras.append(item)
            return f"{item} adicionado à lista de compras."
    
    elif 'limpe a lista de compras' in text or 'apague a lista de compras' in text:
        if not compras:
            return "A lista de compras já está limpa."
        else:
            compras = []
            return "Lista de compras apagada."
        
    elif ('crie' in text or 'cria' in text) and 'lista' in text:
        lista_nome_match = re.search(r'lista chamada (\w+)', text)
        if lista_nome_match:
            lista_nome = lista_nome_match.group(1)
            if lista_nome in listas:
                return f"Já existe uma lista chamada {lista_nome}."
            else:
                listas[lista_nome] = []
                return f"Acabei de criar a lista {lista_nome}."
        else:
            return "Por favor, informe o nome da lista que deseja criar."
    
    elif 'alarme' in text:
        time = extract_time(text)
        date = extract_date(text)
        name = re.search(r'alarme chamado (\w+)', text)
        
        if not time:
            return "Por favor, informe o horário para o alarme."
        if not date:
            return "Por favor, informe a data para o alarme."
        if not name:
            return "Por favor, informe o nome do alarme."

        alarmes.append({'name': name.group(1), 'time': time, 'date': date})
        return f"Alarme {name.group(1)} para o dia {date} às {time} criado com sucesso."
    
    else:
        return "Comando não reconhecido."

class Command(BaseModel):
    text: str

@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.post("/command/")
async def process_command_endpoint(command: Command):
    try:
        logging.info(f"Recebendo comando: {command.text}")
        response = process_user_command(command.text)
        logging.info(f"Resposta gerada: {response}")
        return {"message": response}
    except Exception as e:
        logging.error(f"Erro ao processar comando: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
