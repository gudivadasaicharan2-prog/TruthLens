# TruthLens Debug Audit Report
## Root Cause Analysis

**Date:** June 2, 2026
**Status:** CRITICAL SCHEMA MISMATCH IDENTIFIED

---

## ROOT CAUSE

The backend was refactored to use the new evidence-based verification system with separated scores (AI Detection Score, Evidence Score, Truth Score), but the frontend still expects the old schema.

**Result:** Frontend cannot read the new response format, causing:
- "Unknown" verdicts for images/videos
- "Fact check failed" errors
- Missing confidence scores

---

## SCHEMA MISMATCH ANALYSIS

### Backend Response Schema (NEW - evidence_collector.py)
```json
{
  "content_type": "article",
  "analysis_timestamp": "2026-06-02T00:00:00",
  "verdict": "Probably Authentic",
  "confidence": 0.72,
  "ai_detection_score": 65.0,
  "evidence_score": 78.0,
  "truth_score": 72.8,
  "reasoning": "=== VERIFICATION ANALYSIS REPORT ===...",
  "evidence_count": 7,
  "supporting_evidence_count": 4,
  "contradicting_evidence_count": 1,
  "neutral_evidence_count": 2,
  "sources_consulted": ["Wikipedia", "Government Websites", "News API"],
  "evidence": [...],
  "supporting_evidence": [...],
  "contradicting_evidence": [...],
  "neutral_evidence": [...]
}
```

### Frontend Expected Schema (OLD - Detect.jsx)
```javascript
// Line 260
const verdict = result.result;  // ❌ WRONG - should be result.verdict

// Line 261
const confidence = result.confidence ?? result.authenticity_score;  // ✅ OK

// Line 276-290
result.reasons  // ❌ WRONG - should be result.reasoning

// Line 310-335
result.sources  // ❌ WRONG - should be result.sources_consulted
```

### Frontend Expected Schema (OLD - FactCheck.jsx)
```javascript
// Line 55
const config = result ? statusConfig[result.status] : null;  // ❌ WRONG - should be result.verdict

// Line 119-144
result.status  // ❌ WRONG - should be result.verdict

// Line 153-155
result.confidence  // ✅ OK

// Line 164
result.explanation  // ❌ WRONG - should be result.reasoning

// Line 170-177
result.keywords_used  // ❌ MISSING - not in new schema

// Line 181-238
result.sources  // ❌ WRONG - should be result.sources_consulted
```

---

## DETAILED ISSUES

### 1. IMAGE DETECTION - "Unknown" Verdict

**Problem:** Frontend reads `result.result` but backend returns `result.verdict`

**Location:** 
- Frontend: `frontend/src/pages/Detect.jsx` line 260
- Backend: `backend/app/services/evidence_collector.py` line 356

**Fix:** Change `result.result` to `result.verdict`

---

### 2. VIDEO DETECTION - "Unknown" Verdict

**Problem:** Frontend reads `result.result` but backend returns `result.verdict`

**Location:** 
- Frontend: `frontend/src/pages/Detect.jsx` line 260
- Backend: `backend/app/services/evidence_collector.py` line 356

**Fix:** Change `result.result` to `result.verdict`

---

### 3. FACT CHECKER - "Backend not running"

**Problem:** Frontend reads `result.status` but backend returns `result.verdict`

**Location:** 
- Frontend: `frontend/src/pages/FactCheck.jsx` line 55, 119-144
- Backend: `backend/app/services/evidence_collector.py` line 356

**Fix:** Change `result.status` to `result.verdict`

---

### 4. MISSING FIELDS IN NEW SCHEMA

**Problem:** Frontend expects fields that don't exist in new schema

**Missing fields:**
- `result.result` → should be `result.verdict`
- `result.status` → should be `result.verdict`
- `result.reasons` → should be `result.reasoning`
- `result.sources` → should be `result.sources_consulted`
- `result.keywords_used` → not in new schema
- `result.explanation` → should be `result.reasoning`

**New fields not used by frontend:**
- `ai_detection_score`
- `evidence_score`
- `truth_score`
- `evidence_count`
- `supporting_evidence_count`
- `contradicting_evidence_count`
- `neutral_evidence_count`
- `evidence`
- `supporting_evidence`
- `contradicting_evidence`
- `neutral_evidence`

---

## REQUIRED FIXES

### Frontend Fixes (Detect.jsx)

1. **Line 260:** Change `result.result` to `result.verdict`
2. **Line 276-290:** Change `result.reasons` to `result.reasoning`
3. **Line 310-335:** Change `result.sources` to `result.sources_consulted`
4. **Add:** Display new scores (ai_detection_score, evidence_score, truth_score)

### Frontend Fixes (FactCheck.jsx)

1. **Line 55:** Change `result.status` to `result.verdict`
2. **Line 119-144:** Change `result.status` to `result.verdict`
3. **Line 164:** Change `result.explanation` to `result.reasoning`
4. **Line 170-177:** Remove or adapt `result.keywords_used`
5. **Line 181-238:** Change `result.sources` to `result.sources_consulted`
6. **Add:** Display new scores (ai_detection_score, evidence_score, truth_score)

---

## BACKWARD COMPATIBILITY OPTION

Alternative: Add backward compatibility to backend by mapping new fields to old field names in the API endpoints.

**Pros:** No frontend changes needed
**Cons:** Maintains legacy schema, defeats purpose of new system

**Recommendation:** Update frontend to use new schema (cleaner, future-proof)

---

## NEXT STEPS

1. Fix frontend schema mismatches
2. Add debugging logs to all endpoints
3. Test with provided examples
4. Verify scoring system
5. Generate final report
