# Sprint S2 작업지시서: 핑거프린트 + 다양성 + 측정
# WO v8.0 - CruiseDot YouTube Shorts 파이프라인

**작성일**: 2026-03-10
**문서 버전**: 8.0 (Sprint S2 전용)
**선행 완료**: WO v6.0 Phase 1-6, WO v7.0 SSOT, Sprint S0+S1
**예상 작업 시간**: 18시간 (3일)
**목표**: S등급 달성률 80%→90%+, 알고리즘 감지 회피, 데이터 기반 최적화

---

## Executive Summary

Sprint S1(비주얼+심리학)까지 완료 후, **3가지 구조적 한계** 발견:

| # | 한계 | 현재 | 목표 | 예상 효과 |
|---|------|------|------|-----------|
| 1 | 영상 핑거프린트 동일성 | 밝기/채도/피치 고정 | 편별 고유화 | 알고리즘 감지 회피 |
| 2 | 콘텐츠 구조 단조로움 | 순차형 1종만 | 3종 내러티브 + Re-Hook 20개 | 시청자 피로도 ↓40% |
| 3 | 성과 측정 부재 | 로그만 기록 | 트래킹+주간보고서+감정곡선채점 | 데이터 기반 최적화 |

---

## Phase S2-A: 핑거프린트 분산 (P0, 6시간)

### A-1: 밝기/채도 랜덤 변이 (2시간)

**문제**: 모든 영상이 동일한 SENIOR_FRIENDLY 색보정 → 유튜브 핑거프린트 감지 위험

**현재 코드 상태**:
- `engines/color_correction.py`: ColorCorrectionPreset + ColorCorrectionSettings 존재
  - brightness=1.05, contrast=1.10, saturation=1.08 고정값
- `engines/anti_abuse_video_editor.py`: AntiAbuseVideoEditor 존재 (moviepy 기반, 미연동)
- `video_pipeline/config.py:VisualEffectsConfig`: `ken_burns_random_variance=0.00` (비활성)

**해결**:
```python
# video_pipeline/config.py - VisualEffectsConfig에 추가
fingerprint_brightness_variance: float = 0.05   # ±5% (0.95~1.05 범위)
fingerprint_saturation_variance: float = 0.08   # ±8% (0.92~1.08 범위)
fingerprint_contrast_variance: float = 0.05     # ±5% (0.95~1.05 범위)
enable_fingerprint_variance: bool = True
```

**수정 파일**:
```
video_pipeline/config.py:VisualEffectsConfig     ← 3개 variance 필드 추가
engines/color_correction.py                       ← apply_correction()에 랜덤 변이 적용
  - ColorCorrectionSettings에 variance 파라미터 수용
  - random.uniform(-variance, +variance)로 편별 고유값 생성
  - 시니어 안전 범위 클램핑: brightness 0.90~1.15, saturation 0.85~1.20
generate_video_55sec_pipeline.py                  ← color_correction 호출 시 config 전달
```

**검증 기준**:
- 연속 5편 생성 시 밝기/채도 값 모두 다름 (stdout 로그 확인)
- 시니어 가독성 유지: 밝기 0.90 미만/1.15 초과 클램핑

---

### A-2: TTS 피치 미세 변형 (1.5시간)

**문제**: 동일 음성 반복 → 유튜브 오디오 핑거프린트 감지

**현재 코드 상태**:
- `engines/supertone_tts.py:181-210`: `pitch_shift` 파라미터 이미 존재! (-24~24 범위)
- 현재 기본값: `pitch=0` (고정) → generate()에서 `pitch: int = 0`으로 전달

**해결**:
```python
# video_pipeline/config.py - TTSConfig에 추가
fingerprint_pitch_variance: int = 2  # ±2 반음 (음성 품질 저하 없는 범위)
enable_pitch_variance: bool = True
```

**수정 파일**:
```
video_pipeline/config.py:TTSConfig                ← fingerprint_pitch_variance 추가
engines/supertone_tts.py:generate()               ← 수정
  - config에서 pitch_variance 읽기
  - random.randint(-variance, variance) 적용
  - 호출: self._synthesize_via_api(text, speaker, speed, pitch + pitch_offset, ...)
generate_video_55sec_pipeline.py                  ← TTS 호출 시 config 전달
```

**주의사항**:
- ±2 반음 제한 (3 이상은 음성 부자연스러움)
- 같은 영상 내 모든 세그먼트는 동일 pitch_offset (일관성)
- MOCK 모드에서도 pitch_offset 로깅 (디버깅용)

---

### A-3: 에셋 히스토리 중복 방지 (1.5시간)

**문제**: 연속 영상에서 동일 이미지 반복 사용 → 시청자 피로 + 핑거프린트

**현재 코드 상태** (신규 발견):
- `engines/asset_diversity_manager.py`: **이미 존재!** (UTF-8 인코딩 깨짐)
  - AssetDiversityManager 클래스
  - usage_stats 추적 (Dict[str, int])
  - recent_queue (deque 기반 최근 사용 추적)
  - MAX_USE_COUNT = 3, RECENT_VIDEOS_COUNT = 3
  - 가중치 기반 선택: `weight = max_use_count / (usage_count + 1)`
- `src/utils/asset_matcher.py`: 에셋 매칭 로직 존재
- `cli/generation_log.py`: GenerationLog (port/category 중복만 체크)

**해결**: 기존 `asset_diversity_manager.py` UTF-8 복구 + 확장
```python
# engines/asset_diversity_manager.py 수정
MAX_USE_COUNT = 3 → 2  # 더 엄격한 중복 제한
RECENT_VIDEOS_COUNT = 3 → 10  # 최근 10편으로 확장
# 추가: JSON 파일 영속화 (현재 메모리 only → 파일 기반)
HISTORY_PATH = "outputs/asset_history.json"
```

**수정 파일**:
```
engines/asset_diversity_manager.py                ← UTF-8 복구 + 확장
  - RECENT_VIDEOS_COUNT: 3→10
  - JSON 파일 영속화 추가 (outputs/asset_history.json)
  - get_excluded_files() 메서드 추가

src/utils/asset_matcher.py                        ← match_assets() 수정
  - excluded_files 파라미터 추가
  - 매칭 결과에서 excluded_files 제외
  - 제외 후 후보 없으면 fallback (excluded 무시)

generate_video_55sec_pipeline.py                  ← AssetDiversityManager 연동
```

**검증 기준**:
- 연속 3편 생성 시 동일 이미지 파일 0건
- asset_history.json 정상 기록 확인

---

### A-4: SFX 팩 확장 + 랜덤 선택 (1시간)

**문제**: swoosh, pop SFX가 소수 파일만 사용 → 반복성

**현재 코드 상태**:
- `D:\AntiGravity\Assets\SoundFX\`: SFX 파일 존재
- `engines/ffmpeg_pipeline.py`: SFX 파일 경로 하드코딩

**해결**:
```python
# video_pipeline/config.py에 추가 (또는 기존 HookConfig 확장)
sfx_swoosh_pool: list = field(default_factory=lambda: [])  # 자동 스캔
sfx_pop_pool: list = field(default_factory=lambda: [])
sfx_random_selection: bool = True
```

**수정 파일**:
```
engines/ffmpeg_pipeline.py                        ← SFX 선택 로직 수정
  - 기존: 고정 경로 1개
  - 변경: SFX 풀에서 random.choice()
  - D:\AntiGravity\Assets\SoundFX\ 스캔하여 카테고리별 분류
  - swoosh/*.mp3, pop/*.mp3, transition/*.mp3 등

video_pipeline/config.py                          ← sfx 풀 설정 추가
```

**검증 기준**:
- SFX 폴더 내 파일 3종 이상 확인
- 연속 3편에서 서로 다른 SFX 사용

---

## Phase S2-B: 콘텐츠 구조 다양화 (P1, 7시간)

### B-1: 3종 내러티브 템플릿 (3시간)

**문제**: 모든 스크립트가 순차형(문제→해결→가치→CTA) → 단조로움

**현재 코드 상태**:
- `engines/comprehensive_script_generator.py`: 4-Block 순차형만 존재
  - Block 1(안심) → Block 2(공감) → Block 3(동경) → Block 4(확신)
- 프롬프트에 고정된 순차형 지시

**해결 - 3종 내러티브**:

| # | 유형 | 구조 | 감정 곡선 | 적합 콘텐츠 |
|---|------|------|-----------|------------|
| 1 | **순차형** (기본) | 문제→해결→가치→CTA | ↗↗↗↗ 우상향 | EDUCATION, VALUE_PROOF |
| 2 | **역전형** (결론먼저) | 결론→왜?→증거→CTA | ↘↗↗↗ J커브 | COMPARISON, SOCIAL_PROOF |
| 3 | **대비형** (VS) | A안→B안→대비→선택CTA | ↗↘↗↗ W커브 | FEAR_*, CRITERIA |

```python
# engines/comprehensive_script_generator.py에 추가
NARRATIVE_TEMPLATES = {
    "SEQUENTIAL": {
        "blocks": ["pain_point", "solution", "value_proof", "confirmation"],
        "emotion_curve": [0.35, 0.55, 0.75, 0.90],
        "prompt_instruction": "문제를 먼저 제기하고, 해결책을 순차적으로 제시하세요.",
        "weight": 0.40,  # 40% 확률
    },
    "REVERSE": {
        "blocks": ["conclusion_first", "why_explanation", "evidence", "cta_amplified"],
        "emotion_curve": [0.80, 0.50, 0.70, 0.90],
        "prompt_instruction": "결론(핵심 가치)을 먼저 말하고, 그 이유를 풀어가세요.",
        "weight": 0.35,  # 35% 확률
    },
    "CONTRAST": {
        "blocks": ["option_a", "option_b", "comparison_reveal", "best_choice"],
        "emotion_curve": [0.60, 0.40, 0.75, 0.90],
        "prompt_instruction": "두 가지 선택지를 비교하고, 크루즈의 우위를 드러내세요.",
        "weight": 0.25,  # 25% 확률
    }
}
```

**수정 파일**:
```
engines/comprehensive_script_generator.py         ← NARRATIVE_TEMPLATES 딕셔너리 추가
  - generate_script()에서 content_type 기반 내러티브 자동 선택
  - 랜덤 가중치 선택 (weight 기반)
  - generation_log 히스토리 기반 로테이션 (최근 3편 동일 내러티브 금지)
  - Gemini 프롬프트에 narrative_type별 구조 지시 주입
  - Fallback 모드에서도 Block 순서 변경 적용

  - _generate_fallback_blocks() 수정
    * SEQUENTIAL: 기존 순서 유지
    * REVERSE: Block 4→Block 1→Block 2→Block 3 순서
    * CONTRAST: Block A(육지여행)→Block B(크루즈)→비교→선택

engines/script_validation_orchestrator.py          ← 내러티브 유형별 채점 기준 분기
  - REVERSE 유형: 첫 Block에서 Trust 요소 조기 등장 가산점
  - CONTRAST 유형: 비교 키워드("vs", "반면", "차이") 존재 확인

cli/generation_log.py:GenerationLogEntry           ← narrative_type 필드 추가
```

**검증 기준**:
- 연속 10편 생성 시 3종 모두 최소 2회 사용
- 각 유형별 S등급 채점 통과 확인

---

### B-2: Re-Hook 패턴 통합 + 확장 (1.5시간)

**문제**: Re-Hook 시스템이 2개 파일에 분산 + 패턴 수 부족

**현재 코드 상태** (신규 발견 - 2개 시스템 병존):
- `comprehensive_script_generator.py:2091-2105`: 간단 패턴
  - REHOOK_PATTERNS_9S: 5개 (9초용)
  - REHOOK_PATTERNS_27S: 5개 (27초용)
- `engines/rehook_injector.py`: 고급 시스템 (별도 파일!)
  - ReHookInjector 클래스
  - REHOOK_13S_KEYWORDS: 8개
  - REHOOK_32S_KEYWORDS: 9개
  - REHOOK_TEMPLATES_BY_CATEGORY: 5카테고리 × 2타이밍 × 3개 = ~30 템플릿
  - 카테고리: 기항지정보, 선내시설, 불안해소, 가격비교, 버킷리스트

**→ 2개 시스템 통합 필요 + 패턴 확장**

**해결**:
```python
# 9초용 12개 (기존 5개 + 신규 7개)
REHOOK_PATTERNS_9S = [
    # 기존 5개
    "잠깐, 이건 꼭 들어보세요!",
    "여기서 반전이 있어요!",
    "근데 이게 시작일 뿐이에요!",
    "이 다음이 더 놀라워요!",
    "핵심은 바로 이거예요!",
    # 신규 7개 (학습 데이터 기반)
    "그런데 더 놀라운 건요!",
    "이건 아무도 모르는 팁인데요!",
    "여기서부터가 진짜 꿀팁이에요!",
    "한 가지 더 알려드릴게요!",
    "이 부분을 놓치면 안 돼요!",
    "잠깐만요, 이게 핵심이에요!",
    "여기서 제가 깜짝 놀랐어요!",
]

# 27초용 12개 (기존 5개 + 신규 7개)
REHOOK_PATTERNS_27S = [
    # 기존 5개
    "이게 끝이 아니에요!",
    "세 번째 이유가 가장 중요해요!",
    "여기서부터가 진짜예요!",
    "결정적인 차이는 바로 이거예요!",
    "마지막 이유를 들으면 놀라실 거예요!",
    # 신규 7개
    "근데 진짜 핵심은 따로 있어요!",
    "이 한 가지가 모든 걸 바꿔요!",
    "여기서 포기하면 정말 손해예요!",
    "솔직히 이건 저도 몰랐어요!",
    "이 부분이 가장 많이 물어보시는 거예요!",
    "마지막까지 보셔야 할 이유가 있어요!",
    "가장 중요한 부분이 남았어요!",
]
```

**수정 파일**:
```
engines/comprehensive_script_generator.py:2091-2105  ← 패턴 확장
  - REHOOK_PATTERNS_9S: 5→12개
  - REHOOK_PATTERNS_27S: 5→12개
  - 총 24개 (기존 10개 + 신규 14개)
```

---

### B-3: 뉴스/팁/여행기 포맷 분기 (1.5시간)

**문제**: 모든 영상이 동일한 톤 → 채널 다양성 부족

**현재 코드 상태**:
- `comprehensive_script_generator.py`: content_type 15종 존재
- 톤 구분 없음 (모두 "설명형")

**해결**:
```python
# engines/comprehensive_script_generator.py에 추가
CONTENT_FORMAT = {
    "NEWS": {
        "tone": "정보 전달형",
        "prompt_prefix": "뉴스 앵커처럼 객관적이고 신뢰감 있는 톤으로",
        "tts_speed": 1.05,
        "content_types": ["EDUCATION", "CRITERIA_EDUCATION", "FEAR_HIDDEN_COST"],
    },
    "TIP": {
        "tone": "친구 같은 조언형",
        "prompt_prefix": "친한 언니/형이 알려주듯 편안하고 실용적인 톤으로",
        "tts_speed": 0.95,
        "content_types": ["VALUE_PROOF", "CONVENIENCE", "FEAR_ONBOARD_SYSTEM"],
    },
    "TRAVEL_STORY": {
        "tone": "여행 에세이형",
        "prompt_prefix": "직접 다녀온 여행기처럼 감성적이고 생생한 톤으로",
        "tts_speed": 0.90,
        "content_types": ["BUCKET_LIST", "SOCIAL_PROOF", "COMPARISON"],
    }
}
```

**수정 파일**:
```
engines/comprehensive_script_generator.py         ← CONTENT_FORMAT 딕셔너리 추가
  - content_type → format 자동 매핑
  - Gemini 프롬프트에 톤 지시 주입
  - TTS speed 자동 조절
  - Fallback 모드에서도 톤 반영 (문장 어미 변형)

cli/generation_log.py:GenerationLogEntry          ← content_format 필드 추가
```

---

### B-4: 다음 편 예고 5초 구간 (1시간)

**문제**: 영상 마지막 구간에서 시청자 이탈 → 다음 영상 연결 부재

**현재 코드 상태**:
- CTA 3단계 후 outro_visual_duration: 2.5초 (로고만 표시)
- "다음 편 예고" 기능: 미구현

**해결**:
```python
# video_pipeline/config.py - ScriptConfig에 추가
enable_next_preview: bool = True
next_preview_duration: float = 2.0  # CTA 직후 2초
next_preview_templates: tuple = (
    "다음 영상에서 {next_topic}을 알려드립니다!",
    "다음 편에서 더 놀라운 이야기가 기다리고 있어요!",
    "{next_topic}이 궁금하시면 팔로우 해주세요!",
)
```

**수정 파일**:
```
video_pipeline/config.py:ScriptConfig             ← next_preview 설정 추가
engines/comprehensive_script_generator.py         ← 스크립트 마지막에 preview 세그먼트 추가
  - CTA 직후 "next_preview" segment_type 삽입
  - content_type 기반 next_topic 자동 생성
  - 히스토리에서 아직 안 다룬 토픽 우선

generate_video_55sec_pipeline.py                  ← preview 세그먼트 렌더링
  - 자막 + 오디오 생성
  - outro_visual 시작 전 삽입
```

**주의사항**:
- target_duration 55초 내에 포함 (CTA 시간 조정 필요)
- 총 시간: Hook(5s) + Body(35s) + CTA(7s) + Preview(2s) + Outro(2.5s) ≈ 51.5s ✓

---

## Phase S2-C: 측정 가능성 구축 (P1, 5시간)

### C-1: 트래킹 코드 자동 삽입 (1.5시간)

**문제**: 영상별 성과 추적 불가 → 어떤 전략이 효과적인지 모름

**현재 코드 상태**:
- `cli/auto_mode.py:554-573`: `_create_upload_package()` 존재
- 업로드 패키지에 기본 메타데이터만 포함

**해결**:
```python
# 트래킹 코드 형식: CD-{날짜}-{일련번호}-{content_type}-{narrative}
# 예: CD-20260310-001-EDU-SEQ
```

**수정 파일**:
```
cli/auto_mode.py:_create_upload_package()         ← tracking_code 자동 생성
  - 형식: CD-{YYYYMMDD}-{NNN}-{TYPE_3CHAR}-{NARR_3CHAR}
  - 업로드 패키지 메타데이터에 포함
  - YouTube 설명란 자동 삽입 (숨김 태그)

cli/generation_log.py:GenerationLogEntry          ← tracking_code 필드 추가

engines/comprehensive_script_generator.py         ← script_dict에 tracking_code 포함
```

---

### C-2: S등급 보정 - 감정곡선 검증 항목 (2시간)

**문제**: 감정곡선 검증기는 존재하나 S등급 채점에 미통합 → W커브/J커브 미검증

**현재 코드 상태** (신규 발견):
- `engines/emotion_curve_validator.py`: **이미 존재!**
  - EMOTION_TARGETS: 10개 segment_type별 감정 목표 범위
  - EMOTION_KEYWORDS: 6개 감정 카테고리 (불안/공감/호기심/열망/확신/행동)
  - calculate_segment_emotion() 함수
  - 키워드 기반 감정 점수 계산
- `engines/script_validation_orchestrator.py`: 10개 항목 100점 채점 (감정곡선 미포함)
- `engines/sgrade_constants.py:220-238`: S_GRADE_THRESHOLDS + REQUIREMENTS

**해결**:
```python
# 감정곡선 검증 채점 (기존 100점 체계 내 재배분)
# Specificity(10점) → Specificity(7점) + Emotion_Curve(3점)
# 또는 별도 보너스 점수

EMOTION_CURVE_SCORING = {
    "SEQUENTIAL": {
        "expected": [0.30, 0.55, 0.75, 0.90],  # 우상향
        "tolerance": 0.15,  # ±0.15 허용
    },
    "REVERSE": {
        "expected": [0.80, 0.50, 0.70, 0.90],  # J커브
        "tolerance": 0.15,
    },
    "CONTRAST": {
        "expected": [0.60, 0.40, 0.75, 0.90],  # W커브
        "tolerance": 0.15,
    }
}
```

**수정 파일**:
```
engines/script_validation_orchestrator.py         ← _score_emotion_curve() 추가
  - 스크립트 emotion_score 4개 추출
  - narrative_type별 기대 곡선과 비교
  - tolerance 내 매칭 시 만점
  - 기존 100점 체계 재배분: Specificity 10→7점, Emotion Curve 0→3점

engines/sgrade_constants.py                       ← EMOTION_CURVE_SCORING 상수 추가
  - 3종 내러티브별 기대 곡선 정의
  - tolerance 설정

engines/comprehensive_script_generator.py         ← _quick_self_score()에 감정곡선 점수 반영
```

---

### C-3: 주간 보고서 자동 생성 (1.5시간)

**문제**: 생산된 영상 통계를 수동으로 파악 → 비효율

**현재 코드 상태**:
- `cli/generation_log.py`: GenerationLog 클래스 (entries 리스트)
- 통계 기능: 미구현

**해결**:
```python
# cli/weekly_report.py (신규)
class WeeklyReportGenerator:
    """주간 보고서 자동 생성"""

    def generate(self, log: GenerationLog, week_start: date) -> str:
        """마크다운 형식 주간 보고서 반환"""
        # 1. 기간 내 생성 편수
        # 2. S등급 달성률 (S/A/B/F 분포)
        # 3. 카테고리 분포 (content_type)
        # 4. 내러티브 분포 (narrative_type)
        # 5. 기항지 분포 (port 사용 빈도)
        # 6. 평균 점수 + 최고/최저 점수 영상
        # 7. 다음 주 추천 전략
```

**수정 파일**:
```
cli/weekly_report.py (신규)                       ← WeeklyReportGenerator 클래스
  - GenerationLog 파싱
  - 마크다운 출력 (outputs/reports/weekly_YYYYMMDD.md)
  - content_type, narrative_type, port 분포 차트
  - S등급 달성률 추이

generate.py (또는 cli 명령)                        ← --report 플래그 추가
  - python generate.py --report weekly
  - 자동으로 최근 7일 로그 파싱 → 보고서 생성
```

**출력 예시**:
```markdown
# CruiseDot 주간 보고서 (2026-03-03 ~ 2026-03-09)

## 생산 요약
- 총 생산: 12편
- S등급: 9편 (75%)
- A등급: 2편 (17%)
- B등급: 1편 (8%)
- 평균 점수: 92.3점

## 카테고리 분포
- EDUCATION: 3편 (25%)
- COMPARISON: 2편 (17%)
- FEAR_RESOLUTION: 2편 (17%)
...

## 다음 주 추천
- BUCKET_LIST 콘텐츠 부족 (0편) → 2편 이상 생산 권장
- 알래스카 기항지 활용률 낮음 → 우선 배정
```

---

## 수정 파일 총 목록

| # | 파일 | Phase | 변경 내용 | 유형 |
|---|------|-------|-----------|------|
| 1 | `video_pipeline/config.py` | A-1,A-2,A-4,B-4 | fingerprint 설정 + SFX 풀 + preview | 수정 |
| 2 | `engines/color_correction.py` | A-1 | 밝기/채도 랜덤 변이 적용 | 수정 |
| 3 | `engines/supertone_tts.py` | A-2 | pitch variance 적용 | 수정 |
| 4 | `engines/asset_diversity_manager.py` | A-3 | UTF-8 복구 + 영속화 + 확장 | 수정 |
| 5 | `src/utils/asset_matcher.py` | A-3 | excluded_files 파라미터 | 수정 |
| 5b | `engines/rehook_injector.py` | B-2 | comprehensive_script_generator와 통합 | 수정 |
| 5c | `engines/emotion_curve_validator.py` | C-2 | 내러티브별 곡선 + S등급 채점 통합 | 수정 |
| 6 | `engines/ffmpeg_pipeline.py` | A-4 | SFX 풀 랜덤 선택 | 수정 |
| 7 | `engines/comprehensive_script_generator.py` | B-1,B-2,B-3,B-4,C-1 | 내러티브 3종 + ReHook 확장 + 포맷 분기 + 예고 + 트래킹 | 수정 |
| 8 | `engines/script_validation_orchestrator.py` | B-1,C-2 | 내러티브별 채점 + 감정곡선 | 수정 |
| 9 | `engines/sgrade_constants.py` | C-2 | EMOTION_CURVE_SCORING 상수 | 수정 |
| 10 | `cli/generation_log.py` | B-1,B-3,C-1 | narrative_type + format + tracking_code 필드 | 수정 |
| 11 | `cli/auto_mode.py` | C-1 | tracking_code 생성 + 업로드 패키지 | 수정 |
| 12 | `cli/weekly_report.py` | C-3 | 주간 보고서 생성기 | **신규** |
| 13 | `generate.py` | C-3 | --report 플래그 | 수정 |
| 14 | `generate_video_55sec_pipeline.py` | A-1,A-2,A-3,B-4 | color/pitch/history/preview 연동 | 수정 |

---

## 실행 순서 및 의존성

```
Phase S2-A (핑거프린트) ─── 6시간 ─── P0
  ├── A-1 밝기/채도 랜덤 (2h) ← 독립
  ├── A-2 TTS 피치 변형 (1.5h) ← 독립
  ├── A-3 에셋 히스토리 (1.5h) ← 독립
  └── A-4 SFX 팩 확장 (1h) ← 독립
  [A-1~A-4 병렬 가능]

Phase S2-B (다양화) ─── 7시간 ─── P1
  ├── B-1 내러티브 3종 (3h) ← 독립
  ├── B-2 Re-Hook 확장 (1.5h) ← 독립
  ├── B-3 뉴스/팁/여행기 (1.5h) ← B-1 후
  └── B-4 다음 편 예고 (1h) ← 독립

Phase S2-C (측정) ─── 5시간 ─── P1
  ├── C-1 트래킹 코드 (1.5h) ← 독립
  ├── C-2 감정곡선 채점 (2h) ← B-1 후 (내러티브 유형 필요)
  └── C-3 주간 보고서 (1.5h) ← C-1 후 (tracking_code 필요)
```

**최적 병렬 실행 순서**:
1. 1차 배치: A-1 + A-2 + A-3 + A-4 + B-2 (모두 독립, 병렬)
2. 2차 배치: B-1 + B-4 + C-1 (독립, 병렬)
3. 3차 배치: B-3 + C-2 + C-3 (B-1, C-1 의존)

---

## 검수 체크리스트

### S2-A 완료 시
- [ ] 연속 5편 생성 → 밝기/채도 값 모두 다름
- [ ] 연속 5편 생성 → TTS 피치 값 모두 다름
- [ ] 연속 3편 생성 → 동일 이미지 파일 0건
- [ ] SFX 최소 3종 이상 랜덤 사용 확인
- [ ] 시니어 가독성 유지 (밝기/채도 안전 범위)

### S2-B 완료 시
- [ ] 10편 생성 → 3종 내러티브 모두 2회 이상 사용
- [ ] 24개 Re-Hook 패턴 랜덤 사용 확인
- [ ] 3종 포맷(뉴스/팁/여행기) 톤 차이 육안 확인
- [ ] 다음 편 예고 자막+오디오 정상 출력

### S2-C 완료 시
- [ ] tracking_code 업로드 패키지에 포함
- [ ] 감정곡선 채점 정상 동작 (3종 내러티브별)
- [ ] 주간 보고서 마크다운 정상 출력
- [ ] S등급 채점 100점 체계 유지 (총점 변동 없음)

### 전체 통합 검증
- [ ] `python generate.py --mode auto --dry-run --count 10` → 8편 이상 S등급
- [ ] 기존 WO v7.0 S등급 필수 조건 6개 모두 유지
- [ ] 렌더링 속도 50초 이내 유지 (핑거프린트 추가로 인한 지연 5% 이내)

---

## 리스크 평가

| 변경 | 리스크 | 영향 | 완화 |
|------|--------|------|------|
| 밝기/채도 랜덤 | LOW | 시니어 가독성 | 안전 범위 클램핑 (0.90~1.15) |
| TTS 피치 변형 | LOW | 음성 품질 | ±2 반음 제한 |
| 에셋 히스토리 | LOW | 후보 부족 | fallback (excluded 무시) |
| 내러티브 3종 | MEDIUM | S등급 채점 변동 | 기존 순차형 weight 40% 유지 |
| 감정곡선 채점 | MEDIUM | 점수 재배분 | Specificity 10→7점만 이동 (3점) |
| 주간 보고서 | LOW | 없음 | 읽기 전용 기능 |

---

## 예상 효과

| 지표 | S1 완료 후 | S2 완료 후 | 개선 |
|------|-----------|-----------|------|
| S등급 달성률 | 80% | 90%+ | +10% |
| 핑거프린트 고유성 | 0% (동일) | 95%+ (편별 고유) | 알고리즘 안전 |
| Re-Hook 다양성 | 10패턴 | 24패턴 | 2.4x |
| 내러티브 다양성 | 1종 | 3종 | 3x |
| 콘텐츠 포맷 | 1종 | 3종 (뉴스/팁/여행기) | 3x |
| 성과 추적 | 없음 | 트래킹+보고서 | 데이터 기반 |

---

## 참고 자료

- WO v5.0 Expert Debate Synthesis: `docs/work_orders/WO_20260305_EXPERT_DEBATE_SYNTHESIS_v5.md` Sprint 2 섹션
- 학습 데이터: 4A 프레임워크, PASONA 법칙, 심리적 4단계 구조
- 기존 엔진: anti_abuse_video_editor.py, color_correction.py (재활용 가능)
