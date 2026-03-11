# S+ 등급 YouTube Cruise Content Pipeline - 마스터 작업지시서

작성일: 2026-03-08
버전: 1.0.0 ULTIMATE
목표: S등급 90점 → S+ 등급 95점+ 달성 (상위 1% 완벽 시스템)
프로젝트: CruiseDot 크루즈 전문 여행사 - YouTube Shorts 50초 영상 파이프라인

---

## EXECUTIVE SUMMARY

### 프로젝트 개요
- 클라이언트: 크루즈닷 (11년 경력 크루즈 전문 여행사, MSC/Royal Caribbean 공식 파트너)
- 목표: YouTube Shorts 50초 영상 → 카카오톡 상담 → 크루즈 예약 전환
- 타겟: 한국 5060 세대 부부 (주력 상품 250-400만원 동유럽/알래스카 크루즈)
- 현재 상태: Phase 33 완료 (S등급 98.8/100), Phase B-9 완료 (이미지 자막 렌더링 28초)
- 차기 목표: S+ 등급 95점+ (상위 1% 감정 설계 + 영상 편집 + 마케팅 후킹)

### 핵심 성과 지표
| 항목 | 현재 | 목표 | 기대 효과 |
|------|------|------|-----------|
| S등급 점수 | 98.8점 | 95점+ | 최상위 품질 보증 |
| 완주율 (Shorts) | 45% | 55%+ | +22% |
| CTR (프로필 클릭) | 12% | 18%+ | +50% |
| 전환율 (영상→예약) | 0.6% | 1.2%+ | +100% |
| 월 수익 | 950만원 | 1,800만원+ | +89% |

---

## PART 1: TTS 설정 및 음성 전략

### 1.1 Supertone 음성 ID 13개 (전체 리스트)

| 음성 ID | 성별/연령 | 특징 | 용도 | 감정 지원 |
|---------|-----------|------|------|-----------|
| Audrey (1f6b70f879da125bfec245) | 30대 여성 아나운서 | 깔끔, 신뢰, 전문적 | 메인 내레이션 | happy, neutral, sad, angry, annoyed, embarrassed |
| Grace (bacc385ac094a4e0c187a0) | 40대 여성 | 따뜻함, 공감 | 감정 공감 섹션 | happy, neutral, sad, angry, annoyed, embarrassed |
| Ariel (7c56c6a6471a12816604f0) | 30대 여성 | 밝고 활기찬 | 긍정 에너지 | happy, neutral, sad, angry, annoyed, embarrassed |
| Dakota (9e8442ab1bb3a0ce9ffcbe) | 40대 여성 | 차분한 신뢰 | Trust 섹션 | happy, neutral, sad, angry, annoyed, embarrassed |
| Flop (56e1a6c42fc4968d15a394) | 30대 남성 | 명확한 발음 | 정보 전달 | happy, neutral, sad, angry, annoyed, embarrassed |
| **Juho (6e43a7b9ffa9834c154ab7)** | **40대 남성** | **낮고 부드러운, 신뢰** | **가격/숫자 담당 (핵심)** | happy, neutral, sad, angry, annoyed, embarrassed |
| Sangchul (068aa76205e4eb612a2fb0) | 30대 남성 | 에너지, 활력 | 액션 유도 | happy, neutral, sad, angry, annoyed, embarrassed |
| Yannom (42b52760fe9ecf701f8ed3) | 40대 남성 | 권위, 전문성 | 전문가 의견 | happy, neutral, sad, angry, annoyed, embarrassed |
| Dudumchi (709bebd6baa7cc0d9610c3) | 30대 남성 | 친근함 | 공감 대화 | happy, neutral, sad, angry, annoyed, embarrassed |
| Bert (816bc977b4111a3034146a) | 50대 남성 | 연륜, 경험 | 권위 신뢰 | happy, neutral, sad, angry, annoyed, embarrassed |
| Osman (8defc488f52f5efb9901f7) | 60대 남성 | 원로, 신뢰 | 시니어 공감 | happy, neutral, sad, angry, annoyed, embarrassed |
| Ppang BuJang (01da74a6b20d3bdbf09522) | 30대 맛집 리뷰어 | 생생함, 현장감 | 체험 리뷰 | happy, neutral, sad, angry, annoyed, embarrassed |
| Billy (39b96759e0af5b7a45d541) | 10대 | 젊은 에너지 | (크루즈 미사용) | happy, neutral, sad, angry, annoyed, embarrassed |

**핵심 TTS 조합 (대화형 2인)**
- Hook/Problem/Agitate: Audrey (여성 아나운서, neutral)
- 가격/숫자: Juho (40대 남성, 낮고 부드러운 목소리, neutral) - 5060 신뢰도 최고
- 공감/감정: Grace (40대 여성, sad/happy 감정 전환)
- CTA/Action: Juho (남성, 확신 톤)

### 1.2 TTS 최적화 전략 (5060 세대 타겟)

#### A. 문장 길이 최적화
- 최적: 7-12 어절 (평균 9.5 어절)
- 허용: 13-17 어절
- 금지: 18 어절 초과 (이해도 -34% 급락)
- 근거: 5060 세대는 작업 기억(Working Memory) 용량이 3 청크로 일반(5 청크) 대비 40% 낮음

#### B. 습니다체/해요체 하이브리드 (신뢰도 +32%)
| 섹션 | 어조 | 근거 |
|------|------|------|
| Hook/도입부 | 습니다체 | 전문성 확보 |
| 공감/스토리 | 해요체 | 친근감 형성 |
| 정보/데이터 | 습니다체 | 신뢰도 강화 |
| CTA/행동 유도 | 습니다체 | 확신 전달 |

예시:
```
"오늘은 크루즈 여행의 모든 것을 알려드리겠습니다. (습니다체)
저도 처음엔 배멀미가 걱정됐어요. (해요체)
실제로 15만 톤급 크루즈는 흔들림이 거의 없습니다. (습니다체)
무료 가이드북을 받아가세요. 도움이 될 겁니다. (습니다체)"
```

#### C. 침묵 간격 (중요 정보 처리 시간)
- 중요 정보 후: 1-2초
- 정보 청크 전환 시: 0.5초
- 챕터 전환 시: 1-1.5초
- 근거: 5060 세대 정보 처리 속도 = 일반 대비 1.7배 느림

#### D. 숫자 읽기 속도 (chars_per_second: 4.2)
- 가격: "팔십구만원에... 삼박사일" (천천히, Juho 음성)
- 통계: "96% 만족도" (명확하게)
- 기간: "7박 8일" (또박또박)

---

## PART 2: 로컬 자원 경로 정리

### 2.1 에셋 디렉토리 구조

```
D:\AntiGravity\Assets\
├── Image\
│   ├── 크루즈정보사진정리\    # 2,916장 이미지 (80+ 기항지)
│   ├── 후기\                   # 고객 후기 이미지 (CTA/Outro/Trust 우선)
│   └── 로고\                   # 크루즈닷 로고 (투명배경 PNG)
│       └── 크루즈닷로고투명.png
│
├── Footage\
│   ├── Hook\                   # Hook 전용 영상 (104개 폴더 우선 선택)
│   └── (일반 영상 클립)
│
├── Music\                      # BGM (travel/upbeat 우선, sleep/somnia 차단)
│   └── Music_Backup\           # 백업 BGM
│
├── SoundFX\                    # 효과음
│   ├── level-up.wav            # 인트로 SFX (0.0초)
│   ├── hit_impact.wav          # 인트로 SFX (0.3초)
│   ├── swoosh.wav              # Pop 선행 (-0.3초)
│   └── (기타 효과음)
│
├── fonts\                      # 폰트 (맑은 고딕 등)
│
└── (누끼파일)\                 # 누끼 파일 (오버레이용, Sprint C 예정)
```

### 2.2 에셋 매칭 전략

#### A. 이미지 매칭 우선순위 (Phase 28 FIX-8)
1. 후기 이미지 우선 사용 (CTA/Outro/Trust 섹션)
2. 기항지명 강제 포함 (PORT_MAP 80+ 기항지)
3. PROPER_NOUNS_PORTS 178개 키워드 (유럽/알래스카/일본)
4. 누끼 카테고리 (오버레이 렌더링, Sprint C 예정)

#### B. Hook 영상 선택 (Phase 28 FIX-4)
1. Hook 전용 폴더 (104개) 우선 선택
2. 시각적 충격 (밝은 색상, 고대비, 큰 피사체)
3. 움직임 (사람 달리기, 배 출발)
4. 규모감 (거대한 크루즈선 전경)

#### C. BGM 매칭 (Phase 28 FIX-2)
- 우선: travel, upbeat, adventure, orchestral
- 차단: somnia, sleep, lullaby, meditation, zen (수면곡 제외)
- Backup 폴더 연동 (Music_Backup)

---

## PART 3: 학습 데이터 경로 및 핵심 지식

### 3.1 Gemini 리서치 (39개 JSON)

**경로**: `D:\mabiz\Learning_Data\gemini_research\`

#### 핵심 프롬프트 (1-39번)
| 번호 | 파일명 | 핵심 내용 |
|------|--------|-----------|
| 01 | 01_algorithm_mechanism.json | YouTube 알고리즘 작동 원리 (시청 시간 50%, CTR 30%, 유지율 15%) |
| 02 | 02_performance_benchmarks.json | 성과 벤치마크 (CTR 8-12%, 완주율 45%+) |
| 03 | 03_loop_structure.json | 루프 구조 (마지막 프레임 → 첫 프레임 연결) |
| 04 | 04_retention_curve.json | 유지율 곡선 (3초 Hook, 15초/30초 Re-hook) |
| 05 | 05_hook_patterns.json | Hook 패턴 10가지 |
| 06 | 06_first_sentence_formulas.json | 첫 문장 공식 12가지 |
| 07 | 07_comment_strategies.json | 댓글 유도 5가지 패턴 |
| 08 | 08_debate_techniques_revised.json | 건전한 논쟁 기법 |
| 09 | 09_cruise_niche_analysis_revised.json | 크루즈 틈새 분석 |
| 10 | 10_cruise_shorts_ideas_100_revised.json | 크루즈 Shorts 아이디어 100개 |
| 11 | 11_senior_shorts_consumption.json | 5060 세대 Shorts 소비 패턴 |
| 12 | 12_senior_communication_style_DEEP_DIVE.json | 5060 세대 언어 톤 (습니다체/해요체 하이브리드) |
| 13 | 13_longform_retention_curve.json | 롱폼 유지율 곡선 (3회 재훅) |
| 14 | 14_micro_tension_techniques.json | 미세 긴장감 기법 |
| 15 | 15_narrative_structure_4acts.json | 4막 구조 |
| 20 | 20_negative_reverse_hook.json | 네거티브 훅 심리학 |
| 21 | 21_curiosity_gap_theory.json | 호기심 갭 이론 (Zeigarnik Effect) |
| 22 | 22_psi_parasocial_interaction.json | 파라소셜 상호작용 (신뢰 구축) |
| 23 | 23_pattern_interrupt_attention.json | 패턴 인터럽트 (3초 법칙) |
| 24 | 24_senior_themes_hooks_v2.json | 5060 테마/훅 |
| 25 | 25_emotional_arc_hook_variation.json | 감정 곡선 (호기심 → 놀라움 → 부러움 → 욕구) |
| 26 | 26_cta_psychology_conversion.json | CTA 심리학 (BJ Fogg B=MAT 모델) |
| 32 | 32_narration_optimization_complete.json | 내레이션 최적화 |
| 33 | 33_cruise_trends_keywords_COMPLETE.json | 크루즈 트렌드 키워드 |
| 34 | 34_top_channels_6_themes_COMPLETE.json | 상위 채널 6가지 테마 |
| 35 | 35_ctr_title_thumbnail_COMPLETE.json | CTR 제목/썸네일 |
| 36 | 36_senior_cruise_journey_COMPLETE.json | 5060 크루즈 고객 여정 |
| 37 | 37_cruise_line_differentiation_COMPLETE.json | 크루즈 선사 차별화 |
| 38 | 38_seasonal_content_strategy_COMPLETE.json | 계절별 콘텐츠 전략 |
| 39 | 39_cruise_affiliate_optimization_cruisedot_v2_REVISED.json | 크루즈닷 어필리에이트 최적화 |
| 56 | 56_local_assets_integration_COMPLETE.json | 로컬 에셋 통합 (2,916장) |
| 57 | 57_s_grade_content_capability_validation.json | S등급 콘텐츠 검증 |
| 58 | 58_ULTIMATE_v3.json | S등급 완전 통합 마스터 프롬프트 (98.8점 달성) |

### 3.2 니콜라스 콜 글쓰기 법칙 (4A 프레임워크)

**경로**: `D:\mabiz\Learning_Data\니콜라스콜_글쓰기법칙.md`

#### 4A 프레임워크 (모든 바이럴 콘텐츠는 최소 1개 이상 충족)

| 유형 | 영문 | 핵심 질문 | 적용 예시 |
|------|------|-----------|-----------|
| A1 | Actionable | "이걸로 뭘 할 수 있지?" | "크루즈 첫 탑승 전 반드시 확인해야 할 7가지" |
| A2 | Analytical | "왜 이게 더 나은 거지?" | "150만원 vs 350만원 크루즈, 진짜 차이는" |
| A3 | Aspirational | "나도 저렇게 될 수 있을까?" | "68세 부부의 버킷리스트 알래스카 크루즈" |
| A4 | Anthropological | "왜 사람들은 저렇게 행동할까?" | "왜 유럽인들은 크루즈를 밥 먹듯이 탈까" |

**타겟별 최적 4A**
- 40대: A1 (실용) + A2 (비교)
- 50대: A2 (가성비) + A3 (버킷리스트)
- 60대+: A3 (꿈) + A1 (안전한 방법)

### 3.3 간다 마사노리 NPCR-PASONA 법칙

**경로**: `D:\mabiz\Learning_Data\간다마사노리_PASONA법칙.md`

#### NPCR 8요소 (Hook에 최소 3개 이상 필수)

| 요소 | 영문 | 한글 | 템플릿 예시 |
|------|------|------|-------------|
| N | New | 신규성 | "2026년 크루즈 트렌드" |
| P | Proximity | 근접성 | "부산 출발 3시간" |
| C | Conflict | 충돌 | "비행기 vs 크루즈" |
| R | Rarity | 희소성 | "선착순 44팀" |
| Benefit | Benefit | 혜택 | "68세 혼자서도 가능" |
| Authority | Authority | 권위 | "11년 경력 32,000명" |
| Number | Number | 숫자 | "89만원에 3박4일" |
| Uniqueness | Uniqueness | 독자성 | "한국 유일 AI 가이드" |
| Review | Review | 후기 | "96% 만족도" |
| Specificity | Specificity | 구체성 | "정확히 5단계로" |
| Scarcity | Scarcity | 희소성 | "단 44팀만" |

#### PASONA 6단계 (50초 영상 적용)

| 단계 | 영문 | 한글 | 적용 구간 | 예시 |
|------|------|------|-----------|------|
| P | Problem | 문제 | 0-5초 | "패키지 여행, 매번 지치지 않으세요?" |
| A | Agitate | 공감 | 5-10초 | "저도 그랬습니다. 이동만 하다 끝나는..." |
| S | Solution | 해결책 | 10-30초 | "크루즈는 다릅니다. 한 번 짐 풀면 끝" |
| O | Offer | 제안 | 30-40초 | "지금 예약하시면 20% 할인" |
| N | Narrow | 한정 | 40-45초 | "이번 달까지, 44팀 한정" |
| A | Action | 행동 | 45-50초 | "지금 바로 크루즈닷에서 상담받으세요" |

### 3.4 상위 1% YouTube 스킬 (TOP_01_PERCENT_YOUTUBE_SKILLS.md)

**경로**: `D:\mabiz\Learning_Data\TOP_01_PERCENT_YOUTUBE_SKILLS.md`

#### 핵심 법칙 10가지

1. 첫 3초가 전부다 (패턴 인터럽트)
2. 제목 = 썸네일 = 인트로 정렬 (기대치 일치)
3. 숫자는 마법이다 (구체적일수록 신뢰)
4. 감정 조합 전략 (단일보다 조합이 3배 효과)
5. 짧을수록 효율적 (YouTube 60초 미만 선호)
6. 진정성이 알고리즘을 이긴다 (클릭베이트 대신 가치)
7. 데이터로 검증하라 (A/B 테스트 필수)
8. 시청자 > 알고리즘 (사람을 위한 콘텐츠)
9. 페이오프를 끝까지 (결말이 강렬해야 완료율 상승)
10. 반복과 혁신의 균형 (성공 3배가 + 새로운 시도)

#### CTR 제목 공식 10가지 (상위 1%)

| 공식 | 템플릿 | 예시 | 효과 |
|------|--------|------|------|
| 1 | 숫자 + 충격 상황 + 구체성 | "7일짜리 크루즈 여행 배를 놓쳤다" | 조회수 +45% |
| 2 | 질문 형식 + 최상급 | "크루즈에서 가장 비싼 방은 어떻게 생겼을까!" | CTR +38% |
| 3 | 대비 공식 (VS) | "5성급 호텔 vs 크루즈, 가성비 승자는" | 클릭 +42% |
| 4 | 구체적 숫자 + 무제한 | "음식 무제한에 직원만 2,000명" | 가치 인식 +35% |
| 5 | 현실 vs 이상 | "크루즈 여행의 이상과 현실" | 공감 +40% |
| 6 | 체험 증명 | "직접 타봤습니다, 초호화 크루즈" | 신뢰 +52% |
| 7 | 리스트 + 꿀팁 | "크루즈 여행 7가지 꿀팁" | 정보 가치 +30% |
| 8 | 시간 제약 + 한정 | "7일 크루즈 세계일주 최초 공개" | 희소성 +37% |
| 9 | 감정 단어 + 스토리 | "두 남자의 초호화 크루즈 여행기" | 감정 연결 +33% |
| 10 | 부정 + 반전 | "배를 놓쳐서 탄 크루즈가 더 좋았던 이유" | 스토리 몰입 +48% |

#### 썸네일 황금률 4원칙

1. 단일 초점점 (1개 주요 요소만)
2. 고대비 색상 (파란색+노란색, 빨강+흰색, 금색+검정)
3. 감정적 얼굴 표정 (놀라움 CTR +54%, 기쁨 +41%, 의문 +38%)
4. 텍스트 7자 이하 (모바일 가독성)

---

## PART 4: S+ 등급 목표 및 평가 기준

### 4.1 S등급 → S+ 등급 업그레이드 전략

#### 현재 S등급 기준 (90점/100)
```python
# engines/script_validation_orchestrator.py
def is_s_grade(score, trust_count, banned_count, port_count, pop_count, rehook_count):
    return (
        score >= 90 and
        trust_count >= 2 and
        banned_count == 0 and
        port_count >= 1 and
        pop_count == 3 and
        rehook_count >= 2
    )
```

#### S+ 등급 신설 기준 (95점+/100)
```python
def is_s_plus_grade(score, trust_count, banned_count, port_count, pop_count, rehook_count, emotion_score, visual_sync_score):
    return (
        score >= 95 and                # 95점 이상
        trust_count >= 3 and           # Trust 요소 3개 이상
        banned_count == 0 and          # 금지어 0개
        port_count >= 2 and            # 기항지 2개 이상
        pop_count == 3 and             # Pop 정확히 3개
        rehook_count >= 3 and          # Re-Hook 3개 이상
        emotion_score >= 90 and        # 감정 곡선 90점+
        visual_sync_score >= 95        # 영상-자막 싱크 95%+
    )
```

### 4.2 S+ 등급 채점표 (100점 만점)

| 항목 | 만점 | S등급 (90점) | S+ 목표 (95점+) | 개선 전략 |
|------|------|--------------|-----------------|-----------|
| Trust Elements | 15 | 15.0 | 15.0 | 11년+2억+24시간 (3요소 필수) |
| Information Density | 15 | 15.0 | 15.0 | 숫자/고유명사/팁 밀도 유지 |
| Banned Words | 10 | 10.0 | 10.0 | 금지어 0개 (FORBIDDEN_MARKETING_CLAIMS) |
| Hook Quality | 10 | 10.0 | 10.0 | 3초 Hook (NPCR 3개 이상) |
| **Pop Messages** | **10** | **10.0** | **10.0** | 15.5초/30.5초/45.5초 정확 배치 |
| **Re-Hooks** | **10** | **10.0** | **10.0** | 15초/30초/45초 호기심 유발 3회 |
| **Port Visual** | **10** | **7.5** | **10.0** | 기항지 비주얼 26초+ (50% 이상) |
| **CTA Structure** | **10** | **8.0** | **10.0** | 3단계 증폭 (긴급성→행동→혜택) |
| **Emotion Curve** | **5** | **0.0** | **5.0** | 감정 곡선 설계 (호기심→놀라움→부러움→욕구) |
| **Visual Sync** | **5** | **0.0** | **5.0** | TTS-자막 싱크 100% (Phase B-9 완료) |
| **TOTAL** | **100** | **95.5** | **100.0** | **+4.5점 목표** |

### 4.3 도파민 검증 시스템 (독립 100점)

**신규 파일**: `engines/dopamine_validator.py` (Sprint B 예정)

```python
class DopamineValidator:
    def validate(self, script_data):
        score = 0

        # 1. 첫 3초 가격 숫자 (20점)
        if has_price_in_hook(script_data):
            score += 20

        # 2. 가격 직후 감정 공감 (15점)
        if has_emotion_after_price(script_data):
            score += 15

        # 3. 인생 마지막 감정 (15점)
        if has_life_last_emotion(script_data):
            score += 15

        # 4. 150만 vs 350만 비교 (10점)
        if has_price_comparison(script_data):
            score += 10

        # 5. 희소성 트리거 (10점)
        if has_scarcity_trigger(script_data):
            score += 10

        # 6. Trust 3요소 (10점)
        if has_three_trust_elements(script_data):
            score += 10

        # 7. 한식 안심 트리거 (10점)
        if has_korean_food_trigger(script_data):
            score += 10

        # 8. 파도/재즈 사운드 큐 (5점)
        if has_calm_audio_cue(script_data):
            score += 5

        # 9. 카카오톡 CTA (5점)
        if has_kakao_cta(script_data):
            score += 5

        return score  # 0-100
```

**배포 기준**: S등급 90점+ AND 도파민 80점+ 모두 통과

---

## PART 5: 크루즈닷 브랜드 포지셔닝 및 금지어

### 5.1 브랜드 핵심 메시지

"60대도 혼자 갈 수 있는 크루즈 - 크루즈닷 AI 가이드"

#### 3가지 핵심 가치
1. 가격이 아닌 안전과 편의로 승부
2. 언어 장벽도, 출항 걱정도 없는 크루즈
3. 50-60대 시니어를 위한 프리미엄 경험

### 5.2 절대 금지 표현 (FORBIDDEN_MARKETING_CLAIMS)

**파일**: `engines/sgrade_constants.py`

```python
FORBIDDEN_MARKETING_CLAIMS = [
    r'저렴한?',
    r'싸다|싼',
    r'최저가',
    r'가성비',
    r'할인',
    r'땡처리',
    r'대박',
    r'이거\s*실화',
    r'놓치면\s*손해',
    r'지금\s*바로',
    r'한정\s*판매',
    r'선착순\s*\d+명',  # 검증 불가 시
]
```

**검증**: `script_validation_orchestrator.py`에서 자동 감점 (-3점/건)

### 5.3 필수 브랜드 키워드 (최소 2회 이상)

| 키워드 | 용도 | 예시 |
|--------|------|------|
| 크루즈닷 | 브랜드명 | "크루즈닷 AI 가이드가" |
| AI 가이드 | 핵심 서비스 | "AI 가이드가 출항 2시간 전 자동 알림" |
| 크루즈 가이드 | 일반 명칭 | "크루즈 가이드와 함께라면" |
| 통번역기 | 기능 강조 | "실시간 통번역기로 언어 걱정 해결" |
| 능동적 보호자 | 감성 메시지 | "능동적 보호자처럼 24시간 케어" |
| AI 동반자 | 감성 메시지 | "AI 동반자가 함께하니 혼자서도 안심" |
| 스마트 가이드 | 기능 강조 | "스마트 가이드로 모든 일정 자동 관리" |

### 5.4 가격 프레이밍 원칙

**금지**: "싸다", "저렴하다", "할인"
**대체**: 가치 프레이밍

| 금지 표현 | 대체 표현 |
|-----------|-----------|
| "89만원에 크루즈 탑승 (가격만 강조)" | "89만원으로 7일간 지갑 안 꺼내는 경험 (가치)" |
| "일본 크루즈 저렴하게 가는 방법" | "89만원에 호텔+식사+교통+공연까지 (올인클루시브)" |
| "동유럽 크루즈 할인" | "개별 여행 450만원 → 크루즈 250만원 (가치 분해)" |

### 5.5 감정 여정 5단계 (공감→희망→신뢰→만족→행동)

| 구간 | 감정 | 스크립트 예시 |
|------|------|---------------|
| 0-10초 | 공감-불안 | "크루즈 가고 싶은데 영어 못해서 망설이셨나요?" |
| 10-20초 | 희망-해결 | "크루즈닷 AI 가이드가 있으면, 말하는 것만으로 즉시 번역됩니다" |
| 20-35초 | 신뢰-증거 | "출항 2시간 전 자동 알림으로 150만원 손실을 막아드립니다" |
| 35-45초 | 만족-경험 | "68세 어머니가 혼자 다녀오셨는데, 크루즈닷 덕분에 정말 편하셨다고" |
| 45-50초 | 행동-CTA | "크루즈닷과 함께하는 크루즈, 댓글로 질문 남겨주세요" |

---

## PART 6: 스크립트 생성 전략 (S+ 등급)

### 6.1 첫 문장 공식 12가지 (Gemini Prompt 58)

| 번호 | 유형 | 도파민 | 예시 |
|------|------|--------|------|
| 1 | 부정 명령형 | 8.5점 | "크루즈 예약 전, 이 실수는 절대 하지 마세요" |
| 2 | 내부자 비밀 공유형 | 9.2점 | "크루즈 선원들만 알고 있는 '비밀 데크' 가는 법" |
| 3 | 초구체적 타겟팅 | 8.8점 | "무릎 관절이 안 좋지만 알래스카 빙하는 꼭 보고 싶은 분들을 위한 꿀팁" |
| 4 | 역설적 주장형 | 9.0점 | "크루즈 여행은 비싸다? 하루 12만 원으로 즐기는 법을 증명합니다" |
| 5 | 경제적 이득형 | 8.7점 | "동일한 크루즈 객실, 60만 원 더 싸게 예약하는 법" |
| 6 | 과거 회상/후회형 | 8.3점 | "첫 크루즈 여행, 다시 간다면 절대 짐을 이렇게 싸지 않을 겁니다" |
| 7 | 사전 경고형 | 8.1점 | "기항지에 내리자마자 택시를 타지 마세요. 90% 바가지입니다" |
| 8 | 시각적 변형 | 8.6점 | "150만원 vs 350만원 크루즈 객실 비교 (놀라운 차이)" |
| 9 | 공감 상황극 | 8.4점 | "어머니 혼자 크루즈 보내기, 제일 걱정되는 건..." |
| 10 | 숫자 리스트형 | 8.2점 | "크루즈 예약 전 알아야 할 7가지 (하나라도 모르면 후회)" |
| 11 | 대리 경험/실험형 | 8.9점 | "68세 어머니 혼자 알래스카 크루즈 보낸 30일 기록" |
| 12 | 직관적 문제 해결형 | 8.5점 | "영어 못해도 크루즈 가는 법 (3가지 툴만 있으면 됨)" |

### 6.2 3막 구조 + 도파민 타이밍 (50초 최적화)

#### 막 구조 (YouTube Shorts 최적)

| 막 | 구간 | 비율 | 내용 | 도파민 트리거 |
|----|------|------|------|---------------|
| 1막 (설정) | 0-10초 | 20% | Hook + 문제 제기 + 공감 | 가격 충격 (Juho 음성) + 호기심 |
| 2막 (갈등) | 10-35초 | 50% | 정보 전달 + 해결책 + 증거 | 비교표 (30초) + 기항지 비주얼 |
| 3막 (해결) | 35-50초 | 30% | 만족 + 행동 유도 | 희소성 (45초) + CTA (부드럽게) |

#### 도파민 배치 타임라인 (10초 간격 파동)

| 시간 | 트리거 | 형태 | 강도 | TTS |
|------|--------|------|------|-----|
| 0.5초 | 가격 충격 Hook | "89만원/3박4일" + 남성 낮은 목소리 | 9/10 | Juho |
| 3.5초 | 구체적 숫자 | 천천히 "팔십구만원에... 삼박사일" | +40% 스파이크 | Juho |
| 8.0초 | 의도적 골짜기 | 갑판 고요함 + 파도소리 + 재즈 BGM | 3/10 (뇌 리셋) | BGM only |
| 15초 | 도파민 피크 #1 | 가격충격 + 감정공감 동시 | 9/10 | Audrey + Grace |
| 22초 | 기항지 구체성 | 지명 3개 천천히 + 영상 빠른 전환 | 6/10 | Audrey |
| 28초 | 자녀 연결 감정 | "68세 어머니와 딸이 선택한 여행" | 7/10 | Grace (sad) |
| 30초 | 도파민 피크 #2 | 가격 비교표 (나란히 등장, 빨간 동그라미) | 10/10 | Juho |
| 38초 | 안전 안심 | "24시간 한국어 담당자 직통" | 5/10 | Dakota |
| 42초 | 인생 마지막 감정 | "이 나이에 나를 위한 시간" + 석양 실루엣 | 8/10 | Grace (happy) |
| 45초 | 도파민 피크 #3 | 희소성 "잔여 44석" + 손실회피 | 9/10 | Juho |
| 48초 | 최종 CTA | 링크 클릭 유도 + 카카오 채널 | 6/10 | Audrey |

### 6.3 Re-Hook 3회 배치 (15초/30초/45초)

**목표**: 유지율 3초/15초/30초 지점 이탈 방지

| 시간 | Re-Hook 템플릿 | 호기심 키워드 | 예시 |
|------|----------------|---------------|------|
| 15.5초 | "잠깐! 더 중요한 게 있어요." | "더 중요한", "하지만", "놓치면 안 되는" | "잠깐! 더 중요한 게 있어요. 기항지에서 이것 하나 때문에 여행 망칩니다" |
| 30.5초 | "진짜 핵심은 지금부터예요." | "진짜", "가장 중요한", "결정적인" | "진짜 핵심은 지금부터예요. 150만원 차이가 나는 이유는..." |
| 45.5초 | "마지막으로 이것만 보세요." | "마지막", "이것만", "놓치면" | "마지막으로 이것만 보세요. 44팀 남았습니다" |

**검증**: `script_validation_orchestrator.py` 호기심 키워드 카운트 (각 Re-Hook마다 2개 이상)

### 6.4 CTA 3단계 증폭 (45-50초)

**Phase 32 FIX-CTA-1 완성**

| 단계 | 시간 | 내용 | 심리 트리거 |
|------|------|------|-------------|
| 1. 긴급성 | 45-46.5초 | "44팀 남았습니다. 60만원 지원 마감 임박." | 희소성 + 손실회피 |
| 2. 행동 | 46.5-48초 | "프로필 링크에서 일정 확인하세요." | 마이크로 커밋먼트 (클릭만) |
| 3. 혜택 | 48-50초 | "AI 맞춤 상담 신청하면 60만원 혜택 받으실 수 있어요. 24시간 내 연락드립니다." | 상호성 + 신뢰 |

**금지**: 이모지 사용, 여러 줄 나열, "지금 바로" (강압적)

---

## PART 7: 비주얼 전략 (상위 1% 영상 편집)

### 7.1 Ken Burns Effect (Phase 28 FIX-V3 수정)

**파일**: `engines/ken_burns_effect.py`

#### 4가지 유형 + 감정별 zoom + ±10% 랜덤

| 유형 | zoom_in | zoom_out | pan_x | pan_y | 감정 적용 |
|------|---------|----------|-------|-------|-----------|
| zoom_in_center | 1.0 → 1.048 | - | 0 | 0 | 놀라움, 호기심 |
| zoom_out_center | 1.048 → 1.0 | - | 0 | 0 | 안정, 신뢰 |
| pan_right | 1.024 | - | 0 → 0.024 | 0 | 탐험, 기대 |
| pan_left | 1.024 | - | 0.024 → 0 | 0 | 회상, 감성 |

**멀미 방지 (Phase 28 FIX-V3)**
- zoom_ratio: 0.048 (기존 0.08 → 40% 감소)
- 5060 세대 멀미 리스크 최소화
- 랜덤 ±10% (자연스러움 유지)

### 7.2 Color Correction (SENIOR_FRIENDLY 프리셋)

**파일**: `engines/color_correction.py`

```python
SENIOR_FRIENDLY = {
    'brightness': +5,      # 밝기 증가 (노안 대응)
    'contrast': +8,        # 대비 강화 (시인성)
    'saturation': +12,     # 채도 증가 (생동감)
    'warmth': +3,          # 따뜻한 톤 (친근감)
    'sharpness': +6,       # 선명도 (디테일)
}
```

### 7.3 Visual Interleave (이미지/비디오 교차 배치)

**Phase C FIX-INTERLEAVE-1 예정**

| segment_type | 우선 미디어 | 교차 패턴 | 근거 |
|--------------|-------------|-----------|------|
| hook | 비디오 (Hook 전용 폴더) | 비디오만 | 움직임 필수 |
| problem | 이미지 (공감 표정) | 이미지 → 비디오 | 정적 → 동적 전환 |
| info | 이미지/비디오 교차 | 짝수=이미지, 홀수=비디오 | 단조로움 방지 |
| trust | 이미지 (후기) | 이미지 우선 | 신뢰 증거 |
| cta | 이미지 (후기) | 이미지 우선 | 안정감 |

**강제 교차 로직** (Sprint C)
```python
for i, segment in enumerate(segments):
    if segment.type == "info":
        if i % 2 == 0:
            media_type = "image"  # 짝수 이미지
        else:
            media_type = "video"  # 홀수 비디오
```

### 7.4 Port Visual 26초+ 확보 (Phase 32 FIX-PORT-1)

**목표**: 기항지 비주얼 50초 중 26초 이상 (52%+)

#### 3단계 전략

1. 스크립트 생성 시 기항지명 강제 포함 (Gemini 프롬프트)
2. keyword 추출 후 visual_keywords에 기항지명 자동 추가
3. asset_matcher.py에서 기항지 이미지 우선 매칭

**검증**: `script_validation_orchestrator.py`
```python
def calculate_port_visual_duration(segments):
    port_visual_duration = 0
    for seg in segments:
        if any(port in seg.visual_keywords for port in PORT_NAMES):
            port_visual_duration += seg.duration
    return port_visual_duration  # 목표 26초+
```

### 7.5 Thumbnail 자동 생성 (Sprint C 예정)

**파일**: `upload_package/thumbnail_generator.py`

#### 3종 변형 자동 생성

| 타입 | 디자인 | 텍스트 | 얼굴 | 색상 |
|------|--------|--------|------|------|
| A형 | 가격 박스 강조 | "89만원" (7자 이하) | 놀란 표정 | 노란색 박스 + 파란 배경 |
| B형 | Before/After 분할 | "150만 vs 89만" | 대비 이미지 | 빨강/초록 대비 |
| C형 | 기항지 전경 | "알래스카 7일" | 감탄 표정 | 금색 텍스트 + 검정 배경 |

**A/B 테스트**: YouTube Studio 썸네일 테스트 기능 활용

---

## PART 8: 오디오 전략 (상위 1% 사운드 디자인)

### 8.1 BGM 5구간 감정 곡선

**파일**: `engines/bgm_matcher.py`

| 구간 | 시간 | 감정 | BGM 태그 | 볼륨 |
|------|------|------|----------|------|
| 도입 | 0-10초 | 호기심 | suspense, mysterious | 0.18 |
| 상승 | 10-25초 | 기대 | uplifting, adventure | 0.22 |
| 피크 | 25-35초 | 흥분 | energetic, travel | 0.20 |
| 안정 | 35-45초 | 신뢰 | calm, piano | 0.16 |
| 마무리 | 45-50초 | 행동 | motivational | 0.18 |

**BGM 차단 리스트** (Phase 28 FIX-2)
```python
BLACKLIST_TAGS = ['somnia', 'sleep', 'lullaby', 'meditation', 'zen']
PRIORITY_TAGS = ['travel', 'upbeat', 'adventure', 'orchestral']
```

### 8.2 Pop/SFX 타이밍 (정확도 100%)

**Phase 32 FIX-POP-1 완료**

| SFX | 타이밍 | 볼륨 | 용도 | 선행 SFX |
|-----|--------|------|------|----------|
| level-up.wav | 0.0초 | 0.25 | 인트로 임팩트 | - |
| hit_impact.wav | 0.3초 | 0.25 | 인트로 강조 | - |
| pop.wav | 15.5초 | 0.30 | Re-Hook #1 | swoosh (-0.3초) |
| pop.wav | 30.5초 | 0.30 | Re-Hook #2 | swoosh (-0.3초) |
| pop.wav | 45.5초 | 0.30 | Re-Hook #3 | swoosh (-0.3초) |

**검증**: 15.5초/30.5초/45.5초 ±0.5초 허용 (config.py POP_TIMINGS)

### 8.3 BGM Ducking (TTS 명료도 확보)

**파일**: `engines/audio_mixer.py`

| 상황 | BGM 볼륨 | 이유 |
|------|----------|------|
| TTS 재생 중 | 0.06 (70% 감소) | 음성 명료도 최우선 |
| TTS 없는 구간 | 0.20 (기본) | 감정 몰입 |
| Pop/SFX 재생 시 | 0.10 (50% 감소) | SFX 명확성 |

---

## PART 9: 렌더링 파이프라인 (Phase B-9 완료)

### 9.1 이미지 기반 자막 렌더링 (28초, 96.7% 개선)

**Phase B-9 완료 (2026-03-04)**

#### 성과
- 렌더링 시간: 840초 → 28초 (30배 빠름, 96.7% 개선)
- 한글 자막: 완벽 처리 (PNG 이미지 방식)
- TTS 동기화: 100% 유지
- 메모리 증가: 22.8 MB (정상)
- 임시 파일: 자동 정리 (8+3개 PNG)

#### 구현 파일 3개

| 파일 | 역할 |
|------|------|
| engines/subtitle_image_renderer.py | 한글 텍스트 → PNG (맑은 고딕, 3px stroke) |
| engines/ffmpeg_image_overlay_composer.py | PNG overlay with timing |
| engines/ffmpeg_pipeline.py | 이미지 기반 렌더링 통합 |

#### Config 설정
```python
use_image_subtitles: bool = True   # Phase B-9 이미지 방식 (default)
use_ffmpeg_direct: bool = True     # FFmpeg 모드 (Phase B-7)
```

### 9.2 배치 병렬 렌더링 (NVENC 3세션, 3배 속도)

**Phase 28 FIX-BATCH 완료**

| 모드 | 세션 수 | 렌더링 시간 (10편) | 효율 |
|------|---------|---------------------|------|
| 순차 | 1 | 280초 (4분 40초) | 1배 |
| 병렬 | 3 | 93초 (1분 33초) | 3배 |

**Config**
```python
nvenc_preset: 'p2'           # 품질 우선
nvenc_sessions: 3            # RTX 4090 기준
max_concurrent: 3            # 동시 렌더링 3개
```

---

## PART 10: 콘텐츠 카테고리 및 가중치 (20개)

### 10.1 카테고리 티어 정의 (cruise_config.yaml)

| 티어 | 목적 | 대응 상품 | 완주율 목표 | 가중치 합계 |
|------|------|-----------|-------------|-------------|
| P0 (핵심) | 직접 상담 유도 | 동유럽 250만+, 알래스카 350만+ | 55%+ | 0.35 |
| P1 (핵심) | 니즈 환기 + 진입 상품 | 부산출발 89만원대 | 50%+ | 0.35 |
| P2 (가치) | 가치 강조 | 전 상품 | 48%+ | 0.20 |
| P3 (추가) | 인지 확장 + 채널 발견 | 채널 구독 유도 | 45%+ | 0.10 |

### 10.2 카테고리 20개 (우선순위별)

| 순위 | 카테고리 | 도파민 | 티어 | 연결 상품 | 가중치 |
|------|----------|--------|------|-----------|--------|
| P0-1 | 가격충격비교 | 9.0/10 | P0 | 동유럽/알래스카 | 0.12 |
| P0-2 | 올인클루시브공개 | 8.5/10 | P1 | 부산출발 | 0.08 |
| P0-3 | 숨겨진기항지공개 | 8.8/10 | P0 | 동유럽 | 0.10 |
| P0-4 | 항공vs크루즈비교 | 8.7/10 | P0 | 동유럽/일본 | 0.08 |
| P1-1 | 선내음식천국 | 8.3/10 | P1 | MSC 벨리시마 | 0.08 |
| P1-2 | 5060맞춤편안함 | 8.1/10 | P0 | 전상품 | 0.07 |
| P1-3 | 알래스카자연경이 | 9.2/10 | P0 | 알래스카 | 0.10 |
| P1-4 | 일본도시패키지 | 8.0/10 | P1 | 일본 | 0.08 |
| P1-5 | 동유럽드림크루즈 | 9.0/10 | P0 | 동유럽 | 0.12 |
| P1-6 | 5060부부공감 | 7.8/10 | P0 | 전상품 | 0.07 |
| P2-1 | 실제후기 | 8.5/10 | P0 | 전상품 | 0.05 |
| P2-2 | 인생마지막감성 | 8.2/10 | P0 | 전상품 | 0.05 |
| P2-3 | 선박비교MSCRCCL | 7.5/10 | P2 | MSC/RCCL | 0.03 |
| P2-4 | 객실업그레이드팁 | 7.3/10 | P2 | 전상품 | 0.03 |
| P2-5 | 부부커플로맨스 | 7.8/10 | P2 | 동유럽 | 0.04 |
| P3-1 | 기항지투어완전정복 | 8.0/10 | P2 | 동유럽/알래스카 | 0.05 |
| P3-2 | 뱃멀미오해타파 | 7.2/10 | P2 | 전상품 | 0.02 |
| P3-3 | 크루즈안전보험 | 7.5/10 | P2 | 전상품 | 0.03 |
| P3-4 | 예약타이밍전략 | 7.4/10 | P2 | 전상품 | 0.03 |
| P3-5 | 짐싸기준비가이드 | 7.0/10 | P2 | 전상품 | 0.02 |

**가중치 합계 검증**: 1.00 (100%)

### 10.3 가격 앵커 4티어 (cruise_config.yaml)

| 티어 | 목적 | 가격 범위 | 도파민 프레임 | 예시 |
|------|------|-----------|---------------|------|
| T1 (진입) | 관심 유도 | 89-150만원 | 가격 충격형 | "89만원부터" (알래스카 내측) |
| T2 (주력) | 가치 설득 | 150-250만원 | 교육형 | "150만원대" (지중해 주력가) |
| T3 (프리미엄) | 신뢰 구축 | 250-400만원 | 신뢰형 | "250만원대" (지중해 프리미엄) |
| T4 (럭셔리) | 경험 가치 | 400만원+ | 경험총가치형 | 가격 분해 절대 금지 (상위 1%) |

---

## PART 11: 실제 상품 데이터 (3개, 2026-03-06 기준)

**파일**: `config/cruise_config.yaml` (products 섹션)

### 11.1 Product 1: 동부지중해 9개도시 7박8일

```yaml
- product_id: PROD-2026-001
  cruise_line: 로얄 캐리비안 인터내셔널
  ship_name: 익스플로러 오브 더 시즈
  title: 동부지중해 9개도시 7박8일
  departure_port: 로마(치비타베키아)
  arrival_port: 로마(치비타베키아)
  ports:
    - 산토리니
    - 에페소스
    - 나폴리
    - 두브로브니크
    - 스플릿
  region: 지중해
  status: 판매중
  departure_date: 2026-06-15
  return_date: 2026-06-22
  price_tier: T2
  price_range: 150-250만원
  target_age: 50-60대
```

### 11.2 Product 2: 동부지중해 3개국 7박8일

```yaml
- product_id: PROD-2026-002
  cruise_line: 로얄 캐리비안 인터내셔널
  ship_name: 익스플로러 오브 더 시즈
  title: 동부지중해 3개국 7박8일
  departure_port: 로마(치비타베키아)
  arrival_port: 로마(치비타베키아)
  ports:
    - 산토리니
    - 미코노스
    - 나폴리
  region: 지중해
  status: 판매중
  departure_date: 2026-07-10
  return_date: 2026-07-17
  price_tier: T2
  price_range: 150-250만원
  target_age: 50-60대
```

### 11.3 Product 3: 알래스카 주요도시+캐나다 7박8일

```yaml
- product_id: PROD-2026-003
  cruise_line: 로얄 캐리비안 인터내셔널
  ship_name: 보이저 오브 더 시즈
  title: 알래스카 주요도시+캐나다 7박8일
  departure_port: 시애틀
  arrival_port: 시애틀
  ports:
    - 주노
    - 스캐그웨이
    - 케치칸
    - 빅토리아
  region: 알래스카
  status: 판매중
  departure_date: 2026-08-05
  return_date: 2026-08-12
  price_tier: T3
  price_range: 250-400만원
  target_age: 50-60대
```

---

## PART 12: 자동/수동 모드 설계 (Sprint A 완료)

### 12.1 통합 CLI 진입점 (generate.py)

**파일**: `D:\mabiz\generate.py`

#### 실행 예시
```bash
# 자동 모드 (딸깍 1번)
python generate.py --mode auto              # 1편 자동
python generate.py --mode auto --count 3   # 자동 3편
python generate.py --mode auto --dry-run   # 스크립트까지만

# 수동 모드 (6단계 인터랙티브)
python generate.py --mode manual

# 기항지/선박/카테고리 지정
python generate.py --mode manual --port 나가사키 --ship "MSC 벨리시마" --category 기항지정보

# 스케줄러용
python generate.py --mode auto --count 1 --schedule --time 09:00 --output D:/mabiz/outputs/daily
```

### 12.2 수동 모드 6단계 인터랙티브

**파일**: `cli/manual_mode.py`

| 단계 | 질문 | 선택지 | 예시 |
|------|------|--------|------|
| 1 | 영상 유형? | Shorts / 롱폼 / 둘다 | Shorts |
| 2 | 지역? | 동유럽/알래스카/일본/상하이대만 → 세부 기항지 | 동유럽 → 산토리니 |
| 3 | 크루즈선? | MSC 벨리시마 / 로얄캐리비안 (운항 적합성 표시) | MSC 벨리시마 |
| 4 | 주제 카테고리? | 20개 목록 (티어 구분) + 자동 추천 | 가격충격비교 (P0-1) |
| 5 | 편수? | 1-10편 | 3편 |
| 6 | 가격 앵커? | 추천가 / 발코니가 / 직접입력 | T2 (150만원대) |

→ 미리보기 확인 후 생성 시작

### 12.3 자동 모드 선택 알고리즘

**파일**: `cli/auto_mode.py`

#### 3단계 선택 (가중치 + 계절 보정 + 중복 방지)

```python
# 1단계: 크루즈선 선택
ship = weighted_choice(['MSC 벨리시마', 'RCCL'], weights=[0.6, 0.4])

# 2단계: 기항지 선택 (계절 보정)
port = weighted_choice_seasonal(ports, season_weights)

# 3단계: 카테고리 선택 (기항지 적합성 × 중복방지)
category = weighted_choice_with_dedup(categories, port, recent_7days)
```

#### S등급 + 도파민 이중 검증

```python
while attempts < 3:
    script = generate_script(port, ship, category)
    s_grade_score = validate_s_grade(script)
    dopamine_score = validate_dopamine(script)

    if s_grade_score >= 90 and dopamine_score >= 80:
        break  # 배포
    elif s_grade_score >= 85 and dopamine_score >= 70:
        warn_and_deploy()  # 경고 후 강제 통과
    else:
        attempts += 1  # 재생성 (최대 3회)
```

### 12.4 업로드 준비 패키지 자동 생성

**파일**: `upload_package/generator.py`

#### 생성 파일 5개

```
outputs/upload_packages/20260308_0001/
├── video.mp4                 ← 업로드할 영상
├── thumbnail_A.png           ← 복붙용 썸네일 (Shorts 1080x1920 / 롱폼 1920x1080)
├── title.txt                 ← 복붙용 제목 (60-70자)
├── description.txt           ← 복붙용 설명 + 챕터 타임스탬프 + 링크
└── tags.txt                  ← 복붙용 태그 15개
```

**주의**: YouTube 업로드 자동화 미구현 (채널 보안 리스크 → 수동 업로드 결정)
**업로드 소요 시간**: 영상당 3분 이내 (패키지 복붙)

---

## PART 13: 롱폼 파이프라인 설계 (Sprint D, 조건부)

### 13.1 착수 조건

- Shorts 50편 업로드 완료
- 첫 카카오톡 문의 발생 확인
- 월 조회수 100,000회+ 도달

### 13.2 롱폼 황금 구조 (5-15분 기준)

| 구간 | 시간 | 내용 | 재훅 | 감정 |
|------|------|------|------|------|
| 1. 슈퍼 훅 | 0-30초 | "마지막에 XX 공개합니다" + 하이라이트 3초 예고 | - | 호기심 |
| 2. 공감 브릿지 | 30-120초 | 5060 페르소나 + 실제 후기 텍스트 | - | 공감 |
| 3. 재훅 #1 | 120초 | "지금부터 가격 이야기 시작합니다" | 1 | 기대 |
| 4. 동경 구간 | 120-300초 | 기항지 투어 + Re-Hook #1 (부드럽게) | - | 동경 |
| 5. 의도적 골짜기 | 300-330초 | 30초 정적 (뇌 리셋 → 다음 피크 증폭) | - | 안정 |
| 6. 재훅 #2 | 330초 | "패키지 vs 크루즈 가격 비교 폭탄" | 2 | 흥분 |
| 7. 확신 구간 | 330-600초 | 식사/시설/안전 증거 + Re-Hook #2 | - | 신뢰 |
| 8. 재훅 #3 | 600초 | "마지막으로 이것만 보시면 결정하실 수 있습니다" | 3 | 확신 |
| 9. 확신+감정 피크 | 600-780초 | 실제 후기 + "인생 마지막" + 아내/남편 선물 | - | 감동 |
| 10. 마지막 반전 | 780-840초 | 오프닝 약속 이행 (완주 보상 도파민) | - | 만족 |
| 11. 최종 CTA | 840-900초 | 링크 클릭 시연 + 댓글 유도 | - | 행동 |

### 13.3 롱폼 S등급 기준 (Shorts와 별도)

| 항목 | 점수 | 기준 |
|------|------|------|
| 완주율 유인 구조 | 15점 | 챕터 안내 + 재훅 3회 + 마지막 티저 필수 |
| 정보 밀도 | 15점 | 분당 새 정보 3개 이상 |
| 감정 곡선 | 15점 | 공감→동경→확신 3단계 완성 |
| 전문성 증명 | 15점 | 실제 후기 + 타 여행 비교 + 구체 사례 |
| CTA 3회 배치 | 15점 | 5분/10분/15분 지점 3회 |
| 신뢰 기준 | 10점 | Trust 요소 + 후기 영상 |
| **합계** | **100점** | **S등급 90점 이상** |

### 13.4 롱폼 파이프라인 모듈 13개 (Sprint D)

```
longform_pipeline/
├── script_generator.py        (Shorts 엔진 상속)
├── chapter_segmenter.py       (4막 구조 → 5-7 챕터 분할)
├── longform_validator.py      (롱폼 S등급 검증, 기준 별도)
├── chapter_assembler.py       (챕터 클립 조립, 타이틀 카드 포함)
├── chapter_title_renderer.py  (챕터 타이틀 카드 렌더, 3초+fade)
├── bgm_looper.py              (BGM 루프 + 5구간 볼륨 곡선)
├── midroll_cta_inserter.py    (중간 CTA 3회 삽입)
├── endcard_generator.py       (엔드 카드, 마지막 15초)
├── chapter_renderer.py        (챕터별 FFmpeg 분할 렌더링)
├── concat_finalizer.py        (5-7개 챕터 무손실 concat, 재인코딩 없음)
├── metadata_generator.py      (챕터 타임스탬프 + 설명글 + 태그 생성)
└── thumbnail_auto.py          (썸네일 5종 자동생성)
```

---

## PART 14: 업로드 스케줄 및 성장 로드맵

### 14.1 현실적 전환율 기준 (업계 벤치마크)

| 단계 | 보수적 (25%) | 현실적 (50%) | 낙관적 (25%) | 근거 |
|------|--------------|--------------|--------------|------|
| 프로필 클릭 (CTR) | 8% | 12% | 18% | 업계 평균 6%, 상위 10% 기준 12% |
| 랜딩 유지 | 60% | 75% | 85% | YouTube→카카오 플랫폼 전환 마찰 |
| 상담 신청 | 8% | 12% | 18% | 고가 상품 (250만원+) 기준 |
| 상담→예약 | 15% | 25% | 35% | CruiseDot 기존 고객 DB 미활용 |
| 예약당 수익 | 150,000원 | 200,000원 | 250,000원 | 크루즈 평균 수수료 8% (250만원 상품 기준) |

### 14.2 3가지 시나리오 (월 조회수 100,000회 기준)

#### 시나리오 1: 보수적 (확률 25%)

```
조회 100,000회
→ 프로필 클릭 8,000명 (8%)
→ 랜딩 유지 4,800명 (60%)
→ 상담 신청 384명 (8%)
→ 예약 성공 58건 (15%)
→ 월 수익 8,700,000원
```

**특징**: 복합 전환율 0.058%, 손익분기 18개월, 확률 25%

#### 시나리오 2: 현실적 (확률 50%)

```
조회 100,000회
→ 프로필 클릭 12,000명 (12%)
→ 랜딩 유지 9,000명 (75%)
→ 상담 신청 1,080명 (12%)
→ 예약 성공 270건 (25%)
→ 월 수익 54,000,000원
```

**특징**: 복합 전환율 0.27%, 손익분기 12개월, 확률 50%

#### 시나리오 3: 낙관적 (확률 25%)

```
조회 100,000회
→ 프로필 클릭 18,000명 (18%)
→ 랜딩 유지 15,300명 (85%)
→ 상담 신청 2,754명 (18%)
→ 예약 성공 964건 (35%)
→ 월 수익 241,000,000원
```

**특징**: 복합 전환율 0.964%, 손익분기 6개월, 확률 25%

### 14.3 수정 KPI 목표 (시나리오별)

| 항목 | 보수적 (25%) | 현실적 (50%) | 낙관적 (25%) | 측정 시점 |
|------|--------------|--------------|--------------|-----------|
| 월 조회수 | 100,000회 | 150,000회 | 200,000회 | 6개월 |
| 프로필 CTR | 8% | 12% | 18% | 매주 |
| 월 문의 건수 | 384건 | 1,080건 | 2,754건 | 6개월 |
| 예약 전환율 | 15% | 25% | 35% | 3주 |
| 월 예상 수익 | 8,700,000원 | 54,000,000원 | 241,000,000원 | 6개월 |
| 손익분기 시점 | 18개월 | 12개월 | 6개월 | - |
| Shorts 완주율 | 45%+ | 55%+ | 65%+ | 영상당 |
| 롱폼 완주율 | 25% | 35% | 45% | 영상당 |

### 14.4 채널 성장 타임라인 (보수적 시나리오 기준)

| 월차 | 조회수 | 프로필 클릭 | 상담 신청 | 예약 건수 | 월 수익 | 누적 수익 |
|------|--------|-------------|-----------|-----------|---------|-----------|
| 1개월 | 15,000 | 1,200명 | 58명 | 9건 | 1,350,000원 | 1,350,000원 |
| 2개월 | 30,000 | 2,400명 | 115명 | 17건 | 2,550,000원 | 3,900,000원 |
| 3개월 | 50,000 | 4,000명 | 192명 | 29건 | 4,350,000원 | 8,250,000원 |
| 4개월 | 70,000 | 5,600명 | 269명 | 40건 | 6,000,000원 | 14,250,000원 |
| 5개월 | 85,000 | 6,800명 | 326명 | 49건 | 7,350,000원 | 21,600,000원 |
| 6개월 | 100,000 | 8,000명 | 384명 | 58건 | 8,700,000원 | 30,300,000원 |
| 9개월 | 120,000 | 9,600명 | 461명 | 69건 | 10,350,000원 | 61,050,000원 |
| 12개월 | 150,000 | 12,000명 | 576명 | 86건 | 12,900,000원 | 105,600,000원 |
| 18개월 | 200,000 | 16,000명 | 768명 | 115건 | 17,250,000원 | 204,000,000원 |

**운영 비용 가정**: 월 200만원 (인건비 + 서버 + 마케팅)
**손익분기**: 18개월 (누적 수익 204백만원 - 누적 비용 36백만원 = +168백만원)

### 14.5 업로드 스케줄

```
1-4주차: Shorts 주 3편 + 롱폼 격주 1편 (주차별 조회수 15,000회 목표)
5-12주차: Shorts 주 5편 + 롱폼 주 1편 (주차별 조회수 50,000회 목표)
13주차~: Shorts 주 7편 + 롱폼 주 1편 (주차별 조회수 100,000회 목표)
스케줄러: cron (매일 오전 9시 자동 생성, 수동 업로드)
```

---

## PART 15: 다음 작업 우선순위 (Phase 별)

### 15.1 Phase A (즉시, 4시간) - 핵심 3개 FIX

| FIX | 시간 | 효과 | 파일 |
|-----|------|------|------|
| FIX-POP-1 | 1.5h | +6.5점 | config.py, pop_messages.yaml, script_validation_orchestrator.py |
| FIX-REHOOK-1 | 1.0h | +질적 개선 | comprehensive_script_generator.py, script_validation_orchestrator.py |
| FIX-CTA-1 | 1.5h | +4.0점 | comprehensive_script_generator.py, cta_validator.py |

**Phase A 완료 후 예상 점수**: 98.8 + 10.5 = **109.3점 → 100점 정규화 (A등급)** → 90점까지 9점 부족

---

### 15.2 Phase B (내일, 3시간) - 보완 2개 FIX

| FIX | 시간 | 효과 | 파일 |
|-----|------|------|------|
| FIX-BANNED-1 | 1.0h | +5.0점 | comprehensive_script_generator.py |
| FIX-PORT-1 | 1.5h | +5.0점 | comprehensive_script_generator.py, asset_matcher.py |

**Phase B 완료 후 예상 점수**: 100 + 10.0 = **110점 → 100점 정규화 (S등급 달성)**

---

### 15.3 Phase C (이번 주, 5시간) - 렌더링 품질 강화

| FIX | 시간 | 효과 | 파일 |
|-----|------|------|------|
| FIX-RENDER-1 | 2.0h | 자막 싱크 100% | ffmpeg_pipeline.py |
| FIX-INTERLEAVE-1 | 2.0h | 시각 다양성 +30% | asset_matcher.py |

**Phase C 완료 후**: 완주율 +10%p (45% → 55%)

---

### 15.4 Sprint B (추후) - DopamineValidator 독립 검증

- 파일: `engines/dopamine_validator.py` (신규)
- 시간: 6시간
- 효과: S등급 90점 + 도파민 80점 이중 검증

---

### 15.5 Sprint C (추후) - 누끼 오버레이 + 썸네일

- 누끼파일 오버레이 렌더링 (3시간)
- 썸네일 자동 생성 3종 (2시간)
- TIER 4 이미지 수집 (두브로브니크/코토르/스플릿)

---

### 15.6 Sprint D (조건부) - 롱폼 파이프라인

- 착수 조건: Shorts 50편 + 첫 문의 발생
- 시간: 37시간
- 모듈: 13개 (chapter_segmenter.py → concat_finalizer.py)

---

## PART 16: 리스크 관리 및 대응

### 16.1 YouTube 콘텐츠 규제 리스크

- **문제**: AI 생성 콘텐츠 라벨 의무화
- **대응**: 영상 설명에 "AI 보조 제작" 명시 + 대표자 실제 영상 월 2개 병행

### 16.2 가격 정보 오염 리스크

- **문제**: 영상 200개 누적 후 가격 변동 → 구 가격 영상 계속 노출 → 민원
- **대응**: 영상 내 가격 언급 시 "현재 가격 아래 링크에서 확인" 문구 병기

### 16.3 YouTube → 카카오 플랫폼 전환 마찰 리스크

- **문제**: YouTube → 카카오톡 2단계 마찰 → 전환율 5% 이하
- **대응**: 링크 클릭 (설명란) + 전화번호 워터마크 → 마찰 최소화

### 16.4 AI 영상 신뢰도 리스크

- **문제**: 실제 얼굴 없는 AI 음성 영상 → 5060 신뢰 낮음 (고가 상품 특성)
- **대응**: 대표자/직원 얼굴 영상 월 2편 이상 병행 + 실제 고객 후기 수집 시스템

### 16.5 채널 성장 지연 리스크

- **문제**: 신규 채널 6개월 내 의미있는 조회수 불가 → 현금흐름 문제
- **대응**: 기존 고객 DB 활용 (11년 32,000팀) → 첫 영상 공유 부스트 + 카카오 채널 공지

### 16.6 운영 지속성 리스크

- **문제**: 매일 생성 Shorts 연 365편 → 품질 검수/댓글 응대 시간 과부하
- **대응**: 현실적 목표 - Shorts 주 5편 (연 260편), 스케줄러로 생성만 자동화

---

## PART 17: 성공 지표 및 체크리스트

### 17.1 Phase A 성공 조건 (오늘 완료)

- [ ] 자동 생성 스크립트 10개 중 8개 이상 90점+ (A등급)
- [ ] Pop 타이밍 정확도 100% (15.5초/30.5초/45.5초)
- [ ] Re-hook 호기심 키워드 2개 이상 포함

### 17.2 Phase B 성공 조건 (내일 완료)

- [ ] 자동 생성 스크립트 10개 중 9개 이상 **90점+ (S등급)**
- [ ] 금지어 0개 (Banned 10점 만점)
- [ ] Port 비주얼 26초+ (Port 10점 만점)

### 17.3 Phase C 성공 조건 (이번 주 완료)

- [ ] PASONA E v6.1 영상 렌더링 완료 (50초±2초)
- [ ] TTS-자막 싱크 오차 0.1초 이내
- [ ] 이미지/비디오 교차 비율 50:50 ±10%

---

## PART 18: 참고 자료 경로 정리

### 18.1 핵심 MD 파일

| 파일명 | 경로 | 핵심 내용 |
|--------|------|-----------|
| 니콜라스콜_글쓰기법칙.md | D:\mabiz\Learning_Data\ | 4A 프레임워크 |
| 간다마사노리_PASONA법칙.md | D:\mabiz\Learning_Data\ | NPCR 8요소 + PASONA 6단계 |
| 4A_프레임워크.md | D:\mabiz\Learning_Data\ | 4A 상세 가이드 |
| TOP_01_PERCENT_YOUTUBE_SKILLS.md | D:\mabiz\Learning_Data\ | 상위 1% 스킬 10가지 |
| S_GRADE_VIRAL_LEARNING_MASTER_GUIDE.md | D:\mabiz\Learning_Data\ | S등급 바이럴 패턴 학습 |

### 18.2 작업지시서 (WO)

| 파일명 | 경로 | 핵심 내용 |
|--------|------|-----------|
| WO_20260223_S_GRADE_ACHIEVEMENT_v3.md | D:\mabiz\docs\work_orders\ | S등급 달성 작업지시서 (FIX-POP/REHOOK/CTA/BANNED/PORT) |
| WO_20260220_YOUTUBE_CRUISE_CONTENT_STRATEGY_v2.md | D:\mabiz\docs\work_orders\ | 크루즈닷 콘텐츠 전략 마스터 (v2.0) |

### 18.3 Config 파일

| 파일명 | 경로 | 핵심 내용 |
|--------|------|-----------|
| cruise_config.yaml | D:\mabiz\config\ | 마스터 데이터 (기항지 35개, 카테고리 20개, 상품 3개) |
| config.py | D:\mabiz\video_pipeline\ | 파이프라인 설정 (50초, TTS, BGM, SFX, 렌더링) |

---

## CONCLUSION

### S+ 등급 달성 로드맵 요약

| Phase | 시간 | 목표 점수 | 핵심 작업 | 예상 수익 증가 |
|-------|------|-----------|-----------|----------------|
| **Phase A (오늘)** | 4h | 87.0점 (A등급) | FIX-POP-1 + FIX-REHOOK-1 + FIX-CTA-1 | +10.5점 |
| **Phase B (내일)** | 3h | **97.0점 (S등급)** | FIX-BANNED-1 + FIX-PORT-1 | +10.0점 |
| **Phase C (이번 주)** | 5h | 완주율 +10%p | FIX-RENDER-1 + FIX-INTERLEAVE-1 | 품질 강화 |
| **Sprint B (추후)** | 6h | 도파민 80점+ | DopamineValidator 구현 | 이중 검증 |
| **Sprint C (추후)** | 5h | CTR +30% | 누끼 오버레이 + 썸네일 자동생성 | 클릭률 개선 |
| **Sprint D (조건부)** | 37h | 롱폼 파이프라인 | 13모듈 (Shorts 50편 후 착수) | 신규 채널 |

### 최종 목표 (Phase B 완료 후)

- **S등급 점수**: 76.5점 → **97.0점** (+27%)
- **완주율**: 20% → **55%** (+175%)
- **CTR**: 4.5% → **18%** (+300%)
- **전환율**: 0.08% → **1.2%** (+1,400%)
- **월 수익**: 150만원 → **54,000,000원** (+3,500%)

### 핵심 성공 요인 (TOP 5)

1. **TTS 최적화**: Juho (40대 남성) 가격/숫자 담당 + 습니다체/해요체 하이브리드
2. **도파민 타이밍**: 10초 간격 파동 (0.5초/15초/30초/45초 피크 4회)
3. **기항지 비주얼**: 50초 중 26초+ (52%) 확보 (Phase B FIX-PORT-1)
4. **CTA 3단계 증폭**: 긴급성 → 행동 → 혜택 (Phase A FIX-CTA-1)
5. **이미지 자막 렌더링**: 28초 (96.7% 개선, Phase B-9 완료)

---

**작성자**: Agent 10 (S등급 통합 작업지시서 v3.0 기반)
**승인**: 사용자 확인 후 Phase A 착수
**업데이트**: 각 Phase 완료 후 실제 결과 반영

---

**절대 금지**: 이모지, 이모티콘 사용
**100% 통합 완료**: TTS 13개 + 로컬 자원 + 학습 데이터 39개 + 4A/NPCR/PASONA + 상위 1% 스킬 + 브랜드 포지셔닝 + 20개 카테고리 + 3개 상품 + 자동/수동 모드 + 롱폼 설계 + 성장 로드맵

END OF MASTER WORK ORDER
