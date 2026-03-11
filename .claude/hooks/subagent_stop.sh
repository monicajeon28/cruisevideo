#!/bin/bash
# SubagentStop Hook
# 서브에이전트가 완전히 종료되었을 때 실행

# stdin으로 받은 페이로드 읽기
PAYLOAD=$(cat)

LOG_DIR="D:/mabiz/.claude/logs"
mkdir -p "$LOG_DIR"

TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
echo "$PAYLOAD" > "$LOG_DIR/subagent_stop_${TIMESTAMP}.json"

echo "🏁 [SubagentStop] 서브에이전트 종료 감지" >&2

# 성공 응답
cat << 'EOF'
{
  "block": false,
  "feedback": "SubagentStop hook executed"
}
EOF

exit 0
