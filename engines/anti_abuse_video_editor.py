"""
Anti-Abuse Video Editor
YouTube 어뷰징 방지를 위한 영상 편집
- 원본 영상을 랜덤 구간으로 분할
- 순서 재조합 및 랜덤 효과 적용
- 밝기/속도/반전 등 랜덤화로 핑거프린트 변조
"""

import os
import random
import logging
from pathlib import Path
from typing import List, Tuple, Optional
from moviepy import VideoFileClip, concatenate_videoclips
from moviepy.video import fx as vfx

logger = logging.getLogger(__name__)


class AntiAbuseVideoEditor:
    """어뷰징 방지 영상 편집기"""

    def __init__(self, seed: Optional[int] = None):
        """
        Args:
            seed: 랜덤 시드 (재현성 필요 시 설정)
        """
        if seed is not None:
            random.seed(seed)

    def cut_into_segments(
        self,
        video_path: str,
        segment_durations: List[float]
    ) -> List[VideoFileClip]:
        """
        영상을 지정된 길이로 분할

        Args:
            video_path: 원본 영상 경로
            segment_durations: 각 구간 길이 리스트 (초 단위)
                예: [3.0, 5.0, 3.0] = 0-3초, 3-8초, 8-11초 추출

        Returns:
            분할된 VideoFileClip 리스트
        """
        try:
            clip = VideoFileClip(video_path)
            segments = []
            current_time = 0.0

            for duration in segment_durations:
                end_time = min(current_time + duration, clip.duration)

                if current_time >= clip.duration:
                    logger.warning(f"Video too short: {video_path} ({clip.duration}s)")
                    break

                segment = clip.subclipped(current_time, end_time)
                segments.append(segment)
                current_time = end_time

            logger.info(f"Cut video into {len(segments)} segments: {video_path}")
            return segments

        except (OSError, ValueError, RuntimeError) as e:
            logger.error(f"Failed to cut video: {e}")
            return []

    def apply_random_effects(self, clip: VideoFileClip) -> VideoFileClip:
        """
        랜덤 효과 적용 (어뷰징 방지)

        효과:
        - 밝기 조정: ±5%
        - 속도 조정: 0.95x ~ 1.05x
        - 좌우 반전: 50% 확률

        Args:
            clip: 원본 클립

        Returns:
            효과가 적용된 클립
        """
        try:
            # 1. 밝기 조정 (±5%) — MoviePy 2.x API
            brightness_factor = random.uniform(0.95, 1.05)
            clip = clip.with_effects([vfx.MultiplyColor(brightness_factor)])

            # 2. 속도 조정 (0.95x ~ 1.05x)
            speed_factor = random.uniform(0.95, 1.05)
            clip = clip.with_effects([vfx.MultiplySpeed(speed_factor)])

            # 3. 좌우 반전 (50% 확률)
            mirrored = False
            if random.random() < 0.5:
                clip = clip.with_effects([vfx.MirrorX()])
                mirrored = True

            logger.debug(
                f"Applied random effects: brightness={brightness_factor:.2f}, "
                f"speed={speed_factor:.2f}, mirrored={mirrored}"
            )
            return clip

        except (ValueError, RuntimeError, AttributeError) as e:
            logger.error(f"Failed to apply random effects: {e}")
            return clip

    def cut_and_splice(
        self,
        video_path: str,
        total_duration: float,
        output_path: Optional[str] = None,
        cut_positions: Optional[List[float]] = None,
        shuffle: bool = True,
        apply_effects: bool = True
    ) -> Optional[str]:
        """
        영상을 자르고 재조합 (어뷰징 방지 핵심 함수)

        전략:
        1. 원본 영상을 3~4개 구간으로 분할
        2. 각 구간을 3초 or 5초씩 추출
        3. 랜덤 순서로 재조합
        4. 랜덤 효과 적용 (밝기/속도/반전)

        예시:
        - 원본 15초 영상
        - 분할: [0-3s], [4-7s], [8-13s]
        - 재조합: [8-13s (5초)] + [0-3s (3초)] + [4-7s (3초)] = 11초

        Args:
            video_path: 원본 영상 경로
            total_duration: 목표 길이 (초)
            output_path: 출력 경로 (None이면 자동 생성)
            cut_positions: 컷 위치 리스트 (None이면 자동 생성)
            shuffle: 구간 순서 섞기 여부
            apply_effects: 랜덤 효과 적용 여부

        Returns:
            출력 파일 경로 (실패 시 None)
        """
        try:
            # 출력 경로 생성
            if output_path is None:
                video_stem = Path(video_path).stem
                output_dir = Path(video_path).parent / "AntiAbuse"
                output_dir.mkdir(parents=True, exist_ok=True)
                output_path = str(output_dir / f"{video_stem}_antiabuse.mp4")

            # 원본 영상 로드
            original_clip = VideoFileClip(video_path)
            original_duration = original_clip.duration

            # 컷 위치 자동 생성 (3초, 4초, 8초 위치)
            if cut_positions is None:
                cut_positions = self._generate_cut_positions(original_duration)

            # 구간 길이 계산
            segment_durations = self._calculate_segment_durations(
                cut_positions, total_duration, original_duration
            )

            # 영상 분할
            segments = self.cut_into_segments(video_path, segment_durations)

            if not segments:
                logger.error("No segments created")
                return None

            # 순서 섞기
            if shuffle:
                random.shuffle(segments)
                logger.info(f"Shuffled {len(segments)} segments")

            # 랜덤 효과 적용
            if apply_effects:
                segments = [self.apply_random_effects(seg) for seg in segments]

            # 구간 연결
            final_clip = concatenate_videoclips(segments, method="compose")

            # 목표 길이에 맞게 자르기
            if final_clip.duration > total_duration:
                final_clip = final_clip.subclipped(0, total_duration)

            # 출력 (1080x1920 세로형 유지)
            final_clip.write_videofile(
                output_path,
                codec="libx264",
                audio_codec="aac",
                fps=30,
                preset="medium",
                logger=None  # MoviePy 로그 비활성화
            )

            # 메모리 정리
            final_clip.close()
            original_clip.close()
            for seg in segments:
                seg.close()

            logger.info(f"Anti-abuse video created: {output_path}")
            return output_path

        except (OSError, ValueError, RuntimeError) as e:
            logger.error(f"Failed to cut and splice video: {e}")
            return None

    def _generate_cut_positions(self, duration: float) -> List[float]:
        """
        컷 위치 자동 생성

        전략:
        - 15초 이상: [3.0, 4.0, 8.0] 위치에서 컷
        - 10~15초: [3.0, 6.0] 위치에서 컷
        - 10초 미만: [3.0] 위치에서 컷

        Args:
            duration: 영상 길이 (초)

        Returns:
            컷 위치 리스트
        """
        if duration >= 15.0:
            return [3.0, 4.0, 8.0]
        elif duration >= 10.0:
            return [3.0, 6.0]
        else:
            return [3.0]

    def _calculate_segment_durations(
        self,
        cut_positions: List[float],
        total_duration: float,
        original_duration: float
    ) -> List[float]:
        """
        각 구간의 길이 계산

        전략:
        - 3초 or 5초씩 균등 분배
        - 총합이 total_duration을 초과하지 않도록 조정

        Args:
            cut_positions: 컷 위치 리스트
            total_duration: 목표 길이
            original_duration: 원본 영상 길이

        Returns:
            각 구간 길이 리스트
        """
        num_segments = len(cut_positions) + 1
        base_duration = total_duration / num_segments

        # 3초 또는 5초로 근사
        durations = []
        remaining = total_duration

        for i in range(num_segments):
            if remaining <= 0:
                break

            # 3초 or 5초 중 선택
            if base_duration >= 4.5:
                seg_duration = min(5.0, remaining)
            else:
                seg_duration = min(3.0, remaining)

            durations.append(seg_duration)
            remaining -= seg_duration

        return durations

    def batch_process(
        self,
        video_paths: List[str],
        total_duration: float,
        output_dir: Optional[str] = None
    ) -> List[str]:
        """
        배치 처리 (여러 영상을 한번에)

        Args:
            video_paths: 원본 영상 경로 리스트
            total_duration: 목표 길이
            output_dir: 출력 디렉토리 (None이면 자동)

        Returns:
            처리된 영상 경로 리스트
        """
        if output_dir:
            output_dir_path = Path(output_dir)
            output_dir_path.mkdir(parents=True, exist_ok=True)

        processed_paths = []

        for video_path in video_paths:
            if output_dir:
                filename = Path(video_path).stem + "_antiabuse.mp4"
                output_path = str(output_dir_path / filename)
            else:
                output_path = None

            result_path = self.cut_and_splice(
                video_path,
                total_duration,
                output_path=output_path
            )

            if result_path:
                processed_paths.append(result_path)

        logger.info(f"Batch processed: {len(processed_paths)}/{len(video_paths)} videos")
        return processed_paths


# 사용 예시
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    from path_resolver import get_paths as _gp

    editor = AntiAbuseVideoEditor(seed=42)

    # 1. 단일 영상 처리
    test_video = str(_gp().footage_dir / "test_cruise.mp4")

    if os.path.exists(test_video):
        output = editor.cut_and_splice(
            video_path=test_video,
            total_duration=11.0,  # 11초 영상 생성
            shuffle=True,
            apply_effects=True
        )
        print(f"Output: {output}")

    # 2. 배치 처리
    test_videos = [
        str(_gp().footage_dir / "Pexels" / "cruise_001.mp4"),
        str(_gp().footage_dir / "Pexels" / "cruise_002.mp4"),
    ]

    valid_videos = [v for v in test_videos if os.path.exists(v)]

    if valid_videos:
        outputs = editor.batch_process(
            video_paths=valid_videos,
            total_duration=10.0,
            output_dir=str(_gp().footage_dir / "AntiAbuse")
        )
        print(f"Processed {len(outputs)} videos")
