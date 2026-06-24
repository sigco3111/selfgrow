# 자가발전 문명 시뮬레이션 — 에이전트 규칙

## 1. 기본 규칙

### 🚫 서브에이전트 사용 금지
- 모든 작업은 현재 세션 내에서 직접 수행합니다.
- `task()`로 서브에이전트를 생성하거나 백그라운드 에이전트에 작업을 위임하지 않습니다.
- 탐색(`explore`), 조회(`librarian`), 계획(`plan`), 리뷰(`review-work`) 등 모든 에이전트 유형의 호출이 금지됩니다.
- 예외: 사용자가 명시적으로 "서브에이전트를 써서 조사해줘"라고 요청한 경우에만 허용합니다.

### 🚫 비용 발생 금지
- 외부 API(OpenAI, Anthropic, Google AI 등)를 호출하지 않습니다.
- Web Search, Web Fetch 등 유료/과금 가능한 외부 서비스를 호출하지 않습니다.
- 인터넷 검색, 문서 조회, GitHub 검색 등 외부 네트워크 요청을 보내지 않습니다.
- 모든 작업은 로컬 파일 시스템과 로컬 Python 실행만으로 처리합니다.
- 무료 오픈소스 패키지 설치(pip install)는 예외적으로 허용하되, 사전에 사용자 승인을 받습니다.

### 🇰🇷 한국어 사용
- 사용자와의 모든 질문과 대답은 한국어로 진행합니다.
- 코드 내 주석과 독스트링은 프로젝트 기존 스타일을 따릅니다(현재는 한국어 주석 사용 중).
- 코드 식별자(변수명, 함수명, 클래스명)는 영어를 유지합니다.

---

## 2. 프로젝트 개요

**목표**: 유전 알고리즘 + 시장 메커니즘 + 듀얼 브레인 시스템(RuleBasedBrain/SmartBrain)으로 개체들이 스스로 진화하고 문명을 발전시키는 emergent behavior(창발 행동)를 관찰하는 시뮬레이션. **LLM/외부 AI는 영원히 사용하지 않습니다.**

**현재 단계**: Phase 0 (코어 엔진) ✅ / Phase 1 (밸런싱+전투) ✅ / Phase 2 (전투 심화+파벌) ✅ / Phase 3 (SmartBrain) ✅ / Phase 3.1 (이데올로기/계절/건물/이벤트) ✅ / Phase 4 (UI) ✅ / Phase 4.5 (데이터 내보내기) ✅ / Phase 5 (기술부채해소+CI) ✅

**Python 3.11+**, 표준 라이브러리 + Rich(TUI) 만으로 동작.

---

## 3. 코드베이스 구조

```
selfgrow/
├── 에이전트.md           # 이 파일 — AI 에이전트 규칙
├── README.md             # 프로젝트 개요 및 실행 방법
├── requirements.txt      # 의존성 목록
├── .github/workflows/    # GitHub Actions CI
├── .gitignore
└── sim/
    ├── __init__.py       # 패키지 초기화, 주요 클래스 익스포트
    ├── config.py         # 모든 시뮬레이션 파라미터 (튜너블 상수) — 311줄
    ├── genome.py         # 유전자 — 11개 형질 + 돌연변이/교차 — 90줄
    ├── entity.py         # 개체 — 상태 기계, 행동 실행 — 276줄
    ├── entity_action.py  # 개체 행동 — 채집/소비/탐험 — 125줄
    ├── entity_combat.py  # 전투 — 데미지/약탈/동맹 — 144줄
    ├── entity_craft.py   # 제작 — 레시피/장비 — 43줄
    ├── entity_reproduce.py # 번식 — 유전자 교차/후손 생성 — 63줄
    ├── brain.py          # 두뇌 — 듀얼 시스템入口 — 25줄
    ├── brain_base.py     # Brain 추상 클래스, Experience, Goal — 31줄
    ├── rule_brain.py     # RuleBasedBrain — 점수 기반 FSM — 158줄
    ├── smart_brain.py    # SmartBrain — 경험학습+계획+목표+메시징 — 244줄
    ├── brain_goals.py    # 목표 생성/추적 — 71줄
    ├── brain_planning.py # 멀티스텝 계획 — 59줄
    ├── brain_messaging.py # 메시지 송수신 — 176줄
    ├── messaging.py      # SmartBrain 메시징 — outbox/mailbox 배달 — 20줄
    ├── knowledge.py      # 지식/기술 트리 — 9개 기술 노드 — 99줄
    ├── resource.py       # 자원 — 7개 지형 × 5개 자원 — 104줄
    ├── world.py          # 월드 — 40×30 격자, 공간 질의, 영토 — 208줄
    ├── market.py         # 시장 — 지정가 주문장, 체결, 가격 지수 — 157줄
    ├── trade_network.py  # 무역 네트워크 — 파션 간 자원 교환 — 200줄
    ├── metrics.py        # 통계 — 지니계수, 분업지수, 시계열 — 202줄
    ├── engine.py         # 엔진 — 메인 루프, 개체 생명주기 — 256줄
    ├── faction.py        # 파벌 — 결성/영토/전쟁/음집력 — 251줄
    ├── faction_system.py # 파벌 시스템 — 자동 결성/해체 루프 — 78줄
    ├── diplomacy.py      # 외교 — 4종 조약, 관계 관리 — 118줄
    ├── ideology.py       # 이데올로기 — 4종 행동 바이어스 — 76줄
    ├── cultural.py       # 문화 — 언어/관습/지식 전수 — 131줄
    ├── season.py         # 계절 — 4계절 25틱 순환 — 39줄
    ├── events.py         # 랜덤 이벤트 — 6종 이벤트 — 142줄
    ├── buildings.py      # 건물 — 5종 (저장고/감시탑/벽/대장간/제단)
    ├── spatial.py        # 공간 인덱싱 — QuadTree — 157줄
    ├── research.py       # 글로벌 연구 — 기술 포인트 축적 — 61줄
    ├── experiment.py     # 실험 프레임워크 — 다중 실행 비교 — 162줄
    ├── exporter.py       # 데이터 내보내기 — CSV/JSON — 171줄
    ├── visualizer.py     # 사이버펑크 TUI — Rich 기반 실시간 시각화 — 217줄
    ├── main.py           # CLI 진입점 — argparse + 실행 루프 — 131줄
    └── ui/               # UI 레이아웃 모듈
```

### 모듈 의존성 그래프

```
config.py ── 모든 모듈이 참조 ──┐
                                 ▼
                                    resource.py  genome.py  knowledge.py  metrics.py
                                      └──────┬──────────────┬──────────────┘
                                              ▼
                                          entity.py  ←─── 월드+시장과 상호작용
                                              │
                                              ▼
                                          brain.py  ←─── 듀얼 브레인 시스템
              │
         ┌────┴────┐
         ▼         ▼
      world.py  market.py
         │         │
         └────┬────┘
              ▼
          engine.py  ←─── 메인 루프 조율
              │
         main.py + visualizer.py  ←─── CLI + TUI
```

---

## 4. 시뮬레이션 핵심 메커니즘

### 4.1 개체 (Entity) — entity.py
- 40마리 개체가 `Entity.brain`에 행동 결정 위임 (두뇌 교체 가능)
- `brain.decide()`: 9개 행동(CONSUME/REPRODUCE/GATHER/TRADE/CRAFT/COMBAT/EXPLORE/IDLE)에 점수 매겨 최고 선택
- `execute_action()`: 선택된 행동을 실제로 수행, 이벤트 리스트 반환
- **듀얼 브레인 시스템**: `RuleBasedBrain`(기존 점수 기반) / `SmartBrain`(경험 학습+계획+목표+메시징)
- 개체는 나이(에이징), 배고픔(기아), 전투로 사망 가능

### 4.2 유전자 (Genome) — genome.py
- 10개 수치형 형질(0.0~1.0): risk_tolerance, curiosity, sociability, aggression, industry, innovation_rate, strength, endurance, speed, fertility
- 1개 범주형 형질: specialization (general/farmer/miner/merchant/warrior/crafter/explorer)
- Uniform Crossover + Mutation (rate=0.1, magnitude=0.2)
- 세대(generation) 카운터로 진도 추적

### 4.3 시장 (Market) — market.py
- 지정가 주문장(Order Book): 매수는 가격 내림차순, 매도는 가격 오름차순
- 주문 체결 조건: 매수가 >= 매도가
- 거래 수수료 2%, 주문 20틱 후 자동 만료
- 가격 지수: 최근 100틱의 체결가 이동평균

### 4.4 전투 (Combat) — entity.py
- 같은 타일 이웃 개체와 전투, 기본 데미지 15 (±25% 무작위)
- 무기/갑옷 장비로 공/방 보정, 본거지 영토 내 30% 전투 보정
- 승자가 패자 인벤토리의 60% 약탈
- 발동 조건: 식량 부족(약탈), 영토 내 이방인(영토방어), 일반 공격(aggression > 0.2)

### 4.5 영토 (Territory) — world.py + entity.py
- 개체가 특정 타일에 15틱 이상 머물면 본거지 설정
- 본거지 반경 3(맨해튼 거리) 이내가 영토
- 영토 내 전투 보정 +30%, 타일 클레임 시각화(. 마커)
- 개체 사망 시 클레임 자동 정리

### 4.6 기술 (Knowledge) — knowledge.py
- 9개 기술: basic_agriculture → irrigation/currency → bureaucracy, mining → metallurgy → alchemy, architecture, sailing
- 글로벌 연구 포인트: 전체 개체 혁신성 × 지식 수에 비례해 축적
- 문화적 진화: 인접 개체 간 sociability 비례 지식 전수

### 4.7 통계 (Metrics) — metrics.py
- 10틱마다 Snapshot 저장: 인구, 출생/사망, 전투사망, 평균 에너지/부, 지니계수, 분업지수, 가격, 기술 현황
- 지니계수: 경제 불평등 측정
- 분업지수: 허핀달-허쉬만 지수 기반 직업 다양성

---

## 5. 작업 규칙

### 5.1 코드 수정 원칙
- 기존 스타일(주석 형식, 타입 힌트, import 순서, 네이밍 컨벤션)을 반드시 준수합니다.
- config.py에 새 파라미터를 추가할 때는 기존 형식(섹션 헤더 주석 + 상수 정의)을 따릅니다.
- 모든 새 함수/메서드에는 타입 힌트와 간단한 독스트링(한국어)을 추가합니다.
- `typing` 모듈의 `TYPE_CHECKING`을 활용한 순환 참조 방지 패턴을 유지합니다.
- `from . import config` 패턴으로 전역 설정을 참조합니다.

### 5.2 벡엔드/테스트 원칙
- 로직 변경 후에는 반드시 `python -m sim.main --no-visual --ticks 200 --seed <seed>`로 최소 200틱 실행 검증합니다.
- 기본 시드(42)와 추가 시드(7, 99) 두 개 이상에서 테스트합니다.
- 시뮬레이션이 200틱 이내에 멸종하거나 모든 개체가 비정상 행동을 보이면 변경을 재검토합니다.
- 성능 회귀가 발생하면 원인을 파악하고 최적화합니다.

### 5.3 커밋 규칙
- 커밋 메시지는 한국어로 작성합니다.
- 형식: `[모듈명] 변경 내용 요약`
- 예: `[entity] 전투 데미지 밸런스 조정 및 약탈 트리거 조건 완화`
- 커밋 전에 `git diff --staged`로 변경 사항을 최소 두 번 검토합니다.
- 설정 파일(config.py)과 로직 파일(entity.py, engine.py) 변경은 분리해서 커밋합니다.

### 5.4 파일 규모 제한
- 단일 파일은 700줄을 넘기지 않습니다.
- 현재 최대: `config.py` 311줄, `faction.py` 251줄, `smart_brain.py` 244줄 — 모두 안전 범위.
- 새 기능 추가 시 신규 모듈로 분리하는 것을 우선 고려합니다.
- engine.py는 300줄 미만 유지, 메인 루프 로직은 engine.py에 두고 세부 로직은 개별 모듈로 위임합니다.

---

## 6. 아키텍처 제약

### 6.1 불변 원칙
- **LLM/외부 AI 절대 사용 금지**: 모든 의사결정은 순수 로컬 알고리즘으로 처리. SmartBrain도 로컬 연산만 사용.
- 표준 라이브러리 + Rich만 사용 (외부 패키지 최소화)
- Emergent behavior는 설계된 것이 아니라 관찰되는 것 — 의도적으로 특정 패턴을 강제하지 않음

### 6.2 확장 방향 (Phase 1+)
- **Phase 1** ✅ 완료: 밸런싱, 전투 활성화, 영토 시스템
- **Phase 2** ✅ 완료: 전투 심화, 파벌 시스템, 장비/지식 약탈
- **Phase 3** ✅ 완료: SmartBrain — 경험 기반 학습, 멀티스텝 계획, 목표 설정, 개체 간 메시징 (LLM 없음, 순수 로컬 알고리즘)
- **Phase 3.1** ✅ 완료: 이데올로기, 계절, 건물, 랜덤 이벤트 시스템
- **Phase 4** ✅ 완료: Rich 기반 사이버펑크 TUI 시각화
- **Phase 4.5** ✅ 완료: 데이터 내보내기(CSV/JSON), 외부 분석 도구 연동

> **⚠️ LLM 사용 금지**: 이 프로젝트는 앞으로도 **영원히 LLM/외부 AI를 연결하지 않습니다**.
> 모든 의사결정은 순수 로컬 알고리즘(RuleBasedBrain / SmartBrain)으로 처리합니다.

### 6.3 시각화 규칙
- Rich 라이브러리로 터미널 내에서 동작 (별도 GUI 창 없음)
- `Live` 컨텍스트 매니저로 실시간 갱신
- `--no-visual` 플래그로 헤드리스 모드 지원
- 시각화 로직은 visualizer.py에 격리, 코어 시뮬레이션 로직과 분리

---

## 7. CLI 사용법

```bash
# 기본 실행 (500틱, 실시간 TUI)
python -m sim.main

# 헤드리스 모드 (속도 최대)
python -m sim.main --no-visual --ticks 1000

# 특정 시드 + 느린 속도
python -m sim.main --seed 777 --speed 0.3

# 자주 쓰는 디버깅 명령
python -m sim.main --no-visual --ticks 200 --seed 42
```

---

## 8. 질문 가이드라인

- 결정이 필요한 질문은 사용자에게 2~3개의 선택지를 제공하고, 각각의 예상 결과를 함께 설명합니다.
- 모호한 요청이 들어오면 현재 Phase와 제약 조건을 먼저 확인하고 실행 가능한 범위를 제안합니다.
- 버그가 의심될 때는 가설을 세우고 entity.py → engine.py → config.py 순으로 추적합니다.
- "계속 진행" 같은 모호한 명령이 들어오면 마지막 작업 상태를 요약하고 다음 단계 선택지를 제시합니다.

---

## 9. 테스트 현황

- **총 테스트 수**: 292개 (전체 통과)
- **테스트 파일**: 34개 (`tests/test_*.py`)
- **커버리지**: 미측정 (pytest-cov 설정 완료, 미실행)
- **기존 커버**: entity, genome, market, world, knowledge, season, events, buildings, ideology, faction, diplomacy, brain, performance, interactive_map
- **신규 커버 (Phase 5)**: config, resource, metrics, research, faction_system, diplomacy, entity_action, entity_combat, entity_craft, entity_reproduce, messaging, exporter, experiment
- **미커버 모듈**: brain_base, brain_goals, brain_planning, brain_messaging, smart_brain, rule_brain
