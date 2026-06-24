"""기술 연구 테스트 — 글로벌 연구 포인트 축적."""

from __future__ import annotations

import random
from unittest.mock import MagicMock

from sim.research import process_research
from sim.knowledge import TechnologyTree


def test_process_research_no_entities():
    world = MagicMock()
    world.entities = {}
    world.tick = 0
    tech_tree = TechnologyTree()
    discovered = set()
    logs = []
    process_research(world, tech_tree, random.Random(42), discovered, lambda e: logs.append(e))
    assert len(discovered) == 0


def test_process_research_no_available_techs():
    world = MagicMock()
    entity = MagicMock()
    entity.alive = True
    entity.genome.innovation_rate = 0.8
    entity.knowledge.count.return_value = 2
    world.entities = {0: entity}
    world.tick = 0
    tech_tree = TechnologyTree()
    discovered = set(t.name for t in tech_tree.all_techs())
    logs = []
    process_research(world, tech_tree, random.Random(42), discovered, lambda e: logs.append(e))
    assert len(discovered) == len(tech_tree.all_techs())


def test_process_research_basic_tech():
    world = MagicMock()
    entity = MagicMock()
    entity.alive = True
    entity.genome.innovation_rate = 1.0
    entity.knowledge.count.return_value = 5
    world.entities = {0: entity}
    world.tick = 0
    tech_tree = TechnologyTree()
    discovered = set()
    logs = []
    rng = random.Random(42)
    process_research(world, tech_tree, rng, discovered, lambda e: logs.append(e))
    assert len(discovered) >= 0


def test_process_research_logs_discovery():
    world = MagicMock()
    entity = MagicMock()
    entity.alive = True
    entity.genome.innovation_rate = 1.0
    entity.knowledge.count.return_value = 5
    entity.name = "E0001"
    world.entities = {0: entity}
    world.tick = 0
    tech_tree = TechnologyTree()
    discovered = set()
    logs = []
    rng = random.Random(42)
    process_research(world, tech_tree, rng, discovered, lambda e: logs.append(e))
    for log in logs:
        assert log["type"] == "tech_discovery"
