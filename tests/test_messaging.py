"""메시징 시스템 단위 테스트."""

from __future__ import annotations

from sim.brain import SmartBrain
from sim.entity import Entity
from sim.messaging import process_brain_messages
from sim.world import World


def _make_world_with_smart_entities(n: int = 3) -> tuple[World, list[tuple[int, Entity]]]:
    """SmartBrain을 가진 개체 n마리로 월드 생성. (entity_id, entity) 쌍 리스트 반환."""
    import random
    rng = random.Random(42)
    world = World(seed=42, rng=rng)
    pairs: list[tuple[int, Entity]] = []
    for _ in range(n):
        e = Entity(x=5, y=5, rng=rng)
        e.brain = SmartBrain(rng=rng)
        eid = world.spawn_entity(e)
        pairs.append((eid, e))
    return world, pairs


def test_process_brain_messages_empty():
    """outbox가 비어있으면 mailbox에 메시지 추가 안 됨."""
    world, pairs = _make_world_with_smart_entities(2)
    process_brain_messages(world)
    for _, e in pairs:
        assert len(e.mailbox) == 0


def test_process_brain_messages_delivers():
    """outbox 메시지가 대상 mailbox로 배달됨."""
    world, pairs = _make_world_with_smart_entities(3)
    sender_eid, sender = pairs[0]
    target_eid, target = pairs[1]
    sender.brain.outbox.append(
        type("Msg", (), {
            "target_id": target_eid,
            "msg_type": "trade_offer",
            "data": {"resource": "food"},
        })()
    )
    process_brain_messages(world)
    assert len(target.mailbox) == 1
    assert target.mailbox[0].msg_type == "trade_offer"
    assert len(sender.brain.outbox) == 0


def test_process_brain_messages_ignores_dead():
    """dead 개체의 outbox는 무시됨."""
    world, pairs = _make_world_with_smart_entities(2)
    sender_eid, sender = pairs[0]
    target_eid, target = pairs[1]
    target.alive = False
    sender.brain.outbox.append(
        type("Msg", (), {"target_id": target_eid, "msg_type": "trade", "data": {}})()
    )
    process_brain_messages(world)
    assert len(sender.brain.outbox) == 0  # cleared regardless


def test_process_brain_messages_ignores_invalid_target():
    """존재하지 않는 대상 ID는 무시됨."""
    world, pairs = _make_world_with_smart_entities(2)
    sender_eid, sender = pairs[0]
    sender.brain.outbox.append(
        type("Msg", (), {"target_id": 9999, "msg_type": "trade", "data": {}})()
    )
    process_brain_messages(world)
    assert len(sender.brain.outbox) == 0
