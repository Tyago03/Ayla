import speech_recognition as sr
import pyttsx3
import os

nome = "Tyago"

while (True):
    
    mic = sr.Recognizer()
    
    with sr.Microphone() as source:
        
        engine = pyttsx3.init()
        engine.setProperty('voice', "com.apple.speech.synthesis.voice.luciana")
        mic.adjust_for_ambient_noise(source) 
        
        print("Fale alguma coisa:")
        
        audio = mic.listen(source)

        try:
            frase = mic.recognize_google(audio, language='pt-BR')

            # desligar / reiniciar o computador
            if "desligue" or "desligar" in frase and "computador" in frase:
                engine.say("desligando o computador")
                engine.runAndWait()
                os.system("shutdown -s -t 1")
            elif "reinicie" or "reiniciar" in frase and "computador" in frase:
                engine.say("reiniciando o computador")
                engine.runAndWait()
                os.system("shutdown -r -t 1")

            # abrir programas
            elif 'abrir' in frase and 'opera' in frase:
                os.startfile("<caminho para o opera na sua máquina>")
            elif 'abrir' in frase and 'discord' in frase:
                os.startfile("<caminho para o discord na sua máquina>")
            elif 'abrir' in frase and 'steam' in frase:
                os.startfile("<caminho para a steam na sua máquina>")
            elif 'abrir' in frase and 'vscode' in frase:
                os.startfile("<caminho para o vscode na sua máquina>")

            # checar temperatura, horário e data






            print(frase)
        
        except sr.UnknownValueError:
            print("Não entendi. Dê o comando novamente:")