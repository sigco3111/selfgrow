"""시뮬레이션 저장/로드 — JSON 기반 직렬화/역직렬화."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

from . import config
from .entity import CurrencyType, Entity, EntityState
from .faction import Faction
from .genome import Genome
from .knowledge import KnowledgeBook, TechnologyTree
from .market import Market
from .metrics import MetricsCollector
from .resource import Biome, Tile
from .world import World

if TYPE_CHECKING:
    from .engine import SimulationEngine


# ── 개체 직렬화 ──────────────────────────────

def _serialize_entity(e: Entity) -> dict:
    return {
        "eid": e.eid, "x": e.x, "y": e.y, "name": e.name,
        "energy": e.energy, "max_energy": e.max_energy,
        "age": e.age, "max_age": e.max_age, "alive": e.alive,
        "attack": e.attack, "defense": e.defense,
        "inventory": dict(e.inventory),
        "max_inventory_slots": e.max_inventory_slots,
        "equipped": list(e.equipped),
        "knowledge_known": sorted(e.knowledge.known),
        "reproduction_cooldown": e.reproduction_cooldown,
        "children_count": e.children_count,
        "kill_count": e.kill_count, "faction_id": e.faction_id,
        "currency": e.currency.value, "money": e.money,
        "home_x": e.home_x, "home_y": e.home_y,
        "ideology": e.ideology,
        "buildings": list(e.buildings),
        "last_action": e.last_action,
        "genome": {
            "risk_tolerance": e.genome.risk_tolerance,
            "specialization": e.genome.specialization,
            "curiosity": e.genome.curiosity,
            "sociability": e.genome.sociability,
            "aggression": e.genome.aggression,
            "industry": e.genome.industry,
            "innovation_rate": e.genome.innovation_rate,
            "strength": e.genome.strength,
            "endurance": e.genome.endurance,
            "speed": e.genome.speed,
            "fertility": e.genome.fertility,
            "loyalty": e.genome.loyalty,
            "generation": e.genome.generation,
        },
        "residence_counter": {f"{k[0]},{k[1]}": v
                               for k, v in e.residence_counter.items()},
        "visited_tiles": [f"{x},{y}" for x, y in e.visited_tiles],
        "brain_type": type(e.brain).__name__,
    }


def _deserialize_entity(data: dict, rng) -> Entity:
    g = data["genome"]
    genome = Genome(
        risk_tolerance=g["risk_tolerance"],
        specialization=g["specialization"],
        curiosity=g["curiosity"],
        sociability=g["sociability"],
        aggression=g["aggression"],
        industry=g["industry"],
        innovation_rate=g["innovation_rate"],
        strength=g["strength"],
        endurance=g["endurance"],
        speed=g["speed"],
        fertility=g["fertility"],
        loyalty=g["loyalty"],
        generation=g["generation"],
    )
    e = Entity(data["x"], data["y"], genome=genome, name=data["name"],
               rng=rng, entity_id=data["eid"])
    e.energy = data["energy"]
    e.max_energy = data["max_energy"]
    e.age = data["age"]
    e.max_age = data["max_age"]
    e.alive = data["alive"]
    e.attack = data["attack"]
    e.defense = data["defense"]
    e.inventory = dict(data["inventory"])
    e.max_inventory_slots = data["max_inventory_slots"]
    e.equipped = list(data["equipped"])
    e.knowledge = KnowledgeBook()
    for tech in data["knowledge_known"]:
        e.knowledge.learn(tech)
    e.reproduction_cooldown = data["reproduction_cooldown"]
    e.children_count = data["children_count"]
    e.kill_count = data["kill_count"]
    e.faction_id = data["faction_id"]
    e.currency = CurrencyType(data["currency"])
    e.money = data["money"]
    e.home_x = data.get("home_x")
    e.home_y = data.get("home_y")
    e.ideology = data.get("ideology", "none")
    e.buildings = list(data.get("buildings", []))
    e.last_action = data.get("last_action", "idle")
    rc = data.get("residence_counter", {})
    e.residence_counter = {(int(k.split(",")[0]), int(k.split(",")[1])): v
                            for k, v in rc.items()}
    vt = data.get("visited_tiles", [])
    from collections import deque
    e.visited_tiles = deque(
        [(int(s.split(",")[0]), int(s.split(",")[1])) for s in vt],
        maxlen=config.HOME_SITE_MEMORY,
    )
    return e


# ── 파벌 직렬화 ──────────────────────────────

def _serialize_faction(f: Faction) -> dict:
    return {
        "faction_id": f.faction_id, "name": f.name,
        "leader_id": f.leader_id,
        "members": sorted(f.members),
        "formation_tick": f.formation_tick,
        "territory": [list(t) for t in sorted(f.territory)],
        "wars": dict(f.wars),
        "diplomacy": dict(f.diplomacy),
        "total_kills": f.total_kills,
        "total_losses": f.total_losses,
    }


def _deserialize_faction(data: dict, world: World) -> Faction:
    Faction._next_faction_id = max(Faction._next_faction_id,
                                    data["faction_id"] + 1)
    f = Faction.__new__(Faction)
    f.faction_id = data["faction_id"]
    f.name = data["name"]
    f.leader_id = data["leader_id"]
    f.members = set(data["members"])
    f.formation_tick = data["formation_tick"]
    f.territory = {tuple(t) for t in data["territory"]}
    f.wars = {int(k): v for k, v in data.get("wars", {}).items()}
    f.diplomacy = {int(k): v for k, v in data.get("diplomacy", {}).items()}
    f.total_kills = data.get("total_kills", 0)
    f.total_losses = data.get("total_losses", 0)
    f.wealth_history = []
    from .faction import FACTION_COLORS
    f.color = FACTION_COLORS[f.faction_id % len(FACTION_COLORS)]
    world.faction_registry[f.faction_id] = f
    return f


# ── 타일 직렬화 ──────────────────────────────

def _serialize_tile(t: Tile) -> dict:
    return {
        "biome": t.biome.value,
        "resources": dict(t.resources),
    }


# ── 시장 직렬화 ──────────────────────────────

def _serialize_market(m: Market) -> dict:
    from .market import Order
    return {
        "tick": m.tick,
        "next_order_id": m._next_order_id,
        "buy_orders": [
            {"entity_id": o.entity_id, "resource_type": o.resource_type,
             "quantity": o.quantity, "price": o.price, "age": o.age}
            for o in m.buy_orders
        ],
        "sell_orders": [
            {"entity_id": o.entity_id, "resource_type": o.resource_type,
             "quantity": o.quantity, "price": o.price, "age": o.age}
            for o in m.sell_orders
        ],
        "price_history": {
            k: list(v) for k, v in m.price_history.items()
        },
    }


def _deserialize_market(data: dict, rng) -> Market:
    from .market import Order
    m = Market(rng=rng)
    m.tick = data["tick"]
    m._next_order_id = data["next_order_id"]
    for od in data["buy_orders"]:
        o = Order(order_id=m._next_order_id, entity_id=od["entity_id"],
                  resource_type=od["resource_type"], quantity=od["quantity"],
                  price=od["price"], is_buy=True, age=od["age"])
        m._next_order_id += 1
        m.buy_orders.append(o)
    for od in data["sell_orders"]:
        o = Order(order_id=m._next_order_id, entity_id=od["entity_id"],
                  resource_type=od["resource_type"], quantity=od["quantity"],
                  price=od["price"], is_buy=False, age=od["age"])
        m._next_order_id += 1
        m.sell_orders.append(o)
    for k, v in data.get("price_history", {}).items():
        if k in m.price_history:
            m.price_history[k] = __import__("collections").deque(
                v, maxlen=config.PRICE_HISTORY_LENGTH)
    return m


# ── 기술 트리 직렬화 ──────────────────────────

def _serialize_tech_tree(tt: TechnologyTree) -> dict:
    return {
        name: {"discovered": t.discovered, "research_progress": t.research_progress}
        for name, t in tt.techs.items()
    }


def _deserialize_tech_tree(data: dict, tt: TechnologyTree) -> None:
    for name, info in data.items():
        if name in tt.techs:
            tt.techs[name].discovered = info["discovered"]
            tt.techs[name].research_progress = info["research_progress"]


# ── 메인 저장/로드 ────────────────────────────

def save_game(engine: SimulationEngine, path: str) -> None:
    """엔진 전체 상태를 JSON 파일로 저장."""
    state = {
        "version": 1,
        "seed": engine._seed,
        "tick": engine.world.tick,
        "tick_count": engine.tick_count,
        "next_entity_id": engine.world._next_entity_id,
        "discovered_techs": sorted(engine._discovered_techs),
        "global_research_points": dict(engine._global_research_points),
        "world_width": engine.world.width,
        "world_height": engine.world.height,
        "tile_claims": {
            f"{x},{y}": {"entity_id": eid, "tick": t}
            for (x, y), (eid, t) in engine.world.tile_claims.items()
        },
        "entities": [
            _serialize_entity(e)
            for e in engine.world.entities.values()
        ],
        "factions": [
            _serialize_faction(f)
            for f in engine.world.faction_registry.values()
        ],
        "market": _serialize_market(engine.market),
        "tech_tree": _serialize_tech_tree(engine.tech_tree),
        "tiles": [
            [_serialize_tile(engine.world.tiles[y][x])
             for x in range(engine.world.width)]
            for y in range(engine.world.height)
        ],
    }
    state["trade_network"] = {
        "routes": [
            {
                "faction_a_id": r.faction_a_id,
                "faction_b_id": r.faction_b_id,
                "established_tick": r.established_tick,
                "volume": r.volume,
                "efficiency": r.efficiency,
            }
            for r in engine.trade_network.routes.values()
        ],
        "agreements": [
            {
                "faction_a_id": a.faction_a_id,
                "faction_b_id": a.faction_b_id,
                "created_tick": a.created_tick,
                "duration": a.duration,
                "tax_discount": a.tax_discount,
            }
            for a in engine.trade_network.agreements.values()
        ],
        "_next_route_id": engine.trade_network._next_route_id,
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)


def load_game(path: str) -> SimulationEngine:
    """JSON 파일에서 엔진 전체 상태를 복원."""
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    seed = data["seed"]
    engine_rng = config.create_rng(seed, "engine")
    world_rng = config.create_rng(seed, "world")
    market_rng = config.create_rng(seed, "market")
    event_rng = config.create_rng(seed, "events")
    entity_rng = config.create_rng(seed, "entity")
    brain_rng = config.create_rng(seed, "brain")

    world = World(seed=seed, rng=world_rng)

    for y in range(world.height):
        for x in range(world.width):
            td = data["tiles"][y][x]
            tile = world.tiles[y][x]
            tile.biome = Biome(td["biome"])
            tile.resources = dict(td["resources"])

    world.tick = data["tick"]
    world._next_entity_id = data["next_entity_id"]

    for ed in data["entities"]:
        entity = _deserialize_entity(ed, entity_rng)
        from .brain import create_brain
        entity.brain = create_brain(entity, world, rng=brain_rng)
        world.entities[entity.eid] = entity
        world._index_position(entity.eid, entity.x, entity.y)

    for fd in data["factions"]:
        _deserialize_faction(fd, world)

    for claim_str, claim_data in data.get("tile_claims", {}).items():
        x, y = claim_str.split(",")
        world.tile_claims[(int(x), int(y))] = (
            claim_data["entity_id"], claim_data["tick"])

    market = _deserialize_market(data["market"], market_rng)

    tech_tree = TechnologyTree()
    _deserialize_tech_tree(data.get("tech_tree", {}), tech_tree)

    from .engine import SimulationEngine
    engine = object.__new__(SimulationEngine)
    engine._seed = seed
    engine._rng = engine_rng
    engine.world = world
    engine.market = market
    engine._event_rng = event_rng
    tn_data = data.get("trade_network", {})
    engine.trade_network = __import__(
        "sim.trade_network", fromlist=["get_trade_network"]
    ).get_trade_network()
    for rd in tn_data.get("routes", []):
        from .trade_network import TradeRoute
        route = TradeRoute(
            faction_a_id=rd["faction_a_id"],
            faction_b_id=rd["faction_b_id"],
            established_tick=rd["established_tick"],
            volume=rd.get("volume", 0.0),
            efficiency=rd.get("efficiency", 1.0),
        )
        engine.trade_network.routes[route.key] = route
    for ad in tn_data.get("agreements", []):
        from .trade_network import TradeAgreement
        agreement = TradeAgreement(
            faction_a_id=ad["faction_a_id"],
            faction_b_id=ad["faction_b_id"],
            created_tick=ad["created_tick"],
            duration=ad.get("duration", 200),
            tax_discount=ad.get("tax_discount", 0.3),
        )
        engine.trade_network.agreements[agreement.key] = agreement
    engine.trade_network._next_route_id = tn_data.get("_next_route_id", 0)
    engine.tech_tree = tech_tree
    engine.metrics = MetricsCollector()
    engine.running = False
    engine.tick_count = data["tick_count"]
    engine.event_log = __import__("collections").deque(maxlen=10000)
    engine._global_research_points = data.get("global_research_points", {})
    engine._discovered_techs = set(data.get("discovered_techs", []))

    for entity in world.entities.values():
        entity.apply_knowledge_effects()

    return engine
