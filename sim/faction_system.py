"""파벌 시스템 — 결성, 결속력, 영토, 전쟁, 해체."""

from __future__ import annotations

import random
from typing import TYPE_CHECKING, Callable

from . import config
from .faction import Faction

if TYPE_CHECKING:
    from .world import World


def process_factions(
    world: World,
    rng: random.Random,
    log_event: Callable[[dict], None],
) -> None:
    """파벌 생명주기: 결성, 결속력, 영토, 전쟁, 해체."""
    if not config.FACTION_ENABLED:
        return

    entities = world.entities
    faction_reg = world.faction_registry

    # 1. 기존 파벌 결속력/강도/영토 업데이트
    for faction in faction_reg.values():
        faction.set_cohesion(entities)
        faction.compute_strength(entities)
        faction.update_territory(entities, world)
        faction.tick_wars()

    # 2. 새 파벌 결성 시도
    faction_rng = config.create_rng(rng.getrandbits(32), "faction")
    if faction_rng.random() < config.FACTION_FORM_CHANCE:
        new_factions = Faction.try_form_factions(entities, world, faction_reg)
        for faction in new_factions:
            faction_reg[faction.faction_id] = faction
            for eid in faction.members:
                ent = entities.get(eid)
                if ent:
                    ent.faction_id = faction.faction_id
            log_event({
                "tick": world.tick,
                "type": "faction_formed",
                "data": {
                    "faction": faction.name,
                    "leader": (entities.get(faction.leader_id).name
                               if entities.get(faction.leader_id) else "?"),
                    "members": faction.member_count,
                },
            })

    # 3. 파벌 해체 (멤버 부족)
    disbanded = Faction.cleanup_factions(faction_reg, entities)
    for fid in disbanded:
        faction = faction_reg.pop(fid, None)
        if faction:
            log_event({
                "tick": world.tick,
                "type": "faction_disbanded",
                "data": {
                    "faction": faction.name,
                    "reason": "members_below_2",
                },
            })

    # 4. 외교 틱 처리
    for faction in list(faction_reg.values()):
        diplo_events = faction.tick_diplomacy(faction_reg, entities)
        for evt in diplo_events:
            log_event({
                "tick": world.tick,
                "type": "diplomacy",
                "data": {"message": evt},
            })

    # 5. 자동 전쟁 선포: 같은 타일에서 다른 파벌 멤버 발견 시
    for faction in list(faction_reg.values()):
        for eid in list(faction.members):
            ent = entities.get(eid)
            if not ent or not ent.alive:
                continue
            for other_eid, other_ent in world.entity_at(ent.x, ent.y):
                if (other_ent.alive and other_ent.faction_id >= 0
                        and other_ent.faction_id != faction.faction_id):
                    target_faction = faction_reg.get(other_ent.faction_id)
                    if target_faction:
                        faction.declare_war(target_faction.faction_id)
                        target_faction.declare_war(faction.faction_id)
