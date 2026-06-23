"""듀얼 브레인 시스템 — 개체의 의사결정 엔진.

RuleBasedBrain: 기존 행동 점수 기반 FSM (일반 개체)
SmartBrain:   경험 학습 + 멀티스텝 계획 + 목표 설정 + 메시징 (똑똑한 개체)
LLM/외부 API는 절대 사용하지 않습니다 — 모든 연산은 순수 로컬 알고리즘.
"""

from __future__ import annotations

import random
from collections import deque
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Optional

from . import config
from . import buildings as bld
from .faction import Faction

if TYPE_CHECKING:
    from .entity import Entity, EntityState
    from .world import World
    from .market import Market


# ──────────────────────────────────────────────
# 경험 데이터
# ──────────────────────────────────────────────
@dataclass
class Experience:
    """과거 행동의 기록 — 유사 상황에서 더 나은 선택을 위해 사용."""
    state_snapshot: dict[str, float]  # 에너지비율, 인벤토리, 장비수, 이웃수 등
    action: str                       # 수행한 행동 (EntityState.name.lower())
    outcome_score: float              # 행동 후 N틱 뒤의 결과 점수 (wealth+energy 변화)


# ──────────────────────────────────────────────
# 목표
# ──────────────────────────────────────────────
@dataclass
class Goal:
    """개체의 단기 목표 — SmartBrain이 자동 생성/추적."""
    metric: str        # "food_surplus" | "iron_stock" | "equip_weapon" | "explore" | ...
    target_value: float
    priority: float    # 0.0~1.0
    description: str = ""


# ──────────────────────────────────────────────
# 메시지 프로토콜
# ──────────────────────────────────────────────
@dataclass
class BrainMessage:
    """개체 간 구조화된 메시지 (LLM 없음, 정해진 프로토콜)."""
    msg_type: str      # "trade_offer" | "trade_request" | "alliance_proposal" | "warning"
    sender_id: int
    target_id: int
    data: dict = field(default_factory=dict)


# ──────────────────────────────────────────────
# Brain — 추상 기반
# ──────────────────────────────────────────────
class Brain:
    """두뇌의 추상 기반. 모든 두뇌는 decide()로 행동을 선택."""

    def decide(self, entity: Entity, world: World,
               market: Optional[Market]) -> EntityState:
        """현재 상태 + 기억 + 계획에 따라 행동 선택."""
        raise NotImplementedError

    def feedback(self, entity: Entity, action: str,
                 outcome_score: float) -> None:
        """행동 실행 후 결과를 피드백받아 학습."""
        pass

    def brain_type(self) -> str:
        """두뇌 타입 식별자."""
        return self.__class__.__name__


# ──────────────────────────────────────────────
# RuleBasedBrain — 기존 점수 기반 FSM
# ──────────────────────────────────────────────
class RuleBasedBrain(Brain):
    """기존의 행동 점수 기반 결정 엔진. Entity.decide_action()의 로직 그대로."""

    def decide(self, entity: Entity, world: World,
               market: Optional[Market]) -> EntityState:
        from .entity import EntityState

        if entity.energy <= 0:
            return EntityState.DIE

        scores: dict[EntityState, float] = {}

        # 1. CONSUME — 배고프면 먹기
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
                scores[EntityState.GATHER] = need * 30.0 + random.uniform(0, 10)

        # 4. TRADE
        if market and not entity.inventory_is_full:
            surplus = self._has_surplus(entity)
            if surplus:
                scores[EntityState.TRADE] = (
                    entity.genome.sociability * 50.0 + random.uniform(0, 10))

        # 5. CRAFT
        if entity.genome.industry > 0.4:
            if self._can_craft_anything(entity):
                scores[EntityState.CRAFT] = (
                    entity.genome.industry * 40.0 + random.uniform(0, 10))

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
                entity.genome.curiosity * 20.0 + random.uniform(0, 15))

        # 8. IDLE
        scores[EntityState.IDLE] = 5.0

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
                                   entity.genome.aggression * 30.0 + random.uniform(0, 10))
            elif entity.genome.aggression > 0.1:
                combat_score = max(combat_score, entity.genome.aggression * 15.0)

        # 후퇴
        if energy_ratio < config.COMBAT_RETREAT_THRESHOLD:
            combat_score *= 0.3

        return combat_score


# ──────────────────────────────────────────────
# SmartBrain — 경험 학습 + 계획 + 목표 + 메시징
# ──────────────────────────────────────────────
class SmartBrain(RuleBasedBrain):
    """향상된 의사결정 엔진. LLM 없이 로컬 알고리즘만으로 동작.

    기능:
    - 경험 기반 학습: 과거 행동의 결과를 기억해 유사 상황에서 조정
    - 멀티스텝 계획: 2틱 앞을 내다보고 행동 시퀀스 선택
    - 목표 설정: 자원/장비/안전 상태에 따라 단기 목표 자동 생성
    - 개체 간 메시징: 구조화된 메시지로 거래/협력 (LLM 없는 정해진 프로토콜)
    """

    def __init__(self):
        super().__init__()
        # 경험 메모리 (최근 N개만 저장)
        self.experiences: deque[Experience] = deque(
            maxlen=config.SMART_MEMORY_SIZE)

        # 현재 목표 리스트
        self.goals: list[Goal] = []

        # 멀티스텝 계획 (실행 예정인 액션 시퀀스)
        self.current_plan: list[str] = []  # action names

        # 내보낼 메시지 큐 (엔진이 수집해 전달)
        self.outbox: list[BrainMessage] = []

        # 마지막 행동 기록 (피드백용)
        self._last_action: str = "idle"
        self._last_state_snapshot: dict[str, float] = {}

    def decide(self, entity, world, market) -> EntityState:
        from .entity import EntityState

        if entity.energy <= 0:
            return EntityState.DIE

        # 1. 받은 메시지 처리
        self._process_messages(entity, world)

        # 2. 목표 갱신
        self._update_goals(entity)

        # 3. 계획 검증 — 현재 계획이 여전히 유효한지 확인
        if self.current_plan:
            next_action = self.current_plan[0]
            # 계획이 유효한지 상태 기반으로 확인
            if self._is_plan_valid(next_action, entity, world):
                state = self._action_name_to_state(next_action)
                if state is not None:
                    self.current_plan.pop(0)
                    self._record_state(entity)
                    self._last_action = next_action
                    return state

        # 4. 계획이 없거나 무효면 새 계획 수립
        self.current_plan = []
        best_action = self._plan_and_decide(entity, world, market)

        # 5. 결과 기록
        self._record_state(entity)
        self._last_action = best_action

        return best_action

    # ──────────────────────────────────────────
    # 의사결정 코어
    # ──────────────────────────────────────────

    def _plan_and_decide(self, entity, world, market) -> EntityState:
        """멀티스텝 계획 + 경험 보정으로 최적 행동 선택."""
        from .entity import EntityState

        # 기본 점수 계산 (RuleBasedBrain 로직)
        scores: dict[EntityState, float] = {}
        self._base_scores(entity, world, market, scores)

        if not scores:
            return EntityState.IDLE

        # --- 경험 기반 보정 ---
        current_state = self._make_snapshot(entity)
        for exp in self.experiences:
            sim = self._state_similarity(current_state, exp.state_snapshot)
            if sim > config.SMART_SIMILARITY_THRESHOLD:
                state = self._action_name_to_state(exp.action)
                if state and state in scores:
                    # 유사한 상황에서 이 행동이 좋은 결과를 낳았다면 가산
                    if exp.outcome_score > 0:
                        scores[state] *= (1.0 + sim * exp.outcome_score * 2.0)
                    # 나쁜 결과였다면 감산 (완전히 배제하진 않음)
                    else:
                        scores[state] *= (1.0 - sim * abs(exp.outcome_score) * 0.5)

        # --- 목표 기반 보정 ---
        for goal in self.goals:
            goal_bonus = self._goal_action_bonus(goal, entity, world)
            if goal_bonus > 0:
                for state in self._goal_relevant_actions(goal):
                    if state in scores:
                        scores[state] += goal_bonus * goal.priority

        # --- 멀티스텝 계획: 2-액션 시퀀스 평가 ---
        if random.random() < config.SMART_PLANNING_RATE:
            self._try_multistep_plan(entity, world, market, scores)

        # 최고 점수 선택
        best = max(scores, key=scores.get)

        # 계획 수립: 선택한 액션 후에 할 만한 후속 액션을 계획에 저장
        self._build_plan_from_action(entity, world, market, best)

        return best

    def _base_scores(self, entity, world, market,
                     scores: dict) -> None:
        """RuleBasedBrain의 점수 계산을 그대로 사용."""
        from .entity import EntityState

        hunger_ratio = 1.0 - (entity.energy / entity.max_energy)
        food_available = entity.inventory.get("food", 0)
        if food_available > 0 and hunger_ratio > 0.2:
            scores[EntityState.CONSUME] = hunger_ratio * 100.0
        elif hunger_ratio > 0.6:
            scores[EntityState.GATHER] = hunger_ratio * 90.0

        energy_ratio = entity.energy / entity.max_energy
        food_stored = entity.inventory.get("food", 0)
        if (energy_ratio > config.REPRODUCTION_ENERGY_RATIO
                and entity.reproduction_cooldown <= 0
                and food_stored >= config.REPRODUCTION_MIN_FOOD
                and entity.inventory_used >= 3):
            scores[EntityState.REPRODUCE] = (
                energy_ratio * 40.0 * (0.3 + entity.genome.fertility * 0.7))

        tile = world.tile_at(entity.x, entity.y)
        if tile and tile.total_resources() > 0 and not entity.inventory_is_full:
            need = self._resource_need(entity)
            if need > 0:
                scores[EntityState.GATHER] = max(
                    scores.get(EntityState.GATHER, 0),
                    need * 30.0 + random.uniform(0, 10))

        if market and not entity.inventory_is_full:
            if self._has_surplus(entity):
                scores[EntityState.TRADE] = (
                    entity.genome.sociability * 50.0 + random.uniform(0, 10))

        if entity.genome.industry > 0.4:
            if self._can_craft_anything(entity):
                scores[EntityState.CRAFT] = (
                    entity.genome.industry * 40.0 + random.uniform(0, 10))

        if not entity.buildings:
            for bdef in config.BUILDING_DEFS:
                if bld.can_construct(entity, bdef):
                    scores[EntityState.CONSTRUCT] = 35.0 + entity.genome.industry * 20.0
                    break

        combat_score = self._score_combat(entity, world)
        if combat_score > 0:
            scores[EntityState.COMBAT] = combat_score

        if entity.curiosity_drive() > 0:
            scores[EntityState.EXPLORE] = (
                entity.genome.curiosity * 20.0 + random.uniform(0, 15))

        scores[EntityState.IDLE] = 5.0

    # ──────────────────────────────────────────
    # 멀티스텝 계획
    # ──────────────────────────────────────────

    def _try_multistep_plan(self, entity, world, market,
                            scores: dict) -> None:
        """2-액션 시퀀스를 평가해 현재 점수에 반영."""
        from .entity import EntityState

        # 상위 3개 액션만 시퀀스 평가 (성능)
        candidates = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:3]
        if not candidates:
            return

        best_seq_score = 0.0
        best_seq_actions: tuple = (EntityState.IDLE, EntityState.IDLE)

        for state_a, score_a in candidates:
            for state_b, _ in candidates:
                if state_b == state_a:
                    continue
                # 시퀀스 점수 = 첫 액션 점수 + 두 번째 액션 예상 점수 * 할인율
                seq_score = score_a + scores.get(state_b, 0) * config.SMART_PLANNING_DISCOUNT
                if seq_score > best_seq_score:
                    best_seq_score = seq_score
                    best_seq_actions = (state_a, state_b)

        # 시퀀스 점수가 단일 액션보다 유의미하게 높으면 계획 저장
        if best_seq_score > scores.get(best_seq_actions[0], 0) * 1.3:
            self.current_plan = [
                best_seq_actions[0].name.lower(),
                best_seq_actions[1].name.lower(),
            ]

    def _build_plan_from_action(self, entity, world, market,
                                 chosen_action) -> None:
        """선택된 액션 이후에 실행할 만한 후속 액션을 계획에 저장."""
        # 이미 current_plan이 있다면 _try_multistep_plan에서 설정된 것
        if self.current_plan:
            return
        # 단일 액션 결정의 경우, 후속 액션을 추천
        from .entity import EntityState
        action_name = chosen_action.name.lower()
        follow_up = {
            "gather": "trade",
            "trade": "craft",
            "craft": "construct",
            "construct": "explore",
            "combat": "gather",
            "consume": "gather",
        }
        if action_name in follow_up:
            next_state = self._action_name_to_state(follow_up[action_name])
            if next_state and next_state != chosen_action:
                self.current_plan.append(follow_up[action_name])

    # ──────────────────────────────────────────
    # 목표 시스템
    # ──────────────────────────────────────────

    def _update_goals(self, entity) -> None:
        """현재 상태에 따라 목표 자동 생성/갱신."""
        from .entity import EntityState

        new_goals: list[Goal] = []
        food = entity.inventory.get("food", 0)
        wood = entity.inventory.get("wood", 0)
        stone = entity.inventory.get("stone", 0)
        iron = entity.inventory.get("iron", 0)

        # 식량 부족 → 채집/거래 목표
        if food < 8:
            new_goals.append(Goal(
                "food_surplus", 12.0,
                priority=0.9 - (food / 8.0) * 0.5,
                description="식량 비축이 필요함"))

        # 철 부족 + 전사/장인 특화 → 채광 목표
        if iron < 3 and entity.genome.specialization in ("warrior", "crafter", "miner"):
            new_goals.append(Goal(
                "iron_stock", 5.0,
                priority=0.6,
                description="철 확보가 필요함"))

        # 무기/갑옷 미장착 → 제작 목표
        has_weapon = any("sword" in e or "axe" in e for e in entity.equipped)
        has_armor = any("armor" in e for e in entity.equipped)
        if not has_weapon and entity.genome.aggression > 0.3:
            new_goals.append(Goal(
                "equip_weapon", 1.0,
                priority=0.5,
                description="무기 제작이 필요함"))

        # 재료가 충분하고 아직 장비가 없으면 제작 목표
        if (not has_weapon and wood >= 3 and stone >= 5):
            new_goals.append(Goal(
                "craft_tool", 1.0,
                priority=0.45,
                description="도구 제작이 필요함"))

        # 탐험 (호기심 높고 주변을 다 돌아다녔으면)
        if entity.genome.curiosity > 0.6 and len(entity.visited_tiles) < 20:
            new_goals.append(Goal(
                "explore", 20.0,
                priority=0.3 * entity.genome.curiosity,
                description="새로운 영역 탐험이 필요함"))

        self.goals = new_goals

    def _goal_action_bonus(self, goal: Goal, entity, world) -> float:
        """특정 목표에 대해 현재 선호하는 액션 점수 보정값."""
        if goal.metric == "food_surplus":
            return 15.0
        elif goal.metric == "iron_stock":
            tile = world.tile_at(entity.x, entity.y)
            if tile and tile.resources.get("iron", 0) > 0:
                return 20.0  # 철이 있는 타일이면 채집 우선
            return 10.0
        elif goal.metric == "equip_weapon":
            return 20.0  # 제작 우선
        elif goal.metric == "craft_tool":
            return 15.0
        elif goal.metric == "explore":
            return 10.0
        return 5.0

    def _goal_relevant_actions(self, goal: Goal) -> list:
        """목표 달성에 도움이 되는 액션 목록."""
        from .entity import EntityState
        mapping = {
            "food_surplus": [EntityState.GATHER, EntityState.TRADE],
            "iron_stock": [EntityState.GATHER, EntityState.TRADE],
            "equip_weapon": [EntityState.CRAFT, EntityState.TRADE],
            "craft_tool": [EntityState.CRAFT],
            "explore": [EntityState.EXPLORE],
        }
        return mapping.get(goal.metric, [])

    # ──────────────────────────────────────────
    # 메시징 시스템 (비용 0, 정해진 프로토콜)
    # ──────────────────────────────────────────

    def _process_messages(self, entity, world) -> None:
        """받은 메시지 처리."""
        if not entity.mailbox:
            return
        messages = entity.mailbox.copy()
        entity.mailbox.clear()

        for msg in messages:
            if msg.msg_type == "trade_offer":
                self._handle_trade_offer(entity, world, msg)
            elif msg.msg_type == "trade_request":
                self._handle_trade_request(entity, world, msg)
            elif msg.msg_type == "alliance_proposal":
                self._handle_alliance_proposal(entity, world, msg)
            elif msg.msg_type == "warning":
                self._handle_warning(entity, msg)

    def _handle_trade_offer(self, entity, world, msg: BrainMessage) -> None:
        """거래 제안 처리: 내가 부족한 자원이면 수락 신호를 보냄."""
        resource = msg.data.get("resource", "")
        quantity = msg.data.get("quantity", 0)
        if not resource or quantity <= 0:
            return
        current = entity.inventory.get(resource, 0)
        if current < 3:  # 부족하면 거래 의사 표시
            self._send(entity, BrainMessage(
                msg_type="trade_accept",
                sender_id=id(entity),
                target_id=msg.sender_id,
                data={"resource": resource, "quantity": min(quantity, 3 - current)},
            ))

    def _handle_trade_request(self, entity, world, msg: BrainMessage) -> None:
        """거래 요청 처리: 잉여 자원이 있으면 수락."""
        resource = msg.data.get("resource", "")
        quantity = msg.data.get("quantity", 0)
        if not resource or quantity <= 0:
            return
        current = entity.inventory.get(resource, 0)
        surplus = current - (5 if resource == "food" else 3)
        if surplus >= quantity:
            self._send(entity, BrainMessage(
                msg_type="trade_accept",
                sender_id=id(entity),
                target_id=msg.sender_id,
                data={"resource": resource, "quantity": quantity},
            ))

    def _handle_alliance_proposal(self, entity, world, msg: BrainMessage) -> None:
        """동맹 제안: 사회성과 현재 안전 상태를 고려해 수락/거절."""
        sender_ent = world.entities.get(msg.sender_id)
        if not sender_ent or not sender_ent.alive:
            return
        # 사회성이 높거나, 주변에 적이 많으면 동맹 선호
        threat_level = sum(
            1 for e in world.entities.values()
            if e.alive and e != entity
            and e.genome.aggression > 0.6
            and abs(e.x - entity.x) <= 3)
        acceptance = entity.genome.sociability * 0.6 + min(threat_level * 0.1, 0.3)
        if random.random() < acceptance:
            # 같은 파벌 가입 또는 동맹 제안 수락
            self._send(entity, BrainMessage(
                msg_type="alliance_accepted",
                sender_id=id(entity),
                target_id=msg.sender_id,
                data={},
            ))

    def _handle_warning(self, entity, msg: BrainMessage) -> None:
        """경고 처리: 위험 지역 회피 등."""
        danger_x = msg.data.get("x", entity.x)
        danger_y = msg.data.get("y", entity.y)
        dist = abs(entity.x - danger_x) + abs(entity.y - danger_y)
        if dist <= 2:
            # 위험 지역에서 멀어지도록 탐험 방향 조정 (약한 효과)
            pass

    def _send(self, entity, msg: BrainMessage) -> None:
        """메시지 전송 요청 (outbox에 추가, 엔진이 처리)."""
        self.outbox.append(msg)

    def send_trade_offer(self, entity, world, target_id: int,
                         resource: str, quantity: float) -> None:
        """거래 제안 메시지 전송."""
        self._send(entity, BrainMessage(
            msg_type="trade_offer",
            sender_id=id(entity),
            target_id=target_id,
            data={"resource": resource, "quantity": quantity},
        ))

    def send_trade_request(self, entity, world, target_id: int,
                           resource: str, quantity: float) -> None:
        """거래 요청 메시지 전송."""
        self._send(entity, BrainMessage(
            msg_type="trade_request",
            sender_id=id(entity),
            target_id=target_id,
            data={"resource": resource, "quantity": quantity},
        ))

    # ──────────────────────────────────────────
    # 경험 학습
    # ──────────────────────────────────────────

    def feedback(self, entity, action: str, outcome_score: float) -> None:
        """행동 결과를 경험 메모리에 저장."""
        exp = Experience(
            state_snapshot=self._last_state_snapshot,
            action=action,
            outcome_score=outcome_score,
        )
        self.experiences.append(exp)

    def _record_state(self, entity) -> None:
        """현재 상태를 스냅샷으로 저장."""
        self._last_state_snapshot = self._make_snapshot(entity)

    def _make_snapshot(self, entity) -> dict[str, float]:
        """의사결정에 중요한 상태 변수들로 스냅샷 생성."""
        return {
            "energy_ratio": round(entity.energy / max(entity.max_energy, 1), 3),
            "food": entity.inventory.get("food", 0),
            "wood": entity.inventory.get("wood", 0),
            "stone": entity.inventory.get("stone", 0),
            "iron": entity.inventory.get("iron", 0),
            "gold": entity.inventory.get("gold", 0),
            "equipped_count": len(entity.equipped),
            "kill_count": entity.kill_count,
            "age": entity.age,
        }

    def _state_similarity(self, a: dict[str, float],
                          b: dict[str, float]) -> float:
        """두 상태 스냅샷 간 유사도 (0~1). 코사인 유사도 간소화 버전."""
        if not a or not b:
            return 0.0
        common_keys = set(a.keys()) & set(b.keys())
        if not common_keys:
            return 0.0
        diffs = []
        for key in common_keys:
            max_val = max(abs(a.get(key, 0)), abs(b.get(key, 0)), 0.01)
            diffs.append(abs(a.get(key, 0) - b.get(key, 0)) / max_val)
        avg_diff = sum(diffs) / len(diffs)
        return max(0.0, 1.0 - avg_diff)

    # ──────────────────────────────────────────
    # 유틸리티
    # ──────────────────────────────────────────

    def _action_name_to_state(self, name: str):
        """액션 이름 문자열 → EntityState."""
        from .entity import EntityState
        mapping = {
            "idle": EntityState.IDLE,
            "explore": EntityState.EXPLORE,
            "gather": EntityState.GATHER,
            "trade": EntityState.TRADE,
            "craft": EntityState.CRAFT,
            "construct": EntityState.CONSTRUCT,
            "consume": EntityState.CONSUME,
            "reproduce": EntityState.REPRODUCE,
            "combat": EntityState.COMBAT,
            "die": EntityState.DIE,
        }
        return mapping.get(name)

    def _is_plan_valid(self, action_name: str, entity, world) -> bool:
        """계획된 액션이 여전히 실행 가능한지 확인."""
        from .entity import EntityState
        state = self._action_name_to_state(action_name)
        if state is None:
            return False
        # 간단한 사전 조건 검사
        if state == EntityState.GATHER:
            tile = world.tile_at(entity.x, entity.y)
            return bool(tile and tile.total_resources() > 0)
        if state == EntityState.CONSUME:
            return entity.inventory.get("food", 0) > 0
        if state == EntityState.CRAFT:
            return self._can_craft_anything(entity)
        return True


# ──────────────────────────────────────────────
# 두뇌 팩토리
# ──────────────────────────────────────────────
def create_brain(entity, world) -> Brain:
    """개체의 유전자와 환경에 따라 적절한 두뇌를 생성.

    SmartBrain 할당 확률은 SMART_BRAIN_RATIO에 따르되,
    innovation_rate가 높은 개체일수록 SmartBrain이 될 확률 상승.
    """
    smart_chance = config.SMART_BRAIN_RATIO
    # 혁신성이 높은 개체는 SmartBrain이 될 확률 추가 보정
    innovation_bonus = entity.genome.innovation_rate * 0.3
    smart_chance = min(1.0, smart_chance + innovation_bonus)

    if random.random() < smart_chance:
        return SmartBrain()
    return RuleBasedBrain()
