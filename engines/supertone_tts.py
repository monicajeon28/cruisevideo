#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Supertone TTS Engine - Real API + Mock Fallback

Phase 4: 실제 Supertone Play API 연결
- POST https://supertoneapi.com/v1/text-to-speech/{voice_id}
- Model: sona_speech_2_flash (23언어, 고속)
- 300자 초과 시 자동 분할 + 오디오 결합
- API 실패 시 Mock fallback (무음 오디오) 자동 전환
"""

import os
import re
import time
import random
import hashlib
import subprocess
import threading
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import requests
import logging

logger = logging.getLogger(__name__)


# ============================================================================
# Voice ID Mapping
# ============================================================================

# speaker name → 환경변수 키 매핑
VOICE_ENV_MAP = {
    "audrey": "SUPERTONE_VOICE_AUDREY",
    "juho": "SUPERTONE_VOICE_JUHO",
    "grace": "SUPERTONE_VOICE_GRACE",
    "flop": "SUPERTONE_VOICE_FLOP",
    "osman": "SUPERTONE_VOICE_OSMAN",
    "ppang": "SUPERTONE_VOICE_PPANG",
    "sangchul": "SUPERTONE_VOICE_SANGCHUL",
    "billy": "SUPERTONE_VOICE_BILLY",
    "yannom": "SUPERTONE_VOICE_YANNOM",
    "ariel": "SUPERTONE_VOICE_ARIEL",
    "bert": "SUPERTONE_VOICE_BERT",
    "dakota": "SUPERTONE_VOICE_DAKOTA",
    "dudumchi": "SUPERTONE_VOICE_DUDUMCHI",
}

# 기본 voice_id (환경변수 없을 때)
DEFAULT_VOICE_ID = "1f6b70f879da125bfec245"  # Audrey

# Supertone API 텍스트 최대 길이
MAX_TEXT_LENGTH = 300

# API 요청 간 최소 간격 (초) - Free tier 20 req/min = 3초 간격
MIN_REQUEST_INTERVAL = 3.0


class TTSResult:
    """TTS 합성 결과를 담는 클래스"""
    def __init__(self, success: bool, output_path: str, duration: float,
                 text: str, speaker: str, error: str = None, **kwargs):
        self.success = success
        self.output_path = output_path
        self.duration = duration
        self.text = text
        self.speaker = speaker
        self.error = error
        for key, value in kwargs.items():
            setattr(self, key, value)


class SupertoneTTS:
    """Supertone Play TTS API 클라이언트"""

    BASE_URL = "https://supertoneapi.com/v1"
    MODEL = "sona_speech_2_flash"
    LANGUAGE = "ko"
    OUTPUT_FORMAT = "mp3"
    CHARS_PER_SECOND = 4.2  # config.py chars_per_second와 동기화

    # Supertone API 안전 style 값 (voice_id/model 호환성 보장)
    # "neutral"과 "happy"만 사용 - surprise/sad/angry/fear/disgust는
    # 특정 voice_id+model 조합에서 HTTP 400 에러 발생 가능
    SAFE_STYLES = {"neutral", "happy"}

    # 한글/커스텀/영문 감정 → 안전 style 매핑
    # 긍정 감정 → "happy", 나머지 → None (neutral)
    EMOTION_STYLE_MAP = {
        # 한글 감정 - 긍정 → happy
        "공감": "happy",
        "동경": "happy",
        "따뜻함": "happy",
        "기대": "happy",
        # 한글 감정 - 중립/부정 → neutral (None)
        "안심": "neutral",
        "확신": "neutral",
        "놀라움": "neutral",
        "슬픔": "neutral",
        "분노": "neutral",
        "두려움": "neutral",
        "혐오": "neutral",
        # 영문 커스텀 감정 (CTA 등) → neutral
        "urgency": "neutral",
        "action": "neutral",
        "trust": "neutral",
        # 영문 긍정 → happy
        "warmth": "happy",
        "anticipation": "happy",
        # 영문 감정 - 안전하지 않은 style → neutral 매핑
        "surprise": "neutral",
        "sad": "neutral",
        "angry": "neutral",
        "fear": "neutral",
        "disgust": "neutral",
    }

    def __init__(self):
        self.api_key = os.environ.get("SUPERTONE_API_KEY", "")
        self.output_dir = Path("outputs/tts")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self._api_valid = bool(self.api_key)

        # Voice ID 캐시 (speaker → voice_id)
        self._voice_cache: Dict[str, str] = {}
        self._load_voice_ids()

        # Rate limiting (thread-safe)
        self._last_request_time = 0.0
        self._rate_lock = threading.Lock()

        # API 연속 실패 카운터 (5회 연속 실패 시 mock 전환)
        self._consecutive_failures = 0
        self._max_consecutive_failures = 5

        # S2-A2: 영상별 피치 변이 (세션 단위)
        self._session_pitch_offset: int = 0

        if self._api_valid:
            logger.info(f"[TTS] Supertone API initialized (model={self.MODEL}, voices={len(self._voice_cache)})")
        else:
            logger.warning("[TTS] Supertone API key not found - MOCK mode")

    def start_video_session(self, pitch_variance: int = 2, enable: bool = True) -> int:
        """영상 생성 세션 시작 - 피치 변이를 한 번 결정

        같은 영상 내 모든 TTS 세그먼트는 동일한 pitch_offset 사용.
        Args:
            pitch_variance: 최대 변이 반음 수 (±N, 최대 2)
            enable: 피치 변이 활성화 여부
        Returns:
            결정된 pitch_offset 값
        """
        if not enable:
            self._session_pitch_offset = 0
        else:
            variance = min(abs(pitch_variance), 2)  # ±2 반음 제한
            self._session_pitch_offset = random.randint(-variance, variance)
        logger.info(f"[TTS] Pitch variance applied: offset={self._session_pitch_offset}")
        return self._session_pitch_offset

    def _load_voice_ids(self):
        """환경변수에서 Voice ID 로드"""
        for speaker, env_key in VOICE_ENV_MAP.items():
            voice_id = os.environ.get(env_key, "")
            if voice_id:
                self._voice_cache[speaker] = voice_id

    def _get_voice_id(self, speaker: str) -> str:
        """speaker 이름 → voice_id 변환"""
        speaker_lower = speaker.lower().strip()

        # 캐시에서 조회
        if speaker_lower in self._voice_cache:
            return self._voice_cache[speaker_lower]

        # 환경변수 직접 조회
        env_key = f"SUPERTONE_VOICE_{speaker_lower.upper()}"
        voice_id = os.environ.get(env_key, "")
        if voice_id:
            self._voice_cache[speaker_lower] = voice_id
            return voice_id

        # 기본값 (Audrey)
        return DEFAULT_VOICE_ID

    def _resolve_style(self, style: Optional[str]) -> Optional[str]:
        """감정/스타일 값을 Supertone API 안전 style로 변환

        모든 감정명을 EMOTION_STYLE_MAP을 통해 "happy" 또는 None(neutral)로 매핑.
        surprise/sad/angry/fear/disgust 등은 voice_id에 따라 HTTP 400 발생 가능하므로
        SAFE_STYLES(neutral, happy)만 사용.

        Args:
            style: 원본 감정/스타일 값

        Returns:
            "happy" 또는 None (neutral)
        """
        if not style:
            return None

        style_lower = style.lower().strip()

        # 모든 style을 매핑 테이블로 변환 (SAFE_STYLES 직접 통과 불가)
        mapped = self.EMOTION_STYLE_MAP.get(style_lower) or self.EMOTION_STYLE_MAP.get(style)
        if mapped:
            return mapped if mapped != "neutral" else None

        # 매핑에 없는 경우: SAFE_STYLES 직접 확인
        if style_lower in self.SAFE_STYLES:
            return style_lower if style_lower != "neutral" else None

        # 매핑 실패 → neutral(None) 반환 + 경고
        logger.warning(f"[TTS] Unknown style '{style}' → fallback to neutral")
        return None

    def _rate_limit_wait(self):
        """Rate limit 준수를 위한 대기"""
        with self._rate_lock:
            now = time.monotonic()
            elapsed = now - self._last_request_time
            if elapsed < MIN_REQUEST_INTERVAL:
                wait_time = MIN_REQUEST_INTERVAL - elapsed
                time.sleep(wait_time)
            self._last_request_time = time.monotonic()

    def _split_text(self, text: str) -> List[str]:
        """
        300자 초과 텍스트를 문장 단위로 분할

        분할 우선순위: 마침표 > 물음표 > 느낌표 > 쉼표 > 강제 분할
        """
        if len(text) <= MAX_TEXT_LENGTH:
            return [text]

        chunks = []
        remaining = text

        while remaining:
            if len(remaining) <= MAX_TEXT_LENGTH:
                chunks.append(remaining)
                break

            # 300자 이내에서 문장 끝 찾기
            search_text = remaining[:MAX_TEXT_LENGTH]

            # 마침표/물음표/느낌표 기준 분할
            split_pos = -1
            for sep in [".", "다.", "요.", "까?", "죠?", "!", "?", ",", " "]:
                pos = search_text.rfind(sep)
                if pos > 0:
                    split_pos = pos + len(sep)
                    break

            # 분할점 없으면 강제 300자 분할
            if split_pos <= 0:
                split_pos = MAX_TEXT_LENGTH

            chunk = remaining[:split_pos].strip()
            if chunk:
                chunks.append(chunk)
            remaining = remaining[split_pos:].strip()

        return chunks

    def _call_api(
        self,
        text: str,
        voice_id: str,
        style: str = None,
        speed: float = 1.0,
        pitch_shift: int = 0,
    ) -> Tuple[Optional[bytes], float]:
        """
        Supertone TTS API 단일 호출

        Returns:
            (audio_bytes, duration) 또는 실패 시 (None, 0.0)
        """
        self._rate_limit_wait()

        url = f"{self.BASE_URL}/text-to-speech/{voice_id}"
        headers = {
            "x-sup-api-key": self.api_key,
            "Content-Type": "application/json",
        }

        body = {
            "text": text,
            "language": self.LANGUAGE,
            "model": self.MODEL,
            "output_format": self.OUTPUT_FORMAT,
        }

        # Voice settings
        voice_settings = {}
        if speed != 1.0:
            voice_settings["speed"] = max(0.5, min(2.0, speed))
        if pitch_shift != 0:
            voice_settings["pitch_shift"] = max(-24, min(24, pitch_shift))
        if voice_settings:
            body["voice_settings"] = voice_settings

        # Style (감정) - 한글/커스텀 감정을 API 유효 영문으로 변환
        resolved_style = self._resolve_style(style)
        if resolved_style:
            body["style"] = resolved_style

        try:
            response = requests.post(
                url,
                headers=headers,
                json=body,
                timeout=30,
            )

            if response.status_code == 200:
                # 성공: 바이너리 오디오 + X-Audio-Length 헤더
                audio_bytes = response.content
                duration = float(response.headers.get("X-Audio-Length", 0))

                self._consecutive_failures = 0
                return audio_bytes, duration

            # 에러 처리
            error_msg = f"HTTP {response.status_code}"
            try:
                error_detail = response.json()
                error_msg = f"HTTP {response.status_code}: {error_detail}"
            except (ValueError, KeyError):
                pass

            if response.status_code == 429:
                logger.warning("[TTS API] Rate limited - waiting 60s")
                time.sleep(60)
                return None, 0.0
            elif response.status_code == 402:
                logger.warning("[TTS API] Insufficient credits - switching to MOCK")
                self._api_valid = False
                return None, 0.0
            else:
                logger.error(f"[TTS API] Error: {error_msg}")
                self._consecutive_failures += 1
                return None, 0.0

        except requests.Timeout:
            logger.warning(f"[TTS API] Timeout for text: {text[:50]}...")
            self._consecutive_failures += 1
            return None, 0.0
        except requests.ConnectionError:
            logger.error("[TTS API] Connection error - switching to MOCK")
            self._api_valid = False
            return None, 0.0
        except requests.RequestException as e:
            logger.error(f"[TTS API] Request error: {e}")
            self._consecutive_failures += 1
            return None, 0.0

    def _concatenate_audio(self, audio_parts: List[bytes], output_path: Path) -> Tuple[bool, float]:
        """
        여러 오디오 바이트를 하나의 파일로 결합

        Returns:
            (success, total_duration)
        """
        if len(audio_parts) == 1:
            output_path.write_bytes(audio_parts[0])
            duration = self._get_audio_duration(output_path)
            return True, duration

        # 여러 파트: 임시 파일 저장 후 ffmpeg concat
        temp_files = []
        try:
            for i, audio_bytes in enumerate(audio_parts):
                temp_path = output_path.parent / f"_chunk_{i:02d}_{output_path.stem}.mp3"
                temp_path.write_bytes(audio_bytes)
                temp_files.append(temp_path)

            # concat list 생성
            concat_list = output_path.parent / f"_concat_{output_path.stem}.txt"
            with open(concat_list, "w", encoding="utf-8") as f:
                for tf in temp_files:
                    f.write(f"file '{tf}'\n")

            cmd = [
                "ffmpeg", "-y",
                "-f", "concat", "-safe", "0",
                "-i", str(concat_list),
                "-c", "copy",
                str(output_path),
            ]
            subprocess.run(cmd, check=True, capture_output=True, timeout=30)

            duration = self._get_audio_duration(output_path)
            return True, duration

        except (subprocess.SubprocessError, OSError) as e:
            logger.error(f"[TTS] Audio concat error: {e}")
            return False, 0.0
        finally:
            # 임시 파일 정리
            for tf in temp_files:
                tf.unlink(missing_ok=True)
            concat_list = output_path.parent / f"_concat_{output_path.stem}.txt"
            concat_list.unlink(missing_ok=True)

    def generate(self, text, voice="audrey", emotion="neutral", output_path=None):
        """호환성 래퍼 (구 인터페이스)"""
        result = self.synthesize(text=text, speaker=voice, style=emotion, output_path=output_path)
        return result.output_path if result.success else str(self.output_dir / "mock.mp3")

    def synthesize(
        self,
        text: str,
        speaker: str = "audrey",
        persona: str = None,
        speed: float = 1.0,
        pitch: int = 0,
        energy: int = 100,
        output_path: Optional[str] = None,
        style: str = None,
        auto_emotion: bool = False,
        **kwargs
    ) -> TTSResult:
        """
        TTS 합성 (실제 API + Mock fallback)

        API가 유효하면 Supertone API 호출, 실패 시 Mock으로 자동 전환.

        Args:
            text: 합성할 텍스트
            speaker: 화자 (audrey/juho 등)
            persona: 화자 (speaker와 동일, 호환성)
            speed: 속도 (0.5~2.0, 기본 1.0)
            pitch: 피치 조절 (-24~24)
            energy: 에너지 (무시, API 미지원)
            output_path: 출력 경로 (None이면 자동 생성)
            style: 감정/스타일 (neutral, happy, sad 등)
            auto_emotion: 자동 감정 분석 (무시)

        Returns:
            TTSResult 객체
        """
        # persona와 speaker 호환성 처리
        if persona:
            speaker = persona

        # 출력 경로 생성
        if output_path is None:
            text_hash = hashlib.sha256(text.encode()).hexdigest()[:8]
            ext = self.OUTPUT_FORMAT if self._api_valid else "wav"
            output_path = self.output_dir / f"tts_{speaker}_{text_hash}.{ext}"
        else:
            output_path = Path(output_path)

        output_path.parent.mkdir(parents=True, exist_ok=True)

        # 연속 실패 시 mock 전환
        if self._consecutive_failures >= self._max_consecutive_failures:
            logger.warning(f"[TTS] {self._consecutive_failures} consecutive failures - switching to MOCK")
            self._api_valid = False

        # S2-A2: 세션 피치 변이 적용
        effective_pitch = pitch + self._session_pitch_offset

        # ===== 실제 API 호출 =====
        if self._api_valid:
            result = self._synthesize_via_api(text, speaker, speed, effective_pitch, style, output_path)
            if result is not None:
                return result
            # API 실패 → Mock fallback
            logger.warning(f"[TTS] API failed for '{text[:30]}...' - falling back to MOCK")

        # ===== Mock fallback =====
        return self._synthesize_mock(text, speaker, speed, effective_pitch, style, output_path)

    def _synthesize_via_api(
        self,
        text: str,
        speaker: str,
        speed: float,
        pitch: int,
        style: str,
        output_path: Path,
    ) -> Optional[TTSResult]:
        """실제 Supertone API로 TTS 합성"""
        voice_id = self._get_voice_id(speaker)

        # 텍스트 분할 (300자 제한)
        chunks = self._split_text(text)

        audio_parts = []
        total_api_duration = 0.0

        for i, chunk in enumerate(chunks):
            audio_bytes, chunk_duration = self._call_api(
                text=chunk,
                voice_id=voice_id,
                style=style,
                speed=speed,
                pitch_shift=pitch,
            )
            if audio_bytes is None:
                return None  # API 실패 → caller가 mock fallback

            audio_parts.append(audio_bytes)
            total_api_duration += chunk_duration

            if len(chunks) > 1:
                logger.info(f"[TTS API] Chunk {i+1}/{len(chunks)}: {len(chunk)}자 → {chunk_duration:.2f}s")

        # 오디오 저장/결합
        success, measured_duration = self._concatenate_audio(audio_parts, output_path)
        if not success:
            return None

        # duration 결정: API 헤더 > ffprobe 측정 > 텍스트 추정
        duration = total_api_duration or measured_duration or (len(text) / self.CHARS_PER_SECOND)

        logger.info(f"[TTS API] {output_path.name} ({duration:.2f}s) speaker={speaker} style={style}")

        return TTSResult(
            success=True,
            output_path=str(output_path),
            duration=duration,
            text=text,
            speaker=speaker,
            speed=speed,
            pitch=pitch,
            style=style,
        )

    def _synthesize_mock(
        self,
        text: str,
        speaker: str,
        speed: float,
        pitch: int,
        style: str,
        output_path: Path,
    ) -> TTSResult:
        """Mock TTS (무음 오디오 생성)"""
        duration = len(text) / self.CHARS_PER_SECOND
        if speed != 1.0:
            duration = duration / speed

        cmd = [
            "ffmpeg",
            "-f", "lavfi",
            "-i", "anullsrc=r=44100:cl=mono",
            "-t", str(duration),
            "-y",
            str(output_path),
        ]

        try:
            subprocess.run(cmd, check=True, capture_output=True, text=True, timeout=30)
            logger.info(f"[MOCK TTS] {output_path.name} ({duration:.2f}s) speaker={speaker} style={style}")

            return TTSResult(
                success=True,
                output_path=str(output_path),
                duration=duration,
                text=text,
                speaker=speaker,
                speed=speed,
                pitch=pitch,
                style=style,
            )
        except (subprocess.SubprocessError, OSError) as e:
            logger.error(f"[MOCK TTS] Error: {e}")
            return TTSResult(
                success=False,
                output_path=str(output_path),
                duration=duration,
                text=text,
                speaker=speaker,
                error=str(e),
            )

    def predict_duration(self, text: str, language: str = 'ko') -> float:
        """
        텍스트로 duration 예측

        API가 유효하면 Supertone Predict Duration API 호출 (크레딧 무소비),
        실패 시 텍스트 길이 기반 추정.
        """
        # 빠른 로컬 추정 (API 호출 오버헤드 방지)
        estimated = len(text) / self.CHARS_PER_SECOND

        if not self._api_valid:
            return estimated

        # Predict Duration API는 크레딧 무소비이므로 호출 시도
        voice_id = self._get_voice_id("audrey")
        try:
            self._rate_limit_wait()
            url = f"{self.BASE_URL}/predict-duration/{voice_id}"
            headers = {
                "x-sup-api-key": self.api_key,
                "Content-Type": "application/json",
            }
            body = {
                "text": text[:MAX_TEXT_LENGTH],  # API 제한
                "language": language,
                "model": self.MODEL,
            }

            response = requests.post(url, headers=headers, json=body, timeout=10)
            if response.status_code == 200:
                data = response.json()
                api_duration = float(data.get("duration", 0))
                if api_duration > 0:
                    # 텍스트가 분할된 경우 비율로 추정
                    if len(text) > MAX_TEXT_LENGTH:
                        ratio = len(text) / len(text[:MAX_TEXT_LENGTH])
                        return api_duration * ratio
                    return api_duration
        except (requests.RequestException, ValueError, KeyError):
            pass

        return estimated

    def _get_audio_duration(self, audio_path: Path) -> float:
        """ffprobe로 오디오 파일 duration 추출"""
        try:
            cmd = [
                "ffprobe",
                "-v", "error",
                "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1",
                str(audio_path),
            ]
            result = subprocess.run(cmd, check=True, capture_output=True, text=True, timeout=10)
            return float(result.stdout.strip())
        except (subprocess.SubprocessError, OSError, ValueError) as e:
            logger.warning(f"[TTS] Duration extraction failed: {e}")
            return 0.0
