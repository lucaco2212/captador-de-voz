"""Parser de texto reconocido a estructuras de pedidos."""

from __future__ import annotations

from typing import Dict, List, Optional, Tuple

from models.product_catalog import ProductCatalog


class OrderParser:
    """Convierte frases en español a bloques de boletas separadas por 'aparte'."""

    NUMBER_WORDS = {
        "un": 1,
        "uno": 1,
        "una": 1,
        "dos": 2,
        "tres": 3,
        "cuatro": 4,
        "cinco": 5,
        "seis": 6,
        "siete": 7,
        "ocho": 8,
        "nueve": 9,
        "diez": 10,
    }

    def __init__(self, catalog: ProductCatalog) -> None:
        self.catalog = catalog

    def _parse_quantity(self, token: str) -> Optional[int]:
        if token.isdigit():
            return int(token)
        return self.NUMBER_WORDS.get(token)

    def _parse_single_order(self, text: str) -> Dict[str, int]:
        """Parsea un bloque sin `aparte` a un solo diccionario de productos."""
        tokens = [token for token in text.lower().strip().split() if token]
        current_order: Dict[str, int] = {}

        i = 0
        while i < len(tokens):
            quantity = self._parse_quantity(tokens[i])
            if quantity is None:
                i += 1
                continue

            if i + 1 >= len(tokens):
                break

            word1 = tokens[i + 1]
            word2 = tokens[i + 2] if i + 2 < len(tokens) else None

            # Intento 2 palabras primero (ej. papas fritas)
            if word2:
                product_two_words = self.catalog.resolve_product(word1, word2)
                if product_two_words and product_two_words == f"{word1} {word2}":
                    current_order[product_two_words] = current_order.get(product_two_words, 0) + quantity
                    i += 3
                    continue

            product_one_word = self.catalog.resolve_product(word1)
            if product_one_word:
                current_order[product_one_word] = current_order.get(product_one_word, 0) + quantity
                i += 2
                continue

            i += 2

        return current_order

    def parse_orders(self, text: str) -> List[Dict[str, int]]:
        """Parsea texto completo y retorna boletas separadas por `aparte`."""
        chunks = [chunk.strip() for chunk in text.lower().split("aparte")]
        orders: List[Dict[str, int]] = []

        for chunk in chunks:
            if not chunk:
                continue
            parsed = self._parse_single_order(chunk)
            if parsed:
                orders.append(parsed)

        return orders

    def split_committed_and_pending(self, text: str) -> Tuple[List[Dict[str, int]], str]:
        """Separa boletas cerradas (si hay `aparte`) y texto pendiente.

        Ejemplo:
        - input: "2 cocacolas aparte 5 jugos"
        - committed: [{"cocacola": 2}]
        - pending_text: "5 jugos"
        """
        normalized = text.lower().strip()
        if "aparte" not in normalized:
            return [], normalized

        chunks = [chunk.strip() for chunk in normalized.split("aparte")]
        committed_chunks = chunks[:-1]
        pending_text = chunks[-1]

        committed_orders: List[Dict[str, int]] = []
        for chunk in committed_chunks:
            parsed = self._parse_single_order(chunk)
            if parsed:
                committed_orders.append(parsed)

        return committed_orders, pending_text
