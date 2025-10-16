# Quickstart Guide: Online Collaborative Document System

**Branch**: `001-build-an-simple` | **Date**: 2025-10-16

This guide will get you up and running with the online collaborative document system in your local development environment using Docker and docker-compose.

---

## Prerequisites

- **Docker**: Version 20.10+ ([Install Docker](https://docs.docker.com/get-docker/))
- **docker-compose**: Version 2.0+ (included with Docker Desktop)
- **Git**: For cloning the repository
- **Node.js**: Version 20+ (for frontend development)
- **Python**: Version 3.11+ (for backend development)
- **uv**: Python dependency manager ([Install uv](https://github.com/astral-sh/uv))

---

## Quick Start (5 minutes)

### 1. Clone and Navigate

```bash
git clone <repository-url> online-doc
cd online-doc
git checkout 001-build-an-simple
```

### 2. Start All Services

```bash
docker-compose up -d
```

This starts:
- **PostgreSQL** on port 5432
- **Redis** on port 6379
- **Backend API** on port 8000
- **Frontend** on port 3000

### 3. Access the Application

Open your browser to:
```
http://localhost:3000
```

### 4. Stop Services

```bash
docker-compose down
```

---

## Detailed Setup

### Project Structure

```
online-doc/
├── backend/           # Python FastAPI backend
├── frontend/          # React Next.js frontend
├── k8s/              # Kubernetes manifests
├── specs/            # Feature specifications
├── docker-compose.yml # Local development orchestration
└── README.md
```

---

## Backend Setup

### 1. Install Dependencies

```bash
cd backend

# Install uv if not already installed
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create virtual environment and install dependencies
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
uv pip install -r requirements.txt
```

### 2. Environment Variables

Create `backend/.env`:

```env
# Database
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/online_doc

# Redis
REDIS_URL=redis://localhost:6379

# Authentication
SECRET_KEY=your-secret-key-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60

# Server
HOST=0.0.0.0
PORT=8000
DEBUG=True

# CORS
FRONTEND_URL=http://localhost:3000
```

### 3. Run Database Migrations

```bash
# Apply migrations
alembic upgrade head

# Create initial migration (if needed)
alembic revision --autogenerate -m "Initial schema"
```

### 4. Run Backend Server

```bash
# Development mode with hot reload
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

**API Documentation** (auto-generated):
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

---

## Frontend Setup

### 1. Install Dependencies

```bash
cd frontend
npm install
```

### 2. Environment Variables

Create `frontend/.env.local`:

```env
# API URLs
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
NEXT_PUBLIC_WS_URL=ws://localhost:8000/ws

# App Config
NEXT_PUBLIC_APP_NAME=Online Doc
NEXT_PUBLIC_APP_ENV=development
```

### 3. Run Frontend Server

```bash
npm run dev
```

Frontend available at: http://localhost:3000

---

## Docker Development

### docker-compose.yml Structure

```yaml
services:
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: online_doc
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql+asyncpg://postgres:postgres@postgres:5432/online_doc
      REDIS_URL: redis://redis:6379
    depends_on:
      - postgres
      - redis
    volumes:
      - ./backend:/app

  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    environment:
      NEXT_PUBLIC_API_URL: http://localhost:8000/api/v1
      NEXT_PUBLIC_WS_URL: ws://localhost:8000/ws
    depends_on:
      - backend
    volumes:
      - ./frontend:/app

volumes:
  postgres_data:
```

### Docker Commands

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f backend

# Restart a service
docker-compose restart backend

# Rebuild after code changes
docker-compose up -d --build

# Stop all services
docker-compose down

# Stop and remove volumes (clean slate)
docker-compose down -v
```

---

## Database Management

### Connect to PostgreSQL

```bash
# Via docker-compose
docker-compose exec postgres psql -U postgres -d online_doc

# Via local psql
psql -h localhost -U postgres -d online_doc
```

### Common Database Operations

```bash
# Create new migration
cd backend
alembic revision --autogenerate -m "Description of changes"

# Apply migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1

# View migration history
alembic history

# Reset database (WARNING: deletes all data)
alembic downgrade base
alembic upgrade head
```

---

## Testing

### Backend Tests

```bash
cd backend

# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/unit/test_document_service.py

# Run tests in watch mode
pytest-watch
```

### Frontend Tests

```bash
cd frontend

# Run unit tests
npm run test

# Run unit tests with coverage
npm run test:coverage

# Run E2E tests
npm run test:e2e

# Run E2E tests in UI mode
npm run test:e2e:ui

# Run accessibility tests
npm run test:a11y
```

---

## Development Workflow

### 1. Create Feature Branch

```bash
git checkout -b 002-new-feature
```

### 2. Make Changes

Edit code in `backend/` or `frontend/`

### 3. Run Tests

```bash
# Backend
cd backend && pytest

# Frontend
cd frontend && npm run test
```

### 4. Test Locally

```bash
# Start services
docker-compose up -d

# Test in browser
open http://localhost:3000
```

### 5. Commit Changes

```bash
git add .
git commit -m "feat: add new feature"
```

### 6. Push and Create PR

```bash
git push origin 002-new-feature
# Create pull request in GitHub
```

---

## Troubleshooting

### Port Already in Use

```bash
# Find process using port 8000
lsof -i :8000

# Kill process
kill -9 <PID>
```

### Database Connection Failed

```bash
# Check if PostgreSQL is running
docker-compose ps postgres

# Restart PostgreSQL
docker-compose restart postgres

# Check logs
docker-compose logs postgres
```

### Redis Connection Failed

```bash
# Check if Redis is running
docker-compose ps redis

# Test Redis connection
docker-compose exec redis redis-cli ping
# Should return: PONG
```

### Module Not Found (Python)

```bash
# Ensure virtual environment is activated
source backend/.venv/bin/activate

# Reinstall dependencies
cd backend
uv pip install -r requirements.txt
```

### Cannot Connect to WebSocket

- Ensure backend is running: http://localhost:8000/health
- Check browser console for WebSocket errors
- Verify JWT token is valid
- Check CORS settings in `backend/.env`

---

## Environment-Specific Configurations

### Development (docker-compose)

- Hot reload enabled for both frontend and backend
- Debug mode enabled
- Verbose logging
- CORS allows localhost origins

### Staging/Production (Kubernetes)

See [Kubernetes deployment guide](../k8s/README.md) for:
- Helm charts configuration
- Secret management
- Horizontal pod autoscaling
- Ingress configuration
- Monitoring and logging

---

## Useful Commands Reference

### Backend

```bash
# Run linter
ruff check src/

# Format code
black src/

# Type checking
mypy src/

# Start uvicorn with auto-reload
uvicorn src.main:app --reload

# Generate OpenAPI schema
python -m src.generate_openapi > openapi.yaml
```

### Frontend

```bash
# Run linter
npm run lint

# Format code
npm run format

# Type checking
npm run type-check

# Build for production
npm run build

# Start production server
npm run start

# Analyze bundle size
npm run analyze
```

### Docker

```bash
# Build specific service
docker-compose build backend

# Execute command in running container
docker-compose exec backend bash

# View resource usage
docker stats

# Clean up unused images
docker system prune -a
```

---

## Next Steps

1. **Read the spec**: Review [spec.md](spec.md) for detailed requirements
2. **Explore the API**: Visit http://localhost:8000/docs for interactive API documentation
3. **Review data model**: See [data-model.md](data-model.md) for database schema
4. **Check contracts**: Review [contracts/](contracts/) for API and WebSocket protocols
5. **Start implementing**: See `/speckit.tasks` command output for task breakdown

---

## Support

- **Documentation**: `/docs` directory
- **Issues**: GitHub Issues
- **Slack**: #online-doc-dev
- **Email**: dev-team@example.com

---

## References

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Next.js Documentation](https://nextjs.org/docs)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [Yjs Documentation](https://docs.yjs.dev/)
- [Docker Compose Reference](https://docs.docker.com/compose/)
