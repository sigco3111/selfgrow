from __future__ import annotations

import random
import math
from enum import Enum
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from . import config

if TYPE_CHECKING:
    from .world import World


class EventType(Enum):
    WILDFIRE = "wildfire"
    FLOOD = "flood"
    BOUNTIFUL_HARVEST = "bountiful_harvest"
    PEST_INFESTATION = "pest_infestation"
    ANIMAL_MIGRATION = "animal_migration"
    EARTHQUAKE = "earthquake"


EVENT_NAMES_KR: dict[EventType, str] = {
    EventType.WILDFIRE: "산불",
    EventType.FLOOD: "홍수",
    EventType.BOUNTIFUL_HARVEST: "풍년",
    EventType.PEST_INFESTATION: "역병",
    EventType.ANIMAL_MIGRATION: "동물 대이동",
    EventType.EARTHQUAKE: "지진",
}


@dataclass
class WorldEvent:
    event_type: EventType
    remaining: int
    center_x: int
    center_y: int
    radius: int
    severity: float

    @property
    def name_kr(self) -> str:
        return EVENT_NAMES_KR.get(self.event_type, self.event_type.value)


def generate_event(world: World, rng: random.Random) -> WorldEvent | None:
    events = list(EventType)
    chosen = rng.choice(events)
    cx = rng.randint(0, world.width - 1)
    cy = rng.randint(0, world.height - 1)
    radius = rng.randint(config.EVENT_RADIUS_MIN, config.EVENT_RADIUS_MAX)
    duration = rng.randint(config.EVENT_DURATION_MIN, config.EVENT_DURATION_MAX)
    severity = rng.uniform(config.EVENT_SEVERITY_MIN, config.EVENT_SEVERITY_MAX)
    return WorldEvent(
        event_type=chosen,
        remaining=duration,
        center_x=cx,
        center_y=cy,
        radius=radius,
        severity=severity,
    )


def in_event_area(ev: WorldEvent, x: int, y: int) -> bool:
    dist = math.sqrt((x - ev.center_x) ** 2 + (y - ev.center_y) ** 2)
    return dist <= ev.radius


def apply_event_tick(world: World, ev: WorldEvent) -> list[dict]:
    logs: list[dict] = []
    et = ev.event_type

    for row in world.tiles:
        for tile in row:
            if not in_event_area(ev, tile.x, tile.y):
                continue

            if et == EventType.WILDFIRE:
                if tile.biome.value in ("forest", "plain"):
                    for rtype in list(tile.resources.keys()):
                        tile.resources[rtype] *= 0.5
                    for eid, ent in world.entities.items():
                        if ent.alive and (ent.x, ent.y) == (tile.x, tile.y):
                            ent.energy -= 8.0 * ev.severity
                            if ent.energy <= 0:
                                ent.alive = False
                                logs.append({
                                    "type": "event_death",
                                    "entity_name": ent.name,
                                    "data": {"cause": "wildfire"},
                                })

            elif et == EventType.FLOOD:
                if tile.biome.value in ("water", "swamp", "plain"):
                    for rtype in ("food", "wood"):
                        current = tile.resources.get(rtype, 0)
                        max_val = config.MAX_TILE_RESOURCES.get(
                            tile.biome.value, {}).get(rtype, 0)
                        tile.resources[rtype] = min(
                            max_val * 1.5, current + 3.0 * ev.severity)

            elif et == EventType.BOUNTIFUL_HARVEST:
                for rtype in ("food", "wood"):
                    current = tile.resources.get(rtype, 0)
                    max_val = config.MAX_TILE_RESOURCES.get(
                        tile.biome.value, {}).get(rtype, 0)
                    tile.resources[rtype] = min(
                        max_val * 2.0, current + 5.0 * ev.severity)

            elif et == EventType.PEST_INFESTATION:
                food = tile.resources.get("food", 0)
                tile.resources["food"] = max(0, food - 2.0 * ev.severity)
                for eid, ent in world.entities.items():
                    if ent.alive and (ent.x, ent.y) == (tile.x, tile.y):
                        ent.energy -= 2.0 * ev.severity

            elif et == EventType.ANIMAL_MIGRATION:
                for rtype in ("food", "wood"):
                    current = tile.resources.get(rtype, 0)
                    max_val = config.MAX_TILE_RESOURCES.get(
                        tile.biome.value, {}).get(rtype, 0)
                    tile.resources[rtype] = min(
                        max_val * 1.3, current + 4.0 * ev.severity)

            elif et == EventType.EARTHQUAKE:
                tile.resources["stone"] = tile.resources.get("stone", 0) + 5.0 * ev.severity
                for rtype in ("food", "wood"):
                    tile.resources[rtype] = tile.resources.get(rtype, 0) * 0.7
                for eid, ent in world.entities.items():
                    if ent.alive and (ent.x, ent.y) == (tile.x, tile.y):
                        ent.energy -= 5.0 * ev.severity

    return logs


def process_events(world: World, rng: random.Random | None = None) -> list[dict]:
    rng = rng or random
    logs: list[dict] = []
    active = getattr(world, "event_registry", [])
    remaining: list[WorldEvent] = []

    for ev in active:
        logs.extend(apply_event_tick(world, ev))
        ev.remaining -= 1
        if ev.remaining > 0:
            remaining.append(ev)
        else:
            logs.append({
                "type": "event_ended",
                "data": {"event": ev.name_kr},
            })

    world.event_registry = remaining

    if len(remaining) < config.EVENT_MAX_ACTIVE:
        if rng.random() < config.EVENT_BASE_PROBABILITY:
            world_tick = getattr(world, "tick", 0)
            last_tick = getattr(world, "_last_event_tick", 0)
            if world_tick - last_tick >= config.EVENT_MIN_INTERVAL:
                ev = generate_event(world, rng)
                if ev:
                    remaining.append(ev)
                    world.event_registry = remaining
                    world._last_event_tick = world_tick
                    logs.append({
                        "type": "event_started",
                        "data": {"event": ev.name_kr, "x": ev.center_x, "y": ev.center_y},
                    })

    return logs
