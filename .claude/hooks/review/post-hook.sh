#!/bin/bash
# Review 카테고리 Post-Hook
# 코드 리뷰 후 자동 리포트 생성 및 점수 저장

AGENT_NAME="$1"
LOG_DIR="D:/mabiz/.claude/logs/review"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

mkdir -p "$LOG_DIR"

echo "🔍 [Review] 리뷰 결과 저장 시작..."

# 리뷰 리포트 저장
REVIEW_REPORT="$LOG_DIR/${AGENT_NAME}_${TIMESTAMP}_review.json"

cat > "$REVIEW_REPORT" << EOF
{
  "agent": "$AGENT_NAME",
  "timestamp": "$(date -Iseconds)",
  "category": "review",
  "review_type": "${AGENT_NAME}",
  "git_branch": "$(git branch --show-current 2>/dev/null || echo 'N/A')",
  "last_commit": "$(git log -1 --oneline 2>/dev/null || echo 'N/A')"
}
EOF

echo "  ✅ 리뷰 리포트 저장: $REVIEW_REPORT"

# 추가 품질 게이트 체크
if [ "$AGENT_NAME" = "pre-commit-validator" ]; then
    echo "  🚦 커밋 전 최종 검증 완료"
fi

echo "🔍 [Review] 리뷰 결과 저장 완료"
echo ""
