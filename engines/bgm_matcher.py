#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
BGM Matcher - Phase 28 FIX-2 + FIX-8B 완전 재구축

**주요 기능**:
1. 블랙리스트 강제 필터링 (수면곡/명상곡 완전 차단)
2. 우선 선택 키워드 (travel/upbeat/adventure/inspiring/positive)
3. 감정 곡선 5구간 매칭 (0-10s, 10-25s, 25-40s, 40-50s, 50-55s)
4. Content Type별 BGM 자동 매칭
5. Music → Music_Backup 폴백 시스템

**입력 소스**:
- Primary: D:\AntiGravity\Assets\Music\*.mp3
- Metadata: D:\AntiGravity\Assets\Music\bgm_metadata.json
- Backup: D:\AntiGravity\Assets\Music_Backup\*.mp3

**Phase 28 개선**:
- FIX-2: BGM 수면곡 제외 + travel/upbeat 우선
- FIX-8B: Music_Backup 폴백 연동
"""

import json
import logging
import random
import re
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

# 로깅 설정
logger = logging.getLogger(__name__)


class BGMMatcher:
    """BGM 자동 매칭 엔진 - Phase 28 완전 재구축"""

    def __init__(self, music_root: str = None):
        """
        BGM Matcher 초기화

        Args:
            music_root: BGM 루트 디렉토리 (None이면 PathResolver에서 해결)
        """
        if music_root is None:
            try:
                from path_resolver import get_paths
                music_root = str(get_paths().music_dir)
            except (ImportError, Exception):
                music_root = "D:/AntiGravity/Assets/Music"
        self.music_root = Path(music_root)
        self.backup_root = Path(music_root.replace("Music", "Music_Backup"))
        self.metadata_path = self.music_root / "bgm_metadata.json"

        # 메타데이터 로드
        self.metadata = self._load_metadata()

        # 블랙리스트 (절대 사용 금지)
        self.blacklist_keywords = {
            "somnia", "sleep", "lullaby", "meditation", "zen",
            "ambient", "drone", "dark", "sad", "melancholy",
            "slow", "mellow", "dreamy", "hypnotic", "trance",
            "chill", "lounge", "downtempo", "ethereal", "mystical"
        }

        # 우선 선택 키워드 (travel/upbeat 우선)
        self.priority_keywords = {
            "travel", "upbeat", "adventure", "inspiring", "positive",
            "energetic", "happy", "cheerful", "optimistic", "bright"
        }

        # 감정 곡선 5구간 키워드 매핑
        self.emotion_curve_keywords = {
            "0-10s": ["calm", "gentle", "soft", "peaceful", "soothing"],
            "10-25s": ["warm", "friendly", "conversational", "comfortable", "inviting"],
            "25-40s": ["inspiring", "uplifting", "hopeful", "motivating", "encouraging"],
            "40-50s": ["confident", "strong", "determined", "powerful", "bold"],
            "50-55s": ["peaceful", "resolved", "satisfied", "content", "serene"]
        }

        # Content Type별 BGM 키워드
        self.content_type_keywords = {
            "EDUCATION": ["corporate", "business", "informative", "professional", "clean"],
            "COMPARISON": ["analytical", "tech", "modern", "minimal", "focused"],
            "SOCIAL_PROOF": ["inspiring", "success", "achievement", "triumph", "proud"],
            "FEAR_RESOLUTION": ["calm", "confident", "reassuring", "stable", "secure"],
            "BUCKET_LIST": ["dreamy", "adventure", "epic", "cinematic", "grand"]
        }

        # 블랙리스트 정규식 컴파일
        self.blacklist_pattern = re.compile(
            r'\b(' + '|'.join(re.escape(kw) for kw in self.blacklist_keywords) + r')\b',
            re.IGNORECASE
        )

        logger.info(f"[BGM Matcher] 초기화 완료 (Primary: {self.music_root}, Backup: {self.backup_root})")

    def _load_metadata(self) -> Dict:
        """BGM 메타데이터 로드"""
        if not self.metadata_path.exists():
            logger.warning(f"[BGM Matcher] 메타데이터 없음: {self.metadata_path}")
            return {"bgm_by_mood": {}}

        try:
            with open(self.metadata_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            logger.info(f"[BGM Matcher] 메타데이터 로드 완료 (총 {data.get('total_files', 0)}개 파일)")
            return data
        except (OSError, json.JSONDecodeError, ValueError) as e:
            logger.error(f"[BGM Matcher] 메타데이터 로드 실패: {e}")
            return {"bgm_by_mood": {}}

    def _is_blacklisted(self, filename: str, keywords: List[str]) -> bool:
        """
        블랙리스트 체크 (파일명 + 키워드)

        Args:
            filename: 파일명
            keywords: 키워드 리스트

        Returns:
            블랙리스트 포함 여부
        """
        # 파일명 체크
        if self.blacklist_pattern.search(filename):
            return True

        # 키워드 체크
        for keyword in keywords:
            if keyword.lower() in self.blacklist_keywords:
                return True

        return False

    def _calculate_priority_score(self, keywords: List[str], target_keywords: Set[str]) -> int:
        """
        키워드 우선순위 점수 계산

        Args:
            keywords: BGM 키워드 리스트
            target_keywords: 타겟 키워드 집합

        Returns:
            우선순위 점수 (높을수록 우선)
        """
        score = 0

        # 우선 선택 키워드 매칭
        for keyword in keywords:
            if keyword.lower() in self.priority_keywords:
                score += 10

        # 타겟 키워드 매칭
        for keyword in keywords:
            if keyword.lower() in target_keywords:
                score += 5

        return score

    def _get_files_from_mood_folder(self, mood: str, target_keywords: Set[str]) -> List[Tuple[str, int]]:
        """
        특정 mood 폴더에서 BGM 파일 가져오기

        Args:
            mood: mood 폴더명 (calm, travel, upbeat, energetic 등)
            target_keywords: 타겟 키워드 집합

        Returns:
            (파일 경로, 우선순위 점수) 리스트
        """
        files = []

        # 메타데이터에서 해당 mood의 파일 가져오기
        mood_files = self.metadata.get("bgm_by_mood", {}).get(mood, [])

        for bgm_info in mood_files:
            filename = bgm_info.get("filename", "")
            keywords = bgm_info.get("keywords", [])
            path = bgm_info.get("path", "")

            # 블랙리스트 체크
            if self._is_blacklisted(filename, keywords):
                logger.debug(f"[BGM Matcher] 블랙리스트 필터링: {filename}")
                continue

            # 우선순위 점수 계산
            priority_score = self._calculate_priority_score(keywords, target_keywords)

            files.append((path, priority_score))

        return files

    def _select_from_folder(self, mood: str, target_keywords: Set[str]) -> Optional[str]:
        """
        특정 폴더에서 BGM 선택

        Args:
            mood: mood 폴더명
            target_keywords: 타겟 키워드 집합

        Returns:
            선택된 BGM 파일 경로 (없으면 None)
        """
        files = self._get_files_from_mood_folder(mood, target_keywords)

        if not files:
            return None

        # 점수 순 정렬
        files.sort(key=lambda x: x[1], reverse=True)

        # 상위 30% 중에서 랜덤 선택
        top_count = max(1, len(files) // 3)
        top_files = files[:top_count]

        # 가중치 랜덤 선택
        weights = [score for _, score in top_files]
        if sum(weights) == 0:
            selected = random.choice(top_files)[0]
        else:
            selected = random.choices(top_files, weights=weights, k=1)[0][0]

        logger.info(f"[BGM Matcher] 선택: {Path(selected).name} (폴더: {mood}, 점수: {dict(top_files).get(selected, 0)})")
        return selected

    def select_bgm_for_emotion_curve(self, section: str = "0-10s") -> Optional[str]:
        """
        감정 곡선 구간별 BGM 선택

        Args:
            section: 감정 곡선 구간 (0-10s, 10-25s, 25-40s, 40-50s, 50-55s)

        Returns:
            선택된 BGM 파일 경로
        """
        target_keywords = set(self.emotion_curve_keywords.get(section, []))

        # 우선순위 폴더 순서
        if section in ["0-10s", "50-55s"]:
            mood_priority = ["calm", "relaxing", "travel"]
        elif section in ["10-25s"]:
            mood_priority = ["travel", "calm", "upbeat"]
        elif section in ["25-40s"]:
            mood_priority = ["upbeat", "travel", "energetic"]
        else:  # 40-50s
            mood_priority = ["energetic", "upbeat", "travel"]

        # 우선순위 순서대로 시도
        for mood in mood_priority:
            result = self._select_from_folder(mood, target_keywords)
            if result:
                return result

        # 폴백: 전체 폴더에서 블랙리스트 제외하고 선택
        logger.warning(f"[BGM Matcher] 감정 곡선 {section} 매칭 실패, 폴백 시도")
        return self._select_fallback_bgm()

    def select_bgm_for_content_type(self, content_type: str) -> Optional[str]:
        """
        Content Type별 BGM 선택

        Args:
            content_type: EDUCATION, COMPARISON, SOCIAL_PROOF, FEAR_RESOLUTION, BUCKET_LIST

        Returns:
            선택된 BGM 파일 경로
        """
        target_keywords = set(self.content_type_keywords.get(content_type, []))

        # Content Type별 우선 폴더
        mood_priority_map = {
            "EDUCATION": ["calm", "travel", "upbeat"],
            "COMPARISON": ["upbeat", "energetic", "travel"],
            "SOCIAL_PROOF": ["upbeat", "energetic", "travel"],
            "FEAR_RESOLUTION": ["calm", "travel", "upbeat"],
            "BUCKET_LIST": ["travel", "upbeat", "energetic"]
        }

        mood_priority = mood_priority_map.get(content_type, ["travel", "upbeat", "calm"])

        # 우선순위 순서대로 시도
        for mood in mood_priority:
            result = self._select_from_folder(mood, target_keywords)
            if result:
                return result

        # 폴백
        logger.warning(f"[BGM Matcher] Content Type {content_type} 매칭 실패, 폴백 시도")
        return self._select_fallback_bgm()

    def select_bgm(
        self,
        theme: str = "크루즈",
        persona: str = "액티브시니어",
        content_type: Optional[str] = None,
        emotion_section: Optional[str] = None
    ) -> str:
        """
        테마/페르소나/Content Type 기반 BGM 자동 선택

        Args:
            theme: 테마 (크루즈, 힐링, 레저 등)
            persona: 페르소나 (액티브시니어, 신혼부부 등)
            content_type: Content Type (EDUCATION, COMPARISON 등)
            emotion_section: 감정 곡선 구간 (0-10s, 10-25s 등)

        Returns:
            선택된 BGM 파일 전체 경로

        Raises:
            RuntimeError: BGM 파일이 없을 때
        """
        logger.info(f"[BGM Matcher] 요청: theme={theme}, persona={persona}, content_type={content_type}, emotion_section={emotion_section}")

        # 1. Content Type 우선 매칭
        if content_type:
            result = self.select_bgm_for_content_type(content_type)
            if result:
                return result

        # 2. 감정 곡선 매칭
        if emotion_section:
            result = self.select_bgm_for_emotion_curve(emotion_section)
            if result:
                return result

        # 3. 테마 기반 폴백
        theme_mood_map = {
            "크루즈": "travel",
            "힐링": "calm",
            "레저": "upbeat",
            "음식": "upbeat",
            "여행": "travel",
            "허니문": "travel",
            "기항지": "travel",
            "불안해소": "calm",
            "선내시설": "upbeat"
        }

        mood = theme_mood_map.get(theme, "travel")
        result = self._select_from_folder(mood, set())
        if result:
            return result

        # 4. 최종 폴백
        return self._select_fallback_bgm()

    def _select_fallback_bgm(self) -> str:
        """
        폴백 BGM 선택 (블랙리스트 제외)

        Returns:
            선택된 BGM 파일 경로

        Raises:
            RuntimeError: BGM 파일이 없을 때
        """
        logger.warning("[BGM Matcher] 폴백 모드 진입 (전체 폴더 검색)")

        # Primary 폴더에서 시도
        primary_result = self._select_from_primary_folders()
        if primary_result:
            return primary_result

        # Backup 폴더에서 시도
        backup_result = self._select_from_backup_folders()
        if backup_result:
            logger.info(f"[BGM Matcher] Backup 폴더에서 선택: {Path(backup_result).name}")
            return backup_result

        # 최후의 수단: Primary 폴더 첫 번째 파일
        logger.error("[BGM Matcher] 모든 매칭 실패, 하드코딩 폴백 사용")
        emergency_folders = ["travel", "upbeat", "energetic", "calm"]

        for folder in emergency_folders:
            folder_path = self.music_root / folder
            if folder_path.exists():
                mp3_files = list(folder_path.glob("*.mp3"))
                if mp3_files:
                    selected = str(mp3_files[0])
                    logger.warning(f"[BGM Matcher] 긴급 선택: {Path(selected).name} (폴더: {folder})")
                    return selected

        # 정말 최후: 전체에서 첫 번째 mp3
        all_mp3 = list(self.music_root.glob("**/*.mp3"))
        if all_mp3:
            selected = str(all_mp3[0])
            logger.warning(f"[BGM Matcher] 최후 선택: {Path(selected).name}")
            return selected

        # 모든 시도 실패
        raise RuntimeError(
            "[BGM Matcher] 에셋 폴더에 BGM 파일이 없음. "
            f"에셋 점검 필요 ({self.music_root})."
        )

    def _select_from_primary_folders(self) -> Optional[str]:
        """Primary Music 폴더에서 블랙리스트 제외하고 선택"""
        priority_moods = ["travel", "upbeat", "energetic", "calm"]

        for mood in priority_moods:
            files = self._get_files_from_mood_folder(mood, set())
            if files:
                selected = random.choice(files)[0]
                logger.info(f"[BGM Matcher] Primary 폴백: {Path(selected).name} (폴더: {mood})")
                return selected

        return None

    def _select_from_backup_folders(self) -> Optional[str]:
        """Backup Music_Backup 폴더에서 블랙리스트 제외하고 선택"""
        if not self.backup_root.exists():
            logger.warning(f"[BGM Matcher] Backup 폴더 없음: {self.backup_root}")
            return None

        priority_moods = ["travel", "upbeat", "energetic", "calm"]

        for mood in priority_moods:
            folder_path = self.backup_root / mood
            if not folder_path.exists():
                continue

            mp3_files = list(folder_path.glob("*.mp3"))

            # 블랙리스트 필터링
            filtered_files = []
            for mp3_file in mp3_files:
                if not self.blacklist_pattern.search(mp3_file.name):
                    filtered_files.append(str(mp3_file))

            if filtered_files:
                selected = random.choice(filtered_files)
                logger.info(f"[BGM Matcher] Backup 폴더 선택: {Path(selected).name} (폴더: {mood})")
                return selected

        return None

    @staticmethod
    def get_bgm_volume_for_emotion(emotion_score: float, base_volume: float = 0.20) -> float:
        """감정 점수 기반 BGM 볼륨 동적 조절 (WO v11.0 D-5)

        감정 하강 구간: 볼륨 50% 감소 → 음성 집중 유도
        감정 상승 구간: 볼륨 120% → 기대감/확신 강화
        중간 구간: 기본 볼륨 유지

        Args:
            emotion_score: 감정 점수 (0.0~1.0)
            base_volume: 기본 BGM 볼륨 (기본값 0.20)

        Returns:
            조절된 BGM 볼륨 (float)
        """
        if emotion_score < 0.40:
            return base_volume * 0.5   # 공감/불안 구간: 음성 집중
        elif emotion_score > 0.85:
            return base_volume * 1.2   # 확신/행동 구간: 감정 강화
        else:
            return base_volume          # 중간: 기본 유지

    @staticmethod
    def get_bgm_volume_curve(segments: list, base_volume: float = 0.20) -> list:
        """세그먼트 리스트 기반 BGM 볼륨 곡선 생성 (WO v11.0 D-5)

        Args:
            segments: 세그먼트 딕셔너리 리스트 (emotion_score 키 포함)
            base_volume: 기본 BGM 볼륨

        Returns:
            [{"start_time": float, "end_time": float, "volume": float}, ...]
        """
        volume_curve = []
        for seg in segments:
            emotion_score = seg.get("emotion_score", 0.5)
            start_time = seg.get("start_time", 0.0)
            end_time = seg.get("end_time", start_time + seg.get("duration", 3.0))
            volume = BGMMatcher.get_bgm_volume_for_emotion(emotion_score, base_volume)
            volume_curve.append({
                "start_time": start_time,
                "end_time": end_time,
                "volume": round(volume, 3),
                "emotion_score": emotion_score,
            })
        return volume_curve

    def get_bgm_info(self, theme: str, persona: str) -> Dict:
        """
        디버깅용 BGM 정보

        Args:
            theme: 테마
            persona: 페르소나

        Returns:
            BGM 정보 딕셔너리
        """
        selected = self.select_bgm(theme, persona)

        return {
            "theme": theme,
            "persona": persona,
            "selected_bgm": selected,
            "filename": Path(selected).name
        }


# 사용 예시 및 테스트
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    # BGM Matcher 초기화
    matcher = BGMMatcher()

    # 테스트 케이스 1: Content Type별 선택
    print("\n=== Content Type별 BGM 선택 ===")
    for content_type in ["EDUCATION", "COMPARISON", "SOCIAL_PROOF", "FEAR_RESOLUTION", "BUCKET_LIST"]:
        try:
            bgm = matcher.select_bgm(content_type=content_type)
            print(f"[OK] {content_type}: {Path(bgm).name}")
        except Exception as e:
            print(f"[ERROR] {content_type}: {e}")

    # 테스트 케이스 2: 감정 곡선별 선택
    print("\n=== 감정 곡선별 BGM 선택 ===")
    for section in ["0-10s", "10-25s", "25-40s", "40-50s", "50-55s"]:
        try:
            bgm = matcher.select_bgm(emotion_section=section)
            print(f"[OK] {section}: {Path(bgm).name}")
        except Exception as e:
            print(f"[ERROR] {section}: {e}")

    # 테스트 케이스 3: 테마/페르소나별 선택
    print("\n=== 테마/페르소나별 BGM 선택 ===")
    test_cases = [
        ("크루즈", "액티브시니어"),
        ("힐링", "신혼부부"),
        ("레저", "가족여행"),
        ("여행", "액티브시니어"),
        ("기항지", "액티브시니어")
    ]

    for theme, persona in test_cases:
        try:
            bgm = matcher.select_bgm(theme, persona)
            print(f"[OK] {theme} + {persona}: {Path(bgm).name}")
        except Exception as e:
            print(f"[ERROR] {theme} + {persona}: {e}")

    # 상세 정보 테스트
    print("\n=== 상세 정보 ===")
    info = matcher.get_bgm_info("크루즈", "액티브시니어")
    print(f"테마: {info['theme']}")
    print(f"페르소나: {info['persona']}")
    print(f"선택된 BGM: {info['filename']}")
