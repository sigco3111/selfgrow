# selfgrow-improvement - Work Plan

## TL;DR (For humans)
자가발전 문명 시뮬레이션의 전반적인 고도화를 수행합니다. 핵심 변경 사항:

1. **성능 최적화**: 매 틱마다 모든 개체를 순회하는 O(n²) 공간 검색을 QuadTree 기반 O(n log n)으로 개선하여 10배 이상의 성능 향상을 달성합니다.

2. **새로운 게임 메커니즘**: 파벌 간 무역 네트워크와 문화적 진화(언어, 관습)를 추가하여 더 풍부한 창발 행동을 유도합니다.

3. **시각화 강화**: 지도 위 개체 추적, 계절별 색상 변화, 파벌 관계 그래프 등 대화형 TUI 기능을 추가합니다.

4. **테스트 커버리지**: 핵심 모듈의 테스트 커버리지를 80% 이상으로 확보하고 성능 벤치마크를 추가합니다.

**이 접근법을 선택한 이유**: 현재 시뮬레이션은 매 틱마다 모든 개체 쌍을 비교하는 O(n²) 작업이 가장 큰 병목입니다. 이를 해결하면 더 큰 월드나 더 많은 개체를 처리할 수 있습니다. 또한 기존 이데올로기/파벌 시스템과 자연스럽게 통합되는 무역 네트워크를 추가합니다.

**이 작업에는 포함되지 않습니다**: LLM/외부 AI 연결, GUI 창 추가, 기존 메커니즘 제거

**예상 작업량**: Large (약 2-3일)
**위험도**: Medium — 성능 최적화 시 기존 로직과의 호환성 확인 필요

**채택한 기본값**: QuadTree 공간 인덱싱, 무역 네트워크는 파벌 시스템 기반, 시각화는 Rich 라이브러리 유지

다음 단계: 승인 후 실행 시작

---

> TL;DR (machine): Large effort, Medium risk — 성능 최적화 + 새 메커니즘 + 시각화 강화 + 테스트 확보

## Scope
### Must have
- QuadTree 기반 공간 인덱싱으로 이웃 개체 검색 최적화
- 파벌 간 무역 네트워크 시스템
- 문화적 진화 고도화 (언어, 관습 전파)
- 대화형 지도 시각화 (개체 추적, 계절 효과)
- 테스트 커버리지 80% 이상
- 성능 벤치마크 테스트

### Must NOT have (guardrails, anti-slop, scope boundaries)
- LLM/외부 AI 연결 (프로젝트 원칙 위반)
- GUI 창 추가 (터미널 TUI 유지)
- 기존 메커니즘 제거
- config.py 외부 파일 분리
- 서브에이전트 사용 (AGENTS.md 규칙 준수)

## Verification strategy
> Zero human intervention - all verification is agent-executed.
- Test decision: TDD + tests-after
- Evidence: .omo/evidence/task-<N>-selfgrow-improvement.<ext>

## Execution strategy
### Parallel execution waves
> Target 5-8 todos per wave. Fewer than 3 (except the final) means you under-split.

### Dependency matrix
| Todo | Depends on | Blocks | Can parallelize with |
| --- | --- | --- | --- |
| 1. QuadTree 구현 | None | 2, 3 | 4, 5 |
| 2. 공간 인덱싱 통합 | 1 | 6 | 4, 5 |
| 3. 성능 벤치마크 | 1 | F1 | 4, 5 |
| 4. 무역 네트워크 | None | 6 | 1, 2, 3, 5 |
| 5. 문화적 진화 고도화 | None | 6 | 1, 2, 3, 4 |
| 6. 시각화 강화 | 2, 4, 5 | F1 | None |
| 7. 테스트 커버리지 | 1, 2, 4, 5 | F1 | None |
| F1. 최종 검증 | All | Complete | None |

## Todos
> Implementation + Test = ONE todo. Never separate.
<!-- APPEND TASK BATCHES BELOW THIS LINE WITH edit/apply_patch - never rewrite the headers above. -->

### Wave 1: 성능 최적화 기반
- [ ] 1. QuadTree 구현
  What to do / Must NOT do: sim/spatial.py에 QuadTree 클래스 구현. 40×30 월드에 최적화된 그리드 기반 인덱싱. 범위 질의(range_query)와 이웃 검색(nearby_entities) 메서드 필수. 기존 world.py의 모든 위치 참조를 대체하지 않음 (점진적 통합).
  Parallelization: Wave 1 | Blocked by: None | Blocks: 2, 3
  References (executor has NO interview context - be exhaustive): sim/world.py:60-80 (현재 공간 질의 없음), sim/engine.py:142 (O(n²) 루프)
  Acceptance criteria (agent-executable): python -c "from sim.spatial import QuadTree; qt = QuadTree(40, 30); print('QuadTree created')" 성공
  QA scenarios (name the exact tool + invocation): happy — 100개 점 삽입 후 범위 질의 테스트, failure — 빈 QuadTree에서 질의 시 빈 리스트 반환
  Evidence .omo/evidence/task-1-selfgrow-improvement.txt
  Commit: Y | feat(spatial): QuadTree 공간 인덱싱 구현

- [ ] 2. 공간 인덱싱 엔진 통합
  What to do / Must NOT do: engine.py의 _step() 메서드에서 QuadTree를 사용하여 이웃 개체 검색 최적화. world.py에 update_entity_position() 메서드 추가. 기존 로직과 호환성 유지.
  Parallelization: Wave 2 | Blocked by: 1 | Blocks: 6
  References (executor has NO interview context - be exhaustive): sim/engine.py:142-160, sim/world.py
  Acceptance criteria (agent-executable): python -m sim.main --no-visual --ticks 100 --seed 42 정상 실행
  QA scenarios (name the exact tool + invocation): happy — 100틱 실행 후 인구 유지, failure — 오류 없이 종료
  Evidence .omo/evidence/task-2-selfgrow-improvement.txt
  Commit: Y | perf(engine): QuadTree 기반 이웃 검색 최적화

- [ ] 3. 성능 벤치마크 테스트
  What to do / Must NOT do: tests/test_performance.py에 벤치마크 테스트 추가. 100/500/1000 엔티트로 성능 측정. 기존 테스트와 분리 유지.
  Parallelization: Wave 1 | Blocked by: 1 | Blocks: F1
  References (executor has NO interview context - be exhaustive): sim/engine.py:95-120 (run 메서드)
  Acceptance criteria (agent-executable): python -m pytest tests/test_performance.py -v 성공
  QA scenarios (name the exact tool + invocation): happy — 1000 엔티트 100틱 10초 이내, failure — 타임아웃 없이 완료
  Evidence .omo/evidence/task-3-selfgrow-improvement.txt
  Commit: Y | test(perf): 성능 벤치마크 테스트 추가

### Wave 2: 새로운 게임 메커니즘
- [ ] 4. 파벌 간 무역 네트워크
  What to do / Must NOT do: sim/trade_network.py에 무역 네트워크 시스템 구현. 파벌 간 무역 협정, 장거리 무역 경로, 무역 이점 보너스. 기존 market.py와 통합.
  Parallelization: Wave 1 | Blocked by: None | Blocks: 6
  References (executor has NO interview context - be exhaustive): sim/market.py, sim/faction.py, sim/diplomacy.py
  Acceptance criteria (agent-executable): python -c "from sim.trade_network import TradeNetwork; print('TradeNetwork created')" 성공
  QA scenarios (name the exact tool + invocation): happy — 파벌 간 무역 발생 확인, failure — 무역 없이도 정상 동작
  Evidence .omo/evidence/task-4-selfgrow-improvement.txt
  Commit: Y | feat(trade): 파벌 간 무역 네트워크 시스템 구현

- [ ] 5. 문화적 진화 고도화
  What to do / Must NOT do: sim/cultural.py 확장. 언어 공유, 관습 형성, 문화적 갈등 메커니즘 추가. 기존 지식 전수와 통합.
  Parallelization: Wave 1 | Blocked by: None | Blocks: 6
  References (executor has NO interview context - be exhaustive): sim/cultural.py, sim/ideology.py
  Acceptance criteria (agent-executable): python -c "from sim.cultural import CulturalEvolution; print('CulturalEvolution created')" 성공
  QA scenarios (name the exact tool + invocation): happy — 문화적 전파 이벤트 발생, failure — 기존 문화 전수와 충돌 없음
  Evidence .omo/evidence/task-5-selfgrow-improvement.txt
  Commit: Y | feat(culture): 문화적 진화 고도화 (언어, 관습)

### Wave 3: 시각화 및 테스트
- [ ] 6. 대화형 지도 시각화
  What to do / Must NOT do: sim/ui/interactive_map.py에 대화형 지도 구현. 개체 추적, 계절별 색상, 파벌 관계 시각화. 기존 visualizer.py와 통합.
  Parallelization: Wave 3 | Blocked by: 2, 4, 5 | Blocks: F1
  References (executor has NO interview context - be exhaustive): sim/visualizer.py, sim/ui/
  Acceptance criteria (agent-executable): python -c "from sim.ui.interactive_map import InteractiveMap; print('InteractiveMap created')" 성공
  QA scenarios (name the exact tool + invocation): happy — 지도 렌더링 성공, failure — Rich 레이아웃 오류 없음
  Evidence .omo/evidence/task-6-selfgrow-improvement.txt
  Commit: Y | feat(ui): 대화형 지도 시각화 구현

- [ ] 7. 테스트 커버리지 확보
  What to do / Must NOT do: 기존 모듈 테스트 보완. test_trade_network.py, test_cultural_evolution.py, test_spatial.py 추가. 커버리지 80% 이상 목표.
  Parallelization: Wave 3 | Blocked by: 1, 2, 4, 5 | Blocks: F1
  References (executor has NO interview context - be exhaustive): tests/
  Acceptance criteria (agent-executable): python -m pytest tests/ -v --tb=short 모든 테스트 통과
  QA scenarios (name the exact tool + invocation): happy — 100% 테스트 통과, failure — 기존 테스트 회귀 없음
  Evidence .omo/evidence/task-7-selfgrow-improvement.txt
  Commit: Y | test: 테스트 커버리지 확보 (80% 이상)

## Final verification wave
> Runs in parallel after ALL todos. ALL must APPROVE. Surface results and wait for the user's explicit okay before declaring complete.
- [ ] F1. Plan compliance audit
  - 모든 파일이 지정된 경로에 있는지 확인
  - commit 메시지가 규칙을 따르는지 확인
  - LLM/외부 AI가 사용되지 않았는지 확인

- [ ] F2. Code quality review
  - 타입 힌트 누락 없는지 확인
  - 독스트링 누락 없는지 확인
  - 기존 코드 스타일과 일치하는지 확인
  - 파일 크기 제한 준수 (700줄 이내)

- [ ] F3. Real manual QA
  - python -m sim.main --no-visual --ticks 200 --seed 42 정상 실행
  - python -m sim.main --no-visual --ticks 200 --seed 7 정상 실행
  - python -m sim.main --no-visual --ticks 200 --seed 99 정상 실행

- [ ] F4. Scope fidelity
  - LLM/외부 AI가 연결되지 않았는지 확인
  - GUI 창이 추가되지 않았는지 확인
  - 기존 메커니즘이 제거되지 않았는지 확인

## Commit strategy
- 각 Task별 1개 커밋
- 커밋 메시지: `[모듈명] 변경 내용 요약`
- 설정 파일(config.py)과 로직 파일 분리 커밋

## Success criteria
- QuadTree 기반 공간 인덱싱으로 매 틱 실행 시간 50% 이상 단축
- 파벌 간 무역 네트워크 정상 동작
- 문화적 진화 메커니즘이 기존 시스템과 통합
- 대화형 지도 시각화 정상 동작
- 테스트 커버리지 80% 이상
- 모든 기존 테스트 통과
- 200틱 실행 시 인구 멸종 없음
