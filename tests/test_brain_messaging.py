"""brain_messaging 모듈 테스트 — 메시지 처리."""

import random
from collections import deque
from sim.brain_messaging import process_messages, send_trade_offer, send_trade_request
from sim.brain_messaging import send_alliance_proposal, send_treaty_proposal
from sim.brain_messaging import send_trade_pact_proposal, send_non_aggression_proposal
from sim.brain_base import BrainMessage
from sim.smart_brain import SmartBrain
from sim.entity import Entity
from sim.genome import Genome
from sim.world import World


def _make_pair():
    rng = random.Random(42)
    g1 = Genome()
    g1.sociability = 0.8
    e1 = Entity(5, 5, genome=g1, rng=rng, entity_id=0)
    e1.inventory["food"] = 10
    g2 = Genome()
    g2.sociability = 0.6
    e2 = Entity(5, 5, genome=g2, rng=rng, entity_id=1)
    e2.inventory["food"] = 2
    w = World(seed=42)
    w.entities[0] = e1
    w.entities[1] = e2
    e1.alive = True
    e2.alive = True
    b1 = SmartBrain(rng=rng)
    b2 = SmartBrain(rng=rng)
    e1.brain = b1
    e2.brain = b2
    return e1, e2, w, b1, b2


class TestProcessMessages:
    def test_empty_mailbox_no_error(self):
        e, _, w, b, _ = _make_pair()
        process_messages(e, w, b)

    def test_trade_offer_accepted_when_low(self):
        e1, e2, w, b1, b2 = _make_pair()
        e1.inventory["food"] = 1
        msg = BrainMessage("trade_offer", 1, 0,
                           {"resource": "food", "quantity": 3})
        e1.mailbox.append(msg)
        process_messages(e1, w, b1)
        assert any(m.msg_type == "trade_accept" for m in b1.outbox)


class TestSendFunctions:
    def test_send_trade_offer(self):
        e1, e2, w, b1, b2 = _make_pair()
        send_trade_offer(e1, w, 1, "food", 5, b1)
        assert len(b1.outbox) == 1
        assert b1.outbox[0].msg_type == "trade_offer"

    def test_send_trade_request(self):
        e1, e2, w, b1, b2 = _make_pair()
        send_trade_request(e1, w, 1, "food", 3, b1)
        assert b1.outbox[0].msg_type == "trade_request"

    def test_send_alliance_proposal(self):
        e1, e2, w, b1, b2 = _make_pair()
        send_alliance_proposal(e1, w, 1, b1)
        assert b1.outbox[0].msg_type == "alliance_proposal"

    def test_send_treaty_proposal(self):
        e1, e2, w, b1, b2 = _make_pair()
        send_treaty_proposal(e1, w, 1, "TRADE_PACT", b1)
        assert b1.outbox[0].msg_type == "treaty_proposal"
        assert b1.outbox[0].data["treaty"] == "TRADE_PACT"

    def test_send_trade_pact_proposal(self):
        e1, e2, w, b1, b2 = _make_pair()
        send_trade_pact_proposal(e1, w, 1, b1)
        assert b1.outbox[0].data["treaty"] == "TRADE_PACT"

    def test_send_non_aggression_proposal(self):
        e1, e2, w, b1, b2 = _make_pair()
        send_non_aggression_proposal(e1, w, 1, b1)
        assert b1.outbox[0].data["treaty"] == "NON_AGGRESSION"
