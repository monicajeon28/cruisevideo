#!/bin/bash
# 전역 Error-Hook
# 모든 에이전트에서 에러 발생 시 공통 작업

AGENT_NAME="$1"
ERROR_MSG="$2"
LOG_DIR="D:/mabiz/.claude/logs"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

echo "========================================" | tee -a "$LOG_DIR/agent_errors.log"
echo "❌ 에이전트 에러: $AGENT_NAME" | tee -a "$LOG_DIR/agent_errors.log"
echo "📅 시간: $(date '+%Y-%m-%d %H:%M:%S')" | tee -a "$LOG_DIR/agent_errors.log"
echo "🚨 에러 메시지: $ERROR_MSG" | tee -a "$LOG_DIR/agent_errors.log"
echo "========================================" | tee -a "$LOG_DIR/agent_errors.log"

# 에러 컨텍스트 수집
ERROR_REPORT="$LOG_DIR/errors/${AGENT_NAME}_${TIMESTAMP}_error.json"
mkdir -p "$LOG_DIR/errors"

cat > "$ERROR_REPORT" << EOF
{
  "agent": "$AGENT_NAME",
  "timestamp": "$(date -Iseconds)",
  "error": "$ERROR_MSG",
  "git_branch": "$(git branch --show-current 2>/dev/null || echo 'N/A')",
  "last_commit": "$(git log -1 --oneline 2>/dev/null || echo 'N/A')"
}
EOF

echo "💾 에러 리포트 저장: $ERROR_REPORT" | tee -a "$LOG_DIR/agent_errors.log"

# bug-fixer 에이전트 자동 호출 (선택적)
echo "🔧 bug-fixer 에이전트 자동 호출 권장" | tee -a "$LOG_DIR/agent_errors.log"
echo "" | tee -a "$LOG_DIR/agent_errors.log"
