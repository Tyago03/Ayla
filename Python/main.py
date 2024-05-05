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
ativo = False  
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
                    print("Fale:")
                    print(frase)
                    ativo = True


                # Se o sistema estiver ativado, execute as ações
                if ativo:

                    if ('configuração' in frase) and 'inicial' in frase:
                        engine.say("Vamos começar. Qual é o seu nome?")
                        engine.runAndWait()
                        audio = mic.listen(source)
                        nome_usuario = mic.recognize_google(audio, language='pt-BR').lower()
                        
                        engine.say("Entendi. E em qual cidade você vive?")
                        engine.runAndWait()
                        audio = mic.listen(source)
                        cidade_usuario = mic.recognize_google(audio, language='pt-BR').lower()

                        engine.say(f"Certo. Seu nome é {nome_usuario}, e a cidade é {cidade_usuario}.")
                        engine.runAndWait()
                        ativo = False
                        
                    # desligar / reiniciar o computador
                    elif ('desligue' in frase) and 'computador' in frase:
                        engine.say("desligando o computador")
                        engine.runAndWait()
                        # os.system("shutdown -s -t 1")
                        ativo = False

                    elif ('reinicie' in frase) and 'computador' in frase:
                        engine.say("reiniciando o computador")
                        engine.runAndWait()
                        # os.system("shutdown -r -t 1")
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

                    elif 'que horas são' in frase:
                        if hora.minute == 0:
                            engine.say(f"Agora são {hora.hour} horas em ponto.")
                            engine.runAndWait()
                        else:
                            engine.say(f"Agora são {hora.hour} horas e {hora.minute} minutos.")
                            engine.runAndWait()
                        ativo = False

                    elif any(keyword in frase for keyword in ['temperatura', 'clima']):
                        cid = f"https://api.openweathermap.org/data/2.5/weather?q={cidade_usuario}&appid={APIclima}&lang=pt_br"
                        req = requests.get(cid)
                        dic = requests.get(cid).json()
                        temp = dic['main']['temp'] - 273.15
                        descr = dic['weather'][0]['description']
                        engine.say(f"A temperatura em {cidade_usuario} é de {round(temp, 0)} graus, e o clima é {descr}")
                        engine.runAndWait()
                        ativo = False
                        

        except sr.UnknownValueError:
            print("Não entendi. Dê o comando novamente:")
