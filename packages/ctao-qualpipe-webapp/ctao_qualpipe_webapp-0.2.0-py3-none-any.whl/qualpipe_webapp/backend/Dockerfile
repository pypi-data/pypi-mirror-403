# backend/Dockerfile
FROM harbor.cta-observatory.org/proxy_cache/python:3.12-slim

WORKDIR /app

# Install build dependencies for compiling Python packages
RUN apt-get update && apt-get install -y \
    g++ \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy only the requirements file specified by the build arg (default: requirements.txt)
ARG REQUIREMENTS=requirements.txt
COPY ${REQUIREMENTS} /app/${REQUIREMENTS}

WORKDIR /app

RUN pip install --no-cache-dir -r ${REQUIREMENTS}

# Copy application code (including pre-generated models from CI artifacts)
COPY . /app/backend/

ENV PORT=8000
CMD ["sh", "-c", "python -m uvicorn backend.main:app --host 0.0.0.0 --port $PORT --reload"]
