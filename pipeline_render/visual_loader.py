"""
VisualLoader - 비주얼 자원 로드 모듈 (S2-3-4)

God Object 분리: generate_video_55sec_pipeline.py에서 추출.
Hook 영상, 이미지, 비디오 로드 + Ken Burns 적용.

Usage:
    from pipeline_render import VisualLoader

    loader = VisualLoader(config=config, resources=resources,
                          visual_effects=effects, ...)
    visual_clips, hook_audio = loader.load_visuals(script, actual_durations)
"""

import logging
import random
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from moviepy import VideoFileClip, ColorClip

logger = logging.getLogger(__name__)


class VisualLoader:
    """비주얼 자원 로드 처리기 (의존성 주입)"""

    def __init__(self, config, resources, visual_effects,
                 hook_videos_dir: Path, videos_dir: Path,
                 images_dir: Path, asset_matcher=None):
        """
        Args:
            config: PipelineConfig
            resources: ResourceTracker
            visual_effects: VisualEffects 인스턴스 (scale_to_fit, load_image_safe 등)
            hook_videos_dir: Hook 영상 디렉토리
            videos_dir: 비디오 디렉토리
            images_dir: 이미지 디렉토리
            asset_matcher: AssetMatcher 인스턴스 (None 가능)
        """
        self.config = config
        self._resources = resources
        self._effects = visual_effects
        self.hook_videos = hook_videos_dir
        self.videos = videos_dir
        self.images = images_dir
        self.asset_matcher = asset_matcher

    def _load_hook_clip(self, video_path: Optional[str] = None):
        """Hook 영상 로드 (중복 제거된 단일 메서드)

        Args:
            video_path: Hook 영상 경로 (None이면 랜덤 선택)

        Returns:
            tuple: (clip, source_path) - 클립과 원본 경로
        """
        hook_dur = self.config.hook_duration

        # 영상 경로 결정
        if video_path and Path(video_path).exists():
            target_path = Path(video_path)
        else:
            hook_files = list(self.hook_videos.glob("*.mp4"))
            if not hook_files:
                return None, None
            target_path = random.choice(hook_files)

        video = VideoFileClip(str(target_path))
        self._resources.track(video)
        if video.duration is None:
            logger.warning(f"  Hook 비디오 duration 없음 (손상됨): {target_path}")
            return None, target_path

        # 랜덤 시작점 계산
        max_start = max(0, video.duration - hook_dur)
        random_start = random.uniform(0, max_start) if max_start > 0 else 0
        end_time = min(random_start + hook_dur, video.duration)

        clip = video.subclipped(random_start, end_time)
        self._resources.track(clip)
        clip = clip.without_audio()
        self._resources.track(clip)

        # Hook이 짧으면 freeze frame 패딩
        if clip.duration < hook_dur:
            old_dur = clip.duration
            clip = self._effects.extend_with_freeze(clip, hook_dur)
            logger.info(f"  Hook 패딩: +{hook_dur - old_dur:.2f}초 freeze frame")

        logger.info(f"  Hook 로드: {target_path.name} "
                   f"(시작: {random_start:.1f}초, duration: {clip.duration:.1f}초, 오디오 제거)")
        return clip, target_path

    def _load_video_clip(self, video_path, duration: float):
        """비디오 클립 로드 + 스케일 + freeze 패딩

        Returns:
            clip or None
        """
        video_clip = VideoFileClip(str(video_path))
        self._resources.track(video_clip)
        if video_clip.duration is None:
            logger.warning(f"  비디오 duration 없음 (손상됨): {video_path}")
            return None
        clip_duration = max(0.1, min(duration, video_clip.duration))
        clip = video_clip.subclipped(0, clip_duration)
        self._resources.track(clip)

        clip = self._effects.scale_to_fit(clip, self.config.width, self.config.height)

        if clip.duration < duration:
            old_dur = clip.duration
            clip = self._effects.extend_with_freeze(clip, duration)
            logger.info(f"  비디오: {Path(video_path).name} ({clip_duration:.1f}초 + freeze {duration - old_dur:.1f}초)")
        else:
            logger.info(f"  비디오: {Path(video_path).name} ({clip_duration:.1f}초)")

        return clip

    def load_visuals(self, script: dict, actual_durations: List[float]) -> tuple:
        """비주얼 자원 로드 (이미지/영상 + Hook)

        Returns:
            tuple: (visual_clips, hook_audio)
        """
        visual_clips = []
        hook_audio = None
        hook_dur = self.config.hook_duration
        used_assets = set()  # Track used asset paths for deduplication

        # 스크립트 메타데이터에서 기항지+선박 키워드 추출 (최우선 매칭용)
        metadata = script.get('metadata', {})
        self._script_port = metadata.get('port', script.get('theme', ''))
        self._script_ship = metadata.get('ship', '')
        logger.info(f"  [비주얼] 스크립트 컨텍스트: 기항지={self._script_port}, 선박={self._script_ship}")

        for i, seg in enumerate(script.get('segments', [])):
            if seg.get('section') == 'hook':
                clip = self._load_hook_segment(seg, hook_dur)
                visual_clips.append(clip)
            else:
                clip, matched_path = self._load_content_segment(seg, i, actual_durations, used_assets)
                if matched_path:
                    used_assets.add(matched_path)
                visual_clips.append(clip)

        return (visual_clips, hook_audio)

    def _load_hook_segment(self, seg: dict, hook_dur: float):
        """Hook 세그먼트 로드"""
        hook_path = seg.get('hook_video_path', '')
        clip = None

        try:
            clip, _ = self._load_hook_clip(hook_path if hook_path else None)
        except (OSError, ValueError, RuntimeError) as e:
            logger.error(f"  Hook 영상 로드 실패: {e}")

        if clip is None:
            clip = ColorClip(
                size=(self.config.width, self.config.height),
                color=(0, 0, 0)
            ).with_duration(hook_dur)
            self._resources.track(clip)
            logger.info(f"  Hook: 컬러 배경 (영상 없음, {hook_dur}초)")

        # 1080x1920에 맞게 스케일
        w, h = clip.size
        if w != self.config.width or h != self.config.height:
            clip = self._effects.scale_to_fit(clip, self.config.width, self.config.height)

        return clip

    def _load_content_segment(self, seg: dict, i: int, actual_durations: List[float],
                              used_assets: set = None):
        """콘텐츠 세그먼트 로드 (이미지/영상)

        Phase 5: segment_type별 asset 우선순위 적용
        - pain_point/block1: 일반 이미지 (공감)
        - solution/block2: 크루즈 정보 사진 (해결)
        - value_proof/block3: 기항지 사진 (감동)
        - emotional_peak/block4: 후기 이미지 (증거)
        - cta_*: 후기/Trust 이미지
        - re-hook: 동적 비디오 우선

        Returns:
            tuple: (clip, matched_asset_path or None)
        """
        visual_path = seg.get('visual_path', '')
        duration = actual_durations[i] if i < len(actual_durations) else 3.0
        clip = None
        source_type = None
        matched_path = None

        # Phase 5: segment_type 기반 content_type 힌트 설정
        segment_type = seg.get('segment_type', seg.get('type', ''))
        content_type_hint = self._resolve_content_type_hint(segment_type)
        if content_type_hint:
            seg['_content_type_hint'] = content_type_hint

        # 1. 지정된 경로 사용
        if visual_path and Path(visual_path).exists():
            clip, source_type = self._load_from_path(visual_path, duration)
            if clip is not None:
                matched_path = str(Path(visual_path))

        # 2. 키워드 매칭 또는 랜덤 fallback
        if clip is None:
            clip, source_type, matched_path = self._load_with_matching(seg, duration, used_assets)

        # Ken Burns 효과
        if self.config.enable_ken_burns:
            is_image_source = (source_type == "image")
            should_apply_kb = is_image_source or not self.config.ken_burns_for_images_only

            if should_apply_kb and clip is not None:
                kb_cycle = self._effects.KEN_BURNS_CYCLE
                kb_type = kb_cycle[i % len(kb_cycle)]
                clip = self._effects.apply_ken_burns(clip, effect_type=kb_type)
                self._resources.track(clip)
                logger.info(f"  Ken Burns 적용: {kb_type}")

        # 최종 안전망
        if clip is None:
            logger.error(f"  [CRITICAL] 세그먼트 {i}: 모든 fallback 실패 - ColorClip 강제 생성")
            clip = ColorClip(
                size=(self.config.width, self.config.height),
                color=(30, 30, 30)
            ).with_duration(duration)
            self._resources.track(clip)

        return clip, matched_path

    def _load_from_path(self, visual_path: str, duration: float):
        """지정된 경로에서 클립 로드"""
        if visual_path.lower().endswith(('.mp4', '.mov', '.avi', '.mkv')):
            try:
                clip = self._load_video_clip(visual_path, duration)
                if clip is not None:
                    return clip, "video"
            except (OSError, ValueError, RuntimeError) as e:
                logger.error(f"  비디오 로드 실패 ({visual_path}): {e}")
                return None, None
        else:
            clip = self._effects.load_image_safe(visual_path).with_duration(duration)
            self._resources.track(clip)
            logger.info(f"  이미지 사용: {Path(visual_path).name}")
            return clip, "image"

        return None, None

    def _load_with_matching(self, seg: dict, duration: float, used_assets: set = None):
        """키워드 매칭 → 랜덤 비디오 → 랜덤 이미지 → 컬러 배경 fallback

        Returns:
            tuple: (clip, source_type, matched_path or None)
        """
        narration_text = seg.get('text', '')
        clip = None
        exclude = used_assets or set()

        # AssetMatcher 매칭 시도
        if self.asset_matcher is not None and narration_text:
            clip, matched_path = self._try_asset_matcher(seg, narration_text, duration, exclude_paths=exclude)
            if clip is not None:
                return clip, "video", matched_path

        # 랜덤 비디오
        if clip is None:
            clip = self._try_random_video(duration)
            if clip is not None:
                return clip, "video", None

        # 랜덤 이미지
        if clip is None:
            clip = self._try_random_image(duration)
            if clip is not None:
                return clip, "image", None

        # 컬러 배경
        clip = ColorClip(
            size=(self.config.width, self.config.height),
            color=(30, 30, 30)
        ).with_duration(duration)
        self._resources.track(clip)
        logger.info("  컬러 배경 사용")
        return clip, "color", None

    def _resolve_content_type_hint(self, segment_type: str) -> Optional[str]:
        """Phase 5: segment_type → AssetMatcher content_type 매핑

        Returns:
            content_type 힌트 (Hook/CTA/Body/Trust) 또는 None
        """
        mapping = {
            "block1": "Body",
            "block2": "Body",
            "block3": "Body",
            "block4": "Trust",
            "re-hook": "Hook",
            "rehook": "Hook",
            "re_hook": "Hook",
            "cta_urgency": "CTA",
            "cta_action": "CTA",
            "cta_trust": "CTA",
        }
        return mapping.get(segment_type)

    def _try_asset_matcher(self, seg: dict, narration_text: str, duration: float,
                           exclude_paths: set = None):
        """AssetMatcher로 매칭 시도 (Phase 5: segment_type 우선순위 적용)

        Returns:
            tuple: (clip, matched_path_str) or (None, None)
        """
        try:
            # [FIX S2-5] match_assets API 사용 (get_best_asset_v2 미존재)
            from engines.keyword_extraction.intelligent_keyword_extractor import extract_keywords
            kw_result = extract_keywords(narration_text) if narration_text else None
            keywords = (kw_result.primary + kw_result.english) if kw_result else []

            # 스크립트 기항지+선박 키워드를 최우선 삽입 (주제와 매칭되는 비주얼 보장)
            script_keywords = []
            if hasattr(self, '_script_port') and self._script_port:
                # 기항지명에서 개별 단어 추출 (예: "후쿠오카/부산" → ["후쿠오카", "부산"])
                for port_part in self._script_port.replace('/', ' ').replace(',', ' ').split():
                    port_part = port_part.strip()
                    if port_part and port_part not in script_keywords:
                        script_keywords.append(port_part)
            if hasattr(self, '_script_ship') and self._script_ship:
                ship_name = self._script_ship.strip()
                if ship_name and ship_name not in script_keywords:
                    script_keywords.append(ship_name)

            # 스크립트 키워드를 맨 앞에 배치 (매칭 우선순위 최상)
            keywords = script_keywords + [k for k in keywords if k not in script_keywords]

            # 기본 크루즈 키워드 보강
            if not keywords:
                keywords = ["크루즈", "여행"]
            else:
                for default_kw in ["크루즈", "cruise"]:
                    if default_kw not in keywords:
                        keywords.append(default_kw)

            # Phase 5: segment_type 기반 content_type 결정
            content_type_hint = seg.get('_content_type_hint')
            if content_type_hint:
                content_type = content_type_hint
            else:
                section = seg.get('section', 'Body')
                content_type = "Hook" if section == "hook" else "CTA" if section == "cta" else "Body"

            # Phase 5: re-hook은 비디오 우선, cta/trust는 이미지(후기) 우선
            segment_type = seg.get('segment_type', '')
            prefer_images = segment_type in ('cta_trust', 'cta_action', 'block4')
            allow_videos = segment_type not in ('cta_trust',)

            matches = self.asset_matcher.match_assets(
                keywords=keywords[:5],
                content_type=content_type,
                max_results=5,
                prefer_images=prefer_images,
                allow_videos=allow_videos,
                exclude_paths=exclude_paths,
            )

            # Filter out already-used assets
            if exclude_paths and matches:
                matches = [m for m in matches if str(m.path) not in exclude_paths]

            if matches and matches[0].path.exists():
                matched = matches[0]
                logger.info(f"  [AssetMatcher] 매칭 성공: {matched.path.name} (score={matched.score})")
                logger.info(f"    나레이션: \"{narration_text[:50]}...\"")
                # 이미지 vs 비디오 분기 로딩
                ext = matched.path.suffix.lower()
                if ext in ('.jpg', '.jpeg', '.png', '.webp'):
                    clip = self._effects.load_image_safe(str(matched.path)).with_duration(duration)
                    self._resources.track(clip)
                    clip = self._effects.scale_to_fit(clip, self.config.width, self.config.height)
                else:
                    clip = self._load_video_clip(str(matched.path), duration)
                return clip, str(matched.path)
        except (OSError, ValueError, RuntimeError, AttributeError) as e:
            logger.warning(f"  [AssetMatcher] 매칭 실패: {e} - 랜덤 fallback")
        return None, None

    def _try_random_video(self, duration: float):
        """랜덤 비디오 선택"""
        if not self.videos.exists():
            return None

        video_files = (list(self.videos.glob("*.mp4")) +
                      list(self.videos.glob("*.mov")) +
                      list(self.videos.glob("*.avi")) +
                      list(self.videos.glob("*.mkv")))

        if not video_files:
            return None

        random_video = random.choice(video_files)
        try:
            clip = self._load_video_clip(str(random_video), duration)
            return clip
        except (OSError, ValueError, RuntimeError) as e:
            logger.error(f"  랜덤 비디오 로드 실패: {e}")
            return None

    def _try_random_image(self, duration: float):
        """랜덤 이미지 선택"""
        if not self.images.exists():
            return None

        image_files = list(self.images.glob("**/*.jpg")) + list(self.images.glob("**/*.png"))
        if not image_files:
            return None

        random_image = random.choice(image_files)
        clip = self._effects.load_image_safe(str(random_image)).with_duration(duration)
        self._resources.track(clip)
        logger.info(f"  랜덤 이미지: {random_image.name}")
        return clip
