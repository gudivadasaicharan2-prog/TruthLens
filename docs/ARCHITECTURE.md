# TruthLens Architecture Documentation

**Version:** v2.1.0  
**Last Updated:** July 26, 2026

---

## Table of Contents

- [System Overview](#system-overview)
- [Frontend Architecture](#frontend-architecture)
- [Backend Architecture](#backend-architecture)
- [AI Pipeline Architecture](#ai-pipeline-architecture)
- [Fusion Engine](#fusion-engine)
- [Grad-CAM Explainability](#grad-cam-explainability)
- [Forensic Analysis](#forensic-analysis)
- [Report Generation](#report-generation)
- [Deployment Architecture](#deployment-architecture)

---

## System Overview

TruthLens is a full-stack web application for AI-powered image authenticity analysis. The system consists of:

- **Frontend:** React-based SPA with modern UI/UX
- **Backend:** FastAPI REST API with ML pipeline
- **Database:** PostgreSQL for data persistence
- **ML Models:** PyTorch-based deep learning models
- **Storage:** Local file system for uploads and reports

```
┌─────────────────────────────────────────────────────────────┐
│                         User Browser                         │
│                    (React SPA + Vite)                       │
└────────────────────┬────────────────────────────────────────┘
                     │ HTTP/HTTPS
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                    Backend API (FastAPI)                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  Auth Layer  │  │  API Layer   │  │  Core Layer  │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└────────────────────┬────────────────────────────────────────┘
                     │
        ┌────────────┴────────────┐
        ▼                         ▼
┌───────────────┐         ┌───────────────┐
│  PostgreSQL   │         │  ML Pipeline   │
│   Database    │         │  (PyTorch)     │
└───────────────┘         └───────────────┘
```

---

## Frontend Architecture

### Technology Stack

- **Framework:** React 18 with hooks and concurrent features
- **Build Tool:** Vite for fast development and optimized builds
- **Styling:** Tailwind CSS for utility-first styling
- **Animations:** Framer Motion for smooth transitions
- **Routing:** React Router for client-side routing
- **State Management:** React Context API
- **HTTP Client:** Axios with interceptors
- **Icons:** Lucide React

### Component Structure

```
src/
├── components/
│   ├── ui/                    # Reusable UI components
│   │   ├── Card.jsx          # Glassmorphism card
│   │   ├── Progress.jsx      # Progress indicators
│   │   ├── UploadZone.jsx    # Drag-drop upload
│   │   ├── ImageZoom.jsx     # Image viewer with zoom
│   │   └── Skeleton.jsx      # Loading placeholders
│   ├── Navbar.jsx            # Navigation bar
│   ├── Settings.jsx          # Settings panel
│   ├── ReportCenter.jsx      # Report management
│   └── ThemeToggle.jsx       # Theme switcher
├── pages/                    # Page components
│   ├── Landing.jsx           # Landing page
│   ├── Detect.jsx            # Image upload page
│   ├── Dashboard.jsx         # User dashboard
│   ├── AnalysisProgress.jsx  # Real-time progress
│   ├── AdvancedResults.jsx   # Results display
│   ├── CompareMode.jsx       # Side-by-side comparison
│   ├── BatchMode.jsx         # Batch analysis
│   ├── History.jsx           # Analysis history
│   ├── Settings.jsx          # User settings
│   └── SystemHealth.jsx      # Health dashboard
├── context/                  # React contexts
│   ├── AuthContext.jsx       # Authentication state
│   └── ThemeContext.jsx      # Theme state
├── services/                 # API services
│   └── api.js                # Axios client
└── utils/                    # Utility functions
    ├── accessibility.js      # A11y helpers
    ├── performance.js        # Performance utilities
    └── errorHandling.js     # Error handlers
```

### Data Flow

```
User Action → Component → Context/Service → API → Response → State Update → Re-render
```

### Key Patterns

1. **Context API:** Global state for auth and theme
2. **Custom Hooks:** Reusable logic (useAuth, useTheme)
3. **Lazy Loading:** Code splitting for performance
4. **Memoization:** React.memo, useMemo, useCallback
5. **Error Boundaries:** Graceful error handling

---

## Backend Architecture

### Technology Stack

- **Framework:** FastAPI (ASGI)
- **Language:** Python 3.11+
- **ORM:** SQLAlchemy
- **Database:** PostgreSQL
- **Validation:** Pydantic
- **ML Framework:** PyTorch
- **Image Processing:** OpenCV, Pillow
- **Server:** Gunicorn with Uvicorn workers

### Layer Architecture

```
app/
├── api/                      # API layer
│   └── v1/
│       ├── auth.py           # Authentication endpoints
│       ├── image.py          # Image analysis endpoints
│       └── health.py         # Health check endpoints
├── core/                     # Core functionality
│   ├── config.py            # Configuration management
│   ├── database.py          # Database connection
│   ├── security.py          # Security utilities
│   ├── logger.py            # Structured logging
│   ├── request_tracing.py   # Request ID middleware
│   ├── exceptions.py        # Custom exceptions
│   ├── metrics.py           # Performance metrics
│   ├── resource_monitor.py  # Resource monitoring
│   ├── health.py            # Health check logic
│   ├── file_validation.py   # File upload validation
│   ├── rate_limit.py        # Rate limiting
│   ├── security_headers.py  # Security headers
│   └── audit_logger.py      # Audit logging
├── models/                   # Database models
│   ├── user.py              # User model
│   └── analysis.py          # Analysis model
├── schemas/                  # Pydantic schemas
│   └── user.py              # User schemas
└── main.py                   # Application entry point
```

### Request Flow

```
HTTP Request → Middleware → Route Handler → Service Layer → ML Pipeline → Response
```

### Middleware Stack

1. **Security Headers:** CSP, HSTS, X-Frame-Options, etc.
2. **CORS:** Cross-origin resource sharing
3. **Rate Limiting:** API rate limiting with slowapi
4. **Request Tracing:** Unique request ID assignment
5. **Exception Handling:** Centralized error handling

### Key Patterns

1. **Dependency Injection:** FastAPI Depends()
2. **Async/Await:** Non-blocking I/O
3. **Pydantic Validation:** Request/response validation
4. **Context Managers:** Resource management
5. **Singleton Pattern:** Model loading

---

## AI Pipeline Architecture

### Pipeline Components

```
┌─────────────────────────────────────────────────────────────┐
│                    AI Analysis Pipeline                      │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  1. Image Preprocessing                                     │
│     ├── Resize to 224x224                                   │
│     ├── Normalize                                          │
│     └── Convert to tensor                                   │
│                                                               │
│  2. EfficientNet-B2 Analysis                               │
│     ├── Feature extraction                                  │
│     ├── Classification                                      │
│     └── Confidence score                                    │
│                                                               │
│  3. CLIP Analysis                                           │
│     ├── Image-text encoding                                 │
│     ├── Semantic similarity                                 │
│     └── AI probability                                      │
│                                                               │
│  4. Face Detection                                          │
│     ├── Face localization                                   │
│     ├── Face count                                          │
│     └── Face regions                                        │
│                                                               │
│  5. Forensic Analysis                                       │
│     ├── ELA (Error Level Analysis)                          │
│     ├── Noise analysis                                      │
│     └── Compression artifacts                               │
│                                                               │
│  6. Grad-CAM Generation                                     │
│     ├── Gradient computation                                │
│     ├── Heatmap generation                                  │
│     └── Overlay creation                                    │
│                                                               │
│  7. Fusion Engine                                           │
│     ├── Weighted combination                                │
│     ├── Image type detection                                │
│     └── Final verdict                                       │
│                                                               │
│  8. Report Generation                                       │
│     ├── PDF creation                                        │
│     ├── Metadata inclusion                                  │
│     └── Visualizations                                      │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

### Model Architecture

```
app/ai/
├── models/
│   └── image_model.py          # EfficientNet-B2 classifier
├── detectors/
│   ├── image_detector.py       # Main detection orchestrator
│   ├── clip_detector.py        # CLIP-based detector
│   ├── fusion_config.py        # Fusion configuration
│   └── fusion.py               # Fusion engine
├── classification/
│   └── image_type_classifier.py # Image type detection
├── forensics/
│   ├── ela.py                  # Error Level Analysis
│   └── noise.py                # Noise analysis
└── explainability/
    ├── gradcam.py              # Grad-CAM generator
    ├── colorize.py             # Heatmap colorization
    └── overlay.py              # Overlay generation
```

### Data Flow

```
Image Upload → Preprocessing → Parallel Analysis → Fusion → Results → Report
```

---

## Fusion Engine

### Purpose

The Fusion Engine combines results from multiple detection modules to produce a final verdict with confidence scores.

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Fusion Engine                             │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  Input:                                                       │
│  ├── EfficientNet score (0-1)                                │
│  ├── CLIP score (0-1)                                        │
│  ├── Face detection results                                 │
│  ├── Forensic scores (ELA, noise)                           │
│  └── Image type (document, artwork, portrait, etc.)          │
│                                                               │
│  Processing:                                                 │
│  1. Image Type Detection                                    │
│     ├── Edge detection                                       │
│     ├── Text detection                                       │
│     ├── Color analysis                                       │
│     └── Aspect ratio                                         │
│                                                               │
│  2. Weight Selection                                         │
│     ├── Based on image type                                 │
│     ├── Based on pipeline (default, forensic)              │
│     └── Based on face presence                              │
│                                                               │
│  3. Weighted Combination                                     │
│     ├── EfficientNet: w1                                    │
│     ├── CLIP: w2                                             │
│     ├── Forensics: w3                                       │
│     └── Face: w4                                             │
│                                                               │
│  4. Confidence Calibration                                   │
│     ├── Calibration factor                                   │
│     ├── Threshold adjustment                                │
│     └── Probability display multiplier                       │
│                                                               │
│  Output:                                                      │
│  ├── Final verdict (Real/Fake/Manipulated)                   │
│  ├── Overall confidence (0-100)                             │
│  ├── AI probability (0-100)                                  │
│  └── Detection breakdown                                     │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

### Configuration

Fusion weights are configured in `fusion_config.py`:

```python
# Example weights for document images
weights = {
    'efficientnet': 0.4,
    'clip': 0.3,
    'forensics': 0.2,
    'face': 0.1
}
```

---

## Grad-CAM Explainability

### Purpose

Grad-CAM (Gradient-weighted Class Activation Mapping) provides visual explanations for model predictions by highlighting important regions in the image.

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                   Grad-CAM Pipeline                          │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  1. Model Hooking                                            │
│     ├── Register forward hook                                │
│     ├── Register backward hook                               │
│     └── Capture gradients                                    │
│                                                               │
│  2. Forward Pass                                             │
│     ├── Pass image through model                            │
│     ├── Capture activations                                  │
│     └── Get prediction                                      │
│                                                               │
│  3. Backward Pass                                            │
│     ├── Compute gradients                                    │
│     ├── Weight activations                                   │
│     └── Generate heatmap                                    │
│                                                               │
│  4. Heatmap Processing                                       │
│     ├── Resize to original size                             │
│     ├── Apply colormap (jet)                                 │
│     └── Normalize (0-255)                                   │
│                                                               │
│  5. Overlay Generation                                       │
│     ├── Blend with original image                           │
│     ├── Apply transparency                                   │
│     └── Save as PNG                                         │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

### Implementation

```python
class GradCAMGenerator:
    def __init__(self, model):
        self.model = model
        self.target_layer = self._find_target_layer()
        
    def generate_heatmap(self, image):
        # Forward pass
        activations = self._get_activations(image)
        
        # Backward pass
        gradients = self._get_gradients(image)
        
        # Weight activations
        weights = np.mean(gradients, axis=(1, 2))
        
        # Generate heatmap
        heatmap = np.dot(activations, weights)
        
        return heatmap
```

---

## Forensic Analysis

### Purpose

Forensic analysis examines pixel-level artifacts to detect manipulation and compression inconsistencies.

### Components

#### ELA (Error Level Analysis)

```
┌─────────────────────────────────────────────────────────────┐
│                    ELA Analysis                              │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  1. Re-compression                                           │
│     ├── Save at quality 90 (JPEG)                           │
│     ├── Load re-compressed image                            │
│     └── Compute difference                                  │
│                                                               │
│  2. Difference Calculation                                   │
│     ├── Pixel-wise difference                               │
│     ├── Absolute values                                     │
│     └── Variance calculation                                │
│                                                               │
│  3. Score Normalization                                      │
│     ├── Normalize to 0-1                                    │
│     ├── Apply threshold                                    │
│     └── Return ELA score                                    │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

#### Noise Analysis

```
┌─────────────────────────────────────────────────────────────┐
│                   Noise Analysis                             │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  1. Convert to Grayscale                                     │
│     ├── RGB to Luminance                                    │
│     └── Single channel                                      │
│                                                               │
│  2. Noise Estimation                                         │
│     ├── Gaussian blur                                       │
│     ├── Subtract from original                              │
│     └── Compute standard deviation                           │
│                                                               │
│  3. Score Calculation                                        │
│     ├── Normalize noise level                               │
│     └── Return noise score                                   │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

---

## Report Generation

### Purpose

Generate professional PDF reports with analysis results, visualizations, and metadata.

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                  Report Generation                           │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  1. Data Collection                                          │
│     ├── Analysis results                                    │
│     ├── Metadata (filename, size, type)                     │
│     ├── Visualizations (heatmap, overlay)                   │
│     └── Timestamp                                            │
│                                                               │
│  2. Report Structure                                         │
│     ├── Header (logo, title, date)                          │
│     ├── Executive Summary                                    │
│     ├── Detection Breakdown                                 │
│     ├── Visualizations                                      │
│     ├── Technical Details                                    │
│     └── Footer                                               │
│                                                               │
│  3. PDF Generation                                           │
│     ├── Use ReportLab                                        │
│     ├── Add images                                           │
│     ├── Add tables                                           │
│     └── Format text                                         │
│                                                               │
│  4. File Output                                              │
│     ├── Save to temporary directory                          │
│     ├── Return file path                                     │
│     └── Schedule cleanup                                    │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

### Report Sections

1. **Executive Summary**
   - Verdict (Real/Fake/Manipulated)
   - Overall confidence
   - AI probability

2. **Detection Breakdown**
   - EfficientNet score
   - CLIP score
   - Forensic scores
   - Face detection results

3. **Visualizations**
   - Original image
   - Grad-CAM heatmap
   - Overlay visualization

4. **Technical Details**
   - File metadata
   - Analysis timestamp
   - Model versions

---

## Deployment Architecture

### Development Environment

```
┌─────────────────────────────────────────────────────────────┐
│                  Development Setup                           │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  Frontend: Vite Dev Server (http://localhost:3000)          │
│  Backend: Uvicorn (http://localhost:8000)                   │
│  Database: PostgreSQL (localhost:5432)                      │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

### Production Environment

```
┌─────────────────────────────────────────────────────────────┐
│                 Production Deployment                         │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              Load Balancer (Nginx)                   │   │
│  └──────────────┬──────────────────────────────────────┘   │
│                 │                                            │
│  ┌──────────────┴──────────────┬──────────────────────┐   │
│  ▼                             ▼                      │   │
│  ┌──────────────────┐   ┌──────────────────┐         │   │
│  │  Backend Pod 1   │   │  Backend Pod 2   │   ...   │   │
│  │  (FastAPI)       │   │  (FastAPI)       │         │   │
│  └──────────────────┘   └──────────────────┘         │   │
│         │                       │                      │   │
│         └───────────┬───────────┘                      │   │
│                     ▼                                  │   │
│           ┌──────────────────┐                         │   │
│           │   PostgreSQL     │                         │   │
│           │   (Primary)      │                         │   │
│           └──────────────────┘                         │   │
│                     │                                  │   │
│           ┌──────────────────┐                         │   │
│           │   PostgreSQL     │                         │   │
│           │   (Replica)      │                         │   │
│           └──────────────────┘                         │   │
│                                                               │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              Static Files (CDN)                       │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

### Docker Deployment

```
┌─────────────────────────────────────────────────────────────┐
│              Docker Compose Architecture                     │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  Services:                                                    │
│  1. postgres: PostgreSQL 15-alpine                          │
│  2. backend: FastAPI with Gunicorn                          │
│  3. frontend: Nginx serving static files                    │
│                                                               │
│  Volumes:                                                     │
│  - postgres_data: PostgreSQL persistence                      │
│  - uploads: File upload storage                             │
│                                                               │
│  Networks:                                                    │
│  - truthlens-network: Service communication                  │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

### CI/CD Pipeline

```
┌─────────────────────────────────────────────────────────────┐
│              GitHub Actions Pipeline                         │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  1. Lint Job                                                  │
│     ├── Python linting (flake8)                              │
│     ├── Code formatting (black)                              │
│     └── Import sorting (isort)                              │
│                                                               │
│  2. Backend Tests Job                                         │
│     ├── Install dependencies                                  │
│     ├── Run pytest with coverage                             │
│     └── Upload to Codecov                                   │
│                                                               │
│  3. Frontend Tests Job                                        │
│     ├── Install dependencies                                  │
│     ├── Run Jest with coverage                               │
│     └── Upload to Codecov                                   │
│                                                               │
│  4. Build Job                                                 │
│     ├── Build Docker images                                  │
│     ├── Tag with commit SHA                                  │
│     └── Push to Docker Hub                                  │
│                                                               │
│  5. Deploy Job (develop branch)                              │
│     └── Deploy to staging environment                       │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

---

## Security Architecture

### Security Layers

```
┌─────────────────────────────────────────────────────────────┐
│                   Security Layers                             │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  1. Network Layer                                            │
│     ├── HTTPS/TLS encryption                                   │
│     ├── Firewall rules                                       │
│     └── DDoS protection                                     │
│                                                               │
│  2. Application Layer                                        │
│     ├── Security headers                                     │
│     ├── CORS configuration                                   │
│     ├── Rate limiting                                        │
│     └── Input validation                                    │
│                                                               │
│  3. Authentication Layer                                      │
│     ├── JWT authentication                                   │
│     ├── Google OAuth                                         │
│     ├── Session management                                   │
│     └── Token expiration                                     │
│                                                               │
│  4. Data Layer                                               │
│     ├── Encrypted secrets                                    │
│     ├── SQL injection prevention                             │
│     ├── XSS protection                                       │
│     └── CSRF protection                                     │
│                                                               │
│  5. File Upload Layer                                        │
│     ├── MIME type validation                                 │
│     ├── Magic bytes validation                               │
│     ├── File size limits                                     │
│     └── Executable detection                                 │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

---

## Monitoring Architecture

### Observability Stack

```
┌─────────────────────────────────────────────────────────────┐
│                 Observability Stack                           │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  1. Logging                                                   │
│     ├── Structured JSON logging                              │
│     ├── Request tracing (request ID)                         │
│     ├── Log levels (DEBUG, INFO, WARNING, ERROR)            │
│     └── Log aggregation (ELK)                                │
│                                                               │
│  2. Metrics                                                   │
│     ├── Performance metrics (operation timing)               │
│     ├── Resource metrics (CPU, GPU, memory, disk)           │
│     ├── Business metrics (request count, error rate)         │
│     └── Prometheus export                                     │
│                                                               │
│  3. Tracing                                                   │
│     ├── Distributed tracing (OpenTelemetry)                   │
│     ├── Request propagation                                  │
│     └── Span tracking                                        │
│                                                               │
│  4. Health Checks                                             │
│     ├── Basic health (/health)                                │
│     ├── Readiness check (/health/ready)                      │
│     ├── Liveness check (/health/live)                        │
│     └── Detailed health (/health/detailed)                   │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

---

## Performance Architecture

### Optimization Strategies

```
┌─────────────────────────────────────────────────────────────┐
│              Performance Optimization                         │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  Frontend:                                                    │
│  ├── Code splitting (lazy loading)                          │
│  ├── Memoization (React.memo, useMemo, useCallback)          │
│  ├── Virtual scrolling                                       │
│  ├── Image optimization                                      │
│  ├── Bundle size optimization                                │
│  └── Service worker (offline support)                        │
│                                                               │
│  Backend:                                                     │
│  ├── Async/await (non-blocking I/O)                          │
│  ├── Connection pooling                                     │
│  ├── Model caching (singleton)                               │
│  ├── Response compression                                    │
│  └── CDN for static assets                                   │
│                                                               │
│  ML Pipeline:                                                │
│  ├── Model warm-up at startup                               │
│  ├── Batch processing                                        │
│  ├── GPU acceleration                                       │
│  └── Model quantization (future)                            │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

---

## Conclusion

TruthLens follows a modern, scalable architecture with clear separation of concerns. The system is designed for:

- **Maintainability:** Clean code structure and documentation
- **Scalability:** Horizontal scaling with containerization
- **Security:** Multiple security layers and validation
- **Observability:** Comprehensive logging and monitoring
- **Performance:** Optimization strategies at all layers

For more details, see the specific component documentation and code comments.
