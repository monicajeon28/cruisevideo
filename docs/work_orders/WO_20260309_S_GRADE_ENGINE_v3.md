# WO_20260309_S_GRADE_ENGINE_v3.md
# S등급 엔진 달성 통합 작업지시서 v3.0

**작성일**: 2026-03-09
**작성자**: Claude Code (6-Agent 심층 분석 통합)
**목표**: 78점 → 90점+ (S등급 달성)
**총 소요**: 37시간 (5일)

---

## Executive Summary

### 6-Agent 분석 결과 통합

| Agent | 영역 | 핵심 발견 | 상태 |
|-------|------|-----------|------|
| Architecture Designer | SOLID 원칙 | God Object, SOLID 45% 준수 | 분석 완료 |
| Performance Analyzer | 성능 병목 | 69초→9.7초 가능 (-86%) | 분석 완료 |
| Security Guardian | 보안 취약점 | CRITICAL 2건 + HIGH 4건 | 분석 완료 |
| Refactoring Advisor | Code Smell | 24건 발견, 복잡도 18.4 | 분석 완료 |
| Code Quality Checker | 종합 품질 | TOP 20 이슈, 78→98점 로드맵 | 분석 완료 |
| Cross-Check Reviewer | 크로스체크 | P0-1~3 검증 95/100 | 완료 |

### 현재 점수 분석 (78/100)

| 항목 | 만점 | 현재 | 문제 |
|------|------|------|------|
| 기능 완성도 | 25 | 20 | P0-5 애니메이션, P0-6 freeze |
| 아키텍처 | 20 | 12 | God Object 2200줄, SOLID 45% |
| 성능 | 15 | 15 | 28초 렌더링 (우수) |
| 보안 | 15 | 10 | API 키 노출 CRITICAL 2건 |
| 테스트 | 15 | 0 | 커버리지 0% |
| 코드 품질 | 10 | 11 | 주석 우수 (+1 보너스) |
| **총점** | **100** | **78** | **B등급** |

### S등급 달성 경로 (Quick Path)

| Phase | 소요 | 작업 | 점수 변화 | 누적 |
|-------|------|------|-----------|------|
| **S1 (오늘)** | **4h** | 보안 P0 + Config 통합 + P0-5 수정 | +10점 | **88점** |
| **S2 (내일)** | **8h** | God Object 분리 + 테스트 30개 | +7점 | **95점** |
| S3 (이번 주) | 13h | 성능 최적화 + 테스트 60개 | +3점 | 98점 |
| S4 (다음 주) | 12h | SOLID 완성 + E2E 테스트 | +2점 | 100점 |

**최단 S등급 달성**: Phase S1 + S2 = **12시간 (2일)**

---

## Phase S1: 긴급 수정 (오늘 4시간, +10점)

### S1-1: Config 이중 정의 제거 [P0, 15분, +2점]

**문제**: `PipelineConfig` 클래스가 2곳에 중복 정의됨
- `generate_video_55sec_pipeline.py:90-150` (60개 필드, 구버전)
- `video_pipeline/config.py:34-279` (200개 필드, 최신)

**영향**: Phase A P0-1, P0-2 수정이 **적용 안 됨** (로컬 클래스 우선 참조)

**수정**:
```python
# generate_video_55sec_pipeline.py
# 1. Line 90-150 PipelineConfig 클래스 전체 삭제
# 2. 상단 import에 추가:
from video_pipeline.config import PipelineConfig
```

**검증**:
```python
# 테스트 코드
from generate_video_55sec_pipeline import Video55SecPipeline
pipeline = Video55SecPipeline()
assert pipeline.config.outro_visual_duration == 3.0  # P0-1 적용 확인
assert pipeline.config.image_subtitle_font_size == 80  # P0-2 적용 확인
```

---

### S1-2: API 키 보안 강화 [P0, 60분, +5점]

**문제 CRITICAL-1**: `.env` 파일에 10개 API 키 평문 노출
**문제 CRITICAL-2**: `test_gemini_models.py:9`에 API 키 하드코딩

**수정 순서**:

```bash
# Step 1: .env가 Git 히스토리에 있는지 확인
git log --all --full-history -- .env

# Step 2: .gitignore에 .env 추가 확인
# (이미 있으면 skip)

# Step 3: test_gemini_models.py 하드코딩 제거
```

```python
# test_gemini_models.py 수정
import os
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise ValueError("GEMINI_API_KEY not found in environment")

genai.configure(api_key=api_key)
```

```python
# 전역 검색: 하드코딩 API 키 패턴
# 검색 대상: AIzaSy*, sk-proj-*, sk-ant-*, d9f47ab*
# 발견 시 모두 os.getenv() 방식으로 교체
```

**추가 수정**:
```python
# 에러 로깅에서 API 키 마스킹
# Before:
print(f"API Key: {api_key[:20]}...")  # ❌ 일부 노출

# After:
logger.info("API Key: ****configured****")  # ✅ 마스킹
```

---

### S1-3: P0-5 Outro 애니메이션 재수정 [P0, 40분, +1점]

**문제**: 현재 2-phase 구현에 0.5초 중첩 + 크기 jump

**수정 방안 (Option A: CrossFade 중첩 허용)**:
```python
# generate_video_55sec_pipeline.py:2021-2061

# [FIX S1-3] Outro 로고: 2-phase 중첩 CrossFade (0.6x → 1.0x)
phase1_duration = outro_duration * 0.6  # 60%
phase2_duration = outro_duration * 0.6  # 60% (0.2 중첩)
crossfade_overlap = 0.5  # 중첩 시간

# Phase 1: 작은 로고 (0.6배, FadeOut)
logo_small_dur = logo_with_mask.with_duration(phase1_duration)
logo_small_resized = logo_small_dur.resized(0.6)
logo_small_pos = logo_small_resized.with_position('center')
logo_small_fade = logo_small_pos.with_effects([vfx.FadeIn(0.3), vfx.FadeOut(crossfade_overlap)])
logo_small_start = logo_small_fade.with_start(outro_start)

# Phase 2: 큰 로고 (1.0배, FadeIn)
logo_large_dur = logo_with_mask.with_duration(phase2_duration)
logo_large_resized = logo_large_dur.resized(1.0)
logo_large_pos = logo_large_resized.with_position('center')
logo_large_fade = logo_large_pos.with_effects([vfx.FadeIn(crossfade_overlap)])
phase2_start = outro_start + phase1_duration - crossfade_overlap  # 중첩 시작
logo_large_start = logo_large_fade.with_start(phase2_start)

# 두 phase 추가
final_clips.append(logo_small_start)
final_clips.append(logo_large_start)
```

**예상 동작**:
- 0.0-1.3초: 0.6배 로고 (FadeIn 0.3초)
- 1.3-1.8초: 0.6배 FadeOut + 1.0배 FadeIn (부드러운 전환)
- 1.8-3.0초: 1.0배 로고 유지
- **크기 jump 없음** (FadeOut/FadeIn으로 자연스러운 전환)

---

### S1-4: Path Traversal 방어 [P1, 30분, +1점]

**수정**:
```python
# generate_video_55sec_pipeline.py:_load_script()
# P0-7 검증에 경로 검증 추가

from pathlib import Path

# 허용된 디렉토리 목록
ALLOWED_SCRIPT_DIRS = [
    Path("D:/mabiz/outputs").resolve(),
    Path("D:/mabiz/config").resolve(),
    Path("D:/mabiz/test_scripts").resolve(),
]

def _load_script(self, json_path: str):
    # [FIX S1-4] 경로 검증 (Path Traversal 방어)
    resolved = Path(json_path).resolve()
    if not any(str(resolved).startswith(str(d)) for d in ALLOWED_SCRIPT_DIRS):
        raise ValueError(f"Script path outside allowed directories: {resolved}")

    # 기존 P0-7 검증 계속...
```

---

### S1-5: Prompt Injection 방어 강화 [P1, 30분, +1점]

**수정**:
```python
# engines/comprehensive_script_generator.py:_sanitize_input()

import unicodedata

def _sanitize_input(self, text: str, max_length: int = 50) -> str:
    """[FIX S1-5] Prompt Injection 방어 강화"""
    if not isinstance(text, str):
        raise ValueError(f"Expected str, got {type(text)}")

    # 1. 유니코드 정규화 (NFKC - 변형 문자 통일)
    text = unicodedata.normalize('NFKC', text)

    # 2. 허용 문자만 유지 (한글, 영문, 숫자, 공백, 하이픈)
    text = re.sub(r'[^가-힣a-zA-Z0-9\s\-]', '', text)

    # 3. 기존 forbidden_patterns 유지
    for pattern in self._forbidden_patterns:
        text = re.sub(pattern, '', text, flags=re.IGNORECASE)

    # 4. 길이 제한 (200→50)
    return text[:max_length].strip()
```

---

## Phase S2: 구조 개선 (내일 8시간, +7점)

### S2-1: Video55SecPipeline God Object 분리 [P0, 4h, +4점]

**현재**: 1개 클래스, 2200줄, 30개 메서드, 15개 책임

**목표**: 5개 클래스, 각 300줄 이하, 6개 메서드, 3개 책임

**분리 계획**:

```
generate_video_55sec_pipeline.py (2200줄)
↓ 분리
├── video_pipeline/tts_engine.py (300줄)
│   └── TTSEngine: generate_tts(), _synthesize_segment()
│
├── video_pipeline/visual_composer.py (400줄)
│   └── VisualComposer: apply_ken_burns(), apply_crossfade()
│   └──                  load_visuals(), select_hook_video()
│
├── video_pipeline/audio_mixer.py (250줄)
│   └── AudioMixer: mix_audio(), create_ducked_bgm()
│   └──              add_sfx(), normalize_audio()
│
├── video_pipeline/overlay_renderer.py (300줄)
│   └── OverlayRenderer: render_logo(), render_cta()
│   └──                   render_outro(), render_pop_messages()
│
└── generate_video_55sec_pipeline.py (400줄)
    └── Video55SecPipeline: generate_video_from_script()
    └──                      (Orchestrator, Facade Pattern)
```

**구현 순서**:
1. `tts_engine.py` 추출 (45분)
2. `audio_mixer.py` 추출 (45분)
3. `overlay_renderer.py` 추출 (60분)
4. `visual_composer.py` 추출 (90분)
5. Orchestrator 리팩토링 (30분)

**핵심 원칙**:
- 기존 외부 API 변경 없음 (`generate_video_from_script()` 시그니처 유지)
- 의존성 주입 (DI) 패턴 사용
- 각 모듈 독립 테스트 가능

---

### S2-2: 핵심 단위 테스트 30개 작성 [P0, 4h, +3점]

**우선순위 테스트 목록**:

```python
# tests/test_config.py (5개)
def test_config_singleton()           # Config 단일 인스턴스
def test_config_default_values()      # 기본값 정확성
def test_config_outro_duration()      # P0-1 검증 (3.0초)
def test_config_image_subtitle()      # P0-2 검증 (80px)
def test_config_forbidden_claims()    # 금지 마케팅 문구

# tests/test_script_validation.py (8개)
def test_load_script_valid()          # 정상 스크립트
def test_load_script_missing_theme()  # P0-7 검증
def test_load_script_empty_segments() # P0-7 검증
def test_load_script_invalid_type()   # P0-7 검증
def test_load_script_path_traversal() # S1-4 검증
def test_validate_banned_words()      # 금지어 검출
def test_validate_trust_elements()    # Trust 요소 검증
def test_validate_s_grade_score()     # S등급 90점 기준

# tests/test_subtitle_renderer.py (5개)
def test_render_korean_text()         # 한글 렌더링
def test_render_font_from_config()    # P0-3 Config 참조
def test_render_batch()               # 배치 렌더링
def test_cleanup()                    # 임시 파일 정리
def test_render_empty_text()          # 빈 텍스트 처리

# tests/test_asset_matcher.py (5개)
def test_match_by_keywords()          # 키워드 매칭
def test_match_port_images()          # 기항지 이미지
def test_fallback_random()            # 랜덤 fallback
def test_blacklist_filter()           # 블랙리스트 필터
def test_hook_folder_priority()       # Hook 우선 선택

# tests/test_bgm_matcher.py (4개)
def test_select_travel_bgm()          # 여행 BGM 선택
def test_blacklist_sleep_music()      # 수면곡 차단
def test_priority_score()             # 우선순위 점수
def test_backup_folder_fallback()     # Backup 폴더

# tests/test_security.py (3개)
def test_sanitize_prompt_injection()  # Prompt Injection 차단
def test_sanitize_unicode_bypass()    # 유니코드 우회 차단
def test_api_key_not_in_logs()        # API 키 로그 미노출
```

**테스트 인프라**:
```ini
# pytest.ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
markers =
    slow: marks tests as slow (deselect with '-m "not slow"')
    integration: marks integration tests
    e2e: marks end-to-end tests
```

---

## Phase S3: 성능 최적화 (이번 주 13시간, +3점)

### S3-1: 이미지 매칭 역 인덱스 [P1, 2h]

**현재**: O(N×M) = 3,447 × 5 = 17,235회 비교 (8초)
**목표**: O(M+K) = 5 + 50 = 55회 (0.5초)

```python
# src/utils/asset_matcher.py 수정

class AssetMatcher:
    def __init__(self):
        self._keyword_index = defaultdict(set)  # 역 인덱스
        self._build_index()

    def _build_index(self):
        """[FIX S3-1] 키워드 역 인덱스 구축 (1회, 5초)"""
        for asset_key, asset_info in self._asset_cache.items():
            for keyword in asset_info.get("keywords", []):
                self._keyword_index[keyword.lower()].add(asset_key)
        logger.info(f"[OK] 역 인덱스 구축: {len(self._keyword_index)} 키워드")

    def match_assets(self, keywords, content_type=None, max_results=5):
        """[FIX S3-1] 역 인덱스 기반 O(M+K) 매칭"""
        candidate_keys = set()
        for kw in keywords:
            candidate_keys.update(self._keyword_index.get(kw.lower(), set()))

        # 점수 계산 (후보만 대상)
        scored = []
        for key in candidate_keys:
            score = self._calculate_score(key, keywords, content_type)
            scored.append((key, score))

        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:max_results]
```

---

### S3-2: TTS 병렬화 [P1, 3h]

**현재**: 8개 세그먼트 순차 (15초)
**목표**: 5개 동시 (3초)

```python
# video_pipeline/tts_engine.py (S2-1에서 추출)

import asyncio
from concurrent.futures import ThreadPoolExecutor

class TTSEngine:
    def __init__(self, config, max_concurrent=5):
        self.max_concurrent = max_concurrent
        self._executor = ThreadPoolExecutor(max_workers=max_concurrent)

    def generate_parallel(self, segments):
        """[FIX S3-2] TTS 병렬 생성"""
        futures = []
        for seg in segments:
            future = self._executor.submit(
                self._synthesize_single, seg['text'], seg.get('speaker', 'audrey')
            )
            futures.append(future)

        results = [f.result(timeout=30) for f in futures]
        return results
```

---

### S3-3: BGM 메타데이터 캐싱 [P2, 1h]

```python
# engines/bgm_matcher.py 수정

class BGMMatcher:
    _mood_index = None  # 클래스 레벨 캐싱

    def _build_mood_index(self):
        """[FIX S3-3] BGM 무드 인덱스 (1회 구축)"""
        if BGMMatcher._mood_index is not None:
            return

        BGMMatcher._mood_index = {}
        for mood, files in self.metadata.get("bgm_by_mood", {}).items():
            BGMMatcher._mood_index[mood] = [
                f for f in files
                if not self._is_blacklisted(f.get("filename", ""), f.get("keywords", []))
            ]
        logger.info(f"[OK] BGM 인덱스 구축: {len(BGMMatcher._mood_index)} moods")
```

---

### S3-4: 자막 폰트 캐싱 [P2, 1h]

```python
# engines/subtitle_image_renderer.py 수정

class SubtitleImageRenderer:
    _font_cache = {}  # 클래스 레벨 폰트 캐싱

    def __init__(self, config=None):
        self.config = config or PipelineConfig()
        self.font_size = getattr(self.config, 'image_subtitle_font_size', 80)

        # [FIX S3-4] 폰트 캐싱 (동일 사이즈 재로드 방지)
        cache_key = (self.font_path, self.font_size)
        if cache_key not in SubtitleImageRenderer._font_cache:
            try:
                SubtitleImageRenderer._font_cache[cache_key] = \
                    ImageFont.truetype(self.font_path, self.font_size)
            except Exception:
                SubtitleImageRenderer._font_cache[cache_key] = \
                    ImageFont.load_default()

        self.font = SubtitleImageRenderer._font_cache[cache_key]
```

---

### S3-5: Magic Numbers 상수화 [P2, 1h]

```python
# video_pipeline/constants.py (신규 파일)

"""S등급 엔진 상수 정의 (Magic Numbers 제거)"""

# 영상 레이아웃
VIDEO_WIDTH = 1080
VIDEO_HEIGHT = 1920
VIDEO_FPS = 30

# 세그먼트 제한
MAX_BODY_SEGMENTS = 6
HOOK_MAX_DURATION = 3.5
VIDEO_MAX_DURATION = 58.0

# 자막 위치
SUBTITLE_Y_POSITION = 1350
SUBTITLE_MARGIN_BOTTOM = 200

# 로고
LOGO_DEFAULT_HEIGHT = 200
LOGO_OUTRO_HEIGHT = 300
LOGO_OPACITY = 0.55

# Ken Burns
KEN_BURNS_MIN_SCALE = 0.7
KEN_BURNS_MAX_ZOOM = 0.048

# 오디오
AUDIO_DUCKING_FADE = 0.3
AUDIO_NORMALIZE_TARGET = -14.0

# 타이밍
CROSSFADE_DURATION = 0.25
POP_MESSAGE_OFFSET = 0.5
SWOOSH_LEAD_TIME = 0.3
```

---

### S3-6: Dead Code 정리 [P2, 30min]

**제거 대상**:
```python
# 1. config.py:278 - 비활성화된 Hook Flash 관련 설정
enable_hook_flash: bool = False  # [BUG-1] 비활성화 + 구현 코드 없음

# 2. config.py:88-92 - 미구현 Slide Transition
enable_slide_transition: bool = False
slide_transition_duration: float = 0.5
slide_transition_direction: str = "left"

# 3. generate_video_55sec_pipeline.py - 미사용 변수
hook_audio = None  # Hook 오디오 미사용
```

---

## Phase S4: SOLID 완성 + E2E (다음 주 12시간, +2점)

### S4-1: Strategy Pattern (content_type 분기) [P2, 3h]

```python
# video_pipeline/strategies.py (신규)

from abc import ABC, abstractmethod

class ContentStrategy(ABC):
    @abstractmethod
    def get_prompt_template(self) -> str: pass

    @abstractmethod
    def get_visual_priority(self) -> list: pass

    @abstractmethod
    def get_cta_style(self) -> dict: pass

class EducationStrategy(ContentStrategy):
    def get_prompt_template(self):
        return EDUCATION_TEMPLATE

    def get_visual_priority(self):
        return ["port_landscape", "infographic", "comparison"]

    def get_cta_style(self):
        return {"urgency": "low", "trust": "high"}

class ComparisonStrategy(ContentStrategy):
    # ...

class FearResolutionStrategy(ContentStrategy):
    # ...

# 레지스트리
STRATEGIES = {
    "EDUCATION": EducationStrategy(),
    "COMPARISON": ComparisonStrategy(),
    "FEAR_RESOLUTION": FearResolutionStrategy(),
}
```

### S4-2: Dependency Injection [P2, 2h]

```python
# generate_video_55sec_pipeline.py 수정

class Video55SecPipeline:
    def __init__(
        self,
        config: PipelineConfig = None,
        tts_engine: TTSEngine = None,
        visual_composer: VisualComposer = None,
        audio_mixer: AudioMixer = None,
        overlay_renderer: OverlayRenderer = None,
    ):
        self.config = config or PipelineConfig()
        self.tts = tts_engine or TTSEngine(self.config)
        self.visual = visual_composer or VisualComposer(self.config)
        self.audio = audio_mixer or AudioMixer(self.config)
        self.overlay = overlay_renderer or OverlayRenderer(self.config)
```

### S4-3: E2E 테스트 5개 [P2, 4h]

```python
# tests/e2e/test_full_pipeline.py

@pytest.mark.e2e
@pytest.mark.slow
class TestFullPipeline:
    def test_auto_mode_generates_video(self):
        """Auto 모드 영상 생성 E2E"""

    def test_manual_mode_generates_video(self):
        """Manual 모드 영상 생성 E2E"""

    def test_dry_run_generates_script_only(self):
        """Dry-run 모드 스크립트만 생성"""

    def test_s_grade_loop_reaches_90(self):
        """S등급 루프 90점 도달"""

    def test_batch_3_videos_parallel(self):
        """배치 3개 동시 생성"""
```

### S4-4: Dict → Dataclass 변환 [P2, 3h]

```python
# video_pipeline/models.py (신규)

@dataclass
class ScriptSegment:
    section: str
    text: str
    subtitle: str
    duration: float
    speaker_persona: str = "audrey"
    emotion: str = "neutral"
    visual_keywords: List[str] = field(default_factory=list)

@dataclass
class Script:
    theme: str
    title: str
    segments: List[ScriptSegment]
    content_type: str = "EDUCATION"
    port_name: str = ""
    ship_name: str = ""

    def validate(self) -> bool:
        """S등급 검증"""
        return (
            len(self.segments) >= 3
            and all(s.text.strip() for s in self.segments)
            and self.port_name != ""
        )
```

---

## 점수 추이 예상

```
Phase S1 완료 후:
┌──────────────────────────────────────────────────────┐
│ 기능 완성도: ████████████████████░░░░░  21/25 (+1)   │
│ 아키텍처:    ████████████░░░░░░░░░░░░  12/20 (유지)  │
│ 성능:        ███████████████░░░░░░░░░  15/15 (유지)  │
│ 보안:        ███████████████░░░░░░░░░  15/15 (+5)    │
│ 테스트:      ░░░░░░░░░░░░░░░░░░░░░░░   0/15 (유지)  │
│ 코드 품질:   ██████████████████████░░  11/10 (유지)  │
│ 총점:        ███████████████████████░  88/100 (+10)  │
└──────────────────────────────────────────────────────┘

Phase S2 완료 후:
┌──────────────────────────────────────────────────────┐
│ 기능 완성도: █████████████████████████  25/25 (+4)   │
│ 아키텍처:    ████████████████░░░░░░░░  16/20 (+4)   │
│ 성능:        ███████████████░░░░░░░░░  15/15 (유지)  │
│ 보안:        ███████████████░░░░░░░░░  15/15 (유지)  │
│ 테스트:      ██████░░░░░░░░░░░░░░░░░░   6/15 (+6)   │
│ 코드 품질:   ██████████████████░░░░░░   9/10 (-2)   │
│ 총점:        █████████████████████████ 95/100 (+7)  │
└──────────────────────────────────────────────────────┘
                                        ↑ S등급 달성!
```

---

## 실행 체크리스트

### Phase S1 (오늘 4시간)
- [ ] S1-1: Config 이중 정의 제거 (15분)
- [ ] S1-2: API 키 보안 강화 (60분)
  - [ ] test_gemini_models.py 하드코딩 제거
  - [ ] 전역 하드코딩 API 키 검색 + 제거
  - [ ] 에러 로그 API 키 마스킹
- [ ] S1-3: P0-5 Outro 애니메이션 재수정 (40분)
- [ ] S1-4: Path Traversal 방어 (30분)
- [ ] S1-5: Prompt Injection 강화 (30분)

### Phase S2 (내일 8시간)
- [ ] S2-1: God Object 분리 (4시간)
  - [ ] tts_engine.py 추출
  - [ ] audio_mixer.py 추출
  - [ ] overlay_renderer.py 추출
  - [ ] visual_composer.py 추출
  - [ ] Orchestrator 리팩토링
- [ ] S2-2: 단위 테스트 30개 작성 (4시간)
  - [ ] test_config.py (5개)
  - [ ] test_script_validation.py (8개)
  - [ ] test_subtitle_renderer.py (5개)
  - [ ] test_asset_matcher.py (5개)
  - [ ] test_bgm_matcher.py (4개)
  - [ ] test_security.py (3개)

### Phase S3 (이번 주 13시간)
- [ ] S3-1: 이미지 매칭 역 인덱스 (2시간)
- [ ] S3-2: TTS 병렬화 (3시간)
- [ ] S3-3: BGM 메타데이터 캐싱 (1시간)
- [ ] S3-4: 자막 폰트 캐싱 (1시간)
- [ ] S3-5: Magic Numbers 상수화 (1시간)
- [ ] S3-6: Dead Code 정리 (30분)
- [ ] 추가 테스트 30개 (4.5시간)

### Phase S4 (다음 주 12시간)
- [ ] S4-1: Strategy Pattern (3시간)
- [ ] S4-2: Dependency Injection (2시간)
- [ ] S4-3: E2E 테스트 5개 (4시간)
- [ ] S4-4: Dict → Dataclass (3시간)

---

## 리스크 분석

| 리스크 | 확률 | 영향 | 완화 |
|--------|------|------|------|
| God Object 분리 시 의존성 깨짐 | 중간 | 높음 | 점진적 추출 + 테스트 선행 |
| API 키 재발급 서비스 중단 | 낮음 | 높음 | .env.backup 보관 |
| 테스트 작성 시간 초과 | 높음 | 중간 | 30개→20개 축소 가능 |
| 성능 개선 후 비호환 | 낮음 | 중간 | 기존 API 유지 (Facade) |

---

## 작업지시서 승인

**작성자**: Claude Code (6-Agent 통합)
**승인 요청**: S등급 달성 Phase S1~S4 실행 승인
**예상 효과**: 78점 → 95점 (S등급, +21.8%)
**투자 시간**: 37시간 (5일)
**ROI**: 0.57점/시간

---

*"S등급은 기능이 되는 것이 아니라, 엔진이 짱짱한 것이다"*
*— 6-Agent Consensus, 2026-03-09*
