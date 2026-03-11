# Asset Matcher 사용 가이드

## 개요

**AssetMatcher**는 키워드 기반으로 로컬 이미지/영상 에셋을 자동 매칭하는 엔진입니다.

- **인덱싱**: 4,802개 에셋 자동 스캔
- **기항지 우선**: 178개 기항지 50점 가중치
- **Content Type별 우선순위**: Hook/Body/Trust/CTA/Outro
- **Visual Interleave**: 80% 이미지, 20% 영상
- **Hook 3단계 fallback**: Hook폴더 → Footage → AI영상 → 랜덤

---

## 인덱싱 경로

```python
ASSET_PATHS = {
    # 이미지
    "cruise_photos": "D:/AntiGravity/Assets/Image/크루즈정보사진정리",  # 2,916장
    "review_images": "D:/AntiGravity/Assets/Image/후기",
    "general_images": "D:/AntiGravity/Assets/Image",
    "ai_generated": "D:/AntiGravity/Output/1_Raw_Images",
    "face_swapped": "D:/AntiGravity/Output/2_Face_Swapped",
    "cutouts": "D:/AntiGravity/Output/Cutouts_Auto",
    "cutouts_manual": "D:/AntiGravity/Assets/누끼파일",

    # 영상
    "hook_videos": "D:/AntiGravity/Assets/Footage/Hook",  # 104개 Hook 전용
    "footage": "D:/AntiGravity/Assets/Footage",
    "ai_videos": "D:/AntiGravity/Output/3_Videos",
}
```

---

## 1. 기본 사용법

### 싱글톤 인스턴스 가져오기

```python
from src.utils.asset_matcher import get_asset_matcher

matcher = get_asset_matcher()
```

### 키워드 기반 에셋 매칭

```python
matches = matcher.match_assets(
    keywords=["산토리니", "그리스", "에게해"],
    content_type="Body",  # "Hook", "Body", "Trust", "CTA", "Outro"
    max_results=10,
    prefer_images=True,  # 이미지 우선 (80%)
    allow_videos=True    # 영상 허용 (20%)
)

for match in matches:
    print(f"경로: {match.path}")
    print(f"점수: {match.score}")
    print(f"타입: {match.asset_type}")  # "image" or "video"
    print(f"매칭 키워드: {match.matched_keywords}")
```

---

## 2. Hook 영상 선택

### Hook 전용 영상 (3단계 fallback)

```python
hook_video = matcher.get_hook_video(
    keywords=["크루즈", "나가사키"],
    fallback=True  # fallback 허용
)

if hook_video:
    print(f"Hook 영상: {hook_video}")
```

**Fallback 순서**:
1. **Hook 폴더** 키워드 매칭 (104개)
2. **Footage 폴더** 키워드 매칭
3. **AI 영상** 키워드 매칭
4. **Hook 폴더** 랜덤 선택 (최후)

---

## 3. Visual Interleave (이미지/비디오 교차)

### 46초 메인 비주얼 세그먼트 생성

```python
segments = matcher.get_visual_segments(
    keywords=["산토리니", "그리스", "에게해"],
    total_duration=46.0,  # 55초 - Hook(3초) - Outro(2.5초) - CTA(3.0초)
    content_type="Body",
    interleave_ratio=0.8  # 80% 이미지, 20% 영상
)

for seg in segments:
    print(f"경로: {seg.path}")
    print(f"길이: {seg.duration}초")
    print(f"타입: {seg.asset_type}")  # "image" or "video"

    if seg.asset_type == "image":
        print(f"Ken Burns: {seg.ken_burns_type}")  # zoom_in, zoom_out, pan_left, pan_right
```

**세그먼트 특징**:
- 세그먼트당 5-7초 (랜덤)
- 이미지: Ken Burns 효과 자동 적용
- 영상: 원본 재생

---

## 4. 누끼 파일 매칭

### 카테고리별 누끼 에셋 선택

```python
cutout = matcher.get_cutout_asset(
    keywords=["뷔페", "정찬"],
    category="식사"  # "식사", "선내시설", "액티비티", "기항지", "Trust"
)

if cutout:
    print(f"누끼 파일: {cutout}")
```

**카테고리 키워드**:
- **식사**: 뷔페, 정찬, 다이닝, 레스토랑
- **선내시설**: 수영장, 스파, 카지노, 극장
- **액티비티**: 공연, 쇼, 파티
- **기항지**: 178개 기항지명
- **Trust**: 후기, 만족, 리뷰

---

## 5. Content Type별 우선순위

### Phase 28 FIX-8: 후기 이미지 우선

```python
CONTENT_TYPE_PRIORITY = {
    "Hook": ["hook_videos", "footage", "ai_videos"],  # Hook 전용 폴더 우선
    "Body": ["cruise_photos", "general_images", "ai_generated", "face_swapped"],
    "Trust": ["review_images", "cruise_photos"],  # 후기 이미지 우선
    "CTA": ["review_images", "cruise_photos"],  # 후기 이미지 우선
    "Outro": ["review_images", "cruise_photos"],  # 후기 이미지 우선
}
```

**Trust/CTA/Outro**에서는 `review_images` 폴더 우선 선택.

---

## 6. 매칭 점수 계산

### 점수 구성 (0-100)

```python
score = 0

# 1. 키워드 매칭
for keyword in keywords:
    if keyword in PROPER_NOUNS_PORTS:  # 기항지
        score += 50.0  # 기항지는 2배 가중치
    else:
        score += 10.0

# 2. 카테고리 우선순위
if asset_category == priority_categories[0]:
    score += 20.0  # 1순위
elif asset_category == priority_categories[1]:
    score += 10.0  # 2순위

# 3. 최대 100점
score = min(score, 100.0)
```

**예시**:
- **"산토리니" (기항지)**: 50점
- **"산토리니" + "그리스"**: 60점
- **"산토리니" + "cruise_photos" 1순위**: 70점

---

## 7. 파이프라인 통합 예시

### generate_video_55sec_pipeline.py 통합

```python
from src.utils.asset_matcher import get_asset_matcher

# 초기화
matcher = get_asset_matcher()

# Hook 영상 선택
hook_video = matcher.get_hook_video(
    keywords=script["hook"]["keywords"],
    fallback=True
)

# Body 비주얼 세그먼트
body_segments = matcher.get_visual_segments(
    keywords=script["body"]["keywords"],
    total_duration=46.0,
    content_type="Body",
    interleave_ratio=0.8
)

# Trust 이미지
trust_images = matcher.match_assets(
    keywords=script["trust"]["keywords"],
    content_type="Trust",
    max_results=3,
    prefer_images=True,
    allow_videos=False
)

# CTA 배경
cta_background = matcher.match_assets(
    keywords=script["cta"]["keywords"],
    content_type="CTA",
    max_results=1,
    prefer_images=True
)[0].path

# 누끼 오버레이
cutout_overlay = matcher.get_cutout_asset(
    keywords=["후기", "만족"],
    category="Trust"
)
```

---

## 8. 키워드 추출 연동

### IntelligentKeywordExtractor 통합

```python
from engines.keyword_extraction.intelligent_keyword_extractor import (
    IntelligentKeywordExtractor
)
from src.utils.asset_matcher import get_asset_matcher

# 키워드 추출
extractor = IntelligentKeywordExtractor()
keywords = extractor.extract_simple(
    text="산토리니 파란 지붕 에게해 일몰",
    section="body",
    top_n=10
)

# 에셋 매칭
matcher = get_asset_matcher()
matches = matcher.match_assets(
    keywords=keywords,
    content_type="Body"
)
```

---

## 9. 성능 최적화

### 인덱싱 캐시

- **1회 인덱싱**: 초기화 시 4,802개 에셋 스캔
- **메모리 캐시**: `_asset_cache` 딕셔너리
- **키워드 캐시**: 경로 분석 결과 저장

### 빠른 매칭

- **O(1) 캐시 조회**: 키워드별 에셋 매칭
- **점수 계산 최적화**: 기항지 우선 필터링

---

## 10. 디버깅

### 로깅 활성화

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='[%(levelname)s] %(message)s'
)

# AssetMatcher 로그
# [INFO] [AssetMatcher] 초기화 완료 - 인덱싱: 4802개 에셋
# [INFO] [Hook] 1단계 매칭: cruise_video.mp4 (점수: 75.0)
# [INFO] [VisualSegments] 6개 생성 (이미지: 5, 영상: 1)
```

### 매칭 결과 확인

```python
matches = matcher.match_assets(keywords=["산토리니"])

for match in matches:
    print(f"경로: {match.path}")
    print(f"점수: {match.score}")
    print(f"매칭 키워드: {match.matched_keywords}")
```

---

## 주요 변경 이력

| 날짜 | Phase | 내용 |
|------|-------|------|
| 2026-03-08 | B-9 | AssetMatcher 완전 재구축 (4,802개 에셋 인덱싱) |
| 2026-02-20 | 28 | FIX-4 Hook 전용 폴더 우선, FIX-8 후기 이미지 CTA 연동 |
| 2026-02-20 | 28 | FIX-3 PROPER_NOUNS_PORTS 178개 (유럽/알래스카) |

---

## 참고 파일

- `src/utils/asset_matcher.py` - 메인 코드
- `engines/keyword_extraction/intelligent_keyword_extractor.py` - 키워드 추출
- `video_pipeline/config.py` - 파이프라인 설정
- `generate_video_55sec_pipeline.py` - 파이프라인 통합

---

## FAQ

**Q1. Hook 영상이 매칭되지 않을 때?**

A. 4단계 fallback이 작동하여 Hook 폴더에서 랜덤 선택합니다.

**Q2. 기항지 키워드 매칭 안 됨?**

A. `PROPER_NOUNS_PORTS`에 기항지명이 있는지 확인하세요. (178개 지원)

**Q3. 이미지/영상 비율 변경?**

A. `interleave_ratio=0.7`로 설정하면 70% 이미지, 30% 영상입니다.

**Q4. 커스텀 에셋 경로 추가?**

A. `ASSET_PATHS`에 경로를 추가하고 `_index_assets()` 재실행하세요.

**Q5. 매칭 점수 임계값 변경?**

A. `config.py`에서 `pop_match_threshold=30` 값을 조정하세요.

---

**작성**: Claude Code (code-writer)
**날짜**: 2026-03-08
**Phase**: B-9 Asset Matcher Reconstruction
