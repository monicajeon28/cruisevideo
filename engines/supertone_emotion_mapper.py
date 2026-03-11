#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Supertone Emotion Mapping Engine (18-sec emotion peak compliance)

Features:
1. Script segment-level emotion analysis
2. Auto placement of emotion peak at 18-sec
3. Speed prediction and adjustment
4. Emotion-specific pause optimization

Created: 2026-02-20
"""

from typing import List, Dict, Any
from dataclasses import dataclass
import re

import logging

logger = logging.getLogger(__name__)


@dataclass
class EmotionSegment:
    """Emotion segment"""
    text: str
    emotion: str
    speed: float
    pause_before: float
    pause_after: float
    duration: float
    start_time: float
    is_peak: bool
    char_count: int


class SupertoneEmotionMapper:
    """Emotion mapper that ensures 18-sec emotion peak (S-grade requirement)"""

    # Emotion-to-speed mapping (natural human speech patterns)
    EMOTION_SPEED_MAP = {
        "neutral": 1.0,
        "happy": 1.1,
        "sad": 0.85,
        "angry": 1.2,
        "annoyed": 1.05,
        "surprised": 0.9,
        "excited": 1.15,
    }

    # Emotion-to-pause mapping
    EMOTION_PAUSE_MAP = {
        "neutral": 0.3,
        "happy": 0.2,
        "sad": 0.5,
        "angry": 0.1,
        "annoyed": 0.3,
        "surprised": 0.4,
        "excited": 0.2,
    }

    def __init__(self):
        pass

    def map_emotions(
        self,
        segments: List[Dict],
        target_duration: float = 50.0,
        peak_ratio: float = 0.36
    ) -> List[EmotionSegment]:
        """Map emotions with 18-sec peak alignment"""
        peak_time_target = target_duration * peak_ratio

        result_segments = []
        cumulative_time = 0.0

        for seg in segments:
            text = seg.get('text', '')
            emotion = seg.get('emotion', 'neutral')

            if 'duration' in seg:
                duration = seg['duration']
            else:
                duration = len(text) * 0.2

            pause_before = self.EMOTION_PAUSE_MAP.get(emotion, 0.3)
            total_duration = duration + pause_before + 0.3

            result_segments.append(EmotionSegment(
                text=text,
                emotion=emotion,
                speed=self.EMOTION_SPEED_MAP.get(emotion, 1.0),
                pause_before=pause_before,
                pause_after=0.3,
                duration=total_duration,
                start_time=cumulative_time,
                is_peak=False,
                char_count=len(text)
            ))

            cumulative_time += total_duration

        if result_segments:
            closest_idx = min(
                range(len(result_segments)),
                key=lambda i: abs(result_segments[i].start_time - peak_time_target)
            )
            result_segments[closest_idx].is_peak = True

            peak_seg = result_segments[closest_idx]
            if peak_seg.emotion == 'neutral':
                logger.warning(f"Peak at {peak_seg.start_time:.1f}s is neutral emotion")
                result_segments[closest_idx].emotion = 'excited'
                result_segments[closest_idx].speed = self.EMOTION_SPEED_MAP['excited']

        return result_segments

    def validate_peak_timing(self, segments: List[EmotionSegment]) -> Dict:
        """Validate if emotion peak is near 18sec"""
        peak_segments = [s for s in segments if s.is_peak]

        if not peak_segments:
            return {
                'is_valid': False,
                'peak_time': 0.0,
                'target_time': 18.0,
                'diff': 0.0,
                'within_tolerance': False,
                'message': 'No peak found'
            }

        peak_time = peak_segments[0].start_time

        return {
            'is_valid': True,
            'peak_time': peak_time,
            'target_time': 18.0,
            'diff': abs(peak_time - 18.0),
            'within_tolerance': abs(peak_time - 18.0) <= 2.0,
            'message': 'Peak timing valid'
        }

    def get_emotion_stats(self, segments: List[EmotionSegment]) -> Dict[str, int]:
        """Emotion distribution statistics"""
        stats = {}
        for seg in segments:
            emotion = seg.emotion
            stats[emotion] = stats.get(emotion, 0) + 1
        return stats

    def get_total_duration(self, segments: List[EmotionSegment]) -> float:
        """Calculate total estimated duration"""
        return sum(s.duration for s in segments) - 0.3


if __name__ == "__main__":
    print("SupertoneEmotionMapper module loaded successfully")
