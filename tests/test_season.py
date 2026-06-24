import sys

import pytest

sys.path.insert(0, r'C:\Users\신희정\selfgrow')

from sim.season import Season, compute_season, get_season_effects, season_progress


class TestSeasonCompute:
    def test_tick_0_is_spring(self):
        assert compute_season(0) == Season.SPRING

    def test_tick_24_is_spring(self):
        assert compute_season(24) == Season.SPRING

    def test_tick_25_is_summer(self):
        assert compute_season(25) == Season.SUMMER

    def test_tick_49_is_summer(self):
        assert compute_season(49) == Season.SUMMER

    def test_tick_50_is_autumn(self):
        assert compute_season(50) == Season.AUTUMN

    def test_tick_74_is_autumn(self):
        assert compute_season(74) == Season.AUTUMN

    def test_tick_75_is_winter(self):
        assert compute_season(75) == Season.WINTER

    def test_tick_99_is_winter(self):
        assert compute_season(99) == Season.WINTER

    def test_tick_100_loops_to_spring(self):
        assert compute_season(100) == Season.SPRING

    def test_large_tick_wraps_correctly(self):
        assert compute_season(500) == Season(500 // 25 % 4)


class TestSeasonEffects:
    def test_spring_regen_boost(self):
        eff = get_season_effects(Season.SPRING)
        assert eff.regen_mult == 1.2

    def test_spring_normal_energy(self):
        eff = get_season_effects(Season.SPRING)
        assert eff.energy_mult == 1.0

    def test_summer_energy_penalty(self):
        eff = get_season_effects(Season.SUMMER)
        assert eff.energy_mult == 1.15

    def test_autumn_gather_bonus(self):
        eff = get_season_effects(Season.AUTUMN)
        assert eff.gather_mult == 1.1

    def test_winter_regen_reduced(self):
        eff = get_season_effects(Season.WINTER)
        assert eff.regen_mult == 0.7

    def test_winter_speed_penalty(self):
        eff = get_season_effects(Season.WINTER)
        assert eff.speed_mult == 0.8

    def test_winter_energy_penalty(self):
        eff = get_season_effects(Season.WINTER)
        assert eff.energy_mult == 1.2

    def test_spring_gather_default(self):
        eff = get_season_effects(Season.SPRING)
        assert eff.gather_mult == 1.0

    def test_winter_gather_reduced(self):
        eff = get_season_effects(Season.WINTER)
        assert eff.gather_mult == 0.9


class TestSeasonProgress:
    def test_start_of_season(self):
        assert season_progress(0) == 0.0

    def test_mid_season(self):
        assert season_progress(12) == pytest.approx(12 / 25)

    def test_end_of_season(self):
        assert season_progress(24) == pytest.approx(24 / 25)

    def test_new_season_starts_at_0(self):
        assert season_progress(25) == 0.0


class TestSeasonAdditional:
    def test_spring_speed_default(self):
        eff = get_season_effects(Season.SPRING)
        assert eff.speed_mult == 1.0

    def test_summer_gather_default(self):
        eff = get_season_effects(Season.SUMMER)
        assert eff.gather_mult == 1.0

    def test_autumn_energy_default(self):
        eff = get_season_effects(Season.AUTUMN)
        assert eff.energy_mult == 1.0

    def test_autumn_speed_default(self):
        eff = get_season_effects(Season.AUTUMN)
        assert eff.speed_mult == 1.0
