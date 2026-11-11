from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline


# Exemplos didáticos: texto de entrada e intenção esperada.
EXEMPLOS = [
    ("que horas são", "consultar_hora"),
    ("me diga o horário atual", "consultar_hora"),
    ("quero saber a hora", "consultar_hora"),

    ("qual a temperatura em Goiânia", "consultar_clima"),
    ("como está o clima em Recife", "consultar_clima"),
    ("consulte o tempo em Brasília", "consultar_clima"),

    ("adicione leite à lista de compras", "adicionar_item"),
    ("coloque arroz na lista", "adicionar_item"),
    ("inclua feijão nas compras", "adicionar_item"),
]


def main() -> None:
    textos, intencoes = zip(*EXEMPLOS)

    modelo = make_pipeline(
        TfidfVectorizer(
            strip_accents="unicode",
            ngram_range=(1, 2),
        ),
        LogisticRegression(max_iter=1000, random_state=42),
    )

    # Aqui os parâmetros são aprendidos a partir dos exemplos.
    modelo.fit(textos, intencoes)

    testes = [
        "qual é o horário agora",
        "qual o clima em Salvador",
        "adicione café à lista",
        "me ensine a tocar violão",
    ]

    for texto in testes:
        previsao = modelo.predict([texto])[0]
        print(f"{texto!r} -> {previsao}")


if __name__ == "__main__":
    main()
    