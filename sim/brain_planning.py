"""SmartBrain 멀티스텝 계획 시스템."""

from __future__ import annotations

from typing import TYPE_CHECKING

from . import config

if TYPE_CHECKING:
    from .entity import Entity, EntityState
    from .world import World
    from .market import Market


def try_multistep_plan(entity: Entity, world: World, market: Market,
                       scores: dict, brain) -> None:
    """2-스텝 계획 시도."""
    from .entity import EntityState

    candidates = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:3]
    if not candidates:
        return

    best_seq_score = 0.0
    best_seq_actions: tuple = (EntityState.IDLE, EntityState.IDLE)

    for state_a, score_a in candidates:
        for state_b, _ in candidates:
            if state_b == state_a:
                continue
            seq_score = score_a + scores.get(state_b, 0) * config.SMART_PLANNING_DISCOUNT
            if seq_score > best_seq_score:
                best_seq_score = seq_score
                best_seq_actions = (state_a, state_b)

    if best_seq_score > scores.get(best_seq_actions[0], 0) * 1.3:
        brain.current_plan = [
            best_seq_actions[0].name.lower(),
            best_seq_actions[1].name.lower(),
        ]


def build_plan_from_action(entity: Entity, world: World, market: Market,
                           chosen_action, brain) -> None:
    """선택된 행동에서 후속 계획 생성."""
    if brain.current_plan:
        return
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
        next_state = brain._action_name_to_state(follow_up[action_name])
        if next_state and next_state != chosen_action:
            brain.current_plan.append(follow_up[action_name])