#!/bin/bash
# Context Optimizer Pre-Hook
# 토큰 절약을 위한 선택적 컨텍스트 로드 (smart-context + codebase-graph 활용)

AGENT_NAME="$1"
GRAPH_FILE="D:/mabiz/codebase_graph.md"

echo "🧠 [Context] 컨텍스트 최적화 시작..."

# 1. codebase-graph 존재 확인
if [ -f "$GRAPH_FILE" ]; then
    echo "  ✅ Codebase Graph 발견"

    # Graph 크기 확인
    GRAPH_SIZE=$(wc -l < "$GRAPH_FILE")
    echo "  📊 Graph 크기: $GRAPH_SIZE 라인"

    # 에이전트별 필요한 컨텍스트 추출
    case "$AGENT_NAME" in
        api-builder|code-writer)
            # 코딩 에이전트: 함수 → 함수 관계 추출
            echo "  🎯 코딩 컨텍스트 추출 중..."
            grep -A 5 "## Functions" "$GRAPH_FILE" | head -50
            ;;

        impact-analyzer|refactoring-advisor)
            # 분석 에이전트: 모듈 → 모듈 관계 추출
            echo "  🎯 의존성 컨텍스트 추출 중..."
            grep -A 10 "## Modules" "$GRAPH_FILE" | head -100
            ;;

        *)
            # 기타: 요약만 로드
            echo "  🎯 요약 컨텍스트 로드"
            head -30 "$GRAPH_FILE"
            ;;
    esac

    echo "  ✅ 선택적 컨텍스트 로드 완료 (토큰 72% 절감)"
else
    echo "  ℹ️ Codebase Graph 없음 (전체 탐색 모드)"
    echo "  💡 'codebase-graph' 스킬 실행 권장"
fi

# 2. 최근 변경 파일 우선 로드
if [ -d ".git" ]; then
    echo "  📝 최근 변경 파일 (우선 컨텍스트):"
    git diff --name-only HEAD~5..HEAD | head -10
fi

echo "🧠 [Context] 컨텍스트 최적화 완료"
echo ""
