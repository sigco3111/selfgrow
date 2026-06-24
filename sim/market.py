"""시장 시스템 — 지정가 주문장, 자동 체결, 가격 지수."""

from __future__ import annotations

import bisect
import random
from collections import deque
from dataclasses import dataclass, field
from typing import Optional

from . import config


@dataclass
class Order:
    """시장 주문."""
    order_id: int
    entity_id: int
    resource_type: str
    quantity: float
    price: float          # 단위 가격
    is_buy: bool          # True: 매수, False: 매도
    age: int = 0

    @property
    def total_value(self) -> float:
        return self.quantity * self.price


@dataclass
class TradeRecord:
    """체결된 거래 기록."""
    tick: int
    resource_type: str
    quantity: float
    price: float
    buyer_id: int
    seller_id: int
    tax: float = 0.0


class Market:
    """중앙 시장 — 주문장 + 가격 발견."""

    def __init__(self, rng: random.Random | None = None):
        self._rng = rng
        self._next_order_id = 0
        self.buy_orders: list[Order] = []   # 매수 주문 (가격 내림차순)
        self.sell_orders: list[Order] = []  # 매도 주문 (가격 오름차순)
        self.trade_history: deque[TradeRecord] = deque(maxlen=config.TRADE_HISTORY_MAXLEN)
        self.price_history: dict[str, deque[float]] = {
            r: deque(maxlen=config.PRICE_HISTORY_LENGTH)
            for r in ["food", "wood", "stone", "iron", "gold"]
        }
        self.tick = 0

        # 초기 가격 시드
        for rtype, price in config.BASE_PRICES.items():
            self.price_history[rtype].append(price)

    def place_order(self, seller_id: int, resource_type: str,
                    quantity: float, price: float, is_buy: bool) -> Order:
        """주문 등록 후 즉시 체결 시도."""
        order = Order(
            order_id=self._next_order_id,
            entity_id=seller_id,
            resource_type=resource_type,
            quantity=quantity,
            price=price,
            is_buy=is_buy,
        )
        self._next_order_id += 1

        # 즉시 체결 시도
        self._match_order(order)

        # 잔여 수량이 있으면 주문장에 추가
        if order.quantity > 0.01:
            if is_buy:
                idx = bisect.bisect_left(self.buy_orders, -order.price,
                                         key=lambda o: -o.price)
                self.buy_orders.insert(idx, order)
            else:
                idx = bisect.bisect_left(self.sell_orders, order.price,
                                         key=lambda o: o.price)
                self.sell_orders.insert(idx, order)

        return order

    def _match_order(self, new_order: Order) -> None:
        """신규 주문과 기존 주문장을 체결."""
        if new_order.is_buy:
            # 매수: 매도 주문장에서 가장 싼 것부터 체결
            matching = [o for o in self.sell_orders
                        if o.resource_type == new_order.resource_type
                        and o.price <= new_order.price]
            matching.sort(key=lambda o: o.price)
        else:
            # 매도: 매수 주문장에서 가장 비싼 것부터 체결
            matching = [o for o in self.buy_orders
                        if o.resource_type == new_order.resource_type
                        and o.price >= new_order.price]
            matching.sort(key=lambda o: o.price, reverse=True)

        for existing in matching:
            if new_order.quantity <= 0.01:
                break
            if existing.quantity <= 0.01:
                continue

            trade_qty = min(new_order.quantity, existing.quantity)
            trade_price = existing.price  # 먼저 제출된 주문의 가격으로 체결
            tax = trade_qty * trade_price * config.MARKET_TAX_RATE

            # 체결 기록
            record = TradeRecord(
                tick=self.tick,
                resource_type=new_order.resource_type,
                quantity=trade_qty,
                price=trade_price,
                buyer_id=(new_order.entity_id if new_order.is_buy
                          else existing.entity_id),
                seller_id=(new_order.entity_id if not new_order.is_buy
                           else existing.entity_id),
                tax=tax,
            )
            self.trade_history.append(record)

            # 가격 지수 업데이트
            self.price_history[new_order.resource_type].append(trade_price)

            # 수량 차감
            new_order.quantity -= trade_qty
            existing.quantity -= trade_qty

        # 체결 완료된 주문 제거
        self.sell_orders = [o for o in self.sell_orders if o.quantity > 0.01]
        self.buy_orders = [o for o in self.buy_orders if o.quantity > 0.01]

    def tick_update(self) -> None:
        """매 틱: 주문 에이징 + 만료 제거."""
        self.tick += 1
        for order in self.buy_orders + self.sell_orders:
            order.age += 1
        self.buy_orders = [o for o in self.buy_orders if o.age < config.ORDER_EXPIRY]
        self.sell_orders = [o for o in self.sell_orders if o.age < config.ORDER_EXPIRY]

    def get_average_price(self, resource_type: str) -> float:
        """최근 가격 평균. 데이터가 없으면 기본값."""
        history = self.price_history.get(resource_type, deque())
        if not history:
            return config.BASE_PRICES.get(resource_type, 5.0)
        avg = sum(history) / len(history)
        floor = config.PRICE_FLOOR.get(resource_type, 0.5)
        return max(floor, avg)

    def get_last_price(self, resource_type: str) -> float:
        """마지막 체결 가격."""
        history = self.price_history.get(resource_type, deque())
        if not history:
            return self.get_average_price(resource_type)
        return history[-1]

    def trade_volume(self, resource_type: str | None = None) -> float:
        """누적 거래량."""
        if resource_type:
            return sum(t.quantity for t in self.trade_history
                       if t.resource_type == resource_type)
        return sum(t.quantity for t in self.trade_history)

    def total_taxes(self) -> float:
        """누적 세수."""
        return sum(t.tax for t in self.trade_history)

    def market_summary(self) -> dict:
        """시장 상태 요약."""
        prices = {}
        for r in ["food", "wood", "stone", "iron", "gold"]:
            prices[r] = round(self.get_average_price(r), 2)
        return {
            "prices": prices,
            "open_buy_orders": len(self.buy_orders),
            "open_sell_orders": len(self.sell_orders),
            "total_trades": len(self.trade_history),
            "total_volume": round(self.trade_volume(), 1),
            "total_taxes": round(self.total_taxes(), 2),
        }
