import json
from pathlib import Path
from ayla_v2.evaluate import canonical
from ayla_v2.schemas import Comando


def test_dataset_has_unique_ids_and_correct_splits():
    path = Path(__file__).resolve().parents[1] / "evaluation" / "cases.jsonl"
    cases = [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines()]
    assert len(cases) == 80
    assert len({c['id'] for c in cases}) == 80
    assert len({c['texto'] for c in cases}) == 80
    assert sum(c['split'] == 'dev' for c in cases) == 40
    assert sum(c['split'] == 'holdout' for c in cases) == 40
    for case in cases:
        Comando.model_validate(case['esperado'])


def test_metric_accepts_item_order_and_accents_but_not_missing_items():
    one = dict(intencao='adicionar_item',cidade=None,lista='Café da manhã',itens=['pão','café'])
    two = dict(intencao='adicionar_item',cidade=None,lista='cafe da manha',itens=['cafe','pao'])
    assert canonical(one) == canonical(two)
    two['itens'] = ['cafe']
    assert canonical(one) != canonical(two)


def test_metric_includes_new_name_term_and_reference():
    base=dict(intencao='renomear_lista',cidade=None,lista='viagem',itens=[],novo_nome='férias')
    assert canonical(base) != canonical({**base,'novo_nome':'compras'})
    base=dict(intencao='buscar_item',cidade=None,lista=None,itens=[],termo='café')
    assert canonical(base) != canonical({**base,'termo':'pão'})
    base=dict(intencao='adicionar_item',cidade=None,lista=None,itens=['leite'],usar_lista_anterior=True)
    assert canonical(base) != canonical({**base,'usar_lista_anterior':False})
