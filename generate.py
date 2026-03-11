#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
generate.py - CruiseDot 영상 자동 생성 통합 CLI

사용법:
   python generate.py --mode auto                    자동 모드 1편
   python generate.py --mode auto --count 3          자동 3편
   python generate.py --mode manual --port 나가사키 --ship "MSC 벨리시마" --category 기항지정보
   python generate.py --mode auto --dry-run          스크립트까지만 (렌더링 스킵)

옵션:
  --mode          auto / manual
  --count       생성 편수 (기본 1)
  --port        기항지 코드 또는 한글명 (수동 모드 필수)
  --ship        선박 이름 또는 code (수동 모드 필수)
  --category    카테고리 code 또는 한글명 (수동 모드 필수)
  --tier        가격대 T1/T2/T3  (수동 모드, 미지정 시 자동)
  --output      출력 디렉토리 (기본 outputs/videos)
  --config      설정 yaml 경로 (기본 자동)
  --dry-run     렌더링 스킵 (스크립트만 저장)
  --verbose     상세 로그 출력
"""

import argparse
import json
import sys
import logging
from pathlib import Path
from typing import Optional, List, Dict

# 프로젝트 루트를 sys.path에 추가 (직접 실행 시)
if getattr(sys, 'frozen', False):
    PROJECT_ROOT = Path(sys.executable).parent
else:
    PROJECT_ROOT = Path(__file__).parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

logger = logging.getLogger(__name__)


# ============================================================================
# 1. ArgumentParser
# ============================================================================

def create_parser() -> argparse.ArgumentParser:
    """CLI 인수 파서 구성"""
    parser = argparse.ArgumentParser(
        prog="generate.py",
        description="CruiseDot 크루즈 자동/수동 영상 생성 CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    # 모드 (필수)
    parser.add_argument(
        "--mode",
        required=False,
        default="auto",
        choices=["auto", "manual"],
        help="실행 모드 (auto: 자동 선택, manual: 수동 지정, 기본: auto)",
    )

    # 생성 편수
    parser.add_argument(
        "--count",
        type=int,
        default=1,
        help="생성할 영상 편수 (기본: 1)",
    )

    # 수동 모드 파라미터
    parser.add_argument(
        "--port",
        type=str,
        default=None,
        help="기항지 코드 또는 한글명 (예: NAGASAKI, 나가사키)",
    )
    parser.add_argument(
        "--ship",
        type=str,
        default=None,
        help="선박 이름 또는 code (예: 'MSC 벨리시마', MSC_BELLISSIMA)",
    )
    parser.add_argument(
        "--category",
        type=str,
        default=None,
        help="카테고리 code 또는 한글명 (예: PORT_INFO, 기항지정보)",
    )
    parser.add_argument(
        "--tier",
        choices=["T1_진입가", "T2_주력가", "T3_프리미엄"],
        default=None,
        help="가격대 (미지정 시 카테고리 content_types 기반 자동 선택)",
    )

    # 공통 파라미터
    parser.add_argument(
        "--output",
        type=str,
        default=str(Path("outputs/videos")),
        help="출력 디렉토리 (기본: outputs/videos)",
    )
    parser.add_argument(
        "--config",
        type=str,
        default=str(PROJECT_ROOT / "config" / "cruise_config.yaml"),
        help="설정 yaml 파일 경로",
    )
    parser.add_argument(
        "--log-path",
        type=str,
        default=str(PROJECT_ROOT / "outputs" / "logs" / "generation.json"),
        help="생성 로그 JSON 경로 (기본: outputs/logs/generation.json)",
    )
    parser.add_argument(
        "--skip-upload-pkg",
        action="store_true",
        help="업로드 패키지 생성 스킵",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="렌더링 스킵 - 스크립트 생성/검증만 수행",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="상세 로그 출력 (DEBUG 레벨)",
    )

    # YouTube 트렌드 수집
    parser.add_argument(
        "--collect-trends",
        action="store_true",
        help="YouTube 트렌드 수집 후 종료 (영상 생성 없음)",
    )

    # S2-C3: 주간 보고서
    parser.add_argument(
        "--report",
        action="store_true",
        help="주간 보고서 생성 후 종료 (영상 생성 없음)",
    )
    parser.add_argument(
        "--report-days",
        type=int,
        default=7,
        help="보고서 집계 기간 (기본: 7일)",
    )

    return parser


# ============================================================================
# 2. 한글 입력 해석 함수
# ============================================================================

def resolve_port_code(user_input: str, config) -> Optional[str]:
    """기항지 코드 또는 한글명/영문명 → 코드 변환"""
    if not user_input:
        return None

    upper_input = user_input.upper()

    # 정확한 코드 매칭
    all_ports = config.get_all_port_codes()
    if upper_input in all_ports:
        return upper_input

    # 한글명 또는 영문명 검색
    for region, port_list in config.ports.items():
        for port in port_list:
            name = port.get("name", "") if isinstance(port, dict) else ""
            code = port.get("code", "") if isinstance(port, dict) else str(port)

            # 완전 일치
            if user_input == name:
                return code
            if user_input.upper() == code.upper():
                return code

            # 부분 일치 (예: "나가사키" → "나가사키항")
            if user_input in name:
                return code
            if name in user_input:
                return code
            if user_input.lower() in code.lower():
                return code

    return None


def resolve_ship_code(user_input: str, ships) -> Optional[str]:
    """선박 code 또는 한글명 → code"""
    if not user_input:
        return None

    for ship in ships:
        if user_input.upper() == ship.code.upper():
            return ship.code
        if user_input == ship.name:
            return ship.code

    return None


def resolve_category_code(user_input: str, categories) -> Optional[str]:
    """카테고리 code 또는 한글명 → code"""
    if not user_input:
        return None

    # 정확한 code 매칭
    for cat in categories:
        if user_input.upper() == cat.code.upper():
            return cat.code

    # 정확한 한글명 매칭
    for cat in categories:
        if user_input == cat.name:
            return cat.code

    # 부분 일치 (code 또는 한글명)
    for cat in categories:
        if user_input.lower() in cat.code.lower() or user_input in cat.name:
            return cat.code

    return None


def infer_price_tier(priority: str) -> str:
    """priority 기반 기본 가격대 추론"""
    tier_map = {
        "P0": "T2_주력가",
        "P1": "T2_주력가",
        "P2": "T2_주력가",
        "P3": "T1_진입가",
    }
    return tier_map.get(priority, "T2_주력가")


# ============================================================================
# 3. 자동 모드
# ============================================================================

def run_auto_mode(args, config, gen_log) -> List[Dict]:
    """자동 모드: 가중치 기반 조합 선택 → S등급 루프 → 렌더링 → 패키지"""
    from cli.auto_mode import AutoModeOrchestrator, AutoModeSettings

    settings = AutoModeSettings()
    orch = AutoModeOrchestrator(config, gen_log, settings)

    return orch.run(
        count=args.count,
        output_dir=args.output,
        skip_upload_pkg=args.skip_upload_pkg,
        dry_run=args.dry_run,
    )


# ============================================================================
# 4. 수동 모드
# ============================================================================

def run_manual_mode(args, config, gen_log) -> List[Dict]:
    """수동 모드: 사용자가 지정한 기항지/선박/카테고리로 영상 생성"""
    from cli.auto_mode import AutoModeOrchestrator, AutoModeSettings, Combination
    from cli.generation_log import GenerationLogEntry
    from datetime import datetime

    # --- 필수 파라미터 검증 ---
    if not args.port:
        logger.error("수동 모드에서 --port 는 필수입니다.")
        sys.exit(1)
    if not args.ship:
        logger.error("수동 모드에서 --ship 은 필수입니다.")
        sys.exit(1)
    if not args.category:
        logger.error("수동 모드에서 --category 는 필수입니다.")
        sys.exit(1)

    # --- 기항지 해석 ---
    port_code = resolve_port_code(args.port, config)
    port_name = args.port

    if port_code:
        # config에서 한글명 찾기
        for region, port_list in config.ports.items():
            for p in port_list:
                if isinstance(p, dict) and p.get("code") == port_code:
                    port_name = p.get("name", args.port)
    else:
        # config에 없는 기항지 - 입력값 그대로 사용 (오류 중단 X)
        port_code = args.port.upper()
        port_name = args.port
        logger.info(
            f"기항지 '{args.port}' 를 config에서 찾지 못했습니다. "
            f"입력값 그대로 사용합니다.",
        )

    # --- 선박 해석 ---
    ship_code = resolve_ship_code(args.ship, config.ships)
    if not ship_code:
        logger.error(f"선박 '{args.ship}' 를 찾을 수 없습니다.")
        available = ", ".join(s.name for s in config.ships)
        logger.error(f"  사용 가능한 선박: {available}")
        sys.exit(1)

    ship_name = args.ship
    for s in config.ships:
        if s.code == ship_code:
            ship_name = s.name
            break

    # --- 카테고리 해석 ---
    cat_code = resolve_category_code(args.category, config.categories)
    if not cat_code:
        logger.error(f"카테고리 '{args.category}' 를 찾을 수 없습니다.")
        available = ", ".join(c.name for c in config.categories[:10])
        logger.error(f"  사용 가능 (일부): {available}...")
        sys.exit(1)

    cat_name = args.category
    cat_obj = config.get_category_by_code(cat_code)
    if cat_obj:
        cat_name = cat_obj.name

    # --- 가격대 결정 ---
    price_tier = args.tier or infer_price_tier(cat_obj.priority if cat_obj else "P2")

    # --- content_type 결정 ---
    content_type = ""
    for pt in config.price_tiers:
        if pt.key == price_tier:
            content_type = pt.content_type
            break

    # --- Combination 구성 ---
    combination = Combination(
        port_code=port_code,
        port_name=port_name,
        ship_code=ship_code,
        ship_name=ship_name,
        category_code=cat_code,
        category_name=cat_name,
        price_tier=price_tier,
        content_type=content_type,
        comparison_frame=cat_obj.comparison_frame if cat_obj else "",
    )

    logger.info(
        f"[수동모드] 기항지: {port_name}({port_code}), "
        f"카테고리: {cat_name}, "
        f"선박: {ship_name}, "
        f"가격대: {price_tier}"
    )

    settings = AutoModeSettings()
    orch = AutoModeOrchestrator(config, gen_log, settings)

    results = []
    result = orch.run_s_grade_loop(combination, args.output, args.dry_run)

    if result:
        video_path = result.get("video_path", "")
        logger.info(
            f"[완료] '{result['grade']}' 등급 "
            f"'{result['score']}'점"
        )

        # 업로드 패키지 생성
        if not args.skip_upload_pkg and not args.dry_run:
            pkg_dir = orch._create_upload_package(
                result.get("script", {}),
                video_path,
                combination,
            )
            if pkg_dir:
                logger.info(f"[패키지] {pkg_dir}")

        # 로그 기록
        entry = GenerationLogEntry(
            timestamp=datetime.now().isoformat(),
            timestamp_unix=datetime.now().strftime("%Y-%m-%d"),
            port_code=port_code,
            category_code=cat_code,
            category_name=cat_name,
            ship_code=ship_code,
            price_tier=price_tier,
            s_grade_score=result.get("score", 0.0),
            script_path="",
            upload_pkg_dir="",
            s_grade=result.get("grade", ""),
            grade=result.get("grade", ""),
        )
        gen_log.add_entry(entry)

        results.append(result)
    else:
        logger.warning("[실패] S등급 미달")

    return results


# ============================================================================
# 5. 로깅 설정
# ============================================================================

def setup_logging(verbose: bool) -> None:
    """로깅 레벨 및 형식 설정"""
    level = logging.DEBUG if verbose else logging.INFO
    fmt = "%(asctime)s %(levelname)s %(name)s %(message)s"
    logging.basicConfig(level=level, format=fmt, datefmt="%H:%M:%S")

    # 외부 라이브러리 로그 억제 (verbose가 아닐 때)
    if not verbose:
        for lib in ("PIL", "moviepy", "urllib3", "httpx"):
            logging.getLogger(lib).setLevel(logging.WARNING)


# ============================================================================
# 6. 메인 진입점
# ============================================================================

def main() -> None:
    from cli.config_loader import load_config
    from cli.generation_log import load_generation_log

    parser = create_parser()
    args = parser.parse_args()

    setup_logging(args.verbose)

    # --- 설정 로드 ---
    logger.info("설정 로드: %s", args.config)
    try:
        config_path = args.config
        if not Path(config_path).exists():
            # 기본 경로 시도
            config_path = str(PROJECT_ROOT / "config" / "cruise_config.yaml")
        config = load_config(config_path)
    except FileNotFoundError:
        logger.error(f"설정 파일을 찾을 수 없습니다: {args.config}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"설정 로드 실패: {e}")
        sys.exit(1)

    # --- 생성 로그 초기화 ---
    log_path = args.log_path
    Path(log_path).parent.mkdir(parents=True, exist_ok=True)

    try:
        gen_log = load_generation_log(log_path)
    except Exception as e:
        logger.error(f"생성 로그 초기화 실패: {e}")
        sys.exit(1)

    logger.info(
        "로그 로드 완료 (기록 %d개, 경로: %s)",
        len(gen_log.entries),
        log_path,
    )

    # --- 출력 디렉토리 생성 ---
    Path(args.output).mkdir(parents=True, exist_ok=True)

    # --- YouTube 트렌드 수집 모드 ---
    if args.collect_trends:
        try:
            from engines.youtube_trend_collector import YouTubeTrendCollector
            collector = YouTubeTrendCollector()
            result = collector.collect()
            if result:
                logger.info(
                    "트렌드 수집 완료: %d개 영상, %d개 키워드",
                    result.get("total_videos", 0),
                    len(result.get("trending_keywords", [])),
                )
            else:
                logger.info("트렌드 수집 스킵 (API키 미설정 또는 캐시 유효)")
        except Exception as e:
            logger.warning("트렌드 수집 실패: %s", e)
        return

    # --- S2-C3: 주간 보고서 모드 ---
    if args.report:
        from cli.weekly_report import generate_weekly_report
        report_path = generate_weekly_report(
            gen_log,
            days=args.report_days,
            output_dir=str(Path(args.output).parent / "reports"),
        )
        logger.info(f"주간 보고서 생성 완료: {report_path}")
        return

    # --- 모드별 실행 ---
    if args.mode == "auto":
        results = run_auto_mode(args, config, gen_log)
    else:
        results = run_manual_mode(args, config, gen_log)

    # --- 결과 요약 (JSON 출력 모드) ---
    summary = {
        "mode": args.mode,
        "count": args.count,
        "success": len(results),
        "dry_run": args.dry_run,
    }
    logger.info("결과 요약: %s", json.dumps(summary, ensure_ascii=False))

    # 사람이 읽기 편한 출력
    logger.info(f"{'='*50}")
    logger.info(f"생성 결과: {len(results)}/{args.count} 편 성공")
    for r in results:
        logger.info(f"  - {r.get('grade', '?')}등급 {r.get('score', 0)}점: {r.get('video_path', 'N/A')}")
    logger.info(f"{'='*50}")


if __name__ == "__main__":
    main()
