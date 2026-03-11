#!/bin/bash
# Run Agent with Hooks
# 사용법: bash .claude/hooks/run-agent.sh <agent-name>

AGENT_NAME="$1"

if [ -z "$AGENT_NAME" ]; then
    echo "사용법: bash .claude/hooks/run-agent.sh <agent-name>"
    echo ""
    echo "예시:"
    echo "  bash .claude/hooks/run-agent.sh api-builder"
    echo "  bash .claude/hooks/run-agent.sh youtube-content-orchestrator"
    echo "  bash .claude/hooks/run-agent.sh commission-calculator"
    exit 1
fi

echo "=========================================="
echo "🚀 에이전트 실행 with Hooks"
echo "=========================================="
echo "에이전트: $AGENT_NAME"
echo ""

# Pre-Hook 실행
echo "⏳ Pre-Hook 실행 중..."
bash .claude/hooks/00_hook_router.sh "$AGENT_NAME" pre

echo ""
echo "=========================================="
echo "✅ Pre-Hook 완료"
echo "=========================================="
echo ""
echo "📝 이제 Task tool로 다음 에이전트를 실행하세요:"
echo "   subagent_type: $AGENT_NAME"
echo ""
echo "완료 후 아무 키나 누르면 Post-Hook을 실행합니다..."
read -n 1 -s

echo ""
echo ""
echo "⏳ Post-Hook 실행 중..."
bash .claude/hooks/00_hook_router.sh "$AGENT_NAME" post

echo ""
echo "=========================================="
echo "✅ 완료!"
echo "=========================================="
echo ""

# 결과 요약
echo "📊 생성된 로그:"
echo ""

# Quality Gate 점수 (있는 경우)
LATEST_QUALITY=$(ls -t .claude/logs/quality-gate/${AGENT_NAME}_*_gate.json 2>/dev/null | head -1)
if [ -f "$LATEST_QUALITY" ]; then
    SCORE=$(grep -o '"total_score":[0-9]*' "$LATEST_QUALITY" | cut -d':' -f2)
    STATUS=$(grep -o '"status":"[^"]*"' "$LATEST_QUALITY" | cut -d'"' -f4)
    echo "  🏆 Quality Gate: $SCORE/100 ($STATUS)"
    echo "     파일: $LATEST_QUALITY"
    echo ""
fi

# Parallel 리소스 (Orchestrator인 경우)
if [[ "$AGENT_NAME" == *"orchestrator"* ]]; then
    LATEST_RESOURCE=$(ls -t .claude/logs/parallel/${AGENT_NAME}_*_resources.json 2>/dev/null | head -1)
    if [ -f "$LATEST_RESOURCE" ]; then
        BATCH_SIZE=$(grep -o '"recommended_batch_size":[0-9]*' "$LATEST_RESOURCE" | cut -d':' -f2)
        echo "  ⚡ 권장 배치 크기: $BATCH_SIZE개"
        echo "     파일: $LATEST_RESOURCE"
        echo ""
    fi
fi

# 전역 로그
echo "  📋 전역 로그: .claude/logs/agent_execution.log"
echo ""
