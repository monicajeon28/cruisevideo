#!/bin/bash
# PostToolUse Hook
# Task tool (서브에이전트) 실행 후 자동 실행

# stdin으로 받은 페이로드 읽기
PAYLOAD=$(cat)

# 에이전트 이름 추출
AGENT_NAME=$(echo "$PAYLOAD" | grep -o '"subagent_type":"[^"]*"' | cut -d'"' -f4)

if [ -z "$AGENT_NAME" ]; then
    AGENT_NAME="unknown"
fi

LOG_DIR="D:/mabiz/.claude/logs"
mkdir -p "$LOG_DIR"

TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
echo "$PAYLOAD" > "$LOG_DIR/post_tool_${AGENT_NAME}_${TIMESTAMP}.json"

echo "✅ [PostToolUse] 에이전트 완료: $AGENT_NAME" >&2

# Hook Router 실행 (post)
bash .claude/hooks/00_hook_router.sh "$AGENT_NAME" post 2>&1 >&2

# 성공 응답
cat << 'EOF'
{
  "block": false,
  "feedback": "Post-hook executed successfully"
}
EOF

exit 0
