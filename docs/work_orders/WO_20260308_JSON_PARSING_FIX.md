# Work Order: JSON 파싱 에러 해결

**날짜**: 2026-03-08
**우선순위**: P0 (CRITICAL)
**담당**: 6-Agent 크로스체크 시스템

---

## 📋 현재 상황

### ✅ 성공한 작업
1. **google-genai 패키지 업그레이드**: google.generativeai → google-genai 1.66.0
2. **API 키 연결**: Google AI Studio API 키 작동 확인
3. **모델명 수정**: `models/gemini-2.5-flash` 사용
4. **API 응답 수신**: Gemini가 스크립트 생성 응답 반환

### ❌ 현재 문제

**에러 메시지**:
```
[Gemini] 생성 실패: Unterminated string starting at: line 9 column 13 (char 254)
```

**원인**:
- Gemini API가 반환한 JSON에 한국어 따옴표/줄바꿈이 포함됨
- JSON 파싱 시 이스케이프 처리되지 않은 문자열

**영향**:
- S등급 스크립트 생성 실패 (Fallback 모드로 전환)
- 목표 90점+ 달성 불가 (현재 Fallback: 27-33점)

---

## 🎯 작업 목표

1. **JSON 파싱 성공률**: 100% (현재 0%)
2. **Gemini 응답 처리**: 견고한 에러 핸들링
3. **한국어 텍스트**: 따옴표/줄바꿈 안전 처리
4. **S등급 달성**: 90점+ 스크립트 생성

---

## 📂 수정 대상 파일

**핵심 파일**: `D:\mabiz\engines\comprehensive_script_generator.py`

**수정 위치**: Line 726-756
```python
try:
    # 새 google-genai API 호출
    if not self.client or not self.model_name:
        raise Exception("Gemini client not configured")

    response = self.client.models.generate_content(
        model=self.model_name,
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=0.8,
            max_output_tokens=3500,
            top_p=0.95,
            top_k=40
        )
    )

    response_text = response.text.strip()

    # JSON 추출 (마크다운 코드 블록 제거)
    if "```json" in response_text:
        response_text = response_text.split("```json")[1].split("```")[0].strip()
    elif "```" in response_text:
        response_text = response_text.split("```")[1].split("```")[0].strip()

    # JSON 파싱 ← 여기서 에러 발생!
    data = json.loads(response_text)
```

---

## 🛠️ 해결 방안

### 방안 1: 정규식 기반 JSON 정제
```python
import re

# 이스케이프되지 않은 따옴표 제거
response_text = re.sub(r'(?<!\\)"(?![:,\]}])', '\\"', response_text)

# 줄바꿈 제거
response_text = response_text.replace('\n', '\\n').replace('\r', '\\r')
```

### 방안 2: ast.literal_eval 사용
```python
import ast

# JSON 대신 Python literal로 파싱
data = ast.literal_eval(response_text)
```

### 방안 3: 재시도 + 프롬프트 개선
```python
# Gemini 프롬프트에 명시적 JSON 형식 요구
"""
주의사항:
- JSON 형식 엄수
- 따옴표는 반드시 이스케이프
- 줄바꿈 금지 (\\n 사용)
"""
```

### 방안 4: Pydantic 모델 사용
```python
from pydantic import BaseModel

class ScriptBlock(BaseModel):
    text: str
    emotion: str
    duration: float
    keywords: list[str]

# 자동 검증 + 파싱
data = ScriptBlock.parse_raw(response_text)
```

---

## 📋 6-Agent 작업 분담

### Agent 1: bug-fixer
**역할**: JSON 파싱 에러 즉시 수정
**작업**:
- Line 726-756 분석
- 에러 재현
- 최소 수정으로 해결

### Agent 2: code-writer
**역할**: 견고한 JSON 파싱 로직 구현
**작업**:
- 다중 파싱 전략 (정규식 + ast + json)
- 한국어 안전 처리
- Retry 로직

### Agent 3: red-team-code-validator
**역할**: 보안 취약점 검증
**작업**:
- JSON injection 공격 가능성
- Prompt injection 방어
- API 응답 신뢰성 검증

### Agent 4: blue-team-code-enhancer
**역할**: 코드 품질 개선
**작업**:
- 성능 최적화
- 에러 핸들링 강화
- 로깅 개선

### Agent 5: purple-team-orchestrator
**역할**: Red/Blue 통합 검토
**작업**:
- 보안 vs 성능 균형
- 리스크 우선순위
- 통합 테스트

### Agent 6: comprehensive-reviewer
**역할**: 최종 종합 리뷰 + 보고서
**작업**:
- 코드 스멜 검출
- 누수/충돌 확인
- 상위 1% 품질 검증
- 최종 보고서 작성

---

## ✅ 완료 기준

1. **JSON 파싱 성공**: test_single_production.py 정상 실행
2. **S등급 달성**: 90점+ 스크립트 생성 확인
3. **에러 0건**: 3회 재시도 모두 성공
4. **종합 보고서**: 6-Agent 크로스체크 결과

---

## 📊 예상 효과

**Before (현재)**:
- JSON 파싱 성공률: 0%
- S등급 점수: 27-33점 (Fallback)
- Gemini 활용: 불가

**After (목표)**:
- JSON 파싱 성공률: 100%
- S등급 점수: 90-98점
- Gemini 활용: 완전 작동

**수익 임팩트**:
- 월 수익: Fallback 150만원 → Gemini 950만원 (+533%)
