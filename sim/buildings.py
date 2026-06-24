from __future__ import annotations

import random
from typing import TYPE_CHECKING

from . import config

if TYPE_CHECKING:
    from .entity import Entity
    from .world import World


def can_construct(entity: "Entity", building_def: config.BuildingDef) -> bool:
    existing = sum(1 for b in entity.buildings if b == building_def.name)
    if existing >= building_def.max_per_entity:
        return False
    if building_def.tech_required:
        if not entity.knowledge.know(building_def.tech_required):
            return False
    for rtype, qty in building_def.cost.items():
        if entity.inventory.get(rtype, 0) < qty:
            return False
    return True


def construct(entity: "Entity", building_def: config.BuildingDef, world: "World") -> bool:
    if not can_construct(entity, building_def):
        return False
    for rtype, qty in building_def.cost.items():
        entity.inventory[rtype] = entity.inventory.get(rtype, 0) - qty
        if entity.inventory[rtype] <= 0:
            del entity.inventory[rtype]
    entity.buildings.append(building_def.name)
    return True


def get_building_effects(entity: "Entity") -> dict[str, float]:
    combined: dict[str, float] = {}
    for bname in entity.buildings:
        for bdef in config.BUILDING_DEFS:
            if bdef.name == bname:
                for k, v in bdef.effects.items():
                    if isinstance(v, (int, float)):
                        combined[k] = combined.get(k, 0.0) + v
    return combined


def destroy_random_building(entity: "Entity", rng: random.Random) -> str | None:
    if not entity.buildings:
        return None
    if rng.random() < config.BUILDING_DESTROY_CHANCE:
        removed = rng.choice(entity.buildings)
        entity.buildings.remove(removed)
        return removed
    return None
