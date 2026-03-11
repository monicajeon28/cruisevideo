# WO v7.0: 6-Agent 비판 분석 통합 작업지시서

**작성일**: 2026-03-09
**근거**: 6개 전문 에이전트 병렬 비판 분석 결과
**목표**: Gemini 3대 문제 해결 + 구조적 품질 개선 + YouTube 성과 연동

---

## Executive Summary

6개 에이전트가 독립적으로 분석한 결과, **4대 구조적 병목**이 발견됨:

| # | 병목 | 현재 | 목표 | 예상 효과 |
|---|------|------|------|-----------|
| 1 | Gemini 3대 문제 | block4 60% 실패 | 5% 이하 | S등급 80%+ |
| 2 | 감정곡선+Hook | 완주율 25-30% | 50%+ | 조회수 3x |
| 3 | Config-구현 괴리 6건 | 30/100 프로덕션 | 60/100+ | 품질 2x |
| 4 | S등급 자기채점 | YouTube 성과 무관 | 성과 연동 | 실효성 확보 |

---

## Phase 1: Gemini 3대 문제 근본 해결 (P0, 4시간)

### 1.1 FIX-GEMINI-TOKENS: max_output_tokens 증가 + Structured Output

**파일**: `engines/comprehensive_script_generator.py` (line 1019-1023)

**현재**:
```python
config=types.GenerateContentConfig(
    temperature=0.8,
    max_output_tokens=4500,
    top_p=0.95,
    top_k=40
)
```

**변경**:
```python
config=types.GenerateContentConfig(
    temperature=0.5,          # 0.8→0.5 (금지어 회피 안정화)
    max_output_tokens=8192,   # 4500→8192 (한국어 토큰 여유)
    top_p=0.90,               # 0.95→0.90 (출력 안정화)
    top_k=40
)
```

**근거**: Agent C7 CRITICAL-01. 한국어 1음절 = 1-2토큰. 4-Block JSON 4500토큰 부족.

---

### 1.2 FIX-GEMINI-RETRY: 에러 타입별 재시도 로직

**파일**: `engines/comprehensive_script_generator.py` (line 1065-1068)

**현재**: bare `except Exception` → 즉시 fallback (재시도 0회)

**변경**:
```python
MAX_RETRIES = 3

for attempt in range(MAX_RETRIES):
    try:
        response = self.client.models.generate_content(...)
        response_text = response.text
        if response_text is None:
            raise ValueError("Gemini safety filter blocked response")
        response_text = response_text.strip()

        # block4 존재 확인
        if "block4" not in response_text:
            if attempt < MAX_RETRIES - 1:
                print(f"[Gemini] block4 누락, 재시도 {attempt+2}/{MAX_RETRIES}")
                continue
            raise ValueError("block4 missing after all retries")

        # JSON 파싱 + 금지어 검사
        ...
        break  # 성공 시 루프 탈출

    except (json.JSONDecodeError, ValueError) as e:
        if attempt < MAX_RETRIES - 1:
            print(f"[Gemini] 파싱 실패, 재시도 {attempt+2}/{MAX_RETRIES}")
            continue
        print(f"[Gemini] {MAX_RETRIES}회 실패, Fallback 전환")
        return self._generate_fallback(...)
    except Exception as e:
        print(f"[Gemini] 예외: {type(e).__name__}: {e}")
        return self._generate_fallback(...)
```

**근거**: Agent C7 CRITICAL-02. 60% block4 실패를 재시도로 5%로 줄임.

---

### 1.3 FIX-BANNED-SSOT: 금지어 Single Source of Truth

**파일 3개 동시 수정**:

#### 1.3.1 `sgrade_constants.py` (SSOT)
- `BANNED_WORDS_BY_CATEGORY` + `FORBIDDEN_MARKETING_CLAIMS`를 유일한 진실 원천으로 유지
- `get_all_banned_words() -> List[str]` 함수 추가 (flat list 반환)
- `get_all_banned_patterns() -> List[str]` 함수 추가 (regex list 반환)

#### 1.3.2 `comprehensive_script_generator.py`
- line 79-83의 `BANNED_WORDS` 삭제 → `sgrade_constants.get_all_banned_words()` 참조
- line 912-917의 Gemini 프롬프트 인라인 금지어 → `sgrade_constants` 참조하여 동적 생성
- `_sanitize_banned_from_segments()` (line 1613-1662):
  - FORBIDDEN_MARKETING_CLAIMS에 대한 `re.sub()` 기반 대체 추가
  - replacement_map에 regex 패턴 매핑 추가

#### 1.3.3 `script_validation_orchestrator.py`
- line 536-538의 `FORBIDDEN_PATTERNS_EXCEPTIONS` dict key 순회 버그 수정:
```python
# 현재 (버그): dict key를 regex로 사용
for exception in FORBIDDEN_PATTERNS_EXCEPTIONS:
    masked_text = re.sub(exception, ...)

# 수정: dict values를 flat하게 펼쳐서 순회
for patterns in FORBIDDEN_PATTERNS_EXCEPTIONS.values():
    for pattern in patterns:
        masked_text = re.sub(pattern, "***", masked_text)
```

**근거**: Agent C7 CRITICAL-04, CRITICAL-05, HIGH-02, HIGH-03.

---

### 1.4 FIX-PORT-INJECT: 기항지 강제 삽입

**파일**: `engines/comprehensive_script_generator.py`

**현재**: Hook에 40% 확률 랜덤 삽입 (line 693-696)

**변경**:
1. Hook 기항지 삽입 확률 40% → 100% (필수)
2. `_inject_port_keywords()` 메서드 신규 추가:
   - Trust 강제 삽입(`_inject_trust_elements`)과 동일 패턴
   - Block 2에 기항지명 필수 포함 확인
   - 없으면 Block 2 첫 번째 세그먼트에 강제 삽입

**근거**: Agent C7 CRITICAL-06. Trust에는 보정 로직 있지만 기항지에는 없음.

---

### 1.5 FIX-BANNED-SCORE: 채점 이중 덮어쓰기 수정

**파일**: `engines/script_validation_orchestrator.py` (line 224-238)

**현재**: banned_score와 forbidden_claims_score가 상호 배타적으로 덮어씀

**변경**: 두 점수를 누적 감점으로 통합
```python
banned_score = 10.0
banned_score -= len(found_banned) * 2.5  # 금지어당 -2.5점
banned_score -= len(forbidden_claims) * 3.0  # 허위수치당 -3점
banned_score = max(banned_score, 0.0)
```

**근거**: Agent C7 HIGH-06. 금지어 2개+허위수치 1개일 때 점수 역전 발생.

---

## Phase 2: 감정곡선 + Hook 재설계 (P1, 6시간)

### 2.1 감정곡선 재설계

**파일**: `engines/comprehensive_script_generator.py` EMOTION_SCORES (line 306-311)

**현재**:
```python
안심(0.40) → 공감(0.55) → 동경(0.75) → 확신(0.65)  # Block4 하락!
```

**변경** (도파민 롤러코스터):
```python
충격(0.75) → 낙하(0.35) → 상승(0.70) → PEAK(0.90)  # CTA직전 최고점
```

**EMOTION_RANGES 수정**:
```python
EMOTION_RANGES = {
    "block1": (0.65, 0.80),   # 충격/호기심 (안심→충격)
    "block2": (0.30, 0.45),   # 문제/공포 (공감→낙하)
    "block3": (0.60, 0.80),   # 해결/희망 (동경→상승)
    "block4": (0.85, 0.95),   # 확신 PEAK (확신→PEAK)
}
```

**근거**: Agent 감정설계 치명적 #1. Block4에서 감정 하락은 세일즈 킬러.

### 2.2 FEAR 감정곡선 개별화

**파일**: `engines/comprehensive_script_generator.py` FEAR_SCENARIOS (line 260-302)

**현재**: 7종 모두 `[0.3, 0.6, 0.8, 0.9]` 동일

**변경**:
| 유형 | 강도 | 곡선 |
|------|------|------|
| FEAR_SAFETY | 생존위협 | [0.50, 0.80, 0.90, 0.95] |
| FEAR_LANGUAGE | 생존위협 | [0.45, 0.75, 0.85, 0.95] |
| FEAR_HIDDEN_COST | 금전손실 | [0.40, 0.70, 0.85, 0.90] |
| FEAR_TIME_WASTE | 시간낭비 | [0.30, 0.60, 0.80, 0.90] |
| FEAR_CRUISE_PORT | 불편 | [0.35, 0.65, 0.80, 0.90] |
| FEAR_ONBOARD_SYSTEM | 정보부족 | [0.25, 0.55, 0.75, 0.85] |
| FEAR_INFO_GAP | 정보부족 | [0.20, 0.50, 0.70, 0.85] |

**근거**: Agent 감정설계 치명적 #4. 공포 강도에 따른 차별화 필요.

### 2.3 Hook 5-패턴 다변화

**파일**: `engines/comprehensive_script_generator.py` HOOK_TYPES (line 106-173)

**현재**: 30개 중 22개 "~아세요?" 패턴 (73%)

**목표 배분**:
| 패턴 | 비율 | 예시 |
|------|------|------|
| 역발상(Pattern Interrupt) | 25% (8개) | "크루즈 절대 타지 마세요" |
| 미완결(Open Loop) | 25% (8개) | "이 실수 때문에 50만원 날렸습니다" |
| 대비(Contrast) | 15% (4개) | "제주 3박 vs 크루즈 7박, 같은 가격" |
| 호기심(Curiosity) | 20% (6개) | "크루즈 회사가 절대 안 말하는 3가지" |
| 감정자극(Emotion) | 15% (4개) | "68세 선배가 눈물 흘린 이유" |

**근거**: Agent 감정설계 치명적 #2, Agent 마케팅 치명적 #1. 패턴 피로도 방지.

### 2.4 CTA 순서 변경 + 텍스트 개선

**현재**: urgency(2.5s) → action(2.5s) → trust(2.0s)

**변경**: trust(2.0s) → urgency(2.0s) → action(3.0s)

**근거**: Agent 감정설계 치명적 #3, Agent 마케팅 치명적 #2.
- 5060대는 신뢰 확인 먼저 → 긴급성 → 행동
- action에 3초: "프로필" 대신 구체적 안내 필요

### 2.5 Re-Hook 타이밍 조정 + 콘텐츠 연동

**현재**: Re-Hook1=13초, Re-Hook2=32초, Pop2=32.5초 (0.5초 충돌)

**변경**:
- Re-Hook 1: 13초 → **9초** (8-10초 이탈 지점 방어)
- Re-Hook 2: 32초 → **27초** (Pop2와 5초 간격 확보)
- Pop 3: 46.5초 → **42초** (CTA 시작 전에 배치)

**Re-Hook 텍스트**: Content Type별 동적 생성 (범용 → 콘텐츠 연동)

**근거**: Agent 감정설계 개선 #2. Re-Hook2와 Pop2 충돌 해소.

---

## Phase 3: Config-구현 괴리 해소 (P1, 8시간)

### 3.1 BGMMatcher 연동 (P0)

**파일**: `pipeline_render/audio_mixer.py`

**현재**: `random.choice(bgm_files)` (BGMMatcher 미사용)

**변경**:
- `from engines.bgm_matcher import BGMMatcher` 추가
- `mix_audio()`에서 BGMMatcher.select_bgm() 호출
- content_type 기반 BGM 선택

### 3.2 색보정 엔진 구현 (P1)

**파일**: `engines/ffmpeg_pipeline.py` 또는 신규 `engines/color_correction.py`

**구현**: FFmpeg `eq` 필터로 세그먼트별 밝기/채도/대비 자동 조정
- SENIOR_FRIENDLY 프리셋: brightness=+0.05, saturation=1.15, contrast=0.95

### 3.3 자막 배경 구현 (P1)

**파일**: `engines/subtitle_image_renderer.py`

**현재**: `subtitle_bg_enabled=True`이지만 배경 렌더링 코드 없음

**변경**: 반투명 검정 rounded rect 배경 추가

### 3.4 LUFS 정규화 구현 (P2)

**파일**: `engines/ffmpeg_pipeline.py`

**구현**: FFmpeg `loudnorm` 2-pass 필터로 -14 LUFS 정규화

### 3.5 인터리빙 강제 적용 (P2)

**파일**: `pipeline_render/visual_loader.py`

**구현**: Config의 interleave 설정을 실제 에셋 타입 선택에 강제 적용

### 3.6 Intro SFX 연동 (P2)

**파일**: `pipeline_render/audio_mixer.py`

**구현**: intro_sfx 로딩 + 0초 지점 배치

---

## Phase 4: S등급 채점 시스템 정상화 (P1, 3시간)

### 4.1 자기채점 제거

**파일**: `engines/comprehensive_script_generator.py` `_calculate_s_grade_score()` (line 1691-1776)

**현재**: Pop/ReHook/CTA에 무조건 30점 부여

**변경**:
- 생성기 자체 채점 제거 (또는 예비 점수로만 사용)
- 생성 직후 `ScriptValidationOrchestrator.validate()` 호출하여 단일 채점

### 4.2 검증기 호출 통합

**파일**: `engines/comprehensive_script_generator.py` `generate_script()` 끝부분

```python
# 생성 완료 후 실제 검증
from engines.script_validation_orchestrator import validate_script
validation_result = validate_script(script_output)
script_output['validated_score'] = validation_result.total_score
script_output['s_grade'] = validation_result.grade
```

---

## Phase 5: 보안 즉시 조치 (P0, 1시간)

### 5.1 Gemini API 타임아웃 추가

**파일**: `engines/comprehensive_script_generator.py`

```python
# Gemini 클라이언트에 타임아웃 설정
import httpx
self.client = genai.Client(
    api_key=api_key,
    http_options={"timeout": 60}  # 60초 타임아웃
)
```

### 5.2 response.text None 방어

**파일**: `engines/comprehensive_script_generator.py` (line 1026)

```python
if response.text is None:
    raise ValueError("Gemini response blocked by safety filter")
response_text = response.text.strip()
```

---

## 수정 파일 총 목록

| # | 파일 | Phase | 변경 내용 |
|---|------|-------|-----------|
| 1 | `engines/comprehensive_script_generator.py` | 1,2,4 | tokens+retry+SSOT+port+감정곡선+Hook+CTA+ReHook+채점 |
| 2 | `engines/sgrade_constants.py` | 1 | get_all_banned_words/patterns() 추가 |
| 3 | `engines/script_validation_orchestrator.py` | 1 | FORBIDDEN_PATTERNS_EXCEPTIONS 버그 + banned_score 수정 |
| 4 | `pipeline_render/audio_mixer.py` | 3 | BGMMatcher 연동 + Intro SFX |
| 5 | `engines/subtitle_image_renderer.py` | 3 | 자막 배경 구현 |
| 6 | `engines/ffmpeg_pipeline.py` | 3 | 색보정 + LUFS 정규화 |
| 7 | `pipeline_render/visual_loader.py` | 3 | 인터리빙 강제 + 중복 방지 |

---

## 우선순위별 실행 로드맵

| 순서 | 작업 | 시간 | 예상 효과 |
|------|------|------|-----------|
| **1** | max_output_tokens 8192 + temperature 0.5 | 10분 | block4 실패 60%→5% |
| **2** | response.text None 방어 + 타임아웃 | 10분 | 안정성 |
| **3** | Gemini 재시도 로직 (3회) | 30분 | 성공률 95%+ |
| **4** | 기항지 강제 삽입 100% | 20분 | port_1plus 100% PASS |
| **5** | 금지어 SSOT 통합 | 1시간 | banned_zero 안정 |
| **6** | FORBIDDEN_PATTERNS_EXCEPTIONS 버그 | 10분 | 검증가능수치 오탐 방지 |
| **7** | banned_score 누적 감점 수정 | 10분 | 채점 정확도 |
| **8** | 감정곡선 재설계 | 30분 | 완주율 +15%p |
| **9** | Hook 5-패턴 다변화 | 2시간 | 완주율 +12%p |
| **10** | CTA 순서 변경 | 30분 | 전환율 +300% |
| **11** | BGMMatcher 연동 | 1시간 | BGM 품질 |
| **12** | 자막 배경 구현 | 30분 | 가독성 |
| **13** | S등급 자기채점 제거 + 검증기 통합 | 1시간 | 지표 신뢰성 |

**총 예상 시간: 8-10시간**
**예상 S등급 달성률: 80%+ (Gemini 모드)**
**예상 완주율: 현재 25-30% → 40-50%**

---

## 리스크 평가

| 변경 | 리스크 | 완화 |
|------|--------|------|
| max_output_tokens 8192 | 비용 1.8x 증가 | 성공률 12x 향상으로 상쇄 |
| temperature 0.5 | 창의성 감소 | 안정성 우선, 추후 0.6으로 조정 |
| 감정곡선 변경 | 기존 검증 무효 | 변경 후 10회 검증 필수 |
| Hook 재작성 | friendly_tone 위반 가능 | 작성 후 전수 검증 |
| CTA 순서 | config 영향 | CTA config 동시 수정 |

---

**버전**: WO v7.0 (6-Agent Unified Critical Fix)
**상태**: 작업 대기 (사용자 승인 필요)
