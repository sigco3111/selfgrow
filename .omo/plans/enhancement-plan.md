# 자가발전 문명 시뮬레이션 — 고도화 실행 계획

> **목표**: 웹 시각화를 제외한 모든 고도화 항목(P0~P3)을 순차적으로 진행
> **제약**: LLM/외부AI 금지, 서브에이전트 금지, 단일파일 700줄 제한, engine.py 300줄 목표
> **검증**: 매 단계 `python -m sim.main --no-visual --ticks 200 --seed 42/7/99` 통과

---

## Phase 0 — 기반 정비 (P0)

### 0.1 재현성: 전역 random → 시드 기반 RNG 인스턴스

**목적**: `random` 모듈을 직접 호출하는 모든 모듈을 `random.Random(seed)` 인스턴스로 교체하여 시드 고정 시 완전 재현 가능하게 함

**변경 파일**:
- `sim/config.py` — `SEED` 상수 유지, `def create_rng(seed: int, subsystem: str) -> random.Random` 팩토리 함수 추가
- `sim/world.py` — `self.rng` 유지, `self.random` 필드 추가로 engine/entity/brain 전달
- `sim/engine.py` — `SimulationEngine.__init__()`에서 `random.Random(seed)` 생성, 모든 하위 모듈에 전달
- `sim/entity.py` — `self._rng: random.Random` 필드 추가, `random.choice/uniform/random` 호출을 `self._rng`로 대체
- `sim/brain.py` — `Brain.__init__(rng=None)` 파라미터 추가, SmartBrain/RuleBasedBrain `self._rng` 사용
- `sim/market.py`, `sim/faction.py`, `sim/events.py` — 함수/메서드 시그니처에 `rng: random.Random` 파라미터 추가

**검증**: 시드 42로 두 번 실행 → 매 틱 동일한 개체 상태 비교

---

### 0.2 `id(entity)` → `World`의 안정적 entity ID 사용

**목적**: Python `id()`는 GC 후 재사용 가능 → `World._next_entity_id` 중심으로 통일

**변경 파일**:
- `sim/engine.py` — `_seed_entities()`에서 `world.spawn_entity()` 반환값을 entity_id로 사용
  - `self.world.claim_tile(..., id(entity))` → `self.world.claim_tile(..., eid)`
  - `self._log_event({"entity_id": id(entity), ...})` → `{"entity_id": eid, ...}`
  - `id(entity)` 참조 6곳 모두 교체
  - `_process_brain_messages()`에서 `msg.target_id` → `world.entities.get(msg.target_id)` 유지 (메시지는 entity_id 사용)
- `sim/entity.py` — `_event()` 메서드에서 `"entity_id": id(self)` → `"entity_id": (전달받거나 self._entity_id로)` 
  - `Entity.__init__`에 `entity_id: int` 파라미터 추가
  - `self.eid = entity_id` 저장

**검증**: 200틱 실행 후 `id()` 참조가 entity_id로 대체되었는지 grep 검사. `id(entity)` 패턴이 engine.py 내에 0건인지 확인.

---

### 0.3 매직 넘버 → config.py 이동 (~30개)

**목적**: entity.py/market.py/brain.py에 하드코딩된 수치 상수를 config.py로 이동

**변경 파일**:
- `sim/config.py` — 아래 상수들을 새 섹션에 추가
- `sim/entity.py` — 상수 참조를 `config.XXX`로 대체
- `sim/market.py` — `PRICE_FLOOR`와 `base_prices`를 `config.py`로 이동
- `sim/brain.py` — 메시지 처리 임계값을 config 참조로 대체

**이동할 상수 목록**:

| 현재 위치 | 현재 값 | config.py 이름 |
|-----------|---------|---------------|
| entity.py:314 | `max_slot = 8` | `RESOURCE_MAX_STACK = 8` |
| entity.py:320 | `can_gather = 2.0 * ...` | `BASE_GATHER_RATE = 2.0` |
| entity.py:343 | `consume = min(food, 2.0)` | `CONSUME_FOOD_AMOUNT = 2.0` |
| entity.py:359 | `surplus_threshold = 4 if rtype == "food" else 3` | `TRADE_SURPLUS_THRESHOLD = {"food": 4, "default": 3}` |
| entity.py:361 | `sell_qty = amount * 0.5` | `TRADE_SELL_RATIO = 0.5` |
| entity.py:466 | `int(self.knowledge.count() * 0.3)` | `KNOWLEDGE_INHERIT_RATIO = 0.3` |
| entity.py:471 | `self.inventory.get(rtype, 0) * 0.2` | `RESOURCE_BEQUEST_RATIO = 0.2` |
| entity.py:641 | `len(self.equipped) < 3` | `MAX_EQUIPPED_SLOTS = 3` |
| entity.py:676 | `self.energy -= 5.0` | `AGING_ENERGY_COST = 5.0` |
| market.py:56-58 | base prices dict | `BASE_PRICES` |
| market.py:148-151 | `PRICE_FLOOR` | `PRICE_FLOOR` |
| brain.py:584 (SmartBrain) | `if current < 3` | `SMART_TRADE_THRESHOLD = 3` |
| brain.py:599 | `(5 if food else 3)` | `SMART_SURPLUS_THRESHOLDS` |
| engine.py:300 | `random.random() < 0.4` | `RESEARCH_BASIC_BIAS = 0.4` |
| engine.py:313 | `random.random() < 0.1` | `TECH_PIONEER_CHANCE = 0.1` |
| engine.py:376 | `random.random() < 0.3` | `FACTION_FORM_CHANCE = 0.3` |
| events.py:54 | `randint(3, 8)`, `randint(10, 25)` | `EVENT_RADIUS_RANGE`, `EVENT_DURATION_RANGE` |
| events.py:55 | `uniform(0.3, 1.0)` | `EVENT_SEVERITY_RANGE` |

**검증**: `grep '"food"\|max_slot\|sell_qty\|bequest\|PRICE_FLOOR'` 등으로 잔여 매직 넘버 0건 확인. 200틱 기존 시드와 동일한 결과 비교.

---

### 0.4 성능: 공간 해싱 (Spatial Index)

**목적**: `_cultural_transfer` O(N²), `_do_combat` O(N), `_process_factions` O(F·N²)를 O(N + neighbors)로 축소

**변경 파일**:
- `sim/world.py` — `SpatialIndex` 내부 클래스 또는 `World._spatial: dict[tuple, list[int]]` 추가
  - `update_spatial_index(entity_id, old_x, old_y, new_x, new_y)` — 개체 이동 시 인덱스 갱신
  - `entities_near(x, y, radius) -> list[int]` — 반경 내 개체 ID O(1) 조회
- `sim/entity.py` — `_do_combat()`에서 인접 개체/동맹 조회를 `world.entities_near()`로 대체
- `sim/engine.py` — `_cultural_transfer()`에서 `world.entities_near()` 사용; `_process_factions()`에서 동일 적용
- `sim/entity.py` — `_do_explore()`에서 이동 후 `world.update_spatial_index()` 호출

**자료구조**:
```python
# World에 추가
self._spatial_index: dict[tuple[int, int], list[int]] = {}  # (x,y) → [entity_id, ...]

def entities_near(self, x: int, y: int, radius: int = 1) -> list[int]:
    result = []
    for dx in range(-radius, radius + 1):
        for dy in range(-radius, radius + 1):
            key = (x + dx, y + dy)
            if key in self._spatial_index:
                result.extend(self._spatial_index[key])
    return result
```

**검증**: 200틱 실행 결과(인구, 지니계수)가 리팩토링 전과 동일한지 비교. `_cultural_transfer`의 O(N²)이 O(N·k)로 바뀌었는지 코드 검증.

---

### 0.5 성능: Tech Effects 캐시

**목적**: `get_combined_effects()`가 매 호출마다 `config.TECH_TREE`를 선형 탐색(O(11))하는 것을 O(1) dict lookup으로

**변경 파일**:
- `sim/config.py` 또는 `sim/knowledge.py` — `TECH_EFFECTS: dict[str, dict]` 빌드 `@functools.cache` 또는 모듈 로드 시점에 생성
  ```python
  TECH_EFFECTS: dict[str, dict[str, float]] = {}
  for tdef in TECH_TREE:
      TECH_EFFECTS[tdef.name] = tdef.effect
  ```
- `sim/entity.py` — `get_combined_effects()` 수정
  ```python
  def get_combined_effects(self) -> dict:
      combined = {}
      for tech_name in self.knowledge.known:
          effects = TECH_EFFECTS.get(tech_name, {})
          for k, v in effects.items():
              ...
  ```
- `sim/buildings.py` — `get_building_effects()`도 유사하게 캐시 적용 (선택)

**검증**: `TECH_TREE` 선형 탐색이 사라졌는지 grep 확인. 200틱 실행 결과 동일.

---

### 0.6 메모리 안전: 무제한增长了 자료구조 제한

**목적**: `market.trade_history`, `metrics.snapshots`의 무제한 성장 방지

**변경 파일**:
- `sim/market.py` — `self.trade_history: deque = deque(maxlen=5000)` (또는 config.MAX_TRADE_HISTORY)
- `sim/metrics.py` — `self.snapshots: deque = deque(maxlen=1000)` (또는 config.MAX_SNAPSHOTS)
- `sim/engine.py` — `self.event_log`를 `deque(maxlen=10000)`으로 변경 (현재 list + pop(0) O(n) 해결)
- `sim/faction.py` — `self.wealth_history: deque = deque(maxlen=500)`

**검증**: 5000틱 실행 후 메모리 사용량이 안정적인지 확인 (작업 관리자 또는 `tracemalloc`).

---

### 0.7 데이터 내보내기 (CSV/JSON)

**목적**: README 약속 Phase 4 이행 — 시뮬레이션 결과를 파일로 저장

**신규 파일**:
- `sim/exporter.py` — 내보내기 모듈 (목표: 150줄 이내)

**변경 파일**:
- `sim/main.py` — `--export PATH` CLI 인자 추가, `--export-format {csv,json}` 선택
- `sim/metrics.py` — `export_csv(path)`, `export_json(path)` 메서드 추가

**exporter.py 구조**:
```python
def export_snapshots_csv(snapshots: list[Snapshot], path: str) -> None
def export_snapshots_json(snapshots: list[Snapshot], path: str) -> None
def export_event_log(events: list[dict], path: str) -> None
def export_all(engine: SimulationEngine, path: str, fmt: str = "csv") -> None
```

**내보낼 데이터**:
- `{path}/snapshots.csv` — tick, population, gini, diversity, avg_wealth, smart_count, rule_count, ...
- `{path}/events.jsonl` — event_log (JSON Lines)
- `{path}/prices.csv` — tick, food_price, wood_price, stone_price, iron_price, gold_price
- `{path}/metadata.json` — seed, config params, duration

**검증**: `python -m sim.main --no-visual --ticks 200 --seed 42 --export exports/test` 실행 후 CSV 3개 파일 생성 확인. pandas로 로드 가능한지 확인.

---

## Phase 1 — 테스트 + 모듈 분리 (P1)

### 1.1 패키징: pyproject.toml 추가

**목적**: `pip install -e .` 가능하게 하고 테스트 import 문제 해결

**신규 파일**:
- `pyproject.toml` — setuptools 기반 패키징

**검증**: `pip install -e .` 성공 + `python -c "from sim import SimulationEngine"` 정상 import.

---

### 1.2 테스트 인프라: conftest.py + fixture

**목적**: 테스트 간 공유 fixture로 반복 코드 제거

**신규 파일**:
- `tests/conftest.py` — `seeded_world`, `sample_entity`, `mock_market`, `base_engine` fixture

**구조**:
```python
@pytest.fixture
def seeded_rng():
    return random.Random(42)

@pytest.fixture
def sample_world(seeded_rng):
    world = World(seed=42)
    world._rng = seeded_rng
    return world

@pytest.fixture
def sample_entity(sample_world):
    return Entity(x=10, y=10)

@pytest.fixture
def base_engine():
    return SimulationEngine(seed=42)
```

---

### 1.3 단위 테스트 추가

**목적**: 핵심 로직 14개 모듈 테스트 커버리지 확보

**신규 테스트 파일** (우선순위 순):

1. **`tests/test_entity.py`** (100+라인)
   - `test_decide_action_returns_valid_state` — brain이 항상 유효한 EntityState 반환
   - `test_do_consume_restores_energy` — 식량 소비 후 에너지 증가
   - `test_do_gather_depletes_tile` — 채집 후 타일 자원 감소
   - `test_do_reproduce_creates_child` — 번식 후 자식 개체 생성 확인
   - `test_do_combat_damage_range` — 전투 데미지가 ±25% 범위 내
   - `test_do_craft_consumes_materials` — 제작 시 재료 소비 확인
   - `test_age_update_decreases_energy` — 노화 효과 확인
   - `test_total_wealth_includes_inventory` — 자산 계산 정확성

2. **`tests/test_brain.py`** (120+라인)
   - `test_rule_based_returns_valid_state` — RuleBasedBrain이 항상 유효 상태 반환
   - `test_smart_brain_experience_learning` — 경험 저장/조회
   - `test_smart_brain_goal_generation` — 목표 자동 생성 조건
   - `test_smart_brain_message_handling` — 메시지 송수신
   - `test_state_similarity_identical` — 동일 상태 유사도 = 1.0
   - `test_state_similarity_different` — 완전 다른 상태 유사도 < 0.5

3. **`tests/test_market.py`** (80+라인)
   - `test_place_order_buy` — 매수 주문 등록 확인
   - `test_place_order_sell` — 매도 주문 등록 확인
   - `test_immediate_match` — 가격 조건 충족 시 즉시 체결
   - `test_order_expiry` — 20틱 후 주문 만료
   - `test_tax_collection` — 2% 수수료 정확성
   - `test_price_history` — 가격 지수 업데이트 확인

4. **`tests/test_engine.py`** (100+라인) — **통합 테스트**
   - `test_engine_runs_200_ticks` — 200틱 멸종 없이 실행
   - `test_engine_smart_brain_ratio` — SmartBrain 비율이 config와 일치
   - `test_engine_metrics_recorded` — 스냅샷이 주기적으로 기록됨
   - `test_engine_faction_formation` — 파벌이 조건에 따라 결성됨
   - `test_engine_reproducibility` — 동일 시드 → 동일 결과

5. **`tests/test_faction.py`** (70+라인)
   - `test_try_form_factions_eligibility` — 사회성 조건 충족 시 파벌 결성
   - `test_faction_cohesion_calculation` — 결속력 계산 정확성
   - `test_faction_cleanup_disband` — 멤버 부족 시 해체
   - `test_faction_war_declaration` — 전쟁 선포/타이머/종료

6. **`tests/test_genome.py`** (50+라인)
   - `test_mutation_changes_traits` — 변이 후 형질 변경됨
   - `test_crossover_mixes_traits` — 교차 후 양 부모 특성 혼합
   - `test_random_initial_valid_range` — 초기 형질 0.0~1.0 범위

7. **`tests/test_knowledge.py`** (40+라인)
   - `test_learn_new_tech` — 새 기술 습득
   - `test_share_knowledge` — 지식 전수 조건/범위
   - `test_technology_tree_prerequisites` — 선행 조건 검증

---

### 1.4 Entity 모듈 분리 (700줄 → 350줄)

**목적**: 에이전트.md 700줄 제한 준수, 단일 책임 원칙

**분리 방안**:
- `sim/entity_combat.py` — `Entity._do_combat()` (170줄) + 연관 헬퍼 → `entity_combat.py`
- `sim/entity_reproduce.py` — `Entity._do_reproduce()` (60줄) + `age_update()` → `entity_lifecycle.py`
- `sim/entity_craft.py` — `_do_craft()`, `_do_construct()`, `get_gather_bonus()` → `entity_craft.py`
- `sim/entity.py` — 남은 코어: `__init__`, `decide_action`, `execute_action`, `total_wealth`, 속성, `_do_explore`, `_do_gather`, `_do_consume`, `_do_trade`

**변경 파일**:
- `sim/entity.py` — combat/reproduce/craft 메서드를 import한 함수 호출로 대체
- 신규 `sim/entity_combat.py` (목표: 200줄 이내)
- 신규 `sim/entity_reproduce.py` (목표: 100줄 이내)  
- 신규 `sim/entity_craft.py` (목표: 80줄 이내)
- `sim/__init__.py` — 새 모듈 익스포트

**참고**: Entity 자체는 dataclass로 전환하지 않고 유지 (변경 범위 최소화). `entity.py` 자체를 dataclass로 바꾸면 모든 필드 초기화 로직이 깨짐.

**검증**: 200틱 실행 결과(인구, 지니계수, 이벤트 로그)가 분리 전과 완전히 동일한지 비교. `entity.py` 350줄 이하 확인.

---

### 1.5 Engine 모듈 분리 (442줄 → 250줄)

**목적**: 300줄 목표 준수, 하위 시스템 독립 모듈화

**분리 방안**:
- `sim/research.py` — `Engine._process_research()` (60줄) → `ResearchSystem` 클래스
- `sim/cultural.py` — `Engine._cultural_transfer()` (25줄) → `CulturalTransferSystem` (공간 인덱스 사용)
- `sim/faction_system.py` — `Engine._process_factions()` (70줄) → `FactionSystem` 클래스
- `sim/messaging.py` — `Engine._process_brain_messages()` (15줄) → `MessageSystem` 클래스
- `sim/engine.py` — 남은 것: `_step()` (조정자 역할), `_seed_entities()`, `_log_event()`, `run()`, `state()`

**변경 파일**:
- 신규 `sim/research.py` (목표: 100줄)
- 신규 `sim/cultural.py` (목표: 50줄)
- 신규 `sim/faction_system.py` (목표: 100줄)
- 신규 `sim/messaging.py` (목표: 50줄)
- `sim/engine.py` — 시스템 클래스들을 생성/호출 (442→250줄)
- `sim/__init__.py` — 새 모듈 익스포트
- `tests/test_engine.py` — 시스템별 단위 테스트 추가

**검증**: 200틱 실행 결과 동일. `engine.py` 300줄 이하 확인. 각 시스템이 독립적으로 테스트 가능한지 확인.

---

### 1.6 Brain 모듈 분리 (750줄 → 300+250+200)

**목적**: 700줄 제한 위반 해결

**분리 방안**:
- `sim/brain_base.py` — `Brain` 추상 클래스, `Experience`, `Goal`, `BrainMessage` dataclass
- `sim/brain_rule.py` — `RuleBasedBrain` (250줄 → 200줄)
- `sim/brain_smart.py` — `SmartBrain` (500줄 → 350줄)
- `sim/brain_factory.py` — `create_brain()` 팩토리 함수

**변경 파일**:
- 기존 `sim/brain.py` → 삭제
- 신규 `sim/brain_base.py` (목표: 100줄)
- 신규 `sim/brain_rule.py` (목표: 200줄)
- 신규 `sim/brain_smart.py` (목표: 350줄)
- 신규 `sim/brain_factory.py` (목표: 30줄)
- `sim/__init__.py` — `from .brain_base import Brain, Experience, Goal, BrainMessage`
- `sim/entity.py` — `from .brain_base import Brain, RuleBasedBrain` → `from .brain_rule import RuleBasedBrain`

**검증**: 200틱 실행 결과 동일. 각 brain 파일 400줄 이하 확인. 전체 brain 관련 코드 750→680줄로 축소.

---

## Phase 2 — 기능 고도화 (P2)

### 2.1 외교 시스템

**목적**: 단순 전쟁/평화를 넘어 다양한 외교 관계 지원

**변경 파일**:
- `sim/config.py` — 외교 관련 상수 추가:
  ```python
  DIPLOMACY_ENABLED = True
  DIPLOMATIC_RELATIONS = ["neutral", "alliance", "non_aggression", "trade_pact", "war", "vassal"]
  ALLIANCE_BREAK_COHESION = 0.2
  TRADE_PACT_TAX_DISCOUNT = 0.5
  ```
- `sim/faction.py` — `Faction`에 외교 관계 테이블 추가:
  ```python
  self.diplomacy: dict[int, str] = {}  # faction_id → relation
  def set_relation(self, target_id: int, relation: str) -> bool
  def get_relation(self, target_id: int) -> str
  def propose_treaty(self, target_id: int, treaty_type: str) -> bool
  ```
- `sim/faction_system.py` — 외교 틱 업데이트 (관계 자동 악화/개선, 동맹 자동 결성)
- `sim/entity.py` — `_do_trade()`에서 무역 협정 시 수수료 할인 적용
- `sim/brain_smart.py` — 외교 제안/수락/거절 메시지 핸들러 추가
- `sim/visualizer.py` — 외교 관계 표시 (파벌 패널에 관계 테이블)

**외교 관계 효과**:
| 관계 | 효과 |
|------|-------|
| neutral | 기본, 아무 효과 없음 |
| alliance | 공동 방어, 전투 시 동맹 지원 보너스 +5% 추가 |
| non_aggression | 상호 불가침, 전투 점수 0으로 강제 |
| trade_pact | 상호 거래 수수료 50% 할인 |
| war | 현재와 동일 |
| vassal | 종속 관계, 매 틱 자원의 10%를 상위 파벌에 제공 |

**검증**: 500틱 실행 후 파벌 간 외교 관계가 형성/변경되는지 이벤트 로그 확인.

---

### 2.2 실험 프레임워크

**목적**: 동일 시드에서 config 변경 효과를 통계적으로 비교 가능하게 함

**신규 파일**:
- `sim/experiment.py` (목표: 200줄)

**인터페이스**:
```python
@dataclass
class ExperimentConfig:
    base_seed: int = 42
    trials: int = 10
    max_ticks: int = 500
    overrides: dict = field(default_factory=dict)  # config key → value

@dataclass
class ExperimentResult:
    config: ExperimentConfig
    snapshots: list[Snapshot]  # 마지막 틱 스냅샷만 각 trial별
    survival_rates: list[float]
    avg_final_gini: float
    std_final_gini: float

class ExperimentRunner:
    def run(self, config: ExperimentConfig) -> ExperimentResult
    def compare(self, results: list[ExperimentResult]) -> dict
    def report(self, results: list[ExperimentResult]) -> str
```

**변경 파일**:
- `sim/main.py` — `--experiment FILE` CLI 인자, 실험 설정 JSON 로드
- `sim/config.py` — config override 지원 함수 `def apply_overrides(base: dict, overrides: dict) -> None`

**사용 예**:
```bash
python -m sim.main --experiment experiments/smart_ratio.json
```

```json
{
    "base_seed": 42,
    "trials": 30,
    "max_ticks": 500,
    "overrides": {
        "SMART_BRAIN_RATIO": [0.0, 0.25, 0.5, 0.75, 1.0]
    }
}
```

**검증**: 5개 SMART_BRAIN_RATIO × 10 trials = 50회 실행 완료. 결과 CSV 출력 확인.

---

## Phase 3 — 콘텐츠 심화 (P3)

### 3.1 종교/이데올로기 시스템

**목적**: 개체 집단 내 가치관 분화 → 창발 행동 다양화

**신규 파일**:
- `sim/ideology.py` (목표: 150줄)

**변경 파일**:
- `sim/config.py` — 이데올로기 정의:
  ```python
  IDEOLOGIES = {
      "materialism": {  # 물질 중시 → 거래/채집 선호
          "traits": {"industry": 0.15, "sociability": 0.1},
          "action_bias": {"trade": 1.3, "gather": 1.2, "craft": 1.2},
      },
      "militarism": {   # 군국주의 → 전투/영토 선호
          "traits": {"aggression": 0.2, "loyalty": 0.15},
          "action_bias": {"combat": 1.5, "explore": 1.1},
      },
      "spiritualism": { # 영성 중시 → 지식/사회성 선호
          "traits": {"curiosity": 0.1, "sociability": 0.15},
          "action_bias": {"explore": 1.2, "reproduce": 1.2},
      },
      "egalitarianism": { # 평등주의 → 거래/분배 선호
          "traits": {"sociability": 0.2, "loyalty": 0.1},
          "action_bias": {"trade": 1.4},
      },
  }
  IDEOLOGY_FORMATION_TICKS = 30     # 이데올로기 형성에 필요한 틱
  IDEOLOGY_TRANSFER_RADIUS = 2      # 전파 반경
  IDEOLOGY_CONVERSION_CHANCE = 0.05 # 주변 개체 전향 확률
  ```

- `sim/entity.py` — `self.ideology: str = "none"` 필드 추가, 행동 점수에 이데올로기 보정 적용
- `sim/brain_rule.py` / `sim/brain_smart.py` — `_base_scores()`에 이데올로기 바이어스 곱
- `sim/engine.py` — `_process_ideology()` 틱 함수 추가 (step() 내 호출)
- `sim/cultural.py` — 이데올로기 전파 로직 추가 (기존 지식 전수와 유사)
- `sim/visualizer.py` — 이데올로기 분포 패널 추가

**이데올로기 형성 메커니즘**:
1. 개체의 유전자 형질(aggression, sociability 등)과 경험이 특정 이데올로기와 일치하면 자동 채택
2. 인접 개체 간 낮은 확률로 전파 (문화적 진화와 유사)
3. SmartBrain 개체는 목표 시스템에 이데올로기 반영 가능
4. 같은 이데올로기를 가진 개체 간 사회성/협력 보너스
5. 다른 이데올로기를 가진 개체 간 마찰(사회성 패널티)

**검증**: 500틱 실행 후 2개 이상의 이데올로기가 존재하는지 확인. 동일 이데올로기 파벌 내 결속력 증가 확인.

---

## 실행 로드맵

```
Phase 0: 기반 정비 (P0)
├── 0.1 재현성: RNG 인스턴스화          ⏱ 1일
├── 0.2 id(entity) → entity_id         ⏱ 0.5일
├── 0.3 매직 넘버 → config.py           ⏱ 1일
├── 0.4 공간 해싱                       ⏱ 1.5일
├── 0.5 Tech Effects 캐시               ⏱ 0.5일
├── 0.6 메모리: deque 제한              ⏱ 0.5일
└── 0.7 데이터 내보내기 (CSV/JSON)      ⏱ 1일
                                      ─────
                              소계: 6일

Phase 1: 테스트 + 모듈 분리 (P1)
├── 1.1 pyproject.toml 패키징           ⏱ 0.5일
├── 1.2 conftest.py + fixture           ⏱ 0.5일
├── 1.3 단위 테스트 7개 모듈            ⏱ 3일
├── 1.4 Entity 분리 (3개 모듈)          ⏱ 1.5일
├── 1.5 Engine 분리 (4개 시스템)        ⏱ 1.5일
└── 1.6 Brain 분리 (3개 모듈)           ⏱ 1일
                                      ─────
                              소계: 8일

Phase 2: 기능 고도화 (P2)
├── 2.1 외교 시스템                     ⏱ 2일
└── 2.2 실험 프레임워크                 ⏱ 1.5일
                                      ─────
                              소계: 3.5일

Phase 3: 콘텐츠 심화 (P3)
└── 3.1 종교/이데올로기 시스템          ⏱ 2일
                                      ─────
                              소계: 2일

                      총 예상 기간: 19.5일
```

---

## Phase별 종료 조건 (Definition of Done)

| Phase | 조건 |
|-------|------|
| **0** | `python -m sim.main --no-visual --ticks 200 --seed 42/7/99` 3개 시드 모두 멸종 없이 완료. `id(entity)` grep 0건. `random.Random` 인스턴스 사용 확인. `--export`로 CSV 생성 확인. |
| **1** | `pytest tests/` 통과 (기존 + 신규). `entity.py` 350줄 이하. `engine.py` 300줄 이하. `brain_*.py` 각 400줄 이하. 3개 시드 200틱 통과. |
| **2** | 외교 관계 형성/변경 이벤트 로그 출력 확인. `--experiment`로 50회 연속 실행 완료. 3개 시드 통과. |
| **3** | 이데올로기 분포 시각화 패널 확인. 동일 이데올로기 파벌 내 결속력 통계적 우위 확인. 3개 시드 통과. |

---

## 리스크 및 대응

| 리스크 | 영향 | 대응 |
|--------|------|------|
| 공간 해싱 도입으로 버그 발생 | 시뮬레이션 결과 불일치 | Phase 0.4 전후로 동일 시드 결과 비교 테스트 필수 |
| Entity 분리 중 import 순환 참조 | 컴파일 에러 | `TYPE_CHECKING` + 지연 import 패턴 유지, 분리 전 의존성 그래프 먼저 작성 |
| Phase 2 외교 시스템이 기존 밸런스 붕괴 | 비정상적인 파벌 행동 | config에 `DIPLOMACY_ENABLED = False` 기본값, True일 때만 활성화 |
| Phase 3 이데올로기 = 단순 가중치 조정에 그침 | 창발 행동 부재 | 설계 시 `action_bias` 외에 파벌 형성/지식 전수/거래 선호도까지 영향 범위 확장 |
| 총 19.5일 예상 > 실제 여유 부족 | 중간에 중단 | 각 Phase가 독립적이므로 P0만 완료해도 가치 있음. P0 완료 시점에 중간 점검 권장 |
