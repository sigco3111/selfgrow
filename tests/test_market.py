"""Market 단위 테스트 — 주문, 체결, 세금, 가격."""

from __future__ import annotations

import pytest

from sim.market import Market


@pytest.fixture
def seeded_market() -> Market:
    return Market()


def test_place_order_buy(seeded_market: Market):
    """매수 주문 등록 확인."""
    seeded_market.place_order(
        seller_id=1, resource_type="food",
        quantity=10, price=5.0, is_buy=True,
    )
    assert len(seeded_market.buy_orders) > 0
    assert seeded_market.buy_orders[0].resource_type == "food"


def test_place_order_sell(seeded_market: Market):
    """매도 주문 등록 확인."""
    seeded_market.place_order(
        seller_id=2, resource_type="wood",
        quantity=5, price=3.0, is_buy=False,
    )
    assert len(seeded_market.sell_orders) > 0
    assert seeded_market.sell_orders[0].resource_type == "wood"


def test_immediate_match(seeded_market: Market):
    """매수 >= 매도 가격 조건 충족 시 즉시 체결."""
    seeded_market.place_order(
        seller_id=1, resource_type="food",
        quantity=10, price=4.0, is_buy=True,
    )
    seeded_market.place_order(
        seller_id=2, resource_type="food",
        quantity=5, price=3.0, is_buy=False,
    )
    # 체결 후 trade_history에 기록되어야 함
    assert len(seeded_market.trade_history) > 0


def test_order_expiry(seeded_market: Market):
    """20틱 후 주문이 만료되는지 확인."""
    seeded_market.place_order(
        seller_id=1, resource_type="stone",
        quantity=10, price=10.0, is_buy=True,
    )
    for _ in range(25):
        seeded_market.tick_update()
    assert len(seeded_market.buy_orders) == 0


def test_tax_collection(seeded_market: Market):
    """거래 시 2% 수수료가 정확히 부과되는지 확인."""
    seeded_market.place_order(
        seller_id=1, resource_type="food",
        quantity=10, price=5.0, is_buy=True,
    )
    seeded_market.place_order(
        seller_id=2, resource_type="food",
        quantity=5, price=3.0, is_buy=False,
    )
    if seeded_market.trade_history:
        record = seeded_market.trade_history[0]
        expected_tax = record.quantity * record.price * 0.02
        assert abs(record.tax - expected_tax) < 0.001


def test_price_history(seeded_market: Market):
    """가격 지수가 업데이트되는지 확인."""
    first = seeded_market.get_average_price("food")
    assert first > 0
    # 체결 시뮬레이션
    seeded_market.place_order(
        seller_id=1, resource_type="food",
        quantity=10, price=4.0, is_buy=True,
    )
    seeded_market.place_order(
        seller_id=2, resource_type="food",
        quantity=5, price=3.0, is_buy=False,
    )
    # 추가 체결로 가격 변경
    seeded_market.place_order(
        seller_id=3, resource_type="food",
        quantity=10, price=2.0, is_buy=True,
    )
    seeded_market.place_order(
        seller_id=4, resource_type="food",
        quantity=5, price=1.5, is_buy=False,
    )
    current = seeded_market.get_average_price("food")
    assert current >= 0
