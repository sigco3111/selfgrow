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
    from .entity import EntityState

    candidates = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:3]
    if not candidates:
        return

    beam_width = 2
    depth = config.SMART_PLANNING_DEPTH

    beams: list[tuple[list[str], float]] = [([], 0.0)]
    for state, score in candidates:
        beams.append(([state.name.lower()], score))

    for step in range(1, depth):
        new_beams: list[tuple[list[str], float]] = []
        for path, path_score in beams:
            last_action = path[-1] if path else None
            for state, score in candidates:
                if state.name.lower() == last_action:
                    continue
                discount = config.SMART_PLANNING_DISCOUNT ** step
                new_score = path_score + score * discount
                new_beams.append((path + [state.name.lower()], new_score))
        new_beams.sort(key=lambda x: x[1], reverse=True)
        beams = new_beams[:beam_width]

    if not beams:
        return

    best_path, best_score = beams[0]
    if not best_path:
        return

    first_action = best_path[0]
    first_score = scores.get(EntityState[first_action.upper()], 0)
    if best_score > first_score * 1.3 and len(best_path) >= 2:
        brain.current_plan = best_path


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