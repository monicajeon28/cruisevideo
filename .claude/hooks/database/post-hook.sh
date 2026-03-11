#!/bin/bash
# Database 카테고리 Post-Hook
# DB 작업 후 로깅 및 검증

AGENT_NAME="$1"
LOG_DIR="D:/mabiz/.claude/logs/database"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

mkdir -p "$LOG_DIR"

echo "🗄️ [Database] DB 작업 후처리 시작..."

# DB 작업 로그
DB_LOG="$LOG_DIR/${AGENT_NAME}_${TIMESTAMP}_db.json"

cat > "$DB_LOG" << EOF
{
  "agent": "$AGENT_NAME",
  "timestamp": "$(date -Iseconds)",
  "category": "database",
  "operation": "${AGENT_NAME}",
  "status": "completed"
}
EOF

echo "  ✅ DB 작업 로그 저장: $DB_LOG"

# 마이그레이션인 경우 추가 체크
if [ "$AGENT_NAME" = "schema-migration" ]; then
    echo "  🔄 마이그레이션 완료 - DB 동기화 확인 필요"
fi

echo "🗄️ [Database] 후처리 완료"
echo ""
