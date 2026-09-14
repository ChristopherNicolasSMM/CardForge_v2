"""
Associação de template por linha (_template) — usado quando uma coleção tem
mais de um template e o dataset mistura linhas destinadas a templates
diferentes (ex: cartas de combate vs. cartas de personagem na mesma tabela).

Sem isso, Gerar/Proxy aplicavam sempre UM template a TODAS as linhas do
dataset, então gerar com o template "Personagem" também tentava renderizar
as linhas de "Carta de Jogo" (e vice-versa).

Convenção: a coluna reservada `_template` guarda o nome exato do template
dono daquela linha. Coleções com um único template não precisam preencher
essa coluna — o filtro só entra em ação se pelo menos uma linha do dataset
tiver `_template` preenchido (ver `is_in_use`); do contrário o comportamento
antigo (gera o dataset inteiro) é preservado.
"""
from __future__ import annotations

from dataclasses import dataclass, field


FIELD = "_template"


@dataclass
class TemplateAssignment:
    using_field: bool                  # alguma linha do dataset usa _template?
    matching: list[dict] = field(default_factory=list)    # linhas pro template escolhido
    missing: list[dict] = field(default_factory=list)     # _template vazio
    invalid: list[dict] = field(default_factory=list)     # _template aponta pra template inexistente
    missing_labels: list[str] = field(default_factory=list)
    invalid_labels: list[str] = field(default_factory=list)

    @property
    def problem_count(self) -> int:
        return len(self.missing) + len(self.invalid)


def _label(row: dict, index: int, id_field: str) -> str:
    val = row.get(id_field) if id_field else None
    return str(val) if val else f"linha {index + 1}"


def analyze(rows: list[dict], chosen_template: str, valid_templates: list[str],
            id_field: str = "name") -> TemplateAssignment:
    tagged = [r for r in rows if (r.get(FIELD) or "").strip()]
    using_field = len(tagged) > 0

    if not using_field:
        # Coleção de template único (ou ainda não adotou _template) — mantém
        # o comportamento de sempre: o dataset inteiro é o lote.
        return TemplateAssignment(using_field=False, matching=list(rows))

    valid_set = set(valid_templates)
    result = TemplateAssignment(using_field=True)
    for i, row in enumerate(rows):
        val = (row.get(FIELD) or "").strip()
        if val == chosen_template:
            result.matching.append(row)
        elif val == "":
            result.missing.append(row)
            result.missing_labels.append(_label(row, i, id_field))
        elif val not in valid_set:
            result.invalid.append(row)
            result.invalid_labels.append(f"{_label(row, i, id_field)} → “{val}”")
        # else: val é um template diferente e válido — pertence a outro lote,
        # não é problema nenhum, só não entra nesta geração.
    return result
