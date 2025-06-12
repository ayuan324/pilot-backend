# Use a specific Python version for reproducibility
FROM python:3.12.3-slim-bookworm

# Set working directory
WORKDIR /app

# Set environment variables to prevent Python from writing .pyc files and to buffer output
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    # Set the Python path to include the app directory
    PYTHONPATH=/app

# Install system dependencies needed for building Python packages
# - build-essential: for compiling C extensions (for pandas, numpy, etc.)
# - python3-dev: provides headers for building Python extensions
# - libpq-dev: for building psycopg2 (PostgreSQL adapter)
# - curl: for health checks
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        python3-dev \
        libpq-dev \
        curl \
    # Clean up apt cache to reduce image size
    && rm -rf /var/lib/apt/lists/*

# Copy only the requirements file to leverage Docker cache
COPY backend/requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the backend application code
COPY backend/ .

# Expose the port the app runs on
EXPOSE 8000

# Health check to ensure the application is running
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# The command to run the application
CMD ["python", "production_server.py"] 