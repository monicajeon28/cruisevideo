#!/bin/bash
# 전역 Post-Hook
# 모든 에이전트 실행 후 공통 작업

AGENT_NAME="$1"
LOG_DIR="D:/mabiz/.claude/logs"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

echo "========================================" | tee -a "$LOG_DIR/agent_execution.log"
echo "✅ 에이전트 완료: $AGENT_NAME" | tee -a "$LOG_DIR/agent_execution.log"
echo "📅 시간: $(date '+%Y-%m-%d %H:%M:%S')" | tee -a "$LOG_DIR/agent_execution.log"
echo "========================================" | tee -a "$LOG_DIR/agent_execution.log"

# 성능 메트릭 저장 (선택적)
METRICS_FILE="$LOG_DIR/metrics/${AGENT_NAME}_${TIMESTAMP}.json"
mkdir -p "$LOG_DIR/metrics"

cat > "$METRICS_FILE" << EOF
{
  "agent": "$AGENT_NAME",
  "timestamp": "$(date -Iseconds)",
  "status": "completed"
}
EOF

echo "💾 메트릭 저장: $METRICS_FILE" | tee -a "$LOG_DIR/agent_execution.log"
echo "" | tee -a "$LOG_DIR/agent_execution.log"
