"""시뮬레이션 엔진 — 메인 루프, 개체 생명주기, 이벤트 디스패치."""

from __future__ import annotations

import random
import time
from dataclasses import dataclass, field
from typing import Optional

from . import config
from .brain import BrainMessage, create_brain
from .entity import Entity, EntityState
from .faction import Faction
from .genome import Genome
from .knowledge import TechnologyTree
from .market import Market
from .metrics import MetricsCollector
from .world import World


@dataclass
class EngineState:
    """엔진 상태 요약."""
    tick: int
    population: int
    alive_count: int
    running: bool


class SimulationEngine:
    """시뮬레이션 메인 엔진 — 세계를 생성하고 틱을 실행."""

    def __init__(self, seed: int | None = None):
        self.world = World(seed=seed)
        self.market = Market()
        self.tech_tree = TechnologyTree()
        self.metrics = MetricsCollector()

        self.running = False
        self.tick_count = 0
        self.event_log: list[dict] = []
        self._max_event_log = 10000  # 메모리 보호

        # 기술 발전 관련
        self._global_research_points: dict[str, float] = {}
        self._discovered_techs: set[str] = set()

        # 초기 개체 생성
        self._seed_entities()

    def _seed_entities(self) -> None:
        """초기 개체를 월드에 랜덤 배치."""
        spawnable = []
        for y in range(self.world.height):
            for x in range(self.world.width):
                tile = self.world.tile_at(x, y)
                if tile and tile.is_traversable():
                    spawnable.append((x, y))

        for _ in range(config.INITIAL_ENTITY_COUNT):
            if not spawnable:
                break
            x, y = random.choice(spawnable)
            entity = Entity(x, y)
            # 초기 인벤토리
            entity.inventory["food"] = random.uniform(5, 10)
            entity.inventory["wood"] = random.uniform(2, 5)
            entity.inventory["stone"] = random.uniform(1, 3)

            # 초기 지식 (무작위 1개)
            available = self.tech_tree.get_available(self._discovered_techs)
            if available:
                starter = random.choice(available)
                entity.knowledge.learn(starter.name)

            # 두뇌 할당 (RuleBasedBrain or SmartBrain)
            entity.brain = create_brain(entity, self.world)

            self.world.spawn_entity(entity)

    # ──────────────────────────────────────────
    # 메인 루프
    # ──────────────────────────────────────────
    def run(self, max_ticks: int = 1000, realtime: bool = False,
            on_tick=None) -> None:
        """시뮬레이션 실행."""
        self.running = True
        self.tick_count = 0

        for _ in range(max_ticks):
            if not self.running:
                break
            self._step()
            self.tick_count += 1

            if on_tick:
                on_tick(self)

            if realtime:
                time.sleep(config.TICK_INTERVAL_MS / 1000.0)

            # 멸종 검사
            alive = [e for e in self.world.entities.values() if e.alive]
            if not alive:
                self.running = False
                break

        self.running = False
        return self.state()

    def _step(self) -> None:
        """한 틱 실행."""
        # 1. 월드 업데이트 (자원 재생성)
        self.world.tick_update()

        # 2. 시장 업데이트 (주문 에이징)
        self.market.tick_update()

        # 3. 개체 행동
        entities = list(self.world.entities.values())
        random.shuffle(entities)  # 처리 순서 랜덤화

        for entity in entities:
            if not entity.alive:
                continue

            # 나이 먹기
            entity.age_update()

            if not entity.alive:
                self.metrics.record_death()
                continue

            # 기술 효과 적용
            entity.apply_knowledge_effects()

            # 주거 기록 (매 틱 현재 타일에서 보낸 시간 증가)
            current_pos = (entity.x, entity.y)
            entity.residence_counter[current_pos] = entity.residence_counter.get(current_pos, 0) + 1
            if len(entity.visited_tiles) > config.HOME_SITE_MEMORY:
                entity.visited_tiles.pop(0)
            entity.visited_tiles.append(current_pos)
            # 본거지 결정
            if entity.residence_counter:
                best_tile = max(entity.residence_counter, key=entity.residence_counter.get)
                if (entity.residence_counter[best_tile] >= config.TERRITORY_CLAIM_TICKS
                        and (entity.home_x, entity.home_y) != best_tile):
                    entity.home_x, entity.home_y = best_tile
                    self.world.claim_tile(best_tile[0], best_tile[1], id(entity))

            # 기아
            if entity.energy <= 0:
                entity.alive = False
                self.metrics.record_death()
                self._log_event({
                    "tick": self.world.tick,
                    "type": "starvation",
                    "entity_id": id(entity),
                    "entity_name": entity.name,
                })
                continue

            # 행동 결정 및 실행
            before_wealth = entity.total_wealth()
            before_energy = entity.energy
            action = entity.decide_action(self.world, self.market)
            events = entity.execute_action(action, self.world, self.market)

            # SmartBrain 피드백: 행동 결과 점수 기록
            after_wealth = entity.total_wealth()
            after_energy = entity.energy
            outcome = ((after_wealth - before_wealth) * 0.5
                       + (after_energy - before_energy) * 0.02)
            entity.brain.feedback(entity, entity.last_action, outcome)

            # 이벤트 로그
            for ev in events:
                ev["tick"] = self.world.tick
                self._log_event(ev)
                if ev["type"] == "reproduce":
                    self.metrics.record_birth()
                if ev["type"] == "energy_depleted":
                    self.metrics.record_death()
                if ev.get("data", {}).get("target_alive") is False:
                    self.metrics.record_death()
                    self.metrics.record_kill()
                # 파벌 전투: 파벌 킬/로스 기록
                if ev["type"] == "combat":
                    target_alive = ev.get("data", {}).get("target_alive", True)
                    attacker_faction = self.world.faction_registry.get(
                        getattr(entity, "faction_id", -1), None)
                    if attacker_faction and not target_alive:
                        attacker_faction.total_kills += 1
                if ev["type"] == "equipment_broken":
                    pass  # 이미 entity에서 처리

        # 4. 사망 개체 정리
        dead_ids = [eid for eid, e in self.world.entities.items() if not e.alive]
        for eid in dead_ids:
            self.world.remove_entity(eid)

        # 5. SmartBrain 메시지 수집 및 배달
        self._process_brain_messages()

        # 6. 기술 연구 (글로벌)
        self._process_research()

        # 7. 파벌 생명주기
        self._process_factions()

        # 8. 문화적 진화: 인접 개체 간 지식 전수
        self._cultural_transfer()

        # 9. 주기적 스냅샷
        if self.world.tick % config.METRICS_SNAPSHOT_INTERVAL == 0:
            snap = self.metrics.snapshot(
                self.world.tick, self.world, self.market
            )
            # 기술 정보 갱신
            snap.discovered_techs = self.tech_tree.discover_count()
            snap.total_techs = self.tech_tree.total_count()

    # ──────────────────────────────────────────
    # 하부 프로세스
    # ──────────────────────────────────────────
    def _process_brain_messages(self) -> None:
        """SmartBrain의 outbox 메시지를 수집해 대상 개체의 mailbox로 배달."""
        messages: list[BrainMessage] = []
        for entity in self.world.entities.values():
            if not entity.alive:
                continue
            if hasattr(entity.brain, "outbox"):
                messages.extend(entity.brain.outbox)
                entity.brain.outbox.clear()

        for msg in messages:
            target = self.world.entities.get(msg.target_id)
            if target and target.alive:
                if not hasattr(target, "mailbox"):
                    continue
                target.mailbox.append(msg)

    def _process_research(self) -> None:
        """개체들이 연구 포인트를 생성하고 기술에 집중/분산 투자."""
        research_points = 0.0
        for entity in self.world.entities.values():
            if not entity.alive:
                continue
            innovation = entity.genome.innovation_rate
            knowledge_count = entity.knowledge.count()
            points = (
                innovation * config.RESEARCH_POINT_BASE_RATE
                * (1 + knowledge_count * config.RESEARCH_POINT_PER_KNOWLEDGE)
            )
            research_points += points

        if research_points <= 0:
            return

        available = self.tech_tree.get_available(self._discovered_techs)
        if not available:
            return

        # 집중 연구: 일정 확률로 현재 진행 중인 기술에 계속 투자
        focus_target = None
        for tech in available:
            if tech.research_progress > 0 and random.random() < config.RESEARCH_FOCUS_THRESHOLD:
                focus_target = tech
                break

        if focus_target is None:
            # 새 기술 선택 (지식 전수로 퍼지는 기초 기술 우선)
            basics = [t for t in available if not t.prerequisites]
            if basics and random.random() < 0.4:
                focus_target = random.choice(basics)
            else:
                focus_target = random.choice(available)

        # 연구 포인트 투자
        if focus_target.research(research_points):
            self._discovered_techs.add(focus_target.name)

            # 발견 시 모든 개체에게 알림 (문화적 전파: 인접 개체부터 퍼짐)
            discoverers = []
            for entity in self.world.entities.values():
                if entity.alive and entity.genome.innovation_rate > 0.5:
                    if random.random() < 0.1:  # 10% 확률로 즉시 학습 (선구자)
                        entity.knowledge.learn(focus_target.name)
                        entity.apply_knowledge_effects()
                        discoverers.append(entity.name)

            self._log_event({
                "tick": self.world.tick,
                "type": "tech_discovery",
                "data": {
                    "tech": focus_target.name,
                    "description": focus_target.description,
                    "discoverers": discoverers[:5],
                },
            })

    def _cultural_transfer(self) -> None:
        """인접 개체 간 지식 전수 (문화적 진화)."""
        entities = list(self.world.entities.values())
        for entity in entities:
            if not entity.alive or entity.genome.sociability < 0.2:
                continue
            # 같은 타일 또는 인접 타일의 개체 찾기
            for other in entities:
                if (other is entity or not other.alive):
                    continue
                dist = abs(other.x - entity.x) + abs(other.y - entity.y)
                if dist <= 1:  # 인접 또는 동일 타일
                    transferred = entity.knowledge.share(
                        other.knowledge, entity.genome.sociability
                    )
                    for tech in transferred:
                        self._log_event({
                            "tick": self.world.tick,
                            "type": "knowledge_transfer",
                            "entity_id": id(entity),
                            "entity_name": entity.name,
                            "data": {"from": entity.name, "to": other.name,
                                     "tech": tech},
                        })

    # ──────────────────────────────────────────
    # 파벌 처리
    # ──────────────────────────────────────────
    def _process_factions(self) -> None:
        """파벌 생명주기: 결성, 결속력, 영토, 전쟁, 해체."""
        if not config.FACTION_ENABLED:
            return

        world = self.world
        entities = world.entities
        faction_reg = world.faction_registry

        # 1. 기존 파벌 결속력/강도/영토 업데이트
        for faction in faction_reg.values():
            faction.set_cohesion(entities)
            faction.compute_strength(entities)
            faction.update_territory(entities, world)
            faction.tick_wars()

        # 2. 전쟁 중인 파벌 간 자동 교전: 같은 타일의 적대 파벌 멤버 전투 유도
        # (entity.py의 decide_action에서 처리)

        # 3. 새 파벌 결성 시도
        if random.random() < 0.3:  # 매 틱 30% 확률로 결성 시도 (성능)
            new_factions = Faction.try_form_factions(
                entities, world, faction_reg
            )
            for faction in new_factions:
                faction_reg[faction.faction_id] = faction
                for eid in faction.members:
                    ent = entities.get(eid)
                    if ent:
                        ent.faction_id = faction.faction_id
                self._log_event({
                    "tick": world.tick,
                    "type": "faction_formed",
                    "data": {
                        "faction": faction.name,
                        "leader": entities.get(faction.leader_id).name if entities.get(faction.leader_id) else "?",
                        "members": faction.member_count,
                    },
                })

        # 4.사용자 파벌 해체 (멤버 부족 또는 결속력过低)
        disbanded = Faction.cleanup_factions(faction_reg, entities)
        for fid in disbanded:
            faction = faction_reg.pop(fid, None)
            if faction:
                self._log_event({
                    "tick": world.tick,
                    "type": "faction_disbanded",
                    "data": {
                        "faction": faction.name,
                        "reason": "members_below_2",
                    },
                })

        # 5. 자동 전쟁 선포: 같은 타일에서 다른 파벌 멤버를 공격하면 전쟁
        for faction in list(faction_reg.values()):
            for eid in list(faction.members):
                ent = entities.get(eid)
                if not ent or not ent.alive:
                    continue
                # 같은 타일의 다른 파벌 멤버 확인
                for other_eid, other_ent in entities.items():
                    if (other_ent.alive and other_ent.faction_id >= 0
                            and other_ent.faction_id != faction.faction_id
                            and (other_ent.x, other_ent.y) == (ent.x, ent.y)):
                        target_faction = faction_reg.get(other_ent.faction_id)
                        if target_faction:
                            faction.declare_war(target_faction.faction_id)
                            target_faction.declare_war(faction.faction_id)

    # ──────────────────────────────────────────
    # 이벤트 로그
    # ──────────────────────────────────────────
    def _log_event(self, event: dict) -> None:
        if len(self.event_log) >= self._max_event_log:
            self.event_log.pop(0)
        self.event_log.append(event)

    # ──────────────────────────────────────────
    # 상태 조회
    # ──────────────────────────────────────────
    def state(self) -> EngineState:
        alive = sum(1 for e in self.world.entities.values() if e.alive)
        return EngineState(
            tick=self.world.tick,
            population=len(self.world.entities),
            alive_count=alive,
            running=self.running,
        )

    def get_alive_entities(self) -> list[Entity]:
        return [e for e in self.world.entities.values() if e.alive]
