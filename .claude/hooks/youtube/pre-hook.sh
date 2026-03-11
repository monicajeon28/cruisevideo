#!/bin/bash
# YouTube 카테고리 Pre-Hook
# S등급 크루즈 영상 제작을 위한 Gemini Research 데이터 로드

AGENT_NAME="$1"

# S등급 Learning Data 경로
GEMINI_RESEARCH="D:/mabiz/Learning_Data/gemini_research"
SECTIONS_DIR="$GEMINI_RESEARCH/sections"
LOG_DIR="D:/mabiz/.claude/logs/youtube"

mkdir -p "$LOG_DIR"

echo "📺 [YouTube S등급 시스템] $AGENT_NAME 사전 검증 시작..."
echo ""

# ============================================
# 1. S등급 Learning Data 자동 로드
# ============================================

echo "📚 [S등급 데이터 로드]"

# 필수 섹션 파일들
SECTIONS=(
    "00_sections_master.json"
    "01_hook_master.json"
    "02_script_structure.json"
    "03_keyword_strategy.json"
    "04_engagement_triggers.json"
    "05_seo_optimization.json"
    "07_quality_validation.json"
)

# 에이전트별 필수 섹션 매핑
case "$AGENT_NAME" in
    youtube-concept-generator)
        REQUIRED_SECTIONS=("01_hook_master.json" "03_keyword_strategy.json" "04_engagement_triggers.json")
        echo "  🎯 컨셉 생성 모드: Hook + 키워드 + 공유 트리거"
        ;;
    youtube-script-writer)
        REQUIRED_SECTIONS=("01_hook_master.json" "02_script_structure.json" "04_engagement_triggers.json")
        echo "  📝 스크립트 작성 모드: Hook + 4막 구조 + 트리거"
        ;;
    youtube-seo-optimizer)
        REQUIRED_SECTIONS=("03_keyword_strategy.json" "05_seo_optimization.json")
        echo "  🔍 SEO 최적화 모드: 키워드 + SEO 공식"
        ;;
    youtube-quality-validator)
        REQUIRED_SECTIONS=("00_sections_master.json" "07_quality_validation.json")
        echo "  🏆 품질 검증 모드: S등급 기준 (90점)"
        ;;
    youtube-content-orchestrator)
        REQUIRED_SECTIONS=("${SECTIONS[@]}")
        echo "  🚀 Orchestrator 모드: 전체 섹션 로드"
        ;;
    *)
        REQUIRED_SECTIONS=("00_sections_master.json")
        echo "  📖 기본 모드: 마스터 섹션만"
        ;;
esac

# 섹션 파일 존재 확인 및 내용 출력
LOADED_COUNT=0
for section in "${REQUIRED_SECTIONS[@]}"; do
    SECTION_FILE="$SECTIONS_DIR/$section"
    if [ -f "$SECTION_FILE" ]; then
        echo "  ✅ 로드: $section"
        echo ""
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo "📄 [$section] 내용:"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        cat "$SECTION_FILE"
        echo ""
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo ""

        # 환경 변수로 경로도 전달 (혹시 모르니까)
        export "SECTION_${section%.json}=$SECTION_FILE"
        LOADED_COUNT=$((LOADED_COUNT + 1))
    else
        echo "  ❌ 누락: $section"
    fi
done

echo "  📊 로드 완료: $LOADED_COUNT / ${#REQUIRED_SECTIONS[@]} 섹션"
echo ""

# ============================================
# 2. 크루즈 도메인 문서 로드
# ============================================

echo "🚢 [크루즈 도메인 지식]"

CRUISE_DOCS=(
    "05_cruise_basic_faq.md"
    "02_booking_mistakes_detailed.md"
    "04_comparison_and_positioning.md"
)

for doc in "${CRUISE_DOCS[@]}"; do
    DOC_FILE="$SECTIONS_DIR/$doc"
    if [ -f "$DOC_FILE" ]; then
        echo "  ✅ 로드: $doc"
        echo ""
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo "📄 [$doc] 내용 (처음 100줄):"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        # Markdown 파일은 길 수 있으니 처음 100줄만 출력
        head -100 "$DOC_FILE"
        echo ""
        echo "... (더 많은 내용은 파일 참조)"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo ""

        export "CRUISE_DOC_${doc%.md}=$DOC_FILE"
    fi
done

echo ""

# ============================================
# 3. API 할당량 체크
# ============================================

echo "🔑 [YouTube API 할당량]"

QUOTA_FILE="$LOG_DIR/api_quota_usage.json"
if [ -f "$QUOTA_FILE" ]; then
    QUOTA_USED=$(grep -o '"used":[0-9]*' "$QUOTA_FILE" | cut -d':' -f2)
    QUOTA_LIMIT=10000
    QUOTA_REMAINING=$((QUOTA_LIMIT - QUOTA_USED))

    echo "  사용: $QUOTA_USED / $QUOTA_LIMIT"
    echo "  남음: $QUOTA_REMAINING"

    if [ $QUOTA_REMAINING -lt 1000 ]; then
        echo "  ⚠️ 할당량 부족! 생산 중단 권장"
    else
        echo "  ✅ 할당량 충분"
    fi
else
    echo '{"used": 0, "limit": 10000}' > "$QUOTA_FILE"
    echo "  ✅ 할당량 초기화 완료"
fi

echo ""

# ============================================
# 4. S등급 달성 조건 표시
# ============================================

echo "🏆 [S등급 달성 조건]"
echo "  Hook: 9.0/10 이상"
echo "  Script: 8.5/10 이상"
echo "  키워드 동기화: 95% 이상"
echo "  Share Rate: 40% 이상"
echo "  Comment Rate: 12% 이상"
echo "  SEO 점수: 85점 이상"
echo "  종합 점수: 90점 이상"
echo ""

echo "✅ [YouTube S등급 시스템] 사전 검증 완료"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
