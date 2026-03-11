# EXE Architecture Diagrams - CruiseDot Video Pipeline

**작성자**: A4 (Architecture Designer Agent)
**작성일**: 2026-03-09
**연계 문서**: EXE_ARCHITECTURE_DESIGN.md

---

## 1. 시스템 컨텍스트 다이어그램 (C4 Level 1)

```mermaid
graph TB
    subgraph External
        User[👤 사용자<br/>기획자/운영자]
        Assets[💾 에셋 저장소<br/>D:\AntiGravity\Assets<br/>2GB+]
        Gemini[🤖 Gemini API<br/>스크립트 생성]
        Supertone[🎙️ Supertone TTS<br/>음성 합성]
        FFmpeg[🎬 FFmpeg<br/>영상 렌더링]
    end

    subgraph CruiseDotSystem[CruiseDot Video Generator]
        CLI[⚙️ CLI Interface<br/>Auto/Manual Mode]
        Pipeline[🔧 Video Pipeline<br/>55초 영상 생성]
    end

    User -->|실행 명령| CLI
    CLI -->|영상 생성 요청| Pipeline
    Pipeline -->|이미지/비디오 로드| Assets
    Pipeline -->|대본 생성 API| Gemini
    Pipeline -->|TTS 합성 API| Supertone
    Pipeline -->|렌더링 실행| FFmpeg
    Pipeline -->|MP4 출력| User

    style CruiseDotSystem fill:#e1f5ff,stroke:#0077cc,stroke-width:3px
    style CLI fill:#fff4e6,stroke:#ff9800
    style Pipeline fill:#e8f5e9,stroke:#4caf50
```

---

## 2. 컨테이너 다이어그램 (C4 Level 2) - EXE 내부 구조

```mermaid
graph TB
    subgraph EXE[CruiseDotGenerator.exe]
        direction TB

        subgraph Entry[진입점]
            Main[main.py<br/>CLI 파서]
        end

        subgraph Validation[검증 계층]
            Pipeline[ValidationPipeline<br/>10단계 검증]
            Input[InputValidator]
            API[APIKeyValidator]
            Path[PathValidator]
            Asset[AssetValidator]
            Dep[DependencyValidator]
        end

        subgraph Core[핵심 계층]
            DI[DI Container<br/>의존성 주입]
            Auto[AutoMode<br/>자동 생성]
            Manual[ManualMode<br/>수동 생성]
        end

        subgraph Engines[엔진 계층]
            Script[ScriptGenerator<br/>대본 생성]
            TTS[TTSEngine<br/>음성 합성]
            BGM[BGMMatcher<br/>배경음악 선택]
            AssetM[AssetMatcher<br/>이미지 선택]
            Render[FFmpegRenderer<br/>영상 렌더링]
        end

        subgraph Utils[유틸리티]
            AssetPath[AssetPathResolver<br/>경로 동적 감지]
            Config[ConfigLoader<br/>설정 로드]
        end

        Main --> Pipeline
        Pipeline --> Input
        Pipeline --> API
        Pipeline --> Path
        Pipeline --> Asset
        Pipeline --> Dep

        Main --> DI
        DI --> Auto
        DI --> Manual

        Auto --> Script
        Manual --> Script

        Script --> TTS
        TTS --> BGM
        BGM --> AssetM
        AssetM --> Render

        AssetPath -.-> Script
        AssetPath -.-> BGM
        AssetPath -.-> AssetM
        Config -.-> DI
    end

    External[외부 의존성<br/>Gemini/Supertone/FFmpeg]
    Assets[에셋 디렉토리<br/>2GB+]
    Output[출력<br/>MP4 영상]

    Main --> External
    Render --> External
    AssetPath --> Assets
    Render --> Output

    style EXE fill:#e1f5ff,stroke:#0077cc,stroke-width:3px
    style Entry fill:#fff4e6,stroke:#ff9800
    style Validation fill:#ffebee,stroke:#f44336
    style Core fill:#e8f5e9,stroke:#4caf50
    style Engines fill:#f3e5f5,stroke:#9c27b0
    style Utils fill:#e0f2f1,stroke:#009688
```

---

## 3. ValidationPipeline 시퀀스 다이어그램

```mermaid
sequenceDiagram
    participant User
    participant Main as main.py
    participant Pipeline as ValidationPipeline
    participant Input as InputValidator
    participant API as APIKeyValidator
    participant Path as PathValidator
    participant Asset as AssetValidator
    participant Dep as DependencyValidator

    User->>Main: python generate.py --mode auto
    Main->>Pipeline: validate_all(context)

    Pipeline->>Input: validate(context)
    Input-->>Pipeline: ✅ Input OK

    Pipeline->>API: validate(context)
    API->>API: Check .env
    alt API Keys Missing
        API-->>Pipeline: ❌ CRITICAL: API keys missing
        Pipeline-->>Main: Validation Failed
        Main-->>User: Error Message + Exit(1)
    else API Keys Present
        API-->>Pipeline: ✅ API Keys OK
    end

    Pipeline->>Path: validate(context)
    Path->>Path: get_asset_dir()
    alt Asset Dir Not Found
        Path-->>Pipeline: ❌ CRITICAL: Asset dir not found
        Pipeline-->>Main: Validation Failed
        Main-->>User: Error + Setup Guide
    else Asset Dir Found
        Path-->>Pipeline: ✅ Paths OK
    end

    Pipeline->>Asset: validate(context)
    Asset->>Asset: Count files in Image/Footage/Music
    Asset-->>Pipeline: ⚠️ WARNING: Low asset count

    Pipeline->>Dep: validate(context)
    Dep->>Dep: which ffmpeg
    alt FFmpeg Not Found
        Dep-->>Pipeline: ❌ CRITICAL: FFmpeg missing
        Pipeline-->>Main: Validation Failed
        Main-->>User: Install FFmpeg Guide
    else FFmpeg Found
        Dep-->>Pipeline: ✅ FFmpeg OK
    end

    Pipeline-->>Main: All Checks Passed (with warnings)
    Main->>Main: Start Video Pipeline
    Main-->>User: ✅ Video Generation Started
```

---

## 4. 의존성 주입 (DI) 컴포넌트 다이어그램

```mermaid
graph LR
    subgraph Bootstrap[DI Bootstrap Phase]
        direction TB
        Env[.env<br/>API Keys]
        Config[cruise_config.yaml<br/>설정]
        Bootstrap_py[bootstrap.py<br/>서비스 등록]

        Env --> Bootstrap_py
        Config --> Bootstrap_py
    end

    subgraph Container[DI Container]
        direction TB
        Registry[Service Registry<br/>서비스 목록]
        Singleton[Singletons Cache<br/>인스턴스 캐시]

        Bootstrap_py --> Registry
        Registry --> Singleton
    end

    subgraph Services[Registered Services]
        GeminiClient[gemini_client<br/>Singleton]
        ScriptGen[script_generator<br/>Transient]
        TTSEngine[tts_engine<br/>Singleton]
        BGMMatcher[bgm_matcher<br/>Singleton]
        AssetMatcher[asset_matcher<br/>Singleton]
    end

    subgraph Consumers[Service Consumers]
        Auto[AutoMode]
        Manual[ManualMode]
        Pipeline_Main[Pipeline]
    end

    Registry --> GeminiClient
    Registry --> ScriptGen
    Registry --> TTSEngine
    Registry --> BGMMatcher
    Registry --> AssetMatcher

    Auto -.->|container.get('script_generator')| Container
    Manual -.->|container.get('script_generator')| Container
    Pipeline_Main -.->|container.get('tts_engine')| Container

    Container -->|Inject| ScriptGen
    Container -->|Inject| TTSEngine

    ScriptGen -.->|depends on| GeminiClient

    style Container fill:#e8f5e9,stroke:#4caf50,stroke-width:3px
    style Bootstrap fill:#fff4e6,stroke:#ff9800
    style Services fill:#e1f5ff,stroke:#0077cc
    style Consumers fill:#f3e5f5,stroke:#9c27b0
```

---

## 5. 에셋 경로 동적 감지 플로우차트

```mermaid
flowchart TD
    Start([프로그램 시작]) --> CheckEnv{환경 변수<br/>CRUISE_ASSET_DIR<br/>존재?}

    CheckEnv -->|Yes| ValidateEnv{경로가<br/>존재하고<br/>유효한가?}
    CheckEnv -->|No| CheckFrozen{EXE 모드<br/>sys.frozen?}

    ValidateEnv -->|Yes| UseEnv[환경 변수 경로 사용]
    ValidateEnv -->|No| CheckFrozen

    CheckFrozen -->|Yes| CheckSymlink{심볼릭 링크<br/>./assets/<br/>존재?}
    CheckFrozen -->|No| CheckDefault{기본 경로<br/>D:/AntiGravity/Assets<br/>존재?}

    CheckSymlink -->|Yes| UseSymlink[심볼릭 링크 경로 사용]
    CheckSymlink -->|No| Error1[에러: 심볼릭 링크 없음<br/>setup_assets.bat 실행 안내]

    CheckDefault -->|Yes| UseDefault[기본 경로 사용]
    CheckDefault -->|No| Error2[에러: 에셋 디렉토리 없음<br/>설치 가이드 표시]

    UseEnv --> Validate[에셋 검증<br/>Image/Footage/Music 확인]
    UseSymlink --> Validate
    UseDefault --> Validate

    Validate --> CountFiles{파일 개수<br/>충분한가?}

    CountFiles -->|Yes| Success[✅ 에셋 로드 완료]
    CountFiles -->|No| Warning[⚠️ 경고: 에셋 부족<br/>계속 진행]

    Error1 --> End([프로그램 종료])
    Error2 --> End
    Success --> Continue([파이프라인 계속])
    Warning --> Continue

    style Start fill:#e8f5e9,stroke:#4caf50
    style Success fill:#c8e6c9,stroke:#4caf50,stroke-width:3px
    style Warning fill:#fff9c4,stroke:#fbc02d
    style Error1 fill:#ffcdd2,stroke:#f44336
    style Error2 fill:#ffcdd2,stroke:#f44336
    style End fill:#ffcdd2,stroke:#f44336
    style Continue fill:#c8e6c9,stroke:#4caf50
```

---

## 6. 자동 업데이트 시퀀스 다이어그램

```mermaid
sequenceDiagram
    participant User
    participant EXE as CruiseDot.exe v1.0
    participant Updater as AutoUpdater
    participant GitHub as GitHub Releases API
    participant Download as Download Manager
    participant FS as File System

    User->>EXE: 프로그램 시작
    EXE->>Updater: check_update()

    Updater->>GitHub: GET /repos/cruise/releases/latest
    GitHub-->>Updater: {"tag_name": "v1.1.0"}

    Updater->>Updater: version_compare("1.1.0", "1.0.0")
    Updater-->>EXE: New version: v1.1.0

    EXE->>User: 💡 업데이트 v1.1.0 사용 가능<br/>다운로드? (y/n)
    User-->>EXE: y

    EXE->>Updater: download_update("1.1.0")
    Updater->>Download: 다운로드 시작
    Download->>GitHub: GET /releases/download/v1.1.0/...zip

    loop 다운로드 중
        GitHub-->>Download: 데이터 청크
        Download->>User: 진행률: 45%...
    end

    Download-->>Updater: 다운로드 완료<br/>temp/update_v1.1.0.zip

    Updater->>FS: 현재 EXE 백업<br/>backup/CruiseDot_v1.0.exe
    FS-->>Updater: 백업 완료

    Updater->>FS: ZIP 압축 해제<br/>update_temp/
    FS-->>Updater: 압축 해제 완료

    Updater->>FS: 파일 교체<br/>CruiseDot.exe 삭제 & 이동
    FS-->>Updater: 교체 완료

    Updater->>FS: 임시 파일 정리
    FS-->>Updater: 정리 완료

    Updater->>EXE: 재시작 준비
    EXE->>FS: subprocess.Popen([new_exe])
    EXE->>User: 재시작 중...

    Note over EXE: 프로세스 종료

    FS->>User: 🎉 v1.1.0 시작
```

---

## 7. 배포 디렉토리 구조 다이어그램

```mermaid
graph TB
    subgraph Release[배포 패키지<br/>CruiseDotGenerator_v1.0.0.zip]
        direction TB

        subgraph Root[루트 디렉토리]
            EXE[CruiseDotGenerator.exe<br/>20MB]
            README[README.txt]
            SetupBat[setup_assets.bat]
        end

        subgraph Internal[_internal/<br/>의존성 80MB]
            Google[google/<br/>Gemini SDK]
            PIL[PIL/<br/>이미지 처리]
            Moviepy[moviepy/<br/>영상 편집]
            Numpy[numpy/<br/>수치 연산]
            FFmpegPy[ffmpeg-python/]
        end

        subgraph ConfigDir[config/<br/>설정 파일]
            CruiseYAML[cruise_config.yaml<br/>사용자 설정]
            EnvExample[.env.example<br/>API 키 예시]
        end

        subgraph DocsDir[docs/<br/>문서]
            ReadmeMD[README.md]
            Setup[SETUP_GUIDE.md]
            Troubleshoot[TROUBLESHOOTING.md]
        end

        subgraph AssetsDir[assets/<br/>심볼릭 링크]
            AssetNote[사용자가 setup_assets.bat로 생성<br/>→ D:\AntiGravity\Assets]
        end

        subgraph OutputsDir[outputs/<br/>자동 생성]
            OutputNote[영상 출력 디렉토리<br/>자동 생성됨]
        end

        subgraph TempDir[temp/<br/>자동 생성]
            TempNote[임시 파일<br/>자동 생성됨]
        end
    end

    Root --> Internal
    Root --> ConfigDir
    Root --> DocsDir
    Root --> AssetsDir
    Root --> OutputsDir
    Root --> TempDir

    style Release fill:#e1f5ff,stroke:#0077cc,stroke-width:3px
    style Root fill:#fff4e6,stroke:#ff9800
    style Internal fill:#e8f5e9,stroke:#4caf50
    style ConfigDir fill:#f3e5f5,stroke:#9c27b0
    style DocsDir fill:#e0f2f1,stroke:#009688
    style AssetsDir fill:#fff9c4,stroke:#fbc02d
    style OutputsDir fill:#c8e6c9,stroke:#4caf50
    style TempDir fill:#e0e0e0,stroke:#757575
```

---

## 8. 설정 파일 계층 구조

```mermaid
graph TB
    subgraph ConfigHierarchy[설정 우선순위<br/>높음 → 낮음]
        direction TB

        Env[1. 환경 변수<br/>.env 파일]
        UserConfig[2. 사용자 설정<br/>config/cruise_config.yaml]
        Defaults[3. 기본 설정<br/>_internal/defaults.yaml<br/>EXE 내장]

        Env --> Merge1{병합}
        UserConfig --> Merge1
        Merge1 --> Merge2{병합}
        Defaults --> Merge2

        Merge2 --> Final[최종 AppConfig 객체]
    end

    subgraph EnvFile[.env 파일 내용]
        direction LR
        EnvContent["GEMINI_API_KEY=abc123<br/>SUPERTONE_API_KEY=xyz789<br/>CRUISE_ASSET_DIR=D:/Assets"]
    end

    subgraph UserYAML[cruise_config.yaml]
        direction LR
        UserContent["assets:<br/>  image_dir: 'D:/AntiGravity/Assets/Image'<br/>rendering:<br/>  target_duration: 55.0<br/>  use_nvenc: true"]
    end

    subgraph DefaultYAML[defaults.yaml]
        direction LR
        DefaultContent["version: '1.0.0'<br/>system:<br/>  min_python_version: '3.11'<br/>logging:<br/>  level: 'INFO'"]
    end

    Env -.-> EnvFile
    UserConfig -.-> UserYAML
    Defaults -.-> DefaultYAML

    Final --> App[애플리케이션 실행]

    style ConfigHierarchy fill:#e1f5ff,stroke:#0077cc,stroke-width:3px
    style Env fill:#ffebee,stroke:#f44336
    style UserConfig fill:#fff4e6,stroke:#ff9800
    style Defaults fill:#e8f5e9,stroke:#4caf50
    style Final fill:#c8e6c9,stroke:#4caf50,stroke-width:3px
```

---

## 9. 렌더링 파이프라인 플로우 (EXE 환경)

```mermaid
flowchart TD
    Start([사용자 명령<br/>python generate.py --mode auto]) --> Validate{ValidationPipeline<br/>10단계 검증}

    Validate -->|실패| Error[에러 메시지 출력<br/>프로그램 종료]
    Validate -->|성공| Bootstrap[DI Bootstrap<br/>서비스 등록]

    Bootstrap --> Mode{모드 선택}

    Mode -->|Auto| AutoWeight[auto_weights.json<br/>가중치 로드]
    Mode -->|Manual| ManualInput[CLI 인자 파싱<br/>port/ship/category]

    AutoWeight --> SelectCombo[조합 랜덤 선택<br/>기항지+선박+카테고리]
    ManualInput --> SelectCombo

    SelectCombo --> Script[ScriptGenerator<br/>대본 생성 Gemini API]

    Script --> SGrade{S등급 점수<br/>>= 90?}

    SGrade -->|No| Retry{재시도<br/>< 3회?}
    SGrade -->|Yes| TTS[TTS 음성 합성<br/>Supertone API]

    Retry -->|Yes| Script
    Retry -->|No| Error

    TTS --> BGM[BGM 선택<br/>5구간 감정 곡선]

    BGM --> AssetMatch[이미지/비디오 선택<br/>키워드 매칭]

    AssetMatch --> Render[FFmpeg 렌더링<br/>55초 영상]

    Render --> Output[MP4 출력<br/>outputs/video_20260309.mp4]

    Output --> UploadPkg{업로드 패키지<br/>생성?}

    UploadPkg -->|Yes| GenPkg[title/description/tags 생성<br/>upload_package/]
    UploadPkg -->|No| Success

    GenPkg --> Success[✅ 완료]

    style Start fill:#e8f5e9,stroke:#4caf50
    style Validate fill:#fff4e6,stroke:#ff9800
    style Script fill:#e1f5ff,stroke:#0077cc
    style Render fill:#f3e5f5,stroke:#9c27b0
    style Success fill:#c8e6c9,stroke:#4caf50,stroke-width:3px
    style Error fill:#ffcdd2,stroke:#f44336
```

---

## 10. 클래스 다이어그램 (핵심 컴포넌트)

```mermaid
classDiagram
    class DIContainer {
        -_services: Dict
        -_singletons: Dict
        +register(name, factory, singleton)
        +get(name) Object
        +clear()
    }

    class ValidationPipeline {
        -validators: List~BaseValidator~
        +validate_all(context) Dict
        +print_report(result)
    }

    class BaseValidator {
        <<abstract>>
        #name: str
        #severity: Severity
        +validate(context)* ValidationResult
    }

    class InputValidator {
        +validate(context) ValidationResult
    }

    class APIKeyValidator {
        +validate(context) ValidationResult
    }

    class PathValidator {
        +validate(context) ValidationResult
    }

    class AssetPathResolver {
        <<static>>
        +get_asset_dir() Path
        +get_temp_dir() Path
        +get_output_dir() Path
    }

    class ComprehensiveScriptGenerator {
        -client: GeminiClient
        +__init__(client)
        +generate(prompt) Dict
    }

    class AutoModeOrchestrator {
        -container: DIContainer
        +run()
        -_select_combination() Tuple
    }

    class ManualModeOrchestrator {
        -container: DIContainer
        +run(context)
    }

    class AutoUpdater {
        -repo: str
        -current_version: str
        +check_update() Optional~str~
        +download_update(version) Path
        +apply_update(zip_path)
        +run_update()
    }

    ValidationPipeline --> BaseValidator : contains
    BaseValidator <|-- InputValidator
    BaseValidator <|-- APIKeyValidator
    BaseValidator <|-- PathValidator

    DIContainer --> ComprehensiveScriptGenerator : creates

    AutoModeOrchestrator --> DIContainer : uses
    ManualModeOrchestrator --> DIContainer : uses

    ComprehensiveScriptGenerator --> AssetPathResolver : uses

    style DIContainer fill:#e8f5e9,stroke:#4caf50
    style ValidationPipeline fill:#ffebee,stroke:#f44336
    style AssetPathResolver fill:#e1f5ff,stroke:#0077cc
    style AutoUpdater fill:#f3e5f5,stroke:#9c27b0
```

---

## 11. 배포 프로세스 플로우

```mermaid
flowchart LR
    subgraph Dev[개발 환경]
        Code[코드 작성<br/>Python 3.11]
        Test[테스트<br/>pytest]
        Commit[Git Commit]
    end

    subgraph Build[빌드 환경]
        Spec[cruise_video_generator.spec<br/>PyInstaller 설정]
        BuildScript[scripts/build_exe.py<br/>빌드 자동화]
        PyInstaller[PyInstaller<br/>--onedir 모드]
        CopyConfig[설정 파일 복사<br/>config/ → dist/]
    end

    subgraph Package[패키징]
        Zip[ZIP 압축<br/>CruiseDot_v1.0.0.zip]
        Checksum[SHA256 체크섬 생성]
        Sign[코드 서명<br/>선택사항]
    end

    subgraph Release[릴리스]
        GitHub[GitHub Releases<br/>업로드]
        Changelog[CHANGELOG.md<br/>작성]
        Tag[Git Tag v1.0.0]
    end

    subgraph Deploy[사용자 배포]
        Download[ZIP 다운로드]
        Extract[압축 해제]
        Setup[setup_assets.bat<br/>심볼릭 링크 생성]
        EnvSetup[.env 파일 생성<br/>API 키 입력]
        Run[CruiseDot.exe 실행]
    end

    Code --> Test
    Test --> Commit
    Commit --> Spec

    Spec --> BuildScript
    BuildScript --> PyInstaller
    PyInstaller --> CopyConfig

    CopyConfig --> Zip
    Zip --> Checksum
    Checksum --> Sign

    Sign --> GitHub
    GitHub --> Changelog
    Changelog --> Tag

    Tag --> Download
    Download --> Extract
    Extract --> Setup
    Setup --> EnvSetup
    EnvSetup --> Run

    style Dev fill:#e8f5e9,stroke:#4caf50
    style Build fill:#fff4e6,stroke:#ff9800
    style Package fill:#e1f5ff,stroke:#0077cc
    style Release fill:#f3e5f5,stroke:#9c27b0
    style Deploy fill:#c8e6c9,stroke:#4caf50
```

---

## 12. 에러 핸들링 플로우

```mermaid
flowchart TD
    Start([프로그램 시작]) --> Validate[ValidationPipeline]

    Validate --> Check1{API 키<br/>존재?}

    Check1 -->|No| Error1[에러: API 키 없음<br/>.env.example 복사 안내]
    Check1 -->|Yes| Check2{에셋<br/>디렉토리?}

    Check2 -->|No| Error2[에러: 에셋 없음<br/>setup_assets.bat 실행]
    Check2 -->|Yes| Check3{FFmpeg<br/>설치?}

    Check3 -->|No| Error3[에러: FFmpeg 없음<br/>설치 가이드 링크]
    Check3 -->|Yes| Pipeline[파이프라인 시작]

    Pipeline --> Script[대본 생성]

    Script --> APICall{Gemini API<br/>호출 성공?}

    APICall -->|Timeout| Retry1{재시도<br/>< 3회?}
    APICall -->|API Error| Error4[에러: API 키 무효<br/>또는 할당량 초과]
    APICall -->|Success| TTS

    Retry1 -->|Yes| Script
    Retry1 -->|No| Error5[에러: API 타임아웃<br/>네트워크 확인]

    TTS[TTS 합성] --> TTSCall{Supertone<br/>호출 성공?}

    TTSCall -->|Error| Error6[에러: TTS 실패<br/>API 키 확인]
    TTSCall -->|Success| Render

    Render[영상 렌더링] --> FFmpegCheck{FFmpeg<br/>실행 성공?}

    FFmpegCheck -->|메모리 부족| Error7[에러: 메모리 부족<br/>다른 프로그램 종료]
    FFmpegCheck -->|GPU 오류| Fallback[CPU 모드로 전환<br/>렌더링 계속]
    FFmpegCheck -->|Success| Success

    Fallback --> Success[✅ 완료]

    Error1 --> Guidance1[상세 가이드 표시<br/>docs/SETUP_GUIDE.md]
    Error2 --> Guidance1
    Error3 --> Guidance1
    Error4 --> Guidance1
    Error5 --> Guidance1
    Error6 --> Guidance1
    Error7 --> Guidance1

    Guidance1 --> End([프로그램 종료<br/>Exit Code 1])

    Success --> End2([프로그램 종료<br/>Exit Code 0])

    style Start fill:#e8f5e9,stroke:#4caf50
    style Success fill:#c8e6c9,stroke:#4caf50,stroke-width:3px
    style Error1 fill:#ffcdd2,stroke:#f44336
    style Error2 fill:#ffcdd2,stroke:#f44336
    style Error3 fill:#ffcdd2,stroke:#f44336
    style Error4 fill:#ffcdd2,stroke:#f44336
    style Error5 fill:#ffcdd2,stroke:#f44336
    style Error6 fill:#ffcdd2,stroke:#f44336
    style Error7 fill:#ffcdd2,stroke:#f44336
    style Fallback fill:#fff9c4,stroke:#fbc02d
```

---

## 부록: 다이어그램 범례

### 색상 코드

| 색상 | 의미 | 예시 |
|------|------|------|
| 🟢 녹색 | 성공, 정상 동작 | 검증 통과, 렌더링 완료 |
| 🟡 노란색 | 경고, 선택적 | 에셋 부족 경고, GPU fallback |
| 🔵 파란색 | 정보, 시스템 컴포넌트 | DI Container, Pipeline |
| 🔴 빨간색 | 오류, 실패 | API 키 없음, FFmpeg 없음 |
| 🟣 보라색 | 외부 의존성 | Gemini API, Supertone |
| 🟠 주황색 | 진입점, 사용자 인터페이스 | CLI, main.py |

---

### 화살표 종류

| 화살표 | 의미 |
|--------|------|
| `-->` | 실선 (필수 흐름) |
| `-.->` | 점선 (선택적 의존성) |
| `==>` | 굵은 선 (주요 데이터 흐름) |

---

**작성**: A4 (Architecture Designer Agent)
**연계 문서**: EXE_ARCHITECTURE_DESIGN.md (상세 설명)
**도구**: Mermaid.js (다이어그램 렌더링)
