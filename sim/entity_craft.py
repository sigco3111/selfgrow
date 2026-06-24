"""제작/건설 시스템 — 도구 제작, 건물 건설, 채집 보너스."""

from __future__ import annotations

from typing import TYPE_CHECKING

from . import config
from . import buildings as bld

if TYPE_CHECKING:
    from .entity import Entity


def do_craft(entity: Entity) -> list[dict]:
    """인벤토리 재료를 소비해 도구/무기 제작."""
    effects = entity.get_combined_effects()
    can_craft_iron = effects.get("craft_iron", 0) >= 1

    for recipe_name, ingredients in config.CRAFT_RECIPES.items():
        if recipe_name in entity.equipped:
            continue
        if "iron" in recipe_name and not can_craft_iron:
            continue
        if all(entity.inventory.get(mat, 0) >= qty for mat, qty in ingredients):
            for mat, qty in ingredients:
                entity.inventory[mat] -= qty
                if entity.inventory[mat] <= 0:
                    del entity.inventory[mat]
            entity.equipped.append(recipe_name)
            return [entity._event("craft", {"item": recipe_name})]
    return []


def do_construct(entity: Entity) -> list[dict]:
    """건물 건설."""
    for bdef in config.BUILDING_DEFS:
        if bdef.name in entity.buildings:
            continue
        if bld.construct(entity, bdef, None):
            return [entity._event("construct", {"building": bdef.name})]
    return []


def get_gather_bonus(entity: Entity, resource_type: str) -> float:
    """채집 보너스 계산 (장비 + 기술 효과)."""
    bonus = 1.0
    for item in entity.equipped:
        bonus += config.CRAFT_BONUS.get(item, {}).get(
            f"gather_{resource_type}", 0)
    effects = entity.get_combined_effects()
    gather_key = f"gather_{resource_type}"
    if gather_key in effects:
        bonus *= effects[gather_key]
    return bonus
