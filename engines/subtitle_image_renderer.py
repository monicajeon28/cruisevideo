#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Phase B-9 Subtitle Image Renderer

Renders Korean subtitles as transparent PNG images.
Used in FFmpeg rendering pipeline as image overlays.

Key Features:
- Transparent background (RGBA)
- Korean font support (Malgun Gothic Bold)
- 3px stroke effect
- Center alignment
- Custom positioning/sizing

Usage:
    from engines.subtitle_image_renderer import SubtitleImageRenderer

    renderer = SubtitleImageRenderer()
    renderer.render_to_file(
        "크루즈 여행의 모든 것",
        duration,
        timestamp,
        "temp/subtitle_001.png"
    )

Phase B-9 (2026-03-04):
- Initial implementation: PIL-based subtitle image rendering
- 5060 generation optimization (large text, strong stroke)
- Compatible with config.py settings

Author: Claude Code
"""

import os
import logging
from pathlib import Path
from typing import Tuple, Optional
from PIL import Image, ImageDraw, ImageFont

from video_pipeline.config import PipelineConfig


logger = logging.getLogger(__name__)


class SubtitleImageRenderer:
    """Renders subtitles as PNG images"""

    def __init__(self, config: Optional[PipelineConfig] = None):
        """
        Initialize subtitle image renderer.

        Args:
            config: Video configuration (optional)
        """
        self.config = config or PipelineConfig()

        # Image dimensions (1080x1920 for vertical video)
        self.width = 1080
        self.height = 1920

        # Font configuration (PathResolver SSOT — 디자인 폰트 우선)
        try:
            from path_resolver import get_paths
            self.font_path = get_paths().system_font_path
        except (ImportError, Exception):
            self.font_path = "C:/Windows/Fonts/malgunbd.ttf"

        # [FIX P0-3] config 참조 (하드코딩 제거, SSOT 확립)
        self.font_size = getattr(self.config, 'image_subtitle_font_size',
                                 getattr(self.config, 'subtitle_font_size', 80))
        self.stroke_width = getattr(self.config, 'image_subtitle_stroke_width',
                                     getattr(self.config, 'subtitle_stroke_width', 4))

        # Colors
        self.text_color = (255, 255, 255, 255)  # White RGBA
        self.stroke_color = (0, 0, 0, 255)  # Black RGBA
        self.bg_color = (0, 0, 0, 0)  # Transparent RGBA

        # Position (bottom center)
        self.text_y_position = self.height - 350  # 350px from bottom (YouTube Shorts safe area)

        # Background bar config
        self.bg_enabled = getattr(self.config, 'subtitle_bg_enabled', True)
        raw_opacity = getattr(self.config, 'subtitle_bg_opacity', 0.63)
        # Type safety: float 0.0-1.0 → int 0-255, int 0-255 사용 가능
        if isinstance(raw_opacity, float) and raw_opacity <= 1.0:
            self.bg_opacity = int(raw_opacity * 255)
        elif isinstance(raw_opacity, int) and raw_opacity <= 255:
            self.bg_opacity = raw_opacity
        else:
            self.bg_opacity = 160  # safe default (~0.63)
        self.bg_padding_x = getattr(self.config, 'subtitle_bg_padding', 30)
        self.bg_padding_y = 14

        # Load font
        try:
            self.font = ImageFont.truetype(self.font_path, self.font_size)
            logger.info(f"[OK] Loaded font: {self.font_path} (size {self.font_size})")
        except (OSError, ValueError) as e:
            logger.warning(f"[WARNING] Failed to load font {self.font_path}: {e}")
            self.font = ImageFont.load_default()

    def _wrap_text(self, text: str, font, max_width: int = 840, max_lines: int = 2) -> str:
        """Wrap text to fit within max_width, enforce max_lines.

        Korean text is wrapped at character level since word boundaries
        are less meaningful for layout purposes.

        Args:
            text: Raw subtitle text
            font: PIL ImageFont to measure with
            max_width: Maximum pixel width per line
            max_lines: Maximum number of lines (excess truncated with ellipsis)

        Returns:
            Wrapped text with newline separators
        """
        lines = []
        current_line = ""

        for char in text:
            test_line = current_line + char
            bbox = font.getbbox(test_line)
            width = bbox[2] - bbox[0]
            if width > max_width and current_line:
                lines.append(current_line)
                current_line = char
            else:
                current_line = test_line
        if current_line:
            lines.append(current_line)

        # Enforce max lines
        if len(lines) > max_lines:
            lines = lines[:max_lines]
            lines[-1] = lines[-1][:-1] + "\u2026"

        return "\n".join(lines)

    def render_subtitle(
        self,
        text: str,
        font_size: int = None,
        color: str = None,
    ) -> str:
        """
        Render subtitle text to a temp PNG and return the file path.

        Convenience method for FFmpegPipeline integration.
        Creates a unique temp file in the system temp directory.

        Args:
            text: Subtitle text to render
            font_size: Font size override (None = use config default)
            color: Text color name (None = white)

        Returns:
            str: Path to the rendered PNG file

        Raises:
            RuntimeError: If rendering fails
        """
        import tempfile
        import uuid

        # Generate unique temp path
        temp_dir = Path(tempfile.gettempdir()) / "cruise_subtitles"
        temp_dir.mkdir(parents=True, exist_ok=True)
        output_path = str(temp_dir / f"sub_{uuid.uuid4().hex[:8]}.png")

        # Apply font size override
        font = self.font
        if font_size and font_size != self.font_size:
            try:
                font = ImageFont.truetype(self.font_path, font_size)
            except (OSError, ValueError):
                font = self.font

        # Parse color
        text_color = self.text_color
        if color and isinstance(color, str):
            color_map = {
                'white': (255, 255, 255, 255),
                'yellow': (255, 255, 0, 255),
                'red': (255, 0, 0, 255),
                'green': (0, 255, 0, 255),
                'cyan': (0, 255, 255, 255),
            }
            text_color = color_map.get(color.lower(), self.text_color)
        elif color and isinstance(color, tuple):
            text_color = color

        try:
            img = Image.new("RGBA", (self.width, self.height), self.bg_color)
            draw = ImageDraw.Draw(img)

            # Wrap text to 2 lines max (좌우 120px 패딩 = 총 240px 여유)
            safe_width = self.width - 240  # 1080 - 240 = 840px
            wrapped = self._wrap_text(text, font, max_width=safe_width, max_lines=2)

            bbox = draw.multiline_textbbox(
                (0, 0), wrapped, font=font, stroke_width=self.stroke_width, align="center"
            )
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            text_x = self.width // 2
            text_y = self.text_y_position - text_height // 2

            # 반투명 배경 바 (가독성 향상)
            if self.bg_enabled:
                bg_left = text_x - text_width // 2 - self.bg_padding_x
                bg_top = text_y - self.bg_padding_y
                bg_right = text_x + text_width // 2 + self.bg_padding_x
                bg_bottom = text_y + text_height + self.bg_padding_y
                draw.rounded_rectangle(
                    [bg_left, bg_top, bg_right, bg_bottom],
                    radius=12,
                    fill=(0, 0, 0, self.bg_opacity),
                )

            draw.multiline_text(
                (text_x, text_y),
                wrapped,
                font=font,
                fill=text_color,
                anchor="ma",
                align="center",
                stroke_width=self.stroke_width,
                stroke_fill=self.stroke_color,
            )

            img.save(output_path, "PNG")
            logger.debug(f"[OK] render_subtitle: {text[:20]}... -> {Path(output_path).name}")
            return output_path

        except (OSError, ValueError, RuntimeError) as e:
            logger.error(f"[ERROR] render_subtitle failed: {e}")
            raise RuntimeError(f"Subtitle rendering failed: {e}") from e

    def render_to_file(
        self,
        text: str,
        duration: float,
        start_time: float,
        output_path: str,
    ) -> bool:
        """
        Render subtitle text to PNG file.

        Args:
            text: Subtitle text
            duration: Duration of subtitle display (seconds)
            start_time: Start time of subtitle (seconds)
            output_path: Path to save PNG file

        Returns:
            True if successful, False otherwise
        """
        try:
            # Create image with transparent background
            img = Image.new("RGBA", (self.width, self.height), self.bg_color)
            draw = ImageDraw.Draw(img)

            # Wrap text to 2 lines max
            wrapped = self._wrap_text(text, self.font, max_width=840, max_lines=2)

            # Get multiline text bounding box
            bbox = draw.multiline_textbbox(
                (0, 0), wrapped, font=self.font, stroke_width=self.stroke_width, align="center"
            )
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]

            # Calculate center position (vertically centered around text_y_position)
            text_x = self.width // 2
            text_y = self.text_y_position - text_height // 2

            # 반투명 배경 바 (가독성 향상)
            if self.bg_enabled:
                bg_left = text_x - text_width // 2 - self.bg_padding_x
                bg_top = text_y - self.bg_padding_y
                bg_right = text_x + text_width // 2 + self.bg_padding_x
                bg_bottom = text_y + text_height + self.bg_padding_y
                draw.rounded_rectangle(
                    [bg_left, bg_top, bg_right, bg_bottom],
                    radius=12,
                    fill=(0, 0, 0, self.bg_opacity),
                )

            # Draw text with stroke (outline)
            draw.multiline_text(
                (text_x, text_y),
                wrapped,
                font=self.font,
                fill=self.text_color,
                anchor="ma",
                align="center",
                stroke_width=self.stroke_width,
                stroke_fill=self.stroke_color,
            )

            # Save to file
            img.save(output_path, "PNG")

            logger.debug(
                f"[OK] Rendered subtitle: {text[:20]}... -> {Path(output_path).name} "
                f"({start_time:.1f}s-{start_time+duration:.1f}s)"
            )

            return True

        except (OSError, ValueError, RuntimeError) as e:
            logger.error(f"[ERROR] Failed to render subtitle to {output_path}: {e}")
            return False

    def get_ffmpeg_fade_filter(
        self,
        start_time: float,
        duration: float,
        fade_in: float = 0.2,
        fade_out: float = 0.2,
    ) -> str:
        """FFmpeg alpha fade 필터 문자열 반환 (WO v11.0 D-3)

        자막 PNG 오버레이에 Fade In/Out 애니메이션 적용.
        기존 PNG 렌더링 파이프라인과 호환.

        Args:
            start_time: 자막 시작 시간 (초)
            duration: 자막 표시 시간 (초)
            fade_in: Fade In 시간 (초, 기본 0.2)
            fade_out: Fade Out 시간 (초, 기본 0.2)

        Returns:
            FFmpeg filter 문자열 (overlay + fade alpha)
        """
        end_time = start_time + duration
        fade_out_start = end_time - fade_out

        # FFmpeg alpha expression: fade in + hold + fade out
        alpha_expr = (
            f"if(lt(t-{start_time:.2f},{fade_in:.2f}),"
            f"(t-{start_time:.2f})/{fade_in:.2f},"
            f"if(gt(t,{fade_out_start:.2f}),"
            f"({end_time:.2f}-t)/{fade_out:.2f},"
            f"1))"
        )

        return alpha_expr

    def get_pop_motion_filter(
        self,
        start_time: float,
        duration: float,
        scale_in: float = 0.3,
        pulse_period: float = 0.5,
        fade_out: float = 0.2,
    ) -> dict:
        """Pop 메시지 모션 필터 파라미터 반환 (WO v11.0 D-4)

        Pop 등장: Scale 0%→100% (scale_in 초)
        Pop 유지: 미세 펄스 (100%↔105%)
        Pop 퇴장: Fade Out

        Args:
            start_time: Pop 시작 시간 (초)
            duration: Pop 표시 시간 (초)
            scale_in: Scale In 시간 (초, 기본 0.3)
            pulse_period: 펄스 주기 (초, 기본 0.5)
            fade_out: Fade Out 시간 (초, 기본 0.2)

        Returns:
            dict with 'scale_expr' and 'alpha_expr' FFmpeg expressions
        """
        end_time = start_time + duration
        fade_out_start = end_time - fade_out

        # Scale expression: zoom in (0→1) + gentle pulse (1.0↔1.05)
        scale_expr = (
            f"if(lt(t-{start_time:.2f},{scale_in:.2f}),"
            f"(t-{start_time:.2f})/{scale_in:.2f},"
            f"1.0+0.05*sin(2*PI*(t-{start_time:.2f})/{pulse_period:.2f}))"
        )

        # Alpha expression: hold + fade out
        alpha_expr = (
            f"if(gt(t,{fade_out_start:.2f}),"
            f"({end_time:.2f}-t)/{fade_out:.2f},"
            f"1)"
        )

        return {
            "scale_expr": scale_expr,
            "alpha_expr": alpha_expr,
        }

    def render_batch(
        self,
        subtitles: list,
        output_dir: str,
    ) -> list:
        """
        Render multiple subtitles to PNG files.

        Args:
            subtitles: List of subtitle dicts with keys: text, start_time, duration
            output_dir: Directory to save PNG files

        Returns:
            List of tuples: (output_path, start_time, duration)
        """
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)

        rendered = []

        for i, subtitle in enumerate(subtitles):
            text = subtitle.get("text", "")
            start_time = subtitle.get("start_time", 0.0)
            duration = subtitle.get("duration", 2.0)

            # Generate output path
            output_path = os.path.join(output_dir, f"subtitle_{i:03d}.png")

            # Render
            success = self.render_to_file(text, duration, start_time, output_path)

            if success:
                rendered.append((output_path, start_time, duration))

        logger.info(f"[OK] Rendered {len(rendered)}/{len(subtitles)} subtitles to {output_dir}")

        return rendered

    def cleanup(self, output_dir: str):
        """
        Clean up rendered subtitle PNG files.

        Args:
            output_dir: Directory containing subtitle PNGs
        """
        try:
            for file in Path(output_dir).glob("subtitle_*.png"):
                file.unlink()

            logger.info(f"[OK] Cleaned up subtitle PNGs from {output_dir}")

        except OSError as e:
            logger.warning(f"[WARNING] Failed to cleanup {output_dir}: {e}")


# Export
__all__ = ["SubtitleImageRenderer"]
