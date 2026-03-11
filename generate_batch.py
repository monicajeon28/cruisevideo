#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
배치 병렬 렌더링 CLI (Task #15: FIX-BATCH)

**사용 예시**:
    # 자동 모드 36편을 3세션 병렬 렌더링
    python generate_batch.py --mode auto --count 36 --batch 3

    # 수동 모드 3편 병렬 렌더링
    python generate_batch.py --mode manual --batch 3 \
        --port 나가사키 --ship "MSC 벨리시마" --category 기항지정보

**성능**:
    - 직렬 (--batch 1): 36편 = 72시간
    - 병렬 (--batch 3): 36편 = 24시간 (3배 빠름)
"""

import argparse
import logging
import sys
from pathlib import Path

# 프로젝트 루트를 sys.path에 추가
project_root = Path(__file__).parent.resolve()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from cli.batch_renderer import BatchRenderer


# ============================================================================
# 1. 인수 파서
# ============================================================================

def create_parser() -> argparse.ArgumentParser:
    """인수 파서 구성"""
    parser = argparse.ArgumentParser(
        prog="generate_batch.py",
        description="크루즈 영상 배치 병렬 렌더링 CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    # 모드 (필수)
    parser.add_argument(
        "--mode",
        required=True,
        choices=["auto", "manual"],
        help="실행 모드 (auto: 자동 선택, manual: 수동 지정)",
    )

    # 생성 편수
    parser.add_argument(
        "--count",
        type=int,
        default=1,
        dest="video_count",
        help="생성할 영상 편수 (기본 1)",
    )

    # 병렬 세션 수 (핵심 옵션)
    parser.add_argument(
        "--batch",
        type=int,
        default=3,
        choices=[1, 2, 3],
        dest="batch_workers",
        help="병렬 렌더링 세션 수 (1-3, 기본 3=최대 병렬)",
    )

    # 수동 모드 파라미터
    parser.add_argument(
        "--port",
        type=str,
        default=None,
        help="기항지 코드 또는 한글명 (예: NKS, 나가사키)",
    )
    parser.add_argument(
        "--ship",
        type=str,
        default=None,
        help="선박 이름 또는 ID (예: 'MSC 벨리시마', msc_bellissima)",
    )
    parser.add_argument(
        "--category",
        type=str,
        default=None,
        help="카테고리 ID 또는 한글명 (예: PORT_INFO, 기항지정보)",
    )
    parser.add_argument(
        "--tier",
        choices=["T1_BUDGET", "T2_STANDARD", "T3_PREMIUM"],
        type=str,
        default=None,
        help="가격대 (미지정 시 카테고리 tier 기반 자동 선택)",
    )

    # 공통 파라미터
    parser.add_argument(
        "--output",
        type=str,
        default=str(Path("outputs/batch")),
        dest="output_dir",
        help="출력 디렉토리 (기본: outputs/batch)",
    )
    parser.add_argument(
        "--config",
        type=str,
        default=Path().resolve() / "config" / "cruise_config.yaml",
        dest="config_path",
        help="설정 YAML 파일 경로",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="렌더링 스킵 - 스크립트 생성/검증만 수행",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="상세 로그 출력 (DEBUG 레벨)",
    )

    return parser


# ============================================================================
# 2. 로깅 설정
# ============================================================================

def setup_logging(verbose: bool = False) -> None:
    """로깅 레벨 및 형식 설정"""
    level = logging.DEBUG if verbose else logging.INFO
    log_format = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    logging.basicConfig(level=level, format=log_format, datefmt="%H:%M:%S")

    # 외부 라이브러리 로그 억제 (verbose 아닐 때)
    if not verbose:
        for lib_name in ("urllib3", "requests", "PIL", "openai"):
            logging.getLogger(lib_name).setLevel(logging.WARNING)


# ============================================================================
# 3. 자동 모드
# ============================================================================

def run_auto_mode(args, config, gen_log) -> list:
    """
    자동 모드: 가중치 기반 조합 선택 → S등급 루프 → 배치 렌더링

    Args:
        args: argparse.Namespace
        config: CruiseConfig 인스턴스
        gen_log: GenerationLog 인스턴스

    Returns:
        성공한 스크립트 파일 경로 목록
    """
    from cli.auto_mode import AutoModeOrchestrator

    logger = logging.getLogger(__name__)

    orchestrator = AutoModeOrchestrator(
        cruise_config=config,
        generation_log=gen_log,
        output_dir=args.output_dir,
    )

    # 스크립트 생성 (S등급 루프)
    script_files = []

    logger.info(f"🤖 자동 모드: {args.video_count}편 생성 시작")

    for i in range(args.video_count):
        logger.info(f"📝 {i+1}/{args.video_count}편 스크립트 생성 중...")

        result = orchestrator.generate_single(
            dry_run=True,  # 스크립트만 생성 (렌더링은 배치로)
            enable_upload_package=False  # 업로드 패키지는 나중에
        )

        if result and result.get("script_path"):
            script_files.append(result["script_path"])
            logger.info(
                f"✅ {i+1}편 스크립트 완료: "
                f"{result.get('s_grade_score', 0):.1f}점"
            )
        else:
            logger.warning(f"⚠️ {i+1}편 스크립트 생성 실패 (S등급 미달)")

    logger.info(f"📋 스크립트 생성 완료: {len(script_files)}/{args.video_count}편")

    return script_files


# ============================================================================
# 4. 수동 모드
# ============================================================================

def run_manual_mode(args, config, gen_log) -> list:
    """
    수동 모드: 사용자가 지정한 기항지/선박/카테고리로 스크립트 생성

    Args:
        args: argparse.Namespace
        config: CruiseConfig 인스턴스
        gen_log: GenerationLog 인스턴스

    Returns:
        성공한 스크립트 파일 경로 목록
    """
    logger = logging.getLogger(__name__)

    # 필수 파라미터 검증
    if not args.port:
        logger.error("오류: 수동 모드에서 --port 는 필수입니다.")
        sys.exit(1)
    if not args.ship:
        logger.error("오류: 수동 모드에서 --ship 은 필수입니다.")
        sys.exit(1)
    if not args.category:
        logger.error("오류: 수동 모드에서 --category 는 필수입니다.")
        sys.exit(1)

    # TODO: 수동 모드 구현 (generate.py의 run_manual_mode 참조)
    logger.error("수동 모드는 현재 구현 중입니다.")
    return []


# ============================================================================
# 5. 메인 진입점
# ============================================================================

def main() -> int:
    """메인 진입점"""

    parser = create_parser()
    args = parser.parse_args()

    setup_logging(args.verbose)
    logger = logging.getLogger(__name__)

    logger.info("=" * 60)
    logger.info("🚀 배치 병렬 렌더링 시스템 시작")
    logger.info("=" * 60)
    logger.info(f"모드: {args.mode}")
    logger.info(f"생성 편수: {args.video_count}")
    logger.info(f"병렬 세션: {args.batch_workers}개")
    logger.info(f"출력 디렉토리: {args.output_dir}")
    logger.info("=" * 60)

    # 설정 로드
    logger.info(f"설정 로드 중: {args.config_path}")
    try:
        from cli.config_loader import CruiseConfig

        config = CruiseConfig.from_yaml(Path(args.config_path).resolve())
    except FileNotFoundError:
        logger.error(f"오류: 설정 파일을 찾을 수 없습니다: {args.config_path}")
        return 1
    except Exception as e:
        logger.error(f"오류: 설정 로드 실패: {e}")
        return 1

    # 생성 로그 초기화
    log_path = args.output_dir
    Path(log_path).mkdir(parents=True, exist_ok=True)

    try:
        from cli.generation_log import GenerationLog

        gen_log = GenerationLog()
        gen_log.load()
    except Exception as e:
        logger.error(f"오류: 생성 로그 초기화 실패: {e}")
        return 1

    logger.info(
        f"로그 로드 완료 (기록 {gen_log.get_recent_count()}개, "
        f"경로: {log_path})"
    )

    # 출력 디렉토리 생성
    Path(args.output_dir).mkdir(parents=True, exist_ok=True)

    # 모드별 스크립트 생성
    if args.mode == "auto":
        script_files = run_auto_mode(args, config, gen_log)
    else:
        script_files = run_manual_mode(args, config, gen_log)

    if not script_files:
        logger.error("❌ 생성된 스크립트가 없습니다.")
        return 1

    # 배치 병렬 렌더링 실행
    logger.info("")
    logger.info("=" * 60)
    logger.info("🎬 배치 병렬 렌더링 시작")
    logger.info("=" * 60)

    renderer = BatchRenderer(
        max_workers=args.batch_workers,
        verbose=args.verbose
    )

    results = renderer.render_batch(
        script_files=script_files,
        output_dir=Path(args.output_dir),
        dry_run=args.dry_run
    )

    # 결과 요약
    success_count = sum(1 for r in results if r.success)

    logger.info("")
    logger.info("=" * 60)
    logger.info(f"✅ 배치 렌더링 완료: {success_count}/{len(results)}편 성공")
    logger.info("=" * 60)

    return 0 if success_count == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())
