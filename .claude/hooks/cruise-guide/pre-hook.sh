#!/bin/bash
# Cruise Guide 카테고리 Pre-Hook
# 크루즈 도메인 특화 에이전트 실행 전 Learning Data 자동 로드

AGENT_NAME="$1"
LEARNING_DATA_DIR="D:/mabiz/Learning_Data/gemini_research"
SECTIONS_DIR="$LEARNING_DATA_DIR/sections"

echo "🚢 [Cruise Guide] Learning Data 자동 로드 시작..."

# 에이전트별 필요한 섹션 자동 선택
case "$AGENT_NAME" in
    commission-calculator|affiliate-logic-writer)
        # 수수료/정산 관련
        SECTIONS=(
            "02_booking_mistakes_detailed.md"
            "04_comparison_and_positioning.md"
        )
        ;;

    admin-page-builder|partner-page-builder)
        # Admin/Partner 페이지 관련
        SECTIONS=(
            "09_solo_preparation_problems.md"
            "04_comparison_and_positioning.md"
        )
        ;;

    message-template)
        # 메시지 템플릿 관련
        SECTIONS=(
            "05_cruise_basic_faq.md"
            "02_booking_mistakes_detailed.md"
        )
        ;;

    *)
        # 기본: 모든 섹션 로드
        SECTIONS=(
            "01_strategy_and_disasters.md"
            "02_booking_mistakes_detailed.md"
            "03_onboard_and_port_issues.md"
            "04_comparison_and_positioning.md"
            "05_cruise_basic_faq.md"
        )
        ;;
esac

# 섹션 로드
for section in "${SECTIONS[@]}"; do
    section_path="$SECTIONS_DIR/$section"
    if [ -f "$section_path" ]; then
        echo "  ✅ 로드: $section"
        # Claude Code가 읽을 수 있도록 경로 출력
        echo "LEARNING_DATA_LOADED=$section_path"
    else
        echo "  ⚠️ 섹션 없음: $section"
    fi
done

echo "🚢 [Cruise Guide] Learning Data 로드 완료"
echo ""
