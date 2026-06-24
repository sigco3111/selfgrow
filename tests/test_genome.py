"""Genome 단위 테스트 — 돌연변이, 교차, 초기화."""

from __future__ import annotations

import random

from sim import config
from sim.genome import Genome


def test_random_initial_valid_range():
    """초기 형질이 0.0~1.0 범위인지 확인."""
    g = Genome.random_initial(config.create_rng(42, "test"))
    for trait_name in ["risk_tolerance", "curiosity", "sociability",
                        "aggression", "industry", "innovation_rate",
                        "strength", "endurance", "speed", "fertility"]:
        val = getattr(g, trait_name)
        assert 0.0 <= val <= 1.0, f"{trait_name} = {val}"


def test_mutation_changes_traits():
    """변이 후 적어도 하나의 형질이 변경됨."""
    rng = config.create_rng(42, "test")
    g = Genome.random_initial(rng)
    for _ in range(20):
        mutated = g.mutate(rng)
        if any(getattr(mutated, t) != getattr(g, t)
               for t in ["risk_tolerance", "curiosity", "sociability",
                         "aggression", "industry", "innovation_rate",
                         "strength", "endurance", "speed", "fertility"]):
            return
    assert False, "20회 변이 시도 중 변경된 형질 없음"


def test_mutation_preserves_generation():
    """변이 시 generation 카운터가 증가하는지 확인."""
    rng = config.create_rng(42, "test")
    g = Genome.random_initial(rng)
    gen_before = g.generation
    mutated = g.mutate(rng)
    assert mutated.generation == gen_before + 1


def test_crossover_mixes_traits():
    """교차 후 자식 형질이 부모 사이에 위치하는지 확인."""
    rng = config.create_rng(42, "test")
    parent_a = Genome.random_initial(rng)
    parent_b = Genome.random_initial(rng)
    child = Genome.crossover(parent_a, parent_b, rng)
    for t in ["risk_tolerance", "curiosity", "sociability",
              "aggression", "industry", "innovation_rate",
              "strength", "endurance", "speed", "fertility"]:
        av = getattr(parent_a, t)
        bv = getattr(parent_b, t)
        cv = getattr(child, t)
        # 자식은 부모 중 한쪽 값을 가져야 함 (uniform crossover)
        assert cv == av or cv == bv, f"{t}: child={cv} not in ({av}, {bv})"


def test_crossover_advances_generation():
    """교차 시 자식 generation이 부모 최대값 +1인지 확인."""
    rng = config.create_rng(42, "test")
    p1 = Genome.random_initial(rng)
    p2 = Genome.random_initial(rng)
    child = Genome.crossover(p1, p2, rng)
    assert child.generation == max(p1.generation, p2.generation) + 1


def test_specialization_remains_valid():
    """specialization이 유효한 문자열 집합에 속하는지 확인."""
    g = Genome.random_initial(config.create_rng(42, "test"))
    valid = {"general", "farmer", "miner", "merchant", "warrior",
             "crafter", "explorer"}
    assert g.specialization in valid
