# TruthLens Evidence-Based Verification System - Technical Report

## Executive Summary

TruthLens has been transformed from an AI prediction-based system to an Evidence-Based Verification Platform. This report documents the current implementation, limitations, and required enhancements to achieve research-backed verification capabilities.

---

## Current Implementation Status

### Completed Features

#### 1. Evidence Collection Infrastructure
**File:** `backend/app/services/evidence_collector.py`

- **EvidenceType Enum:** METADATA, FORENSIC, SOURCE, CROSS_REFERENCE, AI_DETECTION, CONTRADICTION, SUPPORTING, NEUTRAL
- **SourceCredibility Enum:** HIGH (0.9), MEDIUM (0.7), LOW (0.4), UNKNOWN (0.5)
- **Evidence Class:** Represents individual evidence pieces with type, source, credibility, confidence, and data
- **EvidenceReport Class:** Aggregates evidence, calculates Truth Score (0-100), generates verdicts with reasoning
- **SourceVerifier Class:** Assesses source credibility against trusted and questionable source lists

#### 2. Image Verification (Evidence-Based)
**File:** `backend/app/services/image_deepfake.py`

**Current Implementation:**
- EXIF metadata extraction
- Image hash generation (perceptual, MD5, SHA256)
- Image type classification (face photo, screenshot, document, graphic)
- OpenCV forensic analysis:
  - Laplacian variance (blur detection)
  - Noise pattern analysis
  - Edge density (Canny detection)
  - Color distribution analysis
  - FFT frequency domain analysis
- Evidence report generation with 5 evidence types

**API Endpoint:** `POST /api/v1/image/analyze`

#### 3. Video Verification (Evidence-Based)
**File:** `backend/app/services/video_deepfake.py`

**Current Implementation:**
- Video metadata extraction (frames, FPS, duration, resolution)
- Face detection in frames
- Frame-level forensic analysis
- Timeline consistency analysis
- Evidence report generation with 4 evidence types

**API Endpoint:** `POST /api/v1/video/analyze`

#### 4. Audio Verification (Evidence-Based)
**File:** `backend/app/services/audio_deepfake.py`

**Current Implementation:**
- Audio metadata extraction (duration, sample rate)
- Spectral analysis (centroid, zero-crossing rate, MFCCs, RMS energy)
- AI voice pattern detection
- Evidence report generation with 3 evidence types

**API Endpoint:** `POST /api/v1/audio/analyze`

#### 5. Article Verification (Evidence-Based)
**File:** `backend/app/services/fake_news.py`

**Current Implementation:**
- Content metadata extraction (title length, word count)
- BERT model analysis (when available)
- Heuristic analysis (sensationalism, source attribution, hedging language)
- Source credibility verification
- Evidence report generation with 4 evidence types

**API Endpoint:** `POST /api/v1/news/analyze`

#### 6. Fact Checker (Evidence-Based)
**File:** `backend/app/services/fact_checker.py`

**Current Implementation:**
- Keyword extraction for search
- General knowledge base verification
- News API source fetching
- Source credibility assessment
- Claim characteristic analysis
- Evidence report generation with 3 evidence types

**API Endpoint:** `POST /api/v1/factcheck/check`

#### 7. Truth Score Calculation
**Implementation:** `backend/app/services/evidence_collector.py`

**Current Formula:**
```
Base Score = Σ(Evidence Confidence × Evidence Credibility Weight)
Cross-Source Bonus = min(Sources × 2, 10)
Truth Score = min(max(Base Score + Cross-Source Bonus, 0), 100)
```

**Verdict Thresholds:**
- 80-100: Likely Authentic
- 60-79: Probably Authentic
- 40-59: Uncertain
- 20-39: Possibly Manipulated
- 0-19: Likely Manipulated

#### 8. Explainability
**Every verdict includes:**
- Verdict
- Confidence (0-1)
- Truth Score (0-100)
- Reasoning (detailed explanation)
- Evidence count breakdown
- Sources consulted
- Full evidence list with details

---

## Current Limitations

### 1. Image Verification Limitations

**Missing Features:**
- ❌ Reverse image search integration
- ❌ Similar image discovery
- ❌ Earliest appearance detection
- ❌ AI-generated image detection (beyond basic heuristics)
- ❌ Advanced AI model integration (Stable Diffusion, Midjourney detection)

**Current AI Detection:**
- Relies on OpenCV forensic heuristics only
- No integration with AI detection models
- Cannot distinguish between AI-generated and authentic images reliably

### 2. Video Verification Limitations

**Missing Features:**
- ❌ Face consistency analysis across frames
- ❌ Lip-sync consistency analysis
- ❌ Reverse search of key frames
- ❌ Deepfake-specific detection (face swapping, reenactment)
- ❌ Temporal consistency analysis

**Current AI Detection:**
- Frame-level OpenCV forensic analysis only
- No deepfake-specific models
- Cannot detect face swaps or voice synthesis

### 3. Audio Verification Limitations

**Missing Features:**
- ❌ Speech-to-text transcription
- ❌ Voice-cloning detection
- ❌ Transcript search
- ❌ Speaker consistency analysis
- ❌ Voice biometric analysis

**Current AI Detection:**
- Librosa-based spectral analysis only
- No voice cloning detection
- No transcription capabilities

### 4. Article Verification Limitations

**Missing Features:**
- ❌ Claim extraction (NLP)
- ❌ Entity extraction (NER)
- ❌ Contradiction detection between sources
- ❌ Advanced NLP models for semantic analysis

**Current AI Detection:**
- BERT model (when available) with limited accuracy
- Heuristic pattern matching
- No semantic understanding

### 5. Fact Checker Limitations

**Missing Features:**
- ❌ Wikipedia integration
- ❌ Government website verification
- ❌ Trusted news organization database
- ❌ Cross-reference evidence aggregation
- ❌ Historical evidence tracking

**Current Sources:**
- NewsAPI (requires API key)
- General knowledge base (limited)
- No fallback to authoritative sources

### 6. Truth Score Limitations

**Current Issues:**
- Single combined score (AI Detection + Evidence)
- No separation between AI Detection Score, Evidence Score, and Truth Score
- Limited weighting of evidence types
- No historical evidence consideration

### 7. Model Limitations

**Current Models:**
- HuggingFace models failing to load (authentication issues)
- No local ML models deployed
- No ensemble methods
- No model versioning or fallback strategies

---

## Required Enhancements

### 1. Image Verification Enhancements

#### Reverse Image Search Integration
**Required APIs/Services:**
- Google Reverse Image Search API
- TinEye API
- Yandex Images API
- Bing Image Search API

**Implementation:**
```python
class ReverseImageSearch:
    def search_similar(self, image_path: str) -> List[Dict]:
        """Find similar images across the web"""
        # Query multiple reverse image search APIs
        # Return similar images with URLs, dates, sources
        pass
    
    def find_earliest_appearance(self, image_path: str) -> Dict:
        """Find the earliest occurrence of this image"""
        # Search for earliest date
        # Return source, date, URL
        pass
```

#### AI-Generated Image Detection
**Required Models:**
- Stable Diffusion detector
- Midjourney detector
- DALL-E detector
- General AI image classifier

**Implementation:**
```python
class AIGeneratedImageDetector:
    def detect_ai_generation(self, image_path: str) -> Dict:
        """Detect if image is AI-generated"""
        # Use specialized AI detection models
        # Return model, confidence, indicators
        pass
```

### 2. Video Verification Enhancements

#### Face Consistency Analysis
**Required Libraries:**
- Face recognition (face_recognition library)
- DeepFace
- InsightFace

**Implementation:**
```python
class FaceConsistencyAnalyzer:
    def analyze_face_consistency(self, video_path: str) -> Dict:
        """Analyze face consistency across frames"""
        # Extract faces from each frame
        # Compare embeddings
        # Detect face swaps
        pass
```

#### Lip-Sync Analysis
**Required Libraries:**
- Wav2Lip
- SyncNet
- Lip-sync detection models

**Implementation:**
```python
class LipSyncAnalyzer:
    def analyze_lip_sync(self, video_path: str) -> Dict:
        """Analyze lip-sync consistency"""
        # Extract audio and video tracks
        # Detect lip movements
        # Compare with speech
        pass
```

### 3. Audio Verification Enhancements

#### Speech-to-Text Transcription
**Required APIs/Models:**
- OpenAI Whisper API
- Google Speech-to-Text
- Azure Speech Services
- Local Whisper model

**Implementation:**
```python
class AudioTranscriber:
    def transcribe(self, audio_path: str) -> Dict:
        """Transcribe audio to text"""
        # Use Whisper or similar
        # Return transcript with timestamps
        pass
```

#### Voice-Cloning Detection
**Required Models:**
- Voice anti-spoofing models
- Voice biometric analysis
- Deep voice detection

**Implementation:**
```python
class VoiceCloningDetector:
    def detect_voice_cloning(self, audio_path: str) -> Dict:
        """Detect if audio is voice-cloned"""
        # Use anti-spoofing models
        # Analyze voice biometrics
        pass
```

### 4. Article Verification Enhancements

#### Claim Extraction
**Required Models:**
- NLP claim extraction models
- Transformer-based extractors
- Fact-checking claim extractors

**Implementation:**
```python
class ClaimExtractor:
    def extract_claims(self, text: str) -> List[Dict]:
        """Extract verifiable claims from text"""
        # Use NLP models
        # Return claims with confidence
        pass
```

#### Entity Extraction
**Required Models:**
- Named Entity Recognition (NER)
- spaCy
- HuggingFace NER models

**Implementation:**
```python
class EntityExtractor:
    def extract_entities(self, text: str) -> List[Dict]:
        """Extract named entities from text"""
        # Use NER models
        # Return entities with types
        pass
```

### 5. Fact Checker Enhancements

#### Wikipedia Integration
**Required API:**
- Wikipedia API
- MediaWiki API

**Implementation:**
```python
class WikipediaVerifier:
    def verify_claim(self, claim: str) -> Dict:
        """Verify claim against Wikipedia"""
        # Search Wikipedia
        # Extract relevant information
        # Return verification result
        pass
```

#### Government Website Verification
**Required:**
- List of government domains
- Web scraping capabilities
- Official document verification

**Implementation:**
```python
class GovernmentVerifier:
    def verify_claim(self, claim: str) -> Dict:
        """Verify claim against government sources"""
        # Search government websites
        # Extract official statements
        # Return verification result
        pass
```

### 6. Truth Score Separation

**New Architecture:**
```python
class TruthScoreCalculator:
    def calculate_ai_detection_score(self, evidence: List[Evidence]) -> float:
        """Calculate AI detection score (0-100)"""
        # Only consider AI_DETECTION evidence
        pass
    
    def calculate_evidence_score(self, evidence: List[Evidence]) -> float:
        """Calculate evidence score (0-100)"""
        # Consider all non-AI evidence
        pass
    
    def calculate_truth_score(self, ai_score: float, evidence_score: float) -> float:
        """Calculate final truth score (0-100)"""
        # Weighted combination
        pass
```

---

## New Architecture

### Proposed System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    TruthLens API Layer                      │
│  (FastAPI Endpoints for Image, Video, Audio, Article, Fact) │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────┐
│              Evidence Collection Service                      │
│  (EvidenceReport, Evidence, SourceVerifier)                  │
└────────────────────┬────────────────────────────────────────┘
                     │
        ┌────────────┼────────────┐
        │            │            │
┌───────▼──────┐ ┌──▼──────────┐ ┌─▼──────────────┐
│ AI Detection │ │  Evidence   │ │  Source       │
│ Service      │ │  Collection │ │  Verification  │
│              │ │  Service    │ │  Service       │
└───────┬──────┘ └──┬──────────┘ └─┬──────────────┘
        │            │            │
┌───────▼──────┐ ┌──▼──────────┐ ┌─▼──────────────┐
│ ML Models    │ │  Forensic   │ │  External      │
│ (HuggingFace)│ │  Analysis   │ │  APIs          │
│              │ │  (OpenCV)   │ │  (NewsAPI,     │
└──────────────┘ └─────────────┘ │   Wikipedia,   │
                                │   Google, etc) │
                                └────────────────┘
```

### Evidence Sources

**Current Sources:**
- EXIF metadata
- Image hashes
- OpenCV forensic analysis
- NewsAPI (when available)
- General knowledge base

**Required New Sources:**
- Reverse image search APIs (Google, TinEye, Yandex)
- Wikipedia API
- Government websites
- Trusted news organizations
- AI detection models
- Speech-to-text services
- Voice biometric analysis
- Face recognition systems
- Lip-sync detection models

---

## Files Modified

### Core Infrastructure
1. `backend/app/services/evidence_collector.py` - **Created**
   - Evidence collection framework
   - Truth score calculation
   - Source verification

2. `backend/app/core/config.py` - **Modified**
   - Added HF_TOKEN field

### Verification Modules
3. `backend/app/services/image_deepfake.py` - **Modified**
   - Added evidence-based verification
   - Metadata extraction
   - Hash generation
   - Forensic analysis integration

4. `backend/app/services/video_deepfake.py` - **Modified**
   - Added evidence-based verification
   - Frame-level analysis
   - Timeline consistency

5. `backend/app/services/audio_deepfake.py` - **Modified**
   - Added evidence-based verification
   - Spectral analysis
   - AI voice pattern detection

6. `backend/app/services/fake_news.py` - **Modified**
   - Added evidence-based verification
   - Source credibility verification
   - Heuristic analysis

7. `backend/app/services/fact_checker.py` - **Modified**
   - Added evidence-based verification
   - Source verification
   - Keyword extraction

---

## APIs Added

### Current API Endpoints

**Image Verification:**
- `POST /api/v1/image/analyze` - Analyze image for deepfakes

**Video Verification:**
- `POST /api/v1/video/analyze` - Analyze video for deepfakes

**Audio Verification:**
- `POST /api/v1/audio/analyze` - Analyze audio for deepfakes

**Article Verification:**
- `POST /api/v1/news/analyze` - Analyze article for fake news

**Fact Checking:**
- `POST /api/v1/factcheck/check` - Verify claims against sources

**Health Check:**
- `GET /api/v1/health` - Check system health and model status

### Required New API Endpoints

**Reverse Image Search:**
- `POST /api/v1/image/reverse-search` - Search for similar images
- `GET /api/v1/image/earliest-appearance/:id` - Get earliest appearance

**Video Analysis:**
- `POST /api/v1/video/face-consistency` - Analyze face consistency
- `POST /api/v1/video/lip-sync` - Analyze lip-sync

**Audio Analysis:**
- `POST /api/v1/audio/transcribe` - Transcribe audio to text
- `POST /api/v1/audio/voice-clone-detect` - Detect voice cloning

**Article Analysis:**
- `POST /api/v1/article/extract-claims` - Extract claims from article
- `POST /api/v1/article/extract-entities` - Extract entities from article

**Fact Checking:**
- `POST /api/v1/factcheck/wikipedia` - Verify against Wikipedia
- `POST /api/v1/factcheck/government` - Verify against government sources

---

## Models Used

### Current Models

**HuggingFace Models (Attempting to Load):**
- `mrm8488/bert-tiny-finetuned-fake-news` - News classification
- `valurank/distilroberta-misinformation` - Misinformation detection
- `distilbert-base-uncased-finetuned-epistemic-headlines` - Headline classification

**Status:** Failing to load due to authentication issues

### Required New Models

**Image Detection:**
- Stable Diffusion detector
- Midjourney detector
- DALL-E detector
- General AI image classifier

**Video Detection:**
- Face recognition models (DeepFace, InsightFace)
- Lip-sync detection models (Wav2Lip, SyncNet)
- Deepfake detection models (FaceForensics++)

**Audio Detection:**
- Whisper (speech-to-text)
- Voice anti-spoofing models
- Voice biometric models

**NLP Models:**
- Claim extraction models
- Named Entity Recognition (NER)
- Contradiction detection models

---

## Evidence Sources Used

### Current Evidence Sources

**Internal:**
- EXIF metadata
- Image hashes (perceptual, MD5, SHA256)
- OpenCV forensic analysis
- Heuristic pattern matching
- General knowledge base

**External:**
- NewsAPI (when API key available)
- Trusted source lists (hardcoded)

### Required New Evidence Sources

**Image Search:**
- Google Reverse Image Search API
- TinEye API
- Yandex Images API
- Bing Image Search API

**Knowledge Bases:**
- Wikipedia API
- MediaWiki API
- Wikidata

**Government Sources:**
- Official government websites
- Government databases
- Official documents

**News Organizations:**
- Trusted news APIs
- News aggregators
- Fact-checking organizations (Snopes, FactCheck.org, PolitiFact)

**AI Detection:**
- AI detection model APIs
- ML model predictions
- Ensemble methods

---

## Implementation Priority

### Phase 1: Critical Enhancements (High Priority)
1. Separate AI Detection Score, Evidence Score, and Truth Score
2. Add Wikipedia integration for fact checking
3. Add government website verification
4. Improve AI detection with local models

### Phase 2: Advanced Features (Medium Priority)
1. Reverse image search integration
2. Speech-to-text transcription
3. Face consistency analysis
4. Claim extraction

### Phase 3: Research Features (Lower Priority)
1. Lip-sync analysis
2. Voice-cloning detection
3. Entity extraction
4. Contradiction detection

---

## Conclusion

TruthLens has been successfully transformed into an Evidence-Based Verification Platform with a solid foundation for research-backed verification. The current implementation provides:

- Evidence collection infrastructure
- Truth score calculation
- Explainability for all verdicts
- Multi-source verification capabilities

However, significant enhancements are required to achieve the full vision of research-backed verification:

- Integration with external APIs (reverse image search, Wikipedia, government sources)
- Advanced AI detection models (face recognition, voice cloning, AI image generation)
- NLP capabilities (claim extraction, entity extraction, contradiction detection)
- Separation of AI Detection Score, Evidence Score, and Truth Score

The current system provides a strong foundation but requires additional development and API integrations to achieve the desired accuracy and reliability for deepfake detection and content verification.

---

**Report Generated:** June 1, 2026
**System Version:** Evidence-Based Verification Platform v1.0
**Status:** Foundation Complete - Enhancements Required
