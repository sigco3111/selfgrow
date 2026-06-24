"""전투 시스템 — 다중 개체 전투, 동맹 지원, 장비 파괴, 지식 약탈."""

from __future__ import annotations

from typing import TYPE_CHECKING

from . import buildings as bld
from . import config

if TYPE_CHECKING:
    from .entity import Entity
    from .world import World


def do_combat(entity: Entity, world: World) -> list[dict]:
    """강화된 전투: 다중 개체 + 동맹 지원 + 장비 파괴 + 지식 약탈."""
    events: list[dict] = []
    same_tile_targets = [(eid, e) for eid, e in world.entity_at(entity.x, entity.y)
                         if e is not entity and e.alive]
    if not same_tile_targets:
        return []

    target_id, target = same_tile_targets[0]

    # ── 동맹 지원: 같은 파벌 멤버가 근처에 있으면 전투 합류 ──
    allies: list[Entity] = []
    if entity.faction_id >= 0:
        faction_registry = getattr(world, "faction_registry", {})
        my_faction = faction_registry.get(entity.faction_id)
        if my_faction:
            for eid, ent in world.entities_near(entity.x, entity.y, config.FACTION_ALLY_SUPPORT_RADIUS):
                if (ent.alive and ent is not entity and ent is not target
                        and ent.faction_id == entity.faction_id):
                    allies.append(ent)

    # ── 영토 보너스 ──
    effects = entity.get_combined_effects()
    extra_home_bonus = effects.get("home_bonus_extra", 0.0)
    home_bonus = 1.0
    if entity.home_x is not None:
        dist_to_home = abs(entity.x - entity.home_x) + abs(entity.y - entity.home_y)
        if dist_to_home <= config.TERRITORY_RADIUS:
            home_bonus = 1.0 + config.COMBAT_HOME_BONUS + extra_home_bonus

    ally_bonus = 1.0
    if allies:
        ally_bonus = 1.0 + config.FACTION_ALLY_COMBAT_BONUS * min(len(allies), 3)

    faction_morale = effects.get("faction_morale", 0.0)
    if entity.faction_id >= 0 and faction_morale > 0:
        ally_bonus += faction_morale

    my_atk = entity.get_effective_attack() * home_bonus * ally_bonus
    my_def = entity.get_effective_defense() * home_bonus * ally_bonus

    # 상대 영토 보너스
    target_home_bonus = 1.0
    if hasattr(target, "home_x") and target.home_x is not None:
        other_dist = abs(target.x - target.home_x) + abs(target.y - target.home_y)
        if other_dist <= config.TERRITORY_RADIUS:
            target_home_bonus = 1.0 + config.COMBAT_HOME_BONUS

    # 상대 동맹 지원
    target_ally_bonus = 1.0
    target_allies: list[Entity] = []
    if target.faction_id >= 0:
        faction_registry = getattr(world, "faction_registry", {})
        target_faction = faction_registry.get(target.faction_id)
        if target_faction:
            for eid, ent in world.entities_near(target.x, target.y, config.FACTION_ALLY_SUPPORT_RADIUS):
                if (ent.alive and ent is not target and ent is not entity
                        and ent.faction_id == target.faction_id):
                    target_allies.append(ent)
    if target_allies:
        target_ally_bonus = 1.0 + config.FACTION_ALLY_COMBAT_BONUS * min(len(target_allies), 3)

    target_atk = target.get_effective_attack() * target_home_bonus * target_ally_bonus
    target_def = target.get_effective_defense() * target_home_bonus * target_ally_bonus

    # ── 데미지 계산 ──
    base_damage = config.COMBAT_BASE_DAMAGE
    variance = 1.0 + entity._rng.uniform(-config.COMBAT_DAMAGE_VARIANCE,
                                          config.COMBAT_DAMAGE_VARIANCE)
    damage_dealt = max(1, (my_atk / (target_def + 1)) * base_damage * variance)
    damage_taken = max(1, (target_atk / (my_def + 1)) * base_damage * variance * 0.7)

    target.energy -= damage_dealt
    entity.energy -= damage_taken

    # ── 동맹도 데미지 기여 ──
    ally_damage = 0.0
    for ally in allies:
        ally_contrib = ally.get_effective_attack() * config.COMBAT_ALLY_CONTRIBUTION
        ally_damage += ally_contrib
        ally.energy -= config.ENERGY_COST["combat"] * 0.3
        events.append(entity._event("ally_attack", {
            "ally": ally.name,
            "damage_contrib": round(ally_contrib, 1),
        }))
    if ally_damage > 0:
        target.energy -= ally_damage * 0.5

    target_killed = target.energy <= 0
    if target_killed:
        target.alive = False
        entity.kill_count += 1

    # ── 전투 이벤트 ──
    ally_names = [a.name for a in allies]
    target_ally_names = [a.name for a in target_allies]
    events.append(entity._event("combat", {
        "target": target.name,
        "damage_dealt": round(damage_dealt, 1),
        "damage_taken": round(damage_taken, 1),
        "allies": ally_names,
        "target_allies": target_ally_names,
        "target_alive": not target_killed,
    }))

    # ── 건물 파괴 ──
    destroyed = bld.destroy_random_building(entity, rng=entity._rng)
    if destroyed:
        events.append(entity._event("building_destroyed", {"building": destroyed}))
    if target_killed:
        destroyed_target = bld.destroy_random_building(target, rng=entity._rng)
        if destroyed_target:
            events.append(entity._event("building_destroyed",
                                         {"building": destroyed_target, "target": target.name}))

    # ── 장비 파괴 ──
    for item in list(entity.equipped):
        if entity._rng.random() < config.EQUIPMENT_BREAK_CHANCE:
            entity.equipped.remove(item)
            events.append(entity._event("equipment_broken", {"item": item}))
    if target_killed:
        for item in list(target.equipped):
            if entity._rng.random() < config.EQUIPMENT_BREAK_CHANCE:
                target.equipped.remove(item)

    # ── 승리: 약탈 ──
    if target_killed:
        loot = {}
        for rtype, amount in target.inventory.items():
            loot_qty = amount * config.COMBAT_WINNER_LOOT_RATIO
            if loot_qty > 0:
                entity.inventory[rtype] = entity.inventory.get(rtype, 0) + loot_qty
                loot[rtype] = round(loot_qty, 1)
        events.append(entity._event("loot", {
            "target": target.name,
            "loot": loot,
        }))

        if target.equipped and entity._rng.random() < config.COMBAT_EQUIPMENT_LOOT_CHANCE:
            stolen_item = entity._rng.choice(target.equipped)
            target.equipped.remove(stolen_item)
            if len(entity.equipped) < config.MAX_EQUIPPED_SLOTS:
                entity.equipped.append(stolen_item)
                events.append(entity._event("equipment_loot", {
                    "item": stolen_item,
                    "from": target.name,
                }))

        if (target.knowledge.count() > 0
                and entity._rng.random() < config.COMBAT_KNOWLEDGE_LOOT_CHANCE):
            stolen_knowledge = entity._rng.choice(list(target.knowledge.known))
            entity.knowledge.learn(stolen_knowledge)
            events.append(entity._event("knowledge_loot", {
                "tech": stolen_knowledge,
                "from": target.name,
            }))

    return events
