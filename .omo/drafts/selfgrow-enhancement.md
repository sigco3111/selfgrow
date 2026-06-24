---
slug: selfgrow-enhancement
status: awaiting-approval
intent: unclear
pending-action: write .omo/plans/selfgrow-enhancement.md
approach: 
현재 Phase 0-4.5까지 완료된 자가발전 문명 시뮬레이션을 고도화하기 위한 포괄적 계획.
SmartBrain 버그 수정, 테스트 보강, 문서 동기화, 기술 부채 해소, 새 기능 추가, CI/CD 구축을 포함.
---

# Draft: selfgrow-enhancement

## Components (topology ledger)
| ID | Component | Outcome | Status | Evidence |
|----|-----------|---------|--------|----------|
| C1 | SmartBrain P0 버그 수정 | SMART_LEARNING_RATE 적용, _handle_warning 구현, alliance faction_id 조건 완화 | active | brain_messaging.py:129-134, config.py:304, brain_messaging.py:88-100 |
| C2 | SmartBrain 기능 강화 | 3+ 스텝 계획, 경험 시간 감쇠, 거래 호가 협상, 계획 실패 학습 | active | brain_planning.py:15-60, smart_brain.py:201-237 |
| C3 | 테스트 커버리지 확대 | test_ideology.py, test_season.py, test_faction_diplomacy.py 신규, 기존 테스트 강화 | active | tests/ 디렉토리 확인 |
| C4 | 문서 동기화 | AGENTS.md Phase 상태 갱신, README.md 새 시스템 문서화, requirements.txt 정리 | active | AGENTS.md, README.md, requirements.txt |
| C5 | 기술 부채 해소 | event_log.py 분할, faction.py 외교 분리, config.py 섹션 분할 | active | sim/ui/event_log.py:389줄, faction.py:326줄, config.py:319줄 |
| C6 | CI/CD 파이프라인 | GitHub Actions로 pytest 자동화 | deferred | .github/workflows/ 미존재 |
| C7 | 외교 시스템 고도화 | 6종 관계(neutral/alliance/non_aggression/trade_pact/war/vassal) 완전 구현 | deferred | faction.py:326줄, enhancement-plan.md:2.1 |
| C8 | 공간 인덱싱 최적화 | O(N²) → O(N log N)으로 world.py 쿼리 개선 | deferred | world.py:208줄 |

## Open assumptions (announced defaults)
| Assumption | Adopted Default | Rationale | Reversible? |
|------------|-----------------|-----------|-------------|
| SmartBrain P0 버그가 현재 시뮬레이션 성능에 영향 | 즉시 수정 | _handle_warning no-op으로 위험 알림 무용, SMART_LEARNING_RATE 미사용으로 학습 비효율 | 예 |
| 테스트는 pytest 사용 | pytest | 기존 tests/ 디렉토리에서 pytest 사용 중 | 예 |
| 문서는 한국어로 작성 | 한국어 | 프로젝트 컨벤션 (AGENTS.md §1.3) | 예 |
| CI/CD는 GitHub Actions 사용 | GitHub Actions | 무료 공개 저장소에 적합 | 예 |
| 공간 인덱싱은 나중에 구현 | deferred | 현재 40x30 격자에서 O(N²) 허용 가능, 확장 시 구현 | 예 |

## Findings (cited - path:lines)
- SmartBrain P0 버그: SMART_LEARNING_RATE 미사용 (config.py:304), _handle_warning no-op (brain_messaging.py:129-134), alliance faction_id 의존 (brain_messaging.py:88-100)
- 테스트 커버리지: test_brain.py 65줄 (6개 테스트), test_engine.py 40줄 (2개 테스트), 이데올로기/계절/외교 테스트 0개
- 기술 부채: event_log.py 389줄 (최대), faction.py 326줄, config.py 319줄
- 문서 불일치: AGENTS.md Phase 3 "진행 중" 명시 (실제 Phase 4 완료), README.md에 새 시스템 문서 없음
- 기존 계획: .omo/plans/enhancement-plan.md (557줄)에 P0-P3 계획 존재

## Decisions (with rationale)
- SmartBrain P0 버그를 최우선으로 수정 (시뮬레이션 정확성 영향)
- 테스트는 기존 패턴 따라 pytest로 확장 (일관성 유지)
- 문서는 한국어로 동기화 (프로젝트 컨벤션)
- CI/CD는 나중에 구현 (현재 로컬 개발 충분)
- 공간 인덱싱은 확장 시 구현 (현재 성능 문제 없음)

## Scope IN
- SmartBrain P0 버그 수정 (SMART_LEARNING_RATE 적용, _handle_warning 구현, alliance faction_id 조건 완화)
- SmartBrain 기능 강화 (3+ 스텝 계획, 경험 시간 감쇠, 거래 호가 협상, 계획 실패 학습)
- 테스트 커버리지 확대 (test_ideology.py, test_season.py, test_faction_diplomacy.py 신규)
- 문서 동기화 (AGENTS.md, README.md, requirements.txt)
- 기술 부채 해소 (event_log.py 분할, faction.py 외교 분리)

## Scope OUT (Must NOT have)
- LLM/외부 AI 통합 (프로젝트 헌법상 영원히 금지)
- GUI/웹 시각화 (현재 Rich TUI 유지)
- 멀티 시나리오 분석 (장기 계획으로 미룸)
- 순수 신경망 브레인 (장기 계획으로 미룸)

## Open questions
- 외교 시스템이 faction.py에 완전히 구현되었는지 검증 필요
- 공간 인덱싱이 실제로 구현되었는지 world.py 검증 필요
- CI/CD 우선순위: GitHub Actions 설정 vs 로컬 개발 환경 개선 중 선택

## Approval gate
status: awaiting-approval
<!-- When exploration is exhausted and unknowns are answered, set status: awaiting-approval. -->
<!-- That durable record is the loop guard: on a later turn read it and resume at the gate instead of re-running exploration. -->
