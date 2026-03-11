# EXE 테스트 빠른 참조 가이드

프로덕션 배포 전 5분 체크리스트

---

## 1분 빠른 검증

```bash
# 1. EXE 빌드
pyinstaller cruise_video_generator.spec

# 2. 기본 실행
dist/CruiseVideoGenerator.exe --version

# 3. 핵심 3개 테스트
cd tests/exe
pytest test_exe_smoke.py::TestEXESmoke::test_exe_launch -v
pytest test_exe_smoke.py::TestEXESmoke::test_assets_access -v
pytest test_security_injection.py::TestPromptInjection::test_prompt_injection_defense -v
```

**결과**: 3 PASSED → 배포 가능

---

## 필수 테스트 (Layer 1 + Layer 2)

### Layer 1: 스모크 테스트 (2분)

```bash
pytest tests/exe/test_exe_smoke.py -v
```

**PASS 기준**: 8개 이상 / 10개 (80%)

**실패 시 대응**:
- `test_exe_exists` 실패 → EXE 빌드 다시
- `test_ffmpeg_available` 실패 → FFmpeg 설치
- `test_assets_access` 실패 → Assets 경로 확인

### Layer 2: 보안 테스트 (10분)

```bash
pytest tests/exe/test_security_injection.py -v -m security
```

**PASS 기준**: 18개 이상 / 20개 (90%)

**실패 시 대응**:
- Prompt Injection 실패 → Input Sanitizer 추가
- Path Traversal 실패 → 경로 검증 로직 추가
- API 키 노출 실패 → 로그 마스킹 추가

---

## 배포 전 체크리스트

```markdown
## 필수 (10분)
- [ ] EXE 빌드 성공 (dist/CruiseVideoGenerator.exe)
- [ ] Layer 1 스모크 테스트 80% PASS
- [ ] Layer 2 보안 테스트 90% PASS
- [ ] EXE 파일 크기 50MB 이상
- [ ] .env.example 파일 존재

## 권장 (20분)
- [ ] Layer 2 JSON 파싱 테스트 80% PASS
- [ ] 수동 실행 테스트 (dist/CruiseVideoGenerator.exe --help)
- [ ] README.txt 작성

## 선택 (1시간)
- [ ] Layer 3 통합 테스트 70% PASS (API 비용 $0.15)
- [ ] 신규 PC에서 배포 패키지 테스트
- [ ] 영상 1편 생성 확인
```

---

## 빠른 명령어 모음

### 테스트 실행

```bash
# 전체 테스트
pytest tests/exe/ -v

# 스모크만
pytest tests/exe/test_exe_smoke.py -v

# 보안만
pytest tests/exe/test_security_injection.py -v

# 느린 테스트 제외
pytest tests/exe/ -v -m "not slow"

# 특정 테스트만
pytest tests/exe/test_exe_smoke.py::TestEXESmoke::test_exe_launch -v

# 실패한 것만 재실행
pytest tests/exe/ --lf -v
```

### EXE 빌드

```bash
# 기본 빌드
pyinstaller cruise_video_generator.spec

# 클린 빌드
pyinstaller --clean cruise_video_generator.spec

# 디버그 모드 빌드
pyinstaller --debug all cruise_video_generator.spec
```

### 수동 검증

```bash
# 버전 확인
dist/CruiseVideoGenerator.exe --version

# 도움말
dist/CruiseVideoGenerator.exe --help

# 환경 변수 확인
dist/CruiseVideoGenerator.exe --check-env

# Dry-run (API 호출 없음)
dist/CruiseVideoGenerator.exe --dry-run --mode auto

# 실제 실행
dist/CruiseVideoGenerator.exe --mode auto --count 1
```

---

## 문제 해결 빠른 가이드

### 문제: EXE 실행 안 됨

```
PermissionError: [Errno 13] Permission denied
```

**해결**:
```bash
# 관리자 권한으로 실행
# 또는 백신 예외 처리
```

### 문제: Assets 경로 오류

```
FileNotFoundError: D:/AntiGravity/Assets/Image
```

**해결**:
```bash
# 경로 생성
mkdir -p D:/AntiGravity/Assets/Image

# 또는 코드 수정
# generate_video_55sec_pipeline.py
ASSETS_DIR = Path("D:/AntiGravity/Assets")  # 절대 경로
```

### 문제: FFmpeg 없음

```
FileNotFoundError: ffmpeg
```

**해결**:
```bash
# Windows
choco install ffmpeg

# 또는 PATH 추가
setx PATH "%PATH%;C:\ffmpeg\bin"
```

### 문제: API 키 없음

```
KeyError: 'GEMINI_API_KEY'
```

**해결**:
```bash
# .env 파일 생성
echo "GEMINI_API_KEY=AIzaSy..." > .env
echo "SUPERTONE_API_KEY=..." >> .env
echo "OPENAI_API_KEY=sk-..." >> .env
```

---

## 성능 목표

| 지표 | 목표 | 확인 방법 |
|------|------|-----------|
| 빌드 시간 | 2분 이하 | `pyinstaller` 실행 시간 |
| EXE 크기 | 50~200MB | `ls -lh dist/CruiseVideoGenerator.exe` |
| 실행 시간 (Dry-run) | 30초 이하 | `--dry-run` 실행 시간 |
| 렌더링 시간 | 60초 이하 | 영상 1편 생성 시간 |
| 메모리 사용 | 2GB 이하 | Task Manager 확인 |

---

## 다음 작업 우선순위

### P0 (즉시, 4시간)

1. **CLI 인터페이스 추가** (2h)
   - `--version`, `--check-env`, `--list-assets`, `--dry-run`
   - `generate_video_55sec_pipeline.py`에 argparse 구현

2. **Input Sanitizer 구현** (2h)
   - `src/utils/input_validator.py` 생성
   - Prompt Injection 차단 (13개 패턴)
   - Path Traversal 차단 (10개 패턴)

### P1 (이번 주, 8시간)

3. **통합 테스트** (4h)
   - `tests/exe/test_exe_rendering.py`
   - 전체 파이프라인 검증

4. **회귀 테스트** (2h)
   - `tests/exe/test_backward_compat.py`
   - 이전 스크립트 호환성

5. **문서화** (2h)
   - README.txt 업데이트
   - .env.example 작성

---

## 예상 ROI

| 작업 | 투자 | 방지 손실 | ROI |
|------|------|-----------|-----|
| Layer 1 스모크 테스트 | 2h | 20h 디버깅 | 10배 |
| Layer 2 보안 테스트 | 3h | 50h 긴급 패치 | 16배 |
| CLI 인터페이스 | 2h | 10h 수동 검증 | 5배 |
| Input Sanitizer | 2h | 30h 보안 수정 | 15배 |
| **합계** | **9h** | **110h** | **12배** |

---

## 체크포인트

### 빌드 직후

```bash
✓ EXE 파일 존재 (dist/CruiseVideoGenerator.exe)
✓ 파일 크기 50MB 이상
✓ --version 실행 성공
```

### 테스트 실행 후

```bash
✓ Layer 1 스모크 테스트 80% PASS (8/10)
✓ Layer 2 보안 테스트 90% PASS (18/20)
✓ Layer 2 JSON 파싱 80% PASS
```

### 수동 검증 후

```bash
✓ --dry-run 정상 실행
✓ --help 도움말 출력
✓ 영상 1편 생성 성공 (선택)
```

### 배포 준비 완료

```bash
✓ .env.example 작성
✓ README.txt 작성
✓ 배포 패키지 압축 (CruiseVideoGenerator_v1.0.zip)
✓ 릴리스 노트 작성
```

---

## 관련 문서

- **전체 전략**: [EXE_TEST_STRATEGY.md](EXE_TEST_STRATEGY.md)
- **테스트 가이드**: [tests/exe/README.md](../tests/exe/README.md)
- **프로젝트 메모리**: [memory/MEMORY.md](../memory/MEMORY.md)

---

**버전**: 1.0
**최종 수정**: 2026-03-09
**담당**: C2 Test Guardian Agent

---

## 마지막 확인

배포 전 3가지만 확인:

1. EXE 실행됨? `dist/CruiseVideoGenerator.exe --version`
2. 스모크 통과? `pytest tests/exe/test_exe_smoke.py -v`
3. 보안 통과? `pytest tests/exe/test_security_injection.py -v`

**3개 모두 YES** → 배포 GO ✅
