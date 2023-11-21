import speech_recognition as sr
import re
import pyttsx3
import os
import openai

nome = "Tyago"

openai.api_key = ' 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'

while(True):

    mic = sr.Recognizer()

    with sr.Microphone() as source:
        engine = pyttsx3.init()
        engine.setProperty('voice', "com.apple.speech.synthesis.voice.luciana")
        mic.adjust_for_ambient_noise(source)
        print("Fale alguma coisa: ")
        audio = mic.listen(source)

        try:
            frase = mic.recognize_google(audio, language='pt-BR')
            print(frase)

            response = openai.Completion.create(
                engine="text-davinci-003",
                prompt=frase,
                max_tokens=150
            )
            assistant_response = response['choices'][0]['text'].strip()
            print(f"Resposta do assistente: {assistant_response}")

            if (re.search("Abra a steam", format(frase))):
                engine.say("Vou iniciar a Steam.")
                os.startfile("Endereço da steam aqui")

            elif (re.search("Abra o opera", format(frase))):
                engine.say("Vou iniciar o Opera.")
                os.startfile("Endereço do opera aqui")
            else:
                engine.say(assistant_response)


        except sr.UnknowValueError:
            print(f"Não entendi, pode repetir {nome}? ")