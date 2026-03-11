#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Hook Structure Validator - S-Grade Hook Quality Check
"""

import logging
from typing import Dict, List, Any
import re

logger = logging.getLogger(__name__)


class HookStructureValidator:
    """
    Hook structure validation (pattern-based)

    Validates:
    - Hook presence in 0-3 sec
    - Forbidden words check
    - Hook pattern matching
    - 3-10 sec value declaration
    """

    # Forbidden greetings (instant F grade if used in first 3 sec)
    FORBIDDEN_GREETINGS = [
        "안녕하세요", "여러분", "오늘은", "대해", "얘기해볼게요",
        "말씀드릴게요", "소개해드릴게요", "시작하겠습니다",
        "구독", "좋아요", "알람"
    ]

    # S-Grade hook patterns
    S_GRADE_HOOK_PATTERNS = [
        {
            "pattern": r"(모르고|못하면|안하면|버립니다|손해|망했습니다|실패|후회|놓치면)",
            "category": "문제+고통+호기심",
            "example": "이거 모르고 크루즈 타면 만원 버립니다",
            "score": 10.0,
            "name": "문제제기형"
        },
        {
            "pattern": r"(비밀|숨겨진|몰랐던|진짜|사실은|알고계세요|아세요|공개합니다)",
            "category": "호기심 갭",
            "example": "크루즈 직원이 절대 말 안 하는 비밀",
            "score": 9.5,
            "name": "비밀공개형"
        },
        {
            "pattern": r"(\d+만원|\d+억|\d+일|\d+명|\d+시간)",
            "category": "충격적 숫자",
            "example": "2,000명의 직원이 있는 배에서 벌어진 일",
            "score": 9.0,
            "name": "숫자충격형"
        }
    ]

    # Value declaration patterns (3-10 sec)
    VALUE_DECLARATION_PATTERNS = [
        r"(제가|저는|실제로|겪은|다녀왔는데|경험)",
        r"(지금|바로|당장|빨리|놓치면|안 보면)",
        r"(알려드림|보여드림|공개|전부|모두|다)",
        r"(전문가|직원|관계자|실무자|알려준)"
    ]

    def validate_hook(self, subtitles: List[Dict], script: str = "") -> Dict[str, Any]:
        """
        Comprehensive hook structure validation

        Args:
            subtitles: List of subtitle dictionaries
            script: Full script text

        Returns:
            {
                'is_valid': bool,
                'score': 0-10,
                'hook_text': str,
                'hook_pattern': dict,
                'has_value_declaration': bool,
                'warnings': List[str],
                'suggestions': List[str]
            }
        """
        if not subtitles:
            return self._create_fail_result("No subtitle data")

        # Extract 0-3 sec hook
        hook_result = self._extract_hook_segment(subtitles, script)
        if not hook_result['is_valid']:
            return hook_result

        hook_text = hook_result['text']

        # Check forbidden words
        forbidden_result = self._check_forbidden_words(hook_text)
        if forbidden_result['has_forbidden']:
            return self._create_forbidden_result(
                hook_text,
                forbidden_result['words'],
                forbidden_result['warnings']
            )

        # Match hook patterns
        pattern_result = self._match_hook_patterns(hook_text)

        # Check 3-10 sec value declaration
        value_result = self._check_value_declaration(subtitles)

        # Calculate total score
        score = self._calculate_score(
            pattern_result,
            value_result,
            hook_text
        )

        return score

    def _extract_hook_segment(self, subtitles: List[Dict], script: str) -> Dict[str, Any]:
        """Extract 0-3 sec hook segment"""
        hook_subs = [s for s in subtitles if s.get('start', 0.0) < 3.0]

        if not hook_subs:
            return {
                'is_valid': False,
                'text': "",
                'score': 0.0,
                'warnings': ['No hook in 0-3 sec range'],
                'suggestions': ['Place hook within first 3 seconds']
            }

        hook_text = " ".join(s.get('text', '').strip() for s in hook_subs).strip()

        if len(hook_text) < 10:
            return {
                'is_valid': False,
                'text': hook_text,
                'score': 0.0,
                'warnings': [f'Hook too short ({len(hook_text)} chars)'],
                'suggestions': ['Hook sentence should be at least 10 characters']
            }

        return {
            'is_valid': True,
            'text': hook_text,
            'score': 5.0
        }

    def _check_forbidden_words(self, text: str) -> Dict[str, Any]:
        """Check forbidden words"""
        found_words = []

        for word in self.FORBIDDEN_GREETINGS:
            if word in text:
                found_words.append(word)

        return {
            'has_forbidden': len(found_words) > 0,
            'words': found_words
        }

    def _match_hook_patterns(self, text: str) -> Dict[str, Any]:
        """Match hook patterns"""
        best_match = None

        for i, pattern_dict in enumerate(self.S_GRADE_HOOK_PATTERNS):
            pattern = pattern_dict.get('pattern', '')
            if re.search(pattern, text, re.IGNORECASE):
                best_match = {
                    'index': i,
                    'name': pattern_dict.get('name', ''),
                    'category': pattern_dict.get('category', ''),
                    'score': pattern_dict.get('score', 0.0),
                    'example': pattern_dict.get('example', '')
                }
                break

        # Check cruise keywords
        cruise_keywords = ['크루즈', '배', '선박', '항구', '승무원', '선실', '승객', '항해']
        has_cruise = any(kw in text for kw in cruise_keywords)

        if not has_cruise:
            return {
                'matched': False,
                'score': 0.0,
                'warnings': ['No cruise-related keywords'],
                'best_match': None
            }

        return {
            'matched': best_match is not None,
            'score': best_match['score'] if best_match else 0.0,
            'best_match': best_match,
            'warnings': []
        }

    def _check_value_declaration(self, subtitles: List[Dict]) -> Dict[str, Any]:
        """Check 3-10 sec value declaration"""
        value_subs = [s for s in subtitles if 3.0 <= s.get('start', 0.0) < 10.0]

        if not value_subs:
            return {
                'has_value': False,
                'text': "",
                'score': 0.0
            }

        value_text = " ".join(s.get('text', '').strip() for s in value_subs).strip()

        # Check value patterns
        has_pattern = False
        for pattern in self.VALUE_DECLARATION_PATTERNS:
            if re.search(pattern, value_text):
                has_pattern = True
                break

        return {
            'has_value': has_pattern,
            'text': value_text,
            'score': 5.0 if has_pattern else 0.0
        }

    def _calculate_score(
        self,
        pattern_result: Dict,
        value_result: Dict,
        hook_text: str
    ) -> Dict[str, Any]:
        """Calculate comprehensive score"""

        total_score = 0.0
        warnings = []
        suggestions = []

        # 1. Hook pattern matching (10 points)
        if pattern_result['matched']:
            pattern_score = pattern_result['score']

            # Reduce by 30% if no cruise keywords
            if not pattern_result.get('has_cruise', True):
                pattern_score *= 0.7
                warnings.append('No cruise keywords (pattern score -30%)')
                suggestions.append('Include cruise keywords: 크루즈, 배, 선박, etc')

            total_score += pattern_score
        else:
            total_score += 3.0  # Base points if no forbidden words
            warnings.append('No S-grade hook pattern used')
            suggestions.append(f'Use one of these patterns: {", ".join([p["name"] for p in self.S_GRADE_HOOK_PATTERNS])}')

        # 2. Value declaration (5 points)
        if value_result['has_value']:
            total_score += value_result['score']
            if value_result.get('bonus', False):
                total_score += 2.0  # Bonus
        else:
            total_score += 2.0  # Base points
            warnings.append('No value declaration in 3-10 sec range')
            suggestions.append('Add immediate value declaration or story start after hook')

        # 3. Hook length adjustment
        hook_len = len(hook_text)
        if hook_len < 15:
            total_score -= 1.0
            warnings.append(f'Hook too short ({hook_len} chars)')
        elif hook_len > 40:
            total_score -= 0.5
            warnings.append(f'Hook too long ({hook_len} chars, recommend 15-40 chars)')

        # 4. Grade determination
        total_score = min(10.0, max(0.0, total_score))

        if total_score >= 9.0:
            grade = 'S'
        elif total_score >= 7.5:
            grade = 'A'
        elif total_score >= 6.0:
            grade = 'B'
        elif total_score >= 4.0:
            grade = 'C'
        else:
            grade = 'F'

        # 5. Final result
        return {
            'is_valid': True,
            'score': total_score,
            'grade': grade,
            'hook_text': hook_text,
            'hook_pattern': pattern_result.get('best_match') if pattern_result['matched'] else "No pattern",
            'has_value_declaration': value_result['has_value'],
            'value_text': value_result.get('text', ''),
            'warnings': warnings,
            'suggestions': suggestions,
            'details': (pattern_result, value_result)
        }

    def _create_fail_result(self, reason: str) -> Dict[str, Any]:
        """Create failure result"""
        return {
            'is_valid': False,
            'score': 0.0,
            'grade': "F",
            'hook_text': "",
            'hook_pattern': None,
            'has_value_declaration': False,
            'warnings': [reason],
            'suggestions': ['Complete script rewrite required']
        }

    def _create_forbidden_result(self, hook_text: str, words: List[str], warnings: List[str]) -> Dict[str, Any]:
        """Create forbidden word result"""
        return {
            'is_valid': False,
            'score': 0.0,
            'grade': "F",
            'hook_text': hook_text,
            'hook_pattern': "Forbidden pattern used",
            'has_value_declaration': False,
            'warnings': [
                f'Forbidden words used: {", ".join(words)}',
                'Greetings/intros in first 3 sec cause 80% viewer drop'
            ],
            'suggestions': [
                'Remove greetings',
                'Start with S-grade hook pattern',
                'Example: "이거 모르고 크루즈 타면 30만원 버립니다"'
            ]
        }


def test_hook_validator():
    """Quick test function"""
    validator = HookStructureValidator()
    result = validator.validate_hook([
        {"text": "이거 모르고 크루즈 타면 30만원 버립니다", "start": 0.0, "end": 2.5}
    ])
    print(f"Validation result: {result}")


if __name__ == "__main__":
    test_hook_validator()
