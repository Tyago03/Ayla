"""O modelo propõe. O backend limita operações e exige confirmação para gravar."""
from datetime import datetime
import re
import time
from typing import Any, Callable

from .conversation import Context, Conversations, short_slot_reply
from .errors import AppError
from .schemas import Comando, key
from .storage import Store
from .weather import Weather

MUTATIONS = {"criar_lista", "renomear_lista", "remover_item", "concluir_item", "reabrir_item"}
LIST_INTENTS = MUTATIONS | {"adicionar_item", "consultar_lista"}
HELP = (
    "Posso conversar, explicar conceitos e ajudar com textos. Com pesquisa autorizada, consulto fontes na web; também faço cálculos e organizo listas, encontro itens salvos e consulto o clima atual.\n"
    "Experimente: ‘Crie a lista viagem’, ‘Adicione passaporte na lista viagem’, "
    "‘Quais listas eu tenho?’, ‘Em qual lista está o café?’, ‘Marque pão como concluído na lista mercado’, "
    "‘Retire leite da lista mercado’ ou ‘Renomeie a lista viagem para férias’.\n"
    "Também informo a data e a hora deste computador. Alterações precisam do seu clique de confirmação. "
    "Use o microfone para ditar e o alto-falante abaixo de uma resposta para ouvi-la. "
    "Não crio alarmes, não faço compras e não executo comandos no computador."
)

class Ayla:
    def __init__(self, store: Store, interpreter: Callable[[str], Comando], weather: Weather):
        self.store, self.interpreter, self.weather = store, interpreter, weather
        self.contexts = Conversations()

    def process(self, text: str, session_id: str | None = None) -> dict[str, Any]:
        start = time.perf_counter()
        ctx = self.contexts.get(session_id)
        if not ctx.lock.acquire(blocking=False):
            raise AppError("Já existe um pedido nesta conversa. Aguarde a resposta.", 429)
        try:
            normalized = key(text).strip(".!? ")
            if normalized in {"sim", "confirmo", "confirmar", "pode confirmar", "ok"}:
                return {"estado": "precisa_esclarecer", "mensagem": "Para alterar uma lista, revise a proposta e use o botão Confirmar. Uma resposta por texto ou voz não confirma a operação."}
            if normalized in {"cancelar", "cancele", "deixa pra lá", "deixa pra la"}:
                ctx.awaiting = None; ctx.slot = None
                for token in ctx.tokens:
                    try: self.store.cancel(token)
                    except AppError: pass
                ctx.tokens.clear()
                return {"estado": "respondido", "mensagem": "Cancelei as propostas ainda pendentes desta conversa. Alterações já confirmadas permanecem salvas.", "cancelou_pendentes": True}
            command = short_slot_reply(text, ctx)
            context_used = command is not None
            if command is None:
                if hasattr(self.interpreter, "interpret"):
                    command = self.interpreter.interpret(text, ctx.public())
                else:
                    command = self.interpreter(text)
            # Referências só são resolvidas para uma lista confirmada ou consultada.
            referential = bool(re.search(r"\b(nela|dela|nessa lista|nesta lista|mesma lista|essa lista|nesta|nessa)\b", text, re.I))
            if command.intencao in LIST_INTENTS and (command.usar_lista_anterior or (not command.lista and referential)):
                if not ctx.last_list:
                    return self._clarify("Qual lista você quer usar? Diga o nome.", command, ctx, "lista")
                if not command.lista:
                    command = command.model_copy(update={"lista": ctx.last_list, "usar_lista_anterior": False})
                    context_used = True
            result = self._dispatch(command, ctx)
            if result["estado"] != "precisa_esclarecer":
                ctx.awaiting = None; ctx.slot = None
            if result.get("lista"):
                ctx.last_list = result["lista"]["nome_exibicao"]
            if result.get("token"):
                ctx.tokens.append(result["token"])
                ctx.tokens = ctx.tokens[-50:]
            result["interpretacao"] = command.model_dump()
            result["contexto_utilizado"] = context_used
            result["latencia_total_ms"] = round((time.perf_counter() - start) * 1000)
            return result
        finally:
            ctx.lock.release()

    def execute(self, command: Comando, session_id: str | None = None) -> dict[str, Any]:
        """Executes a validated tool proposal; mutations still only create pending tokens."""
        ctx = self.contexts.get(session_id)
        with ctx.lock:
            used = False
            if command.usar_lista_anterior and command.intencao in LIST_INTENTS:
                if not ctx.last_list:
                    return self._clarify("Qual lista você quer usar?", command, ctx, "lista")
                if not command.lista:
                    command = command.model_copy(update={"lista": ctx.last_list, "usar_lista_anterior": False})
                    used = True
            result = self._dispatch(command, ctx)
            if result["estado"] != "precisa_esclarecer":
                ctx.awaiting = None; ctx.slot = None
            if result.get("lista"):
                ctx.last_list = result["lista"]["nome_exibicao"]
            if result.get("token"):
                ctx.tokens.append(result["token"])
                ctx.tokens = ctx.tokens[-50:]
            result["interpretacao"] = command.model_dump()
            result["contexto_utilizado"] = used
            return result

    def _dispatch(self, command: Comando, ctx: Context | None = None) -> dict[str, Any]:
        ctx = ctx or Context()
        intent = command.intencao
        # Campos extras de outras operações falham fechados, mesmo com JSON válido.
        allowed = {
            "consultar_clima": {"cidade"}, "adicionar_item": {"lista", "itens"},
            "consultar_lista": {"lista"}, "listar_listas": set(), "criar_lista": {"lista"},
            "renomear_lista": {"lista", "novo_nome"}, "remover_item": {"lista", "itens"},
            "concluir_item": {"lista", "itens"}, "reabrir_item": {"lista", "itens"},
            "buscar_item": {"termo"}, "consultar_data": set(), "consultar_hora": set(),
            "ajuda": set(), "saudacao": set(), "fora_do_escopo": set(),
        }[intent]
        for name in ("cidade", "lista", "itens", "novo_nome", "termo"):
            if getattr(command, name) and name not in allowed:
                raise AppError("A interpretação misturou campos de operações diferentes. Nada foi alterado; reformule o pedido.", 502)
        if command.usar_lista_anterior and intent not in LIST_INTENTS:
            raise AppError("Referência de lista em uma operação incompatível. Reformule o pedido.", 502)

        if intent == "fora_do_escopo":
            return {"estado": "fora_do_escopo", "mensagem": "Ainda não faço esse tipo de pedido. Posso organizar listas, buscar itens, informar data/hora e consultar o clima atual. Diga ‘O que você pode fazer?’ para ver exemplos. Faça uma ação por mensagem."}
        if intent in {"saudacao", "ajuda"}:
            return {"estado": "respondido", "mensagem": ("Oi! Sou a Ayla. " if intent == "saudacao" else "") + HELP}
        if intent in {"consultar_data", "consultar_hora"}:
            now = datetime.now().astimezone()
            days = ["segunda-feira", "terça-feira", "quarta-feira", "quinta-feira", "sexta-feira", "sábado", "domingo"]
            message = f"Agora são {now:%H:%M:%S}." if intent == "consultar_hora" else f"Hoje é {days[now.weekday()]}, {now:%d/%m/%Y}."
            return {"estado": "respondido", "mensagem": message + f" Referência: relógio e fuso deste computador (UTC{now:%z}).", "origem": "Relógio do sistema; não uma previsão do modelo"}
        if intent == "listar_listas":
            catalog = self.store.list_catalog(); total = len(catalog)
            message = ("Você ainda não tem listas salvas. Peça ‘Crie a lista mercado’ para começar." if not catalog else
                       f"Você tem {total} {'lista salva' if total == 1 else 'listas salvas'}. Abra um cartão para ver os itens.")
            return {"estado": "respondido", "mensagem": message, "catalogo": catalog, "total_listas": total, "origem": "Nomes e contagens consultados no banco local"}
        if intent == "buscar_item":
            if not command.termo:
                return self._clarify("Qual item você quer encontrar?", command, ctx, "termo")
            results = self.store.search_items(command.termo)
            message = f"Encontrei {len(results)} {'ocorrência' if len(results) == 1 else 'ocorrências'} de “{command.termo}”." if results else f"Não encontrei “{command.termo}” nas listas salvas."
            return {"estado": "respondido", "mensagem": message, "encontrados": results, "origem": "Busca literal nos itens salvos, sem distinguir acentos"}
        if intent == "consultar_clima":
            if not command.cidade:
                return self._clarify("Em qual cidade? Você pode responder apenas com o nome.", command, ctx, "cidade")
            places = self.weather.search(command.cidade)
            if not places:
                return self._clarify("Não encontrei essa cidade. Informe cidade e estado/país.", command, ctx, "cidade")
            token = self.store.create_pending("weather", {"locations": places})
            return {"estado": "escolher_cidade", "mensagem": "Confirme a localização para consultar o clima atual.", "token": token,
                    "opcoes": [{"indice": i, "nome": p["label"]} for i, p in enumerate(places)]}
        if not command.lista:
            return self._clarify("Qual lista você quer usar? Pode responder só com o nome.", command, ctx, "lista")
        if intent in {"adicionar_item", "remover_item", "concluir_item", "reabrir_item"} and not command.itens:
            return self._clarify("Quais itens? Diga os nomes que quer usar.", command, ctx, "itens")
        if intent == "adicionar_item":
            self.store.get_list(command.lista)
            token = self.store.create_pending("add", command.model_dump())
            return {"estado": "confirmacao_necessaria", "mensagem": f"Posso adicionar estes itens em “{command.lista}”? Confira antes de confirmar.",
                    "token": token, "proposta": {"nome": command.lista, "itens": command.itens}, "rotulo_confirmar": "Confirmar inclusão"}
        if intent == "consultar_lista":
            data = self.store.get_list(command.lista)
            if data is None:
                return {"estado": "respondido", "mensagem": f"A lista “{command.lista}” ainda não existe. Confira o nome em Minhas listas."}
            return {"estado": "respondido", "mensagem": f"Aqui está sua lista “{data['nome_exibicao']}”.", "lista": data}
        if intent == "renomear_lista" and not command.novo_nome:
            return self._clarify("Qual será o novo nome dessa lista?", command, ctx, "novo_nome")
        if intent in MUTATIONS:
            payload, proposal = self.store.prepare_change(command)
            labels = {"criar_lista": "Confirmar criação", "renomear_lista": "Confirmar novo nome", "remover_item": "Confirmar remoção", "concluir_item": "Marcar como concluído", "reabrir_item": "Marcar como pendente"}
            descriptions = {"criar_lista": f"Criar a lista vazia “{command.lista}”?", "renomear_lista": f"Renomear “{command.lista}” para “{command.novo_nome}”? Os itens serão preservados.",
                            "remover_item": f"Remover estes itens de “{command.lista}”? A remoção só acontece após confirmar.", "concluir_item": f"Marcar estes itens de “{command.lista}” como concluídos? Eles continuam salvos.", "reabrir_item": f"Deixar estes itens de “{command.lista}” pendentes novamente?"}
            token = self.store.create_pending("change", payload)
            return {"estado": "confirmacao_necessaria", "mensagem": descriptions[intent], "token": token, "proposta": proposal, "rotulo_confirmar": labels[intent]}
        raise AppError("Operação não permitida.", 400)

    @staticmethod
    def _clarify(message: str, command: Comando | None = None, ctx: Context | None = None, slot: str | None = None) -> dict[str, Any]:
        if ctx is not None:
            ctx.awaiting, ctx.slot = command, slot
        return {"estado": "precisa_esclarecer", "mensagem": message}

    def remember_list(self, data: dict, session_id: str | None) -> None:
        if session_id:
            ctx = self.contexts.get(session_id)
            with ctx.lock:
                ctx.last_list = data["nome_exibicao"]
                ctx.awaiting = None; ctx.slot = None

    def confirm(self, token: str, session_id: str | None = None) -> dict[str, Any]:
        kind = self.store.pending_kind(token)
        if kind == "add":
            data = self.store.confirm_add(token)
            count = len(data["adicionados"])
            message = (f"Tudo certo. Adicionei {count} {'item' if count == 1 else 'itens'} em “{data['nome_exibicao']}”." if count else f"Esses itens já estavam em “{data['nome_exibicao']}”. Não dupliquei entradas.")
        elif kind == "change":
            data = self.store.confirm_change(token)
            texts = {"criar_lista": "Lista criada", "renomear_lista": "Nome atualizado", "remover_item": "Itens removidos", "concluir_item": "Itens marcados como concluídos", "reabrir_item": "Itens marcados como pendentes"}
            message = f"{texts[data['operacao']]}. Aqui está “{data['nome_exibicao']}”."
        else:
            raise AppError("Essa solicitação não é uma alteração de lista.", 409)
        self.remember_list(data, session_id)
        if session_id:
            ctx = self.contexts.get(session_id)
            with ctx.lock:
                if token in ctx.tokens:
                    ctx.tokens.remove(token)
        return {"estado": "respondido", "mensagem": message, "lista": data}

    def reset(self, session_id: str | None) -> None:
        ctx = self.contexts.clear(session_id)
        if ctx:
            with ctx.lock:
                for token in ctx.tokens:
                    try: self.store.cancel(token)
                    except AppError: pass

    def choose_weather(self, token: str, index: int) -> dict[str, Any]:
        location = self.store.consume_location(token, index)
        data = self.weather.current(location)
        return {"estado": "respondido", "mensagem":
                f"{data['local']}: {data['temperatura_c']:g} °C, sensação de {data['sensacao_c']:g} °C. "
                f"Referência: {data['horario']} ({data['fuso']}). Fonte: Open-Meteo; dados de modelo meteorológico.", "clima": data}
