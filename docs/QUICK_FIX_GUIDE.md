# QUICK FIX GUIDE - 4 Critical Issues (1.5 hours)

**Last Updated**: 2026-03-08
**Status**: 4 BLOCKING ISSUES
**Total Time**: 90 minutes

---

## FIX #1: Pop/Re-hook Timing Collision (30 min) ⚠️ CRITICAL

### Problem
Pop#2 (32.5s) and Re-hook#2 (32.0s) are 0.5s apart (violates 1.5s minimum gap).
S-grade validator will REJECT scripts: `pop_timing_accurate = False`

### Solution
Shift Pop#2 from 32.5s → 33.5s (1.0s later)

### Files to Edit

**File 1**: `D:\mabiz\video_pipeline\config.py`
```python
# LINE 168 - CHANGE FROM:
pop_timings: tuple = (15.0, 32.5, 46.5)

# CHANGE TO:
pop_timings: tuple = (15.0, 33.5, 46.5)  # FIX: Shift Pop#2 to avoid Re-hook#2 collision
```

**File 2**: `D:\mabiz\engines\script_validation_orchestrator.py`
```python
# LINE 1360-1365 - CHANGE FROM:
STANDARD_POP_TIMINGS = [
    (14.5, 15.5, 15.0),   # Pop#1: 15s ±0.5s
    (32.0, 33.0, 32.5),   # Pop#2: 32.5s ±0.5s  ← OLD
    (46.0, 47.0, 46.5),   # Pop#3: 46.5s ±0.5s
]

# CHANGE TO:
STANDARD_POP_TIMINGS = [
    (14.5, 15.5, 15.0),   # Pop#1: 15s ±0.5s
    (33.0, 34.0, 33.5),   # Pop#2: 33.5s ±0.5s  ← NEW (shifted +1.0s)
    (46.0, 47.0, 46.5),   # Pop#3: 46.5s ±0.5s
]
```

### Test
```bash
python generate.py --mode auto --dry-run --count 1
# Verify output: pop_timing_accurate = True, S-grade >= 90
```

---

## FIX #2: CTA Duration Validation (15 min) ⚠️ CRITICAL

### Problem
No runtime check that `cta_duration` equals sum of stage durations.
If config changes: 3.0 + 3.5 + 3.5 ≠ 10.0 → timing breaks silently.

### Solution
Add validation in `__post_init__` method

### File to Edit

**File**: `D:\mabiz\video_pipeline\config.py`
```python
# ADD AFTER LINE 182 (after cta_trust_duration definition)

def __post_init__(self):
    """Validate configuration consistency"""
    # CTA duration must equal sum of stages
    expected_cta = (
        self.cta_urgency_duration +
        self.cta_action_duration +
        self.cta_trust_duration
    )
    if abs(self.cta_duration - expected_cta) > 0.01:
        raise ValueError(
            f"CTA duration mismatch: "
            f"cta_duration={self.cta_duration}s, "
            f"sum of stages={expected_cta}s (urgency={self.cta_urgency_duration}s "
            f"+ action={self.cta_action_duration}s + trust={self.cta_trust_duration}s). "
            f"Update cta_duration to {expected_cta}s"
        )
```

### Test
```python
# Test with invalid config (should raise ValueError)
from video_pipeline.config import PipelineConfig

try:
    config = PipelineConfig(
        cta_duration=10.0,
        cta_urgency_duration=2.0,
        cta_action_duration=3.0,
        cta_trust_duration=4.0  # Sum = 9.0 != 10.0
    )
except ValueError as e:
    print(f"✅ Validation works: {e}")
```

---

## FIX #3: Gemini Prompt 3-Stage CTA Verification (20 min) ⚠️ UNCERTAIN

### Problem
Task #20 says "CRITICAL-3: Gemini 프롬프트 3-CTA 반영" is completed, but we need to verify the Gemini prompt template actually includes `cta_urgency`, `cta_action`, `cta_trust` segment types.

### Solution
Search and verify (or add if missing)

### Steps

**Step 1**: Search for CTA keywords
```bash
cd D:\mabiz
grep -n "cta_urgency" engines/comprehensive_script_generator.py
grep -n "cta_action" engines/comprehensive_script_generator.py
grep -n "cta_trust" engines/comprehensive_script_generator.py
```

**Step 2**: If FOUND → Skip to Test
**Step 3**: If NOT FOUND → Read full file
```bash
# Read the Gemini prompt builder
cat engines/comprehensive_script_generator.py | grep -A 50 "Gemini"
```

**Step 4**: If Missing → Add to Gemini Prompt Template
```python
# Example structure to add in Gemini prompt:
"""
REQUIRED SEGMENTS (segment_type):
1. "hook" - 5초 문제-해결-가치 구조
2. "body1" - "body6" - 정보 전달
3. "cta_urgency" - 긴급성 (선착순 44명, 지금 3명 남았어요)
4. "cta_action" - 행동 유도 (프로필 링크에서 지금 바로 확인하세요)
5. "cta_trust" - 신뢰 강화 (11년간 32,000명이 선택한 크루즈닷)

Example Output:
{
  "segments": [
    {"segment_type": "hook", "text": "..."},
    {"segment_type": "body1", "text": "..."},
    {"segment_type": "cta_urgency", "text": "선착순 44명, 지금 3명 남았어요"},
    {"segment_type": "cta_action", "text": "프로필 링크에서 지금 바로 확인하세요"},
    {"segment_type": "cta_trust", "text": "11년간 32,000명이 선택한 크루즈닷"}
  ]
}
"""
```

### Test
```bash
python generate.py --mode auto --dry-run --count 1
# Verify output script has 3 CTA segments: cta_urgency, cta_action, cta_trust
```

### If Missing
If not found in comprehensive_script_generator.py:
1. Create Task: "FIX-CTA-2B: Add 3-stage CTA to Gemini prompt template"
2. Escalate to Task #8 (FIX-CTA-2: CTA 3단계 템플릿 통합)
3. Reference: `engines/cta_validator.py` Lines 301-316 for expected structure

---

## FIX #4: Exception Handling in Quality Gate (20 min) ⚠️ PRODUCTION RISK

### Problem
`estimate_sgrade()` may return `None` or raise exceptions.
No error handling → production crashes.

### Solution
Add try-except in auto_mode quality gate loop

### File to Edit

**File**: `D:\mabiz\cli\auto_mode.py`

**Step 1**: Find the quality gate loop
```bash
grep -n "estimate_sgrade\|quality_gate" D:\mabiz\cli\auto_mode.py
```

**Step 2**: Locate the loop that calls `estimate_sgrade(script)`

**Step 3**: Wrap in try-except
```python
# FIND EXISTING CODE (approximate line numbers may vary):
def quality_gate_loop(scripts, max_attempts=100):
    for i, script in enumerate(scripts):
        score = estimate_sgrade(script)  # ← NO ERROR HANDLING
        if score >= 90:
            return script
    return None

# REPLACE WITH:
def quality_gate_loop(scripts, max_attempts=100):
    """Quality gate with robust error handling"""
    for i, script in enumerate(scripts):
        try:
            # Estimate S-grade score
            score = estimate_sgrade(script)

            # Handle None return (estimation failed)
            if score is None:
                logger.warning(
                    f"Script {i+1}/{len(scripts)}: "
                    f"S-grade estimation returned None (skipping)"
                )
                continue

            # Log result
            logger.info(
                f"Script {i+1}/{len(scripts)}: "
                f"S-grade {score:.1f}/100 {'PASS' if score >= 90 else 'FAIL'}"
            )

            # Success case
            if score >= 90:
                logger.info(f"✅ S-grade script found at position {i+1}")
                return script

        except KeyError as e:
            logger.error(
                f"Script {i+1}/{len(scripts)}: "
                f"Missing required field: {e} (skipping)"
            )
            continue

        except AttributeError as e:
            logger.error(
                f"Script {i+1}/{len(scripts)}: "
                f"Invalid script structure: {e} (skipping)"
            )
            continue

        except ValueError as e:
            logger.error(
                f"Script {i+1}/{len(scripts)}: "
                f"Validation error: {e} (skipping)"
            )
            continue

        except Exception as e:
            logger.error(
                f"Script {i+1}/{len(scripts)}: "
                f"Unexpected error: {type(e).__name__}: {e} (skipping)"
            )
            continue

    # All scripts failed
    logger.error(
        f"❌ Quality gate FAILED: 0/{len(scripts)} scripts achieved S-grade (≥90)"
    )
    return None
```

### Test
```python
# Test with malformed script (missing "hook" segment)
malformed_script = {
    "segments": [
        {"segment_type": "body1", "text": "Test"}
    ]
}

result = quality_gate_loop([malformed_script])
# Should log error and return None (not crash)
```

---

## FINAL VALIDATION CHECKLIST

After applying all 4 fixes:

### 1. Config Validation Test
```bash
cd D:\mabiz
python -c "from video_pipeline.config import PipelineConfig; config = PipelineConfig(); print('✅ Config validated')"
```
Expected: `✅ Config validated` (no ValueError)

### 2. Dry-Run Test
```bash
python generate.py --mode auto --dry-run --count 1
```
Expected output (check console):
- ✅ Script generated successfully
- ✅ S-grade score: 90.0+/100
- ✅ Pop count: 3
- ✅ Pop timing accurate: True
- ✅ CTA segments: 3 (urgency, action, trust)
- ✅ Trust elements: 2+
- ✅ Banned words: 0

### 3. Full Render Test
```bash
python generate.py --mode auto --count 1
```
Expected:
- ✅ Video renders successfully (55s duration)
- ✅ No crashes or exceptions
- ✅ Upload package generated

### 4. S-Grade Score Verification
```bash
# Check the generated script JSON file
cat outputs/auto_mode_*/script.json | grep -A 5 "validation_result"
```
Expected fields:
```json
{
  "validation_result": {
    "grade": "S",
    "score": 90.0,
    "pop_count": 3,
    "pop_timing_accurate": true,
    "trust_count": 2,
    "banned_count": 0
  }
}
```

---

## ROLLBACK PROCEDURE (If Needed)

If issues occur after fixes:

### Rollback Fix #1 (Pop Timing)
```python
# config.py Line 168
pop_timings: tuple = (15.0, 32.5, 46.5)  # Restore original

# script_validation_orchestrator.py Line 1362
(32.0, 33.0, 32.5),  # Restore original
```

### Rollback Fix #2 (CTA Validation)
```python
# Delete __post_init__ method from config.py
```

### Rollback Fix #3 (Gemini Prompt)
```bash
# If you added CTA templates, comment them out
# git diff engines/comprehensive_script_generator.py
```

### Rollback Fix #4 (Exception Handling)
```python
# Revert auto_mode.py to simple version
for i, script in enumerate(scripts):
    score = estimate_sgrade(script)
    if score >= 90:
        return script
```

### Full System Rollback
```bash
# If all fixes fail, revert to Phase 33 baseline
git log --oneline -10  # Find commit hash before fixes
git revert <commit-hash>
```

---

## TROUBLESHOOTING

### Issue: "ValueError: CTA duration mismatch"
**Cause**: CTA stage durations don't sum to `cta_duration`
**Fix**: Update `config.py` to match:
```python
cta_duration = 10.0  # Must equal 3.0 + 3.5 + 3.5
```

### Issue: "pop_timing_accurate = False"
**Cause**: Pop timings violate validation ranges
**Fix**: Verify Fix #1 applied correctly (Pop#2 = 33.5s, not 32.5s)

### Issue: "Script has only 1 CTA segment"
**Cause**: Gemini prompt doesn't include 3-stage CTA template
**Fix**: Complete Fix #3 (add cta_urgency/action/trust to prompt)

### Issue: "estimate_sgrade() crashes on malformed script"
**Cause**: Missing exception handling
**Fix**: Verify Fix #4 applied correctly (try-except in quality_gate_loop)

---

## TIME ESTIMATE

| Fix | Task | Time |
|-----|------|------|
| #1 | Pop timing (2 files) | 30 min |
| #2 | CTA validation (1 file) | 15 min |
| #3 | Gemini prompt verification | 20 min |
| #4 | Exception handling (1 file) | 20 min |
| **TOTAL** | | **85 min** |

Add 5 minutes buffer = **90 minutes total**

---

## NEXT STEPS AFTER FIXES

### Immediate (Today)
- [ ] Deploy to production
- [ ] Monitor S-grade achievement rate (target: 98.8%)
- [ ] Check error logs for estimate_sgrade() failures

### This Week
- [ ] Add Gemini API retry logic (3h)
- [ ] Refactor Pop timing constants to single source (2h)
- [ ] Write unit tests for validators (8h)

### Next Sprint
- [ ] Refactor God Method (validate_script 550 lines → 50 lines + helpers)
- [ ] Parallelize Quality Gate (5x speedup)
- [ ] Add API abstraction layer (future-proofing)

---

**Quick Fix Guide Complete**
**Agent 3 (Cross-Checker) Sign-off**: ✅
