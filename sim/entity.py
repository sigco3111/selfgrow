"""개체 — 시뮬레이션의 기본 단위. 상태 기반 행동 + 진화."""

from __future__ import annotations

import random
from collections import deque
from enum import Enum, auto
from typing import TYPE_CHECKING, Optional

from . import config
from . import buildings as bld
from . import entity_action
from . import entity_combat
from . import entity_craft
from . import entity_reproduce
from .brain import Brain, RuleBasedBrain, create_brain
from .genome import Genome
from .knowledge import KnowledgeBook

if TYPE_CHECKING:
    from .world import World
    from .market import Market


# ──────────────────────────────────────────────
# 개체 상태
# ──────────────────────────────────────────────
class EntityState(Enum):
    IDLE = auto()
    EXPLORE = auto()
    GATHER = auto()
    TRADE = auto()
    CRAFT = auto()
    CONSUME = auto()
    REPRODUCE = auto()
    COMBAT = auto()
    CONSTRUCT = auto()
    DIE = auto()


# ──────────────────────────────────────────────
# 재화 타입
# ──────────────────────────────────────────────
class CurrencyType(Enum):
    NONE = "none"             # 아직 화폐 없음
    SHELL = "shell"           # 조개껍질 (원시 화폐)
    COIN = "coin"             # 금속 화폐


# ──────────────────────────────────────────────
# Entity — 개체
# ──────────────────────────────────────────────
class Entity:
    """생태계의 개체. 유전자 + 상태 + 인벤토리 + 지식."""

    def __init__(self, x: int, y: int, genome: Genome | None = None,
                 name: str | None = None,
                 rng: random.Random | None = None,
                 entity_id: int | None = None):
        self._rng = rng
        self.eid: int = entity_id if entity_id is not None else -1
        self.x = x
        self.y = y
        self.genome = genome or Genome.random_initial(rng=self._rng)
        self.name = name or f"E{self.eid % 10000:04d}"

        # 상태
        self.state = EntityState.IDLE
        self.energy = config.BASE_ENERGY
        self.max_energy = config.BASE_MAX_ENERGY * (
            0.7 + 0.6 * self.genome.endurance
        )
        self.age = 0
        self.max_age = int(config.BASE_LIFESPAN * (
            0.7 + 0.6 * self.genome.endurance
        ))
        self.alive = True

        # 전투
        self.attack = config.BASE_ATTACK + 10.0 * self.genome.strength
        self.defense = config.BASE_DEFENSE + 5.0 * self.genome.endurance

        # 인벤토리
        self.inventory: dict[str, float] = {}
        self.max_inventory_slots = config.BASE_INVENTORY_SLOTS

        # 장착 아이템
        self.equipped: list[str] = []

        # 지식
        self.knowledge = KnowledgeBook()

        # 번식
        self.reproduction_cooldown = 0
        self.children_count = 0

        # 전투
        self.kill_count = 0
        self.faction_id: int = -1  # -1 = 무소속

        # 화폐 (발견 시)
        self.currency: CurrencyType = CurrencyType.NONE
        self.money: float = 0.0

        # 영토/주거 추적
        self.home_x: int | None = x
        self.home_y: int | None = y
        self.residence_counter: dict[tuple[int, int], int] = {}
        self.visited_tiles: deque[tuple[int, int]] = deque(maxlen=config.HOME_SITE_MEMORY)

        # 행동 지속성 (여러 틱에 걸친 행동 완료 추적)
        self.action_progress: float = 0.0

        # 건물 목록
        self.buildings: list[str] = []

        # 두뇌 (의사결정 엔진) - 외부에서 교체 가능
        self.brain: Brain = RuleBasedBrain()

        # 이데올로기 (Phase 3.1)
        self.ideology: str = "none"

        # 메일박스 (다른 개체의 메시지 수신)
        self.mailbox: deque = deque(maxlen=50)

        # 통계 디버깅용
        self.last_action: str = "idle"

    # ──────────────────────────────────────────
    # 코어 속성
    # ──────────────────────────────────────────
    @property
    def speed(self) -> float:
        base = config.BASE_SPEED * (0.5 + 1.0 * self.genome.speed)
        if hasattr(self, "_season_speed_mod"):
            base *= self._season_speed_mod
        return base

    @property
    def inventory_used(self) -> int:
        return len(self.inventory)

    @property
    def inventory_is_full(self) -> bool:
        return self.inventory_used >= self.max_inventory_slots

    def total_wealth(self) -> float:
        """개체의 총 자산 (인벤토리 + 화폐, 기술 보정 포함)."""
        effects = self.get_combined_effects()
        gold_mult = effects.get("gold_value_mult", 1.0)
        total = self.money
        for rtype, amount in self.inventory.items():
            if rtype == "gold":
                total += amount * gold_mult
            else:
                total += amount
        return total

    def get_effective_attack(self) -> float:
        atk = self.attack
        for item in self.equipped:
            bonus = config.CRAFT_BONUS.get(item, {}).get("attack", 0)
            effects = self.get_combined_effects()
            if effects.get("craft_weapon_boost", 0) >= 1 and "sword" in item:
                bonus *= 2.0
            atk += bonus
        return atk

    def get_effective_defense(self) -> float:
        df = self.defense
        for item in self.equipped:
            bonus = config.CRAFT_BONUS.get(item, {}).get("defense", 0)
            df += bonus
        return df

    def get_combined_effects(self) -> dict[str, float]:
        """보유한 모든 기술 effects + 건물 effects를 통합한 dict 반환 (O(k) 조회)."""
        combined: dict[str, float] = {}
        for tech_name in self.knowledge.known:
            effect = config.TECH_EFFECTS_MAP.get(tech_name)
            if effect:
                for k, v in effect.items():
                    if isinstance(v, (int, float)):
                        combined[k] = combined.get(k, 0.0) + v
                    elif isinstance(v, bool) and v:
                        combined[k] = 1.0
        building_effects = bld.get_building_effects(self)
        for k, v in building_effects.items():
            combined[k] = combined.get(k, 0.0) + v
        return combined

    def get_gather_bonus(self, resource_type: str) -> float:
        return entity_craft.get_gather_bonus(self, resource_type)

    # ──────────────────────────────────────────
    # 외교 헬퍼 (Phase 2.1)
    # ──────────────────────────────────────────
    def has_trade_pact_with(self, other_entity: Entity,
                            faction_registry: dict[int, Faction]) -> bool:
        from .faction import Faction as F
        if self.faction_id < 0 or other_entity.faction_id < 0:
            return False
        my_faction = faction_registry.get(self.faction_id)
        target_faction = faction_registry.get(other_entity.faction_id)
        if my_faction and target_faction:
            return (my_faction.has_treaty_with(target_faction.faction_id, "TRADE_PACT")
                    or my_faction.has_treaty_with(target_faction.faction_id, "ALLIANCE"))
        return False

    # ──────────────────────────────────────────
    # 행동 결정 — brain에 위임
    # ──────────────────────────────────────────
    def decide_action(self, world: World, market: Optional[Market]) -> EntityState:
        """두뇌(brain)에 행동 결정을 위임합니다.

        brain 속성을 교체(RuleBasedBrain / SmartBrain)하면
        의사결정 방식이 바뀝니다.
        """
        return self.brain.decide(self, world, market)

    def curiosity_drive(self) -> float:
        """주변에 얼마나 방문하지 않은 타일이 있는지에 따른 호기심."""
        return self.genome.curiosity * self._rng.uniform(0.5, 1.0)

    # ──────────────────────────────────────────
    # 행동 실행
    # ──────────────────────────────────────────
    def execute_action(self, state: EntityState,
                       world: World, market: Optional[Market]) -> list[dict]:
        """선택된 행동을 실행하고 이벤트 로그 반환."""
        events: list[dict] = []
        effects = self.get_combined_effects()
        energy_efficiency = effects.get("energy_efficiency", 0.0)
        season_mult = getattr(self, "_season_energy_mult", 1.0)
        energy_cost = config.ENERGY_COST.get(state.name.lower(), 1.0) * (1.0 - energy_efficiency) * season_mult

        if state == EntityState.EXPLORE:
            result = entity_action.do_explore(self, world)
            events.extend(result)
        elif state == EntityState.GATHER:
            result, gathered = entity_action.do_gather(self, world)
            events.extend(result)
        elif state == EntityState.CONSUME:
            result = entity_action.do_consume(self)
            events.extend(result)
        elif state == EntityState.TRADE:
            if market:
                result = entity_action.do_trade(self, world, market)
                events.extend(result)
        elif state == EntityState.CRAFT:
            result = self._do_craft()
            events.extend(result)
        elif state == EntityState.REPRODUCE:
            result = self._do_reproduce(world)
            events.extend(result)
        elif state == EntityState.COMBAT:
            result = self._do_combat(world)
            events.extend(result)
        elif state == EntityState.CONSTRUCT:
            result = self._do_construct()
            events.extend(result)
        elif state == EntityState.DIE:
            self.alive = False
            events.append(self._event("death", {"reason": "energy_depleted"}))
            return events

        self.energy -= energy_cost
        self.state = state
        self.last_action = state.name.lower()

        if self.energy <= 0:
            self.alive = False
            events.append(self._event("energy_depleted", {"reason": "energy_depleted_during_action"}))
        return events

    def _do_craft(self) -> list[dict]:
        return entity_craft.do_craft(self)

    def _do_construct(self) -> list[dict]:
        return entity_craft.do_construct(self)

    def _do_reproduce(self, world: World) -> list[dict]:
        return entity_reproduce.do_reproduce(self, world)

    def _do_combat(self, world: World) -> list[dict]:
        return entity_combat.do_combat(self, world)

    # ──────────────────────────────────────────
    # 유틸리티
    # ──────────────────────────────────────────
    def _event(self, event_type: str, data: dict) -> dict:
        return {
            "tick": 0,  # 실제 틱은 엔진에서 채움
            "type": event_type,
            "entity_id": self.eid,
            "entity_name": self.name,
            "data": data,
        }

    def age_update(self) -> None:
        return entity_reproduce.age_update(self)

    def apply_knowledge_effects(self) -> None:
        """보유 기술 효과를 개체 속성에 적용.
        기술 습득 시점에 한 번 호출. 전투/행동 시에는 get_combined_effects() 사용.
        """
        effects = self.get_combined_effects()
        # 방어력
        if "defense" in effects:
            self.defense = config.BASE_DEFENSE + 5.0 * self.genome.endurance
            self.defense += effects["defense"]
        # 공격력
        if "attack" in effects:
            self.attack = config.BASE_ATTACK + 10.0 * self.genome.strength
            self.attack += effects["attack"]
        # 최대 에너지
        if "max_energy" in effects:
            base = config.BASE_MAX_ENERGY * (0.7 + 0.6 * self.genome.endurance)
            self.max_energy = base + effects["max_energy"]
            self.energy = min(self.energy, self.max_energy)
        # 최대 인벤토리
        if "max_inventory" in effects:
            self.max_inventory_slots = config.BASE_INVENTORY_SLOTS + int(effects["max_inventory"])

    def status_summary(self) -> str:
        """한 줄 상태 요약."""
        inv = ", ".join(f"{k}:{v:.0f}" for k, v in
                        sorted(self.inventory.items()))
        equipped = f"[{','.join(self.equipped)}]" if self.equipped else ""
        return (f"{self.name} E:{self.energy:.0f}/{self.max_energy:.0f} "
                f"♥{self.age} ⚔{self.kill_count} "
                f"{equipped} | {inv}")
