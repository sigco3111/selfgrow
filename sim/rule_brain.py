"""RuleBasedBrain — 행동 점수 기반 FSM 의사결정 엔진."""

from __future__ import annotations

import random
from typing import TYPE_CHECKING, Optional

from . import config
from . import buildings as bld
from .brain_base import Brain

if TYPE_CHECKING:
    from .entity import Entity, EntityState
    from .world import World
    from .market import Market


class RuleBasedBrain(Brain):
    """기존의 행동 점수 기반 결정 엔진. Entity.decide_action()의 로직 그대로."""

    def __init__(self, rng: random.Random | None = None):
        self._rng = rng or random

    def decide(self, entity: Entity, world: World,
               market: Optional[Market]) -> EntityState:
        from .entity import EntityState

        if entity.energy <= 0:
            return EntityState.DIE

        scores: dict[EntityState, float] = {}

        # 1. CONSUME
        hunger_ratio = 1.0 - (entity.energy / entity.max_energy)
        food_available = entity.inventory.get("food", 0)
        if food_available > 0 and hunger_ratio > 0.2:
            scores[EntityState.CONSUME] = hunger_ratio * 100.0
        elif hunger_ratio > 0.6:
            scores[EntityState.GATHER] = hunger_ratio * 90.0

        # 2. REPRODUCE
        energy_ratio = entity.energy / entity.max_energy
        food_stored = entity.inventory.get("food", 0)
        if (energy_ratio > config.REPRODUCTION_ENERGY_RATIO
                and entity.reproduction_cooldown <= 0
                and food_stored >= config.REPRODUCTION_MIN_FOOD
                and entity.inventory_used >= 3):
            scores[EntityState.REPRODUCE] = (
                energy_ratio * 40.0 * (0.3 + entity.genome.fertility * 0.7))

        # 3. GATHER
        tile = world.tile_at(entity.x, entity.y)
        if tile and tile.total_resources() > 0 and not entity.inventory_is_full:
            need = self._resource_need(entity)
            if need > 0:
                scores[EntityState.GATHER] = need * 30.0 + self._rng.uniform(0, 10)

        # 4. TRADE
        if market and not entity.inventory_is_full:
            surplus = self._has_surplus(entity)
            if surplus:
                scores[EntityState.TRADE] = (
                    entity.genome.sociability * 50.0 + self._rng.uniform(0, 10))

        # 5. CRAFT
        if entity.genome.industry > 0.4:
            if self._can_craft_anything(entity):
                scores[EntityState.CRAFT] = (
                    entity.genome.industry * 40.0 + self._rng.uniform(0, 10))

        # 6. CONSTRUCT
        if not entity.buildings:
            for bdef in config.BUILDING_DEFS:
                if bld.can_construct(entity, bdef):
                    scores[EntityState.CONSTRUCT] = 35.0 + entity.genome.industry * 20.0
                    break

        # 7. COMBAT
        combat_score = self._score_combat(entity, world)
        if combat_score > 0:
            scores[EntityState.COMBAT] = combat_score

        # 8. EXPLORE
        if entity.curiosity_drive() > 0:
            scores[EntityState.EXPLORE] = (
                entity.genome.curiosity * 20.0 + self._rng.uniform(0, 15))

        scores[EntityState.IDLE] = 5.0

        # 이데올로기 행동 바이어스 적용 (Phase 3.1)
        from .ideology import get_action_bias
        action_bias = get_action_bias(entity)
        for action_name, bias in action_bias.items():
            es = getattr(EntityState, action_name.upper(), None)
            if es and es in scores:
                scores[es] *= bias

        return max(scores, key=scores.get)

    def _resource_need(self, entity) -> float:
        need = 0.0
        food = entity.inventory.get("food", 0)
        if food < 5:
            need += 0.5
        wood = entity.inventory.get("wood", 0)
        if wood < 3:
            need += 0.2
        stone = entity.inventory.get("stone", 0)
        if stone < 3:
            need += 0.15
        iron = entity.inventory.get("iron", 0)
        if iron < 2 and entity.genome.specialization in ("miner", "warrior", "crafter"):
            need += 0.15
        return min(1.0, need)

    def _has_surplus(self, entity) -> bool:
        for rtype, amount in entity.inventory.items():
            if rtype == "food" and amount > 5:
                return True
            if rtype != "food" and amount > 3:
                return True
        return False

    def _can_craft_anything(self, entity) -> bool:
        for recipe_name, ingredients in config.CRAFT_RECIPES.items():
            if recipe_name in entity.equipped:
                continue
            if all(entity.inventory.get(mat, 0) >= qty for mat, qty in ingredients):
                return True
        return False

    def _score_combat(self, entity, world) -> float:
        from .entity import EntityState

        combat_score = 0.0
        food_stored = entity.inventory.get("food", 0)
        energy_ratio = entity.energy / entity.max_energy

        nearby_entities = [(eid, e) for eid, e in world.entities.items()
                           if e.alive and e != entity
                           and abs(e.x - entity.x) <= 1
                           and abs(e.y - entity.y) <= 1]
        same_tile = [(eid, e) for (eid, e) in nearby_entities
                     if (e.x, e.y) == (entity.x, entity.y)]

        # 약탈
        if food_stored < 3 and energy_ratio > 0.3:
            for _, neighbor in nearby_entities:
                if neighbor.inventory.get("food", 0) >= 3:
                    combat_score = max(combat_score, 80.0 + (1.0 - energy_ratio) * 30.0)
                    break

        # 영토 방어
        if entity.home_x is not None:
            dist_to_home = abs(entity.x - entity.home_x) + abs(entity.y - entity.home_y)
            if dist_to_home <= config.TERRITORY_RADIUS:
                for _, neighbor in same_tile:
                    other_home = getattr(neighbor, "home_x", None)
                    if other_home is not None:
                        other_dist = abs(neighbor.x - other_home) + abs(neighbor.y - other_home)
                        if other_dist > config.TERRITORY_RADIUS:
                            combat_score = max(combat_score, 60.0 * entity.genome.aggression)

        # 파벌 전쟁
        if entity.faction_id >= 0:
            faction_registry = getattr(world, "faction_registry", {})
            my_faction = faction_registry.get(entity.faction_id)
            if my_faction:
                for eid, neighbor in nearby_entities:
                    if (neighbor.faction_id >= 0
                            and my_faction.is_enemy(eid, faction_registry)):
                        combat_score = max(combat_score,
                                           70.0 * entity.genome.aggression
                                           + entity.genome.loyalty * 30.0)
                        break

        # 일반 공격
        if same_tile:
            if entity.genome.aggression > 0.2:
                combat_score = max(combat_score,
                                   entity.genome.aggression * 30.0 + self._rng.uniform(0, 10))
            elif entity.genome.aggression > 0.1:
                combat_score = max(combat_score, entity.genome.aggression * 15.0)

        # 후퇴
        if energy_ratio < config.COMBAT_RETREAT_THRESHOLD:
            combat_score *= 0.3

        return combat_score

    def brain_type(self) -> str:
        return self.__class__.__name__

    def feedback(self, entity, action: str, outcome_score: float) -> None:
        pass
