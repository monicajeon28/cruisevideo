"""
VisualEffects - 시각 효과 처리 모듈 (S2-3-2)

God Object 분리: generate_video_55sec_pipeline.py에서 추출.
Ken Burns, Crossfade, Scale-to-fit, Image Loading, Freeze Frame 확장.

Usage:
    from pipeline_effects import VisualEffects

    effects = VisualEffects(config=config, resources=resource_tracker)
    clip = effects.load_image_safe("photo.jpg")
    clip = effects.scale_to_fit(clip)
    clip = effects.apply_ken_burns(clip, "zoom_in")
"""

import logging
from typing import List, Optional

import numpy as np
from PIL import Image, ImageOps
from moviepy import (
    ImageClip, ColorClip, CompositeVideoClip,
    concatenate_videoclips,
)

logger = logging.getLogger(__name__)

# WO v12.0 Phase 6: 세그먼트 감정 기반 색보정 오버레이 (5060 시청자 - 매우 은은한 톤)
EMOTION_COLOR_MAP = {
    "안심": (255, 200, 150, 15),   # 따뜻한 오렌지
    "공감": (255, 220, 180, 12),   # 따뜻한 옐로우
    "동경": (150, 200, 255, 15),   # 시원한 블루
    "확신": (255, 255, 200, 10),   # 밝은 따뜻함
    "neutral": (0, 0, 0, 0),       # 오버레이 없음
}


class VisualEffects:
    """시각 효과 처리기 (config + resources 의존성 주입)"""

    KEN_BURNS_CYCLE = ["zoom_in", "pan_right", "zoom_out", "pan_left", "pan_up", "pan_down"]

    # [S2-4-3] Named constants
    FREEZE_SAFE_OFFSET = 0.01  # freeze frame 추출 시 끝에서 오프셋
    MAX_SCALE_FACTOR = 3.0     # scale_to_fit 최대 확대 배율
    MAX_IMAGE_SCALE = 1.5      # load_image_safe 최대 확대 배율

    def __init__(self, config, resources):
        """
        Args:
            config: PipelineConfig (또는 호환 객체)
            resources: ResourceTracker (track 메서드 보유)
        """
        self.config = config
        self._resources = resources

    def extend_with_freeze(self, clip, target_duration: float):
        """클립을 freeze frame으로 target_duration까지 연장"""
        if clip.duration is None or clip.duration <= 0:
            logger.warning("  freeze 연장 불가: duration 없음, 기본값 적용")
            clip = clip.with_duration(target_duration)
            self._resources.track(clip)
            return clip

        if clip.duration >= target_duration:
            return clip

        freeze_duration = target_duration - clip.duration
        safe_time = max(0, clip.duration - self.FREEZE_SAFE_OFFSET)

        last_frame_raw = clip.to_ImageClip(safe_time)
        self._resources.track(last_frame_raw)

        if hasattr(clip, 'size') and clip.size and all(s and s > 0 for s in clip.size):
            last_frame_resized = last_frame_raw.resized(clip.size)
            self._resources.track(last_frame_resized)
            last_frame = last_frame_resized.with_duration(freeze_duration)
        else:
            last_frame_resized = last_frame_raw.resized((self.config.width, self.config.height))
            self._resources.track(last_frame_resized)
            last_frame = last_frame_resized.with_duration(freeze_duration)
        self._resources.track(last_frame)

        extended = concatenate_videoclips([clip, last_frame])
        self._resources.track(extended)
        return extended

    def apply_ken_burns(
        self,
        clip,
        effect_type: str = "zoom_in",
        zoom_ratio: Optional[float] = None,
    ):
        """Ken Burns 효과 적용 (팬/줌으로 정지 이미지에 생동감 부여)"""
        if zoom_ratio is None:
            zoom_ratio = self.config.ken_burns_zoom_ratio

        if clip.duration is None or clip.duration <= 0:
            logger.warning("  Ken Burns 적용 불가: duration 없음")
            return clip

        try:
            original_w, original_h = clip.size
            if not original_w or not original_h:
                logger.warning("  Ken Burns 적용 불가: 클립 크기 없음")
                return clip
        except (AttributeError, TypeError):
            logger.warning("  Ken Burns 적용 불가: 클립 크기 확인 실패")
            return clip

        duration = clip.duration

        def ken_burns_filter(get_frame, t):
            frame = get_frame(t)
            linear_progress = t / duration if duration > 0 else 0
            progress = linear_progress * linear_progress * (3 - 2 * linear_progress)
            max_zoom = zoom_ratio * duration

            if effect_type == "zoom_in":
                scale = 1.0 + (max_zoom * progress)
                x_offset, y_offset = 0.5, 0.5
            elif effect_type == "zoom_out":
                max_scale = 1.0 + max_zoom
                scale = max_scale - (max_zoom * progress)
                x_offset, y_offset = 0.5, 0.5
            elif effect_type == "pan_left":
                scale = 1.0 + (max_zoom * 0.5)
                x_offset = 0.7 - (0.4 * progress)
                y_offset = 0.5
            elif effect_type == "pan_right":
                scale = 1.0 + (max_zoom * 0.5)
                x_offset = 0.3 + (0.4 * progress)
                y_offset = 0.5
            elif effect_type == "pan_up":
                scale = 1.0 + (max_zoom * 0.5)
                x_offset = 0.5
                y_offset = 0.7 - (0.4 * progress)
            elif effect_type == "pan_down":
                scale = 1.0 + (max_zoom * 0.5)
                x_offset = 0.5
                y_offset = 0.3 + (0.4 * progress)
            else:
                scale = 1.0
                x_offset, y_offset = 0.5, 0.5

            img = None
            img_resized = None
            img_cropped = None
            try:
                img = Image.fromarray(frame)
                new_w = int(original_w * scale)
                new_h = int(original_h * scale)
                new_w = new_w + (new_w % 2)
                new_h = new_h + (new_h % 2)
                new_w = max(new_w, original_w)
                new_h = max(new_h, original_h)

                img_resized = img.resize((new_w, new_h), Image.LANCZOS)
                crop_x = int((new_w - original_w) * x_offset)
                crop_y = int((new_h - original_h) * y_offset)
                crop_x = max(0, min(crop_x, new_w - original_w))
                crop_y = max(0, min(crop_y, new_h - original_h))
                img_cropped = img_resized.crop((
                    crop_x, crop_y,
                    crop_x + original_w,
                    crop_y + original_h
                ))
                return np.array(img_cropped)
            finally:
                if img_cropped:
                    img_cropped.close()
                if img_resized:
                    img_resized.close()
                if img:
                    img.close()

        try:
            result_clip = clip.transform(ken_burns_filter)
            self._resources.track(result_clip)
            logger.debug(f"  Ken Burns 적용: {effect_type}, zoom={zoom_ratio}")
            return result_clip
        except (ValueError, RuntimeError, AttributeError) as e:
            logger.warning(f"  Ken Burns 적용 실패: {e}, 원본 반환")
            return clip

    def get_emotion_ken_burns(self, segment_type: str = "body") -> dict:
        """감정곡선 기반 Ken Burns 파라미터 반환 (WO v11.0 D-1)

        Args:
            segment_type: 12-Segment 타입 (hook, agitation, desire_peak 등)

        Returns:
            {"zoom": float, "direction": str}
        """
        try:
            from engines.sgrade_constants import EMOTION_ZOOM_MAP
            params = EMOTION_ZOOM_MAP.get(segment_type)
            if params:
                return params
        except ImportError:
            pass
        # Fallback: 기본 순환 매핑
        cycle_idx = hash(segment_type) % len(self.KEN_BURNS_CYCLE)
        return {
            "zoom": self.config.ken_burns_zoom_ratio,
            "direction": self.KEN_BURNS_CYCLE[cycle_idx]
        }

    # WO v11.0 D-2: 감정곡선 기반 트랜지션 선택
    TRANSITION_MAP = {
        "emotion_drop": "fadeblack",     # 감정 하강 → 암전
        "emotion_rise": "circleopen",    # 감정 상승 → 원형 확장
        "block_change": "wipeleft",      # Block 전환 → 와이프
        "default": "fade",               # 기본 → 페이드
    }

    def select_transition(
        self,
        prev_emotion: float,
        next_emotion: float,
        prev_block: str = "",
        next_block: str = "",
    ) -> str:
        """감정곡선 기반 트랜지션 자동 선택 (WO v11.0 D-2)

        Args:
            prev_emotion: 이전 세그먼트 감정 점수
            next_emotion: 다음 세그먼트 감정 점수
            prev_block: 이전 Block (block1~4)
            next_block: 다음 Block (block1~4)

        Returns:
            FFmpeg xfade 트랜지션 이름
        """
        # Block 전환 시: wipeleft (챕터 전환)
        if prev_block and next_block and prev_block != next_block:
            return self.TRANSITION_MAP["block_change"]

        # 감정 하강 시: fadeblack (대비 효과)
        emotion_delta = next_emotion - prev_emotion
        if emotion_delta < -0.15:
            return self.TRANSITION_MAP["emotion_drop"]

        # 감정 상승 시: circleopen (집중 효과)
        if emotion_delta > 0.15:
            return self.TRANSITION_MAP["emotion_rise"]

        # 기본: fade
        return self.TRANSITION_MAP["default"]

    def apply_crossfade(self, clips: List, overlap: Optional[float] = None):
        """클립 리스트에 크로스페이드 전환 적용"""
        if overlap is None:
            overlap = self.config.crossfade_duration

        if not clips:
            logger.warning("  크로스페이드 적용 불가: 클립 없음")
            return None

        if len(clips) == 1:
            return clips[0]

        try:
            from moviepy.video.fx import CrossFadeIn, CrossFadeOut
        except ImportError:
            logger.warning("  CrossFade 효과 import 실패, FadeIn/FadeOut 대체 사용")
            from moviepy.video.fx import FadeIn, FadeOut
            CrossFadeIn, CrossFadeOut = FadeIn, FadeOut

        result_clips = []
        current_time = 0.0

        for i, clip in enumerate(clips):
            clip_duration = clip.duration
            if clip_duration is None or clip_duration <= 0:
                logger.warning(f"  크로스페이드: clip[{i}] duration 없음, 스킵")
                continue

            try:
                if i == 0:
                    effect_clip = clip.with_effects([CrossFadeOut(overlap)])
                elif i == len(clips) - 1:
                    effect_clip = clip.with_effects([CrossFadeIn(overlap)])
                else:
                    effect_clip = clip.with_effects([
                        CrossFadeIn(overlap),
                        CrossFadeOut(overlap)
                    ])
                self._resources.track(effect_clip)

                processed = effect_clip.with_start(current_time)
                self._resources.track(processed)
                result_clips.append(processed)
                current_time += clip_duration - overlap

            except (ValueError, RuntimeError, AttributeError) as e:
                logger.warning(f"  크로스페이드 clip[{i}] 처리 실패: {e}, 원본 사용")
                processed = clip.with_start(current_time)
                self._resources.track(processed)
                result_clips.append(processed)
                current_time += clip_duration

        if not result_clips:
            logger.error("  크로스페이드: 처리된 클립 없음")
            return None

        total_duration = current_time + overlap
        composite = CompositeVideoClip(
            result_clips,
            size=(self.config.width, self.config.height)
        )
        composite = composite.with_duration(total_duration)
        self._resources.track(composite)

        logger.info(f"  크로스페이드 적용: {len(clips)}개 클립, overlap={overlap}초")
        return composite

    def apply_emotion_color_grade(self, clip, emotion: str):
        """감정 기반 색보정 오버레이 적용 (WO v12.0 Phase 6)

        5060 시청자 대상 — alpha 10~15/255로 매우 은은하게 적용.
        """
        if not getattr(self.config, 'emotion_color_grade_enabled', True):
            return clip

        color = EMOTION_COLOR_MAP.get(emotion, EMOTION_COLOR_MAP["neutral"])
        if color[3] == 0:
            return clip

        # None 가드: size 또는 duration 없으면 스킵
        if not hasattr(clip, 'size') or clip.size is None or clip.duration is None:
            return clip

        try:
            overlay = ColorClip(
                size=clip.size, color=color[:3]
            ).with_duration(clip.duration).with_opacity(color[3] / 255)
            self._resources.track(overlay)

            result = CompositeVideoClip([clip, overlay])
            result = result.with_duration(clip.duration)
            self._resources.track(result)

            logger.debug(f"  감정 색보정 적용: emotion={emotion}, rgba={color}")
            return result
        except (ValueError, RuntimeError, AttributeError) as e:
            logger.warning(f"  감정 색보정 적용 실패: {e}, 원본 반환")
            return clip

    def select_transition_params(self, emotion: str, is_block_change: bool = False) -> dict:
        """감정 기반 전환 파라미터 반환 (WO v12.0 Phase 4)

        Args:
            emotion: 세그먼트 감정 ("안심", "공감", "동경", "확신", "neutral")
            is_block_change: Block이 변경되었는지 여부

        Returns:
            dict: {"crossfade": float, "fade_black": bool}
        """
        style = getattr(self.config, 'transition_style', 'auto')

        if style == 'hard_cut':
            return {"crossfade": 0.0, "fade_black": False}
        if style == 'crossfade':
            return {"crossfade": self.config.crossfade_duration, "fade_black": False}

        # auto 모드: 감정 기반
        emotion_crossfade = {
            "안심": 0.35,
            "공감": 0.30,
            "동경": 0.50,
            "확신": 0.20,
            "neutral": 0.35,
        }
        xfade = emotion_crossfade.get(emotion, 0.35)
        use_black = is_block_change  # Block 전환 시만 fade-to-black

        return {"crossfade": xfade, "fade_black": use_black}

    def create_fade_black_clip(self, duration: float = None):
        """Fade-to-black 삽입용 검정 클립 생성 (WO v12.0 Phase 4)"""
        dur = duration or getattr(self.config, 'fade_black_duration', 0.15)
        clip = ColorClip(
            size=(self.config.width, self.config.height),
            color=(0, 0, 0)
        ).with_duration(dur)
        self._resources.track(clip)
        return clip

    def scale_to_fit(self, clip, target_width: int = 1080, target_height: int = 1920):
        """영상/이미지를 타겟 크기에 맞게 스케일 (crop 대신 검은 여백)"""
        if not hasattr(clip, 'size') or clip.size is None:
            logger.warning("  clip.size 없음, fallback 사용")
            fallback = ColorClip(size=(target_width, target_height), color=(0, 0, 0))
            fallback = fallback.with_duration(clip.duration if clip.duration else 5.0)
            self._resources.track(fallback)
            return fallback

        w, h = clip.size

        if not w or not h or w <= 0 or h <= 0:
            logger.warning(f"  Invalid clip size: ({w}, {h}), fallback 사용")
            fallback = ColorClip(size=(target_width, target_height), color=(0, 0, 0))
            fallback = fallback.with_duration(clip.duration if clip.duration else 5.0)
            self._resources.track(fallback)
            return fallback

        clip_duration = clip.duration if clip.duration is not None else 5.0

        scale_w = target_width / w
        scale_h = target_height / h
        fit_scale = min(scale_w, scale_h)

        fill_scale = max(scale_w, scale_h)
        min_coverage_scale = self.config.min_scale_percent * fill_scale
        scale = max(fit_scale, min(min_coverage_scale, fill_scale))
        scale = min(scale, self.MAX_SCALE_FACTOR)

        new_w = max(1, int(w * scale))
        new_h = max(1, int(h * scale))
        scaled_clip = clip.resized((new_w, new_h))
        self._resources.track(scaled_clip)

        if new_w >= target_width and new_h >= target_height:
            x_pos = (target_width - new_w) // 2
            y_pos = (target_height - new_h) // 2
            positioned_clip = scaled_clip.with_position((x_pos, y_pos))
            self._resources.track(positioned_clip)
            result = CompositeVideoClip([positioned_clip], size=(target_width, target_height))
            result = result.with_duration(clip_duration)
            self._resources.track(result)
            return result

        bg = ColorClip(size=(target_width, target_height), color=(0, 0, 0))
        bg = bg.with_duration(clip_duration)
        self._resources.track(bg)

        x_pos = (target_width - new_w) // 2
        y_pos = (target_height - new_h) // 2
        scaled_clip = scaled_clip.with_position((x_pos, y_pos))
        self._resources.track(scaled_clip)

        composite = CompositeVideoClip([bg, scaled_clip], size=(target_width, target_height))
        composite = composite.with_duration(clip_duration)
        self._resources.track(composite)
        return composite

    def load_image_safe(self, image_path: str, preserve_alpha: bool = False) -> ImageClip:
        """EXIF Orientation 보정 + 1080x1920 리사이즈 이미지 로드"""
        try:
            with Image.open(image_path) as img:
                img_rotated = ImageOps.exif_transpose(img)
                if img_rotated is not None:
                    img = img_rotated

                if preserve_alpha and img.mode == 'RGBA':
                    pass
                elif img.mode != 'RGB':
                    img = img.convert('RGB')

                target_w, target_h = self.config.width, self.config.height
                img_w, img_h = img.size

                if img_w <= 0 or img_h <= 0:
                    logger.error(f"  손상된 이미지: {image_path} ({img_w}x{img_h}), 검은 화면으로 대체")
                    mode = 'RGBA' if preserve_alpha else 'RGB'
                    fill_color = (0, 0, 0, 0) if preserve_alpha else (0, 0, 0)
                    img = Image.new(mode, (target_w, target_h), fill_color)
                    img_w, img_h = target_w, target_h

                target_ratio = target_h / target_w
                img_ratio = img_h / img_w

                if img_ratio > target_ratio:
                    scale = target_w / img_w
                else:
                    scale = target_h / img_h

                scale = min(scale, self.MAX_IMAGE_SCALE)
                new_w = int(img_w * scale)
                new_h = int(img_h * scale)
                img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)

                if new_w >= target_w and new_h >= target_h:
                    left = (new_w - target_w) // 2
                    top = (new_h - target_h) // 2
                    img = img.crop((left, top, left + target_w, top + target_h))
                else:
                    new_img = Image.new('RGB' if not preserve_alpha else 'RGBA',
                                        (target_w, target_h),
                                        (0, 0, 0) if not preserve_alpha else (0, 0, 0, 0))
                    left = (target_w - new_w) // 2
                    top = (target_h - new_h) // 2
                    new_img.paste(img, (left, top))
                    img = new_img

                img_array = np.array(img, dtype=np.uint8).copy()

            result = ImageClip(img_array)
            self._resources.track(result)
            return result

        except (OSError, ValueError, RuntimeError) as e:
            logger.warning(f"EXIF 회전 처리 실패 ({image_path}), EXIF 없이 로드: {e}")
            try:
                with Image.open(image_path) as img:
                    if preserve_alpha and img.mode == 'RGBA':
                        pass
                    elif img.mode != 'RGB':
                        img = img.convert('RGB')
                    img_array = np.array(img, dtype=np.uint8).copy()
                result = ImageClip(img_array)
                self._resources.track(result)
                return result
            except (OSError, ValueError, RuntimeError) as e2:
                logger.error(f"이미지 로드 완전 실패 ({image_path}): {e2}")
                fallback = ImageClip(np.zeros((self.config.height, self.config.width, 3), dtype=np.uint8))
                self._resources.track(fallback)
                return fallback
