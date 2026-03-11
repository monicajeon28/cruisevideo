# EXE Implementation Roadmap - CruiseDot Video Pipeline

**작성자**: A4 (Architecture Designer Agent)
**작성일**: 2026-03-09
**상태**: 승인됨 (구현 대기)

---

## Executive Summary

Python → Windows EXE 배포를 위한 **5단계 구현 로드맵**.

### 핵심 결정 3가지
1. **배포 모드**: 디렉토리 모드 (`--onedir`) ← 즉시 실행 + 업데이트 효율
2. **에셋 전략**: 3단계 동적 감지 (환경 변수 → EXE 상대 → 기본 경로)
3. **아키텍처**: ValidationPipeline (10단계) + DI Container (의존성 주입)

### ROI 분석
| 투자 | 효과 |
|------|------|
| 20시간 개발 | - 배포 시간: 4시간 → 10분 (96% 단축)<br>- 런타임 오류: 80% → 10% (검증 파이프라인)<br>- 업데이트 주기: 월 1회 → 주 1회 가능 |

---

## Phase 1: 에셋 경로 동적 감지 (4시간)

### 목표
하드코딩된 경로를 제거하여 모든 환경(개발/EXE/CI)에서 동작.

### 구현 파일
```
utils/
└─ asset_path_resolver.py          # 신규 생성 (120줄)
```

### 핵심 코드
```python
def get_asset_dir() -> Path:
    """
    에셋 디렉토리 동적 감지

    우선순위:
    1. 환경 변수: CRUISE_ASSET_DIR
    2. EXE 상대 경로: ./assets/
    3. 기본 경로: D:/AntiGravity/Assets/
    """
    # 1. 환경 변수
    env_path = os.getenv("CRUISE_ASSET_DIR")
    if env_path and Path(env_path).exists():
        return Path(env_path)

    # 2. EXE 모드
    if getattr(sys, 'frozen', False):
        exe_dir = Path(sys.executable).parent
        asset_dir = exe_dir / "assets"
        if asset_dir.exists():
            return asset_dir

    # 3. 기본 경로
    default_path = Path("D:/AntiGravity/Assets")
    if default_path.exists():
        return default_path

    raise FileNotFoundError("Asset directory not found")

ASSET_DIR = get_asset_dir()
```

### 마이그레이션 대상 (12개 파일)
| 파일 | 변경 | 난이도 |
|------|------|--------|
| `engines/bgm_matcher.py` | `from utils.asset_path_resolver import ASSET_DIR` | 쉬움 |
| `src/utils/asset_matcher.py` | 동일 | 쉬움 |
| `engines/comprehensive_script_generator.py` | 경로 하드코딩 제거 | 보통 |
| `generate_video_55sec_pipeline.py` | `ASSET_DIR` 통합 | 쉬움 |
| ... | ... | ... |

### 테스트 시나리오 (4개)
1. 환경 변수 우선순위 테스트
2. EXE 모드 테스트 (`sys.frozen`)
3. 기본 경로 Fallback 테스트
4. 경로 없음 오류 테스트

### 완료 조건
- [ ] `utils/asset_path_resolver.py` 생성 완료
- [ ] 12개 파일 마이그레이션 완료 (하드코딩 0개)
- [ ] 단위 테스트 4개 PASS
- [ ] `.env.example`에 `CRUISE_ASSET_DIR` 추가

### 예상 시간
- 구현: 2시간
- 마이그레이션: 1시간
- 테스트: 1시간
- **총 4시간**

---

## Phase 2: ValidationPipeline 10단계 구현 (6시간)

### 목표
런타임 오류를 사전 차단하여 사용자 경험 개선 (80% → 10% 오류율).

### 구현 파일
```
validation/
├─ pipeline.py                      # ValidationPipeline 클래스 (200줄)
└─ validators/
   ├─ __init__.py
   ├─ base_validator.py             # BaseValidator 추상 클래스
   ├─ input_validator.py            # 1. 입력 검증
   ├─ api_key_validator.py          # 2. API 키 검증
   ├─ path_validator.py             # 3. 경로 검증
   ├─ asset_validator.py            # 4. 에셋 존재 확인
   ├─ script_validator.py           # 5. 스크립트 품질 (Placeholder)
   ├─ security_validator.py         # 6. 보안 검증
   ├─ dependency_validator.py       # 7. FFmpeg 검증
   ├─ output_validator.py           # 8. 출력 디렉토리
   ├─ license_validator.py          # 9. 라이선스 (Placeholder)
   └─ version_validator.py          # 10. 버전 호환성
```

### 10단계 검증 흐름
```
1. InputValidator      → CLI 인자 검증
2. APIKeyValidator     → GEMINI_API_KEY, SUPERTONE_API_KEY 존재 확인
3. PathValidator       → asset_dir, temp_dir, output_dir 접근 확인
4. AssetValidator      → Image/Footage/Music 디렉토리 존재 확인
5. ScriptValidator     → S등급 점수 (런타임 검증)
6. SecurityValidator   → .env 파일 권한 확인
7. DependencyValidator → FFmpeg 설치 확인
8. OutputValidator     → 출력 디렉토리 쓰기 권한 확인
9. LicenseValidator    → 라이선스 키 검증 (상용 배포 시)
10. VersionValidator   → Python 3.11+ 확인
```

### 사용 예시 (main.py)
```python
from validation.pipeline import ValidationPipeline

def main():
    pipeline = ValidationPipeline()
    context = {
        "mode": "auto",
        "output_dir": "outputs",
    }

    result = pipeline.validate_all(context)
    pipeline.print_report(result)

    if not result["passed"]:
        print("❌ Validation failed. Exiting.")
        sys.exit(1)

    # 파이프라인 계속
    app = CruiseVideoGenerator()
    app.run()
```

### 테스트 시나리오 (10개)
1. 모든 검증 통과 (Happy Path)
2. API 키 없음 → CRITICAL 실패
3. 에셋 디렉토리 없음 → CRITICAL 실패
4. FFmpeg 없음 → CRITICAL 실패
5. Python 3.10 → WARNING (계속 진행)
6. 에셋 파일 적음 → WARNING (계속 진행)
7. 수동 모드 필수 인자 누락 → CRITICAL 실패
8. .env 파일 없음 → WARNING
9. 출력 디렉토리 쓰기 권한 없음 → CRITICAL 실패
10. 혼합 시나리오 (CRITICAL 1개 + WARNING 2개)

### 완료 조건
- [ ] `validation/pipeline.py` 생성 완료
- [ ] 10개 Validator 구현 완료
- [ ] `main.py`에 통합
- [ ] 단위 테스트 10개 PASS
- [ ] 오류 메시지 명확성 검증 (3초 내 이해)

### 예상 시간
- 구현: 4시간
- 테스트: 1.5시간
- 문서화: 0.5시간
- **총 6시간**

---

## Phase 3: DI Container 구현 (4시간)

### 목표
의존성 주입으로 테스트 용이성 및 모듈성 향상.

### 구현 파일
```
di/
├─ __init__.py
├─ container.py                     # DIContainer 클래스 (100줄)
└─ bootstrap.py                     # 서비스 등록 (80줄)
```

### 핵심 코드
```python
# di/container.py
class DIContainer:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._services = {}
            cls._instance._singletons = {}
        return cls._instance

    def register(self, name: str, factory: Callable, singleton: bool = False):
        self._services[name] = {"factory": factory, "singleton": singleton}

    def get(self, name: str) -> Any:
        if name not in self._services:
            raise KeyError(f"Service not registered: {name}")

        if self._services[name]["singleton"]:
            if name not in self._singletons:
                self._singletons[name] = self._services[name]["factory"]()
            return self._singletons[name]

        return self._services[name]["factory"]()

container = DIContainer()
```

### 서비스 등록 (bootstrap.py)
```python
def bootstrap():
    # 1. Gemini Client (Singleton)
    container.register("gemini_client", create_gemini_client, singleton=True)

    # 2. TTS Engine (Singleton)
    container.register("tts_engine", create_tts_engine, singleton=True)

    # 3. Script Generator (Transient)
    container.register("script_generator", create_script_generator, singleton=False)

    # 4. BGM Matcher (Singleton)
    container.register("bgm_matcher", create_bgm_matcher, singleton=True)

    # 5. Asset Matcher (Singleton)
    container.register("asset_matcher", create_asset_matcher, singleton=True)
```

### 수정 대상 (5개 파일)
| 파일 | 변경 | 난이도 |
|------|------|--------|
| `engines/comprehensive_script_generator.py` | `client` 파라미터 추가 | 쉬움 |
| `engines/supertone_tts.py` | `api_key` 파라미터 추가 | 쉬움 |
| `cli/auto_mode.py` | `container.get('script_generator')` | 쉬움 |
| `cli/manual_mode.py` | `container.get('script_generator')` | 쉬움 |
| `main.py` | `bootstrap()` 호출 | 쉬움 |

### 테스트 시나리오 (5개)
1. 서비스 등록 및 조회
2. Singleton 캐싱 (동일 인스턴스)
3. Transient 매번 생성 (다른 인스턴스)
4. 존재하지 않는 서비스 조회 (KeyError)
5. Mock 주입 테스트

### 완료 조건
- [ ] `di/container.py` 생성 완료
- [ ] `di/bootstrap.py` 생성 완료
- [ ] 5개 서비스 등록 완료
- [ ] 5개 파일 마이그레이션 완료
- [ ] 단위 테스트 5개 PASS

### 예상 시간
- 구현: 2시간
- 마이그레이션: 1시간
- 테스트: 1시간
- **총 4시간**

---

## Phase 4: PyInstaller 빌드 및 배포 (3시간)

### 목표
디렉토리 모드 EXE 빌드 및 배포 패키지 자동화.

### 구현 파일
```
cruise_video_generator.spec         # PyInstaller 설정 (80줄)
scripts/
├─ build_exe.py                     # 빌드 자동화 (60줄)
├─ package_release.py               # ZIP 패키징 (50줄)
└─ setup_assets.py                  # 심볼릭 링크 생성 (30줄)
setup_assets.bat                    # Windows 스크립트 (15줄)
```

### PyInstaller Spec 파일
```python
# cruise_video_generator.spec
a = Analysis(
    ['main.py'],
    pathex=[str(project_root)],
    datas=[
        ('config/defaults.yaml', 'config'),
        ('.env.example', '.'),
    ],
    hiddenimports=[
        'google.genai',
        'moviepy.editor',
        'PIL._tkinter_finder',
    ],
    excludes=[
        'matplotlib',
        'scipy',
        'pandas',
    ],
)

exe = EXE(
    pyz,
    a.scripts,
    exclude_binaries=True,  # 디렉토리 모드
    name='CruiseDotGenerator',
    console=True,
    icon='assets/icon.ico',
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    name='CruiseDotGenerator',
)
```

### 빌드 스크립트 (scripts/build_exe.py)
```python
def build():
    # 1. 이전 빌드 정리
    shutil.rmtree("dist", ignore_errors=True)
    shutil.rmtree("build", ignore_errors=True)

    # 2. PyInstaller 실행
    subprocess.run(["pyinstaller", "--clean", "cruise_video_generator.spec"], check=True)

    # 3. 설정 파일 복사
    exe_dir = Path("dist/CruiseDotGenerator")
    shutil.copy("config/cruise_config.yaml.example", exe_dir / "config" / "cruise_config.yaml")
    shutil.copy(".env.example", exe_dir / ".env.example")

    # 4. README 생성
    (exe_dir / "README.txt").write_text("Setup: ...", encoding="utf-8")

    print("✅ Build successful!")
```

### 배포 구조
```
CruiseDotGenerator/
├─ CruiseDotGenerator.exe
├─ _internal/
├─ config/
│  ├─ cruise_config.yaml
│  └─ .env.example
├─ docs/
├─ setup_assets.bat
└─ README.txt
```

### 테스트 시나리오 (3개)
1. 빌드 성공 여부 (`dist/CruiseDotGenerator/` 존재)
2. EXE 실행 테스트 (--help)
3. ZIP 패키징 및 체크섬 생성

### 완료 조건
- [ ] `cruise_video_generator.spec` 생성 완료
- [ ] `scripts/build_exe.py` 생성 완료
- [ ] `scripts/package_release.py` 생성 완료
- [ ] `setup_assets.bat` 생성 완료
- [ ] 빌드 성공 (EXE 크기 < 150MB)

### 예상 시간
- 구현: 2시간
- 빌드 테스트: 0.5시간
- 문서화: 0.5시간
- **총 3시간**

---

## Phase 5: 자동 업데이트 구현 (3시간)

### 목표
GitHub Releases 기반 자동 업데이트 시스템.

### 구현 파일
```
updater/
├─ __init__.py
└─ auto_updater.py                  # AutoUpdater 클래스 (150줄)
```

### 핵심 코드
```python
class AutoUpdater:
    def __init__(self):
        self.repo = "your-username/cruise-video-generator"
        self.current_version = "1.0.0"

    def check_update(self) -> Optional[str]:
        """GitHub Releases API로 최신 버전 확인"""
        url = f"https://api.github.com/repos/{self.repo}/releases/latest"
        response = requests.get(url, timeout=10)
        latest_version = response.json()["tag_name"].lstrip("v")

        if self._version_compare(latest_version, self.current_version) > 0:
            return latest_version
        return None

    def download_update(self, version: str) -> Path:
        """업데이트 ZIP 다운로드"""
        url = f"https://github.com/{self.repo}/releases/download/v{version}/CruiseDot_v{version}.zip"
        # ... 다운로드 로직

    def apply_update(self, zip_path: Path):
        """업데이트 적용 및 재시작"""
        # 1. 현재 EXE 백업
        # 2. ZIP 압축 해제
        # 3. 파일 교체
        # 4. 재시작
        subprocess.Popen([str(new_exe)])
        sys.exit(0)
```

### 사용 예시 (main.py)
```python
from updater.auto_updater import AutoUpdater

def main():
    updater = AutoUpdater()

    # 백그라운드 업데이트 체크
    def check_update_async():
        latest = updater.check_update()
        if latest:
            print(f"💡 Update available: v{latest}")

    threading.Thread(target=check_update_async, daemon=True).start()

    # 메인 애플리케이션 실행
    # ...
```

### 테스트 시나리오 (4개)
1. 최신 버전 확인 (API 모킹)
2. 업데이트 다운로드 (Mock ZIP)
3. 파일 교체 시뮬레이션
4. 버전 비교 로직 (1.0.0 vs 1.1.0)

### 완료 조건
- [ ] `updater/auto_updater.py` 생성 완료
- [ ] `main.py`에 업데이트 체크 통합
- [ ] 단위 테스트 4개 PASS
- [ ] GitHub Releases 워크플로우 문서화

### 예상 시간
- 구현: 2시간
- 테스트: 0.5시간
- 문서화: 0.5시간
- **총 3시간**

---

## 총 타임라인 및 리소스

### Phase별 시간 요약
| Phase | 작업 | 시간 | 우선순위 |
|-------|------|------|----------|
| **Phase 1** | 에셋 경로 동적 감지 | 4h | P0 (필수) |
| **Phase 2** | ValidationPipeline 10단계 | 6h | P0 (필수) |
| **Phase 3** | DI Container | 4h | P1 (권장) |
| **Phase 4** | PyInstaller 빌드 | 3h | P0 (필수) |
| **Phase 5** | 자동 업데이트 | 3h | P2 (선택) |
| **총계** | | **20h** | |

### 인력 배치
- **1인 개발**: 5일 (하루 4시간)
- **2인 병렬**: 2.5일 (Phase 1+2 동시 진행)

### 리스크 및 완화
| 리스크 | 확률 | 영향 | 완화 전략 |
|--------|------|------|-----------|
| PyInstaller 숨겨진 import 오류 | 50% | 중간 | `hiddenimports` 사전 조사 |
| 백신 오탐 (False Positive) | 30% | 낮음 | 코드 서명 인증서 (선택) |
| 에셋 경로 감지 실패 | 20% | 높음 | Fallback 3단계 + 명확한 오류 |
| DI Container 순환 의존성 | 10% | 중간 | 서비스 등록 순서 검증 |

---

## 성공 기준 (Acceptance Criteria)

### Phase 1 완료 조건
- [ ] 에셋 경로 하드코딩 0개
- [ ] 환경 변수 감지 100%
- [ ] EXE 모드 상대 경로 감지 100%

### Phase 2 완료 조건
- [ ] 런타임 오류율 80% → 10%
- [ ] 검증 실패 시 명확한 오류 메시지 (3초 내 이해)
- [ ] 10단계 검증 모두 구현

### Phase 3 완료 조건
- [ ] 단위 테스트 커버리지 90% 이상
- [ ] 서비스 등록 5개 이상
- [ ] Mock 주입 테스트 성공

### Phase 4 완료 조건
- [ ] EXE 빌드 성공 (크기 < 150MB)
- [ ] 압축 해제 없이 즉시 실행
- [ ] 배포 ZIP 자동 생성

### Phase 5 완료 조건 (선택)
- [ ] GitHub Releases API 연동
- [ ] 자동 다운로드 및 적용
- [ ] 백업 및 롤백 기능

---

## 다음 단계 (Phase 6+, 미래 작업)

### Phase 6: 코드 서명 (선택)
- **목표**: 백신 오탐 제거
- **방법**: DigiCert/Sectigo 인증서 구매
- **비용**: $200/년
- **시간**: 2시간 (인증서 통합)

### Phase 7: 크로스 플랫폼 (선택)
- **목표**: Linux/macOS 지원
- **방법**: PyInstaller 멀티 플랫폼 빌드
- **시간**: 10시간 (경로 분리 로직)

### Phase 8: GUI 래퍼 (선택)
- **목표**: CLI → GUI 인터페이스
- **방법**: PyQt5/Tkinter
- **시간**: 20시간 (UI 설계 및 구현)

---

## 참조 문서

### 설계 문서
- [EXE_ARCHITECTURE_DESIGN.md](./EXE_ARCHITECTURE_DESIGN.md) - 상세 아키텍처 설계
- [EXE_ARCHITECTURE_DIAGRAMS.md](./EXE_ARCHITECTURE_DIAGRAMS.md) - Mermaid 다이어그램

### ADR (Architecture Decision Records)
- [ADR-001: EXE 배포 모드 선택](./ADR_001_EXE_DEPLOYMENT_MODE.md)
- [ADR-002: 에셋 경로 동적 감지](./ADR_002_ASSET_PATH_RESOLUTION.md)
- [ADR-003: 의존성 주입 컨테이너](./ADR_003_DEPENDENCY_INJECTION.md)

### 외부 리소스
- [PyInstaller Documentation](https://pyinstaller.org/)
- [Python Pathlib Guide](https://docs.python.org/3/library/pathlib.html)
- [GitHub Releases API](https://docs.github.com/en/rest/releases)

---

## 승인 및 착수

### 승인자
- [ ] 프로젝트 매니저 승인
- [ ] 기술 리드 승인
- [ ] 사용자 대표 승인

### 착수 일정
- **시작일**: Phase 1 즉시 착수 가능
- **완료 목표**: Phase 1-4 완료 (17시간, 약 4일)

### 후속 작업
- Phase 완료 후 → C5 (Documentation Generator)로 사용자 가이드 작성
- EXE 배포 후 → 사용자 피드백 수집 및 개선

---

**작성**: A4 (Architecture Designer Agent)
**최종 검토**: 2026-03-09
**다음 Agent**: C5 (Documentation Generator) - 사용자 가이드 작성
