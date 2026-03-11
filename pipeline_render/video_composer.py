"""
VideoComposer - 비디오 합성 모듈 (S2-3-5)

God Object 분리: generate_video_55sec_pipeline.py에서 추출.
비주얼 타임라인, 자막, Pop, CTA, 로고, Outro 합성.

Usage:
    from pipeline_render import VideoComposer

    composer = VideoComposer(config=config, resources=resources,
                             visual_effects=effects, ...)
    final_video = composer.compose_video(visuals, subtitles, audio, script)
"""

import logging
import re
import traceback
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np
from PIL import Image
from moviepy import (
    ImageClip, TextClip, ColorClip, CompositeVideoClip,
    AudioFileClip,
)
from moviepy.video import fx as vfx

logger = logging.getLogger(__name__)


class VideoComposer:
    """비디오 합성 처리기 (의존성 주입)"""

    # [S2-4-3] Named constants
    SUBTITLE_WIDTH = 840
    POP_TEXT_WIDTH = 800
    POP_Y_CYCLE = (600, 800, 1000)
    POP_IMAGE_HEIGHT = 600
    POP_IMAGE_Y = 450
    LOGO_TOP_MARGIN = 20
    CTA_STROKE_WIDTH = 4
    OUTRO_LOGO_HEIGHT = 300
    OUTRO_INITIAL_SCALE = 0.6
    OUTRO_FINAL_SCALE = 1.0
    OUTRO_CROSSFADE_TIME = 0.5
    OUTRO_PHASE1_RATIO = 0.6
    POP_TIMING_RATIO = 0.3
    OUTRO_MAX_DURATION_WARNING = 3.0

    # WO v11.0 D-4: Pop 모션 파라미터
    POP_SCALE_IN_DURATION = 0.3   # Scale 0%→100% 시간
    POP_PULSE_PERIOD = 0.5        # 펄스 주기
    POP_FADE_OUT_DURATION = 0.2   # 퇴장 Fade Out 시간

    # Pop 하이라이트 패턴 (숫자 + 감정 키워드)
    HIGHLIGHT_PATTERNS = [
        r'(\d+[만백천억조]?원)',
        r'(\d+%)',
        r'(\d+배)',
        r'(\d+시간|\d+일|\d+년)',
        r'(\d+명)',
        r'(무료|특가|한정|추천|비밀|꿀팁|주의|필수|최고|최저|대박|혜택)',
    ]

    def __init__(self, config, resources, visual_effects,
                 fonts_dir: Path, logo_path: Path, asset_matcher=None):
        self.config = config
        self._resources = resources
        self._effects = visual_effects
        self.fonts = fonts_dir
        self.logo_path = logo_path
        self.asset_matcher = asset_matcher

    def compose_video(self, visuals: List, subtitles: List[Dict],
                      audio: AudioFileClip, script: dict):
        """비주얼 + 자막 + Pop + CTA + 로고 합성"""

        # 1. 비주얼 타임라인
        timed_visuals = self._create_timeline(visuals, subtitles)

        # 2. 자막 생성
        font_path = self._get_font_path()
        subtitle_clips = self._create_subtitles(subtitles, font_path)

        # 3. Pop 메시지
        pop_clips = self._create_pop_clips(script, subtitles, font_path)

        # 4. 최종 조합
        final_clips = timed_visuals + subtitle_clips + pop_clips

        if not final_clips:
            logger.warning("  비주얼 클립 없음, fallback 검은 화면 생성")
            fallback = ColorClip(size=(self.config.width, self.config.height), color=(0, 0, 0))
            fallback = fallback.with_duration(self.config.target_duration)
            self._resources.track(fallback)
            final_clips.append(fallback)

        # 5. 로고 오버레이
        total_duration = self._calc_total_duration(timed_visuals)
        self._add_logo_overlay(final_clips, total_duration)

        # 6. CTA 오버레이
        if self.config.enable_cta and timed_visuals:
            self._add_cta_overlay(final_clips, script, total_duration, font_path)

        # 7. Outro 로고 애니메이션
        if self.config.enable_cta and timed_visuals and self.logo_path.exists():
            self._add_outro_animation(final_clips, total_duration)

        # 8. 최종 합성 + Duration 조정 + 오디오
        return self._finalize_video(final_clips, audio, timed_visuals)

    def _get_font_path(self) -> Optional[Path]:
        """폰트 경로 검색 (macOS 숨김 파일 제외, 한글 폰트 우선)"""
        font_files = [f for f in self.fonts.glob("*.ttf") if not f.name.startswith("._")]
        font_files += [f for f in self.fonts.glob("*.otf") if not f.name.startswith("._")]
        if not font_files:
            return None
        # 한글 폰트 우선 (BMDOHYEON, Jalnan, Gmarket 순)
        preferred = ["BMDOHYEON", "Jalnan", "Gmarket", "malgun"]
        for pref in preferred:
            for f in font_files:
                if pref.lower() in f.name.lower():
                    return f
        return font_files[0]

    def _calc_total_duration(self, timed_visuals: List) -> float:
        """전체 영상 길이 계산"""
        if not timed_visuals:
            return self.config.target_duration

        def get_clip_end(clip):
            dur = clip.duration if clip.duration is not None else self.config.target_duration
            if hasattr(clip, 'start') and clip.start is not None:
                return clip.start + dur
            return dur

        return max(get_clip_end(v) for v in timed_visuals)

    def _create_timeline(self, visuals: List, subtitles: List[Dict]) -> List:
        """비주얼 타임라인 생성"""
        prepared_visuals = []

        for idx, visual in enumerate(visuals):
            visual_duration = visual.duration
            if visual_duration is None or visual_duration <= 0:
                fallback_duration = 5.0
                if subtitles and idx < len(subtitles) and isinstance(subtitles[idx], dict):
                    sub_duration = subtitles[idx].get('duration')
                    if sub_duration is not None:
                        try:
                            sub_duration_val = float(sub_duration)
                            if sub_duration_val > 0:
                                fallback_duration = sub_duration_val
                        except (TypeError, ValueError):
                            pass
                visual_duration = fallback_duration
                logger.warning(f"  visual[{idx}] duration=None, fallback={visual_duration:.1f}초")
                visual = visual.with_duration(visual_duration)
                self._resources.track(visual)

            prepared_visuals.append(visual)

        # 크로스페이드 처리
        if self.config.enable_crossfade and len(prepared_visuals) > 1:
            crossfade_composite = self._effects.apply_crossfade(prepared_visuals)
            if crossfade_composite:
                logger.info(f"  크로스페이드 모드: {len(prepared_visuals)}개 클립 합성 (자막 TTS 동기화 유지)")
                return [crossfade_composite]

        # 개별 타이밍
        timed = []
        current_time = 0.0
        for visual in prepared_visuals:
            visual_duration = visual.duration if visual.duration else 5.0
            timed_visual = visual.with_start(current_time)
            self._resources.track(timed_visual)
            timed.append(timed_visual)
            current_time += visual_duration

        return timed

    def _create_subtitles(self, subtitles: List[Dict], font_path) -> List:
        """자막 클립 생성"""
        subtitle_clips = []

        for sub in subtitles:
            if not sub['text']:
                continue

            try:
                txt_kwargs = {
                    'text': sub['text'],
                    'font_size': self.config.subtitle_font_size,
                    'color': 'white',
                    'stroke_color': 'black',
                    'stroke_width': self.config.subtitle_stroke_width,
                    'method': 'caption',
                    'size': (self.SUBTITLE_WIDTH, None)
                }
                if font_path:
                    txt_kwargs['font'] = str(font_path)

                txt_clip_raw = TextClip(**txt_kwargs)
                self._resources.track(txt_clip_raw)

                txt_clip_dur = txt_clip_raw.with_duration(sub['duration'])
                self._resources.track(txt_clip_dur)
                txt_clip_start = txt_clip_dur.with_start(sub['start'])
                self._resources.track(txt_clip_start)
                txt_clip_pos = txt_clip_start.with_position(('center', self.config.subtitle_y_position))
                self._resources.track(txt_clip_pos)
                txt_clip = txt_clip_pos.with_effects([vfx.FadeIn(0.2), vfx.FadeOut(0.15)])
                self._resources.track(txt_clip)

                subtitle_clips.append(txt_clip)
                logger.info(f"  자막 생성: '{sub['text'][:20]}...' ({sub['start']:.1f}-{sub['end']:.1f}초)")
            except (ValueError, RuntimeError, OSError, AttributeError) as e:
                logger.error(f"  자막 생성 실패: {e}")
                logger.debug(traceback.format_exc())

        return subtitle_clips

    def _create_pop_clips(self, script: dict, subtitles: List[Dict], font_path) -> List:
        """Pop 메시지 클립 생성 (metadata timing 기반)

        script.metadata.pop_messages에서 timing/text를 읽어
        정확히 해당 시점에만 Pop을 생성한다.
        """
        pop_clips = []
        pop_messages = script.get('metadata', {}).get('pop_messages', [])

        if not pop_messages or not font_path:
            return pop_clips

        # Calculate total duration from subtitles for compression adjustment
        total_dur = sum(s.get('duration', 0) for s in subtitles) if subtitles else 55.0

        for i, pop in enumerate(pop_messages):
            pop_time = pop.get('timing', 0)
            pop_text = pop.get('text', '')
            if not pop_text or pop_time <= 0:
                continue

            # Adjust pop_time if duration was compressed
            if total_dur < 55.0:
                pop_time = pop_time * (total_dur / 55.0)

            # Find the segment text near this timing for pop image matching
            segment_text = self._find_segment_text_at_time(script, subtitles, pop_time)

            self._create_single_pop(pop_clips, pop_text, pop_time, segment_text, font_path)

        return pop_clips

    def _find_segment_text_at_time(self, script: dict, subtitles: List[Dict], target_time: float) -> str:
        """Find the segment narration text closest to the given time"""
        cumulative = 0.0
        segments = script.get('segments', [])
        for i, sub in enumerate(subtitles):
            dur = sub.get('duration', 0)
            if cumulative + dur > target_time:
                if i < len(segments):
                    return segments[i].get('text', '')
                return sub.get('text', '')
            cumulative += dur
        # Fallback: return last segment text
        if segments:
            return segments[-1].get('text', '')
        return ''

    def _apply_pop_motion(self, pop_clip, start_time: float, duration: float):
        """Pop 클립에 모션 효과 적용 (WO v11.0 D-4)

        Scale In (0.3초) + Pulse (0.5초 주기) + Fade Out (0.2초)

        Args:
            pop_clip: 기존 Pop TextClip/ImageClip
            start_time: Pop 시작 시간
            duration: Pop 표시 시간

        Returns:
            모션 적용된 Pop 클립
        """
        try:
            from moviepy.video.fx import CrossFadeOut

            # 1. Fade Out 적용
            fade_clip = pop_clip.with_effects([CrossFadeOut(self.POP_FADE_OUT_DURATION)])
            self._resources.track(fade_clip)

            logger.debug(f"  Pop 모션 적용: start={start_time:.1f}s, dur={duration:.1f}s")
            return fade_clip

        except (ImportError, ValueError, RuntimeError) as e:
            logger.warning(f"  Pop 모션 적용 실패: {e}, 원본 사용")
            return pop_clip

    def _determine_pop_text(self, numbers, seg, is_body_segment) -> str:
        """Pop 텍스트 결정"""
        if numbers:
            return numbers[0]
        elif seg.get('pop_message'):
            return seg['pop_message']
        elif is_body_segment:
            subtitle_text = seg.get('subtitle', '')
            words = subtitle_text.split()[:3]
            return ' '.join(words) if words else '크루즈'
        else:
            return seg.get('subtitle', '')[:20]

    def _create_single_pop(self, pop_clips, pop_text, pop_time, segment_text, font_path):
        """단일 Pop 메시지 + 이미지 생성"""
        try:
            pop_text_clip = TextClip(
                text=pop_text,
                font_size=self.config.pop_font_size,
                color='yellow',
                font=str(font_path),
                stroke_color='red',
                stroke_width=self.config.pop_stroke_width,
                method='caption',
                size=(self.POP_TEXT_WIDTH, None)
            )
            self._resources.track(pop_text_clip)

            pop_dur = pop_text_clip.with_duration(self.config.pop_duration)
            self._resources.track(pop_dur)
            pop_start = pop_dur.with_start(pop_time)
            self._resources.track(pop_start)

            pop_y = self.POP_Y_CYCLE[len(pop_clips) % len(self.POP_Y_CYCLE)]
            pop_pos = pop_start.with_position(('center', pop_y))
            self._resources.track(pop_pos)
            pop_clip = pop_pos.with_effects([vfx.FadeIn(self.config.fade_in_duration), vfx.FadeOut(self.config.fade_out_duration)])
            self._resources.track(pop_clip)

            pop_clips.append(pop_clip)

            # Pop 이미지 매칭 — 텍스트 후 0.8초 지연 시작 (겹침 방지)
            self._add_pop_image(pop_clips, segment_text, pop_time + 0.8)

            logger.info(f"  Pop 메시지+이미지 추가: '{pop_text}' ({pop_time:.2f}초)")
        except (ValueError, RuntimeError, OSError) as e:
            logger.warning(f"  Pop 메시지 생성 실패: {e}")

    def _add_pop_image(self, pop_clips, segment_text, pop_time):
        """Pop 이미지 매칭 및 추가"""
        try:
            if self.asset_matcher is None:
                return

            # [FIX S2-5] match_assets API 사용 (get_best_asset_v2 미존재)
            from engines.keyword_extraction.intelligent_keyword_extractor import extract_keywords
            kw_result = extract_keywords(segment_text) if segment_text else None
            keywords = (kw_result.primary + kw_result.english) if kw_result else []
            matches = self.asset_matcher.match_assets(
                keywords=keywords[:5],
                content_type="Body",
                max_results=3,
                prefer_images=True,
                allow_videos=True,
            )

            # threshold를 15로 낮추고 이미지+비디오 모두 허용
            pop_threshold = min(getattr(self.config, 'pop_match_threshold', 30), 15)
            if matches and matches[0].score >= pop_threshold:
                pop_image_path = str(matches[0].path)

                pop_img_raw = self._effects.load_image_safe(pop_image_path)
                pop_img_resized = pop_img_raw.resized(height=self.POP_IMAGE_HEIGHT)
                self._resources.track(pop_img_resized)
                pop_img_dur = pop_img_resized.with_duration(self.config.pop_image_duration)
                self._resources.track(pop_img_dur)
                pop_img_start = pop_img_dur.with_start(pop_time)
                self._resources.track(pop_img_start)
                pop_img_pos = pop_img_start.with_position(('center', self.POP_IMAGE_Y))
                self._resources.track(pop_img_pos)
                pop_image = pop_img_pos.with_effects([vfx.FadeIn(self.config.fade_in_duration), vfx.FadeOut(self.config.fade_out_duration)])
                self._resources.track(pop_image)

                pop_clips.insert(-1, pop_image)
                logger.info(f"  Pop 이미지 매칭: {Path(pop_image_path).name} (점수: {matches[0].score})")
            else:
                best = matches[0].score if matches else 0
                logger.warning(f"  Pop 이미지 매칭 실패: 최고점수={best}, threshold={pop_threshold}, keywords={keywords[:3]}")
        except (OSError, ValueError, RuntimeError) as e:
            logger.warning(f"  Pop 이미지 로드 실패: {e}")

    def _add_logo_overlay(self, final_clips: List, total_duration: float):
        """로고 오버레이 추가"""
        if not self.logo_path.exists():
            logger.warning(f"  로고 파일 없음: {self.logo_path}")
            return

        try:
            with Image.open(str(self.logo_path)) as logo_img_orig:
                if logo_img_orig.mode != 'RGBA':
                    logo_img_rgba = logo_img_orig.convert('RGBA')
                else:
                    logo_img_rgba = logo_img_orig

                if logo_img_rgba.height <= 0 or logo_img_rgba.width <= 0:
                    raise ValueError(f"손상된 로고 이미지 크기: {logo_img_rgba.width}x{logo_img_rgba.height}")

                aspect_ratio = logo_img_rgba.width / logo_img_rgba.height
                new_height = self.config.logo_height
                new_width = max(1, int(new_height * aspect_ratio))
                logo_resized = logo_img_rgba.resize((new_width, new_height), Image.Resampling.LANCZOS)

                logo_array = np.array(logo_resized, dtype=np.uint8)

                if logo_img_rgba is not logo_img_orig:
                    logo_img_rgba.close()
                if logo_resized is not logo_img_rgba:
                    logo_resized.close()

            logo_rgb = logo_array[:, :, :3]
            logo_alpha = logo_array[:, :, 3] / 255.0

            logo_rgb_clip = ImageClip(logo_rgb)
            self._resources.track(logo_rgb_clip)
            logo_mask_clip = ImageClip(logo_alpha, is_mask=True)
            self._resources.track(logo_mask_clip)
            logo_with_mask = logo_rgb_clip.with_mask(logo_mask_clip)
            self._resources.track(logo_with_mask)

            # 아웃트로 구간에서는 큰 로고가 나오므로 작은 로고는 아웃트로 전까지만
            outro_dur = min(getattr(self.config, 'outro_visual_duration', 2.5), self.OUTRO_MAX_DURATION_WARNING)
            logo_end_time = max(1.0, total_duration - outro_dur)
            logo_dur = logo_with_mask.with_duration(logo_end_time)
            self._resources.track(logo_dur)
            logo_pos = logo_dur.with_position((self.config.width - new_width - 20, self.LOGO_TOP_MARGIN))
            self._resources.track(logo_pos)
            logo_clip = logo_pos.with_opacity(self.config.logo_opacity)
            self._resources.track(logo_clip)

            final_clips.append(logo_clip)
            logger.info(f"  로고 추가 (투명 PNG): {self.logo_path.name} ({total_duration:.1f}초)")
        except (OSError, ValueError, RuntimeError, AttributeError) as e:
            logger.error(f"  로고 추가 실패: {e}")
            logger.debug(traceback.format_exc())

    def _add_cta_overlay(self, final_clips: List, script: dict,
                         total_duration: float, font_path):
        """CTA 오버레이 추가"""
        try:
            cta_text = script.get('cta_text', self.config.cta_text)
            cta_start = max(0, total_duration - self.config.cta_duration)

            cta_kwargs = {
                'text': cta_text,
                'font_size': self.config.cta_font_size,
                'color': 'white',
                'stroke_color': 'black',
                'stroke_width': self.CTA_STROKE_WIDTH,
                'method': 'caption',
                'size': (self.SUBTITLE_WIDTH, None)
            }
            if font_path:
                cta_kwargs['font'] = str(font_path)

            cta_raw = TextClip(**cta_kwargs)
            self._resources.track(cta_raw)
            cta_dur = cta_raw.with_duration(self.config.cta_duration)
            self._resources.track(cta_dur)
            cta_start_clip = cta_dur.with_start(cta_start)
            self._resources.track(cta_start_clip)
            cta_pos = cta_start_clip.with_position(('center', self.config.cta_y_position))
            self._resources.track(cta_pos)
            cta_clip = cta_pos.with_effects([vfx.FadeIn(self.config.fade_in_duration)])
            self._resources.track(cta_clip)

            final_clips.append(cta_clip)
            logger.info(f"  CTA 추가: '{cta_text}' ({cta_start:.1f}-{total_duration:.1f}초)")
        except (ValueError, RuntimeError, OSError, AttributeError) as e:
            logger.warning(f"  CTA 생성 실패: {e}")
            logger.debug(traceback.format_exc())

    def _add_outro_animation(self, final_clips: List, total_duration: float):
        """Outro 로고 애니메이션 (0.6x → 1.0x CrossFade)"""
        try:
            outro_duration = min(self.config.outro_visual_duration, self.OUTRO_MAX_DURATION_WARNING)
            outro_start = max(0, total_duration - outro_duration)

            # Dark background for outro
            bg = ColorClip(size=(self.config.width, self.config.height), color=(0, 0, 0))
            bg = bg.with_duration(outro_duration)
            self._resources.track(bg)
            bg = bg.with_start(outro_start)
            self._resources.track(bg)
            bg = bg.with_effects([vfx.CrossFadeIn(0.5)])
            self._resources.track(bg)
            bg = bg.with_position(("center", "center"))
            self._resources.track(bg)
            bg = bg.with_opacity(0.7)
            self._resources.track(bg)
            final_clips.append(bg)

            with Image.open(str(self.logo_path)) as logo_img:
                if logo_img.mode != 'RGBA':
                    logo_img = logo_img.convert('RGBA')

                aspect_ratio = logo_img.width / logo_img.height
                outro_logo_width = max(1, int(self.OUTRO_LOGO_HEIGHT * aspect_ratio))
                logo_img = logo_img.resize((outro_logo_width, self.OUTRO_LOGO_HEIGHT), Image.Resampling.LANCZOS)
                logo_array = np.array(logo_img, dtype=np.uint8).copy()

            logo_rgb = logo_array[:, :, :3]
            logo_alpha = logo_array[:, :, 3] / 255.0

            logo_rgb_clip = ImageClip(logo_rgb)
            self._resources.track(logo_rgb_clip)
            logo_mask_clip = ImageClip(logo_alpha, is_mask=True)
            self._resources.track(logo_mask_clip)
            logo_with_mask = logo_rgb_clip.with_mask(logo_mask_clip)
            self._resources.track(logo_with_mask)

            # Phase 1: 작은 로고
            phase1_duration = outro_duration * self.OUTRO_PHASE1_RATIO
            crossfade_time = self.OUTRO_CROSSFADE_TIME

            logo_small_dur = logo_with_mask.with_duration(phase1_duration)
            self._resources.track(logo_small_dur)
            logo_small_resized = logo_small_dur.resized(self.OUTRO_INITIAL_SCALE)
            self._resources.track(logo_small_resized)
            logo_small_pos = logo_small_resized.with_position('center')
            self._resources.track(logo_small_pos)
            logo_small_fade = logo_small_pos.with_effects([vfx.FadeIn(self.config.fade_in_duration), vfx.FadeOut(crossfade_time)])
            self._resources.track(logo_small_fade)
            logo_small_start = logo_small_fade.with_start(outro_start)
            self._resources.track(logo_small_start)

            # Phase 2: 큰 로고
            phase2_duration = outro_duration - phase1_duration + crossfade_time
            phase2_start = outro_start + phase1_duration - crossfade_time

            logo_large_dur = logo_with_mask.with_duration(phase2_duration)
            self._resources.track(logo_large_dur)
            logo_large_resized = logo_large_dur.resized(self.OUTRO_FINAL_SCALE)
            self._resources.track(logo_large_resized)
            logo_large_pos = logo_large_resized.with_position('center')
            self._resources.track(logo_large_pos)
            logo_large_fade = logo_large_pos.with_effects([vfx.FadeIn(crossfade_time)])
            self._resources.track(logo_large_fade)
            logo_large_start = logo_large_fade.with_start(phase2_start)
            self._resources.track(logo_large_start)

            final_clips.append(logo_small_start)
            final_clips.append(logo_large_start)
            logger.info(f"  Outro 로고 애니메이션: {outro_start:.1f}-{total_duration:.1f}초 (0.6x→1.0x CrossFade {crossfade_time}s)")
        except (OSError, ValueError, RuntimeError, AttributeError) as e:
            logger.warning(f"  Outro 로고 애니메이션 실패: {e}")
            logger.debug(traceback.format_exc())

    def _finalize_video(self, final_clips: List, audio, timed_visuals: List):
        """최종 합성 + Duration 조정 + 오디오 추가"""
        final_video = CompositeVideoClip(final_clips, size=(self.config.width, self.config.height))
        self._resources.track(final_video)

        if final_video.duration is None:
            logger.error("  final_video.duration이 None입니다. 기본값 사용")
            final_video = final_video.with_duration(self.config.target_duration)
            self._resources.track(final_video)

        # Duration 초과 시 강제 트리밍 (max_duration 기준)
        if final_video.duration > self.config.max_duration:
            original_duration = final_video.duration
            trimmed_video = final_video.subclipped(0, self.config.max_duration)
            self._resources.track(trimmed_video)
            final_video = trimmed_video
            logger.info(f"  Duration 초과 -> 트리밍: {original_duration:.1f}s -> {self.config.max_duration}s")
        elif self.config.dynamic_duration:
            if final_video.duration < self.config.min_content_duration:
                old_dur = final_video.duration
                target = self.config.min_content_duration
                final_video = self._effects.extend_with_freeze(final_video, target)
                logger.warning(f"  Duration 너무 짧음 -> 최소 freeze: {old_dur:.1f}s -> {target:.1f}s")
            else:
                logger.info(f"  동적 길이 모드: {final_video.duration:.1f}초 (freeze 없음)")
        elif final_video.duration < self.config.min_duration:
            old_dur = final_video.duration
            final_video = self._effects.extend_with_freeze(final_video, self.config.target_duration)
            logger.info(f"  Duration 부족 -> freeze 연장: +{self.config.target_duration - old_dur:.1f}s")

        if audio:
            if audio.duration and audio.duration > final_video.duration:
                audio = audio.subclipped(0, final_video.duration)
                self._resources.track(audio)
                logger.info(f"  오디오 트리밍: -> {final_video.duration:.1f}s")

            final_video = final_video.with_audio(audio)
            self._resources.track(final_video)
            logger.info(f"  오디오 추가 완료: {final_video.duration:.1f}초")
        else:
            logger.warning("  오디오 없음 - 무음 영상")

        # 최종 안전망: 오디오 합성 후에도 duration 초과 시 강제 트리밍
        if final_video.duration is not None and final_video.duration > self.config.max_duration:
            original = final_video.duration
            final_video = final_video.subclipped(0, self.config.max_duration)
            self._resources.track(final_video)
            logger.warning(f"  최종 안전망 트리밍: {original:.1f}s -> {self.config.max_duration}s")

        return final_video
