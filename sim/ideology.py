"""이데올로기 시스템 — 개체 집단 내 가치관 분화 (Phase 3.1)."""

from __future__ import annotations

import random
from collections import Counter
from typing import TYPE_CHECKING, Optional

from . import config

if TYPE_CHECKING:
    from .entity import Entity
    from .world import World


def determine_ideology(entity: Entity) -> str:
    """개체의 유전자 형질에 가장 적합한 이데올로기 결정."""
    scores: dict[str, float] = {}
    for ideo_name, ideo_data in config.IDEOLOGIES.items():
        score = 0.0
        for trait, bonus in ideo_data["traits"].items():
            value = getattr(entity.genome, trait, 0.0)
            score += value * bonus * 10.0
        scores[ideo_name] = score
    if not scores:
        return "none"
    return max(scores, key=scores.get)


def get_action_bias(entity: Entity) -> dict[str, float]:
    """개체의 이데올로기에 따른 행동 바이어스 반환."""
    if entity.ideology == "none" or entity.ideology not in config.IDEOLOGIES:
        return {}
    return config.IDEOLOGIES[entity.ideology].get("action_bias", {})


def process_ideology(world: World, rng: random.Random) -> list[dict]:
    """이데올로기 형성 및 전파 처리. 이벤트 리스트 반환."""
    events: list[dict] = []
    entities = [e for e in world.entities.values() if e.alive]

    for entity in entities:
        if entity.ideology == "none":
            if entity.age >= config.IDEOLOGY_FORMATION_TICKS:
                entity.ideology = determine_ideology(entity)
                events.append({
                    "type": "ideology_formed",
                    "entity_id": entity.eid,
                    "data": {"ideology": entity.ideology},
                })

    for entity in entities:
        if entity.ideology == "none":
            continue
        effects = entity.get_combined_effects()
        spread_bonus = effects.get("ideology_spread", 0.0)
        conv_chance = config.IDEOLOGY_CONVERSION_CHANCE * (1.0 + spread_bonus)
        radius = config.IDEOLOGY_TRANSFER_RADIUS
        for dx in range(-radius, radius + 1):
            for dy in range(-radius, radius + 1):
                if abs(dx) + abs(dy) > radius:
                    continue
                nx, ny = entity.x + dx, entity.y + dy
                if not (0 <= nx < world.width and 0 <= ny < world.height):
                    continue
                for other_eid, other in world.entity_at(nx, ny):
                    if (other.alive and other.eid != entity.eid
                            and other.ideology != entity.ideology
                            and rng.random() < conv_chance):
                        old = other.ideology
                        other.ideology = entity.ideology
                        events.append({
                            "type": "ideology_conversion",
                            "entity_id": other.eid,
                            "data": {"from": old, "to": entity.ideology},
                        })

    return events


def ideology_summary(world: World) -> dict[str, int]:
    """현재 월드의 이데올로기 분포 반환."""
    counts: Counter[str] = Counter()
    for e in world.entities.values():
        if e.alive and e.ideology != "none":
            counts[e.ideology] += 1
    return dict(counts)


def same_ideology_bonus(entity: Entity, other: Entity) -> float:
    """같은 이데올로기인 경우 협력 보너스, 다른 경우 패널티 반환."""
    if entity.ideology == "none" or other.ideology == "none":
        return 0.0
    if entity.ideology == other.ideology:
        return config.IDEOLOGY_SAME_BONUS
    return -config.IDEOLOGY_DIFFERENT_PENALTY
