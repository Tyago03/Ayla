import speech_recognition as sr
import pyttsx3
import os
from datetime import date
import datetime
import requests

nome = "Tyago"
hora = datetime.datetime.now()
data = date.today()
ds = date.weekday(data)
dias = ['Segunda-feira', 'Terça-feira', 'Quarta-feira', 'Quinta-feira', 'Sexta-feira', 'Sábado', 'Domingo']
meses = ['Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho', 'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro']
APIclima = "3fa1b2a2653d17190c4a1f574d8a259a"

ativo = False  # Variável para controlar se o sistema de voz está ativo
ultima_fala = datetime.datetime.now()

while True:
    mic = sr.Recognizer()

    with sr.Microphone() as source:

        engine = pyttsx3.init()
        engine.setProperty('voice', "com.apple.speech.synthesis.voice.luciana")
        mic.adjust_for_ambient_noise(source)

        audio = mic.listen(source)

        try:
            # Verificar se houve uma fala antes de tentar interpretar a frase
                frase = mic.recognize_google(audio, language='pt-BR').lower()

                # Verificar se a palavra de ativação foi dita e o sistema não estava ativo
                if ('ayla' in frase or 'aylla' in frase or 'aila' in frase or 'ailla' in frase) and not ativo:
                    print("Sistema ativado.")
                    print(frase)
                    ativo = True


                # Se o sistema estiver ativado, execute as ações
                if ativo:

                    # desligar / reiniciar o computador
                    if frase == "desligue o computador":
                        engine.say("desligando o computador")
                        engine.runAndWait()
                        os.system("shutdown -s -t 1")
                        ativo = False

                    elif frase == "reinicie o computador":
                        engine.say("reiniciando o computador")
                        engine.runAndWait()
                        os.system("shutdown -r -t 1")
                        ativo = False

                    # abrir programas
                    elif ('abrir' in frase or 'abra' in frase) and ('opera' in frase or 'ópera' in frase):
                        engine.say("Abrindo o opera.")
                        os.startfile("C:/Users/Pessoal/AppData/Roaming/Microsoft/Windows/Start Menu/Programs/Navegador Opera GX.lnk")
                        engine.runAndWait()
                        ativo = False

                    elif ('abrir' in frase or 'abra' in frase) and 'discord' in frase:
                        engine.say("Abrindo o discordi.")
                        os.startfile("C:/Users/Pessoal/AppData/Roaming/Microsoft/Windows/Start Menu/Programs/Discord Inc/Discord.lnk")
                        engine.runAndWait()
                        ativo = False

                    elif ('abrir' in frase or 'abra' in frase) and 'steam' in frase:
                        engine.say("Abrindo a steam.")
                        os.startfile("C:/Users/Pessoal/AppData/Roaming/Microsoft/Windows/Start Menu/Programs/Steam/Steam.lnk")
                        engine.runAndWait()
                        ativo = False

                    elif ('abrir' in frase or 'abra' in frase) and 'vscode' in frase:
                        engine.say("Abrindo o visual studio code.")
                        os.startfile("C:/Users/Pessoal/AppData/Roaming/Microsoft/Windows/Start Menu/Programs/Visual Studio Code/Visual Studio Code.lnk")
                        engine.runAndWait()
                        ativo = False

                    # checar temperatura, clima, horário e data
                    elif ('qual dia' in frase or 'que dia' in frase) and 'hoje' in frase:
                        engine.say(f"Hoje é {dias[ds]}, dia {data.day} de {meses[data.month - 1]} de {data.year}")
                        engine.runAndWait()
                        ativo = False

                    elif any(keyword in frase for keyword in ['que horas são', 'quais as horas', 'qual o horário', 'qual horario']):
                        if hora.minute == 0:
                            engine.say(f"Agora são {hora.hour} horas em ponto.")
                            engine.runAndWait()
                        else:
                            engine.say(f"Agora são {hora.hour} horas e {hora.minute} minutos.")
                        ativo = False

                    elif any(keyword in frase for keyword in ['temperatura', 'clima']):
                        if 'goiânia' in frase:
                            cid = f"https://api.openweathermap.org/data/2.5/weather?q=goiânia&appid={APIclima}&lang=pt_br"
                            req = requests.get(cid)
                            dic = requests.get(cid).json()
                            temp = dic['main']['temp'] - 273.15
                            descr = dic['weather'][0]['description']
                            engine.say(f"A temperatura em Goiânia é de {round(temp, 0)} graus, e o clima é {descr}")
                            engine.runAndWait()
                            ativo = False
                        else:
                            cid = f"https://api.openweathermap.org/data/2.5/weather?q=brasília&appid={APIclima}&lang=pt_br"
                            req = requests.get(cid)
                            dic = requests.get(cid).json()
                            temp = dic['main']['temp'] - 273.15
                            descr = dic['weather'][0]['description']
                            engine.say(f"A temperatura em Brasília é de {round(temp, 0)} graus, e o clima é {descr}")
                            engine.runAndWait()
                            ativo = False

        except sr.UnknownValueError:
            if ativo:
                print("Não entendi. Dê o comando novamente:")
