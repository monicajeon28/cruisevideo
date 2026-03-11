#!/bin/bash
# PreToolUse Hook
# Task tool (서브에이전트) 실행 전 자동 실행

# 디버깅 로그
DEBUG_LOG="D:/mabiz/.claude/logs/hook_debug.log"
mkdir -p "D:/mabiz/.claude/logs"

echo "=================================" >> "$DEBUG_LOG"
echo "[$(date)] PreToolUse Hook 시작" >> "$DEBUG_LOG"

# stdin으로 받은 페이로드 읽기 (tool_name, tool_input 등 포함)
PAYLOAD=$(cat)

echo "Payload 수신: $PAYLOAD" >> "$DEBUG_LOG"

# 페이로드에서 에이전트 이름 추출 (jq 없이)
AGENT_NAME=$(echo "$PAYLOAD" | grep -o '"subagent_type":"[^"]*"' | cut -d'"' -f4)

# tool_name도 추출
TOOL_NAME=$(echo "$PAYLOAD" | grep -o '"tool_name":"[^"]*"' | cut -d'"' -f4)

echo "Tool Name: $TOOL_NAME" >> "$DEBUG_LOG"
echo "Agent Name: $AGENT_NAME" >> "$DEBUG_LOG"

if [ -z "$AGENT_NAME" ]; then
    AGENT_NAME="unknown"
fi

LOG_DIR="D:/mabiz/.claude/logs"
mkdir -p "$LOG_DIR"

TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
echo "$PAYLOAD" > "$LOG_DIR/pre_tool_${AGENT_NAME}_${TIMESTAMP}.json"

echo "🚀 [PreToolUse] 에이전트 시작: $AGENT_NAME" >&2
echo "🚀 [PreToolUse] Tool: $TOOL_NAME, Agent: $AGENT_NAME" >> "$DEBUG_LOG"

# Hook Router 실행 (pre)
bash .claude/hooks/00_hook_router.sh "$AGENT_NAME" pre >> "$DEBUG_LOG" 2>&1

echo "[$(date)] PreToolUse Hook 완료" >> "$DEBUG_LOG"

# 성공 응답 (계속 진행)
cat << 'EOF'
{
  "block": false,
  "feedback": "Pre-hook executed successfully"
}
EOF

exit 0
