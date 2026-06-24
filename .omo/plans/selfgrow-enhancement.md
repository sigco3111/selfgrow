# selfgrow-enhancement - Work Plan

## TL;DR (For humans)
<!-- Fill this LAST, after the detailed plan below is written, so it summarizes the REAL plan. -->
<!-- Plain English for a non-engineer: NO file paths, NO todo numbers, NO wave/agent/tool names. -->

**What you'll get:** 
자가발전 문명 시뮬레이션의 SmartBrain 시스템을 고도화하고, 테스트 커버리지를 확대하며, 문서를 동기화하고, 기술 부채를 해소하는 포괄적 개선 계획. 15개의 구체적 작업과 최종 검증 4항목으로 구성.

**Why this approach:** 
현재 Phase 0-4.5까지 완료된 프로젝트의 SmartBrain에 P0 버그 3건이 발견되고, 테스트 커버리지가 부족하며, 문서가 실제 코드와 불일치함. 체계적 고도화를 통해 시뮬레이션 정확성과 유지보수성을 향상.

**What it will NOT do:** 
- LLM/외부 AI 통합 (프로젝트 헌법상 영원히 금지)
- GUI/웹 시각화 (현재 Rich TUI 유지)
- 멀티 시나리오 분석 (장기 계획으로 미룸)
- 순수 신경망 브레인 (장기 계획으로 미룸)

**Effort:** Medium (2-3주)
**Risk:** Medium - SmartBrain 변경이 시뮬레이션 밸런스에 영향 가능하나, 단계적 수정과 테스트로 리스크 최소화
**Decisions I made for you:** 
- SmartBrain P0 버그를 최우선으로 수정 (시뮬레이션 정확성 영향)
- 테스트는 기존 패턴 따라 pytest로 확장 (일관성 유지)
- 문서는 한국어로 동기화 (프로젝트 컨벤션)
- CI/CD는 나중에 구현 (현재 로컬 개발 충분)
- 공간 인덱싱은 확장 시 구현 (현재 성능 문제 없음)

Your next move: 계획 승인 또는 고정밀 리뷰 요청. 상세 실행 내용은 아래에 기술.

---

> TL;DR (machine): <1 line - effort, risk, deliverables>

## Scope
### Must have
1. SmartBrain P0 버그 수정 (SMART_LEARNING_RATE 적용, _handle_warning 구현, alliance faction_id 조건 완화)
2. SmartBrain 기능 강화 (3+ 스텝 계획, 경험 시간 감쇠, 거래 호가 협상, 계획 실패 학습)
3. 테스트 커버리지 확대 (test_ideology.py, test_season.py, test_faction_diplomacy.py 신규)
4. 문서 동기화 (AGENTS.md, README.md, requirements.txt)
5. 기술 부채 해소 (event_log.py 분할, faction.py 외교 로직 분리)

### Must NOT have (guardrails, anti-slop, scope boundaries)
1. LLM/외부 AI 통합 (프로젝트 헌법상 영원히 금지)
2. GUI/웹 시각화 (현재 Rich TUI 유지)
3. 멀티 시나리오 분석 (장기 계획으로 미룸)
4. 순수 신경망 브레인 (장기 계획으로 미룸)
5. 기존 기능 변경 (파벌 시스템, 시장 시스템, 유전 알고리즘 등)
6. 새 의존성 추가 (Rich만 사용 유지)
7. 단일 파일 700줄 초과

## Verification strategy
> Zero human intervention - all verification is agent-executed.
- Test decision: tests-after + pytest (기존 테스트 패턴 유지)
- Evidence: .omo/evidence/task-<N>-selfgrow-enhancement.txt
- 검증 도구: pytest, grep, python -c, wc -l, git diff
- 검증 시나리오: 각 todo의 happy + failure QA 시나리오 참조
- 최종 검증: 4개 검증 항목 병렬 실행 (계획 준수, 코드 품질, 수동 QA, 범위 충실도)

## Execution strategy
### Parallel execution waves
> Target 5-8 todos per wave. Fewer than 3 (except the final) means you under-split.

**Wave 1**: SmartBrain P0 버그 수정 + 기능 강화 (6개 todo, 병렬 실행)
- Task 1: SMART_LEARNING_RATE 적용
- Task 2: _handle_warning 구현
- Task 3: Alliance/Treaty faction_id 조건 완화
- Task 4: 3+ 스텝 계획 시스템 (Task 1에만 약한 의존)
- Task 5: 경험 시간 감쇠 (Task 1에만 약한 의존)
- Task 6: 거래 호가 협상 (독립 실행)
- Task 13: requirements.txt LLM 주석 제거 (독립 실행)

**Wave 2**: SmartBrain 기능 강화 (1개 todo, Wave 1 완료 후)
- Task 7: 계획 실패 학습 (Task 1에 의존)

**Wave 3**: 테스트 커버리지 확대 (3개 todo, 병렬 실행, Wave 2 완료 후)
- Task 8: test_ideology.py 신규
- Task 9: test_season.py 강화
- Task 10: test_faction_diplomacy.py 신규

**Wave 4**: 문서 동기화 + 기술 부채 해소 (4개 todo, 병렬 실행, Wave 3 완료 후)
- Task 11: AGENTS.md Phase 상태 갱신
- Task 12: README.md 새 시스템 문서화
- Task 14: event_log.py 분할
- Task 15: faction.py 외교 로직 분리

**Wave 5**: 최종 검증 (4개 todo, 병렬 실행, Wave 4 완료 후)
- F1: 계획 준수 감사
- F2: 코드 품질 리뷰
- F3: 헤드리스 통합 테스트
- F4: 범위 충실도

### Dependency matrix
| Todo | Depends on | Blocks | Can parallelize with |
| --- | --- | --- | --- |
| 1 (SMART_LEARNING_RATE) | 없음 | 4, 5, 6, 7 | 2, 3, 6, 13 |
| 2 (_handle_warning) | 없음 | 4, 5, 6, 7 | 1, 3, 6, 13 |
| 3 (faction_id 조건) | 없음 | 4, 5, 6, 7 | 1, 2, 6, 13 |
| 4 (3+ 스텝 계획) | 1 | 5, 6, 7, 8-10 | 2, 3, 6, 13 |
| 5 (경험 시간 감쇠) | 1 | 6, 7, 8-10 | 2, 3, 4, 13 |
| 6 (거래 호가 협상) | 없음 | 7, 8-10 | 1, 2, 3, 4, 5, 13 |
| 7 (계획 실패 학습) | 1 | 8-10 | 2, 3, 4, 5, 6, 13 |
| 8 (test_ideology) | 1-3 (코어 버그 수정) | F1 | 9, 10, 11-15 |
| 9 (test_season) | 1-3 (코어 버그 수정) | F1 | 8, 10, 11-15 |
| 10 (test_faction_diplomacy) | 1-3 (코어 버그 수정) | F1 | 8, 9, 11-15 |
| 11 (AGENTS.md) | 1-7 (기능 완료) | F1 | 12, 13, 14, 15 |
| 12 (README.md) | 1-7 (기능 완료) | F1 | 11, 13, 14, 15 |
| 13 (requirements.txt) | 없음 | F1 | 1, 2, 3, 4, 5, 6, 7, 11, 12, 14, 15 |
| 14 (event_log.py) | 1-7 (기능 완료) | F1 | 11, 12, 13, 15 |
| 15 (faction.py) | 1-7 (기능 완료) | F1 | 11, 12, 13, 14 |
| F1 (계획 준수) | 1-15 | 없음 | F2, F3, F4 |
| F2 (코드 품질) | 1-15 | 없음 | F1, F3, F4 |
| F3 (헤드리스 QA) | 1-15 | 없음 | F1, F2, F4 |
| F4 (범위 충실도) | 1-15 | 없음 | F1, F2, F3 |

## Todos
> Implementation + Test = ONE todo. Never separate.
<!-- APPEND TASK BATCHES BELOW THIS LINE WITH edit/apply_patch - never rewrite the headers above. -->

### Wave 1: SmartBrain P0 버그 수정 (C1)
- [ ] 1. SMART_LEARNING_RATE 적용 및 테스트
  What to do / Must NOT do: 
  - `smart_brain.py:88,90`에서 고정 배수(2.0, 0.5)를 `config.SMART_LEARNING_RATE`로 교체
  - **정확한 적용 공식**: 
    - Line 88: `scores[state] *= (1.0 + sim * exp.outcome_score * config.SMART_LEARNING_RATE * 2.0)`
    - Line 90: `scores[state] *= (1.0 - sim * abs(exp.outcome_score) * config.SMART_LEARNING_RATE * 0.5)`
    - **의도적 비대칭 유지**: 양성 피드백은 2배, 음성 피드백은 0.5배 스케일링
    - SMART_LEARNING_RATE는 전체 스케일 팩터 역할 (기본값 0.1)
    - 현재 동작과 동일한 결과: 2.0 = 0.1 * 20, 0.5 = 0.1 * 5 (하지만/config로 제어 가능)
  - **대안적 구현 (선택 가능)**: config.py에 두 파라미터 추가
    - `SMART_LEARNING_RATE_POS = 2.0` (양성 피드백 배율)
    - `SMART_LEARNING_RATE_NEG = 0.5` (음성 피드백 배율)
    - smart_brain.py에서 `config.SMART_LEARNING_RATE_POS`와 `config.SMART_LEARNING_RATE_NEG` 사용
  - `brain_planning.py:31`의 `scores.get(state_b, 0) * config.SMART_PLANNING_DISCOUNT` 로직 검증
  - `test_brain.py`에 learning rate 적용 테스트 추가
  Must NOT: 다른 로직 변경, 비대칭 비율 변경 (현재 4:1 비율 유지)
  Parallelization: Wave 1 | Blocked by: 없음 | Blocks: 4, 5, 6, 7
  References (executor has NO interview context - be exhaustive): 
    - smart_brain.py:88-90 (경험 보정 로직)
    - config.py:304 (SMART_LEARNING_RATE 정의)
    - brain_planning.py:31 (계획 할인율)
    - test_brain.py:81-86 (기존 피드백 테스트)
  Acceptance criteria (agent-executable): 
    - `python -c "from sim.smart_brain import SmartBrain; print('import ok')"` 성공
    - `pytest tests/test_brain.py -v` 통과
    - `grep -n "SMART_LEARNING_RATE" sim/smart_brain.py` 결과 2건 이상 (88, 90줄)
    - `grep -n "SMART_PLANNING_DISCOUNT" sim/brain_planning.py` 결과 1건 이상
    - 기존 4:1 비대칭 비율 유지 확인 (양성 2.0, 음성 0.5 스케일)
  QA scenarios (name the exact tool + invocation): 
    - happy: `python -m sim.main --no-visual --ticks 100 --seed 42` 실행 후 SmartBrain 개체가 학습을 통해 행동 점수 변동 확인
    - failure: learning rate가 0이면 점수 변동 없음, 1.0이면 과도한 변동
    - Evidence .omo/evidence/task-1-selfgrow-enhancement.txt
  Commit: Y | fix(brain): SMART_LEARNING_RATE 적용 및 학습 비율 제어

- [ ] 2. _handle_warning 구현 및 테스트
  What to do / Must NOT do:
  - `brain_messaging.py:129-134`의 no-op 핸들러를 실제 위험 회피 행동으로 구현
  - 위험 메시지 수신 시 COMBAT 점수 가산 또는 IDLE 선택 유도
  - `test_brain.py`에 warning 핸들러 테스트 추가
  Must NOT: 다른 메시지 핸들러 변경, entity.py 직접 수정
  Parallelization: Wave 1 | Blocked by: 없음 | Blocks: 4, 5, 6, 7
  References (executor has NO interview context - be exhaustive):
    - brain_messaging.py:129-134 (_handle_warning 현재 구현)
    - brain_messaging.py:22-35 (다른 핸들러 패턴)
    - entity.py:213-219 (decide_action 메서드)
    - test_brain.py:48-53 (기존 메시지 테스트)
  Acceptance criteria (agent-executable):
    - `grep -A 10 "_handle_warning" sim/brain_messaging.py`에서 pass문 없음
    - `pytest tests/test_brain.py -v` 통과
    - `python -c "from sim.brain_messaging import _handle_warning; print('import ok')"` 성공
  QA scenarios (name the exact tool + invocation):
    - happy: 위험 메시지 전송 시 수신 개체가 위험 지역 회피 행동 실행
    - failure: 위험 메시지가 너무 멀리 있으면 무시 (dist > 2)
    - Evidence .omo/evidence/task-2-selfgrow-enhancement.txt
  Commit: Y | fix(brain): _handle_warning 위험 회피 행동 구현

- [ ] 3. Alliance/Treaty faction_id 조건 완화 및 테스트
  What to do / Must NOT do:
  - `brain_messaging.py:88-100`의 `_handle_alliance_accepted`에서 faction_id >= 0 조건 제거 또는 완화
  - `brain_messaging.py:103-126`의 `_handle_treaty_proposal`에서 동일 조건 완화
  - 파벌 미소속 개체 간 동맹/조약 가능하게 변경
  - `test_brain.py`에 외교 메시지 테스트 추가
  Must NOT: 파벌 시스템 자체 변경, faction.py 수정
  Parallelization: Wave 1 | Blocked by: 없음 | Blocks: 4, 5, 6, 7
  References (executor has NO interview context - be exhaustive):
    - brain_messaging.py:88-100 (_handle_alliance_accepted)
    - brain_messaging.py:103-126 (_handle_treaty_proposal)
    - faction.py:1-50 (파벌 시스템 구조)
    - test_brain.py:48-53 (기존 메시지 테스트)
  Acceptance criteria (agent-executable):
    - `grep -n "faction_id" sim/brain_messaging.py`에서 88-100줄에 >= 0 조건 없음
    - `pytest tests/test_brain.py -v` 통과
    - `python -c "from sim.brain_messaging import _handle_alliance_accepted; print('import ok')"` 성공
  QA scenarios (name the exact tool + invocation):
    - happy: 파벌 미소속 SmartBrain 개체 2마리가 동맹 메시지 교환 시 성공
    - failure: faction_id가 -1인 개체도 동맹 수락 가능
    - Evidence .omo/evidence/task-3-selfgrow-enhancement.txt
  Commit: Y | fix(brain): alliance/treaty faction_id 조건 완화

### Wave 2: SmartBrain 기능 강화 (C2)
- [ ] 4. 3+ 스텝 계획 시스템 구현
  What to do / Must NOT do:
  - `brain_planning.py:15-60`의 2-스텝 계획을 3+ 스텝으로 확장
  - **구체적 알고리즘 (빔 서치)**:
    1. 현재 상태에서 상위 3개 후보 행동 선택 (기존 로직 유지)
    2. 각 행동 적용 후 상태 시뮬레이션 (기존 로직 유지)
    3. 다음 스텝에서 다시 상위 2개 후보 행동 선택 (빔 폭 2)
    4. `SMART_PLANNING_DEPTH`만큼 반복 (기본값 3)
    5. 각 경로의 총점 = ∑(행동점수 * 할인율^스텝)
    6. 최고 점수 경로를 계획으로 선택
  - **구현 방식**: `try_multistep_plan`을 재귀 대신 반복문으로 구현
    - `for depth in range(config.SMART_PLANNING_DEPTH):` 루프
    - 각 깊이에서 `candidates = get_top_actions(current_state, beam_width=2)`
    - `beam_width`는 고정 2 (성능 보장)
  - `SMART_PLANNING_DEPTH` 파라미터를 config.py에 추가 (기본값: 3)
  - `test_brain.py`에 멀티스텝 계획 테스트 추가
  Must NOT: 기존 2-스텝 로직 제거, 계획 유효성 검증 변경, 빔 폭 변경 (2 고정)
  Parallelization: Wave 1 | Blocked by: 1 | Blocks: 5, 6, 7, 8-10
  References (executor has NO interview context - be exhaustive):
    - brain_planning.py:15-60 (현재 2-스텝 계획)
    - config.py:299-306 (SmartBrain 파라미터)
    - smart_brain.py:52-60 (계획 실행 로직)
    - test_brain.py:64-80 (유사도 테스트)
  Acceptance criteria (agent-executable):
    - `grep -n "SMART_PLANNING_DEPTH" sim/config.py` 결과 1건 이상
    - `grep -n "SMART_PLANNING_DEPTH" sim/brain_planning.py` 결과 1건 이상 (사용 검증)
    - `grep -n "for depth in range" sim/brain_planning.py` 결과 1건 이상 (반복문 구현)
    - `pytest tests/test_brain.py -v` 통과
    - `python -c "from sim.brain_planning import try_multistep_plan; print('import ok')"` 성공
  QA scenarios (name the exact tool + invocation):
    - happy: SmartBrain 개체가 3개 이상 행동 계획 수립 후 실행
    - failure: 최대 깊이 초과 시 2-스텝으로 폴백 (beam_width=2 유지)
    - Evidence .omo/evidence/task-4-selfgrow-enhancement.txt
  Commit: Y | feat(brain): 3+ 스텝 멀티스텝 계획 시스템

- [ ] 5. 경험 시간 감쇠 시스템 구현
  What to do / Must NOT do:
  - `smart_brain.py:36`의 경험 메모리에 시간 감쇠 적용
  - **구체적 구현 방식 (병렬 deque)**:
    1. `self.experiences: deque[Experience]` 유지 (기존 코드 변경 최소화)
    2. `self.experience_ticks: deque[int]` 추가 (동일한 maxlen)
    3. 경험 저장 시: `self.experiences.append(exp)`, `self.experience_ticks.append(current_tick)`
    4. `_state_similarity` 호출 시 시간 가중치 적용:
       ```python
       def _weighted_similarity(self, state: dict, current_tick: int) -> float:
           total_sim = 0.0
           total_weight = 0.0
           for exp, tick in zip(self.experiences, self.experience_ticks):
               sim = self._state_similarity(state, exp.state_snapshot)
               age = current_tick - tick
               weight = config.SMART_MEMORY_DECAY ** age  # 지수 감쇠
               total_sim += sim * weight
               total_weight += weight
           return total_sim / total_weight if total_weight > 0 else 0.0
       ```
  - `SMART_MEMORY_DECAY` 파라미터를 config.py에 추가 (기본값: 0.95)
  - `test_brain.py`에 시간 감쇠 테스트 추가
  Must NOT: Experience 데이터클래스 변경, 메모리 크기 변경, 유사도 알고리즘 변경
  Parallelization: Wave 1 | Blocked by: 1 | Blocks: 6, 7, 8-10
  References (executor has NO interview context - be exhaustive):
    - smart_brain.py:36 (경험 메모리 초기화)
    - smart_brain.py:201-207 (경험 저장)
    - smart_brain.py:212-223 (_make_snapshot)
    - smart_brain.py:225-237 (_state_similarity)
    - brain_base.py:8-13 (Experience 데이터클래스)
    - config.py:300 (SMART_MEMORY_SIZE)
  Acceptance criteria (agent-executable):
    - `grep -n "SMART_MEMORY_DECAY" sim/config.py` 결과 1건 이상
    - `grep -n "SMART_MEMORY_DECAY" sim/smart_brain.py` 결과 1건 이상 (사용 검증)
    - `grep -n "experience_ticks" sim/smart_brain.py` 결과 2건 이상 (초기화, 저장)
    - `pytest tests/test_brain.py -v` 통과
    - `python -c "from sim.smart_brain import SmartBrain; print('import ok')"` 성공
  QA scenarios (name the exact tool + invocation):
    - happy: 오래된 경험은 최신 경험보다 낮은 가중치 적용 (감쇠 공식: `decay^(현재틱 - 경험틱)`)
    - failure: 감쇠율 1.0이면 시간 무시, 0.0이면 즉시 무시
    - Evidence .omo/evidence/task-5-selfgrow-enhancement.txt
  Commit: Y | feat(brain): 경험 시간 감쇠 시스템

- [ ] 6. 거래 호가 협상 시스템 구현 (신규 기능)
  What to do / Must NOT do:
  - `brain_messaging.py:37-66`의 거래 메시지에 price 필드 추가
  - `trade_counter` 메시지 타입 추가 (카운터오퍼)
  - `brain_messaging.py:22-35`에 `_handle_trade_counter` 핸들러 추가
  - `smart_brain.py:178-184`에 `send_trade_counter` 메서드 추가
  Must NOT: 실제 자원 이동 로직 변경, market.py 수정
  Parallelization: Wave 1 (독립 실행 가능) | Blocked by: 없음 | Blocks: 7
  References (executor has NO interview context - be exhaustive):
    - brain_messaging.py:37-66 (거래 메시지 처리)
    - brain_messaging.py:22-35 (메시지 타입 목록)
    - smart_brain.py:178-184 (거래 메시지 발송)
  Acceptance criteria (agent-executable):
    - `grep -n "trade_counter" sim/brain_messaging.py` 결과 2건 이상 (핸들러, 타입)
    - `pytest tests/test_brain.py -v` 통과
    - `python -c "from sim.brain_messaging import _handle_trade_counter; print('import ok')"` 성공
  QA scenarios (name the exact tool + invocation):
    - happy: 거래 제안 시 price 포함, 카운터오퍼 후 최종 체결
    - failure: 가격 불일치 시 거래 거절
    - Evidence .omo/evidence/task-6-selfgrow-enhancement.txt
  Commit: Y | feat(brain): 거래 호가 협상 시스템

- [ ] 7. 계획 실패 학습 시스템 구현
  What to do / Must NOT do:
  - `smart_brain.py:52-60`에서 계획 실패 시 `feedback(-1.0)` 호출
  - `_is_plan_valid` 실패 시 해당 행동-상태 쌍의 점수 하락 유도
  - `test_brain.py`에 계획 실패 학습 테스트 추가
  Must NOT: 계획 자체 변경, 피드백 로직 변경
  Parallelization: Wave 2 | Blocked by: 1 (SMART_LEARNING_RATE 적용 후 피드백 효과 보장) | Blocks: 8, 9, 10
  References (executor has NO interview context - be exhaustive):
    - smart_brain.py:52-60 (계획 실행 로직)
    - smart_brain.py:257-269 (_is_plan_valid)
    - smart_brain.py:201-207 (피드백 메서드)
    - test_brain.py:81-86 (기존 피드백 테스트)
  Acceptance criteria (agent-executable):
    - `grep -n "feedback(-1.0)" sim/smart_brain.py` 결과 1건 이상
    - `pytest tests/test_brain.py -v` 통과
    - `python -c "from sim.smart_brain import SmartBrain; print('import ok')"` 성공
  QA scenarios (name the exact tool + invocation):
    - happy: 잘못된 계획 실행 후 해당 행동 점수 하락
    - failure: 피드백이 음수일 때만 점수 하락, 양수일 때는 상승
    - Evidence .omo/evidence/task-7-selfgrow-enhancement.txt
  Commit: Y | feat(brain): 계획 실패 학습 시스템

### Wave 3: 테스트 커버리지 확대 (C3)
- [ ] 8. test_ideology.py 신규 작성
  What to do / Must NOT do:
  - `tests/test_ideology.py` 파일 생성
  - 이데올로기 시스템 단위 테스트 6개 이상 작성
  - 이데올로기 생성, 행동 바이어스, 전파 로직 테스트
  Must NOT: 기존 테스트 파일 수정, ideology.py 변경
  Parallelization: Wave 3 | Blocked by: 1-7 (SmartBrain 기능 완료 후) | Blocks: F1
  References (executor has NO interview context - be exhaustive):
    - ideology.py:1-76 (이데올로기 시스템)
    - sim/__init__.py:1-21 (내보내기)
    - tests/conftest.py:1-50 (공유 fixture)
    - tests/test_brain.py:1-86 (기존 테스트 패턴)
  Acceptance criteria (agent-executable):
    - `ls tests/test_ideology.py` 성공
    - `pytest tests/test_ideology.py -v` 통과
    - `grep -c "def test_" tests/test_ideology.py` 결과 6 이상
  QA scenarios (name the exact tool + invocation):
    - happy: 이데올로기 생성, 바이어스 적용, 전파 성공
    - failure: 잘못된 이데올로기 타입 생성 시 예외 발생
    - Evidence .omo/evidence/task-8-selfgrow-enhancement.txt
  Commit: Y | test(ideology): 이데올로기 시스템 단위 테스트

- [ ] 9. test_season.py 강화
  What to do / Must NOT do:
  - 기존 `tests/test_season.py`에 계절별 효과 테스트 추가
  - 자원 재생, 에너지 소비, 채집 보너스, 이동 속도 계절별 검증
  - 테스트 수를 25개 이상으로 확장 (기존 21개 + 신규 4개)
  Must NOT: season.py 변경, 기존 테스트 제거
  Parallelization: Wave 3 | Blocked by: 1-7 (SmartBrain 기능 완료 후) | Blocks: F1
  References (executor has NO interview context - be exhaustive):
    - season.py:1-39 (계절 시스템)
    - config.py:312-319 (계절 파라미터)
    - tests/test_season.py:1-62 (기존 테스트)
    - tests/conftest.py:1-50 (공유 fixture)
  Acceptance criteria (agent-executable):
    - `pytest tests/test_season.py -v` 통과
    - `grep -c "def test_" tests/test_season.py` 결과 25 이상 (기존 21 + 신규 4개)
    - `python -c "from sim.season import get_season_effect; print('import ok')"` 성공
  QA scenarios (name the exact tool + invocation):
    - happy: 각 계절에서 올바른 효과 배율 적용
    - failure: 잘못된 계절 인덱스 시 기본값 반환
    - Evidence .omo/evidence/task-9-selfgrow-enhancement.txt
  Commit: Y | test(season): 계절별 효과 단위 테스트 확대

- [ ] 10. test_faction_diplomacy.py 신규 작성
  What to do / Must NOT do:
  - `tests/test_faction_diplomacy.py` 파일 생성
  - 파벌 외교 시스템 단위 테스트 8개 이상 작성
  - 동맹, 조약, 비공격 협정, 무역 협정 테스트
  Must NOT: faction.py 변경, 기존 테스트 파일 수정
  Parallelization: Wave 3 | Blocked by: 1-7 (SmartBrain 기능 완료 후) | Blocks: F1
  References (executor has NO interview context - be exhaustive):
    - faction.py:1-326 (파벌 시스템)
    - brain_messaging.py:22-35 (메시지 타입)
    - tests/conftest.py:1-50 (공유 fixture)
    - tests/test_brain.py:1-86 (기존 테스트 패턴)
  Acceptance criteria (agent-executable):
    - `ls tests/test_faction_diplomacy.py` 성공
    - `pytest tests/test_faction_diplomacy.py -v` 통과
    - `grep -c "def test_" tests/test_faction_diplomacy.py` 결과 8 이상
  QA scenarios (name the exact tool + invocation):
    - happy: 동맹 제안 → 수락 → 동맹 성립
    - failure: 비공격 협정 위반 시 관계 악화
    - Evidence .omo/evidence/task-10-selfgrow-enhancement.txt
  Commit: Y | test(faction): 파벌 외교 시스템 단위 테스트

### Wave 4: 문서 동기화 (C4) + 기술 부채 해소 (C5)
- [ ] 11. AGENTS.md Phase 상태 갱신
  What to do / Must NOT do:
  - `AGENTS.md` §6.2의 "Phase 3 (진행 중)" → "Phase 4.5 완료"로 갱신
  - 완료된 Phase 목록 추가 (3.1 이데올로기/계절/건물/이벤트, 4 UI, 4.5 데이터 내보내기)
  Must NOT: 다른 섹션 변경, 규칙 변경
  Parallelization: Wave 4 | Blocked by: 1-10 | Blocks: F1
  References (executor has NO interview context - be exhaustive):
    - AGENTS.md — `grep -n "Phase" AGENTS.md` 로 위치 먼저 확인 후 갱신
    - README.md:150-200 (개발 진행 상황)
    - .omo/plans/ 디렉토리 (기존 계획 파일 확인)
  Acceptance criteria (agent-executable):
    - `grep -n "Phase" AGENTS.md` 결과 "진행 중" 없음
    - `grep -n "Phase 4.5" AGENTS.md` 결과 1건 이상
    - `python -c "open('AGENTS.md').read()"` 오류 없음 (파일 읽기 가능 확인)
  QA scenarios (name the exact tool + invocation):
    - happy: AGENTS.md의 Phase 상태가 실제 코드와 일치
    - failure: 문법 오류 없음, 가독성 유지
    - Evidence .omo/evidence/task-11-selfgrow-enhancement.txt
  Commit: Y | docs: AGENTS.md Phase 상태 동기화

- [ ] 12. README.md 새 시스템 문서화
  What to do / Must NOT do:
  - `README.md`에 "계절/이벤트/건물/이데올로기 시스템" 섹션 추가
  - 각 시스템의 기능과 매커니즘 설명
  - 기존 "주요 기능" 섹션에 4개 시스템 추가
  Must NOT: 기존 섹션 삭제, 실행 방법 변경
  Parallelization: Wave 4 | Blocked by: 1-10 | Blocks: F1
  References (executor has NO interview context - be exhaustive):
    - README.md:1-50 (주요 기능)
    - season.py:1-39 (계절 시스템)
    - events.py:1-142 (이벤트 시스템)
    - buildings.py:1-44 (건물 시스템)
    - ideology.py:1-76 (이데올로기 시스템)
  Acceptance criteria (agent-executable):
    - `grep -n "계절" README.md` 결과 1건 이상
    - `grep -n "이벤트" README.md` 결과 1건 이상
    - `grep -n "건물" README.md` 결과 1건 이상
    - `grep -n "이데올로기" README.md` 결과 1건 이상
  QA scenarios (name the exact tool + invocation):
    - happy: 새 시스템 문서가 기존 형식과 일관성 유지
    - failure: 마크다운 문법 오류 없음
    - Evidence .omo/evidence/task-12-selfgrow-enhancement.txt
  Commit: Y | docs: README.md 새 시스템 문서화

- [ ] 13. requirements.txt LLM 주석 제거
  What to do / Must NOT do:
  - `requirements.txt`에서 LLM 관련 주석 라인 3줄 제거
  - "Phase 1+: LLM 통합 시 추가 예정" 주석도 제거
  Must NOT: Rich 의존성 변경, 새 의존성 추가
  Parallelization: Wave 1 (독립 실행 가능) | Blocked by: 없음 | Blocks: F1
  References (executor has NO interview context - be exhaustive):
    - requirements.txt:1-9 (현재 내용)
    - AGENTS.md:60-70 (LLM 사용 금지 규칙)
  Acceptance criteria (agent-executable):
    - `grep -n "openai" requirements.txt` 결과 0건
    - `grep -n "anthropic" requirements.txt` 결과 0건
    - `grep -n "httpx" requirements.txt` 결과 0건
    - `pip install -r requirements.txt` 성공
  QA scenarios (name the exact tool + invocation):
    - happy: requirements.txt에 Rich만 남음
    - failure: 설치 오류 없음
    - Evidence .omo/evidence/task-13-selfgrow-enhancement.txt
  Commit: Y | cleanup: requirements.txt LLM 주석 제거

- [ ] 14. sim/ui/event_log.py 분할
  What to do / Must NOT do:
  - `sim/ui/event_log.py`를 3개 파일로 분할:
    - `sim/ui/event_types.py`: 이벤트 타입 정의 (18종)
    - `sim/ui/event_filters.py`: 이벤트 필터링 로직
    - `sim/ui/event_log.py`: 메인 클래스 (남은 부분)
  - 기존 import 경로 유지 (event_log.py에서 re-export)
  - `sim/__init__.py`에 새 모듈 추가 내보내기
  Must NOT: 기존 API 변경, visualizer.py 수정
  Parallelization: Wave 4 | Blocked by: 1-10 | Blocks: F1
  References (executor has NO interview context - be exhaustive):
    - sim/ui/event_log.py:1-389 (현재 구조)
    - visualizer.py:1-217 (event_log 사용 방식)
    - sim/__init__.py:1-21 (내보내기)
  Acceptance criteria (agent-executable):
    - `ls sim/ui/event_types.py sim/ui/event_filters.py` 성공
    - `python -c "from sim.ui.event_log import EventLog; print('import ok')"` 성공
    - `grep -n "event_types\|event_filters" sim/__init__.py` 결과 1건 이상
    - `pytest tests/ -v` 통과
    - `wc -l sim/ui/event_log.py` 결과 280줄 이하
  QA scenarios (name the exact tool + invocation):
    - happy: 분할 후 기존 기능 정상 동작
    - failure: import 오류 없음, circular import 없음
    - Evidence .omo/evidence/task-14-selfgrow-enhancement.txt
  Commit: Y | refactor(ui): event_log.py 모듈 분할

- [ ] 15. faction.py에서 외교 로직 분리
  What to do / Must NOT do:
  - `faction.py`의 외교 관련 로직을 `sim/diplomacy.py`로 추출
  - faction.py는 파벌 생명주기만 담당하도록 정리
  - 기존 API 유지 (faction.py에서 diplomacy 모듈 호출)
  - `sim/__init__.py`에 `DiplomacyManager` 추가 내보내기
  Must NOT: 기존 API 변경, brain_messaging.py 수정
  Parallelization: Wave 4 | Blocked by: 1-10 | Blocks: F1
  References (executor has NO interview context - be exhaustive):
    - faction.py:1-326 (현재 구조)
    - faction.py:136-260 (외교 로직, DIPLOMACY_TYPES 포함)
    - brain_messaging.py:88-126 (외교 메시지 처리)
    - sim/__init__.py:1-21 (내보내기)
  Acceptance criteria (agent-executable):
    - `ls sim/diplomacy.py` 성공
    - `python -c "from sim.diplomacy import DiplomacyManager; print('import ok')"` 성공
    - `grep -n "DiplomacyManager" sim/__init__.py` 결과 1건 이상
    - `pytest tests/ -v` 통과
    - `wc -l sim/faction.py` 결과 250줄 이하
  QA scenarios (name the exact tool + invocation):
    - happy: 분할 후 기존 파벌/외교 기능 정상 동작
    - failure: import 오류 없음, circular import 없음
    - Evidence .omo/evidence/task-15-selfgrow-enhancement.txt
  Commit: Y | refactor(faction): 외교 로직 diplomacy.py로 분리

## Final verification wave
> Runs in parallel after ALL todos. ALL must APPROVE. Surface results and wait for the user's explicit okay before declaring complete.

- [ ] F1. 계획 준수 감사
  What to do / Must NOT do:
  - 모든 todo가 수용 기준을 충족하는지 검증
  - 각 todo의 QA 시나리오 실행 및 결과 확인
  - .omo/evidence/ 디렉토리에 증거 파일 존재 확인
  Must NOT: 코드 수정, 테스트 변경
  Parallelization: Wave 5 | Blocked by: 1-15 | Blocks: 사용자 승인
  References: 모든 todo의 수용 기준 참조
  Acceptance criteria (agent-executable):
    - `ls .omo/evidence/task-*-selfgrow-enhancement.txt` 결과 15건 이상
    - `pytest tests/ -v` 전체 통과
    - `python -m sim.main --no-visual --ticks 100 --seed 42` 정상 종료
  QA scenarios: happy: 모든 검증 통과, failure: 1개 이상 실패 시 해당 todo 재검토
  Evidence .omo/evidence/F1-selfgrow-enhancement.txt

- [ ] F2. 코드 품질 리뷰
  What to do / Must NOT do:
  - 코드 스타일 일관성 검사 (한국어 주석, 영어 식별자)
  - 파일 크기 제한 준수 확인 (700줄 이하)
  - import 문 정리 및 순환 참조 없음 확인
  - 타입 힌트 완성도 검사
  Must NOT: 기능 변경, 로직 수정
  Parallelization: Wave 5 | Blocked by: 1-15 | Blocks: 사용자 승인
  References: AGENTS.md §5.1 (코드 수정 원칙)
  Acceptance criteria (agent-executable):
    - `find sim/ -name "*.py" -exec wc -l {} \; | sort -rn | head -1` 결과 700줄 이하
    - `grep -r "from __future__ import annotations" sim/` 파일당 1건
    - `python -m py_compile sim/*.py` 오류 없음
  QA scenarios: happy: 코드 품질 기준 충족, failure: 스타일 위반 0건
  Evidence .omo/evidence/F2-selfgrow-enhancement.txt

- [ ] F3. 헤드리스 통합 테스트
  What to do / Must NOT do:
  - `python -m sim.main --no-visual --ticks 200 --seed 42` 실행
  - `python -m sim.main --no-visual --ticks 200 --seed 7` 실행
  - `python -m sim.main --no-visual --ticks 200 --seed 99` 실행
  - 각 시드에서 시뮬레이션이 200틱 이내에 멸종하지 않는지 확인
  - SmartBrain 개체가 정상적으로 행동하는지 확인
  Must NOT: 코드 수정, 설정 변경
  Parallelization: Wave 5 | Blocked by: 1-15 | Blocks: 사용자 승인
  References: AGENTS.md §5.2 (테스트 원칙)
  Acceptance criteria (agent-executable):
    - 3개 시드 모두에서 `population > 0` 상태로 200틱 완료
    - `smart_count > 0` 상태에서 SmartBrain 개체 존재
    - `kill_count`가 비정상적으로 급증하지 않음
  QA scenarios: happy: 3개 시드 모두 정상 종료, failure: 1개 시드라도 멸종 시 재검토
  Evidence .omo/evidence/F3-selfgrow-enhancement.txt

- [ ] F4. 범위 충실도
  What to do / Must NOT do:
  - 변경된 파일이 Scope IN에만 해당하는지 확인
  - Scope OUT (LLM, GUI, 멀티 시나리오, 신경망)에 해당하는 변경 없는지 확인
  - 기존 기능이 의도치 않게 변경되지 않았는지 확인
  Must NOT: 범위 초과 변경, 새 기능 추가
  Parallelization: Wave 5 | Blocked by: 1-15 | Blocks: 사용자 승인
  References: Scope IN/OUT 섹션 참조
  Acceptance criteria (agent-executable):
    - `git diff --name-only` 결과가 Scope IN에만 해당
    - `grep -r "openai\|anthropic\|httpx" sim/` 결과 0건 (LLM 사용 없음)
    - `grep -r "import tkinter\|import flask\|import streamlit" sim/` 결과 0건 (GUI 없음)
  QA scenarios: happy: 범위 준수, failure: 범위 초과 변경 발견 시 해당 변경 롤백
  Evidence .omo/evidence/F4-selfgrow-enhancement.txt

## Commit strategy
- 각 todo 완료 시 개별 커밋 (한국어 메시지)
- 형식: `[모듈명] 변경 내용 요약`
- 예: `[brain] SMART_LEARNING_RATE 적용 및 학습 비율 제어`
- 커밋 전 `git diff --staged`로 변경 사항 최소 2회 검토
- 설정 파일(config.py)과 로직 파일(entity.py, brain.py) 변경은 분리해서 커밋
- Wave별 묶음 커밋 가능 (예: Wave 1 완료 후 1개 커밋)
- 최종 검증 통과 후 사용자 승인 시에만 커밋 허용

## Success criteria
1. SmartBrain P0 버그 3건 모두 수정됨 (SMART_LEARNING_RATE 적용, _handle_warning 구현, alliance faction_id 조건 완화)
2. SmartBrain 기능 4건 모두 강화됨 (3+ 스텝 계획, 경험 시간 감쇠, 거래 호가 협상, 계획 실패 학습)
3. 테스트 파일 3개 신규/강화됨 (test_ideology.py, test_season.py, test_faction_diplomacy.py)
4. 문서 3건 동기화됨 (AGENTS.md, README.md, requirements.txt)
5. 기술 부채 2건 해소됨 (event_log.py 분할, faction.py 외교 로직 분리)
6. 모든 테스트 통과 (pytest tests/ -v)
7. 3개 시드(42, 7, 99)에서 200틱 실행 정상 종료
8. 코드 품질 기준 충족 (700줄 이하, 타입 힌트, 한국어 주석)
9. 범위 준수 (LLM/GUI/멀티 시나리오/신경망 변경 없음)
10. 최종 검증 4항목 모두 통과

## Open questions
- 외교 시스템이 faction.py에 완전히 구현되었는지 검증 필요 (Task 15에서 해소)
- 공간 인덱싱이 실제로 구현되었는지 world.py 검증 필요 (현재 범위 외)
- CI/CD 우선순위: GitHub Actions 설정 vs 로컬 개발 환경 개선 중 선택 (현재 범위 외)
