#!/bin/bash
# Parallel Execution Pre-Hook
# 병렬 실행 시 리소스 체크 및 배치 크기 조절

AGENT_NAME="$1"
LOG_DIR="D:/mabiz/.claude/logs/parallel"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

mkdir -p "$LOG_DIR"

echo "⚡ [Parallel] 병렬 실행 리소스 체크 시작..."

# 1. CPU 사용률 체크 (Windows)
if command -v wmic &> /dev/null; then
    CPU_USAGE=$(wmic cpu get loadpercentage 2>/dev/null | grep -o '[0-9]*' | head -1)
    if [ -z "$CPU_USAGE" ]; then
        CPU_USAGE=50  # wmic 실패 시 기본값
    fi
    echo "  💻 CPU 사용률: ${CPU_USAGE}%"
else
    # Linux/Mac
    if command -v top &> /dev/null; then
        CPU_USAGE=$(top -bn1 2>/dev/null | grep "Cpu(s)" | sed "s/.*, *\([0-9.]*\)%* id.*/\1/" | awk '{print 100 - $1}')
        if [ -z "$CPU_USAGE" ]; then
            CPU_USAGE=50
        fi
        echo "  💻 CPU 사용률: ${CPU_USAGE}%"
    else
        CPU_USAGE=50  # 기본값
        echo "  💻 CPU 체크 건너뜀 (명령어 없음, 기본값: 50%)"
    fi
fi

# 2. 메모리 사용률 체크
if command -v free &> /dev/null; then
    MEMORY_USAGE=$(free 2>/dev/null | grep Mem | awk '{printf "%.0f", $3/$2 * 100}')
    if [ -z "$MEMORY_USAGE" ]; then
        MEMORY_USAGE=50
    fi
    echo "  🧠 메모리 사용률: ${MEMORY_USAGE}%"
else
    echo "  🧠 메모리 체크 건너뜀 (명령어 없음, 기본값: 50%)"
    MEMORY_USAGE=50  # 기본값
fi

# 3. 권장 배치 크기 계산
# 안전한 정수 변환
if [ -z "$CPU_USAGE" ] || ! [[ "$CPU_USAGE" =~ ^[0-9]+$ ]]; then
    CPU_USAGE=50
fi

if [ -z "$MEMORY_USAGE" ] || ! [[ "$MEMORY_USAGE" =~ ^[0-9]+$ ]]; then
    MEMORY_USAGE=50
fi

if [ "$CPU_USAGE" -lt 50 ] && [ "$MEMORY_USAGE" -lt 50 ]; then
    BATCH_SIZE=50
    RECOMMENDATION="🟢 리소스 충분: 대용량 배치 (50개) 권장"
elif [ "$CPU_USAGE" -lt 70 ] && [ "$MEMORY_USAGE" -lt 70 ]; then
    BATCH_SIZE=25
    RECOMMENDATION="🟡 리소스 보통: 중형 배치 (25개) 권장"
elif [ "$CPU_USAGE" -lt 85 ] && [ "$MEMORY_USAGE" -lt 85 ]; then
    BATCH_SIZE=10
    RECOMMENDATION="🟠 리소스 부족: 소형 배치 (10개) 권장"
else
    BATCH_SIZE=1
    RECOMMENDATION="🔴 리소스 한계: 순차 처리 (1개) 권장"
fi

echo ""
echo "========================================="
echo "⚡ 병렬 실행 권장 설정"
echo "========================================="
echo "  $RECOMMENDATION"
echo "  권장 배치 크기: $BATCH_SIZE개"
echo "========================================="

# 4. 병렬 실행 에이전트 전용 경고
if [[ "$AGENT_NAME" == *"orchestrator"* ]]; then
    echo "  🎯 Orchestrator 감지: 배치 크기 $BATCH_SIZE 적용 권장"
fi

# 5. 리소스 리포트 저장
RESOURCE_REPORT="$LOG_DIR/${AGENT_NAME}_${TIMESTAMP}_resources.json"

cat > "$RESOURCE_REPORT" << EOF
{
  "agent": "$AGENT_NAME",
  "timestamp": "$(date -Iseconds)",
  "resources": {
    "cpu_usage": ${CPU_USAGE},
    "memory_usage": ${MEMORY_USAGE},
    "recommended_batch_size": ${BATCH_SIZE}
  }
}
EOF

echo "💾 리소스 리포트 저장: $RESOURCE_REPORT"
echo "⚡ [Parallel] 리소스 체크 완료"
echo ""
