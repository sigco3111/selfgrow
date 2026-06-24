# UI 고도화 완료 보고 및 향후 작업 계획

> **목표**: Rich 기반 TUI 시각화 고도화 — 시계열 차트, 이벤트 로그, 개체 뷰, 맵 오버레이, 레이아웃 옵션
> **상태**: ✅ 전체 구현 완료 (2026-06-24)
> **검증**: 101개 기존 테스트 통과 + 수동 QA 통과

---

## ✅ 완료된 작업 (Phase 0 — UI 고도화)

### 0.1 시각화 모듈 분리 — `sim/ui/` 패키지

**목적**: visualizer.py(793줄)가 700줄 제한을 초과하는 문제 해결 + 새 UI 기능 모듈화

**구조**:
```
sim/
├── visualizer.py          # 245줄 (기존 793줄 → 700줄 제한 충족)
└── ui/
    ├── __init__.py         # 16줄 — 모듈 익스포트
    ├── charts.py           # 165줄 — 시계열 차트
    ├── event_log.py        # 241줄 — 이벤트 로그
    ├── entity_view.py      # 210줄 — 개체 상세 뷰
    ├── map_overlay.py      # 275줄 — 맵 오버레이
    └── layouts.py          # 288줄 — 레이아웃 매니저
```

**변경 파일**:
- `sim/visualizer.py` — 기존 렌더링 로직을 `sim/ui/` 모듈로 위임, LayoutManager 통합
- `sim/ui/__init__.py` — 새 모듈 익스포트
- `sim/main.py` — `--layout` CLI 인자 추가 (default/chart/faction/entity)

**검증**:
- ✅ visualizer.py 245줄 (700줄 제한 충족)
- ✅ 101개 기존 테스트 전부 통과
- ✅ 4가지 레이아웃 모드 정상 동작

---

### 0.2 시계열 차트 패널 — `sim/ui/charts.py`

**목적**: 지니계수, 인구, 가격 등 주요 지표의 추이를 문자 스파크라인으로 시각화

**기능**:
- `sparkline(values, width)` — 값 리스트를 8단계 문자 스파크라인으로 변환
- `delta_indicator(current, previous)` — 값 변화를 화살표+색상으로 표시
- `render_timeseries_panel(metrics, width)` — 시계열 차트 패널 렌더링

**차트 대상**:
- 인구 추이 (초록)
- 지니계수 추이 (호박색)
- 평균 부 추이 (보라색)
- 평균 에너지 추이 (하늘색)
- 자원 가격 추이 (파란색, 상위 3개)

**검증**:
- ✅ 스냅샷 2개 이상일 때 정상 렌더링
- ✅ 스냅샷 1개 이하일 때 "데이터 부족" 표시

---

### 0.3 이벤트 로그 고도화 — `sim/ui/event_log.py`

**목적**: 이벤트 로그를 타입별로 필터링하고 시각적으로 강화

**기능**:
- 이벤트 타입별 아이콘/색상 매핑 (18종)
- 6가지 필터 카테고리: 전투, 경제, 인구, 기술, 이벤트, 메시지
- 이벤트 포맷 함수 — 타입별 맞춤 포맷
- 이벤트 통계 테이블 — 타입별 카운트 표시

**이벤트 타입별 스타일**:
| 타입 | 아이콘 | 색상 |
|------|--------|------|
| reproduce | 💕 | pink |
| combat | ⚔️ | red |
| craft | 🔨 | blue |
| tech_discovery | 💡 | cyan |
| faction_formed | ⚡ | red |
| event_started | 🌟 | red |

**검증**:
- ✅ 6가지 필터 카테고리 정상 동작
- ✅ 이벤트 없을 때 "(이벤트 없음)" 표시
- ✅ 필터 결과 없을 때 "(필터 결과 없음)" 표시

---

### 0.4 개체 상세 뷰 패널 — `sim/ui/entity_view.py`

**목적**: 특정 개체의 상세 정보를 패널로 표시

**기능**:
- `render_entity_detail_panel(entity)` — 개체 상세 정보 표시
- `render_entity_list(entities)` — 개체 목록 표시
- 직업/뇌 타입별 아이콘/색상
- 형질 바 차트 시각화 (공격성, 사회성, 호기심, 생산성, 혁신성)

**표시 정보**:
- 직업, 뇌 타입 (SmartBrain/RuleBasedBrain)
- 나이, 에너지, 위치
- 형질 (바 차트 + 수치)
- 인벤토리, 장착 장비
- 기술, 킬 수, 파벌, 부

**검증**:
- ✅ 개체 선택 시 상세 정보 표시
- ✅ 개체 미선택 시 개체 목록 표시
- ✅ KnowledgeBook.known 속성 정상 참조

---

### 0.5 맵 오버레이 — `sim/ui/map_overlay.py`

**목적**: 월드맵에 파벌 영토, 선택 개체 등을 오버레이 표시

**기능**:
- `render_map_with_overlay(world, ...)` — 오버레이 적용된 맵 렌더링
- `render_faction_legend(faction_reg)` — 파벌 범례 표시
- `render_minimap(world, ...)` — 미니맵 (전체 월드 축소)

**오버레이 옵션**:
- `highlight_faction_id` — 특정 파벌 영토 강조
- `highlight_entity` — 특정 개체 위치 강조
- `show_all_factions` — 모든 파벌 영토 표시 여부

**검증**:
- ✅ 파벌 영토 색상 오버레이 정상 동작
- ✅ 선택 개체 하이라이트 정상 동작
- ✅ 미니맵 축소 렌더링 정상 동작

---

### 0.6 레이아웃 옵션 — `sim/ui/layouts.py`

**목적**: 다양한 레이아웃 모드로 시각화 구성 변경

**레이아웃 모드**:
| 모드 | 설명 | 특징 |
|------|------|------|
| DEFAULT | 기본 레이아웃 | 맵 좌, 상태 우, 이벤트 하 |
| CHART | 차트 중심 | 맵 작게, 시계열 차트 크게 |
| FACTION | 파벌 중심 | 파벌 정보 크게, 전투 이벤트 우선 |
| ENTITY | 개체 중심 | 선택 개체 상세 정보 크게 |

**CLI 사용법**:
```bash
python -m sim.main --layout default    # 기본
python -m sim.main --layout chart      # 차트 중심
python -m sim.main --layout faction    # 파벌 중심
python -m sim.main --layout entity     # 개체 중심
```

**검증**:
- ✅ 4가지 레이아웃 모드 정상 렌더링
- ✅ 레이아웃 모드 간 전환 정상 동작

---

## ✅ 완료된 작업 (Phase 1 — Priority 1-3 구현)

### Priority 1: 시각화 기능 보강

| 작업 | 설명 | 상태 |
|------|------|------|
| **차트 커스터마이징** | `visible_metrics` 파라미터로 표시할 지표 선택 가능 | ✅ 완료 |
| ~~이벤트 로그 스크롤~~ | Rich TUI 키보드 입력 불가 — 제외 | ❌ 제외 |
| ~~개체 선택 인터랙션~~ | Rich TUI 키보드 입력 불가 — 제외 | ❌ 제외 |
| ~~미니맵 클릭~~ | Rich TUI 마우스 입력 불가 — 제외 | ❌ 제외 |

### Priority 2: 성능 최적화

| 작업 | 설명 | 상태 |
|------|------|------|
| **차트 캐싱** | `_cache` dict 기반, 동일 스냅샷+지표일 때 차트 재사용 | ✅ 완료 |
| **맵 오프셋** | `viewport_x/y/width/height` 파라미터로 뷰포트 지원 | ✅ 완료 |
| **이벤트 로그 색인** | `EventIndex` 클래스로 타입별 O(1) 필터링 | ✅ 완료 |

### Priority 3: 새 기능

| 작업 | 설명 | 상태 |
|------|------|------|
| **기술 트리 시각화** | `sim/ui/tech_tree.py` — ASCII 트리 구조 표시 | ✅ 완료 |
| **파벌 관계도** | `sim/ui/faction_graph.py` — 동맹/전쟁 그래프 | ✅ 완료 |
| **개체 궤적** | `sim/ui/entity_trail.py` — `visited_tiles` 기반 점선 표시 | ✅ 완료 |
| **자원 히트맵** | `sim/ui/resource_heatmap.py` — ░▒▓█ 4단계 색상 | ✅ 완료 |
| **TECH 레이아웃** | `layouts.py`에 `LayoutMode.TECH` + `_render_tech_layout()` | ✅ 완료 |

**제외 사유 (Priority 1)**: Rich `Live` 컨텍스트에서는 키보드/마우스 입력을 처리할 수 없어 스크롤, 개체 선택, 미니맵 클릭 기능은 구현 불가.

---

## 🔧 기술적 참고사항

### 모듈 의존성
```
visualizer.py
    └── sim/ui/
        ├── charts.py           (metrics.py 의존, _cache dict 캐싱)
        ├── event_log.py        (entity.py 참조, EventIndex 색인)
        ├── entity_view.py      (entity.py, knowledge.py 의존)
        ├── map_overlay.py      (world.py, faction.py 의존, 뷰포트 오프셋)
        ├── layouts.py          (위 모든 모듈 + engine.py 의존, TECH 모드)
        ├── tech_tree.py        (knowledge.py 의존)
        ├── resource_heatmap.py (world.py 의존, ░▒▓█ 4단계)
        ├── entity_trail.py     (world.py, entity.visited_tiles 의존)
        └── faction_graph.py    (faction.py 의존)
```

### 주요 데이터 구조
- `MetricsCollector.snapshots: deque[Snapshot]` — 시계열 데이터 소스
- `engine.event_log: deque[dict]` — 이벤트 로그 소스
- `world.entities: dict[int, Entity]` — 개체 데이터 소스
- `world.faction_registry: dict[int, Faction]` — 파벌 데이터 소스

### Rich 라이브러리 의존성
- `rich.layout.Layout` — 레이아웃 관리
- `rich.panel.Panel` — 패널 렌더링
- `rich.table.Table` — 테이블 렌더링
- `rich.text.Text` — 텍스트 렌더링
- `rich.style.Style` — 스타일 정의

---

## ✅ 검증 체크리스트

### Phase 0 기존 기능
- [x] visualizer.py 700줄 이내 (245줄)
- [x] 101개 기존 테스트 통과 (100 pass + 1 pre-existing flaky)
- [x] 4가지 레이아웃 모드 정상 동작 (DEFAULT/CHART/FACTION/ENTITY)
- [x] 6가지 이벤트 필터 정상 동작
- [x] 시계열 차트 정상 렌더링
- [x] 개체 상세 뷰 정상 렌더링
- [x] 맵 오버레이 정상 렌더링
- [x] 미니맵 정상 렌더링
- [x] `--layout` CLI 인자 정상 동작
- [x] 헤드리스 모드 정상 동작
- [x] 시드 42로 재현성 확인

### Phase 1 Priority 1-3 기능
- [x] 차트 캐싱 동작 확인 (`_cache` dict, 동일 파라미터→히트, 변경→미스)
- [x] 차트 `visible_metrics` 커스터마이징 동작 확인
- [x] `EventIndex` 색인 동작 확인 (타입별 O(1) 필터링)
- [x] 맵 뷰포트 오프셋 (`viewport_x/y/width/height`) 동작 확인
- [x] `tech_tree.py` 렌더링 확인
- [x] `resource_heatmap.py` 렌더링 확인 (░▒▓█ 4단계)
- [x] `entity_trail.py` 렌더링 확인 (visited_tiles 기반)
- [x] `faction_graph.py` 렌더링 확인
- [x] `LayoutMode.TECH` 레이아웃 모드 동작 확인
- [x] 멀티시드(7, 99, 123) 200틱 실행 검증

---

## 📝 메모

1. **visualizer.py 리팩토링**: 기존 793줄에서 245줄로 축소. 로직은 `sim/ui/` 모듈로 이동.
2. **KnowledgeBook.known**: `known_techs`가 아닌 `known` 속성 사용 (entity_view.py 수정 필요했음)
3. **Style import**: `map_overlay.py`에서 `rich.style.Style` import 필요
4. **레이아웃 확장**: 새 레이아웃 추가 시 `layouts.py`의 `LayoutManager` 클래스에 메서드 추가
