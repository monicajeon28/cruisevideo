#!/bin/bash
# UserPromptSubmit Hook
# 사용자 프롬프트 제출 시 자동 실행

# stdin으로 받은 페이로드 읽기
PAYLOAD=$(cat)

# 로그 저장
LOG_DIR="D:/mabiz/.claude/logs"
mkdir -p "$LOG_DIR"

TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
echo "$PAYLOAD" > "$LOG_DIR/user_prompt_${TIMESTAMP}.json"

echo "🎯 [UserPromptSubmit] 프롬프트 제출 감지" >&2

# 성공 응답 (block: false = 계속 진행)
cat << 'EOF'
{
  "block": false,
  "feedback": "Hook executed: UserPromptSubmit"
}
EOF

exit 0
