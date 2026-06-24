"""기술 연구 시스템 — 글로벌 연구 포인트 축적 및 기술 발견."""

from __future__ import annotations

import random
from typing import TYPE_CHECKING, Callable

from . import config

if TYPE_CHECKING:
    from .knowledge import TechnologyTree
    from .world import World


def process_research(
    world: World,
    tech_tree: TechnologyTree,
    rng: random.Random,
    discovered_techs: set[str],
    log_event: Callable[[dict], None],
) -> None:
    """개체들이 연구 포인트를 생성하고 기술에 집중/분산 투자."""
    research_points = 0.0
    total_innovation = 0.0
    for entity in world.entities.values():
        if not entity.alive:
            continue
        innovation = entity.genome.innovation_rate
        knowledge_count = entity.knowledge.count()
        effects = entity.get_combined_effects()
        learning_bonus = 1.0 + effects.get("learning_speed", 0.0)
        points = (
            innovation * config.RESEARCH_POINT_BASE_RATE
            * (1 + knowledge_count * config.RESEARCH_POINT_PER_KNOWLEDGE)
            * learning_bonus
        )
        research_points += points
        total_innovation += innovation

    if research_points <= 0:
        return

    available = tech_tree.get_available(discovered_techs)
    if not available:
        return

    focus_target = None
    for tech in available:
        if tech.research_progress > 0 and rng.random() < config.RESEARCH_FOCUS_THRESHOLD:
            focus_target = tech
            break

    if focus_target is None:
        basics = [t for t in available if not t.prerequisites]
        if basics and rng.random() < config.RESEARCH_BASIC_BIAS:
            focus_target = rng.choice(basics)
        else:
            focus_target = rng.choice(available)

    if focus_target.research(research_points):
        discovered_techs.add(focus_target.name)

        discoverers = []
        for entity in world.entities.values():
            if entity.alive and entity.genome.innovation_rate > 0.5:
                if rng.random() < config.TECH_PIONEER_CHANCE:
                    entity.knowledge.learn(focus_target.name)
                    entity.apply_knowledge_effects()
                    discoverers.append(entity.name)

        log_event({
            "tick": world.tick,
            "type": "tech_discovery",
            "data": {
                "tech": focus_target.name,
                "description": focus_target.description,
                "discoverers": discoverers[:5],
            },
        })
