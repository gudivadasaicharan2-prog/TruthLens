# TruthLens - Enterprise AI Image Authenticity Platform

<div align="center">

![TruthLens Logo](https://img.shields.io/badge/TruthLens-v2.1.0-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Python](https://img.shields.io/badge/python-3.11+-blue)
![React](https://img.shields.io/badge/react-18+-61DAFB)
![Status](https://img.shields.io/badge/status-production--ready-success)

**AI-Powered Deepfake Detection & Image Authenticity Analysis**

A production-ready, enterprise-grade web application for detecting AI-generated images, deepfakes, and manipulated content using advanced machine learning models.

[Features](#features) • [Architecture](#architecture) • [Installation](#installation) • [Documentation](#documentation) • [Deployment](#deployment)

</div>

---

## Overview

TruthLens is a sophisticated AI-powered platform designed to detect image authenticity and identify AI-generated content. It combines multiple deep learning models including EfficientNet-B4, CLIP, face detection, and forensic analysis to provide comprehensive image analysis with explainable AI visualizations.

### Key Capabilities

- **Multi-Model Analysis**: Combines EfficientNet, CLIP, face detection, and forensic analysis
- **Explainable AI**: Grad-CAM heatmaps and overlay visualizations
- **Real-time Progress**: WebSocket-style live analysis updates
- **Batch Processing**: Analyze multiple images simultaneously
- **Comparison Mode**: Side-by-side image comparison
- **Professional Reports**: PDF export with detailed findings
- **Enterprise Dashboard**: System health monitoring and analytics

---

## Features

### Core Analysis Features
- **Image Upload**: Drag-and-drop interface with file validation
- **Face Detection**: Identifies faces and facial features
- **Whole-Image Detection**: EfficientNet-B4 deep learning analysis
- **CLIP Analysis**: Semantic image-text relationship analysis
- **Forensics**: Pixel-level artifact examination and metadata analysis
- **Fusion Engine**: Combines all detection modules for final verdict
- **Grad-CAM**: Explainable AI heatmaps and overlays

### User Interface Features
- **Real-time Progress**: Live step-by-step analysis updates
- **Advanced Results**: Executive summary, detection breakdown, evidence panel
- **Compare Mode**: Side-by-side image comparison with differences
- **Batch Mode**: Multiple image analysis with queue management
- **Searchable History**: Filter, sort, and export analysis history
- **Report Center**: Preview, download, and share professional reports
- **System Health Dashboard**: Real-time system metrics and monitoring

### Enterprise Features
- **Settings**: Theme, animations, language, confidence threshold, auto-download
- **Accessibility**: Keyboard navigation, ARIA labels, screen reader support
- **Performance**: Lazy loading, code splitting, memoization, image caching
- **Security**: File validation, secure headers, CSRF protection
- **Responsive**: Mobile-first design with touch-friendly interactions

---

## Architecture

### Technology Stack

#### Frontend
- **React 18**: Modern React with hooks and concurrent features
- **Vite**: Fast build tool and dev server
- **Tailwind CSS**: Utility-first CSS framework
- **Framer Motion**: Production-ready motion library
- **Lucide React**: Beautiful icon library
- **React Router**: Client-side routing
- **Axios**: HTTP client with interceptors

#### Backend
- **FastAPI**: Modern, fast web framework for building APIs
- **Python 3.11+**: Latest Python features
- **SQLAlchemy**: SQL toolkit and ORM
- **PostgreSQL**: Relational database
- **Pydantic**: Data validation using Python type annotations
- **PyTorch**: Deep learning framework
- **OpenCV**: Computer vision library
- **Pillow**: Image processing library

#### ML Models
- **EfficientNet-B4**: Convolutional neural network for image classification
- **CLIP**: Contrastive language-image pre-training
- **Face Detection**: Multi-task cascaded CNN for face detection
- **Grad-CAM**: Gradient-weighted class activation mapping

### Project Structure

```
truthlens/
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── ui/              # Reusable UI components
│   │   │   │   ├── Card.jsx
│   │   │   │   ├── Progress.jsx
│   │   │   │   ├── UploadZone.jsx
│   │   │   │   ├── ImageZoom.jsx
│   │   │   │   └── Skeleton.jsx
│   │   │   ├── Navbar.jsx
│   │   │   ├── Settings.jsx
│   │   │   ├── ReportCenter.jsx
│   │   │   └── ThemeToggle.jsx
│   │   ├── pages/
│   │   │   ├── Landing.jsx
│   │   │   ├── AnalysisProgress.jsx
│   │   │   ├── AdvancedResults.jsx
│   │   │   ├── CompareMode.jsx
│   │   │   ├── BatchMode.jsx
│   │   │   ├── History.jsx
│   │   │   └── SystemHealth.jsx
│   │   ├── services/
│   │   │   └── api.js
│   │   ├── context/
│   │   │   ├── AuthContext.jsx
│   │   │   └── ThemeContext.jsx
│   │   ├── utils/
│   │   │   ├── accessibility.js
│   │   │   ├── performance.js
│   │   │   └── errorHandling.js
│   │   ├── App.jsx
│   │   └── main.jsx
│   ├── public/
│   ├── package.json
│   ├── vite.config.js
│   └── tailwind.config.js
│
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   └── v1/
│   │   │       ├── auth.py
│   │   │       ├── analysis.py
│   │   │       └── health.py
│   │   ├── models/
│   │   │   └── user.py
│   │   ├── schemas/
│   │   │   └── analysis.py
│   │   ├── services/
│   │   │   ├── efficientnet.py
│   │   │   ├── clip.py
│   │   │   ├── face_detection.py
│   │   │   ├── forensics.py
│   │   │   └── fusion.py
│   │   ├── explainability/
│   │   │   ├── gradcam.py
│   │   │   ├── colorize.py
│   │   │   └── overlay.py
│   │   ├── core/
│   │   │   ├── config.py
│   │   │   ├── security.py
│   │   │   └── database.py
│   │   └── main.py
│   ├── requirements.txt
│   └── .env.example
│
├── TruthLensDataset/
│   └── evaluation/
│       ├── metadata/
│       └── datasets.json
│
├── docker-compose.yml
├── Dockerfile
├── .gitignore
└── README.md
```

---

## Installation

### Prerequisites

- **Node.js** 18+ and npm
- **Python** 3.11+
- **PostgreSQL** 15+
- **Docker** and Docker Compose (optional but recommended)
- **Git**

### Backend Setup

1. **Clone the repository**
```bash
git clone https://github.com/yourusername/truthlens.git
cd truthlens
```

2. **Navigate to backend directory**
```bash
cd backend
```

3. **Create virtual environment**
```bash
python -m venv venv
```

4. **Activate virtual environment**
```bash
# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

5. **Install dependencies**
```bash
pip install -r requirements.txt
```

6. **Configure environment variables**
```bash
cp .env.example .env
```

Edit `.env` with your configuration:
```env
DATABASE_URL=postgresql://postgres:password@localhost:5432/truthlens
SECRET_KEY=your-secret-key-here
JWT_SECRET=your-jwt-secret-here
API_KEY=your-api-key-here
CORS_ORIGINS=http://localhost:3000,https://yourdomain.com
MAX_FILE_SIZE=10485760
ALLOWED_MIME_TYPES=image/jpeg,image/png,image/webp
UPLOAD_DIR=./uploads
MODEL_PATH=./models
```

7. **Create uploads directory**
```bash
mkdir uploads
```

8. **Initialize database**
```bash
python -c "from app.core.database import init_db; init_db()"
```

9. **Start backend server**
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Backend API will be available at `http://localhost:8000`

### Frontend Setup

1. **Navigate to frontend directory**
```bash
cd frontend
```

2. **Install dependencies**
```bash
npm install
```

3. **Configure environment variables**
```bash
cp .env.example .env
```

Edit `.env` with your configuration:
```env
VITE_API_URL=http://localhost:8000
VITE_ENABLE_ANALYTICS=false
```

4. **Start development server**
```bash
npm run dev
```

Frontend will be available at `http://localhost:3000`

### Docker Setup (Recommended)

1. **Ensure Docker and Docker Compose are installed**

2. **Start all services**
```bash
docker-compose up --build
```

This will start:
- PostgreSQL on port 5432
- Backend API on port 8000
- Frontend on port 3000

3. **Stop services**
```bash
docker-compose down
```

---

## Configuration

### Backend Configuration

Key configuration options in `.env`:

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | - |
| `SECRET_KEY` | Application secret key | - |
| `JWT_SECRET` | JWT signing secret | - |
| `API_KEY` | External API key | - |
| `CORS_ORIGINS` | Allowed CORS origins | `http://localhost:3000` |
| `MAX_FILE_SIZE` | Maximum upload size in bytes | `10485760` (10MB) |
| `ALLOWED_MIME_TYPES` | Allowed file MIME types | `image/jpeg,image/png,image/webp` |
| `UPLOAD_DIR` | Upload directory path | `./uploads` |
| `MODEL_PATH` | Model directory path | `./models` |

### Frontend Configuration

Key configuration options in `.env`:

| Variable | Description | Default |
|----------|-------------|---------|
| `VITE_API_URL` | Backend API URL | `http://localhost:8000` |
| `VITE_ENABLE_ANALYTICS` | Enable analytics tracking | `false` |

---

## Documentation

### API Documentation

Once the backend is running, visit:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

### API Endpoints

#### Authentication
- `POST /api/v1/auth/register` - Register new user
- `POST /api/v1/auth/login` - Login user
- `GET /api/v1/auth/me` - Get current user info
- `POST /api/v1/auth/logout` - Logout user

#### Analysis
- `POST /api/v1/analysis/upload` - Upload image for analysis
- `GET /api/v1/analysis/{analysis_id}` - Get analysis results
- `GET /api/v1/analysis/{analysis_id}/heatmap` - Get heatmap image
- `GET /api/v1/analysis/{analysis_id}/overlay` - Get overlay image

#### History
- `GET /api/v1/history` - Get user analysis history
- `DELETE /api/v1/history/{analysis_id}` - Delete analysis

#### Health
- `GET /api/v1/health` - System health status

### Component Documentation

#### UI Components
- **Card**: Glassmorphism card with hover effects
- **Progress**: Animated progress bars and step indicators
- **UploadZone**: Drag-and-drop file upload area
- **ImageZoom**: Click-to-zoom image viewer
- **Skeleton**: Loading placeholder components

#### Pages
- **Landing**: Marketing page with hero section
- **AnalysisProgress**: Real-time analysis progress
- **AdvancedResults**: Detailed results dashboard
- **CompareMode**: Side-by-side image comparison
- **BatchMode**: Multiple image analysis
- **History**: Analysis history with filters
- **SystemHealth**: System monitoring dashboard

---

## Deployment

### Production Build

#### Frontend
```bash
cd frontend
npm run build
```

The optimized build will be in `frontend/dist/`

#### Backend
```bash
cd backend
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### Docker Deployment

Build and run with Docker Compose:
```bash
docker-compose -f docker-compose.prod.yml up -d
```

### Environment Variables for Production

Ensure these are set in production:
- Strong `SECRET_KEY` and `JWT_SECRET`
- Production `DATABASE_URL`
- Proper `CORS_ORIGINS`
- Secure `API_KEY`
- HTTPS enabled

### Health Checks

Backend health check endpoint:
```bash
curl http://your-domain.com/api/v1/health
```

Expected response:
```json
{
  "status": "healthy",
  "timestamp": "2026-07-26T12:00:00Z",
  "services": {
    "database": "connected",
    "model": "loaded",
    "storage": "available"
  }
}
```

---

## Testing

### Running Tests

#### Backend Tests
```bash
cd backend
pytest tests/ -v
```

#### Frontend Tests
```bash
cd frontend
npm test
```

### End-to-End Testing

See `TESTING_CHECKLIST.md` for comprehensive testing procedures.

---

## Design System

### Color Palette

| Color | Hex | Usage |
|-------|-----|-------|
| Background | `#0B1220` | Main background |
| Card | `#111827` | Card backgrounds |
| Accent | `#3B82F6` | Primary actions, highlights |
| Success | `#22C55E` | Success states |
| Warning | `#F59E0B` | Warning states |
| Danger | `#EF4444` | Error states |
| Text Primary | `#F0F4FF` | Primary text |
| Text Secondary | `#A0AEC0` | Secondary text |

### Typography

- **Headings**: Inter (Space Grotesk fallback)
- **Body**: Inter (DM Sans fallback)
- **Monospace**: JetBrains Mono

### Styling

- **Glassmorphism**: Backdrop blur with transparency
- **Rounded Corners**: 16px default
- **Shadows**: Soft glow effects
- **Animations**: Smooth Framer Motion transitions

---

## Security

### Security Features

- File upload validation (MIME type, size, extension)
- JWT authentication with secure cookies
- CSRF protection
- Secure headers (HSTS, X-Frame-Options, etc.)
- Input sanitization
- XSS protection via React
- Environment variable configuration

### Security Review

See `SECURITY_REVIEW.md` for detailed security analysis.

---

## Performance

### Performance Features

- Code splitting and lazy loading
- Image optimization and caching
- Memoization and debouncing
- Virtual scrolling for large lists
- Service worker for offline support
- Bundle size optimization

### Performance Audit

See `PERFORMANCE_AUDIT.md` for detailed performance analysis.

---

## Contributing

We welcome contributions! Please follow these guidelines:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Code Style

- **Python**: Follow PEP 8
- **JavaScript/React**: Follow ESLint rules
- **CSS**: Use Tailwind CSS utilities
- **Commits**: Use conventional commit messages

---

## License

This project is licensed under the MIT License - see the LICENSE file for details.

---

## Acknowledgments

- **EfficientNet**: Google Research
- **CLIP**: OpenAI
- **Framer Motion**: Matt Perry
- **Tailwind CSS**: Adam Wathan
- **Lucide Icons**: Feather Icons

---

## Contact

- **Email**: support@truthlens.app
- **Website**: https://truthlens.app
- **Documentation**: https://docs.truthlens.app

---

## Roadmap

### v2.2.0 (Upcoming)
- [ ] Video deepfake detection
- [ ] Audio deepfake detection
- [ ] Real-time webcam analysis
- [ ] Mobile applications
- [ ] API rate limiting
- [ ] Multi-language support

### v2.3.0 (Future)
- [ ] Browser extension
- [ ] API for third-party integration
- [ ] Advanced forensic tools
- [ ] Team collaboration features
- [ ] Enterprise SSO integration

---

## Version History

### v2.1.0 (Current)
- Enterprise-grade UI redesign
- System health dashboard
- Compare mode
- Batch analysis
- Advanced results page
- Professional report center
- Enhanced settings
- Accessibility features
- Performance optimization
- Security improvements

### v2.0.0
- Multi-model analysis pipeline
- Grad-CAM visualizations
- Real-time progress updates
- Enhanced security
- Performance optimizations

### v1.0.0
- Initial release
- Basic image analysis
- User authentication
- History tracking

