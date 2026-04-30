from models.order import Order
from models.product_catalog import ProductCatalog
from models.receipt_generator import ReceiptGenerator


def test_receipt_contains_total_and_lines() -> None:
    catalog = ProductCatalog.default()
    order = Order(items={"cocacola": 2, "jugos": 1}, catalog=catalog)
    receipt = ReceiptGenerator.generate_receipt_text(order)

    assert "FRUNA" in receipt
    assert "Cocacola" in receipt
    assert "Jugos" in receipt
    assert "TOTAL: $2300" in receipt


def test_order_filters_non_positive_items() -> None:
    catalog = ProductCatalog.default()
    order = Order(items={"cocacola": 2, "jugos": 0, "ramitas": -1}, catalog=catalog)
    assert order.items == {"cocacola": 2}
