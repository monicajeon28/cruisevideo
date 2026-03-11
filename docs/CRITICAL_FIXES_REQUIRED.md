# CRITICAL FIXES REQUIRED - IMMEDIATE ACTION

**Date**: 2026-03-08
**Status**: 4 CRITICAL ISSUES BLOCKING DEPLOYMENT
**Estimated Fix Time**: 1.5 hours total

---

## PRIORITY 0: FIX BEFORE DEPLOYMENT

### 1. CRITICAL-1: Pop/Re-hook Timing Collision (30 min)

**Problem**:
```python
pop_timings = (15.0, 32.5, 46.5)     # Pop#2 at 32.5s
rehook_timings = (13.0, 32.0)        # Re-hook#2 at 32.0s
# GAP = 0.5s ❌ VIOLATES 1.5s MINIMUM
```

**Impact**: S-grade validator REJECTS script (pop_timing_accurate = False)

**Fix**:
```python
# File: video_pipeline/config.py Line 168
# CHANGE FROM:
pop_timings: tuple = (15.0, 32.5, 46.5)

# CHANGE TO:
pop_timings: tuple = (15.0, 33.5, 46.5)  # Shift Pop#2 by +1.0s

# File: engines/script_validation_orchestrator.py Line 1362
# CHANGE FROM:
(32.0, 33.0, 32.5),  # Pop#2: 32.5s ±0.5s

# CHANGE TO:
(33.0, 34.0, 33.5),  # Pop#2: 33.5s ±0.5s
```

**Validation**:
```bash
python generate.py --mode auto --dry-run --count 1
# Verify: S-grade score >= 90, pop_timing_accurate = True
```

---

### 2. CRITICAL-2: CTA Duration Validation Missing (15 min)

**Problem**: No runtime check for CTA stage sum consistency

**Fix**:
```python
# File: video_pipeline/config.py
# ADD after Line 182 (after cta_trust_duration)

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
            f"sum of stages={expected_cta}s. "
            f"Update cta_duration to match stage sum."
        )
```

**Validation**:
```python
# Test with invalid config
config = PipelineConfig(
    cta_duration=10.0,
    cta_urgency_duration=2.0,
    cta_action_duration=3.0,
    cta_trust_duration=4.0  # Sum = 9.0 != 10.0
)
# Should raise ValueError
```

---

### 3. CRITICAL-3: Verify Gemini Prompt Has 3-Stage CTA (20 min)

**Problem**: Uncertain if Gemini prompt includes cta_urgency/action/trust templates

**Action Required**:
```bash
# Step 1: Search for CTA keywords
grep -r "cta_urgency" engines/comprehensive_script_generator.py
grep -r "cta_action" engines/comprehensive_script_generator.py
grep -r "cta_trust" engines/comprehensive_script_generator.py

# Step 2: If NOT FOUND, read full file
# Read: engines/comprehensive_script_generator.py (all lines)

# Step 3: If missing, add to Gemini prompt template:
# Example structure in prompt:
{
  "segments": [
    {"segment_type": "hook", "text": "..."},
    {"segment_type": "body1", "text": "..."},
    {"segment_type": "cta_urgency", "text": "선착순 44명, 지금 3명 남았어요"},
    {"segment_type": "cta_action", "text": "프로필 링크에서 지금 바로 확인하세요"},
    {"segment_type": "cta_trust", "text": "11년간 32,000명이 선택한 크루즈닷"}
  ]
}
```

**If Missing**: Escalate to Task #8 (FIX-CTA-2: CTA 3단계 템플릿 통합)

---

### 4. ERROR-1: estimate_sgrade() None-Handling (20 min)

**Problem**: No exception handling if S-grade estimation fails

**Fix**:
```python
# File: cli/auto_mode.py (quality gate loop)
# FIND: quality_gate_loop() or similar method
# ADD exception handling:

def quality_gate_loop(scripts, max_attempts=100):
    """Quality gate with robust error handling"""
    for i, script in enumerate(scripts):
        try:
            score = estimate_sgrade(script)

            # Handle None return
            if score is None:
                logger.warning(
                    f"Script {i+1}/{len(scripts)}: "
                    f"S-grade estimation returned None (skipping)"
                )
                continue

            # Success case
            if score >= 90:
                logger.info(
                    f"Script {i+1}/{len(scripts)}: "
                    f"S-grade {score:.1f}/100 (PASS)"
                )
                return script

        except (KeyError, AttributeError, ValueError) as e:
            logger.error(
                f"Script {i+1}/{len(scripts)}: "
                f"Validation error: {e} (skipping)"
            )
            continue

        except Exception as e:
            logger.error(
                f"Script {i+1}/{len(scripts)}: "
                f"Unexpected error: {e} (skipping)"
            )
            continue

    # All scripts failed
    logger.error(
        f"Quality gate FAILED: 0/{len(scripts)} scripts achieved S-grade"
    )
    return None
```

---

## VALIDATION CHECKLIST

After applying all 4 fixes:

- [ ] **Unit Test**: Run `pytest tests/` (if tests exist)
- [ ] **Dry Run**: `python generate.py --mode auto --dry-run --count 1`
- [ ] **S-Grade Check**: Verify output script has:
  - [ ] Score >= 90
  - [ ] Pop count = 3
  - [ ] Pop timing accurate = True
  - [ ] CTA segments = 3 (urgency, action, trust)
  - [ ] Trust elements >= 2
  - [ ] Banned words = 0
- [ ] **Full Render**: `python generate.py --mode auto --count 1` (no dry-run)
- [ ] **Video Quality**: Check 55s video renders successfully

---

## POST-DEPLOYMENT MONITORING

After deploying fixes, monitor for:

1. **S-Grade Achievement Rate**: Should be 90%+ (was 81.8%, target 98.8%)
2. **Script Generation Failures**: Log any estimate_sgrade() None returns
3. **Pop Timing Validation**: Verify no "Pop 타이밍 부정확" errors
4. **CTA Structure**: Ensure all scripts have 3 CTA segments

---

## ROLLBACK PLAN

If issues occur after deployment:

```bash
# Revert to Phase 33 baseline
git revert <commit-hash>

# Or: Manual rollback
# 1. Restore config.py pop_timings to (15.0, 32.5, 46.5)
# 2. Remove __post_init__ validation
# 3. Comment out exception handling in auto_mode.py
```

---

## NEXT STEPS (After Critical Fixes)

**Short-term (This Week)**:
- Add Gemini API retry logic (ERROR-3)
- Refactor Pop timing constants (SMELL-1)
- Write unit tests for validators (TEST-1)

**Medium-term (Next Sprint)**:
- Refactor validate_script() God Method (SMELL-3)
- Parallelize Quality Gate (BOTTLENECK-1)
- Create API abstraction layer (ARCH-3)

---

**Agent 3 (Cross-Checker) Sign-off**: ✅
**Recommended Action**: Fix 4 critical issues (1.5h), then deploy.
