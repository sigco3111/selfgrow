"""생식 및 노화 시스템 — 번식, 돌연변이, 노화."""

from __future__ import annotations

from typing import TYPE_CHECKING

from . import config
from .genome import Genome

if TYPE_CHECKING:
    from .entity import Entity
    from .world import World


def do_reproduce(entity: Entity, world: World) -> list[dict]:
    """자손 생산. 돌연변이 적용."""
    from .entity import Entity  # 순환 참조 방지: 런타임에만 import
    neighbors = world.get_neighbors(entity.x, entity.y)
    if not neighbors:
        return []

    partner = None
    for eid, other in world.entities_near(entity.x, entity.y, 1):
        if (other.alive and other is not entity
                and other.reproduction_cooldown <= 0
                and other.energy / other.max_energy > 0.5):
            partner = other
            break

    if partner is None:
        child_genome = entity.genome.mutate(rng=entity._rng)
    else:
        child_genome = Genome.crossover(entity.genome, partner.genome, rng=entity._rng)
        child_genome = child_genome.mutate(rng=entity._rng)
        partner.reproduction_cooldown = config.REPRODUCTION_COOLDOWN
        partner.children_count += 1
        partner.energy -= config.ENERGY_COST["reproduce"] * 0.5

    nx, ny = entity._rng.choice(neighbors)

    child = Entity(
        x=nx, y=ny,
        genome=child_genome,
        name=f"{entity.name}-{entity.children_count + 1}",
        rng=entity._rng,
    )
    transfer_count = max(1, int(entity.knowledge.count() * config.KNOWLEDGE_INHERIT_RATIO))
    for tech in list(entity.knowledge.known)[:transfer_count]:
        child.knowledge.learn(tech)

    for rtype in ["food", "wood"]:
        bequest = entity.inventory.get(rtype, 0) * config.RESOURCE_BEQUEST_RATIO
        if bequest > 0:
            child.inventory[rtype] = bequest
            entity.inventory[rtype] -= bequest

    child_id = world.spawn_entity(child)
    child.eid = child_id
    child.name = f"E{child_id:04d}"
    entity.children_count += 1
    entity.reproduction_cooldown = config.REPRODUCTION_COOLDOWN
    entity.energy -= config.ENERGY_COST["reproduce"]

    return [entity._event("reproduce", {
        "child": child.name,
        "partner": partner.name if partner else None,
        "sexual": partner is not None,
        "child_gen": child_genome.generation,
    })]


def age_update(entity: Entity) -> None:
    """나이 먹기. 수명 초과 시 에너지 급감."""
    entity.age += 1
    if entity.age > entity.max_age:
        entity.energy -= config.AGING_ENERGY_COST
    if entity.reproduction_cooldown > 0:
        entity.reproduction_cooldown -= 1
