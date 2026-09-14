"""
Deep merge para herança de templates.

Regra:
  child sobrescreve parent propriedade a propriedade.
  Listas de layers são mergeadas por id: child sobrescreve
  apenas as propriedades do layer que declara.
  Se child declarar layer com "delete": true, ele é removido.
  Se child declarar layer sem id existente no pai, ele é ADICIONADO.
"""
from __future__ import annotations
import copy
from typing import Any


def deep_merge(base: dict, override: dict) -> dict:
    """
    Merge recursivo: override tem prioridade sobre base.
    Listas NÃO são mergeadas — override substitui completamente
    (exceto para 'layers', que tem lógica especial via merge_layers).
    """
    result = copy.deepcopy(base)
    for key, val in override.items():
        if key == "layers":
            result["layers"] = merge_layers(
                result.get("layers", []), val
            )
        elif isinstance(val, dict) and isinstance(result.get(key), dict):
            result[key] = deep_merge(result[key], val)
        else:
            result[key] = copy.deepcopy(val)
    return result


def merge_layers(base_layers: list[dict], override_layers) -> list[dict]:
    """
    Mescla layers da lista base com os overrides do filho.

    override_layers pode ser:
      • lista de dicts  → cada item é mergeado com o layer base de mesmo id
      • dict {id: {...}} → forma de mapa, mais concisa para overrides parciais
    """
    # Normaliza para lista
    if isinstance(override_layers, dict):
        override_list = [{"id": k, **v} for k, v in override_layers.items()]
    else:
        override_list = list(override_layers)

    # Indexa base por id para acesso rápido
    base_map: dict[str, dict] = {}
    base_order: list[str]     = []
    for layer in base_layers:
        lid = layer.get("id", "")
        base_map[lid] = copy.deepcopy(layer)
        base_order.append(lid)

    # Aplica overrides
    added: list[dict] = []
    for ov in override_list:
        lid = ov.get("id", "")
        if ov.get("delete"):
            base_map.pop(lid, None)
            if lid in base_order:
                base_order.remove(lid)
        elif lid in base_map:
            # Merge profundo do layer existente
            base_map[lid] = _merge_layer(base_map[lid], ov)
        else:
            # Layer novo — adiciona ao final
            added.append(copy.deepcopy(ov))

    # Reconstrói a lista na ordem original + novos
    result = [base_map[lid] for lid in base_order if lid in base_map]
    result.extend(added)
    return result


def _merge_layer(base: dict, override: dict) -> dict:
    """Merge de um único layer: suporta 'style' aninhado."""
    result = copy.deepcopy(base)
    for key, val in override.items():
        if key == "style" and isinstance(val, dict) and isinstance(result.get("style"), dict):
            result["style"] = {**result["style"], **val}
        else:
            result[key] = copy.deepcopy(val)
    return result
