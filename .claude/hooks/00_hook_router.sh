#!/bin/bash
# Hook Router - 에이전트별 자동 Hook 라우팅
# 각 에이전트가 실행될 때 자동으로 적절한 Hook을 실행

AGENT_NAME="$1"
HOOK_TYPE="$2"  # pre, post, error
HOOK_DIR="$(dirname "$0")"

# 에이전트 카테고리 추출
get_category() {
    local agent="$1"
    case "$agent" in
        # A: Planning
        dependency-planner|idea-to-spec|architecture-designer|project-scaffolder|mvp-definer)
            echo "planning" ;;

        # B: Coding
        context-optimizer|api-builder|code-writer|module-boundary|security-guardian|type-safety)
            echo "coding" ;;

        # C: Review
        comprehensive-reviewer|code-quality-checker|impact-analyzer|documentation-generator|pre-commit-validator|refactoring-advisor|test-guardian)
            echo "review" ;;

        # D: Production
        cost-advisor|deployment-checker|scale-advisor)
            echo "production" ;;

        # F: Database
        data-seeder|database-optimizer|database-query|schema-migration)
            echo "database" ;;

        # G: Git
        branch-strategy|git-commit|merge-conflict|pr-creator)
            echo "git" ;;

        # K: Error
        error-manager|bug-fixer)
            echo "error" ;;

        # L: Cruise Guide (도메인 특화)
        commission-calculator|affiliate-logic-writer|admin-page-builder|image-manager|message-template|partner-*)
            echo "cruise-guide" ;;

        # S: Testing
        visual-regression|e2e-test-builder|load-tester)
            echo "testing" ;;

        # Y: YouTube
        youtube-*)
            echo "youtube" ;;

        # N: AI
        ai-prompt-engineer|ai-response-validator)
            echo "ai" ;;

        *)
            echo "general" ;;
    esac
}

# Hook 실행
run_hook() {
    local category="$1"
    local hook_type="$2"
    local hook_file="$HOOK_DIR/${category}/${hook_type}-hook.sh"

    if [ -f "$hook_file" ]; then
        echo "[Hook Router] 실행: $hook_file"
        bash "$hook_file" "$AGENT_NAME"
    fi
}

# 전역 Hook 실행 (모든 에이전트 공통)
global_hook="$HOOK_DIR/global/${HOOK_TYPE}-hook.sh"
if [ -f "$global_hook" ]; then
    echo "[Hook Router] 전역 Hook 실행: $global_hook"
    bash "$global_hook" "$AGENT_NAME"
fi

# 카테고리별 Hook 실행
CATEGORY=$(get_category "$AGENT_NAME")
run_hook "$CATEGORY" "$HOOK_TYPE"

# 에이전트 전용 Hook 실행 (있는 경우)
agent_hook="$HOOK_DIR/agents/${AGENT_NAME}/${HOOK_TYPE}-hook.sh"
if [ -f "$agent_hook" ]; then
    echo "[Hook Router] 에이전트 전용 Hook 실행: $agent_hook"
    bash "$agent_hook"
fi

# 추가 공통 Hook 실행
# Security Hook (API/Database 작업 시)
if [[ "$CATEGORY" == "database" ]] || [[ "$AGENT_NAME" == *"api"* ]]; then
    security_hook="$HOOK_DIR/security/${HOOK_TYPE}-hook.sh"
    if [ -f "$security_hook" ]; then
        echo "[Hook Router] Security Hook 실행: $security_hook"
        bash "$security_hook" "$AGENT_NAME"
    fi
fi

# Context Optimizer Hook (코딩 작업 시)
if [[ "$CATEGORY" == "coding" ]] && [[ "$HOOK_TYPE" == "pre" ]]; then
    context_hook="$HOOK_DIR/context/pre-hook.sh"
    if [ -f "$context_hook" ]; then
        echo "[Hook Router] Context Optimizer 실행: $context_hook"
        bash "$context_hook" "$AGENT_NAME"
    fi
fi

# Quality Gate Hook (코딩 작업 완료 시)
if [[ "$CATEGORY" == "coding" ]] && [[ "$HOOK_TYPE" == "post" ]]; then
    quality_hook="$HOOK_DIR/quality-gate/post-hook.sh"
    if [ -f "$quality_hook" ]; then
        echo "[Hook Router] Quality Gate 실행: $quality_hook"
        bash "$quality_hook" "$AGENT_NAME"
    fi
fi

# Learning Hook (YouTube/AI 작업 완료 시)
if ([[ "$CATEGORY" == "youtube" ]] || [[ "$CATEGORY" == "ai" ]] || [[ "$CATEGORY" == "cruise-guide" ]]) && [[ "$HOOK_TYPE" == "post" ]]; then
    learning_hook="$HOOK_DIR/learning/post-hook.sh"
    if [ -f "$learning_hook" ]; then
        echo "[Hook Router] Learning Feedback 실행: $learning_hook"
        bash "$learning_hook" "$AGENT_NAME"
    fi
fi

# Parallel Execution Hook (Orchestrator 실행 시)
if [[ "$AGENT_NAME" == *"orchestrator"* ]] && [[ "$HOOK_TYPE" == "pre" ]]; then
    parallel_hook="$HOOK_DIR/parallel/pre-hook.sh"
    if [ -f "$parallel_hook" ]; then
        echo "[Hook Router] Parallel Execution 체크: $parallel_hook"
        bash "$parallel_hook" "$AGENT_NAME"
    fi
fi
