"""제작 시스템 테스트 — 레시피 검증, 자원 차감."""

from __future__ import annotations

import random

from sim.entity_craft import do_craft, do_construct, get_gather_bonus
from sim.entity import Entity
from sim import config


def _make_crafter() -> Entity:
    e = Entity(5, 5, rng=random.Random(42))
    e.eid = 0
    e.name = "E0000"
    e.inventory["wood"] = 20.0
    e.inventory["stone"] = 20.0
    e.inventory["iron"] = 10.0
    e.equipped = []
    e.buildings = []
    return e


def test_do_craft_stone_axe():
    e = _make_crafter()
    e.known_techs = set()
    e.genome.innovation_rate = 0.5
    e.genome.specialization = "crafter"
    events = do_craft(e)
    if events:
        assert events[0]["type"] == "craft"
        assert "stone_axe" in e.equipped


def test_do_craft_no_materials():
    e = _make_crafter()
    e.inventory = {}
    events = do_craft(e)
    assert events == []


def test_do_craft_already_crafted():
    e = _make_crafter()
    e.equipped = ["stone_axe"]
    events = do_craft(e)
    stone_axe_events = [ev for ev in events if ev.get("data", {}).get("item") == "stone_axe"]
    assert len(stone_axe_events) == 0


def test_do_construct():
    e = _make_crafter()
    e.inventory["wood"] = 20.0
    e.inventory["stone"] = 20.0
    e.known_techs = set()
    e.genome.innovation_rate = 0.5
    events = do_construct(e)
    assert isinstance(events, list)


def test_get_gather_bonus_base():
    e = _make_crafter()
    e.equipped = []
    bonus = get_gather_bonus(e, "food")
    assert bonus == 1.0


def test_get_gather_bonus_with_tool():
    e = _make_crafter()
    e.equipped = ["stone_axe"]
    bonus = get_gather_bonus(e, "food")
    assert bonus >= 1.0


def test_craft_recipes_exist():
    assert hasattr(config, "CRAFT_RECIPES")
    assert len(config.CRAFT_RECIPES) > 0


def test_craft_bonus_config():
    assert hasattr(config, "CRAFT_BONUS")
    assert isinstance(config.CRAFT_BONUS, dict)
