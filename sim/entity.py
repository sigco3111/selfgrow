"""개체 — 시뮬레이션의 기본 단위. 상태 기반 행동 + 진화."""

from __future__ import annotations

import math
import random
from collections import Counter
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import TYPE_CHECKING, Optional

from . import config
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

        # 통계 디버깅용
        self.last_action: str = "idle"

    # ──────────────────────────────────────────
    # 코어 속성
    # ──────────────────────────────────────────
    @property
    def speed(self) -> float:
        return config.BASE_SPEED * (0.5 + 1.0 * self.genome.speed)

    @property
    def inventory_used(self) -> int:
        return len(self.inventory)

    @property
    def inventory_is_full(self) -> bool:
        return self.inventory_used >= self.max_inventory_slots

    def total_wealth(self) -> float:
        """개체의 총 자산 (인벤토리 + 화폐)."""
        return sum(self.inventory.values()) + self.money

    def get_effective_attack(self) -> float:
        atk = self.attack
        for item in self.equipped:
            bonus = config.CRAFT_BONUS.get(item, {}).get("attack", 0)
            atk += bonus
        return atk

    def get_effective_defense(self) -> float:
        df = self.defense
        for item in self.equipped:
            bonus = config.CRAFT_BONUS.get(item, {}).get("defense", 0)
            df += bonus
        return df

    def get_gather_bonus(self, resource_type: str) -> float:
        bonus = 1.0
        for item in self.equipped:
            bonus += config.CRAFT_BONUS.get(item, {}).get(
                f"gather_{resource_type}", 0)
        # 기술 보너스
        if self.knowledge.know("basic_agriculture") and resource_type == "food":
            bonus *= 1.5
        if self.knowledge.know("irrigation") and resource_type == "food":
            bonus *= 2.0
        if self.knowledge.know("mining") and resource_type in ("stone", "iron"):
            bonus *= 1.5
        return bonus

    # ──────────────────────────────────────────
    # 행동 결정 (Decision Engine)
    # ──────────────────────────────────────────
    def decide_action(self, world: World, market: Optional[Market]) -> EntityState:
        """현재 상태 + 환경 + 유전자에 기반해 행동 점수 계산 후 최고 선택."""
        if self.energy <= 0:
            return EntityState.DIE

        scores: dict[EntityState, float] = {}

        # 1. CONSUME — 배고프면 먹기
        hunger_ratio = 1.0 - (self.energy / self.max_energy)
        food_available = self.inventory.get("food", 0)
        if food_available > 0 and hunger_ratio > 0.2:
            scores[EntityState.CONSUME] = hunger_ratio * 100.0
        elif hunger_ratio > 0.6:
            # 매우 배고프면 채집부터
            scores[EntityState.GATHER] = hunger_ratio * 90.0

        # 2. REPRODUCE — 번식 조건 (까다롭게)
        energy_ratio = self.energy / self.max_energy
        food_stored = self.inventory.get("food", 0)
        if (energy_ratio > config.REPRODUCTION_ENERGY_RATIO
                and self.reproduction_cooldown <= 0
                and food_stored >= config.REPRODUCTION_MIN_FOOD
                and self.inventory_used >= 3):
            scores[EntityState.REPRODUCE] = (energy_ratio * 40.0
                                             * (0.3 + self.genome.fertility * 0.7))

        # 3. GATHER — 자원 채집
        tile = world.tile_at(self.x, self.y)
        if tile and tile.total_resources() > 0 and not self.inventory_is_full:
            need = self._resource_need()
            if need > 0:
                scores[EntityState.GATHER] = need * 30.0 + random.uniform(0, 10)

        # 4. TRADE — 거래 가능성
        if market and not self.inventory_is_full:
            # 거래할 게 있으면
            surplus = self._has_surplus()
            if surplus:
                scores[EntityState.TRADE] = (
                    self.genome.sociability * 50.0 + random.uniform(0, 10))

        # 5. CRAFT — 제작
        if self.genome.industry > 0.4:
            can_craft = self._can_craft_anything()
            if can_craft:
                scores[EntityState.CRAFT] = (
                    self.genome.industry * 40.0 + random.uniform(0, 10))

        # 6. COMBAT — 공격 (약탈 + 영토방어 + 일반)
        combat_score = 0.0
        food_stored = self.inventory.get("food", 0)
        nearby_entities = [(eid, e) for eid, e in world.entities.items()
                           if e.alive and e != self
                           and abs(e.x - self.x) <= 1 and abs(e.y - self.y) <= 1]
        same_tile = [(eid, e) for (eid, e) in nearby_entities
                     if (e.x, e.y) == (self.x, self.y)]

        # 6a. 약탈: 식량이 부족하고 이웃이 식량을 가지고 있으면 (충분한 에너지 있을 때만)
        if food_stored < 3 and energy_ratio > 0.3:
            for _, neighbor in nearby_entities:
                if neighbor.inventory.get("food", 0) >= 3:
                    combat_score = max(combat_score, 80.0 + (1.0 - energy_ratio) * 30.0)
                    break

        # 6b. 영토방어: 내 본거지 근처에 다른 개체가 있으면
        if self.home_x is not None:
            dist_to_home = abs(self.x - self.home_x) + abs(self.y - self.home_y)
            if dist_to_home <= config.TERRITORY_RADIUS:
                for _, neighbor in same_tile:
                    other_home = getattr(neighbor, "home_x", None)
                    if other_home is not None:
                        other_dist = abs(neighbor.x - other_home) + abs(neighbor.y - other_home)
                        if other_dist > config.TERRITORY_RADIUS:
                            combat_score = max(combat_score, 60.0 * self.genome.aggression)

        # 6c. 일반 공격: 같은 타일에 다른 개체가 있으면
        if same_tile:
            if self.genome.aggression > 0.2:
                combat_score = max(combat_score,
                                   self.genome.aggression * 30.0 + random.uniform(0, 10))
            elif self.genome.aggression > 0.1:
                # 약간만 공격적이어도 일정 확률로 공격
                combat_score = max(combat_score, self.genome.aggression * 15.0)

        if combat_score > 0:
            scores[EntityState.COMBAT] = combat_score

        # 7. EXPLORE — 기본 행동 (항상 선택 가능)
        if self.curiosity_drive() > 0:
            scores[EntityState.EXPLORE] = (
                self.genome.curiosity * 20.0 + random.uniform(0, 15))

        # 8. IDLE — 아무것도 안 함 (마지막 보루)
        scores[EntityState.IDLE] = 5.0

        # 최고 점수 선택
        best = max(scores, key=scores.get)
        return best

    def _resource_need(self) -> float:
        """자원 부족도 (0~1). 높을수록 채집이 시급."""
        need = 0.0
        # 식량
        food = self.inventory.get("food", 0)
        if food < 5:
            need += 0.5
        # 목재
        wood = self.inventory.get("wood", 0)
        if wood < 3:
            need += 0.2
        # 돌
        stone = self.inventory.get("stone", 0)
        if stone < 3:
            need += 0.15
        # 철
        iron = self.inventory.get("iron", 0)
        if iron < 2 and self.genome.specialization in ("miner", "warrior", "crafter"):
            need += 0.15
        return min(1.0, need)

    def _has_surplus(self) -> bool:
        """거래할 여분 자원이 있는가?"""
        for rtype, amount in self.inventory.items():
            if rtype == "food" and amount > 5:
                return True
            if rtype != "food" and amount > 3:
                return True
        return False

    def _can_craft_anything(self) -> bool:
        for recipe_name, ingredients in config.CRAFT_RECIPES.items():
            # 장비 중복 확인
            if recipe_name in self.equipped:
                continue
            if all(self.inventory.get(mat, 0) >= qty for mat, qty in ingredients):
                return True
        return False

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
        energy_cost = config.ENERGY_COST.get(state.name.lower(), 1.0)

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
        """이웃 타일로 이동."""
        neighbors = world.get_neighbors(self.x, self.y)
        if not neighbors:
            return []

        if self.genome.curiosity > 0.6 and len(neighbors) > 2:
            unvisited = [n for n in neighbors if n not in self.visited_tiles]
            if unvisited:
                nx, ny = random.choice(unvisited)
                self.x, self.y = nx, ny
                return [self._event("move", {"to": (nx, ny)})]

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
            max_slot = 8  # 한 자원당 최대 8단위까지
            if amount >= max_slot:
                continue

            can_gather = 2.0 * self.get_gather_bonus(rtype)
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

        consume = min(food, 2.0)
        self.inventory["food"] = food - consume
        gained = consume * config.FOOD_ENERGY
        self.energy = min(self.max_energy, self.energy + gained)
        return [self._event("consume", {"food": consume, "energy_gained": gained})]

    def _do_trade(self, world: World, market: Market) -> list[dict]:
        """시장에 매도 주문 등록 및 주변 개체와 직거래."""
        events = []

        # 1. 팔 surplus 자원: 매도 주문 등록
        for rtype, amount in list(self.inventory.items()):
            if amount > 3:
                sell_qty = amount * 0.5  # 절반 판매
                unit_price = market.get_average_price(rtype) * (0.85 + 0.3 * self.genome.sociability)
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
                unit_price = market.get_average_price(rtype) * (0.85 + 0.3 * self.genome.sociability)
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
        for recipe_name, ingredients in config.CRAFT_RECIPES.items():
            if recipe_name in self.equipped:
                continue
            # 금속 관련 레시피는 야금술 필요
            if "iron" in recipe_name and not self.knowledge.know("metallurgy"):
                continue

            if all(self.inventory.get(mat, 0) >= qty for mat, qty in ingredients):
                for mat, qty in ingredients:
                    self.inventory[mat] -= qty
                    if self.inventory[mat] <= 0:
                        del self.inventory[mat]
                self.equipped.append(recipe_name)
                return [self._event("craft", {"item": recipe_name})]
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
        """같은 타일의 적과 전투."""
        same_tile = [(eid, e) for eid, e in world.entities.items()
                     if (e.x, e.y) == (self.x, self.y) and e != self and e.alive]
        if not same_tile:
            return []

        target_id, target = same_tile[0]

        # 영토 보너스: 본거지 근처에서 싸우면 공/방 +30%
        home_bonus = 1.0
        if self.home_x is not None:
            dist_to_home = abs(self.x - self.home_x) + abs(self.y - self.home_y)
            if dist_to_home <= config.TERRITORY_RADIUS:
                home_bonus = 1.0 + config.COMBAT_HOME_BONUS

        my_atk = self.get_effective_attack() * home_bonus
        target_def = target.get_effective_defense()

        # 상대가 본거지 근처이면 방어 보너스
        target_home_bonus = 1.0
        other_home_x = getattr(target, "home_x", None)
        other_home_y = getattr(target, "home_y", None)
        if other_home_x is not None:
            other_dist = abs(target.x - other_home_x) + abs(target.y - other_home_y)
            if other_dist <= config.TERRITORY_RADIUS:
                target_home_bonus = 1.0 + config.COMBAT_HOME_BONUS
        target_def = target.get_effective_defense() * target_home_bonus

        # 데미지 계산
        base_damage = config.COMBAT_BASE_DAMAGE
        variance = 1.0 + random.uniform(-config.COMBAT_DAMAGE_VARIANCE,
                                         config.COMBAT_DAMAGE_VARIANCE)
        damage_dealt = max(1, (my_atk / (target_def + 1)) * base_damage * variance)
        damage_taken = max(1, (target.get_effective_attack() / (self.get_effective_defense() + 1))
                          * base_damage * variance * 0.7)

        target.energy -= damage_dealt
        self.energy -= damage_taken

        # 승리: 패자 인벤토리 약탈
        target_killed = target.energy <= 0
        if target_killed:
            target.alive = False
            self.kill_count += 1

        events = [self._event("combat", {
            "target": target.name,
            "damage_dealt": round(damage_dealt, 1),
            "damage_taken": round(damage_taken, 1),
            "target_alive": not target_killed,
        })]

        if target_killed:
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
        """보유 기술 효과 적용."""
        bonuses = {
            "defense": 0,
            "sociability": 0,
        }
        for tech_name in self.knowledge.known:
            from .config import TECH_TREE
            for tdef in TECH_TREE:
                if tdef.name == tech_name:
                    effect = tdef.effect
                    if "defense" in effect:
                        self.defense += effect["defense"]
                    if "sociability" in effect:
                        # 적용을 genome에 직접 하지는 않고 getter에서 처리
                        pass

    def status_summary(self) -> str:
        """한 줄 상태 요약."""
        inv = ", ".join(f"{k}:{v:.0f}" for k, v in
                        sorted(self.inventory.items()))
        equipped = f"[{','.join(self.equipped)}]" if self.equipped else ""
        return (f"{self.name} E:{self.energy:.0f}/{self.max_energy:.0f} "
                f"♥{self.age} ⚔{self.kill_count} "
                f"{equipped} | {inv}")
