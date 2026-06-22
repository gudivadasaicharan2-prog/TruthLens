# TruthLens Testing Guide
## Manual Testing Instructions

**Date:** June 2, 2026
**Status:** Ready for Testing

---

## Pre-Test Checklist

### Server Status
- ✅ Backend: Running at http://localhost:8000
- ✅ Frontend: Running at http://localhost:3002
- ⚠️ Some HuggingFace models failing to load (authentication issues)
- ✅ All API routes registered

### Before Testing
1. Open browser to http://localhost:3002
2. Open browser DevTools (F12) to Console tab
3. Open backend terminal to view debug logs
4. Ensure you have test files ready (images, videos, audio)

---

## Test Cases

### FACT CHECKER TESTS

#### Test 1: Scientific Fact
**Input:** "The Earth revolves around the Sun."

**Expected Results:**
- Verdict: Likely True or Probably Authentic
- Confidence: > 70%
- AI Detection Score: 50-70 (neutral to authentic)
- Evidence Score: > 70 (supporting from Wikipedia)
- Truth Score: > 70
- Sources: Wikipedia, NASA, ESA
- Reasoning: Should mention Wikipedia verification

**Steps:**
1. Navigate to Fact Checker page
2. Enter: "The Earth revolves around the Sun."
3. Click "🔍 Check This Claim"
4. Wait for analysis
5. Check results

**Backend Logs to Verify:**
```
[DEBUG] Fact check request received: The Earth revolves around the Sun.
[DEBUG] Calling run_fact_check service...
[DEBUG] Fact check result keys: dict_keys([...])
[DEBUG] Fact check verdict: ...
[DEBUG] Fact check confidence: ...
[DEBUG] Fact check truth_score: ...
```

---

#### Test 2: Recent Event
**Input:** "India landed Chandrayaan-3 near the Moon's south pole."

**Expected Results:**
- Verdict: Likely True or Probably Authentic
- Confidence: > 70%
- AI Detection Score: 50-70
- Evidence Score: > 70
- Truth Score: > 70
- Sources: Wikipedia, ISRO, NASA
- Reasoning: Should mention Wikipedia and Government verification

**Steps:**
1. Clear previous result
2. Enter: "India landed Chandrayaan-3 near the Moon's south pole."
3. Click "🔍 Check This Claim"
4. Wait for analysis
5. Check results

---

#### Test 3: General Statement
**Input:** "IPL is one of the most popular T20 leagues in the world."

**Expected Results:**
- Verdict: Probably Authentic or Uncertain
- Confidence: 50-70%
- AI Detection Score: 50-70
- Evidence Score: 50-70
- Truth Score: 50-70
- Sources: Wikipedia, News sources
- Reasoning: Should mention Wikipedia verification

**Steps:**
1. Clear previous result
2. Enter: "IPL is one of the most popular T20 leagues in the world."
3. Click "🔍 Check This Claim"
4. Wait for analysis
5. Check results

---

### IMAGE VERIFICATION TESTS

#### Test 1: Normal Photo
**Input:** Upload a real photo (e.g., portrait of a person)

**Expected Results:**
- Verdict: Likely Authentic or Probably Authentic
- Confidence: > 60%
- AI Detection Score: > 60
- Evidence Score: > 60
- Truth Score: > 60
- Image Type: face_photo
- Evidence: Forensic analysis, metadata

**Steps:**
1. Navigate to Detect page
2. Click "Image" tab
3. Upload a real photo
4. Click "Analyze Image"
5. Wait for analysis
6. Check results

**Backend Logs to Verify:**
```
[DEBUG] Image analysis request received: filename.jpg
[DEBUG] Image file size: XXXX bytes
[DEBUG] Calling analyze_image service...
[DEBUG] Image analysis result keys: dict_keys([...])
[DEBUG] Image analysis verdict: ...
[DEBUG] Image analysis confidence: ...
[DEBUG] Image analysis truth_score: ...
```

---

#### Test 2: Edited Photo
**Input:** Upload an edited photo (e.g., with filters or modifications)

**Expected Results:**
- Verdict: Possibly Manipulated or Uncertain
- Confidence: 40-60%
- AI Detection Score: 40-60
- Evidence Score: 40-60
- Truth Score: 40-60
- Evidence: Forensic anomalies detected

**Steps:**
1. Clear previous result
2. Upload an edited photo
3. Click "Analyze Image"
4. Wait for analysis
5. Check results

---

#### Test 3: AI-Generated Image (if available)
**Input:** Upload an AI-generated image

**Expected Results:**
- Verdict: Likely Manipulated or Possibly Manipulated
- Confidence: 30-50%
- AI Detection Score: 30-50
- Evidence Score: 30-50
- Truth Score: 30-50
- Evidence: AI generation patterns detected

**Steps:**
1. Clear previous result
2. Upload AI-generated image
3. Click "Analyze Image"
4. Wait for analysis
5. Check results

---

### VIDEO VERIFICATION TESTS

#### Test 1: Normal Video
**Input:** Upload a real video (e.g., recording of a person speaking)

**Expected Results:**
- Verdict: Likely Authentic or Probably Authentic
- Confidence: > 60%
- AI Detection Score: > 60
- Evidence Score: > 60
- Truth Score: > 60
- Evidence: Frame consistency, forensic analysis

**Steps:**
1. Navigate to Detect page
2. Click "Video" tab
3. Upload a real video
4. Click "Analyze Video"
5. Wait for analysis (may take longer)
6. Check results

**Backend Logs to Verify:**
```
[DEBUG] Video analysis request received: filename.mp4
[DEBUG] Video file size: XXXX bytes
[DEBUG] Calling analyze_video service...
[DEBUG] Video analysis result keys: dict_keys([...])
[DEBUG] Video analysis verdict: ...
[DEBUG] Video analysis confidence: ...
[DEBUG] Video analysis truth_score: ...
```

---

#### Test 2: Manipulated Video
**Input:** Upload a manipulated video (if available)

**Expected Results:**
- Verdict: Possibly Manipulated or Uncertain
- Confidence: 40-60%
- AI Detection Score: 40-60
- Evidence Score: 40-60
- Truth Score: 40-60
- Evidence: Frame inconsistencies detected

**Steps:**
1. Clear previous result
2. Upload manipulated video
3. Click "Analyze Video"
4. Wait for analysis
5. Check results

---

### AUDIO VERIFICATION TESTS

#### Test 1: Real Speech
**Input:** Upload real speech recording

**Expected Results:**
- Verdict: Likely Authentic or Probably Authentic
- Confidence: > 60%
- AI Detection Score: > 60
- Evidence Score: > 60
- Truth Score: > 60
- Evidence: Spectral analysis, voice patterns

**Steps:**
1. Navigate to Detect page
2. Click "Audio" tab
3. Upload real speech
4. Click "Analyze Audio"
5. Wait for analysis
6. Check results

**Backend Logs to Verify:**
```
[DEBUG] Audio analysis request received: filename.mp3
[DEBUG] Audio file size: XXXX bytes
[DEBUG] Calling analyze_audio service...
[DEBUG] Audio analysis result keys: dict_keys([...])
[DEBUG] Audio analysis verdict: ...
[DEBUG] Audio analysis confidence: ...
[DEBUG] Audio analysis truth_score: ...
```

---

#### Test 2: Synthetic Speech (if available)
**Input:** Upload AI-generated speech

**Expected Results:**
- Verdict: Possibly Manipulated
- Confidence: 30-50%
- AI Detection Score: 30-50
- Evidence Score: 30-50
- Truth Score: 30-50
- Evidence: Synthetic voice indicators

**Steps:**
1. Clear previous result
2. Upload synthetic speech
3. Click "Analyze Audio"
4. Wait for analysis
5. Check results

---

### NEWS VERIFICATION TESTS

#### Test 1: Real News Article
**Input:** 
- Title: "NASA announces new discovery on Mars"
- Content: Full article text from trusted source
- URL: https://nasa.gov/...

**Expected Results:**
- Verdict: Probably Authentic or Likely Authentic
- Confidence: > 60%
- AI Detection Score: 50-70
- Evidence Score: > 60
- Truth Score: > 60
- Sources: Wikipedia, Government, News API
- Evidence: Claim extraction, entity extraction, source verification

**Steps:**
1. Navigate to Detect page
2. Click "News" tab
3. Enter title, content, URL
4. Click "Analyze News"
5. Wait for analysis
6. Check results

**Backend Logs to Verify:**
```
[DEBUG] News analysis request received: title=NASA...
[DEBUG] Calling analyze_news service...
[DEBUG] News analysis result keys: dict_keys([...])
[DEBUG] News analysis verdict: ...
[DEBUG] News analysis confidence: ...
[DEBUG] News analysis truth_score: ...
```

---

## Success Criteria

### All Tests Should:
- ✅ Not display "Unknown" verdict
- ✅ Not display "Backend not running" error
- ✅ Display a meaningful verdict
- ✅ Display confidence value
- ✅ Display AI Detection Score
- ✅ Display Evidence Score
- ✅ Display Truth Score
- ✅ Display reasoning
- ✅ Display sources consulted
- ✅ Backend logs should show debug information

### Known Limitations:
- ⚠️ Some HuggingFace models fail to load (authentication issues)
- ⚠️ System falls back to heuristics when models fail
- ⚠️ No reverse image search (requires external API)
- ⚠️ No speech-to-text (requires external API)

---

## Troubleshooting

### If Verdict is "Unknown":
1. Check browser console for errors
2. Check backend logs for errors
3. Verify frontend is reading correct fields
4. Verify backend is returning correct fields

### If "Backend not running":
1. Check if backend server is running
2. Check if port 8000 is accessible
3. Check browser console for network errors
4. Check backend logs for errors

### If Scores are Fixed Values:
1. Check if evidence is being collected
2. Check if AI_DETECTION evidence exists
3. Check if non-AI evidence exists
4. Verify scoring calculations in evidence_collector.py

---

## Test Results Template

Copy and fill this out for each test:

```
Test: [Test Name]
Input: [What was tested]
Expected Verdict: [Expected]
Actual Verdict: [Actual]
Expected Confidence: [Expected]
Actual Confidence: [Actual]
Expected Truth Score: [Expected]
Actual Truth Score: [Actual]
Sources Consulted: [List]
Evidence Count: [Number]
Status: [PASS/FAIL]
Notes: [Any observations]
```

---

**Testing Status:** Ready to begin
**Backend:** Running at http://localhost:8000
**Frontend:** Running at http://localhost:3002
