# 성능 최적화 구현 가이드

## 우선순위 1: AssetMatcher 인덱스 캐싱 (30분)

### 구현 파일
- src/utils/asset_matcher.py

### 변경 내용
캐시 파일 경로:
- D:/mabiz/cache/asset_index.pkl
- D:/mabiz/cache/asset_index_meta.json

기대 효과:
- 인덱싱: 2초 → 0.05초 (40배 빠름)

---

## 우선순위 2: SupertoneTTS 병렬 생성 (1시간)

### 구현 파일
- engines/supertone_tts.py

### 변경 내용
ThreadPoolExecutor 활용 (max_workers=4)

기대 효과:
- TTS 생성: 15초 → 5초 (3배 빠름)

---

## 우선순위 3: FFmpegPipeline 병렬 렌더링 (2시간)

### 구현 파일
- engines/ffmpeg_parallel_renderer.py (신규)

### 변경 내용
NVENC 3세션 병렬 렌더링

기대 효과:
- 렌더링: 28초 → 12초 (2.3배 빠름)

---

## 총 예상 효과

현재: 28초 (1.78x)
최적화 후: 12초 (4.16x, 목표 233% 초과)

영상 생성량: 150편/월 → 350편/월 (+133%)
