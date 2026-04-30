# Multi-stage build: Node builds the SPA, then a slim Python image runs FastAPI.
# Final image serves both the API/WebSocket and the prebuilt frontend on one port.

# ---------- Stage 1: build the React frontend ----------
FROM node:20-alpine AS frontend-build

WORKDIR /app/frontend

# Install deps first (better layer caching).
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci

# Build the SPA. Output lands in /app/frontend/dist.
COPY frontend/ ./
RUN npm run build


# ---------- Stage 2: Python runtime ----------
FROM python:3.13-slim AS runtime

# Avoid .pyc clutter and make stdout/stderr unbuffered (important for `docker logs`).
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Install backend deps first for layer caching.
COPY backend/requirements.txt backend/requirements.txt
RUN pip install -r backend/requirements.txt

# Copy backend source.
COPY backend/ backend/

# Copy the prebuilt frontend from stage 1 to the location main.py expects:
# Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"
# = /app/frontend/dist
COPY --from=frontend-build /app/frontend/dist /app/frontend/dist

# Mark this as a server deployment so the in-app updater is disabled.
ENV JUDGEMENT_SERVER_MODE=1

EXPOSE 8000

# Single worker is correct here: GameManager state is in-process memory.
# Multiple workers would mean players landing on different workers see
# different games. Add a load balancer + shared store before scaling.
CMD ["python", "-m", "uvicorn", "backend.app.main:app", \
     "--host", "0.0.0.0", "--port", "8000", \
     "--ws", "websockets", \
     "--proxy-headers", "--forwarded-allow-ips", "*"]
