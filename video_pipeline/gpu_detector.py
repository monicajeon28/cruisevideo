"""
NVENC GPU 자동 감지 모듈
- NVENC 사용 가능 여부 자동 판단
- PipelineConfig에서 use_nvenc 기본값으로 사용

구현 목적:
- 팀원별 GPU 환경 자동 대응 (NVENC 초 vs CPU 분)
- NVIDIA GPU 지원 여부 확인
- 사용자 설정 부담 제로
"""

import logging
import subprocess
import shutil

logger = logging.getLogger(__name__)


def detect_nvenc_support() -> bool:
    """
    NVENC 인코딩 지원 여부 자동 감지

    Returns:
        True: 사용 가능 (NVIDIA GPU + NVENC 지원)
        False: 사용 불가 (CPU 모드로 fallback)

    체크 순서:
    1. FFmpeg 설치 여부
    2. h264_nvenc 인코더 지원 여부
    """
    try:
        # 단계 1: FFmpeg 설치 여부 확인
        ffmpeg_path = shutil.which("ffmpeg")
        if not ffmpeg_path:
            logger.info("FFmpeg 미설치 - CPU 안정 모드 사용 (3-5분)")
            return False

        # 단계 2: h264_nvenc 인코더 지원 확인
        result = subprocess.run(
            [ffmpeg_path, '-encoders'],
            capture_output=True,
            timeout=10,
            text=True,
            encoding='utf-8',
            errors='replace',
        )

        if 'h264_nvenc' in result.stdout:
            nvidia_name = get_gpu_name()
            if nvidia_name:
                logger.info(f"NVENC GPU 감지: {nvidia_name} - 고속 모드 활성화 (30초)")
            else:
                logger.info("NVENC 인코더 감지 - 고속 모드 활성화 (30초)")
            return True
        else:
            logger.info("NVENC 미감지 - CPU 안정 모드 활성화 (3-5분)")
            return False

    except FileNotFoundError:
        logger.info("FFmpeg 경로 없음 - CPU 안정 모드 사용 (3-5분)")
        return False
    except subprocess.TimeoutExpired:
        logger.info("FFmpeg 응답 시간 초과 - CPU 안정 모드 사용 (3-5분)")
        return False
    except (OSError, RuntimeError) as e:
        logger.info(f"GPU 감지 실패: {e} - CPU 안정 모드 사용 (3-5분)")
        return False


def get_gpu_name() -> str:
    """
    GPU 정보 조회 (디버깅용)

    Returns:
        GPU 이름 (예: "NVIDIA GeForce RTX 4070") 또는 빈 문자열

    지원 방법:
    - nvidia-smi 명령어
    """
    try:
        result = subprocess.run(
            ['nvidia-smi', '--query-gpu=name', '--format=csv,noheader,nounits'],
            capture_output=True,
            timeout=5,
            text=True,
            encoding='utf-8',
            errors='replace',
        )

        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')
            names = [line.strip() for line in lines if line.strip()]
            if names:
                return names[0]
    except FileNotFoundError:
        pass
    except subprocess.TimeoutExpired:
        logger.debug("GPU 정보 조회 시간 초과")
    except (OSError, RuntimeError) as e:
        logger.debug(f"GPU 정보 조회 실패: {e}")

    return ""


def get_render_time_estimate(use_nvenc: bool) -> str:
    """
    렌더링 예상 시간 반환 (사용자 안내용)

    Args:
        use_nvenc: NVENC 사용 여부

    Returns:
        예상 시간 문자열 (예: "약 30초")
    """
    if use_nvenc:
        return "약 30초 (NVENC 고속 모드)"
    else:
        return "약 3-5분 (CPU 안정 모드)"


if __name__ == "__main__":
    import sys
    import io

    # Windows 콘솔 UTF-8 인코딩 설정
    if sys.platform == 'win32':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

    logging.basicConfig(
        level=logging.INFO,
        format='%(levelname)s - %(message)s'
    )

    print("=" * 60)
    print("NVENC 자동 감지 진단 도구")
    print("=" * 60)
    print()

    # NVENC 지원 여부
    nvenc = detect_nvenc_support()

    # GPU 정보
    gpu = get_gpu_name()

    # 렌더링 예상 시간
    estimate = get_render_time_estimate(nvenc)

    print()
    print("진단 결과:")
    print("-" * 40)
    print(f"NVENC 지원:      {'사용 가능' if nvenc else '사용 불가'}")
    print(f"GPU 정보:        {gpu or 'N/A (감지 실패)'}")
    print(f"렌더링 예상 시간: {estimate}")
    print("-" * 40)
    print()

    if nvenc:
        print("고속 NVENC 모드로 영상 생성 (30초)")
    else:
        print("안정 CPU 모드로 영상 생성 (3-5분)")
        print("  - NVENC를 사용하려면 NVIDIA GPU + 드라이버 필요")

    print()
    print("=" * 60)
