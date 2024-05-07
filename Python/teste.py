import speech_recognition as sr
import pyttsx3
from datetime import date
import datetime
import requests


# Variáveis
nome_usuario = None
cidade_usuario = None
compras = []
hora = datetime.datetime.now()
data = date.today()
ds = date.weekday(data)
dias = ['Segunda-feira', 'Terça-feira', 'Quarta-feira', 'Quinta-feira', 'Sexta-feira', 'Sábado', 'Domingo']
meses = ['Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho', 'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro']
APIclima = "3fa1b2a2653d17190c4a1f574d8a259a"

def init_engine():
    engine = pyttsx3.init()
    engine.setProperty('voice', "com.apple.speech.synthesis.voice.luciana")
    engine.setProperty('rate', 150)  # Velocidade da fala
    return engine

def init_recognizer():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        recognizer.adjust_for_ambient_noise(source, duration=1)  # Calibrar por 1 segundo
    recognizer.energy_threshold += 100  # Ajustar a sensibilidade conforme necessário
    return recognizer

'''def init_recognizer():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        recognizer.adjust_for_ambient_noise(source)  # Calibra baseado no ruído do ambiente
        initial_threshold = recognizer.energy_threshold
        while True:
            try:
                print("Ajustando sensibilidade...")
                audio = recognizer.listen(source, timeout=1)
                # Tenta detectar se o ambiente mudou significativamente
                if recognizer.energy_threshold > initial_threshold + 50:
                    recognizer.adjust_for_ambient_noise(source)
                    print("Ambiente ruidoso, recalibrando...")
                break
            except sr.WaitTimeoutError:
                continue  # Continua tentando ajustar até conseguir uma leitura estável
    return recognizer'''

def listen_to_speech(recognizer, source):
    try:
        print("Ouvindo...")
        audio = recognizer.listen(source, timeout=5, phrase_time_limit=3)
        return recognizer.recognize_google(audio, language='pt-BR').lower()
    except sr.UnknownValueError:
        return "Não entendi"
    except sr.RequestError:
        return "Erro de serviço"

def respond(engine, text):
    print(f"Resposta: {text}")
    engine.say(text)
    engine.runAndWait()
    engine.stop()

def get_user_confirmation(engine, recognizer, source, info_type):
    while True:
        respond(engine, f"{info_type.capitalize()} entendido é {globals()[info_type]}. Esse é o seu {info_type}?")
        response = listen_to_speech(recognizer, source)
        if response:
            if 'sim' in response:
                break
            elif 'não' in response or 'nao' in response:
                respond(engine, f"Por favor, diga o seu {info_type} novamente.")
                globals()[info_type] = listen_to_speech(recognizer, source)
                if globals()[info_type] is None:
                    respond(engine, "Não consegui entender, vamos tentar novamente.")
                    continue
        else:
            respond(engine, "Não consegui entender, por favor repita.")

def configuracao_inicial(recognizer, source, engine):
    global nome_usuario, cidade_usuario

    while nome_usuario is None:
        respond(engine, "Por favor, diga o seu nome.")
        nome_usuario = listen_to_speech(recognizer, source)
        if nome_usuario:
            get_user_confirmation(engine, recognizer, source, 'nome_usuario')
        else:
            respond(engine, "Não consegui entender, vamos tentar novamente.")

def main():
    recognizer = init_recognizer()
    engine = init_engine()

    respond(engine, "Olá! Eu me chamo Ayla, sua assistente virtual. Para começarmos, vamos configurar uma conta para você.")
    configuracao_inicial(recognizer, engine)

    with sr.Microphone() as source:
        while True:

            command = listen_to_speech(recognizer, source)

            # função configuração inicial
            if 'configuração' in command and 'inicial' in command:
                configuracao_inicial(recognizer, source, engine)

            # função quem sou eu
            elif 'quem' in command and 'sou' in command and 'eu' in command:
                respond(engine, f"Você é {nome_usuario}")

            # função pegar horário
            elif 'horas' in command and 'são' in command:
                if hora.minute == 0:
                    engine.say(f"Agora são {hora.hour} horas.")
                    engine.runAndWait()
                else:
                    engine.say(f"Agora são {hora.hour} horas e {hora.minute} minutos.")
                    engine.runAndWait()

            # função pegar data
            elif ('qual dia' in command or 'que dia' in command) and 'hoje' in command:
                engine.say(f"Hoje é {dias[ds]}, dia {data.day} de {meses[data.month - 1]} de {data.year}")
                engine.runAndWait()

            # função adicionar na lista de compras
            if ('adiciona' in command or 'adicione' in command or 'coloca' in command or 'coloque' in command) and 'lista' in command and ('compras' in command or 'compra' in command):
                item = command.replace('adiciona', '').replace('adicione', '').replace('coloca', '').replace('coloque', '').replace('lista', '').replace('compras', '').replace('compra', '').strip()
                compras.append(item)
                respond(engine, f"{item} adicionado à sua lista de compras.")

            # função limpar lista de compras
            elif ('limpar' in command or 'limpe' in command) and 'lista' in command and ('compra' in command or 'compras' in command):
                compras.clear()
                respond(engine, "Acabei de limpar sua lista de compras.")

            # função pegar temperatura e clima
            elif 'qual' in command and ('temperatura' in command or 'clima' in command):
                cid = f"https://api.openweathermap.org/data/2.5/weather?q={cidade_usuario}&appid={APIclima}&lang=pt_br"
                try:
                    response = requests.get(cid)
                    if response.status_code == 200:
                        dic = response.json()
                        temp = dic['main']['temp'] - 273.15
                        descr = dic['weather'][0]['description']
                        engine.say(f"A temperatura em {cidade_usuario} é de {round(temp, 0)} graus, e o clima é {descr}")
                    else:
                        engine.say("Houve um problema ao obter o clima.")
                except requests.RequestException:
                    engine.say("Erro ao acessar o serviço de clima.")
                engine.runAndWait()


            elif command:
                respond(engine, command)

            else:
                respond(engine, "Não entendi, por favor repita.")

if __name__ == "__main__":
    main()
