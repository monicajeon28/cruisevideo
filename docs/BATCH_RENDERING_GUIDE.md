# 배치 병렬 렌더링 가이드 (Task #15: FIX-BATCH)

## 개요

NVENC GPU 3세션 병렬 렌더링 시스템으로, 영상 생산 시간을 3배 단축합니다.

## 성능 비교

| 모드 | 렌더링 시간 | 100편 생산 | 속도 |
|------|-------------|-----------|------|
| **직렬** (--batch 1) | 2시간/편 | 200시간 | 1배 |
| **병렬** (--batch 3) | 2시간/3편 | 67시간 | **3배** |

## 사용 방법

### 1. 기본 사용 (자동 모드 + 병렬 3세션)

```bash
python generate_batch.py --mode auto --count 36 --batch 3
```

- 36편을 3세션 병렬 렌더링
- 예상 시간: 24시간 (직렬 72시간 → 3배 빠름)

### 2. 직렬 렌더링 (기존 방식)

```bash
python generate_batch.py --mode auto --count 10 --batch 1
```

- 10편을 1세션 직렬 렌더링
- 예상 시간: 20시간

### 3. 수동 모드 + 병렬 렌더링

```bash
python generate_batch.py \
    --mode manual \
    --batch 3 \
    --port 나가사키 \
    --ship "MSC 벨리시마" \
    --category 기항지정보 \
    --count 3
```

### 4. DRY-RUN (테스트용)

```bash
python generate_batch.py --mode auto --count 5 --batch 3 --dry-run
```

- 스크립트 생성까지만 실행 (렌더링 스킵)
- GPU 메모리 체크만 수행

## 주요 기능

### 1. 병렬 세션 관리
- `multiprocessing.Pool(3)` - 3개 프로세스 병렬
- NVENC 세션 분리 (GPU 메모리 7.5GB 이내)

### 2. 에러 복구
- 1개 작업 실패 시 나머지 계속 진행
- 타임아웃 2시간 (렌더링 시간 초과 방지)

### 3. 실시간 모니터링
- GPU 메모리 사용량 체크 (nvidia-smi)
- 렌더링 진행 상황 로그 출력

## 시스템 요구 사항

### GPU
- NVIDIA RTX 3060 이상 (12GB VRAM)
- NVENC 지원 GPU

### 메모리
- GPU 메모리: 7.5GB 사용 (3세션 × 2.5GB)
- CPU 메모리: 16GB 권장

### 소프트웨어
- FFmpeg (NVENC 컴파일)
- Python 3.11+
- nvidia-smi (GPU 모니터링)

## 파일 구조

```
D:\mabiz\
├── generate_batch.py           # 배치 렌더링 CLI (신규)
├── cli/
│   └── batch_renderer.py       # 배치 렌더러 클래스 (신규)
├── generate.py                 # 기존 단일 렌더링 CLI
└── generate_video_55sec_pipeline.py  # 렌더링 파이프라인
```

## 출력 예시

```
==================================================
🚀 배치 병렬 렌더링 시스템 시작
==================================================
모드: auto
생성 편수: 36
병렬 세션: 3개
출력 디렉토리: outputs/batch
==================================================

📋 배치 렌더링 시작 - 36편 / 3세션 병렬

🎬 시작: Job#1 [cruise_nagasaki_msc_port_info]
🎬 시작: Job#2 [cruise_alaska_royal_bucket_list]
🎬 시작: Job#3 [cruise_busan_msc_convenience]

✅ 완료: Job#1 [cruise_nagasaki_msc_port_info] | 118.2분 | 245.3MB
🎬 시작: Job#4 [cruise_europe_msc_fear_relief]

...

==================================================
📊 배치 렌더링 완료
==================================================
✅ 성공: 36/36편
⏱️ 총 시간: 1440.5분 (24.0시간)
📦 총 용량: 8821.4MB (8.6GB)
⚡ 평균 렌더링 시간: 120.0분/편
==================================================
```

## 문제 해결

### GPU 메모리 부족

**증상**:
```
⚠️ GPU 메모리 부족 - 8.5GB < 7.5GB
```

**해결**:
1. `--batch 2`로 세션 수 감소
2. 다른 GPU 프로그램 종료

### 렌더링 타임아웃

**증상**:
```
⏰ 타임아웃: Job#5 [cruise_alaska_royal_bucket_list]
```

**해결**:
1. 타임아웃 시간 증가 (batch_renderer.py line 241)
2. 스크립트 길이 확인 (55초 초과 여부)

### 프로세스 충돌

**증상**:
```
💥 예외: Job#3 - [Errno 11] Resource temporarily unavailable
```

**해결**:
1. `--batch 1`로 직렬 모드 실행
2. 시스템 재시작

## 성능 최적화 팁

### 1. 최적 배치 크기
- RTX 3060 (12GB): `--batch 3` (권장)
- RTX 3070 (8GB): `--batch 2`
- RTX 3080 (10GB): `--batch 3`

### 2. 렌더링 순서
- Hook 전용 영상 먼저 (빠른 렌더링)
- 복잡한 효과 영상 나중에

### 3. 디스크 I/O
- SSD 사용 권장 (HDD 대비 2배 빠름)
- 출력 디렉토리를 별도 SSD에 분리

## 통계 추적

배치 렌더링 후 자동 생성되는 통계:

```json
{
  "total_jobs": 36,
  "success": 36,
  "failed": 0,
  "total_duration_minutes": 1440.5,
  "avg_duration_minutes": 120.0,
  "total_size_mb": 8821.4,
  "speedup": 3.0
}
```

## 다음 단계

1. **실시간 모니터링 대시보드** (선택)
   - 웹 UI로 렌더링 진행 상황 확인
   - GPU 메모리/온도 그래프

2. **자동 스케줄링** (선택)
   - 야간 자동 렌더링 (cron/Task Scheduler)
   - 100편 자동 생산

3. **클라우드 렌더링** (확장)
   - AWS EC2 G4dn 인스턴스
   - 10세션 병렬 (10배 속도)
