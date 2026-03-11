#!/bin/bash
# YouTube 카테고리 Post-Hook
# 유튜브 콘텐츠 생산 후 자동 로깅 및 학습 데이터 수집

AGENT_NAME="$1"
LOG_DIR="D:/mabiz/.claude/logs/youtube"
LEARNING_DATA_DIR="D:/mabiz/Learning_Data/youtube_analytics"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

mkdir -p "$LOG_DIR"
mkdir -p "$LEARNING_DATA_DIR"

echo "📺 [YouTube] 후처리 시작..."

# 1. 생산 로그 기록
PRODUCTION_LOG="$LOG_DIR/production_${TIMESTAMP}.json"

cat > "$PRODUCTION_LOG" << EOF
{
  "agent": "$AGENT_NAME",
  "timestamp": "$(date -Iseconds)",
  "status": "completed",
  "next_learning_cycle": "$(date -d '+6 hours' -Iseconds 2>/dev/null || date -v+6H -Iseconds 2>/dev/null)"
}
EOF

echo "  ✅ 생산 로그 저장: $PRODUCTION_LOG"

# 2. API 사용량 업데이트
QUOTA_FILE="$LOG_DIR/api_quota_usage.json"
if [ -f "$QUOTA_FILE" ]; then
    # API 사용량 증가 (실제로는 에이전트가 리포트해야 함)
    case "$AGENT_NAME" in
        youtube-video-producer)
            INCREMENT=1600  # 영상 업로드 비용
            ;;
        youtube-seo-optimizer)
            INCREMENT=100   # 검색 API 비용
            ;;
        *)
            INCREMENT=50    # 기본 비용
            ;;
    esac

    CURRENT_USED=$(grep -o '"used":[0-9]*' "$QUOTA_FILE" | cut -d':' -f2)
    NEW_USED=$((CURRENT_USED + INCREMENT))

    echo "{\"used\": $NEW_USED, \"limit\": 10000}" > "$QUOTA_FILE"
    echo "  📊 API 사용량 업데이트: +$INCREMENT (총 $NEW_USED)"
fi

# 3. 학습 데이터 수집 트리거 (6시간마다)
LAST_LEARNING="$LEARNING_DATA_DIR/last_learning_cycle.txt"
if [ -f "$LAST_LEARNING" ]; then
    LAST_TIME=$(cat "$LAST_LEARNING")
    CURRENT_TIME=$(date +%s)
    ELAPSED=$((CURRENT_TIME - LAST_TIME))

    if [ $ELAPSED -gt 21600 ]; then  # 6시간 = 21600초
        echo "  🎓 학습 사이클 트리거 (6시간 경과)"
        echo "  → youtube-performance-collector 실행 권장"
        date +%s > "$LAST_LEARNING"
    fi
else
    date +%s > "$LAST_LEARNING"
fi

echo "📺 [YouTube] 후처리 완료"
echo ""
