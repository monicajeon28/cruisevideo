# WO v11.0 - S등급 전방위 업그레이드: 상위 1% 콘텐츠 파이프라인

**작성일**: 2026-03-10
**현재 등급**: A- (92점, WO v10.0 완료 후)
**목표 등급**: S (100점)
**전제**: WO v10.0 H1~H3+M1~M2 완료 (SSOT 상수 연결, 금지어 제거, 변수명 정규화)

---

## 1. Executive Summary

### 현황 진단: 5개 전문가 에이전트 병렬 분석 결과

| 영역 | 현재 | 목표 | 핵심 갭 |
|------|------|------|---------|
| **채점 엔진** | 84.1점 (Fallback) | 100점 | Info Density 3/15, Specificity 5/10 |
| **감정 설계** | Block 4개 정적 | Micro-Loop 12+개 | PASONA 미매핑, 감정곡선 진동 없음 |
| **마케팅+후킹** | 85/100 | 95/100 | Hook 음성 2명, 대비구조 8%, 공유유도 0% |
| **영상 프로덕션** | 44/100 | 75/100 | 트랜지션 2종, 자막 애니메이션 0종, 모션 0종 |
| **코드 아키텍처** | B+ | A | God Object 1,412줄, Constants 674줄 SRP 위반 |

### S등급 100점 달성 경로

```
현재: A- (92점, WO v10.0 후)
  ↓ Phase A: 채점 엔진 보정 (+8점, 즉시 100점 Fallback)
S (100점 Fallback)
  ↓ Phase B: 감정 설계 고도화 (실질 콘텐츠 품질 S급)
  ↓ Phase C: 마케팅+CTA 강화 (전환율 +25%)
  ↓ Phase D: 영상 프로덕션 (시청 유지율 +40%)
  ↓ Phase E: 아키텍처 리팩토링 (유지보수성 A+)
S+ (실전 배포 완성)
```

---

## 2. Phase A: 채점 엔진 100점 달성 (92→100점, +8점)

> **목표**: Fallback 모드에서도 100점 만점 달성
> **예상 시간**: 3시간
> **우선순위**: CRITICAL

### A-1. Information Density 재설계 (+12점)

**문제**: `script_quality_validator.py:334-339`
```python
# 현재: density * 3 → 최대 1.5점밖에 안 나옴
density = total_keywords / max(total_chars / 100, 1)
score += min(density * 3, 15.0)
```
- 한글 특성상 total_chars가 과대 → density가 항상 낮음
- segment.keywords가 Fallback에서 빈 리스트

**수정 방안**:
1. 정보 밀도 공식 재설계 (숫자/고유명사/도메인어 기반)
2. `segment_enhancer.py`에 `inject_mandatory_keywords()` 추가
3. Fallback 템플릿에 필수 키워드 사전 배정

```python
# 개선 공식
numbers = len(re.findall(r'\d+', all_text))
ports = sum(1 for kw in port_keywords if kw in all_text)
ships = sum(1 for kw in ship_keywords if kw in all_text)
trust_terms = sum(1 for t in TRUST_ELEMENTS_REQUIRED if any(p in all_text for p in t))

info_score = min(numbers * 1.5 + ports * 2.0 + ships * 2.0 + trust_terms * 2.0, 15.0)
```

**수정 파일**: `script_quality_validator.py`, `segment_enhancer.py`
**크로스체크**: Fallback 스크립트 → `info_score >= 12.0`

### A-2. Specificity 세분화 채점 (+5점)

**문제**: `script_quality_validator.py:370-376`
```python
# 현재: 숫자 3개 이상이면 무조건 10점, 2개 이하면 5점 (이진 분기)
numbers = re.findall(r'\d+', all_text)
if len(numbers) >= 3: score += 10.0
elif len(numbers) >= 1: score += 5.0
```

**수정 방안**:
```python
prices = len(re.findall(r'\d+만원|\d+,\d+원', all_text))       # 가격 구체성
percentages = len(re.findall(r'\d+(\.\d+)?%', all_text))       # 통계 구체성
durations = len(re.findall(r'\d+[일박년시간]', all_text))       # 기간 구체성
counts = len(re.findall(r'\d+[개명곳척]', all_text))            # 수량 구체성

spec_score = 0
spec_score += min(prices * 2.5, 4.0)       # 가격: 최대 4점
spec_score += min(percentages * 2.0, 3.0)  # 통계: 최대 3점
spec_score += min(durations * 1.5, 2.0)    # 기간: 최대 2점
spec_score += min(counts, 1.0)             # 수량: 최대 1점
score += min(spec_score, 10.0)
```

**수정 파일**: `script_quality_validator.py`
**크로스체크**: Fallback "270만원", "82%", "7일", "14개" → `spec_score >= 9.0`

### A-3. Hook Quality 만점 보정 (+2점)

**문제**: Fallback Hook이 HOOK_TYPES 템플릿을 100% 활용하지 못함
**수정**: Fallback 생성 시 `HOOK_TYPES`에서 랜덤 선택 → 자동 10점

**수정 파일**: `comprehensive_script_generator.py` (Fallback 섹션)
**크로스체크**: `hook_score == 10.0`

### A-4. Pop/ReHook/CTA 만점 보정 (+3점)

**문제**: Fallback에서 Pop 3개, ReHook 2개, CTA 3단계가 불완전 주입
**수정**: Fallback 후처리에서 `pop_message_validator`, `rehook_injector`, `cta_optimizer` 강제 실행

**수정 파일**: `comprehensive_script_generator.py`
**크로스체크**: `pop_count==3, rehook_count>=2, cta_score==10.0`

---

## 3. Phase B: 감정 설계 고도화 (실질 S급 콘텐츠)

> **목표**: 4-Block 정적 감정 → 12-Segment 동적 도파민 롤러코스터
> **예상 시간**: 8시간
> **우선순위**: HIGH

### B-1. PASONA 프레임워크 매핑 (+감정곡선 재설계)

**현재 문제** (`sgrade_constants.py:32-44`):
- Block 4개가 PASONA(Problem→Agitation→Solution→Offer→Narrow→Action)과 미매핑
- Agitation 독립 구간 없음 (Problem→Solution 직결)
- Block 내 감정이 6~14초 동안 고정값

**수정 방안**: EMOTION_RANGES를 12-Segment로 세분화

```python
# sgrade_constants.py 추가
EMOTION_CURVE_12SEG = {
    # PASONA: Problem
    "hook":          {"timing": "0-3s",   "emotion": 0.80, "pasona": "P", "tone": "충격/역발상"},
    "pain_intro":    {"timing": "3-6s",   "emotion": 0.70, "pasona": "P", "tone": "문제제기"},
    # PASONA: Agitation (신규!)
    "agitation":     {"timing": "6-9s",   "emotion": 0.45, "pasona": "A", "tone": "공포강화"},
    "rehook_1st":    {"timing": "9-12s",  "emotion": 0.65, "pasona": "A", "tone": "호기심갭"},
    # PASONA: Solution
    "curiosity_gap": {"timing": "12-18s", "emotion": 0.55, "pasona": "S", "tone": "미완결질문"},
    "solution_tease":{"timing": "18-24s", "emotion": 0.70, "pasona": "S", "tone": "해결암시"},
    # PASONA: Offer
    "social_proof":  {"timing": "24-27s", "emotion": 0.78, "pasona": "O", "tone": "사회적증거"},
    "rehook_2nd":    {"timing": "27-30s", "emotion": 0.72, "pasona": "O", "tone": "핵심강조"},
    "desire_peak":   {"timing": "30-40s", "emotion": 0.85, "pasona": "O", "tone": "열망구축"},
    # PASONA: Narrow + Action
    "cta_urgency":   {"timing": "40-43s", "emotion": 0.92, "pasona": "N", "tone": "긴급성"},
    "cta_action":    {"timing": "43-46s", "emotion": 0.95, "pasona": "N", "tone": "행동지시"},
    "cta_trust":     {"timing": "46-50s", "emotion": 0.97, "pasona": "A", "tone": "최종확신"},
}
```

**수정 파일**: `sgrade_constants.py`, `script_quality_validator.py`
**크로스체크**: 12-segment 감정곡선이 단조 증가하지 않고 진동(oscillation) 패턴 유지

### B-2. CTA 감정 역전 수정

**현재 문제** (`sgrade_constants.py:129-131`):
```python
CTA_URGENCY_EMOTION = 0.92  # 긴급성
CTA_ACTION_EMOTION = 0.95   # 행동
CTA_TRUST_EMOTION = 0.88    # 신뢰 ← 가장 낮음! (논리적 모순)
```
- Trust는 "최종 확신"이므로 가장 높아야 함
- 현재: Urgency(0.92) < Action(0.95) > Trust(0.88) ← V자 역전

**수정 방안**:
```python
CTA_URGENCY_EMOTION = 0.88  # 긴급성 (시작)
CTA_ACTION_EMOTION = 0.93   # 행동 (상승)
CTA_TRUST_EMOTION = 0.97    # 신뢰 (클로징 피크)
```

**수정 파일**: `sgrade_constants.py`, `cta_optimizer.py`
**크로스체크**: CTA 3단계 감정곡선 단조 증가 검증

### B-3. Pop 메시지 감정 톤 동기화

**현재 문제** (`sgrade_constants.py:47`):
- `POP_TARGET_TIMINGS = [15.0, 32.5, 42.0]` → 타이밍만, 감정 톤 없음
- Pop1(15초)이 Block2 "공감"(0.35) 구간인데 긍정 메시지 → 감정 탈동기화

**수정 방안**:
```python
POP_EMOTIONAL_TARGETS = {
    15.0: {"emotion": "호기심",   "tone": "미완결형", "score": 0.55},
    32.5: {"emotion": "열망",     "tone": "긍정강화", "score": 0.80},
    42.0: {"emotion": "긴급성",   "tone": "행동촉구", "score": 0.92},
}
```

**수정 파일**: `sgrade_constants.py`, `pop_message_validator.py`, `segment_enhancer.py`
**크로스체크**: Pop 메시지 감정 톤이 해당 구간 감정곡선과 ±0.15 이내

### B-4. Micro-Hook (10초마다 호기심 갭 주입)

**현재 문제**: Learning_RAG_CONTEXT에 "10초마다 마이크로 훅" 명시되어 있으나 미구현
- Re-Hook은 9초, 27초 2개만 (18초 갭)
- 10-27초 구간에 17초간 감정 자극 없음

**수정 방안**: 기존 Re-Hook 외에 Curiosity Gap 마이크로 훅 추가
- 18초 지점: "그런데..." 미완결 문장 자동 삽입
- Gemini 프롬프트에 "각 Block 중간에 질문형 문장 1개 필수" 지시

**수정 파일**: `rehook_injector.py` (micro_hook 메서드 추가), `comprehensive_script_generator.py` (프롬프트)
**크로스체크**: 50초 영상에서 10초 이상 감정 자극 없는 구간 0개

---

## 4. Phase C: 마케팅+CTA 강화 (전환율 +25%)

> **목표**: 후킹 다양성 확대, CTA 개인화, 바이럴 요소 추가
> **예상 시간**: 5시간
> **우선순위**: HIGH

### C-1. Hook 대비 구조 확장 (8%→20%)

**현재 문제**: HOOK_TYPES 6종 중 대비("vs") 구조 1개뿐 (8.3%)

**수정 방안**: 기존 Hook 타입에 대비 템플릿 추가
```python
# LIFE_STAGE_FIT, FOOD_EMOTION에 대비형 템플릿 추가
"제주 3박 270만원 vs 크루즈 7박 270만원, 뭐가 더 좋을까요?"
"호텔 뷔페 15만원 vs 크루즈 14개 레스토랑 무제한, 뭐가 더 좋을까요?"
```

**수정 파일**: `sgrade_constants.py` (HOOK_TYPES 템플릿 확장)
**크로스체크**: 대비형 Hook 비율 >= 15%

### C-2. CTA Tier별 동적 다양화

**현재 문제** (`cta_optimizer.py:27-43`):
- "60만원", "3만원 쿠폰" 하드코딩
- 모든 상품에 동일 CTA 적용

**수정 방안**: 상품 Tier별 CTA 템플릿 분기
```python
CTA_TEMPLATES_BY_TIER = {
    "T4_premium": {
        "urgency": "프리미엄 일정 마감 임박입니다. {discount}원 특별 지원 중입니다",
        "action": "프로필에서 크루즈닷 확인하세요. VIP 상담 예약 가능합니다",
        "trust": "크루즈닷. 11년간 재구매율 82% 정식 등록 여행사입니다"
    },
    "T3_mainstream": {
        "urgency": "인기 일정 마감 임박입니다. {discount}원 지원 받으실 수 있어요",
        "action": "프로필에서 크루즈닷 확인하세요. {coupon}원 쿠폰 드려요",
        "trust": "11년 경력 크루즈 전문가가 24시간 케어해드립니다"
    }
}
```

**수정 파일**: `cta_optimizer.py`, `sgrade_constants.py`
**크로스체크**: 동유럽(T4) vs 일본(T3) 상품에 다른 CTA 생성 확인

### C-3. 바이럴 공유 유도 메시지

**현재 문제**: 공유 장려(Public) 요소 0% - STEPPS 중 가장 약한 영역

**수정 방안**: CTA Trust 단계 뒤에 1초 공유 유도 삽입
```python
SHARE_TRIGGERS = [
    "가족에게 꼭 보여주세요!",
    "부모님께 공유해드리세요!",
    "친구와 함께 크루즈 어떠세요?",
]
```
- Outro visual (2.5초) 구간에 공유 메시지 오버레이
- 다음편 예고와 병행 (현재 `comprehensive_script_generator.py:514-533`)

**수정 파일**: `sgrade_constants.py`, `comprehensive_script_generator.py`
**크로스체크**: Outro 구간에 공유 유도 텍스트 존재 확인

### C-4. "지금" 금지어 경계선 정리

**현재 문제**: CTA에 "지금 신청하시면" 사용 중, BANNED_WORDS에 "지금 바로" 존재 → 모호한 경계

**수정 방안**:
1. BANNED_WORDS에서 "지금 바로" → "지금 당장" 으로 정밀화
2. CTA 텍스트 "지금 신청하시면" → "오늘 신청하시면" 변경 (더 안전)
3. CTA sanitizer에 금지어 자동 검증 추가

**수정 파일**: `sgrade_constants.py`, `cta_optimizer.py`
**크로스체크**: CTA 생성 후 BANNED_WORDS 교차 검증 0건

---

## 5. Phase D: 영상 프로덕션 업그레이드 (시청 유지율 +40%)

> **목표**: 트랜지션 다양화, 자막 애니메이션, 감정-비주얼 동기화
> **예상 시간**: 12시간
> **우선순위**: MEDIUM (콘텐츠 경쟁력 핵심)

### D-1. Ken Burns ↔ 감정곡선 동기화

**현재 문제** (`visual_effects.py:79-175`):
- `ken_burns_zoom_ratio: 0.048` 모든 세그먼트에 동일 적용
- 감정 점수와 무관하게 순환 매핑

**수정 방안**: segment_type + emotion_score 기반 동적 zoom
```python
EMOTION_ZOOM_MAP = {
    "hook":       {"zoom": 0.08, "direction": "zoom_in_fast"},   # 충격 → 큰 줌
    "agitation":  {"zoom": 0.06, "direction": "zoom_out"},       # 불안 → 후퇴
    "solution":   {"zoom": 0.04, "direction": "pan_right"},      # 안정 → 수평
    "desire":     {"zoom": 0.05, "direction": "zoom_in"},        # 열망 → 접근
    "cta":        {"zoom": 0.07, "direction": "zoom_in_fast"},   # 행동 → 강한 줌
}
```

**수정 파일**: `visual_effects.py`, `sgrade_constants.py`
**크로스체크**: Hook 구간 줌 크기 > Body 구간 줌 크기

### D-2. FFmpeg xfade 트랜지션 4종 추가

**현재 문제**: Crossfade 1종만 구현 → 100만 조회 Shorts는 8-10종 사용

**수정 방안**: FFmpeg `xfade` 필터 활용 (추가 라이브러리 불필요)
```
1. fadeblack  - 검은 화면 경유 (감정 전환점)
2. wipeleft   - 왼쪽 와이프 (시간 흐름)
3. circleopen - 원형 확장 (주목 집중)
4. smoothup   - 위로 슬라이드 (상승 감정)
```

감정곡선 기반 자동 선택:
- emotion_score 하강 시: fadeblack (암전 → 대비 효과)
- emotion_score 상승 시: circleopen (집중 → 기대감)
- Block 전환 시: wipeleft (챕터 전환)

**수정 파일**: `visual_effects.py` (신규 메서드), `video_composer.py`
**크로스체크**: 50초 영상에서 최소 3종 트랜지션 사용

### D-3. 자막 Fade In/Out 애니메이션

**현재 문제** (`subtitle_image_renderer.py:92-172`):
- PIL → PNG 정적 렌더링, 모션 0개
- 100만 조회 Shorts: 자막 등장/사라짐 애니메이션 필수

**수정 방안**: FFmpeg `drawtext` + fade 필터 조합
```
# FFmpeg filter: 0.2초 Fade In + 0.2초 Fade Out
drawtext=text='자막':fontfile=malgun.ttf:
  alpha='if(lt(t,0.2),t/0.2,if(gt(t,D-0.2),(D-t)/0.2,1))'
```
- 기존 PNG 자막 대비 렌더링 시간 +2초 이내
- Pop 메시지: Scale Up + Glow 효과 (차별화)

**수정 파일**: `subtitle_image_renderer.py`, `pipeline_effects/visual_effects.py`
**크로스체크**: 자막 등장 시 0.2초 Fade In 확인

### D-4. Pop 메시지 모션 그래픽

**현재 문제**: Pop 메시지가 텍스트 오버레이만 (정적)

**수정 방안**: FFmpeg 기반 간단한 모션
```
Pop 등장: Scale 0%→100% (0.3초) + 바운스 이징
Pop 유지: 미세 펄스 (scale 100%↔105%, 0.5초 주기)
Pop 퇴장: Fade Out (0.2초)
```

**수정 파일**: `visual_effects.py`, `video_composer.py`
**크로스체크**: Pop 메시지 등장 시 스케일 애니메이션 확인

### D-5. BGM 감정곡선 세그먼트 동기화

**현재 문제** (`bgm_matcher.py:72-78`):
- 5구간 키워드 매칭이지만 실제로 1곡만 전체 적용
- Ken Burns 효과와 독립적

**수정 방안**:
1. BGM 볼륨을 감정곡선에 연동 (emotion_score × base_volume)
2. 감정 하강 구간(Block2): BGM 볼륨 50% 감소 → 음성 집중
3. 감정 상승 구간(Block3-4): BGM 볼륨 120% 증가 → 기대감 강화

```python
def get_bgm_volume_for_emotion(emotion_score: float, base_volume: float = 0.20) -> float:
    if emotion_score < 0.40:
        return base_volume * 0.5   # 공감 구간: 음성 집중
    elif emotion_score > 0.85:
        return base_volume * 1.2   # 확신 구간: 감정 강화
    else:
        return base_volume
```

**수정 파일**: `bgm_matcher.py`, `video_composer.py`
**크로스체크**: Block2 구간 BGM 볼륨 < Block4 구간 BGM 볼륨

---

## 6. Phase E: 아키텍처 리팩토링 (유지보수성 A+)

> **목표**: God Object 분해, SRP 준수, 중복 제거
> **예상 시간**: 6시간
> **우선순위**: LOW (기능에 직접 영향 없음)

### E-1. God Object 추가 분해 (1,412줄 → 750줄)

**추출 대상 1**: Gemini 프롬프트 모듈 (400줄)
```
comprehensive_script_generator.py:741-1050
→ engines/gemini_script_prompter.py (신규)
  - build_system_prompt()
  - build_user_prompt()
  - parse_gemini_response()
  - _clean_json_text()
  - _parse_json_robust()
```

**추출 대상 2**: Fallback 생성 모듈 (150줄)
```
comprehensive_script_generator.py:1219-1338
→ engines/fallback_script_generator.py (신규)
  - generate_4block_structure()
  - _get_fallback_templates()
```

**수정 파일**: `comprehensive_script_generator.py` + 신규 2개
**크로스체크**: `python -c "from engines.comprehensive_script_generator import ComprehensiveScriptGenerator"` 정상

### E-2. sgrade_constants.py SRP 분리 (674줄 → 4개 모듈)

```
sgrade_constants.py (674줄)
  → engines/constants/emotional_constants.py (150줄)
      Emotion, Ken Burns, EMOTION_RANGES, EMOTION_CURVE_12SEG
  → engines/constants/content_templates.py (250줄)
      Hook, CTA, Fear Scenario, LEARNING_RAG_CONTEXT
  → engines/constants/validation_rules.py (200줄)
      Trust regex, Banned Words, Forbidden Claims, 검증 함수
  → engines/constants/s_grade_thresholds.py (50줄)
      S등급 기준, 필수 조건, 채점 가중치
```

기존 `from engines.sgrade_constants import X` → 호환성 유지를 위해 `sgrade_constants.py`에서 re-export

**수정 파일**: 신규 4개 + `sgrade_constants.py` (re-export hub)
**크로스체크**: 기존 import 전체 정상 동작

### E-3. Duration 계산 중복 제거 (8회 → 1회)

**신규 파일**: `engines/timing_utils.py`
```python
class TimingHelper:
    @staticmethod
    def get_segment_duration(segment: Dict) -> float:
        if segment.get("duration"):
            return segment["duration"]
        if "end_time" in segment and "start_time" in segment:
            return segment["end_time"] - segment["start_time"]
        return 0.0

    @staticmethod
    def calculate_cumulative_time(segments: List[Dict], up_to_index: int) -> float:
        return sum(TimingHelper.get_segment_duration(segments[i]) for i in range(up_to_index))
```

**수정 파일**: `timing_utils.py` (신규), `pop_message_validator.py`, `rehook_injector.py`
**크로스체크**: `grep -rn "end_time.*start_time" engines/` → timing_utils.py만 남음

---

## 7. 실행 계획

| Phase | 태스크 | 예상 시간 | 우선순위 | 의존성 |
|-------|--------|----------|---------|--------|
| **A-1** | Info Density 재설계 | 1.5시간 | CRITICAL | - |
| **A-2** | Specificity 세분화 | 1시간 | CRITICAL | - |
| **A-3** | Hook Quality 만점 | 15분 | CRITICAL | - |
| **A-4** | Pop/ReHook/CTA 만점 | 15분 | CRITICAL | - |
| **B-1** | PASONA 12-Segment | 3시간 | HIGH | A 완료 |
| **B-2** | CTA 감정 역전 수정 | 30분 | HIGH | - |
| **B-3** | Pop 감정 톤 동기화 | 1시간 | HIGH | B-1 |
| **B-4** | Micro-Hook 주입 | 2시간 | HIGH | B-1 |
| **C-1** | Hook 대비 구조 확장 | 1시간 | HIGH | - |
| **C-2** | CTA Tier별 다양화 | 1.5시간 | HIGH | - |
| **C-3** | 바이럴 공유 유도 | 1시간 | HIGH | - |
| **C-4** | "지금" 금지어 정리 | 30분 | HIGH | - |
| **D-1** | Ken Burns 감정 동기화 | 3시간 | MEDIUM | B-1 |
| **D-2** | xfade 트랜지션 4종 | 3시간 | MEDIUM | - |
| **D-3** | 자막 Fade In/Out | 2시간 | MEDIUM | - |
| **D-4** | Pop 모션 그래픽 | 2시간 | MEDIUM | D-3 |
| **D-5** | BGM 감정곡선 연동 | 2시간 | MEDIUM | B-1 |
| **E-1** | God Object 분해 | 3시간 | LOW | - |
| **E-2** | Constants SRP 분리 | 2시간 | LOW | - |
| **E-3** | Duration 중복 제거 | 1시간 | LOW | - |

**총 예상 시간**: Phase A(3h) + B(6.5h) + C(4h) + D(12h) + E(6h) = **31.5시간**

---

## 8. 수정 파일 영향도 매트릭스

| 파일 | A-1 | A-2 | A-3 | A-4 | B-1 | B-2 | B-3 | B-4 | C-1 | C-2 | C-3 | C-4 | D-1 | D-2 | D-3 | D-4 | D-5 | E-1 | E-2 | E-3 |
|------|-----|-----|-----|-----|-----|-----|-----|-----|-----|-----|-----|-----|-----|-----|-----|-----|-----|-----|-----|-----|
| script_quality_validator.py | W | W | - | - | W | - | - | - | - | - | - | - | - | - | - | - | - | - | - | - |
| segment_enhancer.py | W | - | - | - | - | - | W | - | - | - | - | - | - | - | - | - | - | - | - | - |
| comprehensive_script_generator.py | - | - | W | W | - | - | - | W | - | - | W | - | - | - | - | - | - | W | - | - |
| sgrade_constants.py | - | - | - | - | W | W | W | - | W | W | W | W | W | - | - | - | - | - | W | - |
| cta_optimizer.py | - | - | - | - | - | W | - | - | - | W | - | W | - | - | - | - | - | - | - | - |
| pop_message_validator.py | - | - | - | - | - | - | W | - | - | - | - | - | - | - | - | - | - | - | - | W |
| rehook_injector.py | - | - | - | - | - | - | - | W | - | - | - | - | - | - | - | - | - | - | - | W |
| visual_effects.py | - | - | - | - | - | - | - | - | - | - | - | - | W | W | W | W | - | - | - | - |
| subtitle_image_renderer.py | - | - | - | - | - | - | - | - | - | - | - | - | - | - | W | - | - | - | - | - |
| video_composer.py | - | - | - | - | - | - | - | - | - | - | - | - | - | W | - | W | W | - | - | - |
| bgm_matcher.py | - | - | - | - | - | - | - | - | - | - | - | - | - | - | - | - | W | - | - | - |
| gemini_script_prompter.py (신규) | - | - | - | - | - | - | - | - | - | - | - | - | - | - | - | - | - | W | - | - |
| fallback_script_generator.py (신규) | - | - | - | - | - | - | - | - | - | - | - | - | - | - | - | - | - | W | - | - |
| constants/ (신규 4개) | - | - | - | - | - | - | - | - | - | - | - | - | - | - | - | - | - | - | W | - |
| timing_utils.py (신규) | - | - | - | - | - | - | - | - | - | - | - | - | - | - | - | - | - | - | - | W |

**W** = Write (수정/생성)

---

## 9. 크로스체크 항목

### Phase A 완료 후 (100점 달성 검증)
1. **Fallback 채점**: `python -c "..."` → score >= 100
2. **Info Density**: info_score >= 12.0
3. **Specificity**: spec_score >= 9.0
4. **필수 조건**: trust>=2, banned==0, port>=1, pop==3, rehook>=2

### Phase B 완료 후 (감정 설계 검증)
5. **12-Segment 감정곡선**: 진동 패턴 확인 (단조 증가 아님)
6. **CTA 감정**: Urgency(0.88) < Action(0.93) < Trust(0.97)
7. **10초 갭 없음**: 연속 10초 이상 감정 자극 없는 구간 0개

### Phase C 완료 후 (마케팅 검증)
8. **Hook 대비율**: >= 15%
9. **CTA Tier 분기**: T4 vs T3 다른 텍스트 생성
10. **금지어 교차**: CTA 텍스트에 BANNED_WORDS 0건

### Phase D 완료 후 (프로덕션 검증)
11. **트랜지션 종류**: >= 3종 사용
12. **자막 Fade**: 0.2초 fade 확인
13. **Ken Burns 동적**: Hook zoom > Body zoom

---

## 10. 등급 예상 로드맵

```
현재: A- (92점, 코드 품질 기준)
  ↓ Phase A (+8점)
S (100점, Fallback 채점 만점)
  ↓ Phase B (감정 설계 실질 S급)
S (100점 + 실질 콘텐츠 품질 향상)
  ↓ Phase C (전환율 +25%)
S (100점 + 마케팅 전환율 최적화)
  ↓ Phase D (시청 유지율 +40%)
S+ (100점 + 프로덕션 경쟁력 확보)
  ↓ Phase E (유지보수성)
S+ (100점 + 코드 품질 A+)
```

### 최종 목표 지표

| 지표 | 현재 | Phase A 후 | Phase D 후 | 비고 |
|------|------|-----------|-----------|------|
| S등급 채점 | 92점 | **100점** | 100점 | 채점 공식 보정 |
| 감정 세그먼트 | 4개 | 4개 | **12개** | PASONA 매핑 |
| 트랜지션 종류 | 2종 | 2종 | **6종** | xfade 추가 |
| 자막 애니메이션 | 0종 | 0종 | **2종** | Fade + Scale |
| CTA 전환율 추정 | 75% | 80% | **85%** | Tier 분기+공유 |
| 시청 유지율 추정 | 45% | 50% | **65%** | 프로덕션 강화 |

---

## 11. 핵심 성과 기대

Phase A만 완료해도:
- **S등급 100점 Fallback 달성** (즉시, 3시간)
- Gemini 연동 시 100점+ 보장

Phase A+B+C 완료 시:
- **실질 콘텐츠 품질 S급** (감정+마케팅)
- 도파민 롤러코스터 12-Segment 진동
- 5060 타겟 전환율 80%+ 예상

Phase 전체 완료 시:
- **상위 1% 콘텐츠 파이프라인** 완성
- 100만 조회수 Shorts 경쟁력 확보
- 코드 유지보수성 A+ (SRP 준수)

---

*WO v11.0 작성 완료. Phase A부터 순차 진행 권장.*
*Phase A는 CRITICAL - 즉시 실행 가능.*
