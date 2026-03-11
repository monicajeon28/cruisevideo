# WO v10.0 - 코드 품질 S등급(A+) 달성 작업지시서

**작성일**: 2026-03-10
**현재 등급**: B+ (85점)
**목표 등급**: A+ (95+점)
**전제**: Phase A (C+→B+) 완료 상태에서 시작

---

## 현황 요약

| 카테고리 | 현재 | 목표 | 갭 |
|----------|------|------|-----|
| SSOT 일관성 | 95% | 100% | V3/V5/V6 3건 |
| God Object | 1,681줄 | <800줄 | 상수+위임 추출 필요 |
| Middle Man | 15개 래퍼 | 0개 | 직접 호출 전환 |
| 매직넘버 | ~10개 | 0개 | 상수화 필요 |
| EXE 배포 | CONDITIONAL | GO | W1/W2 2건 |
| 미사용 import | 4건 | 0건 | 삭제 |
| 보안 | PASS | PASS | 유지 |

---

## Phase B: A- 등급 달성 (85→92점, +7점)

### B-1. SSOT 타이밍 충돌 해소 (+3점)

**문제**: Pop/ReHook 생성기와 검증기가 서로 다른 타이밍 사용

| 구분 | 생성 (script_metadata_generator.py) | 검증 (pop_message_validator.py / rehook_injector.py) |
|------|-------------------------------------|------------------------------------------------------|
| Pop | `[15.0, 32.5, 42.0]` (168행) | `[5.0, 18.0, 40.0]` (34행) |
| ReHook | `[9.0, 27.0]` (233-254행) | `[13.0, 32.0]` (224-229행) |

**수정 방안**:
1. `engines/sgrade_constants.py`에 SSOT 상수 추가:
   ```python
   POP_TARGET_TIMINGS = [15.0, 32.5, 42.0]  # WO v7.0 SSOT
   REHOOK_TARGET_TIMINGS = [9.0, 27.0]       # WO v7.0 SSOT
   ```
2. `pop_message_validator.py` 34행: `TARGET_TIMINGS = [5.0, 18.0, 40.0]` → `from engines.sgrade_constants import POP_TARGET_TIMINGS`로 교체
3. `pop_message_validator.py` 38행: `REHOOK_TIMINGS = [13.0, 32.0]` → `from engines.sgrade_constants import REHOOK_TARGET_TIMINGS`로 교체
4. `rehook_injector.py` 224행: `11.0 <= cumulative_time <= 15.0` → `REHOOK_TARGET_TIMINGS[0] - 2.0 <= cumulative_time <= REHOOK_TARGET_TIMINGS[0] + 2.0`
5. `rehook_injector.py` 229행: `30.0 <= cumulative_time <= 34.0` → `REHOOK_TARGET_TIMINGS[1] - 2.0 <= cumulative_time <= REHOOK_TARGET_TIMINGS[1] + 2.0`
6. `script_metadata_generator.py` 168행: `target_timings = [15.0, 32.5, 42.0]` → `from engines.sgrade_constants import POP_TARGET_TIMINGS`로 교체

**관련 파일**: `sgrade_constants.py`, `pop_message_validator.py`, `rehook_injector.py`, `script_metadata_generator.py`
**크로스체크**: 전후 S등급 채점 결과 비교 (Pop 10점 + ReHook 10점 유지 확인)

---

### B-2. HOOK_TYPES 스키마 통합 (+1점)

**문제**: 2개 파일에 서로 다른 스키마의 HOOK_TYPES 존재

| 파일 | 키 수 | 스키마 |
|------|-------|--------|
| `comprehensive_script_generator.py` 197행 | 10+ | `{templates: [5개], emotion, voice}` |
| `hook_generator.py` 27행 | 6 | `{templates: [2개], score_weight}` |

**수정 방안**:
1. `comprehensive_script_generator.py`의 HOOK_TYPES를 정본으로 채택 (더 풍부한 템플릿)
2. `hook_generator.py`에 `score_weight` 속성을 `comprehensive_script_generator.py` HOOK_TYPES에 병합
3. `hook_generator.py`의 HOOK_TYPES 삭제, `comprehensive_script_generator.py`에서 import
4. 또는 `engines/hook_constants.py`로 분리하여 양쪽에서 import

**관련 파일**: `comprehensive_script_generator.py`, `hook_generator.py`
**크로스체크**: Hook 선택 로직이 양쪽에서 동일 결과 산출 확인

---

### B-3. EXE 배포 CONDITIONAL→GO 전환 (+1점)

**수정 항목**:

| # | 항목 | 수정 내용 |
|---|------|----------|
| W1 | upload_package hiddenimports | `cruisedot.spec`에 `'upload_package'`, `'upload_package.__init__'`, `'upload_package.generator'` 3개 추가 |
| W2 | src/__init__.py 부재 | `D:\mabiz\src\__init__.py` 빈 파일 생성 |
| W3 | generate.py __file__ | 33/104/110/430행에 `sys.frozen` 분기 추가 또는 `path_resolver.get_project_root()` 사용 |

**관련 파일**: `cruisedot.spec`, `src/__init__.py` (신규), `generate.py`
**크로스체크**: `python -c "import upload_package; print('OK')"` 성공 확인

---

### B-4. Middle Man 위임 래퍼 제거 (+2점)

**문제**: `comprehensive_script_generator.py` 1546-1613행에 15개 위임 메서드가 단순 pass-through

**수정 방안**:
1. `generate_script()` 메서드 내부에서 위임 래퍼 대신 직접 호출로 전환:
   ```python
   # Before (Middle Man)
   segments = self._inject_trust_elements(segments, port, ship)

   # After (Direct)
   segments = self._enhancer.inject_trust_elements(segments, port, ship)
   ```
2. 15개 위임 메서드 전체 삭제 (1546-1613행, 약 68줄 감소)
3. `generate_script()` 내 14곳 호출을 직접 호출로 교체

**삭제 대상 메서드 목록**:
- `_inject_trust_elements` → `self._enhancer.inject_trust_elements`
- `_assign_dialogue_voices` → `self._enhancer.assign_dialogue_voices`
- `_generate_cta` → `self._enhancer.generate_cta`
- `_validate_emotion_curve` → `self._quality_validator.validate_emotion_curve`
- `_enforce_emotion_curve` → `self._quality_validator.enforce_emotion_curve`
- `_validate_empathy_trust_ratio` → `self._quality_validator.validate_empathy_trust_ratio`
- `_check_banned_words` → `self._quality_validator.check_banned_words`
- `_sanitize_banned_from_segments` → `self._quality_validator.sanitize_banned_from_segments`
- `_inject_port_keywords` → `self._enhancer.inject_port_keywords`
- `_extract_port_keywords` → `self._enhancer.extract_port_keywords`
- `_calculate_s_grade_score` → `self._quality_validator.calculate_s_grade_score`
- `_generate_title` → `self._metadata_gen.generate_title`
- `_inject_pop_metadata` → `self._metadata_gen.inject_pop_metadata`
- `_inject_rehook_segments` → `self._metadata_gen.inject_rehook_segments`
- `_dataclass_to_dict` → `self._metadata_gen.dataclass_to_dict`

**관련 파일**: `comprehensive_script_generator.py`
**크로스체크**: generate_script() 출력 동일성 확인

---

## Phase C: A 등급 달성 (92→95점, +3점)

### C-1. 상수 추출로 God Object 경량화 (+1.5점)

**문제**: `comprehensive_script_generator.py`에 500+줄의 상수 블록

**수정 방안**:
1. `engines/script_constants.py` 신규 파일 생성
2. 이동 대상:
   - `HOOK_TYPES` (~197-420행, ~220줄)
   - `FEAR_SCENARIOS` (~421행 이후, ~50줄)
   - `LEARNING_RAG_CONTEXT` (~85-196행, ~110줄)
3. `comprehensive_script_generator.py`에서 import로 교체
4. 예상 파일 크기: 1,681줄 → ~1,300줄 (380줄 감소)

**관련 파일**: `comprehensive_script_generator.py`, `script_constants.py` (신규)
**크로스체크**: import 체인 정상 확인, 순환 참조 없음 확인

---

### C-2. 매직넘버 상수화 (+0.5점)

**수정 대상**:
| 위치 | 현재 | 상수명 |
|------|------|--------|
| generator 653행 | `emotion_score: 0.35` | `HOOK_EMOTION_SCORE = 0.35` |
| generator 654행 | `duration_target: 3.0` | `HOOK_DURATION = 3.0` |
| generator 674행 | `emotion_score: 0.92` | `CTA_URGENCY_EMOTION = 0.92` |
| generator 688행 | `emotion_score: 0.95` | `CTA_ACTION_EMOTION = 0.95` |
| generator 703행 | `emotion_score: 0.88` | `CTA_TRUST_EMOTION = 0.88` |
| generator 677행 | `timing: 43.0` | `CTA_URGENCY_TIMING = 43.0` |
| generator 691행 | `timing: 45.0` | `CTA_ACTION_TIMING = 45.0` |
| generator 705행 | `timing: 48.0` | `CTA_TRUST_TIMING = 48.0` |

**수정 방안**: `sgrade_constants.py`에 추가 후 import

---

### C-3. 미사용 import + 명명 정리 (+0.5점)

**삭제 대상**:
| 파일 | import | 이유 |
|------|--------|------|
| `comprehensive_script_generator.py:32` | `Tuple` | 미사용 |
| `segment_enhancer.py:17` | `Optional` | 미사용 |
| `script_quality_validator.py:16` | `Tuple` | 미사용 |
| `script_quality_validator.py:29` | `EMOTION_SCORES` | 미사용 (주석만 참조) |

**명명 통일**: `re-hook` / `rehook` / `re_hook` → `rehook`으로 통일
- segment_type: `"rehook"` (현재 `"re-hook"`)
- 메서드명: `inject_rehook_segments` (현재 OK)
- 변수명: `rehook_count` (현재 OK)

---

### C-4. "충격" 감정명 vs 금지어 충돌 해소 (+0.5점)

**문제**: `sgrade_constants.py`에서 "충격"이 EMOTION_SCORES (감정명)이자 BANNED_WORDS (금지어)

**수정 방안**:
- Option A: 감정명을 "임팩트"로 변경 (EMOTION_SCORES, EMOTION_RANGES, voice_assignment 등 전체)
- Option B: banned word 체크에서 `.emotion` 필드가 아닌 `.text` 필드만 검사하는 것을 명시적으로 문서화 (현재 이미 `.text`만 검사하므로 실제 충돌 없음)

**권장**: Option B (이미 기능적 충돌 없음, 주석 추가만으로 해결)

---

## Phase D: A+ 등급 달성 (95→98점, +3점) - 선택사항

### D-1. generate_script() 리팩토링 (+1점)
- 258줄 메서드를 3개 하위 메서드로 분할:
  - `_prepare_segments()`: Steps 1-9 (세그먼트 생성+검증)
  - `_build_segment_dicts()`: Steps 10-15.5 (dict 조립)
  - `_compose_output()`: Step 16 (ScriptOutput 생성)

### D-2. Gemini 프롬프트 외부화 (+1점)
- `_generate_with_gemini()` 내 160줄 프롬프트 → `templates/gemini_prompt.txt`

### D-3. DI (Dependency Injection) 도입 (+1점)
- `__init__`에서 하드코딩 인스턴스 생성 → 파라미터 주입으로 테스트 용이성 확보

---

## 실행 계획

| Phase | 태스크 | 예상 시간 | 우선순위 |
|-------|--------|----------|---------|
| **B-1** | SSOT 타이밍 통합 (Pop+ReHook) | 15분 | CRITICAL |
| **B-2** | HOOK_TYPES 통합 | 10분 | HIGH |
| **B-3** | EXE 배포 W1/W2/W3 수정 | 10분 | HIGH |
| **B-4** | Middle Man 15개 제거 | 15분 | HIGH |
| **C-1** | 상수 추출 (script_constants.py) | 20분 | MEDIUM |
| **C-2** | 매직넘버 상수화 | 10분 | MEDIUM |
| **C-3** | 미사용 import + 명명 통일 | 5분 | LOW |
| **C-4** | "충격" 충돌 문서화 | 5분 | LOW |
| **D-1~3** | 리팩토링 (선택) | 30분 | OPTIONAL |

---

## 수정 파일 영향도 매트릭스

| 파일 | B-1 | B-2 | B-3 | B-4 | C-1 | C-2 | C-3 | C-4 |
|------|-----|-----|-----|-----|-----|-----|-----|-----|
| sgrade_constants.py | W | - | - | - | - | W | - | W |
| pop_message_validator.py | W | - | - | - | - | - | - | - |
| rehook_injector.py | W | - | - | - | - | - | - | - |
| script_metadata_generator.py | W | - | - | - | - | - | - | - |
| comprehensive_script_generator.py | - | W | - | W | W | W | W | - |
| hook_generator.py | - | W | - | - | - | - | - | - |
| cruisedot.spec | - | - | W | - | - | - | - | - |
| generate.py | - | - | W | - | - | - | - | - |
| src/__init__.py (신규) | - | - | W | - | - | - | - | - |
| script_constants.py (신규) | - | - | - | - | W | - | - | - |
| segment_enhancer.py | - | - | - | - | - | - | W | - |
| script_quality_validator.py | - | - | - | - | - | - | W | - |

**W** = Write (수정)

---

## 크로스체크 항목

Phase B/C 완료 후 반드시 검증:
1. **Import 체인**: 모든 .py 파일 `python -c "import 모듈명"` 성공
2. **순환 참조**: sgrade_constants ← 다른 모듈 (단방향만)
3. **S등급 채점**: Pop 3개 + ReHook 2개 + Trust 3종 유지
4. **EXE spec**: `pyinstaller --check cruisedot.spec` 정상
5. **Middle Man 제거 후**: generate_script() 출력 동일성
6. **HOOK_TYPES 통합 후**: Hook 선택 로직 양 파일 호환

---

## 등급 예상 로드맵

```
현재: B+ (85점)
  ↓ Phase B-1~B-4 (+7점)
A- (92점)
  ↓ Phase C-1~C-4 (+3점)
A (95점)
  ↓ Phase D-1~D-3 (+3점, 선택)
A+ (98점)
```
