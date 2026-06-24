"""SmartBrain 목표 시스템 — 자원/장비/탐험 목표 자동 생성 및 보너스."""

from __future__ import annotations

from typing import TYPE_CHECKING

from . import config
from .brain_base import Goal

if TYPE_CHECKING:
    from .entity import Entity, EntityState
    from .world import World


def update_goals(entity: Entity, brain) -> None:
    """자원/장비/안전 상태에 따라 단기 목표 자동 생성."""
    from .entity import EntityState

    new_goals: list[Goal] = []
    food = entity.inventory.get("food", 0)
    wood = entity.inventory.get("wood", 0)
    stone = entity.inventory.get("stone", 0)
    iron = entity.inventory.get("iron", 0)

    if food < 8:
        new_goals.append(Goal(
            "food_surplus", 12.0,
            priority=0.9 - (food / 8.0) * 0.5,
            description="식량 비축이 필요함"))

    if iron < 3 and entity.genome.specialization in ("warrior", "crafter", "miner"):
        new_goals.append(Goal(
            "iron_stock", 5.0,
            priority=0.6,
            description="철 확보가 필요함"))

    has_weapon = any("sword" in e or "axe" in e for e in entity.equipped)
    has_armor = any("armor" in e for e in entity.equipped)
    if not has_weapon and entity.genome.aggression > 0.3:
        new_goals.append(Goal(
            "equip_weapon", 1.0,
            priority=0.5,
            description="무기 제작이 필요함"))

    if (not has_weapon and wood >= 3 and stone >= 5):
        new_goals.append(Goal(
            "craft_tool", 1.0,
            priority=0.45,
            description="도구 제작이 필요함"))

    if entity.genome.curiosity > 0.6 and len(entity.visited_tiles) < 20:
        new_goals.append(Goal(
            "explore", 20.0,
            priority=0.3 * entity.genome.curiosity,
            description="새로운 영역 탐험이 필요함"))

    brain.goals = new_goals


def goal_action_bonus(goal: Goal, entity: Entity, world: World) -> float:
    """목표에 따른 행동 보너스 계산."""
    if goal.metric == "food_surplus":
        return 15.0
    elif goal.metric == "iron_stock":
        tile = world.tile_at(entity.x, entity.y)
        if tile and tile.resources.get("iron", 0) > 0:
            return 20.0
        return 10.0
    elif goal.metric == "equip_weapon":
        return 20.0
    elif goal.metric == "craft_tool":
        return 15.0
    elif goal.metric == "explore":
        return 10.0
    return 5.0


def goal_relevant_actions(goal: Goal) -> list:
    """목표와 관련된 행동 목록 반환."""
    from .entity import EntityState
    mapping = {
        "food_surplus": [EntityState.GATHER, EntityState.TRADE],
        "iron_stock": [EntityState.GATHER, EntityState.TRADE],
        "equip_weapon": [EntityState.CRAFT, EntityState.TRADE],
        "craft_tool": [EntityState.CRAFT],
        "explore": [EntityState.EXPLORE],
    }
    return mapping.get(goal.metric, [])