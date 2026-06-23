import sys

import pytest

sys.path.insert(0, r'C:\Users\신희정\selfgrow')

from sim.config import BUILDING_DEFS, BuildingDef
from sim.entity import Entity
from sim import buildings as bld


class TestBuildingDefs:
    def test_five_building_types(self):
        assert len(BUILDING_DEFS) == 5

    def test_each_building_has_name_and_cost(self):
        for bd in BUILDING_DEFS:
            assert bd.name
            assert len(bd.cost) >= 1
            assert bd.effects

    def test_storehouse_effects(self):
        storehouse = [b for b in BUILDING_DEFS if b.name == "storehouse"][0]
        assert storehouse.effects["max_inventory"] == 5
        assert storehouse.effects["max_food_storage"] == 10.0

    def test_wall_defense_bonus(self):
        wall = [b for b in BUILDING_DEFS if b.name == "wall"][0]
        assert wall.effects["defense_bonus"] == 0.3


class TestCanConstruct:
    def test_can_build_with_enough_resources(self):
        entity = Entity(10, 10)
        entity.inventory = {"wood": 10, "stone": 10}
        storehouse = [b for b in BUILDING_DEFS if b.name == "storehouse"][0]
        assert bld.can_construct(entity, storehouse)

    def test_cannot_build_without_resources(self):
        entity = Entity(10, 10)
        entity.inventory = {}
        storehouse = [b for b in BUILDING_DEFS if b.name == "storehouse"][0]
        assert not bld.can_construct(entity, storehouse)

    def test_cannot_exceed_max(self):
        entity = Entity(10, 10)
        entity.inventory = {"wood": 99, "stone": 99}
        entity.buildings = ["storehouse"]
        storehouse = [b for b in BUILDING_DEFS if b.name == "storehouse"][0]
        assert not bld.can_construct(entity, storehouse)

    def test_can_build_multiple_types(self):
        entity = Entity(10, 10)
        entity.inventory = {"wood": 99, "stone": 99, "iron": 99, "gold": 99}
        for bd in BUILDING_DEFS:
            assert bld.can_construct(entity, bd)


class TestConstruct:
    def test_construct_deducts_resources(self):
        entity = Entity(10, 10)
        entity.inventory = {"wood": 10, "stone": 10}
        storehouse = [b for b in BUILDING_DEFS if b.name == "storehouse"][0]
        bld.construct(entity, storehouse, None)
        assert entity.inventory["wood"] == 5
        assert entity.inventory["stone"] == 7
        assert "storehouse" in entity.buildings

    def test_construct_fails_without_resources(self):
        entity = Entity(10, 10)
        entity.inventory = {}
        storehouse = [b for b in BUILDING_DEFS if b.name == "storehouse"][0]
        assert not bld.construct(entity, storehouse, None)
        assert "storehouse" not in entity.buildings


class TestBuildingEffects:
    def test_single_building_effects(self):
        entity = Entity(10, 10)
        entity.buildings = ["storehouse"]
        effects = bld.get_building_effects(entity)
        assert effects["max_inventory"] == 5.0

    def test_multiple_building_effects_accumulate(self):
        entity = Entity(10, 10)
        entity.buildings = ["storehouse", "watchtower"]
        effects = bld.get_building_effects(entity)
        assert effects["max_inventory"] == 5.0
        assert effects["explore_range"] == 2.0
        assert effects["detection_radius"] == 1.0


class TestDestroyBuilding:
    def test_destroy_removes_building(self):
        entity = Entity(10, 10)
        entity.buildings = ["storehouse"]
        destroyed = bld.destroy_random_building(entity)
        if destroyed:
            assert "storehouse" not in entity.buildings
        else:
            assert "storehouse" in entity.buildings
