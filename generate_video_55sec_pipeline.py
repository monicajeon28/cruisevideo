#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
55초 YouTube Shorts 영상 자동 생성 파이프라인

입력: Claude 스크립트 JSON
출력: 55초 MP4 영상 (1080x1920)
"""

import os
import sys
import json
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from dotenv import load_dotenv
import random
import gc
import re
import shutil
import tempfile
import traceback
import logging
# [FIX S1-1] Config 단일 소스 (video_pipeline/config.py)
from video_pipeline.config import PipelineConfig
# [EXE] PathResolver - 하드코딩 경로 제거
from path_resolver import get_paths

# [S2-4-4] 모듈 레벨 side effects → _setup_environment()로 이동
# TEMP_DIR은 상수로만 유지 (디렉토리 생성은 __init__에서)
TEMP_DIR = Path(os.environ.get('RENDER_TEMP_DIR', 'temp'))

# MoviePy (v2.x에서는 fx를 메서드로 사용)
from moviepy import (
    VideoFileClip, ImageClip, AudioFileClip,
    CompositeVideoClip, CompositeAudioClip,
    TextClip, ColorClip, concatenate_videoclips,
    concatenate_audioclips, vfx
)
from PIL import Image, ImageOps
import numpy as np

# Supertone TTS
from engines.supertone_tts import SupertoneTTS

# AssetMatcher (키워드 기반 에셋 매칭)
try:
    from src.utils.asset_matcher import AssetMatcher
except ImportError:
    logging.getLogger(__name__).warning("AssetMatcher import 실패 - 랜덤 선택 모드로 동작")
    AssetMatcher = None

# [S2-3-2] VisualEffects 분리 모듈
from pipeline_effects.visual_effects import VisualEffects
# [S2-3-3] AudioMixer 분리 모듈
from pipeline_render.audio_mixer import AudioMixer
# [S2-3-4] VisualLoader 분리 모듈
from pipeline_render.visual_loader import VisualLoader
# [S2-3-5] VideoComposer 분리 모듈
from pipeline_render.video_composer import VideoComposer

# [S2-4-4] load_dotenv는 __init__에서 호출 (모듈 레벨 제거)

# 로깅 설정
logger = logging.getLogger("Video55SecPipeline")
logger.setLevel(logging.INFO)
if not logger.handlers:
    # 콘솔 핸들러
    _handler = logging.StreamHandler()
    _handler.setFormatter(logging.Formatter('[%(levelname)s] %(message)s'))
    logger.addHandler(_handler)

    # [FIX] 파일 핸들러 추가 (배치 실행 시 로그 보존)
    try:
        from datetime import datetime
        _log_dir = get_paths().logs_dir
        _log_dir.mkdir(parents=True, exist_ok=True)
        _file_handler = logging.FileHandler(
            _log_dir / f"pipeline_{datetime.now():%Y%m%d_%H%M%S}.log",
            encoding='utf-8'
        )
        _file_handler.setFormatter(logging.Formatter(
            '[%(asctime)s] [%(levelname)s] %(message)s'
        ))
        logger.addHandler(_file_handler)
    except OSError as _e:
        logger.warning(f"로그 파일 생성 실패 (콘솔만 사용): {_e}")


# [FIX S1-1] 구버전 PipelineConfig 삭제됨 (60개 필드, 구버전)
# SSOT: video_pipeline/config.py PipelineConfig (200+ 필드, 최신)


class ResourceTracker:
    """MoviePy 클립 리소스 추적 및 안전한 해제

    MoviePy에서 VideoFileClip/AudioFileClip은 파일 핸들을 보유.
    subclipped() 등으로 생성된 자식 클립은 부모 데이터를 참조.
    부모를 먼저 close()하면 자식이 무효화됨.
    → 모든 클립을 추적하고 렌더링 완료 후 일괄 해제.
    """

    def __init__(self):
        self._clips: List = []

    def track(self, clip):
        """클립 등록 (생성 즉시 호출). 등록된 클립을 그대로 반환."""
        if clip is not None:
            self._clips.append(clip)
        return clip

    def close_all(self):
        """모든 등록된 클립 안전하게 해제 (역순: 자식 → 부모)"""
        for clip in reversed(self._clips):
            try:
                clip.close()
            except (OSError, AttributeError, RuntimeError):
                pass  # 정리 실패는 무시 (이중 close, 이미 해제된 리소스)
        self._clips.clear()
        gc.collect()

    def __del__(self):
        """GC 수거 시 미해제 리소스 안전망 (WO v7.0 Phase 5.2)"""
        # close_all()이 gc.collect() 호출 → __del__ 재귀 방지: 직접 정리
        for clip in reversed(self._clips):
            try:
                clip.close()
            except (OSError, AttributeError, RuntimeError):
                pass
        self._clips.clear()


class Video55SecPipeline:
    """55초 영상 자동 생성 파이프라인"""

    # [S2-4-3] Named constants (매직 넘버 제거)
    MIN_DISK_SPACE_MB = 500
    DEFAULT_PERSONA = 'grace'
    MAX_SHORTS_DURATION_WARNING = 58  # 초과 시 경고
    MIN_SHORTS_DURATION_WARNING = 52  # 미만 시 경고
    HOOK_MAX_TEXT_CHARS = 30
    HOOK_MAX_DURATION_WARNING = 3.5
    OUTRO_MAX_DURATION_WARNING = 3.0
    EMPTY_SEGMENT_DURATION = 0.5

    _env_initialized = False

    @classmethod
    def _setup_environment(cls):
        """[S2-4-4] 환경 설정 (모듈 레벨 side effects → 클래스 메서드)"""
        if cls._env_initialized:
            return
        cls._env_initialized = True

        # 임시 디렉토리 생성
        TEMP_DIR.mkdir(parents=True, exist_ok=True)
        os.environ['TMPDIR'] = str(TEMP_DIR)
        os.environ['TEMP'] = str(TEMP_DIR)
        os.environ['TMP'] = str(TEMP_DIR)

        # Windows 콘솔 인코딩
        if sys.platform == 'win32':
            import io
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
            sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

        # Path 설정
        sys.path.insert(0, str(Path(__file__).parent))

        # .env 로드
        load_dotenv(get_paths().env_file)

    def __init__(self, config: PipelineConfig = None):
        self._setup_environment()
        self.config = config or PipelineConfig()
        self.tts = SupertoneTTS()
        # S2-A2: 세션별 TTS 피치 변이 활성화
        self.tts.start_video_session(
            pitch_variance=getattr(self.config, 'fingerprint_pitch_variance', 2),
            enable=getattr(self.config, 'enable_pitch_variance', True),
        )
        self.assets_root = get_paths().assets_root
        self.output_root = get_paths().final_videos_dir
        self.output_root.mkdir(parents=True, exist_ok=True)
        self._resources = ResourceTracker()
        # [S2-3-2] VisualEffects 위임 객체
        self._visual_effects = VisualEffects(config=self.config, resources=self._resources)
        # [S2-3-3] AudioMixer 위임 객체 (sfx/bgm 경로는 아래에서 설정 후 갱신)
        self._audio_mixer = None  # _init_paths 이후 초기화

        # 자원 경로 (실제 로컬 경로)
        self.hook_videos = self.assets_root / "Footage" / "Hook"
        self.footage = self.assets_root / "Footage"
        self.videos = self.assets_root / "Footage"
        self.images = self.assets_root / "Image"
        self.bgm = self.assets_root / "Music"
        self.sfx = self.assets_root / "SoundFX"
        self.fonts = self.assets_root / "fonts"
        self.logo_path = self.assets_root / "Image" / "로고" / "크루즈닷로고투명.png"
        # [S2-3-3] AudioMixer 초기화 (sfx/bgm 경로 확정 후)
        self._audio_mixer = AudioMixer(
            config=self.config, resources=self._resources,
            sfx_dir=self.sfx, bgm_dir=self.bgm
        )

        # AssetMatcher 초기화 (키워드 기반 에셋 매칭)
        self.asset_matcher = None
        if AssetMatcher is not None:
            try:
                # AssetMatcher는 파라미터 없이 초기화 (내부적으로 ASSET_PATHS 사용)
                self.asset_matcher = AssetMatcher()
                logger.info("AssetMatcher 초기화 완료 (키워드 매칭 활성화)")
            except (ImportError, OSError, ValueError) as e:
                logger.warning(f"AssetMatcher 초기화 실패: {e} - 랜덤 선택 모드로 동작")

        # [S2-3-4] VisualLoader 초기화 (asset_matcher 확정 후)
        self._visual_loader = VisualLoader(
            config=self.config, resources=self._resources,
            visual_effects=self._visual_effects,
            hook_videos_dir=self.hook_videos,
            videos_dir=self.videos, images_dir=self.images,
            asset_matcher=self.asset_matcher
        )
        # [S2-3-5] VideoComposer 초기화
        self._video_composer = VideoComposer(
            config=self.config, resources=self._resources,
            visual_effects=self._visual_effects,
            fonts_dir=self.fonts, logo_path=self.logo_path,
            asset_matcher=self.asset_matcher
        )

    def _check_disk_space(self, required_mb: int = 500) -> bool:
        """렌더링 전 디스크 공간 검사 (MVP)

        Args:
            required_mb: 필요한 최소 여유 공간 (MB), 기본 500MB

        Returns:
            bool: 공간 충분하면 True

        Raises:
            IOError: 공간 부족 시
        """
        try:
            output_dir = self.output_root
            if not output_dir.exists():
                output_dir = get_paths().output_root

            usage = shutil.disk_usage(output_dir)
            free_mb = usage.free // (1024 * 1024)

            if free_mb < required_mb:
                raise IOError(f"디스크 공간 부족: {free_mb}MB 남음, 최소 {required_mb}MB 필요")

            logger.debug(f"  디스크 공간 확인: {free_mb}MB 사용 가능")
            return True

        except IOError:
            raise
        except (OSError, ValueError) as e:
            logger.warning(f"  디스크 공간 확인 실패 (계속 진행): {e}")
            return True

    def _extend_with_freeze(self, clip, target_duration: float):
        """클립을 freeze frame으로 target_duration까지 연장 [S2-3-2 위임]"""
        return self._visual_effects.extend_with_freeze(clip, target_duration)

    # ============================================================
    # S등급 시각 효과 메서드
    # ============================================================

    def _apply_ken_burns(self, clip, effect_type: str = "zoom_in", zoom_ratio: float = None):
        """Ken Burns 효과 적용 [S2-3-2 위임]"""
        return self._visual_effects.apply_ken_burns(clip, effect_type, zoom_ratio)

    # Ken Burns 효과 유형 순환 리스트 [S2-3-2: VisualEffects에서 참조]
    KEN_BURNS_CYCLE = VisualEffects.KEN_BURNS_CYCLE

    def _get_ken_burns_type(self, segment_index: int) -> str:
        """세그먼트 인덱스에 따라 Ken Burns 유형 순환 반환 [S2-3-2 위임]"""
        return self._visual_effects.KEN_BURNS_CYCLE[segment_index % len(self._visual_effects.KEN_BURNS_CYCLE)]

    def _apply_crossfade(self, clips: List, overlap: float = None):
        """클립 리스트에 크로스페이드 전환 적용 [S2-3-2 위임]"""
        return self._visual_effects.apply_crossfade(clips, overlap)

    # ============================================================
    # S등급 오디오 메서드
    # ============================================================

    def _create_ducked_bgm(self, bgm_clip, narration_segments, duck_level=None, fade_duration=None, base_volume=None):
        """나레이션 구간 BGM 볼륨 더킹 [S2-3-3 위임]"""
        return self._audio_mixer.create_ducked_bgm(bgm_clip, narration_segments, duck_level, fade_duration, base_volume)

    def _scale_to_fit(self, clip, target_width: int = 1080, target_height: int = 1920):
        """영상/이미지를 타겟 크기에 맞게 스케일 [S2-3-2 위임]"""
        return self._visual_effects.scale_to_fit(clip, target_width, target_height)

    def _load_image_safe(self, image_path: str, preserve_alpha: bool = False) -> ImageClip:
        """EXIF Orientation 보정 + 1080x1920 리사이즈 이미지 로드 [S2-3-2 위임]"""
        return self._visual_effects.load_image_safe(image_path, preserve_alpha)

    def generate_video_from_script(
        self,
        script_json_path: str,
        output_name: str = "output_55sec.mp4"
    ) -> str:
        """
        스크립트 JSON  55초 영상

        Args:
            script_json_path: Claude 생성 스크립트 JSON 경로
            output_name: 출력 파일명

        Returns:
            생성된 영상 파일 경로
        """
        # 매 영상마다 리소스 추적기 리셋 (안전한 순서: 새 인스턴스 먼저 생성)
        old_resources = getattr(self, '_resources', None)
        self._resources = ResourceTracker()  # 먼저 새 인스턴스 생성
        self._visual_effects._resources = self._resources  # [S2-3-2] 위임 객체 동기화
        self._audio_mixer._resources = self._resources  # [S2-3-3] AudioMixer 동기화
        self._visual_loader._resources = self._resources  # [S2-3-4] VisualLoader 동기화
        self._video_composer._resources = self._resources  # [S2-3-5] VideoComposer 동기화
        if old_resources:
            try:
                old_resources.close_all()
            except (OSError, AttributeError, RuntimeError) as e:
                logger.warning(f"  이전 리소스 해제 중 오류 (무시됨): {e}")

        # [FIX] 디스크 공간 사전 검사 (배치 실행 시 중요)
        self._check_disk_space(self.MIN_DISK_SPACE_MB)

        # S2-A1: 색보정 핑거프린트 분산 (영상별 밝기/채도/대비 미세 변이)
        if getattr(self.config, 'enable_fingerprint_variance', False):
            try:
                from engines.color_correction import ColorCorrectionEngine
                self._cc_engine = ColorCorrectionEngine.from_preset(
                    getattr(self.config, 'color_correction_preset', 'senior_friendly')
                )
                self._cc_engine.apply_fingerprint_variance(
                    brightness_var=getattr(self.config, 'fingerprint_brightness_variance', 0.05),
                    saturation_var=getattr(self.config, 'fingerprint_saturation_variance', 0.08),
                    contrast_var=getattr(self.config, 'fingerprint_contrast_variance', 0.05),
                )
            except (ImportError, Exception) as e:
                logger.warning(f"  [S2-A1] 핑거프린트 분산 실패 (무시): {e}")

        # S2-A2: TTS 피치 새 세션 시작 (영상마다 다른 피치)
        self.tts.start_video_session(
            pitch_variance=getattr(self.config, 'fingerprint_pitch_variance', 2),
            enable=getattr(self.config, 'enable_pitch_variance', True),
        )

        logger.info(f"{'='*80}")
        logger.info(f"55초 영상 생성 파이프라인 시작")
        logger.info(f"{'='*80}")

        # Step 1: 스크립트 로드
        script = self._load_script(script_json_path)

        # [Phase 2] 콘텐츠 구조 검증 및 권장사항
        self._validate_content_structure(script)

        # ===== speaker_persona 필드 자동 추가 =====
        narrators = script.get('narrators', {})
        default_persona = None

        # 독백형 나레이터
        if 'narrator' in narrators:
            default_persona = narrators['narrator'].get('persona', 'grace')

        # 대화형 나레이터 (A, B)
        narrator_personas = {}
        if 'A' in narrators:
            narrator_personas['A'] = narrators['A'].get('persona', 'grace')
        if 'B' in narrators:
            narrator_personas['B'] = narrators['B'].get('persona', 'jihoon')

        # 모든 세그먼트에 speaker_persona 추가
        for seg in script.get('segments', []):
            if seg.get('section') == 'hook':
                continue  # Hook은 원본 오디오 사용

            if 'speaker_persona' not in seg:
                speaker = seg.get('speaker', 'narrator')

                # 대화형 (A, B)
                if speaker in narrator_personas:
                    seg['speaker_persona'] = narrator_personas[speaker]
                # 독백형 (narrator)
                elif default_persona:
                    seg['speaker_persona'] = default_persona
                else:
                    seg['speaker_persona'] = self.DEFAULT_PERSONA

        logger.info("speaker_persona 필드 자동 추가 완료")
        # ===== 추가 끝 =====

        # Step 1.5: Hook duration 사전 확인 (TTS 생성 전 동기화 필수)
        logger.info("[Step 1.5/7] Hook duration 확인...")
        self._get_hook_duration(script)

        # Step 2: TTS 생성 (Supertone)
        logger.info("[Step 2/7] TTS 나레이션 생성...")
        tts_files, actual_durations = self._generate_tts(script)

        # Step 3: 자막 타이밍 계산 (95% 싱크)
        logger.info("[Step 3/7] 자막 타이밍 계산...")
        subtitles = self._calculate_subtitle_timing(script, actual_durations)

        # Step 4: 비주얼 로드 (이미지/영상 + Hook)
        logger.info("[Step 4/7] 비주얼 자원 로드...")
        visuals, hook_audio = self._load_visuals(script, actual_durations)

        # Step 5: 오디오 믹싱 (나레이션 + BGM + 효과음 + Hook 오디오)
        logger.info("[Step 5/7] 오디오 믹싱...")
        final_audio = self._mix_audio(tts_files, script, actual_durations, hook_audio)

        # Step 6: 영상 조합 (비주얼 + 자막)
        logger.info("[Step 6/7] 영상 조합...")
        final_video = self._compose_video(visuals, subtitles, final_audio, script)

        # Step 7: 렌더링 (55초 MP4)
        logger.info("[Step 7/7] 최종 렌더링...")
        output_path = self.output_root / output_name
        try:
            final_video.write_videofile(
                str(output_path),
                fps=self.config.fps,
                codec=self.config.codec,
                audio_codec=self.config.audio_codec,
                audio_bitrate=self.config.audio_bitrate,  # [Phase1] 192k
                preset=self.config.preset,
                bitrate=self.config.bitrate  # [Phase1] 6000k
            )

            logger.info(f"영상 생성 완료: {output_path}")
            logger.info(f"  길이: {final_video.duration:.2f}초")
            logger.info(f"  해상도: {self.config.width}x{self.config.height}")
        finally:
            # ResourceTracker로 모든 클립 일괄 해제 (역순: 자식→부모)
            self._resources.close_all()

            # [FIX] TTS 임시 파일 정리 (배치 실행 시 누적 방지)
            try:
                narration_temp = get_paths().narration_temp_dir
                if narration_temp.exists():
                    shutil.rmtree(narration_temp, ignore_errors=True)
                    logger.debug("TTS 임시 파일 정리 완료")
            except OSError as e:
                logger.warning(f"TTS 임시 파일 정리 실패 (무시됨): {e}")

            # [WO v7.0 Phase 5.2] Subtitle PNG 임시 파일 안전망 정리
            subtitle_temp = Path(tempfile.gettempdir()) / "cruise_subtitles"
            if subtitle_temp.exists():
                try:
                    shutil.rmtree(subtitle_temp, ignore_errors=True)
                except OSError:
                    pass

        return str(output_path)

    def _load_script(self, json_path: str) -> dict:
        """
        스크립트 JSON 로드 및 검증 (에러 처리 강화)

        Args:
            json_path: 스크립트 JSON 파일 경로

        Returns:
            검증된 스크립트 dict

        Raises:
            FileNotFoundError: 파일이 없는 경우
            ValueError: JSON 파싱 실패 또는 필수 필드 누락
            TypeError: 잘못된 데이터 타입
        """
        path = Path(json_path)

        # [FIX S1-4] Path Traversal 방어 (허용 디렉토리 외 접근 차단)
        ALLOWED_SCRIPT_DIRS = get_paths().get_allowed_script_dirs()
        resolved_path = Path(json_path).resolve()
        # [FIX S1-4b] is_relative_to() 사용 (startswith 우회 방지: D:/mabiz_evil/ 차단)
        if not any(resolved_path.is_relative_to(d) for d in ALLOWED_SCRIPT_DIRS):
            raise ValueError(f"[SECURITY] Script path outside allowed directories: {resolved_path}")

        if not path.exists():
            raise FileNotFoundError(f"스크립트 파일을 찾을 수 없습니다: {json_path}")

        try:
            with open(path, 'r', encoding='utf-8') as f:
                script = json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"스크립트 JSON 파싱 실패 ({json_path}): {e}")

        # [FIX P0-7] 입력 검증 추가 (런타임 에러 사전 방지)
        if not isinstance(script, dict):
            raise TypeError(f"script must be dict, got {type(script).__name__}")

        # 필수 필드 호환 (comprehensive_script_generator 출력 형식 지원)
        if 'theme' not in script:
            # metadata.topic 또는 title에서 theme 추출
            theme = (script.get('metadata', {}).get('topic', '')
                     or script.get('title', '크루즈 여행'))
            script['theme'] = theme

        required_keys = ['theme', 'segments']
        for key in required_keys:
            if key not in script:
                raise ValueError(f"script missing required key: '{key}'")

        # segments 타입 및 내용 검증
        if not isinstance(script.get('segments'), list):
            raise TypeError(f"script['segments'] must be list, got {type(script.get('segments')).__name__}")

        if len(script['segments']) == 0:
            raise ValueError("script['segments'] cannot be empty")

        # 각 세그먼트 필수 필드 검증 (section/segment_type, text)
        for i, seg in enumerate(script['segments']):
            if not isinstance(seg, dict):
                raise TypeError(f"script['segments'][{i}] must be dict, got {type(seg).__name__}")
            # segment_type → section 호환 (comprehensive_script_generator 출력)
            if 'section' not in seg and 'segment_type' in seg:
                st = seg['segment_type']
                if st == 'hook':
                    seg['section'] = 'hook'
                elif st in ('cta_urgency', 'cta_action', 'cta_trust', 'share_trigger', 'follow_cta'):
                    seg['section'] = 'outro'
                else:
                    seg['section'] = 'body'
            if 'section' not in seg:
                raise ValueError(f"script['segments'][{i}] missing 'section' field")
            if 'text' not in seg:
                raise ValueError(f"script['segments'][{i}] missing 'text' field")

        return script

    def _validate_content_structure(self, script: dict) -> None:
        """
        [Phase 2] 콘텐츠 구조 검증 및 S등급 권장사항 로깅

        55초 쇼츠 최적 구조:
        - Hook (2-3초): 충격적 문장, 가격 강조
        - Body (5개 세그먼트 권장): 정보 전달
        - CTA (2초): 팔로우/댓글 유도
        """
        segments = script.get('segments', [])

        # 섹션별 분류
        hook_segments = [s for s in segments if s.get('section') == 'hook']
        body_segments = [s for s in segments if s.get('section') == 'body']
        outro_segments = [s for s in segments if s.get('section') == 'outro']

        # 총 예상 시간 계산
        total_estimated = sum(s.get('duration', 5.0) for s in segments)

        logger.info(f"  [콘텐츠 구조 분석]")
        logger.info(f"    Hook: {len(hook_segments)}개, Body: {len(body_segments)}개, Outro: {len(outro_segments)}개")
        logger.info(f"    예상 총 시간: {total_estimated:.1f}초")

        # S등급 권장사항 검사
        warnings = []

        # 1. Body 세그먼트 수 검사 (5개 권장, 7개 초과 시 경고)
        if len(body_segments) > 6:
            warnings.append(f"Body 세그먼트 {len(body_segments)}개 → 5-6개로 축소 권장 (집중력 유지)")

        # 2. Hook 검사
        if hook_segments:
            hook_dur = hook_segments[0].get('duration', 3.0)
            hook_text = hook_segments[0].get('text', '')
            if hook_dur > self.HOOK_MAX_DURATION_WARNING:
                warnings.append(f"Hook {hook_dur}초 → 2-3초로 단축 권장")
            if len(hook_text) > self.HOOK_MAX_TEXT_CHARS:
                warnings.append(f"Hook 텍스트 {len(hook_text)}자 → 20자 이내 권장 (임팩트)")

        # 3. Outro/CTA 검사
        if outro_segments:
            outro_dur = outro_segments[0].get('duration', 4.0)
            if outro_dur > self.OUTRO_MAX_DURATION_WARNING:
                warnings.append(f"Outro {outro_dur}초 → 2-3초로 단축 권장")

        # 4. 총 시간 검사
        if total_estimated > self.MAX_SHORTS_DURATION_WARNING:
            warnings.append(f"총 시간 {total_estimated:.1f}초 → 55초 이내 권장 (쇼츠 최적)")

        # 경고 출력
        if warnings:
            logger.warning("  [S등급 권장사항]")
            for w in warnings:
                logger.warning(f"    - {w}")
        else:
            logger.info("  [S등급 구조 충족] 콘텐츠 구조 최적화됨")

    def _get_hook_duration(self, script: dict) -> float:
        """
        Hook duration 반환 (항상 config.hook_duration 사용, 기본 3초)

        어뷰징 방지를 위해 Hook은 고정 길이.
        [FIX S2-0-2] hook_dur 로컬 상수 → config 참조
        [FIX S2-0-3] config mutation 제거 (읽기만, 쓰기 없음)
        """
        logger.info(f"  Hook duration: {self.config.hook_duration}초 (고정)")
        return self.config.hook_duration

    def _generate_tts(self, script: dict) -> Tuple[List[Optional[str]], List[float]]:
        """
        Supertone TTS 생성 (Phase 3: ThreadPoolExecutor 병렬화)

        Returns:
            (tts_files: List[str], actual_durations: List[float])
        """
        from concurrent.futures import ThreadPoolExecutor, as_completed

        segments = script.get('segments', [])
        if not segments:
            logger.warning("스크립트에 segments가 없습니다")
            return [], []

        narration_temp = get_paths().narration_temp_dir
        narration_temp.mkdir(parents=True, exist_ok=True)

        api_available = self.tts._api_valid
        max_workers = min(self.config.async_tts_max_concurrent, len(segments))

        # 결과를 인덱스별로 저장할 배열 (순서 보장)
        tts_files = [None] * len(segments)
        actual_durations = [0.0] * len(segments)

        def _synthesize_one(idx: int, seg: dict):
            """단일 세그먼트 TTS 합성 (스레드 안전)"""
            # [WO v12.0 Phase 1] Hook도 TTS 생성 (0초부터 나레이션 재생)

            persona = seg.get('speaker_persona', 'grace')
            emotion = seg.get('emotion', 'neutral')
            text = seg.get('text', '')
            if not text:
                return idx, None, self.EMPTY_SEGMENT_DURATION

            output_path = narration_temp / f"segment_{idx:02d}_{emotion}.mp3"

            if api_available:
                result = self.tts.synthesize(
                    text=text,
                    persona=persona,
                    output_path=str(output_path),
                    style=emotion,
                    auto_emotion=True,
                )
                if result.success:
                    return idx, str(output_path), result.duration
                else:
                    predicted = self.tts.predict_duration(text, language='ko')
                    return idx, None, predicted
            else:
                predicted = self.tts.predict_duration(text, language='ko')
                return idx, None, predicted

        # 병렬 TTS 합성 (ThreadPoolExecutor)
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(_synthesize_one, i, seg): i
                for i, seg in enumerate(segments)
            }
            for future in as_completed(futures):
                try:
                    idx, file_path, duration = future.result()
                    tts_files[idx] = file_path
                    # [CRITICAL FIX] Hook TTS desync 방지: hook 세그먼트는
                    # config.hook_duration으로 클램핑하여 visual/audio/subtitle 싱크 유지
                    if idx < len(segments) and segments[idx].get('section') == 'hook':
                        clamped = min(duration, self.config.hook_duration)
                        if duration > self.config.hook_duration:
                            logger.info(
                                f"  Hook TTS 클램핑: {duration:.2f}초 → {clamped:.2f}초 "
                                f"(config.hook_duration={self.config.hook_duration}초)"
                            )
                        actual_durations[idx] = clamped
                    else:
                        actual_durations[idx] = duration
                except (OSError, RuntimeError, ValueError) as e:
                    failed_idx = futures.get(future, -1)
                    logger.error(f"  TTS 세그먼트 {failed_idx} 실패: {e}")
                    # tts_files[idx]는 None 유지, actual_durations[idx]는 predicted 유지

        # 로그 요약
        success_count = sum(1 for f in tts_files if f is not None)
        logger.info(
            f"  TTS 완료: {success_count}/{len(segments)}편 성공 "
            f"(workers={max_workers}, 병렬)"
        )

        return tts_files, actual_durations

    def _calculate_subtitle_timing(
        self,
        script: dict,
        actual_durations: List[float]
    ) -> List[Dict]:
        """
        자막 타이밍 계산 (95% 싱크)

        문장 단위로 계산, 단어별은 균등 분배 (추정)
        """
        subtitles = []
        cumulative_time = 0.0

        hook_dur = self.config.hook_duration

        for i, seg in enumerate(script.get('segments', [])):
            if seg.get('section') == 'hook':
                # Hook 자막 (실제 hook duration 사용)
                subtitles.append({
                    'text': seg.get('subtitle', ''),
                    'start': 0.0,
                    'end': hook_dur,
                    'duration': hook_dur,
                    'section': 'hook'
                })
                cumulative_time = hook_dur
                continue

            # TTS 실제 duration 사용 (IndexError 방지)
            duration = actual_durations[i] if i < len(actual_durations) else 3.0

            # 문장 자막 (KeyError 방지)
            subtitles.append({
                'text': seg.get('subtitle', seg.get('text', '')),
                'start': cumulative_time,
                'end': cumulative_time + duration,
                'duration': duration,
                'section': seg.get('section', 'body')
            })

            cumulative_time += duration

        # 총 길이 검증
        total_duration = cumulative_time
        logger.info(f"  총 길이 (조정 전): {total_duration:.2f}초")

        # Duration 초과 시 실제 속도 조정 (단순 경고가 아닌 실제 트리밍)
        target = self.config.target_duration  # 55.0
        max_dur = self.config.max_duration    # 58.0

        if total_duration > max_dur:
            # 속도 배율 계산: 전체를 target_duration에 맞춤
            speed_factor = total_duration / target
            logger.warning(
                f"  {total_duration:.1f}초 → {target:.1f}초 압축 "
                f"(속도 {speed_factor:.2f}x)"
            )

            # Hook을 제외한 body/outro 세그먼트의 duration을 비례 축소
            # Hook은 고정 길이이므로 조정하지 않음
            hook_total = sum(
                s['duration'] for s in subtitles if s.get('section') == 'hook'
            )
            non_hook_total = total_duration - hook_total
            available_for_non_hook = target - hook_total

            if non_hook_total > 0 and available_for_non_hook > 0:
                shrink_ratio = available_for_non_hook / non_hook_total
            else:
                shrink_ratio = target / total_duration

            # 자막 타이밍 재계산
            new_cumulative = 0.0
            for sub in subtitles:
                if sub.get('section') == 'hook':
                    sub['start'] = new_cumulative
                    sub['end'] = new_cumulative + sub['duration']
                    new_cumulative += sub['duration']
                else:
                    new_duration = sub['duration'] * shrink_ratio
                    sub['start'] = new_cumulative
                    sub['end'] = new_cumulative + new_duration
                    sub['duration'] = new_duration
                    new_cumulative += new_duration

            # actual_durations도 동기화 (visuals/audio에서 사용)
            for i, sub in enumerate(subtitles):
                if i < len(actual_durations):
                    actual_durations[i] = sub['duration']

            total_duration = new_cumulative
            logger.info(f"  총 길이 (조정 후): {total_duration:.2f}초")

        elif total_duration < self.MIN_SHORTS_DURATION_WARNING:
            logger.warning(f"{self.MIN_SHORTS_DURATION_WARNING}초 미만! 무음 추가 필요")
        else:
            logger.info(f"  {total_duration:.1f}초 → 55초 ±3초 이내 ✓")

        return subtitles

    def _load_visuals(self, script: dict, actual_durations: List[float]) -> tuple:
        """비주얼 자원 로드 (이미지/영상 + Hook) [S2-3-4 위임]"""
        return self._visual_loader.load_visuals(script, actual_durations)

    def _mix_audio(self, tts_files, script, actual_durations, hook_audio=None):
        """오디오 믹싱 (나레이션 + BGM + Pop + 아웃트로) [S2-3-3 위임]"""
        return self._audio_mixer.mix_audio(tts_files, script, actual_durations, hook_audio)

    def _compose_video(self, visuals, subtitles, audio, script):
        """비주얼 + 자막 + Pop + CTA + 로고 합성 [S2-3-5 위임]"""
        return self._video_composer.compose_video(visuals, subtitles, audio, script)

def create_sample_script() -> str:
    """테스트용 샘플 스크립트 생성"""
    sample_script = {
        "theme": "크루즈",
        "title": "발리 크루즈 여행 가이드",
        "segments": [
            {
                "section": "hook",
                "text": "발리 크루즈, 당신이 몰랐던 진짜 비밀!",
                "subtitle": "발리 크루즈 완전 정복",
                "duration": 3.0
            },
            {
                "section": "body",
                "text": "발리는 인도네시아에서 가장 아름다운 섬입니다.",
                "subtitle": "인도네시아 최고의 여행지",
                "speaker_persona": "grace",
                "emotion": "happy",
                "visual_path": "",
                "duration": 5.0
            },
            {
                "section": "body",
                "text": "크루즈로 즐기는 발리는 특별한 경험을 선사합니다.",
                "subtitle": "특별한 크루즈 여행",
                "speaker_persona": "grace",
                "emotion": "excited",
                "visual_path": "",
                "duration": 5.0
            },
            {
                "section": "body",
                "text": "최고의 여행 시기는 4월부터 10월까지입니다.",
                "subtitle": "건기 여행이 최고!",
                "speaker_persona": "grace",
                "emotion": "neutral",
                "visual_path": "",
                "duration": 5.0
            },
            {
                "section": "body",
                "text": "현지 음식과 문화를 즐길 수 있는 기회도 많습니다.",
                "subtitle": "음식과 문화 체험",
                "speaker_persona": "grace",
                "emotion": "happy",
                "visual_path": "",
                "duration": 5.0
            },
            {
                "section": "body",
                "text": "가격은 시즌에 따라 다르지만 합리적입니다.",
                "subtitle": "합리적인 가격",
                "speaker_persona": "grace",
                "emotion": "neutral",
                "visual_path": "",
                "duration": 4.0
            },
            {
                "section": "body",
                "text": "발리 크루즈, 지금 바로 예약하세요!",
                "subtitle": "지금 바로 예약!",
                "speaker_persona": "grace",
                "emotion": "excited",
                "visual_path": "",
                "duration": 4.0
            },
            {
                "section": "outro",
                "text": "더 많은 정보는 크루즈닷에서 확인하세요.",
                "subtitle": "크루즈닷에서 만나요!",
                "speaker_persona": "grace",
                "emotion": "neutral",
                "visual_path": "",
                "duration": 4.0
            }
        ]
    }

    # 샘플 스크립트 저장
    output_dir = get_paths().project_root / "outputs" / "test_scripts"
    output_dir.mkdir(parents=True, exist_ok=True)

    output_path = output_dir / "sample_bali_cruise_script.json"
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(sample_script, f, ensure_ascii=False, indent=2)

    logger.info(f"샘플 스크립트 생성: {output_path}")
    return str(output_path)


def main():
    """테스트 실행"""
    print("55초 영상 생성 파이프라인 테스트\n")

    # 샘플 스크립트 생성
    script_path = create_sample_script()

    # 파이프라인 실행
    pipeline = Video55SecPipeline()

    try:
        output_video = pipeline.generate_video_from_script(
            script_json_path=script_path,
            output_name="test_bali_cruise_55sec.mp4"
        )

        print(f"\n 완료: {output_video}")

    except Exception as e:
        print(f"\n 오류 발생: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
