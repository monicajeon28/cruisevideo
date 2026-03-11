#!/bin/bash
# 크루즈 가이드 워크플로우 예시
# 사용법: bash .claude/hooks/workflow-examples/cruise-guide-workflow.sh <agent-name>

AGENT="${1:-commission-calculator}"

echo "=========================================="
echo "🚢 크루즈 가이드 워크플로우"
echo "=========================================="
echo "에이전트: $AGENT"
echo ""

# Step 1: Pre-Hook (Learning Data 자동 로드)
echo "Step 1: Learning Data 자동 로드"
echo ""

case "$AGENT" in
    commission-calculator|affiliate-logic-writer)
        echo "  📚 로드될 섹션:"
        echo "    • 02_booking_mistakes_detailed.md (예약 실수)"
        echo "    • 04_comparison_and_positioning.md (직구 vs 여행사)"
        ;;
    admin-page-builder|partner-page-builder)
        echo "  📚 로드될 섹션:"
        echo "    • 09_solo_preparation_problems.md (혼자 준비 문제)"
        echo "    • 04_comparison_and_positioning.md (비교 포지셔닝)"
        ;;
    message-template)
        echo "  📚 로드될 섹션:"
        echo "    • 05_cruise_basic_faq.md (기초 FAQ)"
        echo "    • 02_booking_mistakes_detailed.md (예약 실수)"
        ;;
    *)
        echo "  📚 로드될 섹션: 기본 섹션 (전체)"
        ;;
esac

echo ""
bash .claude/hooks/quick-hooks.sh pre $AGENT

echo ""
echo "=========================================="
echo "Step 2: Task tool 실행"
echo "=========================================="
echo ""
echo "이제 Claude Code에서 다음을 실행하세요:"
echo ""
echo "  \"$AGENT 에이전트로 [작업 설명]\""
echo ""
echo "완료되면 아무 키나 누르세요..."
read -n 1 -s

echo ""
echo ""
echo "=========================================="
echo "Step 3: Post-Hook (도메인 품질 검증)"
echo "=========================================="
echo "  • Learning Data 적용 여부 확인"
echo "  • 크루즈 용어 사용 검증"
echo "  • 고객 Pain Point 해결 확인"
echo ""
bash .claude/hooks/quick-hooks.sh post $AGENT

echo ""
echo "=========================================="
echo "✅ 크루즈 가이드 워크플로우 완료"
echo "=========================================="
echo ""

# Cruise Guide 품질 리포트
LATEST_CG=$(ls -t .claude/logs/cruise-guide/${AGENT}_*_quality.json 2>/dev/null | head -1)
if [ -f "$LATEST_CG" ]; then
    echo "📊 도메인 품질 리포트: $LATEST_CG"
    cat "$LATEST_CG"
else
    echo "ℹ️ 품질 리포트 없음"
fi
