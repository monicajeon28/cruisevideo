#!/bin/bash
# Testing 카테고리 Post-Hook
# 테스트 실행 후 결과 수집 및 커버리지 리포트

AGENT_NAME="$1"
LOG_DIR="D:/mabiz/.claude/logs/testing"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

mkdir -p "$LOG_DIR"

echo "🧪 [Testing] 테스트 결과 수집 시작..."

# 테스트 결과 로그
TEST_LOG="$LOG_DIR/${AGENT_NAME}_${TIMESTAMP}_test.json"

cat > "$TEST_LOG" << EOF
{
  "agent": "$AGENT_NAME",
  "timestamp": "$(date -Iseconds)",
  "category": "testing",
  "test_type": "${AGENT_NAME}",
  "status": "completed"
}
EOF

echo "  ✅ 테스트 로그 저장: $TEST_LOG"

# 커버리지 체크 (Jest 기준)
if [ -d "coverage" ]; then
    echo "  📊 커버리지 리포트 발견: coverage/"
    if [ -f "coverage/coverage-summary.json" ]; then
        COVERAGE=$(grep -o '"total":{[^}]*}' coverage/coverage-summary.json | head -1)
        echo "  📈 커버리지: $COVERAGE"
    fi
fi

echo "🧪 [Testing] 결과 수집 완료"
echo ""
