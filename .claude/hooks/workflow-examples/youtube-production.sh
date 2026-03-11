#!/bin/bash
# YouTube 콘텐츠 자동 생산 워크플로우
# 사용법: bash .claude/hooks/workflow-examples/youtube-production.sh [count]

AGENT="youtube-content-orchestrator"
COUNT="${1:-150}"

echo "=========================================="
echo "📺 YouTube 콘텐츠 자동 생산"
echo "=========================================="
echo "목표: $COUNT개"
echo ""

# Step 1: Pre-Hook (리소스 체크, API 할당량)
echo "Step 1: 사전 검증"
echo "  • CPU/메모리 리소스 체크"
echo "  • YouTube API 할당량 확인"
echo "  • 학습 데이터 로드"
echo ""
bash .claude/hooks/quick-hooks.sh pre $AGENT

echo ""

# 리소스 리포트 확인
LATEST_RESOURCE=$(ls -t .claude/logs/parallel/${AGENT}_*_resources.json 2>/dev/null | head -1)
if [ -f "$LATEST_RESOURCE" ]; then
    BATCH_SIZE=$(grep -o '"recommended_batch_size":[0-9]*' "$LATEST_RESOURCE" | cut -d':' -f2)
    CPU=$(grep -o '"cpu_usage":[0-9]*' "$LATEST_RESOURCE" | cut -d':' -f2)
    MEMORY=$(grep -o '"memory_usage":[0-9]*' "$LATEST_RESOURCE" | cut -d':' -f2)

    echo "=========================================="
    echo "📊 리소스 상태"
    echo "=========================================="
    echo "  CPU: ${CPU}%"
    echo "  메모리: ${MEMORY}%"
    echo "  권장 배치 크기: ${BATCH_SIZE}개"
    echo ""

    if [ "$BATCH_SIZE" -lt 10 ]; then
        echo "⚠️ 리소스 부족! 배치 크기가 작습니다."
        echo "   계속하시겠습니까? (y/n)"
        read -n 1 -r
        echo ""
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            echo "중단됨"
            exit 1
        fi
    fi
fi

echo "=========================================="
echo "Step 2: Task tool 실행"
echo "=========================================="
echo ""
echo "이제 Claude Code에서 다음을 실행하세요:"
echo ""
echo "  \"youtube-content-orchestrator 에이전트로"
echo "   $COUNT개 콘텐츠 자동 생산해줘\""
echo ""
echo "생산 완료 후 아무 키나 누르세요..."
read -n 1 -s

echo ""
echo ""
echo "=========================================="
echo "Step 3: Post-Hook (학습 데이터 수집)"
echo "=========================================="
echo "  • 생산 로그 기록"
echo "  • API 사용량 업데이트"
echo "  • 학습 사이클 트리거 (6시간마다)"
echo ""
bash .claude/hooks/quick-hooks.sh post $AGENT

echo ""
echo "=========================================="
echo "✅ 생산 완료"
echo "=========================================="
echo ""

# YouTube 로그 확인
LATEST_PROD=$(ls -t .claude/logs/youtube/production_*.json 2>/dev/null | head -1)
if [ -f "$LATEST_PROD" ]; then
    echo "📊 생산 리포트: $LATEST_PROD"
    cat "$LATEST_PROD"
    echo ""
fi

# API 사용량
QUOTA_FILE=".claude/logs/youtube/api_quota_usage.json"
if [ -f "$QUOTA_FILE" ]; then
    USED=$(grep -o '"used":[0-9]*' "$QUOTA_FILE" | cut -d':' -f2)
    LIMIT=$(grep -o '"limit":[0-9]*' "$QUOTA_FILE" | cut -d':' -f2)
    REMAINING=$((LIMIT - USED))

    echo "📊 YouTube API 할당량:"
    echo "   사용: $USED / $LIMIT"
    echo "   남음: $REMAINING"
    echo ""

    if [ "$REMAINING" -lt 1000 ]; then
        echo "⚠️ API 할당량 부족! 내일까지 대기 권장"
    fi
fi

echo ""
echo "생산된 영상은 output/videos/ 디렉토리에서 확인하세요"
