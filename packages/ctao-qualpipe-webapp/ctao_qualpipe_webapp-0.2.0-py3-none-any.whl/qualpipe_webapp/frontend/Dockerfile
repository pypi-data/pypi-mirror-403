# frontend/Dockerfile
# Stage 1: Build stage (with build tools)
FROM harbor.cta-observatory.org/proxy_cache/python:3.12-slim AS builder

WORKDIR /build

# Install build dependencies for Python packages (libsas)
RUN apt-get update && apt-get install -y build-essential python3-dev

ARG REQUIREMENTS=requirements.txt
COPY ${REQUIREMENTS} ./

# Install packages (compile ndindex, libsass, ecc.)
RUN pip install --no-cache-dir --user -r ${REQUIREMENTS}

# Stage 2: Runtime stage (without build tools)
FROM harbor.cta-observatory.org/proxy_cache/python:3.12-slim

WORKDIR /app

# Copy only installed packages from builder
COPY --from=builder /root/.local /root/.local

# Make sure scripts in .local are usable
ENV PATH=/root/.local/bin:$PATH

# Copy application code (including pre-generated models from CI artifacts)
COPY . /app/

# # Install npm dependencies for frontend JS
# WORKDIR /app/static
# RUN npm install
# WORKDIR /app

ENV PORT=8001
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port $PORT"]
