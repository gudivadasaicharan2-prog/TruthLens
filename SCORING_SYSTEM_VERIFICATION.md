# Scoring System Verification Report

**Date:** June 2, 2026
**Status:** ✅ VERIFIED - Scores vary based on input

---

## Scoring System Analysis

### AI Detection Score (`calculate_ai_detection_score`)

**Location:** `evidence_collector.py` lines 93-118

**Logic:**
```python
if not ai_evidence:
    return 50.0  # Neutral if no AI detection evidence

# Calculate weighted average of AI detection confidence
weighted_score = 0.0
total_weight = 0.0

for evidence in ai_evidence:
    weight = evidence.credibility.value
    fake_probability = evidence.confidence
    authenticity_score = (1.0 - fake_probability) * 100
    weighted_score += weight * authenticity_score
    total_weight += weight

return min(max(weighted_score / total_weight, 0), 100)
```

**Verification:**
- ✅ Returns 50.0 only when NO AI_DETECTION evidence exists
- ✅ Calculates weighted average based on evidence credibility and confidence
- ✅ Converts fake probability to authenticity score (1 - fake_probability) * 100
- ✅ Varies based on input evidence
- ✅ Not a fixed value when evidence exists

**Potential Issue:**
- ⚠️ Returns 50.0 when no AI evidence (neutral default)
- This is acceptable as a fallback when AI detection fails

---

### Evidence Score (`calculate_evidence_score`)

**Location:** `evidence_collector.py` lines 120-154

**Logic:**
```python
if not non_ai_evidence:
    return 50.0

# Weight evidence by credibility and confidence
weighted_score = 0.0
total_weight = 0.0

for evidence in non_ai_evidence:
    weight = evidence.credibility.value * evidence.confidence
    if evidence.evidence_type == EvidenceType.SUPPORTING:
        weighted_score += weight * 100
    elif evidence.evidence_type == EvidenceType.CONTRADICTION:
        weighted_score += weight * 0
    else:
        weighted_score += weight * 50  # Neutral evidence
    total_weight += weight

base_score = weighted_score / total_weight

# Adjust for cross-source agreement
if len(self.sources) > 1:
    agreement_bonus = min(len(self.sources) * 2, 10)
    base_score += agreement_bonus

return min(max(base_score, 0), 100)
```

**Verification:**
- ✅ Returns 50.0 only when NO non-AI evidence exists
- ✅ Calculates weighted score based on evidence type, credibility, and confidence
- ✅ Supporting evidence contributes 100% of weight
- ✅ Contradicting evidence contributes 0% of weight
- ✅ Neutral evidence contributes 50% of weight
- ✅ Adds cross-source agreement bonus (up to +10 points)
- ✅ Varies based on input evidence
- ✅ Not a fixed value when evidence exists

**Potential Issue:**
- ⚠️ Returns 50.0 when no evidence (neutral default)
- This is acceptable as a fallback when evidence collection fails

---

### Truth Score (`calculate_truth_score`)

**Location:** `evidence_collector.py` lines 156-183

**Logic:**
```python
# Weighted combination of AI and Evidence scores
base_truth_score = (ai_score * 0.4) + (evidence_score * 0.6)

# Source Credibility Bonus
source_bonus = self._calculate_source_bonus()

# Cross-Source Agreement Bonus
agreement_bonus = self._calculate_agreement_bonus()

# Metadata Consistency Bonus
metadata_bonus = self._calculate_metadata_bonus()

# Apply bonuses (max 15 points total)
total_bonus = min(source_bonus + agreement_bonus + metadata_bonus, 15)

final_score = base_truth_score + total_bonus

return min(max(final_score, 0), 100)
```

**Verification:**
- ✅ Combines AI Detection Score (40%) and Evidence Score (60%)
- ✅ Adds Source Credibility Bonus (0-5 points)
- ✅ Adds Cross-Source Agreement Bonus (0-5 points)
- ✅ Adds Metadata Consistency Bonus (0-3 points)
- ✅ Maximum bonus capped at 15 points
- ✅ Varies based on input scores and evidence
- ✅ Not a fixed value

**Bonus Calculations:**

**Source Credibility Bonus:**
- Average credibility ≥ 0.8: +5 points
- Average credibility ≥ 0.6: +3 points
- Average credibility ≥ 0.4: +1 point
- Otherwise: 0 points

**Cross-Source Agreement Bonus:**
- ≥ 5 sources: +5 points
- ≥ 3 sources: +3 points
- ≥ 2 sources: +1 point
- < 2 sources: 0 points

**Metadata Consistency Bonus:**
- Supporting metadata evidence exists: +3 points
- Otherwise: 0 points

---

## Confidence Calculation

**Location:** `evidence_collector.py` lines 233-264 (generate_verdict)

**Logic:**
```python
truth_score = self.calculate_truth_score(ai_score, evidence_score)

if truth_score >= 80:
    verdict = "Likely Authentic"
    confidence = 0.85
elif truth_score >= 60:
    verdict = "Probably Authentic"
    confidence = 0.72
elif truth_score >= 40:
    verdict = "Uncertain"
    confidence = 0.50
elif truth_score >= 20:
    verdict = "Possibly Manipulated"
    confidence = 0.40
else:
    verdict = "Likely Manipulated"
    confidence = 0.30
```

**Verification:**
- ✅ Confidence varies based on truth_score ranges
- ✅ Not a fixed value
- ✅ Truth score drives both verdict and confidence

**Potential Issue:**
- ⚠️ Confidence is FIXED within each truth_score range
  - 80-100: always 0.85
  - 60-79: always 0.72
  - 40-59: always 0.50
  - 20-39: always 0.40
  - 0-19: always 0.30

**Recommendation:**
- Consider making confidence proportional to truth_score within ranges
- Example: confidence = 0.5 + (truth_score - 40) * 0.0175 for 40-59 range
- This would make confidence vary more smoothly

---

## Summary

### Scores That Vary Based on Input
✅ **AI Detection Score** - Varies based on AI_DETECTION evidence
✅ **Evidence Score** - Varies based on non-AI evidence
✅ **Truth Score** - Varies based on AI and Evidence scores + bonuses

### Scores That Have Fixed Fallbacks
⚠️ **AI Detection Score** - Returns 50.0 when no AI evidence
⚠️ **Evidence Score** - Returns 50.0 when no evidence
⚠️ **Confidence** - Fixed within truth_score ranges

### Conclusion

The scoring system is **NOT using fixed values** for the main scores (AI Detection, Evidence, Truth). These scores vary based on the actual evidence collected.

However:
1. There are neutral fallbacks (50.0) when no evidence exists - this is acceptable
2. Confidence is fixed within truth_score ranges - this could be improved for smoother variation

**Overall Assessment:** ✅ Scoring system is working correctly and varies based on input

---

**Verification Status:** COMPLETE
