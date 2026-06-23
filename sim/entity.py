"""개체 — 시뮬레이션의 기본 단위. 상태 기반 행동 + 진화."""

from __future__ import annotations

import math
import random
from collections import Counter
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import TYPE_CHECKING, Optional

from . import config
from . import buildings as bld
from .brain import Brain, RuleBasedBrain, create_brain
from .faction import Faction
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
                 name: str | None = None):
        self.x = x
        self.y = y
        self.genome = genome or Genome.random_initial()
        self.name = name or f"E{id(self) % 10000:04d}"

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
        self.visited_tiles: list[tuple[int, int]] = []

        # 행동 지속성 (여러 틱에 걸친 행동 완료 추적)
        self.action_progress: float = 0.0

        # 건물 목록
        self.buildings: list[str] = []

        # 두뇌 (의사결정 엔진) - 외부에서 교체 가능
        self.brain: Brain = RuleBasedBrain()

        # 메일박스 (다른 개체의 메시지 수신)
        self.mailbox: list[dict] = []

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
        """보유한 모든 기술 effects + 건물 effects를 통합한 dict 반환."""
        combined: dict[str, float] = {}
        for tech_name in self.knowledge.known:
            for tdef in config.TECH_TREE:
                if tdef.name == tech_name:
                    for k, v in tdef.effect.items():
                        if isinstance(v, (int, float)):
                            combined[k] = combined.get(k, 0.0) + v
                        elif isinstance(v, bool) and v:
                            combined[k] = 1.0
        building_effects = bld.get_building_effects(self)
        for k, v in building_effects.items():
            combined[k] = combined.get(k, 0.0) + v
        return combined

    def get_gather_bonus(self, resource_type: str) -> float:
        bonus = 1.0
        for item in self.equipped:
            bonus += config.CRAFT_BONUS.get(item, {}).get(
                f"gather_{resource_type}", 0)
        effects = self.get_combined_effects()
        gather_key = f"gather_{resource_type}"
        if gather_key in effects:
            bonus *= effects[gather_key]
        return bonus

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
        return self.genome.curiosity * random.uniform(0.5, 1.0)

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
            result = self._do_explore(world)
            events.extend(result)
        elif state == EntityState.GATHER:
            result, gathered = self._do_gather(world)
            events.extend(result)
        elif state == EntityState.CONSUME:
            result = self._do_consume()
            events.extend(result)
        elif state == EntityState.TRADE:
            if market:
                result = self._do_trade(world, market)
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

    # ── 세부 행동 구현 ──

    def _do_explore(self, world: World) -> list[dict]:
        """이웃 타일로 이동. 항해술(sailing) 보유 시 물 타일 통과 및 추가 이동."""
        effects = self.get_combined_effects()
        can_cross_water = effects.get("cross_water", 0) >= 1
        explore_range = int(effects.get("explore_range", 0))

        neighbors = world.get_neighbors(self.x, self.y, filter_traversable=not can_cross_water)
        if not neighbors:
            return []

        if self.genome.curiosity > 0.6 and len(neighbors) > 2:
            unvisited = [n for n in neighbors if n not in self.visited_tiles]
            if unvisited:
                nx, ny = random.choice(unvisited)
                self.x, self.y = nx, ny
                # 추가 이동 (sailing)
                if explore_range > 0 and random.random() < 0.3:
                    extended = world.get_neighbors(nx, ny, filter_traversable=not can_cross_water)
                    if extended:
                        ex, ey = random.choice(extended)
                        self.x, self.y = ex, ey
                return [self._event("move", {"to": (self.x, self.y)})]

        nx, ny = random.choice(neighbors)
        self.x, self.y = nx, ny
        return [self._event("move", {"to": (nx, ny)})]

    def _do_gather(self, world: World) -> tuple[list[dict], float]:
        """현재 타일에서 자원 채취."""
        events = []
        total_gathered = 0.0
        tile = world.tile_at(self.x, self.y)
        if not tile:
            return events, 0.0

        effects = self.get_combined_effects()
        max_food_storage = effects.get("max_food_storage", 0.0)

        # 특화에 따라 선호 자원 결정
        pref = self.genome.specialization
        gather_order = ["food", "wood", "stone", "iron", "gold"]

        if pref == "farmer":
            gather_order = ["food", "wood", "stone", "iron", "gold"]
        elif pref == "miner":
            gather_order = ["stone", "iron", "gold", "wood", "food"]

        for rtype in gather_order:
            if self.inventory_is_full:
                break
            amount = self.inventory.get(rtype, 0)
            max_slot = 8
            if rtype == "food" and max_food_storage > 0:
                max_slot += int(max_food_storage)
            if amount >= max_slot:
                continue

            season_gather = getattr(self, "_season_gather_mult", 1.0)
            can_gather = 2.0 * self.get_gather_bonus(rtype) * season_gather
            gathered = tile.gather(rtype, can_gather)
            if gathered > 0:
                self.inventory[rtype] = self.inventory.get(rtype, 0) + gathered
                total_gathered += gathered
                events.append(self._event("gather", {
                    "resource": rtype, "amount": round(gathered, 2)
                }))
            if self.inventory_is_full:
                break

        return events, total_gathered

    def _do_consume(self) -> list[dict]:
        """식량을 소비해 에너지 회복."""
        food = self.inventory.get("food", 0)
        if food <= 0:
            return []

        effects = self.get_combined_effects()
        food_energy_mult = effects.get("food_energy_mult", 1.0)

        consume = min(food, 2.0)
        self.inventory["food"] = food - consume
        gained = consume * config.FOOD_ENERGY * food_energy_mult
        self.energy = min(self.max_energy, self.energy + gained)
        return [self._event("consume", {"food": consume, "energy_gained": gained})]

    def _do_trade(self, world: World, market: Market) -> list[dict]:
        """시장에 매도 주문 등록 및 주변 개체와 직거래."""
        events = []
        effects = self.get_combined_effects()
        trade_efficiency = effects.get("trade_efficiency", 0.0)
        trade_gold_bonus = effects.get("trade_gold_bonus", 0.0)
        market_tax_discount = effects.get("market_tax_discount", 0.0)

        # 1. 팔 surplus 자원: 매도 주문 등록
        for rtype, amount in list(self.inventory.items()):
            surplus_threshold = 4 if rtype == "food" else 3
            if amount > surplus_threshold:
                sell_qty = amount * 0.5  # 절반 판매
                price_mult = 0.85 + 0.3 * self.genome.sociability + trade_efficiency * 0.3
                unit_price = market.get_average_price(rtype) * price_mult

                # 금 거래 보너스 (alchemy)
                if rtype == "gold" and trade_gold_bonus > 0:
                    unit_price *= 1.0 + trade_gold_bonus

                market.place_order(
                    seller_id=id(self),
                    resource_type=rtype,
                    quantity=sell_qty,
                    price=unit_price,
                    is_buy=False,
                )
                events.append(self._event("trade_offer", {
                    "sell": rtype, "qty": round(sell_qty, 1), "unit_price": round(unit_price, 2)
                }))

        # 2. 살 자원: 부족한 자원 매수
        for rtype in ["food", "wood", "stone"]:
            if self.inventory.get(rtype, 0) < 2:
                buy_qty = 3 - self.inventory.get(rtype, 0)
                price_mult = 0.85 + 0.3 * self.genome.sociability + trade_efficiency * 0.3
                unit_price = market.get_average_price(rtype) * price_mult
                market.place_order(
                    seller_id=id(self),
                    resource_type=rtype,
                    quantity=buy_qty,
                    price=unit_price,
                    is_buy=True,
                )
                events.append(self._event("trade_bid", {
                    "buy": rtype, "qty": round(buy_qty, 1), "unit_price": round(unit_price, 2)
                }))

        return events

    def _do_craft(self) -> list[dict]:
        """인벤토리 재료를 소비해 도구/무기 제작."""
        effects = self.get_combined_effects()
        can_craft_iron = effects.get("craft_iron", 0) >= 1

        for recipe_name, ingredients in config.CRAFT_RECIPES.items():
            if recipe_name in self.equipped:
                continue
            # 금속 관련 레시피는 야금술(metallurgy) 필요
            if "iron" in recipe_name and not can_craft_iron:
                continue

            if all(self.inventory.get(mat, 0) >= qty for mat, qty in ingredients):
                for mat, qty in ingredients:
                    self.inventory[mat] -= qty
                    if self.inventory[mat] <= 0:
                        del self.inventory[mat]
                self.equipped.append(recipe_name)
                return [self._event("craft", {"item": recipe_name})]
        return []

    def _do_construct(self) -> list[dict]:
        for bdef in config.BUILDING_DEFS:
            if bdef.name in self.buildings:
                continue
            if bld.construct(self, bdef, None):
                return [self._event("construct", {"building": bdef.name})]
        return []

    def _do_reproduce(self, world: World) -> list[dict]:
        """자손 생산. 돌연변이 적용."""
        neighbors = world.get_neighbors(self.x, self.y)
        if not neighbors:
            return []

        # 짝 찾기 (같은 타일 또는 인접 타일)
        partner = None
        for eid, other in world.entities.items():
            if (other.alive and other != self
                    and other.reproduction_cooldown <= 0
                    and other.energy / other.max_energy > 0.5
                    and abs(other.x - self.x) <= 1
                    and abs(other.y - self.y) <= 1):
                partner = other
                break

        if partner is None:
            # 무성생식 (단독 번식)
            child_genome = self.genome.mutate()
        else:
            # 유성생식 (교차 + 변이)
            child_genome = Genome.crossover(self.genome, partner.genome)
            child_genome = child_genome.mutate()
            partner.reproduction_cooldown = config.REPRODUCTION_COOLDOWN
            partner.children_count += 1
            partner.energy -= config.ENERGY_COST["reproduce"] * 0.5

        # 자손 위치
        nx, ny = random.choice(neighbors)

        child = Entity(
            x=nx, y=ny,
            genome=child_genome,
            name=f"{self.name}-{self.children_count + 1}",
        )
        # 부모 지식 일부 상속 (문화적 진화)
        transfer_count = max(1, int(self.knowledge.count() * 0.3))
        for tech in list(self.knowledge.known)[:transfer_count]:
            child.knowledge.learn(tech)

        # 부모 자원 일부 상속
        for rtype in ["food", "wood"]:
            bequest = self.inventory.get(rtype, 0) * 0.2
            if bequest > 0:
                child.inventory[rtype] = bequest
                self.inventory[rtype] -= bequest

        world.spawn_entity(child)
        self.children_count += 1
        self.reproduction_cooldown = config.REPRODUCTION_COOLDOWN
        self.energy -= config.ENERGY_COST["reproduce"]

        return [self._event("reproduce", {
            "child": child.name,
            "partner": partner.name if partner else None,
            "sexual": partner is not None,
            "child_gen": child_genome.generation,
        })]

    def _do_combat(self, world: World) -> list[dict]:
        """강화된 전투: 다중 개체 + 동맹 지원 + 장비 파괴 + 지식 약탈."""
        events = []
        same_tile_targets = [(eid, e) for eid, e in world.entities.items()
                             if (e.x, e.y) == (self.x, self.y) and e != self and e.alive]
        if not same_tile_targets:
            return []

        target_id, target = same_tile_targets[0]

        # ── 동맹 지원: 같은 파벌 멤버가 근처에 있으면 전투 합류 ──
        allies: list[Entity] = []
        if self.faction_id >= 0:
            faction_registry = getattr(world, "faction_registry", {})
            my_faction = faction_registry.get(self.faction_id)
            if my_faction:
                for eid, ent in world.entities.items():
                    if (ent.alive and ent != self and ent != target
                            and ent.faction_id == self.faction_id):
                        dist = abs(ent.x - self.x) + abs(ent.y - self.y)
                        if dist <= config.FACTION_ALLY_SUPPORT_RADIUS:
                            allies.append(ent)

        # ── 영토 보너스 ──
        effects = self.get_combined_effects()
        extra_home_bonus = effects.get("home_bonus_extra", 0.0)
        home_bonus = 1.0
        if self.home_x is not None:
            dist_to_home = abs(self.x - self.home_x) + abs(self.y - self.home_y)
            if dist_to_home <= config.TERRITORY_RADIUS:
                home_bonus = 1.0 + config.COMBAT_HOME_BONUS + extra_home_bonus

        # 동맹 보너스
        ally_bonus = 1.0
        if allies:
            ally_bonus = 1.0 + config.FACTION_ALLY_COMBAT_BONUS * min(len(allies), 3)

        # 파벌 사기 보너스 (bureaucracy)
        faction_morale = effects.get("faction_morale", 0.0)
        if self.faction_id >= 0 and faction_morale > 0:
            ally_bonus += faction_morale

        my_atk = self.get_effective_attack() * home_bonus * ally_bonus
        my_def = self.get_effective_defense() * home_bonus * ally_bonus

        # 상대 영토 보너스
        target_home_bonus = 1.0
        other_home_x = getattr(target, "home_x", None)
        other_home_y = getattr(target, "home_y", None)
        if other_home_x is not None:
            other_dist = abs(target.x - other_home_x) + abs(target.y - other_home_y)
            if other_dist <= config.TERRITORY_RADIUS:
                target_home_bonus = 1.0 + config.COMBAT_HOME_BONUS

        # 상대 동맹 지원
        target_ally_bonus = 1.0
        target_allies: list[Entity] = []
        if target.faction_id >= 0:
            faction_registry = getattr(world, "faction_registry", {})
            target_faction = faction_registry.get(target.faction_id)
            if target_faction:
                for eid, ent in world.entities.items():
                    if (ent.alive and ent != target and ent != self
                            and ent.faction_id == target.faction_id):
                        dist = abs(ent.x - target.x) + abs(ent.y - target.y)
                        if dist <= config.FACTION_ALLY_SUPPORT_RADIUS:
                            target_allies.append(ent)
        if target_allies:
            target_ally_bonus = 1.0 + config.FACTION_ALLY_COMBAT_BONUS * min(len(target_allies), 3)

        target_atk = target.get_effective_attack() * target_home_bonus * target_ally_bonus
        target_def = target.get_effective_defense() * target_home_bonus * target_ally_bonus

        # ── 데미지 계산 ──
        base_damage = config.COMBAT_BASE_DAMAGE
        variance = 1.0 + random.uniform(-config.COMBAT_DAMAGE_VARIANCE,
                                         config.COMBAT_DAMAGE_VARIANCE)
        damage_dealt = max(1, (my_atk / (target_def + 1)) * base_damage * variance)
        damage_taken = max(1, (target_atk / (my_def + 1)) * base_damage * variance * 0.7)

        target.energy -= damage_dealt
        self.energy -= damage_taken

        # ── 동맹도 데미지 기여 (일부) ──
        ally_damage = 0.0
        for ally in allies:
            ally_contrib = ally.get_effective_attack() * config.COMBAT_ALLY_CONTRIBUTION
            ally_damage += ally_contrib
            ally.energy -= config.ENERGY_COST["combat"] * 0.3  # 동맹도 에너지 소모
            events.append(self._event("ally_attack", {
                "ally": ally.name,
                "damage_contrib": round(ally_contrib, 1),
            }))
        if ally_damage > 0:
            target.energy -= ally_damage * 0.5  # 동맹 데미지 50%만 적용 (밸런스)

        target_killed = target.energy <= 0
        if target_killed:
            target.alive = False
            self.kill_count += 1

        # ── 전투 이벤트 ──
        ally_names = [a.name for a in allies]
        target_ally_names = [a.name for a in target_allies]
        events.append(self._event("combat", {
            "target": target.name,
            "damage_dealt": round(damage_dealt, 1),
            "damage_taken": round(damage_taken, 1),
            "allies": ally_names,
            "target_allies": target_ally_names,
            "target_alive": not target_killed,
        }))

        # ── 건물 파괴 (전투 후) ──
        destroyed = bld.destroy_random_building(self)
        if destroyed:
            events.append(self._event("building_destroyed", {"building": destroyed}))
        if target_killed:
            destroyed_target = bld.destroy_random_building(target)
            if destroyed_target:
                events.append(self._event("building_destroyed",
                                           {"building": destroyed_target, "target": target.name}))

        # ── 장비 파괴 (전투 후) ──
        for item in list(self.equipped):
            if random.random() < config.EQUIPMENT_BREAK_CHANCE:
                self.equipped.remove(item)
                events.append(self._event("equipment_broken", {
                    "item": item,
                }))
        if target_killed:
            for item in list(target.equipped):
                if random.random() < config.EQUIPMENT_BREAK_CHANCE:
                    target.equipped.remove(item)

        # ── 승리: 약탈 ──
        if target_killed:
            # 인벤토리 약탈
            loot = {}
            for rtype, amount in target.inventory.items():
                loot_qty = amount * config.COMBAT_WINNER_LOOT_RATIO
                if loot_qty > 0:
                    self.inventory[rtype] = self.inventory.get(rtype, 0) + loot_qty
                    loot[rtype] = round(loot_qty, 1)
            events.append(self._event("loot", {
                "target": target.name,
                "loot": loot,
            }))

            # 장비 약탈 (확률적)
            if target.equipped and random.random() < config.COMBAT_EQUIPMENT_LOOT_CHANCE:
                stolen_item = random.choice(target.equipped)
                target.equipped.remove(stolen_item)
                if len(self.equipped) < 3:  # 장비 슬롯 제한
                    self.equipped.append(stolen_item)
                    events.append(self._event("equipment_loot", {
                        "item": stolen_item,
                        "from": target.name,
                    }))

            # 지식 약탈 (확률적)
            if (target.knowledge.count() > 0
                    and random.random() < config.COMBAT_KNOWLEDGE_LOOT_CHANCE):
                stolen_knowledge = random.choice(list(target.knowledge.known))
                self.knowledge.learn(stolen_knowledge)
                events.append(self._event("knowledge_loot", {
                    "tech": stolen_knowledge,
                    "from": target.name,
                }))

        return events

    # ──────────────────────────────────────────
    # 유틸리티
    # ──────────────────────────────────────────
    def _event(self, event_type: str, data: dict) -> dict:
        return {
            "tick": 0,  # 실제 틱은 엔진에서 채움
            "type": event_type,
            "entity_id": id(self),
            "entity_name": self.name,
            "data": data,
        }

    def age_update(self) -> None:
        """나이 먹기. 수명 초과 시 에너지 급감."""
        self.age += 1
        if self.age > self.max_age:
            self.energy -= 5.0  # 노화
        if self.reproduction_cooldown > 0:
            self.reproduction_cooldown -= 1

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
