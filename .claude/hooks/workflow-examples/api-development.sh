#!/bin/bash
# API 개발 워크플로우 예시
# 사용법: bash .claude/hooks/workflow-examples/api-development.sh

AGENT="api-builder"

echo "=========================================="
echo "🚀 API 개발 워크플로우"
echo "=========================================="
echo ""

# Step 1: Pre-Hook
echo "Step 1: Pre-Hook 실행"
echo "  • 보안 체크 (하드코딩된 시크릿 탐지)"
echo "  • Codebase Graph 로드 (컨텍스트 최적화)"
echo "  • 관련 스킬 로드 (api-first-design, clean-code-mastery)"
echo ""
bash .claude/hooks/quick-hooks.sh pre $AGENT

echo ""
echo "=========================================="
echo "Step 2: Task tool 실행"
echo "=========================================="
echo ""
echo "이제 Claude Code에서 다음을 실행하세요:"
echo ""
echo "  \"api-builder 에이전트로 다음 API를 만들어줘:"
echo "   - GET /api/users (목록 조회)"
echo "   - POST /api/users (생성)"
echo "   - GET /api/users/[id] (단일 조회)\""
echo ""
echo "완료되면 아무 키나 누르세요..."
read -n 1 -s

echo ""
echo ""
echo "=========================================="
echo "Step 3: Post-Hook 실행"
echo "=========================================="
echo "  • TypeScript 타입 체크"
echo "  • ESLint 자동 검사"
echo "  • Quality Gate (복잡도, 커버리지, 점수 계산)"
echo ""
bash .claude/hooks/quick-hooks.sh post $AGENT

echo ""
echo "=========================================="
echo "Step 4: 결과 확인"
echo "=========================================="
echo ""

# Quality Gate 결과
LATEST_QG=$(ls -t .claude/logs/quality-gate/${AGENT}_*_gate.json 2>/dev/null | head -1)
if [ -f "$LATEST_QG" ]; then
    SCORE=$(grep -o '"total_score":[0-9]*' "$LATEST_QG" | cut -d':' -f2)
    STATUS=$(grep -o '"status":"[^"]*"' "$LATEST_QG" | cut -d'"' -f4)

    echo "🏆 Quality Gate 결과:"
    echo "   점수: $SCORE/100"
    echo "   상태: $STATUS"
    echo ""

    if [ "$STATUS" = "PASS" ]; then
        echo "✅ 품질 기준 통과! 커밋 가능합니다."
    else
        echo "⚠️ 품질 개선 필요. refactoring-advisor 실행을 권장합니다."
    fi
else
    echo "ℹ️ Quality Gate 결과 없음"
fi

echo ""
echo "=========================================="
echo "✅ API 개발 워크플로우 완료"
echo "=========================================="
