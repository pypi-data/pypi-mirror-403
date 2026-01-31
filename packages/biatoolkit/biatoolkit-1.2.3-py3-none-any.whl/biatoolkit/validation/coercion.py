# biatoolkit/validation/coercion.py

from __future__ import annotations

from typing import Any, Iterable, Mapping, Optional
import math


def ensure_list(value: Any) -> list:
    """
    Normaliza um valor para sempre retornar uma lista.

    Regras:
    - None -> []
    - list -> a própria lista
    - tuple/set -> list(value)
    - dict (ou Mapping) -> [value]  (não "explode" dict em chaves)
    - qualquer outro -> [value]

    Por que existe:
    - Muitas APIs retornam ora um item único (dict), ora uma lista.
    - Este helper padroniza o consumo e reduz if/else espalhado.

    Args:
        value: qualquer valor.

    Returns:
        list: lista normalizada.
    """
    if value is None:
        return []

    if isinstance(value, list):
        return value

    if isinstance(value, (tuple, set)):
        return list(value)

    # Dict/Mapping deve ser tratado como item único, não iterável de chaves.
    if isinstance(value, Mapping):
        return [value]

    return [value]


def unwrap_dollar_value(value: Any) -> Any:
    """
    "Desembrulha" valores no formato {"$": "..."} (comum em integrações legadas).

    Exemplo:
        {"$": "123"} -> "123"
        {"$": 123} -> 123

    Se não for dict com a chave "$", retorna o valor original.

    Args:
        value: valor de entrada.

    Returns:
        Any: valor desembrulhado ou original.
    """
    if isinstance(value, dict) and "$" in value:
        return value.get("$")
    return value


def to_int(value: Any, default: int = 0) -> int:
    """
    Converte um valor para int de forma segura.

    Regras:
    - None / "" -> default
    - strings com espaços são aceitas (" 12 ")
    - strings numéricas com sinal são aceitas ("-3")
    - floats numéricos -> int(value) (trunca)
    - NaN/inf -> default

    Obs:
    - Não tenta "extrair número do meio do texto" (isso é responsabilidade
      de parse específico, ex: parse_int_list).

    Args:
        value: valor a converter.
        default: fallback.

    Returns:
        int: convertido ou default.
    """
    try:
        if value is None:
            return default

        if isinstance(value, bool):
            # Evita True->1 / False->0 de forma "surpresa"
            return default

        if isinstance(value, str):
            s = value.strip()
            if s == "":
                return default
            return int(s)

        if isinstance(value, float):
            if math.isnan(value) or math.isinf(value):
                return default
            return int(value)

        return int(value)
    except (TypeError, ValueError):
        return default


def to_float(value: Any, default: float = 0.0) -> float:
    """
    Converte um valor para float de forma segura.

    Regras:
    - None / "" -> default
    - aceita strings com vírgula decimal ("12,34")
    - NaN/inf -> default

    Args:
        value: valor a converter.
        default: fallback.

    Returns:
        float: convertido ou default.
    """
    try:
        if value is None:
            return default

        if isinstance(value, bool):
            return default

        if isinstance(value, str):
            s = value.strip()
            if s == "":
                return default
            s = s.replace(",", ".")
            v = float(s)
        else:
            v = float(value)

        if math.isnan(v) or math.isinf(v):
            return default

        return v
    except (TypeError, ValueError):
        return default




# Classe fachada para coerção
class BiaCoercion:
    """
    Fachada estática para funções de coerção do Bia Toolkit.
    Permite referenciar e utilizar as utilidades de coerção de forma padronizada.
    """
    @staticmethod
    def ensure_list(*args, **kwargs):
        return ensure_list(*args, **kwargs)

    @staticmethod
    def unwrap_dollar_value(*args, **kwargs):
        return unwrap_dollar_value(*args, **kwargs)

    @staticmethod
    def to_int(*args, **kwargs):
        return to_int(*args, **kwargs)

    @staticmethod
    def to_float(*args, **kwargs):
        return to_float(*args, **kwargs)
