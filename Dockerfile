# --- Stage 1: Builder ---
FROM python:3.11-slim as builder

WORKDIR /build

# Only install essential build tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Leverage Docker layer caching for dependencies
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# --- Stage 2: Runtime ---
FROM python:3.11-slim as runtime

WORKDIR /app

# Install only the runtime library dependencies (curl for healthcheck)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy only the installed python packages from the builder stage
COPY --from=builder /root/.local /root/.local
COPY . .

# Ensure scripts in .local/bin are in the PATH
ENV PATH=/root/.local/bin:$PATH
# Prevent Python from writing .pyc files and enable unbuffered logging
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

EXPOSE 8000

# Health check (matches your API route structure)
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health || exit 1

# Start the application
CMD ["python", "main.py"]