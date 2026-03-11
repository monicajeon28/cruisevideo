#!/bin/bash
# Quick Hooks - 빠른 Hook 실행 헬퍼

show_help() {
    echo "Quick Hooks - 빠른 Hook 실행 헬퍼"
    echo ""
    echo "사용법:"
    echo "  bash .claude/hooks/quick-hooks.sh <명령> [에이전트]"
    echo ""
    echo "명령:"
    echo "  pre <agent>      - Pre-Hook만 실행"
    echo "  post <agent>     - Post-Hook만 실행"
    echo "  full <agent>     - Pre → (대기) → Post 전체 실행"
    echo "  test             - 테스트 에이전트로 Hook 테스트"
    echo "  logs [agent]     - 로그 확인"
    echo "  clean            - 오래된 로그 정리"
    echo ""
    echo "자주 쓰는 에이전트:"
    echo "  • api-builder              - API 설계/코드 생성"
    echo "  • commission-calculator    - 크루즈 수수료 계산"
    echo "  • youtube-content-orchestrator - 유튜브 콘텐츠 생산"
    echo "  • bug-fixer               - 버그 자동 수정"
    echo "  • code-writer             - 코드 작성"
    echo ""
    echo "예시:"
    echo "  bash .claude/hooks/quick-hooks.sh pre api-builder"
    echo "  bash .claude/hooks/quick-hooks.sh full commission-calculator"
    echo "  bash .claude/hooks/quick-hooks.sh logs youtube-content-orchestrator"
}

CMD="$1"
AGENT="$2"

case "$CMD" in
    pre)
        if [ -z "$AGENT" ]; then
            echo "에러: 에이전트 이름이 필요합니다"
            echo "사용법: bash .claude/hooks/quick-hooks.sh pre <agent>"
            exit 1
        fi
        echo "🚀 Pre-Hook: $AGENT"
        bash .claude/hooks/00_hook_router.sh "$AGENT" pre
        ;;

    post)
        if [ -z "$AGENT" ]; then
            echo "에러: 에이전트 이름이 필요합니다"
            echo "사용법: bash .claude/hooks/quick-hooks.sh post <agent>"
            exit 1
        fi
        echo "✅ Post-Hook: $AGENT"
        bash .claude/hooks/00_hook_router.sh "$AGENT" post
        ;;

    full)
        if [ -z "$AGENT" ]; then
            echo "에러: 에이전트 이름이 필요합니다"
            exit 1
        fi
        bash .claude/hooks/run-agent.sh "$AGENT"
        ;;

    test)
        echo "🧪 Hook 테스트 실행..."
        bash .claude/hooks/00_hook_router.sh test-agent pre
        echo ""
        bash .claude/hooks/00_hook_router.sh test-agent post
        echo ""
        echo "✅ 테스트 완료. 로그 확인:"
        tail -20 .claude/logs/agent_execution.log
        ;;

    logs)
        if [ -z "$AGENT" ]; then
            # 전체 로그
            echo "📋 최근 실행 로그:"
            tail -50 .claude/logs/agent_execution.log
        else
            # 특정 에이전트 로그
            echo "📋 $AGENT 관련 로그:"
            echo ""

            # Quality Gate
            if [ -d ".claude/logs/quality-gate" ]; then
                LATEST_QG=$(ls -t .claude/logs/quality-gate/${AGENT}_*_gate.json 2>/dev/null | head -1)
                if [ -f "$LATEST_QG" ]; then
                    echo "🏆 Quality Gate:"
                    cat "$LATEST_QG"
                    echo ""
                fi
            fi

            # Cruise Guide
            if [ -d ".claude/logs/cruise-guide" ]; then
                LATEST_CG=$(ls -t .claude/logs/cruise-guide/${AGENT}_*_quality.json 2>/dev/null | head -1)
                if [ -f "$LATEST_CG" ]; then
                    echo "🚢 Cruise Guide:"
                    cat "$LATEST_CG"
                    echo ""
                fi
            fi

            # YouTube
            if [ -d ".claude/logs/youtube" ]; then
                LATEST_YT=$(ls -t .claude/logs/youtube/production_*.json 2>/dev/null | head -1)
                if [ -f "$LATEST_YT" ]; then
                    echo "📺 YouTube:"
                    cat "$LATEST_YT"
                    echo ""
                fi
            fi

            # 전역 로그에서 해당 에이전트 추출
            echo "📋 실행 기록:"
            grep "$AGENT" .claude/logs/agent_execution.log | tail -20
        fi
        ;;

    clean)
        echo "🧹 오래된 로그 정리 중..."

        # 7일 이상 된 로그 삭제
        find .claude/logs -name "*.json" -mtime +7 -delete 2>/dev/null

        # 로그 파일 압축 (1000줄 이상일 경우)
        if [ -f ".claude/logs/agent_execution.log" ]; then
            LINES=$(wc -l < .claude/logs/agent_execution.log)
            if [ "$LINES" -gt 1000 ]; then
                tail -500 .claude/logs/agent_execution.log > .claude/logs/agent_execution.log.tmp
                mv .claude/logs/agent_execution.log.tmp .claude/logs/agent_execution.log
                echo "  ✅ agent_execution.log 압축 (500줄 유지)"
            fi
        fi

        echo "✅ 정리 완료"
        ;;

    help|--help|-h|"")
        show_help
        ;;

    *)
        echo "알 수 없는 명령: $CMD"
        echo ""
        show_help
        exit 1
        ;;
esac
