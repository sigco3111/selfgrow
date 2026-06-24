---
slug: selfgrow-improvement
status: awaiting-approval
intent: unclear
pending-action: write .omo/plans/selfgrow-improvement.md
approach: 종합 고도화 — 성능 최적화, 새로운 메커니즘, 시각화 강화, 테스트 커버리지 확보
---

# Draft: selfgrow-improvement

## Components (topology ledger)
| id | outcome | status | evidence path |
|----|---------|--------|---------------|
| perf | O(n²) → O(n log n) 공간 인덱싱으로 10배 성능 향상 | active | engine.py:142, world.py |
| mechanics | 무역 네트워크, 공급망, 문화적 진화 고도화 | active | market.py, cultural.py |
| visual | 대화형 지도, 계절 시각화, 파벌 관계 그래프 | active | visualizer.py, ui/ |
| testing | 테스트 커버리지 80% 이상, 성능 벤치마크 | active | tests/ |
| analysis | 시뮬레이션 결과 분석 도구, 비교 시각화 | active | exporter.py, experiment.py |

## Open assumptions (announced defaults)
| assumption | adopted default | rationale | reversible? |
|------------|-----------------|-----------|-------------|
| 성능 우선순위 | 공간 인덱싱이 가장 큰 병목 | O(n²) 쿼리가 매 틱마다 반복됨 | Yes |
| 새 메커니즘 범위 | 무역 네트워크 + 문화적 진화 | 기존 시스템과 자연스럽게 통합 | Yes |
| 시각화 수준 | 대화형 지도 + 실시간 차트 | 현재 TUI는 읽기 어렵고 정보 밀도 낮음 | Yes |
| 테스트 전략 | TDD + 성능 벤치마크 | 안정성과 성능 동시 확보 | Yes |

## Findings (cited - path:lines)
- engine.py:142 — 매 틱마다 `entities` 리스트를 순회하며 이웃 개체를 찾음 (O(n²))
- world.py — 공간 질의 메서드가 없음, 모든 엔티티를 순회해야 함
- market.py — 단순 주문장, 복잡한 무역 네트워크 없음
- cultural.py — 지식 전수만 있음, 문화적 진화 메커니즘 부족
- visualizer.py — 기본 TUI, 대화형 기능 없음
- tests/ — 13개 테스트 파일, 커버리지 불명

## Decisions (with rationale)
1. **공간 인덱싱 도입**: QuadTree 또는 Grid 기반 인덱싱으로 이웃 개체 검색 O(n) → O(log n)
2. **무역 네트워크**: 파벌 간 무역 협정, 장거리 무역 경로
3. **문화적 진화 강화**: 이데올로기, 언어, 관습의 복합적 전파
4. **시각화 고도화**: 지도 위 개체 추적, 계절별 색상 변화, 파벌 관계 시각화
5. **성능 벤치마크**: 매 변경마다 성능 회귀 검사

## Scope IN
- 성능 최적화 (공간 인덱싱, 루프 최적화)
- 새로운 게임 메커니즘 (무역 네트워크, 문화적 진화)
- 시각화 강화 (대화형 지도, 차트)
- 테스트 커버리지 확보
- 분석 도구 개선

## Scope OUT (Must NOT have)
- LLM/외부 AI 연결 (프로젝트 원칙 위반)
- GUI 창 추가 (터미널 TUI 유지)
- 기존 메커니즘 제거
- 설정 파일 분리 (현재 config.py 유지)

## Open questions
- 없음 (UNCLEAR intent이므로 best-practice defaults 채택)

## Approval gate
status: awaiting-approval
