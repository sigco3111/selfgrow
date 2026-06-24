"""SmartBrain 메시징 시스템 — 개체 간 구조화된 메시지 교환."""

from __future__ import annotations

from typing import TYPE_CHECKING

from . import config
from .brain_base import BrainMessage

if TYPE_CHECKING:
    from .entity import Entity
    from .world import World


def process_messages(entity: Entity, world: World, brain) -> None:
    """메일박스의 메시지 처리."""
    if not entity.mailbox:
        return
    messages = entity.mailbox.copy()
    entity.mailbox.clear()

    for msg in messages:
        if msg.msg_type == "trade_offer":
            _handle_trade_offer(entity, world, msg, brain)
        elif msg.msg_type == "trade_request":
            _handle_trade_request(entity, world, msg, brain)
        elif msg.msg_type == "trade_counter":
            _handle_trade_counter(entity, world, msg, brain)
        elif msg.msg_type == "alliance_proposal":
            _handle_alliance_proposal(entity, world, msg, brain)
        elif msg.msg_type == "alliance_accepted":
            _handle_alliance_accepted(entity, world, msg, brain)
        elif msg.msg_type == "treaty_proposal":
            _handle_treaty_proposal(entity, world, msg, brain)
        elif msg.msg_type == "warning":
            _handle_warning(entity, msg, brain)


def _handle_trade_offer(entity: Entity, world: World, msg: BrainMessage, brain) -> None:
    resource = msg.data.get("resource", "")
    quantity = msg.data.get("quantity", 0)
    if not resource or quantity <= 0:
        return
    current = entity.inventory.get(resource, 0)
    if current < config.SMART_TRADE_THRESHOLD:
        brain._send(entity, BrainMessage(
            msg_type="trade_accept",
            sender_id=entity.eid,
            target_id=msg.sender_id,
            data={"resource": resource, "quantity": min(quantity, config.SMART_TRADE_THRESHOLD - current)},
        ))


def _handle_trade_request(entity: Entity, world: World, msg: BrainMessage, brain) -> None:
    resource = msg.data.get("resource", "")
    quantity = msg.data.get("quantity", 0)
    if not resource or quantity <= 0:
        return
    current = entity.inventory.get(resource, 0)
    surplus_threshold = config.SMART_SURPLUS_THRESHOLDS.get(resource, config.SMART_SURPLUS_THRESHOLDS["default"])
    surplus = current - surplus_threshold
    if surplus >= quantity:
        brain._send(entity, BrainMessage(
            msg_type="trade_accept",
            sender_id=entity.eid,
            target_id=msg.sender_id,
            data={"resource": resource, "quantity": quantity},
        ))


def _handle_trade_counter(entity: Entity, world: World, msg: BrainMessage, brain) -> None:
    resource = msg.data.get("resource", "")
    quantity = msg.data.get("quantity", 0)
    counter_price = msg.data.get("price", 0)
    if not resource or quantity <= 0:
        return
    current = entity.inventory.get(resource, 0)
    if current >= quantity:
        brain._send(entity, BrainMessage(
            msg_type="trade_accept",
            sender_id=entity.eid,
            target_id=msg.sender_id,
            data={"resource": resource, "quantity": quantity, "price": counter_price},
        ))


def _handle_alliance_proposal(entity: Entity, world: World, msg: BrainMessage, brain) -> None:
    sender_ent = world.entities.get(msg.sender_id)
    if not sender_ent or not sender_ent.alive:
        return
    threat_level = sum(
        1 for e in world.entities.values()
        if e.alive and e != entity
        and e.genome.aggression > 0.6
        and abs(e.x - entity.x) <= 3)
    acceptance = entity.genome.sociability * 0.6 + min(threat_level * 0.1, 0.3)
    if brain._rng.random() < acceptance:
        brain._send(entity, BrainMessage(
            msg_type="alliance_accepted",
            sender_id=entity.eid,
            target_id=msg.sender_id,
            data={},
        ))


def _handle_alliance_accepted(entity: Entity, world: World, msg: BrainMessage, brain) -> None:
    sender_ent = world.entities.get(msg.sender_id)
    if not sender_ent or not sender_ent.alive:
        return
    if entity.faction_id >= 0 and sender_ent.faction_id >= 0:
        if entity.faction_id == sender_ent.faction_id:
            return
        from .faction import Faction as Fct
        my_faction = world.faction_registry.get(entity.faction_id)
        target_faction = world.faction_registry.get(sender_ent.faction_id)
        if my_faction and target_faction:
            my_faction.propose_treaty(target_faction, "ALLIANCE")


def _handle_treaty_proposal(entity: Entity, world: World, msg: BrainMessage, brain) -> None:
    treaty_type = msg.data.get("treaty", "")
    if treaty_type not in ("TRADE_PACT", "NON_AGGRESSION"):
        return
    sender_ent = world.entities.get(msg.sender_id)
    if not sender_ent or not sender_ent.alive:
        return
    if entity.faction_id >= 0 and sender_ent.faction_id >= 0:
        if entity.faction_id == sender_ent.faction_id:
            return
    acceptance = entity.genome.sociability * 0.5
    if brain._rng.random() < acceptance:
        if entity.faction_id >= 0 and sender_ent.faction_id >= 0:
            from .faction import Faction as Fct
            my_faction = world.faction_registry.get(entity.faction_id)
            target_faction = world.faction_registry.get(sender_ent.faction_id)
            if my_faction and target_faction:
                my_faction.propose_treaty(target_faction, treaty_type)
        brain._send(entity, BrainMessage(
            msg_type="treaty_accepted",
            sender_id=entity.eid,
            target_id=msg.sender_id,
            data={"treaty": treaty_type},
        ))


def _handle_warning(entity: Entity, msg: BrainMessage, brain) -> None:
    danger_x = msg.data.get("x", entity.x)
    danger_y = msg.data.get("y", entity.y)
    dist = abs(entity.x - danger_x) + abs(entity.y - danger_y)
    if dist <= 2:
        if not hasattr(brain, '_danger_level'):
            brain._danger_level = 0
        brain._danger_level = min(brain._danger_level + 1, 5)
        brain._danger_origin = (danger_x, danger_y)


def send_trade_offer(entity: Entity, world: World, target_id: int,
                     resource: str, quantity: float, brain) -> None:
    brain._send(entity, BrainMessage(
        msg_type="trade_offer",
        sender_id=entity.eid,
        target_id=target_id,
        data={"resource": resource, "quantity": quantity},
    ))


def send_trade_request(entity: Entity, world: World, target_id: int,
                       resource: str, quantity: float, brain) -> None:
    brain._send(entity, BrainMessage(
        msg_type="trade_request",
        sender_id=entity.eid,
        target_id=target_id,
        data={"resource": resource, "quantity": quantity},
    ))


def send_trade_counter(entity: Entity, world: World, target_id: int,
                       resource: str, quantity: float, price: float, brain) -> None:
    brain._send(entity, BrainMessage(
        msg_type="trade_counter",
        sender_id=entity.eid,
        target_id=target_id,
        data={"resource": resource, "quantity": quantity, "price": price},
    ))


def send_alliance_proposal(entity: Entity, world: World, target_id: int, brain) -> None:
    brain._send(entity, BrainMessage(
        msg_type="alliance_proposal",
        sender_id=entity.eid,
        target_id=target_id,
        data={},
    ))


def send_treaty_proposal(entity: Entity, world: World, target_id: int,
                         treaty_type: str, brain) -> None:
    brain._send(entity, BrainMessage(
        msg_type="treaty_proposal",
        sender_id=entity.eid,
        target_id=target_id,
        data={"treaty": treaty_type},
    ))


def send_trade_pact_proposal(entity: Entity, world: World, target_id: int, brain) -> None:
    send_treaty_proposal(entity, world, target_id, "TRADE_PACT", brain)


def send_non_aggression_proposal(entity: Entity, world: World, target_id: int, brain) -> None:
    send_treaty_proposal(entity, world, target_id, "NON_AGGRESSION", brain)