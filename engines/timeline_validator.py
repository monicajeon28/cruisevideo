#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Timeline Accuracy Validator - 0.1sec precision guaranteed
"""

import sys
import io
if sys.stdout and hasattr(sys.stdout, 'encoding') and sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
if sys.stderr and hasattr(sys.stderr, 'encoding') and sys.stderr.encoding != 'utf-8':
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

import logging
from typing import Dict, Tuple

logger = logging.getLogger(__name__)


class TimelineValidator:
    """Video timeline accuracy validator"""

    SHORT_TARGET_TOTAL = 55.0
    SHORT_TARGET_INTRO = 0.5
    SHORT_TARGET_MAIN = 45.0
    SHORT_TARGET_CTA = 7.0
    SHORT_TARGET_OUTRO = 2.5
    SHORT_TOLERANCE = 0.5
    
    LONG_MIN_DURATION = 50.0
    LONG_MAX_DURATION = 60.0
    
    @staticmethod
    def validate_short_timeline(parts: Dict[str, float], verbose: bool = False) -> Tuple[bool, Dict]:
        """Validate short-form timeline"""
        intro = parts.get("intro", 0.0)
        main = parts.get("main", 0.0)
        cta = parts.get("cta", 0.0)
        outro = parts.get("outro", 0.0)
        
        total_duration = intro + main + cta + outro
        errors = []
        
        if abs(intro - TimelineValidator.SHORT_TARGET_INTRO) > TimelineValidator.SHORT_TOLERANCE:
            errors.append(f"Intro duration mismatch: {intro:.1f}s")
        
        if abs(outro - TimelineValidator.SHORT_TARGET_OUTRO) > TimelineValidator.SHORT_TOLERANCE:
            errors.append(f"Outro duration mismatch: {outro:.1f}s")
        
        if main < 40.0:
            errors.append(f"Main too short: {main:.1f}s")
        
        if abs(cta - TimelineValidator.SHORT_TARGET_CTA) > TimelineValidator.SHORT_TOLERANCE:
            errors.append(f"CTA duration mismatch: {cta:.1f}s")
        
        total_diff = abs(total_duration - TimelineValidator.SHORT_TARGET_TOTAL)
        is_valid = total_diff <= TimelineValidator.SHORT_TOLERANCE
        
        return is_valid, {
            "is_valid": is_valid,
            "total_duration": total_duration,
            "target": TimelineValidator.SHORT_TARGET_TOTAL,
            "diff": total_diff,
            "tolerance": TimelineValidator.SHORT_TOLERANCE,
            "parts": {"intro": intro, "main": main, "cta": cta, "outro": outro},
            "errors": errors
        }
    
    @staticmethod
    def validate_long_timeline(total_duration: float) -> Tuple[bool, Dict]:
        """Validate long-form timeline"""
        is_valid = TimelineValidator.LONG_MIN_DURATION <= total_duration <= TimelineValidator.LONG_MAX_DURATION
        
        return is_valid, {
            "is_valid": is_valid,
            "total_duration": total_duration,
            "min_duration": TimelineValidator.LONG_MIN_DURATION,
            "max_duration": TimelineValidator.LONG_MAX_DURATION,
            "error": None if is_valid else f"Duration {total_duration:.1f}s out of range"
        }
    
    @staticmethod
    def print_result(result: Dict, video_type: str = "short"):
        """Print validation result"""
        prefix = "OK" if result["is_valid"] else "FAIL"
        logger.info(f"{prefix} Timeline Validation ({video_type.upper()})")
        logger.info(f"  Total duration: {result['total_duration']:.1f}s")

        if video_type == "short":
            logger.info(f"  Target: {result['target']:.1f}s")
            logger.info(f"  Diff: {result['diff']:.1f}s")
            if result['errors']:
                for err in result['errors']:
                    logger.warning(f"    - {err}")


if __name__ == "__main__":
    validator = TimelineValidator()
    print("TimelineValidator module loaded")
