# biatoolkit/validation.py

from typing import Any, Iterable
import re


def parse_int_list(
    value: Any,
    *,
    dedupe: bool = True,
    keep_order: bool = True,
) -> list[int]:
    """
    Normaliza um valor arbitrário em uma lista de inteiros.

    Casos suportados:
    - None -> []
    - int -> [int]
    - str -> extrai números (ex: "100, 200" / "SKU=300231 x2")
    - list/tuple -> processa cada item recursivamente

    Comportamento:
    - Ignora valores inválidos
    - Deduplica por padrão
    - Mantém a ordem de aparição por padrão

    Args:
        value: Valor de entrada (None, int, str, list, etc.)
        dedupe: Remove valores duplicados.
        keep_order: Mantém a ordem original dos valores.

    Returns:
        list[int]: Lista normalizada de inteiros.
    """
    if value is None:
        return []

    # Normaliza para iterável
    if isinstance(value, (list, tuple, set)):
        raw: Iterable[Any] = value
    else:
        raw = [value]

    numbers: list[int] = []

    for item in raw:
        if item is None:
            continue

        # Inteiro direto
        if isinstance(item, int):
            numbers.append(item)
            continue

        # String ou outros tipos
        text = str(item)
        matches = re.findall(r"\d+", text)
        for m in matches:
            try:
                numbers.append(int(m))
            except ValueError:
                continue

    if not dedupe:
        return numbers

    if keep_order:
        seen = set()
        ordered: list[int] = []
        for n in numbers:
            if n not in seen:
                seen.add(n)
                ordered.append(n)
        return ordered

    return list(set(numbers))

def sanitize_like(
    value: str,
    *,
    max_len: int = 80,
    upper: bool = True,
) -> str:
    """
    Sanitiza um texto para uso seguro em filtros do tipo LIKE/search.

    Regras aplicadas:
    - Remove caracteres fora de uma allowlist básica
    - Limita o tamanho do texto
    - Escapa aspas simples
    - Escapa curingas comuns (% e _)
    - Converte para UPPER por padrão

    Args:
        value: Texto de entrada.
        max_len: Tamanho máximo permitido.
        upper: Converte o texto final para maiúsculas.

    Returns:
        str: Texto sanitizado.
    """
    if not value:
        return ""

    # Normaliza e corta tamanho
    text = str(value).strip()[:max_len]

    # Allowlist simples (letras, números, acentos, espaço e alguns símbolos, incluindo ', %, _)
    # Mantém ', %, _ para escapá-los depois
    text = re.sub(r"[^0-9A-Za-zÀ-ÿ\s\-\(\)\./'_%]", " ", text)

    # Escapes básicos
    text = text.replace("'", "''")
    text = text.replace("%", r"\%" ).replace("_", r"\_")

    # Normaliza espaços
    text = re.sub(r"\s+", " ", text).strip()


    return text.upper() if upper else text


# Classe fachada para validação
class BiaValidation:
    """
    Fachada estática para funções de validação do Bia Toolkit.
    Permite referenciar e utilizar as utilidades de validação de forma padronizada.
    """
    @staticmethod
    def parse_int_list(*args, **kwargs):
        return parse_int_list(*args, **kwargs)

    @staticmethod
    def sanitize_like(*args, **kwargs):
        return sanitize_like(*args, **kwargs)