"""개체 행동 구현 — 탐험, 채집, 소비, 거래."""

from __future__ import annotations

from typing import TYPE_CHECKING

from . import config
from .market import Market

if TYPE_CHECKING:
    from .entity import Entity, EntityState
    from .world import World


def do_explore(entity: Entity, world: World) -> list[dict]:
    """이웃 타일로 이동. 항해술(sailing) 보유 시 물 타일 통과 및 추가 이동."""
    effects = entity.get_combined_effects()
    can_cross_water = effects.get("cross_water", 0) >= 1
    explore_range = int(effects.get("explore_range", 0))

    neighbors = world.get_neighbors(entity.x, entity.y, filter_traversable=not can_cross_water)
    if not neighbors:
        return []

    if entity.genome.curiosity > 0.6 and len(neighbors) > 2:
        unvisited = [n for n in neighbors if n not in entity.visited_tiles]
        if unvisited:
            nx, ny = entity._rng.choice(unvisited)
            world.move_entity(entity.eid, nx, ny)
            if explore_range > 0 and entity._rng.random() < 0.3:
                extended = world.get_neighbors(nx, ny, filter_traversable=not can_cross_water)
                if extended:
                    ex, ey = entity._rng.choice(extended)
                    world.move_entity(entity.eid, ex, ey)
            return [entity._event("move", {"to": (entity.x, entity.y)})]

    nx, ny = entity._rng.choice(neighbors)
    world.move_entity(entity.eid, nx, ny)
    return [entity._event("move", {"to": (nx, ny)})]


def do_gather(entity: Entity, world: World) -> tuple[list[dict], float]:
    """현재 타일에서 자원 채취."""
    events = []
    total_gathered = 0.0
    tile = world.tile_at(entity.x, entity.y)
    if not tile:
        return events, 0.0

    effects = entity.get_combined_effects()
    max_food_storage = effects.get("max_food_storage", 0.0)

    # 특화에 따라 선호 자원 결정
    pref = entity.genome.specialization
    gather_order = ["food", "wood", "stone", "iron", "gold"]

    if pref == "farmer":
        gather_order = ["food", "wood", "stone", "iron", "gold"]
    elif pref == "miner":
        gather_order = ["stone", "iron", "gold", "wood", "food"]

    for rtype in gather_order:
        if entity.inventory_is_full:
            break
        amount = entity.inventory.get(rtype, 0)
        max_slot = config.RESOURCE_MAX_STACK
        if rtype == "food" and max_food_storage > 0:
            max_slot += int(max_food_storage)
        if amount >= max_slot:
            continue

        season_gather = getattr(entity, "_season_gather_mult", 1.0)
        can_gather = config.BASE_GATHER_RATE * entity.get_gather_bonus(rtype) * season_gather
        gathered = tile.gather(rtype, can_gather)
        if gathered > 0:
            entity.inventory[rtype] = entity.inventory.get(rtype, 0) + gathered
            total_gathered += gathered
            events.append(entity._event("gather", {
                "resource": rtype, "amount": round(gathered, 2)
            }))
        if entity.inventory_is_full:
            break

    # ── 화폐 시스템 활성화 (currency 기술 필요) ──
    if total_gathered > 0 and entity.knowledge.know(config.CURRENCY_ACTIVATION_TECH):
        from .entity import CurrencyType
        if entity.currency == CurrencyType.NONE:
            entity.currency = CurrencyType.SHELL
            events.append(entity._event("currency_activate", {"type": "shell"}))
        if entity.currency == CurrencyType.SHELL:
            shell_income = total_gathered * config.CURRENCY_SHELL_GATHER_RATE
            entity.money += shell_income
            if entity.money >= config.CURRENCY_SHELL_TO_COIN_THRESHOLD:
                entity.currency = CurrencyType.COIN
                events.append(entity._event("currency_upgrade", {"type": "coin"}))

    return events, total_gathered


def do_consume(entity: Entity) -> list[dict]:
    """식량을 소비해 에너지 회복."""
    food = entity.inventory.get("food", 0)
    if food <= 0:
        return []

    effects = entity.get_combined_effects()
    food_energy_mult = effects.get("food_energy_mult", 1.0)

    consume = min(food, config.CONSUME_FOOD_AMOUNT)
    entity.inventory["food"] = food - consume
    gained = consume * config.FOOD_ENERGY * food_energy_mult
    entity.energy = min(entity.max_energy, entity.energy + gained)
    return [entity._event("consume", {"food": consume, "energy_gained": gained})]


def do_trade(entity: Entity, world: World, market: Market) -> list[dict]:
    """시장에 매도 주문 등록 및 주변 개체와 직거래."""
    events = []
    effects = []
    effects = entity.get_combined_effects()
    trade_efficiency = effects.get("trade_efficiency", 0.0)
    trade_gold_bonus = effects.get("trade_gold_bonus", 0.0)
    market_tax_discount = effects.get("market_tax_discount", 0.0)
    coin_bonus = config.CURRENCY_COIN_TRADE_BONUS if entity.currency.value == "coin" else 0.0

    # 1. 팔 surplus 자원: 매도 주문 등록
    for rtype, amount in list(entity.inventory.items()):
        surplus_threshold = config.TRADE_SURPLUS_THRESHOLD.get(rtype, config.TRADE_SURPLUS_THRESHOLD["default"])
        if amount > surplus_threshold:
            sell_qty = amount * config.TRADE_SELL_RATIO
            price_mult = 0.85 + 0.3 * entity.genome.sociability + trade_efficiency * 0.3 + coin_bonus
            unit_price = market.get_average_price(rtype) * price_mult
            if rtype == "gold" and trade_gold_bonus > 0:
                unit_price *= 1.0 + trade_gold_bonus

            market.place_order(
                seller_id=entity.eid,
                resource_type=rtype,
                quantity=sell_qty,
                price=unit_price,
                is_buy=False,
            )
            events.append(entity._event("trade_offer", {
                "sell": rtype, "qty": round(sell_qty, 1), "unit_price": round(unit_price, 2)
            }))

    # 2. 살 자원: 부족한 자원 매수
    for rtype in ["food", "wood", "stone"]:
        deficit_threshold = config.TRADE_SURPLUS_THRESHOLD.get(rtype, config.TRADE_SURPLUS_THRESHOLD["default"]) - 2
        if entity.inventory.get(rtype, 0) < deficit_threshold:
            buy_qty = 3 - entity.inventory.get(rtype, 0)
            price_mult = 0.85 + 0.3 * entity.genome.sociability + trade_efficiency * 0.3 - coin_bonus * 0.5
            unit_price = market.get_average_price(rtype) * price_mult
            market.place_order(
                seller_id=entity.eid,
                resource_type=rtype,
                quantity=buy_qty,
                price=unit_price,
                is_buy=True,
            )
            events.append(entity._event("trade_bid", {
                "buy": rtype, "qty": round(buy_qty, 1), "unit_price": round(unit_price, 2)
            }))

    return events