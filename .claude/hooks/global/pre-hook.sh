#!/bin/bash
# 전역 Pre-Hook
# 모든 에이전트 실행 전 공통 작업

AGENT_NAME="$1"
LOG_DIR="D:/mabiz/.claude/logs"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

# 로그 디렉토리 생성
mkdir -p "$LOG_DIR"

echo "========================================" | tee -a "$LOG_DIR/agent_execution.log"
echo "🚀 에이전트 시작: $AGENT_NAME" | tee -a "$LOG_DIR/agent_execution.log"
echo "📅 시간: $(date '+%Y-%m-%d %H:%M:%S')" | tee -a "$LOG_DIR/agent_execution.log"
echo "========================================" | tee -a "$LOG_DIR/agent_execution.log"

# 환경 변수 체크
if [ ! -f "D:/mabiz/.env" ]; then
    echo "⚠️ [경고] .env 파일이 없습니다" | tee -a "$LOG_DIR/agent_execution.log"
fi

# Git 상태 체크 (Git 관련 에이전트가 아닌 경우에도 유용)
if [ -d ".git" ]; then
    BRANCH=$(git branch --show-current 2>/dev/null)
    echo "🌿 현재 브랜치: $BRANCH" | tee -a "$LOG_DIR/agent_execution.log"
fi

# 컨텍스트 크기 측정 (선택적)
CONTEXT_SIZE=$(find . -name "*.ts" -o -name "*.tsx" -o -name "*.py" | wc -l)
echo "📊 프로젝트 파일 수: $CONTEXT_SIZE" | tee -a "$LOG_DIR/agent_execution.log"

echo "" | tee -a "$LOG_DIR/agent_execution.log"
