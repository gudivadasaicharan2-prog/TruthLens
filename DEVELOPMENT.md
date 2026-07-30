# Development Setup Guide

This guide helps you set up a development environment for TruthLens.

## Prerequisites

- **Node.js** 18+ and npm
- **Python** 3.11+
- **PostgreSQL** 15+
- **Git**
- **Docker** and Docker Compose (optional but recommended)

## Initial Setup

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/truthlens.git
cd truthlens
```

### 2. Install Pre-commit Hooks

```bash
pip install pre-commit
pre-commit install
```

### 3. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install development dependencies
pip install pytest pytest-cov flake8 black isort pre-commit

# Configure environment
cp .env.example .env
# Edit .env with your configuration

# Create uploads directory
mkdir uploads
```

### 4. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Install development dependencies
npm install --save-dev @testing-library/react @testing-library/jest-dom @testing-library/user-event jest jest-environment-jsdom

# Configure environment
cp .env.example .env
# Edit .env with your configuration
```

### 5. Database Setup

```bash
# Start PostgreSQL (if using Docker)
docker-compose up -d postgres

# Or use local PostgreSQL
# Create database
createdb truthlens

# Run migrations (if available)
cd backend
python -c "from app.core.database import init_db; init_db()"
```

## Running the Application

### Development Mode

#### Backend

```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Backend API will be available at `http://localhost:8000`

#### Frontend

```bash
cd frontend
npm run dev
```

Frontend will be available at `http://localhost:3000`

### Docker Mode

```bash
# Start all services
docker-compose up --build

# Stop services
docker-compose down
```

## Code Style

### Python

- **Formatter:** Black
- **Linter:** Flake8
- **Import Sorter:** isort
- **Style Guide:** PEP 8

Run formatters:
```bash
cd backend
black app
isort app
flake8 app
```

### JavaScript/React

- **Linter:** ESLint
- **Formatter:** Prettier (if configured)
- **Style Guide:** Airbnb Style Guide

Run linter:
```bash
cd frontend
npm run lint
```

## Testing

### Backend Tests

```bash
cd backend
pytest tests/ -v
pytest tests/ --cov=app --cov-report=html
```

### Frontend Tests

```bash
cd frontend
npm test
npm test -- --coverage
```

### E2E Tests

```bash
npx playwright test
```

## Common Development Tasks

### Adding a New API Endpoint

1. Create route in `backend/app/api/v1/`
2. Add Pydantic schema if needed
3. Add tests in `backend/tests/`
4. Update API documentation

### Adding a New Frontend Component

1. Create component in `frontend/src/components/`
2. Add tests in `frontend/tests/`
3. Export from appropriate file
4. Add to routing if it's a page

### Adding a New ML Model

1. Add model code to `backend/app/ai/models/`
2. Update `backend/app/ai/detectors/` if needed
3. Add tests in `backend/tests/test_ai_pipeline.py`
4. Update documentation

## Debugging

### Backend Debugging

```bash
# Run with debugger
cd backend
python -m pdb app/main.py

# Or use VS Code debugger
# Set breakpoints in VS Code
```

### Frontend Debugging

```bash
# Chrome DevTools
# Open http://localhost:3000
# Press F12 or right-click > Inspect

# React DevTools
# Install React DevTools extension
```

## Troubleshooting

### Backend Issues

**Import errors:**
```bash
# Ensure virtual environment is activated
# Reinstall dependencies
pip install -r requirements.txt
```

**Database connection errors:**
```bash
# Check PostgreSQL is running
docker-compose ps postgres

# Check DATABASE_URL in .env
# Ensure database exists
```

### Frontend Issues

**Module not found:**
```bash
# Reinstall dependencies
rm -rf node_modules package-lock.json
npm install
```

**Build errors:**
```bash
# Clear cache
rm -rf dist
npm run build
```

## Performance Tips

### Backend

- Use async/await for I/O operations
- Implement caching for expensive operations
- Use connection pooling
- Profile with `cProfile` if needed

### Frontend

- Use React.memo for expensive components
- Implement virtual scrolling for large lists
- Lazy load routes with React.lazy
- Optimize images

## Security Tips

- Never commit secrets
- Use environment variables for sensitive data
- Validate all inputs
- Keep dependencies updated
- Run security audits regularly

## Getting Help

- Check documentation in `docs/`
- Review existing issues on GitHub
- Ask questions in discussions
- Create a new issue for bugs

## Contributing

See `CONTRIBUTING.md` for contribution guidelines.
