# TruthLens - AI-Powered Fake News & Deepfake Detection Platform

A full-stack web application for detecting fake news, deepfakes, and misinformation across multiple media types using AI.

## Tech Stack

### Frontend
- React.js 18
- Tailwind CSS
- Framer Motion (animations)
- Recharts (data visualization)
- Lucide React (icons)
- React Router (routing)
- Axios (API client)

### Backend
- FastAPI (Python 3.11+)
- SQLAlchemy (ORM)
- PostgreSQL (database)
- JWT Authentication
- Pydantic (data validation)

## Project Structure

```
truthlens/
├── frontend/
│   ├── src/
│   │   ├── components/      # Reusable UI components
│   │   ├── pages/           # Page components
│   │   ├── services/        # API service layer
│   │   ├── context/         # React Context (Auth)
│   │   ├── App.jsx          # Main app with routing
│   │   └── main.jsx         # Entry point
│   ├── package.json
│   └── tailwind.config.js
│
├── backend/
│   ├── app/
│   │   ├── api/v1/          # API endpoints
│   │   ├── models/          # Database models
│   │   ├── schemas/         # Pydantic schemas
│   │   ├── services/        # ML services (mock for now)
│   │   ├── core/            # Config, security, database
│   │   └── main.py          # FastAPI app
│   ├── requirements.txt
│   └── .env.example
│
└── docker-compose.yml
```

## Features

- **News Analysis**: Detect fake news articles with AI
- **Image Deepfake Detection**: Identify manipulated images
- **Video Detection**: Spot deepfake videos with frame analysis
- **Audio Analysis**: Detect AI-generated audio
- **Fact Checking**: Verify claims against credible sources
- **User Dashboard**: View statistics and analysis history
- **User Profiles**: Track personal analysis history

## Setup Instructions

### Prerequisites
- Node.js 18+
- Python 3.11+
- PostgreSQL 15+
- npm
- pip

### Backend Setup

1. Navigate to the backend directory:
```bash
cd truthlens/backend
```

2. Create a virtual environment:
```bash
python -m venv venv
```

3. Activate the virtual environment:
```bash
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate
```

4. Install dependencies:
```bash
pip install -r requirements.txt
```

5. Create a `.env` file:
```bash
cp .env.example .env
```

6. Update the `.env` file with your database credentials:
```
DATABASE_URL=postgresql://postgres:password@localhost:5432/truthlens
SECRET_KEY=your-secret-key-here
ACCESS_TOKEN_EXPIRE_MINUTES=60
UPLOAD_DIR=./uploads
ALLOWED_ORIGINS=http://localhost:3000
```

7. Create the uploads directory:
```bash
mkdir uploads
```

8. Run database migrations (optional - for production):
```bash
alembic upgrade head
```

9. Start the backend server:
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The backend API will be available at `http://localhost:8000`

### Frontend Setup

1. Navigate to the frontend directory:
```bash
cd truthlens/frontend
```

2. Install dependencies:
```bash
npm install
```

3. Start the development server:
```bash
npm run dev
```

The frontend will be available at `http://localhost:3000`

### Using Docker Compose (Recommended)

1. Ensure Docker and Docker Compose are installed

2. Start all services:
```bash
cd truthlens
docker-compose up --build
```

This will start:
- PostgreSQL on port 5432
- Backend API on port 8000
- Frontend on port 3000

## API Endpoints

### Authentication
- `POST /api/v1/auth/register` - Register a new user
- `POST /api/v1/auth/login` - Login user
- `GET /api/v1/auth/me` - Get current user

### Analysis
- `POST /api/v1/news/analyze` - Analyze news article
- `POST /api/v1/image/analyze` - Analyze image for deepfakes
- `POST /api/v1/video/analyze` - Analyze video for deepfakes
- `POST /api/v1/audio/analyze` - Analyze audio for AI generation
- `POST /api/v1/factcheck/` - Fact check a claim

### Dashboard
- `GET /api/v1/dashboard/stats` - Get dashboard statistics
- `GET /api/v1/dashboard/daily` - Get daily detection data
- `GET /api/v1/dashboard/breakdown` - Get content type breakdown

### User
- `GET /api/v1/users/history` - Get user analysis history

## Design System

### Colors
- Background: Deep Navy (#0B1120)
- Accent: Cyan (#00D4FF)
- Text Primary: White (#F0F4FF)
- Text Secondary: Gray (#A0AEC0)
- Danger: Red (#FF4757)
- Success: Green (#2ED573)
- Warning: Amber (#FFA502)

### Typography
- Headings: Space Grotesk
- Body: DM Sans

### Styling
- Glassmorphism cards with backdrop blur
- Hex grid background pattern
- Framer Motion animations
- Responsive design (mobile + desktop)

## ML Services

Currently, the application uses mock ML services that return realistic fake data. The structure is ready for integration with real ML models:

- `app/services/fake_news.py` - News analysis service
- `app/services/image_deepfake.py` - Image deepfake detection
- `app/services/video_deepfake.py` - Video deepfake detection
- `app/services/audio_deepfake.py` - Audio deepfake detection
- `app/services/fact_checker.py` - Fact checking service

To integrate real ML models, replace the mock functions with actual model inference calls.

## Database Schema

### Users Table
- user_id (UUID, PK)
- name (String)
- email (String, Unique)
- password_hash (String)
- role (Enum: general/journalist/student/government)
- is_admin (Boolean)
- created_at (Timestamp)

### News Analyses Table
- analysis_id (UUID, PK)
- user_id (UUID, FK)
- news_title (Text)
- news_content (Text)
- news_url (String)
- result (Enum: Real/Fake/Suspicious)
- confidence (Float)
- reasons (JSONB)
- sources (JSONB)
- created_at (Timestamp)

### Media Analyses Table
- media_id (UUID, PK)
- user_id (UUID, FK)
- file_type (Enum: image/video/audio)
- file_path (String)
- result (String)
- confidence (Float)
- metadata (JSONB)
- created_at (Timestamp)

### Fact Checks Table
- check_id (UUID, PK)
- user_id (UUID, FK)
- claim (Text)
- status (Enum: True/False/Partially False/Unverified)
- sources (JSONB)
- created_at (Timestamp)

## Development

### Running Tests
```bash
# Backend
cd backend
pytest

# Frontend
cd frontend
npm test
```

### Building for Production
```bash
# Frontend
cd frontend
npm run build

# Backend
cd backend
# Use gunicorn or similar WSGI server
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker
```

## License

This project is for educational purposes.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
