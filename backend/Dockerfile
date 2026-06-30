# Stage 1: Build dependencies
FROM python:3.12-slim AS builder

WORKDIR /build

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Stage 2: Clean runtime image
FROM python:3.12-slim AS runtime

WORKDIR /app

ENV PATH="/opt/venv/bin:$PATH"
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Create secure system user
RUN groupadd -g 10001 talentmind && \
    useradd -u 10001 -g talentmind -m -s /bin/bash talentmind && \
    chown -R talentmind:talentmind /app

# Copy virtual environment and files
COPY --from=builder /opt/venv /opt/venv
COPY --chown=talentmind:talentmind app/ app/
COPY --chown=talentmind:talentmind .env .env

USER talentmind

EXPOSE 8000

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]

