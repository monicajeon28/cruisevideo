#!/bin/bash
# Database 카테고리 Pre-Hook
# DB 작업 전 백업 및 보안 체크

AGENT_NAME="$1"

echo "🗄️ [Database] DB 작업 사전 검증 시작..."

# 1. 환경 변수 체크
if [ -f "D:/mabiz/.env" ]; then
    echo "  ✅ .env 파일 존재"

    # DATABASE_URL 존재 확인 (내용은 보이지 않음)
    if grep -q "DATABASE_URL" "D:/mabiz/.env"; then
        echo "  ✅ DATABASE_URL 설정됨"
    else
        echo "  ⚠️ DATABASE_URL 없음!"
    fi
else
    echo "  ❌ .env 파일 없음! DB 연결 불가"
fi

# 2. Prisma 스키마 검증 (선택적)
if [ -f "prisma/schema.prisma" ] && command -v npx &> /dev/null; then
    echo "  🔍 Prisma 스키마 검증 중..."
    npx prisma validate 2>&1 | head -10
fi

# 3. 위험 작업 경고
case "$AGENT_NAME" in
    schema-migration)
        echo "  ⚠️ 스키마 마이그레이션: DB 백업 권장!"
        ;;
    database-query)
        echo "  ℹ️ DB 쿼리 실행: 읽기 전용 권장"
        ;;
esac

echo "🗄️ [Database] 사전 검증 완료"
echo ""
