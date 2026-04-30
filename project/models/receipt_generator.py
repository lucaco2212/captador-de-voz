"""Generador de texto para boletas FRUNA."""

from __future__ import annotations

from models.order import Order


class ReceiptGenerator:
    """Construye representación textual de una boleta FRUNA."""

    @staticmethod
    def _human_name(product_key: str) -> str:
        return product_key.title()

    @classmethod
    def generate_receipt_text(cls, order: Order) -> str:
        lines = ["       FRUNA", "------------------------------", f"Fecha: {order.created_at.strftime('%Y-%m-%d %H:%M')}", "", "Detalle:"]

        subtotals = order.subtotal_por_producto
        for product, quantity in order.items.items():
            subtotal = subtotals[product]
            product_name = cls._human_name(product)
            lines.append(f"{product_name:<16} x{quantity:<3} ${subtotal}")

        lines.append("------------------------------")
        lines.append(f"TOTAL: ${order.total_final}")
        return "\n".join(lines)
