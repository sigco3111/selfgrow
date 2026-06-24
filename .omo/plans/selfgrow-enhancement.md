# selfgrow 고도화 계획

> **작성일**: 2026-06-24
> **목적**: 다음 세션에서 바로 실행할 수 있는 체계적인 고도화 로드맵
> **예상 범위**: 기술 부채 해소 → 모듈 통합 → 신규 기능 → 문서 현행화

---

## 1. 프로젝트 현황

### 1.1 현재 상태
- **총 모듈**: 76개 (sim/ 47 + sim/ui/ 12 + tests/ 17)
- **총 라인 수**: ~7,800줄
- **현재 Phase**: Phase 5 완료 (AGENTS.md는 Phase 4.5까지만 문서화)
- **외부 의존성**: Rich(TUI) 하나만 사용
- **Python 버전**: 3.11+

### 1.2 구현된 시스템
| 카테고리 | 시스템 | 모듈 |
|---------|--------|------|
| 코어 | 유전 알고리즘 (11형질 + 7직업) | `genome.py` |
| 코어 | 듀얼 브레인 (RuleBased + Smart) | `brain.py`, `brain_*.py` |
| 코어 | 시장 (지정가 주문장, 2% 수수료) | `market.py` |
| 전투 | 다중 개체, 동맹, 장비/지식 약탈 | `entity_combat.py` |
| 사회 | 파벌 (결성/영토/전쟁) | `faction.py`, `faction_system.py` |
| 사회 | 외교 (4종 조약) | `diplomacy.py` |
| 사회 | 이데올로기 (4종) | `ideology.py` |
| 사회 | 문화 (언어/관습) | `cultural.py` |
| 환경 | 계절 (4계절 25틱) | `season.py` |
| 환경 | 랜덤 이벤트 (6종) | `events.py` |
| 환경 | 건물 (5종) | `buildings.py` |
| 인프라 | 공간 인덱싱 (QuadTree) | `spatial.py` |
| 인프라 | 무역 네트워크 | `trade_network.py` |
| 인프라 | 글로벌 연구 | `research.py` |
| 분석 | 실험 프레임워크 | `experiment.py` |
| 분석 | 데이터 내보내기 (CSV/JSON) | `exporter.py` |
| UI | Rich 기반 TUI (5개 레이아웃) | `visualizer.py`, `sim/ui/` |

### 1.3 현재 기술 부채
| # | 심각도 | 파일 | 문제 |
|---|--------|------|------|
| 1 | 🔴 | `faction_system.py:92-103` | 동일한 전쟁 선포 루프가 2회 실행 (버그) |
| 2 | 🟠 | `config.py:22-31, 410-422` | `create_rng` 함수 중복 정의 |
| 3 | 🔴 | `trade_network.py:43-44` | `is_active` 항상 True 반환 (duration 무시) |
| 4 | 🟠 | `engine.py:135` | 매 틱마다 이벤트 RNG 재생성 |
| 5 | 🟠 | `faction.py:96-99` | O(n²) 응집력 계산 (15명 파벌 → 105쌍 비교) |
| 6 | 🟠 | `market.py:81-85` | 매 주문마다 전체 정렬 O(n log n) |
| 7 | 🟡 | `spatial.py` | QuadTree 171줄 구현, 미사용 |

### 1.4 테스트 커버리지 현황
- **기존 테스트**: 161개 (전체 통과)
- **테스트 미커버 모듈**: 22개 (metrics, resource, world, brain_*, entity_* 등)
- **pytest-cov**: 미설정
- **커버리지 수치**: 미측정

---

## 2. 고도화 계획 (4 Wave)

### 🌊 Wave 1 — 기술 부채 해소 + 인프라

> **목적**: 기존 버그 수정 및 성능 최적화
> **의존성**: 없음 (7개 작업 병렬 실행)
> **예상 소요**: 2~3시간

| # | 작업 | 파일 | 변경량 | 검증 방법 |
|---|------|------|--------|-----------|
| T1 | faction_system.py 중복 전쟁 루프 제거 | `sim/faction_system.py:92-103` | -13줄 | `pytest tests/test_faction.py tests/test_faction_diplomacy.py -q` |
| T2 | config.py 중복 create_rng 정리 | `sim/config.py:22-31` | -10줄 | `pytest tests/ -q` |
| T3 | trade_network.py is_active 버그 수정 | `sim/trade_network.py:43-44` | ~7줄 | `pytest tests/test_trade_network.py -q` |
| T4 | engine.py 이벤트 RNG 캐싱 | `sim/engine.py:135` | ±1줄 | `pytest tests/test_engine.py -q` |
| T5 | faction.py O(n²) → O(n) 응집력 최적화 | `sim/faction.py:96-99` | ~15줄 | `pytest tests/test_faction.py -q` |
| T6 | market.py bisect.insort 최적화 | `sim/market.py:81-85` | ~10줄 | `pytest tests/test_market.py -q` |
| T9 | pytest 설정 + 커버리지 구성 | `pyproject.toml` | +20줄 | 경고 없이 실행 |

#### T1 상세: faction_system.py 중복 제거
```python
# 삭제 대상: L92-105 (L79-91과 완전히 동일)
# 확인 방법: diff로 두 블록 비교
```

#### T3 상세: trade_network.py is_active 수정
```python
# 변경 전
@property
def is_active(self) -> bool:
    return True  # 버그

# 변경 후
def is_expired(self, current_tick: int) -> bool:
    return (current_tick - self.created_tick) >= self.duration
```

#### T5 상세: faction.py 응집력 최적화
```python
# 변경 전: O(n²) 쌍 비교
for i, e1 in enumerate(alive_members):
    for e2 in alive_members[i + 1:]:
        ideology_bonus += same_ideology_bonus(e1, e2)

# 변경 후: O(n) 카운트 + 조합 공식
ideology_counts = {}
for e in alive_members:
    ideology_counts[e.ideology] = ideology_counts.get(e.ideology, 0) + 1
# 조합: sum(cnt*(cnt-1)/2 for cnt in ideology_counts.values())
```

#### T9 상세: pytest 설정
```toml
# pyproject.toml에 추가
[tool.pytest.ini_options]
testpaths = ["tests"]
markers = [
    "performance: performance benchmark tests",
]
addopts = "-v --tb=short"

[tool.coverage.run]
source = ["sim"]
omit = ["tests/*", "sim/ui/*"]

[tool.coverage.report]
fail_under = 60
show_missing = true
```

---

### 🌊 Wave 2 — 모듈 통합 + 테스트 확대

> **목적**: 누락 모듈 테스트 추가 및 미통합 모듈 연결
> **의존성**: Wave 1 완료 후 (6개 작업 병렬 실행)
> **예상 소요**: 4~6시간

| # | 작업 | 파일 | 변경량 | 검증 방법 |
|---|------|------|--------|-----------|
| T7 | QuadTree를 world.py에 통합 | `sim/world.py`, `sim/spatial.py` | ~40줄 | `pytest tests/test_spatial.py tests/test_performance.py -q` |
| T8 | trade_network를 engine.py에 통합 | `sim/engine.py`, `sim/entity_action.py` | ~25줄 | `pytest tests/test_engine.py tests/test_trade_network.py -q` |
| T10 | 테스트 배치 1: 코어 모듈 | `tests/test_world.py` 등 5개 | +250~350줄 | 185개+ 테스트 |
| T11 | 테스트 배치 2: 파벌/개체 | `tests/test_faction_system.py` 등 6개 | +300~400줄 | 210개+ 테스트 |
| T12 | 테스트 배치 3: 브레인/지원 | `tests/test_brain_*.py` 등 9개 | +350~500줄 | 240개+ 테스트 |
| T20 | GitHub Actions CI 파이프라인 | `.github/workflows/ci.yml` | +40줄 | YAML 검증 |

#### T7 상세: QuadTree 통합
```python
# world.py 변경
from .spatial import QuadTree

class World:
    def __init__(self, width: int, height: int):
        # 기존: self._spatial_index: Dict[Tuple[int,int], List[int]] = {}
        self._quadtree = QuadTree(0, 0, width, height)
    
    def spawn_entity(self, entity_id: int, x: int, y: int) -> None:
        self._quadtree.insert(entity_id, x, y)
    
    def remove_entity(self, entity_id: int, x: int, y: int) -> None:
        self._quadtree.remove(entity_id, x, y)
    
    def entities_near(self, x: int, y: int, radius: int) -> List[int]:
        return self._quadtree.query_radius(x, y, radius)
```

#### T8 상세: trade_network 통합
```python
# engine.py __init__에 추가
from .trade_network import get_trade_network
self.trade_network = get_trade_network()

# engine.py _step()에 추가 (파벌 처리 후)
self.trade_network.tick(self.faction_manager.faction_reg, self.world)
```

#### T10 상세: 테스트 배치 1 목록
- `tests/test_world.py`: 지형 생성, 엔티티 생성/제거, 타일 클레임, 공간 쿼리
- `tests/test_resource.py`: 바이옴 자원 생성, 타일 속성
- `tests/test_config.py`: 설정 오버라이드, create_rng 결정론
- `tests/test_metrics.py`: 스냅샷 기록, 지니계수, HHI
- `tests/test_research.py`: 글로벌 연구 포인트 축적

#### T11 상세: 테스트 배치 2 목록
- `tests/test_faction_system.py`: process_factions 생명주기
- `tests/test_diplomacy.py`: 조약 제안, 관계, tick_diplomacy
- `tests/test_entity_action.py`: 행동 점수, 결정 로직
- `tests/test_entity_combat.py`: 데미지 계산, 장비 보정
- `tests/test_entity_craft.py`: 레시피 검증, 자원 차감
- `tests/test_entity_reproduce.py`: 후손 생성, 유전자 교차

#### T12 상세: 테스트 배치 3 목록
- `tests/test_brain_base.py`: 기본 두뇌 인터페이스
- `tests/test_brain_goals.py`: 목표 생성, 추적
- `tests/test_brain_planning.py`: 멀티스텝 계획
- `tests/test_brain_messaging.py`: 메시지 송수신
- `tests/test_smart_brain.py`: 경험 학습, 피드백
- `tests/test_rule_brain.py`: 점수 계산
- `tests/test_messaging.py`: 메시지 배달
- `tests/test_exporter.py`: CSV/JSON 내보내기
- `tests/test_experiment.py`: 실험 프레임워크

---

### 🌊 Wave 3 — 신규 기능 개발

> **목적**: 화폐 시스템, 기술 확장, 저장/로드 등 핵심 기능 추가
> **의존성**: Wave 2 완료 후 (6개 작업 병렬 실행)
> **예상 소요**: 6~8시간

| # | 작업 | 파일 | 변경량 | 검증 방법 |
|---|------|------|--------|-----------|
| T13 | AGENTS.md 현행화 (Phase 5+) | `AGENTS.md` | ~80줄 | 문서 일치 확인 |
| T15 | 화폐 시스템 활성화 | `entity.py`, `entity_action.py`, `config.py` | ~200줄 | 200틱 시뮬레이션 |
| T16 | 기술 트리 Tier 5+ (5개 기술) | `config.py` | +30줄 | 기술 발견 테스트 |
| T17 | 시뮬레이션 저장/로드 | `sim/savefile.py` (신규) | +250줄 | 라운드트립 테스트 |
| T18 | 새 이데올로기 2종 | `config.py`, `ideology.py` | +65줄 | 이데올로기 테스트 |
| T19 | 새 랜덤 이벤트 2종 | `config.py`, `events.py` | +75줄 | 이벤트 테스트 |

#### T15 상세: 화폐 시스템
```python
# entity.py에 추가
class CurrencyType(Enum):
    NONE = "none"
    SHELL = "shell"
    COIN = "coin"

# config.py에 추가
CURRENCY_RATES = {
    "shell_gather_rate": 0.1,
    "coin_trade_bonus": 0.2,
    "shell_to_coin_threshold": 100,
}

# entity_action.py에 추가
def do_trade(entity, partner, resource_type, amount):
    # 기존: 직접 자원 교환
    # 변경: 화폐를 통한 거래 경로 추가
    if entity.currency_type != CurrencyType.NONE:
        # 화폐 기반 거래
        cost = calculate_currency_cost(resource_type, amount)
        if entity.currency >= cost:
            entity.currency -= cost
            # 자원 전달
```

#### T16 상세: Tier 5+ 기술
```python
# config.py TECH_TREE에 추가
"printing": {
    "tier": 5,
    "requires": ["currency", "architecture"],
    "description": "인쇄술 — 지식 전파 속도 +50%",
},
"gunpowder": {
    "tier": 5,
    "requires": ["metallurgy", "alchemy"],
    "description": "화약 — 공격 +10, 원거리 전투",
},
"navigation": {
    "tier": 5,
    "requires": ["sailing", "currency"],
    "description": "항해술 — 무역 효율 +40%, 탐험 범위 +2",
},
"democracy": {
    "tier": 5,
    "requires": ["bureaucracy"],
    "description": "민주주의 — 파벌 결속 +0.3, 독재 없음",
},
"philosophy": {
    "tier": 5,
    "requires": ["printing"],
    "description": "철학 — 이데올로기 전파 +30%, 학습 속도 +20%",
},
```

#### T17 상세: 저장/로드 기능
```python
# sim/savefile.py (신규 모듈)
@dataclass
class SaveState:
    tick: int
    seed: int
    entities: List[dict]
    world: dict
    market: dict
    factions: List[dict]
    tech_tree: dict
    metrics: dict

def save_game(engine: SimulationEngine, path: str) -> None:
    state = SaveState(
        tick=engine.tick,
        seed=engine._seed,
        entities=[serialize_entity(e) for e in engine.world.entities.values()],
        # ...
    )
    with open(path, 'w') as f:
        json.dump(asdict(state), f, indent=2, default=str)

def load_game(path: str) -> SaveState:
    with open(path, 'r') as f:
        data = json.load(f)
    return SaveState(**data)
```

#### T18 상세: 새 이데올로기
```python
# config.py IDEOLOGIES에 추가
"environmentalism": {
    "preferred_actions": ["gather", "explore"],
    "avoided_actions": ["craft", "combat"],
    "trait_weights": {"curiosity": 0.3, "innovation_rate": -0.2},
    "description": "환경주의 — 자연 보전, 채집/탐험 선호",
},
"technocracy": {
    "preferred_actions": ["craft", "research"],
    "avoided_actions": ["gather"],
    "trait_weights": {"innovation_rate": 0.4, "industry": 0.2},
    "description": "기술주의 — 기술 발전, 제작/연구 선호",
},
```

#### T19 상세: 새 이벤트
```python
# config.py EVENT_TYPES에 추가
"FESTIVAL": {
    "duration": 20,
    "effects": {
        "energy_bonus": 10,
        "trade_bonus": 0.3,
        "sociability_bonus": 0.2,
    },
    "description": "축제 — 사회적 보너스, 무역 활성화",
},
"EPIDEMIC": {
    "duration": 30,
    "effects": {
        "energy_drain": 5,
        "death_chance": 0.05,
        "movement_penalty": 0.5,
    },
    "description": "전염병 — 에너지 소모, 이동 제한",
},
```

---

### 🌊 Wave 4 — 문서 정리

> **목적**: 프로젝트 문서 현행화
> **의존성**: Wave 3 완료 후
> **예상 소요**: 1시간

| # | 작업 | 파일 | 변경량 |
|---|------|------|--------|
| T14 | README.md 현행화 | `README.md` | ~60줄 |

#### T14 상세: README.md 업데이트 항목
- 기능 목록에 화폐 시스템, Tier 5 기술, 저장/로드 추가
- 개발 진행 상황에 Phase 5+ 추가
- 시스템 구조도 업데이트
- CLI 사용법 업데이트 (--save, --load 플래그)

---

## 3. 실행 방법

### 3.1 다음 세션 시작 시
```
1. 이 문서(.omo/plans/selfgrow-enhancement.md) 읽기
2. 현재 상태 확인: git status, git log --oneline -5
3. 테스트 실행: python -m pytest tests/ -q (161개 통과 확인)
4. Wave 1부터 순차 실행
```

### 3.2 각 Wave 실행 순서
```
Wave 1: T1~T9 병렬 실행 → 전체 테스트 통과 확인
Wave 2: T7~T20 병렬 실행 → 전체 테스트 통과 확인
Wave 3: T13~T19 병렬 실행 → 전체 테스트 통과 확인
Wave 4: T14 실행 → 문서 완료
```

### 3.3 커밋 전략
각 작업 완료 시마다 원자적 커밋:
```
[faction_system] Remove duplicate war declaration loop
[config] Remove duplicate create_rng definition
[trade_network] Fix is_active always-True bug
[engine] Cache event RNG to avoid per-tick recreation
[faction] Optimize O(n²) cohesion to O(n)
[market] Replace full sort with bisect.insort
[pytest] Add pytest config, coverage settings
[world] Integrate QuadTree for spatial queries
[engine] Integrate trade_network into main tick loop
[tests] Add tests for core modules (batch 1)
[tests] Add tests for faction/entity modules (batch 2)
[tests] Add tests for brain/support modules (batch 3)
[config] Add Tier 5+ technologies
[config] Add new ideologies: environmentalism, technocracy
[events] Add festival and epidemic random events
[entity] Activate CurrencyType system
[savefile] Add JSON-based simulation save/load
[ci] Add GitHub Actions CI pipeline
[docs] Update AGENTS.md through Phase 5+
[docs] Update README.md through Phase 5+
```

---

## 4. 검증 체크리스트

### Wave 1 완료 시
- [ ] `faction_system.py`에 중복 루프 없음
- [ ] `config.py`에 `create_rng` 1개만 존재
- [ ] `trade_network.py`의 `is_expired()` 메서드 정상 동작
- [ ] `engine.py`의 이벤트 RNG가 한 번만 생성됨
- [ ] `faction.py`의 응집력 계산이 O(n)으로 동작
- [ ] `market.py`의 주문 삽입이 bisect로 동작
- [ ] `pytest` 실행 시 경고 없음
- [ ] 기존 161개 테스트 전체 통과

### Wave 2 완료 시
- [ ] `world.py`가 QuadTree 사용
- [ ] `engine.py`가 `trade_network.process_trades()` 호출
- [ ] 신규 테스트 80개+ 추가
- [ ] 총 테스트 240개+ 통과
- [ ] 커버리지 60% 이상

### Wave 3 완료 시
- [ ] 화폐 시스템 동작 (CurrencyType != NONE)
- [ ] Tier 5 기술 5개 존재
- [ ] 저장/로드 라운드트립 통과
- [ ] 새 이데올로기 6종 존재
- [ ] 새 이벤트 8종 존재

### Wave 4 완료 시
- [ ] AGENTS.md가 Phase 5+ 반영
- [ ] README.md가 현재 상태 반영

---

## 5. 예상 성과

| 항목 | 현재 | 목표 |
|------|------|------|
| 테스트 수 | 161개 | **240개+** |
| 커버리지 | 미측정 | **60%+** |
| 기술 부채 | 7건 | **0건** |
| 기능 수 | Phase 5 | **Phase 5+** |
| CI/CD | 없음 | **GitHub Actions** |
| 문서 | Phase 4.5 기준 | **Phase 5+ 현행화** |

---

## 6. 참고 사항

### 6.1 파일별 라인 수 제한
- AGENTS.md 규칙: 단일 파일 700줄 미만
- 현재 최대: `config.py` 321줄, `ui/layouts.py` 310줄
- 준수 여부: ✅ 모든 파일 통과

### 6.2 주의 사항
- `faction.py` ↔ `diplomacy.py` 순환 의존성 존재 (lazy import로 회피 중)
- `entity.py`는 30+ 속성을 가진 God Object (분리 검토 필요)
- `smart_brain.py`의 `experiences`/`experience_ticks` 평행 deque 동기화 필요

### 6.3 확장 가능 영역 (장기)
- `CurrencyType` Enum 활성화 ✅ (T15)
- 기술 트리 Tier 5+ 확장 ✅ (T16)
- 시뮬레이션 저장/로드 ✅ (T17)
- 추가 이데올로기 ✅ (T18)
- 추가 이벤트 ✅ (T19)
- 로깅 시스템 (표준 `logging` 모듈 도입)
- 멀티 프로세스 시뮬레이션
- 웹 기반 시각화 (Rich 대신 브라우저)

---

**이 문서는 `.omo/plans/selfgrow-enhancement.md`에 저장되어 있습니다.**
**다음 세션에서 이 문서를 참조하여 실행을 시작하세요.**
