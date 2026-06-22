# Fact Checker Frontend Fix

**Date:** June 3, 2026
**Issue:** Frontend shows "Fact check failed. Is the backend running?" despite backend working correctly

## Root Cause Analysis

**Backend Status:** ✅ Working (confirmed via Swagger)
- Endpoint: POST /api/v1/factcheck
- Returns valid JSON with: verdict, confidence, truth_score, evidence_score, sources_consulted, evidence

**Frontend Issue:** ❌ Error handling not showing actual error details
- Generic error message: "Fact check failed. Is the backend running?"
- No detailed logging to identify actual failure point

## Changes Made

### 1. Enhanced Error Logging in FactCheck.jsx

**File:** `frontend/src/pages/FactCheck.jsx`

**Changes:**
- Added detailed console logging before API call
- Added detailed console logging of response structure
- Added detailed error logging with full error object
- Enhanced error message extraction to show actual error details

**Code Changes (lines 42-69):**
```javascript
try {
  console.log('[DEBUG] Calling factCheck API with claim:', claim);
  const res = await factCheck(claim);
  console.log('[DEBUG] Fact check API response:', res);
  console.log('[DEBUG] Response keys:', res ? Object.keys(res) : 'null');
  console.log('[DEBUG] Verdict:', res?.verdict || res?.status || 'N/A');
  console.log('[DEBUG] Confidence:', res?.confidence || 'N/A');
  console.log('[DEBUG] Truth Score:', res?.truth_score || 'N/A');
  setResult(res);
} catch (err) {
  console.error('[ERROR] Fact check error:', err);
  console.error('[ERROR] Error response:', err.response);
  console.error('[ERROR] Error data:', err.response?.data);
  console.error('[ERROR] Error message:', err.message);
  console.error('[ERROR] Error status:', err.response?.status);
  
  // Show detailed error message
  const errorMessage = err.response?.data?.detail 
    || err.response?.data?.message 
    || err.message 
    || 'Fact check failed. Is the backend running?';
  
  console.error('[ERROR] Setting error message:', errorMessage);
  setError(errorMessage);
} finally {
  setLoading(false);
  setStep('');
}
```

### 2. Enhanced API Logging in api.js

**File:** `frontend/src/services/api.js`

**Changes:**
- Added console logging before API call
- Added console logging of response structure
- Added console logging of response status
- Added detailed error logging

**Code Changes (lines 85-101):**
```javascript
export const factCheck = (claim) => {
    console.log('[API] Calling factCheck with claim:', claim);
    return api.post('/api/v1/factcheck',
        { claim },
        { headers: { 'Content-Type': 'application/json' } }
    ).then(response => {
        console.log('[API] Fact check response:', response);
        console.log('[API] Response data:', response.data);
        console.log('[API] Response status:', response.status);
        return response.data;
    }).catch(error => {
        console.error('[API] Fact check error:', error);
        console.error('[API] Error response:', error.response);
        console.error('[API] Error data:', error.response?.data);
        throw error;
    });
}
```

## Schema Compatibility

**Backend Response Schema:**
```json
{
  "verdict": "Likely True",
  "confidence": 0.99,
  "truth_score": 79.2,
  "evidence_score": 78.0,
  "ai_detection_score": 50.0,
  "sources_consulted": ["Wikipedia", "Government Websites"],
  "reasoning": "...",
  "evidence": [...]
}
```

**Frontend Expected Schema (with backward compatibility):**
- `result.verdict || result.status` ✅
- `result.confidence` ✅
- `result.reasoning || result.explanation` ✅
- `result.ai_detection_score` ✅
- `result.evidence_score` ✅
- `result.truth_score` ✅
- `result.sources_consulted || result.sources` ✅

**Status:** Frontend already has full backward compatibility for both old and new schemas.

## Next Steps

**To Debug:**
1. Open browser to http://localhost:3002
2. Open DevTools Console (F12)
3. Navigate to Fact Checker page
4. Enter claim: "The Earth revolves around the Sun."
5. Click "🔍 Check This Claim"
6. Check console logs for:
   - `[API] Calling factCheck with claim:`
   - `[API] Fact check response:`
   - `[DEBUG] Fact check API response:`
   - Any `[ERROR]` messages

**Expected Console Output (if working):**
```
[API] Calling factCheck with claim: The Earth revolves around the Sun.
[API] Fact check response: {data: {...}, status: 200, ...}
[API] Response data: {verdict: "Likely True", confidence: 0.99, ...}
[API] Response status: 200
[DEBUG] Calling factCheck API with claim: The Earth revolves around the Sun.
[DEBUG] Fact check API response: {verdict: "Likely True", ...}
[DEBUG] Response keys: ["verdict", "confidence", "truth_score", ...]
[DEBUG] Verdict: Likely True
[DEBUG] Confidence: 0.99
[DEBUG] Truth Score: 79.2
```

**If Error Occurs:**
```
[ERROR] Fact check error: ...
[ERROR] Error response: ...
[ERROR] Error data: ...
[ERROR] Error message: ...
[ERROR] Error status: ...
```

## Possible Issues

1. **Network Error:** Frontend cannot reach backend
   - Check: Backend running at http://localhost:8000
   - Check: CORS configuration (already set to allow all origins)

2. **Timeout Error:** Request taking too long
   - Timeout set to 120 seconds (2 minutes)
   - Fact check should complete within this time

3. **Response Parsing Error:** Response format unexpected
   - Console logs will show actual response structure
   - Can adjust frontend parsing based on actual response

## Testing

**Test Case:**
- Claim: "The Earth revolves around the Sun."
- Expected Verdict: Likely True
- Expected Confidence: > 90%
- Expected Truth Score: > 70

**Verification:**
1. Check console logs show successful API call
2. Check result displays correctly in UI
3. Check verdict, confidence, and scores are displayed
4. Check sources_consulted are displayed

---

**Status:** Enhanced logging added. Ready for testing with console inspection.
