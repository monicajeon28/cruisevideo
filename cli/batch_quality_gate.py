#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Batch Quality Gate - S등급 사전 필터링 (FR-4)

Pre-Render Filter: S-grade <70 scripts rejected before render
Impact: 3x effective throughput (10 → 30 scripts/day)

Author: Code Writer Agent (2026-03-08)
Based on: output/05_PRD_DOCUMENT.md FR-4
"""

import logging
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple
from collections import defaultdict

logger = logging.getLogger(__name__)


class BatchQualityGate:
    """
    배치 생성 품질 게이트 시스템

    기능:
    1. S-grade <70 스크립트 사전 필터링 (렌더링 전)
    2. 실패 원인 분석 및 통계 (Common failure patterns)
    3. 배치 품질 리포트 생성 (HTML/JSON)

    Usage:
        gate = BatchQualityGate()
        passed, rejected = gate.pre_render_filter(scripts)
        report = gate.generate_batch_report(passed, rejected)
    """

    # S등급 최소 점수 (70점 미만 즉시 제거)
    MIN_SGRADE = 70.0

    # S등급 목표 점수 (90점 이상)
    TARGET_SGRADE = 90.0

    # 실패 원인 카테고리
    FAILURE_CATEGORIES = {
        "low_score": "S-grade score < 70",
        "banned_words": "Banned words detected",
        "trust_insufficient": "Trust elements < 2",
        "pop_count_wrong": "Pop count != 3",
        "rehook_missing": "Re-hook count < 2",
        "port_visual_short": "Port visual duration < 20s",
        "cta_incomplete": "CTA 3-stage incomplete"
    }

    def __init__(self, output_dir: Path = None):
        """
        Args:
            output_dir: 리포트 저장 디렉토리 (기본: output/batch_reports)
        """
        self.output_dir = output_dir or Path("output/batch_reports")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"BatchQualityGate 초기화 완료 (MIN: {self.MIN_SGRADE}, TARGET: {self.TARGET_SGRADE})")

    def pre_render_filter(
        self,
        scripts: List[Dict],
        validator=None
    ) -> Tuple[List[Dict], List[Tuple[Dict, float, List[str]]]]:
        """
        렌더링 전 품질 필터 (S-grade <70 제거)

        Args:
            scripts: 생성된 스크립트 리스트
            validator: ScriptValidationOrchestrator 인스턴스 (없으면 생성)

        Returns:
            (passed_scripts, rejected_scripts)
            - passed_scripts: S-grade >= 70인 스크립트 리스트
            - rejected_scripts: [(script, score, issues), ...] 리스트
        """
        if not scripts:
            logger.warning("[Quality Gate] 입력 스크립트 없음")
            return [], []

        # Validator 준비
        if validator is None:
            try:
                from engines.script_validation_orchestrator import ScriptValidationOrchestrator
                validator = ScriptValidationOrchestrator()
            except (ImportError, OSError, RuntimeError) as e:
                logger.error(f"[Quality Gate] Validator 로드 실패: {e}")
                # Validator 없이 모든 스크립트 통과 (fallback)
                return scripts, []

        passed = []
        rejected = []

        logger.info(f"[Quality Gate] 품질 필터 시작: {len(scripts)}개 스크립트")

        for idx, script in enumerate(scripts):
            try:
                # S-grade 검증 (script metadata에 pop_messages 포함)
                script_metadata = script.get("metadata", {}) if isinstance(script, dict) else {}
                validation = validator.validate(script, metadata=script_metadata)
                score = validation.score
                grade = validation.grade
                issues = validation.issues

                # 품질 게이트 기준 체크
                if score >= self.MIN_SGRADE:
                    passed.append(script)
                    logger.info(
                        f"[Quality Gate] ✅ Script {idx+1}/{len(scripts)} 통과: "
                        f"{score:.1f}점 ({grade})"
                    )
                else:
                    rejected.append((script, score, issues))
                    logger.warning(
                        f"[Quality Gate] ❌ Script {idx+1}/{len(scripts)} 거절: "
                        f"{score:.1f}점 < {self.MIN_SGRADE}점 (이슈: {len(issues)}개)"
                    )

                    # 실패 원인 상세 로그
                    for issue in issues[:3]:  # 상위 3개만 출력
                        logger.warning(f"  - {issue}")

            except (ValueError, RuntimeError, KeyError, TypeError) as e:
                logger.error(
                    f"[Quality Gate] Script {idx+1} 검증 실패: {e}"
                )
                # 검증 실패 시 스크립트는 제외 (안전하게)
                rejected.append((script, 0.0, [f"Validation error: {str(e)}"]))

        pass_rate = len(passed) / len(scripts) * 100 if scripts else 0.0
        logger.info(
            f"[Quality Gate] 필터링 완료: {len(passed)}/{len(scripts)} 통과 ({pass_rate:.1f}%)"
        )

        return passed, rejected

    def generate_batch_report(
        self,
        passed: List[Dict],
        rejected: List[Tuple[Dict, float, List[str]]],
        attempts: int = 0,
        elapsed_time: float = 0.0
    ) -> Dict:
        """
        배치 품질 리포트 생성

        Args:
            passed: 통과한 스크립트 리스트
            rejected: 거절된 스크립트 리스트 (score, issues 포함)
            attempts: 총 시도 횟수
            elapsed_time: 소요 시간 (초)

        Returns:
            리포트 딕셔너리 (JSON 저장용)
        """
        total_count = len(passed) + len(rejected)
        if total_count == 0:
            logger.warning("[Quality Gate] 리포트 생성 실패: 스크립트 없음")
            return {}

        # 실패 원인 분석
        failure_reasons = defaultdict(int)
        for script, score, issues in rejected:
            for issue in issues:
                # 이슈 텍스트에서 카테고리 추출
                category = self._categorize_issue(issue)
                failure_reasons[category] += 1

        # 통과 스크립트 점수 통계
        passed_scores = [s.get("sgrade_score", 0.0) for s in passed]
        avg_passed_score = sum(passed_scores) / len(passed_scores) if passed_scores else 0.0

        # 거절 스크립트 점수 통계
        rejected_scores = [score for _, score, _ in rejected]
        avg_rejected_score = sum(rejected_scores) / len(rejected_scores) if rejected_scores else 0.0

        # 리포트 구성
        report = {
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_scripts": total_count,
                "passed_count": len(passed),
                "rejected_count": len(rejected),
                "pass_rate": len(passed) / total_count * 100,
                "attempts": attempts,
                "elapsed_time_sec": elapsed_time
            },
            "score_statistics": {
                "passed_avg": round(avg_passed_score, 1),
                "passed_min": round(min(passed_scores), 1) if passed_scores else 0.0,
                "passed_max": round(max(passed_scores), 1) if passed_scores else 0.0,
                "rejected_avg": round(avg_rejected_score, 1),
                "rejected_min": round(min(rejected_scores), 1) if rejected_scores else 0.0,
                "rejected_max": round(max(rejected_scores), 1) if rejected_scores else 0.0
            },
            "failure_breakdown": dict(failure_reasons),
            "common_failures": sorted(
                failure_reasons.items(),
                key=lambda x: x[1],
                reverse=True
            )[:5],  # Top 5 실패 원인
            "passed_scripts": [
                {
                    "category": s.get("context", {}).get("category", "N/A"),
                    "port": s.get("context", {}).get("port_name", "N/A"),
                    "sgrade_score": s.get("sgrade_score", 0.0),
                    "grade": s.get("grade", "N/A")
                }
                for s in passed
            ],
            "rejected_scripts": [
                {
                    "category": s.get("context", {}).get("category", "N/A"),
                    "port": s.get("context", {}).get("port_name", "N/A"),
                    "score": score,
                    "issues": issues[:3]  # 상위 3개 이슈만
                }
                for s, score, issues in rejected
            ]
        }

        # JSON 파일 저장
        report_path = self._save_report_json(report)
        logger.info(f"[Quality Gate] 배치 리포트 저장: {report_path}")

        # HTML 리포트 생성 (선택적)
        try:
            html_path = self._generate_html_report(report)
            logger.info(f"[Quality Gate] HTML 리포트 저장: {html_path}")
        except (OSError, ValueError, RuntimeError) as e:
            logger.warning(f"[Quality Gate] HTML 리포트 생성 실패: {e}")

        return report

    def _categorize_issue(self, issue_text: str) -> str:
        """
        이슈 텍스트에서 실패 카테고리 추출

        Returns:
            카테고리 문자열
        """
        issue_lower = issue_text.lower()

        if "금지어" in issue_lower or "banned" in issue_lower:
            return "banned_words"
        elif "trust" in issue_lower or "신뢰" in issue_lower:
            return "trust_insufficient"
        elif "pop" in issue_lower:
            return "pop_count_wrong"
        elif "re-hook" in issue_lower or "리훅" in issue_lower:
            return "rehook_missing"
        elif "port" in issue_lower or "기항지" in issue_lower:
            return "port_visual_short"
        elif "cta" in issue_lower:
            return "cta_incomplete"
        elif "점수" in issue_lower or "score" in issue_lower:
            return "low_score"
        else:
            return "other"

    def _save_report_json(self, report: Dict) -> Path:
        """
        리포트를 JSON 파일로 저장

        Returns:
            저장된 파일 경로
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"batch_report_{timestamp}.json"
        filepath = self.output_dir / filename

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        return filepath

    def _generate_html_report(self, report: Dict) -> Path:
        """
        리포트를 HTML 파일로 생성

        Returns:
            저장된 HTML 파일 경로
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"batch_report_{timestamp}.html"
        filepath = self.output_dir / filename

        # HTML 템플릿
        html = f"""
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Batch Quality Report - {report['timestamp']}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: auto; background: white; padding: 20px; border-radius: 8px; }}
        h1 {{ color: #333; }}
        h2 {{ color: #555; border-bottom: 2px solid #ddd; padding-bottom: 10px; }}
        .summary {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 15px; margin-bottom: 30px; }}
        .summary-box {{ background: #f9f9f9; padding: 15px; border-radius: 5px; border-left: 4px solid #4CAF50; }}
        .summary-box.rejected {{ border-left-color: #f44336; }}
        .summary-box h3 {{ margin: 0 0 10px 0; font-size: 14px; color: #777; }}
        .summary-box .value {{ font-size: 32px; font-weight: bold; color: #333; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
        th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }}
        th {{ background: #4CAF50; color: white; }}
        tr:hover {{ background: #f9f9f9; }}
        .pass {{ color: #4CAF50; font-weight: bold; }}
        .fail {{ color: #f44336; font-weight: bold; }}
        .chart {{ margin: 20px 0; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Batch Quality Gate Report</h1>
        <p>Generated: {report['timestamp']}</p>

        <div class="summary">
            <div class="summary-box">
                <h3>Total Scripts</h3>
                <div class="value">{report['summary']['total_scripts']}</div>
            </div>
            <div class="summary-box">
                <h3>Passed (Pass Rate)</h3>
                <div class="value pass">{report['summary']['passed_count']} ({report['summary']['pass_rate']:.1f}%)</div>
            </div>
            <div class="summary-box rejected">
                <h3>Rejected</h3>
                <div class="value fail">{report['summary']['rejected_count']}</div>
            </div>
        </div>

        <h2>Score Statistics</h2>
        <table>
            <tr>
                <th>Category</th>
                <th>Average</th>
                <th>Min</th>
                <th>Max</th>
            </tr>
            <tr>
                <td class="pass">Passed Scripts</td>
                <td>{report['score_statistics']['passed_avg']}</td>
                <td>{report['score_statistics']['passed_min']}</td>
                <td>{report['score_statistics']['passed_max']}</td>
            </tr>
            <tr>
                <td class="fail">Rejected Scripts</td>
                <td>{report['score_statistics']['rejected_avg']}</td>
                <td>{report['score_statistics']['rejected_min']}</td>
                <td>{report['score_statistics']['rejected_max']}</td>
            </tr>
        </table>

        <h2>Common Failure Reasons (Top 5)</h2>
        <table>
            <tr>
                <th>Reason</th>
                <th>Count</th>
                <th>Percentage</th>
            </tr>
"""

        # 실패 원인 Top 5
        total_failures = sum(count for _, count in report['common_failures'])
        for reason, count in report['common_failures']:
            percentage = count / total_failures * 100 if total_failures > 0 else 0
            html += f"""
            <tr>
                <td>{reason}</td>
                <td>{count}</td>
                <td>{percentage:.1f}%</td>
            </tr>
"""

        html += """
        </table>

        <h2>Passed Scripts</h2>
        <table>
            <tr>
                <th>Category</th>
                <th>Port</th>
                <th>S-Grade Score</th>
                <th>Grade</th>
            </tr>
"""

        # 통과 스크립트 리스트
        for s in report['passed_scripts']:
            html += f"""
            <tr>
                <td>{s['category']}</td>
                <td>{s['port']}</td>
                <td class="pass">{s['sgrade_score']:.1f}</td>
                <td>{s['grade']}</td>
            </tr>
"""

        html += """
        </table>

        <h2>Rejected Scripts</h2>
        <table>
            <tr>
                <th>Category</th>
                <th>Port</th>
                <th>Score</th>
                <th>Issues</th>
            </tr>
"""

        # 거절 스크립트 리스트
        for s in report['rejected_scripts']:
            issues_html = "<br>".join(s['issues'])
            html += f"""
            <tr>
                <td>{s['category']}</td>
                <td>{s['port']}</td>
                <td class="fail">{s['score']:.1f}</td>
                <td>{issues_html}</td>
            </tr>
"""

        html += """
        </table>
    </div>
</body>
</html>
"""

        # HTML 파일 저장
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(html)

        return filepath


# ============================================================================
# Convenience Function
# ============================================================================

def filter_scripts_by_quality(scripts: List[Dict], validator=None) -> Tuple[List[Dict], List]:
    """
    품질 필터 편의 함수

    Usage:
        passed, rejected = filter_scripts_by_quality(scripts)
    """
    gate = BatchQualityGate()
    return gate.pre_render_filter(scripts, validator)


# ============================================================================
# Unit Tests
# ============================================================================

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)

    # 샘플 테스트
    test_scripts = [
        {
            "context": {"category": "기항지정보", "port_name": "산토리니"},
            "sgrade_score": 95.0,
            "grade": "S_GRADE",
            "segments": []
        },
        {
            "context": {"category": "불안해소", "port_name": "나가사키"},
            "sgrade_score": 88.0,
            "grade": "A_GRADE",
            "segments": []
        },
        {
            "context": {"category": "가격비교", "port_name": "후쿠오카"},
            "sgrade_score": 65.0,  # 거절 대상
            "grade": "C_GRADE",
            "segments": []
        },
    ]

    gate = BatchQualityGate()

    # Validator 없이 테스트 (점수만 체크)
    class MockValidator:
        def validate(self, script):
            class Result:
                def __init__(self, script):
                    self.score = script.get("sgrade_score", 0.0)
                    self.grade = script.get("grade", "F_GRADE")
                    self.issues = ["테스트 이슈"] if self.score < 70 else []
            return Result(script)

    passed, rejected = gate.pre_render_filter(test_scripts, MockValidator())

    print("\n=== Batch Quality Gate Test Result ===")
    print(f"Passed: {len(passed)}")
    print(f"Rejected: {len(rejected)}")

    report = gate.generate_batch_report(passed, rejected, attempts=5, elapsed_time=120.5)
    print(f"\nReport generated: {report['summary']['pass_rate']:.1f}% pass rate")
