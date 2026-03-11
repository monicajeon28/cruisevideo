# YouTube Shorts 파이프라인 아키텍처 다이어그램 모음
## 시스템 구조 시각화 (Mermaid Diagrams)

**작성일**: 2026-03-09
**목적**: 현재 아키텍처 vs 목표 아키텍처 비교 시각화

---

## 1. 시스템 컨텍스트 다이어그램 (C4 Level 1)

### 현재 시스템 전체 구조

```mermaid
graph TB
    subgraph External_Users["External Users"]
        USER[크루즈 영상<br/>마케터]
        VIEWER[YouTube<br/>시청자]
    end

    subgraph Video_Pipeline_System["YouTube Shorts 영상 생성 파이프라인"]
        PIPELINE[Video Generation<br/>Pipeline]
    end

    subgraph External_Systems["External Systems"]
        SUPERTONE[Supertone API<br/>TTS 엔진]
        GEMINI[Google Gemini<br/>스크립트 생성]
        PEXELS[Pexels API<br/>비주얼 소스]
        YOUTUBE[YouTube<br/>플랫폼]
    end

    subgraph Storage["Storage Systems"]
        ASSETS[로컬 에셋<br/>D:/AntiGravity/Assets]
        OUTPUT[Output 저장소<br/>D:/AntiGravity/Output]
    end

    USER -->|스크립트 요청| PIPELINE
    PIPELINE -->|TTS 생성 요청| SUPERTONE
    PIPELINE -->|스크립트 생성| GEMINI
    PIPELINE -->|비주얼 다운로드| PEXELS
    PIPELINE -->|에셋 읽기| ASSETS
    PIPELINE -->|영상 저장| OUTPUT
    USER -->|수동 업로드| YOUTUBE
    OUTPUT -->|MP4 파일| USER
    YOUTUBE -->|시청| VIEWER

    style PIPELINE fill:#ff6b6b,stroke:#c92a2a,color:#fff
    style USER fill:#51cf66,stroke:#2f9e44,color:#fff
    style VIEWER fill:#51cf66,stroke:#2f9e44,color:#fff
```

---

## 2. 컨테이너 다이어그램 (C4 Level 2)

### 현재 아키텍처 - Monolithic Structure

```mermaid
graph TB
    subgraph CLI["CLI Container"]
        CLI_MAIN[generate.py<br/>진입점]
        AUTO_MODE[auto_mode.py<br/>자동 모드]
        MANUAL_MODE[manual_mode.py<br/>수동 모드]
    end

    subgraph Pipeline_Container["Pipeline Container (Core)"]
        GOD_OBJECT[Video55SecPipeline<br/>2000+ 라인<br/>God Object]
        CONFIG[PipelineConfig<br/>200+ 필드]
    end

    subgraph Engines_Container["Engines Container (20+ 모듈)"]
        SCRIPT_GEN[Script Generator<br/>Gemini 연동]
        TTS_ENG[TTS Engine<br/>Supertone]
        BGM_MATCH[BGM Matcher<br/>감정 곡선]
        ASSET_MATCH[Asset Matcher<br/>키워드 매칭]
        SUBTITLE_REND[Subtitle Renderer<br/>이미지 방식]
        FFMPEG_COMP[FFmpeg Composer<br/>렌더링]
    end

    subgraph Storage_Container["Storage Container"]
        ASSETS_DB[(Assets DB<br/>2916 이미지)]
        OUTPUT_DB[(Output DB<br/>생성 영상)]
    end

    CLI_MAIN --> AUTO_MODE
    CLI_MAIN --> MANUAL_MODE
    AUTO_MODE --> GOD_OBJECT
    MANUAL_MODE --> GOD_OBJECT

    GOD_OBJECT -.직접 호출.-> SCRIPT_GEN
    GOD_OBJECT -.직접 호출.-> TTS_ENG
    GOD_OBJECT -.직접 호출.-> BGM_MATCH
    GOD_OBJECT -.직접 호출.-> ASSET_MATCH
    GOD_OBJECT -.직접 호출.-> SUBTITLE_REND
    GOD_OBJECT -.직접 호출.-> FFMPEG_COMP

    GOD_OBJECT --> CONFIG
    ASSET_MATCH --> ASSETS_DB
    GOD_OBJECT --> OUTPUT_DB

    style GOD_OBJECT fill:#ff6b6b,stroke:#c92a2a,color:#fff
    style CONFIG fill:#ffd93d,stroke:#fab005
```

**문제점**:
- `GOD_OBJECT`가 모든 엔진 직접 제어 (Tight Coupling)
- 단위 테스트 불가 (전체만 가능)
- 엔진 교체 시 `GOD_OBJECT` 수정 필수

---

### 목표 아키텍처 - Layered + DI

```mermaid
graph TB
    subgraph Presentation["Presentation Layer"]
        CLI[CLI Interface<br/>generate.py]
        API[REST API<br/>(Future)]
    end

    subgraph Application["Application Layer"]
        ORCHESTRATOR[Video Generation<br/>Orchestrator<br/>200 라인]
        USE_CASES[Use Cases<br/>- GenerateVideo<br/>- ValidateScript<br/>- RenderSubtitle]
    end

    subgraph Domain["Domain Layer"]
        INTERFACES[Interfaces<br/>- ITTSEngine<br/>- IBGMMatcher<br/>- IAssetMatcher]
        ENTITIES[Entities<br/>- Script<br/>- Video<br/>- Audio]
    end

    subgraph Infrastructure["Infrastructure Layer"]
        ADAPTERS[Adapters<br/>- SupertoneTTSAdapter<br/>- BGMMatcherAdapter<br/>- AssetMatcherAdapter]
        REPOSITORIES[Repositories<br/>- VideoRepository<br/>- AssetRepository]
    end

    subgraph DI["DI Container"]
        CONTAINER[AppContainer<br/>의존성 주입]
    end

    CLI --> ORCHESTRATOR
    API -.Future.-> ORCHESTRATOR
    ORCHESTRATOR --> USE_CASES
    USE_CASES --> INTERFACES
    INTERFACES -.구현.-> ADAPTERS
    ADAPTERS --> REPOSITORIES

    CONTAINER -.주입.-> ORCHESTRATOR
    CONTAINER -.주입.-> USE_CASES
    CONTAINER -.주입.-> ADAPTERS

    style ORCHESTRATOR fill:#51cf66,stroke:#2f9e44,color:#fff
    style INTERFACES fill:#339af0,stroke:#1864ab,color:#fff
    style CONTAINER fill:#ff6b6b,stroke:#c92a2a,color:#fff
```

**개선점**:
- `ORCHESTRATOR` 200 라인 (기존 2000 라인 대비 90% 감소)
- Interface 의존 (구체 구현 모름)
- DI Container 자동 주입 (테스트 용이)

---

## 3. 컴포넌트 다이어그램 (C4 Level 3)

### 스크립트 생성 컴포넌트

```mermaid
graph LR
    subgraph Script_Generation["스크립트 생성 서브시스템"]
        SG_FACADE[ScriptGenerationFacade]

        subgraph Generation
            GEMINI_GEN[GeminiScriptGenerator<br/>Gemini API 연동]
            PASONA_TMPL[PasonaTemplateEngine<br/>템플릿 적용]
        end

        subgraph Validation
            S_GRADE_VAL[SGradeValidator<br/>90점 필수 검증]
            BANNED_CHECK[BannedWordChecker<br/>금지어 검증]
            TRUST_CHECK[TrustElementChecker<br/>Trust 3종 검증]
        end

        subgraph Enhancement
            POP_INJECT[PopMessageInjector<br/>3개 Pop 주입]
            REHOOK_INJECT[RehookInjector<br/>15초/32초 Re-hook]
        end
    end

    INPUT[Input<br/>기항지, 선박, 카테고리] --> SG_FACADE
    SG_FACADE --> GEMINI_GEN
    GEMINI_GEN --> PASONA_TMPL
    PASONA_TMPL --> S_GRADE_VAL

    S_GRADE_VAL --> BANNED_CHECK
    BANNED_CHECK --> TRUST_CHECK
    TRUST_CHECK --> POP_INJECT
    POP_INJECT --> REHOOK_INJECT

    REHOOK_INJECT --> OUTPUT[Output<br/>S등급 스크립트 JSON]

    style SG_FACADE fill:#845ef7,stroke:#5f3dc4,color:#fff
    style S_GRADE_VAL fill:#ff6b6b,stroke:#c92a2a,color:#fff
```

---

### 오디오 생성 컴포넌트

```mermaid
graph LR
    subgraph Audio_Generation["오디오 생성 서브시스템"]
        AG_FACADE[AudioGenerationFacade]

        subgraph TTS_Layer
            TTS_ADAPTER[SupertoneTTSAdapter<br/>ITTSEngine 구현]
            ASYNC_TTS[AsyncTTSProcessor<br/>5개 동시 요청]
        end

        subgraph BGM_Layer
            BGM_MATCHER[BGMMatcher<br/>감정 곡선 매칭]
            BGM_BLACKLIST[BGMBlacklist<br/>수면곡 차단]
        end

        subgraph Mixing_Layer
            AUDIO_MIXER[AudioMixer<br/>BGM + TTS + SFX]
            DUCKING[DuckingProcessor<br/>나레이션 구간 BGM 감소]
            LUFS_NORM[LUFSNormalizer<br/>-14dB 정규화]
        end
    end

    SCRIPT[Script JSON] --> AG_FACADE
    AG_FACADE --> TTS_ADAPTER
    TTS_ADAPTER --> ASYNC_TTS
    ASYNC_TTS --> AUDIO_MIXER

    AG_FACADE --> BGM_MATCHER
    BGM_MATCHER --> BGM_BLACKLIST
    BGM_BLACKLIST --> AUDIO_MIXER

    AUDIO_MIXER --> DUCKING
    DUCKING --> LUFS_NORM
    LUFS_NORM --> OUTPUT[Audio<br/>MP3/WAV]

    style AG_FACADE fill:#845ef7,stroke:#5f3dc4,color:#fff
    style BGM_BLACKLIST fill:#ff6b6b,stroke:#c92a2a,color:#fff
    style LUFS_NORM fill:#51cf66,stroke:#2f9e44,color:#fff
```

---

### 비주얼 생성 컴포넌트

```mermaid
graph LR
    subgraph Visual_Generation["비주얼 생성 서브시스템"]
        VG_FACADE[VisualGenerationFacade]

        subgraph Asset_Matching
            KEYWORD_EXT[KeywordExtractor<br/>178개 기항지]
            ASSET_MATCHER[AssetMatcher<br/>로컬 2916 이미지]
            PEXELS_FETCH[PexelsVideoFetcher<br/>API 폴백]
        end

        subgraph Visual_Effects
            KEN_BURNS[KenBurnsEffect<br/>6종 타입]
            COLOR_CORR[ColorCorrection<br/>Natural 프리셋]
            CROSSFADE[CrossfadeTransition<br/>0.25초 겹침]
        end

        subgraph Interleaving
            VISUAL_INTERLEAVE[VisualInterleave<br/>이미지/비디오 교차]
            SEGMENT_BALANCE[SegmentBalancer<br/>80% 이미지 20% 비디오]
        end
    end

    SCRIPT[Script JSON] --> VG_FACADE
    VG_FACADE --> KEYWORD_EXT
    KEYWORD_EXT --> ASSET_MATCHER
    ASSET_MATCHER -.로컬 부족 시.-> PEXELS_FETCH

    ASSET_MATCHER --> VISUAL_INTERLEAVE
    PEXELS_FETCH --> VISUAL_INTERLEAVE
    VISUAL_INTERLEAVE --> SEGMENT_BALANCE

    SEGMENT_BALANCE --> KEN_BURNS
    KEN_BURNS --> COLOR_CORR
    COLOR_CORR --> CROSSFADE
    CROSSFADE --> OUTPUT[VisualSegments<br/>List]

    style VG_FACADE fill:#845ef7,stroke:#5f3dc4,color:#fff
    style PEXELS_FETCH fill:#ffd93d,stroke:#fab005
```

---

### 렌더링 컴포넌트 (Phase B-9)

```mermaid
graph LR
    subgraph Rendering_Subsystem["렌더링 서브시스템"]
        RENDER_FACADE[RenderingFacade]

        subgraph Subtitle_Layer
            SUBTITLE_IMG_REND[SubtitleImageRenderer<br/>한글 텍스트 → PNG]
            PIL_PROCESSOR[PIL Processor<br/>맑은 고딕 3px stroke]
        end

        subgraph Overlay_Layer
            FFMPEG_OVERLAY[FFmpegImageOverlayComposer<br/>PNG 이미지 오버레이]
            CTA_OVERLAY[CTAOverlay<br/>3단계 증폭]
            POP_OVERLAY[PopMessageOverlay<br/>3개 Pop]
        end

        subgraph Final_Render
            FFMPEG_PIPELINE[FFmpegPipeline<br/>최종 합성]
            NVENC_RENDER[NVENCRenderer<br/>GPU 가속 28초]
        end
    end

    VISUALS[VisualSegments] --> RENDER_FACADE
    AUDIO[Audio Mix] --> RENDER_FACADE
    SCRIPT[Script JSON] --> RENDER_FACADE

    RENDER_FACADE --> SUBTITLE_IMG_REND
    SUBTITLE_IMG_REND --> PIL_PROCESSOR
    PIL_PROCESSOR --> FFMPEG_OVERLAY

    RENDER_FACADE --> CTA_OVERLAY
    RENDER_FACADE --> POP_OVERLAY

    FFMPEG_OVERLAY --> FFMPEG_PIPELINE
    CTA_OVERLAY --> FFMPEG_PIPELINE
    POP_OVERLAY --> FFMPEG_PIPELINE
    VISUALS --> FFMPEG_PIPELINE
    AUDIO --> FFMPEG_PIPELINE

    FFMPEG_PIPELINE --> NVENC_RENDER
    NVENC_RENDER --> OUTPUT[MP4<br/>55초 1080x1920]

    style RENDER_FACADE fill:#845ef7,stroke:#5f3dc4,color:#fff
    style NVENC_RENDER fill:#51cf66,stroke:#2f9e44,color:#fff
    style PIL_PROCESSOR fill:#339af0,stroke:#1864ab,color:#fff
```

---

## 4. 데이터 흐름 다이어그램 (DFD)

### 전체 데이터 플로우

```mermaid
flowchart TD
    START([시작<br/>사용자 요청]) --> INPUT_CONFIG{입력 설정<br/>기항지/선박/카테고리}

    INPUT_CONFIG --> SCRIPT_GEN[스크립트 생성<br/>Gemini API]
    SCRIPT_GEN --> S_GRADE_VAL{S등급 검증<br/>90점 이상?}

    S_GRADE_VAL -->|실패| SCRIPT_GEN
    S_GRADE_VAL -->|통과| PARALLEL_PROCESS{병렬 처리}

    PARALLEL_PROCESS --> TTS_GEN[TTS 오디오 생성<br/>5개 동시 요청]
    PARALLEL_PROCESS --> BGM_SELECT[BGM 선택<br/>감정 곡선 매칭]
    PARALLEL_PROCESS --> VISUAL_MATCH[비주얼 매칭<br/>키워드 기반]

    TTS_GEN --> AUDIO_MIX[오디오 믹싱<br/>BGM + TTS + SFX]
    BGM_SELECT --> AUDIO_MIX

    VISUAL_MATCH --> KEN_BURNS_FX[Ken Burns 효과<br/>6종 타입 순환]
    KEN_BURNS_FX --> CROSSFADE_FX[Crossfade 전환<br/>0.25초 겹침]

    CROSSFADE_FX --> SUBTITLE_RENDER[자막 렌더링<br/>PNG 이미지]
    AUDIO_MIX --> SUBTITLE_RENDER

    SUBTITLE_RENDER --> FFMPEG_COMPOSE[FFmpeg 합성<br/>NVENC GPU]
    FFMPEG_COMPOSE --> DISK_WRITE[(디스크 저장<br/>Output 디렉토리)]

    DISK_WRITE --> END([완료<br/>MP4 55초])

    style S_GRADE_VAL fill:#ff6b6b,stroke:#c92a2a,color:#fff
    style PARALLEL_PROCESS fill:#ffd93d,stroke:#fab005
    style FFMPEG_COMPOSE fill:#51cf66,stroke:#2f9e44,color:#fff
```

---

## 5. 배포 다이어그램 (Deployment)

### 현재 배포 구조 (로컬 Windows 환경)

```mermaid
graph TB
    subgraph Local_Machine["로컬 PC (Windows 11)"]
        subgraph Application_Node["Application Node"]
            PYTHON[Python 3.12<br/>가상환경]
            PIPELINE[Video Pipeline<br/>generate.py]
        end

        subgraph GPU_Node["GPU Node"]
            NVENC[NVIDIA RTX<br/>NVENC 인코더]
        end

        subgraph Storage_Node["Storage Node"]
            ASSETS_DISK[D:/AntiGravity/Assets<br/>2.5GB 에셋]
            OUTPUT_DISK[D:/AntiGravity/Output<br/>생성 영상]
            TEMP_DISK[temp/<br/>임시 파일]
        end
    end

    subgraph External_APIs["External APIs (Cloud)"]
        SUPERTONE_API[Supertone TTS API<br/>Seoul Region]
        GEMINI_API[Google Gemini API<br/>Global]
        PEXELS_API[Pexels API<br/>Global]
    end

    PIPELINE --> PYTHON
    PIPELINE --> NVENC
    PIPELINE --> ASSETS_DISK
    PIPELINE --> OUTPUT_DISK
    PIPELINE --> TEMP_DISK

    PIPELINE -->|HTTPS| SUPERTONE_API
    PIPELINE -->|HTTPS| GEMINI_API
    PIPELINE -->|HTTPS| PEXELS_API

    style PIPELINE fill:#845ef7,stroke:#5f3dc4,color:#fff
    style NVENC fill:#51cf66,stroke:#2f9e44,color:#fff
```

---

### 목표 배포 구조 (Cloud 확장 가능)

```mermaid
graph TB
    subgraph Cloud_Infra["Cloud Infrastructure (Future)"]
        subgraph K8s_Cluster["Kubernetes Cluster"]
            POD1[Video Pipeline Pod 1<br/>Stateless]
            POD2[Video Pipeline Pod 2<br/>Stateless]
            POD3[Video Pipeline Pod 3<br/>Stateless]
        end

        subgraph Services
            LOAD_BALANCER[Load Balancer]
            API_GATEWAY[API Gateway]
        end

        subgraph Storage
            S3_ASSETS[S3/Cloud Storage<br/>Assets Bucket]
            S3_OUTPUT[S3/Cloud Storage<br/>Output Bucket]
            REDIS_CACHE[Redis Cache<br/>TTS 결과 캐싱]
        end

        subgraph GPU_Pool
            GPU1[GPU Instance 1<br/>NVENC]
            GPU2[GPU Instance 2<br/>NVENC]
        end
    end

    USER[사용자] --> LOAD_BALANCER
    LOAD_BALANCER --> API_GATEWAY
    API_GATEWAY --> POD1
    API_GATEWAY --> POD2
    API_GATEWAY --> POD3

    POD1 --> S3_ASSETS
    POD2 --> S3_ASSETS
    POD3 --> S3_ASSETS

    POD1 --> GPU1
    POD2 --> GPU2
    POD3 --> GPU1

    POD1 --> REDIS_CACHE
    POD2 --> REDIS_CACHE
    POD3 --> REDIS_CACHE

    POD1 --> S3_OUTPUT
    POD2 --> S3_OUTPUT
    POD3 --> S3_OUTPUT

    style LOAD_BALANCER fill:#ff6b6b,stroke:#c92a2a,color:#fff
    style GPU1 fill:#51cf66,stroke:#2f9e44,color:#fff
    style GPU2 fill:#51cf66,stroke:#2f9e44,color:#fff
```

---

## 6. 시퀀스 다이어그램 (상세 플로우)

### 영상 생성 전체 플로우 (성공 케이스)

```mermaid
sequenceDiagram
    actor User
    participant CLI
    participant Orchestrator
    participant ScriptGen
    participant SGradeVal
    participant TTSGen
    participant BGMMatcher
    participant AssetMatcher
    participant Renderer
    participant Storage

    User->>CLI: python generate.py --auto
    CLI->>Orchestrator: generate_video(config)

    rect rgb(220, 220, 255)
        Note over Orchestrator,SGradeVal: Phase 1: 스크립트 생성 (3초)
        Orchestrator->>ScriptGen: generate(port, ship, category)
        ScriptGen->>ScriptGen: Gemini API 호출
        ScriptGen->>SGradeVal: validate(script)

        alt S등급 미달 (< 90점)
            SGradeVal-->>ScriptGen: 재생성 요청
            ScriptGen->>ScriptGen: Gemini API 재호출
        end

        SGradeVal-->>ScriptGen: 통과 (90점+)
        ScriptGen-->>Orchestrator: Script JSON
    end

    rect rgb(255, 220, 220)
        Note over Orchestrator,AssetMatcher: Phase 2: 병렬 처리 (15초)

        par TTS 생성
            Orchestrator->>TTSGen: generate_audio(script)
            TTSGen->>TTSGen: 5개 동시 요청 (Async)
            TTSGen-->>Orchestrator: AudioClips
        and BGM 선택
            Orchestrator->>BGMMatcher: match(emotion_curve)
            BGMMatcher->>BGMMatcher: 블랙리스트 필터링
            BGMMatcher-->>Orchestrator: BGM Path
        and 비주얼 매칭
            Orchestrator->>AssetMatcher: match(keywords)
            AssetMatcher->>AssetMatcher: 로컬 에셋 검색

            alt 로컬 부족
                AssetMatcher->>AssetMatcher: Pexels API 폴백
            end

            AssetMatcher-->>Orchestrator: VisualSegments
        end
    end

    rect rgb(220, 255, 220)
        Note over Orchestrator,Storage: Phase 3: 렌더링 (28초)
        Orchestrator->>Renderer: render(audio, visuals, script)
        Renderer->>Renderer: 자막 PNG 생성 (PIL)
        Renderer->>Renderer: FFmpeg 이미지 오버레이
        Renderer->>Renderer: NVENC GPU 렌더링
        Renderer->>Storage: save(video.mp4)
        Storage-->>Renderer: 저장 완료
        Renderer-->>Orchestrator: Video Path
    end

    Orchestrator-->>CLI: 성공 (영상 경로)
    CLI-->>User: ✅ 영상 생성 완료 (55초)
```

---

### 스크립트 검증 플로우 (S등급 루프)

```mermaid
sequenceDiagram
    participant ScriptGen as Script Generator
    participant Gemini as Gemini API
    participant SGrade as S-Grade Validator
    participant BannedCheck as Banned Word Checker
    participant TrustCheck as Trust Element Checker
    participant PopCheck as Pop Message Validator

    ScriptGen->>Gemini: generate_script(prompt)
    Gemini-->>ScriptGen: Raw Script JSON

    loop S등급 달성까지 (최대 3회)
        ScriptGen->>SGrade: validate(script)

        SGrade->>BannedCheck: check_banned_words()
        alt 금지어 발견
            BannedCheck-->>SGrade: -5점 (금지어 1개당)
        else 금지어 없음
            BannedCheck-->>SGrade: +10점
        end

        SGrade->>TrustCheck: check_trust_elements()
        alt Trust 3종 미달
            TrustCheck-->>SGrade: -5점 (요소 누락당)
        else Trust 3종 충족
            TrustCheck-->>SGrade: +15점
        end

        SGrade->>PopCheck: check_pop_messages()
        alt Pop 3개 아님
            PopCheck-->>SGrade: -3점 (개수 차이당)
        else Pop 정확히 3개
            PopCheck-->>SGrade: +10점
        end

        SGrade->>SGrade: calculate_total_score()

        alt 점수 < 90점
            SGrade-->>ScriptGen: 재생성 요청 (GAP 리포트)
            ScriptGen->>Gemini: regenerate_with_feedback(gap_report)
        else 점수 >= 90점
            SGrade-->>ScriptGen: ✅ S등급 통과 (90점+)
        end
    end

    alt 3회 재시도 후 실패
        ScriptGen-->>ScriptGen: ❌ 예외 발생 (S등급 미달)
    else 성공
        ScriptGen-->>ScriptGen: ✅ S등급 스크립트 확정
    end
```

---

## 7. 의존성 그래프

### 현재 의존성 (Tight Coupling)

```mermaid
graph TD
    PIPELINE[Video55SecPipeline<br/>2000 라인]

    PIPELINE -->|직접 의존| TTS[SupertoneTTS]
    PIPELINE -->|직접 의존| BGM[BGMMatcher]
    PIPELINE -->|직접 의존| ASSET[AssetMatcher]
    PIPELINE -->|직접 의존| SUBTITLE[SubtitleRenderer]
    PIPELINE -->|직접 의존| FFMPEG[FFmpegComposer]
    PIPELINE -->|직접 의존| SCRIPT[ScriptGenerator]
    PIPELINE -->|직접 의존| SGRADE[SGradeValidator]
    PIPELINE -->|직접 의존| KEYWORD[KeywordExtractor]
    PIPELINE -->|직접 의존| COLOR[ColorCorrection]
    PIPELINE -->|직접 의존| KENBURNS[KenBurnsEffect]

    TTS -->|의존| SUPERTONE_API[Supertone API]
    SCRIPT -->|의존| GEMINI_API[Gemini API]
    ASSET -->|의존| PEXELS_API[Pexels API]

    style PIPELINE fill:#ff6b6b,stroke:#c92a2a,color:#fff
```

**문제**: 모든 화살표가 `PIPELINE`에서 시작 (단방향 의존, 테스트 불가)

---

### 목표 의존성 (Layered + DI)

```mermaid
graph TD
    subgraph Presentation
        CLI[CLI Interface]
    end

    subgraph Application
        ORCH[Orchestrator]
        USE_CASE[Use Cases]
    end

    subgraph Domain
        ITTS[ITTSEngine<br/>Interface]
        IBGM[IBGMMatcher<br/>Interface]
        IASSET[IAssetMatcher<br/>Interface]
    end

    subgraph Infrastructure
        TTS_ADAPTER[SupertoneTTSAdapter]
        BGM_IMPL[BGMMatcher Impl]
        ASSET_IMPL[AssetMatcher Impl]
    end

    CLI -->|의존| ORCH
    ORCH -->|의존| USE_CASE
    USE_CASE -->|의존| ITTS
    USE_CASE -->|의존| IBGM
    USE_CASE -->|의존| IASSET

    ITTS -.구현.-> TTS_ADAPTER
    IBGM -.구현.-> BGM_IMPL
    IASSET -.구현.-> ASSET_IMPL

    TTS_ADAPTER -->|의존| SUPERTONE_API[Supertone API]

    style ITTS fill:#339af0,stroke:#1864ab,color:#fff
    style IBGM fill:#339af0,stroke:#1864ab,color:#fff
    style IASSET fill:#339af0,stroke:#1864ab,color:#fff
```

**개선점**:
- Domain이 Infrastructure 모름 (DIP 준수)
- Interface에 의존 (Mock 주입 가능)
- 단방향 화살표 (Acyclic Dependency)

---

## 8. 레이어 다이어그램

### Layered Architecture 상세

```mermaid
graph TB
    subgraph Presentation_Layer["📱 Presentation Layer"]
        CLI_INTERFACE[CLI Interface<br/>generate.py]
        REST_API[REST API<br/>(Future Expansion)]
    end

    subgraph Application_Layer["🎯 Application Layer"]
        ORCHESTRATOR[Video Generation<br/>Orchestrator]

        subgraph Use_Cases
            UC_GEN[Generate Video<br/>Use Case]
            UC_VAL[Validate Script<br/>Use Case]
            UC_RENDER[Render Subtitle<br/>Use Case]
        end

        subgraph DTOs
            VIDEO_DTO[VideoDTO]
            SCRIPT_DTO[ScriptDTO]
            AUDIO_DTO[AudioDTO]
        end
    end

    subgraph Domain_Layer["🏛️ Domain Layer"]
        subgraph Entities
            SCRIPT_ENTITY[Script Entity]
            VIDEO_ENTITY[Video Entity]
            AUDIO_ENTITY[Audio Entity]
        end

        subgraph Value_Objects
            VISUAL_VO[Visual VO]
            SUBTITLE_VO[Subtitle VO]
            CTA_VO[CTA VO]
        end

        subgraph Interfaces
            ITTS[ITTSEngine]
            IBGM[IBGMMatcher]
            IASSET[IAssetMatcher]
            IRENDERER[IRenderer]
        end
    end

    subgraph Infrastructure_Layer["🔧 Infrastructure Layer"]
        subgraph Adapters
            TTS_ADAPTER[SupertoneTTSAdapter]
            BGM_ADAPTER[BGMMatcherAdapter]
            ASSET_ADAPTER[AssetMatcherAdapter]
            FFMPEG_ADAPTER[FFmpegRendererAdapter]
        end

        subgraph Repositories
            VIDEO_REPO[VideoRepository]
            ASSET_REPO[AssetRepository]
        end

        subgraph External
            SUPERTONE[Supertone API Client]
            GEMINI[Gemini API Client]
            PEXELS[Pexels API Client]
        end
    end

    CLI_INTERFACE --> ORCHESTRATOR
    REST_API -.Future.-> ORCHESTRATOR

    ORCHESTRATOR --> UC_GEN
    ORCHESTRATOR --> UC_VAL
    ORCHESTRATOR --> UC_RENDER

    UC_GEN --> SCRIPT_ENTITY
    UC_GEN --> VIDEO_ENTITY
    UC_GEN --> ITTS
    UC_GEN --> IBGM

    ITTS -.구현.-> TTS_ADAPTER
    IBGM -.구현.-> BGM_ADAPTER
    IASSET -.구현.-> ASSET_ADAPTER
    IRENDERER -.구현.-> FFMPEG_ADAPTER

    TTS_ADAPTER --> SUPERTONE
    ASSET_ADAPTER --> PEXELS

    style Presentation_Layer fill:#e3f2fd
    style Application_Layer fill:#fff3e0
    style Domain_Layer fill:#f3e5f5
    style Infrastructure_Layer fill:#e8f5e9
```

---

## 9. 플러그인 아키텍처

### Content Type Plugin System

```mermaid
graph LR
    subgraph Core_System["Core System"]
        PLUGIN_REGISTRY[Plugin Registry<br/>중앙 관리]
    end

    subgraph Plugin_Interface["Plugin Interface"]
        I_CONTENT_TYPE[IContentTypePlugin<br/>Interface]
    end

    subgraph Plugins["Plugins (확장 가능)"]
        EDUCATION[Education Plugin<br/>교육형]
        COMPARISON[Comparison Plugin<br/>비교형]
        BUCKET_LIST[Bucket List Plugin<br/>버킷리스트]
        FEAR_RESOLVE[Fear Resolution Plugin<br/>불안 해소]
        CUSTOM[Custom Plugin<br/>(사용자 정의)]
    end

    PLUGIN_REGISTRY -->|관리| I_CONTENT_TYPE

    I_CONTENT_TYPE -.구현.-> EDUCATION
    I_CONTENT_TYPE -.구현.-> COMPARISON
    I_CONTENT_TYPE -.구현.-> BUCKET_LIST
    I_CONTENT_TYPE -.구현.-> FEAR_RESOLVE
    I_CONTENT_TYPE -.구현.-> CUSTOM

    EDUCATION -->|제공| HOOK_TMPL_E[Hook Templates]
    EDUCATION -->|제공| BGM_KEYWORDS_E[BGM Keywords]
    EDUCATION -->|제공| CTA_TEXT_E[CTA Text]

    COMPARISON -->|제공| HOOK_TMPL_C[Hook Templates]
    COMPARISON -->|제공| BGM_KEYWORDS_C[BGM Keywords]
    COMPARISON -->|제공| CTA_TEXT_C[CTA Text]

    style PLUGIN_REGISTRY fill:#ff6b6b,stroke:#c92a2a,color:#fff
    style I_CONTENT_TYPE fill:#339af0,stroke:#1864ab,color:#fff
    style CUSTOM fill:#51cf66,stroke:#2f9e44,color:#fff
```

**확장 방법**:
```python
# 새 플러그인 추가 (기존 코드 수정 없음)
class CustomPlugin(IContentTypePlugin):
    def get_hook_templates(self):
        return ["커스텀 Hook"]

    def get_bgm_keywords(self):
        return ["custom", "keywords"]

    def get_cta_text(self):
        return "커스텀 CTA"

# 등록 (config.yaml 또는 런타임)
ContentTypeRegistry.register("CUSTOM", CustomPlugin())
```

---

## 10. 성능 최적화 다이어그램

### 병렬 처리 파이프라인

```mermaid
gantt
    title 영상 생성 타임라인 (병렬 처리)
    dateFormat  X
    axisFormat %s초

    section 스크립트
    Gemini API 호출       :s1, 0, 3s
    S등급 검증             :s2, after s1, 1s

    section 오디오 (병렬)
    TTS 생성 (5개 동시)    :a1, after s2, 8s
    BGM 선택               :a2, after s2, 2s
    오디오 믹싱            :a3, after a1, 3s

    section 비주얼 (병렬)
    키워드 추출            :v1, after s2, 1s
    에셋 매칭              :v2, after v1, 4s
    Ken Burns 적용         :v3, after v2, 3s
    Crossfade 전환         :v4, after v3, 2s

    section 렌더링
    자막 PNG 생성          :r1, after a3, 3s
    FFmpeg 이미지 오버레이 :r2, after r1, 5s
    NVENC GPU 렌더링      :r3, after r2, 20s

    section 총 시간
    전체                   :crit, 0, 46s
```

**최적화 포인트**:
- TTS + BGM + 비주얼 병렬 처리 (15초 → 8초, 47% 단축)
- NVENC GPU 렌더링 (840초 → 28초, 96.7% 단축)
- AsyncTTS 5개 동시 요청 (40초 → 8초, 80% 단축)

---

## 11. 에러 처리 플로우

### Retry + Fallback 전략

```mermaid
graph TD
    START([영상 생성 시작]) --> TRY_PRIMARY{Primary 시도}

    TRY_PRIMARY -->|성공| SUCCESS([✅ 성공])
    TRY_PRIMARY -->|실패| RETRY_COUNT{재시도 횟수<br/>< 3?}

    RETRY_COUNT -->|YES| EXPONENTIAL_BACKOFF[Exponential Backoff<br/>1초 → 2초 → 4초]
    EXPONENTIAL_BACKOFF --> TRY_PRIMARY

    RETRY_COUNT -->|NO| FALLBACK_CHECK{Fallback<br/>사용 가능?}

    FALLBACK_CHECK -->|YES| TRY_FALLBACK[Fallback 시도<br/>예: Pexels API]
    TRY_FALLBACK -->|성공| SUCCESS
    TRY_FALLBACK -->|실패| CIRCUIT_BREAKER{Circuit Breaker<br/>열림?}

    CIRCUIT_BREAKER -->|YES| FAIL_FAST([⚡ Fail Fast<br/>즉시 실패])
    CIRCUIT_BREAKER -->|NO| FINAL_RETRY[Final Retry<br/>마지막 시도]

    FINAL_RETRY -->|성공| SUCCESS
    FINAL_RETRY -->|실패| ERROR_LOG[에러 로깅<br/>Sentry/CloudWatch]

    ERROR_LOG --> NOTIFY_USER([❌ 사용자 알림<br/>실패 원인])

    FALLBACK_CHECK -->|NO| ERROR_LOG

    style SUCCESS fill:#51cf66,stroke:#2f9e44,color:#fff
    style FAIL_FAST fill:#ff6b6b,stroke:#c92a2a,color:#fff
    style NOTIFY_USER fill:#ffd93d,stroke:#fab005
```

---

## 12. 캐싱 전략

### Multi-Level Cache

```mermaid
graph LR
    REQUEST[요청] --> L1_CHECK{L1 Cache<br/>메모리}

    L1_CHECK -->|HIT| L1_RETURN[메모리에서 반환<br/>0.001초]
    L1_CHECK -->|MISS| L2_CHECK{L2 Cache<br/>Redis}

    L2_CHECK -->|HIT| L2_RETURN[Redis에서 반환<br/>0.01초]
    L2_CHECK -->|MISS| L3_CHECK{L3 Cache<br/>디스크}

    L3_CHECK -->|HIT| L3_RETURN[디스크에서 반환<br/>0.1초]
    L3_CHECK -->|MISS| API_CALL[API 호출<br/>3초]

    API_CALL --> UPDATE_L3[L3 업데이트<br/>디스크 저장]
    UPDATE_L3 --> UPDATE_L2[L2 업데이트<br/>Redis 저장]
    UPDATE_L2 --> UPDATE_L1[L1 업데이트<br/>메모리 저장]
    UPDATE_L1 --> RETURN[반환]

    L1_RETURN --> RETURN
    L2_RETURN --> RETURN
    L3_RETURN --> RETURN

    style L1_RETURN fill:#51cf66,stroke:#2f9e44,color:#fff
    style L2_RETURN fill:#ffd93d,stroke:#fab005
    style L3_RETURN fill:#ff922b,stroke:#fd7e14
    style API_CALL fill:#ff6b6b,stroke:#c92a2a,color:#fff
```

**캐시 대상**:
- TTS 결과 (동일 텍스트 재생성 방지)
- BGM 매칭 결과 (감정 곡선 패턴)
- 에셋 인덱스 (2916 이미지 메타데이터)

---

## 부록: 다이어그램 규칙

### Mermaid 색상 코드

| 색상 | 의미 | 사용 예 |
|------|------|---------|
| `#ff6b6b` (빨강) | 문제점, 병목, Critical | God Object, Tight Coupling |
| `#51cf66` (초록) | 성공, 최적화, 권장 | S등급 달성, NVENC 렌더링 |
| `#339af0` (파랑) | 인터페이스, 추상화 | ITTSEngine, IBGMMatcher |
| `#845ef7` (보라) | Orchestrator, Facade | VideoGenerationOrchestrator |
| `#ffd93d` (노랑) | 경고, 주의 | Fallback, Retry |

### 다이어그램 유형 선택 가이드

| 목적 | 다이어그램 유형 | Mermaid 문법 |
|------|----------------|-------------|
| 전체 시스템 구조 | System Context (C4 L1) | `graph TB` |
| 컨테이너 구조 | Container Diagram (C4 L2) | `graph TB` |
| 클래스 관계 | Component Diagram (C4 L3) | `graph LR` |
| 실행 흐름 | Sequence Diagram | `sequenceDiagram` |
| 데이터 흐름 | Data Flow Diagram | `flowchart TD` |
| 일정 계획 | Gantt Chart | `gantt` |

---

**문서 작성**: A4 (Architecture Designer Agent)
**작성일**: 2026-03-09
**버전**: 1.0
**용도**: 아키텍처 리뷰 시각화 자료
