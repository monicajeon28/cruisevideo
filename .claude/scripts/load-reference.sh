#!/bin/bash
# 크루즈 마케팅 콘텐츠 자동 참조 스크립트
# 사용법: bash load-reference.sh [토픽명 또는 키워드]

SECTIONS_DIR="D:/mabiz/Learning_Data/gemini_research/sections"
INDEX_FILE="D:/mabiz/Learning_Data/gemini_research/INDEX.md"

# 색상 정의
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 사용법 출력
usage() {
    echo ""
    echo "크루즈 마케팅 콘텐츠 자동 참조 시스템"
    echo "=========================================="
    echo ""
    echo "사용법:"
    echo "  bash load-reference.sh [옵션] [토픽/키워드]"
    echo ""
    echo "옵션:"
    echo "  -l, --list        사용 가능한 모든 섹션 목록 표시"
    echo "  -s, --search      키워드로 섹션 검색"
    echo "  -i, --index       인덱스 파일 열기"
    echo "  -h, --help        도움말 표시"
    echo ""
    echo "토픽 번호:"
    echo "  1  전략 DNA & 직접 예약 재앙"
    echo "  2  예약 단계 실수 (금전적 손실)"
    echo "  3  기항지 트러블 & 선내 문제"
    echo "  4  직구 vs 여행사 비교"
    echo "  5  크루즈 기초 FAQ 100개"
    echo "  6  일본 기항지 가이드"
    echo "  7  한국/동남아 기항지 가이드"
    echo "  8  중국 기항지 & 도쿄 쇼핑"
    echo "  9  혼자 준비 문제점 150개"
    echo "  10 연령대별 특수 문제"
    echo ""
    echo "키워드 예시:"
    echo "  bash load-reference.sh booking     # '예약' 관련 섹션"
    echo "  bash load-reference.sh japan       # '일본' 관련 섹션"
    echo "  bash load-reference.sh faq         # 'FAQ' 섹션"
    echo "  bash load-reference.sh senior      # '시니어' 관련 섹션"
    echo ""
}

# 섹션 목록 표시
list_sections() {
    echo -e "${GREEN}사용 가능한 섹션:${NC}"
    echo ""

    local files=("$SECTIONS_DIR"/*.md)
    local count=1

    for file in "${files[@]}"; do
        if [ -f "$file" ]; then
            local filename=$(basename "$file")
            local size=$(du -h "$file" | cut -f1)

            # 제목 추출 (첫 번째 # 라인)
            local title=$(grep -m 1 "^# " "$file" | sed 's/^# //')

            echo -e "${BLUE}[$count] $filename${NC} (${size})"
            echo "    $title"
            echo ""
            ((count++))
        fi
    done
}

# 키워드로 검색
search_sections() {
    local keyword="$1"
    echo -e "${GREEN}검색 키워드: '$keyword'${NC}"
    echo ""

    grep -l -i "$keyword" "$SECTIONS_DIR"/*.md | while read file; do
        local filename=$(basename "$file")
        echo -e "${BLUE}일치 파일: $filename${NC}"

        # 키워드가 포함된 라인 미리보기 (최대 3줄)
        grep -i -n -C 1 "$keyword" "$file" | head -20
        echo ""
        echo "---"
        echo ""
    done
}

# 토픽 번호로 파일 선택
get_file_by_number() {
    local num="$1"
    case $num in
        1) echo "01_strategy_and_disasters.md" ;;
        2) echo "02_booking_mistakes_detailed.md" ;;
        3) echo "03_onboard_and_port_issues.md" ;;
        4) echo "04_comparison_and_positioning.md" ;;
        5) echo "05_cruise_basic_faq.md" ;;
        6) echo "06_japan_ports_guide.md" ;;
        7) echo "07_korea_and_sea_ports.md" ;;
        8) echo "08_china_ports_extended.md" ;;
        9) echo "09_solo_preparation_problems.md" ;;
        10) echo "10_age_group_specific_issues.md" ;;
        *) echo "" ;;
    esac
}

# 키워드로 파일 찾기
find_file_by_keyword() {
    local keyword=$(echo "$1" | tr '[:upper:]' '[:lower:]')

    case $keyword in
        *strategy*|*전략*|*disaster*|*재앙*)
            echo "01_strategy_and_disasters.md" ;;
        *booking*|*예약*|*mistake*|*실수*)
            echo "02_booking_mistakes_detailed.md" ;;
        *port*|*기항지*|*onboard*|*선내*)
            echo "03_onboard_and_port_issues.md" ;;
        *comparison*|*비교*|*직구*|*여행사*)
            echo "04_comparison_and_positioning.md" ;;
        *faq*|*기초*|*처음*)
            echo "05_cruise_basic_faq.md" ;;
        *japan*|*일본*|*후쿠오카*|*오키나와*|*나가사키*)
            echo "06_japan_ports_guide.md" ;;
        *korea*|*한국*|*부산*|*제주*|*동남아*|*싱가포르*|*푸켓*)
            echo "07_korea_and_sea_ports.md" ;;
        *china*|*중국*|*상하이*|*도쿄*|*쇼핑*)
            echo "08_china_ports_extended.md" ;;
        *solo*|*혼자*|*준비*|*problem*)
            echo "09_solo_preparation_problems.md" ;;
        *age*|*연령*|*senior*|*시니어*|*부부*|*가족*)
            echo "10_age_group_specific_issues.md" ;;
        *)
            # 키워드가 파일명에 포함되는지 확인
            grep -l -i "$keyword" "$SECTIONS_DIR"/*.md 2>/dev/null | head -1 | xargs basename 2>/dev/null
            ;;
    esac
}

# 파일 정보 표시
show_file_info() {
    local file="$1"

    if [ ! -f "$file" ]; then
        echo -e "${YELLOW}[오류] 파일을 찾을 수 없습니다: $file${NC}"
        return 1
    fi

    echo ""
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}파일 정보${NC}"
    echo -e "${GREEN}========================================${NC}"

    # 메타데이터 추출
    echo -e "${BLUE}파일명:${NC} $(basename "$file")"
    echo -e "${BLUE}크기:${NC} $(du -h "$file" | cut -f1)"
    echo -e "${BLUE}라인 수:${NC} $(wc -l < "$file")"
    echo ""

    # 제목과 설명 추출 (첫 20줄에서)
    head -20 "$file" | grep -A 1 "^# " | head -5
    echo ""

    # 키워드 추출
    echo -e "${BLUE}키워드:${NC}"
    grep "키워드:" "$file" | head -1
    echo ""

    echo -e "${GREEN}========================================${NC}"
    echo ""
    echo "이 파일을 Claude Code에서 읽으려면:"
    echo -e "${YELLOW}Read $file${NC}"
    echo ""
}

# 메인 로직
main() {
    if [ $# -eq 0 ]; then
        usage
        exit 0
    fi

    case "$1" in
        -h|--help)
            usage
            ;;
        -l|--list)
            list_sections
            ;;
        -i|--index)
            echo "인덱스 파일 열기: $INDEX_FILE"
            cat "$INDEX_FILE"
            ;;
        -s|--search)
            if [ -z "$2" ]; then
                echo "검색 키워드를 입력하세요."
                exit 1
            fi
            search_sections "$2"
            ;;
        [0-9]|[0-9][0-9])
            # 숫자로 선택
            filename=$(get_file_by_number "$1")
            if [ -z "$filename" ]; then
                echo "잘못된 토픽 번호입니다. 1-10 사이의 숫자를 입력하세요."
                exit 1
            fi
            show_file_info "$SECTIONS_DIR/$filename"
            ;;
        *)
            # 키워드로 검색
            filename=$(find_file_by_keyword "$1")
            if [ -z "$filename" ]; then
                echo "키워드 '$1'와 일치하는 섹션을 찾을 수 없습니다."
                echo ""
                echo "검색을 시도합니다..."
                search_sections "$1"
            else
                show_file_info "$SECTIONS_DIR/$filename"
            fi
            ;;
    esac
}

# 스크립트 실행
main "$@"
