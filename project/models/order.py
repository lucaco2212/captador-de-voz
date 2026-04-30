"""Modelo de datos para una boleta/pedido."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict

from models.product_catalog import ProductCatalog


@dataclass
class Order:
    """Representa una boleta con ítems, subtotales y total."""

    items: Dict[str, int]
    catalog: ProductCatalog
    created_at: datetime = field(default_factory=datetime.now)

    def __post_init__(self) -> None:
        """Elimina ítems inválidos o con cantidad no positiva."""
        self.items = {key: qty for key, qty in self.items.items() if qty > 0}

    @property
    def subtotal_por_producto(self) -> Dict[str, int]:
        """Retorna subtotal por producto (precio * cantidad)."""
        return {
            product: self.catalog.get_price(product) * quantity
            for product, quantity in self.items.items()
        }

    @property
    def total_final(self) -> int:
        """Retorna suma de subtotales."""
        return sum(self.subtotal_por_producto.values())
