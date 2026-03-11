# ADR-002: 에셋 경로 동적 감지 전략

## 상태
**승인됨** (2026-03-09)

## 컨텍스트

현재 코드베이스는 Windows 절대 경로를 하드코딩하고 있음:

```python
# 현재 코드 (engines/bgm_matcher.py)
ASSET_DIR = "D:/AntiGravity/Assets/"
```

### 문제점
1. **환경 의존성**: 다른 PC에서 실행 불가
2. **EXE 호환성**: PyInstaller frozen 환경 미고려
3. **개발/배포 분리 없음**: 개발 환경과 배포 환경 경로 동일
4. **테스트 어려움**: Mock 경로 주입 불가

### 요구사항
- 개발 환경: `D:/AntiGravity/Assets/`
- EXE 환경: `./assets/` (심볼릭 링크)
- 사용자 환경: 환경 변수로 커스터마이징 가능
- Fallback: 안전한 기본 경로

## 결정

**3단계 우선순위 경로 감지 시스템을 구현한다:**

1. **환경 변수** (`CRUISE_ASSET_DIR`) - 최우선
2. **EXE 상대 경로** (`./assets/`) - PyInstaller frozen 환경
3. **기본 경로** (`D:/AntiGravity/Assets/`) - 개발 환경

## 근거

### 1. 환경 변수 우선 (유연성)

```python
# 사용자가 커스텀 경로 설정 가능
CRUISE_ASSET_DIR=E:/MyAssets/
```

**장점**:
- 사용자 환경 적응
- CI/CD 파이프라인 지원
- 테스트 격리 (Mock 경로)

**적용 사례**:
- 회사 PC: `D:/Assets/`
- 집 PC: `E:/CruiseAssets/`
- CI 환경: `/tmp/test_assets/`

### 2. EXE 상대 경로 (배포 환경)

```python
if getattr(sys, 'frozen', False):
    # PyInstaller EXE 모드
    exe_dir = Path(sys.executable).parent
    asset_dir = exe_dir / "assets"
```

**장점**:
- 이동 가능성 (폴더 전체 이동 OK)
- 심볼릭 링크 지원
- 명확한 구조

**구조**:
```
CruiseDotGenerator/
├─ CruiseDotGenerator.exe
├─ _internal/
└─ assets/  → D:\AntiGravity\Assets\ (symlink)
```

### 3. 기본 경로 (개발 환경)

```python
default_path = Path("D:/AntiGravity/Assets")
if default_path.exists():
    return default_path
```

**장점**:
- 개발자 환경 즉시 동작
- `.env` 파일 없이도 작동
- 기존 에셋 활용

## 구현

### utils/asset_path_resolver.py (신규 생성)

```python
"""
에셋 경로 동적 감지 모듈
우선순위: 환경 변수 > EXE 상대 경로 > 기본 경로
"""

import os
import sys
from pathlib import Path
from typing import Optional

def get_asset_dir() -> Path:
    """
    에셋 디렉토리 동적 감지

    우선순위:
    1. 환경 변수: CRUISE_ASSET_DIR
    2. EXE 기준 상대 경로: ../assets/
    3. 개발 환경 경로: D:/AntiGravity/Assets/

    Returns:
        Path: 검증된 에셋 디렉토리 경로

    Raises:
        FileNotFoundError: 에셋 디렉토리를 찾을 수 없을 때

    Example:
        >>> asset_dir = get_asset_dir()
        >>> bgm_path = asset_dir / "Music" / "travel_bgm.mp3"
    """
    # 1. 환경 변수 확인
    env_path = os.getenv("CRUISE_ASSET_DIR")
    if env_path:
        path = Path(env_path)
        if path.exists() and path.is_dir():
            print(f"[INFO] Asset directory: {path} (from CRUISE_ASSET_DIR)")
            return path.resolve()

    # 2. EXE 기준 상대 경로 (PyInstaller frozen 환경)
    if getattr(sys, 'frozen', False):
        exe_dir = Path(sys.executable).parent
        asset_dir = exe_dir / "assets"
        if asset_dir.exists():
            print(f"[INFO] Asset directory: {asset_dir} (from EXE symlink)")
            return asset_dir.resolve()

    # 3. 개발 환경 기본 경로
    default_path = Path("D:/AntiGravity/Assets")
    if default_path.exists():
        print(f"[INFO] Asset directory: {default_path} (default dev path)")
        return default_path.resolve()

    # 모든 경로 실패 시 오류
    raise FileNotFoundError(
        "Asset directory not found. Please:\n"
        "1. Set CRUISE_ASSET_DIR environment variable, or\n"
        "2. Create symlink: mklink /D assets D:\\AntiGravity\\Assets, or\n"
        "3. Ensure D:/AntiGravity/Assets exists"
    )

# 전역 상수 (모듈 로드 시 1회 실행)
ASSET_DIR = get_asset_dir()
```

### 기존 코드 마이그레이션 예시

**Before (하드코딩)**:
```python
# engines/bgm_matcher.py
class BGMMatcher:
    def __init__(self):
        self.bgm_dir = Path("D:/AntiGravity/Assets/Music")
```

**After (동적 감지)**:
```python
# engines/bgm_matcher.py
from utils.asset_path_resolver import ASSET_DIR

class BGMMatcher:
    def __init__(self):
        self.bgm_dir = ASSET_DIR / "Music"
```

## 결과

### 장점
- ✅ 환경 독립성: 모든 PC에서 동작
- ✅ EXE 호환성: PyInstaller frozen 환경 대응
- ✅ 테스트 용이: Mock 경로 주입 가능
- ✅ 사용자 친화: 환경 변수로 커스터마이징
- ✅ 안전성: 경로 없으면 명확한 오류 메시지

### 단점
- ❌ 초기 설정 필요: 환경 변수 또는 심볼릭 링크
- ❌ 문서화 필요: 사용자 가이드 작성

### 완화 전략
- `setup_assets.bat` 제공 (심볼릭 링크 자동 생성)
- `.env.example`에 `CRUISE_ASSET_DIR` 예시
- README.txt에 설치 가이드

## 대안

### 대안 1: 설정 파일 방식 (`config.yaml`)

```yaml
assets:
  base_dir: "D:/AntiGravity/Assets"
```

**기각 이유**:
- 환경 변수보다 유연성 떨어짐
- 설정 파일 자체 경로도 동적 감지 필요 (순환 문제)

### 대안 2: 사용자 입력 프롬프트

```python
asset_dir = input("Enter asset directory: ")
```

**기각 이유**:
- CLI 자동화 불가
- 매 실행마다 입력 (사용자 경험 저하)

### 대안 3: 에셋 내장 (EXE에 포함)

```python
# PyInstaller datas
datas = [('D:/AntiGravity/Assets', 'assets')]
```

**기각 이유**:
- 2GB+ 에셋 → EXE 크기 폭발
- 업데이트 시 2GB 재배포

## 영향 범위

### 변경 필요 파일 (12개)

| 파일 | 변경 내용 |
|------|-----------|
| `utils/asset_path_resolver.py` | 신규 생성 |
| `engines/bgm_matcher.py` | `ASSET_DIR` import |
| `src/utils/asset_matcher.py` | `ASSET_DIR` import |
| `engines/comprehensive_script_generator.py` | 경로 하드코딩 제거 |
| `generate_video_55sec_pipeline.py` | `ASSET_DIR` 통합 |
| `validation/validators/path_validator.py` | `get_asset_dir()` 사용 |
| `validation/validators/asset_validator.py` | `ASSET_DIR` 검증 |
| `.env.example` | `CRUISE_ASSET_DIR` 추가 |
| `setup_assets.bat` | 심볼릭 링크 생성 스크립트 |
| `docs/SETUP_GUIDE.md` | 설치 가이드 업데이트 |
| `tests/test_asset_path.py` | 단위 테스트 추가 |
| `README.txt` | 빠른 시작 가이드 |

### 예상 작업 시간
- 구현: 2시간
- 테스트: 1시간
- 문서화: 1시간
- **총 4시간**

## 테스트 시나리오

### 1. 환경 변수 우선순위 테스트
```python
def test_env_var_priority():
    os.environ["CRUISE_ASSET_DIR"] = "/tmp/test_assets"
    asset_dir = get_asset_dir()
    assert asset_dir == Path("/tmp/test_assets")
```

### 2. EXE 모드 테스트
```python
def test_exe_mode(monkeypatch):
    monkeypatch.setattr(sys, 'frozen', True)
    monkeypatch.setattr(sys, 'executable', r"C:\App\CruiseDot.exe")
    asset_dir = get_asset_dir()
    assert asset_dir == Path(r"C:\App\assets")
```

### 3. 기본 경로 Fallback 테스트
```python
def test_default_path():
    # 환경 변수 제거
    os.environ.pop("CRUISE_ASSET_DIR", None)
    asset_dir = get_asset_dir()
    assert asset_dir == Path("D:/AntiGravity/Assets")
```

### 4. 경로 없음 오류 테스트
```python
def test_no_path_error(monkeypatch):
    monkeypatch.setenv("CRUISE_ASSET_DIR", "")
    monkeypatch.setattr(sys, 'frozen', False)
    monkeypatch.setattr(Path, 'exists', lambda self: False)

    with pytest.raises(FileNotFoundError, match="Asset directory not found"):
        get_asset_dir()
```

## 측정 지표

### 성공 기준
- [ ] 개발 환경에서 즉시 동작 (환경 변수 없이)
- [ ] EXE 환경에서 심볼릭 링크 감지 100%
- [ ] 경로 없음 시 명확한 오류 메시지 (3초 내 이해)
- [ ] 12개 파일 마이그레이션 완료 (하드코딩 0개)

### 모니터링
- 경로 감지 실패 로그
- 사용자 이슈 리포트 (경로 문제)
- CI/CD 빌드 성공률

## 롤백 계획

### 문제 발생 시
1. `utils/asset_path_resolver.py` 비활성화
2. 기존 하드코딩 경로 복원
3. 영향 받은 12개 파일 롤백

### 롤백 소요 시간
- 1시간 (Git revert)

## 참조
- [Python pathlib Documentation](https://docs.python.org/3/library/pathlib.html)
- [PyInstaller Runtime Information](https://pyinstaller.org/en/stable/runtime-information.html)
- 프로젝트 문서: `docs/architecture/EXE_ARCHITECTURE_DESIGN.md`

## 변경 이력
| 날짜 | 변경 내용 | 작성자 |
|------|-----------|--------|
| 2026-03-09 | 초안 작성 및 승인 | A4 (Architecture Designer) |

---

**이전 ADR**: ADR-001 (EXE 배포 모드 선택)
**다음 ADR**: ADR-003 (의존성 주입 컨테이너 설계)
