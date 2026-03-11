#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
배치 병렬 렌더링 시스템 (Task #15: FIX-BATCH)

**목표**:
- NVENC GPU 3세션 병렬 렌더링
- 100편 생산 시간: 200시간 → 67시간 (3배 속도)

**주요 기능**:
1. multiprocessing.Pool(3) - 3개 프로세스 병렬
2. NVENC 세션 분리 (GPU 메모리 7.5GB 이내)
3. 에러 핸들링 (1개 실패 시 나머지 계속)
4. 진행 상황 실시간 모니터링

**사용 예시**:
    from cli.batch_renderer import BatchRenderer

    renderer = BatchRenderer(max_workers=3)
    results = renderer.render_batch(
        script_files=["script1.json", "script2.json", "script3.json"],
        output_dir="outputs/batch"
    )
"""

import multiprocessing
import subprocess
import sys
import time
import logging
import os
import shutil
from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)


# ============================================================================
# 1. 렌더링 작업 데이터클래스
# ============================================================================

@dataclass
class RenderJob:
    """단일 렌더링 작업"""
    script_path: Path
    output_path: Path
    job_id: int

    def __str__(self) -> str:
        return f"Job#{self.job_id} [{self.script_path.stem}]"


@dataclass
class RenderResult:
    """렌더링 결과"""
    job: RenderJob
    success: bool
    duration: float  # 초
    error_message: str = ""
    output_size_mb: float = 0.0  # MB

    def __str__(self) -> str:
        status = "[SUCCESS]" if self.success else "[FAILED]"
        return (
            f"{status} {self.job} | "
            f"Duration: {self.duration:.1f}s | "
            f"Size: {self.output_size_mb:.1f}MB"
        )


# ============================================================================
# 2. 배치 렌더러 클래스
# ============================================================================

class BatchRenderer:
    """NVENC 3세션 병렬 렌더링 시스템"""

    # GPU 메모리 제한 (RTX 3060 12GB 기준)
    GPU_MEMORY_PER_SESSION_GB = 2.5  # 세션당 2.5GB (총 7.5GB)
    MAX_WORKERS = 3  # NVENC 세션 최대 3개

    def __init__(
        self,
        max_workers: int = 3,
        verbose: bool = True,
        enable_gpu_check: bool = True
    ):
        """
        배치 렌더러 초기화

        Args:
            max_workers: 병렬 프로세스 수 (기본 3)
            verbose: 상세 로그 출력 여부
            enable_gpu_check: GPU 메모리 사전 체크 (nvidia-smi 필요)
        """
        self.max_workers = min(max_workers, self.MAX_WORKERS)
        self.verbose = verbose
        self.enable_gpu_check = enable_gpu_check

        logger.info(
            f"[BATCH] 배치 렌더러 초기화 - "
            f"병렬 세션: {self.max_workers}개"
        )

        # GPU 메모리 사전 체크 (선택)
        if self.enable_gpu_check:
            self._check_gpu_memory()

    def _check_gpu_memory(self) -> None:
        """GPU 메모리 사용량 확인 (nvidia-smi)"""
        try:
            result = subprocess.run(
                [
                    "nvidia-smi",
                    "--query-gpu=memory.free",
                    "--format=csv,noheader,nounits"
                ],
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode == 0:
                free_memory_mb = int(result.stdout.strip())
                free_memory_gb = free_memory_mb / 1024

                required_gb = self.GPU_MEMORY_PER_SESSION_GB * self.max_workers

                logger.info(
                    f"[GPU] GPU 메모리: {free_memory_gb:.1f}GB 사용 가능 | "
                    f"필요: {required_gb:.1f}GB ({self.max_workers}세션)"
                )

                if free_memory_gb < required_gb:
                    logger.warning(
                        f"[WARNING] GPU 메모리 부족 - "
                        f"{free_memory_gb:.1f}GB < {required_gb:.1f}GB. "
                        f"렌더링 중 메모리 오류 가능성 있음."
                    )
        except (OSError, subprocess.SubprocessError, ValueError) as e:
            logger.debug(f"nvidia-smi 체크 실패 (무시): {e}")

    def render_batch(
        self,
        script_files: List[Path],
        output_dir: Path,
        dry_run: bool = False
    ) -> List[RenderResult]:
        """
        배치 병렬 렌더링 실행

        Args:
            script_files: 스크립트 파일 경로 리스트
            output_dir: 출력 디렉토리
            dry_run: True이면 렌더링 스킵 (테스트용)

        Returns:
            RenderResult 리스트 (성공/실패 포함)
        """
        start_time = time.time()

        # 출력 디렉토리 생성
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        # 작업 리스트 생성
        jobs = [
            RenderJob(
                script_path=Path(script_file),
                output_path=output_dir / f"{Path(script_file).stem}.mp4",
                job_id=i + 1
            )
            for i, script_file in enumerate(script_files)
        ]

        logger.info(
            f"[START] 배치 렌더링 시작 - "
            f"{len(jobs)}편 / {self.max_workers}세션 병렬"
        )

        # 병렬 렌더링 실행
        if dry_run:
            logger.info("[DRY-RUN] DRY-RUN 모드 - 렌더링 스킵")
            results = [
                RenderResult(
                    job=job,
                    success=True,
                    duration=0.0,
                    error_message="DRY-RUN"
                )
                for job in jobs
            ]
        else:
            with multiprocessing.Pool(self.max_workers) as pool:
                results = pool.map(self._render_single, jobs)

        # 통계 계산
        total_duration = time.time() - start_time
        success_count = sum(1 for r in results if r.success)
        total_size_mb = sum(r.output_size_mb for r in results if r.success)

        logger.info("")
        logger.info("=" * 60)
        logger.info("[COMPLETE] 배치 렌더링 완료")
        logger.info("=" * 60)
        logger.info(f"[SUCCESS] 성공: {success_count}/{len(jobs)}편")
        logger.info(f"[TIME] 총 시간: {total_duration / 60:.1f}분")
        logger.info(f"[SIZE] 총 용량: {total_size_mb:.1f}MB")

        if success_count > 0:
            avg_time_per_video = total_duration / success_count
            logger.info(f"[AVG] 평균 렌더링 시간: {avg_time_per_video / 60:.1f}분/편")

        # 실패한 작업 출력
        failed = [r for r in results if not r.success]
        if failed:
            logger.error("")
            logger.error("[FAILED] 실패한 작업:")
            for r in failed:
                logger.error(f"  - {r.job}: {r.error_message}")

        logger.info("=" * 60)

        return results

    def _render_single(self, job: RenderJob) -> RenderResult:
        """
        단일 영상 렌더링 (subprocess로 generate_video_55sec_pipeline.py 호출)

        Args:
            job: RenderJob 인스턴스

        Returns:
            RenderResult 인스턴스
        """
        # [CRITICAL-2 2026-03-08] 프로세스별 임시 디렉토리 분리
        temp_dir = Path(f"temp/render_job_{job.job_id}_{os.getpid()}")
        temp_dir.mkdir(parents=True, exist_ok=True)

        start_time = time.time()

        logger.info(f"[RENDER] 시작: {job} | Temp: {temp_dir}")

        try:
            # 환경 변수로 임시 디렉토리 전달
            env = os.environ.copy()
            env['RENDER_TEMP_DIR'] = str(temp_dir)

            # generate_video_55sec_pipeline.py 호출
            # (실제 파이프라인은 스크립트 파일을 직접 읽어서 렌더링)
            cmd = [
                sys.executable,
                "generate_video_55sec_pipeline.py",
                str(job.script_path),
                "--output",
                str(job.output_path)
            ]

            if self.verbose:
                logger.debug(f"  CMD: {' '.join(cmd)}")

            # subprocess 실행 (타임아웃 2시간)
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=7200,  # 2시간
                encoding='utf-8',
                errors='replace',  # 인코딩 에러 무시
                env=env  # 환경 변수 전달
            )

            duration = time.time() - start_time

            # 성공 여부 확인
            if result.returncode == 0 and job.output_path.exists():
                output_size_mb = job.output_path.stat().st_size / (1024 * 1024)

                logger.info(
                    f"[OK] 완료: {job} | "
                    f"{duration / 60:.1f}분 | "
                    f"{output_size_mb:.1f}MB"
                )

                return RenderResult(
                    job=job,
                    success=True,
                    duration=duration,
                    output_size_mb=output_size_mb
                )
            else:
                # 실패
                error_msg = result.stderr[-500:] if result.stderr else "Unknown error"

                logger.error(f"[ERROR] 실패: {job} | {error_msg}")

                return RenderResult(
                    job=job,
                    success=False,
                    duration=duration,
                    error_message=error_msg
                )

        except subprocess.TimeoutExpired:
            duration = time.time() - start_time
            error_msg = "렌더링 타임아웃 (2시간 초과)"

            logger.error(f"[TIMEOUT] 타임아웃: {job}")

            return RenderResult(
                job=job,
                success=False,
                duration=duration,
                error_message=error_msg
            )

        except (OSError, ValueError, RuntimeError) as e:
            duration = time.time() - start_time
            error_msg = str(e)

            logger.error(f"[EXCEPTION] 예외: {job} - {error_msg}")

            return RenderResult(
                job=job,
                success=False,
                duration=duration,
                error_message=error_msg
            )

        finally:
            # [CRITICAL-2] 임시 디렉토리 정리
            try:
                if temp_dir.exists():
                    shutil.rmtree(temp_dir, ignore_errors=True)
                    logger.debug(f"  Cleanup: {temp_dir} 삭제 완료")
            except OSError as e:
                logger.debug(f"  Cleanup 실패 (무시): {e}")


# ============================================================================
# 3. CLI 진입점 (테스트용)
# ============================================================================

if __name__ == "__main__":
    import argparse

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s"
    )

    parser = argparse.ArgumentParser(description="배치 병렬 렌더링 시스템")
    parser.add_argument(
        "scripts",
        nargs="+",
        help="스크립트 파일 경로 (공백으로 구분)"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="outputs/batch",
        help="출력 디렉토리 (기본: outputs/batch)"
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=3,
        help="병렬 세션 수 (기본: 3)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="렌더링 스킵 (테스트용)"
    )

    args = parser.parse_args()

    # 렌더링 실행
    renderer = BatchRenderer(max_workers=args.workers)
    results = renderer.render_batch(
        script_files=[Path(s) for s in args.scripts],
        output_dir=Path(args.output),
        dry_run=args.dry_run
    )

    # 종료 코드 (실패 1개라도 있으면 1)
    exit_code = 0 if all(r.success for r in results) else 1
    exit(exit_code)
