"""문화적 진화 — 인접 개체 간 지식 전수."""

from __future__ import annotations

import random
from typing import TYPE_CHECKING, Callable

if TYPE_CHECKING:
    from .world import World


def cultural_transfer(
    world: World,
    rng: random.Random,
    log_event: Callable[[dict], None],
) -> None:
    """인접 개체 간 지식 전수 (문화적 진화, 공간 인덱스 활용)."""
    for entity in list(world.entities.values()):
        if not entity.alive or entity.genome.sociability < 0.2:
            continue
        for eid, other in world.entities_near(entity.x, entity.y, 1):
            if other is entity or not other.alive:
                continue
            transferred = entity.knowledge.share(
                other.knowledge, entity.genome.sociability,
                rng=rng,
            )
            for tech in transferred:
                log_event({
                    "tick": world.tick,
                    "type": "knowledge_transfer",
                    "entity_id": entity.eid,
                    "entity_name": entity.name,
                    "data": {"from": entity.name, "to": other.name,
                             "tech": tech},
                })
