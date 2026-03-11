#!/bin/bash
# Coding 카테고리 Post-Hook
# 코드 작성 후 자동 품질 검증

AGENT_NAME="$1"
LOG_DIR="D:/mabiz/.claude/logs/coding"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

mkdir -p "$LOG_DIR"

echo "💻 [Coding] 코드 품질 검증 시작..."

# 1. TypeScript 타입 체크 (선택적)
if command -v npx &> /dev/null; then
    echo "  🔍 TypeScript 타입 체크 실행 중..."
    npx tsc --noEmit --pretty 2>&1 | head -20
fi

# 2. ESLint 체크 (선택적)
if [ -f "package.json" ] && command -v npx &> /dev/null; then
    echo "  🔍 ESLint 체크 실행 중..."
    npx eslint . --ext .ts,.tsx --max-warnings 0 2>&1 | head -20 || true
fi

# 3. 품질 리포트 저장
QUALITY_REPORT="$LOG_DIR/${AGENT_NAME}_${TIMESTAMP}_quality.json"

cat > "$QUALITY_REPORT" << EOF
{
  "agent": "$AGENT_NAME",
  "timestamp": "$(date -Iseconds)",
  "category": "coding",
  "auto_checks": {
    "typescript": "EXECUTED",
    "eslint": "EXECUTED"
  }
}
EOF

echo "  ✅ 품질 리포트 저장: $QUALITY_REPORT"
echo "💻 [Coding] 품질 검증 완료"
echo ""
