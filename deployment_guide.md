# TalentMind AI — Production Deployment Guide

This guide details the steps to containerize, configure, deploy, and verify the **TalentMind AI Platform** using Docker and Docker Compose.

---

## Architecture Overview

TalentMind AI is containerized as a multi-service architecture comprising:
1. **Database Service (`db`)**: PostgreSQL 16 relational store for transactional candidate, job, evidence, and analytics metadata.
2. **Backend Service (`backend`)**: FastAPI Python server executing AI agents, orchestrating FAISS vector queries, and managing local cross-encoder models.
3. **Frontend Service (`frontend`)**: Next.js (built as a standalone production image) containing the cinematic storytelling landing page and the high-fidelity recruiter tools workspace.

---

## Directory Setup

The workspace structure for deployment is configured as follows:
```
talentmind-ai/
├── Dockerfile                  # Next.js multi-stage build configuration
├── docker-compose.yml          # Core orchestration compose configuration
├── .dockerignore               # Build context exclusions
├── backend/
│   ├── Dockerfile              # Python FastAPI Docker image configuration
│   └── requirements.txt        # Python backend library dependencies
└── src/                        # Next.js workspace source code
```

---

## 1. Environment Variables Configuration

Create a `.env` file at the root or within `./backend` to control application configurations.

### Backend Environment Variables (`./backend/.env`):
| Variable | Production Value | Description |
| :--- | :--- | :--- |
| `APP_ENV` | `production` | Deploys backend in production mode. |
| `APP_DEBUG` | `false` | Disables traceback leaks in responses. |
| `DATABASE_URL` | `postgresql+asyncpg://postgres:postgres@db:5432/talentmind` | Relational store connection string. |
| `FLAG_SEMANTIC_SEARCH` | `true` | Enables semantic candidate matching. |
| `FLAG_EVIDENCE_ENGINE` | `true` | Activates verification timeline engine. |
| `FLAG_EXPLAINABILITY` | `true` | Renders candidate match narratives. |

### Frontend Environment Variables:
| Variable | Value | Description |
| :--- | :--- | :--- |
| `NEXT_PUBLIC_API_URL` | `http://localhost:8000` | Gateway endpoint for client API calls. |

---

## 2. Docker Compose Deployment

Build and orchestrate all components with a single command:

```bash
# Build images and start services in the background
docker-compose up --build -d
```

### Checking Container Status
Check if all containers are healthy and running:
```bash
docker-compose ps
```

You should see:
* `talentmind_db` - **Healthy** (Port 5432)
* `talentmind_backend` - **Healthy** (Port 8000)
* `talentmind_frontend` - **Healthy** (Port 3000)

---

## 3. Health Checks & Verification

Each container is configured with a custom health check:

### PostgreSQL Health Check
Validates database engine connectivity inside PostgreSQL container:
```bash
pg_isready -U postgres -d talentmind
```

### Backend Health Check
Executes a lightweight Python liveness check directly via `urllib` to verify ASGI server response without requiring `curl` binaries in the secure runtime container:
```bash
python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/live')"
```

### Frontend Health Check
Performs a Node.js HTTP request to check if Next.js handles incoming HTTP traffic:
```bash
node -e "require('http').get('http://localhost:3000/', (r) => process.exit(r.statusCode < 400 ? 0 : 1))"
```

---

## 4. Manual Operations

To run database migrations or execute seed scripts inside the backend container:

```bash
# Enter the backend container
docker-compose exec backend /bin/bash

# Inside the container, run database checks
python scripts/dashboard_stats.py
```

To view logs for troubleshooting:
```bash
docker-compose logs -f backend
docker-compose logs -f frontend
```

---

## 5. Teardown
To shut down the architecture and clean up volumes:
```bash
docker-compose down -v
```
