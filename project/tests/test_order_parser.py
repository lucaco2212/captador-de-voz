from models.product_catalog import ProductCatalog
from parser.order_parser import OrderParser


def build_parser() -> OrderParser:
    return OrderParser(ProductCatalog.default())


def test_parse_orders_with_aparte_and_plural() -> None:
    parser = build_parser()
    text = "2 cocacolas 3 cereales 1 galleta aparte 5 jugos"
    assert parser.parse_orders(text) == [
        {"cocacola": 2, "cereales": 3, "galletas": 1},
        {"jugos": 5},
    ]


def test_parse_orders_ignores_unknown_tokens() -> None:
    parser = build_parser()
    text = "2 cocacolas foo bar 4 ramitas"
    assert parser.parse_orders(text) == [{"cocacola": 2, "ramitas": 4}]


def test_support_number_words() -> None:
    parser = build_parser()
    text = "dos cocacolas tres cereales"
    assert parser.parse_orders(text) == [{"cocacola": 2, "cereales": 3}]


def test_split_committed_and_pending() -> None:
    parser = build_parser()
    committed, pending = parser.split_committed_and_pending("2 cocacolas aparte 5 jugos")
    assert committed == [{"cocacola": 2}]
    assert pending == "5 jugos"
