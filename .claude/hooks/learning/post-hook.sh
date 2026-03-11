#!/bin/bash
# Learning Feedback Post-Hook
# 학습 데이터 자동 수집 (YouTube, AI 에이전트용)

AGENT_NAME="$1"
LEARNING_DIR="D:/mabiz/Learning_Data"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

echo "🎓 [Learning] 학습 데이터 수집 시작..."

# 에이전트별 학습 데이터 수집
case "$AGENT_NAME" in
    youtube-*)
        # YouTube 에이전트 학습 데이터
        YOUTUBE_DIR="$LEARNING_DIR/youtube_analytics"
        mkdir -p "$YOUTUBE_DIR/feedback"

        FEEDBACK_FILE="$YOUTUBE_DIR/feedback/${AGENT_NAME}_${TIMESTAMP}.json"

        cat > "$FEEDBACK_FILE" << EOF
{
  "agent": "$AGENT_NAME",
  "timestamp": "$(date -Iseconds)",
  "execution_context": {
    "mode": "auto_or_manual",
    "batch_size": "N/A"
  },
  "performance_indicators": {
    "to_be_collected": "조회수, 참여율, 클릭율 등은 실제 업로드 후 6시간 뒤 수집"
  }
}
EOF

        echo "  ✅ YouTube 학습 데이터 저장: $FEEDBACK_FILE"
        ;;

    ai-prompt-engineer|ai-response-validator)
        # AI 에이전트 학습 데이터
        AI_DIR="$LEARNING_DIR/ai_patterns"
        mkdir -p "$AI_DIR/feedback"

        FEEDBACK_FILE="$AI_DIR/feedback/${AGENT_NAME}_${TIMESTAMP}.json"

        cat > "$FEEDBACK_FILE" << EOF
{
  "agent": "$AGENT_NAME",
  "timestamp": "$(date -Iseconds)",
  "ai_metrics": {
    "prompt_quality": "TBD",
    "response_accuracy": "TBD"
  }
}
EOF

        echo "  ✅ AI 학습 데이터 저장: $FEEDBACK_FILE"
        ;;

    cruise-guide|commission-calculator|affiliate-logic-writer)
        # 크루즈 도메인 학습 데이터
        CRUISE_DIR="$LEARNING_DIR/cruise_patterns"
        mkdir -p "$CRUISE_DIR/feedback"

        FEEDBACK_FILE="$CRUISE_DIR/feedback/${AGENT_NAME}_${TIMESTAMP}.json"

        cat > "$FEEDBACK_FILE" << EOF
{
  "agent": "$AGENT_NAME",
  "timestamp": "$(date -Iseconds)",
  "domain_specific": {
    "learning_data_used": "YES",
    "customer_pain_points_addressed": "TBD"
  }
}
EOF

        echo "  ✅ 크루즈 학습 데이터 저장: $FEEDBACK_FILE"
        ;;

    *)
        echo "  ℹ️ 학습 데이터 수집 대상 아님"
        ;;
esac

# 학습 사이클 체크 (일일 집계)
DAILY_SUMMARY="$LEARNING_DIR/daily_summary_$(date +%Y%m%d).json"
if [ ! -f "$DAILY_SUMMARY" ]; then
    cat > "$DAILY_SUMMARY" << EOF
{
  "date": "$(date +%Y-%m-%d)",
  "agents_executed": [],
  "total_executions": 0
}
EOF
fi

# 실행 카운트 증가
CURRENT_COUNT=$(grep -o '"total_executions":[0-9]*' "$DAILY_SUMMARY" | cut -d':' -f2)
NEW_COUNT=$((CURRENT_COUNT + 1))

# 간단한 업데이트 (jq 없이)
sed -i "s/\"total_executions\":$CURRENT_COUNT/\"total_executions\":$NEW_COUNT/" "$DAILY_SUMMARY" 2>/dev/null

echo "  📊 일일 실행 카운트: $NEW_COUNT"
echo "🎓 [Learning] 학습 데이터 수집 완료"
echo ""
