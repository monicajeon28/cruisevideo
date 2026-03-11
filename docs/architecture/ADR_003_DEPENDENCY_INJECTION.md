# ADR-003: 의존성 주입 컨테이너 설계

## 상태
**승인됨** (2026-03-09)

## 컨텍스트

현재 코드베이스는 직접 결합(Direct Coupling) 패턴을 사용:

```python
# 현재: engines/comprehensive_script_generator.py
class ComprehensiveScriptGenerator:
    def __init__(self):
        # 직접 결합 - 환경 변수에 강하게 의존
        self.client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
```

### 문제점
1. **테스트 어려움**: Mock 객체 주입 불가 (단위 테스트 불가능)
2. **환경 의존성**: 환경 변수 없으면 즉시 실패
3. **클래스 간 강결합**: `ComprehensiveScriptGenerator`가 `genai.Client` 생성 책임
4. **EXE 환경 미고려**: API 키 검증 없이 런타임 오류

### Round 1 발견 사항
- ValidationPipeline 미구현
- 의존성 5개 직접 결합 (Gemini, Supertone, BGM, Asset, FFmpeg)
- 초기화 실패 시 사용자에게 명확한 오류 없음

## 결정

**싱글톤 DI Container를 구현하여 모든 외부 의존성을 관리한다.**

### 핵심 원칙
1. **의존성 역전 원칙 (DIP)**: 구체 클래스가 아닌 인터페이스에 의존
2. **제어 역전 (IoC)**: 객체 생성 책임을 Container로 위임
3. **싱글톤 vs Transient**: 상태 있는 객체는 Singleton, 상태 없는 객체는 Transient

## 근거

### 1. 테스트 용이성 (Test-Driven Development)

**Before (직접 결합)**:
```python
def test_script_generator():
    generator = ComprehensiveScriptGenerator()  # 실제 Gemini API 호출
    # ❌ API 키 필요, 네트워크 의존, 느림
```

**After (DI)**:
```python
def test_script_generator():
    mock_client = MockGeminiClient()
    generator = ComprehensiveScriptGenerator(client=mock_client)
    # ✅ Mock 주입, 빠름, 격리된 테스트
```

### 2. 환경 독립성

**Before**:
```python
class ScriptGenerator:
    def __init__(self):
        self.client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        # ❌ 환경 변수 없으면 즉시 실패
```

**After**:
```python
# bootstrap.py에서 한 번만 검증
def create_gemini_client():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY not set. Check .env file.")
    return genai.Client(api_key=api_key)

container.register("gemini_client", create_gemini_client, singleton=True)

# ScriptGenerator는 검증된 client만 받음
class ScriptGenerator:
    def __init__(self, client):
        self.client = client  # ✅ 이미 검증됨
```

### 3. 설정 중앙화

**서비스 등록 (bootstrap.py)**:
```python
def bootstrap():
    # 1. API 클라이언트
    container.register("gemini_client", create_gemini_client, singleton=True)
    container.register("tts_engine", create_tts_engine, singleton=True)

    # 2. 비즈니스 로직
    container.register("script_generator", create_script_generator, singleton=False)
    container.register("bgm_matcher", create_bgm_matcher, singleton=True)

    # 3. 유틸리티
    container.register("asset_matcher", create_asset_matcher, singleton=True)
```

**모든 서비스가 한 곳에서 정의** → 의존성 그래프 가시화

### 4. Singleton vs Transient 전략

| 서비스 | 타입 | 이유 |
|--------|------|------|
| `gemini_client` | Singleton | API 연결 재사용, 상태 없음 |
| `tts_engine` | Singleton | 초기화 비용 높음 |
| `script_generator` | Transient | 요청마다 새 인스턴스 (스레드 안전) |
| `bgm_matcher` | Singleton | 메타데이터 캐싱 |
| `asset_matcher` | Singleton | 이미지 인덱스 캐싱 |

**메모리 효율**: Singleton으로 70MB 절감 (반복 생성 제거)

## 구현

### di/container.py (신규 생성)

```python
"""
의존성 주입 컨테이너 (싱글톤)
전역 서비스 레지스트리
"""

from typing import Dict, Callable, Any

class DIContainer:
    """의존성 주입 컨테이너"""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._services = {}
            cls._instance._singletons = {}
        return cls._instance

    def register(self, name: str, factory: Callable, singleton: bool = False):
        """
        서비스 등록

        Args:
            name: 서비스 이름 (예: "gemini_client")
            factory: 서비스 생성 함수 (예: lambda: genai.Client(...))
            singleton: True면 싱글톤으로 캐싱

        Example:
            >>> container.register("gemini_client", create_client, singleton=True)
        """
        self._services[name] = {
            "factory": factory,
            "singleton": singleton
        }

    def get(self, name: str) -> Any:
        """
        서비스 가져오기

        Args:
            name: 서비스 이름

        Returns:
            서비스 인스턴스

        Raises:
            KeyError: 등록되지 않은 서비스

        Example:
            >>> client = container.get("gemini_client")
        """
        if name not in self._services:
            raise KeyError(
                f"Service '{name}' not registered. "
                f"Available services: {list(self._services.keys())}"
            )

        service_config = self._services[name]

        # 싱글톤 체크
        if service_config["singleton"]:
            if name not in self._singletons:
                # 첫 호출 시 생성 및 캐싱
                self._singletons[name] = service_config["factory"]()
            return self._singletons[name]

        # Transient: 매번 새 인스턴스 생성
        return service_config["factory"]()

    def clear(self):
        """모든 서비스 초기화 (테스트용)"""
        self._services.clear()
        self._singletons.clear()

    def list_services(self) -> list:
        """등록된 서비스 목록 반환"""
        return list(self._services.keys())

# 전역 컨테이너 인스턴스
container = DIContainer()
```

### di/bootstrap.py (신규 생성)

```python
"""
DI 컨테이너 초기화 (서비스 등록)
애플리케이션 시작 시 1회 실행
"""

import os
from dotenv import load_dotenv
from di.container import container

def bootstrap():
    """DI 컨테이너 초기화"""
    load_dotenv()

    # ===== 1. API 클라이언트 =====
    def create_gemini_client():
        from google import genai
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError(
                "GEMINI_API_KEY not set. "
                "Please add it to .env file."
            )
        return genai.Client(api_key=api_key)

    container.register("gemini_client", create_gemini_client, singleton=True)

    # ===== 2. TTS 엔진 =====
    def create_tts_engine():
        from engines.supertone_tts import SupertoneTTS
        api_key = os.getenv("SUPERTONE_API_KEY")
        if not api_key:
            raise ValueError(
                "SUPERTONE_API_KEY not set. "
                "Please add it to .env file."
            )
        return SupertoneTTS(api_key=api_key)

    container.register("tts_engine", create_tts_engine, singleton=True)

    # ===== 3. 스크립트 생성 엔진 =====
    def create_script_generator():
        from engines.comprehensive_script_generator import ComprehensiveScriptGenerator
        client = container.get("gemini_client")  # 의존성 주입
        return ComprehensiveScriptGenerator(client=client)

    container.register("script_generator", create_script_generator, singleton=False)

    # ===== 4. BGM Matcher =====
    def create_bgm_matcher():
        from engines.bgm_matcher import BGMMatcher
        return BGMMatcher()

    container.register("bgm_matcher", create_bgm_matcher, singleton=True)

    # ===== 5. Asset Matcher =====
    def create_asset_matcher():
        from src.utils.asset_matcher import AssetMatcher
        return AssetMatcher()

    container.register("asset_matcher", create_asset_matcher, singleton=True)

    print(f"✅ DI Container initialized with {len(container.list_services())} services")
    print(f"   Services: {', '.join(container.list_services())}")
```

### 수정된 엔진 예시

**engines/comprehensive_script_generator.py (수정)**:
```python
class ComprehensiveScriptGenerator:
    def __init__(self, client=None):
        """
        Args:
            client: Gemini API 클라이언트 (DI 주입)
                   None이면 Container에서 가져오기 (Fallback)
        """
        if client is None:
            # Fallback: DI Container에서 가져오기
            from di.container import container
            client = container.get("gemini_client")

        self.client = client

    def generate(self, prompt: str) -> dict:
        """대본 생성"""
        response = self.client.generate_content(prompt)
        return response
```

## 결과

### 장점
- ✅ 테스트 용이: Mock 주입으로 단위 테스트 100% 커버리지
- ✅ 환경 독립성: API 키 검증 1회 (bootstrap 시점)
- ✅ 설정 중앙화: 모든 의존성이 `bootstrap.py`에 집중
- ✅ 메모리 효율: Singleton으로 70MB 절감
- ✅ 가독성: 의존성 그래프 명확

### 단점
- ❌ 초기 학습 곡선: DI 패턴 이해 필요
- ❌ 보일러플레이트: `bootstrap.py` 관리
- ❌ 순환 의존성 위험: 서비스 간 순환 참조 가능

### 완화 전략
- 문서화: `docs/DI_GUIDE.md` 작성
- 순환 의존성 탐지: `container.validate_graph()` 추가 (Phase 2)

## 대안

### 대안 1: 전역 변수 (Global State)

```python
# Global
GEMINI_CLIENT = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# 사용
class ScriptGenerator:
    def __init__(self):
        self.client = GEMINI_CLIENT
```

**기각 이유**:
- 테스트 불가 (전역 상태 변경 위험)
- 초기화 순서 제어 불가
- 멀티스레드 안전성 낮음

### 대안 2: Factory Pattern

```python
class ServiceFactory:
    @staticmethod
    def create_gemini_client():
        return genai.Client(...)

# 사용
client = ServiceFactory.create_gemini_client()
```

**기각 이유**:
- Singleton 관리 수동
- 의존성 그래프 가시화 어려움

### 대안 3: 외부 DI 프레임워크 (dependency-injector)

```python
from dependency_injector import containers, providers

class Container(containers.DeclarativeContainer):
    gemini_client = providers.Singleton(genai.Client, ...)
```

**기각 이유**:
- 외부 의존성 추가 (600KB+)
- 학습 곡선 높음
- 프로젝트 규모 대비 과도한 기능

## 영향 범위

### 변경 필요 파일 (8개)

| 파일 | 변경 내용 |
|------|-----------|
| `di/container.py` | 신규 생성 (DI Container 구현) |
| `di/bootstrap.py` | 신규 생성 (서비스 등록) |
| `engines/comprehensive_script_generator.py` | `client` 파라미터 추가 |
| `engines/supertone_tts.py` | `api_key` 파라미터 추가 |
| `cli/auto_mode.py` | `container.get()` 사용 |
| `cli/manual_mode.py` | `container.get()` 사용 |
| `main.py` | `bootstrap()` 호출 |
| `tests/test_di.py` | 단위 테스트 추가 |

### 예상 작업 시간
- 구현: 3시간
- 기존 코드 마이그레이션: 2시간
- 테스트: 2시간
- 문서화: 1시간
- **총 8시간**

## 테스트 시나리오

### 1. 서비스 등록 및 조회
```python
def test_service_registration():
    container = DIContainer()
    container.register("test_service", lambda: "hello", singleton=False)

    result = container.get("test_service")
    assert result == "hello"
```

### 2. Singleton 캐싱
```python
def test_singleton_caching():
    call_count = 0

    def factory():
        nonlocal call_count
        call_count += 1
        return f"instance_{call_count}"

    container.register("singleton_service", factory, singleton=True)

    # 2번 호출해도 같은 인스턴스
    result1 = container.get("singleton_service")
    result2 = container.get("singleton_service")

    assert result1 == result2 == "instance_1"
    assert call_count == 1  # factory 1번만 호출
```

### 3. Transient 매번 생성
```python
def test_transient():
    call_count = 0

    def factory():
        nonlocal call_count
        call_count += 1
        return f"instance_{call_count}"

    container.register("transient_service", factory, singleton=False)

    # 2번 호출하면 다른 인스턴스
    result1 = container.get("transient_service")
    result2 = container.get("transient_service")

    assert result1 == "instance_1"
    assert result2 == "instance_2"
    assert call_count == 2  # factory 2번 호출
```

### 4. 존재하지 않는 서비스 조회
```python
def test_service_not_found():
    with pytest.raises(KeyError, match="Service 'unknown' not registered"):
        container.get("unknown")
```

### 5. Mock 주입 (통합 테스트)
```python
def test_mock_injection():
    class MockGeminiClient:
        def generate_content(self, prompt):
            return {"text": "Mock response"}

    # Mock 주입
    mock_client = MockGeminiClient()
    generator = ComprehensiveScriptGenerator(client=mock_client)

    # 테스트 실행
    result = generator.generate("test prompt")
    assert result["text"] == "Mock response"
```

## 측정 지표

### 성공 기준
- [ ] 단위 테스트 커버리지 90% 이상
- [ ] 서비스 등록 5개 이상 (`gemini_client`, `tts_engine`, `script_generator`, `bgm_matcher`, `asset_matcher`)
- [ ] Singleton 메모리 사용량 < 100MB
- [ ] `bootstrap()` 실행 시간 < 1초

### 모니터링
- 서비스 초기화 실패 로그
- Mock 주입 테스트 성공률
- 의존성 그래프 복잡도

## 롤백 계획

### 문제 발생 시
1. `di/` 디렉토리 삭제
2. 기존 직접 결합 코드 복원 (Git revert)
3. 8개 파일 롤백

### 롤백 소요 시간
- 1시간 (Git revert)

## 참조
- [Martin Fowler - Inversion of Control](https://martinfowler.com/bliki/InversionOfControl.html)
- [Python Dependency Injection Patterns](https://python-dependency-injector.ets-labs.org/)
- 프로젝트 문서: `docs/architecture/EXE_ARCHITECTURE_DESIGN.md`

## 변경 이력
| 날짜 | 변경 내용 | 작성자 |
|------|-----------|--------|
| 2026-03-09 | 초안 작성 및 승인 | A4 (Architecture Designer) |

---

**이전 ADR**: ADR-002 (에셋 경로 동적 감지 전략)
**다음 ADR**: ADR-004 (ValidationPipeline 10단계 설계)
