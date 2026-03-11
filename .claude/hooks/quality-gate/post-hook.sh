#!/bin/bash
# Quality Gate Post-Hook
# 코드 작성 후 품질 게이트 (점수 80 미만 시 경고)

AGENT_NAME="$1"
LOG_DIR="D:/mabiz/.claude/logs/quality-gate"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

mkdir -p "$LOG_DIR"

echo "🚦 [Quality Gate] 품질 게이트 검증 시작..."

# 1. 복잡도 체크 (cyclomatic complexity)
# 간단한 함수 길이 체크로 근사
echo "  📏 함수 복잡도 체크 중..."

# 최근 변경된 TypeScript 파일에서 긴 함수 탐지
LONG_FUNCTIONS=$(git diff --name-only | grep -E '\.(ts|tsx)$' | xargs -I {} sh -c '
    awk "/^function|^export function|^const.*=.*=>/ {start=NR} start && NR-start>50 {print FILENAME\":\"NR; start=0}" {}
' 2>/dev/null | wc -l)

if [ "$LONG_FUNCTIONS" -gt 0 ]; then
    echo "  ⚠️ 긴 함수 발견: $LONG_FUNCTIONS개 (50줄 초과)"
    COMPLEXITY_SCORE=60
else
    echo "  ✅ 함수 복잡도 양호"
    COMPLEXITY_SCORE=90
fi

# 2. 테스트 커버리지 체크
echo "  🧪 테스트 커버리지 체크 중..."
COVERAGE_SCORE=0

if [ -f "coverage/coverage-summary.json" ]; then
    # Jest 커버리지 파싱
    COVERAGE=$(grep -o '"lines":{"total":[0-9]*,"covered":[0-9]*' coverage/coverage-summary.json | head -1)
    TOTAL=$(echo "$COVERAGE" | grep -o 'total":[0-9]*' | cut -d':' -f2)
    COVERED=$(echo "$COVERAGE" | grep -o 'covered":[0-9]*' | cut -d':' -f2)

    if [ -n "$TOTAL" ] && [ "$TOTAL" -gt 0 ]; then
        COVERAGE_SCORE=$((COVERED * 100 / TOTAL))
        echo "  📊 커버리지: $COVERAGE_SCORE%"
    fi
else
    echo "  ℹ️ 커버리지 리포트 없음"
    COVERAGE_SCORE=50  # 기본값
fi

# 3. ESLint 경고 개수
echo "  🔍 ESLint 경고 체크 중..."
ESLINT_WARNINGS=0

if command -v npx &> /dev/null; then
    ESLINT_OUTPUT=$(npx eslint . --ext .ts,.tsx --format json 2>/dev/null || echo '[]')
    ESLINT_WARNINGS=$(echo "$ESLINT_OUTPUT" | grep -o '"warningCount":[0-9]*' | cut -d':' -f2 | awk '{s+=$1} END {print s}')
    echo "  ⚠️ ESLint 경고: $ESLINT_WARNINGS개"
fi

# 경고 개수에 따른 점수 (0개=100, 10개=80, 20개 이상=60)
# 빈 문자열 처리
if [ -z "$ESLINT_WARNINGS" ]; then
    ESLINT_WARNINGS=0
fi

if [ "$ESLINT_WARNINGS" -eq 0 ]; then
    ESLINT_SCORE=100
elif [ "$ESLINT_WARNINGS" -lt 10 ]; then
    ESLINT_SCORE=80
else
    ESLINT_SCORE=60
fi

# 4. 종합 점수 계산
TOTAL_SCORE=$(( (COMPLEXITY_SCORE + COVERAGE_SCORE + ESLINT_SCORE) / 3 ))

echo ""
echo "========================================="
echo "🏆 종합 품질 점수: $TOTAL_SCORE/100"
echo "========================================="
echo "  • 복잡도: $COMPLEXITY_SCORE"
echo "  • 커버리지: $COVERAGE_SCORE"
echo "  • ESLint: $ESLINT_SCORE"
echo "========================================="

# 5. 품질 게이트 판정
if [ "$TOTAL_SCORE" -lt 80 ]; then
    echo "❌ 품질 게이트 FAIL (기준: 80점)"
    echo "   개선 권장: refactoring-advisor 또는 test-guardian 실행"
    GATE_STATUS="FAIL"
else
    echo "✅ 품질 게이트 PASS"
    GATE_STATUS="PASS"
fi

# 6. 리포트 저장
QUALITY_REPORT="$LOG_DIR/${AGENT_NAME}_${TIMESTAMP}_gate.json"

cat > "$QUALITY_REPORT" << EOF
{
  "agent": "$AGENT_NAME",
  "timestamp": "$(date -Iseconds)",
  "total_score": $TOTAL_SCORE,
  "breakdown": {
    "complexity": $COMPLEXITY_SCORE,
    "coverage": $COVERAGE_SCORE,
    "eslint": $ESLINT_SCORE
  },
  "status": "$GATE_STATUS",
  "threshold": 80
}
EOF

echo "💾 품질 리포트 저장: $QUALITY_REPORT"
echo "🚦 [Quality Gate] 검증 완료"
echo ""
