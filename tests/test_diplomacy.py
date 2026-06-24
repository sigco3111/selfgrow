"""외교 시스템 테스트 — 조약, 관계, tick_diplomacy."""

from __future__ import annotations

from unittest.mock import MagicMock

from sim.diplomacy import DiplomacyManager
from sim.faction import Faction
from sim import config


def _make_faction(fid: int) -> Faction:
    world = MagicMock()
    return Faction(name=f"F{fid}", leader_id=fid * 10, world=world)


def test_set_relation():
    dm = DiplomacyManager()
    f = _make_faction(0)
    dm.set_relation(f, 1, "ALLIANCE")
    assert dm.get_relation(f, 1) == "ALLIANCE"


def test_set_relation_invalid():
    dm = DiplomacyManager()
    f = _make_faction(0)
    dm.set_relation(f, 1, "INVALID")
    assert dm.get_relation(f, 1) is None


def test_get_relation_none():
    dm = DiplomacyManager()
    f = _make_faction(0)
    assert dm.get_relation(f, 1) is None


def test_remove_relation():
    dm = DiplomacyManager()
    f = _make_faction(0)
    dm.set_relation(f, 1, "ALLIANCE")
    dm.remove_relation(f, 1)
    assert dm.get_relation(f, 1) is None


def test_has_treaty_with():
    dm = DiplomacyManager()
    f = _make_faction(0)
    dm.set_relation(f, 1, "TRADE_PACT")
    assert dm.has_treaty_with(f, 1, "TRADE_PACT")
    assert not dm.has_treaty_with(f, 1, "ALLIANCE")


def test_is_neutral():
    dm = DiplomacyManager()
    f1 = _make_faction(0)
    f2 = _make_faction(1)
    assert dm.is_neutral(f1, 1)


def test_is_not_neutral_at_war():
    dm = DiplomacyManager()
    f1 = _make_faction(0)
    f1.declare_war(1)
    assert not dm.is_neutral(f1, 1)


def test_is_not_neutral_alliance():
    dm = DiplomacyManager()
    f1 = _make_faction(0)
    dm.set_relation(f1, 1, "ALLIANCE")
    assert not dm.is_neutral(f1, 1)


def test_propose_treaty_alliance():
    dm = DiplomacyManager()
    f1 = _make_faction(0)
    f2 = _make_faction(1)
    old = config.DIPLOMACY_ENABLED
    config.DIPLOMACY_ENABLED = True
    try:
        result = dm.propose_treaty(f1, f2, "ALLIANCE")
        assert result is True
        assert dm.get_relation(f1, f2.faction_id) == "ALLIANCE"
        assert dm.get_relation(f2, f1.faction_id) == "ALLIANCE"
    finally:
        config.DIPLOMACY_ENABLED = old


def test_propose_treaty_trade_pact():
    dm = DiplomacyManager()
    f1 = _make_faction(0)
    f2 = _make_faction(1)
    old = config.DIPLOMACY_ENABLED
    config.DIPLOMACY_ENABLED = True
    try:
        result = dm.propose_treaty(f1, f2, "TRADE_PACT")
        assert result is True
        assert dm.get_relation(f1, f2.faction_id) == "TRADE_PACT"
    finally:
        config.DIPLOMACY_ENABLED = old


def test_propose_treaty_non_aggression():
    dm = DiplomacyManager()
    f1 = _make_faction(0)
    f2 = _make_faction(1)
    old = config.DIPLOMACY_ENABLED
    config.DIPLOMACY_ENABLED = True
    try:
        result = dm.propose_treaty(f1, f2, "NON_AGGRESSION")
        assert result is True
        assert dm.get_relation(f1, f2.faction_id) == "NON_AGGRESSION"
    finally:
        config.DIPLOMACY_ENABLED = old


def test_propose_treaty_disabled():
    dm = DiplomacyManager()
    f1 = _make_faction(0)
    f2 = _make_faction(1)
    old = config.DIPLOMACY_ENABLED
    config.DIPLOMACY_ENABLED = False
    try:
        result = dm.propose_treaty(f1, f2, "ALLIANCE")
        assert result is False
    finally:
        config.DIPLOMACY_ENABLED = old


def test_propose_treaty_at_war():
    dm = DiplomacyManager()
    f1 = _make_faction(0)
    f2 = _make_faction(1)
    f1.declare_war(f2.faction_id)
    old = config.DIPLOMACY_ENABLED
    config.DIPLOMACY_ENABLED = True
    try:
        result = dm.propose_treaty(f1, f2, "ALLIANCE")
        assert result is False
    finally:
        config.DIPLOMACY_ENABLED = old


def test_break_treaty():
    dm = DiplomacyManager()
    f1 = _make_faction(0)
    f2 = _make_faction(1)
    dm.set_relation(f1, f2.faction_id, "ALLIANCE")
    dm.remove_relation(f1, f2.faction_id)
    assert dm.get_relation(f1, f2.faction_id) is None
