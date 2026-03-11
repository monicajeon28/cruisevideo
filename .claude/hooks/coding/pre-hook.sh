#!/bin/bash
# Coding 카테고리 Pre-Hook
# 코드 작성 전 컨텍스트 최적화 및 스킬 로드

AGENT_NAME="$1"

echo "💻 [Coding] 코딩 환경 준비 시작..."

# 1. codebase-graph 확인
GRAPH_FILE="D:/mabiz/codebase_graph.md"
if [ -f "$GRAPH_FILE" ]; then
    echo "  ✅ Codebase Graph 발견: $GRAPH_FILE"
    echo "CODEBASE_GRAPH=$GRAPH_FILE"
else
    echo "  ℹ️ Codebase Graph 없음 (전체 탐색 모드)"
fi

# 2. 관련 스킬 로드
case "$AGENT_NAME" in
    api-builder)
        echo "  📚 스킬 로드: api-first-design, clean-code-mastery, security-shield"
        ;;
    code-writer)
        echo "  📚 스킬 로드: clean-code-mastery, naming-convention-guard"
        ;;
    security-guardian)
        echo "  📚 스킬 로드: security-shield"
        ;;
esac

# 3. Git 상태 확인
if [ -d ".git" ]; then
    CHANGED_FILES=$(git diff --name-only | wc -l)
    echo "  📝 변경된 파일: $CHANGED_FILES개"
fi

echo "💻 [Coding] 준비 완료"
echo ""
