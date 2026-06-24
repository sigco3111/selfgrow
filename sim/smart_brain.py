"""SmartBrain — 경험 학습 + 멀티스텝 계획 + 목표 설정 + 메시징 의사결정 엔진.
LLM/외부 API는 절대 사용하지 않습니다 — 모든 연산은 순수 로컬 알고리즘.
"""

from __future__ import annotations

import random
from collections import deque
from typing import TYPE_CHECKING, Optional

from . import config
from . import brain_goals as goals_mod
from . import brain_messaging as messaging_mod
from . import brain_planning as planning_mod
from .brain_base import BrainMessage, Experience, Goal
from .rule_brain import RuleBasedBrain

if TYPE_CHECKING:
    from .entity import Entity, EntityState
    from .world import World
    from .market import Market


class SmartBrain(RuleBasedBrain):
    """향상된 의사결정 엔진. LLM 없이 로컬 알고리즘만으로 동작.

    기능:
    - 경험 기반 학습: 과거 행동의 결과를 기억해 유사 상황에서 조정
    - 멀티스텝 계획: 2틱 앞을 내다보고 행동 시퀀스 선택
    - 목표 설정: 자원/장비/안전 상태에 따라 단기 목표 자동 생성
    - 개체 간 메시징: 구조화된 메시지로 거래/협력 (LLM 없는 정해진 프로토콜)
    """

    def __init__(self, rng: random.Random | None = None):
        super().__init__(rng=rng)
        self.experiences: deque[Experience] = deque(maxlen=config.SMART_MEMORY_SIZE)
        self.goals: list[Goal] = []
        self.current_plan: list[str] = []
        self.outbox: list[BrainMessage] = []
        self._last_action: str = "idle"
        self._last_state_snapshot: dict[str, float] = {}

    def decide(self, entity, world, market) -> EntityState:
        from .entity import EntityState

        if entity.energy <= 0:
            return EntityState.DIE

        messaging_mod.process_messages(entity, world, self)
        goals_mod.update_goals(entity, self)

        if self.current_plan:
            next_action = self.current_plan[0]
            if self._is_plan_valid(next_action, entity, world):
                state = self._action_name_to_state(next_action)
                if state is not None:
                    self.current_plan.pop(0)
                    self._record_state(entity)
                    self._last_action = next_action
                    return state

        self.current_plan = []
        best_action = self._plan_and_decide(entity, world, market)

        self._record_state(entity)
        self._last_action = best_action

        return best_action

    # ── 의사결정 코어 ──

    def _plan_and_decide(self, entity, world, market) -> EntityState:
        from .entity import EntityState

        scores: dict[EntityState, float] = {}
        self._base_scores(entity, world, market, scores)

        if not scores:
            return EntityState.IDLE

        current_state = self._make_snapshot(entity)
        for exp in self.experiences:
            sim = self._state_similarity(current_state, exp.state_snapshot)
            if sim > config.SMART_SIMILARITY_THRESHOLD:
                state = self._action_name_to_state(exp.action)
                if state and state in scores:
                    if exp.outcome_score > 0:
                        scores[state] *= (1.0 + sim * exp.outcome_score * 2.0)
                    else:
                        scores[state] *= (1.0 - sim * abs(exp.outcome_score) * 0.5)

        for goal in self.goals:
            goal_bonus = goals_mod.goal_action_bonus(goal, entity, world)
            if goal_bonus > 0:
                for state in goals_mod.goal_relevant_actions(goal):
                    if state in scores:
                        scores[state] += goal_bonus * goal.priority

        if self._rng.random() < config.SMART_PLANNING_RATE:
            planning_mod.try_multistep_plan(entity, world, market, scores, self)

        from .ideology import get_action_bias
        action_bias = get_action_bias(entity)
        for action_name, bias in action_bias.items():
            from .entity import EntityState as ES2
            es = getattr(ES2, action_name.upper(), None)
            if es and es in scores:
                scores[es] *= bias

        best = max(scores, key=scores.get)
        planning_mod.build_plan_from_action(entity, world, market, best, self)
        return best

    def _base_scores(self, entity, world, market, scores: dict) -> None:
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
                    need * 30.0 + self._rng.uniform(0, 10))

        if market and not entity.inventory_is_full:
            if self._has_surplus(entity):
                scores[EntityState.TRADE] = (
                    entity.genome.sociability * 50.0 + self._rng.uniform(0, 10))

        if entity.genome.industry > 0.4:
            if self._can_craft_anything(entity):
                scores[EntityState.CRAFT] = (
                    entity.genome.industry * 40.0 + self._rng.uniform(0, 10))

        if not entity.buildings:
            from . import buildings as bld
            for bdef in config.BUILDING_DEFS:
                if bld.can_construct(entity, bdef):
                    scores[EntityState.CONSTRUCT] = 35.0 + entity.genome.industry * 20.0
                    break

        combat_score = self._score_combat(entity, world)
        if combat_score > 0:
            scores[EntityState.COMBAT] = combat_score

        if entity.curiosity_drive() > 0:
            scores[EntityState.EXPLORE] = (
                entity.genome.curiosity * 20.0 + self._rng.uniform(0, 15))

        scores[EntityState.IDLE] = 5.0

    # ── 목표 위임 ──

    def _update_goals(self, entity) -> None:
        goals_mod.update_goals(entity, self)

    # ── 메시징 위임 ──

    def _send(self, entity, msg: BrainMessage) -> None:
        self.outbox.append(msg)

    def send_trade_offer(self, entity, world, target_id: int,
                         resource: str, quantity: float) -> None:
        messaging_mod.send_trade_offer(entity, world, target_id, resource, quantity, self)

    def send_trade_request(self, entity, world, target_id: int,
                           resource: str, quantity: float) -> None:
        messaging_mod.send_trade_request(entity, world, target_id, resource, quantity, self)

    def send_alliance_proposal(self, entity, world, target_id: int) -> None:
        messaging_mod.send_alliance_proposal(entity, world, target_id, self)

    def send_treaty_proposal(self, entity, world, target_id: int,
                              treaty_type: str) -> None:
        messaging_mod.send_treaty_proposal(entity, world, target_id, treaty_type, self)

    def send_trade_pact_proposal(self, entity, world, target_id: int) -> None:
        messaging_mod.send_trade_pact_proposal(entity, world, target_id, self)

    def send_non_aggression_proposal(self, entity, world, target_id: int) -> None:
        messaging_mod.send_non_aggression_proposal(entity, world, target_id, self)

    # ── 경험 학습 ──

    def feedback(self, entity, action: str, outcome_score: float) -> None:
        exp = Experience(
            state_snapshot=self._last_state_snapshot,
            action=action,
            outcome_score=outcome_score,
        )
        self.experiences.append(exp)

    def _record_state(self, entity) -> None:
        self._last_state_snapshot = self._make_snapshot(entity)

    def _make_snapshot(self, entity) -> dict[str, float]:
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

    # ── 유틸리티 ──

    def _action_name_to_state(self, name: str):
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
        from .entity import EntityState
        state = self._action_name_to_state(action_name)
        if state is None:
            return False
        if state == EntityState.GATHER:
            tile = world.tile_at(entity.x, entity.y)
            return bool(tile and tile.total_resources() > 0)
        if state == EntityState.CONSUME:
            return entity.inventory.get("food", 0) > 0
        if state == EntityState.CRAFT:
            return self._can_craft_anything(entity)
        return True
