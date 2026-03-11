# WO v9.0 - CruiseDot EXE 배포 엔진 작업지시서

**작성일**: 2026-03-10
**버전**: v9.0 (EXE Deployment)
**목표**: Python 파이프라인 → 단독 실행 EXE 배포
**분석 기반**: 6개 전문 에이전트 종합 (Architecture, Dependencies, Refactoring, Security, Performance, Code Quality)

---

## Executive Summary

| 항목 | 현재 상태 | 목표 |
|------|----------|------|
| **배포 형태** | python generate.py (개발 환경 필수) | CruiseDot.exe (단독 실행) |
| **프로젝트 크기** | ~500+ 파일 | ~25개 코어 파일 |
| **데드 코드** | ~200+ 미사용 파일 | 0개 |
| **하드코딩 경로** | 60+ 인스턴스 (D:\mabiz 등) | 0개 (PathResolver) |
| **print() 호출** | 308개 (EXE 크래시 원인) | 0개 (전체 logger) |
| **EXE 크기 예상** | - | ~150-200MB (최적화 후) |
| **외부 의존성** | 35+ 패키지 | 7개 코어 |
| **보안 이슈** | 4 CRITICAL + 6 HIGH | 0 CRITICAL |
| **예상 작업일** | - | **11-15일** |

---

## CRITICAL BLOCKERS (EXE 빌드 불가 원인 3건)

### BLOCKER-1: print() 308개 → Windowed EXE 크래시

**증상**: PyInstaller `--windowed` 모드에서 `sys.stdout = None`이므로 모든 `print()` 호출이 `AttributeError` 발생

**규모**: 30개 파일, 308개 print() 호출

| 파일 | print 수 | 우선순위 |
|------|---------|---------|
| engines/comprehensive_script_generator.py | 61 | P0 (코어) |
| batch_scripts/bulk_script_orchestrator.py | 24 | P1 |
| generate.py | 20 | P0 (진입점) |
| engines/sgrade_constants.py | 19 | P0 (코어) |
| batch_scripts/daily_topics_generator.py | 14 | P1 |
| engines/bgm_matcher.py | 13 | P0 (코어) |
| engines/color_correction.py | 10 | P0 (코어) |
| 기타 23개 파일 | 147 | P1-P2 |

**해결**: 전체 `print()` → `logger.info()` / `logger.debug()` 마이그레이션

### BLOCKER-2: 하드코딩 절대경로 60+ 인스턴스

**증상**: `D:\mabiz\`, `D:\AntiGravity\Assets\`, `C:\Windows\Fonts` 등 개발기 전용 경로가 배포 환경에 없음

**핵심 위치**:

| 파일 | 라인 | 하드코딩 |
|------|------|---------|
| generate_video_55sec_pipeline.py | 73, 168, 179-180, 244, 444, 480-481, 607, 818 | D:\mabiz, D:\AntiGravity |
| video_pipeline/config.py | 80, 171, 195 | D:\mabiz |
| engines/ffmpeg_pipeline.py | 87, 744-784 | D:\mabiz, ffmpeg 경로 |
| src/utils/asset_matcher.py | 59-70 | D:\AntiGravity\Assets |
| engines/bgm_matcher.py | 37 | D:\AntiGravity |
| subtitle_image_renderer.py | - | C:\Windows\Fonts |

**해결**: PathResolver 패턴 도입 (env → paths.yaml → EXE상대 → fallback)

### BLOCKER-3: batch_renderer.py의 subprocess python 호출

**증상**: `subprocess.run(["python", "generate.py", ...])` — Frozen EXE에서 `python` 인터프리터 없음

**위치**: `cli/batch_renderer.py` (배치 렌더링 진입점)

**해결**: `subprocess.run([sys.executable, ...])` 또는 in-process 호출로 전환

---

## Phase 0: 데드 코드 정리 (1일)

### 목적
~200개 미사용 파일 삭제 → 프로젝트 25개 코어 파일로 축소

### 삭제 대상

| 디렉토리 | 미사용 파일 수 | 설명 |
|----------|--------------|------|
| engines/ | ~85+ | 초기 프로토타입, 중복 엔진 |
| src/ | ~90+ | 레거시 유틸리티, 테스트 |
| batch_scripts/ | ~10 | 이전 배치 시스템 |
| video_pipeline/ | ~5 | 미사용 모듈 |
| Dmabiz*.py | ~10 | 손상된 루트 파일 |
| *.spec (테스트용) | 2 | cruise_ai_mini.spec, exe_bundle_test.spec |
| requirements*.txt (중복) | ~20 | 16개 requirements 파일 → 2개로 통합 |

### 보존 대상 (코어 파이프라인 ~25파일)

```
generate.py                          # CLI 진입점
generate_batch.py                    # 배치 진입점
generate_video_55sec_pipeline.py     # 메인 파이프라인 (854줄)

cli/
  auto_mode.py                       # 자동 모드
  config_loader.py                   # 설정 로더
  generation_log.py                  # 생성 로그
  batch_renderer.py                  # 배치 렌더러
  batch_quality_gate.py              # 품질 게이트
  weekly_report.py                   # 주간 보고서

pipeline_effects/
  visual_effects.py                  # Ken Burns + 색보정

pipeline_render/
  audio_mixer.py                     # 오디오 믹싱
  visual_loader.py                   # 이미지/비디오 로더
  video_composer.py                  # 최종 합성

video_pipeline/
  config.py                          # PipelineConfig (SSOT)
  gpu_detector.py                    # GPU 감지

engines/ (코어만)
  comprehensive_script_generator.py  # 대본 생성 (2118줄 - Phase 2에서 리팩토링)
  supertone_tts.py                   # TTS API
  ffmpeg_pipeline.py                 # FFmpeg 렌더링
  subtitle_image_renderer.py         # 자막 렌더링
  bgm_matcher.py                     # BGM 매칭
  color_correction.py                # 색보정
  s_grade_validator.py               # S등급 채점
  hook_generator.py                  # 후킹 생성
  rehook_injector.py                 # Re-Hook
  cta_optimizer.py                   # CTA 최적화
  pop_message_validator.py           # Pop 검증
  asset_diversity_manager.py         # 에셋 다양성

src/utils/
  asset_matcher.py                   # 이미지 매칭
```

### 실행 방법
```bash
# 1. 백업 브랜치 생성
git checkout -b backup/pre-exe-cleanup

# 2. 코어 파일 목록 확인 후 나머지 삭제
# 3. requirements.txt 통합 (requirements_core.txt + requirements_dev.txt)
```

### 검증
- [ ] `python generate.py --help` 정상 동작
- [ ] `python generate.py --fallback --port MED_BARCELONA` 1편 생성 성공
- [ ] import 에러 0건

---

## Phase 1: CRITICAL EXE 블로커 해소 (3일)

### 1-1. print() → logger 마이그레이션 (1.5일)

**원칙**:
- `print(f"...")` → `logger.info(f"...")`
- 진행률 표시 print → `logger.info` + tqdm (선택)
- 에러 print → `logger.error`
- 디버그 print → `logger.debug`

**파일별 작업량**:

| 파일 | print 수 | 난이도 | 예상시간 |
|------|---------|--------|---------|
| engines/comprehensive_script_generator.py | 61 | 중 | 2h |
| generate.py | 20 | 하 | 30m |
| engines/sgrade_constants.py | 19 | 하 | 30m |
| engines/bgm_matcher.py | 13 | 하 | 20m |
| engines/color_correction.py | 10 | 하 | 15m |
| batch_scripts/*.py | 38 | 중 | 1h |
| 기타 24개 파일 | 147 | 하-중 | 3h |

**안전장치 (runtime_hook)**:
```python
# build_hooks/runtime_hook_stdout.py
import sys, os
if getattr(sys, 'frozen', False):
    if sys.stdout is None:
        sys.stdout = open(os.devnull, 'w')
    if sys.stderr is None:
        sys.stderr = open(os.devnull, 'w')
```

### 1-2. 하드코딩 경로 → PathResolver (1일)

**PathResolver 구현**:
```python
# video_pipeline/path_resolver.py
class PathResolver:
    """4단계 경로 해석: env → paths.yaml → EXE상대 → fallback"""

    def __init__(self):
        self._exe_dir = self._get_exe_dir()
        self._config = self._load_paths_yaml()

    @staticmethod
    def _get_exe_dir() -> Path:
        if getattr(sys, 'frozen', False):
            return Path(sys.executable).parent
        return Path(__file__).parent.parent

    def resolve(self, key: str) -> Path:
        # 1. 환경변수
        env_val = os.environ.get(f"CRUISEDOT_{key.upper()}")
        if env_val and Path(env_val).exists():
            return Path(env_val)

        # 2. paths.yaml
        yaml_val = self._config.get(key)
        if yaml_val and Path(yaml_val).exists():
            return Path(yaml_val)

        # 3. EXE 상대경로
        relative = self._exe_dir / self.DEFAULTS[key]
        if relative.exists():
            return relative

        # 4. 개발환경 fallback
        return Path(self.DEV_DEFAULTS[key])

    DEFAULTS = {
        'assets_root': 'assets',
        'output_root': 'outputs',
        'sfx_dir': 'assets/sfx',
        'bgm_dir': 'assets/bgm',
        'fonts_dir': 'fonts',
        'temp_dir': 'temp',
    }

    DEV_DEFAULTS = {
        'assets_root': r'D:\AntiGravity\Assets',
        'output_root': r'D:\mabiz\outputs',
        'sfx_dir': r'D:\AntiGravity\Assets\sfx',
        'bgm_dir': r'D:\AntiGravity\Assets\bgm',
        'fonts_dir': r'C:\Windows\Fonts',
        'temp_dir': r'D:\mabiz\temp',
    }
```

**마이그레이션 대상** (42개 위치):
- `generate_video_55sec_pipeline.py` (8곳)
- `video_pipeline/config.py` (3곳)
- `engines/ffmpeg_pipeline.py` (4곳)
- `src/utils/asset_matcher.py` (3곳)
- 기타 engines/*.py (24곳)

### 1-3. subprocess python → sys.executable (0.5일)

**현재** (cli/batch_renderer.py):
```python
subprocess.run(["python", "generate.py", ...])
```

**수정**:
```python
import sys
subprocess.run([sys.executable, "generate.py", ...])
```

**추가 검토**: engines/ffmpeg_pipeline.py의 subprocess 호출도 EXE 환경에서 ffmpeg 경로 동적 해석 필요

### Phase 1 검증
- [ ] 프로젝트 내 `print(` 검색 결과 0건 (테스트 코드 제외)
- [ ] `D:\mabiz` / `D:\AntiGravity` 하드코딩 0건
- [ ] `subprocess.run(["python"` 0건
- [ ] Fallback 모드 1편 생성 성공

---

## Phase 2: God Object 분리 + 코드 정리 (2일)

### 2-1. comprehensive_script_generator.py 분리 (2118줄 → 4모듈)

현재 이 파일은 새로운 God Object로, S등급 채점/대본 생성/Gemini API/프롬프트 관리를 모두 포함.

**분리 계획**:
```
engines/
  script_generator/
    __init__.py                    # public API re-export
    generator.py                   # Gemini API 호출 + 대본 생성 (~500줄)
    prompt_builder.py              # 프롬프트 템플릿 관리 (~400줄)
    fallback_templates.py          # Fallback 대본 템플릿 (~300줄)
    script_post_processor.py       # 후처리 + 검증 (~400줄)
```

**원칙**: 기존 `from engines.comprehensive_script_generator import ...` 호환 유지

### 2-2. __file__ 사용처 EXE 호환 (6개 파일)

```python
# Before
base_dir = Path(__file__).parent

# After
def _get_base_dir():
    if getattr(sys, 'frozen', False):
        return Path(sys.executable).parent
    return Path(__file__).parent
```

### Phase 2 검증
- [ ] `comprehensive_script_generator.py` 4모듈 분리 완료
- [ ] 기존 import 호환 유지
- [ ] `__file__` → EXE 안전 패턴 전환 완료

---

## Phase 3: 의존성 최적화 (1일)

### 3-1. 불필요 패키지 제거

| 패키지 | 크기 | 현재 용도 | 조치 |
|--------|------|----------|------|
| scipy | 80MB | `uniform_filter1d` 1곳 | numpy 구현으로 대체 |
| opencv-python | 70MB | 코어 파이프라인 미사용 | 제거 |
| pandas | 40MB | 코어 파이프라인 미사용 | 제거 |
| librosa | 60MB | 코어 파이프라인 미사용 | 제거 |
| konlpy + JPype1 | 50MB | 키워드 추출 (선택) | 제거 |
| fastapi + uvicorn | 20MB | Analytics 서버 (별도) | 제거 |
| anthropic | 10MB | 미사용 | 제거 |
| praw | 5MB | 미사용 | 제거 |

**절감**: ~335MB → EXE 크기 150-200MB 가능

### 3-2. scipy → numpy 대체

```python
# Before (engines/color_correction.py)
from scipy.ndimage import uniform_filter1d

# After
def uniform_filter1d_numpy(arr, size, axis=0):
    """numpy로 구현한 1D uniform filter"""
    kernel = np.ones(size) / size
    if axis == 0:
        return np.array([np.convolve(arr[:, i], kernel, mode='same')
                         for i in range(arr.shape[1])]).T
    return np.array([np.convolve(arr[i], kernel, mode='same')
                     for i in range(arr.shape[0])])
```

### 3-3. requirements 파일 통합 (26개 → 2개)

```
requirements_core.txt      # EXE 빌드에 필요한 7개 패키지
requirements_dev.txt       # 개발/테스트 도구
```

**requirements_core.txt**:
```
moviepy>=2.0.0
imageio>=2.31.1
imageio-ffmpeg>=0.4.9
Pillow>=10.4.0
numpy>=1.24.3
google-generativeai==0.3.2
python-dotenv==1.0.0
tqdm==4.66.1
requests==2.31.0
psutil
tenacity
PyYAML>=6.0.1
```

### Phase 3 검증
- [ ] `import scipy` 제거, numpy 대체 동작 확인
- [ ] 코어 파이프라인에서 opencv/pandas/librosa import 0건
- [ ] requirements_core.txt로 clean venv 설치 + 1편 생성 성공

---

## Phase 4: 보안 강화 (1일)

### 4-1. API 키 관리

| 키 | 현재 | 목표 |
|----|------|------|
| GEMINI_API_KEY | .env 평문 | .env (EXE 외부) + 존재 검증 |
| SUPERTONE_API_KEY | .env 평문 | .env (EXE 외부) + 존재 검증 |
| PEXELS_API_KEY | .env 평문 | .env (EXE 외부) + 존재 검증 |

**원칙**: .env 파일은 EXE와 같은 디렉토리에 위치, EXE에 번들링하지 않음

```python
# video_pipeline/env_loader.py
def load_env_for_exe():
    """EXE 환경에서 .env 로드"""
    if getattr(sys, 'frozen', False):
        env_path = Path(sys.executable).parent / '.env'
    else:
        env_path = Path(__file__).parent.parent / '.env'

    if not env_path.exists():
        logger.warning(f".env 파일 없음: {env_path}")
        logger.warning("API 키가 없으면 Fallback 모드로 동작합니다")
        return

    load_dotenv(env_path)
```

### 4-2. .env 하드코딩 경로 제거

```python
# Before
load_dotenv(Path("D:/mabiz/.env"))

# After
load_env_for_exe()
```

### 4-3. .env.template 작성

```env
# CruiseDot EXE 설정 파일
# 이 파일을 .env로 복사하고 API 키를 입력하세요

# Gemini API (대본 생성, 필수)
GEMINI_API_KEY=your_gemini_api_key_here

# Supertone TTS API (음성 합성, 선택 - 없으면 Mock 모드)
SUPERTONE_API_KEY=
SUPERTONE_VOICE_AUDREY=
SUPERTONE_VOICE_JUHO=

# Pexels API (동영상 소스, 선택)
PEXELS_API_KEY=
```

### Phase 4 검증
- [ ] .env 하드코딩 경로 0건
- [ ] API 키 없이도 Fallback 모드 정상 동작
- [ ] .env.template 제공

---

## Phase 5: PyInstaller 빌드 (2일)

### 5-1. 빌드 환경 준비

```bash
pip install pyinstaller==6.3.0
```

### 5-2. PyInstaller Spec 파일 (이미 생성됨)

위치: `D:\mabiz\cruisedot_pipeline.spec`

핵심 설정:
- **모드**: onedir (단일 디렉토리, onefile 아님)
- **진입점**: generate.py
- **Hidden imports**: moviepy.video.*, imageio 플러그인, PIL 등 40+
- **제외**: torch, tensorflow, pandas, matplotlib, konlpy, fastapi, pytest, tkinter
- **번들 데이터**: config/, data/, fonts/ 디렉토리
- **런타임 훅**: FFmpeg PATH 설정 + .env 로더 + stdout 안전장치
- **UPX**: 비활성 (numpy 호환 문제)

### 5-3. 배포 디렉토리 구조

```
CruiseDot/
  CruiseDot.exe              # 메인 실행파일
  _internal/                  # PyInstaller 내부 (자동)
  tools/
    ffmpeg.exe                # FFmpeg 바이너리 (필수)
  assets/
    images/                   # 크루즈 이미지 에셋
    sfx/                      # 효과음
    bgm/                      # 배경음악
  fonts/
    NotoSansKR-Bold.ttf       # 자막 폰트
  config/
    paths.yaml                # 경로 설정
    pipeline_config.yaml      # 파이프라인 설정 (선택)
  outputs/                    # 생성 영상 출력 폴더
  logs/                       # 로그 파일
  .env                        # API 키 (사용자 작성)
  .env.template               # API 키 템플릿
```

### 5-4. 빌드 스크립트

```python
# build.py
"""CruiseDot EXE 빌드 스크립트"""
import subprocess
import shutil
from pathlib import Path

def build():
    # 1. PyInstaller 빌드
    subprocess.run([
        "pyinstaller",
        "cruisedot_pipeline.spec",
        "--clean",
        "--noconfirm"
    ], check=True)

    # 2. 추가 파일 복사
    dist = Path("dist/CruiseDot")
    shutil.copytree("config", dist / "config", dirs_exist_ok=True)
    shutil.copy2(".env.template", dist / ".env.template")

    # 3. FFmpeg 복사
    ffmpeg_src = Path("tools/ffmpeg.exe")
    if ffmpeg_src.exists():
        (dist / "tools").mkdir(exist_ok=True)
        shutil.copy2(ffmpeg_src, dist / "tools/ffmpeg.exe")

    print(f"Build complete: {dist}")

if __name__ == "__main__":
    build()
```

### Phase 5 검증
- [ ] `pyinstaller cruisedot_pipeline.spec --clean` 빌드 성공
- [ ] `dist/CruiseDot/CruiseDot.exe --help` 정상 출력
- [ ] `dist/CruiseDot/CruiseDot.exe --fallback --port MED_BARCELONA` 1편 생성

---

## Phase 6: 통합 테스트 + 클린 머신 검증 (1일)

### 6-1. 로컬 통합 테스트

| 테스트 | 명령어 | 기대 결과 |
|--------|--------|----------|
| 도움말 | `CruiseDot.exe --help` | 사용법 출력 |
| Fallback 단일 | `CruiseDot.exe --fallback --port MED_BARCELONA` | 1편 MP4 생성 |
| Fallback 배치 | `CruiseDot.exe --batch --count 3 --fallback` | 3편 생성 |
| API 모드 | `CruiseDot.exe --port AK_JUNEAU` | Gemini 대본 + 영상 |
| 보고서 | `CruiseDot.exe --report` | MD 보고서 생성 |
| .env 미존재 | .env 삭제 후 실행 | Fallback 모드 자동 전환 |

### 6-2. 클린 머신 테스트 체크리스트

- [ ] Python 미설치 환경에서 EXE 실행
- [ ] FFmpeg 미설치 상태 → 번들 FFmpeg 사용 확인
- [ ] GPU 없는 환경 → CPU 렌더링 fallback
- [ ] 다른 드라이브 (E:\, F:\) 설치 테스트
- [ ] 한글 경로 (`C:\사용자\바탕화면\크루즈닷`) 테스트
- [ ] 관리자 권한 없이 실행

---

## 스프린트 일정

| Phase | 작업 | 예상일 | 의존성 |
|-------|------|--------|--------|
| **Phase 0** | 데드 코드 정리 (~200파일) | **1일** | 없음 |
| **Phase 1** | CRITICAL 블로커 3건 | **3일** | Phase 0 |
| **Phase 2** | God Object 분리 + __file__ | **2일** | Phase 1 |
| **Phase 3** | 의존성 최적화 | **1일** | Phase 0 |
| **Phase 4** | 보안 강화 | **1일** | Phase 1 |
| **Phase 5** | PyInstaller 빌드 | **2일** | Phase 1-4 |
| **Phase 6** | 통합 테스트 | **1일** | Phase 5 |
| **합계** | | **11일** | |

```
Day 1     : Phase 0 (데드 코드 정리)
Day 2-4   : Phase 1 (print→logger, PathResolver, subprocess)
Day 5-6   : Phase 2 (God Object 분리) + Phase 3 (의존성 최적화, 병렬)
Day 7     : Phase 4 (보안 강화)
Day 8-9   : Phase 5 (PyInstaller 빌드 + 디버깅)
Day 10-11 : Phase 6 (통합 테스트 + 클린 머신)
```

---

## 리스크 매트릭스

| 리스크 | 확률 | 영향 | 완화 전략 |
|--------|------|------|----------|
| MoviePy Hidden Import 누락 | 높음 | 빌드 실패 | spec 파일 hidden imports 점진 추가 |
| FFmpeg GPU 감지 실패 (EXE) | 중간 | CPU fallback | gpu_detector.py EXE 호환 확인 |
| 한글 경로 인코딩 오류 | 중간 | 경로 실패 | UTF-8 강제 + Path 객체 사용 |
| numpy/Pillow 버전 충돌 | 낮음 | 빌드 실패 | requirements 버전 고정 |
| 에셋 번들 크기 초과 (>1GB) | 중간 | 배포 불편 | 에셋 외부 디렉토리 (번들 미포함) |

---

## Architecture Decision Records (ADR)

### ADR-1: PyInstaller onedir vs onefile

**결정**: onedir (디렉토리 모드)

**근거**:
- onefile은 시작 시 임시 폴더에 전체 압축 해제 → 시작 30초+ 지연
- onedir은 즉시 실행, 업데이트 시 개별 파일 교체 가능
- 에셋 (이미지/BGM/SFX)이 수백MB → 외부 디렉토리가 합리적

### ADR-2: scipy 제거 vs 유지

**결정**: 제거 (numpy 대체)

**근거**:
- 80MB 절감
- 사용처: `uniform_filter1d` 1곳 (color_correction.py)
- numpy convolution으로 동일 결과 구현 가능

### ADR-3: 에셋 번들링 vs 외부 디렉토리

**결정**: 외부 디렉토리 (EXE 옆 assets/ 폴더)

**근거**:
- 이미지 2,916장 + BGM + SFX = 수백MB
- 사용자가 에셋 추가/교체 가능해야 함
- EXE 업데이트 시 에셋 재다운로드 불필요

---

## 이미 생성된 파일 (Architecture Agent)

| 파일 | 설명 | 상태 |
|------|------|------|
| `cruisedot_pipeline.spec` | PyInstaller 빌드 스펙 | 생성완료 (Phase 1 후 수정 필요) |
| `build_hooks/runtime_hook_moviepy.py` | FFmpeg PATH 런타임 훅 | 생성완료 |
| `build_hooks/runtime_hook_paths.py` | .env 로더 런타임 훅 | 생성완료 |
| `config/paths.yaml` | 외부 경로 설정 | 생성완료 |
| `docs/exe_packaging_architecture.md` | 아키텍처 상세 문서 | 생성완료 |

---

## 성공 기준

| 기준 | 조건 |
|------|------|
| **빌드 성공** | `pyinstaller cruisedot_pipeline.spec` 에러 0건 |
| **단독 실행** | Python 미설치 PC에서 EXE 실행 성공 |
| **Fallback 영상** | .env 없이 1편 50초 MP4 생성 |
| **API 영상** | Gemini API로 S등급(90+) 영상 생성 |
| **배치 모드** | 3편 연속 배치 생성 성공 |
| **EXE 크기** | ≤200MB (에셋 제외) |
| **시작 시간** | ≤5초 (splash 포함) |
| **한글 경로** | 한글 폴더명에서 정상 동작 |

---

*WO v9.0 - CruiseDot EXE 배포 엔진 작업지시서*
*6개 전문 에이전트 (Architecture, Dependencies, Refactoring, Security, Performance, Code Quality) 분석 종합*
*2026-03-10 작성*
