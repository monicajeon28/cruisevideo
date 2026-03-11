#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PipelineConfig - 55초 영상 파이프라인 설정

[S2-3-1] God Object 분리: 95+ 필드 → 8개 논리 그룹 + Facade
기존 API 100% 호환: config.bgm_volume == config.audio.bgm_volume

Usage:
    from video_pipeline.config import PipelineConfig

    config = PipelineConfig()
    config = PipelineConfig(target_duration=55.0, fps=30)

    # 새로운 접근 (논리 그룹)
    config.audio.bgm_volume
    config.video.fps
"""

from dataclasses import dataclass, field
from pathlib import Path


def _default_use_nvenc() -> bool:
    """NVENC GPU 인코딩 사용 여부 자동 감지"""
    try:
        from video_pipeline.gpu_detector import detect_nvenc_support
        return detect_nvenc_support()
    except (ImportError, OSError, RuntimeError, SyntaxError):
        return False


def _resolve_path(key: str) -> str:
    """PathResolver를 통한 지연 경로 해결 (순환참조 방지)"""
    try:
        from path_resolver import get_paths
        paths = get_paths()
        mapping = {
            'sfx_base_dir': str(paths.sfx_dir),
            'cta_overlay_config_path': str(paths.config_dir / "cta_overlay_config.yaml"),
            'intro_sfx_path': str(paths.intro_sfx_path),
        }
        return mapping.get(key, "")
    except (ImportError, Exception):
        # PathResolver 미사용 환경에서는 기존 기본값 유지
        fallbacks = {
            'sfx_base_dir': "D:/AntiGravity/Assets/SoundFX",
            'cta_overlay_config_path': "D:/mabiz/config/cta_overlay_config.yaml",
            'intro_sfx_path': "D:/AntiGravity/Assets/SoundFX/level-up-08-402152.mp3",
        }
        return fallbacks.get(key, "")


# ============================================================================
# 1. Sub-Config Dataclasses (논리 그룹별 분리)
# ============================================================================

@dataclass
class VideoEncodingConfig:
    """비디오 인코딩 설정"""
    target_duration: float = 55.0
    min_duration: float = 53.0
    max_duration: float = 58.0
    fps: int = 30
    width: int = 1080
    height: int = 1920
    min_scale_percent: float = 0.7
    codec: str = 'libx264'
    audio_codec: str = 'aac'
    preset: str = 'veryfast'
    bitrate: str = '6000k'
    audio_bitrate: str = '192k'
    use_nvenc: bool = field(default_factory=_default_use_nvenc)
    nvenc_preset: str = 'p2'
    nvenc_profile: str = 'high'
    dynamic_duration: bool = True
    min_content_duration: float = 25.0


@dataclass
class AudioConfig:
    """오디오/BGM/SFX 설정"""
    bgm_volume: float = 0.20
    bgm_allowed_categories: list = field(default_factory=lambda: ['travel', 'upbeat', 'energetic', 'calm', 'leisure', 'relaxing'])
    bgm_ducking_volume: float = 0.06
    pop_sfx_volume: float = 0.30
    intro_sfx_volume: float = 0.55
    outro_sfx_volume: float = 0.3
    hit_impact_volume: float = 0.25
    swoosh_volume: float = 0.18
    bell_emphasis_volume: float = 0.30
    narration_volume: float = 1.0
    enable_ducking: bool = True
    duck_level: float = 0.18
    duck_fade_duration: float = 0.3
    enable_lufs_normalization: bool = True
    target_lufs: float = -14.0
    true_peak: float = -1.5
    lra: float = 11.0
    # S2-A4: SFX 풀 랜덤 선택
    sfx_random_selection: bool = True
    sfx_base_dir: str = field(default_factory=lambda: _resolve_path('sfx_base_dir'))


@dataclass
class SubtitleConfig:
    """자막/Pop 텍스트 설정"""
    subtitle_font_size: int = 58
    subtitle_stroke_width: int = 3
    image_subtitle_font_size: int = 80
    image_subtitle_stroke_width: int = 4
    subtitle_y_position: int = 1350
    subtitle_bg_enabled: bool = True
    subtitle_bg_opacity: float = 0.7
    subtitle_bg_padding: int = 25
    pop_font_size: int = 100
    pop_stroke_width: int = 5
    pop_stroke_color: str = '#000000'
    hook_subtitle_stroke_color: str = '#000000'
    hook_subtitle_font_size: int = 70
    hook_subtitle_color: str = 'yellow'
    hook_subtitle_bg_opacity: float = 0.85
    hook_subtitle_max_width: int = 820
    subtitle_max_width: int = 920
    subtitle_chars_per_line: int = 10


@dataclass
class TTSConfig:
    """TTS 음성 합성 설정"""
    tts_max_retries: int = 3
    tts_base_delay: float = 1.0
    tts_max_delay: float = 10.0
    max_tts_chars_per_segment: int = 250
    chars_per_second: float = 4.2
    tts_min_speed: float = 0.75
    tts_max_speed: float = 1.15
    min_tts_chars: int = 210
    enable_async_tts: bool = True
    async_tts_max_concurrent: int = 5
    async_tts_rate_limit: float = 5.0
    enable_dialogue_tts: bool = True
    dialogue_host_voice: str = "audrey"
    dialogue_guest_voice: str = "juho"
    enable_hook_tts: bool = True
    use_hook_original_audio: bool = False
    # S2-A2: 피치 핑거프린트 분산
    fingerprint_pitch_variance: int = 2    # ±2 반음 (음성 품질 저하 없는 범위)
    enable_pitch_variance: bool = True


@dataclass
class VisualEffectsConfig:
    """시각 효과 설정 (Ken Burns, Crossfade, 색보정)"""
    enable_crossfade: bool = True
    crossfade_duration: float = 0.35
    enable_ken_burns: bool = True
    ken_burns_zoom_ratio: float = 0.048
    ken_burns_random_variance: float = 0.00
    ken_burns_emotion_weight_enabled: bool = True
    ken_burns_for_images_only: bool = True
    enable_color_correction: bool = True
    color_correction_preset: str = "natural"
    color_correction_apply_to_hook: bool = True
    color_correction_auto_detect: bool = True
    enable_visual_interleaving: bool = True
    interleave_image_segments: tuple = ('pain_point', 'value_proof_1', 'value_proof_2', 'emotional_peak', 'offer')
    interleave_video_segments: tuple = ('solution', 'trust_insurance', 'affinity', 'narrowing', 'cta')
    fade_in_duration: float = 0.2
    fade_out_duration: float = 0.3
    enable_sentence_visual_mapping: bool = True
    # S2-A1: 색보정 핑거프린트 분산
    fingerprint_brightness_variance: float = 0.05  # ±5%
    fingerprint_saturation_variance: float = 0.08  # ±8%
    fingerprint_contrast_variance: float = 0.05    # ±5%
    enable_fingerprint_variance: bool = True
    # WO v12.0 Phase 6: 감정 기반 색보정 오버레이
    emotion_color_grade_enabled: bool = True
    # WO v12.0 Phase 4: 장면 전환 스타일
    transition_style: str = "auto"  # "auto" / "crossfade" / "hard_cut"
    fade_black_duration: float = 0.15  # Fade-to-black 삽입 시간 (Block 전환 시)
    # WO v12.0 Phase 3: Pop 스타일
    pop_style: str = "badge"  # "badge" / "classic"


@dataclass
class MarketingConfig:
    """CTA/Re-hook/Pop 마케팅 설정"""
    enable_cta: bool = True
    cta_duration: float = 3.0
    cta_text: str = "프로필에서 확인하세요"
    cta_font_size: int = 64
    cta_y_position: int = 1550
    enable_urgency: bool = True   # WO v7.0: CTA 3단계 활성화 (urgency→action→trust)
    enable_trust: bool = True     # WO v7.0: CTA 3단계 활성화 (urgency→action→trust)
    cta_urgency_duration: float = 3.0
    cta_action_duration: float = 3.5
    cta_trust_duration: float = 3.5
    enable_cta_image_overlay: bool = True
    cta_overlay_config_path: str = field(default_factory=lambda: _resolve_path('cta_overlay_config_path'))
    enable_rehooks: bool = True
    enable_rehook_15s: bool = True
    enable_rehook_30s: bool = True
    enable_rehook_45s: bool = False
    rehook_timings: tuple = (9.0, 27.0)  # WO v7.0: 8-10초 이탈 방지 + Pop2 충돌 해소
    rehook_pop_overlap_threshold: float = 1.5
    pop_timings: tuple = (15.0, 32.5, 42.0)  # WO v7.0: Pop3 CTA 전 배치
    pop_duration: float = 1.5
    pop_image_duration: float = 2.0
    pop_image_delay_offset: float = 0.8
    pop_image_height: int = 960
    pop_image_position: str = "center"
    pop_y_positions: tuple = (750,)
    pop_match_threshold: int = 30


@dataclass
class HookConfig:
    """Hook 설정 (3-5초 도입부)"""
    hook_duration_min: float = 4.5
    hook_duration_max: float = 5.5
    hook_duration: float = 3.0
    enable_intro_sfx: bool = True
    intro_sfx_path: str = field(default_factory=lambda: _resolve_path('intro_sfx_path'))
    hook_pop_enabled: bool = False
    hook_pop_timings: tuple = (0.3, 1.2, 2.2)
    hook_semantic_matching: bool = True


@dataclass
class BrandingConfig:
    """로고/아웃트로 설정"""
    logo_height: int = 200
    logo_opacity: float = 0.75
    outro_visual_enabled: bool = True
    outro_visual_duration: float = 2.5
    outro_logo_scale: float = 0.2


@dataclass
class ScriptConfig:
    """스크립트 생성/검증 설정"""
    max_script_chars: int = 450
    max_body_segments: int = 6
    protected_segments: tuple = ('cta', 'loop_trigger', 'hook')
    enable_script_validation: bool = True
    script_validation_min_grade: str = 'S'
    script_validation_blocking: bool = False
    script_validation_require_s_grade: bool = True
    random_start_offsets: tuple = (3, 5, 6, 8)
    fallback_visual_duration: float = 5.0
    # S2-B4: 다음 편 예고 구간
    enable_next_preview: bool = True
    next_preview_duration: float = 2.0


# ============================================================================
# 2. PipelineConfig Facade (기존 API 100% 호환)
# ============================================================================

# 각 서브 config 클래스와 필드명 매핑 (한 번만 계산)
_SUB_CONFIG_CLASSES = [
    VideoEncodingConfig, AudioConfig, SubtitleConfig, TTSConfig,
    VisualEffectsConfig, MarketingConfig, HookConfig, BrandingConfig, ScriptConfig,
]

_FIELD_TO_SUB: dict = {}
for _cls in _SUB_CONFIG_CLASSES:
    for _f in _cls.__dataclass_fields__:
        _FIELD_TO_SUB[_f] = _cls.__name__


class PipelineConfig:
    """
    파이프라인 설정 Facade.

    기존 flat 접근과 새로운 그룹 접근 모두 지원:
        config.bgm_volume           # 기존 (backward compatible)
        config.audio.bgm_volume     # 새로운 (논리 그룹)
    """

    __slots__ = (
        'video', 'audio', 'subtitle', 'tts',
        'visual_effects', 'marketing', 'hook', 'branding', 'script',
    )

    def __init__(self, **kwargs):
        # 서브 config 초기화
        object.__setattr__(self, 'video', VideoEncodingConfig())
        object.__setattr__(self, 'audio', AudioConfig())
        object.__setattr__(self, 'subtitle', SubtitleConfig())
        object.__setattr__(self, 'tts', TTSConfig())
        object.__setattr__(self, 'visual_effects', VisualEffectsConfig())
        object.__setattr__(self, 'marketing', MarketingConfig())
        object.__setattr__(self, 'hook', HookConfig())
        object.__setattr__(self, 'branding', BrandingConfig())
        object.__setattr__(self, 'script', ScriptConfig())

        # kwargs를 적절한 서브 config에 배분
        for key, value in kwargs.items():
            self._set_field(key, value)

    def _sub_configs(self):
        """모든 서브 config 반환"""
        return (
            self.video, self.audio, self.subtitle, self.tts,
            self.visual_effects, self.marketing, self.hook,
            self.branding, self.script,
        )

    def _set_field(self, name: str, value):
        """필드를 적절한 서브 config에 설정"""
        for sub in self._sub_configs():
            if hasattr(sub, name):
                setattr(sub, name, value)
                return
        raise TypeError(f"PipelineConfig has no field '{name}'")

    def __getattr__(self, name: str):
        """서브 config에서 필드 검색 (backward compatibility)"""
        # __slots__에 정의된 서브 config 자체 접근은 여기 오지 않음
        for sub in (
            object.__getattribute__(self, 'video'),
            object.__getattribute__(self, 'audio'),
            object.__getattribute__(self, 'subtitle'),
            object.__getattribute__(self, 'tts'),
            object.__getattribute__(self, 'visual_effects'),
            object.__getattribute__(self, 'marketing'),
            object.__getattribute__(self, 'hook'),
            object.__getattribute__(self, 'branding'),
            object.__getattribute__(self, 'script'),
        ):
            try:
                return getattr(sub, name)
            except AttributeError:
                continue
        raise AttributeError(f"PipelineConfig has no attribute '{name}'")

    def __setattr__(self, name: str, value):
        """필드 설정을 적절한 서브 config에 위임"""
        if name in self.__slots__:
            object.__setattr__(self, name, value)
            return
        for sub in self._sub_configs():
            if hasattr(sub, name):
                setattr(sub, name, value)
                return
        raise AttributeError(f"PipelineConfig has no attribute '{name}'")

    def __repr__(self):
        return (
            f"PipelineConfig(\n"
            f"  video={self.video!r},\n"
            f"  audio={self.audio!r},\n"
            f"  subtitle={self.subtitle!r},\n"
            f"  tts={self.tts!r},\n"
            f"  visual_effects={self.visual_effects!r},\n"
            f"  marketing={self.marketing!r},\n"
            f"  hook={self.hook!r},\n"
            f"  branding={self.branding!r},\n"
            f"  script={self.script!r},\n"
            f")"
        )
