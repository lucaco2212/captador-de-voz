"""Catálogo interno de productos FRUNA y utilidades de normalización."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional


@dataclass(frozen=True)
class ProductCatalog:
    """Mantiene precios y normalización de nombres de productos."""

    prices: Dict[str, int]

    @classmethod
    def default(cls) -> "ProductCatalog":
        """Construye el catálogo por defecto solicitado."""
        prices = {
            "cocacola": 800,
            "cereales": 1200,
            "galletas": 600,
            "jugos": 700,
            "chocolates": 500,
            "papas fritas": 900,
            "ramitas": 650,
            "gomitas": 550,
        }
        return cls(prices=prices)

    def normalize_token(self, token: str) -> str:
        """Normaliza un token intentando convertir singular/plural.

        Se prioriza devolver una clave exacta existente en el catálogo.
        """
        clean = token.strip().lower()
        if clean in self.prices:
            return clean

        # singular -> plural común en español
        if f"{clean}s" in self.prices:
            return f"{clean}s"
        if f"{clean}es" in self.prices:
            return f"{clean}es"

        # plural -> singular simple
        if clean.endswith("es") and clean[:-2] in self.prices:
            return clean[:-2]
        if clean.endswith("s") and clean[:-1] in self.prices:
            return clean[:-1]

        # caso especial cocacolas -> cocacola
        if clean.endswith("s") and clean[:-1] in self.prices:
            return clean[:-1]

        return clean

    def resolve_product(self, word1: str, word2: Optional[str] = None) -> Optional[str]:
        """Resuelve producto por 1 o 2 palabras y retorna clave válida o None."""
        candidate_1 = self.normalize_token(word1)
        if candidate_1 in self.prices:
            return candidate_1

        if word2:
            phrase = f"{word1} {word2}".strip().lower()
            candidate_2 = self.normalize_token(phrase)
            if candidate_2 in self.prices:
                return candidate_2

        return None

    def get_price(self, product_name: str) -> int:
        """Obtiene precio unitario para un producto normalizado."""
        return self.prices[product_name]
