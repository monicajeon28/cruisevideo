# WO v12.0: 비주얼 품질 업그레이드 작업지시서

**작성일**: 2026-03-11
**기반 분석**: 3개 전문 에이전트 병렬 심층 검토
- Production Animation Expert
- Creative Director + Senior Python Developer
- Architecture & Efficiency Expert

**현재 상태**: S-grade 97점 달성, MoviePy+FFmpeg+NVENC 파이프라인
**목표**: 프로덕션급 비주얼 품질 → 상위 1% YouTube Shorts 수준

---

## 전략 결정: Remotion vs MoviePy 강화

### 3개 에이전트 만장일치 결론: **MoviePy 강화 (Remotion 보류)**

| 기준 | MoviePy 강화 | Remotion 마이그레이션 | Hybrid |
|------|-------------|---------------------|--------|
| 구현 시간 | **20-40시간** | 120-200시간 | 60-120시간 |
| 시각 품질 | 6/10 → **8/10** | 9/10 | 8/10 |
| 렌더 속도 | **30-60초 (NVENC)** | 2-5분 (Chromium) | 혼합 |
| 유지보수 | **단일 Python** | Python+Node.js | 2개 런타임 |
| 한글 지원 | **PIL 검증완료** | CSS CJK 미검증 | 혼합 |
| EXE 배포 | **PyInstaller 준비됨** | Node.js 번들 필요 | 불가능 |
| 종합 점수 | **7.1/10** | 5.3/10 | 5.4/10 |

**결론**: MoviePy Phase 0+1이 Remotion 대비 **80% 비주얼 향상을 10% 노력**으로 달성.
Remotion은 틱톡 스타일 단어별 자막이 필요할 때만 재검토.

---

## Phase 0: 즉시 수정 (CRITICAL, 완료됨)

| # | 수정 | 상태 | 파일 |
|---|------|------|------|
| 0-1 | 인트로 SFX 제거 → 나레이션 즉시 시작 | **완료** | `audio_mixer.py` |
| 0-2 | 아웃트로 로고 중복 제거 (워터마크 아웃트로 전 중단) | **완료** | `video_composer.py` |
| 0-3 | 자막 좌우 패딩 120px + 반투명 배경 바 | **완료** | `subtitle_image_renderer.py` |
| 0-4 | SFX 파일명 일치 (level-up, hit_impact, swoosh) | **완료** | `audio_mixer.py` |
| 0-5 | Pop SFX를 metadata 타이밍 기반으로 변경 | **완료** | `audio_mixer.py` |
| 0-6 | 스마트 텍스트 절삭 (Trust 우선 보존) | **완료** | `comprehensive_script_generator.py` |

---

## Phase 1: Hook 즉시 나레이션 (CRITICAL, 2시간)

### 문제
- 현재: Hook 구간 0-3초 = **무음** (BGM만 재생, TTS 없음)
- `audio_mixer.py` line 174: "Hook 구간: 무음"
- `generate_video_55sec_pipeline.py` line 633: Hook segment TTS 스킵

### 해결
Hook TTS를 0.0초부터 재생하여 시청자가 즉시 후킹 나레이션을 듣게 함.

### 변경 파일
1. **`generate_video_55sec_pipeline.py`**: `_synthesize_one()`에서 Hook segment도 TTS 생성
2. **`audio_mixer.py`**: Hook 구간 무음 로직 제거, TTS 0.0초부터 배치

### 상세 코드 변경

**`generate_video_55sec_pipeline.py`** (Hook TTS 활성화):
```python
# BEFORE: Hook은 TTS 스킵
if segment_type == 'hook':
    return (idx, None, hook_duration)

# AFTER: Hook도 TTS 생성
# Hook segment도 다른 segment와 동일하게 TTS 생성
# (hook_duration만큼만 재생되도록 audio_mixer에서 조정)
```

**`audio_mixer.py`** (Hook 무음 해제):
```python
# BEFORE: Hook 구간은 silent
if i == 0 and is_hook:
    continue  # skip hook TTS

# AFTER: Hook TTS를 0.0초에 배치
# Hook TTS가 있으면 0.0초부터 재생
```

---

## Phase 2: 자막 시스템 완전 개선 (HIGH, 4시간)

### 2-1. 자막 Y 위치 안전 영역 이동
- **현재**: `self.height - 200` = 1720px (하단 200px) → YouTube 하단 UI와 겹침
- **변경**: `self.height - 350` = 1570px (하단 350px) → 안전 영역 내
- YouTube Shorts 하단 15% = 288px 이므로 350px이면 안전

### 2-2. 자막 배경 바 render_to_file에도 적용
- `render_subtitle()`은 이미 반투명 배경 추가 (Phase 0-3)
- `render_to_file()`에도 동일 적용 필요

### 2-3. config 값 반영 (기존 버그 수정)
- `subtitle_bg_enabled`, `subtitle_bg_opacity`, `subtitle_bg_padding` 설정이 존재하나 **미사용**
- config 값을 실제 렌더러에 연결

### 2-4. 자막 Fade In/Out
- 각 자막 세그먼트에 0.2초 FadeIn + 0.15초 FadeOut
- 현재: 자막이 갑자기 나타나고 갑자기 사라짐
- `_create_subtitles()`에서 `vfx.FadeIn(0.2)` + `vfx.FadeOut(0.15)` 적용

### 변경 파일
- `engines/subtitle_image_renderer.py`
- `pipeline_render/video_composer.py`

---

## Phase 3: Pop 메시지 비주얼 업그레이드 (HIGH, 6시간)

### 현재 문제
- 노란 글씨 + 빨간 스트로크 = 시각적으로 저렴함
- 배경 없음 → 밝은 영상 위에서 가독성 떨어짐

### 3가지 Pop 스타일 구현

#### Style 1: Info Badge (기본)
- 반투명 검정 pill 모양 배경 (둥근 양끝)
- 흰색 텍스트, 스트로크 없음
- 위치: 화면 상단 1/3 중앙
- 용도: 일반 정보 ("벨리시마호 5성급 시설 보유")

#### Style 2: Price Card
- 넓은 둥근 사각형 카드
- 2줄: 라벨(작은 회색) + 금액(큰 골드)
- 위치: 화면 중앙
- 용도: 가격 정보 ("1인 89만원", "총 비용 120만원")

#### Style 3: Highlight Bar
- 전체 너비 반투명 바
- 왼쪽 골드 accent 바 (4px)
- 키워드 하이라이트 (숫자를 골드로)
- 용도: 핵심 강조 ("2억 보험 자동 포함")

### 구현 방식
- PIL로 각 스타일의 배경 이미지를 렌더 → numpy 배열 → `ImageClip`
- `config.pop_style` 설정으로 선택 ("badge" / "card" / "bar" / "classic")
- `_create_single_pop()`에서 스타일별 분기

### Scale-In 애니메이션
- 현재 `_apply_pop_motion()`은 FadeOut만 적용
- **추가**: 0.3초 Scale-In (0.6x → 1.0x) + 0.5초 Pulse + 0.2초 FadeOut
- MoviePy `clip.transform()`으로 프레임별 scale 적용
- 또는 FFmpeg 경로의 기존 `get_pop_motion_filter()` expression 활용

### 변경 파일
- `pipeline_render/video_composer.py`
- `video_pipeline/config.py` (pop_style 추가)

---

## Phase 4: 장면 전환 효과 (MEDIUM, 4시간)

### 현재
- 단순 하드컷 또는 CrossFadeIn/Out (0.35초)

### 추가할 전환 3종

#### 4-1. Fade to Black
- 0.15초 검정 컬러클립 삽입
- 용도: "챕터 전환" 느낌 (Block 변경 시)
- 구현: 간단한 `ColorClip` 삽입

#### 4-2. Wipe Left
- 다음 클립이 오른쪽에서 슬라이드인
- 용도: "다음 주제" 전환
- 구현: `clip.with_position(lambda t: ...)` 위치 애니메이션

#### 4-3. 감정 기반 전환 자동 선택
- `visual_effects.py`의 `TRANSITION_MAP` + `select_transition()` 이미 존재하나 **미사용**
- 감정 점수에 따라 자동 선택: 안심→crossfade, 공감→fade_black, 동경→wipe, 확신→zoom

### 변경 파일
- `pipeline_effects/visual_effects.py`
- `pipeline_render/video_composer.py` (`_create_timeline()`에서 전환 적용)

---

## Phase 5: 정보 카드 시각화 모듈 (MEDIUM, 8시간)

### Remotion 가이드에서 MoviePy로 구현 가능한 5가지

#### 5-1. Number Highlight
- 큰 숫자 강조 디스플레이: "총 비용 89만원"
- PIL 렌더 → ImageClip

#### 5-2. Comparison Card
- 좌우 비교: "발코니 vs 내측 선실"
- 2컬럼 PIL 레이아웃

#### 5-3. Pros/Cons Card
- 체크마크(녹색) / X(빨강) 리스트
- PIL 아이콘 + 텍스트

#### 5-4. Itinerary Timeline
- Day 1 → Day 2 → Day 3 수직 타임라인
- 크루즈 기항지 핵심 정보

#### 5-5. Price Breakdown
- "크루즈 vs 호텔+항공" 비용 비교 표
- 골드 하이라이트로 "승자" 행 표시

### 신규 모듈
```python
# pipeline_render/card_renderer.py
class CardRenderer:
    def render_number_highlight(self, label, value, accent_color) -> np.ndarray
    def render_comparison(self, left_items, right_items) -> np.ndarray
    def render_pros_cons(self, pros, cons) -> np.ndarray
    def render_itinerary(self, stops: List[dict]) -> np.ndarray
    def render_price_breakdown(self, items: List[dict]) -> np.ndarray
```

### 스크립트 연동
- `comprehensive_script_generator.py`에서 `segment_type`에 "card_price", "card_compare" 등 추가
- `video_composer.py`에서 segment_type별 카드 렌더러 호출

---

## Phase 6: Ken Burns + 감정 색보정 (LOW, 4시간)

### 6-1. Ken Burns 감정 가중치 활성화
- `config.ken_burns_emotion_weight_enabled = False` → `True`
- 이미 구현되어 있으나 비활성화 상태
- 감정별 줌 강도 자동 조절

### 6-2. 세그먼트 감정별 색보정 오버레이
- 안심(따뜻) → 약간 따뜻한 톤 오버레이
- 동경(시원) → 약간 시원한 톤 오버레이
- ColorClip 반투명 레이어로 간단 구현

---

## 우선순위 요약

| Phase | 핵심 | 임팩트 | 노력 | 우선순위 |
|-------|------|--------|------|---------|
| **0** | 즉시 수정 (SFX, 자막, Pop, Trust) | CRITICAL | **완료** | **완료** |
| **1** | Hook 즉시 나레이션 | CRITICAL (리텐션) | 2시간 | **P0** |
| **2** | 자막 안전영역 + Fade + config 연결 | HIGH (가독성) | 4시간 | **P0** |
| **3** | Pop 배지 스타일 + Scale-In 애니메이션 | HIGH (품질) | 6시간 | **P1** |
| **4** | 장면 전환 3종 + 감정 자동선택 | MEDIUM (흐름) | 4시간 | **P1** |
| **5** | 정보 카드 시각화 모듈 | MEDIUM (다양성) | 8시간 | **P2** |
| **6** | Ken Burns 감정 + 색보정 | LOW (분위기) | 4시간 | **P2** |

**총 예상 시간**: Phase 1-2 (P0) = 6시간, Phase 3-4 (P1) = 10시간, Phase 5-6 (P2) = 12시간

---

## Remotion 재검토 조건

다음 중 하나라도 해당하면 Remotion Hybrid 재검토:
1. 틱톡 스타일 단어별 자막 애니메이션이 필수가 될 때
2. 웹 기반 미리보기/편집기가 필요할 때
3. 타겟 오디언스가 2030 세대로 확장될 때
4. 정보 시각화(차트, 대시보드) 비중이 50% 이상일 때

---

## 변경 파일 목록

| 파일 | Phase | 변경 유형 |
|------|-------|----------|
| `pipeline_render/audio_mixer.py` | 0, 1 | SFX 수정, Hook 나레이션 |
| `pipeline_render/video_composer.py` | 0, 2, 3, 4 | 로고, Pop, 전환, 자막 |
| `engines/subtitle_image_renderer.py` | 0, 2 | 배경 바, 안전영역, config |
| `engines/comprehensive_script_generator.py` | 0 | 스마트 절삭 |
| `generate_video_55sec_pipeline.py` | 1 | Hook TTS 활성화 |
| `pipeline_effects/visual_effects.py` | 4, 6 | 전환, Ken Burns |
| `video_pipeline/config.py` | 2, 3, 6 | 새 설정값 |
| `pipeline_render/card_renderer.py` | 5 | **신규 생성** |
