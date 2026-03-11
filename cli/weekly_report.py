#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
cli/weekly_report.py - S2-C3: 주간 보고서 자동 생성

GenerationLog 기반으로 주간 성과를 자동 집계하여
Markdown 보고서를 생성한다.

사용법:
    python generate.py --report
    python generate.py --report --report-days 14

산출물:
    outputs/reports/weekly_report_20260310.md
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


def generate_weekly_report(
    gen_log,
    days: int = 7,
    output_dir: str = "outputs/reports",
) -> str:
    """주간 보고서 Markdown 생성

    Args:
        gen_log: GenerationLog 인스턴스
        days: 집계 기간 (기본 7일)
        output_dir: 보고서 저장 디렉토리

    Returns:
        저장된 보고서 파일 경로
    """
    stats = gen_log.get_statistics(days=days)
    recent = gen_log.get_recent_entries(days=days)

    now = datetime.now()
    date_str = now.strftime("%Y%m%d")
    report_title = f"CruiseDot 영상 생성 보고서 ({days}일)"

    lines = []
    lines.append(f"# {report_title}")
    lines.append(f"")
    lines.append(f"**생성일**: {now.strftime('%Y-%m-%d %H:%M')}")
    lines.append(f"**집계 기간**: 최근 {days}일")
    lines.append(f"")

    # ── 1. 요약 ──────────────────────────────────────────
    lines.append(f"## 1. 요약")
    lines.append(f"")
    lines.append(f"| 항목 | 값 |")
    lines.append(f"|------|-----|")
    lines.append(f"| 전체 누적 | {stats['total_entries']}편 |")
    lines.append(f"| 최근 {days}일 | {stats['recent_entries']}편 |")
    lines.append(f"| 평균 점수 | {stats['avg_score']}점 |")
    lines.append(f"| S등급 비율 | {stats['s_grade_rate']}% |")
    lines.append(f"")

    # ── 2. 등급 분포 ─────────────────────────────────────
    grade_counts = stats.get("grade_counts", {})
    lines.append(f"## 2. 등급 분포")
    lines.append(f"")
    if grade_counts:
        lines.append(f"| 등급 | 편수 | 비율 |")
        lines.append(f"|------|------|------|")
        total = stats['recent_entries'] or 1
        for grade in ["S", "A", "B", "C", "F"]:
            count = grade_counts.get(grade, 0)
            rate = round(count / total * 100, 1)
            bar = "█" * int(rate / 5) if rate > 0 else "-"
            lines.append(f"| {grade} | {count} | {rate}% {bar} |")
    else:
        lines.append("데이터 없음")
    lines.append(f"")

    # ── 3. 기항지별 생성 현황 ────────────────────────────
    port_counts = stats.get("port_counts", {})
    lines.append(f"## 3. 기항지별 생성 현황")
    lines.append(f"")
    if port_counts:
        lines.append(f"| 기항지 | 편수 |")
        lines.append(f"|--------|------|")
        sorted_ports = sorted(port_counts.items(), key=lambda x: x[1], reverse=True)
        for port, count in sorted_ports:
            lines.append(f"| {port} | {count} |")
    else:
        lines.append("데이터 없음")
    lines.append(f"")

    # ── 4. 카테고리별 생성 현황 ──────────────────────────
    cat_counts = stats.get("category_counts", {})
    lines.append(f"## 4. 카테고리별 생성 현황")
    lines.append(f"")
    if cat_counts:
        lines.append(f"| 카테고리 | 편수 |")
        lines.append(f"|----------|------|")
        sorted_cats = sorted(cat_counts.items(), key=lambda x: x[1], reverse=True)
        for cat, count in sorted_cats:
            lines.append(f"| {cat} | {count} |")
    else:
        lines.append("데이터 없음")
    lines.append(f"")

    # ── 5. 내러티브/포맷 다양성 (S2 추적) ───────────────
    narrative_counts: Dict[str, int] = {}
    format_counts: Dict[str, int] = {}
    for entry in recent:
        nt = getattr(entry, 'narrative_type', '') or ''
        cf = getattr(entry, 'content_format', '') or ''
        if nt:
            narrative_counts[nt] = narrative_counts.get(nt, 0) + 1
        if cf:
            format_counts[cf] = format_counts.get(cf, 0) + 1

    lines.append(f"## 5. 다양성 지표 (S2)")
    lines.append(f"")

    if narrative_counts:
        lines.append(f"### 내러티브 유형")
        lines.append(f"| 유형 | 편수 | 비율 |")
        lines.append(f"|------|------|------|")
        total_n = sum(narrative_counts.values()) or 1
        for nt, count in sorted(narrative_counts.items()):
            lines.append(f"| {nt} | {count} | {round(count/total_n*100, 1)}% |")
        lines.append(f"")

    if format_counts:
        lines.append(f"### 콘텐츠 포맷")
        lines.append(f"| 포맷 | 편수 | 비율 |")
        lines.append(f"|------|------|------|")
        total_f = sum(format_counts.values()) or 1
        for cf, count in sorted(format_counts.items()):
            lines.append(f"| {cf} | {count} | {round(count/total_f*100, 1)}% |")
        lines.append(f"")

    if not narrative_counts and not format_counts:
        lines.append("S2 다양성 데이터 없음 (아직 S2 기능으로 생성된 영상 없음)")
        lines.append(f"")

    # ── 6. 최근 생성 목록 (최대 20편) ────────────────────
    lines.append(f"## 6. 최근 생성 목록")
    lines.append(f"")
    if recent:
        lines.append(f"| # | 날짜 | 기항지 | 카테고리 | 등급 | 점수 | 트래킹 |")
        lines.append(f"|---|------|--------|----------|------|------|--------|")
        for i, entry in enumerate(recent[-20:], 1):
            date = getattr(entry, 'timestamp_unix', '')
            grade = getattr(entry, 's_grade', '') or getattr(entry, 'grade', '')
            score = getattr(entry, 's_grade_score', 0)
            tracking = getattr(entry, 'tracking_code', '') or '-'
            lines.append(
                f"| {i} | {date} | {entry.port_code} | "
                f"{entry.category_code} | {grade} | {score} | {tracking} |"
            )
    else:
        lines.append("데이터 없음")
    lines.append(f"")

    # ── 7. 권고사항 ──────────────────────────────────────
    lines.append(f"## 7. 권고사항")
    lines.append(f"")
    recommendations = _generate_recommendations(stats, recent, days)
    for rec in recommendations:
        lines.append(f"- {rec}")
    lines.append(f"")

    lines.append(f"---")
    lines.append(f"*자동 생성: CruiseDot Weekly Report Generator (S2-C3)*")

    # ── 저장 ─────────────────────────────────────────────
    report_content = "\n".join(lines)

    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)
    report_file = out_path / f"weekly_report_{date_str}.md"

    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report_content)

    logger.info(f"[WeeklyReport] 보고서 생성: {report_file}")
    return str(report_file)


def _generate_recommendations(
    stats: Dict,
    recent: list,
    days: int,
) -> List[str]:
    """통계 기반 권고사항 자동 생성"""
    recs = []

    # S등급 비율 체크
    s_rate = stats.get('s_grade_rate', 0)
    if s_rate < 50:
        recs.append(f"S등급 비율 {s_rate}%로 낮음. Gemini API 연결 또는 스크립트 품질 개선 필요")
    elif s_rate >= 90:
        recs.append(f"S등급 비율 {s_rate}% 우수! 현재 품질 수준 유지")

    # 기항지 편중 체크
    port_counts = stats.get('port_counts', {})
    if port_counts:
        max_port = max(port_counts.values())
        total = stats.get('recent_entries', 1) or 1
        if max_port / total > 0.4:
            top_port = max(port_counts, key=port_counts.get)
            recs.append(f"기항지 '{top_port}' 편중 ({max_port}/{total}편). 다른 기항지 확대 권장")

    # 카테고리 편중 체크
    cat_counts = stats.get('category_counts', {})
    if cat_counts:
        max_cat = max(cat_counts.values())
        total = stats.get('recent_entries', 1) or 1
        if max_cat / total > 0.5:
            top_cat = max(cat_counts, key=cat_counts.get)
            recs.append(f"카테고리 '{top_cat}' 편중 ({max_cat}/{total}편). 다양한 카테고리 활용 권장")

    # 생산량 체크
    daily_avg = round(stats.get('recent_entries', 0) / max(days, 1), 1)
    if daily_avg < 5:
        recs.append(f"일 평균 {daily_avg}편 생산. 목표 일 100편 대비 부족. 배치 병렬 처리 활용 권장")
    elif daily_avg >= 50:
        recs.append(f"일 평균 {daily_avg}편 생산. 목표 대비 양호")

    if not recs:
        recs.append("특이사항 없음")

    return recs
