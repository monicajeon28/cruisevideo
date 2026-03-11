#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ColorCorrectionEngine - 색보정 시스템

기능:
- 시니어 시청자 맞춤 (너무 어둡거나 채도 높지 않게)
- 크루즈 여행 테마 (밝고 따뜻한 톤)
- numpy 기반 프레임 단위 처리
- FFmpeg 렌더링과 호환
- S2-A1: 핑거프린트 분산 (밝기/채도/대비 미세 변이)

성능 목표:
- 프레임 처리 numpy 사용
- 메모리 스트리밍 방식 (전체 로드 없음)
"""

import logging
import random
from enum import Enum
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional, Tuple

import numpy as np

try:
    from scipy.ndimage import uniform_filter
    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False

logger = logging.getLogger(__name__)


class ColorCorrectionPreset(Enum):
    """색보정 프리셋 (크루즈 여행 테마별)"""
    WARM_CRUISE = "warm_cruise"            # 따뜻한 크루즈 (일몰, 해변)
    COOL_CRUISE = "cool_cruise"            # 신선한 크루즈 (바다, 하늘)
    LUXURY_CRUISE = "luxury_cruise"        # 럭셔리 크루즈 (실내, 야경)
    SENIOR_FRIENDLY = "senior_friendly"    # 시니어 최적화 (기본값)
    COLOR_BLIND = "color_blind"            # 적록색약 최적화 (50대 남성 8%)
    NATURAL = "natural"                    # 자연스러운 보정
    NONE = "none"                          # 보정 없음


@dataclass
class ColorCorrectionSettings:
    """색보정 설정 (시니어 최적화 기본값)"""

    # 밝기/대비
    brightness: float = 0.0          # -1.0 ~ 1.0 (0 = 변화없음, 양수 = 살짝 밝게)
    contrast: float = 1.0            # 0.5 ~ 2.0 (1.0 = 변화없음, >1 = 약간 선명)

    # 채도
    saturation: float = 1.0          # 0.0 ~ 2.0 (1.0 = 변화없음, >1 = 약간 선명)

    # 색온도
    warmth: float = 0.0              # -1.0 ~ 1.0 (0 = 중립, 양수 = 따뜻함)
    tint: float = 0.0                # -1.0 ~ 1.0 (0 = 중립, 양수 = 마젠타)

    # 감마
    gamma: float = 1.0               # 0.1 ~ 3.0 (1.0 = 변화없음)

    # 하이라이트/섀도우
    highlights: float = 0.0          # -1.0 ~ 1.0 (0 = 변화없음, 음수 = 복구)
    shadows: float = 0.0             # -1.0 ~ 1.0 (0 = 변화없음, 양수 = 밝게)

    # 비네트 - 시니어에게는 비활성화 권장
    vignette_strength: float = 0.0   # 0.0 ~ 1.0 (0 = 없음)
    vignette_radius: float = 0.8     # 0.3 ~ 1.0 (중앙부터 효과 시작점)

    # 샤프닝 - 시니어 시력 고려
    sharpness: float = 0.0           # 0.0 ~ 2.0 (0.5 = 약간 선명)

    # LUT (3D-LUT) 파일 경로 (고급 색보정)
    lut_path: Optional[str] = None
    lut_strength: float = 1.0        # 0.0 ~ 1.0 (LUT 적용 강도)


# 프리셋 설정값
PRESET_SETTINGS: Dict[ColorCorrectionPreset, ColorCorrectionSettings] = {
    ColorCorrectionPreset.WARM_CRUISE: ColorCorrectionSettings(
        brightness=0.05,
        contrast=1.05,
        saturation=1.1,
        warmth=0.15,         # 따뜻한 톤
        gamma=1.0,
        highlights=-0.1,     # 하이라이트 살짝 억제
    ),
    ColorCorrectionPreset.COOL_CRUISE: ColorCorrectionSettings(
        brightness=0.03,
        contrast=1.05,
        saturation=1.05,
        warmth=-0.1,         # 시원한 톤
        tint=-0.05,          # 청록색 틴트
        gamma=1.0,
    ),
    ColorCorrectionPreset.LUXURY_CRUISE: ColorCorrectionSettings(
        brightness=0.02,
        contrast=1.1,
        saturation=0.95,     # 채도 약간 낮춤 (고급스러움)
        warmth=0.05,
        shadows=0.1,         # 약간 어두운 분위기
        vignette_strength=0.15,  # 살짝 비네트
    ),
    ColorCorrectionPreset.SENIOR_FRIENDLY: ColorCorrectionSettings(
        brightness=0.08,     # 살짝 밝게
        contrast=1.08,       # 약간 선명
        saturation=1.05,     # 약간 생동감
        warmth=0.05,         # 살짝 따뜻
        shadows=0.1,         # 어두운 부분 밝게
        sharpness=0.3,       # 선명도 향상
    ),
    ColorCorrectionPreset.COLOR_BLIND: ColorCorrectionSettings(
        brightness=0.1,      # 밝게 (색상 구분 보조)
        contrast=1.15,       # 높은 대비 (색상 경계 강조)
        saturation=1.1,      # 높은 채도 (색상 구분 용이)
        warmth=0.0,          # 중립 (색상 왜곡 방지)
        sharpness=0.5,       # 선명도 강화 (경계 구분)
    ),
    ColorCorrectionPreset.NATURAL: ColorCorrectionSettings(
        brightness=0.02,
        contrast=1.02,
        saturation=1.0,
        warmth=0.0,
    ),
    ColorCorrectionPreset.NONE: ColorCorrectionSettings(
        brightness=0.0,
        contrast=1.0,
        saturation=1.0,
        warmth=0.0,
        gamma=1.0,
    ),
}


class ColorCorrectionEngine:
    """
    색보정 엔진 (numpy 기반)

    MoviePy 클립에 적용 가능한 프레임 필터 생성
    시니어 시청자에게 최적화된 색보정
    """

    def __init__(self, settings: ColorCorrectionSettings = None):
        """
        Args:
            settings: 색보정 설정 (None이면 SENIOR_FRIENDLY 프리셋 사용)
        """
        self.settings = settings or PRESET_SETTINGS[ColorCorrectionPreset.SENIOR_FRIENDLY]
        self._lut_data = None

        if self.settings.lut_path:
            self._load_lut(self.settings.lut_path)

    # S2-A1: 핑거프린트 분산 ─────────────────────────────────
    _fingerprint_offsets: Dict[str, float] = {}

    def apply_fingerprint_variance(
        self,
        brightness_var: float = 0.05,
        saturation_var: float = 0.08,
        contrast_var: float = 0.05,
    ) -> Dict[str, float]:
        """영상별 밝기/채도/대비 미세 변이 적용 (S2-A1)

        각 영상 생성 세션마다 호출하여 고유 핑거프린트 생성.
        ±variance 범위 내에서 랜덤 오프셋을 적용.

        Args:
            brightness_var: 밝기 변이 범위 (0.05 = ±5%)
            saturation_var: 채도 변이 범위 (0.08 = ±8%)
            contrast_var: 대비 변이 범위 (0.05 = ±5%)

        Returns:
            적용된 오프셋 딕셔너리
        """
        b_offset = random.uniform(-brightness_var, brightness_var)
        s_offset = random.uniform(-saturation_var, saturation_var)
        c_offset = random.uniform(-contrast_var, contrast_var)

        self.settings.brightness += b_offset
        self.settings.saturation += s_offset
        self.settings.contrast += c_offset

        self._fingerprint_offsets = {
            "brightness": round(b_offset, 4),
            "saturation": round(s_offset, 4),
            "contrast": round(c_offset, 4),
        }

        logger.info(
            f"  [S2-A1] 핑거프린트 분산 적용: "
            f"밝기{b_offset:+.3f}, 채도{s_offset:+.3f}, 대비{c_offset:+.3f}"
        )
        return self._fingerprint_offsets

    @property
    def fingerprint_offsets(self) -> Dict[str, float]:
        return dict(self._fingerprint_offsets)

    # ────────────────────────────────────────────────────────

    @classmethod
    def from_preset(cls, preset: str = "senior_friendly") -> "ColorCorrectionEngine":
        """프리셋으로 엔진 생성"""
        try:
            preset_enum = ColorCorrectionPreset(preset)
        except ValueError:
            preset_enum = ColorCorrectionPreset.SENIOR_FRIENDLY
        return cls(settings=PRESET_SETTINGS.get(preset_enum))

    def _load_lut(self, lut_path: str) -> None:
        """LUT 파일 로드 (.cube 형식)"""
        try:
            with open(lut_path, 'r') as f:
                lines = f.readlines()

            size = 0
            data = []

            for line in lines:
                line = line.strip()
                if not line or line.startswith('#') or line.startswith('TITLE'):
                    continue
                if line.startswith('LUT_3D_SIZE'):
                    size = int(line.split()[-1])
                    continue
                parts = line.split()
                if len(parts) == 3:
                    data.append([float(x) for x in parts])

            if size > 0 and len(data) == size ** 3:
                self._lut_data = np.array(data).reshape(size, size, size, 3)
                logger.info(f"  LUT 로드 완료: {lut_path} ({size}x{size}x{size})")
            else:
                logger.warning(f"  LUT 파싱 실패: {lut_path}")
        except (OSError, ValueError) as e:
            logger.warning(f"  LUT 로드 실패: {e}")

    def create_filter(self) -> Callable[[np.ndarray], np.ndarray]:
        """MoviePy용 필터 함수 생성

        Returns:
            프레임(numpy array)을 받아 보정된 프레임을 반환하는 함수
        """
        s = self.settings

        def correct_frame(frame: np.ndarray) -> np.ndarray:
            """단일 프레임 색보정"""
            # float로 변환 (0-1 범위)
            img = frame.astype(np.float64) / 255.0

            # 1. 밝기 조정
            if s.brightness != 0:
                img = img + s.brightness

            # 2. 대비 조정
            if s.contrast != 1.0:
                img = (img - 0.5) * s.contrast + 0.5

            # 3. 감마 보정
            if s.gamma != 1.0:
                img = np.power(np.clip(img, 0, 1), 1.0 / s.gamma)

            # 4. 채도 조정 - RGB to HSV
            if s.saturation != 1.0:
                gray = 0.299 * img[:, :, 0] + 0.587 * img[:, :, 1] + 0.114 * img[:, :, 2]
                for c in range(3):
                    img[:, :, c] = gray + (img[:, :, c] - gray) * s.saturation

            # 5. 색온도 조정
            if s.warmth != 0:
                shift = s.warmth * 0.1
                img[:, :, 0] = img[:, :, 0] + shift   # R
                img[:, :, 2] = img[:, :, 2] - shift   # B

            # 6. 틴트 조정
            if s.tint != 0:
                shift = s.tint * 0.05
                img[:, :, 1] = img[:, :, 1] - shift   # G

            # 7. 하이라이트/섀도우 조정
            if s.highlights != 0 or s.shadows != 0:
                luma = 0.299 * img[:, :, 0] + 0.587 * img[:, :, 1] + 0.114 * img[:, :, 2]

                if s.shadows != 0:
                    shadow_mask = np.clip(1 - luma * 2, 0, 1)
                    for c in range(3):
                        img[:, :, c] = img[:, :, c] + shadow_mask * s.shadows * 0.3

                if s.highlights != 0:
                    highlight_mask = np.clip((luma - 0.5) * 2, 0, 1)
                    for c in range(3):
                        img[:, :, c] = img[:, :, c] + highlight_mask * s.highlights * 0.3

            # 8. 샤프닝
            if s.sharpness > 0 and HAS_SCIPY:
                blurred = uniform_filter(img, size=(3, 3, 1))
                img = img + s.sharpness * (img - blurred)

            # 9. 비네트 효과
            if s.vignette_strength > 0:
                h, w = img.shape[:2]
                cy, cx = h / 2, w / 2
                y_grid, x_grid = np.mgrid[0:h, 0:w]
                dist = np.sqrt((x_grid - cx) ** 2 + (y_grid - cy) ** 2)
                max_dist = np.sqrt(cx ** 2 + cy ** 2)
                dist = dist / max_dist
                mask = 1 - s.vignette_strength * np.clip(
                    (dist - s.vignette_radius) / (1 - s.vignette_radius), 0, 1
                ) ** 2
                img = img * mask[:, :, np.newaxis]

            # 10. LUT 적용 (있는 경우)
            if self._lut_data is not None:
                img = _apply_lut(img, self._lut_data, s.lut_strength)

            # 클리핑 및 uint8 변환
            return np.clip(img * 255, 0, 255).astype(np.uint8)

        return correct_frame

    def apply_to_clip(self, clip):
        """MoviePy 클립에 색보정 적용

        Args:
            clip: VideoClip 또는 ImageClip

        Returns:
            색보정된 클립
        """
        if self.is_identity():
            logger.info("색보정 없음 (NONE 프리셋)")
            return clip

        try:
            corrected = clip.image_transform(self.create_filter())
            logger.info(
                f"색보정 적용: brightness={self.settings.brightness:.2f}, "
                f"contrast={self.settings.contrast:.2f}, "
                f"saturation={self.settings.saturation:.2f}"
            )
            return corrected
        except Exception as e:
            logger.warning(f"색보정 적용 실패: {e}, 원본 반환")
            return clip

    def is_identity(self) -> bool:
        """보정이 필요 없는지 확인"""
        s = self.settings
        return (
            s.brightness == 0
            and s.contrast == 1.0
            and s.saturation == 1.0
            and s.warmth == 0
            and s.tint == 0
            and s.gamma == 1.0
            and s.highlights == 0
            and s.shadows == 0
            and s.vignette_strength == 0
            and s.sharpness == 0
            and s.lut_path is None
        )

    def summary(self) -> str:
        """현재 설정 요약 문자열 반환"""
        s = self.settings
        parts = []

        if s.brightness != 0:
            parts.append(f"밝기 {s.brightness:+.1%}")
        if s.contrast != 1.0:
            parts.append(f"대비 {s.contrast:.1%}")
        if s.saturation != 1.0:
            parts.append(f"채도 {s.saturation:.1%}")
        if s.warmth != 0:
            direction = "따뜻함" if s.warmth > 0 else "차가움"
            parts.append(f"온도 {direction} ({abs(s.warmth):.1%})")
        if s.gamma != 1.0:
            parts.append(f"감마 {s.gamma:.2f}")
        if s.sharpness > 0:
            parts.append(f"선명도 {s.sharpness:.1%}")

        return ", ".join(parts) if parts else "보정 없음"


def _apply_lut(img: np.ndarray, lut: np.ndarray, strength: float = 1.0) -> np.ndarray:
    """3D LUT 적용 (삼선형 보간)"""
    size = lut.shape[0]

    r_idx = np.clip(img[:, :, 0] * (size - 1), 0, size - 1)
    g_idx = np.clip(img[:, :, 1] * (size - 1), 0, size - 1)
    b_idx = np.clip(img[:, :, 2] * (size - 1), 0, size - 1)

    r0 = np.floor(r_idx).astype(int)
    g0 = np.floor(g_idx).astype(int)
    b0 = np.floor(b_idx).astype(int)

    r1 = np.minimum(r0 + 1, size - 1)
    g1 = np.minimum(g0 + 1, size - 1)
    b1 = np.minimum(b0 + 1, size - 1)

    rf = r_idx - r0
    gf = g_idx - g0
    bf = b_idx - b0

    # 삼선형 보간 (간략화)
    c000 = lut[r0, g0, b0]
    c100 = lut[r1, g0, b0]
    c010 = lut[r0, g1, b0]
    c001 = lut[r0, g0, b1]
    c110 = lut[r1, g1, b0]
    c101 = lut[r1, g0, b1]
    c011 = lut[r0, g1, b1]
    c111 = lut[r1, g1, b1]

    result = (
        c000 * (1 - rf[:, :, np.newaxis]) * (1 - gf[:, :, np.newaxis]) * (1 - bf[:, :, np.newaxis]) +
        c100 * rf[:, :, np.newaxis] * (1 - gf[:, :, np.newaxis]) * (1 - bf[:, :, np.newaxis]) +
        c010 * (1 - rf[:, :, np.newaxis]) * gf[:, :, np.newaxis] * (1 - bf[:, :, np.newaxis]) +
        c001 * (1 - rf[:, :, np.newaxis]) * (1 - gf[:, :, np.newaxis]) * bf[:, :, np.newaxis] +
        c110 * rf[:, :, np.newaxis] * gf[:, :, np.newaxis] * (1 - bf[:, :, np.newaxis]) +
        c101 * rf[:, :, np.newaxis] * (1 - gf[:, :, np.newaxis]) * bf[:, :, np.newaxis] +
        c011 * (1 - rf[:, :, np.newaxis]) * gf[:, :, np.newaxis] * bf[:, :, np.newaxis] +
        c111 * rf[:, :, np.newaxis] * gf[:, :, np.newaxis] * bf[:, :, np.newaxis]
    )

    # 원본과 LUT 결과 블렌딩
    return img * (1 - strength) + result * strength


def detect_preset(theme: str = None, keywords: List[str] = None) -> ColorCorrectionPreset:
    """테마/키워드 기반 자동 프리셋 감지"""
    if theme:
        theme_lower = theme.lower()

        if any(k in theme_lower for k in ("럭셔리", "프리미엄", "luxury", "야경")):
            return ColorCorrectionPreset.LUXURY_CRUISE
        if any(k in theme_lower for k in ("일몰", "sunset", "해변", "beach", "따뜻")):
            return ColorCorrectionPreset.WARM_CRUISE
        if any(k in theme_lower for k in ("바다", "ocean", "신선", "fresh", "하늘")):
            return ColorCorrectionPreset.COOL_CRUISE

    if keywords:
        kw_lower = " ".join(keywords).lower()

        warm_kw = ("sunset", "beach", "golden", "일몰", "해변", "황금")
        cool_kw = ("ocean", "sea", "sky", "바다", "파랑", "하늘")
        lux_kw = ("luxury", "premium", "night", "야경", "럭셔리", "고급")

        warm_score = sum(1 for k in warm_kw if k in kw_lower)
        cool_score = sum(1 for k in cool_kw if k in kw_lower)
        lux_score = sum(1 for k in lux_kw if k in kw_lower)

        if lux_score > warm_score and lux_score > cool_score:
            return ColorCorrectionPreset.LUXURY_CRUISE
        if warm_score > cool_score:
            return ColorCorrectionPreset.WARM_CRUISE
        if cool_score > warm_score:
            return ColorCorrectionPreset.COOL_CRUISE

    # 기본값: 시니어 친화적
    return ColorCorrectionPreset.SENIOR_FRIENDLY


def get_segment_engine(
    segment_type: str,
    theme: str = None
) -> ColorCorrectionEngine:
    """세그먼트 타입별 색보정 엔진 생성"""
    if segment_type == "hook":
        return ColorCorrectionEngine(ColorCorrectionSettings(
            brightness=0.1,
            contrast=1.1,
            saturation=1.1,
            warmth=0.05,
        ))

    if segment_type == "pop":
        return ColorCorrectionEngine(ColorCorrectionSettings(
            brightness=0.08,
            contrast=1.12,
            saturation=1.05,
        ))

    if segment_type == "cta":
        return ColorCorrectionEngine(ColorCorrectionSettings(
            brightness=0.05,
            contrast=1.05,
            saturation=1.0,
            warmth=0.03,
        ))

    # 기본: 테마 기반 또는 시니어 친화적
    preset = detect_preset(theme)
    return ColorCorrectionEngine.from_preset(preset.value)


# === 간편 함수형 API ===

def apply_color_correction(clip, preset: str = "senior_friendly", settings=None):
    """클립에 색보정 적용 (간편 함수)"""
    if settings:
        engine = ColorCorrectionEngine(settings)
    else:
        engine = ColorCorrectionEngine.from_preset(preset)
    return engine.apply_to_clip(clip)


def get_cruise_color_filter(warmth: float = 0.5) -> Callable:
    """크루즈 여행 최적화 색보정 필터 생성"""
    settings = ColorCorrectionSettings(
        brightness=0.05,
        contrast=1.05,
        saturation=1.0 + warmth * 0.1,
        warmth=warmth * 0.15 - 0.05,
        gamma=1.0,
        sharpness=0.3,
    )
    engine = ColorCorrectionEngine(settings)
    return engine.create_filter()


# === 배치 처리용 ===

class BatchColorCorrector:
    """배치 영상 처리용 색보정기"""

    def __init__(self, preset: str = "senior_friendly"):
        self.engine = ColorCorrectionEngine.from_preset(preset)
        self._filter = self.engine.create_filter()

    def apply(self, clip):
        """클립에 미리 생성된 필터 적용"""
        return clip.image_transform(self._filter)

    def batch_apply(self, clips: list, resources=None) -> list:
        """여러 클립에 색보정 일괄 적용"""
        results = []
        for clip in clips:
            corrected = self.apply(clip)
            if resources:
                resources.track(corrected)
            results.append(corrected)
        return results


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    print("=" * 60)
    print("ColorCorrectionEngine Validation")
    print("=" * 60)

    # 프리셋 확인
    for preset in ColorCorrectionPreset:
        engine = ColorCorrectionEngine.from_preset(preset.value)
        print(f"  {preset.value}: {engine.summary()}")

    print("\n자동 프리셋 감지:")
    print(f"  '야경' -> {detect_preset('야경').value}")
    print(f"  '바다', '하늘' -> {detect_preset(keywords=['바다', '하늘']).value}")
    print(f"  '일몰', '해변' -> {detect_preset(keywords=['일몰', '해변']).value}")

    # S2-A1 핑거프린트 테스트
    print("\n[S2-A1] 핑거프린트 분산 테스트:")
    engine = ColorCorrectionEngine.from_preset("senior_friendly")
    for i in range(3):
        offsets = engine.apply_fingerprint_variance()
        print(f"  Session {i+1}: {offsets}")
