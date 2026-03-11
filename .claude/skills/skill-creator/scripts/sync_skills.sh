#!/bin/bash
#
# sync_skills.sh - Git Bash/WSL 스킬 동기화
#
# Usage:
#   bash sync_skills.sh [skill-name]     # 특정 스킬 동기화
#   bash sync_skills.sh --all            # 모든 스킬 동기화
#
# Detects environment and syncs accordingly:
#   Git Bash (Windows) → WSL Ubuntu
#   WSL Ubuntu → Windows (Git Bash)

set -e

# 환경 감지
detect_environment() {
    if [[ -n "$WSL_DISTRO_NAME" ]] || [[ -f /proc/version ]] && grep -qi microsoft /proc/version 2>/dev/null; then
        echo "wsl"
    elif [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "cygwin" ]] || [[ -n "$MSYSTEM" ]]; then
        echo "gitbash"
    else
        echo "unknown"
    fi
}

# 경로 설정
setup_paths() {
    ENV=$(detect_environment)
    
    case $ENV in
        "wsl")
            LOCAL_SKILLS="$HOME/.claude/skills"
            REMOTE_SKILLS="/mnt/c/Users/lpian/.claude/skills"
            ;;
        "gitbash")
            LOCAL_SKILLS="$HOME/.claude/skills"
            REMOTE_SKILLS="/home/elon/.claude/skills"
            ;;
        *)
            echo "Unknown environment. Cannot sync."
            exit 1
            ;;
    esac
}

# 단일 스킬 동기화
sync_skill() {
    local skill_name=$1
    
    if [[ ! -d "$LOCAL_SKILLS/$skill_name" ]]; then
        echo "❌ Skill not found: $LOCAL_SKILLS/$skill_name"
        exit 1
    fi
    
    case $ENV in
        "wsl")
            # WSL → Windows
            cp -r "$LOCAL_SKILLS/$skill_name" "$REMOTE_SKILLS/"
            echo "✅ Synced $skill_name: WSL → Windows"
            ;;
        "gitbash")
            # Git Bash → WSL
            if command -v wsl &> /dev/null; then
                wsl -e bash -c "cp -r /mnt/c/Users/lpian/.claude/skills/$skill_name ~/.claude/skills/"
                echo "✅ Synced $skill_name: Windows → WSL"
            else
                echo "⚠️ WSL not available. Manual sync required."
            fi
            ;;
    esac
}

# 모든 스킬 동기화
sync_all() {
    case $ENV in
        "wsl")
            # WSL → Windows
            cp -r "$LOCAL_SKILLS"/* "$REMOTE_SKILLS/"
            echo "✅ All skills synced: WSL → Windows"
            ;;
        "gitbash")
            # Git Bash → WSL
            if command -v wsl &> /dev/null; then
                wsl -e bash -c "cp -r /mnt/c/Users/lpian/.claude/skills/* ~/.claude/skills/"
                echo "✅ All skills synced: Windows → WSL"
            else
                echo "⚠️ WSL not available. Manual sync required."
            fi
            ;;
    esac
}

# 메인
main() {
    setup_paths
    
    echo "Environment: $ENV"
    echo "Local skills: $LOCAL_SKILLS"
    
    if [[ $# -eq 0 ]]; then
        echo "Usage: sync_skills.sh [skill-name] or sync_skills.sh --all"
        exit 1
    fi
    
    if [[ "$1" == "--all" ]]; then
        sync_all
    else
        sync_skill "$1"
    fi
}

main "$@"
