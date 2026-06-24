"""파벌 시스템 — 개체 집단, 영토, 동맹, 전쟁."""

from __future__ import annotations

import math
import random
from typing import TYPE_CHECKING, Optional

from . import config

if TYPE_CHECKING:
    from .entity import Entity
    from .world import World


# 파벌별 고유 색상 인덱스 (시각화용)
FACTION_COLORS = [
    "cp.red",
    "cp.blue",
    "cp.green",
    "cp.purple",
    "cp.amber",
    "cp.cyan",
    "cp.pink",
    "cp.magenta",
]


class Faction:
    """파벌 — 개체들의 집단. 영토 공유, 협력 전투, 파벌 전쟁."""

    _next_faction_id: int = 0

    def __init__(self, name: str, leader_id: int, world: World):
        self.faction_id = Faction._next_faction_id
        Faction._next_faction_id += 1

        self.name = name
        self.leader_id = leader_id
        self.members: set[int] = {leader_id}  # entity_id set
        self.formation_tick = world.tick

        # 파벌 영토: 지도자 본거지 기준 반경 내 타일
        self.territory: set[tuple[int, int]] = set()

        # 전쟁 상태: 상대 faction_id -> 남은 틱
        self.wars: dict[int, int] = {}

        # 외교 관계 테이블: faction_id -> relation_name
        self.diplomacy: dict[int, str] = {}

        # 통계
        self.total_kills = 0
        self.total_losses = 0
        self.wealth_history: list[float] = []

        # 시각화용 색상
        self.color = FACTION_COLORS[self.faction_id % len(FACTION_COLORS)]

    @property
    def member_count(self) -> int:
        return len(self.members)

    @property
    def cohesion(self) -> float:
        """파벌 결속력 = 최근 계산된 loyalty 평균 * 생존율."""
        return getattr(self, "_cohesion", 0.5)

    def set_cohesion(self, entities: dict[int, Entity]) -> None:
        """결속력 계산 (멤버 loyalty 평균 * 생존율 + 동일 이데올로기 보너스)."""
        if not self.members:
            self._cohesion = 0.0
            return

        # 이데올로기 보너스를 위해 지연 import
        from .ideology import same_ideology_bonus

        total_loyalty = 0.0
        alive_members: list[Entity] = []
        for eid in self.members:
            ent = entities.get(eid)
            if ent and ent.alive:
                total_loyalty += ent.genome.loyalty
                alive_members.append(ent)

        if not alive_members:
            self._cohesion = 0.0
            return

        avg_loyalty = total_loyalty / len(alive_members)
        survival_rate = len(alive_members) / max(1, len(self.members))

        # 동일 이데올로기 페어 보너스 계산
        ideology_bonus = 0.0
        pair_count = 0
        for i, e1 in enumerate(alive_members):
            for e2 in alive_members[i + 1:]:
                ideology_bonus += same_ideology_bonus(e1, e2)
                pair_count += 1

        avg_ideology_bonus = ideology_bonus / max(1, pair_count) if pair_count > 0 else 0.0

        self._cohesion = (avg_loyalty * survival_rate) + avg_ideology_bonus

    @property
    def total_strength(self) -> float:
        return getattr(self, "_strength", 0.0)

    def compute_strength(self, entities: dict[int, Entity]) -> float:
        """모든 멤버의 공격력 합계."""
        total = 0.0
        for eid in self.members:
            ent = entities.get(eid)
            if ent and ent.alive:
                total += ent.get_effective_attack() + ent.get_effective_defense()
        self._strength = total
        return total

    def is_at_war_with(self, faction_id: int) -> bool:
        return faction_id in self.wars

    def declare_war(self, target_faction_id: int) -> None:
        if target_faction_id not in self.wars:
            self.wars[target_faction_id] = config.FACTION_WAR_DURATION

    def tick_wars(self) -> None:
        """전쟁 타이머 감소, 만료된 전쟁 제거."""
        expired = []
        for enemy_id, remaining in self.wars.items():
            self.wars[enemy_id] = remaining - 1
            if remaining <= 0:
                expired.append(enemy_id)
        for eid in expired:
            del self.wars[eid]

    # ──────────────────────────────────────────
    # 외교 관계 (Phase 2.1)
    # ──────────────────────────────────────────

    DIPLOMACY_TYPES = ("ALLIANCE", "TRADE_PACT", "NON_AGGRESSION", "VASSAL")

    def set_relation(self, target_id: int, treaty: str) -> None:
        if treaty in self.DIPLOMACY_TYPES:
            self.diplomacy[target_id] = treaty

    def get_relation(self, target_id: int) -> str | None:
        return self.diplomacy.get(target_id)

    def remove_relation(self, target_id: int) -> None:
        self.diplomacy.pop(target_id, None)

    def has_treaty_with(self, target_id: int, treaty: str) -> bool:
        return self.diplomacy.get(target_id) == treaty

    def is_neutral(self, target_id: int) -> bool:
        return (not self.is_at_war_with(target_id)
                and not self.has_treaty_with(target_id, "ALLIANCE")
                and not self.has_treaty_with(target_id, "VASSAL")
                and not self.has_treaty_with(target_id, "NON_AGGRESSION"))

    def propose_treaty(self, target_faction: Faction, treaty: str) -> bool:
        if not config.DIPLOMACY_ENABLED:
            return False
        if treaty not in self.DIPLOMACY_TYPES:
            return False
        if self.is_at_war_with(target_faction.faction_id):
            return False

        if treaty == "ALLIANCE":
            self.set_relation(target_faction.faction_id, "ALLIANCE")
            target_faction.set_relation(self.faction_id, "ALLIANCE")
        elif treaty == "TRADE_PACT":
            self.set_relation(target_faction.faction_id, "TRADE_PACT")
            target_faction.set_relation(self.faction_id, "TRADE_PACT")
        elif treaty == "NON_AGGRESSION":
            self.set_relation(target_faction.faction_id, "NON_AGGRESSION")
            target_faction.set_relation(self.faction_id, "NON_AGGRESSION")
        elif treaty == "VASSAL":
            self.set_relation(target_faction.faction_id, "VASSAL")
            target_faction.set_relation(self.faction_id, "ALLIANCE")
        return True

    def break_treaty(self, target_faction: Faction) -> None:
        treaty = self.get_relation(target_faction.faction_id)
        if treaty is None:
            return
        if treaty == "VASSAL":
            self.set_relation(target_faction.faction_id, "WAR")
            target_faction.set_relation(self.faction_id, "WAR")
        else:
            self.remove_relation(target_faction.faction_id)
            target_faction.remove_relation(self.faction_id)
        self._cohesion = max(0.0, self.cohesion - config.ALLIANCE_BREAK_COHESION)

    def tick_diplomacy(self, faction_registry: dict[int, Faction],
                       entities: dict[int, Entity]) -> list[str]:
        events: list[str] = []
        if not config.DIPLOMACY_ENABLED:
            return events
        for target_id, treaty in list(self.diplomacy.items()):
            target_faction = faction_registry.get(target_id)
            if target_faction is None:
                self.remove_relation(target_id)
                continue
            if treaty == "ALLIANCE":
                self._process_alliance_tick(target_faction, entities, events)
            elif treaty == "TRADE_PACT":
                self._process_trade_pact_tick(target_faction, entities, events)
            elif treaty == "NON_AGGRESSION":
                self._process_non_aggression_tick(target_faction, entities, events)
            elif treaty == "VASSAL":
                self._process_vassal_tick(target_faction, entities, events)
        return events

    def _process_alliance_tick(self, target: Faction, entities: dict[int, Entity],
                               events: list[str]) -> None:
        if self.is_at_war_with(target.faction_id) or target.is_at_war_with(self.faction_id):
            self.break_treaty(target)
            events.append(f"Alliance broken between {self.name} and {target.name}")

    def _process_trade_pact_tick(self, target: Faction, entities: dict[int, Entity],
                                 events: list[str]) -> None:
        pass

    def _process_non_aggression_tick(self, target: Faction, entities: dict[int, Entity],
                                     events: list[str]) -> None:
        if self.is_at_war_with(target.faction_id):
            self.remove_relation(target.faction_id)
            target.remove_relation(self.faction_id)
            events.append(f"Non-aggression pact broken between {self.name} and {target.name}")

    def _process_vassal_tick(self, target: Faction, entities: dict[int, Entity],
                             events: list[str]) -> None:
        tribute_events = self._collect_vassal_tribute(target, entities)
        events.extend(tribute_events)

    def _collect_vassal_tribute(self, overlord: Faction,
                                entities: dict[int, Entity]) -> list[str]:
        events: list[str] = []
        for member_id in list(self.members):
            ent = entities.get(member_id)
            if ent is None or not ent.alive:
                continue
            tribute_wood = int(ent.inventory.get("wood", 0) * config.VASSAL_TRIBUTE_RATIO)
            tribute_stone = int(ent.inventory.get("stone", 0) * config.VASSAL_TRIBUTE_RATIO)
            tribute_food = int(ent.inventory.get("food", 0) * config.VASSAL_TRIBUTE_RATIO)
            if tribute_wood > 0 or tribute_stone > 0 or tribute_food > 0:
                ent.inventory["wood"] = ent.inventory.get("wood", 0) - tribute_wood
                ent.inventory["stone"] = ent.inventory.get("stone", 0) - tribute_stone
                ent.inventory["food"] = ent.inventory.get("food", 0) - tribute_food
                for overlord_member_id in overlord.members:
                    overlord_ent = entities.get(overlord_member_id)
                    if overlord_ent and overlord_ent.alive:
                        overlord_ent.inventory["wood"] = overlord_ent.inventory.get("wood", 0) + tribute_wood
                        overlord_ent.inventory["stone"] = overlord_ent.inventory.get("stone", 0) + tribute_stone
                        overlord_ent.inventory["food"] = overlord_ent.inventory.get("food", 0) + tribute_food
                        break
                if tribute_wood > 0 or tribute_stone > 0 or tribute_food > 0:
                    events.append(f"{self.name} pays tribute to {overlord.name}")
        return events

    def is_enemy(self, entity_id: int, faction_registry: dict[int, Faction]) -> bool:
        """특정 개체가 이 파벌의 적인가? (같은 faction의 멤버면 적이 아님)."""
        # 자기 멤버는 적이 아님
        if entity_id in self.members:
            return False
        # entity가 속한 파벌 찾기
        for fid, faction in faction_registry.items():
            if fid == self.faction_id:
                continue
            if entity_id in faction.members:
                return self.is_at_war_with(fid)
        return False

    def get_enemy_factions(self, faction_registry: dict[int, Faction]) -> list[Faction]:
        return [f for fid, f in faction_registry.items()
                if fid in self.wars]

    def update_territory(self, entities: dict[int, Entity], world: World) -> None:
        """파벌 영토 갱신: 멤버들의 본거지 정보를 기반으로 영토 재계산."""
        new_territory: set[tuple[int, int]] = set()
        for eid in self.members:
            ent = entities.get(eid)
            if ent and ent.alive:
                hx, hy = getattr(ent, "home_x", None), getattr(ent, "home_y", None)
                if hx is not None:
                    for dx in range(-config.TERRITORY_RADIUS, config.TERRITORY_RADIUS + 1):
                        for dy in range(-config.TERRITORY_RADIUS, config.TERRITORY_RADIUS + 1):
                            tx, ty = hx + dx, hy + dy
                            if (0 <= tx < world.width and 0 <= ty < world.height
                                    and abs(dx) + abs(dy) <= config.TERRITORY_RADIUS):
                                new_territory.add((tx, ty))
        self.territory = new_territory

    # ──────────────────────────────────────────
    # 정적 메서드 — 파벌 관리
    # ──────────────────────────────────────────

    @staticmethod
    def get_faction_for_entity(entity_id: int,
                                faction_registry: dict[int, Faction]) -> Faction | None:
        """개체가 속한 파벌 반환."""
        for faction in faction_registry.values():
            if entity_id in faction.members:
                return faction
        return None

    @staticmethod
    def try_form_factions(entities: dict[int, Entity],
                           world: World,
                           faction_registry: dict[int, Faction]) -> list[Faction]:
        """자발적 파벌 결성 시도. 사회성 높은 개체들이 모여 파벌 형성."""
        new_factions: list[Faction] = []
        if not config.FACTION_ENABLED:
            return new_factions

        # 이미 파벌에 속한 개체는 제외
        faction_members: set[int] = set()
        for f in faction_registry.values():
            faction_members.update(f.members)

        eligible = [(eid, e) for eid, e in entities.items()
                    if e.alive and eid not in faction_members
                    and e.genome.sociability >= config.FACTION_FORMATION_SOCIABILITY]

        if len(eligible) < config.FACTION_FORMATION_MIN_MEMBERS:
            return new_factions

        # 클러스터링: 가까운 개체끼리 그룹화
        used: set[int] = set()
        for eid, ent in eligible:
            if eid in used:
                continue

            cluster = [(eid, ent)]
            used.add(eid)

            for other_id, other_ent in eligible:
                if other_id in used:
                    continue
                dist = abs(other_ent.x - ent.x) + abs(other_ent.y - ent.y)
                if dist <= config.FACTION_FORMATION_RADIUS:
                    cluster.append((other_id, other_ent))
                    used.add(other_id)

            # 최소 인원 충족 시 파벌 결성
            if len(cluster) >= config.FACTION_FORMATION_MIN_MEMBERS:
                # 지도자 = 가장 높은 aggression * strength
                leader = max(cluster, key=lambda item:
                             item[1].genome.aggression * (0.5 + 0.5 * item[1].genome.strength))
                leader_id, leader_ent = leader

                # 파벌 이름 = 지도자 이름 기반
                fname = f"Clan-{leader_ent.name}"

                faction = Faction(fname, leader_id, world)
                for cid, _ in cluster:
                    faction.members.add(cid)
                    ent_obj = entities.get(cid)
                    if ent_obj:
                        ent_obj.faction_id = faction.faction_id

                new_factions.append(faction)

        return new_factions

    @staticmethod
    def cleanup_factions(faction_registry: dict[int, Faction],
                          entities: dict[int, Entity]) -> list[int]:
        """사장된 파벌 제거. 해체된 파벌 ID 목록 반환."""
        disbanded: list[int] = []
        for fid, faction in list(faction_registry.items()):
            # 살아있는 멤버만 카운트
            alive_members = [eid for eid in faction.members
                             if eid in entities and entities[eid].alive]
            if len(alive_members) < 2:
                # 1명 이하: 해체
                for eid in faction.members:
                    ent = entities.get(eid)
                    if ent:
                        ent.faction_id = -1
                disbanded.append(fid)
            elif faction.cohesion < config.FACTION_COHESION_BREAKUP:
                # 결속력 너무 낮음: 일부 이탈
                for eid in list(faction.members):
                    ent = entities.get(eid)
                    if ent and ent.alive and ent.genome.loyalty < config.FACTION_COHESION_BREAKUP:
                        faction.members.discard(eid)
                        ent.faction_id = -1
                        # 이탈자가 지도자면 새 지도자 선출
                        if eid == faction.leader_id and faction.members:
                            candidates = [entities.get(m) for m in faction.members if m in entities and entities.get(m)]
                            if candidates:
                                new_leader = max(candidates, key=lambda e: e.genome.aggression)
                                faction.leader_id = new_leader.eid
        return disbanded
