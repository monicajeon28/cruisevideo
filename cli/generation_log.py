#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
cli/generation_log.py — 영상 생성 이력 관리 + 중복 방지

JSONL 파일 구조:
{
  "entries": [{...}, ...],
  "updated_at": "2026-03-09 12:00:00"
}
"""

import json
import logging
import os
from typing import List, Dict, Tuple
from pathlib import Path
from datetime import datetime, timedelta
from dataclasses import dataclass, field, asdict

logger = logging.getLogger(__name__)


@dataclass
class GenerationLogEntry:
    timestamp: str               # ISO 8601
    timestamp_unix: str          # Unix timestamp 문자열 (예: "2026-03-09")
    port_code: str               # 기항지 코드 (예: "NAGASAKI")
    category_code: str           # 카테고리 code (예: "PORT_INFO")
    category_name: str = ""      # 카테고리 한글명
    ship_code: str = ""          # 선박 code
    price_tier: str = ""         # "T1_진입가" / "T2_주력가" / "T3_프리미엄" 등
    s_grade_score: float = 0.0   # 예: 92.5
    script_path: str = ""        # 출력 JSON 경로
    upload_pkg_dir: str = ""     # 업로드 패키지 디렉토리
    s_grade: str = ""            # "S" / "A" / "B"
    grade: str = ""              # "S" / "A" / "B"
    voice_male: str = ""         # dialogue 남성 음성 (예: "juho")
    voice_female: str = ""       # dialogue 여성 음성 (예: "audrey")
    # S2-B1: 내러티브 유형
    narrative_type: str = ""     # "SEQUENTIAL" / "REVERSE" / "CONTRAST"
    # S2-B3: 콘텐츠 포맷
    content_format: str = ""     # "NEWS" / "TIP" / "TRAVEL_STORY"
    # S2-C1: 트래킹 코드
    tracking_code: str = ""      # "CD-20260310-001-EDU-SEQ"


@dataclass
class DuplicateCheckResult:
    """중복 체크 결과"""

    def __init__(self, allowed: bool = True, reason: str = "", port_count: int = 0, category_count: int = 0):
        self.allowed = allowed
        self.reason = reason          # 차단 이유 (허용 시 "")
        self.port_count = port_count      # "port" 또는 "category" count
        self.category_count = category_count

    def __bool__(self) -> bool:
        return self.allowed

    def __repr__(self) -> str:
        if self.allowed:
            return (
                f"허용 ("
                f"port={self.port_count}, "
                f"category={self.category_count})"
            )
        return f"차단: {self.reason}"


class GenerationLog:
    """
    JSONL 관리 클래스

    중복 방지 로직:
    - 동일 기항지 7일 내 최대 4편
    - 동일 카테고리 7일 내 최대 5편
    """

    def __init__(self, log_path: str):
        self.entries: List[GenerationLogEntry] = []
        self.log_path = Path(log_path)
        self._load()

    # ------------------------------------------------------------------
    # 내부 메서드
    # ------------------------------------------------------------------

    def _load(self) -> None:
        """기존 로그 파일 로드. 파일이 없으면 빈 상태로 초기화."""
        if not self.log_path.exists():
            logger.info("[GenerationLog] 신규 로그 파일: %s", self.log_path)
            self.entries = []
            return

        try:
            with open(self.log_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            self.entries = [
                GenerationLogEntry(**entry) for entry in data.get("entries", [])
            ]
            logger.info("[GenerationLog] %d개 기록 로드", len(self.entries))
        except Exception as e:
            logger.warning("[GenerationLog] 로드 실패, 초기화: %s", e)
            self.entries = []

    # ------------------------------------------------------------------
    # 공개 메서드 — 저장
    # ------------------------------------------------------------------

    def save(self) -> None:
        """로그 파일 저장. 실패 시 예외 전파 (조용히 실패 금지)."""
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "entries": [asdict(e) for e in self.entries],
            "updated_at": datetime.now().isoformat(),
        }
        with open(self.log_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def add_entry(self, entry: GenerationLogEntry) -> None:
        """기록 추가 후 즉시 저장."""
        if not entry.timestamp:
            entry.timestamp = datetime.now().isoformat()
        if not entry.timestamp_unix:
            entry.timestamp_unix = datetime.now().strftime("%Y-%m-%d")
        self.entries.append(entry)
        self.save()
        logger.info(
            "[GenerationLog] 기록 추가: %s / %s",
            entry.port_code, entry.category_code
        )

    # ------------------------------------------------------------------
    # 공개 메서드 — 조회
    # ------------------------------------------------------------------

    def get_recent_entries(self, days: int = 7) -> List[GenerationLogEntry]:
        """최근 N일 내 기록만 반환. 날짜 파싱 실패 항목은 제외."""
        cutoff = datetime.now() - timedelta(days=days)
        recent = []
        for entry in self.entries:
            try:
                entry_dt = datetime.fromisoformat(entry.timestamp)
                if entry_dt >= cutoff:
                    recent.append(entry)
            except (ValueError, TypeError):
                continue
        return recent

    # ------------------------------------------------------------------
    # 공개 메서드 — 중복 체크
    # ------------------------------------------------------------------

    def check_port_limit(
        self,
        port_code: str,
        max_per_week: int = 4,
        window_days: int = 7,
    ) -> DuplicateCheckResult:
        """기항지 주당 편수 초과 여부를 확인한다."""
        recent = self.get_recent_entries(window_days)
        count = sum(1 for e in recent if e.port_code == port_code)
        if count >= max_per_week:
            return DuplicateCheckResult(
                allowed=False,
                reason=f"{port_code} {count}/{max_per_week}편 (최근 {window_days}일)",
                port_count=count,
            )
        return DuplicateCheckResult(allowed=True, port_count=count, reason="")

    def check_category_limit(
        self,
        category_code: str,
        max_per_week: int = 5,
        window_days: int = 7,
    ) -> DuplicateCheckResult:
        """카테고리 주당 편수 초과 여부를 확인한다."""
        recent = self.get_recent_entries(window_days)
        count = sum(1 for e in recent if e.category_code == category_code)
        if count >= max_per_week:
            return DuplicateCheckResult(
                allowed=False,
                reason=f"{category_code} {count}/{max_per_week}편 (최근 {window_days}일)",
                category_count=count,
            )
        return DuplicateCheckResult(allowed=True, category_count=count, reason="")

    def check_combination(
        self,
        port_code: str,
        category_code: str,
        max_port_per_week: int = 4,
        max_category_per_week: int = 5,
        window_days: int = 7,
    ) -> DuplicateCheckResult:
        """기항지 + 카테고리 조합 허용 여부를 통합 체크한다.

        기항지 한도 초과 → 카테고리 한도 초과 순서로 평가하며,
        두 조건 모두 통과해야 허용(True)을 반환한다.
        """
        port_check = self.check_port_limit(port_code, max_port_per_week, window_days)
        if not port_check.allowed:
            return port_check

        cat_check = self.check_category_limit(category_code, max_category_per_week, window_days)
        if not cat_check.allowed:
            return cat_check

        return DuplicateCheckResult(
            allowed=True,
            port_count=port_check.port_count,
            category_count=cat_check.category_count,
            reason="",
        )

    # ------------------------------------------------------------------
    # dialogue 음성 추적 메서드
    # ------------------------------------------------------------------

    def record_voice_combination(self, voice_male: str, voice_female: str) -> None:
        """
        음성 조합 사용 기록 (현재 entry에 포함)

        Note: 실제 기록은 add_entry 시 voice_male, voice_female 필드로 저장됨.
        이 메서드는 호환성을 위해 제공되며, 별도 동작은 하지 않음.
        """
        logger.debug(
            "[GenerationLog] 음성 조합 기록 예정: %s + %s (add_entry 시 저장)",
            voice_male, voice_female
        )

    def get_recent_voice_combinations(self, days: int = 7) -> List[Tuple[str, str]]:
        """
        최근 N일 내 사용된 음성 조합 목록 반환

        Returns:
            [(male, female), ...] 튜플 리스트
        """
        recent = self.get_recent_entries(days)
        combinations: List[Tuple[str, str]] = []

        for entry in recent:
            male = entry.voice_male or ""
            female = entry.voice_female or ""

            # 음성 정보가 있는 경우만 추가
            if male or female:
                combinations.append((male, female))

        logger.debug(
            "[GenerationLog] 최근 %d일 음성 조합 %d개",
            days, len(combinations)
        )

        return combinations

    # ------------------------------------------------------------------
    # S2-C1: 트래킹 코드 생성
    # ------------------------------------------------------------------

    # content_type → 3자 약어 매핑
    _TYPE_ABBREV = {
        "EDUCATION": "EDU", "COMPARISON": "CMP", "VALUE_PROOF": "VAL",
        "CONVENIENCE": "CNV", "BUCKET_LIST": "BKT", "SOCIAL_PROOF": "SOC",
        "FEAR_RESOLUTION": "FRR", "FEAR_HIDDEN_COST": "FHC",
        "FEAR_ONBOARD_SYSTEM": "FOS", "FEAR_QUALITY_CONCERN": "FQC",
        "FEAR_SEASICKNESS": "FSS", "CRITERIA_EDUCATION": "CRI",
        "PORT_INFO": "PRT", "SHIP_FACILITY": "SHP", "LUXURY_EXPERIENCE": "LUX",
    }

    # narrative_type → 3자 약어 매핑
    _NARR_ABBREV = {
        "SEQUENTIAL": "SEQ", "REVERSE": "REV", "CONTRAST": "CON",
    }

    def generate_tracking_code(
        self,
        content_type: str,
        narrative_type: str = "SEQUENTIAL",
    ) -> str:
        """트래킹 코드 자동 생성

        형식: CD-{YYYYMMDD}-{NNN}-{TYPE_3CHAR}-{NARR_3CHAR}
        예: CD-20260310-001-EDU-SEQ
        """
        date_str = datetime.now().strftime("%Y%m%d")
        type_abbr = self._TYPE_ABBREV.get(content_type, content_type[:3].upper())
        narr_abbr = self._NARR_ABBREV.get(narrative_type, "SEQ")

        today_entries = [
            e for e in self.entries
            if e.tracking_code and e.tracking_code.startswith(f"CD-{date_str}")
        ]
        seq_num = len(today_entries) + 1

        return f"CD-{date_str}-{seq_num:03d}-{type_abbr}-{narr_abbr}"

    # ------------------------------------------------------------------
    # 공개 메서드 — 통계
    # ------------------------------------------------------------------

    def get_statistics(self, days: int = 7) -> Dict:
        """생성 통계 요약을 반환한다."""
        recent = self.get_recent_entries(days)

        port_counts: Dict[str, int] = {}
        category_counts: Dict[str, int] = {}
        grade_counts: Dict[str, int] = {}
        total_score = 0.0

        for entry in recent:
            port_counts[entry.port_code] = port_counts.get(entry.port_code, 0) + 1
            category_counts[entry.category_code] = category_counts.get(entry.category_code, 0) + 1
            grade = entry.s_grade or entry.grade or ""
            if grade:
                grade_counts[grade] = grade_counts.get(grade, 0) + 1
            total_score += entry.s_grade_score

        avg_score = round(
            total_score / len(recent), 1
        ) if recent else 0.0

        s_grade_rate = round(grade_counts.get("S", 0) / len(recent) * 100, 1) if recent else 0.0

        return {
            "total_entries": len(self.entries),
            "recent_entries": len(recent),
            "port_counts": port_counts,
            "category_counts": category_counts,
            "grade_counts": grade_counts,
            "avg_score": avg_score,
            "s_grade_rate": s_grade_rate,
        }


# ----------------------------------------------------------------------
# 편의 함수
# ----------------------------------------------------------------------

def load_generation_log(log_path: str) -> GenerationLog:
    """GenerationLog 인스턴스를 반환하는 편의 함수."""
    return GenerationLog(log_path)
