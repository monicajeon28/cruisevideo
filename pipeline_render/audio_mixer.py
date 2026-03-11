"""
AudioMixer - 오디오 믹싱 모듈 (S2-3-3)

God Object 분리: generate_video_55sec_pipeline.py에서 추출.
BGM 더킹, 나레이션 조합, Pop/Outro 효과음 믹싱.

Usage:
    from pipeline_render import AudioMixer

    mixer = AudioMixer(config=config, resources=resource_tracker,
                       sfx_dir=sfx_path, bgm_dir=bgm_path)
    audio = mixer.mix_audio(tts_files, script, actual_durations)
"""

import logging
import random
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
from moviepy import AudioClip, AudioFileClip, CompositeAudioClip, vfx

logger = logging.getLogger(__name__)


class AudioMixer:
    """오디오 믹싱 처리기 (config + resources + paths 의존성 주입)"""

    # [S2-4-3] Named constants
    DEFAULT_AUDIO_FPS = 44100
    POP_TIMING_RATIO = 0.3
    OUTRO_SFX_LEAD_TIME = 3  # 아웃트로 SFX는 TTS 종료 N초 전 시작

    # [S2-A4] SFX 카테고리별 키워드 매핑
    SFX_CATEGORY_KEYWORDS = {
        "pop": ["pop", "bubble", "notification", "ding", "chime"],
        "outro": ["horn", "ship", "boat", "whistle", "farewell"],
        "swoosh": ["swoosh", "whoosh", "swipe", "transition"],
        "hit": ["hit", "impact", "punch", "slam"],
        "level": ["level", "upgrade", "power"],
    }

    def __init__(self, config, resources, sfx_dir: Path, bgm_dir: Path):
        """
        Args:
            config: PipelineConfig (또는 호환 객체)
            resources: ResourceTracker (track 메서드 보유)
            sfx_dir: SFX 파일 디렉토리 경로
            bgm_dir: BGM 파일 디렉토리 경로
        """
        self.config = config
        self._resources = resources
        self.sfx = sfx_dir
        self.bgm = bgm_dir

    def _select_sfx(self, category: str, default_filename: str) -> Optional[Path]:
        """SFX 풀에서 카테고리별 랜덤 선택 (S2-A4)

        Args:
            category: SFX 카테고리 ("pop", "outro", "swoosh" 등)
            default_filename: 기본 파일명 (풀이 비었을 때 fallback)

        Returns:
            선택된 SFX 파일 Path (없으면 기본 경로)
        """
        sfx_random = getattr(self.config, 'sfx_random_selection', False)

        if not sfx_random:
            return self.sfx / default_filename

        keywords = self.SFX_CATEGORY_KEYWORDS.get(category, [category])
        candidates = []

        for ext in ("*.mp3", "*.wav", "*.ogg"):
            for f in self.sfx.glob(ext):
                name_lower = f.stem.lower()
                if any(kw in name_lower for kw in keywords):
                    candidates.append(f)

        if not candidates:
            fallback = self.sfx / default_filename
            if not fallback.exists():
                logger.warning(f"  SFX fallback 파일 없음: {fallback}")
                return None
            logger.debug(f"  SFX 풀 '{category}' 후보 없음, 기본값 사용: {default_filename}")
            return fallback

        selected = random.choice(candidates)
        logger.info(f"  SFX 랜덤 선택 [{category}]: {selected.name} (후보 {len(candidates)}개)")
        return selected

    def create_ducked_bgm(
        self,
        bgm_clip,
        narration_segments: List[Tuple[float, float]],
        duck_level: float = None,
        fade_duration: float = None,
        base_volume: float = None
    ):
        """나레이션 구간에서 BGM 볼륨을 자동으로 낮춤 (더킹)"""
        if duck_level is None:
            duck_level = self.config.duck_level
        if fade_duration is None:
            fade_duration = self.config.duck_fade_duration
        if base_volume is None:
            base_volume = self.config.bgm_volume

        if not narration_segments:
            result = bgm_clip.with_volume_scaled(base_volume)
            self._resources.track(result)
            return result

        def volume_at_time(t):
            """시간 t에서의 볼륨 계산"""
            for start, end in narration_segments:
                fade_out_start = max(0, start - fade_duration)
                if fade_out_start <= t < start:
                    if fade_duration <= 0:
                        return base_volume * duck_level
                    progress = (t - fade_out_start) / fade_duration
                    target = base_volume * duck_level
                    return base_volume - progress * (base_volume - target)

                if start <= t < end:
                    return base_volume * duck_level

                if end <= t < end + fade_duration:
                    if fade_duration <= 0:
                        return base_volume
                    progress = (t - end) / fade_duration
                    target = base_volume * duck_level
                    return target + progress * (base_volume - target)

            return base_volume

        def make_frame(t):
            """볼륨 조절된 프레임 생성"""
            if isinstance(t, np.ndarray):
                frames = bgm_clip.get_frame(t)
                volumes = np.array([volume_at_time(ti) for ti in t])
                if len(frames.shape) > 1:
                    volumes = volumes.reshape(-1, 1)
                return frames * volumes
            else:
                return bgm_clip.get_frame(t) * volume_at_time(t)

        try:
            ducked_raw = AudioClip(make_frame, duration=bgm_clip.duration)
            self._resources.track(ducked_raw)

            fps = getattr(bgm_clip, 'fps', None) or self.DEFAULT_AUDIO_FPS
            ducked = ducked_raw.with_fps(fps)
            self._resources.track(ducked)

            logger.info(f"  오디오 더킹 적용: {len(narration_segments)}개 구간, duck={duck_level*100:.0f}%")
            return ducked

        except (ValueError, RuntimeError, TypeError, ZeroDivisionError) as e:
            logger.warning(f"  오디오 더킹 실패: {e}, 기본 볼륨 적용")
            result = bgm_clip.with_volume_scaled(base_volume)
            self._resources.track(result)
            return result

    def mix_audio(
        self,
        tts_files: List[Optional[str]],
        script: dict,
        actual_durations: List[float],
        hook_audio=None
    ):
        """오디오 믹싱 (나레이션 + BGM + Pop 효과음 + 아웃트로 효과음)"""
        audio_clips = []

        # [WO v12.0 Phase 1] Hook 나레이션 0초부터 즉시 시작
        logger.info(f"  Hook 구간: 나레이션 즉시 시작 (0-{self.config.hook_duration:.1f}초)")

        # 1. 나레이션 조합
        narration_clips = []
        narration_segments = []
        current_time = 0.0

        for i, tts_file in enumerate(tts_files):
            target_duration = actual_durations[i] if i < len(actual_durations) else 3.0

            if tts_file is None:
                current_time += target_duration
                continue

            audio = AudioFileClip(tts_file)
            self._resources.track(audio)

            if audio.duration is None or audio.duration <= 0:
                logger.warning(f"  나레이션 duration 없음: {tts_file}")
                current_time += target_duration
                continue

            # Duration 압축: actual_durations가 TTS 원본보다 짧으면 속도 조절 또는 트리밍
            clip_duration = audio.duration
            if target_duration < clip_duration and target_duration > 0:
                speed_ratio = clip_duration / target_duration
                if speed_ratio <= 1.5:
                    # Speed up audio to fit (max 1.5x to preserve intelligibility)
                    audio = audio.with_effects([vfx.MultiplySpeed(speed_ratio)])
                    self._resources.track(audio)
                    logger.info(f"  나레이션 속도조절: {clip_duration:.2f}초 → {target_duration:.2f}초 ({speed_ratio:.2f}x)")
                else:
                    # Too much compression - trim and log warning
                    audio = audio.subclipped(0, target_duration)
                    self._resources.track(audio)
                    logger.warning(f"  TTS trim: {clip_duration:.1f}s → {target_duration:.1f}s (ratio {speed_ratio:.2f}x too high for speed-up)")
                clip_duration = target_duration

            start_time = current_time
            audio_vol = audio.with_volume_scaled(self.config.narration_volume)
            self._resources.track(audio_vol)
            audio = audio_vol.with_start(start_time)
            self._resources.track(audio)

            narration_clips.append(audio)
            current_time += clip_duration

            narration_segments.append((start_time, current_time))

            logger.info(f"  나레이션 추가: {Path(tts_file).name} (시작: {start_time:.2f}초, 길이: {clip_duration:.2f}초)")

        total_narration_duration = current_time

        if not narration_clips:
            logger.info("Mock mode: 나레이션 없음, BGM과 효과음만 사용")
            total_narration_duration = sum(actual_durations)

        # 1.5 Intro SFX 비활성화 — 후킹 나레이션 즉시 시작 우선
        # (인트로 효과음이 후킹 포인트를 방해하므로 제거)
        logger.info("  Intro SFX 비활성화: 나레이션 즉시 시작")

        # 2. Pop 효과음 추가 (metadata.pop_messages 타이밍 기반)
        pop_sfx_path = self._select_sfx("pop", "pop_2-389266.mp3")
        pop_messages = script.get('metadata', {}).get('pop_messages', [])
        if pop_sfx_path and pop_sfx_path.exists() and pop_messages:
            for pop_msg in pop_messages:
                pop_time = pop_msg.get('timing', 0)
                if pop_time <= 0:
                    continue

                try:
                    # Swoosh before pop
                    swoosh_sfx = self._select_sfx("swoosh", "swoosh-016-383771.mp3")
                    if swoosh_sfx and swoosh_sfx.exists():
                        try:
                            swoosh_clip = AudioFileClip(str(swoosh_sfx))
                            self._resources.track(swoosh_clip)
                            swoosh_vol = getattr(self.config, 'swoosh_volume', 0.18)
                            swoosh_clip = swoosh_clip.with_volume_scaled(swoosh_vol)
                            self._resources.track(swoosh_clip)
                            swoosh_time = max(0, pop_time - 0.3)
                            swoosh_clip = swoosh_clip.with_start(swoosh_time)
                            self._resources.track(swoosh_clip)
                            audio_clips.append(swoosh_clip)
                            logger.info(f"  Swoosh SFX 추가: {swoosh_time:.2f}초 (pop 0.3초 전)")
                        except Exception as e:
                            logger.warning(f"  Swoosh SFX failed: {e}")

                    pop_audio = AudioFileClip(str(pop_sfx_path))
                    self._resources.track(pop_audio)
                    pop_audio_start = pop_audio.with_start(pop_time)
                    self._resources.track(pop_audio_start)
                    pop_audio_final = pop_audio_start.with_volume_scaled(self.config.pop_sfx_volume)
                    self._resources.track(pop_audio_final)
                    audio_clips.append(pop_audio_final)
                    logger.info(f"  Pop 효과음 추가: {pop_time:.2f}초 '{pop_msg.get('text', '')[:15]}'")
                except (OSError, ValueError) as e:
                    logger.warning(f"  Pop 효과음 로드 실패: {e}")
        elif not pop_messages:
            logger.warning("  Pop 메타데이터 없음 - Pop SFX 생략")
        else:
            logger.warning(f"  Pop 효과음 파일 없음: {pop_sfx_path}")

        # 3. BGM (0초부터 전체 영상, 더킹 적용)
        bgm_files = list(self.bgm.glob("**/*.mp3"))
        if bgm_files:
            bgm_file = random.choice(bgm_files)
            bgm_target_duration = max(total_narration_duration, self.config.target_duration)

            bgm = AudioFileClip(str(bgm_file))
            self._resources.track(bgm)

            bgm_clip_duration = min(bgm_target_duration, bgm.duration)

            bgm = bgm.subclipped(0, bgm_clip_duration)
            self._resources.track(bgm)

            if self.config.enable_ducking and narration_segments:
                bgm = self.create_ducked_bgm(
                    bgm,
                    narration_segments,
                    duck_level=self.config.duck_level,
                    fade_duration=self.config.duck_fade_duration,
                    base_volume=self.config.bgm_volume
                )
                logger.info(f"  BGM 더킹 적용: {len(narration_segments)}개 구간, duck={self.config.duck_level*100:.0f}%")
            else:
                bgm = bgm.with_volume_scaled(self.config.bgm_volume)
                self._resources.track(bgm)

            bgm = bgm.with_start(0)
            self._resources.track(bgm)
            audio_clips.append(bgm)
            logger.info(f"  BGM 추가: {bgm_file.name} (0-{bgm_clip_duration:.1f}초)")
        else:
            logger.warning("  BGM 파일 없음")

        # 4. 아웃트로 효과음 (S2-A4: SFX 풀 랜덤 선택)
        outro_sfx_path = self._select_sfx("outro", "ship-horn-352063.mp3")
        if outro_sfx_path and outro_sfx_path.exists():
            outro_start = max(0, total_narration_duration - self.OUTRO_SFX_LEAD_TIME)
            outro_sfx = AudioFileClip(str(outro_sfx_path))
            self._resources.track(outro_sfx)
            outro_sfx_vol = outro_sfx.with_volume_scaled(self.config.outro_sfx_volume)
            self._resources.track(outro_sfx_vol)
            outro_sfx_final = outro_sfx_vol.with_start(outro_start)
            self._resources.track(outro_sfx_final)
            audio_clips.append(outro_sfx_final)
            logger.info(f"  아웃트로 SFX 추가: {outro_start:.1f}초 시작 (TTS 종료 3초 전)")

        # 최종 믹싱
        audio_clips.extend(narration_clips)

        if audio_clips:
            final_audio = CompositeAudioClip(audio_clips)
            self._resources.track(final_audio)
            return final_audio
        else:
            logger.warning("  오디오 트랙 없음")
            return None
