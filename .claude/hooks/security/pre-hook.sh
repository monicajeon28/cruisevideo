#!/bin/bash
# Security Pre-Hook
# API/Database 작업 전 보안 검사 (OWASP Top 10 기반)

AGENT_NAME="$1"
LOG_DIR="D:/mabiz/.claude/logs/security"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

mkdir -p "$LOG_DIR"

echo "🔒 [Security] 보안 검사 시작..."

# 1. 하드코딩된 시크릿 탐지
echo "  🔍 하드코딩된 시크릿 검사 중..."

# 일반적인 시크릿 패턴
PATTERNS=(
    "password.*=.*['\"].*['\"]"
    "api[_-]?key.*=.*['\"].*['\"]"
    "secret.*=.*['\"].*['\"]"
    "token.*=.*['\"].*['\"]"
    "AWS_ACCESS_KEY"
    "PRIVATE_KEY"
)

FOUND_SECRETS=0
for pattern in "${PATTERNS[@]}"; do
    if git grep -i -E "$pattern" -- '*.ts' '*.tsx' '*.js' '*.jsx' '*.py' 2>/dev/null | grep -v ".env" | grep -v "node_modules" | head -3; then
        FOUND_SECRETS=$((FOUND_SECRETS + 1))
    fi
done

if [ $FOUND_SECRETS -gt 0 ]; then
    echo "  ⚠️ 하드코딩된 시크릿 발견! ($FOUND_SECRETS개 패턴 일치)"
else
    echo "  ✅ 하드코딩된 시크릿 없음"
fi

# 2. SQL Injection 패턴 체크 (기본)
echo "  🔍 SQL Injection 패턴 검사 중..."
if git grep -E "execute\(.*\+.*\)" -- '*.ts' '*.py' 2>/dev/null | head -3; then
    echo "  ⚠️ 잠재적 SQL Injection 패턴 발견"
else
    echo "  ✅ SQL Injection 패턴 없음"
fi

# 3. .env 파일 보안 체크
if [ -f "D:/mabiz/.env" ]; then
    # .env가 .gitignore에 있는지 확인
    if [ -f ".gitignore" ]; then
        if grep -q ".env" ".gitignore"; then
            echo "  ✅ .env가 .gitignore에 등록됨"
        else
            echo "  ⚠️ .env가 .gitignore에 없음! Git 커밋 위험"
        fi
    fi
fi

# 4. 보안 리포트 저장
SECURITY_REPORT="$LOG_DIR/${AGENT_NAME}_${TIMESTAMP}_security.json"

cat > "$SECURITY_REPORT" << EOF
{
  "agent": "$AGENT_NAME",
  "timestamp": "$(date -Iseconds)",
  "checks": {
    "hardcoded_secrets": "$FOUND_SECRETS patterns",
    "sql_injection": "CHECKED",
    "env_gitignore": "CHECKED"
  }
}
EOF

echo "  💾 보안 리포트 저장: $SECURITY_REPORT"
echo "🔒 [Security] 보안 검사 완료"
echo ""
